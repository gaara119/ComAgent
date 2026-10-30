"""Finite selected-document service checks; all model/retrieval data are local fixtures."""
from dataclasses import replace
from hashlib import sha256
import json

import pytest

from qa_agent.config import Settings
from qa_agent.rag import service
from qa_agent.rag.answer import DocumentAnswer, SearchTranslation
from qa_agent.schemas import IntentContract


@pytest.fixture
def local_service(tmp_path, monkeypatch):
    def deny(*a, **kw): raise AssertionError('No real model, API or database')
    monkeypatch.setattr('socket.socket.connect', deny)
    monkeypatch.setattr('psycopg.connect', deny)
    documents = []
    for doc_id, text in [('doc-a', '甲是一支乐队。'), ('doc-b', '乙是一支乐队。'), ('doc-c', '其他资料。')]:
        path = tmp_path/(doc_id+'.md');path.write_text(text, encoding='utf-8')
        documents.append({'doc_id': doc_id, 'title': doc_id, 'language': 'zh',
            'content_hash': sha256(path.read_bytes()).hexdigest(), 'resolved_path': path})
    settings = Settings(db_url='', rag_answer_mode='llm')
    monkeypatch.setattr(service, 'get_settings', lambda: settings)
    monkeypatch.setattr(service, 'load_documents', lambda manifest: documents)
    calls = {'retrieve': [], 'model': [], 'constructed': 0}
    def chunk(doc_id, number):
        document = next(d for d in documents if d['doc_id'] == doc_id)
        return {'chunk_id': f'{doc_id}-chunk', 'evidence_id': f'E{number}', 'doc_id': doc_id,
            'doc_title': document['title'], 'page': None, 'section_path': ['简介'],
            'text': document['resolved_path'].read_text(encoding='utf-8'), 'bbox': None, 'score': 1.0}
    def retrieve(question, scope, **kwargs):
        calls['retrieve'].append({'question': question, 'scope': scope, 'query': kwargs.get('query')})
        ids = [scope] if isinstance(scope, str) else scope
        return [chunk(doc, i+1) for i, doc in enumerate(ids)], {'allowed_doc_ids': list(ids), 'retrieval_method': 'fixture'}
    monkeypatch.setattr(service, 'retrieve', retrieve)
    class LocalLLM:
        def __init__(self, settings):calls['constructed'] += 1
        def complete_json(self, system, user, model, trace):
            payload = json.loads(user);calls['model'].append({'model': model.__name__, 'payload': payload})
            if model is SearchTranslation:return SearchTranslation(english_query='What is this band?')
            evidence = payload['evidence']
            return DocumentAnswer(status='SUCCEEDED',
                answer=' '.join(f"{c['text']}[{c['evidence_id']}]" for c in evidence),
                citation_ids=[c['evidence_id'] for c in evidence])
    monkeypatch.setattr(service, 'JsonLLM', LocalLLM)
    return documents, settings, calls, chunk


def run(ids, question='这两份资料说的乐队是什么？'):
    return service.run_documents_qa(question=question, doc_ids=ids,
        trace_id='local-multidoc-test', intent=IntentContract(route='doc'))


def test_single_wrapper_preserves_legacy_scope_metadata_and_original_question(local_service):
    _, _, calls, _ = local_service
    q = '金属乐队是什么？'
    result = service.run_doc_qa(question=q, doc_id='doc-a', trace_id='single-local', intent=IntentContract(route='doc'))
    assert result.status == 'SUCCEEDED' and result.sql is None
    assert result.metadata['doc_id'] == 'doc-a' and 'doc_ids' not in result.metadata
    assert calls['retrieve'] == [{'question': q, 'scope': 'doc-a', 'query': q}]
    assert calls['model'][0]['payload']['question'] == q
    assert {e.doc_id for e in result.evidences} == {'doc-a'}
    assert result.metadata['validation_status'] == 'passed'


def test_multi_retrieves_exact_selected_list_once_and_answers_original_once(local_service):
    _, _, calls, _ = local_service
    q = '这两份登记资料分别说的乐队是什么？'
    result = run(['doc-a', 'doc-b'], q)
    assert result.status == 'SUCCEEDED' and result.sql is None
    assert calls['retrieve'] == [{'question': q, 'scope': ['doc-a', 'doc-b'], 'query': q}]
    assert len(calls['model']) == 1 and calls['model'][0]['payload']['question'] == q
    assert {e.doc_id for e in result.evidences} == {'doc-a', 'doc-b'}
    assert result.metadata['doc_ids'] == ['doc-a', 'doc-b']
    assert result.metadata['cited_evidence_ids'] == ['E1', 'E2']


