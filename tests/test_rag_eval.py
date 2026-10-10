from copy import deepcopy
import json
from argparse import Namespace

import pytest

from eval.rag_dataset import load_dataset, require_run_permission, review_hash, reviewed
from eval.rag_metrics import answer_surface_match, measure_response
from eval.rag_run_eval import evaluate


@pytest.fixture
def item():
    return {'id': 'rag-test', 'question': 'What class?', 'doc_id': 'doc-one', 'answer': 'Class B',
            'reference_text': 'A Class B device.', 'physical_pages': [2], 'page_numbering': 'physical_pdf_1_based',
            'split': 'dev', 'family_id': 'one-family', 'source_qa_id': 'qa-test', 'source_sha256': 'a' * 64,
            'source_qa_sha256': 'b' * 64, 'evidence_source': 'text', 'answer_form': 'String',
            'gold_review': {'status': 'needs_human_review'}}


def test_draft_gold_only_dev(item):
    assert require_run_permission([item], 'dev', True) == [item]
    with pytest.raises(ValueError, match='人工'):
        require_run_permission([item], 'dev', False)
    with pytest.raises(ValueError, match='保留'):
        require_run_permission([item], 'holdout', False)
    with pytest.raises(ValueError, match='开发'):
        require_run_permission([item], 'holdout', True, True, 'freeze')


def test_human_acceptance_is_bound_to_content(item):
    item['gold_review'] = {'status': 'accepted', 'reviewer': 'B', 'content_sha256': review_hash(item)}
    assert reviewed(item)
    item['physical_pages'] = [1]
    assert not reviewed(item)


def test_family_cannot_cross_split(item, tmp_path):
    other = deepcopy(item)
    other.update(id='rag-other', split='holdout')
    path = tmp_path / 'items.jsonl'
    path.write_text(json.dumps(item) + '\n' + json.dumps(other), encoding='utf8')
    with pytest.raises(ValueError, match='family'):
        load_dataset(path)


def test_authentic_citation_and_gold_page(item):
    payload = {'status': 'SUCCEEDED', 'answer': 'Class B [E1]',
               'evidences': [{'evidence_id': 'E1', 'doc_id': 'doc-one', 'page': 2, 'text': 'A Class B device.'}],
               'metadata': {'retrieved_pages': [{'doc_id': 'doc-one', 'page': 2}]}}
    metrics = measure_response(item, payload, ['Cover', 'Equipment: A Class B device.'])
    for key in ['all_evidence_text_authentic', 'all_evidence_from_selected_doc', 'evidence_gold_page_hit',
                'retrieval_gold_page_hit', 'answer_has_known_evidence_id', 'answer_surface_match']:
        assert metrics[key] is True
    assert metrics['semantic_answer_correctness'] == 'needs_human_review'


@pytest.mark.parametrize('page,doc_id,text', [(0, 'doc-one', 'A Class B device.'),
                                          (3, 'doc-one', 'A Class B device.'),
                                          (True, 'doc-one', 'A Class B device.'),
                                          (2, 'doc-other', 'A Class B device.'),
                                          (2, 'doc-one', 'Invented quotation')])
def test_wrong_doc_page_or_quote_fails(item, page, doc_id, text):
    payload = {'evidences': [{'evidence_id': 'E1', 'doc_id': doc_id, 'page': page, 'text': text}]}
    assert measure_response(item, payload, ['Cover', 'A Class B device.'])['all_evidence_text_authentic'] is False


def test_empty_evidence_never_passes_vacuously(item):
    metrics = measure_response(item, {}, ['Cover', 'A Class B device.'])
    assert not metrics['all_evidence_text_authentic']
    assert not metrics['all_evidence_from_selected_doc']
    assert metrics['retrieval_gold_page_hit'] is None


def test_independent_second_pdf_view_allows_legitimate_reading_order(item):
    payload = {'evidences': [{'evidence_id': 'E1', 'doc_id': 'doc-one', 'page': 2, 'text': 'A Class B device.'}]}
    primary = ['Cover', 'A Class B unrelated-column device.']
    alternate = ['Cover', 'A Class B device. Another column.']
    assert not measure_response(item, payload, primary)['all_evidence_text_authentic']
    assert measure_response(item, payload, primary, [alternate])['all_evidence_text_authentic']
    assert measure_response(item, payload, primary, [primary, alternate])['all_evidence_text_authentic']


def test_duplicate_evidence_ids_are_detected(item):
    evidence = {'evidence_id': 'E1', 'doc_id': 'doc-one', 'page': 2, 'text': 'A Class B device.'}
    assert not measure_response(item, {'evidences': [evidence, evidence]}, ['Cover', 'A Class B device.'])['unique_evidence_ids']


def test_numeric_substring_does_not_count_a_different_number():
    assert answer_surface_match('71%', 'The proportion is 71% [E1].')
    assert not answer_surface_match('71%', 'The proportion is 171% [E1].')


def test_real_gold_remains_pending_and_has_fixed_split():
    data = load_dataset()
    assert len(data) == 20
    assert sum(item['split'] == 'dev' for item in data) == 14
    assert sum(item['split'] == 'holdout' for item in data) == 6
    assert all(item['source_qa']['evidence_source'] == 'text' for item in data)
    assert all(item['machine_verification']['reference_is_exact_pdf_substring'] for item in data)
    # Test the real initial delivery, not an assertion that would prevent users
    # from accepting their reviewed gold in future.
    assert all(item['source_qa_id'] == item['source_qa']['ID'] for item in data)


def test_holdout_guard_runs_before_any_network(monkeypatch):
    def forbid_client(*args, **kwargs):
        raise AssertionError('Holdout guard must run before network access')
    monkeypatch.setattr('eval.rag_run_eval.httpx.Client', forbid_client)
    args = Namespace(dataset=__import__('eval.rag_dataset', fromlist=['DEFAULT_DATASET']).DEFAULT_DATASET,
                     split='holdout', draft_gold=False, allow_holdout=False, frozen_tag=None)
    with pytest.raises(ValueError, match='保留'):
        evaluate(args)
