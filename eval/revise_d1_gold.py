"""Create a separate D1 gold revision without changing original review records.

Only three reviewed development cases change: sql-11 gets SQL-level rounding;
sql-22 and sql-24 explicitly request first_name. No LLM requests are made.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eval.dataset import DEFAULT_DATASET, load_dataset, review_hash
from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql


CHANGES = {
    "sql-11": {
        "gold_sql": "SELECT ROUND(AVG(total), 2) AS average_total FROM invoice;",
        "reason": "原题要求保留两位小数；原 AVG(total) 返回多位小数。修正版在 SQL 层执行 ROUND 并保存真实结果，不依靠评测器金额量化掩盖显示差异。",
    },
    "sql-22": {
        "question": "列出 2004 年 1 月 1 日之前入职的员工编号、名字（仅 first_name，不包含姓氏 last_name）和入职日期，按员工编号升序。",
        "reason": "保留原 gold 的 first_name 投影意图，明确名字的字段含义；不因旧模型额外返回 last_name 而放宽列数比较。",
    },
    "sql-24": {
        "question": "列出邮箱以 @gmail.com 结尾的客户编号、名字（仅 first_name，不包含姓氏 last_name）和邮箱，按客户编号升序。",
        "reason": "保留原 gold 的 first_name 投影意图，明确名字的字段含义；不因旧模型额外返回 last_name 而修改标准结果。",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revise(source: Path, output: Path, manifest_path: Path, *, overwrite: bool = False) -> dict:
    source, output, manifest_path = source.resolve(), output.resolve(), manifest_path.resolve()
    if source in {output, manifest_path} or output == manifest_path:
        raise ValueError("修正版及 manifest 必须与原题集使用不同文件路径。")
    for target in (output, manifest_path):
        if target.exists() and not overwrite:
            raise ValueError("修正版输出已存在；核对后使用 --overwrite 仅替换独立修正版。")
    source_hash = sha256(source)
    original = load_dataset(source)
    if len(original) != 30 or Counter(item["split"] for item in original) != {"dev": 21, "holdout": 9}:
        raise ValueError("修订只适用于原 D1 的 30 题、21 dev / 9 holdout 题集。")
    indexed = {item["id"]: item for item in original}
    if not set(CHANGES) <= indexed.keys() or any(indexed[key]["split"] != "dev" for key in CHANGES):
        raise ValueError("三个修订 ID 必须存在且全部为 dev。")
    settings = get_settings()
    catalog = load_catalog(settings.catalog_path)
    checked_at = datetime.now(timezone.utc).isoformat()
    revised = deepcopy(original)
    revisions = []
    for item in revised:
        if item["id"] in CHANGES:
            change = CHANGES[item["id"]]
            before = {key: deepcopy(item[key]) for key in ("question", "gold_sql", "gold_result", "gold_columns")}
            for key in ("question", "gold_sql"):
                if key in change:
                    item[key] = change[key]
            validated = validate_sql(item["gold_sql"], catalog, max_rows=settings.max_rows)
            result = execute_sql(validated.sql, settings.db_url,
                                 statement_timeout_ms=settings.statement_timeout_ms,
                                 max_rows=settings.max_rows)
            if result.truncated:
                raise ValueError("修订标准结果不能截断。")
            item["gold_columns"], item["gold_result"] = result.columns, result.table
            item["gold_generated_at_utc"] = checked_at
            item["gold_revision"] = {
                "parent_dataset_sha256": source_hash,
                "reason": change["reason"],
                "reviewer_type": "ai",
                "reviewed_at_utc": checked_at,
                "human_accepted": False,
            }
            revisions.append({"id": item["id"], "reason": change["reason"],
                              "before": before,
                              "after": {key: deepcopy(item[key]) for key in before},
                              "executed_gold_sql": validated.sql,
                              "actual_gold_row_count": result.row_count,
                              "truncated": result.truncated,
                              "ai_semantic_review": "accepted",
                              "human_accepted": False})
        # Neither an AI review nor this revision records human acceptance.
        item["gold_review"] = {"status": "needs_human_review", "reviewer": None,
                               "content_sha256": review_hash(item)}
    if sha256(source) != source_hash:
        raise ValueError("修订过程中原题集发生变化，请重新核对。")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in revised), encoding="utf-8")
    manifest = {
        "created_at_utc": checked_at,
        "reviewer_type": "ai",
        "scope": "独立 D1 修正版；仅对开发题修正语义和标准 SQL；全部保持待人工复核。",
        "parent_dataset": str(source),
        "parent_dataset_sha256": source_hash,
        "dataset": str(output),
        "dataset_sha256": sha256(output),
        "split_counts": dict(Counter(item["split"] for item in revised)),
        "source_sha256": sorted({item["source_sha256"] for item in revised}),
        "changed_ids": sorted(CHANGES),
        "unchanged_case_count": 27,
        "changes": revisions,
        "gold_sql_executed_in_this_revision": len(revisions),
        "model_prediction_count": 0,
        "holdout_prediction_count": 0,
        "holdout_items_identical_to_parent": all(
            item == indexed[item["id"]] for item in revised if item["split"] == "holdout"),
        "human_accepted_count": 0,
        "gold_pending_human_review": len(revised),
        "reproduce": "python -m eval.revise_d1_gold",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=ROOT / "eval/datasets/nl2sql_chinook_d1_acceptance.jsonl")
    parser.add_argument("--manifest", type=Path, default=ROOT / "eval/datasets/nl2sql_chinook_d1_acceptance.manifest.json")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        manifest = revise(args.source, args.output, args.manifest, overwrite=args.overwrite)
    except Exception as exc:
        print("D1 gold revision failed: " + sanitize_error(exc, get_settings()), file=sys.stderr)
        return 1
    print("独立修正版已生成：30 题；21 dev / 9 holdout；3 项修订；0 次模型预测；0 项人工接受。")
    print("原题集保持不变；保留题内容保持不变：" + str(manifest["holdout_items_identical_to_parent"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
