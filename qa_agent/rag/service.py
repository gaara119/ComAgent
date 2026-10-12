"""B's single-document handler, using A's model and response contracts."""
from __future__ import annotations

import json
import re

from qa_agent.config import get_settings, sanitize_error
from qa_agent.llm import JsonLLM, LLMError
from qa_agent.rag.answer import SearchTranslation, answer_from_chunks, citation_coverage_diagnostics
from qa_agent.rag.parsers import DocumentError, load_documents
from qa_agent.rag.retriever import retrieve
from qa_agent.schemas import AnswerEnvelope, ErrorDetail, Evidence, IntentContract
from qa_agent.trace import TraceRecorder


def run_doc_qa(*, question: str, doc_id: str, trace_id: str, intent: IntentContract) -> AnswerEnvelope:
    settings = get_settings()
    trace = TraceRecorder(trace_id=trace_id, settings=settings)
    metadata = {"doc_id": doc_id, "answer_mode": settings.rag_answer_mode,
                "model": settings.llm_model if settings.rag_answer_mode == "llm" else None}
    try:
        with trace.step("doc_scope", {"doc_id": doc_id}) as step:
            matches = [d for d in load_documents(settings.rag_manifest_path) if d["doc_id"] == doc_id]
            if len(matches) != 1:
                raise DocumentError("所选文档不存在于允许清单中。", "document_not_found")
            document = matches[0]
            from qa_agent.documents import verify_document_hash
            try:
                verify_document_hash(document)
            except ValueError as exc:
                raise DocumentError(str(exc), "document_hash_mismatch") from exc
            step.output_summary = {"doc_id": doc_id, "title": document["title"], "content_hash": document["content_hash"]}
        llm = JsonLLM(settings)
        query = question
        # English PDFs need an English lexical query; this is a real, recorded model call.
        if (settings.rag_answer_mode == "llm" and re.search(r"[\u3400-\u9fff]", question)
                and document.get("language", "").lower() in {"en", "eng", "english", "en-us", "en-gb"}):
            with trace.step("query_translate", {"source_language": "zh", "target_language": "en"}) as step:
                translation = llm.complete_json(
                    "将用户问题译为英文检索问题。保留原始年度、金额、单位和实体；不得回答问题或新增事实。只返回english_query。",
                    json.dumps({"question": question}, ensure_ascii=False), SearchTranslation, trace)
                query = translation.english_query
                step.output_summary = {"query": query}
        with trace.step("retrieve", {"doc_id": doc_id, "question": question, "query": query}) as step:
            chunks, retrieval_metadata = retrieve(question, doc_id, settings=settings, query=query)
            if any(c["doc_id"] != doc_id for c in chunks):
                raise DocumentError("检索证据超出用户限定文档，已停止回答。", "rag_scope_violation")
            metadata.update(retrieval_metadata)
            metadata.update(retrieved_evidence_ids=[c["evidence_id"] for c in chunks],
                            retrieved_pages=[{"doc_id": c["doc_id"], "page": c["page"], "chunk_id": c["chunk_id"],
                                              "section_path": c["section_path"], "bbox": c.get("bbox"),
                                              "coordinate_system": c.get("coordinate_system"),
                                              "location_status": c.get("location_status", "legacy_not_verified"),
                                              "section_location_status": c.get("section_location_status", "legacy_not_verified"),
                                              "evidence_id": c["evidence_id"]} for c in chunks])
            step.output_summary = {**retrieval_metadata, "chunks": [
                {k: c[k] for k in ("chunk_id", "evidence_id", "doc_id", "page", "section_path", "score")} for c in chunks]}
        with trace.step("doc_answer", {"mode": settings.rag_answer_mode, "evidence_count": len(chunks)}) as step:
            answer, used = answer_from_chunks(question, chunks, llm, trace, mode=settings.rag_answer_mode)
            step.output_summary = {"status": answer.status, "used_evidence_ids": [c["evidence_id"] for c in used]}
            coverage = citation_coverage_diagnostics(answer)
            metadata["citation_coverage"] = coverage
            if answer._validation_warnings:
                step.status = "warn"
                metadata.update(faithfulness_uncertain=True, warnings=answer._validation_warnings)
                step.output_summary["validation_warnings"] = answer._validation_warnings
            if coverage["potential_uncited_statement_count"]:
                step.status = "warn"
                step.output_summary["warning"] = "存在可能未标引用的文字陈述，须人工复核；启发式检查不等同事实判定。"
        evidences = [Evidence(**{key: c[key] for key in
                               ("evidence_id", "doc_id", "doc_title", "page", "section_path", "text", "bbox")}) for c in used]
        metadata["cited_evidence_ids"] = [c["evidence_id"] for c in used]
        metadata.update(validation_status="unverified" if answer._validation_warnings else "passed",
                        validation_retries=sum(s.name == "rag_retry" for s in trace.steps),
                        faithfulness_uncertain=bool(answer._validation_warnings),
                        semantic_faithfulness="not_verified" if answer._validation_warnings else "pending_human_review")
        metadata.update(latency_ms=trace.latency_ms, llm_attempts=trace.llm_attempts)
        return AnswerEnvelope(trace_id=trace.trace_id, status=answer.status, answer=answer.answer,
                              evidences=evidences, intent=intent, steps=trace.steps, metadata=metadata)
    except Exception as exc:
        message = sanitize_error(exc, settings)
        code = getattr(exc, "code", "rag_error")
        metadata.update(latency_ms=trace.latency_ms, llm_attempts=trace.llm_attempts)
        if code in {"rag_citation_invalid", "rag_number_invalid"}:
            metadata.update(validation_status="failed", validation_retries=sum(s.name == "rag_retry" for s in trace.steps),
                            semantic_faithfulness="not_verified")
        return AnswerEnvelope(trace_id=trace.trace_id, status="FAILED", answer=message, intent=intent,
                              steps=trace.steps, metadata=metadata,
                              error=ErrorDetail(code=code, message=message, retryable=getattr(exc, "retryable", False)))
