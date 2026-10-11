"""Verify actual D2 artifacts and live file endpoints without more model calls."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import httpx
import numpy as np
from qa_agent.config import get_settings, sanitize_error
from qa_agent.nlu.value_index import load_value_index
from qa_agent.rag.index import load_index


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'eval/reports/d2-acceptance/engineering.json')
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; use a fresh output path')
    settings=get_settings()
    checks=[]
    def check(name,condition,details=None):
        checks.append({'name':name,'passed':bool(condition),'actual':details})
    check('python_3_12',sys.version_info[:2]==(3,12),sys.version.split()[0])
    initial=json.loads((ROOT/'eval/artifacts/d2/preflight-initial.json').read_text(encoding='utf8'))
    check('shared_schema_unchanged',digest(ROOT/'qa_agent/schemas.py')==initial['d1_evidence_hashes']['qa_agent/schemas.py'])
    try:
        index=load_value_index(settings.value_index_path)
        metadata=json.loads((settings.value_index_path/'index_meta.json').read_text(encoding='utf8'))
        check('value_artifacts_hash_verified',index is not None,metadata['standard_count'])
        check('low_cardinality_columns_all_built',len(metadata['column_audit'])==34 and all(r['status']=='indexed' and r['distinct_non_null_count']<5000 for r in metadata['column_audit']),len(metadata['column_audit']))
        vectors=np.load(settings.value_index_path/'embeddings.npy',allow_pickle=False)
        check('value_vectors_real_finite_normalized',vectors.shape==(5528,1024) and np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-4),list(vectors.shape))
        check('pending_aliases_excluded',metadata['alias_audit']['accepted_count']==0 and metadata['alias_audit']['excluded_count']==81,metadata['alias_audit'])
        check('alias_snapshot_current',metadata['alias_audit']['input_sha256']==digest(ROOT/'data/aliases/aliases.csv'))
    except Exception as exc:
        check('value_index_ready',False,sanitize_error(exc,settings))
    try:
        chunks,metadata=load_index(settings=settings)
        check('rag_index_and_sources_verified',len(metadata['documents'])==13 and len(chunks)==2193,{'documents':len(metadata['documents']),'chunks':len(chunks)})
        vectors=np.load(settings.rag_index_path/'embeddings.npy',allow_pickle=False)
        check('rag_vectors_real_finite_normalized',vectors.shape==(2193,1024) and np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors,axis=1),1,atol=1e-4),list(vectors.shape))
        check('runtime_top8_top20_rrf60',(settings.rag_top_k,settings.rag_candidate_k,settings.rag_rrf_k)==(8,20,60))
        non_pdf_ids={d['doc_id'] for d in metadata['documents'] if not d['path'].endswith('.pdf')}
        check('non_pdf_locations_do_not_invent_pages',all(c['page'] is None for c in chunks if c['doc_id'] in non_pdf_ids))
    except Exception as exc:
        check('rag_index_ready',False,sanitize_error(exc,settings))
    old=json.loads((ROOT/'eval/artifacts/d2/d1-index-preservation.json').read_text(encoding='utf8'))
    # The preservation file records the source filenames and SHA256 before D2.
    for name,sha in old['sha256'].items():
        path=ROOT/old['path']/name
        check('d1_index_preserved:'+name,path.is_file() and digest(path)==sha)
    with httpx.Client(timeout=30,trust_env=False) as client:
        health=client.get('http://127.0.0.1:8000/health').json()
        check('real_api_model_database_ready',health.get('stage')=='D2' and health.get('database_ready') and health.get('llm_configured') and health.get('model')=='deepseek-flash',health)
        check('real_ui_ready',client.get('http://127.0.0.1:8501/_stcore/health').status_code==200)
        listed=client.get('http://127.0.0.1:8000/api/documents').json()
        documents=listed.get('documents',[])
        check('all13_live_documents_ready',listed.get('status')=='READY' and len(documents)==13 and all(d['ready'] for d in documents))
        for doc in documents:
            response=client.get('http://127.0.0.1:8000/api/documents/'+doc['doc_id']+'/file')
            check('actual_download_hash:'+doc['doc_id'],response.status_code==200 and hashlib.sha256(response.content).hexdigest()==doc['content_hash'],{'status':response.status_code,'bytes':len(response.content),'mime':response.headers.get('content-type')})
            if doc['format']=='pdf':
                for page in sorted({1,doc['page_count']}):
                    response=client.get(f"http://127.0.0.1:8000/api/documents/{doc['doc_id']}/pages/{page}")
                    check(f"actual_pdf_preview:{doc['doc_id']}:{page}",response.status_code==200 and response.content.startswith(b'\x89PNG\r\n\x1a\n'))
            else:
                response=client.get(f"http://127.0.0.1:8000/api/documents/{doc['doc_id']}/pages/1")
                check('non_pdf_page_rejected:'+doc['doc_id'],response.status_code==404 and doc['page_count'] is None)
        check('unknown_document_rejected',client.get('http://127.0.0.1:8000/api/documents/d2-unregistered/file').status_code==404)
    for suite,expected in [('nl2sql',35),('robust',21),('rag',21)]:
        report=json.loads((ROOT/f'eval/artifacts/d2/{suite}/final/report.json').read_text(encoding='utf8'))
        check('actual_dev_prediction_count:'+suite,report['status']=='COMPLETED' and report['prediction_count']==expected and report['holdout_prediction_count']==0,report['prediction_count'])
        check('gold_still_pending:'+suite,report['gold_human_accepted_count']==0)
    gate=json.loads((ROOT/'eval/artifacts/d2/nl2sql/review-gate/report.json').read_text(encoding='utf8'))
    check('formal_review_gate_zero_predictions',gate['status']=='READINESS_ONLY' and gate['prediction_count']==0)
    record={'created_at_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS' if all(r['passed'] for r in checks) else 'FAIL',
            'passed':sum(r['passed'] for r in checks),'total':len(checks),'checks':checks,
            'scope':'Actual current artifacts, live registered file/download/page endpoints; no additional benchmark/model calls; human review not simulated'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'status':record['status'],'passed':record['passed'],'total':record['total'],'failed':[r for r in checks if not r['passed']]},ensure_ascii=False))
    return 0 if record['status']=='PASS' else 1


if __name__=='__main__':
    raise SystemExit(main())
