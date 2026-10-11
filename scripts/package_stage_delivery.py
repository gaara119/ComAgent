"""Create a portable stage ZIP from an explicit file manifest and verify it.

Large installed models/venvs and all private .env files are excluded. Paths
remain relative to the project root. Each archive is immutable and includes
content hashes; extraction is checked in a fresh workspace directory.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import zipfile
from html.parser import HTMLParser
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings


def banned(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return (any(part in {".git", ".venv", "__pycache__", ".pytest_cache", ".runtime"} for part in relative.parts)
            or path.name.startswith(".env") and path.name != ".env.example"
            or relative.as_posix().startswith(("data/models/", "data/indexes/"))
            or path.suffix in {".pyc", ".pyo"})


def build(manifest_path: Path, output: Path, verification: Path):
    if output.exists() or verification.exists():
        raise ValueError("交付文件或验证记录已存在；请使用新版本文件名。")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = set()
    for name in manifest["include"]:
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or not path.exists():
            raise ValueError(f"交付来源无效：{name}")
        paths.update(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else paths.add(path)
    excluded = manifest.get("exclude_prefixes", [])
    paths = sorted(p for p in paths if not banned(p)
                   and not any(p.relative_to(ROOT).as_posix().startswith(prefix) for prefix in excluded))
    settings = get_settings()
    secrets = {settings.llm_api_key, settings.db_url, settings.aw_db_url,
               os.getenv("POSTGRES_PASSWORD", ""), os.getenv("DB_READER_PASSWORD", ""),
               os.getenv("AW_POSTGRES_PASSWORD", ""), os.getenv("AW_READER_PASSWORD", "")}
    for url in [settings.db_url, settings.aw_db_url]:
        if url:
            secrets.add(urlsplit(url).password or "")
    needles = [value.encode() for value in secrets if len(value) >= 8]
    hashes, unsafe = {}, []
    for path in paths:
        raw = path.read_bytes()
        name = path.relative_to(ROOT).as_posix()
        if any(secret in raw for secret in needles) or re.search(rb"\bsk-[A-Za-z0-9_-]{20,}", raw):
            unsafe.append(name)
        hashes[name] = sha256(raw).hexdigest()
    if unsafe:
        raise ValueError("交付安全扫描失败，含凭据的文件：" + ", ".join(unsafe))
    verification.parent.mkdir(parents=True, exist_ok=True)
    record = {"stage": manifest["stage"], "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "archive_name": output.name, "file_count": len(paths), "sha256": hashes,
              "entry_document": manifest["entry_document"], "credentials_scan": "PASS"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr("交付说明.txt", "解压整个ZIP后再打开以下验收报告：\n" + manifest["entry_document"]
                        + "\n证据使用相对路径；源码、测试、原始日志与截图在同一目录结构内。\n"
                        + "真实.env、模型权重与虚拟环境不在附件中。请按README配置本地环境。\n")
        archive.writestr("delivery-manifest.json", json.dumps(record, ensure_ascii=False, indent=2))
    extraction = ROOT / ".runtime" / ("delivery-check-" + manifest["stage"] + "-" + output.stem)
    if extraction.exists():
        raise ValueError("验证解压目录已存在，不能覆盖。")
    extraction.mkdir(parents=True)
    with zipfile.ZipFile(output) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise ValueError("ZIP CRC校验失败：" + corrupt)
        for info in archive.infolist():
            target = (extraction / info.filename).resolve()
            if not target.is_relative_to(extraction.resolve()):
                raise ValueError("ZIP路径越界。")
        archive.extractall(extraction)
    mismatches = [name for name, expected in hashes.items()
                  if sha256((extraction / name).read_bytes()).hexdigest() != expected]
    entry = extraction / manifest["entry_document"]
    if mismatches or not entry.is_file():
        raise ValueError("解压验证失败：" + ", ".join(mismatches))
    record.update(archive_sha256=sha256(output.read_bytes()).hexdigest(), archive_bytes=output.stat().st_size,
                  extraction_hash_check="PASS", crc_check="PASS", entry_document_exists=True)
    class Links(HTMLParser):
        def __init__(self):
            super().__init__()
            self.targets = []
        def handle_starttag(self, tag, attrs):
            if tag in {"a", "img"}:
                self.targets.extend(value for key, value in attrs if key in {"href", "src"} and value)
    checked, missing_links = 0, []
    for report in [entry, entry.with_suffix(".md")]:
        if not report.exists():
            continue
        content = report.read_text(encoding="utf-8")
        if report.suffix == ".html":
            parser = Links()
            parser.feed(content)
            targets = parser.targets
        else:
            targets = re.findall(r"\]\(([^)]+)\)", content)
        for target in targets:
            target = target.strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("#"):
                continue
            local = (report.parent / unquote(parsed.path)).resolve()
            checked += 1
            if not local.is_relative_to(extraction.resolve()) or not local.exists():
                missing_links.append(target)
    if missing_links:
        raise ValueError("解压后验收报告相对证据链接缺失：" + ", ".join(missing_links))
    record.update(entry_relative_links_checked=checked, missing_entry_links=[], relative_links_check="PASS")
    verification.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: record[key] for key in ["stage", "file_count", "archive_name", "archive_bytes",
                                                  "archive_sha256", "credentials_scan", "extraction_hash_check"]}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()
    build(args.manifest, args.output, args.verification)


if __name__ == "__main__":
    main()
