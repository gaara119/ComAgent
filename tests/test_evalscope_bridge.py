"""Boundary tests only; fixtures are not RAG evaluation scores or new questions."""
from concurrent.futures import ThreadPoolExecutor
import json
from time import monotonic, sleep

import pytest

from benchmarks.rag_evalscope.bridge import canonical_hash, file_hash, load_results, read_capture
from benchmarks.rag_evalscope.budget import PhysicalBudget, BudgetStop
from benchmarks.rag_evalscope.run import ragas_config


def fixture_result(tmp_path):
    capture = {'request': {'messages': [{'content': json.dumps({'question': 'q', 'evidence': [{'evidence_id': 'E1', 'doc_id': 'd', 'text': 'ctx'}]})}]},
               'response': {'choices': [{'message': {'content': json.dumps({'status': 'SUCCEEDED', 'answer': 'a'})}}]}}
    path = tmp_path / 'capture.json'
    path.write_text(json.dumps(capture), 'utf-8')
    content = read_capture(capture)
    record = {'id': 's:q', 'arm': 'BASE', 'raw_response': {'answer': 'a'}, 'source': {'code_hash': 'code1'},
              'attempts': [{'provider_attempts': [{'capture_id': 'cap1', 'source_sha256': file_hash(path)}]}]}
    official = [{k: content[k] for k in ('user_input', 'response', 'retrieved_contexts')} | {'faithfulness': .5}]
    output = tmp_path / 'scores.json'
    output.write_text(json.dumps(official), 'utf-8')
    sample = {'sample_id': 'sample1', 'id': 's:q', 'arm': 'BASE', 'prediction_sha256': canonical_hash(record['raw_response']),
              'run_sha256': canonical_hash(record['source']), 'capture_id': 'cap1', 'capture_sha256': file_hash(path),
              'capture_path': 'capture.json', 'question_sha256': canonical_hash('q'), 'evidence_sha256': canonical_hash(content['provided_evidence']),
              'rag_response_sha256': canonical_hash('a'), 'official_row_index': 0, 'metric_names': ['faithfulness']}
    result = {'schema': 'evalscope-agent-binding-v1', 'framework': 'EvalScope', 'evalscope_version': '1.14.1', 'tool': 'RAGAS',
              'official_result': {'path': 'scores.json', 'sha256': file_hash(output)}, 'samples': [sample]}
    result_path = tmp_path / 'binding.json'
    result_path.write_text(json.dumps(result), 'utf-8')
    return result_path, {'s:q': {}}, [record], result


def test_join_preserves_actual_framework_metric_source(tmp_path):
    path, cases, records, _ = fixture_result(tmp_path)
    joined = load_results(path, cases, records)
    assert joined['s:q', 'BASE']['source'] == 'EvalScope'
    assert joined['s:q', 'BASE']['samples'][0]['metrics']['faithfulness'] == .5
    assert joined['s:q', 'BASE']['retrieval_recall_at_k'] is None


@pytest.mark.parametrize('field', ['prediction_sha256', 'run_sha256', 'question_sha256', 'evidence_sha256', 'capture_sha256', 'rag_response_sha256'])
def test_wrong_run_prediction_question_context_cannot_reuse_scores(tmp_path, field):
    path, cases, records, value = fixture_result(tmp_path)
    value['samples'][0][field] = 'changed'
    path.write_text(json.dumps(value), 'utf-8')
    with pytest.raises(ValueError):
        load_results(path, cases, records)


def test_mteb_global_score_not_relabelled_as_matching_ragas(tmp_path):
    path, cases, records, value = fixture_result(tmp_path)
    value['tool'] = 'MTEB'
    path.write_text(json.dumps(value), 'utf-8')
    with pytest.raises(ValueError, match='version/tool'):
        load_results(path, cases, records)


def test_undeclared_metric_and_duplicate_sample_rejected(tmp_path):
    path, cases, records, value = fixture_result(tmp_path)
    value['samples'].append(value['samples'][0])
    path.write_text(json.dumps(value), 'utf-8')
    with pytest.raises(ValueError, match='duplicate'):
        load_results(path, cases, records)


