"""Version the two explicitly authorized 老美 relationships and rebuild the index.

Existing tables/indexes are immutable. Embeddings for unchanged surfaces are
reused only from a hash-verified, configuration-compatible existing index.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

import numpy as np
import psycopg

from qa_agent.config import get_settings, sanitize_error
from qa_agent.nlu.value_index import ValueIndex
from qa_agent.sql.catalog import load_catalog
from scripts.build_value_index import ALIAS_FIELDS, load_reviewed_aliases, read_values, write_index


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorization',type=Path,required=True)
    parser.add_argument('--source-aliases',type=Path,default=ROOT/'data/aliases/aliases-d2-reviewed.csv')
    parser.add_argument('--source-index',type=Path,default=ROOT/'data/indexes/values-d2-reviewed')
    parser.add_argument('--output-aliases',type=Path,default=ROOT/'data/aliases/aliases-oct12-approved.csv')
    parser.add_argument('--output-index',type=Path,default=ROOT/'data/indexes/values-oct12-approved')
    parser.add_argument('--artifacts',type=Path,default=ROOT/'eval/artifacts/oct12/nlu-clarify')
    args=parser.parse_args()
    if args.output_aliases.exists() or args.output_index.exists():
        raise ValueError('Refusing to overwrite a prior alias/index version')
    source_text=args.authorization.read_text(encoding='utf-8-sig')
    if not ('老美' in source_text and 'USA' in source_text and '同意' in source_text):
        raise ValueError('Authorization document does not contain the supplied concrete alias decision')
    source_sha=sha256(args.authorization.read_bytes()).hexdigest()
    with args.source_aliases.open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    updates=[]
    for row in rows:
        if row['alias']=='老美' and row['standard_value']=='USA' and row['column'] in {'customer.country','invoice.billing_country'}:
            if row['review_status']!='approved_candidate':
                raise ValueError('Source alias version does not match the attested starting policy')
            before=dict(row)
            row.update(review_status='approved',reviewer='user-explicit-oct12-task',
                       source='user_authorized:12号任务.md:sha256:'+source_sha)
            updates.append({'alias_id':row['alias_id'],'before':before,'after':dict(row)})
    if len(updates)!=2:
        raise ValueError('Expected exactly the two existing USA/老美 relationships')
    settings=get_settings()
    values,column_audit=read_values(load_catalog(settings.catalog_path),settings.db_url)
    if any(entry.get('status')=='failed' for entry in column_audit):
        raise ValueError('Live read-only value inspection did not complete')
    # Verify that both authoritative target fields still contain USA.
    standards={(row.column,row.standard_value) for row in values}
    if not {('customer.country','USA'),('invoice.billing_country','USA')} <= standards:
        raise ValueError('Approved target is absent from the actual database')
    prior=ValueIndex.load(args.source_index)
    if prior.embeddings is None:
        raise ValueError('Source value index has no verified embeddings')
    aliases_tmp=args.artifacts/'aliases-oct12-prepared.csv'
    args.artifacts.mkdir(parents=True,exist_ok=True)
    with aliases_tmp.open('x',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=ALIAS_FIELDS)
        writer.writeheader();writer.writerows(rows)
    aliases,alias_audit=load_reviewed_aliases(aliases_tmp,values)
    if alias_audit['invalid']:
        raise ValueError('Alias target validation failed')
    records=sorted(values+aliases,key=lambda row:(row.column,row.standard_value,row.kind,row.surface))
    identity=lambda row:(row.column,row.standard_value,row.surface)
    positions={identity(row):number for number,row in enumerate(prior.records)}
    if len(positions)!=len(prior.records) or any(identity(row) not in positions for row in records):
        raise ValueError('Live values changed; full embedding generation is required, no unsafe reuse')
    vectors=np.asarray([prior.embeddings[positions[identity(row)]] for row in records],dtype=np.float32)
    ValueIndex(records,vectors)
    args.output_aliases.parent.mkdir(parents=True,exist_ok=True)
    args.output_aliases.write_bytes(aliases_tmp.read_bytes())
    metadata=write_index(values,aliases,args.output_index,column_audit,alias_audit,
                         build_embeddings=False,settings=settings)
    np.save(args.output_index/'embeddings.npy',vectors,allow_pickle=False)
    metadata.update(vectors_enabled=True,vector_count=len(vectors),vector_shape=list(vectors.shape),
                    embedding=prior.metadata['embedding'],
                    embedding_reuse={'source_index':args.source_index.relative_to(ROOT).as_posix(),
                                     'source_meta_sha256':sha256((args.source_index/'index_meta.json').read_bytes()).hexdigest(),
                                     'reason':'All text surfaces unchanged; vectors reordered by verified record identity',
                                     'reused_count':len(vectors)},
                    alias_source=args.output_aliases.relative_to(ROOT).as_posix())
    metadata['artifact_sha256']['embeddings.npy']=sha256((args.output_index/'embeddings.npy').read_bytes()).hexdigest()
    (args.output_index/'index_meta.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    ValueIndex.load(args.output_index)
    dates_sql="SELECT MIN(invoice_date)::date, MAX(invoice_date)::date, ARRAY_AGG(DISTINCT EXTRACT(YEAR FROM invoice_date)::int ORDER BY EXTRACT(YEAR FROM invoice_date)::int) FROM public.invoice"
    with psycopg.connect(settings.db_url,connect_timeout=5) as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        connection.execute("SET LOCAL statement_timeout='5000ms'")
        first,last,years=connection.execute(dates_sql).fetchone()
    audit={'created_at_utc':datetime.now(timezone.utc).isoformat(),
           'authorization_source':str(args.authorization),'authorization_sha256':source_sha,
           'authorization_kind':'explicit_user_document_instruction','human_signatures_added':False,
           'source_alias_sha256':sha256(args.source_aliases.read_bytes()).hexdigest(),
           'new_alias_sha256':sha256(args.output_aliases.read_bytes()).hexdigest(),
           'updated_relationships':updates,'other_relationships_changed':0,
           'policy_counts':dict(Counter(row['review_status'] for row in rows)),
           'live_date_verification':{'sql':dates_sql,'read_only':True,'statement_timeout_ms':5000,
                                     'min_date':str(first),'max_date':str(last),'available_years':years},
           'index':metadata}
    (args.artifacts/'alias-index-build.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'policy_counts':audit['policy_counts'],'live_date_verification':audit['live_date_verification'],
                      'record_count':metadata['record_count'],'vectors_reused':len(vectors)},ensure_ascii=False))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print(sanitize_error(error,get_settings()),file=sys.stderr)
        raise SystemExit(1)
