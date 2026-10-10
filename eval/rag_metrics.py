"""Mechanical RAG evidence diagnostics; no semantic accuracy claims."""
from __future__ import annotations

import re
import unicodedata
from typing import Any


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).replace("\u00ad", "").split()).casefold()


def answer_surface_match(reference_answer: str, answer: str) -> bool:
    """A diagnostic substring check, deliberately not a semantic correctness test."""
    expected = normalize_text(reference_answer)
    actual = normalize_text(answer)
    if not expected:
        return False
    # Exact numeric tokens avoid incorrectly finding 71% inside 171%.
    if re.fullmatch(r"[\d.,]+%?", expected):
        return re.search(r"(?<![\d.])" + re.escape(expected) + r"(?![\d.])", actual) is not None
    return expected in actual


def measure_response(item: dict, response: dict, pdf_pages: list[str],
                     additional_pdf_pages: list[list[str]] | None = None) -> dict[str, Any]:
    evidences = response.get("evidences") or []
    doc_id = item["doc_id"]
    expected_pages = set(item["physical_pages"])
    checks = []
    for evidence in evidences:
        page = evidence.get("page")
        same_doc = evidence.get("doc_id") == doc_id
        valid_page = isinstance(page, int) and not isinstance(page, bool) and 1 <= page <= len(pdf_pages)
        text = evidence.get("text", "")
        if not isinstance(text, str):
            text = ""
        page_views = [pdf_pages[page - 1]] if valid_page else []
        if valid_page and additional_pdf_pages:
            page_views.extend(view[page - 1] for view in additional_pdf_pages if page <= len(view))
        authentic = (same_doc and valid_page and bool(normalize_text(text))
                     and any(normalize_text(text) in normalize_text(view) for view in page_views))
        checks.append({"evidence_id": evidence.get("evidence_id"), "doc_id": evidence.get("doc_id"),
                       "page": page, "same_selected_doc": same_doc, "valid_physical_page": valid_page,
                       "text_is_pdf_page_substring": authentic,
                       "gold_page": same_doc and valid_page and page in expected_pages})
    ids = [e.get("evidence_id") for e in evidences]
    unique_ids = len(ids) == len(set(ids)) and all(isinstance(i, str) and i for i in ids)
    cited_ids = re.findall(r"\[([^\[\]]+)\]", response.get("answer", ""))
    evidence_ids = {value for value in ids if isinstance(value, str)}
    known_citations = [value for value in cited_ids if value in evidence_ids]
    # Candidate lists are actual retriever metadata. No gold is passed to API.
    candidates = response.get("metadata", {}).get("retrieved_pages", [])
    retrieved_hit = None
    if isinstance(candidates, list) and candidates:
        if all(isinstance(value, dict) for value in candidates):
            retrieved_hit = any(value.get("doc_id") == doc_id and isinstance(value.get("page"), int)
                                and not isinstance(value.get("page"), bool)
                                and value.get("page") in expected_pages for value in candidates)
        elif all(isinstance(value, int) and not isinstance(value, bool) for value in candidates):
            retrieved_hit = any(value in expected_pages for value in candidates)
    return {
        "status_succeeded": response.get("status") == "SUCCEEDED",
        "response_intent_doc": response.get("intent", {}).get("route") == "doc" if isinstance(response.get("intent"), dict) else False,
        "evidence_count": len(evidences), "has_evidence": bool(evidences),
        "unique_evidence_ids": unique_ids,
        "all_evidence_from_selected_doc": bool(checks) and all(x["same_selected_doc"] for x in checks),
        "all_evidence_text_authentic": bool(checks) and all(x["text_is_pdf_page_substring"] for x in checks),
        "evidence_gold_page_hit": any(x["gold_page"] for x in checks),
        "retrieval_gold_page_hit": retrieved_hit,
        "answer_has_known_evidence_id": bool(known_citations),
        "answer_surface_match": answer_surface_match(item["answer"], response.get("answer", "")),
        "semantic_answer_correctness": "needs_human_review",
        "claim_grounding": "needs_human_review", "evidence_checks": checks,
    }
