"""Real D2 SQL API checks and diagnostic NLU on/off probes (dev only).

This is not formal EX and does not approve aliases or gold labels. The ablation
uses the same runtime chat implementation/model/DB, with only nlu_enabled
changed in a local Settings copy; it does not mutate the running API or .env.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx

from qa_agent.config import get_settings, sanitize_error
from qa_agent.llm import JsonLLM
from qa_agent.pipeline import chat
from qa_agent.schemas import ChatRequest


def cases():
    return [
        {"case_id": "api-clear-sql01-dev", "base_id": "sql-01", "question": "客户表共有多少位客户？", "expected_status": "SUCCEEDED", "expected_count": 59},
        {"case_id": "api-canonical-sql02-dev", "base_id": "sql-02", "question": "来自 Brazil 的客户有多少位？", "expected_status": "SUCCEEDED", "expected_count": 5, "expected_method": "exact"},
        {"case_id": "api-fuzzy-sql02-dev", "base_id": "sql-02", "question": "来自 Brasil 的客户有多少位？", "expected_status": "SUCCEEDED", "expected_count": 5, "expected_method": "fuzzy"},
        {"case_id": "api-pinyin-sql05-dev", "base_id": "sql-05", "question": "u s a 的客户有多少位？", "expected_status": "SUCCEEDED", "expected_count": 13, "expected_method": "pinyin"},
        {"case_id": "api-semantic-sql02-dev", "base_id": "sql-02", "question": "来自巴西的客户有多少位？", "expected_status": "SUCCEEDED", "expected_count": 5},
        {"case_id": "api-pending-alias-diagnostic-dev", "base_id": "sql-02", "question": "巴稀的客户有多少位？", "expected_status": "SUCCEEDED", "expected_count": 5, "pending_alias_diagnostic": True},
        {"case_id": "api-unknown-explicit-engineering", "base_id": None, "question": "客户国家恰好为 Narnia，保留原值，不做近似，有多少位客户？", "expected_status": "SUCCEEDED", "expected_count": 0, "expected_no_bindings": True},
        {"case_id": "api-genre-ambiguity-engineering", "base_id": None, "question": "名称为摇滚的流派有哪些？", "expected_status": "NEEDS_CLARIFICATION", "ambiguity_diagnostic": True},
        {"case_id": "api-role-typo-robust03-dev", "base_id": "sql-07", "question": "列出职位为 Sales Suport Agent 的员工编号、名字和姓氏，按员工编号升序。", "expected_status": "SUCCEEDED", "expected_employee_ids": [3, 4, 5], "expected_method": "fuzzy"},
        {"case_id": "api-pinyin-robust11-dev", "base_id": "sql-02", "question": "来自 ba xi 的客户有多少位？", "expected_status": "SUCCEEDED", "expected_count": 5, "expected_method": "llm"},
        {"case_id": "api-pinyin-robust13-dev", "base_id": "sql-32", "question": "客户所在国家为 jia na da 的客户有多少位？", "expected_status": "SUCCEEDED", "expected_count": 8, "expected_method": "llm"},
    ]


def _count(response):
    rows = response.get("table") or []
    return next(iter(rows[0].values())) if len(rows) == 1 and len(rows[0]) == 1 else None


def _check(case, response):
    errors = []
    if response.get("status") != case["expected_status"]:
        errors.append("unexpected_status")
    if "expected_count" in case and _count(response) != case["expected_count"]:
        errors.append("unexpected_count")
    if "expected_employee_ids" in case and [row.get("employee_id") for row in response.get("table") or []] != case["expected_employee_ids"]:
        errors.append("unexpected_employee_ids")
    nlu = response.get("metadata", {}).get("nlu", {})
    if case.get("expected_method") and case["expected_method"] not in {item.get("method") for item in nlu.get("bindings", [])}:
        errors.append("expected_link_method_not_observed")
    if case.get("expected_no_bindings") and nlu.get("bindings"):
        errors.append("unknown_literal_replaced")
    if case["expected_status"] == "NEEDS_CLARIFICATION" and (response.get("sql") or response.get("table")):
        errors.append("ambiguity_should_not_execute")
    if case.get("pending_alias_diagnostic") and any(item.get("method") in {"exact", "pinyin"} for item in nlu.get("bindings", [])):
        # The production build excludes all unapproved Chinese aliases. A
        # semantic candidate decision is different from alias/pinyin success.
        errors.append("unapproved_alias_claimed_as_exact_or_pinyin")
    return errors


def append_record(path, value):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")


def run_api(api_url, output):
    result = []
    with httpx.Client(timeout=180) as client:
        for case in cases():
            started = perf_counter()
            request = {"session_id": "d2-engineering-" + case["case_id"], "message": case["question"],
                       "scope": {"route": "sql", "db_id": "chinook", "doc_ids": []}}
            try:
                http = client.post(api_url.rstrip("/") + "/api/chat", json=request)
                http.raise_for_status()
                response = http.json()
                errors = _check(case, response)
                record = {**case, "test_kind": "real_model_real_DB_main_API", "request": request,
                          "response": response, "errors": errors, "passed": not errors,
                          "client_latency_ms": round((perf_counter() - started) * 1000)}
            except Exception as exc:
                record = {**case, "test_kind": "real_model_real_DB_main_API", "passed": False,
                          "errors": [sanitize_error(exc, get_settings())],
                          "client_latency_ms": round((perf_counter() - started) * 1000)}
            append_record(output / "api-responses.jsonl", record)
            result.append(record)
            print(json.dumps({"case_id": case["case_id"], "status": record.get("response", {}).get("status"),
                              "passed": record["passed"], "errors": record["errors"], "latency_ms": record["client_latency_ms"]}, ensure_ascii=False), flush=True)
    return result


def run_ablation(output):
    settings = get_settings()
    selected = [cases()[1], cases()[2], cases()[3]]
    results = []
    for case in selected:
        for enabled in (False, True):
            copied_settings = replace(settings, nlu_enabled=enabled)
            started = perf_counter()
            response = chat(ChatRequest(message=case["question"]), llm=JsonLLM(copied_settings), settings=copied_settings)
            value = response.model_dump(mode="json")
            errors = _check({key: item for key, item in case.items() if key != "expected_method"}, value)
            record = {**case, "test_kind": "real_model_real_DB_same_runtime_direct_diagnostic_ablation",
                      "nlu_enabled": enabled, "source": "same qa_agent.pipeline.chat; not main API EX benchmark",
                      "response": value, "passed": not errors, "errors": errors,
                      "client_latency_ms": round((perf_counter() - started) * 1000),
                      "model": settings.llm_model, "safety_checks_enabled": True,
                      "response_cache_used": False, "human_review_status": "pending"}
            append_record(output / "ablation-responses.jsonl", record)
            results.append(record)
            print(json.dumps({"case_id": case["case_id"], "nlu_enabled": enabled, "status": value["status"],
                              "passed": record["passed"], "latency_ms": record["client_latency_ms"]}, ensure_ascii=False), flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "eval/artifacts/d2/a-live")
    parser.add_argument("--mode", choices=["api", "ablation", "both"], default="both")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = ["api-responses.jsonl", "ablation-responses.jsonl", "summary.json"]
    if any((args.output_dir / name).exists() for name in files):
        raise ValueError("输出目录已含检查结果，请选新目录，不覆盖原始证据。")
    start = datetime.now(timezone.utc).isoformat()
    api = run_api(args.api_url, args.output_dir) if args.mode in {"api", "both"} else []
    ablation = run_ablation(args.output_dir) if args.mode in {"ablation", "both"} else []
    sources = ["qa_agent/nlu/linker.py", "qa_agent/pipeline.py", "qa_agent/sql/validator.py", "qa_agent/sql/executor.py", "scripts/check_d2_sql_live.py"]
    summary = {"started_at_utc": start, "ended_at_utc": datetime.now(timezone.utc).isoformat(),
               "command": [sys.executable, *sys.argv], "api_url": args.api_url, "model": get_settings().llm_model,
               "api_passed": sum(item["passed"] for item in api), "api_count": len(api),
               "ablation_passed": sum(item["passed"] for item in ablation), "ablation_count": len(ablation),
               "human_review_status": "pending", "holdout_model_requests": 0,
               "source_sha256": {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
               "api_errors": [{"case_id": item["case_id"], "errors": item["errors"]} for item in api if not item["passed"]],
               "ablation_errors": [{"case_id": item["case_id"], "nlu_enabled": item["nlu_enabled"], "errors": item["errors"]} for item in ablation if not item["passed"]]}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("api_passed", "api_count", "ablation_passed", "ablation_count")}, ensure_ascii=False))
    # Diagnostic failures are recorded, not hidden by deleting failed rows.
    if summary["api_errors"] or summary["ablation_errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
