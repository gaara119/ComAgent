"""Component-level adapters over the production RAG tools.

No reference answers, gold document IDs or scoring labels are consulted here.
The caller supplies an allowed search scope or an explicitly diagnostic evidence
set. Extractive mode is a source display and is never a semantic answer score.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import re

from qa_agent.config import sanitize_error
from qa_agent.llm import JsonLLM
from qa_agent.rag.answer import answer_from_chunks, citation_coverage_diagnostics, source_evidence_groups
from qa_agent.rag.parsers import DocumentError
from qa_agent.rag.retriever import retrieve
from qa_agent.trace import TraceRecorder


def retrieve_for_evaluation(question: str, doc_ids: list[str], *, settings,
                            strategy: str | None = None) -> tuple[list[dict], dict]:
    """Run the same retriever as normal QA, without generation or gold access."""
    if (not isinstance(doc_ids, list) or not doc_ids or
            any(not isinstance(value, str) or not value.strip() for value in doc_ids) or
            len(doc_ids) != len(set(doc_ids))):
        raise DocumentError("评测检索需要非空、无重复的允许文档范围。", "rag_scope_invalid")
    chunks, metadata = retrieve(question, doc_ids, settings=settings, strategy=strategy)
    if any(chunk["doc_id"] not in doc_ids for chunk in chunks):
        raise DocumentError("检索结果超出允许来源。", "rag_scope_violation")
    return chunks, metadata


def _usage(trace: TraceRecorder) -> dict:
    """Keep observed subtotals; unknown provider usage is not billed as zero."""
    attempts = [step for step in trace.steps if step.name == "llm"]
    physical_calls = trace.llm_attempts
    missing_usage = 0
    prompt, completion, hit, miss = [], [], [], []
    def integer(value):
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    for step in attempts:
        usage = step.output_summary.get("usage") or {}
        if not integer(usage.get("prompt_tokens")) or not integer(usage.get("completion_tokens")):
            missing_usage += 1
        if integer(usage.get("prompt_tokens")):
            prompt.append(usage["prompt_tokens"])
        if integer(usage.get("completion_tokens")):
            completion.append(usage["completion_tokens"])
        cached = usage.get("prompt_cache_hit_tokens")
        if not integer(cached):
            cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
        if integer(cached):
            hit.append(cached)
        uncached = usage.get("prompt_cache_miss_tokens")
        if not integer(uncached) and integer(cached) and integer(usage.get("prompt_tokens")):
            uncached = usage["prompt_tokens"] - cached
        if integer(uncached):
            miss.append(uncached)
    # A missing trace row also cannot silently become a zero-usage call.
    missing_usage += max(0, physical_calls - len(attempts))
    return {
        "physical_calls": physical_calls,
        "input_tokens": sum(prompt) if len(prompt) == physical_calls else None,
        "output_tokens": sum(completion) if len(completion) == physical_calls else None,
        "cache_hit_input_tokens": sum(hit) if len(hit) == physical_calls else None,
        "cache_miss_input_tokens": sum(miss) if len(miss) == physical_calls else None,
        "observed_input_tokens": sum(prompt), "observed_output_tokens": sum(completion),
        "missing_usage_attempts": missing_usage,
        "usage_complete": missing_usage == 0,
        "cache_usage_complete": len(hit) == physical_calls and len(miss) == physical_calls,
    }


def generate_for_evaluation(question: str, chunks: list[dict], *, settings,
                            answer_mode: str = "extractive") -> dict:
    """Generate with a frozen evidence set and the actual answer validator.

    This entry does not retrieve or translate, which lets a diagnostic hold the
    evidence constant. LLM mode is explicit and uses the existing request-local
    attempt bound, timeout, JSON validation and citation retry mechanism.
    """
    trace = TraceRecorder(settings=settings)
    inputs = deepcopy(chunks)
    result = {
        "status": "FAILED", "answer": "", "citation_ids": [], "used_evidence": [],
        "input_chunks": inputs, "answer_mode": answer_mode, "validation_warnings": [],
        "semantic_status": "not_applicable_extractive" if answer_mode == "extractive" else "not_verified",
        "citation_coverage": {}, "error": None,
        "answer_implementation_sha256": sha256(Path(__file__).with_name("answer.py").read_bytes()).hexdigest(),
    }
    try:
        with trace.step("evaluation_evidence", {"evidence_count": len(inputs)}) as step:
            if answer_mode not in {"extractive", "llm"}:
                raise DocumentError("生成评测模式必须是 extractive 或 llm。", "rag_answer_mode")
            ids = [chunk.get("evidence_id") for chunk in inputs]
            if (len(ids) != len(set(ids)) or
                    any(not isinstance(value, str) or not re.fullmatch(r"E[1-9]\d*", value) for value in ids)):
                raise DocumentError("评测证据ID无效或重复。", "rag_citation_invalid")
            provided = [{key: chunk[key] for key in
                         ("evidence_id", "doc_id", "doc_title", "page", "section_path", "text")}
                        for chunk in inputs]
            result["generation_input"] = {"question": question, "evidence": provided}
            groups = source_evidence_groups(inputs)
            if groups:
                result["generation_input"]["source_groups"] = groups
            step.output_summary = {"evidence_ids": ids}
        with trace.step("doc_answer", {"mode": answer_mode, "evidence_count": len(inputs)}) as step:
            llm = JsonLLM(settings) if answer_mode == "llm" else None
            answer, used = answer_from_chunks(question, inputs, llm, trace, mode=answer_mode)
            if any(chunk not in inputs for chunk in used):
                raise DocumentError("回答引用超出本次实际输入证据。", "rag_scope_violation")
            result.update(status=answer.status, answer=answer.answer,
                          citation_ids=list(answer.citation_ids), used_evidence=deepcopy(used),
                          validation_warnings=deepcopy(answer._validation_warnings),
                          citation_coverage=citation_coverage_diagnostics(answer))
            step.output_summary = {"status": answer.status, "citation_ids": list(answer.citation_ids)}
    except Exception as exc:
        result["error"] = {"code": getattr(exc, "code", "rag_evaluation_error"),
                           "message": sanitize_error(exc, settings)}
    result.update(trace=[step.model_dump(mode="json") for step in trace.steps], usage=_usage(trace),
                  latency_ms=trace.latency_ms, trace_id=trace.trace_id)
    return result