def test_official_nan_is_unscored_without_changing_raw_evidence(tmp_path):
    path, cases, records, value = fixture_result(tmp_path)
    raw_path = tmp_path / 'scores.json'
    rows = json.loads(raw_path.read_text('utf-8'))
    rows[0]['faithfulness'] = float('nan')
    rows[0]['answer_correctness'] = .75
    raw_path.write_text(json.dumps(rows), 'utf-8')
    original_bytes = raw_path.read_bytes()
    value['official_result']['sha256'] = file_hash(raw_path)
    value['samples'][0]['metric_names'].append('answer_correctness')
    path.write_text(json.dumps(value), 'utf-8')
    sample = load_results(path, cases, records)['s:q', 'BASE']['samples'][0]
    assert sample['metrics'] == {'faithfulness': None, 'answer_correctness': .75}
    assert sample['metric_statuses'] == {'faithfulness': 'framework_nonfinite_score'}
    assert raw_path.read_bytes() == original_bytes


@pytest.mark.parametrize('value', ['nan', float('inf'), -1, 2, True])
def test_invalid_official_metrics_are_not_silently_discarded(tmp_path, value):
    path, cases, records, binding = fixture_result(tmp_path)
    raw_path = tmp_path / 'scores.json'
    rows = json.loads(raw_path.read_text('utf-8'))
    rows[0]['faithfulness'] = value
    raw_path.write_text(json.dumps(rows), 'utf-8')
    binding['official_result']['sha256'] = file_hash(raw_path)
    path.write_text(json.dumps(binding), 'utf-8')
    with pytest.raises(ValueError, match='Malformed'):
        load_results(path, cases, records)


def test_budget_counts_failed_missing_usage_conservatively_and_blocks_retries(tmp_path):
    budget = PhysicalBudget(tmp_path, max_calls=2)
    first = budget.reserve({'model': 'deepseek-flash'})
    budget.settle(first, status='transport_error', error_type='ConnectError')
    assert first['missing_usage'] and first['input_tokens_conservative_reserve'] >= 40000
    with pytest.raises(BudgetStop):
        budget.reserve({})
    assert len(budget.records) == 1


def test_budget_first_probe_is_serial_and_limit_shared(tmp_path):
    budget = PhysicalBudget(tmp_path, max_calls=2)
    first = budget.reserve({})
    with ThreadPoolExecutor(max_workers=1) as pool:
        waiting = pool.submit(budget.reserve, {})
        sleep(.03)
        assert len(budget.records) == 1 and not waiting.done()
        budget.settle(first, status='completed', response={'usage': {'prompt_tokens': 5, 'completion_tokens': 2}})
        second = waiting.result(timeout=2)
    assert len(budget.records) == 2
    budget.settle(second, status='completed', response={})
    with pytest.raises(BudgetStop):
        budget.reserve({})


def test_budget_stops_before_reserved_tail(tmp_path):
    budget = PhysicalBudget(tmp_path, seconds=1, no_send_tail=2)
    with pytest.raises(BudgetStop):
        budget.reserve({})
    assert not budget.records


def test_budget_persists_zero_call_framework_failure_receipt(tmp_path):
    budget = PhysicalBudget(tmp_path, start_on_first_call=True)
    ledger = json.loads((tmp_path / 'budget-ledger.json').read_text('utf-8'))
    assert ledger['physical_calls'] == 0
    assert ledger['records'] == []
    assert ledger['phase_starts_on_first_actual_call'] is True
    budget.stop_reason = 'framework_startup_failed_before_any_API_call'
    budget.persist()
    assert json.loads((tmp_path / 'budget-ledger.json').read_text('utf-8'))['stop_reason'] == budget.stop_reason


def test_official_current_config_fields_and_no_generation():
    config = ragas_config('input.json', 'http://127.0.0.1:1234/v1')
    assert config['eval_backend'] == 'RAGEval'
    assert config['eval_config']['eval']['metrics'] == ['faithfulness']
    assert 'testset_generation' not in config['eval_config']
