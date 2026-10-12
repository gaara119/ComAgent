"""Verify the two latest DEV defects under the separately restarted source."""
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_value_bindings
from eval.metrics import compare_plan_results, compare_results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/"eval/artifacts/oct12") or out.exists():
        raise ValueError("Use a fresh Oct12 evidence folder")
    out.mkdir(parents=True)
    settings=get_settings();catalog=load_catalog(settings.catalog_path)
    source=ROOT/"eval/artifacts/d2-final/review/sql-dev-v1.jsonl"
    expected_digest="7b4c18f203ce0d88f38837f0c788cbcff142b559dc70d3f281990a2d47175f35"
    if sha256(source.read_bytes()).hexdigest()!=expected_digest:
        raise ValueError("Historical DEV view changed")
    rows=[json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    if any(item["split"]!="dev" for item in rows):
        raise ValueError("DEV only")
    old=next(item for item in rows if item["id"]=="sql-19")
    cases=[{"id":"sql-19","question":old["question"],"gold_sql":old["gold_sql"],"ordered":True},
           {"id":"oct12-midnight-invoice-ratio","question":"2024年账单国家为Brazil的发票金额占同年所有发票金额的比例是多少？",
            "gold_sql":"SELECT SUM(CASE WHEN billing_country='Brazil' THEN total ELSE 0 END)/NULLIF(SUM(total),0) AS share FROM invoice WHERE invoice_date>='2024-01-01' AND invoice_date<'2025-01-01'","ordered":False}]
    failed=json.loads((ROOT/"eval/artifacts/oct12/ui-live/run-003/invoice-ratio-raw.json").read_text(encoding="utf-8"))
    response=failed.get("response",failed)
    actual=next(step["output_summary"]["sql"] for step in response["steps"] if step["name"]=="sql_gen" and step["status"]=="ok")
    validate_value_bindings(actual,catalog,[{"column":"invoice.billing_country","operator":"=","value":"Brazil"}],
        ratio_context={"task_type":"ratio","metric":"invoice_revenue","denominator":"同期全部发票金额","time_scope":{"current":{"start":"2024-01-01","end":"2025-01-01"}}})
    actual_result=execute_sql(actual,settings.db_url,settings.statement_timeout_ms)
    gold=execute_sql(cases[1]["gold_sql"],settings.db_url,settings.statement_timeout_ms)
    sql_proof={"measurement":"Actual originally rejected SQL validated and read-only executed; not a new model prediction",
               "old_evidence":"eval/artifacts/oct12/ui-live/run-003/invoice-ratio-raw.json","sql":actual,
               "columns":actual_result.columns,"rows":actual_result.rows,"expected_rows":gold.rows,
               "comparison":compare_results(gold.rows,actual_result.rows).as_dict()}
    (out/"original-midnight-sql-readonly.json").write_text(json.dumps(sql_proof,ensure_ascii=False,indent=2),encoding="utf-8")
    records=[]
    with httpx.Client(timeout=240,trust_env=False) as client:
        for case in cases:
            expected=execute_sql(case["gold_sql"],settings.db_url,settings.statement_timeout_ms)
            request={"session_id":"oct12-repair-"+uuid4().hex,"message":case["question"],"scope":{"route":"sql","db_id":"chinook","doc_ids":[]}}
            actual_response=client.post("http://127.0.0.1:8000/api/chat",json=request).raise_for_status().json()
            if actual_response["status"] in {"SUCCEEDED","EMPTY_RESULT"} and actual_response.get("table") is not None:
                numeric=[i for i,name in enumerate(expected.columns) if not any(word in name for word in ("name","country","title"))]
                options={"ordered":case["ordered"],"expected_columns":expected.columns,"actual_columns":actual_response.get("metadata",{}).get("result_columns"),"numeric_columns":numeric,
                         "round_numeric_columns":[i for i in numeric if any(word in expected.columns[i] for word in ("share","ratio","amount","revenue","growth"))]}
                comparison=compare_plan_results(expected.rows,actual_response["table"],actual_sql=actual_response.get("sql"),catalog=catalog,**options).as_dict()
                legacy=compare_results(expected.rows,actual_response["table"],**options).as_dict()
            else:
                comparison={"matched":False,"reason":actual_response["status"]};legacy=comparison
            record={**case,"split":"dev","request":request,"response":actual_response,"readonly_gold":{"columns":expected.columns,"rows":expected.rows},"comparison":comparison,"legacy_comparison":legacy}
            (out/(case["id"]+".json")).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
            records.append(record)
            print(case["id"],actual_response["status"],comparison,flush=True)
    report={"created_at_utc":datetime.now(timezone.utc).isoformat(),"command":[sys.executable,"-B",*sys.argv],"measurement":"Actual scoped DEV regression after two technical repairs; not a recomputed 77-case score", "count":len(records),"matched":sum(record["comparison"].get("matched") is True for record in records),"original_failed_sql_readonly_matched":sql_proof["comparison"]["matched"],"unchanged_dev_sha256":expected_digest,"held_predictions":0,"human_gold_changes":0}
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return 0 if report["matched"]==report["count"] and report["original_failed_sql_readonly_matched"] else 1


if __name__=="__main__":
    raise SystemExit(main())
