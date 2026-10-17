"""Serve the packaged UI and proxy the project's loopback FastAPI. Standard library only."""
from __future__ import annotations
import argparse
import json
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parent
DIST = ROOT / 'dist'
MAX_BODY = 1024 * 1024

def api_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme not in {'http','https'} or parts.hostname not in {'127.0.0.1','localhost','::1'}:
        raise argparse.ArgumentTypeError('API must be a loopback http(s) URL.')
    if parts.username or parts.password or parts.query or parts.fragment or parts.path not in {'','/'}:
        raise argparse.ArgumentTypeError('API URL cannot contain credentials, paths or query strings.')
    try:
        if parts.port is not None and not 1 <= parts.port <= 65535: raise ValueError()
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Invalid API port.') from exc
    return value.rstrip('/')

def allowed_api(path: str, method: str) -> bool:
    decoded = unquote(unquote(path)).replace('\\', '/')
    if any(part in {'.', '..'} for part in decoded.split('/')):
        return False
    if method == 'POST': return path in {'/api/chat','/api/context'}
    return method in {'GET','HEAD'} and (path in {'/health', '/api/documents'} or bool(re.fullmatch(r'/api/documents/[^/\\]+/(?:file|pages/[1-9][0-9]*)', decoded)))

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(req.full_url, 502, 'UI proxy does not follow redirects.', headers, fp)

def make_handler(upstream_url: str):
    upstream_url = api_url(upstream_url)
    # This proxy connects only to the configured local API, ignoring OS HTTP proxy settings.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args,directory=str(DIST),**kwargs)

        def json_response(self, status: int, value: dict):
            content=json.dumps(value,ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(content)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers()
            if self.command != 'HEAD': self.wfile.write(content)

        def json_error(self, status: int, detail: str):
            return self.json_response(status, {'detail': detail})

        def proxy(self):
            parts=urlsplit(self.path)
            if not allowed_api(parts.path,self.command):
                return self.json_error(404,'此UI代理未开放该接口。')
            body=None
            if self.command == 'POST':
                try: length=int(self.headers.get('Content-Length','0'))
                except ValueError: return self.json_error(400,'无效请求长度。')
                if length < 1 or length > MAX_BODY: return self.json_error(413,'请求体为空或超过1MB。')
                if self.headers.get('Content-Type','').split(';')[0].strip() != 'application/json':
                    return self.json_error(415,'问答请求必须使用application/json。')
                body=self.rfile.read(length)
            headers={'Accept':self.headers.get('Accept','application/json')}
            if body is not None: headers['Content-Type']='application/json'
            if self.headers.get('Range'): headers['Range']=self.headers['Range']
            target=upstream_url+parts.path+('?' + parts.query if parts.query else '')
            request=Request(target,data=body,headers=headers,method=self.command)
            started=False
            try:
                try: response=opener.open(request,timeout=245)
                except HTTPError as exc: response=exc
                with response:
                    self.send_response(response.status)
                    for name in ['Content-Type','Content-Length','Content-Disposition','Content-Range','Accept-Ranges','ETag']:
                        if response.headers.get(name): self.send_header(name,response.headers[name])
                    self.send_header('Cache-Control','no-store')
                    self.send_header('X-Content-Type-Options','nosniff')
                    self.end_headers()
                    started=True
                    if self.command != 'HEAD':
                        while chunk := response.read(64*1024): self.wfile.write(chunk)
            except (URLError,TimeoutError,OSError):
                if started:
                    # A disconnected browser must not turn an already-started response into another response.
                    return
                self.json_error(503,'无法连接原项目API。请先启动FastAPI，并确认端口设置。')

        def static_allowed(self):
            try:
                target=(DIST/unquote(unquote(urlsplit(self.path).path)).replace('\\','/').lstrip('/')).resolve()
                return target.is_relative_to(DIST.resolve())
            except (OSError,ValueError): return False

        def do_GET(self):
            path=urlsplit(self.path).path
            if path == '/ui-health':
                return self.json_response(200, {'status':'ok','service':'comagent-workbench-ui','version':'1.1.0','api_url':upstream_url})
            if path == '/health' or path.startswith('/api/'): return self.proxy()
            if not self.static_allowed(): return self.json_error(403,'文件路径不允许。')
            return super().do_GET()

        def do_HEAD(self):
            path=urlsplit(self.path).path
            if path == '/ui-health':
                return self.json_response(200, {'status':'ok','service':'comagent-workbench-ui','version':'1.1.0','api_url':upstream_url})
            if path == '/health' or path.startswith('/api/'): return self.proxy()
            if not self.static_allowed(): return self.json_error(403,'文件路径不允许。')
            return super().do_HEAD()

        def do_POST(self): return self.proxy()

        def end_headers(self):
            self.send_header('X-Content-Type-Options','nosniff')
            super().end_headers()

        def list_directory(self,path): return self.json_error(403,'不提供目录浏览。')
    return Handler

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-url',type=api_url,default='http://127.0.0.1:8000')
    parser.add_argument('--port',type=int,default=8501)
    args=parser.parse_args()
    if not 1 <= args.port <= 65535: parser.error('Invalid UI port.')
    if not (DIST/'index.html').is_file(): parser.error('dist/index.html is missing; restore the package or run the frontend build.')
    try: server=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(args.api_url))
    except OSError as exc:
        parser.exit(1,f'Cannot bind UI port {args.port}. Choose another --port.\n{exc}\n')
    server.daemon_threads=True
    print(f'ComAgent UI: http://127.0.0.1:{server.server_port}',flush=True)
    print(f'Local API: {args.api_url}',flush=True)
    print('Press Ctrl+C to stop this UI. Existing API/Streamlit processes are not stopped.',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == '__main__': main()
