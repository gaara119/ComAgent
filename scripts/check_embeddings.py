"""Check the actual local CPU BGE encoder without an LLM call."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.rag.embeddings import get_embedder


def main() -> int:
    started = time.perf_counter()
    embedder = get_embedder()
    if embedder is None:
        print("Model unavailable; run scripts/download_embeddings.py first.")
        return 2
    vectors = embedder.encode([
        "How can I put my MacBook Air to sleep?",
        "Close the MacBook Air display to put it to sleep.",
        "The oil reservoir contains sandstone.",
    ])
    norms = np.linalg.norm(vectors, axis=1)
    related = float(vectors[0] @ vectors[1])
    unrelated = float(vectors[0] @ vectors[2])
    checks = {"actual_shape_3_by_1024": vectors.shape == (3, 1024),
              "finite_normalized_vectors": bool(np.isfinite(vectors).all() and np.allclose(norms, 1)),
              "single_pair_similarity_smoke": related > unrelated}
    record = {"checks": checks, "shape": list(vectors.shape), "norms": norms.tolist(),
              "related_cosine": related, "unrelated_cosine": unrelated,
              "elapsed_s": round(time.perf_counter() - started, 3), "model": embedder.metadata(),
              "llm_calls": 0, "note": "This single pair smoke verifies encoder execution; it is not a retrieval accuracy metric."}
    (ROOT / "notes/embedding-check.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"checks": checks, "elapsed_s": record["elapsed_s"], "providers": record["model"]["providers"]}, ensure_ascii=False))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
