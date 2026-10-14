"""Independent post-run completeness, attempts and known-usage inspection."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
result = {"at_utc": datetime.now(timezone.utc).isoformat(), "model_calls_in_this_check": 0,
          "database_connections_in_this_check": 0, "holdout_predictions_in_this_check": 0,
          "runs": {}, "known_usage_warning": "Token totals sum provider-reported usage. A timeout without usage is UNKNOWN, not a proven zero or complete invoice."}
for run_name, expected in (("aw-ablation-live-001", 42), ("sql-scale-live-001", 180)):
    directory = ROOT / "eval/artifacts/d4" / run_name
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (directory / "responses.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == expected and all(row["matched"] for row in rows)
    assert all(row["legacy_matched"] for row in rows)
    assert all(row.get("split") == "dev" for row in rows)
    assert report["runtime_and_sources_unchanged"] and report["holdout_predictions"] == 0
    group_key = "arm" if run_name.startswith("aw") else "scale"
    groups = Counter(row[group_key] for row in rows)
    if group_key == "arm":
        assert groups == {"full": 21, "subgraph": 21}
        assert all(count == 2 for count in Counter(row["id"] for row in rows).values())
    else:
        assert groups == {"original": 60, "10000": 60, "100000": 60}
        assert all(count == 3 for count in Counter((row["id"], row["scale"]) for row in rows).values())
        assert len({row["id"] for row in rows}) == 20
        assert all({row["repetition"] for row in rows if row["id"] == ident and row["scale"] == scale} == {1, 2, 3}
                   for ident, scale in {(row["id"], row["scale"]) for row in rows})
    llm_steps = [(row, step) for row in rows for step in row["response"]["steps"] if step["name"] == "llm"]
    missing = [{"id": row["id"], "group": row[group_key], "status": step["status"],
                "latency_ms": step["latency_ms"], "error": step.get("output_summary", {}).get("error"),
                "provider_capture": step.get("output_summary", {}).get("provider_capture")}
               for row, step in llm_steps if not step.get("output_summary", {}).get("usage")]
    usage = Counter()
    for _, step in llm_steps:
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            usage[key] += step.get("output_summary", {}).get("usage", {}).get(key, 0)
    from_reports = Counter()
    for group in report["groups"].values():
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            from_reports[key] += group["usage_total"].get(key, 0)
    assert usage == from_reports
    result["runs"][run_name] = {
        "response_count": len(rows), "unique_questions": len({row["id"] for row in rows}),
        "group_counts": dict(groups), "main_ex_correct": sum(row["matched"] for row in rows),
        "legacy_ex_correct": sum(row["legacy_matched"] for row in rows),
        "source_hashes_unchanged": True, "holdout_predictions": 0,
        "model_attempts_from_raw_steps": len(llm_steps),
        "model_error_attempts": sum(step["status"] == "error" for _, step in llm_steps),
        "provider_reported_usage": dict(usage), "missing_provider_usage_attempts": missing,
        "zero_model_call_predictions": sum(not any(step["name"] == "llm" for step in row["response"]["steps"]) for row in rows),
        "source_escape_failures": sum(row.get("failure_category") == "stress_query_escaped_physical_schema" for row in rows),
        "empty_result_records": [{"id": row["id"], "group": row[group_key], "repetition": row.get("repetition")}
                                 for row in rows if row["response"]["status"] == "EMPTY_RESULT"]}
result["status"] = "ACTUALLY_CHECKED_BOTH_COMPLETE_RUNS"
target = ROOT / "eval/artifacts/d4/a-readiness-001/completed-run-check.json"
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
