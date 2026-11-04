"""Current human review is distinct from immutable historical pending fields."""
import hashlib
import json

import pytest

from benchmarks.agent240.review_status import apply_status, current_status, target_hash


def test_current_review_overlay_preserves_old_pending_and_checks_content(tmp_path):
    case = {'id': 's:q', 'question': 'one?', 'reference': {'rows': [[1]], 'columns': ['n']},
            'reference_provenance': {'gold_human_review_status': 'pending'}}
    dataset = tmp_path / 'dataset.json'
    dataset.write_text(json.dumps({'cases': [case]}), 'utf-8')
    overlay = tmp_path / 'status.json'
    overlay.write_text(json.dumps({'schema': 'current-human-gold-review-v1',
        'dataset_sha256': hashlib.sha256(dataset.read_bytes()).hexdigest(),
        'source': {'kind': 'user_confirmation'},
        'cases': [{'id': 's:q', 'status': 'human_reviewed', 'target_sha256': target_hash(case)}]}), 'utf-8')
    summary = apply_status({'s:q': case}, dataset, overlay)
    assert summary['reviewed_questions'] == 1
    assert current_status(case) == 'human_reviewed'
    assert case['reference_provenance']['gold_human_review_status'] == 'pending'
    case['reference']['rows'] = [[2]]
    with pytest.raises(ValueError, match='Gold/wording changed'):
        apply_status({'s:q': case}, dataset, overlay)


def test_actual_240_reviewed_without_rewriting_original_labels():
    from pathlib import Path
    from benchmarks.agent240.evaluate import load_bundle
    root = Path(__file__).resolve().parents[1]
    manifest, cases, _ = load_bundle(root / 'benchmarks/agent240/data')
    assert all(current_status(c) == 'human_reviewed' for c in cases.values())
    assert manifest['current_gold_review']['reviewed_questions'] == 240
    assert all(c['reference_provenance']['gold_human_review_status'] == 'pending' for c in cases.values())
