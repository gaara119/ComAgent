"""Real local BGE-M3 dense embeddings using verified QInt8 ONNX weights."""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
from threading import RLock

import numpy as np

from qa_agent.config import Settings, get_settings


class EmbeddingError(RuntimeError):
    pass


class BGEEmbedder:
    def __init__(self, model_path: Path, max_length: int, batch_size: int):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.root = model_path
        self.max_length = max_length
        self.batch_size = batch_size
        self.lock = RLock()
        self.manifest = json.loads((model_path / "download_manifest.json").read_text(encoding="utf-8"))
        for item in self.manifest["files"]:
            path = (model_path / item["path"]).resolve()
            if not path.is_relative_to(model_path.resolve()) or not path.is_file():
                raise EmbeddingError("BGE 模型文件不完整，请重新运行下载校验脚本。")
            result = sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    result.update(block)
            if result.hexdigest() != item["sha256"]:
                raise EmbeddingError("BGE 模型文件哈希不一致，停止加载。")
        options = ort.SessionOptions()
        options.intra_op_num_threads = min(4, os.cpu_count() or 2)
        options.inter_op_num_threads = 1
        options.enable_mem_pattern = False
        self.session = ort.InferenceSession(str(model_path / "onnx/model_quantized.onnx"),
                                           sess_options=options, providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_file(str(model_path / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=max_length)
        self.tokenizer.enable_padding(pad_id=1, pad_token="<pad>")

    def metadata(self) -> dict:
        return {**self.manifest, "max_length": self.max_length, "batch_size": self.batch_size,
                "providers": self.session.get_providers(), "mode": "bge-m3_onnx_int8",
                "model_id": self.manifest["model"], "model_revision": self.manifest["revision"],
                "model_sha256": next(f["sha256"] for f in self.manifest["files"]
                                     if f["path"] == "onnx/model_quantized.onnx")}

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 1024), dtype=np.float32)
        vectors = []
        with self.lock:
            for start in range(0, len(texts), self.batch_size):
                encoded = self.tokenizer.encode_batch(texts[start:start + self.batch_size])
                values = {
                    "input_ids": np.asarray([item.ids for item in encoded], dtype=np.int64),
                    "attention_mask": np.asarray([item.attention_mask for item in encoded], dtype=np.int64),
                    "token_type_ids": np.asarray([item.type_ids for item in encoded], dtype=np.int64),
                }
                inputs = {item.name: values[item.name] for item in self.session.get_inputs()}
                output = self.session.run(None, inputs)[0]
                dense = output[:, 0, :] if output.ndim == 3 else output
                dense = np.asarray(dense, dtype=np.float32)
                if dense.shape[1] != 1024 or not np.isfinite(dense).all():
                    raise EmbeddingError("BGE 返回的向量维度或数值无效。")
                dense /= np.maximum(np.linalg.norm(dense, axis=1, keepdims=True), 1e-12)
                vectors.append(dense)
                completed = start + len(encoded)
                if len(texts) >= 32 and (completed % 64 == 0 or completed == len(texts)):
                    print(f"BGE encoded {completed}/{len(texts)} chunks", flush=True)
        return np.vstack(vectors)


@lru_cache(maxsize=2)
def _load(path: str, max_length: int, batch_size: int, manifest_mtime: int) -> BGEEmbedder:
    return BGEEmbedder(Path(path), max_length, batch_size)


def get_embedder(settings: Settings | None = None) -> BGEEmbedder | None:
    settings = settings or get_settings()
    manifest_path = settings.bge_model_path / "download_manifest.json"
    if not manifest_path.is_file():
        return None
    if settings.rag_embedding_device != "cpu" or settings.rag_embedding_quantization != "int8":
        raise EmbeddingError("当前 BGE 实现要求 cpu/int8，与本次配置一致。")
    return _load(str(settings.bge_model_path.resolve()), settings.rag_embedding_max_length,
                 settings.rag_embedding_batch_size, manifest_path.stat().st_mtime_ns)
