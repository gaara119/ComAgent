"""Lossless user-source presentation with lexical reading-order hints.

This module chooses no conditions, defaults or history. Every source character
remains present once, in source order. Retrieval only identifies paragraph IDs;
it never certifies the meaning or applicability of a paragraph.
"""
from __future__ import annotations

from hashlib import sha256
import re


def _tokens(text: str) -> list[str]:
    from qa_agent.rag.retriever import tokenize

    # The shared tokenizer also emits individual CJK characters. They are useful
    # for broad document recall, but overwhelm short-question paragraph ranking.
    # This affects navigation only: no character is removed from the source.
    return [token for token in tokenize(text)
            if len(token) > 1 or not re.fullmatch(r"[\u3400-\u9fff]", token)]


def source_paragraphs(text: str, query: str, *, source_id: str = "brief",
                      priority_limit: int = 6) -> dict:
    """Represent the whole text once, with exact Unicode offsets and BM25 IDs.

    Quote validation must keep using the original string, not paragraph IDs or
    this reading order. Empty lines, whitespace, line endings and repeated text
    retain their original positions. A match is not an authority decision.
    """
    if not isinstance(text, str) or not isinstance(query, str):
        raise TypeError("Source text and navigation query must be strings")
    if (not isinstance(source_id, str) or not source_id
            or type(priority_limit) is not int or not 0 <= priority_limit <= 12):
        raise ValueError("Invalid source navigation identity or priority limit")
    paragraphs, offset = [], 0
    for number, part in enumerate(text.splitlines(keepends=True), 1):
        paragraphs.append({"paragraph_id": f"P{number}", "start": offset,
                           "end": offset + len(part), "text": part})
        offset += len(part)
    assert offset == len(text)

    priority = []
    query_tokens = list(dict.fromkeys(_tokens(query)))
    if paragraphs and query_tokens and priority_limit:
        from rank_bm25 import BM25Okapi

        corpus = [_tokens(paragraph["text"]) for paragraph in paragraphs]
        if any(corpus):
            scores = BM25Okapi(corpus, epsilon=.25).get_scores(query_tokens)
            query_set = set(query_tokens)
            # Like the shared RAG lexical channel, retain matching passages even
            # when ubiquitous terms receive zero/negative Okapi scores.
            order = sorted((i for i, tokens in enumerate(corpus)
                            if query_set.intersection(tokens)),
                           key=lambda i: (-float(scores[i]), i))
            priority = [paragraphs[i]["paragraph_id"]
                        for i in order[:priority_limit]]
    return {
        "source_id": source_id,
        "content_sha256": sha256(text.encode("utf-8")).hexdigest(),
        "length": len(text),
        "offset_unit": "Unicode code points; start inclusive, end exclusive",
        "paragraphs": paragraphs,
        "priority_paragraph_ids": priority,
        "navigation_method": "shared_tokens_BM25_v1",
        "authority": "仅阅读顺序提示；所有段落均完整保留，匹配不证明语义、适用范围或默认授权",
        "citation_rule": "refs仍使用原source_id及连续原文quote；paragraph_id不是可引用来源",
    }
