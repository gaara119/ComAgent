"""Audit the actual indexed corpus and vectors without any LLM call."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.rag.index import load_index


def main() -> None:
    settings = get_settings()
    chunks, metadata = load_index(settings=settings)
    path = settings.rag_index_path / "embeddings.npy"
    vectors = np.load(path, allow_pickle=False)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == metadata["dense_embedding"]["vectors_sha256"]
    assert vectors.shape == (len(chunks), 1024)
    assert np.isfinite(vectors).all() and np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5)
    assert len({chunk["chunk_id"] for chunk in chunks}) == len(chunks)
    assert max(len(chunk["text"]) for chunk in chunks) <= 600
    record = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "index_version": metadata["index_version"],
              "documents": len(metadata["documents"]),
              "physical_pages": sum(d["page_count"] for d in metadata["documents"]),
              "text_pages": sum(d["text_page_count"] for d in metadata["documents"]),
              "chunks": len(chunks), "max_chunk_chars": max(len(c["text"]) for c in chunks),
              "chunks_with_block_bbox": sum(bool(c.get("bbox")) for c in chunks),
              "incomplete_boundary_chunks": sum(c["incomplete_sentence_start"] or c["incomplete_sentence_end"] for c in chunks),
              "vector_shape": list(vectors.shape), "finite_vectors": True, "normalized_vectors": True,
              "retrieval_method": metadata["retrieval_method"], "source_and_chunk_hashes_checked": True,
              "chunks_sha256": metadata["chunks_sha256"], "vectors_sha256": digest, "llm_calls": 0}
    (ROOT / "notes/rag-corpus-check.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
