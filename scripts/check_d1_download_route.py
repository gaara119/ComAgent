"""Probe pinned hf-mirror URLs with bounded reads; do not redownload the corpus."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
REVISION = "7f833e3eda9a571a9ea545a8f6d476fa1685033d"


def main() -> None:
    checks = []
    with httpx.Client(follow_redirects=True, timeout=15) as client:
        for name in ("qas_v2.json", "pdfs.zip"):
            url = f"https://hf-mirror.com/datasets/opendatalab/OHR-Bench/resolve/{REVISION}/{name}"
            record = {"file": name, "requested_url": url, "read_limit_bytes": 8}
            try:
                with client.stream("GET", url, headers={"Range": "bytes=0-7"}) as response:
                    prefix = next(response.iter_bytes(chunk_size=8), b"")
                    record.update(http_status=response.status_code,
                                  content_range=response.headers.get("content-range"),
                                  bytes_read=len(prefix),
                                  zip_magic_matches=prefix.startswith(b"PK") if name.endswith(".zip") else None)
                    record["exact_range_succeeded"] = (
                        response.status_code == 206 and len(prefix) == 8
                        and (response.headers.get("content-range") or "").startswith("bytes 0-7/")
                    )
            except httpx.HTTPError as exc:
                # No credentials are used and transport exception text is not saved.
                record.update(error_type=type(exc).__name__, exact_range_succeeded=False)
            checks.append(record)
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "method": "GET Range bytes=0-7 with streaming read capped at eight bytes",
              "checks": checks, "corpus_redownloaded": False,
              "actual_corpus_provenance": "data/docs/source_manifest.json",
              "scope": "Current mirror route probe only; does not rewrite historical download provenance."}
    target = ROOT / "eval/reports/d1-acceptance/requested-download-route.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
