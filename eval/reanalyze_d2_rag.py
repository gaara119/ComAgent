"""Recheck saved real responses without another API/model call; preserve raw runs."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.d2_rag_eval import load_d2_rag, evidence_diagnostics, candidate_gold_hit
from qa_agent.rag.index import load_index
from qa_agent.config import get_settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--responses', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, default=ROOT/'eval/datasets/rag_single.jsonl')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; preserve previous analysis')
    actual = [json.loads(line) for line in args.responses.read_text(encoding='utf8').splitlines() if line]
    dataset = {r['id']: r for r in load_d2_rag(args.dataset)}
    if not actual or len({r['id'] for r in actual}) != len(actual):
        parser.error('Actual responses must be nonempty and unique')
    settings = get_settings()
    records, metadata = load_index(settings=settings)
    chunks = {r['chunk_id']: r for r in records}
    rows = []
    for row in actual:
        item = dataset[row['id']]
        if item['split'] != 'dev':
            parser.error('D2 offline analysis only accepts actually run development responses')
        payload = row.get('response') or {}
        candidates = (payload.get('metadata') or {}).get('retrieved_pages', [])
        history = item.get('exposure_history') or {}
        rows.append({'id': row['id'], 'is_d1_common': bool(history.get('d1_model_exposed') or history.get('model_prediction_count',0)>0),
                     'answerable': item.get('answerable',True),
                     'hit_at_5': candidate_gold_hit(item,candidates,chunks) if item.get('answerable',True) else None,
                     **evidence_diagnostics(item,payload,chunks)})
    available = [r for r in rows if r['answerable']]
    output = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'method': 'Offline mechanical reanalysis of preserved actual API responses; zero additional predictions/model calls',
              'responses_sha256': hashlib.sha256(args.responses.read_bytes()).hexdigest(),
              'dataset_sha256': hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
              'index_chunks_sha256': metadata['chunks_sha256'],
              'strict_quote_definition': 'Complete normalized reference or at least one complete registered gold quote contained in a Top5 chunk; a short chunk contained in a long reference is insufficient',
              'hit_at_5': {'passed':sum(r['hit_at_5'] for r in available),'denominator':len(available)},
              'complete_gold_quote_hit_at_5': {'passed':sum(r['exact_gold_quote_hit_at_5'] for r in available),'denominator':len(available)},
              'd1_common_count': sum(r['is_d1_common'] for r in rows),
              'new_d2_count': sum(not r['is_d1_common'] for r in rows),
              'human_review_count':0, 'records': rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({key:value for key,value in output.items() if key!='records'},ensure_ascii=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
