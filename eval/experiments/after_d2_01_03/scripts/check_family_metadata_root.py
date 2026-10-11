"""Read existing split/family metadata only; never expose held questions or gold."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parents[1]
new_path = EXP / 'data/cases-v6-reviewed.jsonl'
new = [json.loads(line) for line in new_path.read_text(encoding='utf-8').splitlines() if line]
sources = [
    'eval/datasets/nl2sql_chinook_d2.jsonl', 'eval/datasets/robust.jsonl',
    'eval/datasets/rag_single.jsonl',
    'eval/datasets/d3/aw_schema_link.dev.v2.jsonl',
    'eval/datasets/d3/aw_schema_link.holdout.jsonl',
    'eval/datasets/d3/clarify/dev.jsonl',
    'eval/datasets/d3/clarify/protected_holdout/cases.jsonl',
]
held_families, dev_families, rows = set(), set(), []
for name in sources:
    path = ROOT / name
    if not path.is_file():
        rows.append({'path': name, 'status': 'missing'})
        continue
    splits = Counter()
    missing = 0
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        # Only these fields leave this loop; never write any other source field.
        row = json.loads(line)
        split = row.get('split', 'holdout' if 'holdout' in name else 'unknown')
        family = row.get('family_id')
        splits[split] += 1
        if family:
            (held_families if split == 'holdout' else dev_families).add(str(family))
        else:
            missing += 1
    rows.append({'path': name, 'sha256': sha256(path.read_bytes()).hexdigest(),
                 'split_counts': dict(splits), 'missing_family_id': missing,
                 'content_exposed_to_report_or_model': False})
report = {
    'new_label_file': str(new_path.relative_to(ROOT)).replace('\\', '/'),
    'new_label_sha256': sha256(new_path.read_bytes()).hexdigest(),
    'new_case_count': len(new), 'new_family_count': len({row['family_id'] for row in new}),
    'sources': rows,
    'exact_held_family_collisions_new_ids': [row['id'] for row in new if row['family_id'] in held_families],
    'exact_dev_family_collisions_new_ids': [row['id'] for row in new if row['family_id'] in dev_families],
    'predictions_generated': 0,
    'limitation': 'Different family namespaces and missing older family metadata prevent proof of semantic independence. No held question/SQL/answer was used to fill this gap. Synthetic DEV only; root historical exposure remains disclosed.',
}
target = EXP / 'checks/root-family-metadata.json'
with target.open('x', encoding='utf-8') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
print(json.dumps({key: report[key] for key in ['new_case_count','new_family_count','exact_held_family_collisions_new_ids','exact_dev_family_collisions_new_ids','predictions_generated']}, ensure_ascii=False))
