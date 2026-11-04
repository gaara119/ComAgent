"""HTTP forwarding guard shared by all RAGAS retries and repair calls."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from pathlib import Path
from threading import Lock, BoundedSemaphore, Thread, Event
from time import monotonic, perf_counter

import httpx


class BudgetStop(RuntimeError):
    pass


class PhysicalBudget:
    def __init__(self, directory, *, max_calls=120, seconds=1200, no_send_tail=120, concurrency=4, start_on_first_call=False):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.max_calls = max_calls
        self.seconds = seconds
        self.start_on_first_call = start_on_first_call
        self.deadline = float('inf') if start_on_first_call else monotonic() + seconds
        self.no_send_tail = no_send_tail
        self.lock = Lock()
        self.semaphore = BoundedSemaphore(concurrency)
        self.records = []
        self.stop_reason = None
        self.probe_done = Event()
        # A framework import/startup failure still needs an explicit zero-call
        # receipt; absence of a ledger must never be interpreted as zero usage.
        self.persist()

    def reserve(self, body):
        # Exactly one real connectivity probe may be in flight until settled.
        while True:
            with self.lock:
                pending_probe = bool(self.records) and self.records[0]['status'] == 'reserved'
                if not pending_probe:
                    if not self.records and self.start_on_first_call:
                        self.deadline = monotonic() + self.seconds
                    if self.stop_reason or len(self.records) >= self.max_calls or monotonic() >= self.deadline - self.no_send_tail:
                        self.stop_reason = self.stop_reason or 'call_or_deadline_limit'
                        self.persist()
                        raise BudgetStop(self.stop_reason)
                    item = {'physical_call': len(self.records) + 1, 'status': 'reserved',
                            'request_model': body.get('model'), 'request': body,
                            'reserved_utc': datetime.now(timezone.utc).isoformat(),
                            'missing_usage': True, 'input_tokens_conservative_reserve': max(40000, len(json.dumps(body, ensure_ascii=False).encode()) + 1024),
                            'output_tokens_conservative_reserve': 4096}
                    self.records.append(item)
                    self.persist()
                    return item
            if not self.probe_done.wait(timeout=62):
                raise BudgetStop('first_probe_not_settled')

    def settle(self, record, *, status, response=None, elapsed_ms=None, error_type=None):
        with self.lock:
            usage = (response or {}).get('usage') or {}
            known = all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('prompt_tokens', 'completion_tokens'))
            if known and 'total_tokens' in usage:
                known = type(usage['total_tokens']) is int and usage['total_tokens'] == usage['prompt_tokens'] + usage['completion_tokens']
            record.update(status=status, response=response, elapsed_ms=elapsed_ms, error_type=error_type,
                          missing_usage=not known, usage=usage,
                          input_tokens_conservative_reserve=0 if known else record['input_tokens_conservative_reserve'],
                          output_tokens_conservative_reserve=0 if known else record['output_tokens_conservative_reserve'])
            if record['physical_call'] == 1 and status != 'completed':
                self.stop_reason = 'first_actual_probe_failed_no_further_upstream_calls'
            if record['physical_call'] == 1:
                self.probe_done.set()
            self.persist()

    def persist(self):
        value = {'kind': 'actual_RAGAS_judge_calls_separate_from_Agent_predictions',
                 'max_physical_calls': self.max_calls, 'physical_calls': len(self.records),
                 'stop_reason': self.stop_reason, 'phase_starts_on_first_actual_call': self.start_on_first_call, 'records': self.records}
        (self.directory / 'budget-ledger.json').write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


@contextmanager
def guarded_endpoint(budget, *, api_key, upstream='https://api.deepseek.com'):
    if upstream.rstrip('/') not in {'https://api.deepseek.com', 'https://api.deepseek.com/v1'}:
        raise ValueError('Only the approved DeepSeek endpoint is permitted')
    client = httpx.Client(timeout=60, trust_env=False)

    def redact(value):
        if isinstance(value, str):
            return re.sub(r'sk-[A-Za-z0-9]{12,}', '[REDACTED]', value.replace(api_key, '[REDACTED]'))
        if isinstance(value, dict):
            return {k: redact(v) for k, v in value.items()}
        if isinstance(value, list):
            return [redact(v) for v in value]
        return value

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, payload):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Provider settlement remains recorded after caller timeout.

        def do_POST(self):
            if self.path.rstrip('/') != '/v1/chat/completions':
                self.reply(400, {'error': {'message': 'Only chat completions are enabled; embeddings are unused for Faithfulness.'}})
                return
            try:
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
                if body.get('model') != 'deepseek-flash' or body.get('stream'):
                    raise ValueError('Unexpected model or stream setting')
                body['max_tokens'] = min(body.get('max_tokens') or body.get('max_completion_tokens') or 4096, 4096)
                body.pop('max_completion_tokens', None)
                with budget.semaphore:
                    item = budget.reserve(body)
                    started = perf_counter()
                    try:
                        response = client.post(upstream.rstrip('/') + '/chat/completions', json=body,
                                               headers={'Authorization': 'Bearer ' + api_key})
                        try:
                            payload = redact(response.json())
                        except ValueError:
                            payload = {'error': {'message': 'non_JSON_upstream_response'}}
                        succeeded = response.status_code == 200 and isinstance(payload, dict) and bool(payload.get('choices')) and not payload.get('error')
                        budget.settle(item, status='completed' if succeeded else 'upstream_error',
                                      response=payload, elapsed_ms=(perf_counter() - started) * 1000)
                        self.reply(response.status_code, payload)
                    except Exception as exc:
                        budget.settle(item, status='transport_error', error_type=type(exc).__name__,
                                      elapsed_ms=(perf_counter() - started) * 1000)
                        self.reply(502, {'error': {'message': 'upstream_transport_error'}})
            except BudgetStop:
                self.reply(429, {'error': {'message': 'Shared physical call/time budget stopped'}})
            except (ValueError, TypeError, json.JSONDecodeError):
                self.reply(400, {'error': {'message': 'Invalid guarded request'}})

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1'
    finally:
        server.shutdown()
        server.server_close()
        client.close()
