"""Build the actual D3 AW table/column vectors with existing BGE-M3."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.rag.embeddings import get_embedder
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.schema_linker import build_schema_index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog/adventureworks.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "data/indexes/schema-aw-d3-v2")
    args = parser.parse_args()
    embedder = get_embedder(get_settings())
    if embedder is None:
        raise RuntimeError("Verified local BGE-M3 is unavailable")
    metadata = build_schema_index(load_catalog(args.catalog), args.catalog, args.output, embedder)
    summary = {key: metadata[key] for key in ("format", "database", "catalog_sha256", "table_count", "column_count", "table_vector_shape", "column_vector_shape", "tables.npy_sha256", "columns.npy_sha256")}
    artifact = ROOT / "eval/artifacts/d3/a/schema-index-summary.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
