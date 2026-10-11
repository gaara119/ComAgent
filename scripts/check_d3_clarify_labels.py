"""Check only the new D3 dev rule labels and preserve raw engineering commands."""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa_agent.clarify.rules import RuleEngine, SemanticIntent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'eval/artifacts/d3/b/module-check-v1')
    parser.add_argument('--include-independent-review-tests',action='store_true')
    args=parser.parse_args()
    output=args.output if args.output.is_absolute() else ROOT/args.output
    if output.exists():
        raise SystemExit('Output already exists; preserve previous evidence.')
    output.mkdir(parents=True)
    cmd=[sys.executable,'-B','-m','pytest','tests/test_d3_clarify.py']
    if args.include_independent_review_tests:
        cmd.append('tests/test_d3_clarify_ai_counterexamples.py')
    cmd+=['-q','--basetemp','.runtime/pytest-d3-b-recorded']
    completed=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (output/'pytest.stdout.txt').write_text(completed.stdout,encoding='utf-8')
    (output/'pytest.stderr.txt').write_text(completed.stderr,encoding='utf-8')
    (output/'command.json').write_text(json.dumps({'command':cmd,'cwd':str(ROOT),'exit_code':completed.returncode,
        'created_at_utc':datetime.now(timezone.utc).isoformat()},ensure_ascii=False,indent=2),encoding='utf-8')
    source=ROOT/'eval/datasets/d3/clarify/dev.jsonl'
    records=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines() if line]
    checks=[]
    for row in records:
        semantic=dict(row['reference_semantics'])
        ambiguity=semantic.pop('_ambiguity',None)
        # Canonical pairs are verified in D1 catalog / D2 value-index audit.
        # This is a rule fixture, not a measured linker/model answer.
        mentions=([{'mention_id':'fixture-'+row['id'],'original_text':ambiguity,'candidates':[
            {'candidate_id':'fixture-rock','column':'genre.name','standard_value':'Rock'},
            {'candidate_id':'fixture-roll','column':'genre.name','standard_value':'Rock And Roll'}]}] if ambiguity else [])
        result=RuleEngine().evaluate(row['question'],SemanticIntent.model_validate(semantic),ambiguous=mentions,available_years=[2021,2022,2023,2024,2025])
        checks.append({'id':row['id'],'expected_level':row['expected_level'],'actual_level':result.level,
                       'passed':result.level==row['expected_level'],'issues':[item.as_dict() for item in result.issues],
                       'assumptions':result.assumptions,'mode':'programmatic reference-semantics rule check; no model prediction'})
    record={'source':str(source.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha256(source.read_bytes()).hexdigest(),
            'dev_cases':len(checks),'passed':sum(item['passed'] for item in checks),'holdout_predictions':0,
            'pytest_exit_code':completed.returncode,'checks':checks,'human_review_status':'pending_human_review'}
    (output/'rule-label-checks.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({key:record[key] for key in ('dev_cases','passed','pytest_exit_code','holdout_predictions')},ensure_ascii=False))
    return int(completed.returncode!=0 or not all(item['passed'] for item in checks))


if __name__=='__main__':raise SystemExit(main())
