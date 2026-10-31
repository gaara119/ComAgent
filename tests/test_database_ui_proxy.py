"""Local proxy contract tests; no real database or model requests."""
import importlib.util
import json
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler

import pytest

spec = importlib.util.spec_from_file_location('registry_ui_proxy', Path(__file__).resolve().parents[1] / 'frontend-workbench/run_ui.py')
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)
ID = 'pg-' + 'a' * 32


@pytest.mark.parametrize('method,path,allowed', [
    ('GET', '/api/databases', True), ('POST', '/api/databases', True),
    ('POST', f'/api/databases/{ID}/refresh', True), ('DELETE', f'/api/databases/{ID}', True),
    ('DELETE', '/api/databases/chinook', False), ('POST', '/api/databases/chinook/refresh', False),
    ('GET', f'/api/databases/{ID}/password', False), ('POST', '/api/databases/../../private', False),
    ('POST', '/api/databases/%252e%252e/refresh', False), ('PUT', '/api/databases', False),
    ('POST', '/api/documents/import', True), ('POST', '/api/documents/text', True),
    ('GET', '/api/documents/imports/' + 'b' * 32, True),
    ('GET', '/api/documents/imports/private', False), ('DELETE', '/api/documents/import', False),
])
def test_database_proxy_allowlist(method, path, allowed):
    assert ui.allowed_api(path, method) is allowed


@pytest.fixture
def proxy(request):
    requests = []
    class Backend(BaseHTTPRequestHandler):
        def handle_request(self):
            length = int(self.headers.get('Content-Length', '0'))
            body = self.rfile.read(length) if length else None
            requests.append({'method': self.command, 'path': self.path, 'body': body})
            result = {'databases': []} if self.command == 'GET' else {'db_id': ID, 'name': 'Local fixture', 'removed': self.command == 'DELETE'}
            content = json.dumps(result).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        do_GET = do_POST = do_DELETE = handle_request
        def log_message(self, *args):
            pass
    backend = ThreadingHTTPServer(('127.0.0.1', 0), Backend)
    server = ThreadingHTTPServer(('127.0.0.1', 0), ui.make_handler(f'http://127.0.0.1:{backend.server_port}',getattr(request,'param',None)))
    for instance in (backend, server):
        threading.Thread(target=instance.serve_forever, daemon=True).start()
    opener = build_opener(ProxyHandler({}))
    def call(method, path, payload=None, headers=None):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(f'http://127.0.0.1:{server.server_port}{path}', data=body, method=method,
                          headers={'Content-Type': 'application/json', **(headers or {})})
        try:
            response = opener.open(request, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.loads(response.read())
    yield call, requests, server.server_port
    for instance in (server, backend):
        instance.shutdown()
        instance.server_close()


def test_registration_refresh_delete_and_list_reach_only_allowed_backend(proxy):
    call, requests, port = proxy
    payload = {'name': 'Fixture', 'host': '127.0.0.1', 'database': 'demo'}
    assert call('GET', '/api/databases')[0] == 200
    assert call('POST', '/api/databases', payload, {'Origin': f'http://127.0.0.1:{port}'})[0] == 200
    assert json.loads(requests[-1]['body']) == payload
    assert call('POST', f'/api/databases/{ID}/refresh')[0] == 200
    assert requests[-1]['method'] == 'POST' and requests[-1]['body'] is None
    assert call('DELETE', f'/api/databases/{ID}')[1]['removed'] is True


def test_document_and_text_uploads_and_job_polling_reach_allowed_backend(proxy):
    call, requests, port = proxy
    assert call('POST', '/api/documents/text', {'title':'Fixture', 'text':'Source text.'})[0] == 200
    assert json.loads(requests[-1]['body'])['text'] == 'Source text.'
    assert call('POST', '/api/documents/import', {'title':'Fixture', 'filename':'a.txt', 'content_base64':'eA=='})[0] == 200
    assert call('GET', '/api/documents/imports/' + 'b' * 32)[0] == 200
    count = len(requests)
    assert call('POST', '/api/documents/text', {'title':'Blocked','text':'Source'}, {'Origin':'https://foreign.example'})[0] == 403
    assert len(requests) == count


@pytest.mark.parametrize('proxy',[18501],indirect=True)
def test_explicit_docker_public_port_preserves_same_origin_boundary(proxy):
    call,requests,_=proxy
    headers={'Host':'127.0.0.1:18501','Origin':'http://127.0.0.1:18501'}
    assert call('POST','/api/documents/text',{'title':'Mapped','text':'Source'},headers)[0]==200
    before=len(requests)
    assert call('POST','/api/documents/text',{'title':'Wrong','text':'Source'},
                {'Host':'127.0.0.1:18502','Origin':'http://127.0.0.1:18502'})[0]==403
    assert len(requests)==before


@pytest.mark.parametrize('headers', [{'Origin': 'https://foreign.example'}, {'Host': 'foreign.example'}, {'Origin': 'http://127.0.0.1:1'}])
def test_foreign_origin_or_host_never_laundered_into_database_management(proxy, headers):
    call, requests, _ = proxy
    assert call('POST', '/api/databases', {'name': 'blocked'}, headers)[0] == 403
    assert requests == []
