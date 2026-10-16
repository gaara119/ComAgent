"""Resolve explicitly activated DEV revisions while retaining legacy fallbacks."""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def active_dataset_path(suite: str, fallback: Path, *, root: Path = ROOT) -> Path:
    pointer = root / "eval/datasets/current.json"
    if not pointer.is_file():
        return fallback
    record = json.loads(pointer.read_text("utf-8"))
    if record.get("format_version") != 1 or not record.get("dev_only"):
        raise ValueError("激活题库指针格式无效或未限定开发集")
    entry = record.get("suites", {}).get(suite)
    if entry is None:
        return fallback
    target = (root / entry["path"]).resolve()
    if not target.is_relative_to((root / "eval/datasets").resolve()) or not target.is_file():
        raise ValueError("激活题库文件缺失或路径越界")
    raw = target.read_bytes()
    if sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError("激活题库已更改，须版本化后重新激活")
    if any(json.loads(line).get("split") != "dev" for line in raw.decode("utf-8").splitlines() if line.strip()):
        raise ValueError("激活题库必须仅包含开发题，保留集不能隐式运行")
    return target
