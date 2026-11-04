"""Recover actual RAG inputs from immutable provider captures; no predictions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from benchmarks.agent240.evaluate import load_bundle
from benchmarks.rag_evalscope.bridge import VERSION, OFFICIAL_REVISION, canonical_hash, file_hash, read_capture, delivered_answers


def write(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def export(bundle, project_root, output):
    output, project_root = Path(output), Path(project_root).resolve()
    if output.exists():
        raise ValueError('Output already exists')
    manifest, cases, records = load_bundle(bundle)
    index = {s['sha256']: s['path'] for s in manifest['source_files']}
    samples, skipped, captures = [], [], {}
    for record in records:
        for attempt in record['attempts']:
            for provider in attempt.get('provider_attempts', []):
                relative = index.get(provider['source_sha256'])
                if relative is None:
                    raise ValueError('Actual provider source is missing from immutable manifest')
                path = (project_root / relative).resolve()
                if not path.is_relative_to(project_root) or file_hash(path) != provider['source_sha256']:
                    raise ValueError('Provider source path/hash mismatch')
                content = read_capture(json.loads(path.read_text('utf-8')))
                if content is None:
                    continue
                raw = path.read_bytes()
                if re.search(rb'sk-[A-Za-z0-9]{20,}', raw):
                    raise ValueError('Sensitive key found; capture export blocked')
                capture_name = 'captures/' + provider['capture_id']
                captures[capture_name] = raw
                sample = {'sample_id': record['id'] + '/' + record['arm'] + '/' + provider['capture_id'],
                          'id': record['id'], 'arm': record['arm'], 'suite': cases[record['id']]['suite'],
                          'configuration': record['configuration'],
                          'prediction_sha256': canonical_hash(record['raw_response']),
                          'run_sha256': canonical_hash(record['source']),
                          'capture_id': provider['capture_id'], 'capture_path': capture_name,
                          'capture_sha256': provider['source_sha256'],
                          'question_sha256': canonical_hash(content['user_input']),
                          'evidence_sha256': canonical_hash(content['provided_evidence']),
                          'rag_response_sha256': canonical_hash(content['response']),
                          'eval_input': {k: content[k] for k in ('user_input', 'response', 'retrieved_contexts')},
                          'provided_evidence': content['provided_evidence'],
                          'delivered': content['response'] in delivered_answers(record),
                          'generation_status': content['generation_status'],
                          'evidence_origin': 'actual_provider_request_not_filtered_final_citations'}
                samples.append(sample)
    output.mkdir(parents=True)
    for name, raw in captures.items():
        p = output / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    eligible = [s for s in samples if s['delivered'] and s['generation_status'] == 'SUCCEEDED']
    write(output / 'ragas-input.json', [s['eval_input'] for s in eligible])
    write(output / 'samples.json', eligible)
    write(output / 'all-generation-attempts.json', samples)
    receipt = {'evalscope_version': VERSION, 'official_revision': OFFICIAL_REVISION,
               'mode': 'actual_inputs_export_no_API', 'new_model_calls': 0,
               'agent_tasks': 240, 'agent_predictions': 480, 'RAG_generation_attempts': len(samples),
               'delivered_RAG_subtasks': len(eligible),
               'RAGAS': {'status': 'ready_for_explicit_faithfulness_judging',
                         'reference': 'none; Faithfulness is against actual provided context only',
                         'scope': 'RAG subtask, not the mixed Agent final answer'},
               'MTEB': {'status': 'not_ready', 'reason': 'No exhaustive human-reviewed corpus/qrels or frozen full ranked retrieval trace; no synthetic qrels or Gold-selected corpus built'},
               'files': {p.relative_to(output).as_posix(): file_hash(p) for p in output.rglob('*') if p.is_file()}}
    write(output / 'readiness.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path('benchmarks/agent240/data'))
    parser.add_argument('--project-root', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.bundle, args.project_root, args.output), ensure_ascii=False)[:1500])


if __name__ == '__main__':
    main()
