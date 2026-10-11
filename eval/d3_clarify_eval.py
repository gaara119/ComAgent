"""Run only frozen D3 clarification DEV through the actual API, with raw evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4

import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa_agent.config import get_settings, sanitize_error


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    args=parser.parse_args()
    destination=args.output if args.output.is_absolute() else ROOT/args.output
    destination.mkdir(parents=True,exist_ok=True)
    source=ROOT/'eval/datasets/d3/clarify/dev.jsonl'
    cases=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines() if line]
    if len(cases)!=21 or any(row['split']!='dev' for row in cases):raise SystemExit('Refuse mixed/heldout source.')
    settings=get_settings()
    code_hashes={str(path.relative_to(ROOT)).replace('\\','/'):sha256(path.read_bytes()).hexdigest()
                 for path in [ROOT/'qa_agent/pipeline.py',ROOT/'qa_agent/schemas.py',
                              ROOT/'qa_agent/config.py',ROOT/'qa_agent/llm.py',ROOT/'qa_agent/sql/generator.py',
                              ROOT/'qa_agent/sql/executor.py',ROOT/'qa_agent/sql/validator.py',ROOT/'qa_agent/sql/prompts/multi_table.txt',
                              ROOT/'qa_agent/nlu/linker.py',
                              *sorted((ROOT/'qa_agent/clarify').rglob('*.py')),
                              *sorted((ROOT/'qa_agent/clarify/prompts').glob('*.txt')),
                              ROOT/'qa_agent/clarify/clarify_rules.yaml']}
    metadata={'created_at_utc':datetime.now(timezone.utc).isoformat(),'command':[sys.executable,'-B',*sys.argv],
              'dataset':str(source.relative_to(ROOT)).replace('\\','/'),'dataset_sha256':sha256(source.read_bytes()).hexdigest(),
              'code_sha256':code_hashes,'model':settings.llm_model,'review_status':'pending_human_review',
              'measurement':'D3 new development labels: real API level/execute gate checks, not official competition score',
              'holdout_predictions':0,'request_fields':['session_id','message','scope']}
    meta=destination/'run.json'
    if meta.exists():
        old=json.loads(meta.read_text(encoding='utf-8'))
        if old['dataset_sha256']!=metadata['dataset_sha256'] or old['code_sha256']!=code_hashes:
            raise SystemExit('Code/dataset changed; use a fresh output version.')
    else:meta.write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=240,trust_env=False) as client:
        health=client.get(args.base_url.rstrip('/')+'/health').json()
        if health.get('stage')!='D3':raise SystemExit('D3 service is not active; no predictions generated.')
        for case in cases:
            target=destination/(case['id']+'.json')
            if target.exists():continue
            request={'session_id':'d3-dev-'+str(uuid4()),'message':case['question'],'scope':case['scope']}
            started=perf_counter()
            response=None
            error=None
            try:
                raw=client.post(args.base_url.rstrip('/')+'/api/chat',json=request)
                raw.raise_for_status()
                response=raw.json()
            except Exception as exc:
                error=sanitize_error(exc,settings)
            record={'id':case['id'],'request':request,'response':response,'error':error,
                    'latency_ms':round((perf_counter()-started)*1000),'created_at_utc':datetime.now(timezone.utc).isoformat()}
            target.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'id':case['id'],'status':(response or {}).get('status'),'error':error},ensure_ascii=False),flush=True)
    judgments=[]
    for case in cases:
        record=json.loads((destination/(case['id']+'.json')).read_text(encoding='utf-8'))
        response=record.get('response') or {}
        actual=(response.get('metadata') or {}).get('clarify',{}).get('level')
        status=response.get('status')
        level_correct=actual==case['expected_level']
        should_ask=case['expected_level']=='L2'
        behavior_correct=(status=='NEEDS_CLARIFICATION' and response.get('sql') is None and
                          not any(step['name']=='sql_exec' for step in response.get('steps',[]))
                          if should_ask else status in {'SUCCEEDED','EMPTY_RESULT'} and response.get('sql') is not None)
        judgments.append({'id':case['id'],'expected_level':case['expected_level'],'actual_level':actual,
                          'status':status,'level_correct':level_correct,'behavior_correct':behavior_correct,
                          'passed':level_correct and behavior_correct,'evidence':case['id']+'.json',
                          'reference_review':'pending_human_review','answer_business_correctness':'not decided by level-only metric'})
    asks=[row for row in judgments if row['expected_level']=='L2']
    nonasks=[row for row in judgments if row['expected_level']!='L2']
    total_usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0,'actual_llm_attempts':0}
    for case in cases:
        raw=json.loads((destination/(case['id']+'.json')).read_text(encoding='utf-8'))
        for step in (raw.get('response') or {}).get('steps',[]):
            if step['name']=='llm':
                total_usage['actual_llm_attempts']+=1
                usage=step.get('output_summary',{}).get('usage',{})
                for key in ('prompt_tokens','completion_tokens','total_tokens'):total_usage[key]+=usage.get(key,0)
    report={'status':'COMPLETED','dev_prediction_count':len(judgments),'holdout_prediction_count':0,
            'passed':sum(row['passed'] for row in judgments),'total':len(judgments),
            'l2_recall':sum(row['status']=='NEEDS_CLARIFICATION' for row in asks)/len(asks),
            'non_l2_false_ask_rate':sum(row['status']=='NEEDS_CLARIFICATION' for row in nonasks)/len(nonasks),
            'usage':total_usage,'judgments':judgments,'human_review_status':'pending_human_review',
            'score_label':'本轮D3开发集上的自动评测／AI预审结果；标签待人工最终核对'}
    (destination/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('dev_prediction_count','holdout_prediction_count','passed','total','l2_recall','non_l2_false_ask_rate')},ensure_ascii=False))


if __name__=='__main__':main()