@pytest.mark.parametrize('ids,code', [([], 'invalid_document_scope'),
    ('doc-a', 'invalid_document_scope'), (['doc-a', 'doc-a'], 'invalid_document_scope'),
    (['doc-a', 1], 'invalid_document_scope'), ([' doc-a'], 'invalid_document_scope'),
    (['doc-a', 'missing'], 'document_not_found')])
def test_invalid_or_unregistered_scope_fails_before_model_and_retrieval(local_service, ids, code):
    _, _, calls, _ = local_service
    result = run(ids)
    assert result.status == 'FAILED' and result.error.code == code
    assert calls['retrieve'] == [] and calls['model'] == [] and calls['constructed'] == 0


def test_each_selected_document_is_hash_verified_before_retrieval(local_service):
    documents, _, calls, _ = local_service
    documents[1]['resolved_path'].write_text('已改动内容。', encoding='utf-8')
    result = run(['doc-a', 'doc-b'])
    assert result.status == 'FAILED' and result.error.code == 'document_hash_mismatch'
    assert calls['retrieve'] == [] and calls['model'] == []


def test_unselected_registered_retrieval_chunk_is_blocked_before_answer(local_service, monkeypatch):
    _, _, calls, chunk = local_service
    monkeypatch.setattr(service, 'retrieve', lambda *a, **kw: ([chunk('doc-c', 1)], {}))
    result = run(['doc-a', 'doc-b'])
    assert result.status == 'FAILED' and result.error.code == 'rag_scope_violation'
    assert calls['model'] == [] and result.evidences == []


@pytest.mark.parametrize('forged', ['outside-doc', 'changed-text'])
def test_cited_evidence_must_be_actual_retrieved_chunk_not_only_known_ID(local_service, monkeypatch, forged):
    _, _, _, chunk = local_service
    used = chunk('doc-c', 1) if forged == 'outside-doc' else dict(chunk('doc-a', 1), text='伪造内容。')
    monkeypatch.setattr(service, 'answer_from_chunks', lambda *a, **kw:
        (DocumentAnswer(status='SUCCEEDED', answer='资料说明。[E1]', citation_ids=['E1']), [used]))
    result = run(['doc-a', 'doc-b'])
    assert result.status == 'FAILED' and result.error.code == 'rag_scope_violation'
    assert result.evidences == []


def test_colliding_evidence_IDs_do_not_allow_ambiguous_multi_doc_citation(local_service, monkeypatch):
    _, _, calls, chunk = local_service
    monkeypatch.setattr(service, 'retrieve', lambda *a, **kw: ([chunk('doc-a', 1), chunk('doc-b', 1)], {}))
    result = run(['doc-a', 'doc-b'])
    assert result.status == 'FAILED' and result.error.code == 'rag_scope_violation'
    assert calls['model'] == []


def test_empty_retrieval_stays_empty_without_model_answer(local_service, monkeypatch):
    _, _, calls, _ = local_service
    monkeypatch.setattr(service, 'retrieve', lambda *a, **kw: ([], {}))
    result = run(['doc-a', 'doc-b'])
    assert result.status == 'EMPTY_RESULT' and result.evidences == [] and calls['model'] == []


def test_all_English_docs_translate_once_but_answer_uses_original_question(local_service):
    documents, _, calls, _ = local_service
    for document in documents:document['language'] = 'en'
    q = '这两份资料的乐队是什么？'
    result = run(['doc-a', 'doc-b'], q)
    assert result.status == 'SUCCEEDED'
    assert [c['model'] for c in calls['model']] == ['SearchTranslation', 'DocumentAnswer']
    assert calls['retrieve'][0]['question'] == q and calls['retrieve'][0]['query'] == 'What is this band?'
    assert calls['model'][-1]['payload']['question'] == q


def test_mixed_language_selection_keeps_original_query_and_all_selected_docs(local_service):
    documents, _, calls, _ = local_service
    documents[0]['language'] = 'en'
    q = '这两份资料的乐队是什么？'
    result = run(['doc-a', 'doc-b'], q)
    assert result.status == 'SUCCEEDED'
    assert len(calls['model']) == 1 and calls['retrieve'][0]['query'] == q
    assert calls['retrieve'][0]['scope'] == ['doc-a', 'doc-b']
