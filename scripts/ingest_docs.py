"""Build the registered documents' real page chunks and retrieval index."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qa_agent.config import get_settings, sanitize_error
from qa_agent.rag.index import build_index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--index-path", type=Path)
    args = parser.parse_args()
    settings = get_settings()
    try:
        metadata = build_index(args.manifest, args.index_path, settings=settings)
    except Exception as exc:
        print(sanitize_error(exc, settings), file=sys.stderr)
        return 2
    report = {
        "created_at": metadata["created_at"], "retrieval_method": metadata["retrieval_method"],
        "chunk_count": metadata["chunk_count"], "chunking": metadata["chunking"],
        "dense_embedding": metadata["dense_embedding"],
        "documents": [{k: d[k] for k in ("doc_id", "title", "page_count", "text_page_count", "chunk_count", "content_hash")}
                      for d in metadata["documents"]],
    }
    output = Path(__file__).resolve().parents[1] / "notes/rag-index-check.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
