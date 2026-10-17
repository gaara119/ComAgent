"""Persist chunks and provenance; reject modified documents or index artifacts."""
from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from qa_agent.config import get_settings
from qa_agent.rag.chunker import chunk_pages
from qa_agent.rag.parsers import DocumentError, load_documents, parse_pdf, parse_document

INDEX_VERSION = 4


def _fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def _parsing_signature(settings) -> str:
    """Invalidate cached source locations when parsing or chunking code changes."""
    return _fingerprint({"implementation": {
        name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ("parsers.py", "chunker.py")},
        "max_chars": getattr(settings, "rag_chunk_chars", 500),
        "overlap": getattr(settings, "rag_chunk_overlap", 80)})


def _embedding_text(chunk: dict) -> str:
    return "\n".join([chunk["doc_title"], *chunk["section_path"], chunk["text"]])


def _previous_index(target: Path, settings) -> tuple[list[dict], dict, str]:
    if not (target / "index_meta.json").exists():
        return [], {}, "missing"
    try:
        # Old source hashes may differ during incremental ingestion. The cached
        # artifacts themselves still need all integrity checks before any reuse.
        chunks, metadata = load_index(target, settings=settings, verify_sources=False)
        return chunks, metadata, "verified"
    except DocumentError as exc:
        # build_index repairs a corrupt cache from original sources; runtime
        # load_index continues to reject it rather than serving bad evidence.
        return [], {}, f"cold_rebuild:{exc.code}"


