"""Run the real RAG tools against versioned, source-anchored development labels."""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter, monotonic

from qa_agent.config import PROJECT_ROOT, Settings, get_settings, sanitize_error
from qa_agent.documents import load_documents
from qa_agent.rag.index import build_index, load_index
from qa_agent.rag.evaluation import retrieve_for_evaluation, generate_for_evaluation
from qa_agent.rag.retrieval_cache import clear_retrieval_cache
from benchmarks.rag.dataset import load_dataset, verify_sources
from benchmarks.rag.metrics import retrieval_metrics, answer_diagnostics


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_fingerprint():
    paths = [*PROJECT_ROOT.glob('qa_agent/rag/*.py'), *Path(__file__).parent.glob('*.py'),
             *[PROJECT_ROOT/'qa_agent'/name for name in ('llm.py','config.py','documents.py','trace.py','schemas.py')],
             PROJECT_ROOT/'requirements-runtime.txt']
    files = {p.relative_to(PROJECT_ROOT).as_posix(): hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
             for p in sorted(set(paths))}
    return files, hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def fixed_evidence(case, documents, all_chunks, condition):
    """Gold evidence is used ONLY by this explicitly diagnostic generator mode."""
    labels = case.required_evidence
    if condition == 'missing_key':
        labels = labels[:-1]
    by_id = {d['doc_id']: d for d in documents}
    selected = [{'chunk_id': 'reference-'+e.id, 'doc_id': e.doc_id,
                 'doc_title': by_id[e.doc_id]['title'], 'page': e.page,
                 'section_path': e.section_path, 'text': e.quote, 'bbox': None,
                 'label_origin': e.id} for e in labels]
    if condition == 'reference_noise':
        positives = {e.doc_id for e in case.required_evidence}
        noise = [dict(c) for c in all_chunks if c['doc_id'] in case.doc_ids and c['doc_id'] not in positives][:2]
        selected.extend(noise)
    return [dict(c, evidence_id=f'E{i}') for i, c in enumerate(selected, 1)]


def error_categories(row):
    if row.get('error'):
        return ['execution_failure']
    errors = []
    metrics = row.get('retrieval', {})
    if metrics.get('eligible'):
        if metrics.get('recall@5', 0) < 1:
            errors.append('evidence_missing_at_5')
        if metrics.get('mrr@5', 0) < 1:
            errors.append('first_evidence_below_rank_1')
        availability = row.get('retrieval_diagnostics',{})
        if availability.get('corpus_evidence_coverage',1) < 1:
            errors.append('chunk_evidence_fragmented_or_absent')
        elif availability.get('candidate_evidence_coverage',1) < 1:
            errors.append('candidate_recall_failure')
        elif metrics.get('recall@5',0) < 1:
            errors.append('ranking_cutoff_failure')
    diagnostics = row.get('answer_diagnostics', {})
    if diagnostics.get('citation_ids_valid') is False:
        errors.append('invalid_citation_id')
    # EMPTY_RESULT is a real system status, never inferred from an English keyword.
    if row.get('generation'):
        refused = row['generation'].get('status') == 'EMPTY_RESULT'
        answerable = row['answerable'] if row.get('evidence_condition_answerable') is None else row['evidence_condition_answerable']
        if answerable and refused:
            errors.append('answerable_refused')
        elif not answerable and not refused:
            errors.append('unanswerable_not_refused')
    return errors


