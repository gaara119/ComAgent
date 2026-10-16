import argparse,importlib.util,json,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
mock=load('controlled_mock',ROOT/'tests'/'mock_api.py');ui=load('ui_server',ROOT/'run_ui.py')
parser=argparse.ArgumentParser();parser.add_argument('--api-port',type=int,default=35170);parser.add_argument('--ui-port',type=int,default=35171);args=parser.parse_args()
api=ThreadingHTTPServer(('127.0.0.1',args.api_port),mock.MockHandler)
server=ThreadingHTTPServer(('127.0.0.1',args.ui_port),ui.make_handler(f'http://127.0.0.1:{args.api_port}'))
for value in [api,server]:value.daemon_threads=True
threading.Thread(target=api.serve_forever,daemon=True).start()
print(json.dumps({'ui':f'http://127.0.0.1:{args.ui_port}','controlled_fixture_api':f'http://127.0.0.1:{args.api_port}','real_model_calls':0,'real_database_queries':0}),flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close();api.shutdown();api.server_close()