def _write(path: Path, data: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def build_index(manifest_path=None, index_path=None, *, settings=None) -> dict:
    settings = settings or get_settings()
    manifest_path = Path(manifest_path or settings.rag_manifest_path)
    target = Path(index_path or settings.rag_index_path)
    documents = load_documents(manifest_path)
    old_chunks, old_metadata, cache_status = _previous_index(target, settings)
    old_documents = {d["doc_id"]: d for d in old_metadata.get("documents", [])}
    old_by_document: dict[str, list[dict]] = defaultdict(list)
    for chunk in old_chunks:
        old_by_document[chunk["doc_id"]].append(chunk)
    parsing_signature = _parsing_signature(settings)
    incremental = {"enabled": True, "cache_status": cache_status, "reused_document_count": 0,
                   "parsed_document_count": 0, "reused_chunk_count": 0,
                   "reused_vector_count": 0, "embedded_chunk_count": 0,
                   "removed_document_count": len(set(old_documents) - {d["doc_id"] for d in documents})}
    chunks: list[dict] = []
    summaries, failures = [], []
    for document in documents:
        summary = {key: document.get(key, "") for key in
                   ("doc_id", "title", "format", "path", "content_hash", "source_url", "license", "language", "domain",
                    "source_document_id", "entity_ref", "is_derived", "derived_from", "license_note")}
        try:
            if document.get("ingestion_status", "").lower() in {"failed", "excluded"}:
                raise DocumentError("清单标为失败或排除，不建立运行索引。", "manifest_not_ready")
            from qa_agent.documents import verify_document_hash
            try:
                verify_document_hash(document)
            except ValueError as exc:
                raise DocumentError(str(exc), "document_hash_mismatch") from exc
            source_fingerprint = _fingerprint({"parsing_signature": parsing_signature,
                "document": {key: value for key, value in document.items() if key != "resolved_path"}})
            previous = old_documents.get(document["doc_id"], {})
            own_chunks = old_by_document.get(document["doc_id"], [])
            if (previous.get("ingestion_fingerprint") == source_fingerprint and own_chunks
                    and len(own_chunks) == previous.get("chunk_count")):
                chunks.extend(own_chunks)
                summaries.append(dict(previous))
                incremental["reused_document_count"] += 1
                incremental["reused_chunk_count"] += len(own_chunks)
                continue
            incremental["parsed_document_count"] += 1
            pages = parse_pdf(document) if document["format"] == "pdf" else parse_document(document)
            own_chunks = chunk_pages(pages, max_chars=getattr(settings, "rag_chunk_chars", 500),
                                     overlap=getattr(settings, "rag_chunk_overlap", 80))
            if not own_chunks:
                raise DocumentError(f"文档 {document['doc_id']} 没有可用解析文本，不生成假片段。", "document_no_text")
            chunks.extend(own_chunks)
            summary.update(ingestion_status="ingested", ingestion_fingerprint=source_fingerprint,
                           page_count=len(pages) if document["format"] == "pdf" else None,
                           parsed_record_count=len(pages), text_page_count=sum(bool(p["text"]) for p in pages),
                           chunk_count=len(own_chunks), blank_pages=[p["page"] for p in pages if not p["text"]],
                           parsers=sorted({p.get("parser", "pdfplumber+PyMuPDF") for p in pages}),
                           warnings=[w for p in pages for w in p.get("warnings", [])],
                           source_location_sample={key: own_chunks[0].get(key) for key in
                                                   ("chunk_id", "page", "section_path", "bbox", "char_start", "char_end", "parser")})
            summaries.append(summary)
        except DocumentError as exc:
            failures.append({**summary, "ingestion_status": "failed", "error_code": exc.code,
                             "error": str(exc), "chunk_count": 0})
    if not chunks:
        raise DocumentError("清单中没有成功解析的文档，未创建索引。", "documents_no_text")
    data = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in chunks).encode("utf-8")
    target.mkdir(parents=True, exist_ok=True)
    metadata = {"index_version": INDEX_VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
                "retrieval_method": "bm25", "manifest_hash": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                "documents": summaries, "failed_documents": failures, "chunk_count": len(chunks),
                "incremental": incremental,
                "chunks_sha256": hashlib.sha256(data).hexdigest(),
                "parsing": {"text": "pdfplumber/PyMuPDF + RapidOCR + python-docx + BeautifulSoup + Markdown",
                            "layout": "actual physical PDF/image coordinates; section paths for other formats",
                            "bbox_scope": "union_of_text_blocks within one source region",
                            "coordinate_system": "visible CropBox PDF points; top-left origin; unrotated",
                            "scanned_page_policy": "rendered OCR when raster covers >=80% including long hidden OCR layers",
                            "section_policy": "same-column native typography on current page, otherwise unknown"},
                "chunking": {"max_chars": getattr(settings, "rag_chunk_chars", 500),
                             "overlap": getattr(settings, "rag_chunk_overlap", 80), "cross_page": False, "cross_section": False,
                             "boundary_policy": "complete_sentence_or_table_line",
                             "incomplete_chunk_count": sum(c["incomplete_sentence_start"] or c["incomplete_sentence_end"] for c in chunks)},
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
            provenance = embedder.metadata() if callable(getattr(embedder, "metadata", None)) else {}
            # Unknown encoder identity must never permit reuse across builds.
            signature = _fingerprint({"encoder": provenance, "text_template": "title-section-source:v1",
                "max_length": getattr(settings, "rag_embedding_max_length", 512),
                "device": getattr(settings, "rag_embedding_device", "cpu"),
                "quantization": getattr(settings, "rag_embedding_quantization", "int8")}) if provenance else None
            old_dense = old_metadata.get("dense_embedding", {})
            old_rows = {}
            if signature and old_dense.get("enabled") and old_dense.get("embedding_signature") == signature:
                old_vectors = np.load(target / "embeddings.npy", allow_pickle=False)
                old_rows = {chunk["chunk_id"]: (_embedding_text(chunk), old_vectors[i])
                            for i, chunk in enumerate(old_chunks)}
            embedding_texts = [_embedding_text(c) for c in chunks]
            rows, pending = [None] * len(chunks), []
            for i, chunk in enumerate(chunks):
                cached = old_rows.get(chunk["chunk_id"])
                if cached is not None and cached[0] == embedding_texts[i]:
                    rows[i] = cached[1]
                    incremental["reused_vector_count"] += 1
                else:
                    pending.append(i)
            if pending:
                encoded = np.asarray(embedder.encode([embedding_texts[i] for i in pending]), dtype=np.float32)
                if encoded.ndim != 2 or len(encoded) != len(pending) or not np.isfinite(encoded).all():
                    raise DocumentError("真实 dense 编码结果维度或数值异常。", "embedding_invalid")
                for i, vector in zip(pending, encoded):
                    rows[i] = vector
            incremental["embedded_chunk_count"] = len(pending)
            try:
                vectors = np.asarray(rows, dtype=np.float32)
            except ValueError as exc:
                raise DocumentError("增量 dense 编码维度与缓存不一致。", "embedding_invalid") from exc
            if vectors.ndim != 2 or len(vectors) != len(chunks) or not np.isfinite(vectors).all():
                raise DocumentError("真实 dense 编码结果维度或数值异常。", "embedding_invalid")
            temporary = target / "embeddings.tmp.npy"
            np.save(temporary, vectors, allow_pickle=False)
            temporary.replace(target / "embeddings.npy")
            metadata["dense_embedding"] = {**provenance, "enabled": True, "dimension": vectors.shape[1],
                                           "embedding_signature": signature,
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
    if not isinstance(metadata, dict) or metadata.get("index_version") not in {2, 3, INDEX_VERSION} or hashlib.sha256(raw).hexdigest() != metadata.get("chunks_sha256"):
        raise DocumentError("文档索引内容不完整或已修改，请重新建索引。", "rag_index_corrupt")
    if verify_sources:
        docs = load_documents(settings.rag_manifest_path)
        from qa_agent.documents import verify_document_hash
        for document in docs:
            try:
                verify_document_hash(document)
            except ValueError as exc:
                raise DocumentError(str(exc), "document_hash_mismatch") from exc
        failed_ids = {d["doc_id"] for d in metadata.get("failed_documents", [])}
        current = {d["doc_id"]: d["content_hash"] for d in docs if d["doc_id"] not in failed_ids}
        indexed = {d["doc_id"]: d["content_hash"] for d in metadata["documents"]}
        if current != indexed or hashlib.sha256(settings.rag_manifest_path.read_bytes()).hexdigest() != metadata["manifest_hash"]:
            raise DocumentError("清单或源文件已变化，请重新建立文档索引。", "rag_index_stale")
    try:
        chunks = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        if len(chunks) != metadata["chunk_count"] or len({c["chunk_id"] for c in chunks}) != len(chunks):
            raise ValueError("chunk count or IDs")
    except (ValueError, KeyError) as exc:
        raise DocumentError("文档索引 chunk 格式异常。", "rag_index_corrupt") from exc
    dense = metadata.get("dense_embedding", {})
    if dense.get("enabled"):
        import numpy as np
        path = target / "embeddings.npy"
        try:
            if hashlib.sha256(path.read_bytes()).hexdigest() != dense.get("vectors_sha256"):
                raise ValueError("dense artifact hash")
            matrix = np.load(path, allow_pickle=False, mmap_mode="r")
            if matrix.ndim != 2 or matrix.shape != (len(chunks), dense.get("dimension")):
                raise ValueError("dense row count/dimension")
            if not np.isfinite(matrix).all():
                raise ValueError("dense values")
        except (OSError, ValueError) as exc:
            raise DocumentError("dense 矩阵行数或维度与登记片段不一致。", "rag_index_corrupt") from exc
    return chunks, metadata
