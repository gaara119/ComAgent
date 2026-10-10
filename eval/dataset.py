"""Dataset provenance, manual review integrity, and holdout safety."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "eval/datasets/nl2sql_chinook.jsonl"


def load_dataset(path: Path = DEFAULT_DATASET) -> list[dict[str, Any]]:
    items = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("题库有重复 id")
    groups: dict[str, str] = {}
    for item in items:
        if item["split"] not in {"dev", "holdout"}:
            raise ValueError(f"{item['id']} 的 split 无效")
        family = item["family_id"]
        if family in groups and groups[family] != item["split"]:
            raise ValueError(f"同源题 {family} 被拆分到开发集和保留集")
        groups[family] = item["split"]
    return items


def review_hash(item: dict[str, Any]) -> str:
    material = {key: item.get(key) for key in (
        "id", "question", "gold_sql", "gold_result", "gold_columns", "column_types",
        "monetary_columns", "ordered", "split", "family_id", "source_sha256")}
    data = json.dumps(material, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def reviewed(item: dict[str, Any]) -> bool:
    review = item.get("gold_review", {})
    return (review.get("status") == "accepted" and bool(review.get("reviewer"))
            and review.get("content_sha256") == review_hash(item))


def require_run_permission(items: list[dict[str, Any]], *, split: str = "dev", draft_gold: bool = False,
                           allow_holdout: bool = False, frozen_tag: str | None = None) -> list[dict[str, Any]]:
    if split == "holdout" and (not allow_holdout or not frozen_tag):
        raise ValueError("保留集禁止默认评测；需要 --allow-holdout 和实际冻结 Git tag --frozen-tag")
    if draft_gold and split != "dev":
        raise ValueError("草稿 gold 只能在开发集探索，不能运行保留集")
    selected = [item for item in items if item["split"] == split]
    if not selected:
        raise ValueError(f"题库中没有 {split} 题")
    if not draft_gold:
        pending = [item["id"] for item in selected if not reviewed(item)]
        if pending:
            raise ValueError("gold 尚未人工接受或接受后被更改：" + ", ".join(pending))
    return selected
