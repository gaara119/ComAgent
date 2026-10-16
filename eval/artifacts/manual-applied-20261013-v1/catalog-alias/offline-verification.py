from __future__ import annotations
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import yaml
from qa_agent.nlu.value_index import ValueRecord
from qa_agent.sql.catalog import load_catalog
from scripts.apply_manual_catalog_aliases import structural_view, CONDITIONAL_LIMIT, INSUFFICIENT_LIMIT
from scripts.build_value_index import load_reviewed_aliases

def sha(path): return sha256(path.read_bytes()).hexdigest()
source = ROOT / 'data/catalog/adventureworks.yaml'
target = ROOT / 'data/catalog/adventureworks-manual-applied-v1.yaml'
old = yaml.safe_load(source.read_text(encoding='utf-8-sig'))
new = yaml.safe_load(target.read_text(encoding='utf-8-sig'))
ledger = json.loads((ROOT/'notes/manual-applied-20261013-v1/catalog-alias-application.json').read_text(encoding='utf-8'))
catalog = load_catalog(target)
checks = {}
checks['actual_structure_keys_rows_samples_unchanged'] = structural_view(old) == structural_view(new)
checks['runtime_load_68_tables_456_columns'] = len(catalog.tables) == 68 and sum(len(t.columns) for t in catalog.tables) == 456
checks['all_historical_input_hashes_unchanged'] = all(sha(ROOT/path) == expected for path, expected in ledger['input_sha256'].items())
checks['output_catalog_hash_matches_ledger'] = sha(target) == ledger['output_catalog_sha256']
alias_path = ROOT/'data/aliases/aliases-manual-applied-v1.csv'
checks['output_alias_hash_matches_ledger'] = sha(alias_path) == ledger['output_aliases_sha256']
with alias_path.open(encoding='utf-8-sig', newline='') as stream:
    aliases = list(csv.DictReader(stream))
checks['exactly_81_original_alias_relationship_ids'] = len(aliases) == len({r['alias_id'] for r in aliases}) == 81
unsupported = {row['alias_id']: row for row in aliases if row['alias_id'] in {'a-0c47392129d13dd6','a-c748b229db869a4e'}}
checks['two_evidence_insufficient_relationships_are_disabled'] = len(unsupported) == 2 and all(r['review_status']=='evidence_insufficient' for r in unsupported.values())
checks['both_lao_mei_relationships_remain_direct_approved'] = len([r for r in aliases if r['alias']=='老美' and r['review_status']=='approved' and r['standard_value']=='USA']) == 2
values = [ValueRecord.from_dict(json.loads(line)) for line in (ROOT/'data/indexes/values-oct12-approved/values.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
current, before_audit = load_reviewed_aliases(ROOT/'data/aliases/aliases-oct12-approved.csv', values)
applied, after_audit = load_reviewed_aliases(alias_path, values)
checks['alias_builder_accepts_56_direct_23_conditional_2_excluded'] = after_audit['accepted_count']==79 and after_audit['direct_count']==56 and after_audit['candidate_only_count']==23 and after_audit['excluded_count']==2 and not after_audit['invalid']
checks['candidate_relations_not_promoted_to_unique_binding'] = [(r.alias_id,r.kind) for r in current] == [(r.alias_id,r.kind) for r in applied]
checks['same_approved_alias_records_can_reuse_old_embeddings'] = [r.as_dict() for r in current] == [r.as_dict() for r in applied]
checks['condition_and_evidence_limits_reach_real_runtime_prompt'] = CONDITIONAL_LIMIT in catalog.prompt_schema() and INSUFFICIENT_LIMIT in catalog.prompt_schema()
archive = catalog.get_table('transactionhistoryarchive', 'production').description
checks['archive_description_no_longer_asserts_business_invalidity'] = '不据此判断交易已无效' in archive and '不代表当前有效交易' not in archive
field = next(c for c in catalog.get_table('stateprovince', 'person').columns if c.name=='isonlystateprovinceflag')
checks['unproven_boolean_meanings_not_in_runtime_description'] = '不足以确定 true/false' in field.description and '证据不足的业务映射' in field.description
result = {'scope':'Offline checks on formal catalog/alias versions only; no model calls, database writes or holdout reads', 'checks': checks,
          'passed':sum(checks.values()), 'total':len(checks), 'all_passed':all(checks.values()), 'alias_builder_audit':after_audit,
          'runtime_configuration_switch_owned_by_parent_task':True}
output = ROOT/'eval/artifacts/manual-applied-20261013-v1/catalog-alias/offline-verification-portable.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(0 if result['all_passed'] else 1)
