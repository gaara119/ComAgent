"""Run only development conversations, retaining every real request and response."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import httpx
from eval.metrics import compare_plan_results
from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql


def period(year):
    return {'start':f'{year}-01-01','end':f'{year+1}-01-01'}


def invoice_sql(year,country=None,metric='invoice_revenue',scope='invoice.billing_country',growth=False):
    aggregate={'invoice_revenue':'SUM','average_invoice_amount':'AVG','invoice_count':'COUNT'}[metric]
    value='i.invoice_id' if metric=='invoice_count' else 'i.total'
    joined=scope=='customer.country' and country is not None
    source='public.invoice i'+(' JOIN public.customer c ON i.customer_id=c.customer_id' if joined else '')
    field='c.country' if joined else 'i.billing_country'
    selected=f'{field}=\'{country}\'' if country else None
    if growth:
        current=f"{aggregate}(CASE WHEN i.invoice_date>=DATE '{year}-01-01' AND i.invoice_date<DATE '{year+1}-01-01' THEN {value} END)"
        base=f"{aggregate}(CASE WHEN i.invoice_date>=DATE '{year-1}-01-01' AND i.invoice_date<DATE '{year}-01-01' THEN {value} END)"
        return f'SELECT ({current}-{base})/NULLIF({base},0) AS value FROM {source}'+(' WHERE '+selected if selected else '')
    conditions=[f"i.invoice_date>=DATE '{year}-01-01'",f"i.invoice_date<DATE '{year+1}-01-01'"]+([selected] if selected else [])
    return f'SELECT {aggregate}({value}) AS value FROM {source} WHERE '+ ' AND '.join(conditions)


def detail_sql(year,genre=None,artist=None,country=None,metric='detail_revenue',top=None):
    source='public.invoice_line il JOIN public.invoice i ON il.invoice_id=i.invoice_id JOIN public.track t ON t.track_id=il.track_id'
    where=[f"i.invoice_date>=DATE '{year}-01-01'",f"i.invoice_date<DATE '{year+1}-01-01'"]
    if genre:
        source+=' JOIN public.genre g ON t.genre_id=g.genre_id';where.append(f"g.name='{genre}'")
    if artist:
        source+=' JOIN public.album a ON t.album_id=a.album_id JOIN public.artist ar ON a.artist_id=ar.artist_id';where.append(f"ar.name='{artist}'")
    if country:where.append(f"i.billing_country='{country}'")
    aggregate='SUM(il.quantity)' if metric=='purchased_quantity' else 'SUM(il.unit_price*il.quantity)'
    projection='t.track_id,'+aggregate+' AS value' if top else aggregate+' AS value'
    return 'SELECT '+projection+' FROM '+source+' WHERE '+' AND '.join(where)+(f' GROUP BY t.track_id ORDER BY value DESC,t.track_id ASC LIMIT {top}' if top else '')


def ratio_sql(num,den=None):
    divisor=f"SUM(CASE WHEN i.billing_country='{den}' THEN i.total END)" if den else 'SUM(i.total)'
    return f"SELECT SUM(CASE WHEN c.country='{num}' THEN i.total END)/NULLIF({divisor},0) AS share FROM public.invoice i JOIN public.customer c ON i.customer_id=c.customer_id WHERE i.invoice_date>=DATE '2023-01-01' AND i.invoice_date<DATE '2024-01-01'"


def turn(message,year=None,metric=None,filters=None,sql=None,**extra):
    expected={**extra}
    if year is not None:expected['current']=period(year)
    if metric is not None:expected['metric']=metric
    if filters is not None:expected['filters']=filters
    return {'message':message,'expected':expected,'gold_sql':sql,'ordered':'ORDER BY' in (sql or '')}


def new_cases():
    c=lambda field,value:{'column':field,'operator':'=','value':value}
    bill=lambda country:c('invoice.billing_country',country)
    residence=lambda country:c('customer.country',country)
    genre=lambda name:c('genre.name',name)
    artist=lambda name:c('artist.name',name)
    return [
      {'id':'d4-dialog-01','split':'dev','purpose':'国家/指标/期间/地区字段/删除','turns':[
        turn('2023年账单国为美国的发票销售额是多少？',2023,'invoice_revenue',[bill('USA')],invoice_sql(2023,'USA')),
        turn('换成加拿大。',2023,'invoice_revenue',[bill('Canada')],invoice_sql(2023,'Canada')),
        turn('改看发票张数。',2023,'invoice_count',[bill('Canada')],invoice_sql(2023,'Canada','invoice_count')),
        turn('期间改成2024年。',2024,'invoice_count',[bill('Canada')],invoice_sql(2024,'Canada','invoice_count')),
        turn('改按客户所在地统计。',2024,'invoice_count',[residence('Canada')],invoice_sql(2024,'Canada','invoice_count','customer.country')),
        turn('去掉客户所在地限制。',2024,'invoice_count',[],invoice_sql(2024,None,'invoice_count'))]},
      {'id':'d4-dialog-02','split':'dev','purpose':'同比期间推导、指标改变','turns':[
        turn('2024年账单国为美国的发票销售额同比增长率是多少？',2024,'invoice_revenue',[bill('USA')],invoice_sql(2024,'USA',growth=True),task_type='growth',base=period(2023)),
        turn('换成加拿大。',2024,'invoice_revenue',[bill('Canada')],invoice_sql(2024,'Canada',growth=True),task_type='growth',base=period(2023)),
        turn('改成2025年同比。',2025,'invoice_revenue',[bill('Canada')],invoice_sql(2025,'Canada',growth=True),task_type='growth',base=period(2024)),
        turn('指标换成平均每张发票金额。',2025,'average_invoice_amount',[bill('Canada')],invoice_sql(2025,'Canada','average_invoice_amount',growth=True),task_type='growth',base=period(2024)),
        turn('国家换成德国。',2025,'average_invoice_amount',[bill('Germany')],invoice_sql(2025,'Germany','average_invoice_amount',growth=True),task_type='growth',base=period(2024)),
        turn('期间改成2023年。',2023,'average_invoice_amount',[bill('Germany')],invoice_sql(2023,'Germany','average_invoice_amount',growth=True),task_type='growth',base=period(2022))]},
      {'id':'d4-dialog-03','split':'dev','purpose':'对象替换、添加独立国家条件','turns':[
        turn('2022年艺术家 Metallica 的销售额是多少？',2022,'detail_revenue',[artist('Metallica')],detail_sql(2022,artist='Metallica')),
        turn('改成流派 Metal。',2022,'detail_revenue',[genre('Metal')],detail_sql(2022,genre='Metal')),
        turn('期间改成2023年，限定账单国为德国。',2023,'detail_revenue',[genre('Metal'),bill('Germany')],detail_sql(2023,genre='Metal',country='Germany')),
        turn('指标改成购买数量。',2023,'purchased_quantity',[genre('Metal'),bill('Germany')],detail_sql(2023,genre='Metal',country='Germany',metric='purchased_quantity')),
        turn('期间改成2024年。',2024,'purchased_quantity',[genre('Metal'),bill('Germany')],detail_sql(2024,genre='Metal',country='Germany',metric='purchased_quantity')),
        turn('账单国家换成巴西。',2024,'purchased_quantity',[genre('Metal'),bill('Brazil')],detail_sql(2024,genre='Metal',country='Brazil',metric='purchased_quantity'))]},
      {'id':'d4-dialog-04','split':'dev','purpose':'TopN、排名指标、增删范围','turns':[
        turn('2023年按购买数量排名前3的曲目，返回曲目编号和购买数量；并列按曲目编号升序。',2023,'purchased_quantity',[],detail_sql(2023,metric='purchased_quantity',top=3),top_n=3,task_type='ranking'),
        turn('改成前5首。',2023,'purchased_quantity',[],detail_sql(2023,metric='purchased_quantity',top=5),top_n=5,task_type='ranking'),
        turn('指标改成销售额。',2023,'detail_revenue',[],detail_sql(2023,metric='detail_revenue',top=5),top_n=5,task_type='ranking'),
        turn('期间改成2024年。',2024,'detail_revenue',[],detail_sql(2024,metric='detail_revenue',top=5),top_n=5,task_type='ranking'),
        turn('加上账单国家为法国。',2024,'detail_revenue',[bill('France')],detail_sql(2024,country='France',metric='detail_revenue',top=5),top_n=5,task_type='ranking'),
        turn('去掉账单国家限制。',2024,'detail_revenue',[],detail_sql(2024,metric='detail_revenue',top=5),top_n=5,task_type='ranking')]},
      {'id':'d4-dialog-05','split':'dev','purpose':'分子/分母独立作用域','turns':[
        turn('2023年巴西居住客户的销售额占当年全部发票金额的比例是多少？',2023,'invoice_revenue',[{**residence('Brazil'),'binding_scope':'numerator'}],ratio_sql('Brazil'),task_type='ratio'),
        turn('分子换成德国居住客户的销售额。',2023,'invoice_revenue',[{**residence('Germany'),'binding_scope':'numerator'}],ratio_sql('Germany'),task_type='ratio'),
        turn('分母改成2023年账单国为德国的销售额。',2023,'invoice_revenue',[{**residence('Germany'),'binding_scope':'numerator'},{**bill('Germany'),'binding_scope':'denominator'}],ratio_sql('Germany','Germany'),task_type='ratio'),
        turn('分子换成法国居住客户的销售额。',2023,'invoice_revenue',[{**residence('France'),'binding_scope':'numerator'},{**bill('Germany'),'binding_scope':'denominator'}],ratio_sql('France','Germany'),task_type='ratio'),
        turn('分母改成2023年全部发票金额。',2023,'invoice_revenue',[{**residence('France'),'binding_scope':'numerator'}],ratio_sql('France'),task_type='ratio'),
        turn('分子换成巴西居住客户的销售额。',2023,'invoice_revenue',[{**residence('Brazil'),'binding_scope':'numerator'}],ratio_sql('Brazil'),task_type='ratio')]},
    ]


def original_cases():
    source=ROOT/'eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl'
    rows=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines() if line.strip()]
    if any(row.get('split')!='dev' for row in rows):raise ValueError('DEV source only')
    result=[]
    for row in rows:
        if row['id'] not in {'sp03-26','sp03-27','sp03-28'}:continue
        controller=row['controller'];supplements=controller['allowed_user_supplements']
        result.append({'id':row['id'],'split':'dev','purpose':'原失败对话逐字复测','initial':row['input'],'supplements':supplements,
                       'gold_sql':row['gold_sql'],'post_completion_turns':controller['post_completion_turns'],
                       'source':str(source.relative_to(ROOT)),'source_sha256':sha256(source.read_bytes()).hexdigest()})
    return result


def original_expected(case_id,message):
    """Explicit DEV transcript labels; no held labels or prediction-derived gold."""
    country=lambda field,value,role=None:{'column':field,'operator':'=','value':value,**({'binding_scope':role} if role else {})}
    if case_id=='sp03-26':
        if message=='同比增长多少？':return {'task_type':'growth','metric':None,'time_scope':None,'filters':[]}
        year=2025 if '2025' in message or '平均' in message else 2024
        metric=None if '2024年全年' in message else 'average_invoice_amount' if '平均' in message else 'invoice_revenue'
        return {'task_type':'growth','metric':metric,'current':period(year),'base':period(year-1),'filters':[],'comparison':{'type':'yoy'}}
    if case_id=='sp03-27':
        if message=='2023年销售额占比是多少？':return {'task_type':'ratio','metric':'invoice_revenue','current':period(2023),'filters':[]}
        numerator='Germany' if '德国' in message else 'Brazil'
        values=[country('customer.country',numerator,'numerator')]
        if message.startswith('分母改成'):values.append(country('invoice.billing_country','Germany','denominator'))
        return {'task_type':'ratio','metric':'invoice_revenue','current':period(2023),'filters':values}
    if case_id=='sp03-28':
        values=[] if message=='2022年金属乐队的销售额是多少？' else [country('artist.name','Metallica')] if 'Metallica' in message else [country('genre.name','Metal')]
        year=2023 if message.startswith('期间改成') else 2022
        if year==2023:values.append(country('invoice.billing_country','Germany'))
        return {'metric':'detail_revenue','current':period(year),'filters':values}
    raise ValueError('Unknown original DEV transcript')


def contract_check(expected,response):
    semantic=response.get('metadata',{}).get('clarify',{}).get('semantic_contract') or {}
    issues=[]
    for field,wanted in expected.items():
        if field in {'current','base'}:
            got=(semantic.get('time_scope') or {}).get(field) or {}
            if any(got.get(key)!=value for key,value in wanted.items()):issues.append({'field':field,'expected':wanted,'actual':got})
        elif field=='filters':
            keys=('column','operator','value','binding_scope')
            normalize=lambda items:sorted(json.dumps({key:item.get(key) for key in keys},ensure_ascii=False,sort_keys=True) for item in items)
            if normalize(semantic.get('filters') or [])!=normalize(wanted):issues.append({'field':'filters','expected':wanted,'actual':semantic.get('filters')})
        elif semantic.get(field)!=wanted:issues.append({'field':field,'expected':wanted,'actual':semantic.get(field)})
    return {'matched':not issues,'issues':issues}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);parser.add_argument('--api',default='http://127.0.0.1:8000')
    parser.add_argument('--only',nargs='+');parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    output=(ROOT/args.output).resolve()
    if not output.is_relative_to(ROOT/'eval/artifacts/d4') or output.exists():raise SystemExit('Use a fresh D4 evidence directory')
    output.mkdir(parents=True)
    cases=original_cases()+new_cases()
    if args.only:
        if set(args.only)-{case['id'] for case in cases}:raise SystemExit('Unknown DEV case')
        cases=[case for case in cases if case['id'] in args.only]
    (output/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
    source_paths=['qa_agent/clarify/service.py','qa_agent/clarify/state.py','qa_agent/clarify/extractor.py',
                  'qa_agent/clarify/sql_guard.py','qa_agent/clarify/prompts/intent_patch.txt','qa_agent/pipeline.py',
                  'qa_agent/sql/generator.py','qa_agent/sql/ratio_guard.py','qa_agent/sql/prompts/multi_table.txt',
                  'scripts/run_d4_multiturn.py','tests/test_d4_multiturn.py']
    snapshots=[]
    for relative in source_paths:
        source=ROOT/relative;target=output/'source_snapshot'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        snapshots.append({'path':relative,'sha256':sha256(source.read_bytes()).hexdigest(),
                          'snapshot':str(target.relative_to(ROOT))})
    (output/'command.json').write_text(json.dumps({'argv':sys.argv,'cwd':str(ROOT),'source_snapshot':snapshots,
                      'split':'dev','held_predictions':0,'note':'No environment values or private config copied.'},ensure_ascii=False,indent=2),encoding='utf-8')
    if args.prepare:
        print(json.dumps({'state':'PREPARED_NOT_RUN','cases':len(cases),'new_dialogue_turns':30,'model_calls':0},ensure_ascii=False));return
    settings=get_settings();catalog=load_catalog(settings.catalog_path)
    def run(case):
        directory=output/case['id'];directory.mkdir();session='d4-multiturn-'+uuid4().hex;records=[];response=None
        with httpx.Client(timeout=240,trust_env=False) as client:
            def send(message,expected=None,gold_sql=None,ordered=False,choice_id=None):
                nonlocal response
                index=len(records);target=directory/f'{index:02d}';target.mkdir()
                payload={'session_id':session,'message':message,'scope':{'route':'sql','db_id':'chinook','doc_ids':[]}}
                if response and response.get('status')=='NEEDS_CLARIFICATION':
                    payload.update(clarification_id=response['clarification']['clarification_id'],intent_version=response['intent']['intent_version'])
                    if choice_id:payload['choice_id']=choice_id
                (target/'request.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
                before=perf_counter();raw=client.post(args.api+'/api/chat',json=payload);elapsed=(perf_counter()-before)*1000
                (target/'response.raw.json').write_bytes(raw.content);raw.raise_for_status();response=raw.json()
                conditions=contract_check(expected or {},response)
                version=response.get('intent',{}).get('intent_version')
                previous=records[-1]['intent_version'] if records else 0
                version_ok=version==previous+1
                comparison={'matched':None,'reason':'no SQL expected at incomplete clarification turn'}
                strict_comparison={'matched':None,'reason':'no SQL expected at incomplete clarification turn'}
                if gold_sql:
                    reference=execute_sql(gold_sql,settings.db_url,statement_timeout_ms=settings.statement_timeout_ms,max_rows=200)
                    reference_record={'sql':gold_sql,'result':reference.as_dict() if hasattr(reference,'as_dict') else {'columns':reference.columns,'rows':reference.rows},'readonly':True,'statement_timeout_ms':settings.statement_timeout_ms}
                    (target/'reference-readonly.json').write_text(json.dumps(reference_record,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
                    if response.get('status') in {'SUCCEEDED','EMPTY_RESULT'} and response.get('table') is not None:
                        # Plan §5.2 rounds numeric results to two decimal places.
                        # Preserve full raw SQL/results and an unrounded strict
                        # diagnostic alongside the primary plan EX; no gold edits.
                        numeric=list(range(len(reference.columns)))
                        common={'ordered':ordered,'expected_columns':reference.columns,
                                'actual_columns':response.get('metadata',{}).get('result_columns'),
                                'numeric_columns':numeric,'actual_sql':response.get('sql'),'catalog':catalog}
                        comparison=compare_plan_results(reference.rows,response['table'],round_numeric_columns=numeric,**common).as_dict()
                        strict_comparison=compare_plan_results(reference.rows,response['table'],round_numeric_columns=[],**common).as_dict()
                    else:
                        comparison={'matched':False,'reason':response.get('status')}
                        strict_comparison=dict(comparison)
                record={'index':index,'message':message,'status':response.get('status'),'intent_version':version,'version_correct':version_ok,'condition_check':conditions,'result_check':comparison,'strict_result_check':strict_comparison,'trace_id':response.get('trace_id'),'latency_ms':elapsed,'request_file':str((target/'request.json').relative_to(ROOT)),'response_file':str((target/'response.raw.json').relative_to(ROOT)),'expected':expected,'sql':response.get('sql'),'semantic_contract':response.get('metadata',{}).get('clarify',{}).get('semantic_contract'),'invalidated_execution':response.get('metadata',{}).get('clarify',{}).get('invalidated_execution')}
                records.append(record);print(json.dumps({'case':case['id'],'turn':index,'status':record['status'],'condition':conditions['matched'],'result':comparison['matched']},ensure_ascii=False),flush=True)
            try:
                if 'turns' in case:
                    for item in case['turns']:send(item['message'],item['expected'],item['gold_sql'],item['ordered'])
                else:
                    send(case['initial'],original_expected(case['id'],case['initial']))
                    used=set()
                    while response.get('status')=='NEEDS_CLARIFICATION' and len(records)<5:
                        card=response['clarification'];issues=card.get('issues') or [];keys=[issue.get('field') for issue in issues]
                        if case['id']=='sp03-26' and 'time_scope.current' in keys:
                            keys=['time_scope.current']+[key for key in keys if key!='time_scope.current']
                        key=next((key for key in keys if key in case['supplements'] and key not in used),None)
                        if case['id']=='sp03-28':
                            option=next((option for option in card.get('options',[]) if 'Metallica' in option.get('label','')),None)
                            if option:send(option['label'],original_expected(case['id'],option['label']),gold_sql=case['gold_sql'],choice_id=option['id']);continue
                        if not key:break
                        used.add(key);message=case['supplements'][key]['answer']
                        send(message,original_expected(case['id'],message),gold_sql=case['gold_sql'] if len(keys)==1 else None)
                    if response.get('status') in {'SUCCEEDED','EMPTY_RESULT'}:
                        # Oct12-authorized denominator default may eliminate a
                        # clarification. Preserve the original explicit answer
                        # as a subsequent confirmation rather than forcing a card.
                        if case['id']=='sp03-27' and 'denominator' not in used:
                            message=case['supplements']['denominator']['answer'];send(message,original_expected(case['id'],message),gold_sql=case['gold_sql'])
                        for item in case['post_completion_turns']:send(item['message'],original_expected(case['id'],item['message']),gold_sql=item['gold_sql'])
                completed=len(records)==len(case.get('turns',records)) and all(record['status'] not in {'FAILED','UNSUPPORTED'} and record['condition_check']['matched'] and record['version_correct'] and record['result_check']['matched'] is not False for record in records)
                if 'turns' not in case:completed=completed and len(records)>=len(case['post_completion_turns'])+2 and records[-1]['result_check']['matched'] is True
                item={'id':case['id'],'split':'dev','completed_all_turns':completed,'turns':records}
            except Exception as exc:
                item={'id':case['id'],'split':'dev','completed_all_turns':False,'turns':records,'error':sanitize_error(exc,settings)}
        (directory/'report.json').write_text(json.dumps(item,ensure_ascii=False,indent=2,default=str),encoding='utf-8');return item
    with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(run,cases))
    new=[record for record in records if record['id'].startswith('d4-dialog-')]
    turns=[turn for record in new for turn in record['turns']]
    sql_turns=[turn for turn in turns if turn['result_check']['matched'] is not None]
    report={'state':'COMPLETED','created_at':datetime.now(timezone.utc).isoformat(),'held_predictions':0,
            'scoring_rule':'Plan §5.2: numeric two decimal places, ignore column names/order, preserve requested row ordering; strict full-precision diagnostic separately.',
            'case_count':len(records),'all_turns_success':sum(record['completed_all_turns'] for record in records),'new_conversations':len(new),'new_all_turns_success':sum(record['completed_all_turns'] for record in new),'condition_correct_turns':sum(turn['condition_check']['matched'] for turn in turns),'condition_turns':len(turns),'result_correct_turns':sum(turn['result_check']['matched'] is True for turn in sql_turns),'result_turns':len(sql_turns),
            'strict_result_correct_turns':sum(turn['strict_result_check']['matched'] is True for turn in sql_turns),'records':records}
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8');print(json.dumps({key:value for key,value in report.items() if key!='records'},ensure_ascii=False),flush=True)
    if report['all_turns_success']!=len(records):raise SystemExit(1)


if __name__=='__main__':main()
