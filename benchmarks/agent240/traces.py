"""Export/reuse actual initial and supplement traces; never invoke the Agent.

The portable final-response bundle remains unchanged. This sidecar adds the
already saved initial/supplement request bodies, states and stage spans.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from benchmarks.agent240.metrics import percentile


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export(bundle, project_root, output):
    bundle, project_root, output = Path(bundle), Path(project_root).resolve(), Path(output)
    if output.exists() or output.with_suffix('.manifest.json').exists():
        raise ValueError('Choose a fresh sidecar path')
    source_manifest = json.loads((bundle / 'manifest.json').read_text('utf-8'))
    declared = {r['path']: r['sha256'] for r in source_manifest['source_files']}
    records = [json.loads(s) for s in (bundle / 'records.jsonl').read_text('utf-8').splitlines() if s.strip()]
    rows = []
    for record in records:
        exported = []
        for attempt in record['attempts']:
            name, expected = attempt['source_path'], attempt['source_sha256']
            source = (project_root / name).resolve()
            if not source.is_relative_to(project_root) or declared.get(name) != expected or file_hash(source) != expected:
                raise ValueError('Source attempt missing, changed or outside declared project: ' + name)
            original = json.loads(source.read_text('utf-8-sig'))
            response = original['response']
            metadata = response.get('metadata') or {}
            exported.append({
                'kind': attempt['kind'], 'request': original.get('request'),
                'http_status': original.get('http_status'), 'elapsed_ms': original.get('elapsed_ms'),
                'sent_utc': original.get('sent_utc'),
                'status': response.get('status'), 'steps': response.get('steps', []),
                'intent': response.get('intent'), 'clarification': response.get('clarification'),
                'sql': response.get('sql'), 'answer': response.get('answer'),
                'state_metadata': {k: metadata[k] for k in ('clarify', 'session_context', 'reference_clock') if k in metadata},
                'source_path': name, 'source_sha256': expected})
        rows.append({'id': record['id'], 'arm': record['arm'],
                     'prediction_sha256': canonical(record['raw_response']), 'attempts': exported})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes((''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)).encode())
    manifest = {'schema': 'actual-agent-trace-sidecar-v1', 'records_sha256': file_hash(bundle / 'records.jsonl'),
                'file': output.name, 'sha256': file_hash(output), 'predictions': len(rows),
                'actual_question_requests': sum(len(r['attempts']) for r in rows),
                'new_API_calls': 0, 'new_SQL_executions': 0,
                'source': 'existing initial/supplement HTTP envelopes; every source SHA checked',
                'context_policy': 'B full text remains in dataset.json; source ingest ACK is separate in bundle manifest'}
    output.with_suffix('.manifest.json').write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode())
    return manifest


def load(path, records, records_path):
    path = Path(path)
    manifest = json.loads(path.with_suffix('.manifest.json').read_text('utf-8'))
    if manifest['schema'] != 'actual-agent-trace-sidecar-v1' or manifest.get('file', path.name) != path.name or manifest['sha256'] != file_hash(path) or manifest['records_sha256'] != file_hash(records_path):
        raise ValueError('Trace sidecar hash/version differs from prediction bundle')
    predictions = {(r['id'], r['arm']): r for r in records}
    result = {}
    for line in path.read_text('utf-8').splitlines():
        row = json.loads(line)
        key = row['id'], row['arm']
        if key not in predictions or key in result or row['prediction_sha256'] != canonical(predictions[key]['raw_response']):
            raise ValueError('Trace sidecar does not bind to this exact prediction')
        if len(row['attempts']) != len(predictions[key]['attempts']):
            raise ValueError('Trace attempt count differs')
        for actual, saved in zip(row['attempts'], predictions[key]['attempts']):
            if actual['source_sha256'] != saved['source_sha256'] or actual['kind'] != saved['kind']:
                raise ValueError('Trace attempt identity mismatch')
        result[key] = row
    return result


def stage_timing(trace, record):
    if trace is None:
        return {'status': 'not_verified', 'reason': 'complete attempt traces unavailable',
                'model_ms': None, 'SQL_ms': None, 'retrieval_ms': None}
    steps = [s for a in trace['attempts'] for s in a.get('steps', [])]
    models = [s for s in steps if s.get('name') == 'llm']
    sql = [s for s in steps if s.get('name') == 'sql_exec']

    def total(items):
        values = [s.get('latency_ms') for s in items]
        return sum(values) if all(type(v) in (float, int) and math.isfinite(v) and v >= 0 for v in values) else None

    retries = [s for s in models if type(s.get('input_summary', {}).get('attempt')) is int and s['input_summary']['attempt'] > 1]
    retry_ids = {Path(s.get('output_summary', {}).get('provider_capture', '')).name for s in retries}
    providers = {p['capture_id']: p for a in record['attempts'] for p in a.get('provider_attempts', [])}
    retry_providers = [providers[i] for i in retry_ids if i in providers]
    from benchmarks.agent240.metrics import provider_totals
    cost = provider_totals([{'provider_attempts': retry_providers, 'provider_collection_complete': len(retry_providers) == len(retries),
                             'no_model_call_verified': not retries}])
    return {'status': 'verified_existing_attempt_traces', 'model_ms': total(models),
            'SQL_ms': total(sql) if sql else None, 'retrieval_ms': None,
            'retrieval_status': 'not_verified; original trace has no separately instrumented retrieval span',
            'model_spans': len(models), 'SQL_spans': len(sql), 'model_retry_spans': len(retries),
            'model_retry_usage': cost,
            'SQL_repair_events': sum(s.get('name') == 'sql_repair' for s in steps),
            'RAG_regeneration_events': sum(s.get('name') == 'rag_regenerate' for s in steps),
            'clock_and_state_attempts': len(trace['attempts']),
            'timing_boundary': 'model=sum llm spans; SQL=sum sql_exec spans; not additive to enclosing planner/generator spans or HTTP wall time'}


def summarize_timings(rows):
    result = {}
    for key in ('model_ms', 'SQL_ms', 'retrieval_ms'):
        values = [r.get('stage_timing', {}).get(key) for r in rows]
        values = [v for v in values if v is not None]
        result[key] = {'known': len(values), 'p50': percentile(values, 50), 'p90': percentile(values, 90)}
    result['model_retry_spans'] = sum(r.get('stage_timing', {}).get('model_retry_spans', 0) for r in rows)
    retry_ledgers = [r.get('stage_timing', {}).get('model_retry_usage', {}) for r in rows]
    retry_cost = {}
    for name in ('physical_calls', 'input_tokens', 'output_tokens', 'cache_hit_tokens', 'cache_miss_tokens'):
        known = [u[name] for u in retry_ledgers if type(u.get(name)) is int]
        retry_cost[name] = sum(known) if len(known) == len(rows) else None
        retry_cost[name + '_observed_sum'] = sum(known)
    result['model_retry_usage'] = retry_cost
    result['SQL_repair_events'] = sum(r.get('stage_timing', {}).get('SQL_repair_events', 0) for r in rows)
    result['RAG_regeneration_events'] = sum(r.get('stage_timing', {}).get('RAG_regeneration_events', 0) for r in rows)
    return result


def scope_inventory(cases):
    """Verify supplied B text and turn grouping without changing or trimming it."""
    from collections import Counter, defaultdict
    groups = defaultdict(list)
    for case in cases.values():
        if case.get('group') == 'B':
            groups[case['suite'], case['case_id']].append(case)
    conversations = []
    for (suite, case_id), items in sorted(groups.items()):
        turns = [c['turn_index'] for c in items]
        bodies = [(c.get('source_context') or {}).get('text') for c in items]
        full_text = bool(bodies and all(isinstance(t, str) and t for t in bodies) and len(set(bodies)) == 1)
        ordered = turns == sorted(turns) and len(set(turns)) == len(turns)
        if not full_text or not ordered:
            raise ValueError('B full context or supplied turn order inconsistent')
        conversations.append({'suite': suite, 'case_id': case_id, 'questions': len(items),
                              'turn_indices': turns, 'full_text_characters': len(bodies[0]),
                              'full_text_sha256': hashlib.sha256(bodies[0].encode()).hexdigest(),
                              'full_context_preserved': True, 'question_order_preserved': True})
    return {'by_suite_group': dict(Counter(c['suite'] + '/' + c['group'] for c in cases.values())),
            'B_conversations': conversations, 'heldout_loaded': False,
            'retired_32_loaded': False}


def export_run_configurations(bundle, project_root, output):
    """Keep sanitized actual feature/model settings, never .env or DB credentials."""
    bundle, root, output = Path(bundle), Path(project_root).resolve(), Path(output)
    if output.exists():
        raise ValueError('Choose a fresh configuration evidence path')
    records = [json.loads(s) for s in (bundle / 'records.jsonl').read_text('utf-8').splitlines() if s.strip()]
    configs = {}
    allowed = {'model', 'llm_temperature', 'llm_temperature_effective', 'llm_thinking', 'llm_max_tokens',
               'llm_timeout_seconds', 'llm_call_max_attempts', 'llm_request_max_attempts', 'statement_timeout_ms',
               'max_rows', 'component_mode', 'cumulative_stage', 'nlu_enabled', 'link_grounding_enabled',
               'semantic_gate_enabled', 'clarify_grounding_enabled', 'clarify_state_enabled', 'aw_schema_mode',
               'aw_schema_pruning_enabled', 'typed_sql_compiler_enabled', 'schema_recall_enhanced',
               'rag_retrieval_strategy', 'rag_cache_enabled', 'sql_prompt_sha256', 's1_question_rewrite_enabled'}
    for record in records:
        key = record['suite'] + '/' + record['configuration']
        if key in configs:
            continue
        source = record.get('source') or {}
        health_path = (root / source['path'] / 'health-before.json').resolve()
        if not health_path.is_relative_to(root) or not health_path.exists():
            configs[key] = {'status': 'not_verified', 'source_snapshot': source}
            continue
        health = json.loads(health_path.read_text('utf-8-sig'))
        configs[key] = {'status': 'recorded_historical_health', 'actual_settings': {k: health[k] for k in sorted(allowed) if k in health},
                        'source_path': health_path.relative_to(root).as_posix(), 'source_sha256': file_hash(health_path),
                        'source_snapshot': source}
    output.write_bytes((json.dumps({'schema': 'actual-run-settings-v1', 'configurations': configs,
                       'records_sha256': file_hash(bundle / 'records.jsonl'),
                       'boundary': 'Historical recorded configuration, not a current service readiness check; original source snapshots remain archived.'}, ensure_ascii=False, indent=2) + '\n').encode())
    return configs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.bundle, args.source_root, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