def main(mode=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--dataset', type=Path, default=Path('benchmarks/rag/fixtures/dataset.json'))
    parser.add_argument('--output', type=Path, required=True, help='New directory; existing evidence is never overwritten')
    parser.add_argument('--work-dir', type=Path, default=Path('.runtime/rag-benchmark'))
    parser.add_argument('--mode', choices=['retrieval','generation','end_to_end'], default=mode or 'retrieval')
    parser.add_argument('--strategies', nargs='+', choices=['bm25','dense','hybrid','hybrid_rerank'], default=['bm25'])
    parser.add_argument('--embedding', choices=['none','bge'], default='none')
    parser.add_argument('--model-path', type=Path, default=Path('data/models/bge-m3'))
    parser.add_argument('--answer-mode', choices=['extractive','llm'], default='extractive')
    parser.add_argument('--condition', choices=['reference','reference_noise','missing_key'], default='reference')
    parser.add_argument('--repeat', type=int, choices=range(1,11), default=1)
    parser.add_argument('--top-k', type=int, choices=range(5,21), default=5)
    parser.add_argument('--candidate-k', type=int, default=20)
    parser.add_argument('--chunk-chars', type=int, default=500)
    parser.add_argument('--overlap', type=int, default=80)
    parser.add_argument('--cache', choices=['cold','warm'], default='cold')
    parser.add_argument('--max-model-calls', type=int, default=0)
    parser.add_argument('--deadline-seconds', type=int, default=600)
    pre=argparse.ArgumentParser(add_help=False);pre.add_argument('--config',type=Path)
    selected,_=pre.parse_known_args()
    if selected.config:
        config=json.loads(selected.config.read_text('utf-8'))
        allowed={'dataset','strategies','embedding','top_k','candidate_k_per_channel','chunk_chars','overlap','rrf_k','cache','repeat','answer_mode','scope','semantic_review'}
        if set(config)-allowed:parser.error('Unknown config fields: '+str(set(config)-allowed))
        if config.get('rrf_k',60)!=60 or config.get('scope','dev_only')!='dev_only':parser.error('This entry fixes rrf_k=60 and dev_only scope')
        config={('candidate_k' if k=='candidate_k_per_channel' else k):v for k,v in config.items() if k not in {'rrf_k','scope','semantic_review'}}
        parser.set_defaults(**config)
    args = parser.parse_args()
    if args.repeat not in range(1,11) or args.top_k not in range(5,21) or any(s not in {'bm25','dense','hybrid','hybrid_rerank'} for s in args.strategies):
        parser.error('Invalid config repeat/top_k/strategies')
    if args.output.exists():
        parser.error('Output already exists. Choose a new run directory.')
    if len(set(args.strategies)) != len(args.strategies):
        parser.error('Strategies must be unique')
    if args.candidate_k < args.top_k or args.chunk_chars < 200 or not 0 <= args.overlap < args.chunk_chars:
        parser.error('Require candidate-k >= top-k, chunk-chars >=200, 0<=overlap<chunk-chars')
    if args.deadline_seconds < 1:
        parser.error('deadline-seconds must be positive')
    if args.mode == 'generation' and len(args.strategies) != 1:
        parser.error('Fixed-evidence diagnosis has no retrieval strategy comparison; pass one strategy')
    if args.answer_mode == 'llm' and args.mode != 'retrieval' and args.max_model_calls < 2:
        parser.error('Paid generation requires explicit --max-model-calls >=2; default makes zero API calls')
    dataset_path = args.dataset.resolve()
    dataset = load_dataset(dataset_path, split='dev')
    sources = verify_sources(dataset, dataset_path)
    manifest = (dataset_path.parent / dataset.corpus_manifest).resolve()
    settings = (get_settings() if args.answer_mode == 'llm' and args.mode != 'retrieval' else Settings(db_url=''))
    # A unique work directory avoids overwriting a user index or changing another experiment.
    index_path = (args.work_dir / ('index-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))).resolve()
    model_path = args.model_path.resolve() if args.embedding == 'bge' else index_path/'.disabled-model'
    settings = replace(settings, db_url='', aw_db_url='', rag_manifest_path=manifest, rag_index_path=index_path,
        bge_model_path=model_path, rag_top_k=args.top_k, rag_candidate_k=args.candidate_k,
        rag_chunk_chars=args.chunk_chars, rag_chunk_overlap=args.overlap, rag_answer_mode=args.answer_mode,
        llm_max_attempts=1, llm_request_max_attempts=2, llm_timeout_seconds=60)
    if args.answer_mode == 'llm' and args.mode != 'retrieval' and not settings.llm_configured:
        parser.error('Configure a local model API key before explicitly enabling paid generation')
    args.output.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    code_files, code_hash = source_fingerprint()
    build_began = perf_counter()
    metadata = build_index(manifest, index_path, settings=settings)
    build_ms = (perf_counter()-build_began)*1000
    chunks, _ = load_index(settings=settings)
    documents = load_documents(manifest)
    packages = {}
    for name in ['numpy','rank-bm25','onnxruntime','pydantic','openai']:
        try: packages[name] = version(name)
        except PackageNotFoundError: packages[name] = None
    try:
        commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=PROJECT_ROOT, text=True).strip()
        dirty = subprocess.check_output(['git','diff','--name-only','HEAD'], cwd=PROJECT_ROOT, text=True).splitlines()
    except (OSError,subprocess.CalledProcessError):
        commit, dirty = None, ['git_unavailable']
    manifest_record = {'format_version':1, 'dataset_version':dataset.version, 'dataset_sha256':digest(dataset_path),
        'sources':sources,'code_sha256':code_hash,'source_files':code_files, 'commit':commit,'tracked_changes':dirty,
        'source_hash_protocol':'sha256 of code text with CRLF normalized to LF; document hashes use raw bytes',
        'command':sys.argv,'started_at':started,'mode':args.mode,'condition':args.condition if args.mode=='generation' else 'retrieved',
        'config':{'path':str(args.config),'sha256':digest(args.config)} if args.config else None,
        'answer_mode':args.answer_mode,'strategies':args.strategies,'split':'dev','heldout_read':False,
        'cache_protocol':args.cache,'cache_scope':'retrieval caches; OS page cache and encoder session are not flushed',
        'repeat':args.repeat,'top_k':args.top_k,'candidate_k_per_channel':args.candidate_k,
        'candidate_budget_note':'Hybrid may fuse up to 2*candidate_k distinct candidates; total candidate budgets are not equated.',
        'index':{'chunk_count':len(chunks),'chunks_sha256':metadata['chunks_sha256'],'chunking':metadata['chunking'],
                 'dense_embedding':metadata.get('dense_embedding'),'build_ms':round(build_ms,3)},
        'runtime':{'python':platform.python_version(),'platform':platform.platform(),'processor':platform.processor(),'packages':packages},
        'model':{'requested':settings.llm_model if args.answer_mode=='llm' and args.mode!='retrieval' else None,
                 'temperature':settings.llm_temperature,'timeout':settings.llm_timeout_seconds,
                 'max_attempts':1,'request_max_attempts':2,'max_tokens':settings.llm_max_tokens},
        'budget':{'max_model_calls':args.max_model_calls,'reserved_per_question':2,'deadline_seconds':args.deadline_seconds},
        'reference_review':'pending_human_review; authored synthetic development fixtures',
        'semantic_metrics':'not_verified unless separately supplied, prediction-hash-bound assessments are applied',
        'scope_note':'Multi-turn retrieval_question is supplied explicitly; this does not test conversation rewriting.'}
    write_json(args.output/'manifest.json', manifest_record)
    deadline = monotonic()+args.deadline_seconds
    calls_reserved = 0
    rows = []
    with (args.output/'predictions.jsonl').open('w',encoding='utf-8') as stream:
        # Rotate strategy order by repeat to avoid assigning all first-use cost to one arm.
        for repeat in range(args.repeat):
            order = args.strategies[repeat % len(args.strategies):]+args.strategies[:repeat % len(args.strategies)]
            for strategy in order:
                for case in dataset.cases:
                    row = {'id':case.id,'strategy':strategy,'repeat':repeat+1,'category':case.category,
                           'family_id':case.family_id,'answerable':case.answerable,'question':case.question,
                           'retrieval_question':case.retrieval_question or case.question,'allowed_doc_ids':case.doc_ids,
                           'reference_review_status':case.review_status,'error':None}
                    row['evidence_condition_answerable'] = (case.answerable and args.condition!='missing_key') if args.mode=='generation' else None
                    began = perf_counter()
                    try:
                        if monotonic() >= deadline:
                            raise RuntimeError('stage_deadline_exceeded; request not sent')
                        if strategy != 'bm25' and not metadata.get('dense_embedding',{}).get('enabled'):
                            raise RuntimeError('dense_not_available; comparison arm not verified, no silent BM25 fallback')
                        if args.cache == 'cold': clear_retrieval_cache()
                        if args.mode == 'generation':
                            evidence = fixed_evidence(case, documents, chunks, args.condition)
                            retrieval = {'diagnostic_fixed_evidence':True,'allowed_doc_ids':case.doc_ids}
                        else:
                            if args.cache == 'warm':
                                retrieve_for_evaluation(case.retrieval_question or case.question,case.doc_ids,settings=settings,strategy=strategy)
                                row['warmup_ms'] = round((perf_counter()-began)*1000,3)
                                began = perf_counter()
                            evidence, retrieval = retrieve_for_evaluation(case.retrieval_question or case.question,case.doc_ids,settings=settings,strategy=strategy)
                        row['input_chunks'] = evidence
                        row['retrieval_trace'] = retrieval
                        if args.mode != 'retrieval':
                            if args.answer_mode == 'llm':
                                if calls_reserved+2 > args.max_model_calls or monotonic()+120 > deadline:
                                    raise RuntimeError('generation_budget_exhausted; request not sent')
                                calls_reserved += 2  # Includes failed/missing-usage attempts; never automatically extended.
                            generated = generate_for_evaluation(case.retrieval_question or case.question,evidence,
                                                                settings=settings,answer_mode=args.answer_mode)
                            row['generation'] = generated
                            if generated.get('error'): row['error'] = generated['error']
                        # Stop the tool clock before consulting any labels for scoring.
                        row['latency_ms'] = round((perf_counter()-began)*1000,3)
                        allowed_chunks = [c for c in chunks if c['doc_id'] in case.doc_ids]
                        row['retrieval'] = (retrieval_metrics(evidence,case.required_evidence,k=5,corpus_chunks=allowed_chunks)
                                            if args.mode!='generation' else {'eligible':False,'diagnostic_fixed_evidence':True})
                        if args.mode != 'generation' and case.required_evidence:
                            candidate_ids={c['chunk_id'] for channel in retrieval.get('rankings',{}).values() for c in channel}
                            candidates=[c for c in allowed_chunks if c['chunk_id'] in candidate_ids]
                            row['retrieval_diagnostics']={
                                'corpus_evidence_coverage':retrieval_metrics(allowed_chunks,case.required_evidence,k=max(1,len(allowed_chunks)))['evidence_coverage@'+str(max(1,len(allowed_chunks)))],
                                'candidate_evidence_coverage':retrieval_metrics(candidates,case.required_evidence,k=max(1,len(candidates)))['evidence_coverage@'+str(max(1,len(candidates)))]}
                        if args.mode != 'retrieval':
                            row['answer_diagnostics'] = answer_diagnostics(generated['answer'],generated['citation_ids'],
                                evidence,case.facts,case.answerable,status=generated['status'])
                    except Exception as exc:
                        row['error'] = {'type':type(exc).__name__,'message':sanitize_error(exc,settings)}
                    row.setdefault('latency_ms',round((perf_counter()-began)*1000,3))
                    row['error_categories'] = error_categories(row)
                    row['prediction_sha256'] = hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
                    rows.append(row)
                    stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
                print(f'{args.mode} {strategy} repeat={repeat+1} done',flush=True)
    assert source_fingerprint()[1] == code_hash, 'Source changed during run; results are invalid'
    verify_sources(dataset,dataset_path)
    manifest_record.update(finished_at=datetime.now(timezone.utc).isoformat(),logical_question_count=len(rows),
                           model_calls_reserved=calls_reserved)
    write_json(args.output/'manifest.json',manifest_record)
    from benchmarks.rag.report import write_report
    write_report(args.output,rows,manifest_record)
    print(json.dumps({'output':str(args.output),'logical_questions':len(rows),'errors':sum(bool(r['error']) for r in rows)},ensure_ascii=False))
    return 1 if any(r['error'] for r in rows) else 0


def write_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
