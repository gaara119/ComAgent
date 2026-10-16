"""D2 immutable value-index records; only reviewed aliases may enter runtime."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata

import numpy as np


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def pinyin_key(value: str) -> str:
    from pypinyin import Style, lazy_pinyin
    return re.sub(r"[\s\-_'’]+", "", "".join(lazy_pinyin(normalize(value), style=Style.NORMAL)))


def record_id(column: str, standard_value: str) -> str:
    return "v-" + sha256((column + "\0" + standard_value).encode()).hexdigest()[:20]


@dataclass(frozen=True)
class ValueRecord:
    candidate_id: str
    column: str
    standard_value: str
    surface: str
    source: str
    kind: str = "standard"
    alias_id: str | None = None

    @classmethod
    def from_dict(cls, item: dict) -> "ValueRecord":
        return cls(**{key: item[key] for key in cls.__dataclass_fields__ if key in item})

    def as_dict(self) -> dict:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


class ValueIndex:
    def __init__(self, records: list[ValueRecord], embeddings: np.ndarray | None = None,
                 metadata: dict | None = None):
        self.records = records
        self.metadata = metadata or {}
        self.embeddings = embeddings
        self.exact: dict[str, list[int]] = {}
        self.pinyin: dict[str, list[int]] = {}
        self.by_id: dict[str, list[int]] = {}
        for number, record in enumerate(records):
            self.exact.setdefault(normalize(record.surface), []).append(number)
            self.pinyin.setdefault(pinyin_key(record.surface), []).append(number)
            self.by_id.setdefault(record.candidate_id, []).append(number)
        if embeddings is not None:
            if embeddings.ndim != 2 or embeddings.shape[0] != len(records) or not np.isfinite(embeddings).all():
                raise ValueError("值向量与记录的行数或数值不一致。")
            norms = np.linalg.norm(embeddings, axis=1)
            if len(norms) and not np.allclose(norms, 1, atol=1e-3):
                raise ValueError("值向量必须为归一化向量。")

    @classmethod
    def load(cls, path: Path) -> "ValueIndex":
        metadata = json.loads((path / "index_meta.json").read_text(encoding="utf-8"))
        if metadata.get("format_version") != 1 or not metadata.get("complete"):
            raise ValueError("值索引格式不受支持或构建未完成。")
        for name, expected in metadata.get("artifact_sha256", {}).items():
            file_path = (path / name).resolve()
            if not file_path.is_relative_to(path.resolve()) or not file_path.is_file():
                raise ValueError("值索引文件缺失或路径无效。")
            if sha256(file_path.read_bytes()).hexdigest() != expected:
                raise ValueError("值索引文件摘要不一致，请重新构建。")
        records = [ValueRecord.from_dict(json.loads(line)) for line in
                   (path / "records.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        vectors = np.load(path / "embeddings.npy", allow_pickle=False) if (path / "embeddings.npy").is_file() else None
        result = cls(records, vectors, metadata)
        if metadata.get("vector_count") != (0 if vectors is None else len(vectors)):
            raise ValueError("值索引审计的向量行数与实际文件不符。")
        return result


@lru_cache(maxsize=2)
def _cached(path: str, mtime: int) -> ValueIndex:
    return ValueIndex.load(Path(path))


def load_value_index(path: Path) -> ValueIndex | None:
    metadata = path / "index_meta.json"
    return _cached(str(path.resolve()), metadata.stat().st_mtime_ns) if metadata.is_file() else None
