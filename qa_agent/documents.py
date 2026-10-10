"""Registered PDF documents: canonical paths and actual content hashes."""
from __future__ import annotations

import csv
from hashlib import sha256
from pathlib import Path
import re

from qa_agent.config import PROJECT_ROOT, get_settings


class DocumentError(ValueError):
    pass


def verify_document_hash(document: dict) -> str:
    path = Path(document["resolved_path"])
    digest = sha256(path.read_bytes()).hexdigest()
    if digest != document["content_hash"]:
        raise DocumentError("文档内容与清单哈希不一致，请重新核验资料并建立索引。")
    return digest


def load_documents(manifest_path: Path | None = None,
                   project_root: Path = PROJECT_ROOT) -> list[dict]:
    manifest_path = Path(manifest_path or get_settings().rag_manifest_path)
    project_root = Path(project_root).resolve()
    if not manifest_path.is_file():
        raise DocumentError("文档清单尚未准备，请先运行资料准备脚本。")
    with manifest_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"doc_id", "title", "format", "path", "content_hash"}
        if not required.issubset(reader.fieldnames or ()):
            raise DocumentError("文档清单缺少 doc_id/title/format/path/content_hash 字段。")
        documents = []
        seen = set()
        for raw in reader:
            item = {key: (value or "").strip() for key, value in raw.items() if key is not None}
            doc_id = item["doc_id"]
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", doc_id) or doc_id in seen:
                raise DocumentError("文档 ID 无效或重复。")
            seen.add(doc_id)
            path = Path(item["path"])
            path = (path if path.is_absolute() else project_root / path).resolve()
            if not path.is_relative_to(project_root / "data"):
                raise DocumentError("文档路径必须位于项目 data 目录中。")
            if item["format"].lower() != "pdf" or path.suffix.lower() != ".pdf":
                raise DocumentError("D1 文档入口当前要求原生 PDF。")
            if not path.is_file():
                raise DocumentError("清单中的文档文件不存在，请重新准备资料。")
            if not re.fullmatch(r"[0-9a-fA-F]{64}", item["content_hash"]):
                raise DocumentError("文档清单必须记录实际 SHA256。")
            if not item["title"]:
                raise DocumentError("文档标题不能为空。")
            item["content_hash"] = item["content_hash"].lower()
            item["resolved_path"] = path
            documents.append(item)
    return documents


def get_document(doc_id: str) -> dict:
    for document in load_documents():
        if document["doc_id"] == doc_id:
            verify_document_hash(document)
            return document
    raise KeyError(doc_id)
