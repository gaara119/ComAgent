"""Record isolated review artifacts and prepare runtime tests without applying code."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'qa_agent/clarify/extractor.py'
CANDIDATE = HERE / 'extractor_candidate-v3.py'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
old_meta = json.loads((HERE / 'candidate-meta-v2.json').read_text(encoding='utf-8'))
if sha(SOURCE) != old_meta['source_sha256']:
    raise SystemExit('Runtime source changed: stop instead of replacing another agent\'s work.')
patch = ''.join(difflib.unified_diff(SOURCE.read_text(encoding='utf-8').splitlines(keepends=True),
    CANDIDATE.read_text(encoding='utf-8').splitlines(keepends=True),
    fromfile='a/qa_agent/clarify/extractor.py', tofile='b/qa_agent/clarify/extractor.py'))
(HERE / 'candidate-v3.patch').write_text(patch, encoding='utf-8')
staged_test = (HERE / 'test_candidate_v3.py').read_text(encoding='utf-8')
test = staged_test.replace('import importlib.util\n', '').replace('ROOT=Path(__file__).resolve().parents[4]',
    'ROOT=Path(__file__).resolve().parents[1]')
start = test.index("spec=importlib.util.spec_from_file_location(")
end = test.index('\n\n\nclass Model:', start)
test = test[:start] + 'from qa_agent.clarify import extractor as candidate' + test[end:]
formal = ROOT / 'tests/test_oct12_attribute_lookup.py'
if formal.exists():
    raise SystemExit('Formal test already exists: stop to preserve another agent\'s work.')
formal.write_text(test, encoding='utf-8')
(HERE / 'test-v3-results.txt').write_text(
    'COMMAND: .\\.venv\\Scripts\\python.exe -m pytest notes/oct12/staging/sql19/test_candidate_v3.py -q\n'
    'CWD: E:\\中国电子杯-赛题八\\system\n'
    '........................................................                 [100%]\n'
    '56 passed in 1.25s\nEXIT_CODE: 0\n'
    'Observed tool output copied to this new evidence file; tests were not rerun to create it.\n', encoding='utf-8')
metadata = {
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'source_file': str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
    'source_sha256': sha(SOURCE), 'candidate_sha256': sha(CANDIDATE),
    'candidate_file': str(CANDIDATE.relative_to(ROOT)).replace('\\', '/'),
    'formal_test_file': str(formal.relative_to(ROOT)).replace('\\', '/'),
    'formal_test_sha256': sha(formal), 'business_source_applied': False,
    'replaces_unapplied_candidate_version': 2,
    'strategy': 'Whole-question clause whitelist + actual catalog fields + explicit model N/primary-order agreement',
    'tested': {'isolated_tests': 56, 'passed': 56, 'live_model_requests': 0, 'held_questions': 0},
    'classification_scope': 'ranking + metric None + bounded customer object only',
    'unmodified': ['top_n', 'order', 'metric', 'business code', 'golds', 'human review', 'alias status'],
    'limitations': ['Correction proves primary-order and N agreement, not independent correctness of every model tie-breaker or projection; current sql-19 model tie-breaker is verified in actual provider response.'],
    'independent_review': 'pending sibling UI review of v3',
}
(HERE / 'candidate-meta-v3.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
review = {
    'review_kind': 'AI self-review after independent v1/v2 feedback',
    'candidate_sha256': sha(CANDIDATE), 'runtime_unchanged_sha256': sha(SOURCE),
    'checks': [
        {'scope': 'sql-19 complete wording, actual schema, unchanged accepted gold', 'judgment': 'AI建议通过'},
        {'scope': 'business suffixes from independent rejected v1 review', 'judgment': 'AI建议通过', 'proof': 'all 13 rejected by v3 full-clause whitelist'},
        {'scope': 'model top_n missing/different', 'judgment': 'AI建议通过', 'proof': 'None/3/6 remain ranking; explicit N and model N unchanged'},
        {'scope': 'model primary sort missing/different', 'judgment': 'AI建议通过', 'proof': '8 malformed/mismatched orders remain ranking; nothing filled in'},
        {'scope': 'real customer field/direction canonicalization', 'judgment': 'AI建议通过', 'proof': 'actual catalog fields only; original model order retained'},
        {'scope': 'different metric, task, database, object', 'judgment': 'AI建议通过', 'proof': 'existing fixture counterexamples unchanged'},
        {'scope': 'runtime and gold application', 'judgment': '未应用', 'proof': 'isolated candidate only; formal test staged for root application'},
    ],
    'human_signature': None, 'human_confirmation_date': None,
    'independent_review': 'pending sibling v3 review',
}
(HERE / 'ai-self-review-v3.json').write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(metadata, ensure_ascii=False, indent=2))
