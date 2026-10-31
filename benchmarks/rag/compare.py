"""Paired comparison; reject changed questions, sources, parameters or scoring code."""
import argparse
import json
from pathlib import Path
from benchmarks.rag.report import paired


def compare_runs(before,after,before_strategy='bm25',after_strategy='hybrid_rerank',allow_code_change=False):
    before,after=Path(before),Path(after)
    manifests=[json.loads((p/'manifest.json').read_text('utf-8')) for p in (before,after)]
    if any(m.get('mode')=='generation' for m in manifests):raise ValueError('Fixed-evidence diagnosis is not a retrieval accuracy comparison')
    keys=['dataset_sha256','top_k','candidate_k_per_channel','cache_protocol','mode','condition','repeat','model','answer_mode']
    if not allow_code_change:keys+=['code_sha256']
    for key in keys:
        if manifests[0].get(key)!=manifests[1].get(key):raise ValueError('Incompatible experiment field: '+key)
    for key in ['chunks_sha256','chunking','dense_embedding']:
        if manifests[0]['index'].get(key)!=manifests[1]['index'].get(key):raise ValueError('Different corpus/index: '+key)
    def read(path,strategy,label):
        rows=[json.loads(line) for line in (path/'predictions.jsonl').read_text('utf-8').splitlines() if line.strip()]
        return [dict(r,strategy=label) for r in rows if r['strategy']==strategy]
    left,right=read(before,before_strategy,'before'),read(after,after_strategy,'after')
    if not left or not right:raise ValueError('Requested strategy has no predictions')
    keyed={(r['id'],r['repeat']):r for r in left}
    for r in right:
        previous=keyed.get((r['id'],r['repeat']))
        if previous is None:raise ValueError('Different case/repeat set')
        for key in ['question','retrieval_question','allowed_doc_ids','answerable']:
            if previous.get(key)!=r.get(key):raise ValueError('Changed question/scope: '+r['id'])
    return {'comparison':paired(left+right,baseline='before'),'code_change_allowed':allow_code_change,
            'before_code':manifests[0]['code_sha256'],'after_code':manifests[1]['code_sha256'],
            'claim':'paired source-evidence retrieval diagnostics on dev; no significance or answer-quality claim'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True)
    p.add_argument('--before-strategy',default='bm25');p.add_argument('--after-strategy',default='hybrid_rerank');p.add_argument('--allow-code-change',action='store_true');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=compare_runs(a.before,a.after,a.before_strategy,a.after_strategy,a.allow_code_change)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
