"""Real API regression for a trusted year button, including another missing slot."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4

import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa_agent.config import get_settings,sanitize_error


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    args=parser.parse_args()
    destination=args.output if args.output.is_absolute() else ROOT/args.output
    if destination.exists():raise SystemExit('Choose a new evidence directory.')
    settings=get_settings()
    with httpx.Client(timeout=240,trust_env=False) as client:
        health=client.get(args.base_url+'/health').json()
        if health.get('stage')!='D3':raise SystemExit('D3 API is not active; no prediction generated.')
        destination.mkdir(parents=True)
        (destination/'run.json').write_text(json.dumps({'command':[sys.executable,'-B',*sys.argv],
            'created_at_utc':datetime.now(timezone.utc).isoformat(),'health':health,
            'source':'new explicit development interaction counterexamples; not held-out cases',
            'state_sha256':sha256((ROOT/'qa_agent/clarify/state.py').read_bytes()).hexdigest(),
            'protected_holdout_predictions':0,'human_review_status':'pending_human_review'},ensure_ascii=False,indent=2),encoding='utf-8')
        checks=[]
        count=0
        def ask(name,request):
            nonlocal count
            started=perf_counter();error=None
            try:
                response=client.post(args.base_url+'/api/chat',json=request)
                response.raise_for_status();value=response.json()
            except Exception as exc:value={};error=sanitize_error(exc,settings)
            record={'request':request,'response':value,'error':error,
                    'latency_ms':round((perf_counter()-started)*1000)}
            (destination/(name+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            count+=1
            print(json.dumps({'case':name,'status':value.get('status'),'error':error},ensure_ascii=False),flush=True)
            return value
        cases=[('valid-year','账单国家为USA的发票销售额最近一年同比增长多少？','SUCCEEDED'),
               ('missing-metric','账单国家为USA的某个指标最近一年同比增长多少？我还没决定统计哪个指标。','NEEDS_CLARIFICATION')]
        for name,question,status in cases:
            request={'session_id':'d3-button-'+str(uuid4()),'message':question,
                     'scope':{'route':'sql','db_id':'chinook','doc_ids':[]}}
            before=ask(name+'-before',request)
            issues=(before.get('clarification') or {}).get('issues') or []
            checks.append({'name':name+'-real-period-ambiguity','passed':before.get('status')=='NEEDS_CLARIFICATION' and
                           any(issue.get('id')=='ambiguous:time_scope' for issue in issues),'evidence':name+'-before.json'})
            card=before.get('clarification') or {}
            if not card or not any(option.get('id')=='year:2024' for option in card.get('options') or []):
                checks.append({'name':name+'-trusted-choice-result','passed':False,'reason':'Actual card lacks year:2024; no fabricated choice sent.','evidence':name+'-before.json'})
                continue
            after=ask(name+'-after',{**request,'message':next(option['label'] for option in card['options'] if option['id']=='year:2024'),
                        'choice_id':'year:2024','clarification_id':card['clarification_id'],'intent_version':card['intent_version']})
            intent=after.get('intent') or {};period=intent.get('time_scope') or {}
            remaining=(after.get('clarification') or {}).get('issues') or []
            passed=(after.get('status')==status and (period.get('current') or {}).get('start')=='2024-01-01' and
                    (period.get('base') or {}).get('start')=='2023-01-01' and
                    intent.get('intent_version',0)>card['intent_version'] and
                    not any(issue.get('id')=='ambiguous:time_scope' for issue in remaining))
            if status=='NEEDS_CLARIFICATION':
                passed=passed and any(issue.get('id')=='missing:metric' for issue in remaining) and not after.get('sql')
            else:passed=passed and bool(after.get('sql'))
            checks.append({'name':name+'-trusted-choice-result','passed':bool(passed),'evidence':name+'-after.json',
                           'reason':'Valid user calendar choice resolves only period ambiguity; another missing metric still asks before SQL.'})
        report={'checks':checks,'passed':sum(item['passed'] for item in checks),'total':len(checks),
                'actual_api_requests':count,'protected_holdout_predictions':0,'human_review_status':'pending_human_review',
                'measurement':'actual affected trusted-year-button API regression; not all-question interaction success rate'}
        (destination/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({key:report[key] for key in ('passed','total','actual_api_requests')},ensure_ascii=False))
        return int(not all(item['passed'] for item in checks))


if __name__=='__main__':raise SystemExit(main())
