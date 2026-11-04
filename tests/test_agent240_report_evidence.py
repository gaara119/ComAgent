"""Regression receipts are panel-bound evidence, never new model predictions."""
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from benchmarks.agent240.regression_report import (
    load_regression_evidence, regression_evidence_markdown,
)


DATA = Path(__file__).resolve().parents[1] / 'benchmarks' / 'agent240' / 'data'


def panel_manifest():
    return {'files': {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest()
                      for name in ('dataset.json', 'records.jsonl')}}


def test_actual_portable_receipts_verify_without_API_or_regrading():
    value = load_regression_evidence(panel_manifest())
    assert value['status'] == 'hash_verified'
    receipts = value['receipts']
    assert receipts['controlled-faults.json']['new_model_API_calls'] == 0
    assert receipts['controlled-faults.json']['transient_recovery'] == {
        'recovered': 6, 'eligible_scenarios': 6}
    assert receipts['all-agent-regressions.junit.xml'] == {
        'tests': 244, 'failures': 0, 'errors': 0, 'skipped': 0}
    assert receipts['gold-status-correction.json']['reviewed_questions'] == 240
    assert receipts['review-consistency-audit.json']['findings_summary']['labels_changed'] == 0


def test_receipts_for_other_predictions_are_not_claimed_as_tested():
    manifest = panel_manifest()
    manifest['files']['records.jsonl'] = '0' * 64
    value = load_regression_evidence(manifest)
    assert value['status'] == 'not_verified'
    assert 'another historical panel' in value['reason']


def test_receipt_tampering_fails_instead_of_reusing_old_pass(tmp_path):
    dest = tmp_path / 'receipts'
    shutil.copytree(DATA / 'regression-evidence', dest)
    path = dest / 'controlled-faults.json'
    fault = json.loads(path.read_text('utf-8'))
    fault['transient_recovery']['recovered'] = 99
    path.write_text(json.dumps(fault), 'utf-8')
    with pytest.raises(ValueError, match='receipt hash mismatch'):
        load_regression_evidence(panel_manifest(), directory=dest)


def test_report_separates_Gold_from_prediction_and_fixture_boundaries():
    report = regression_evidence_markdown({'source_manifest': panel_manifest()})
    assert '当前Gold人工审核覆盖240/240' in report
    assert '不是同一清单' in report
    assert 'MockTransport' in report
    assert '66项' in report
    assert '不相加' in report
    assert '不是当前240题' in report
    assert '金额无可靠计费单价依据，保持未核验' in report
