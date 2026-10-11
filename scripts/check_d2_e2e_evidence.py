"""Offline authenticity checks over actual D2 E2E responses; no model/DB calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.rag.index import load_index
from qa_agent.rag.answer import DocumentAnswer, validate_answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; keep the prior check and choose a new output")
    settings = get_settings()
    all_chunks, meta = load_index(settings=settings)
    chunks = {c["chunk_id"]: c for c in all_chunks}
    checks = []
    for path in sorted(args.run_dir.glob("*-raw.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        response = record["response"]
        if record["request"]["scope"]["route"] != "doc":
            continue
        doc_id = record["request"]["scope"]["doc_ids"][0]
        candidates = response.get("metadata", {}).get("retrieved_pages", [])
        source_by_id = {c["evidence_id"]: chunks.get(c["chunk_id"]) for c in candidates}
        used = response.get("evidences", [])
        evidence_checks = []
        for evidence in used:
            source = source_by_id.get(evidence["evidence_id"])
            keys = ("doc_id", "page", "section_path", "text", "bbox")
            matching = bool(source) and all(evidence.get(k) == source.get(k) for k in keys)
            evidence_checks.append({"evidence_id": evidence["evidence_id"], "source_chunk_exists": bool(source),
                                    "doc_page_section_text_bbox_match": matching,
                                    "selected_doc_matches": evidence["doc_id"] == doc_id,
                                    "source_chunk_id": source["chunk_id"] if source else None,
                                    "source_parser": source.get("parser") if source else None,
                                    "source_warnings": source.get("warnings", []) if source else []})
        available = [{**chunks[c["chunk_id"]], "evidence_id": c["evidence_id"]}
                     for c in candidates if c["chunk_id"] in chunks]
        validation = {"passed": False}
        try:
            validate_answer(DocumentAnswer(status=response["status"], answer=response["answer"],
                                           citation_ids=[e["evidence_id"] for e in used]), available)
            validation["passed"] = True
        except Exception as exc:
            validation["error_type"] = type(exc).__name__
            validation["error"] = str(exc)
        checks.append({"raw_response": path.resolve().relative_to(ROOT).as_posix(),
                       "response_sha256": sha256(path.read_bytes()).hexdigest(), "trace_id": response["trace_id"],
                       "status": response["status"], "doc_id": doc_id, "evidence_count": len(used),
                       "evidence_checks": evidence_checks, "citation_number_validation": validation,
                       "all_source_checks_passed": all(c["doc_page_section_text_bbox_match"] and c["selected_doc_matches"] for c in evidence_checks),
                       "human_faithfulness_review": "pending"})
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "command": " ".join(sys.argv),
              "method": "actual response joined to independently loaded hash-verified current index",
              "index_chunk_sha256": meta["chunks_sha256"], "source_verification_enabled": True,
              "human_review_count": 0, "checks": checks,
              "passed": bool(checks) and all(c["all_source_checks_passed"] and c["citation_number_validation"]["passed"] for c in checks)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "checked_responses": len(checks), "output": args.output.as_posix()}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
