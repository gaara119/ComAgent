"""Public first-run workflow over real files, parser, index and answer validator."""
import json
import sys
import pytest
from benchmarks.rag.runner import main
from benchmarks.rag.review import apply_assessments


def test_public_offline_workflow_and_review_template(tmp_path,monkeypatch):
    output=tmp_path/'result'
    args=['benchmark','--output',str(output),'--work-dir',str(tmp_path/'work'),'--embedding','none']
    monkeypatch.setattr(sys,'argv',args)
    assert main('end_to_end')==0
    rows=[json.loads(s) for s in (output/'predictions.jsonl').read_text('utf-8').splitlines()]
    assert len(rows)==32
    assert all(r['generation']['usage']['physical_calls']==0 for r in rows)
    assert all(r['generation']['semantic_status']=='not_applicable_extractive' for r in rows)
    assert all(r['allowed_doc_ids']==r['retrieval_trace']['allowed_doc_ids'] or
               sorted(r['allowed_doc_ids'])==r['retrieval_trace']['allowed_doc_ids'] for r in rows)
    template=json.loads((output/'review-template.json').read_text('utf-8'))
    applied=apply_assessments(rows,template)
    assert applied['summary']['human']['answer_correctness']['mean'] is None
    assert applied['summary']['ai']['assessed_records']==0
    summary=json.loads((output/'summary.json').read_text('utf-8'))['groups']['bm25']
    assert summary['answerable_metric_denominator']==29
    assert summary['physical_calls']==0
    assert summary['semantic_answer_correctness'] is None
    with pytest.raises(SystemExit):main('end_to_end')  # Preserve previous evidence.


def test_missing_evidence_diagnosis_is_not_normal_retrieval_accuracy(tmp_path,monkeypatch):
    output=tmp_path/'diagnosis'
    monkeypatch.setattr(sys,'argv',['benchmark','--output',str(output),'--work-dir',str(tmp_path/'work'),
                                  '--condition','missing_key','--embedding','none'])
    assert main('generation')==0
    summary=json.loads((output/'summary.json').read_text('utf-8'))['groups']['bm25']
    assert summary['answerable_metric_denominator']==0
    assert summary['recall@5'] is None
    assert summary['ndcg@5'] is None
    assert summary['semantic_answer_correctness'] is None
