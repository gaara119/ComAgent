"""Run the 21 reviewed AW DEV questions once through the active public API.

Only question, source scope and independent session identifiers are sent. Gold,
labels and review records stay local and are read only for after-call scoring.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter
from types import SimpleNamespace
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx

from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.catalog import load_catalog
from scripts.d4_bench_utils import compare_case, provenance, runtime_source_files, summarize, trace_cost, write_json


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def associate_provider(envelope: dict, output: Path) -> list[dict]:
    records = []
    for step in envelope.get("steps", []):
        if step.get("name") != "llm":
            continue
        name = step.get("output_summary", {}).get("provider_capture")
        if not name:
            records.append({"available": False, "reason": "No provider capture in this actual LLM trace step."})
            continue
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            records.append({"available": False, "provider_capture": name, "reason": "Captured source file missing."})
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("trace_id") != envelope["trace_id"]:
            raise ValueError("Provider trace does not match this API response.")
        destination = output / "provider" / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and digest(destination) != digest(path):
            raise ValueError("Existing provider evidence has different content.")
        shutil.copyfile(path, destination)
        records.append({"available": True, "trace_id": envelope["trace_id"], "source": name,
            "copy": destination.relative_to(output).as_posix(), "sha256": digest(path),
            "attempt": payload.get("attempt"),
            "provider_response_id": (payload.get("response") or {}).get("id"),
            "provider_model": (payload.get("response") or {}).get("model"),
            "has_actual_response": bool(payload.get("response")),
            "error": payload.get("error")})
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "eval/datasets/manual-applied-20261013-v3/aw-dev.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "eval/artifacts/manual-applied-20261013-v1/aw-live-001")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--case-id", action="append", help="Scoped regression IDs from the same verified AW21 DEV source")
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.dataset = args.dataset.resolve()
    if args.output.exists() or not args.output.is_relative_to(ROOT / "eval/artifacts"):
        raise ValueError("Use a fresh, project-local artifact directory.")
    cases = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if len(cases) != 21 or len({row["id"] for row in cases}) != 21 or any(
        row.get("split") != "dev" or row.get("db_id") != "adventureworks" or
        row.get("dataset_version") != "manual-applied-20261013-v3" or not row.get("enabled") or not row.get("scorable")
        for row in cases):
        raise ValueError("Only the exact active reviewed AW21 DEV version is permitted.")
    if args.case_id:
        wanted = set(args.case_id)
        if not wanted <= {row["id"] for row in cases}:
            raise ValueError("Regression IDs must belong to the reviewed development source.")
        cases = [row for row in cases if row["id"] in wanted]
    expected_count = len(cases)
    settings = get_settings()
    if settings.aw_schema_mode != "subgraph" or settings.aw_catalog_path.name != "adventureworks-manual-applied-v1.yaml":
        raise ValueError("Reviewed catalog and normal subgraph mode must be active.")
    catalog = load_catalog(settings.aw_catalog_path)
    index_meta = settings.aw_schema_index_path / "metadata.json"
    if json.loads(index_meta.read_text(encoding="utf-8"))["catalog_sha256"] != digest(settings.aw_catalog_path):
        raise ValueError("The active schema index does not match the reviewed catalog.")
    evidence_files = [args.dataset, settings.aw_catalog_path, index_meta, ROOT / "api/main.py",
        ROOT / "eval/metrics.py", Path(__file__).resolve(), ROOT / "scripts/d4_bench_utils.py"] + runtime_source_files(ROOT)
    meta = provenance(ROOT, settings, evidence_files)
    meta.update({"dataset_version": "manual-applied-20261013-v3", "mode": "subgraph", "API": args.api + "/api/chat",
        "scope": "One actual independent request per reviewed development case; no new ablation or holdout predictions",
        "request_fields": ["session_id", "message", "scope"], "gold_or_review_sent_to_system": False,
        "concurrency": 1, "other_correctness_suites_may_run_concurrently": True,
        "not_an_efficiency_measurement": True, "gold_method": "Reuse newly verified qa_reader read-only 5s results",
        "catalog_tables": len(catalog.tables), "catalog_columns": sum(len(t.columns) for t in catalog.tables),
        "requested_case_ids": [case["id"] for case in cases], "requests_planned": expected_count,
        "schema_index_artifact_sha256": {path.name: digest(path) for path in settings.aw_schema_index_path.iterdir() if path.is_file()}})
    args.output.mkdir(parents=True)
    write_json(args.output / "command.json", {"command": [sys.executable, "-B", *sys.argv], "cwd": str(ROOT),
        "started_at_utc": datetime.now(timezone.utc).isoformat(), "python_version": sys.version.split()[0]})
    write_json(args.output / "provenance.json", meta)
    records = []
    with httpx.Client(timeout=240, trust_env=False) as client:
        health = client.get(args.api + "/health").raise_for_status().json()
        if not health.get("aw_database_ready") or health.get("aw_schema_mode") != "subgraph":
            raise ValueError("Actual active API is not ready for AW subgraph calls.")
        write_json(args.output / "health-before.json", health)
        for case in cases:
            gold_path = (ROOT / case["gold_verification_evidence"]).resolve()
            verified = json.loads(gold_path.read_text(encoding="utf-8"))
            expected_rows = [[row[column] for column in case["gold_columns"]] for row in case["gold_result"]]
            if verified["columns"] != case["gold_columns"] or verified["rows"] != expected_rows or verified["submitted_sql"] != case["gold_sql"]:
                raise ValueError("This reviewed gold does not match its actual read-only result record.")
            if verified["current_user"] != "qa_reader" or verified["transaction_read_only"] != "on" or verified["statement_timeout"] != "5s":
                raise ValueError("Gold verification did not use the expected read-only/timeout policy.")
            gold = SimpleNamespace(columns=case["gold_columns"], rows=expected_rows)
            payload = {"session_id": "reviewed-aw-" + uuid4().hex,
                "message": case["question"], "scope": {"route": "sql", "db_id": "adventureworks", "doc_ids": []}}
            record = {"id": case["id"], "split": "dev", "dataset_version": case["dataset_version"],
                "request": payload, "gold_verification_evidence": case["gold_verification_evidence"],
                "gold_verification_sha256": digest(gold_path), "gold_or_review_sent_to_system": False,
                "started_at_utc": datetime.now(timezone.utc).isoformat()}
            started = perf_counter()
            try:
                raw = client.post(args.api + "/api/chat", json=payload)
                record["http_status"] = raw.status_code
                record["raw_response_text"] = raw.text
                raw.raise_for_status()
                envelope = raw.json()
                record["response"] = envelope
                record["cost"] = trace_cost(envelope)
                record.update(compare_case(case, envelope, catalog, gold))
                record["provider_records"] = associate_provider(envelope, args.output)
                record["provider_capture_complete"] = bool(record["provider_records"]) and all(p["available"] for p in record["provider_records"])
                write_json(args.output / "traces" / (case["id"] + ".json"), {"trace_id": envelope["trace_id"], "steps": envelope["steps"], "metadata": envelope.get("metadata")})
            except Exception as error:
                record.update({"matched": False, "legacy_matched": False, "failure_category": "runner_exception",
                    "error": sanitize_error(error, settings)})
            record["elapsed_ms"] = round((perf_counter() - started) * 1000, 3)
            record["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            records.append(record)
            write_json(args.output / "cases" / (case["id"] + ".json"), record)
            with (args.output / "responses.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(case["id"], record.get("response", {}).get("status", "NO_RESPONSE"), "EX=" + str(record["matched"]), flush=True)
            write_json(args.output / "report.json", {"status": "RUNNING", "completed": len(records), "expected": expected_count})
        write_json(args.output / "health-after.json", client.get(args.api + "/health").raise_for_status().json())
    source_after = provenance(ROOT, settings, evidence_files)["source_sha256"]
    write_json(args.output / "source-sha256-after.json", source_after)
    report = {"status": "ACTUALLY_RUN_DEV", "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "summary": summarize(records), "source_sha256": meta["source_sha256"],
        "runtime_and_dataset_sources_unchanged": meta["source_sha256"] == source_after,
        "provider_capture_complete_requests": sum(r.get("provider_capture_complete", False) for r in records),
        "provider_records": sum(len(r.get("provider_records", [])) for r in records),
        "held_predictions": 0, "business_prompt_or_gold_changed": False,
        "measurement_caveat": "Current API correctness regression only; concurrent suites mean recorded latency is not a new efficiency score.",
        "failed_cases": [{"id": r["id"], "status": r.get("response", {}).get("status"), "reason": r.get("failure_category"), "error": r.get("error")} for r in records if not r.get("matched")]}
    write_json(args.output / "report.json", report)
    lines = [f"# 正式审核应用后 AW开发集 API 回归（本轮{expected_count}题）", "", "采用 v3 正式题库、新中文目录和匹配BGE索引；每题一次正常subgraph请求。", "",
        f"方案EX：{report['summary']['correct']}/{expected_count}；旧EX：{report['summary']['legacy_correct']}/{expected_count}。",
        f"provider关联完整：{report['provider_capture_complete_requests']}/{expected_count}；原始返回/调用记录：{report['provider_records']}条。", "",
        "只发送题面、来源范围和独立session；gold/标签/审核文件仅留在本地评分。保留集未读取、未预测。",
        "SQL gold复用本轮已保存的qa_reader只读5秒实跑记录，并逐项核对SQL/列/结果摘要。",
        "本次是正确性回归，其他正确性套件可同时运行，耗时不作为新效率成绩。", "",
        "|原ID|实际状态|方案EX|旧EX|问题|", "|---|---|---|---|---|"]
    for r in records:
        lines.append(f"|{r['id']}|{r.get('response',{}).get('status','NO_RESPONSE')}|{r['matched']}|{r['legacy_matched']}|{r.get('failure_category') or ''}|")
    lines.extend(["", "命令与来源摘要见command.json/provenance.json；逐题raw request/response见cases/和responses.jsonl；trace见traces/；provider原始记录见provider/。"])
    (args.output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("runtime_and_dataset_sources_unchanged", "provider_capture_complete_requests", "provider_records", "failed_cases")}, ensure_ascii=False), flush=True)
    return 0 if report["summary"]["correct"] == expected_count and report["runtime_and_dataset_sources_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
