"""Run six DEV cross-source cases on the actual existing API; preserve raw turns."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql
from eval.metrics import compare_plan_results


def gold_sql(case):
    if case["expected_plan"] == "sql_to_doc":
        dates = (f"JOIN public.invoice i ON i.invoice_id=il.invoice_id WHERE i.invoice_date>=DATE '{case['year']}-01-01' "
                 f"AND i.invoice_date<DATE '{case['year']+1}-01-01' " if case.get("year") else "")
        return ("SELECT a.artist_id AS artist_id,a.name AS artist_name,SUM(il.unit_price*il.quantity) AS sales_amount "
                "FROM public.artist a JOIN public.album al ON al.artist_id=a.artist_id "
                "JOIN public.track t ON t.album_id=al.album_id JOIN public.invoice_line il ON il.track_id=t.track_id "
                + dates + "GROUP BY a.artist_id,a.name ORDER BY sales_amount DESC,a.artist_id ASC LIMIT 1")
    return ("SELECT AVG(i.total) AS average_invoice_amount FROM public.invoice i "
            "JOIN public.customer c ON c.customer_id=i.customer_id "
            f"WHERE c.country='{case['country']}' AND i.invoice_date>=DATE '{case['year']}-01-01' "
            f"AND i.invoice_date<DATE '{case['year']+1}-01-01'")


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--reference-only", action="store_true", help="Read-only reference queries; no HTTP/model/prediction")
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / "eval/artifacts/d4") or out.exists():
        raise ValueError("Use a fresh D4 evidence directory")
    source = ROOT / "eval/datasets/d4/cross_source_dev.jsonl"
    cases = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(cases) != 6 or any(case["split"] != "dev" for case in cases):
        raise ValueError("Only the six new DEV cases may run")
    if args.only:
        cases = [case for case in cases if case["id"] in args.only]
    settings = get_settings()
    catalog = load_catalog(settings.catalog_path)
    out.mkdir(parents=True)
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, *sys.argv],
        "source": source.relative_to(ROOT).as_posix(), "source_sha256": sha256(source.read_bytes()).hexdigest(),
        "settings_public": settings.public(), "count": len(cases), "matched": 0,
        "reference_review_status": "pending_human_review", "held_predictions": 0, "cases": []}
    if args.reference_only:
        report.update(status="REFERENCE_SQL_CHECKS_ONLY", matched=None, model_calls=0,
                      system_predictions=0, measurement="Read-only label preparation, not fusion execution or EX")
        for case in cases:
            query = gold_sql(case)
            validated = validate_sql(query, catalog)
            result = execute_sql(validated.sql, settings.db_url, settings.statement_timeout_ms)
            write(out / (case["id"] + "-reference.json"), {"id": case["id"], "split": "dev",
                "gold_sql": query, "result": {"columns": result.columns, "rows": result.rows},
                "reference_review_status": "pending_human_review", "model_calls": 0, "system_predictions": 0})
            report["cases"].append({"id": case["id"], "row_count": result.row_count,
                                    "reference_file": case["id"] + "-reference.json"})
            print(json.dumps(report["cases"][-1], ensure_ascii=False), flush=True)
        write(out / "report.json", report)
        return 0
    with httpx.Client(timeout=300, trust_env=False) as client:
        health = client.get(args.api + "/health").raise_for_status().json()
        write(out / "health-before.json", health)
        if not health.get("database_ready"):
            report["status"] = "BLOCKED_DATABASE_NOT_READY"
            write(out / "report.json", report)
            return 2
        for case in cases:
            session = "d4-fusion-" + uuid4().hex
            query = gold_sql(case)
            validated = validate_sql(query, catalog)
            expected = execute_sql(validated.sql, settings.db_url, settings.statement_timeout_ms)
            request = {"session_id": session, "message": case["question"], "scope": case["scope"]}
            turns = []
            response = client.post(args.api + "/api/chat", json=request).raise_for_status().json()
            turns.append({"request": request, "response": response})
            initial_ok = response["status"] == case.get("expected_initial_status", case["expected_status"])
            if case.get("followup") and response["status"] == "NEEDS_CLARIFICATION":
                card = response["clarification"]
                request = {**request, "message": case["followup"], "clarification_id": card["clarification_id"],
                           "intent_version": card["intent_version"]}
                response = client.post(args.api + "/api/chat", json=request).raise_for_status().json()
                turns.append({"request": request, "response": response})
            options = {"expected_columns": expected.columns,
                       "actual_columns": response.get("metadata", {}).get("result_columns"),
                       "numeric_columns": [name for name in expected.columns if name != "artist_name"],
                       "monetary_columns": [name for name in expected.columns if name in {"sales_amount", "average_invoice_amount"}],
                       "ordered": True}
            comparison = compare_plan_results(expected.rows, response.get("table") or [],
                actual_sql=response.get("sql"), catalog=catalog, **options).as_dict()
            fusion = response.get("metadata", {}).get("fusion", {})
            names = [step["name"] for step in response.get("steps", [])]
            checks = {"initial_status": initial_ok, "final_status": response["status"] == case["expected_status"],
                      "database_result": comparison["matched"], "plan_kind": fusion.get("kind") == case["expected_plan"],
                      "actual_steps": all(name in names for name in case["expected_steps"])}
            if case["expected_status"] == "EMPTY_RESULT":
                checks.update(no_wrong_document=not response.get("evidences"),
                              document_insufficient=fusion.get("document_status") == "insufficient")
            else:
                checks["actual_document_citation"] = bool(response.get("evidences"))
            if case["expected_plan"] == "doc_to_sql":
                checks.update(definition_used=bool(fusion.get("definition_used_in_generation")),
                              definition_guard=fusion.get("definition_sql_guard") == "passed_before_readonly_execution")
            result = {"case": case, "gold_sql": query, "gold_result": {"columns": expected.columns, "rows": expected.rows},
                      "turns": turns, "comparison": comparison, "checks": checks, "matched": all(checks.values()),
                      "answer_semantics": "pending_human_review; automatic checks verify result and source flow, not every document statement"}
            write(out / (case["id"] + ".json"), result)
            report["matched"] += int(result["matched"])
            report["cases"].append({"id": case["id"], "matched": result["matched"], "checks": checks,
                                    "actual_status": response["status"], "response_file": case["id"] + ".json"})
            print(json.dumps(report["cases"][-1], ensure_ascii=False), flush=True)
            write(out / "report.json", report)
    report["status"] = "COMPLETED"
    write(out / "report.json", report)
    return 0 if report["matched"] == report["count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
