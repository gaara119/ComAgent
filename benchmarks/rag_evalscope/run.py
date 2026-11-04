"""Run pinned official EvalScope/RAGAS Faithfulness on saved actual subtasks.

Requires a separate optional EvalScope environment. Default prepares only;
--run-judge explicitly enables the independently budgeted model judge.
"""
from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from time import monotonic, sleep

from benchmarks.rag_evalscope.bridge import VERSION, canonical_hash, file_hash
from benchmarks.rag_evalscope.budget import PhysicalBudget, guarded_endpoint


def write(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def local_caches(directory):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for name, suffix in {'MTEB_CACHE': 'mteb', 'HF_HOME': 'huggingface',
                         'HF_DATASETS_CACHE': 'huggingface/datasets', 'MODELSCOPE_CACHE': 'modelscope',
                         'EVALSCOPE_CACHE': 'evalscope', 'TIKTOKEN_CACHE_DIR': 'tiktoken',
                         'NLTK_DATA': 'nltk'}.items():
        os.environ[name] = str(root / suffix)
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_DATASETS_OFFLINE'] = '1'
    os.environ['RAGAS_DO_NOT_TRACK'] = 'true'


def ragas_config(testset_file, endpoint):
    return {'eval_backend': 'RAGEval', 'work_dir': str(Path(testset_file).parent / 'framework-output'),
            'eval_config': {'tool': 'RAGAS', 'eval': {
        'testset_file': str(testset_file), 'critic_llm': {'model_name': 'deepseek-flash',
            'api_base': endpoint, 'api_key': 'LOCAL_BUDGET_GUARD', 'temperature': 0.0, 'max_tokens': 4096},
        'embeddings': {'model_name_or_path': 'text-embedding-3-small', 'provider': 'openai',
            'api_base': endpoint, 'api_key': 'LOCAL_BUDGET_GUARD'},
        'metrics': ['faithfulness'], 'batch_size': 4, 'raise_exceptions': False}}}


def verify_outbound_scope(inputs):
    audit = json.loads((inputs / 'source-scope-audit.json').read_text('utf-8'))
    for name in ('samples.json', 'ragas-input.json'):
        if file_hash(inputs / name) != audit['input_file_sha256'][name]:
            raise ValueError('Outbound input changed after source/sensitivity audit')
    samples = json.loads((inputs / 'samples.json').read_text('utf-8'))
    allowed = {'artist-metallica', 'artist-iron-maiden', 'artist-u2', 'artist-led-zeppelin', 'project-metric-manual'}
    if len(samples) != 30 or any(not s.get('delivered') for s in samples):
        raise ValueError('Only the audited 30 delivered RAG subtasks are enabled')
    if not audit.get('all_provided_text_traced_to_registered_public_or_project_example_sources') or audit.get('private_session_source_context_included'):
        raise ValueError('Public-source provenance is incomplete')
    if any(e.get('doc_id') not in allowed for s in samples for e in s['provided_evidence']):
        raise ValueError('Source outside audited public artist/example manual scope')


def worker(input_dir, output, endpoint):
    local_caches(output / 'framework-cache')
    from evalscope import run_task
    from evalscope.backend.rag_eval.ragas.arguments import RAGASToolConfig
    if version('evalscope') != VERSION:
        raise ValueError('Pinned EvalScope version required')
    samples = json.loads((input_dir / 'samples.json').read_text('utf-8'))
    for start in range(0, len(samples), 4):
        batch = samples[start:start+4]
        path = output / f'batch-{start:03d}.json'
        write(path, [s['eval_input'] for s in batch])
        config = ragas_config(path, endpoint)
        RAGASToolConfig.model_validate(config['eval_config'])
        write(output / f'batch-{start:03d}-config.json', config)
        run_task(config)


def bind_scores(inputs, output):
    samples = json.loads((inputs / 'samples.json').read_text('utf-8'))
    official_rows, bound, fragments = [], [], []
    for start in range(0, len(samples), 4):
        path = output / f'batch-{start:03d}_score.json'
        if not path.exists():
            continue
        rows = json.loads(path.read_text('utf-8'))
        fragments.append({'path': path.name, 'sha256': file_hash(path), 'rows': len(rows)})
        batch = samples[start:start+4]
        if len(rows) != len(batch):
            raise ValueError('Official RAGAS batch cardinality mismatch')
        for sample, row in zip(batch, rows):
            expected = sample['eval_input']
            if any(row.get(k) != expected[k] for k in ('user_input', 'response', 'retrieved_contexts')):
                raise ValueError('Official output rows did not preserve sample identity')
            item = {k: v for k, v in sample.items() if k not in {'eval_input', 'provided_evidence', 'delivered', 'generation_status', 'evidence_origin'}}
            item['official_row_index'] = len(official_rows)
            item['metric_names'] = ['faithfulness']
            official_rows.append(row)
            bound.append(item)
    # A byte-for-byte concatenation of official per-sample rows, not custom scores.
    write(output / 'official-ragas-scores.json', official_rows)
    for sample in bound:
        source = inputs / sample['capture_path']
        target = output / sample['capture_path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    result = {'schema': 'evalscope-agent-binding-v1', 'framework': 'EvalScope',
              'evalscope_version': VERSION, 'tool': 'RAGAS', 'scope': 'delivered_RAG_subtask',
              'judge_model': 'deepseek-flash', 'judge_calibration': 'not_human_calibrated',
              'coverage_boundary': 'Conditional on 30 actually delivered document subtasks out of 60 document-target configuration predictions; not whole-Agent accuracy.',
              'official_result': {'path': 'official-ragas-scores.json', 'sha256': file_hash(output / 'official-ragas-scores.json')},
              'official_fragments': fragments,
              'score_storage': 'Official per-batch rows concatenated without changing metric names or values; original fragments preserved.',
              'samples': bound, 'planned_samples': len(samples), 'observed_samples': len(bound),
              'MTEB': {'status': 'not_verified', 'reason': 'Missing complete reviewed corpus/qrels; no synthetic labels created'},
              'embedding_note': 'Faithfulness does not use embeddings; configured client is unused and guard rejects embedding requests.'}
    write(output / 'agent-binding.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-judge', action='store_true')
    parser.add_argument('--worker-endpoint')
    args = parser.parse_args()
    if args.worker_endpoint:
        worker(args.inputs, args.output, args.worker_endpoint)
        return
    if args.output.exists():
        raise ValueError('Fresh output directory required')
    args.output.mkdir(parents=True)
    if not args.run_judge:
        write(args.output / 'readiness.json', {'status': 'not_run', 'new_model_calls': 0,
              'command_requires': '--run-judge in the pinned optional environment', 'evalscope_installed': version('evalscope') if __import__('importlib').util.find_spec('evalscope') else None})
        return
    verify_outbound_scope(args.inputs)
    from qa_agent.config import get_settings
    settings = get_settings()
    if not settings.llm_api_key or settings.llm_model != 'deepseek-flash':
        raise ValueError('Approved configured DeepSeek model/key required')
    budget = PhysicalBudget(args.output, max_calls=120, seconds=1200, no_send_tail=120, concurrency=4, start_on_first_call=True)
    with guarded_endpoint(budget, api_key=settings.llm_api_key, upstream=settings.llm_base_url) as endpoint:
        command = [sys.executable, '-B', '-m', 'benchmarks.rag_evalscope.run', '--inputs', str(args.inputs.resolve()),
                   '--output', str(args.output.resolve()), '--worker-endpoint', endpoint]
        with (args.output / 'framework.stdout.log').open('wb') as stdout, (args.output / 'framework.stderr.log').open('wb') as stderr:
            process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
            startup_deadline = monotonic() + 300
            while process.poll() is None:
                if not budget.records and monotonic() >= startup_deadline:
                    budget.stop_reason = 'framework_startup_timeout_before_any_API_call'
                    budget.persist()
                    process.terminate()
                    break
                if monotonic() >= budget.deadline or budget.stop_reason:
                    process.terminate()
                    break
                sleep(.5)
            process.wait(timeout=65)
    result = bind_scores(args.inputs, args.output)
    if process.returncode and not budget.stop_reason:
        budget.stop_reason = ('framework_startup_failed_before_any_API_call'
                              if not budget.records else 'framework_worker_failed')
    budget.persist()
    known = [r for r in budget.records if not r['missing_usage']]
    usage_complete = len(known) == len(budget.records)
    cache_complete = all(type(r['usage'].get('prompt_cache_hit_tokens')) is int and type(r['usage'].get('prompt_cache_miss_tokens')) is int for r in known) and usage_complete
    usage = {'input_tokens': sum(r['usage']['prompt_tokens'] for r in known) if usage_complete else None,
             'output_tokens': sum(r['usage']['completion_tokens'] for r in known) if usage_complete else None,
             'cache_hit_tokens': sum(r['usage']['prompt_cache_hit_tokens'] for r in known) if cache_complete else None,
             'cache_miss_tokens': sum(r['usage']['prompt_cache_miss_tokens'] for r in known) if cache_complete else None,
             'observed_input_tokens': sum(r['usage']['prompt_tokens'] for r in known),
             'observed_output_tokens': sum(r['usage']['completion_tokens'] for r in known),
             'missing_usage_calls': len(budget.records) - len(known),
             'input_tokens_conservative_reserve': sum(r['input_tokens_conservative_reserve'] for r in budget.records),
             'output_tokens_conservative_reserve': sum(r['output_tokens_conservative_reserve'] for r in budget.records)}
    write(args.output / 'execution.json', {'worker_exit_code': process.returncode,
          'evalscope_version': version('evalscope'), 'ragas_version': version('ragas'),
          'model': 'deepseek-flash', 'physical_calls': len(budget.records),
          'observed_samples': result['observed_samples'], 'planned_samples': result['planned_samples'],
          'stop_reason': budget.stop_reason, 'new_Agent_predictions': 0, 'usage': usage,
          'historical_Agent_physical_calls': 755, 'source': 'EvalScope/RAGAS judge separate cost ledger'})
    result['judge_evidence'] = {name: {'path': name + '.json', 'sha256': file_hash(args.output / (name + '.json'))}
                                for name in ('execution', 'budget-ledger')}
    write(args.output / 'agent-binding.json', result)
    print(json.dumps({'observed_samples': result['observed_samples'], 'physical_calls': len(budget.records)}))


if __name__ == '__main__':
    main()
