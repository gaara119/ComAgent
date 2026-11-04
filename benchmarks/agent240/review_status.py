"""Current human-review evidence layered over immutable historical exports."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def target_hash(case):
    provenance = case.get('reference_provenance') or {}
    target = {k: case.get(k) for k in (
        'id', 'original_id', 'question', 'expected_route', 'labels', 'reference_datetime',
        'timezone', 'source_context', 'reference', 'reference_answer', 'reference_answer_scope')}
    target['reference_semantics'] = {k: provenance.get(k) for k in (
        'gold_evidence', 'gold_source_plan', 'grading_criteria')}
    return hashlib.sha256(json.dumps(target, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def apply_status(cases, dataset_path, overlay_path):
    path = Path(overlay_path)
    overlay = json.loads(path.read_text('utf-8'))
    if overlay.get('schema') != 'current-human-gold-review-v1' or overlay.get('dataset_sha256') != hashlib.sha256(Path(dataset_path).read_bytes()).hexdigest():
        raise ValueError('Current Gold review status belongs to another dataset version')
    statuses = {entry['id']: entry for entry in overlay['cases']}
    if set(statuses) != set(cases) or len(statuses) != len(overlay['cases']):
        raise ValueError('Review status scope must match the exact original 240 IDs')
    for case_id, case in cases.items():
        status = statuses[case_id]
        if status.get('status') != 'human_reviewed' or status.get('target_sha256') != target_hash(case):
            raise ValueError('Gold/wording changed after the human-review confirmation: ' + case_id)
        # Do not overwrite the old pending field, Gold, reference results or signatures.
        case['current_gold_review'] = {**status, 'evidence_source': overlay['source'],
                                      'historical_export_status': case.get('reference_provenance', {}).get('gold_human_review_status')}
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'status': 'human_review_complete_user_confirmed', 'reviewed_questions': len(statuses),
            'source': overlay['source'], 'historical_export_fields_unchanged': True}


def current_status(case):
    return (case.get('current_gold_review') or {}).get('status') or case.get('reference_provenance', {}).get('gold_human_review_status', 'not_recorded')
