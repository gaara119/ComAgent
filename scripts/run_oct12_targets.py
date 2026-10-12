"""Actual loopback DEV defect checks, separate from historical official scores."""
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
from eval.metrics import compare_plan_results, compare_results
from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql


def compare(sql, result, response, catalog, ordered=False):
    if response.get("status") not in {"SUCCEEDED", "EMPTY_RESULT"} or response.get("table") is None:
        return {"matched": False, "reason": response.get("status")}
    numeric = [i for i, name in enumerate(result.columns) if not any(key in name for key in ("name", "country", "title"))]
    options = dict(ordered=ordered, expected_columns=result.columns,
                   actual_columns=response.get("metadata", {}).get("result_columns"), numeric_columns=numeric,
                   round_numeric_columns=[i for i in numeric if any(word in result.columns[i] for word in ("revenue", "amount", "share", "growth", "ratio"))])
    return {**compare_plan_results(result.rows, response["table"], actual_sql=response.get("sql"), catalog=catalog, **options).as_dict(),
            "legacy": compare_results(result.rows, response["table"], **options).as_dict()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--only", nargs="+", help="Explicit DEV IDs for a separately recorded retry; original run remains intact")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "eval/artifacts/oct12") or output.exists():
        raise SystemExit("Use a fresh Oct12 evidence directory")
    output.mkdir(parents=True)
    settings = get_settings()
    catalog = load_catalog(settings.catalog_path)
    source = ROOT / "eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if any(item.get("split") != "dev" for item in rows):
        raise SystemExit("Synthetic DEV only")
    selected = {"sp01-05", "sp01-07", "sp01-10", "sp01-22", "sp03-06", "sp03-14", "sp03-19", "sp03-22"}
    cases = [{"id": item["id"], "question": item["input"], "gold_sql": item["gold_sql"],
              "ordered": item["id"] in {"sp03-14", "sp03-19"}} for item in rows if item["id"] in selected]
    cases += [
        {"id": "oct12-default-who", "question": "谁买得最多？给我前三位。", "ordered": True,
         "gold_sql": "SELECT customer_id,SUM(total) AS amount FROM invoice GROUP BY customer_id ORDER BY amount DESC,customer_id ASC LIMIT 3"},
        {"id": "oct12-default-repeat", "question": "复购客户有多少？", "gold_sql": "SELECT COUNT(*) AS repeat_customer_count FROM (SELECT customer_id FROM invoice GROUP BY customer_id HAVING COUNT(*)>=2) c"},
        {"id": "oct12-default-track", "question": "最热门的3首曲目是什么？", "ordered": True,
         "gold_sql": "SELECT track_id,SUM(quantity) AS purchased_quantity FROM invoice_line GROUP BY track_id ORDER BY purchased_quantity DESC,track_id ASC LIMIT 3"},
        {"id": "oct12-default-region", "question": "2024年巴西销售额是多少？",
         "gold_sql": "SELECT SUM(total) AS amount FROM invoice WHERE billing_country='Brazil' AND invoice_date>='2024-01-01' AND invoice_date<'2025-01-01'"},
        {"id": "oct12-explicit-region", "question": "2024年按客户所在地统计巴西销售额是多少？",
         "gold_sql": "SELECT SUM(i.total) AS amount FROM invoice i JOIN customer c ON i.customer_id=c.customer_id WHERE c.country='Brazil' AND i.invoice_date>='2024-01-01' AND i.invoice_date<'2025-01-01'"},
        {"id": "oct12-default-ratio", "question": "2024年法国销售额占比是多少？",
         "gold_sql": "SELECT SUM(CASE WHEN billing_country='France' THEN total ELSE 0 END)/NULLIF(SUM(total),0) AS share FROM invoice WHERE invoice_date>='2024-01-01' AND invoice_date<'2025-01-01'"},
        {"id": "oct12-alias-us", "question": "老美有多少客户？", "gold_sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country='USA'"},
        {"id": "oct12-context-year", "question": "2023年谁买得最多？给我前三位。", "followup": "改成前5位。", "ordered": True,
         "gold_sql": "SELECT customer_id,SUM(total) AS amount FROM invoice WHERE invoice_date>='2023-01-01' AND invoice_date<'2024-01-01' GROUP BY customer_id ORDER BY amount DESC,customer_id ASC LIMIT 5"},
        {"id": "oct12-context-numerator", "question": "2023年法国居住客户的销售额占比是多少？", "followup": "分子换成德国居住客户的销售额。",
         "gold_sql": "SELECT SUM(CASE WHEN c.country='Germany' THEN i.total ELSE 0 END)/NULLIF(SUM(i.total),0) AS share FROM invoice i JOIN customer c ON i.customer_id=c.customer_id WHERE i.invoice_date>='2023-01-01' AND i.invoice_date<'2024-01-01'"},
    ]
    if args.only:
        requested = set(args.only)
        if requested - {item["id"] for item in cases}:
            raise SystemExit("Unknown DEV target ID")
        cases = [item for item in cases if item["id"] in requested]
    records = []
    with httpx.Client(timeout=240, trust_env=False) as client:
        for case in cases:
            session = "oct12-target-" + uuid4().hex
            turns = []
            payload = {"session_id": session, "message": case["question"], "scope": {"route": "sql", "db_id": "chinook", "doc_ids": []}}
            result = execute_sql(case["gold_sql"], settings.db_url, settings.statement_timeout_ms, max_rows=200)
            response = None
            try:
                response = client.post("http://127.0.0.1:8000/api/chat", json=payload).raise_for_status().json()
                turns.append({"request": payload, "response": response})
                if case["id"] == "sp03-06" and response.get("status") == "NEEDS_CLARIFICATION":
                    card = response["clarification"]
                    payload = {**payload, "message": "2024年，和2023年比。", "clarification_id": card["clarification_id"],
                               "intent_version": response["intent"]["intent_version"]}
                    response = client.post("http://127.0.0.1:8000/api/chat", json=payload).raise_for_status().json()
                    turns.append({"request": payload, "response": response})
                if case.get("followup") and response.get("status") in {"SUCCEEDED", "EMPTY_RESULT"}:
                    payload = {"session_id": session, "message": case["followup"], "scope": payload["scope"]}
                    response = client.post("http://127.0.0.1:8000/api/chat", json=payload).raise_for_status().json()
                    turns.append({"request": payload, "response": response})
                comparison = compare(case["gold_sql"], result, response, catalog, case.get("ordered", False))
                if case["id"] == "sp03-06":
                    # Preserve the original full reference mismatch. Separately
                    # inspect what the question actually asks; this is a label
                    # review diagnostic, not an altered gold or formal score.
                    names = response.get("metadata", {}).get("result_columns") or []
                    if names == ["yoy_growth_rate"] and response.get("table") is not None:
                        requested = compare_plan_results([[row[2]] for row in result.rows], response["table"],
                            expected_columns=["yoy_growth_rate"], actual_columns=names, numeric_columns=[0],
                            actual_sql=response.get("sql"), catalog=catalog)
                        comparison["requested_growth_value_check"] = requested.as_dict()
                        comparison["reference_projection_review"] = "原gold附当前额/基期额，题面只问同比；保留原EX，待人工决定投影要求"
                    comparison["initial_period_issue_count"] = len(turns[0]["response"].get("clarification", {}).get("issues", []))
                if case["id"] == "sp03-14":
                    comparison["time_word_not_entity"] = all(item.get("original_text") != "每年" for item in response.get("metadata", {}).get("nlu", {}).get("mentions", []))
                if case["id"] == "oct12-alias-us":
                    comparison["direct_alias_L0"] = response.get("metadata", {}).get("clarify", {}).get("level") == "L0"
            except Exception as exc:
                comparison = {"matched": False, "reason": sanitize_error(exc, settings)}
            record = {**case, "split": "dev", "gold_review": "pending_human_review", "turns": turns,
                      "readonly_gold": {"columns": result.columns, "rows": result.rows}, "comparison": comparison}
            records.append(record)
            (output / (case["id"] + ".json")).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            print(case["id"], response.get("status") if response else "NO_RESPONSE", comparison, flush=True)
    report = {"measurement": "actual DEV targeted exploratory checks; not a held/formal score", "count": len(records),
              "matched": sum(item["comparison"].get("matched") is True for item in records),
              "holdout_prediction_count": 0, "human_review_status": "pending_human_review",
              "command": [sys.executable, "-B", *sys.argv], "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "source": source.relative_to(ROOT).as_posix(), "source_sha256": sha256(source.read_bytes()).hexdigest(),
              "explicit_retry_ids": args.only or [],
              "records": [{"id": item["id"], "comparison": item["comparison"], "evidence": item["id"] + ".json"} for item in records]}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
