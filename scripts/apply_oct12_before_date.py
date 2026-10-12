"""Apply only the independently reviewed strict-before candidate by content hash."""
from datetime import datetime,timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--version',required=True,choices=['v4','v5','v6'])
    args=parser.parse_args()
    folder=ROOT/'notes/oct12/staging/sql22'
    metadata=json.loads((folder/f'candidate-meta-{args.version}.json').read_text(encoding='utf-8'))
    review=json.loads((folder/f'ai-review-{args.version}-pass-2-probes.json').read_text(encoding='utf-8'))
    if review.get('passed') is not True or review.get('candidate_sha256')!=metadata['candidate_sha256']:
        raise ValueError('Independent review is not accepted')
    source=ROOT/metadata['source_file']
    candidate=ROOT/metadata['candidate_file']
    before=source.read_bytes();after=candidate.read_bytes()
    if sha256(before).hexdigest()!=metadata['source_sha256'] or sha256(after).hexdigest()!=metadata['candidate_sha256']:
        raise ValueError('Candidate or runtime baseline changed')
    if sha256((ROOT/metadata['formal_test_file']).read_bytes()).hexdigest()!=metadata['formal_test_sha256']:
        raise ValueError('Reviewed formal test changed')
    out=ROOT/'eval/artifacts/oct12/repairs-source-004'
    if out.exists():
        raise ValueError('Preserve prior application evidence')
    out.mkdir(parents=True)
    (out/'rules.py.before.txt').write_bytes(before)
    source.write_bytes(after)
    record={'created_at_utc':datetime.now(timezone.utc).isoformat(),'file':metadata['source_file'],
        'before_sha256':sha256(before).hexdigest(),'after_sha256':sha256(after).hexdigest(),
        'self_review':metadata,'independent_review':review,
        'gold_changes':0,'human_review_changes':0,'held_predictions':0}
    (out/'application.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'applied':metadata['source_file'],'after_sha256':record['after_sha256']},ensure_ascii=False))

if __name__=='__main__':
    main()
