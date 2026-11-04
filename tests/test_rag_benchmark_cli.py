"""CLI boundaries and tiny temporary integration fixtures, not benchmark data."""
import csv
from hashlib import sha256
import json
import sys

import pytest

import benchmarks.rag.runner as runner
from benchmarks.rag.review import apply_assessments


@pytest.fixture
def explicit_unit_dataset(tmp_path, monkeypatch):
    """One disposable source and one question exercise I/O without the retired 32."""
    from qa_agent import documents

    source = tmp_path / 'data' / 'unit.md'
    source.parent.mkdir()
    source.write_text('# Unit example\n\nThe temporary fixture code is TEST123.\n', encoding='utf-8')
    source_hash = sha256(source.read_bytes()).hexdigest()
    manifest = tmp_path / 'manifest.csv'
    with manifest.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, ['doc_id', 'title', 'format', 'path', 'content_hash'])
        writer.writeheader()
        writer.writerow({'doc_id': 'unit-source', 'title': 'Unit example', 'format': 'md',
                         'path': 'data/unit.md', 'content_hash': source_hash})
    path = tmp_path / 'unit-dataset.json'
    path.write_text(json.dumps({
        'version': 'temporary-unit-integration-v1', 'title': 'Disposable test input',
        'corpus_manifest': 'manifest.csv',
        'cases': [{'id': 'unit-question', 'split': 'dev', 'family_id': 'unit',
                   'category': 'unit-only', 'question': 'What is the temporary fixture code?',
                   'doc_ids': ['unit-source'], 'answerable': True, 'reference_answer': 'TEST123',
                   'required_evidence': [{'id': 'unit-evidence', 'doc_id': 'unit-source', 'page': None,
                                          'section_path': ['Unit example'],
                                          'quote': 'The temporary fixture code is TEST123.',
                                          'source_sha256': source_hash}]}]
    }), encoding='utf-8')
    original = documents.load_documents

    def load_local(manifest_path=None, project_root=None):
        return original(manifest_path, project_root=tmp_path)

    monkeypatch.setattr(documents, 'load_documents', load_local)
    monkeypatch.setattr(runner, 'load_documents', load_local)
    return path


def test_dataset_must_be_explicit_before_any_work(tmp_path, monkeypatch, capsys):
    output = tmp_path / 'must-not-exist'
    monkeypatch.setattr(sys, 'argv', ['benchmark', '--output', str(output)])
    with pytest.raises(SystemExit) as exc:
        runner.main('end_to_end')
    assert exc.value.code == 2
    assert 'explicit --dataset' in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize('selector', ['path', 'copied_version', 'legacy_config'])
def test_retired_dataset_is_rejected_before_index_or_model(tmp_path, monkeypatch, capsys, selector):
    output = tmp_path / 'must-not-exist'
    retired = runner.PROJECT_ROOT / 'benchmarks/rag/fixtures/dataset.json'
    args = ['benchmark', '--output', str(output)]
    if selector == 'legacy_config':
        config = tmp_path / 'legacy-config.json'
        config.write_text(json.dumps({'dataset': str(retired)}), encoding='utf-8')
        args += ['--config', str(config)]
    else:
        if selector == 'copied_version':
            copied = tmp_path / 'renamed.json'
            copied.write_text(json.dumps({'version': 'rag-fixtures-v1', 'cases': []}), encoding='utf-8')
            retired = copied
        args += ['--dataset', str(retired)]
    monkeypatch.setattr(sys, 'argv', args)
    monkeypatch.setattr(runner, 'build_index', lambda *a, **k: pytest.fail('Must not build a retired index'))
    monkeypatch.setattr(runner, 'get_settings', lambda: pytest.fail('Must not access model settings'))
    with pytest.raises(SystemExit) as exc:
        runner.main('end_to_end')
    assert exc.value.code == 2
    assert 'retired' in capsys.readouterr().err
    assert not output.exists()


def test_explicit_tiny_offline_workflow_and_review_template(tmp_path, monkeypatch, explicit_unit_dataset):
    output = tmp_path / 'result'
    args = ['benchmark', '--dataset', str(explicit_unit_dataset), '--output', str(output),
            '--work-dir', str(tmp_path / 'work'), '--embedding', 'none']
    monkeypatch.setattr(sys, 'argv', args)
    assert runner.main('end_to_end') == 0
    rows = [json.loads(s) for s in (output / 'predictions.jsonl').read_text('utf-8').splitlines()]
    assert len(rows) == 1
    assert rows[0]['id'] == 'unit-question'
    assert all(r['generation']['usage']['physical_calls'] == 0 for r in rows)
    assert all(r['generation']['semantic_status'] == 'not_applicable_extractive' for r in rows)
    template = json.loads((output / 'review-template.json').read_text('utf-8'))
    applied = apply_assessments(rows, template)
    assert applied['summary']['human']['answer_correctness']['mean'] is None
    assert applied['summary']['ai']['assessed_records'] == 0
    summary = json.loads((output / 'summary.json').read_text('utf-8'))['groups']['bm25']
    assert summary['answerable_metric_denominator'] == 1
    assert summary['physical_calls'] == 0
    assert summary['semantic_answer_correctness'] is None
    with pytest.raises(SystemExit):
        runner.main('end_to_end')  # Preserve previous evidence.


def test_missing_evidence_diagnosis_is_not_normal_retrieval_accuracy(tmp_path, monkeypatch, explicit_unit_dataset):
    output = tmp_path / 'diagnosis'
    monkeypatch.setattr(sys, 'argv', [
        'benchmark', '--dataset', str(explicit_unit_dataset), '--output', str(output),
        '--work-dir', str(tmp_path / 'work'), '--condition', 'missing_key', '--embedding', 'none'])
    assert runner.main('generation') == 0
    summary = json.loads((output / 'summary.json').read_text('utf-8'))['groups']['bm25']
    assert summary['answerable_metric_denominator'] == 0
    assert summary['recall@5'] is None
    assert summary['ndcg@5'] is None
    assert summary['semantic_answer_correctness'] is None
