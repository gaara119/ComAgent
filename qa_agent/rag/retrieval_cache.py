"""Bounded, stat-invalidated caches for already verified retrieval artifacts."""
from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache
import os
from pathlib import Path
from threading import RLock

from qa_agent.config import PROJECT_ROOT
from qa_agent.rag.parsers import DocumentError

_LOCK = RLock()
_SNAPSHOTS = OrderedDict()
_SCOPES = OrderedDict()
_QUERIES = OrderedDict()


@lru_cache(maxsize=1)
def _windows_info_api():
    import ctypes
    from ctypes import wintypes
    class BasicInfo(ctypes.Structure):
        _fields_ = [(name, ctypes.c_longlong) for name in
                    ("CreationTime", "LastAccessTime", "LastWriteTime", "ChangeTime")] + [
                    ("FileAttributes", wintypes.DWORD)]
    function = ctypes.WinDLL("kernel32", use_last_error=True).GetFileInformationByHandleEx
    function.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    function.restype = wintypes.BOOL
    return ctypes, BasicInfo, function


def _change_stamp(path, stat):
    if os.name != "nt":
        return stat.st_ctime_ns
    # On Windows st_ctime is creation time, not the change time. In particular,
    # editing then restoring mtime must not reuse a previously verified source.
    # https://learn.microsoft.com/windows/win32/api/winbase/ns-winbase-file_basic_info
    try:
        import msvcrt
        ctypes, BasicInfo, function = _windows_info_api()
        information = BasicInfo()
        with path.open("rb") as stream:
            handle = msvcrt.get_osfhandle(stream.fileno())
            if function(handle, 0, ctypes.byref(information), ctypes.sizeof(information)) and information.ChangeTime > 0:
                return information.ChangeTime
    except (OSError, AttributeError):
        pass
    # Filesystems lacking ChangeTime must rehash rather than silently trust
    # restored timestamps. This path sacrifices speed, not source validation.
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_retrieval_cache():
    with _LOCK:
        _SNAPSHOTS.clear()
        _SCOPES.clear()
        _QUERIES.clear()


def _signature(paths):
    values = []
    for path in paths:
        try:
            stat = path.stat()
            values.append((str(path.absolute()), str(path.resolve()), stat.st_dev, stat.st_ino,
                           stat.st_size, stat.st_mtime_ns, _change_stamp(path, stat)))
        except OSError:
            values.append((str(path.absolute()), "missing"))
    return tuple(values)


def _put(cache, key, value, maximum):
    cache[key] = value
    cache.move_to_end(key)
    while len(cache) > maximum:
        cache.popitem(last=False)


def snapshot(settings, loader):
    from qa_agent.rag import index as index_module
    import numpy as np
    enabled = getattr(settings, "rag_cache_enabled", True)
    target = Path(settings.rag_index_path)
    key = (str(target.resolve()), str(Path(settings.rag_manifest_path).resolve()),
           id(loader), id(index_module.load_documents))
    with _LOCK:
        previous = _SNAPSHOTS.get(key) if enabled else None
        if previous is not None and _signature(previous[0]) == previous[1]:
            _SNAPSHOTS.move_to_end(key)
            return previous[2], previous[3], previous[4], previous[1], True
    # Read source paths through the same validated manifest loader as load_index.
    documents = index_module.load_documents(settings.rag_manifest_path)
    watch = [Path(settings.rag_manifest_path), target / "index_meta.json",
             target / "chunks.jsonl", target / "embeddings.npy"]
    for document in documents:
        watch.append(Path(document["resolved_path"]))
        raw_path = Path(document["path"])
        watch.append(raw_path if raw_path.is_absolute() else PROJECT_ROOT / raw_path)
    before = _signature(watch)
    chunks, metadata = loader(settings=settings)
    matrix = None
    dense = metadata.get("dense_embedding", {})
    if dense.get("enabled"):
        import hashlib
        path = target / "embeddings.npy"
        if hashlib.sha256(path.read_bytes()).hexdigest() != dense.get("vectors_sha256"):
            raise DocumentError("dense 索引文件已修改，请重建索引。", "rag_index_corrupt")
        # Keep a bounded in-memory read-only copy. A long-lived Windows mmap
        # prevents safe replacement/rebuild of the underlying .npy file.
        matrix = np.load(path, allow_pickle=False)
        matrix.flags.writeable = False
        if matrix.ndim != 2 or matrix.shape != (len(chunks), dense.get("dimension")):
            raise DocumentError("dense 向量维度与片段不匹配。", "embedding_invalid")
    after = _signature(watch)
    if before != after:
        raise DocumentError("索引或来源在读取期间变化，请稍后重试。", "rag_index_stale")
    if enabled:
        with _LOCK:
            _put(_SNAPSHOTS, key, (watch, after, chunks, metadata, matrix), 2)
    return chunks, metadata, matrix, after, False


def scoped_corpus(signature, allowed, selected, tokenizer, enabled=True):
    from rank_bm25 import BM25Okapi
    key = (signature, tuple(sorted(allowed)), id(tokenizer))
    with _LOCK:
        value = _SCOPES.get(key) if enabled else None
        if value is not None:
            _SCOPES.move_to_end(key)
            return value[0], value[1], True
    corpus = [tokenizer("\n".join([chunk["doc_title"], *chunk["section_path"], chunk["text"]]))
              for _, chunk in selected]
    value = (corpus, BM25Okapi(corpus, epsilon=.25) if any(corpus) else None)
    if enabled:
        with _LOCK:
            _put(_SCOPES, key, value, 16)
    return value[0], value[1], False


def query_vector(key, encoder, text, enabled=True):
    import numpy as np
    with _LOCK:
        value = _QUERIES.get(key) if enabled else None
        if value is not None:
            _QUERIES.move_to_end(key)
            return value.copy(), True
    value = np.asarray(encoder.encode([text]), dtype=np.float32)
    if enabled:
        with _LOCK:
            _put(_QUERIES, key, value.copy(), 128)
    return value, False
