import json
from pathlib import Path
from dataclasses import asdict
from scripts.d4_sql_scale import load_cases,remap_sql,explain_readonly
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import validate_sql
from qa_agent.sql.executor import execute_sql
s=get_settings();root=Path('.').resolve();out=root/'eval/artifacts/d4/sql-scale-gold-readonly-001';out.mkdir()
man=json.loads((root/'eval/artifacts/d4/sql-scale-data-001/manifest.json').read_text('utf-8'))
cases,_=load_cases();groups=[('original','public',s.catalog_path)]+[(str(x['line_count']),x['schema'],root/x['catalog']) for x in man['scales']]
records=[]
for scale,schema,path in groups:
 cat=load_catalog(path)
 for case in cases:
  stmt=remap_sql(case['gold_sql'],schema) if schema!='public' else case['gold_sql']
  valid=validate_sql(stmt,cat,max_rows=s.max_rows)
  result=execute_sql(valid.sql,s.db_url,statement_timeout_ms=s.statement_timeout_ms,max_rows=s.max_rows)
  record={'id':case['id'],'scale':scale,'sql':valid.sql,'result':asdict(result),'system_prediction':False}
  records.append(record)
  (out/f'{scale}-{case["id"]}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf-8')
report={'references':len(records),'readonly_executed':len(records),'model_calls':0,'system_predictions':0,'held_queries':0,'source_manifest':'eval/artifacts/d4/sql-scale-data-001/manifest.json','statement_timeout_ms':s.statement_timeout_ms}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(report,ensure_ascii=False))
