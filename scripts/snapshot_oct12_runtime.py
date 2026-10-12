"""Record source/config provenance for local Oct12 service phases without secrets."""
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT / "eval/artifacts/oct12") or output.exists():
        raise SystemExit("Use a fresh Oct12 snapshot path")
    output.mkdir(parents=True)
    paths = sorted({p for folder in ("qa_agent", "api", "ui", "eval") for p in (ROOT / folder).rglob("*")
                    if p.is_file() and (p.suffix == ".py" or (folder == "qa_agent" and p.suffix in {".txt", ".yaml"}))
                    and "__pycache__" not in p.parts and not p.is_relative_to(ROOT / "eval/experiments")
                    and not p.is_relative_to(ROOT / "eval/artifacts") and not p.is_relative_to(ROOT / "eval/reports")})
    hashes = {}
    for path in paths:
        relative = path.relative_to(ROOT)
        raw = path.read_bytes()
        destination = output / "source" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        hashes[relative.as_posix()] = sha256(raw).hexdigest()
    settings = get_settings()
    safe_config = {**settings.public(), "llm_base_url": settings.llm_base_url,
                   "value_index_path": settings.value_index_path.relative_to(ROOT).as_posix(),
                   "rag_index_path": settings.rag_index_path.relative_to(ROOT).as_posix(),
                   "nlu_fuzzy_threshold": settings.nlu_fuzzy_threshold, "nlu_vector_threshold": settings.nlu_vector_threshold}
    index_hashes = {folder: {p.name: sha256(p.read_bytes()).hexdigest() for p in folder.glob("*") if p.is_file()}
                    for folder in ()}  # filled without printing embeddings or raw values
    for label, folder in (("values", settings.value_index_path), ("rag", settings.rag_index_path), ("aw_schema", settings.aw_schema_index_path)):
        index_hashes[label] = {p.name: sha256(p.read_bytes()).hexdigest() for p in folder.glob("*") if p.is_file()}
    record = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "source_sha256": hashes,
              "source_count": len(hashes), "safe_config": safe_config, "index_sha256": index_hashes,
              "api_launcher_pid": (ROOT / ".runtime/d2-api.pid").read_text().strip(),
              "ui_launcher_pid": (ROOT / ".runtime/d2-ui.pid").read_text().strip(),
              "limit": "Local files/config snapshot plus owned-process startup evidence; not remote imported-module attestation.",
              "credentials_included": False}
    (output / "manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"source_count": len(hashes), "snapshot": output.relative_to(ROOT).as_posix()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
