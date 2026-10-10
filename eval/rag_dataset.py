"""RAG gold provenance and human acceptance, independent of SQL gold."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "eval/datasets/rag_ohr.jsonl"


def load_dataset(path: Path = DEFAULT_DATASET) -> list[dict[str, Any]]:
    items = [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("RAG gold contains duplicate IDs")
    families: dict[str, str] = {}
    for item in items:
        if item["split"] not in {"dev", "holdout"}:
            raise ValueError("Invalid RAG split")
        family = item["family_id"]
        if family in families and families[family] != item["split"]:
            raise ValueError("The same question family crosses dev and holdout")
        families[family] = item["split"]
        if item["page_numbering"] != "physical_pdf_1_based" or any(page < 1 for page in item["physical_pages"]):
            raise ValueError("RAG physical PDF pages must start at 1")
    return items


def review_hash(item: dict[str, Any]) -> str:
    material = {key: item.get(key) for key in (
        "id", "question", "doc_id", "answer", "reference_text", "physical_pages",
        "page_numbering", "split", "family_id", "source_qa_id", "source_sha256",
        "source_qa_sha256", "evidence_source", "answer_form")}
    content = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf8")
    return hashlib.sha256(content).hexdigest()


def reviewed(item: dict[str, Any]) -> bool:
    review = item.get("gold_review", {})
    return (review.get("status") == "accepted" and bool(review.get("reviewer"))
            and review.get("content_sha256") == review_hash(item))


def require_run_permission(items: list[dict], split: str, draft_gold: bool,
                           allow_holdout: bool = False, frozen_tag: str | None = None) -> list[dict]:
    if split == "holdout" and (not allow_holdout or not frozen_tag):
        raise ValueError("保留题需要显式 --allow-holdout 和冻结 --frozen-tag")
    if draft_gold and split != "dev":
        raise ValueError("--draft-gold 只能运行开发题")
    selected = [item for item in items if item["split"] == split]
    if not selected:
        raise ValueError("RAG selected split is empty")
    pending = [item["id"] for item in selected if not reviewed(item)]
    if pending and not draft_gold:
        raise ValueError("RAG gold 等待人工接受或接受后变更：" + ", ".join(pending))
    return selected


def write_review_table(items: list[dict], directory: Path | None = None) -> Path:
    directory = directory or ROOT / "eval/datasets/rag_review"
    directory.mkdir(parents=True, exist_ok=True)
    lines = ["# D1 RAG 20 道官方 QA 人工审核表", "",
             "题目与答案保留官方英文；引用取自本地原始 PDF 文字层。页码为物理 PDF 页，1 起。",
             "机器核对仅证明引用确实位于该页，不代表答案语义已被人工确认。",
             "请核对题意、答案、原文、页码；实际回答是否完整、是否由引用支持，仍需逐项人工查看。",
             "", "全集 20 题；开发 14 题；保留 6 题。保留题审核允许，D1 模型预测禁止默认运行。",
             "", "开发集覆盖 law/textbook/manual/news/academic 五域；唯一入选 finance 文本题放在保留集。", ""]
    for item in items:
        lines += [f"## {item['id']} · {item['domain']} · {item['split']}", "",
                  f"审核状态：{item['gold_review']['status']}；官方 QA ID：`{item['source_qa_id']}`。",
                  f"文档：**{item['doc_title']}**（`{item['doc_id']}`）；物理页：{item['physical_pages']}。", "",
                  "**问题**：" + item["question"], "", "**标准答案**：" + item["answer"], "",
                  "**PDF 原文**：", "", "```text", item["reference_text"], "```", "",
                  "- [ ] 问题含义明确，标准答案符合原文。",
                  "- [ ] 已打开原 PDF 核对物理页码、版面与引用。",
                  "- [ ] 已记录审核人；正式评测前用审核脚本接受该题。", ""]
    target = directory / "rag_gold_review.md"
    target.write_text("\n".join(lines), encoding="utf8")
    return target
