"""Confirm the candidate-domain retry fix leaves existing business logic intact."""
import ast
import copy
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
old_path = ROOT / 'eval/artifacts/manual-applied-20261013-v1/aw-live-001/source/pruner-before-repair.py'
new_path = ROOT / 'qa_agent/sql/pruner.py'
old, new = [ast.parse(path.read_text(encoding='utf-8-sig')) for path in (old_path, new_path)]

def prompt(tree):
    return next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'PRUNER_PROMPT' for target in node.targets))

def method(tree, name):
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'SchemaPruner')
    return next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)

normalized_prune = copy.deepcopy(method(new, 'prune'))
replacements = 0
for node in ast.walk(normalized_prune):
    if isinstance(node, ast.keyword) and node.arg == 'response_model' and isinstance(node.value, ast.Call):
        if isinstance(node.value.func, ast.Name) and node.value.func.id == 'make_pruning_decision_model':
            node.value = ast.Name(id='PruningDecision', ctx=ast.Load())
            replacements += 1
checks = {
    'business_pruner_prompt_exactly_unchanged': prompt(old) == prompt(new),
    'required_bindings_logic_exactly_unchanged': ast.dump(method(old, '_required')) == ast.dump(method(new, '_required')),
    'bounded_recall_and_real_bridge_logic_exactly_unchanged': ast.dump(method(old, '_bounded_candidates')) == ast.dump(method(new, '_bounded_candidates')),
    'prune_algorithm_only_changes_response_model_constraint': replacements == 1 and ast.dump(method(old, 'prune')) == ast.dump(normalized_prune),
}
result = {'checks': checks, 'all_passed': all(checks.values()),
          'old_source_sha256': sha256(old_path.read_bytes()).hexdigest(),
          'new_source_sha256': sha256(new_path.read_bytes()).hexdigest(),
          'business_prompt_sha256': sha256(prompt(new).encode('utf-8')).hexdigest()}
(Path(__file__).parent / 'semantic-scope-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(0 if result['all_passed'] else 1)
