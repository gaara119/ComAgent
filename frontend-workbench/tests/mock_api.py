"""Controlled API fixture for UI checks; never connects to a model/database."""
import argparse, base64, json
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

requests=[]
contexts={}
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aVxkAAAAASUVORK5CYII=')
def envelope(**changes):
    result={'trace_id':'controlled-ui-fixture','status':'SUCCEEDED','answer':'测试接口返回5位客户。','sql':'SELECT COUNT(*) AS customer_count FROM customer;', 'table':[{'customer_count':5}],'evidences':[],'clarification':None,'intent':{'intent_version':1,'route':'sql','task_type':'lookup','metric':'count','time_scope':None,'filters':[],'grouping':[],'order':None,'assumptions':[],'unresolved':[]},'steps':[{'name':'受控测试步骤','status':'ok','latency_ms':1,'input_summary':{'fixture_input':'explicit-source'},'output_summary':{'fixture_count':5}}],'error':None,'metadata':{'result_columns':['customer_count'],'truncated':False}}
    result.update(changes);return result
class MockHandler(BaseHTTPRequestHandler):
    def emit(self,value,status=200):
        body=json.dumps(value,ensure_ascii=False).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path=='/health':return self.emit({'status':'ok','stage':'UI_TEST_FIXTURE','database_ready':True,'aw_database_ready':True,'llm_configured':True,'ui_test_fixture':True})
        if self.path=='/api/documents':return self.emit({'status':'READY','documents':[{'doc_id':'doc-test','title':'受控测试文档','format':'pdf','page_count':1,'ready':True}]})
        if self.path=='/__test_requests':return self.emit(requests)
        if self.path=='/api/documents/doc-test/pages/1':
            self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(PNG)));self.end_headers();self.wfile.write(PNG);return
        if self.path=='/api/documents/doc-test/file':
            body=b'controlled-test-file';self.send_response(200);self.send_header('Content-Type','text/plain');self.send_header('Content-Disposition','attachment; filename="fixture.txt"');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        self.emit({'detail':'fixture path not found'},404)
    def do_POST(self):
        if self.path not in {'/api/chat','/api/context'}:return self.emit({'detail':'fixture path not found'},404)
        try:data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        except Exception:return self.emit({'detail':'invalid JSON'},400)
        requests.append(data)
        if self.path=='/api/context':
            if not isinstance(data.get('text'),str) or not 1<=len(data['text'])<=120000:return self.emit({'detail':'invalid context'},422)
            previous=contexts.get(data['session_id'],{})
            saved={'session_id':data['session_id'],'context_id':f"fixture-context-{len(contexts)+1}-{previous.get('version',0)+1}",
                   'version':previous.get('version',0)+1,'characters':len(data['text']),
                   'content_sha256':sha256(data['text'].encode()).hexdigest(),'text':data['text']}
            contexts[data['session_id']]=saved
            return self.emit({key:value for key,value in saved.items() if key!='text'},201)
        allowed={'session_id','message','scope','clarification_id','intent_version','choice_id','context_id'}
        if set(data)-allowed or not {'session_id','message','scope'}<=set(data):return self.emit({'detail':'invalid ChatRequest fields'},422)
        if data.get('context_id') and contexts.get(data['session_id'],{}).get('context_id')!=data['context_id']:
            return self.emit({'detail':'wrong context binding'},409)
        if data.get('clarification_id'):
            if data['clarification_id']!='card-test-1' or data.get('intent_version')!=3:return self.emit({'detail':'stale clarification version'},409)
            return self.emit(envelope(answer='测试续问已接收法国条件。'))
        if data['scope'].get('route')=='hybrid':
            if data['scope'].get('db_id')!='chinook' or data['scope'].get('doc_ids')!=[]:
                return self.emit({'detail':'wrong hybrid scope'},422)
            definition='客单价' in data['message']
            missing='资料不足' in data['message']
            fusion={'plan_stages':['检索指标定义','按定义查询数据库'] if definition else ['查询艺术家排名','检索艺术家介绍'], 'completed_stages':2,'definition_used_in_generation':definition,'document_status':'insufficient' if missing else 'SUCCEEDED'}
            if definition:fusion['definition_context']={'expression':'AVG(invoice.total)','definition_quote':'客单价为平均每张发票金额'}
            else:fusion['transferred_entity']={'artist_id':1,'artist_name':'测试艺术家'}
            table=[{'average_invoice_amount':'5.25'}] if definition else [{'artist_id':1,'artist_name':'测试艺术家','sales_amount':'100.00'}]
            return self.emit(envelope(answer='已按指标手册定义计算 [E1]。' if definition else '已查询排名并检索对应介绍 [E1]。',status='EMPTY_RESULT' if missing else 'SUCCEEDED',sql='SELECT AVG(invoice.total) AS average_invoice_amount FROM invoice;' if definition else 'SELECT artist_id, artist_name, sales_amount FROM controlled_artist_ranking;',table=table,evidences=[] if missing else [{'evidence_id':'E1','doc_id':'doc-test','doc_title':'受控测试文档','page':1,'text':'测试原文介绍及客单价定义。'}],metadata={'fusion':fusion}))
        if data['scope'].get('route')=='doc':
            if data['scope'].get('doc_ids')!=['doc-test'] or data['scope'].get('db_id') is not None:return self.emit({'detail':'wrong document scope'},422)
            return self.emit(envelope(answer='受控文档结论 [E1]。',sql=None,table=None,evidences=[{'evidence_id':'E1','doc_id':'doc-test','doc_title':'受控测试文档','page':1,'section_path':['测试节'],'text':'测试原文 <script>window.UNTRUSTED_EXECUTED=true</script>','bbox':[0.1,0.1,0.9,0.9]}]))
        text=data['message']
        if '中文表头' in text:return self.emit(envelope(answer='表头按返回标签展示，原始数据保持不变。',metadata={'result_columns':['customer_count'],'column_labels':{'customer_count':'客户数量'}}))
        if '敏感诊断' in text:
            credentials={'api_key':'fixture-hidden-key','password':'fixture-hidden-password','secret':'fixture-hidden-secret','authorization':'fixture-hidden-auth','db_url':'fixture-hidden-db','dsn':'fixture-hidden-dsn','system_prompt':'fixture-hidden-system','user_prompt':'fixture-hidden-user','full_prompt':'fixture-hidden-full','catalog':{'tables':['fixture-hidden-catalog']}}
            embedded=' '.join(['sk'+'-fixture-hidden-inline','Bearer '+'fixture-hidden-bearer','postgresql:'+ '//reader:fixture-hidden-password@localhost/db'])
            return self.emit(envelope(answer='敏感诊断保护测试。',table=[{'ratio':'0.123456','amount':'12345678901234567890.123456789'}],metadata={'nlu':{'patches':[{'original':'测试','replacement':'规范名称','context':credentials,'note':embedded,'long_text':'x'*5000}],'mentions':[]},'result_format':{'ratio':{'kind':'percentage','scale':100}}},steps=[{'name':'诊断脱敏验证','status':'ok','latency_ms':1,'input_summary':credentials,'output_summary':{'note':embedded,'safe_count':35}}]))
        if '默认切换' in text:return self.emit(envelope(answer='按已授权默认查询，可切换统计口径。',metadata={'clarify':{'switch':{'clarification_id':'card-test-1','intent_version':3,'question':'切换统计口径','options':[{'id':'country-france','label':'按法国'}]}}}))
        if '百分比' in text:return self.emit(envelope(answer='原始比例按显式格式展示。',table=[{'ratio':'0.123456','scaled':'12.3456','amount':'12345678901234567890.123456789'}],metadata={'result_columns':['ratio','scaled','amount'],'result_format':{'ratio':{'kind':'percentage','scale':100},'scaled':{'kind':'percentage','scale':1}}}))
        if '选表' in text:return self.emit(envelope(answer='按真实外键选择相关表。',metadata={'schema_linker':{'selected_tables':['sales.salesorderheader','sales.salesorderdetail'],'reasons':{'sales.salesorderheader':['销售金额依据'],'sales.salesorderdetail':['明细关联依据']},'join_paths':[{'from':'salesorderheader','to':'salesorderdetail','key':'salesorderid'}],'excluded_tables':{'sales.currency':'无关币种表'},'disconnected_components':[['sales.salesorderheader'],['sales.salesorderdetail']]}}))
        if '澄清' in text:return self.emit(envelope(status='NEEDS_CLARIFICATION',answer='请选择国家。',sql=None,table=None,clarification={'clarification_id':'card-test-1','intent_version':3,'resume_supported':True,'question':'请选择要补充的国家','options':[{'id':'country-france','label':'法国'}]}))
        if '空集' in text:return self.emit(envelope(status='EMPTY_RESULT',answer='没有匹配记录。',table=[],metadata={'result_columns':['customer_id']}))
        if '空值' in text:return self.emit(envelope(answer='合计为NULL。',table=[{'total_amount':None}],metadata={'result_columns':['total_amount']}))
        if '精度' in text:return self.emit(envelope(answer='保留原始金额字符串。',table=[{'amount':'12345678901234567890.123456789'}],metadata={'result_columns':['amount']}))
        if '保留别名' in text:return self.emit(envelope(answer='结果列名与内部键不会相互覆盖。',table=[{'__ui_key':'original-value'}],metadata={'result_columns':['__ui_key']}))
        if '截断' in text:return self.emit(envelope(metadata={'result_columns':['customer_count'],'truncated':True}))
        if 'HTTP失败' in text:return self.emit({'detail':'受控接口拒绝请求'},422)
        return self.emit(envelope())
    def log_message(self,*args):pass
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=35170);args=parser.parse_args();server=ThreadingHTTPServer(('127.0.0.1',args.port),MockHandler)
    print(f'Controlled fixture: http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
