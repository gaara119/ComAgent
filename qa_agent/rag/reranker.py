"""Local query-coverage reranking; no additional model or reference labels."""
from __future__ import annotations

from collections import Counter
from math import log


def rerank(order, scores, chunks, corpus, query_tokens):
    terms = set(query_tokens)
    frequency = Counter(token for row in corpus for token in set(row))
    weights = {token: log(1 + (len(corpus) + 1) / (frequency[token] + 1)) for token in terms}
    total = sum(weights.values()) or 1.0
    maximum = max(scores.values(), default=1.0) or 1.0
    pairs = set(zip(query_tokens, query_tokens[1:]))
    details = {}
    for i in order:
        words = set(corpus[i])
        coverage = sum(value for token, value in weights.items() if token in words) / total
        phrase = len(pairs.intersection(zip(corpus[i], corpus[i][1:]))) / max(len(pairs), 1)
        value = .60 * scores[i] / maximum + .30 * coverage + .10 * phrase
        details[i] = {"rrf_component": scores[i] / maximum, "query_coverage": coverage,
                      "phrase_coverage": phrase, "score": value}
    return sorted(order, key=lambda i: (-details[i]["score"], chunks[i]["chunk_id"])), details


def source_neighbors(order, chunks, top_k):
    """Recover at most two adjacent pieces, keeping independent citations."""
    if not order or top_k < 2:
        return order[:top_k], []
    anchor = order[0]
    own = chunks[anchor]
    record = own.get("source_record_id")
    start, end = own.get("char_start"), own.get("char_end")
    if not record or not isinstance(start, int) or not isinstance(end, int):
        return order[:top_k], []
    identity = lambda item: (item["doc_id"], item.get("page"), tuple(item.get("section_path", [])),
                             item.get("parser"), item.get("source_record_id"))
    group = sorted((i for i, item in enumerate(chunks) if identity(item) == identity(own)),
                   key=lambda i: (chunks[i].get("char_start", -1), chunks[i]["chunk_id"]))
    position = group.index(anchor)
    neighbors = []
    previous = own.get("incomplete_sentence_start") or own.get("boundary_start") == "heading_line"
    following = own.get("incomplete_sentence_end") or own.get("boundary_end") == "heading_line"
    for direction, enabled in ((-1, previous), (1, following)):
        pos = position + direction
        if not enabled or not 0 <= pos < len(group):
            continue
        index = group[pos]
        other = chunks[index]
        a, b = other.get("char_start"), other.get("char_end")
        if not isinstance(a, int) or not isinstance(b, int):
            continue
        gap = start - b if direction < 0 else a - end
        if -80 <= gap <= 120 and other.get("text", "").strip():
            neighbors.append(index)
    expanded = [anchor, *neighbors, *(i for i in order if i != anchor and i not in neighbors)][:top_k]
    return expanded, [{"anchor_chunk_id": own["chunk_id"], "neighbor_chunk_id": chunks[i]["chunk_id"],
                       "reason": "adjacent_piece_of_same_source_record", "page": own.get("page"),
                       "source_record_id": record} for i in neighbors if i in expanded]
