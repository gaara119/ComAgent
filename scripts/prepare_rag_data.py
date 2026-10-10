"""Fetch a small, pinned OHR-Bench PDF subset with verified HTTP byte ranges.

No ZIP-wide download or server-side execution is involved. Selected PDF entries
are decompressed locally and checked against ZIP CRC32 and the SHA256 manifest.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
import zlib
from pathlib import Path
from urllib.parse import quote

import httpx

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/ohr"
REVISION = "7f833e3eda9a571a9ea545a8f6d476fa1685033d"
ZIP_URL = f"https://huggingface.co/datasets/opendatalab/OHR-Bench/resolve/{REVISION}/pdfs.zip"
ZIP_SIZE = 1516951813
QA_REVISION = "1f421eb428f9f5b8ac0bc8064d6ad1f13fab7af7"
QA_SHA256 = "2446db28741fa9f392067ee7aae7f3b05e0d85c584069a50ddd5b1b5bc783f58"
QA_URL = f"https://raw.githubusercontent.com/opendatalab/OHR-Bench/{QA_REVISION}/data/qas_v2.json"


def fetch_official_qa() -> None:
    qa_path = RAW / "qas_v2.json"
    if not qa_path.exists() or hashlib.sha256(qa_path.read_bytes()).hexdigest() != QA_SHA256:
        response = httpx.get(QA_URL, follow_redirects=True, timeout=120)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest() != QA_SHA256:
            raise ValueError("Official pinned QA SHA256 mismatch")
        qa_path.write_bytes(response.content)
    source = {"github_revision": QA_REVISION, "qa_url": QA_URL,
              "qa_sha256": QA_SHA256, "hf_revision": REVISION}
    (RAW / "qa_source.json").write_text(json.dumps(source, indent=2), encoding="utf8")


class RemoteZip:
    def __init__(self, zip_url: str = ZIP_URL):
        self.zip_url = zip_url
        self.client = httpx.Client(follow_redirects=True, timeout=120)
        self.transferred = 0

    def read_range(self, start: int, length: int) -> bytes:
        # A distinct query prevents intermediaries from reusing another range.
        response = self.client.get(
            self.zip_url + f"?range_start={start}",
            headers={"Range": f"bytes={start}-{start + length - 1}"},
        )
        response.raise_for_status()
        expected = f"bytes {start}-{start + length - 1}/{ZIP_SIZE}"
        if response.status_code != 206 or response.headers.get("content-range") != expected:
            raise ValueError("Upstream did not honor the exact byte range")
        if len(response.content) != length:
            raise ValueError("Truncated HTTP range")
        self.transferred += length
        return response.content

    def entries(self) -> list[dict]:
        tail = self.read_range(ZIP_SIZE - 65536, 65536)
        eocd = tail.rfind(b"PK\x05\x06")
        if eocd < 0:
            raise ValueError("ZIP end-of-central-directory not found")
        values = struct.unpack("<4s4H2LH", tail[eocd:eocd + 22])
        count, directory_size, directory_offset = values[4], values[5], values[6]
        directory = self.read_range(directory_offset, directory_size)
        offset, items = 0, []
        while offset < len(directory):
            header = struct.unpack("<4s6H3L5H2L", directory[offset:offset + 46])
            if header[0] != b"PK\x01\x02":
                raise ValueError("Invalid central directory entry")
            name_len, extra_len, comment_len = header[10:13]
            name = directory[offset + 46:offset + 46 + name_len].decode("utf8")
            items.append({"name": name, "method": header[4], "crc32": header[7],
                          "compressed_size": header[8], "size": header[9],
                          "local_offset": header[16]})
            offset += 46 + name_len + extra_len + comment_len
        if len(items) != count:
            raise ValueError("ZIP entry count mismatch")
        return items

    def extract(self, item: dict, target: Path) -> dict:
        header = self.read_range(item["local_offset"], 30)
        local = struct.unpack("<4s5H3L2H", header)
        if local[0] != b"PK\x03\x04":
            raise ValueError("Invalid ZIP local header")
        data_offset = item["local_offset"] + 30 + local[-2] + local[-1]
        compressed = self.read_range(data_offset, item["compressed_size"])
        if item["method"] == 8:
            data = zlib.decompress(compressed, -15)
        elif item["method"] == 0:
            data = compressed
        else:
            raise ValueError("Unsupported ZIP compression")
        if len(data) != item["size"] or binascii.crc32(data) & 0xFFFFFFFF != item["crc32"]:
            raise ValueError("ZIP size/CRC integrity mismatch")
        if not data.startswith(b"%PDF-"):
            raise ValueError("Entry is not a PDF")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return {"entry": item["name"], "path": target.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
                "zip_crc32": f"{item['crc32']:08x}", "source_url": self.zip_url,
                "source_revision": REVISION}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--doc-name", action="append", default=[])
    parser.add_argument("--selected-d1", action="store_true", help="Fetch the frozen six-document D1 subset")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    if args.selected_d1:
        import sys
        sys.path.insert(0, str(ROOT))
        from eval.rag_build_gold import DOCUMENTS
        args.doc_name.extend(doc_name for _, _, doc_name in DOCUMENTS)
    if args.doc_name:
        fetch_official_qa()
    remote = RemoteZip()
    entries = remote.entries()
    (RAW / "zip_entries.json").write_text(json.dumps(entries, indent=2), encoding="utf8")
    if args.list:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    records = []
    existing_path = RAW / "download_records.json"
    existing = json.loads(existing_path.read_text(encoding="utf8")) if existing_path.exists() else []
    previous = {x["entry"]: x for x in existing}
    for doc_name in args.doc_name:
        matches = [e for e in entries if e["name"].endswith(doc_name + ".pdf")]
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one PDF for {doc_name}; got {len(matches)}")
        pdf_root = (ROOT / "data/docs/raw").resolve()
        target = (pdf_root / (doc_name + ".pdf")).resolve()
        if not target.is_relative_to(pdf_root):
            raise ValueError("Selected PDF path must stay in data/docs/raw")
        saved = previous.get(matches[0]["name"])
        if saved and target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == saved["sha256"]:
            records.append(saved)
            print(f"Verified existing PDF: {doc_name}", flush=True)
            continue
        record = remote.extract(matches[0], target)
        records.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    if records:
        by_entry = {x["entry"]: x for x in existing + records}
        existing_path.write_text(json.dumps(list(by_entry.values()), ensure_ascii=False, indent=2), encoding="utf8")
    print(f"Downloaded byte ranges: {remote.transferred:,}; full ZIP: {ZIP_SIZE:,}")


if __name__ == "__main__":
    main()
