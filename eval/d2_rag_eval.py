"""D2 RAG evaluation through the shared API; no gold or holdout sent online."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import httpx
from eval.rag_metrics import answer_surface_match, normalize_text
from eval.run_eval import _git, validate_frozen_tag
from qa_agent.config import get_settings, sanitize_error
from qa_agent.schemas import AnswerEnvelope, ChatRequest

ROOT = Path(__file__).resolve().parents[1]


def load_d2_rag(path: Path) -> list[dict]:
    rows=[json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]
    ids=[r["id"] for r in rows]
    if len(ids)!=len(set(ids)):
        raise ValueError("Duplicate RAG IDs")
    groups={}
    for row in rows:
        if row["split"] not in {"dev","holdout"}:
            raise ValueError("Invalid split")
        family=row["family_id"]
        if family in groups and groups[family]!=row["split"]:
            raise ValueError("RAG question family crosses splits")
        groups[family]=row["split"]
        if any(not isinstance(p,int) or p<1 for p in row.get("physical_pages",[])):
            raise ValueError("Invalid physical page")
    return rows


def candidate_gold_hit(item: dict, candidates: list[dict], chunks: dict[str,dict]) -> bool:
    pages=set(item.get("physical_pages",[]))
    gold=item.get("gold_evidence",[])
    for candidate in candidates[:5]:
        if candidate.get("doc_id") != item["doc_id"]:
            continue
        if candidate.get("page") in pages:
            return True
        chunk=chunks.get(candidate.get("chunk_id"),candidate)
        for evidence in gold:
            if evidence.get("doc_id",item["doc_id"])!=item["doc_id"]:
                continue
            if evidence.get("page") is not None:
                continue
            text=normalize_text(evidence.get("text", ""))
            source=normalize_text(chunk.get("text", ""))
            if text and text in source:
                return True
    return False


def evidence_diagnostics(item: dict, payload: dict, chunks: dict[str,dict]) -> dict:
    candidates=(payload.get("metadata") or {}).get("retrieved_pages",[])
    by_evidence={r.get("evidence_id"):chunks.get(r.get("chunk_id")) for r in candidates}
    checks=[]
    for evidence in payload.get("evidences",[]):
        source=by_evidence.get(evidence.get("evidence_id"))
        checks.append(bool(source) and all(evidence.get(key)==source.get(key) for key in
                     ("doc_id","page","section_path","text","bbox")) and evidence.get("doc_id")==item["doc_id"])
    reference=normalize_text(item.get("reference_text", ""))
    strict=False
    for candidate in candidates[:5]:
        chunk=chunks.get(candidate.get("chunk_id"),{})
        text=normalize_text(chunk.get("text", ""))
        if candidate.get("doc_id")==item["doc_id"] and text and reference and reference in text:
            strict=True
        for gold in item.get("gold_evidence",[]):
            quote=normalize_text(gold.get("text", ""))
            if quote and candidate.get("doc_id")==gold.get("doc_id",item["doc_id"]) and quote in text:
                strict=True
    return {"evidence_authentic_index_text":bool(checks) and all(checks),
            "exact_gold_quote_hit_at_5":strict if item.get("answerable",True) else None}


def evaluate_rag(args):
    settings=get_settings()
    items=load_d2_rag(args.dataset)
    if args.split=="holdout":
        if not args.allow_holdout or not args.frozen_tag or args.draft_gold:
            raise ValueError("Holdout requires frozen tag + explicit permission; never draft")
        validate_frozen_tag(args.frozen_tag)
    selected=[r for r in items if r["split"]==args.split]
    if not selected:
        raise ValueError("Selected RAG split is empty")
    directory=args.output or ROOT / "eval/artifacts/d2/rag" / (args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    if (directory / "report.json").exists():
        raise ValueError("Run directory already contains results; choose a fresh run ID")
    # D1's review hash covers its fields. New D2 gold requires a separate explicit
    # review of answerability and section evidence; a stale accepted flag is insufficient.
    from eval.rag_dataset import reviewed
    pending=[r["id"] for r in selected if not reviewed(r)]
    blockers=[]
    if pending and not args.draft_gold:
        blockers.append("RAG gold pending human review: " + ", ".join(pending))
    if not settings.llm_configured:
        blockers.append("Model credentials unavailable")
    index_path=settings.rag_index_path
    try:
        from qa_agent.rag.index import load_index
        index_chunks,index_metadata=load_index(index_path,settings=settings)
        chunks={r["chunk_id"]:r for r in index_chunks}
    except Exception as exc:
        blockers.append("RAG index/source verification failed: " + sanitize_error(exc,settings))
        chunks={}
    provenance={"created_at_utc":datetime.now(timezone.utc).isoformat(),"git_commit":_git("rev-parse","HEAD"),
                "working_tree_dirty":bool(_git("status","--porcelain")),"configured_model":settings.llm_model,
                "actual_models":[],"dataset":args.dataset.resolve().relative_to(ROOT).as_posix(),
                "dataset_sha256":hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                "index_path":index_path.relative_to(ROOT).as_posix(),
                "index_meta_sha256":hashlib.sha256((index_path/"index_meta.json").read_bytes()).hexdigest() if (index_path/"index_meta.json").exists() else None,
                "gold_review":"draft" if args.draft_gold else "human_accepted", "gold_not_sent_to_online_api":True}
    report={"status":"READINESS_ONLY", "suite":"rag", "split":args.split,"run_id":args.run_id,
            "selected_count":len(selected),"prediction_count":0,"holdout_prediction_count":0,
            "gold_human_accepted_count":len(selected)-len(pending),"answer_human_review_count":0,
            "blockers":blockers,"provenance":provenance}
    directory.mkdir(parents=True,exist_ok=True)
    rows=[]
    if not blockers:
        with httpx.Client(timeout=args.timeout,trust_env=False) as client, (directory/"responses.jsonl").open("w",encoding="utf8") as stream:
            for item in selected:
                request=ChatRequest(session_id=f"d2-rag-{args.run_id}-{item['id']}", message=item["question"],
                                    scope={"route":"doc","db_id":None,"doc_ids":[item["doc_id"]]})
                row={"id":item["id"],"doc_id":item["doc_id"],"split":item["split"],"request":request.model_dump(),
                     "reference_answer":item["answer"],"answerable":item.get("answerable",True),
                     "is_d1_common":bool(item.get("exposure_history",{}).get("d1_model_exposed", False)
                                         or item.get("exposure_history",{}).get("model_prediction_count",0)>0),
                     "response":None,"failure":None,"semantic_review":"pending_human_review"}
                started=time.perf_counter()
                try:
                    response=client.post(args.base_url.rstrip("/")+"/api/chat",json=request.model_dump())
                    response.raise_for_status()
                    envelope=AnswerEnvelope.model_validate(response.json())
                    row["response"]=envelope.model_dump(mode="json")
                    for step in envelope.steps:
                        actual_model=step.output_summary.get("model") if step.name=="llm" else None
                        if actual_model and actual_model not in provenance["actual_models"]:
                            provenance["actual_models"].append(actual_model)
                except Exception as exc:
                    row["failure"]=sanitize_error(exc,settings)
                payload=row["response"] or {}
                evidences=payload.get("evidences",[])
                metadata=payload.get("metadata",{})
                candidates=metadata.get("retrieved_pages",[])
                row["metrics"]={
                    "status_succeeded":payload.get("status")=="SUCCEEDED",
                    "hit_at_5":candidate_gold_hit(item,candidates,chunks) if row["answerable"] else None,
                    "evidence_in_selected_doc":bool(evidences) and all(e["doc_id"]==item["doc_id"] for e in evidences),
                    "insufficient_correct":payload.get("status") in {"EMPTY_RESULT","UNSUPPORTED"} and not evidences if not row["answerable"] else None,
                    "answer_surface_match":answer_surface_match(item["answer"],payload.get("answer","")) if row["answerable"] else None,
                    "human_correctness":"pending", "human_faithfulness":"pending"}
                row["metrics"].update(evidence_diagnostics(item,payload,chunks))
                row["latency_ms"]=round((time.perf_counter()-started)*1000,2)
                error_code=(payload.get("error") or {}).get("code","")
                row["error_code"]=error_code or None
                row["error_type"]=("timeout" if (row["failure"] and "timeout" in row["failure"].lower()) or "timeout" in error_code else
                                   "format" if row["failure"] else
                                   "unfaithful" if error_code in {"rag_number_invalid","rag_citation_invalid","rag_scope_violation"} else
                                   "format" if payload.get("status")=="FAILED" else
                                   "retrieval_miss" if row["answerable"] and not row["metrics"]["hit_at_5"] else
                                   "unfaithful" if not row["answerable"] and not row["metrics"]["insufficient_correct"] else None)
                rows.append(row)
                stream.write(json.dumps(row,ensure_ascii=False)+"\n")
                stream.flush()
                print(json.dumps({"id":row["id"],"status":payload.get("status","FAILED"),
                                  "hit_at_5":row["metrics"]["hit_at_5"],"latency_ms":row["latency_ms"]},ensure_ascii=False),flush=True)
        answerable=[r for r in rows if r["answerable"]]
        unavailable=[r for r in rows if not r["answerable"]]
        report.update(status="COMPLETED",prediction_count=len(rows),
                      hit_at_5={"passed":sum(r["metrics"]["hit_at_5"] for r in answerable),"denominator":len(answerable)},
                      exact_gold_quote_hit_at_5={"passed":sum(r["metrics"]["exact_gold_quote_hit_at_5"] for r in answerable),"denominator":len(answerable)},
                      insufficient_handling={"passed":sum(r["metrics"]["insufficient_correct"] for r in unavailable),"denominator":len(unavailable)},
                      mechanical_metrics={key:{"passed":sum(r["metrics"][key] is True for r in rows),"denominator":len(rows)}
                                          for key in ("status_succeeded","evidence_in_selected_doc","evidence_authentic_index_text")},
                      error_types=dict(Counter(r["error_type"] for r in rows if r["error_type"])),
                      mean_latency_ms=sum(r["latency_ms"] for r in rows)/len(rows),
                      api_status_counts=dict(Counter((r["response"] or {}).get("status","FAILED") for r in rows)))
        report["segments"]={}
        for name,is_common in (("d1_common",True),("new_d2",False)):
            segment=[r for r in rows if r["is_d1_common"] is is_common]
            available=[r for r in segment if r["answerable"]]
            report["segments"][name]={"prediction_count":len(segment),
                "hit_at_5_passed":sum(r["metrics"]["hit_at_5"] for r in available),
                "hit_at_5_denominator":len(available),
                "actual_status_counts":dict(Counter((r["response"] or {}).get("status","FAILED") for r in segment)),
                "human_correctness_review_count":0}
    (directory/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
    lines=["# D2 RAG 开发集实际运行", "", f"状态：{report['status']}；实际运行 {len(rows)}/{len(selected)}。", "",
           "gold 尚待人工审核；机械检查与辅助模型判断均不等同正式答案正确率/忠实度。保留题 D5 待测。", ""]
    if rows:
        for label,key in [("可回答题 Hit@5","hit_at_5"),("证据不足处理","insufficient_handling")]:
            value=report[key]
            lines += [f"- {label}：{value['passed']}/{value['denominator']}。"]
        lines += ["", "Hit@5 只查看最终融合排名的前5个候选；无答案题不进入命中率分母。",
                  "按总计划，PDF Hit@5 为金标证据页命中；非 PDF 为金标片段命中。另报更严格的完整 gold 原文片段命中诊断，不把它混作另一口径的正式成绩。",
                  "引用真实性同时核对 evidence_id 对应实际 chunk 的文档、页码、章节、文字与 bbox，不替代对原文件/OCR错误和语义的人工复核。"]
    else:
        lines += ["- " + item for item in blockers]
    (directory/"report.md").write_text("\n".join(lines)+"\n",encoding="utf8")
    review=["# D2 RAG 实际回答待人工复核", "", "逐题核对答案完整性、事实对应引用的对象/年度/单位与页码或章节；机器没有代替人工接受。", ""]
    for row in rows:
        response=row["response"] or {}
        review += [f"## {row['id']}", "",row["request"]["message"], "", "标准答案："+row["reference_answer"], "",
                   "实际回答："+response.get("answer", row["failure"] or ""), "", "实际证据：", "",
                   "```json",json.dumps(response.get("evidences",[]),ensure_ascii=False,indent=2),"```", "",
                   "- [ ] 答案正确且完整。", "- [ ] 每个事实由所引用片段支持。", "- [ ] 页码/章节与原文件一致。", ""]
    (directory/"human_review.md").write_text("\n".join(review),encoding="utf8")
    return report,directory
