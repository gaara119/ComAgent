"""Cryptographically bind external EvalScope scores to the actual Agent run.

No EvalScope dependency is imported by the Agent scorer. This module does not
rename custom metrics or transfer MTEB leaderboard results to Agent questions.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

VERSION = '1.14.1'
OFFICIAL_REVISION = '9d298b839375e735fbbef992b4042e0852d0b8aa'


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_capture(value):
    messages = (value.get('request') or {}).get('messages') or []
    if not messages:
        return None
    try:
        request = json.loads(messages[-1]['content'])
        response = json.loads(value['response']['choices'][0]['message']['content'])
    except (ValueError, KeyError, TypeError, IndexError):
        return None
    if not isinstance(request, dict) or not isinstance(request.get('question'), str) or not isinstance(request.get('evidence'), list):
        return None
    if not request['evidence'] or any(not isinstance(e, dict) or not isinstance(e.get('text'), str) for e in request['evidence']):
        return None
    if not isinstance(response, dict) or not isinstance(response.get('answer'), str):
        return None
    return {'user_input': request['question'], 'response': response['answer'],
            'retrieved_contexts': [e['text'] for e in request['evidence']],
            'provided_evidence': request['evidence'], 'generation_status': response.get('status')}


def delivered_answers(record):
    payload = record.get('raw_response') or {}
    outputs = ((payload.get('metadata') or {}).get('fusion') or {}).get('actual_outputs') or {}
    return {payload.get('answer', ''), *(v.get('answer', '') for v in outputs.values())}


def bounded_path(parent, relative):
    path = (parent / relative).resolve()
    if not path.is_relative_to(parent.resolve()):
        raise ValueError('External evidence path escapes its result directory')
    return path


def _verify_sample(sample, record, root):
    if sample['prediction_sha256'] != canonical_hash(record['raw_response']):
        raise ValueError('EvalScope prediction hash differs from Agent response')
    source = record.get('source') or {}
    if sample['run_sha256'] != canonical_hash(source):
        raise ValueError('EvalScope run/configuration binding differs')
    provider = next((p for a in record['attempts'] for p in a.get('provider_attempts', [])
                     if p['capture_id'] == sample['capture_id'] and p['source_sha256'] == sample['capture_sha256']), None)
    if provider is None:
        raise ValueError('Generation capture is not from this Agent run')
    capture_path = bounded_path(root, sample['capture_path'])
    if file_hash(capture_path) != sample['capture_sha256']:
        raise ValueError('Generation capture changed')
    capture = json.loads(capture_path.read_text('utf-8'))
    content = read_capture(capture)
    if content is None or content['response'] not in delivered_answers(record):
        raise ValueError('EvalScope sample is not a delivered RAG subtask')
    if (sample['question_sha256'] != canonical_hash(content['user_input']) or
            sample['evidence_sha256'] != canonical_hash(content['provided_evidence']) or
            sample['rag_response_sha256'] != canonical_hash(content['response'])):
        raise ValueError('EvalScope question/context/answer binding changed')
    return content


def load_results(path, cases, records):
    """Return {(Agent ID, arm): bound external RAG metrics} for Agent reports.

    Only a real EvalScope RAGAS per-sample score file, with the exact actual
    generation captures, is accepted. MTEB results need a separate matching
    retrieval run/qrel adapter and are not accepted by this answer-score join.
    """
    path = Path(path)
    payload = json.loads(path.read_text('utf-8'))
    if payload.get('schema') != 'evalscope-agent-binding-v1' or payload.get('framework') != 'EvalScope':
        raise ValueError('Not an EvalScope Agent binding result')
    if payload.get('evalscope_version') != VERSION or payload.get('tool') != 'RAGAS':
        raise ValueError('Unsupported or mismatched EvalScope version/tool')
    raw_spec = payload['official_result']
    raw_path = bounded_path(path.parent, raw_spec['path'])
    if file_hash(raw_path) != raw_spec['sha256']:
        raise ValueError('Official EvalScope result hash mismatch')
    official_rows = json.loads(raw_path.read_text('utf-8'))
    by_key = {(r['id'], r['arm']): r for r in records}
    seen, seen_rows, output = set(), set(), {}
    allowed = {'faithfulness', 'answer_relevancy', 'context_precision', 'context_recall', 'answer_correctness'}
    for sample in payload['samples']:
        key = sample['id'], sample['arm']
        if sample['id'] not in cases or key not in by_key or sample['sample_id'] in seen:
            raise ValueError('Unknown/duplicate EvalScope sample')
        seen.add(sample['sample_id'])
        content = _verify_sample(sample, by_key[key], path.parent)
        row_index = sample['official_row_index']
        if type(row_index) is not int or not 0 <= row_index < len(official_rows) or row_index in seen_rows:
            raise ValueError('Invalid or reused official EvalScope row')
        seen_rows.add(row_index)
        row = official_rows[row_index]
        if row.get('user_input') != content['user_input'] or row.get('response') != content['response'] or row.get('retrieved_contexts') != content['retrieved_contexts']:
            raise ValueError('Official EvalScope row does not match the actual RAG input/output')
        metrics, metric_statuses = {}, {}
        for name in sample['metric_names']:
            if name not in allowed:
                raise ValueError('Unsupported external metric; no custom renaming')
            value = row.get(name)
            if type(value) is float and math.isnan(value):
                # Some official serializers preserve NaN rather than JSON null.
                # Keep raw framework bytes and hashes intact; the report layer
                # treats that observation as unscored, never as zero or a pass.
                metric_statuses[name] = 'framework_nonfinite_score'
                value = None
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1):
                raise ValueError('Malformed EvalScope metric value')
            metrics[name] = value
        current = output.setdefault(key, {'source': 'EvalScope', 'tool': 'RAGAS',
            'evalscope_version': VERSION, 'scope': 'delivered_RAG_subtask', 'samples': [],
            'retrieval_recall_at_k': None})
        current['samples'].append({'sample_id': sample['sample_id'], 'metrics': metrics,
                                   'metric_statuses': metric_statuses,
                                   'capture_sha256': sample['capture_sha256'],
                                   'status': 'verified' if any(v is not None for v in metrics.values()) else 'not_verified'})
    if payload.get('judge_evidence'):
        for spec in payload['judge_evidence'].values():
            linked = bounded_path(path.parent, spec['path'])
            if file_hash(linked) != spec['sha256']:
                raise ValueError('EvalScope judge ledger/execution evidence hash mismatch')
    return output
