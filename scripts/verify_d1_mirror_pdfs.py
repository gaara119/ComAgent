"""Download the six frozen PDFs via hf-mirror and compare original SHA256s."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from prepare_rag_data import RemoteZip, REVISION, ROOT


def main() -> None:
    manifest = json.loads((ROOT / "data/docs/source_manifest.json").read_text(encoding="utf-8"))
    mirror_url = f"https://hf-mirror.com/datasets/opendatalab/OHR-Bench/resolve/{REVISION}/pdfs.zip"
    remote = RemoteZip(zip_url=mirror_url)
    target_root = (ROOT / "data/raw/ohr/hf-mirror-verified").resolve()
    checks = []
    try:
        entries = {entry["name"]: entry for entry in remote.entries()}
        for source in manifest["downloads"]:
            target = (target_root / source["entry"]).resolve()
            if not target.is_relative_to(target_root):
                raise ValueError("Mirror download must stay in the task cache directory")
            result = remote.extract(entries[source["entry"]], target)
            result["original_sha256"] = source["sha256"]
            result["matches_original_pdf"] = result["sha256"] == source["sha256"]
            checks.append(result)
            if not result["matches_original_pdf"]:
                raise ValueError("Mirror PDF differs from original pinned source")
            print(json.dumps({"entry": source["entry"], "sha256_match": True}, ensure_ascii=False), flush=True)
    finally:
        remote.client.close()
        report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
                  "download_url": mirror_url, "source_revision": REVISION,
                  "status": "PASS" if len(checks) == 6 and all(c["matches_original_pdf"] for c in checks) else "INCOMPLETE",
                  "downloads": checks, "bytes_transferred": remote.transferred,
                  "original_pdf_and_index_changed": False,
                  "qas_v2_route": "Mirror root URL returned 404; retain pinned official GitHub QA source.",
                  "route_probe": "eval/reports/d1-acceptance/requested-download-route.json"}
        (ROOT / "eval/reports/d1-acceptance/requested-mirror-pdfs.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
