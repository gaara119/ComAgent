"""D4 paired AW development ablation using the SAME actual chat pipeline.

Both arms generate/validate/repair/execute/score normally. Only Settings'
schema mode differs; all 21 development questions are passed without labels.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qa_agent.config import get_settings, sanitize_error
from qa_agent.pipeline import chat
from qa_agent.schemas import ChatRequest, SourceScope
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql
from scripts.d4_bench_utils import compare_case, provenance, runtime_source_files, summarize, trace_cost, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    if args.output.exists():
        raise ValueError("Choose a fresh evidence directory")
    args.output.mkdir(parents=True)
    settings = get_settings()
    source = ROOT / "eval/datasets/d3/aw_schema_link.dev.v2.jsonl"
    cases = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(cases) != 21 or any(case.get("split") != "dev" for case in cases):
        raise ValueError("Only the fixed 21 AW development cases are permitted")
    catalog = load_catalog(settings.aw_catalog_path)
    evidence_sources = [source, settings.aw_catalog_path, ROOT / "eval/metrics.py",
        ROOT / "scripts/d4_aw_ablation.py", ROOT / "scripts/d4_bench_utils.py"] + runtime_source_files(ROOT)
    metadata = provenance(ROOT, settings, evidence_sources)
    metadata.update({"group_difference": "aw_schema_mode only", "arms": ["full", "subgraph"],
        "selector_inputs": "question + authentic candidate catalog + verified bindings; no gold tables/SQL/results",
        "gold_review": "source statuses retained; team approval tracked separately", "catalog_table_count": len(catalog.tables),
        "ordering": "paired alternating full/subgraph then subgraph/full, same question in each pair",
        "scoring": "plan §5.2 main EX: continuous numeric quantities rounded to 2 decimals; integer keys/counts exact; global column mapping; row order follows case. Legacy exact non-money quantities reported separately.",
        "concurrency": 1,
        "not_run": ["recall-only arm", "recall+FK arm", "9 held questions"]})
    write_json(args.output / "provenance.json", metadata)
    os.environ["LLM_CAPTURE_DIR"] = str((args.output / "provider").resolve())
    started = perf_counter()
    from qa_agent.rag.embeddings import get_embedder
    embedder = get_embedder(settings)
    if embedder is not None:
        embedder.encode(["D4性能测试初始化"])
    write_json(args.output / "setup.json", {"actual_local_model_setup_ms": round((perf_counter()-started)*1000,3),
        "model_call": False, "excluded_from_request_latency": True,
        "purpose": "Load the existing local embedder once before both arms; no question, labels, SQL or gold supplied."})
    records = []
    for position, case in enumerate(cases):
        validated = validate_sql(case["gold_sql"], catalog, max_rows=settings.max_rows)
        gold = execute_sql(validated.sql, settings.aw_db_url, statement_timeout_ms=settings.statement_timeout_ms,
                           max_rows=settings.max_rows, db_id="adventureworks")
        write_json(args.output / "gold-readonly" / f"{case['id']}.json", {
            "id": case["id"], "sql": validated.sql, "result": asdict(gold),
            "source_gold_review": case.get("gold_review"), "prediction": False})
        for arm in (["full", "subgraph"] if position % 2 == 0 else ["subgraph", "full"]):
            request = ChatRequest(session_id=f"d4-aw-{uuid4().hex}-{case['id']}-{arm}",
                message=case["question"], scope=SourceScope(route="sql", db_id="adventureworks"))
            active_settings = replace(settings, aw_schema_mode=arm)
            record = {"id": case["id"], "split": "dev", "arm": arm,
                      "request": request.model_dump(mode="json")}
            started = perf_counter()
            try:
                envelope = chat(request, settings=active_settings).model_dump(mode="json")
                record["response"] = envelope
                record["cost"] = trace_cost(envelope)
                record.update(compare_case(case, envelope, catalog, gold))
                # Labels are used ONLY after inference for recall measurement.
                selected = set((envelope.get("metadata", {}).get("schema_linker") or {}).get("selected_tables", []))
                if arm == "full":
                    selected = {f"{table.schema}.{table.name}" for table in catalog.tables}
                labels = set(case["gold_tables"])
                record.update({"selected_table_count": len(selected), "schema_recall": len(selected & labels)/len(labels),
                               "schema_precision": len(selected & labels)/len(selected) if selected else 0})
            except Exception as exc:
                record.update({"matched": False, "legacy_matched": False, "failure_category": "runner_exception",
                               "error": sanitize_error(exc, settings)})
            record["elapsed_ms"] = round((perf_counter() - started) * 1000, 3)
            records.append(record)
            write_json(args.output / "cases" / f"{case['id']}-{arm}.json", record)
            with (args.output / "responses.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(case["id"], arm, record["matched"], record["elapsed_ms"], flush=True)
            write_json(args.output / "report.json", {"status": "RUNNING", "completed": len(records), "expected": 42})
    end_sources = provenance(ROOT, settings, evidence_sources)["source_sha256"]
    write_json(args.output / "source-sha256-after.json", end_sources)
    summary = {"status": "ACTUALLY_RUN_DEV", "provenance": metadata, "holdout_predictions": 0,
        "runtime_and_sources_unchanged": metadata["source_sha256"] == end_sources,
        "groups": {arm: summarize([row for row in records if row["arm"] == arm]) for arm in ("full", "subgraph")}}
    for arm, group in summary["groups"].items():
        rows = [row for row in records if row["arm"] == arm]
        group["mean_selected_table_count"] = sum(row.get("selected_table_count", 0) for row in rows)/len(rows)
        group["mean_schema_recall"] = sum(row.get("schema_recall", 0) for row in rows)/len(rows)
        group["mean_schema_precision"] = sum(row.get("schema_precision", 0) for row in rows)/len(rows)
    write_json(args.output / "report.json", summary)
    full, subgraph = summary["groups"]["full"], summary["groups"]["subgraph"]
    lines = ["# D4 ④全量schema／完整子图真实开发对照", "", "21道相同开发题，42次真实pipeline调用；9道保留题未读未运行。", "",
        "|方式|EX|旧EX|全链路输入token|SQL生成输入token|④选表输入token|端到端P50/P90 ms|", "|---|---|---|---|---|---|---|"]
    for arm, group in summary["groups"].items():
        usage = group["usage_total"]
        lines.append(f"|{arm}|{group['correct']}/21|{group['legacy_correct']}/21|{usage.get('prompt_tokens',0)}|"
            f"{usage.get('sql_generation_prompt_tokens',0)}|{usage.get('schema_selection_prompt_tokens',0)}|"
            f"{group['end_to_end']['p50_ms']}/{group['end_to_end']['p90_ms']}|")
    lines += ["", "全链路token包含NLU、④剪枝、SQL生成与技术修复；不能用SQL生成阶段节省量代替总节省量。",
              "主EX遵循方案§5.2的两位小数和全局列映射；旧EX对非金额连续值仍作精确比较。参考答案/人工状态未改写。",
              "单次实测受模型随机性和网络影响；无统计显著性保证，所有失败计入EX。两中间消融组本轮未扩展。",
              "逐题真实请求、响应、SQL、trace/usage、评分与provider原始返回见 cases/、responses.jsonl、provider/。"]
    (args.output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
