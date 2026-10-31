"""Exercise a running empty container over real HTTP without a model API key."""
import argparse
import base64
import io
import json
import os
from pathlib import Path
import sys
import time
from urllib.request import ProxyHandler, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8501')
    parser.add_argument('--verify-persistence',action='store_true')
    args=parser.parse_args()
    opener=build_opener(ProxyHandler({}))
    public_port=os.getenv('COMAGENT_UI_PORT','8501')
    origin='http://127.0.0.1:'+public_port
    def call(path,payload=None):
        request=Request(args.base_url+path,data=None if payload is None else json.dumps(payload).encode(),
                        headers={'Content-Type':'application/json','Host':'127.0.0.1:'+public_port,'Origin':origin})
        with opener.open(request,timeout=15) as response:
            return response.status,json.load(response)
    assert call('/ui-health')[1]['status']=='ok'
    assert call('/health')[1]['service']=='comagent'
    assert '/api/documents/import' in call('/openapi.json')[1]['paths']
    call('/api/databases')
    receipt_path=ROOT/'.runtime/container-smoke.json'
    def verify_database(db_id):
        from deployment.container_entrypoint import credential_key
        os.environ['COMAGENT_CREDENTIAL_KEY']=credential_key(ROOT/'.runtime')
        from qa_agent.database_registry import get_registry
        from qa_agent.sql.executor import execute_sql
        connection=get_registry().get_connection(db_id)
        result=execute_sql('SELECT COUNT(*) AS count FROM public.release_probe',connection.db_url)
        assert result.table==[{'count':1}],result.table
    if args.verify_persistence:
        receipt=json.loads(receipt_path.read_text('utf-8'))
        _,listing=call('/api/documents')
        assert set(receipt['doc_ids']).issubset({d['doc_id'] for d in listing['documents'] if d['ready']})
        from qa_agent.context import ContextStore
        from qa_agent.schemas import ChatRequest
        context=ContextStore().resolve(ChatRequest(message='verify persistence',session_id=receipt['session_id'],context_id=receipt['context_id']))
        assert len(context.text)==receipt['context_characters']
        if receipt.get('db_id'):verify_database(receipt['db_id'])
        print('PASS persisted documents, context and encrypted connection after restart',flush=True)
        return
    import fitz
    from docx import Document
    marker=uuid4().hex[:8]
    pdf=fitz.open();pdf.new_page().insert_text((50,65),'Cedar budget is 202631 dollars. '+marker)
    pdf_bytes=pdf.tobytes();pdf.close()
    doc=Document();doc.add_paragraph('Cedar budget is 202631 dollars. '+marker)
    stream=io.BytesIO();doc.save(stream)
    samples=[('text',None,('Pasted Cedar budget is 202631 dollars. '+marker).encode()),
             ('txt','probe.txt',('TXT Cedar budget is 202631 dollars. '+marker).encode()),
             ('pdf','probe.pdf',pdf_bytes),('docx','probe.docx',stream.getvalue())]
    ids=[]
    for kind,name,raw in samples:
        payload={'title':'Container check '+kind}
        payload.update({'filename':name,'content_base64':base64.b64encode(raw).decode()} if name else {'text':raw.decode()})
        status,job=call('/api/documents/'+('import' if name else 'text'),payload)
        assert status==202,job
        deadline=time.monotonic()+90
        while job['status'] in ('queued','indexing'):
            assert time.monotonic()<deadline,job
            time.sleep(.2);_,job=call('/api/documents/imports/'+job['job_id'])
        assert job['status']=='ready',job
        doc_id=job['document']['doc_id'];ids.append(doc_id)
        status,answer=call('/api/chat',{'session_id':'container-'+marker+kind,'message':'What is the Cedar budget?',
                                      'scope':{'route':'doc','doc_ids':[doc_id]}})
        assert status==200 and answer['status']=='SUCCEEDED' and '202631' in answer['answer'],answer
        assert answer['evidences'],answer
        print('PASS',kind,flush=True)
    _,documents=call('/api/documents')
    assert set(ids).issubset({d['doc_id'] for d in documents['documents'] if d['ready']})
    session_id='context-'+marker
    status,context=call('/api/context',{'session_id':session_id,'text':'Original full text. '*400})
    assert status==201 and context['characters']==len('Original full text. '*400)
    host=os.getenv('COMAGENT_SMOKE_DB_HOST')
    db_id=None
    if host:
        status,registered=call('/api/databases',{'name':'Release verification database','host':host,
           'database':'postgres','user':'qa_reader','password':os.environ['COMAGENT_SMOKE_DB_PASSWORD'],'schemas':['public']})
        assert status==201,registered
        db_id=registered['db_id']
        verify_database(db_id)
        print('PASS encrypted database registration and read-only query',flush=True)
    receipt_path.write_text(json.dumps({'doc_ids':ids,'session_id':session_id,'context_id':context['context_id'],
                                      'context_characters':context['characters'],'db_id':db_id}),encoding='utf-8')
    print(json.dumps({'passed':True,'uploads':len(ids),'session_context':True,'answer_mode':'extractive',
                      'model_api_calls':0,'registered_database_verified':bool(host)}),flush=True)


if __name__=='__main__':main()
