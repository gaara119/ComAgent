#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$project_dir"
project_python="$project_dir/.venv/bin/python"
if [[ ! -x "$project_python" ]]; then
    project_python="$project_dir/.venv/Scripts/python.exe"
fi
if [[ ! -f "$project_python" ]]; then
    printf '%s\n' 'Missing project .venv; follow README.' >&2
    exit 1
fi
api_port="${API_PORT:-8000}"
ui_port="${UI_PORT:-8501}"
export QA_API_BASE_URL="http://127.0.0.1:$api_port"
export DEMO_UI_PORT="$ui_port"
mkdir -p -- .runtime
if ! "$project_python" - <<'PY'
import json, os, urllib.request
try:
    with urllib.request.urlopen(os.environ['QA_API_BASE_URL'] + '/health', timeout=3) as response:
        value = json.load(response)
    raise SystemExit(0 if value.get('status') == 'ok' and value.get('service') == 'comagent' and value.get('capabilities', {}).get('document_upload') else 1)
except Exception:
    raise SystemExit(1)
PY
then
    "$project_python" - <<'PY'
import os, socket
from urllib.parse import urlsplit
try:
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', urlsplit(os.environ['QA_API_BASE_URL']).port))
except OSError:
    raise SystemExit('API port is occupied. Select another API_PORT; no process was stopped.')
PY
    nohup "$project_python" -m uvicorn api.main:app --host 127.0.0.1 --port "$api_port" > .runtime/api.stdout.log 2> .runtime/api.stderr.log &
    printf '%s\n' "$!" > .runtime/api.pid
    "$project_python" - <<'PY'
import json, os, time, urllib.request
for attempt in range(20):
    try:
        with urllib.request.urlopen(os.environ['QA_API_BASE_URL'] + '/health', timeout=3) as response:
            value = json.load(response)
        if value.get('status') == 'ok' and value.get('service') == 'comagent' and value.get('capabilities', {}).get('document_upload'):
            break
    except Exception:
        pass
    time.sleep(0.5)
else:
    raise SystemExit('API did not become ready. See .runtime/api.stderr.log.')
PY
fi
"$project_python" - <<'PY'
import os, socket
try:
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', int(os.environ['DEMO_UI_PORT'])))
except (ValueError, OSError):
    raise SystemExit('UI port is invalid or occupied. Select another UI_PORT; no process was stopped.')
PY
printf 'API: %s/docs\nDemo: http://127.0.0.1:%s\n' "$QA_API_BASE_URL" "$ui_port"
exec "$project_python" frontend-workbench/run_ui.py --api-url "$QA_API_BASE_URL" --port "$ui_port"
