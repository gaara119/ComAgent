import importlib.util,json,sys,threading,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ui_server',ROOT/'run_ui.py');ui=importlib.util.module_from_spec(spec);spec.loader.exec_module(ui)
spec=importlib.util.spec_from_file_location('mock_api',Path(__file__).with_name('mock_api.py'));mock=importlib.util.module_from_spec(spec);spec.loader.exec_module(mock)
def start(handler):
    server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start();return server
def call(port,path,body=None,content_type='application/json'):
    req=Request(f'http://127.0.0.1:{port}{path}',data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':content_type})
    try:resp=urlopen(req,timeout=5)
    except HTTPError as exc:resp=exc
    with resp:return resp.status,resp.headers,resp.read()
class ProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api=start(mock.MockHandler);cls.server=start(ui.make_handler(f'http://127.0.0.1:{cls.api.server_port}'))
    @classmethod
    def tearDownClass(cls):
        for server in [cls.server,cls.api]:server.shutdown();server.server_close()
    def test_health_and_static(self):
        code,_,body=call(self.server.server_port,'/health');self.assertEqual(code,200);self.assertTrue(json.loads(body)['ui_test_fixture'])
        code,_,body=call(self.server.server_port,'/');self.assertEqual(code,200);self.assertIn(b'/assets/app.js',body)
        code,_,body=call(self.server.server_port,'/ui-health');self.assertEqual(code,200);self.assertEqual(json.loads(body)['service'],'comagent-workbench-ui');self.assertNotIn('ui_test_fixture',json.loads(body))
    def test_request_body_and_clarification_version(self):
        payload={'session_id':'controlled-test-session','message':'澄清测试','scope':{'route':'sql','db_id':'chinook','doc_ids':[]}}
        code,_,body=call(self.server.server_port,'/api/chat',payload);self.assertEqual(code,200);card=json.loads(body)['clarification'];self.assertEqual(card['intent_version'],3)
        payload.update(message='法国',clarification_id=card['clarification_id'],intent_version=3,choice_id='country-france')
        code,_,body=call(self.server.server_port,'/api/chat',payload);self.assertEqual(code,200);self.assertEqual(mock.requests[-1],payload)
        payload['intent_version']=1;code,_,_=call(self.server.server_port,'/api/chat',payload);self.assertEqual(code,409)
    def test_local_file_boundary(self):
        for path in ['/../package.json','/%2e%2e/package.json','/%2e%2e/%2e%2e/.env']:
            code,_,_=call(self.server.server_port,path);self.assertIn(code,[403,404])
        code,_,_=call(self.server.server_port,'/');self.assertEqual(code,200)
    def test_proxy_allowlist_and_mime(self):
        code,_,_=call(self.server.server_port,'/__test_requests');self.assertEqual(code,404)
        code,_,_=call(self.server.server_port,'/api/private-admin');self.assertEqual(code,404)
        code,_,_=call(self.server.server_port,'/arbitrary',{});self.assertEqual(code,404)
        code,_,_=call(self.server.server_port,'/api/chat',{},'text/plain');self.assertEqual(code,415)
        code,headers,_=call(self.server.server_port,'/api/documents/doc-test/file');self.assertEqual(code,200);self.assertIn('attachment',headers['Content-Disposition'])
        for path in ['/api/documents/../health','/api/documents/%2e%2e/health','/api/documents/%252e%252e/health','/api/documents/doc-test/private']:
            code,_,_=call(self.server.server_port,path);self.assertEqual(code,404)
    def test_removed_review_routes(self):
        for path in ['/review/index.html','/review/AI-report.md']:
            code,_,_=call(self.server.server_port,path);self.assertEqual(code,404)
    def test_api_unavailable_is_honest_503(self):
        unused=start(mock.MockHandler);port=unused.server_port;unused.shutdown();unused.server_close()
        server=start(ui.make_handler(f'http://127.0.0.1:{port}'))
        try:
            code,_,body=call(server.server_port,'/health');self.assertEqual(code,503);self.assertIn('无法连接',json.loads(body)['detail'])
            code,_,body=call(server.server_port,'/ui-health');self.assertEqual(code,200);self.assertEqual(json.loads(body)['service'],'comagent-workbench-ui')
        finally:server.shutdown();server.server_close()
    def test_upstream_redirects_are_not_followed(self):
        class Redirect(BaseHTTPRequestHandler):
            followed=False
            def do_GET(self):
                if self.path=='/health':
                    self.send_response(302);self.send_header('Location','/redirect-target');self.end_headers()
                else:
                    Redirect.followed=True;self.send_response(200);self.end_headers()
            def log_message(self,*args):pass
        upstream=start(Redirect);server=start(ui.make_handler(f'http://127.0.0.1:{upstream.server_port}'))
        try:
            code,_,_=call(server.server_port,'/health');self.assertEqual(code,502);self.assertFalse(Redirect.followed)
        finally:
            for value in [server,upstream]:value.shutdown();value.server_close()
    def test_only_loopback_targets(self):
        self.assertEqual(ui.api_url('http://127.0.0.1:8000'),'http://127.0.0.1:8000')
        for value in ['https://example.com','http://user:secret@localhost:8000','http://localhost:8000/other']:
            with self.assertRaises(Exception):ui.api_url(value)
if __name__=='__main__':unittest.main()
