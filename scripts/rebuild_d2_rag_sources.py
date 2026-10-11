"""Rebuild D2 RAG provenance in a new index, retaining verified parse caches."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import inspect
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings, sanitize_error
import qa_agent.rag.index as indexing
from qa_agent.rag.parsers import parse_pdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-path", type=Path, default=ROOT/"data/indexes/docs-d2-final-v4")
    parser.add_argument("--evidence", type=Path, default=ROOT/"eval/artifacts/d2-final/rag")
    parser.add_argument("--parse-cache-from",type=Path)
    parser.add_argument("--vectors-from",type=Path)
    args = parser.parse_args()
    settings = get_settings()
    args.evidence.mkdir(parents=True, exist_ok=True)
    cache = args.evidence/"parsed-sources"
    cache.mkdir(exist_ok=True)
    parser_bytes = (ROOT/"qa_agent/rag/parsers.py").read_bytes()
    code_hash = hashlib.sha256(parser_bytes).hexdigest()
    import qa_agent.rag.parsers as parsing
    # The PDF parser imports heading classification from chunker.py. Include
    # that dependency, so changing procedure/heading rules cannot silently
    # reuse old parsed section labels.
    parse_dependency_hash = hashlib.sha256(parser_bytes + inspect.getsource(parsing.is_heading_candidate).encode()).hexdigest()
    ocr_fingerprints = {name:hashlib.sha256(inspect.getsource(getattr(parsing,name)).encode()).hexdigest()
                        for name in ("_ocr_text","_ocr_engine","_scan_image_coverage")}
    previous_fingerprints = json.loads((args.parse_cache_from/"ocr-cache-fingerprints.json").read_text(encoding="utf8")) if args.parse_cache_from else None
    events = []
    def cached_parse(document):
        path = cache/f"{document['doc_id']}.json"
        old_path = args.parse_cache_from/"parsed-sources"/path.name if args.parse_cache_from else path
        cached = json.loads((path if path.exists() else old_path).read_text(encoding="utf8")) if path.exists() or old_path.exists() else None
        reusable = cached and cached.get("parse_dependency_sha256")==parse_dependency_hash and cached.get("source_sha256")==document["content_hash"]
        print(f"{'Cache' if reusable else 'Parsing'} {document['doc_id']}", flush=True)
        ocr_cache = {page["page"]:page for page in cached["pages"] if page["parser"]=="RapidOCR"} if (cached
                    and cached.get("source_sha256")==document["content_hash"] and previous_fingerprints==ocr_fingerprints) else {}
        pages = cached["pages"] if reusable else parse_pdf(document,rendered_ocr_cache=ocr_cache)
        if not reusable:
            path.write_text(json.dumps({"parser_sha256":code_hash,"parse_dependency_sha256":parse_dependency_hash,"source_sha256":document["content_hash"],
                                        "pages":pages},ensure_ascii=False),encoding="utf8")
        event = {"doc_id":document["doc_id"],"pages":len(pages),"cache_reused":bool(reusable),
                 "verified_rendered_ocr_cache_pages":len(ocr_cache) if not reusable else 0,
                 "ocr_pages":sum(p["parser"]=="RapidOCR" for p in pages),
                 "utc":datetime.now(timezone.utc).isoformat()}
        events.append(event)
        (args.evidence/"parse-events.json").write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding="utf8")
        print(json.dumps(event,ensure_ascii=False),flush=True)
        return pages
    indexing.parse_pdf = cached_parse
    if args.vectors_from:
        import numpy as np
        import qa_agent.rag.embeddings as embedding_module
        old_meta = json.loads((args.vectors_from/"index_meta.json").read_text(encoding="utf8"))
        old_dense = old_meta["dense_embedding"]
        old_vector_path = args.vectors_from/"embeddings.npy"
        if hashlib.sha256(old_vector_path.read_bytes()).hexdigest()!=old_dense["vectors_sha256"]:
            raise ValueError("Vector cache hash mismatch")
        old_chunks = [json.loads(line) for line in (args.vectors_from/"chunks.jsonl").read_text(encoding="utf8").splitlines() if line.strip()]
        if hashlib.sha256((args.vectors_from/"chunks.jsonl").read_bytes()).hexdigest()!=old_meta["chunks_sha256"]:
            raise ValueError("Chunk cache hash mismatch")
        old_matrix = np.load(old_vector_path,allow_pickle=False)
        lookup = {"\n".join([c["doc_title"],*c["section_path"],c["text"]]):old_matrix[i] for i,c in enumerate(old_chunks)}
        original_encoder = embedding_module.get_embedder
        class VerifiedVectorCache:
            def __init__(self,encoder):
                self.encoder,self.reused = encoder,0
                current = encoder.metadata()
                if any(current.get(key)!=old_dense.get(key) for key in ("model_sha256","model_revision","max_length","mode")):
                    raise ValueError("Vector cache model/config mismatch")
            def metadata(self):
                return {**self.encoder.metadata(),"exact_input_vector_cache_reused":self.reused,
                        "vector_cache_source":str(args.vectors_from.resolve().relative_to(ROOT)).replace("\\","/")}
            def encode(self,texts):
                missing = [i for i,text in enumerate(texts) if text not in lookup]
                fresh = self.encoder.encode([texts[i] for i in missing])
                results = [lookup.get(text) for text in texts]
                for i,vector in zip(missing,fresh):
                    results[i] = vector
                self.reused += len(texts)-len(missing)
                print(f"Verified vector cache reused {len(texts)-len(missing)}/{len(texts)}; newly encoded {len(missing)}",flush=True)
                return np.asarray(results,dtype=np.float32)
        embedding_module.get_embedder = lambda settings: VerifiedVectorCache(original_encoder(settings))
    try:
        metadata = indexing.build_index(index_path=args.index_path, settings=settings)
    except Exception as exc:
        print(sanitize_error(exc,settings),file=sys.stderr)
        return 2
    metadata.update(command=".\\.venv\\Scripts\\python.exe -B scripts/rebuild_d2_rag_sources.py "+" ".join(sys.argv[1:]),
                    parser_sha256=code_hash, parse_dependency_sha256=parse_dependency_hash, original_index_preserved="data/indexes/docs-final")
    (args.evidence/"docs-audit.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf8")
    (args.evidence/"ocr-cache-fingerprints.json").write_text(json.dumps(ocr_fingerprints,indent=2),encoding="utf8")
    print(json.dumps({"chunks":metadata["chunk_count"],"failures":len(metadata["failed_documents"]),
                      "index":str(args.index_path)},ensure_ascii=False),flush=True)
    return 2 if metadata["failed_documents"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
