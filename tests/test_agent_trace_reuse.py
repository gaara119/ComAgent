"""Reuse actual traces without replaying requests or counting nested spans twice."""
import hashlib
import json
from pathlib import Path

import pytest

from benchmarks.agent240.traces import canonical, load, scope_inventory, stage_timing


def test_nested_stage_timings_are_not_added_to_model_and_sql():
    trace = {'attempts': [{'steps': [
        {'name': 'sql_gen', 'latency_ms': 500},
        {'name': 'llm', 'latency_ms': 450, 'input_summary': {'attempt': 1}},
        {'name': 'sql_exec', 'latency_ms': 25}]}]}
    record = {'attempts': [{'provider_attempts': []}]}
    values = stage_timing(trace, record)
    assert values['model_ms'] == 450
    assert values['SQL_ms'] == 25
    assert values['retrieval_ms'] is None


def test_missing_trace_is_not_zero_retrieval_or_zero_model_time():
    values = stage_timing(None, {})
    assert values['status'] == 'not_verified'
    assert values['model_ms'] is None and values['retrieval_ms'] is None


def test_B_contexts_preserved_and_turn_order_checked():
    cases = {str(i): {'suite': 'legacy40', 'case_id': 'B-01', 'group': 'B',
                      'turn_index': i, 'source_context': {'text': 'full original body'}} for i in (1, 2)}
    result = scope_inventory(cases)
    assert result['B_conversations'][0]['full_context_preserved']
    cases['2']['source_context']['text'] = 'trimmed'
    with pytest.raises(ValueError, match='full context'):
        scope_inventory(cases)


def test_trace_loader_rejects_stale_prediction_binding(tmp_path):
    record = {'id': 'x', 'arm': 'BASE', 'raw_response': {'answer': 'new'}, 'attempts': []}
    records_path = tmp_path / 'records.jsonl'
    records_path.write_text(json.dumps(record), 'utf-8')
    trace = tmp_path / 'trace.jsonl'
    trace.write_text(json.dumps({'id': 'x', 'arm': 'BASE', 'prediction_sha256': canonical({'answer': 'old'}), 'attempts': []}), 'utf-8')
    manifest = {'schema': 'actual-agent-trace-sidecar-v1',
                'records_sha256': hashlib.sha256(records_path.read_bytes()).hexdigest(),
                'sha256': hashlib.sha256(trace.read_bytes()).hexdigest()}
    trace.with_suffix('.manifest.json').write_text(json.dumps(manifest), 'utf-8')
    with pytest.raises(ValueError, match='exact prediction'):
        load(trace, [record], records_path)


def test_real_original_240_sidecar_has_all_498_attempts_and_755_model_spans():
    from benchmarks.agent240.evaluate import load_bundle
    root = Path(__file__).resolve().parents[1]
    bundle = root / 'benchmarks/agent240/data'
    _, cases, records = load_bundle(bundle)
    traces = load(bundle / 'phase-traces.jsonl', records, bundle / 'records.jsonl')
    assert len(cases) == 240 and len(records) == len(traces) == 480
    assert sum(len(r['attempts']) for r in traces.values()) == 498
    assert sum(stage_timing(traces[r['id'], r['arm']], r)['model_spans'] for r in records) == 755
    assert len(scope_inventory(cases)['B_conversations']) == 6
