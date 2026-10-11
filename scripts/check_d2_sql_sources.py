"""Actual main-API regression for explicit source rejection and legal emptiness."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
from qa_agent.config import get_settings, sanitize_error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "eval/artifacts/d2/a-live/source-guard")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw = args.output_dir / "responses.jsonl"
    if raw.exists():
        raise ValueError("不能覆盖已有原始记录，请选择新 --output-dir。")
    cases = [
        {"id": "unknown-explicit-source", "question": "请仅查询数据库中明确不存在的 d2_nonexistent_table_20261010 表，列出前5行。不得换成customer或其他现有表，不得猜测结果；无法执行就如实失败。", "expected_status": "FAILED", "expected_no_execution": True},
        {"id": "known-customer-source", "question": "customer 表共有多少位客户？", "expected_status": "SUCCEEDED", "expected_count": 59, "expected_source": "customer"},
        {"id": "known-source-legal-empty-count", "question": "customer 表国家恰好为 Narnia，保留原值，不做近似，有多少位客户？", "expected_status": "SUCCEEDED", "expected_count": 0, "expected_source": "customer"},
        {"id": "known-invoice-source", "question": "invoice 表共有多少张发票？", "expected_status": "SUCCEEDED", "expected_count": 412, "expected_source": "invoice"},
    ]
    results = []
    started = datetime.now(timezone.utc).isoformat()
    with httpx.Client(timeout=180) as client:
        for case in cases:
            request = {"session_id": "d2-source-guard-" + case["id"], "message": case["question"],
                       "scope": {"route": "sql", "db_id": "chinook", "doc_ids": []}}
            start = perf_counter()
            errors, response = [], {}
            try:
                http = client.post(args.api_url.rstrip("/") + "/api/chat", json=request)
                http.raise_for_status()
                response = http.json()
                if response["status"] != case["expected_status"]:
                    errors.append("unexpected_status")
                steps = response.get("steps", [])
                if case.get("expected_no_execution"):
                    if response.get("sql") or response.get("table"):
                        errors.append("unknown_source_has_query_or_rows")
                    if any(step["name"] in {"sql_exec", "llm"} for step in steps):
                        errors.append("unknown_source_called_model_or_database")
                    if response.get("error", {}).get("code") != "sql_rejected":
                        errors.append("expected_actual_source_error_missing")
                else:
                    table = response.get("table") or []
                    count = next(iter(table[0].values())) if len(table) == 1 and len(table[0]) == 1 else None
                    if count != case["expected_count"]:
                        errors.append("unexpected_count")
                    source_step = next((step for step in steps if step["name"] == "requested_source_check"), None)
                    if source_step is None or source_step["output_summary"].get("explicit_tables") != [case["expected_source"]]:
                        errors.append("explicit_source_not_observed")
                    if not any(step["name"] == "sql_exec" for step in steps):
                        errors.append("known_source_not_executed")
            except Exception as exc:
                errors.append(sanitize_error(exc, get_settings()))
            record = {**case, "test_kind": "actual_main_API_model_DB_engineering; unknown source has zero model/execute calls",
                      "request": request, "response": response, "errors": errors, "passed": not errors,
                      "client_latency_ms": round((perf_counter() - start) * 1000), "human_review_status": "pending"}
            with raw.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            results.append(record)
            print(json.dumps({"id": case["id"], "status": response.get("status"), "passed": record["passed"],
                              "errors": errors, "latency_ms": record["client_latency_ms"]}, ensure_ascii=False), flush=True)
    summary = {"started_at_utc": started, "ended_at_utc": datetime.now(timezone.utc).isoformat(),
               "command": [sys.executable, *sys.argv], "passed": sum(item["passed"] for item in results),
               "count": len(results), "holdout_requests": 0, "human_review_status": "pending",
               "source_sha256": {name: sha256((ROOT / name).read_bytes()).hexdigest()
                                  for name in ("qa_agent/pipeline.py", "qa_agent/sql/validator.py", "scripts/check_d2_sql_sources.py")},
               "original_bug_record": "eval/artifacts/d2/e2e/browser/d2-live-v1/failure-raw.json",
               "errors": [{"id": item["id"], "errors": item["errors"]} for item in results if not item["passed"]]}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": summary["passed"], "count": summary["count"]}, ensure_ascii=False))
    if summary["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
