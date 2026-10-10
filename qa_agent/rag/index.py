"""Persist chunks and provenance; reject modified documents or index artifacts."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from qa_agent.config import get_settings
from qa_agent.rag.chunker import chunk_pages
from qa_agent.rag.parsers import DocumentError, load_documents, parse_pdf

INDEX_VERSION = 1


def _write(path: Path, data: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def build_index(manifest_path=None, index_path=None, *, settings=None) -> dict:
    settings = settings or get_settings()
    manifest_path = Path(manifest_path or settings.rag_manifest_path)
    target = Path(index_path or settings.rag_index_path)
    documents = load_documents(manifest_path)
    chunks: list[dict] = []
    summaries = []
    for document in documents:
        pages = parse_pdf(document)
        own_chunks = chunk_pages(pages)
        if not own_chunks:
            raise DocumentError(f"文档 {document['doc_id']} 没有文本层；D1 不虚构 OCR 内容。", "pdf_no_text")
        chunks.extend(own_chunks)
        summaries.append({key: document.get(key, "") for key in
                          ("doc_id", "title", "path", "content_hash", "source_url", "license", "language", "domain")})
        summaries[-1].update(page_count=len(pages), text_page_count=sum(bool(p["text"]) for p in pages),
                             chunk_count=len(own_chunks), blank_pages=[p["page"] for p in pages if not p["text"]])
    data = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")
    target.mkdir(parents=True, exist_ok=True)
    metadata = {"index_version": INDEX_VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
                "retrieval_method": "bm25", "manifest_hash": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                "documents": summaries, "chunk_count": len(chunks),
                "chunks_sha256": hashlib.sha256(data).hexdigest(),
                "parsing": {"text": "pdfplumber text layer", "layout": "PyMuPDF.get_text(dict)",
                            "bbox_scope": "union_of_text_blocks", "coordinate_system": "PDF points; top-left origin"},
                "chunking": {"max_chars": 600, "overlap": 80, "cross_page": False},
                "dense_embedding": {"enabled": False}}
    # Dense is used only if the real model and encoder are present. Root owns embeddings.py.
    try:
        from qa_agent.rag.embeddings import get_embedder
    except ImportError:
        get_embedder = None
    if get_embedder is not None:
        embedder = get_embedder(settings)
        if embedder is not None:
            import numpy as np
            embedding_texts = ["\n".join([c["doc_title"], *c["section_path"], c["text"]]) for c in chunks]
            vectors = np.asarray(embedder.encode(embedding_texts), dtype=np.float32)
            if vectors.ndim != 2 or len(vectors) != len(chunks) or not np.isfinite(vectors).all():
                raise DocumentError("真实 dense 编码结果维度或数值异常。", "embedding_invalid")
            temporary = target / "embeddings.tmp.npy"
            np.save(temporary, vectors, allow_pickle=False)
            temporary.replace(target / "embeddings.npy")
            provenance = embedder.metadata() if callable(getattr(embedder, "metadata", None)) else {}
            metadata["dense_embedding"] = {**provenance, "enabled": True, "dimension": vectors.shape[1],
                                           "vectors_sha256": hashlib.sha256((target / "embeddings.npy").read_bytes()).hexdigest()}
            metadata["retrieval_method"] = "bm25+bge-m3_dense_rrf"
    _write(target / "chunks.jsonl", data)
    _write(target / "index_meta.json", json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"))
    return metadata


def load_chunks(index_path=None, *, settings=None, verify_sources: bool = True) -> list[dict]:
    chunks, _ = load_index(index_path, settings=settings, verify_sources=verify_sources)
    return chunks


def load_index(index_path=None, *, settings=None, verify_sources: bool = True) -> tuple[list[dict], dict]:
    settings = settings or get_settings()
    target = Path(index_path or settings.rag_index_path)
    try:
        metadata = json.loads((target / "index_meta.json").read_text(encoding="utf-8"))
        raw = (target / "chunks.jsonl").read_bytes()
    except (OSError, ValueError) as exc:
        raise DocumentError("文档索引尚未建立或无法读取，请运行 scripts/ingest_docs.py。", "rag_index_missing") from exc
    if metadata.get("index_version") != INDEX_VERSION or hashlib.sha256(raw).hexdigest() != metadata.get("chunks_sha256"):
        raise DocumentError("文档索引内容不完整或已修改，请重新建索引。", "rag_index_corrupt")
    if verify_sources:
        docs = load_documents(settings.rag_manifest_path)
        from qa_agent.documents import verify_document_hash
        for document in docs:
            try:
                verify_document_hash(document)
            except ValueError as exc:
                raise DocumentError(str(exc), "document_hash_mismatch") from exc
        current = {d["doc_id"]: d["content_hash"] for d in docs}
        indexed = {d["doc_id"]: d["content_hash"] for d in metadata["documents"]}
        if current != indexed or hashlib.sha256(settings.rag_manifest_path.read_bytes()).hexdigest() != metadata["manifest_hash"]:
            raise DocumentError("清单或源 PDF 已变化，请重新建立文档索引。", "rag_index_stale")
    try:
        chunks = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        if len(chunks) != metadata["chunk_count"] or len({c["chunk_id"] for c in chunks}) != len(chunks):
            raise ValueError("chunk count or IDs")
    except (ValueError, KeyError) as exc:
        raise DocumentError("文档索引 chunk 格式异常。", "rag_index_corrupt") from exc
    return chunks, metadata
