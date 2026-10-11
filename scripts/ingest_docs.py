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
    parser.add_argument("--output-dir", type=Path, help="D2 alias for --index-path; preserve the D1 index")
    parser.add_argument("--audit-output", type=Path, default=Path("eval/artifacts/d2/docs-audit.json"))
    args = parser.parse_args()
    settings = get_settings()
    try:
        if args.index_path and args.output_dir and args.index_path != args.output_dir:
            raise ValueError("--index-path 与 --output-dir 不得指向不同位置。")
        metadata = build_index(args.manifest, args.output_dir or args.index_path, settings=settings)
    except Exception as exc:
        print(sanitize_error(exc, settings), file=sys.stderr)
        return 2
    report = {
        "created_at": metadata["created_at"], "retrieval_method": metadata["retrieval_method"],
        "chunk_count": metadata["chunk_count"], "chunking": metadata["chunking"],
        "dense_embedding": metadata["dense_embedding"],
        "manifest_document_count": len(metadata["documents"])+len(metadata.get("failed_documents", [])),
        "parsed_document_count": len(metadata["documents"]), "documents": metadata["documents"],
        "failed_documents": metadata.get("failed_documents", []),
        "command": " ".join([".\\.venv\\Scripts\\python.exe", *sys.argv]),
    }
    output = args.audit_output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["failed_documents"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
