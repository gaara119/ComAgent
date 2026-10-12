"""Document-isolated lexical retrieval and optional actual dense RRF fusion."""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

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


def retrieve(question: str, doc_id: str, *, settings=None, query: str | None = None) -> tuple[list[dict], dict]:
    from rank_bm25 import BM25Okapi

    settings = settings or get_settings()
    chunks, metadata = load_index(settings=settings)
    # Candidate restriction happens before scoring for both retrieval channels.
    selected = [(index, chunk) for index, chunk in enumerate(chunks) if chunk["doc_id"] == doc_id]
    if not selected:
        raise DocumentError("指定文档尚未建立索引。", "document_not_indexed")
    corpus = [tokenize("\n".join([chunk["doc_title"], *chunk["section_path"], chunk["text"]])) for _, chunk in selected]
    query_tokens = tokenize(query or question)
    lexical_scores = BM25Okapi(corpus, epsilon=0.25).get_scores(query_tokens)
    lexical_order = sorted(range(len(selected)), key=lambda i: (-float(lexical_scores[i]), selected[i][1]["chunk_id"]))
    # BM25Okapi can produce zero/negative scores for a term appearing in every
    # passage. Such a term still matches; only true token-disjoint passages
    # are excluded, rather than silently dropping the whole lexical channel.
    query_set = set(query_tokens)
    lexical_order = [i for i in lexical_order if query_set.intersection(corpus[i])]
    candidate_k = getattr(settings, "rag_candidate_k", 20)
    rrf_k = getattr(settings, "rag_rrf_k", 60)
    lexical_order = lexical_order[:candidate_k]
    ranking = {i: 1 / (rrf_k + rank) for rank, i in enumerate(lexical_order, 1)}
    dense_scores = None
    dense_config = metadata.get("dense_embedding", {})
    method = "bm25"
    dense_order = []
    if dense_config.get("enabled"):
        import numpy as np
        from qa_agent.rag.embeddings import get_embedder
        path = Path(settings.rag_index_path) / "embeddings.npy"
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != dense_config.get("vectors_sha256"):
            raise DocumentError("dense 索引文件不完整或已修改，请重新建索引。", "rag_index_corrupt")
        embedder = get_embedder(settings)
        if embedder is None:
            raise DocumentError("索引使用的真实 BGE 模型不可用，请恢复模型或重建索引。", "embedding_unavailable")
        active_meta = embedder.metadata() if callable(getattr(embedder, "metadata", None)) else {}
        for key in ("model_sha256", "model_revision", "model_id", "model", "revision", "files", "max_length",
                    "mode", "pooling", "normalization"):
            if key in dense_config and active_meta.get(key) != dense_config[key]:
                raise DocumentError("当前 dense 模型与建索引时不同，请重新建索引。", "embedding_model_mismatch")
        all_vectors = np.load(path, allow_pickle=False)
        q = np.asarray(embedder.encode([query or question]), dtype=np.float32)
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
    fused_order = sorted(ranking, key=lambda i: (-ranking[i], selected[i][1]["chunk_id"]))
    ordered = fused_order[:settings.rag_top_k]
    results = []
    for position, i in enumerate(ordered, 1):
        item = dict(selected[i][1])
        item.update(evidence_id=f"E{position}", score=round(ranking[i], 8),
                    bm25_score=round(float(lexical_scores[i]), 6))
        if dense_scores is not None:
            item["dense_score"] = round(float(dense_scores[i]), 6)
        results.append(item)
    def ranking_records(order, scores):
        return [{"rank": rank, "chunk_id": selected[i][1]["chunk_id"], "doc_id": selected[i][1]["doc_id"],
                 "page": selected[i][1]["page"], "section_path": selected[i][1]["section_path"],
                 "score": round(float(scores[i]), 8)} for rank, i in enumerate(order, 1)]
    return results, {"retrieval_method": method, "candidate_count": len(selected), "top_k": settings.rag_top_k,
                     "candidate_k_per_channel": candidate_k, "rrf_k": rrf_k, "rank_starts_at": 1,
                     "rankings": {"bm25": ranking_records(lexical_order, lexical_scores),
                                  "dense": ranking_records(dense_order, dense_scores) if dense_scores is not None else [],
                                  "rrf": ranking_records(fused_order, ranking)},
                     "hit_at_5_scope": [selected[i][1]["chunk_id"] for i in fused_order[:5]],
                     "retrieved_count": len(results), "index_created_at": metadata["created_at"],
                     "index_chunks_sha256": metadata["chunks_sha256"],
                     "query": query or question, "dense_enabled": dense_scores is not None}
