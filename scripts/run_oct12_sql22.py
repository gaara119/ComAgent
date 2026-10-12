"""Run only the unchanged accepted DEV sql-22 after the date-boundary fix."""
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
from eval.metrics import compare_plan_results,compare_results

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",required=True,type=Path);args=parser.parse_args()
    out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/"eval/artifacts/oct12") or out.exists():
        raise ValueError("Use a fresh Oct12 evidence folder")
    source=ROOT/"eval/artifacts/d2-final/review/sql-dev-v1.jsonl"
    if sha256(source.read_bytes()).hexdigest()!="7b4c18f203ce0d88f38837f0c788cbcff142b559dc70d3f281990a2d47175f35":
        raise ValueError("Historical DEV source changed")
    cases=[json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    if any(item["split"]!="dev" for item in cases):
        raise ValueError("DEV only")
    case=next(item for item in cases if item["id"]=="sql-22")
    settings=get_settings();catalog=load_catalog(settings.catalog_path)
    expected=execute_sql(case["gold_sql"],settings.db_url,settings.statement_timeout_ms)
    request={"session_id":"oct12-sql22-"+uuid4().hex,"message":case["question"],"scope":{"route":"sql","db_id":"chinook","doc_ids":[]}}
    with httpx.Client(timeout=240,trust_env=False) as client:
        response=client.post("http://127.0.0.1:8000/api/chat",json=request).raise_for_status().json()
    options={"ordered":True,"expected_columns":expected.columns,"actual_columns":response.get("metadata",{}).get("result_columns"),"numeric_columns":["employee_id"],"temporal_columns":["hire_date"]}
    comparison=(compare_plan_results(expected.rows,response["table"],actual_sql=response.get("sql"),catalog=catalog,**options).as_dict() if response.get("table") is not None else {"matched":False,"reason":response["status"]})
    legacy=compare_results(expected.rows,response["table"],**options).as_dict() if response.get("table") is not None else comparison
    intent_scope=(response.get("intent") or {}).get("time_scope") or {}
    current=intent_scope.get("current") or {}
    scope_ok=current.get("end")=="2004-01-01" and not current.get("start") and current.get("grain")=="before"
    record={"id":"sql-22","split":"dev","measurement":"Actual scoped regression; does not overwrite phase3 34/35 or claim new full35/77 run",
            "created_at_utc":datetime.now(timezone.utc).isoformat(),"command":[sys.executable,"-B",*sys.argv],"request":request,"response":response,
            "gold_sql":case["gold_sql"],"readonly_gold":{"columns":expected.columns,"rows":expected.rows},"comparison":comparison,"legacy_comparison":legacy,
            "literal_strict_before_intent":scope_ok,"gold_changed":False,"held_predictions":0}
    out.mkdir(parents=True)
    (out/"sql-22.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"report.json").write_text(json.dumps({"count":1,"matched":int(comparison["matched"]),"literal_strict_before_intent":scope_ok,"actual_status":response["status"],"response_file":"sql-22.json","held_predictions":0,"human_gold_changes":0},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"sql22_comparison":comparison,"literal_strict_before_intent":scope_ok,"actual_status":response["status"]},ensure_ascii=False))
    return 0 if comparison["matched"] and scope_ok else 1

if __name__=="__main__":
    raise SystemExit(main())
