"""Verify D3 session patches against real API responses and read-only DB evidence.

These explicit development flows are independent of all protected datasets.
Expected answers are queried separately; no expected result is sent to /api/chat.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter
from uuid import uuid4

import httpx
import psycopg
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope
from sqlglot.schema import MappingSchema

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.catalog import load_catalog


def canonical(value):
    if isinstance(value, (int,float,Decimal)):
        return str(Decimal(str(value)).normalize())
    if isinstance(value,str):
        try:return str(Decimal(value).normalize())
        except Exception:pass
    return value


def invoice_amount(result):
    """Read the real invoice SUM projection; context columns may accompany it."""
    rows=result.get('table') or []
    if len(rows)!=1 or not result.get('sql'):return '<no unique invoice amount>'
    tree=sqlglot.parse_one(result['sql'],read='postgres')
    if not isinstance(tree,exp.Select):return '<no direct aggregate projection>'
    aliases={table.alias_or_name:table.name for table in tree.find_all(exp.Table)}
    names=[]
    for projected in tree.expressions:
        value=projected.this if isinstance(projected,exp.Alias) else projected
        if isinstance(value,exp.Sum) and isinstance(value.this,exp.Column) and value.this.name=='total':
            column=value.this
            if (column.table and aliases.get(column.table)=='invoice') or (not column.table and set(aliases.values())=={'invoice'}):
                names.append(projected.alias_or_name)
    if len(names)==1 and names[0] in rows[0]:return rows[0][names[0]]
    return '<no unique verified invoice SUM projection>'


def observed_country_result_sources(sql,catalog):
    """Extract observed physical sources independently of the expected target."""
    checked=normalize_identifiers(sqlglot.parse_one(sql,read='postgres'),dialect='postgres')
    checked=qualify(checked,dialect='postgres',db='public',
                    schema=MappingSchema(catalog.sqlglot_schema(),dialect='postgres',normalize=False),
                    allow_partial_qualification=False,validate_qualify_columns=True)
    scopes=list(traverse_scope(checked))
    if len(scopes)!=1 or not isinstance(checked,exp.Select):
        return {'verified':False,'reason':'Complex derived sources are not independently proved in this bounded D3 check.','sources':[]}
    aliases={alias:source for alias,(_,source) in scopes[0].selected_sources.items()}
    result=[]
    nodes=[('SELECT',node) for node in checked.expressions]+[
        ('GROUP BY',checked.args.get('group')),('HAVING',checked.args.get('having'))]
    for position,node in nodes:
        if node is None:continue
        for column in node.find_all(exp.Column):
            table=aliases.get(column.table)
            if not isinstance(table,exp.Table):continue
            source=f'{table.name}.{column.name}'
            if source in {'invoice.billing_country','customer.country','employee.country'}:
                result.append({'position':position,'source':source,'sql_column':column.sql(dialect='postgres')})
    return {'verified':True,'sources':result}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    args=parser.parse_args()
    output=args.output if args.output.is_absolute() else ROOT/args.output
    if output.exists():raise SystemExit('Preserve previous evidence; choose a fresh output path.')
    settings=get_settings()
    with httpx.Client(timeout=240,trust_env=False) as client:
        health=client.get(args.base_url+'/health').json()
        if health.get('stage')!='D3' or not health.get('database_ready'):
            raise SystemExit('D3 and existing Chinook DB must be active; no predictions generated.')
        output.mkdir(parents=True)
        code_paths=[ROOT/'qa_agent/pipeline.py',ROOT/'qa_agent/schemas.py',*sorted((ROOT/'qa_agent/clarify').rglob('*.py')),
                    ROOT/'qa_agent/config.py',ROOT/'qa_agent/llm.py',ROOT/'qa_agent/sql/generator.py',
                    ROOT/'qa_agent/sql/executor.py',ROOT/'qa_agent/sql/validator.py',ROOT/'qa_agent/sql/prompts/multi_table.txt',
                    ROOT/'qa_agent/nlu/linker.py',
                    *sorted((ROOT/'qa_agent/clarify/prompts').glob('*.txt')),ROOT/'qa_agent/clarify/clarify_rules.yaml']
        (output/'run.json').write_text(json.dumps({'command':[sys.executable,'-B',*sys.argv],
            'created_at_utc':datetime.now(timezone.utc).isoformat(),'health':health,
            'code_sha256':{str(path.relative_to(ROOT)).replace('\\','/'):sha256(path.read_bytes()).hexdigest() for path in code_paths},
            'model':settings.llm_model,'source':'new explicit D3 development interaction scenarios',
            'protected_holdout_predictions':0,'human_review_status':'pending_human_review'},ensure_ascii=False,indent=2),encoding='utf-8')
        records=[]
        checks=[]
        catalog=load_catalog(settings.catalog_path)

        def ask(name,session,message,*,card=None,choice_id=None):
            request={'session_id':session,'message':message,'scope':{'route':'sql','db_id':'chinook','doc_ids':[]}}
            if card:request.update(clarification_id=card['clarification_id'],intent_version=card['intent_version'])
            if choice_id:request['choice_id']=choice_id
            start=perf_counter()
            try:
                response=client.post(args.base_url+'/api/chat',json=request)
                response.raise_for_status();value=response.json();error=None
            except Exception as exc:value=None;error=sanitize_error(exc,settings)
            record={'name':name,'request':request,'response':value,'error':error,
                    'latency_ms':round((perf_counter()-start)*1000),'created_at_utc':datetime.now(timezone.utc).isoformat()}
            (output/(name+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
            records.append(record)
            print(json.dumps({'name':name,'status':(value or {}).get('status'),'error':error},ensure_ascii=False),flush=True)
            return value or {}

        def check(name,passed,reason,evidence):
            checks.append({'name':name,'passed':bool(passed),'reason':reason,'evidence':evidence})

        # Same-field country changes keep the date. A country-scope change uses
        # the real customer -> invoice FK and must invalidate fields/schema.
        session='d3-condition-flow-'+str(uuid4())
        steps=[('country-initial','2024年按账单国家统计美国发票总额。','USA',2024,'invoice.billing_country',None),
               ('country-value','改成加拿大，其他条件保持不变。','Canada',2024,'invoice.billing_country',{'result'}),
               ('country-field','改按客户所在地统计，其他条件保持不变。','Canada',2024,'customer.country',{'fields','schema','result'}),
               ('country-period','改成2023年，其他条件保持不变。','Canada',2023,'customer.country',{'derived_period','result'})]
        for name,message,country,year,column,expected_invalidated in steps:
            result=ask(name,session,message)
            sql=('SELECT SUM(invoice.total) AS amount FROM invoice WHERE invoice.billing_country = %s '
                 'AND invoice.invoice_date >= %s::date AND invoice.invoice_date < %s::date' if column=='invoice.billing_country' else
                 'SELECT SUM(invoice.total) AS amount FROM invoice JOIN customer ON customer.customer_id=invoice.customer_id '
                 'WHERE customer.country = %s AND invoice.invoice_date >= %s::date AND invoice.invoice_date < %s::date')
            params=(country,f'{year}-01-01',f'{year+1}-01-01')
            # Never hold a database transaction while waiting for a model call.
            # Keep the existing role-level idle timeout and per-query timeout.
            with psycopg.connect(settings.db_url,connect_timeout=5) as connection:
                connection.read_only=True
                with connection.cursor() as cursor:
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)",(str(settings.statement_timeout_ms),))
                    cursor.execute("SELECT current_user, current_setting('transaction_read_only'), current_setting('statement_timeout')")
                    role,readonly,timeout=cursor.fetchone()
                    cursor.execute(sql,params);gold=cursor.fetchone()[0]
            reference={'sql':sql,'parameters':list(params),'columns':['amount'],'rows':[[str(gold) if gold is not None else None]],
                       'database_role':role,'transaction_read_only':readonly,'statement_timeout':timeout,
                       'human_review_status':'pending_human_review'}
            (output/(name+'.reference.json')).write_text(json.dumps(reference,ensure_ascii=False,indent=2),encoding='utf-8')
            actual=invoice_amount(result)
            check(name+'-actual-amount',result.get('status')=='SUCCEEDED' and canonical(actual)==canonical(gold),
                  'Actual invoice SUM projection equals independent read-only SUM under explicit country scope and retained year; additional country context columns are allowed.',[name+'.json',name+'.reference.json'])
            intent=result.get('intent') or {}
            filters=intent.get('filters') or []
            check(name+'-verified-country',any(item.get('column')==column and item.get('operator')=='=' and item.get('value')==country for item in filters),
                  'Verified intent filter uses the explicit current field/value, without old-country IN merge.',[name+'.json'])
            current=((intent.get('time_scope') or {}).get('current') or {})
            check(name+'-retained-period',current.get('start')==f'{year}-01-01' and current.get('end')==f'{year+1}-01-01',
                  'Intent preserves or replaces only the user-specified period.',[name+'.json'])
            if expected_invalidated is not None:
                actual_invalidated=set((result.get('metadata') or {}).get('clarify',{}).get('invalidated') or [])
                check(name+'-invalidation',actual_invalidated==expected_invalidated,
                      f'Expected invalidations {sorted(expected_invalidated)}; actual {sorted(actual_invalidated)}.',[name+'.json'])
            if column=='customer.country':
                try:
                    observed=observed_country_result_sources(result.get('sql') or '',catalog)
                except Exception as exc:
                    observed={'verified':False,'sources':[],'reason':sanitize_error(exc,settings)}
                observed['expected_scope_from_explicit_user_change']=column
                (output/(name+'.country-sources.json')).write_text(json.dumps(observed,ensure_ascii=False,indent=2),encoding='utf-8')
                check(name+'-country-output-source',result.get('status')=='SUCCEEDED' and observed['verified'] and
                      not any(item['source']=='invoice.billing_country' for item in observed['sources']),
                      'Physical SELECT/GROUP BY/HAVING country sources follow explicit customer-country scope; output aliases do not decide the source; independent employee.country is allowed.',
                      [name+'.json',name+'.country-sources.json'])
        # Actual free text restores a missing year, without a trusted choice.
        session='d3-free-flow-'+str(uuid4())
        initial=ask('free-year-initial',session,'按账单国家统计USA的发票总额同比增长率是多少？')
        card=initial.get('clarification') or {}
        check('free-year-initial-is-l2',initial.get('status')=='NEEDS_CLARIFICATION' and initial.get('sql') is None,
              'Missing current year asks before any SQL execution.', ['free-year-initial.json'])
        if card.get('clarification_id'):
            resumed=ask('free-year-resumed',session,'2024年',card=card)
            current=(((resumed.get('intent') or {}).get('time_scope') or {}).get('current') or {})
            base=(((resumed.get('intent') or {}).get('time_scope') or {}).get('base') or {})
            check('free-year-resumed-actual-query',resumed.get('status')=='SUCCEEDED' and bool(resumed.get('sql')) and current.get('start')=='2024-01-01' and base.get('start')=='2023-01-01',
                  'Actual free input applies explicit 2024 and derives actual 2023 YoY base; real query runs.', ['free-year-resumed.json'])
            stale=ask('stale-card-rejected',session,'2024年',card=card)
            check('stale-card-rejected-without-query',stale.get('status')=='FAILED' and (stale.get('error') or {}).get('code')=='clarification_conflict' and
                  not any(step.get('name') in {'value_link','llm','sql_gen','sql_exec'} for step in stale.get('steps',[])),
                  'Old card/version is rejected before model or SQL work.', ['stale-card-rejected.json'])
        else:
            check('free-year-resumed-actual-query',False,'Initial response did not provide a resumable card.', ['free-year-initial.json'])
        report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'passed':sum(item['passed'] for item in checks),
                'total':len(checks),'actual_api_requests':len(records),'protected_holdout_predictions':0,
                'technical_checks':sum(not item['name'].endswith('-country-output-source') for item in checks),
                'technical_passed':sum(item['passed'] for item in checks if not item['name'].endswith('-country-output-source')),
                'country_output_source_checks':sum(item['name'].endswith('-country-output-source') for item in checks),
                'country_output_source_passed':sum(item['passed'] for item in checks if item['name'].endswith('-country-output-source')),
                'human_review_status':'pending_human_review','notes':'These state/DB checks are actual dev interactions, not held-out or competition scores.'}
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({key:report[key] for key in ('passed','total','actual_api_requests','protected_holdout_predictions')},ensure_ascii=False))
        return int(not all(item['passed'] for item in checks))


if __name__=='__main__':raise SystemExit(main())
