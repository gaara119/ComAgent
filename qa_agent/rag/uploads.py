"""Local document imports using the existing parsers and incremental RAG index.

Original source files are never replaced. Publication is serialized; a failed
build never changes the live manifest/index. Backups remain for local recovery.
"""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import csv
from dataclasses import replace
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import shutil
from threading import Lock
import time
from uuid import uuid4
from zipfile import ZipFile, BadZipFile
from filelock import FileLock, Timeout

from qa_agent.config import PROJECT_ROOT, get_settings

MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_JSON_BYTES = 12 * 1024 * 1024
MAX_TEXT_CHARS = 120000
_POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="document-import")
_QUEUE = Lock()
_PENDING: set[str] = set()
_FIELDS = ["doc_id", "title", "format", "path", "content_hash", "source_url",
           "license", "language", "domain", "entity_ref", "ingestion_status"]


class ImportError(ValueError):
    def __init__(self, message, status_code=422):
        super().__init__(message)
        self.status_code = status_code


def prepare_file(filename: str, content_base64: str) -> tuple[bytes, str]:
    suffix = Path(filename.replace("\\", "/")).suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt", ".md", ".markdown"}:
        raise ImportError("支持 PDF、Word（.docx）、TXT 和 Markdown 文件。")
    if len(content_base64) > ((MAX_FILE_BYTES + 2) // 3) * 4:
        raise ImportError("单个文件不能超过 8 MB。", 413)
    try:
        raw = base64.b64decode(content_base64, validate=True)
    except ValueError:
        raise ImportError("文件编码无效，请重新选择文件。") from None
    if not raw or len(raw) > MAX_FILE_BYTES:
        raise ImportError("文件为空或超过 8 MB。", 413)
    if suffix in {".txt", ".md", ".markdown"}:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ImportError("TXT / Markdown 请保存为 UTF-8 编码后上传。") from None
        if not text.strip() or "\x00" in text:
            raise ImportError("文件没有有效的文字内容。")
        return text.encode("utf-8"), "md"
    if suffix == ".pdf":
        from pypdf import PdfReader
        try:
            if not raw.startswith(b"%PDF-"):
                raise ValueError()
            reader = PdfReader(io.BytesIO(raw))
            if reader.is_encrypted or not 1 <= len(reader.pages) <= 100:
                raise ValueError()
        except Exception:
            raise ImportError("PDF 无效、已加密或超过 100 页，请拆分或解密后上传。") from None
        return raw, "pdf"
    try:
        with ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            if ("word/document.xml" not in archive.namelist() or len(entries) > 2000
                    or sum(item.file_size for item in entries) > 32 * 1024 * 1024
                    or any(item.flag_bits & 1 for item in entries)):
                raise ValueError()
    except (BadZipFile, ValueError):
        raise ImportError("Word 文件无效、已加密或解压规模过大，请转换为普通 DOCX。") from None
    return raw, "docx"


def _job_root(root: Path) -> Path:
    return root / ".runtime/document-imports"


def _write_job(directory: Path, value: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    temp = directory / "job.tmp"
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    # A Windows reader/virus scanner can briefly hold the destination open.
    # Retry publication rather than incorrectly turning a successful import
    # into a failure simply because the browser polled the receipt concurrently.
    for attempt in range(20):
        try:
            temp.replace(directory / "job.json")
            break
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(.02)


def get_job(job_id: str, *, root: Path = PROJECT_ROOT) -> dict:
    import re
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise ImportError("导入任务不存在。", 404)
    path = _job_root(root) / job_id / "job.json"
    if not path.is_file():
        raise ImportError("导入任务不存在。", 404)
    value = json.loads(path.read_text(encoding="utf-8"))
    # A server restart does not pretend a queued/running task has completed.
    if value["status"] in {"queued", "indexing"} and value.get("process_id") != os.getpid():
        value.update(status="interrupted", message="服务已重启，此导入未确认完成，请检查文档列表后重试。")
    return {key: item for key, item in value.items() if key != "process_id"}


def submit_import(title: str, raw: bytes, fmt: str, *, settings=None, root: Path = PROJECT_ROOT) -> dict:
    title = title.strip()
    if not title or len(title) > 200:
        raise ImportError("请填写 1–200 字符的资料标题。")
    settings = settings or get_settings()
    with _QUEUE:
        if len(_PENDING) >= 4:
            raise ImportError("已有多份资料正在导入，请稍后再试。", 429)
        job_id = uuid4().hex
        _PENDING.add(job_id)
        directory = _job_root(root) / job_id
        value = {"job_id": job_id, "status": "queued", "title": title,
                 "message": "等待解析与建立检索索引。", "process_id": os.getpid()}
        try:
            _write_job(directory, value)
            _POOL.submit(_worker, job_id, title, raw, fmt, settings, root)
        except Exception:
            _PENDING.discard(job_id)
            raise
    return {key: item for key, item in value.items() if key != "process_id"}


def _worker(job_id, title, raw, fmt, settings, root):
    directory = _job_root(root) / job_id
    value = {"job_id": job_id, "status": "indexing", "title": title,
             "message": "正在解析、切片并建立本地检索索引。", "process_id": os.getpid()}
    try:
        _write_job(directory, value)
        document = import_document(title, raw, fmt, settings=settings, root=root, job_id=job_id)
        value.update(status="ready", message="资料已进入知识库，可以选择该文档提问。", document=document)
    except Exception as exc:
        import traceback
        (directory / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        value.update(status="failed", message=str(exc) if isinstance(exc, ImportError) else
                     "导入失败，原知识库未替换。请检查文件及本地解析/向量模型配置。",
                     error_type=type(exc).__name__)
    finally:
        try:
            _write_job(directory, value)
        finally:
            with _QUEUE:
                _PENDING.discard(job_id)


def import_document(title: str, raw: bytes, fmt: str, *, settings, root: Path = PROJECT_ROOT,
                    job_id: str | None = None) -> dict:
    """Build a candidate first; preserve live sources, corpus and failed receipts."""
    from qa_agent.rag.index import build_index, load_index
    from qa_agent.documents import load_documents, verify_document_hash
    root = root.resolve()
    manifest = settings.rag_manifest_path.resolve()
    index = settings.rag_index_path.resolve()
    if (not manifest.is_relative_to(root / "data") or not index.is_relative_to(root / "data")
            or manifest.is_relative_to(index)):
        raise ImportError("当前知识库路径不在项目 data 目录中，不能通过页面修改。", 409)
    job_id = job_id or uuid4().hex
    directory = _job_root(root) / job_id
    directory.mkdir(parents=True, exist_ok=True)
    lock = _job_root(root) / "publish.lock"
    # OS-backed locks are released when the process exits. A leftover file
    # after a crash must not permanently disable future imports.
    publication_lock = FileLock(lock)
    try:
        publication_lock.acquire(timeout=0)
    except Timeout:
        raise ImportError("另一份资料正在更新知识库，请完成后重试。", 409) from None
    source = root / "data/docs/uploads" / f"user-{job_id}.{fmt}"
    published = False
    try:
        old_manifest = manifest.read_bytes() if manifest.is_file() else None
        old_index_exists = index.is_dir()
        previous = None
        if old_index_exists and any(index.iterdir()):
            try:
                previous_chunks, previous = load_index(settings=settings)
            except Exception:
                raise ImportError("当前知识库索引未通过完整性核验，请先恢复索引后再添加资料。", 409) from None
        rows, fields = [], list(_FIELDS)
        if old_manifest is not None:
            # Reject changed/missing sources before publishing any additions.
            for document in load_documents(manifest, project_root=root):
                verify_document_hash(document)
                if document["content_hash"] == sha256(raw).hexdigest():
                    raise ImportError("相同内容的文档已经登记，请直接在文档范围中选择。", 409)
            reader = csv.DictReader(io.StringIO(old_manifest.decode("utf-8-sig")))
            fields = list(dict.fromkeys([*(reader.fieldnames or []), *_FIELDS]))
            rows = list(reader)
            (directory / "manifest.before.csv").write_bytes(old_manifest)
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(raw)
        row = {"doc_id": f"user-{job_id}", "title": title, "format": fmt,
               "path": source.relative_to(root).as_posix(), "content_hash": sha256(raw).hexdigest(),
               "source_url": "", "license": "用户添加；未声明公开传播许可", "language": "unknown",
               "domain": "user_upload", "entity_ref": "", "ingestion_status": "prepared"}
        if "relative_path" in fields:
            row["relative_path"] = row["path"]
        if "content_sha256" in fields:
            row["content_sha256"] = row["content_hash"]
        candidate_manifest = directory / "manifest.candidate.csv"
        with candidate_manifest.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows([*rows, row])
        # Docker deployments mount data and .runtime as independent volumes.
        # Directory rename is atomic only within one filesystem, so candidate
        # indexes and the previous-index backup must share the live index's
        # parent. Receipts and manifest snapshots remain in the job directory.
        index.parent.mkdir(parents=True, exist_ok=True)
        index_staging = index.parent / f".{index.name}.import-{job_id}"
        index_staging.mkdir()
        candidate_index = index_staging / "index.candidate"
        candidate_settings = replace(settings, rag_manifest_path=candidate_manifest, rag_index_path=candidate_index)
        # Append to a verified corpus without reparsing/re-embedding its original
        # pages. Shipped indexes can predate incremental fingerprints; rebuilding
        # them here makes a tiny upload encode thousands of unrelated chunks.
        if previous:
            added_manifest = directory / "manifest.added.csv"
            with added_manifest.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerow(row)
            added_settings = replace(candidate_settings, rag_manifest_path=added_manifest)
            metadata = build_index(added_manifest, candidate_index, settings=added_settings)
            added_chunks, _ = load_index(candidate_index, settings=added_settings)
            old_dense = previous.get("dense_embedding", {})
            new_dense = metadata.get("dense_embedding", {})
            if bool(old_dense.get("enabled")) != bool(new_dense.get("enabled")):
                raise ImportError("新增资料的向量配置与原索引不一致，已取消更新。", 409)
            if old_dense.get("enabled"):
                for key in ("model_sha256", "model_revision", "max_length", "pooling", "normalization"):
                    if not old_dense.get(key) or old_dense.get(key) != new_dense.get(key):
                        raise ImportError("新增资料与原索引的编码模型或参数不同，已取消更新。", 409)
                for key in ("files", "model_id", "mode"):
                    if key in old_dense and old_dense[key] != new_dense.get(key):
                        raise ImportError("新增资料的编码器或分词器与原索引不同，已取消更新。", 409)
                import numpy as np
                vectors = np.concatenate((np.load(index / "embeddings.npy", allow_pickle=False),
                                          np.load(candidate_index / "embeddings.npy", allow_pickle=False)))
                np.save(candidate_index / "embeddings.npy", vectors, allow_pickle=False)
                new_dense["vectors_sha256"] = sha256((candidate_index / "embeddings.npy").read_bytes()).hexdigest()
                # A merged legacy corpus has no single whole-corpus signature.
                new_dense.pop("embedding_signature", None)
            all_chunks = [*previous_chunks, *added_chunks]
            chunk_bytes = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in all_chunks).encode("utf-8")
            (candidate_index / "chunks.jsonl").write_bytes(chunk_bytes)
            metadata.update(documents=[*previous["documents"], *metadata["documents"]],
                            failed_documents=previous.get("failed_documents", []),
                            chunk_count=len(all_chunks), chunks_sha256=sha256(chunk_bytes).hexdigest(),
                            manifest_hash=sha256(candidate_manifest.read_bytes()).hexdigest())
            metadata["incremental"].update(reused_document_count=len(previous["documents"]),
                reused_chunk_count=len(previous_chunks),
                reused_vector_count=len(previous_chunks) if old_dense.get("enabled") else 0)
            metadata["chunking"]["incomplete_chunk_count"] = sum(
                bool(c.get("incomplete_sentence_start") or c.get("incomplete_sentence_end")) for c in all_chunks)
            (candidate_index / "index_meta.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            metadata = build_index(candidate_manifest, candidate_index, settings=candidate_settings)
        summary = next((doc for doc in metadata["documents"] if doc["doc_id"] == row["doc_id"]), None)
        if not summary or not summary.get("chunk_count"):
            raise ImportError("资料未提取到可检索文字；扫描 PDF 需要可用的本地 OCR 模型。")
        # Do not publish a candidate that silently drops any previously indexed document.
        if previous:
            old_ids = {doc["doc_id"] for doc in previous.get("documents", [])}
            if not old_ids.issubset({doc["doc_id"] for doc in metadata["documents"]}):
                raise ImportError("新索引未保留已有文档，已取消更新。", 409)
            old_dense = previous.get("dense_embedding", {})
            new_dense = metadata.get("dense_embedding", {})
            if old_dense.get("enabled") and (not new_dense.get("enabled") or
                    old_dense.get("model_sha256") != new_dense.get("model_sha256")):
                raise ImportError("新增资料不能降级或切换原向量模型，已取消更新。", 409)
        backup_index = index_staging / "index.before"
        if (manifest.read_bytes() if manifest.is_file() else None) != old_manifest:
            raise ImportError("导入期间文档清单已被其他进程修改，已取消发布，请重试。", 409)
        # Validate the combined corpus, vector shape and all source hashes
        # before touching either of the live paths.
        load_index(candidate_index, settings=candidate_settings)
        try:
            if old_index_exists:
                index.rename(backup_index)
            index.parent.mkdir(parents=True, exist_ok=True)
            candidate_index.rename(index)
            manifest.parent.mkdir(parents=True, exist_ok=True)
            temporary = manifest.with_name(manifest.name + ".upload.tmp")
            temporary.write_bytes(candidate_manifest.read_bytes())
            temporary.replace(manifest)
        except Exception:
            if index.is_dir() and (backup_index.is_dir() or not old_index_exists):
                shutil.rmtree(index)
            if backup_index.is_dir():
                backup_index.rename(index)
            if old_manifest is not None:
                manifest.write_bytes(old_manifest)
            elif manifest.is_file():
                manifest.unlink()
            raise
        published = True
        from qa_agent.rag.retrieval_cache import clear_retrieval_cache
        clear_retrieval_cache()
        return {key: row[key] for key in ("doc_id", "title", "format", "content_hash")} | {
            "ready": True, "chunk_count": summary["chunk_count"], "page_count": summary.get("page_count")}
    finally:
        if not published and source.is_file():
            source.unlink()
        publication_lock.release()
