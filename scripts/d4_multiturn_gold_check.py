"""Read-only DEV reference checks. No model calls or question-system requests."""
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_d4_multiturn import original_cases, new_cases
from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql
from qa_agent.sql.repair_guard import validate_chinook_fk_joins


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    output=(ROOT/args.output).resolve()
    if not output.is_relative_to(ROOT/'eval/artifacts/d4') or output.exists():raise SystemExit('Fresh D4 output required')
    output.mkdir(parents=True)
    settings=get_settings();catalog=load_catalog(settings.catalog_path)
    references=[]
    for case in original_cases():
        references.append((case['id']+':final',case['gold_sql']))
        references.extend((case['id']+':post-'+str(index+1),turn['gold_sql']) for index,turn in enumerate(case['post_completion_turns']))
    for case in new_cases():references.extend((case['id']+':turn-'+str(index+1),turn['gold_sql']) for index,turn in enumerate(case['turns']))
    rows=[]
    for identifier,sql in references:
        began=perf_counter()
        try:
            checked=validate_sql(sql,catalog,max_rows=200);validate_chinook_fk_joins(checked.sql,catalog)
            result=execute_sql(checked.sql,settings.db_url,statement_timeout_ms=settings.statement_timeout_ms,max_rows=200)
            record={'id':identifier,'status':'EXECUTED_READONLY','sql':sql,'validated_sql':checked.sql,'sql_sha256':sha256(sql.encode()).hexdigest(),
                    'columns':result.columns,'rows':result.rows,'table':result.table,'row_count':result.row_count,'truncated':result.truncated,'elapsed_ms':(perf_counter()-began)*1000}
        except Exception as exc:
            record={'id':identifier,'status':'FAILED','sql':sql,'error':sanitize_error(exc,settings)}
        rows.append(record)
    report={'state':'COMPLETED','created_at_utc':datetime.now(timezone.utc).isoformat(),'reference_count':len(rows),'executed_readonly':sum(row['status']=='EXECUTED_READONLY' for row in rows),
            'statement_timeout_ms':settings.statement_timeout_ms,'model_calls':0,'system_predictions':0,'held_queries':0,'records':rows}
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({key:value for key,value in report.items() if key!='records'},ensure_ascii=False))
    if report['executed_readonly']!=len(rows):raise SystemExit(1)


if __name__=='__main__':main()
