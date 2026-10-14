"""Check registered fusion documents and actual retrieval; no DB/model call."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.documents import load_documents, verify_document_hash
from qa_agent.rag.retriever import retrieve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT / "eval/artifacts/d4") or out.exists():
        raise ValueError("Use a fresh D4 evidence directory")
    settings = get_settings()
    docs = load_documents(settings.rag_manifest_path)
    records = []
    for doc_id, query in [("project-metric-manual", "客单价 平均每张发票金额 定义 AVG invoice.total"),
                          ("artist-iron-maiden", "Iron Maiden 音乐风格 背景"),
                          ("artist-u2", "U2 音乐风格 背景")]:
        document = next(d for d in docs if d["doc_id"] == doc_id)
        verify_document_hash(document)
        chunks, metadata = retrieve(query, doc_id, settings=settings)
        records.append({"doc_id": doc_id, "entity_ref": document["entity_ref"],
            "source_sha256": document["content_hash"], "query": query, "metadata": metadata,
            "chunks": chunks, "scope_valid": all(c["doc_id"] == doc_id for c in chunks),
            "manual_expression_found": (any("AVG(invoice.total)" in c["text"] for c in chunks)
                                        if doc_id == "project-metric-manual" else None)})
        print(json.dumps({"doc_id": doc_id, "actual_retrieved_chunks": len(chunks),
                          "method": metadata["retrieval_method"],
                          "manual_expression_found": records[-1]["manual_expression_found"]}, ensure_ascii=False), flush=True)
    out.mkdir(parents=True)
    payload = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, *sys.argv],
               "records": records, "llm_calls": 0, "db_queries": 0, "held_predictions": 0}
    (out / "source-retrieval.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(r["scope_valid"] and r["chunks"] for r in records) and records[0]["manual_expression_found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
