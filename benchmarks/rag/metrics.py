"""Deterministic evidence diagnostics, separate from semantic review scores.

Quotes and locations define stable evidence units, independent of chunk IDs.
These metrics test retrieval of labelled text; they do not prove entailment.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Mapping


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).replace("\u00ad", "").split()).casefold()


def _dict(value) -> dict:
    return value.model_dump() if hasattr(value, "model_dump") else dict(value)


def evidence_match(chunk: dict, evidence) -> bool:
    """Full labelled quote, correct document, physical page and section prefix."""
    label = _dict(evidence)
    quote = normalize_text(label["quote"])
    section = label.get("section_path", [])
    return (chunk.get("doc_id") == label["doc_id"]
            and type(chunk.get("page")) is type(label["page"]) and chunk.get("page") == label["page"]
            and (not section or chunk.get("section_path", [])[:len(section)] == section)
            and bool(quote) and quote in normalize_text(chunk.get("text", "")))


def retrieval_metrics(chunks: list[dict], required_evidence: list, k: int = 5,
                      *, corpus_chunks: list[dict] | None = None) -> dict:
    """Evaluate unique source-evidence coverage, not raw chunk/page coincidence.

    Standard binary nDCG uses chunk qrels derived from *all* frozen allowed
    corpus chunks. A chunk is relevant iff it contains a full labelled quote
    at the correct locator; different overlapping chunks are independent qrels.
    Repeated retrieval of one chunk ID receives no additional gain. Without
    the corpus, IDCG is unknown and standard nDCG remains None.

    novelty_ndcg is a separate mechanical source-unit novelty diagnostic, not
    standard nDCG: rank gains occur only when a previously unseen evidence unit
    appears; its ideal has min(K, |labels|) gains. Recall counts all units.
    """
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")
    labels = [_dict(evidence) for evidence in required_evidence]
    if len({label["id"] for label in labels}) != len(labels):
        raise ValueError("Evidence IDs must be unique")
    result = {"eligible": bool(labels), "metric_protocol": "source_quote_chunk_qrels_v2",
              "matched_evidence_ids": [], "rank_matches": []}
    keys = [f"{name}@{k}" for name in ("hit", "recall", "mrr", "ndcg", "precision", "evidence_coverage", "novelty_ndcg", "novelty_precision")]
    if not labels:
        return {**result, **{key: None for key in keys}}
    seen = set()
    gains = []
    seen_ranked_chunks = set()
    relevant_rank_gains = []
    first_rank = None
    for rank, chunk in enumerate(chunks[:k], 1):
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            raise ValueError("Retrieved chunks require nonempty stable chunk IDs")
        matches = {label["id"] for label in labels if evidence_match(chunk, label)}
        relevant_rank_gains.append(1.0 if matches and chunk_id not in seen_ranked_chunks else 0.0)
        seen_ranked_chunks.add(chunk_id)
        novel = matches - seen
        gains.append(1.0 if novel else 0.0)
        if matches and first_rank is None:
            first_rank = rank
        seen.update(matches)
        result["rank_matches"].append({"rank": rank, "chunk_id": chunk.get("chunk_id"),
                                      "evidence_ids": sorted(matches), "new_evidence_ids": sorted(novel)})
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(labels)) + 1))
    standard_ndcg = None
    relevant_chunk_count = None
    if corpus_chunks is not None:
        corpus = {}
        for item in corpus_chunks:
            chunk_id = item.get("chunk_id")
            if not isinstance(chunk_id, str) or not chunk_id:
                raise ValueError("Frozen corpus chunks require nonempty stable chunk IDs")
            if chunk_id in corpus:
                raise ValueError("Frozen corpus chunk IDs must be unique")
            corpus[chunk_id] = item
        relevant = {chunk_id for chunk_id, item in corpus.items()
                    if any(evidence_match(item, label) for label in labels)}
        relevant_chunk_count = len(relevant)
        seen_chunks = set()
        chunk_gains = []
        for item in chunks[:k]:
            chunk_id = item.get("chunk_id")
            if chunk_id not in corpus:
                raise ValueError("Retrieved chunk is absent from the frozen allowed corpus")
            if any(item.get(field) != corpus[chunk_id].get(field)
                   for field in ("doc_id", "page", "section_path", "text")):
                raise ValueError("Retrieved chunk content differs from its frozen qrel source")
            chunk_gains.append(1.0 if chunk_id in relevant and chunk_id not in seen_chunks else 0.0)
            seen_chunks.add(chunk_id)
        chunk_dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(chunk_gains, 1))
        chunk_ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
        standard_ndcg = chunk_dcg / chunk_ideal if chunk_ideal else 0.0
    coverage = len(seen) / len(labels)
    return {**result, "matched_evidence_ids": sorted(seen),
            f"hit@{k}": bool(seen), f"recall@{k}": coverage,
            f"mrr@{k}": 1 / first_rank if first_rank else 0.0,
            f"ndcg@{k}": standard_ndcg, f"novelty_ndcg@{k}": dcg / ideal,
            "relevant_chunk_count": relevant_chunk_count, f"precision@{k}": sum(relevant_rank_gains) / k,
            f"novelty_precision@{k}": sum(gains) / k,
            f"evidence_coverage@{k}": coverage}


def _surface_contains(answer: str, expected: str) -> bool:
    actual, value = normalize_text(answer), normalize_text(expected)
    if not value:
        return False
    # Never count 71 as a match for 171, or 20 for 2026.
    left = r"(?<![\d.])" if value[0].isdigit() else ""
    right = r"(?![\d.])" if value[-1].isdigit() else ""
    return re.search(left + re.escape(value) + right, actual) is not None


def answer_diagnostics(answer: str, citations: list, input_chunks: list[dict], facts: list,
                       answerable: bool, status: str | None = None) -> dict:
    """Mechanical labels remain diagnostics; semantic metrics stay null."""
    by_id = {chunk.get("evidence_id"): chunk for chunk in input_chunks if chunk.get("evidence_id")}
    cited_ids = []
    quote_checks = []
    for citation in citations:
        if isinstance(citation, str):
            cited_ids.append(citation)
            continue
        citation = _dict(citation)
        evidence_id = citation.get("evidence_id")
        cited_ids.append(evidence_id)
        original = by_id.get(evidence_id)
        quote_checks.append(bool(original) and all(citation.get(key) == original.get(key)
                                                  for key in ("doc_id", "page", "section_path", "text")
                                                  if key in citation))
    textual_citations = re.findall(r"\[(E\d+)\]", answer)
    all_ids = set(cited_ids) | set(textual_citations)
    valid = all(evidence_id in by_id for evidence_id in all_ids)
    covered = [_dict(fact)["id"] for fact in facts
               if any(_surface_contains(answer, variant) for variant in _dict(fact)["accepted_answers"])]
    # Status is authoritative only when explicitly supplied. Regex is disclosed
    # as heuristic and never determines business correctness or refusal recall.
    refusal = status in {"EMPTY_RESULT", "NO_DATA", "NOT_FOUND"}
    heuristic = bool(re.search(r"资料不足|证据不足|无法.*(?:确定|回答)|not enough (?:information|evidence)|insufficient (?:information|evidence)", answer, re.I))
    return {"lexical_fact_coverage": len(covered) / len(facts) if facts else None,
            "matched_fact_ids": covered, "citation_ids_valid": valid,
            "citation_count": len(all_ids), "citation_quotes_unchanged": all(quote_checks) if quote_checks else None,
            "refusal_status": refusal if status is not None else None,
            "refusal_surface_heuristic": heuristic, "reference_answerable": answerable,
            "semantic_answer_correctness": None, "semantic_faithfulness": None,
            "semantic_citation_support": None, "semantic_review_status": "not_verified"}


def semantic_scores(assessment: Mapping | None) -> dict:
    """Only explicit human/AI review records can populate semantic metrics.

    Callers must bind assessments to the prediction hash before using this
    helper. An AI judgement is reported as AI judgement, never a human signoff.
    """
    names = ("answer_correct", "fact_support_rate", "citation_support_precision", "citable_fact_coverage")
    if assessment is None:
        return {name: None for name in names} | {"review_status": "not_verified"}
    reviewer = assessment.get("reviewer_type")
    if reviewer not in {"human", "ai"}:
        raise ValueError("Semantic assessments must disclose reviewer_type=human|ai")
    result = {"review_status": "human_reviewed" if reviewer == "human" else "ai_reviewed",
              "reviewer_type": reviewer}
    for name in names:
        value = assessment.get(name)
        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError(f"Invalid semantic score: {name}")
        result[name] = value
    return result


def percentile(values: list[float], p: float) -> float | None:
    """Linear interpolation of sorted finite samples; empty input is unknown."""
    if not 0 <= p <= 100:
        raise ValueError("Percentile must be in [0,100]")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
        raise ValueError("Latency samples must be finite numbers")
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * p / 100
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def percentiles(values: list[float]) -> dict:
    return {"count": len(values), "p50": percentile(values, 50), "p90": percentile(values, 90),
            "method": "linear_interpolation_(n-1)*p"}
