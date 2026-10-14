"""Same 20 Chinook DEV questions, three repetitions at original/10k/100k.

All predictions use chat(), so NLU, linking, generation, validation, bounded
repair and read-only execution have the same runtime as the application.
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
import psycopg
import sqlglot
from sqlglot import exp

from qa_agent.config import get_settings, sanitize_error
from qa_agent.pipeline import chat
from qa_agent.schemas import ChatRequest, SourceScope
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql
from scripts.d4_bench_utils import compare_case, provenance, runtime_source_files, summarize, trace_cost, write_json


def remap_sql(source_sql, schema):
    tree = sqlglot.parse_one(source_sql, read="postgres")
    # These reused DEV golds are direct SELECTs with genuine physical tables.
    # Refuse CTEs rather than mistaking a CTE alias for a source table.
    if tree.args.get("with_"):
        raise ValueError("Stress label remapping only supports these verified direct SELECT golds")
    for table in tree.find_all(exp.Table):
        if table.db not in {"", "public"}:
            raise ValueError("A reused Chinook standard SQL unexpectedly references another schema")
        table.set("db", exp.to_identifier(schema))
    return tree.sql(dialect="postgres")


def load_cases():
    join_path = ROOT / "eval/datasets/oct12/chinook_join_dev_v1.jsonl"
    sql_path = ROOT / "eval/artifacts/d2-final/review/sql-dev-v1.jsonl"
    joins = [json.loads(line) for line in join_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    single = [json.loads(line) for line in sql_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = {"sql-09", "sql-15", "sql-18", "sql-33", "sql-39"}
    cases = joins + [case for case in single if case["id"] in ids]
    if len(joins) != 15 or len(cases) != 20 or any(case.get("split") != "dev" for case in cases):
        raise ValueError("Stress test requires exactly these 20 previously exposed DEV questions")
    return cases, [join_path, sql_path]


def explain_readonly(db_url, sql, timeout_ms):
    with psycopg.connect(db_url, connect_timeout=5) as conn:
        conn.read_only = True
        with conn.transaction():
            conn.execute("SELECT set_config('statement_timeout',%s,true)", (str(timeout_ms),))
            return conn.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql).fetchone()[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scale-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.scale_manifest = args.scale_manifest.resolve()
    if args.output.exists():
        raise ValueError("Choose a fresh evidence directory")
    scales = json.loads(args.scale_manifest.read_text(encoding="utf-8"))
    if scales.get("status") != "ACTUALLY_CREATED_AND_VERIFIED" or not scales.get("original_public_unchanged"):
        raise ValueError("Only verified, isolated stress copies may be benchmarked")
    if {scale["line_count"] for scale in scales["scales"]} != {10000, 100000}:
        raise ValueError("Both planned stress scales are required")
    args.output.mkdir(parents=True)
    settings = get_settings()
    cases, sources = load_cases()
    groups = [{"id":"original","schema":"public","catalog":settings.catalog_path,
               "line_count":scales["original_public_fingerprints"]["invoice_line"]["count"]}] + [
        {"id":str(scale["line_count"]),"schema":scale["schema"],"catalog":ROOT / scale["catalog"],
         "line_count":scale["line_count"]} for scale in scales["scales"]]
    evidence_sources = sources + [args.scale_manifest] + [group["catalog"] for group in groups] + [
        ROOT / "eval/metrics.py", ROOT / "scripts/d4_sql_scale.py", ROOT / "scripts/d4_bench_utils.py"] + runtime_source_files(ROOT)
    metadata = provenance(ROOT, settings, evidence_sources)
    case_scope = {}
    for case in cases:
        tables = {table.name for table in sqlglot.parse_one(case["gold_sql"], read="postgres").find_all(exp.Table)}
        case_scope[case["id"]] = {"tables": sorted(tables),
            "scale_effect": "expanded_invoice_line" if "invoice_line" in tables else (
                "expanded_invoice" if "invoice" in tables else "nonexpanded_dimension_control")}
    metadata.update({"question_count":20,"repetitions":3,"expected_predictions":180,
        "same_questions_all_scales":True,"concurrency":1,"warmup":"one-time local model setup before request timing; recorded separately",
        "gold_policy":"validated standard SQL is separately executed on EVERY physical schema; never reuse original result",
        "scoring": "plan §5.2 main EX: continuous numeric quantities rounded to 2 decimals; integer keys/counts exact; legacy exact non-money quantities separately",
        "question_scope": case_scope,
        "scope_counts": {name: sum(value["scale_effect"] == name for value in case_scope.values())
            for name in ("expanded_invoice_line", "expanded_invoice", "nonexpanded_dimension_control")},
        "groups":[{**group,"catalog":group["catalog"].relative_to(ROOT).as_posix()} for group in groups]})
    write_json(args.output / "provenance.json", metadata)
    write_json(args.output / "questions.json", [{"id":case["id"],"question":case["question"],"split":"dev",
        "source_gold_review":case.get("gold_review")} for case in cases])
    os.environ["LLM_CAPTURE_DIR"] = str((args.output / "provider").resolve())
    # Load the same existing embedder once. This is setup, not a fake warm query.
    started = perf_counter()
    from qa_agent.rag.embeddings import get_embedder
    embedder = get_embedder(settings)
    if embedder is not None:
        embedder.encode(["D4性能测试初始化"])
    write_json(args.output / "setup.json", {"actual_local_model_setup_ms":round((perf_counter()-started)*1000,3),
                                           "model_call":False,"excluded_from_request_latency":True})
    catalogs, golds = {}, {}
    for group in groups:
        catalog = load_catalog(group["catalog"])
        catalogs[group["id"]] = catalog
        for case in cases:
            sql = validate_sql(remap_sql(case["gold_sql"], group["schema"]), catalog, max_rows=settings.max_rows).sql
            gold = execute_sql(sql, settings.db_url, statement_timeout_ms=settings.statement_timeout_ms,
                               max_rows=settings.max_rows)
            golds[(group["id"],case["id"])] = gold
            write_json(args.output / "gold-readonly" / group["id"] / f"{case['id']}.json", {
                "id":case["id"],"schema":group["schema"],"sql":sql,"result":asdict(gold),
                "source_gold_review":case.get("gold_review"),"derivation":"same SQL business logic, only physical schema remapped"})
        for name, sql in {
            "indexed_invoice_lookup":f"SELECT COUNT(*) FROM {group['schema']}.invoice_line WHERE invoice_id=1",
            "scan_aggregate":f"SELECT SUM(unit_price*quantity) FROM {group['schema']}.invoice_line"}.items():
            validated = validate_sql(sql, catalog).sql
            write_json(args.output / "explain-readonly" / f"{group['id']}-{name}.json", {
                "command":"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + validated,
                "connection":"existing qa_reader; read_only transaction; 5000ms timeout",
                "plan":explain_readonly(settings.db_url,validated,settings.statement_timeout_ms)})
    records = []
    # Rotate scale order across repetitions so original is not always first.
    for repetition in range(1,4):
        for case in cases:
            offset = (repetition - 1) % len(groups)
            for group in groups[offset:] + groups[:offset]:
                active_settings = replace(settings, catalog_path=group["catalog"])
                request = ChatRequest(session_id=f"d4-scale-{uuid4().hex}-{case['id']}",message=case["question"],
                                      scope=SourceScope(route="sql",db_id="chinook"))
                record = {"id":case["id"],"scale":group["id"],"schema":group["schema"],"repetition":repetition,
                          "split":"dev","request":request.model_dump(mode="json")}
                started = perf_counter()
                try:
                    envelope = chat(request,settings=active_settings).model_dump(mode="json")
                    record["response"] = envelope
                    record["cost"] = trace_cost(envelope)
                    record.update(compare_case(case,envelope,catalogs[group["id"]],golds[(group["id"],case["id"])]))
                    record["executed_source_tables"] = [step.get("output_summary",{}).get("tables",[]) for step in
                        envelope.get("steps",[]) if step["name"] == "sql_validate" and step.get("status") != "error"]
                    if group["schema"] != "public" and envelope.get("sql"):
                        actual = sqlglot.parse_one(envelope["sql"],read="postgres")
                        # Returning to public would invalidate the data-scale claim.
                        physical = [table for table in actual.find_all(exp.Table)]
                        if any(table.db != group["schema"] for table in physical):
                            record.update({"matched":False,"legacy_matched":False,
                                           "failure_category":"stress_query_escaped_physical_schema"})
                except Exception as exc:
                    record.update({"matched":False,"legacy_matched":False,"failure_category":"runner_exception",
                                   "error":sanitize_error(exc,settings)})
                record["elapsed_ms"] = round((perf_counter()-started)*1000,3)
                records.append(record)
                write_json(args.output / "cases" / f"{case['id']}-{group['id']}-r{repetition}.json",record)
                with (args.output / "responses.jsonl").open("a",encoding="utf-8") as stream:
                    stream.write(json.dumps(record,ensure_ascii=False)+"\n")
                print(len(records),"/180",case["id"],group["id"],repetition,record["matched"],record["elapsed_ms"],flush=True)
                write_json(args.output / "report.json",{"status":"RUNNING","completed":len(records),"expected":180})
    end_sources = provenance(ROOT, settings, evidence_sources)["source_sha256"]
    write_json(args.output / "source-sha256-after.json", end_sources)
    summary = {"status":"ACTUALLY_RUN_DEV","provenance":metadata,"holdout_predictions":0,
               "runtime_and_sources_unchanged": metadata["source_sha256"] == end_sources,
               "groups":{group["id"]:summarize([row for row in records if row["scale"]==group["id"]]) for group in groups}}
    write_json(args.output / "report.json",summary)
    lines = ["# D4 SQL数据规模效率实测","","同20道既有开发问题，每规模每题3次，共180次完整chat调用；原库与副本结果分别计算。","",
        "|规模|请求/正确|NLU P50/P90 ms|值链接|④定位|SQL生成|SQL执行|检索|答案组织|端到端P50/P90 ms|",
        "|---|---|---|---|---|---|---|---|---|---|"]
    for group in groups:
        measured = summary["groups"][group["id"]]
        parts = []
        for stage in ("nlu","value_link","schema_selection","sql_generation","sql_execution","retrieval","answer_generation"):
            value = measured["stages"].get(stage,{"p50_ms":0,"p90_ms":0})
            parts.append(f"{value['p50_ms']}/{value['p90_ms']}")
        lines.append(f"|{group['line_count']}明细|{measured['requests']}/{measured['correct']}|"+"|".join(parts)+
            f"|{measured['end_to_end']['p50_ms']}/{measured['end_to_end']['p90_ms']}|")
    lines += ["","Chinook链路不调用AW④或文档检索，相应阶段0代表未使用，并非测得零开销。NLU取clarification_gate，值链接单列。",
              f"固定20题中，涉及invoice_line的{metadata['scope_counts']['expanded_invoice_line']}题、只涉及扩容invoice的{metadata['scope_counts']['expanded_invoice']}题、未扩容维表对照{metadata['scope_counts']['nonexpanded_dimension_control']}题；不可把维表延迟当明细扩容影响。",
              "主EX按方案§5.2取连续数值两位小数，旧EX另报；全部原始结果不变。原题带固定时间筛选时，不保证一定扫描所有新增行。",
              "嵌套trace步骤不能相加；端到端使用独立实际计时。失败、重试均计入请求统计，不能只取成功请求掩盖性能。",
              "一次性本地模型加载单独保存在setup.json。压测复制策略改变IDs、日期、发票数量和总额，均为合成压测数据。",
              "每题每规模参考SQL与结果见gold-readonly；两条代表性SQL的EXPLAIN ANALYZE见explain-readonly。"]
    (args.output / "report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
