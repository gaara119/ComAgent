"""Restore only the exact self-owned V2 increment; preserve trial evidence."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / 'eval/experiments/after_d2_01_03'
RUNTIME = EXP / 'runtime_eval'


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    import sys
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(RUNTIME))
    from snapshot import snapshot
    v1 = json.loads((RUNTIME / 'V1-code-snapshot.json').read_text(encoding='utf-8'))
    v2 = json.loads((RUNTIME / 'V2-code-snapshot.json').read_text(encoding='utf-8'))
    current = snapshot()
    assert current['files'] == v2['files'] and current['safe_config'] == v2['safe_config'], 'Unrelated changes detected; do not restore'
    archive = RUNTIME / 'version-changes/V2'
    report = archive / 'actual-restore-to-V1.json'
    if report.exists():
        raise RuntimeError('Restore record exists; do not replay')
    restores = ['qa_agent/pipeline.py', 'qa_agent/sql/validator.py']
    for name in restores:
        assert sha(ROOT / name) == v2['files'][name]
        assert sha(archive / 'before' / name) == v1['files'][name]
    helper = ROOT / 'qa_agent/sql/ratio_guard.py'
    assert helper.resolve().is_relative_to(ROOT.resolve()) and sha(helper) == v2['files']['qa_agent/sql/ratio_guard.py']
    assert sha(archive / 'after/qa_agent/sql/ratio_guard.py') == sha(helper)
    test = ROOT / 'tests/test_special_v2_ratio_scope.py'
    delta = json.loads((archive / 'source-delta.json').read_text(encoding='utf-8'))
    expected_test = next(f['after_sha256'] for f in delta['files'] if f['path'] == 'tests/test_special_v2_ratio_scope.py')
    assert test.resolve().is_relative_to(ROOT.resolve()) and sha(test) == expected_test
    saved_test = archive / 'after/tests/test_special_v2_ratio_scope.py'
    saved_test.parent.mkdir(parents=True, exist_ok=True)
    if saved_test.exists():
        assert sha(saved_test) == expected_test
    else:
        with saved_test.open('xb') as handle:
            handle.write(test.read_bytes())
    for name in restores:
        (ROOT / name).write_bytes((archive / 'before' / name).read_bytes())
    helper.unlink()  # one verified self-owned file, never a recursive cleanup
    test.unlink()  # exact bytes remain in the V2 archive, no broken active import
    final = snapshot()
    assert final['files'] == v1['files'] and final['safe_config'] == v1['safe_config']
    record = {'at': datetime.now(timezone.utc).isoformat(), 'command': [sys.executable, '-B', *sys.argv],
              'restored_files': restores, 'removed_self_owned_files': ['qa_agent/sql/ratio_guard.py', 'tests/test_special_v2_ratio_scope.py'],
              'trial_after_bytes_preserved': True, 'before_sha_match_V1': True,
              'final_runtime_files_and_safe_config_match_V1': True,
              'retained_prompt': 'qa_agent/clarify/prompts/intent_patch.txt',
              'reason': 'V2 rejects two actual valid ratio expressions/provenance paths without reliable end-to-end benefit; restore only this trial increment, retain evidence and V1 local patch correction.',
              'git_reset_or_clean_used': False, 'database_changes': 0, 'prediction_calls': 0}
    with report.open('x', encoding='utf-8') as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
