"""Document-isolated lexical retrieval and optional actual dense RRF fusion."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import re
from time import perf_counter

from qa_agent.config import get_settings
from qa_agent.rag.index import load_index
from qa_agent.rag.parsers import DocumentError

_STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "and", "in", "for", "on", "as", "at", "by",
         "what", "which", "how", "much", "many", "please", "tell", "me", "does", "did", "from", "with"}


def tokenize(text: str) -> list[str]:
    """Keep numbers (including accounting commas), Latin terms and CJK bigrams."""
    output: list[str] = []
    for token in re.findall(r"\d[\d,]*(?:\.\d+)?|[a-zA-Z]+|[\u3400-\u9fff]+", text.lower()):
        if re.fullmatch(r"[\u3400-\u9fff]+", token):
            import jieba
            output.extend(term for term in jieba.cut_for_search(token, HMM=False) if term.strip())
            output.extend(token)
            output.extend(token[i:i + 2] for i in range(len(token) - 1))
        elif token not in _STOP:
            token = token.replace(",", "")
            if len(token) > 5 and token.endswith("ies"):
                token = token[:-3] + "y"
            elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
                token = token[:-1]
            output.append(token)
    return output


def retrieve(question: str, doc_id: str | list[str], *, settings=None, query: str | None = None,
             strategy: str | None = None) -> tuple[list[dict], dict]:
    from qa_agent.rag.retrieval_cache import snapshot, scoped_corpus, query_vector
    settings = settings or get_settings()
    strategy = strategy or getattr(settings, "rag_retrieval_strategy", "hybrid")
    if strategy not in {"bm25", "dense", "hybrid", "hybrid_rerank"}:
        raise DocumentError("未知的检索策略。", "rag_strategy_invalid")
    began = perf_counter()
    chunks, metadata, all_vectors, signature, snapshot_hit = snapshot(settings, load_index)
    source_ms = (perf_counter() - began) * 1000
    # Candidate restriction happens before scoring for both retrieval channels.
    allowed = {doc_id} if isinstance(doc_id, str) else set(doc_id)
    if not allowed or any(not isinstance(value, str) or not value for value in allowed):
        raise DocumentError("检索需要非空的明确文档范围。", "rag_scope_invalid")
    indexed_ids = {chunk["doc_id"] for chunk in chunks}
    if not allowed.issubset(indexed_ids):
        raise DocumentError("指定文档尚未建立索引。", "document_not_indexed")
    selected = [(index, chunk) for index, chunk in enumerate(chunks) if chunk["doc_id"] in allowed]
    if not selected:
        raise DocumentError("指定文档尚未建立索引。", "document_not_indexed")
    cache_enabled = getattr(settings, "rag_cache_enabled", True)
    lexical_began = perf_counter()
    query_tokens = tokenize(query or question)
    if strategy == "dense":
        import numpy as np
        corpus, lexical_model, corpus_hit = [], None, False
        lexical_scores = np.zeros(len(selected), dtype=np.float32)
    else:
        corpus, lexical_model, corpus_hit = scoped_corpus(signature, allowed, selected, tokenize, cache_enabled)
        lexical_scores = lexical_model.get_scores(query_tokens) if lexical_model is not None else [0.] * len(selected)
    lexical_order = sorted(range(len(selected)), key=lambda i: (-float(lexical_scores[i]), selected[i][1]["chunk_id"]))
    # BM25Okapi can produce zero/negative scores for a term appearing in every
    # passage. Such a term still matches; only true token-disjoint passages
    # are excluded, rather than silently dropping the whole lexical channel.
    query_set = set(query_tokens)
    lexical_order = [i for i in lexical_order if strategy != "dense" and query_set.intersection(corpus[i])]
    candidate_k = getattr(settings, "rag_candidate_k", 20)
    rrf_k = getattr(settings, "rag_rrf_k", 60)
    lexical_order = lexical_order[:candidate_k]
    ranking = {i: 1 / (rrf_k + rank) for rank, i in enumerate(lexical_order, 1)}
    lexical_ms = (perf_counter() - lexical_began) * 1000
    dense_scores = None
    dense_config = metadata.get("dense_embedding", {})
    method = "bm25"
    dense_order = []
    query_hit = False
    dense_began = perf_counter()
    # A keyword-only control uses the same frozen chunks/index, not a missing
    # model directory. Never initialize or query the encoder in this arm.
    if dense_config.get("enabled") and strategy != "bm25":
        import numpy as np
        from qa_agent.rag.embeddings import get_embedder
        embedder = get_embedder(settings)
        if embedder is None:
            raise DocumentError("索引使用的真实 BGE 模型不可用，请恢复模型或重建索引。", "embedding_unavailable")
        active_meta = embedder.metadata() if callable(getattr(embedder, "metadata", None)) else {}
        for key in ("model_sha256", "model_revision", "model_id", "model", "revision", "files", "max_length",
                    "mode", "pooling", "normalization"):
            if key in dense_config and active_meta.get(key) != dense_config[key]:
                raise DocumentError("当前 dense 模型与建索引时不同，请重新建索引。", "embedding_model_mismatch")
        model_key = (str(Path(settings.bge_model_path).resolve()),
                     json.dumps(active_meta, sort_keys=True, default=str), query or question)
        q, query_hit = query_vector(model_key, embedder, query or question, cache_enabled)
        if all_vectors.ndim != 2 or all_vectors.shape[0] != len(chunks) or q.shape != (1, all_vectors.shape[1]):
            raise DocumentError("dense 向量维度与 chunk 不匹配。", "embedding_invalid")
        vectors = all_vectors[[i for i, _ in selected]]
        denominator = np.maximum(np.linalg.norm(vectors, axis=1) * np.linalg.norm(q[0]), 1e-12)
        dense_scores = (vectors @ q[0]) / denominator
        if not np.isfinite(dense_scores).all():
            raise DocumentError("dense 相似度出现非有限值。", "embedding_invalid")
        dense_order = sorted(range(len(selected)), key=lambda i: (-float(dense_scores[i]), selected[i][1]["chunk_id"]))[:candidate_k]
        for rank, i in enumerate(dense_order, 1):
            ranking[i] = ranking.get(i, 0) + 1 / (rrf_k + rank)
        method = "bm25+bge-m3_dense_rrf"
    elif strategy == "dense":
        raise DocumentError("纯向量对照需要真实dense索引。", "embedding_unavailable")
    dense_ms = (perf_counter() - dense_began) * 1000 if dense_scores is not None else 0.
    fusion_began = perf_counter()
    fused_order = sorted(ranking, key=lambda i: (-ranking[i], selected[i][1]["chunk_id"]))
    fusion_ms = (perf_counter() - fusion_began) * 1000
    rerank_details, expansion = {}, []
    rerank_began = perf_counter()
    if strategy == "dense":
        ordered = dense_order[:settings.rag_top_k]
        method = "bge-m3_dense"
    elif strategy == "hybrid_rerank":
        from qa_agent.rag.reranker import rerank, source_neighbors
        selected_chunks = [chunk for _, chunk in selected]
        reordered, rerank_details = rerank(fused_order, ranking, selected_chunks, corpus, query_tokens)
        ordered, expansion = source_neighbors(reordered, selected_chunks, settings.rag_top_k)
        method += "+local_coverage_rerank+source_neighbors"
    else:
        ordered = fused_order[:settings.rag_top_k]
    rerank_ms = (perf_counter() - rerank_began) * 1000 if strategy == "hybrid_rerank" else 0.
    results = []
    for position, i in enumerate(ordered, 1):
        item = deepcopy(selected[i][1])
        score = float(dense_scores[i]) if strategy == "dense" else float(lexical_scores[i]) if strategy == "bm25" else ranking.get(i, 0.)
        item.update(evidence_id=f"E{position}", score=round(score, 8),
                    score_type="cosine_similarity" if strategy == "dense" else "bm25" if strategy == "bm25" else "rrf",
                    retrieval_origin="source_neighbor" if i not in ranking else "ranked_candidate",
                    bm25_score=round(float(lexical_scores[i]), 6))
        if dense_scores is not None:
            item["dense_score"] = round(float(dense_scores[i]), 6)
        if i in rerank_details:
            item["rerank"] = rerank_details[i]
        results.append(item)
    def ranking_records(order, scores):
        return [{"rank": rank, "chunk_id": selected[i][1]["chunk_id"], "doc_id": selected[i][1]["doc_id"],
                 "page": selected[i][1]["page"], "section_path": selected[i][1]["section_path"],
                 "score": round(float(scores[i]), 8)} for rank, i in enumerate(order, 1)]
    return results, {"retrieval_method": method, "candidate_count": len(selected), "top_k": settings.rag_top_k,
                     "allowed_doc_ids": sorted(allowed),
                     "searched_page_count": len({(c["doc_id"], c["page"]) for _, c in selected}),
                     "candidate_k_per_channel": candidate_k, "rrf_k": rrf_k, "rank_starts_at": 1,
                     "rankings": {"bm25": ranking_records(lexical_order, lexical_scores),
                                  "dense": ranking_records(dense_order, dense_scores) if dense_scores is not None else [],
                                  "rrf": ranking_records(fused_order, ranking) if strategy not in {"dense", "bm25"} else []},
                     "hit_at_5_scope": [selected[i][1]["chunk_id"] for i in ordered[:5]],
                     "retrieval_strategy": strategy,
                     "reranker": {"kind": "local_query_coverage_not_cross_encoder", "enabled": strategy == "hybrid_rerank",
                                  "weights": {"rrf": .60, "query_coverage": .30, "phrase": .10},
                                  "source_expansion": expansion},
                     "final_ranking": [{"rank": pos, "chunk_id": selected[i][1]["chunk_id"]}
                                       for pos, i in enumerate(ordered, 1)],
                     "cache": {"enabled": cache_enabled, "snapshot_hit": snapshot_hit,
                               "corpus_hit": corpus_hit, "query_vector_hit": query_hit},
                     "retrieval_timing_ms": {"source_validation": round(source_ms, 3),
                                             "lexical_scoring": round(lexical_ms, 3),
                                             "dense_scoring": round(dense_ms, 3),
                                             "fusion_ordering": round(fusion_ms, 3),
                                             "reranking_and_neighbors": round(rerank_ms, 3),
                                             "total": round((perf_counter() - began) * 1000, 3)},
                     "retrieved_count": len(results), "index_created_at": metadata["created_at"],
                     "index_chunks_sha256": metadata["chunks_sha256"],
                     "query": query or question, "dense_enabled": dense_scores is not None}
