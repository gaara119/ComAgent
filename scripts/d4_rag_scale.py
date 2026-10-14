"""D4 real 10/100 PDF-page libraries and 20 DEV questions x 3 per scale.

The ten evidence pages come from already exposed development questions. Ten
original questions plus ten explicitly marked equivalent variants are used;
no held labels, complete OHR QA archive or system-generated labels are read.
Original physical page numbers and chunks remain unchanged. Real BGE vectors
are subset from the verified existing index, not duplicated or synthesized.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import csv
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np

from eval.rag_metrics import answer_surface_match, normalize_text
from qa_agent.config import get_settings, sanitize_error
from qa_agent.llm import JsonLLM
from qa_agent.rag.answer import answer_from_chunks, citation_coverage_diagnostics
from qa_agent.rag.index import load_index
from qa_agent.rag.retriever import retrieve
from qa_agent.trace import TraceRecorder
from scripts.d4_bench_utils import provenance, summarize, trace_cost, write_json


VARIANTS = {
    "rag-02":"Within how many days after Physician Sales & Service, Inc.'s first fiscal quarter ends must the financial results of the combined post-Merger operations be published?",
    "rag-03":"For what period in years following the Merger's effective date does PSS agree to file every report required under Section 13 of the Securities Exchange Act of 1934?",
    "rag-05":"Around Holmfirth and Glossop, which rivers provide drainage on the western side of the primary watershed?",
    "rag-06":"Which arable crops are considered the most satisfactory for the soils of the Coal Measures?",
    "rag-10":"Under the FCC rules, what digital-device class is specified for this equipment?",
    "rag-11":"What application enables movies to be created and shared in just minutes?",
    "rag-15":"Which five fundamental capabilities do ASQ and Forbes Insights identify as essential to a successful organizational culture?",
    "rag-16":"According to the research, what percentage of senior leaders describe their quality programs as advanced or world class?",
    "rag-18":"What measure quantifies the correlation of attention distributions on label words with the model's final prediction?",
    "rag-19":"On which datasets did the proposed anchor reweighting method yield significant performance improvements?",
}


def efficiency_cases(source):
    all_cases = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(all_cases) != 21 or any(case.get("split") != "dev" for case in all_cases):
        raise ValueError("Only the existing 21-row safe development view is permitted")
    by_id = {case["id"]:case for case in all_cases}
    cases, pages = [], set()
    for original_id, wording in VARIANTS.items():
        case = by_id[original_id]
        if case.get("source_type") != "ohr_official" or len(case.get("physical_pages",[])) != 1:
            raise ValueError("Each efficiency family must be an exposed OHR PDF question with one verified page")
        pages.add((case["doc_id"],case["physical_pages"][0]))
        original = copy.deepcopy(case)
        original.update(efficiency_id=f"d4-eff-{original_id}-original",efficiency_source="existing DEV original")
        variant = copy.deepcopy(case)
        variant.update(question=wording,efficiency_id=f"d4-eff-{original_id}-variant",
            efficiency_source="project-authored equivalent English efficiency variant",
            source_question=case["question"],original_dev_id=original_id,
            gold_review={"status":"pending_human_review","reviewer":None,"review_date":None},
            ai_review={"pass_1":"AI建议通过","pass_1_reason":"保留原题对象、期间、数量单位和关系，仅英语表达改写；来源答案及证据继承原DEV",
                       "pass_2":"AI建议通过","pass_2_reason":"再逐句核对主体/属性/条件，不增加算法指令或新筛选条件；不充当人工签字"})
        cases.extend([original,variant])
    if len(cases) != 20 or len(pages) != 10:
        raise ValueError("Exactly twenty questions over ten distinct real PDF evidence pages are required")
    return cases,pages


def prepare(output: Path):
    if output.exists():
        raise ValueError("Choose a fresh library directory; previous indexes and evidence remain unchanged")
    output.mkdir(parents=True)
    settings = get_settings()
    source = ROOT / "eval/artifacts/d2-final/review/rag-dev-view.jsonl"
    cases,evidence_pages = efficiency_cases(source)
    chunks,source_meta = load_index(settings=settings)
    source_matrix = Path(settings.rag_index_path) / "embeddings.npy"
    dense = source_meta.get("dense_embedding",{})
    if not dense.get("enabled") or hashlib.sha256(source_matrix.read_bytes()).hexdigest() != dense.get("vectors_sha256"):
        raise ValueError("Efficiency libraries require the existing verified actual BGE dense index")
    vectors = np.load(source_matrix,allow_pickle=False,mmap_mode="r")
    doc_ids = sorted({doc for doc,_ in evidence_pages})
    known_pdf = {doc["doc_id"] for doc in source_meta["documents"] if doc["format"] == "pdf"}
    if not set(doc_ids) <= known_pdf:
        raise ValueError("All selected source documents must be real PDFs")
    available = {(chunk["doc_id"],chunk["page"]) for chunk in chunks
                 if chunk["doc_id"] in doc_ids and isinstance(chunk.get("page"),int)}
    if not evidence_pages <= available or len(available) < 100:
        raise ValueError(f"Cannot build exact 10/100 real-page libraries: actual available {len(available)}")
    # Add diverse real pages round-robin among the same five DEV documents.
    by_doc = {doc:sorted(page for name,page in available-evidence_pages if name==doc) for doc in doc_ids}
    expansion = []
    while len(expansion) < 90:
        progress = False
        for doc in doc_ids:
            if by_doc[doc] and len(expansion)<90:
                expansion.append((doc,by_doc[doc].pop(0)))
                progress = True
        if not progress:
            raise ValueError("Insufficient distinct development-document pages for 100-page library")
    with settings.rag_manifest_path.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        header=reader.fieldnames
        documents=[row for row in reader if row["doc_id"] in doc_ids]
    if len(documents)!=len(doc_ids):
        raise ValueError("Source manifest must identify every development PDF exactly once")
    reports=[]
    started=perf_counter()
    for count,pages in ((10,evidence_pages),(100,evidence_pages|set(expansion))):
        library=output/f"pages-{count}"
        library.mkdir()
        selected_indices=[index for index,chunk in enumerate(chunks) if (chunk["doc_id"],chunk.get("page")) in pages]
        selected_chunks=[chunks[index] for index in selected_indices]
        selected_vectors=np.asarray(vectors[selected_indices],dtype=np.float32)
        manifest=library/"manifest.csv"
        with manifest.open("w",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=header)
            writer.writeheader();writer.writerows(documents)
        raw="".join(json.dumps(chunk,ensure_ascii=False)+"\n" for chunk in selected_chunks).encode("utf-8")
        (library/"chunks.jsonl").write_bytes(raw)
        np.save(library/"embeddings.npy",selected_vectors,allow_pickle=False)
        meta=copy.deepcopy(source_meta)
        meta.update(created_at=datetime.now(timezone.utc).isoformat(),manifest_hash=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            chunks_sha256=hashlib.sha256(raw).hexdigest(),chunk_count=len(selected_chunks),failed_documents=[],
            documents=[doc for doc in source_meta["documents"] if doc["doc_id"] in doc_ids],
            stress_library={"is_derived":True,"derivation":"subset of verified existing parsed PDF chunks and actual dense rows",
                "physical_page_count":count,"source_index":Path(settings.rag_index_path).relative_to(ROOT).as_posix(),
                "source_chunks_sha256":source_meta["chunks_sha256"],"original_page_numbers_preserved":True,
                "scope_doc_ids":doc_ids,"selected_pages":[{"doc_id":doc,"page":page} for doc,page in sorted(pages)]})
        meta["dense_embedding"]["vectors_sha256"]=hashlib.sha256((library/"embeddings.npy").read_bytes()).hexdigest()
        write_json(library/"index_meta.json",meta)
        active=replace(settings,rag_index_path=library,rag_manifest_path=manifest)
        actual,verified=load_index(settings=active)
        actual_pages={(chunk["doc_id"],chunk["page"]) for chunk in actual}
        if actual_pages!=pages or len(actual_pages)!=count:
            raise ValueError("Library page count/source verification failed")
        reports.append({"pages":count,"chunks":len(actual),"documents":len(doc_ids),
            "index":library.relative_to(ROOT).as_posix(),"manifest":manifest.relative_to(ROOT).as_posix(),
            "selected_pages":meta["stress_library"]["selected_pages"],"all_twenty_questions_evidence_available":True,
            "source_hash_and_dense_dimensions_verified":True})
    (output/"questions.jsonl").write_text("".join(json.dumps(case,ensure_ascii=False)+"\n" for case in cases),encoding="utf-8")
    summary={"status":"ACTUALLY_BUILT_VERIFIED","build_ms":round((perf_counter()-started)*1000,3),
        "actual_model_build_calls":0,"dense_source":"verified original BGE-M3 vectors, original row subset",
        "holdout_predictions":0,"questions":20,"original_dev_families":10,"new_equal_meaning_variants":10,
        "new_variants_human_status":"pending_human_review","source_safe_dev_view":source.relative_to(ROOT).as_posix(),
        "source_safe_dev_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"doc_ids":doc_ids,"libraries":reports}
    write_json(output/"manifest.json",summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


def run(library_root: Path,output:Path, *, retrieval_only=False):
    if output.exists():
        raise ValueError("Choose a fresh evidence directory")
    manifest=json.loads((library_root/"manifest.json").read_text(encoding="utf-8"))
    if manifest["status"]!="ACTUALLY_BUILT_VERIFIED":
        raise ValueError("Only actually verified libraries can be tested")
    cases=[json.loads(line) for line in (library_root/"questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(cases)!=20 or any(case.get("split")!="dev" for case in cases):
        raise ValueError("Only twenty fixed development efficiency questions are allowed")
    output.mkdir(parents=True)
    settings=get_settings()
    os.environ["LLM_CAPTURE_DIR"]=str((output/"provider").resolve())
    metadata=provenance(ROOT,settings,[library_root/"manifest.json",library_root/"questions.jsonl",
        ROOT/"qa_agent/rag/retriever.py",ROOT/"qa_agent/rag/answer.py"])
    metadata.update(expected_predictions=120,concurrency=1,repetitions=3,
        mode="local_retrieval_only" if retrieval_only else "retrieval_and_actual_model_answer",
        external_model_calls_authorized_and_attempted=not retrieval_only,
        warmup="no synthetic warm questions; first actual request includes cold setup where needed",
        accuracy_note="surface-answer check is diagnostic only, not semantic correctness; new variants await human confirmation",
        retrieval_scope="all five allowed development documents; both channels score ALL library chunks")
    write_json(output/"provenance.json",metadata)
    records=[]
    libraries=manifest["libraries"]
    for repetition in range(1,4):
        for case in cases:
            ordered=libraries if repetition%2 else list(reversed(libraries))
            for library in ordered:
                active=replace(settings,rag_index_path=ROOT/library["index"],rag_manifest_path=ROOT/library["manifest"])
                trace=TraceRecorder(settings=active)
                record={"id":case["efficiency_id"],"original_dev_id":case.get("original_dev_id",case["id"]),
                    "split":"dev","pages":library["pages"],"repetition":repetition,
                    "request":{"question":case["question"],"scope_doc_ids":manifest["doc_ids"]},
                    "semantic_answer_review":"pending_human_review","matched":False,"legacy_matched":False}
                started=perf_counter()
                try:
                    with trace.step("retrieve",{"scope_doc_ids":manifest["doc_ids"]}) as step:
                        chunks,retrieval=retrieve(case["question"],manifest["doc_ids"],settings=active)
                        step.output_summary=retrieval
                    if retrieval["candidate_count"]!=library["chunks"] or retrieval.get("searched_page_count")!=library["pages"]:
                        raise ValueError("Not all library chunks/pages entered real retrieval scoring")
                    gold_pages=set(case["physical_pages"])
                    hit=any(item["doc_id"]==case["doc_id"] and item["page"] in gold_pages
                            for item in retrieval["rankings"]["rrf"][:5])
                    record.update(retrieval=retrieval,retrieved_chunks=chunks,hit_at_5=hit,matched=hit)
                    if retrieval_only:
                        record.update(status="RETRIEVED_ONLY",answer_generation="NOT_RUN",
                            answer_not_run_reason="External-send approval review rejected model experiment; local retrieval remains authorized",
                            failure_category=None if hit else "retrieval_miss")
                    else:
                        with trace.step("doc_answer",{"evidence_count":len(chunks)}) as step:
                            answer,used=answer_from_chunks(case["question"],chunks,JsonLLM(active),trace,mode="llm")
                            step.output_summary={"status":answer.status,"citation_ids":answer.citation_ids}
                    first5=set(retrieval["hit_at_5_scope"])
                    hit=any(chunk["chunk_id"] in first5 and chunk["doc_id"]==case["doc_id"] and chunk["page"] in gold_pages for chunk in chunks)
                    # Use complete ranking IDs to avoid losing top-5 when top_k
                    # is configured smaller; current top_k normally equals 8.
                    hit=hit or any(item["doc_id"]==case["doc_id"] and item["page"] in gold_pages
                                   for item in retrieval["rankings"]["rrf"][:5])
                    if not retrieval_only:
                        diagnostic=answer_surface_match(case["answer"],answer.answer)
                        record.update(status=answer.status,answer=answer.answer,citation_ids=answer.citation_ids,
                            used_evidence=used,retrieved_chunks=chunks,retrieval=retrieval,hit_at_5=hit,
                            surface_answer_match=diagnostic,citation_coverage=citation_coverage_diagnostics(answer),
                            validation_warnings=answer._validation_warnings,
                            validation_status="unverified" if answer._validation_warnings else "passed",
                            matched=hit,failure_category=None if hit else "retrieval_miss")
                except Exception as exc:
                    record.update(status="FAILED",failure_category=getattr(exc,"code","runner_exception"),
                                  error=sanitize_error(exc,active))
                envelope={"steps":[step.model_dump(mode="json") for step in trace.steps]}
                record["steps"]=envelope["steps"]
                record["cost"]=trace_cost(envelope)
                record["elapsed_ms"]=round((perf_counter()-started)*1000,3)
                records.append(record)
                write_json(output/"cases"/f"{case['efficiency_id']}-p{library['pages']}-r{repetition}.json",record)
                with (output/"responses.jsonl").open("a",encoding="utf-8") as stream:
                    stream.write(json.dumps(record,ensure_ascii=False)+"\n")
                print(len(records),"/120",record["id"],library["pages"],repetition,record["status"],record["elapsed_ms"],flush=True)
                write_json(output/"report.json",{"status":"RUNNING","completed":len(records),"expected":120})
    summary={"status":"ACTUALLY_RUN_RETRIEVAL_ONLY" if retrieval_only else "ACTUALLY_RUN_DEV",
             "provenance":metadata,"holdout_predictions":0,"groups":{}}
    for library in libraries:
        rows=[row for row in records if row["pages"]==library["pages"]]
        group=summarize(rows)
        # Never call retrieval-hit or heuristic answer checking SQL EX/RAG accuracy.
        group.pop("ex",None);group.pop("correct",None);group.pop("legacy_correct",None)
        group.update(hit_at_5_count=sum(row.get("hit_at_5",False) for row in rows),
            successful_answer_count=sum(row["status"] in {"SUCCEEDED","EMPTY_RESULT"} for row in rows),
            status_counts=dict(Counter(row["status"] for row in rows)),
            surface_answer_match_count=sum(row.get("surface_answer_match",False) for row in rows),
            unverified_count=sum(row.get("validation_status")=="unverified" for row in rows),
            failure_categories=dict(Counter(row.get("failure_category") for row in rows if row.get("failure_category"))),
            human_semantic_reviewed_count=0,library_pages=library["pages"],library_chunks=library["chunks"])
        summary["groups"][str(library["pages"])]=group
    write_json(output/"report.json",summary)
    lines=["# D4 文档10页／100页真实效率测试" + ("（仅本地检索）" if retrieval_only else ""),"",
        "同20题每规模每题3次，120次实际" + ("本地检索，模型回答未运行" if retrieval_only else "检索与模型回答") +
        "；10个已暴露DEV原题＋10个保持含义的英文改写。",
        "新增改写参考语义待人工确认，不把启发式答案覆盖视为完整正确率；两规模全范围检索同5份PDF。","",
        "|规模|片段|请求|Hit@5|返回状态|检索P50/P90 ms|答案生成P50/P90 ms|端到端P50/P90 ms|输入token|",
        "|---|---|---|---|---|---|---|---|---|"]
    for key,group in summary["groups"].items():
        ret=group["stages"]["retrieval"];ans=group["stages"]["answer_generation"];e2e=group["end_to_end"]
        lines.append(f"|{key}真实页|{group['library_chunks']}|{group['requests']}|{group['hit_at_5_count']}/60|"
            f"{group['status_counts']}|{ret['p50_ms']}/{ret['p90_ms']}|{ans['p50_ms']}/{ans['p90_ms']}|"
            f"{e2e['p50_ms']}/{e2e['p90_ms']}|{group['usage_total'].get('prompt_tokens',0)}|")
    lines += ["","每次记录candidate_count与searched_page_count，必须分别等于登记片段数与10/100才计入有效规模测试。",
        "首个实际请求可能包含本地模型/分词冷启动；无虚构热身。本表不单独剔除首请求，所有失败与重试均保留。",
        "构库为既有真实解析片段与BGE向量的子集，未重复页面凑规模；原文档、旧索引、原页码和来源哈希不变。"]
    (output/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare",action="store_true")
    parser.add_argument("--libraries",type=Path)
    parser.add_argument("--retrieval-only",action="store_true",help="local scoring only, never instantiate or call the external LLM")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output=args.output.resolve()
    if args.libraries is not None:
        args.libraries=args.libraries.resolve()
    if args.prepare:
        prepare(args.output)
    else:
        if args.libraries is None:
            parser.error("--libraries is required for actual runs")
        run(args.libraries,args.output,retrieval_only=args.retrieval_only)


if __name__=="__main__":
    main()
