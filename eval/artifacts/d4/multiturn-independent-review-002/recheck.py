"""Offline rescore of saved DEV outputs; no DB connection and no model call."""
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from eval.metrics import compare_plan_results
from qa_agent.sql.catalog import load_catalog

output=Path(__file__).with_name('report.json')
if output.exists():
    raise SystemExit('Preserve existing independent review output')
catalog=load_catalog(ROOT/'data/catalog/chinook.yaml')
rows=[]
sources=[]
for source_dir in ('multiturn-original-live-001','multiturn-new-live-001'):
    directory=ROOT/'eval/artifacts/d4'/source_dir
    report_path=directory/'report.json'
    original=json.loads(report_path.read_text(encoding='utf-8'))
    sources.append({'path':str(report_path.relative_to(ROOT)),
                    'sha256':sha256(report_path.read_bytes()).hexdigest()})
    for case in original['records']:
        if case.get('split')!='dev':
            raise SystemExit('Only saved DEV outputs may be rescored')
        for turn in case['turns']:
            if turn['result_check']['matched'] is None:
                continue
            target=directory/case['id']/f"{turn['index']:02d}"
            response_file=target/'response.raw.json'
            reference_file=target/'reference-readonly.json'
            response=json.loads(response_file.read_text(encoding='utf-8'))
            reference=json.loads(reference_file.read_text(encoding='utf-8'))
            columns=reference['result']['columns']
            numeric=list(range(len(columns)))
            common={'ordered':'ORDER BY' in reference['sql'].upper(),
                    'expected_columns':columns,'actual_columns':response.get('metadata',{}).get('result_columns'),
                    'numeric_columns':numeric,'actual_sql':response.get('sql'),'catalog':catalog}
            if response.get('status') in {'SUCCEEDED','EMPTY_RESULT'}:
                plan=compare_plan_results(reference['result']['rows'],response['table'],round_numeric_columns=numeric,**common).as_dict()
                strict=compare_plan_results(reference['result']['rows'],response['table'],round_numeric_columns=[],**common).as_dict()
            else:
                plan=strict={'matched':False,'reason':response.get('status')}
            rows.append({'source_run':source_dir,'case_id':case['id'],'turn_index':turn['index'],
                         'old_rule_check':turn['result_check'],'plan_2dp_check':plan,'strict_full_precision_check':strict,
                         'condition_check':turn['condition_check'],'version_correct':turn['version_correct'],
                         'response':str(response_file.relative_to(ROOT)),'response_sha256':sha256(response_file.read_bytes()).hexdigest(),
                         'reference':str(reference_file.relative_to(ROOT)),'reference_sha256':sha256(reference_file.read_bytes()).hexdigest()})
summaries=[]
for name in ('multiturn-original-live-001','multiturn-new-live-001'):
    selected=[row for row in rows if row['source_run']==name]
    summaries.append({'run':name,'sql_turns':len(selected),
                      'old_rule_correct':sum(row['old_rule_check']['matched'] for row in selected),
                      'plan_2dp_correct':sum(row['plan_2dp_check']['matched'] for row in selected),
                      'strict_full_precision_correct':sum(row['strict_full_precision_check']['matched'] for row in selected)})
result={'state':'OFFLINE_RESCORE_COMPLETED_NOT_NEW_PREDICTION','at_utc':datetime.now(timezone.utc).isoformat(),
        'model_calls':0,'database_queries':0,'held_predictions':0,
        'command':[sys.executable,str(Path(__file__).resolve())],
        'scope':'Existing DEV raw responses and captured readonly reference results only. Raw files/gold/manual review records unchanged.',
        'primary_rule':'Plan §5.2 numeric results rounded to 2 decimal places; requested row order retained.',
        'old_rule_note':'Original runner rounded amount outputs but retained unrounded growth and ratio values.',
        'catalog_sha256':sha256((ROOT/'data/catalog/chinook.yaml').read_bytes()).hexdigest(),
        'source_reports':sources,'summaries':summaries,'rows':rows}
output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'state':result['state'],'summaries':summaries,'model_calls':0,'database_queries':0,'held_predictions':0},ensure_ascii=False))
