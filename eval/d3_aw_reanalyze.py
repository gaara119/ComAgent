"""Observe saved live responses; never rerun or alter predictions."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("eval/reports/d3-aw-live-dev-run1/responses.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("eval/reports/d3-aw-live-dev-run1/schema-observation.json"))
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Do not overwrite existing observation evidence")
    data = args.input.read_bytes()
    records = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
    if any(record.get("split") != "dev" for record in records):
        raise ValueError("Observer does not process protected holdout predictions")
    observations = []
    for record in records:
        response = record.get("response") or {}
        metadata = response.get("metadata") or {}
        bundle = metadata.get("schema_linker") or metadata.get("schema_bundle") or metadata.get("schema_linking") or {}
        selected, gold = set(bundle.get("selected_tables", [])), set(record.get("gold_tables", []))
        validate_steps = [step for step in response.get("steps", []) if step.get("name") == "sql_validate"]
        executor_steps = [step for step in response.get("steps", []) if step.get("name") == "sql_exec"]
        actual_sources = (validate_steps[-1].get("output_summary", {}).get("tables") or []) if validate_steps else []
        observations.append({"id":record["id"], "status":response.get("status"), "ex_matched":record.get("matched"),
            "db_id":metadata.get("db_id"),"sql_execution_db_ids":[step.get("input_summary", {}).get("db_id") for step in executor_steps],
            "selected_tables":sorted(selected),"candidate_count":len(selected),"gold_tables":sorted(gold),
            "table_recall":len(selected&gold)/len(gold) if gold else None,
            "table_precision":len(selected&gold)/len(selected) if selected else 0,
            "all_gold_recalled":bool(gold and gold<=selected),"missing_gold_tables":sorted(gold-selected),
            "actual_validated_sql_tables":actual_sources,
            "validated_sources_stay_in_aw_schemas":all(table.split(".",1)[0] in {"humanresources","person","production","purchasing","sales"} for table in actual_sources),
            "actual_user_facets":bundle.get("query_facets", []),
            "schema_latency_ms":sum(step.get("latency_ms", 0) for step in response.get("steps",[]) if step.get("name")=="schema_link")})
    count = len(observations)
    report = {"created_at":datetime.now(timezone.utc).isoformat(),"mode":"saved-response observation only; no model calls",
              "raw_response_file":args.input.as_posix(),"raw_response_sha256":sha256(data).hexdigest(),
              "input_responses_unchanged":sha256(args.input.read_bytes()).hexdigest()==sha256(data).hexdigest(),
              "development_count":count,"holdout_predictions_observed":0,
              "all_gold_recalled_cases":sum(r["all_gold_recalled"] for r in observations),
              "mean_table_recall":sum(r["table_recall"] or 0 for r in observations)/count,
              "mean_table_precision":sum(r["table_precision"] for r in observations)/count,
              "average_candidate_table_count":sum(r["candidate_count"] for r in observations)/count,
              "average_actual_schema_latency_ms":sum(r["schema_latency_ms"] for r in observations)/count,
              "validated_aw_scope_cases":sum(r["validated_sources_stay_in_aw_schemas"] for r in observations),
              "actual_sql_execution_adventureworks_cases":sum(r["sql_execution_db_ids"] and all(d=="adventureworks" for d in r["sql_execution_db_ids"]) for r in observations),
              "gold_human_status":"pending_human_review","rows":observations}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
