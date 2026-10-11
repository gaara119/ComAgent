"""Apply the user's attested audit to a new revision; preserve old evidence.

Only development questions are exposed in the new review workspace. Original
mixed datasets, original alias drafts and historical human fields stay intact.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.dataset import review_hash
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql
from scripts.build_value_index import ALIAS_FIELDS


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    directory = ROOT / "eval/artifacts/d2-final/review"
    directory.mkdir(parents=True, exist_ok=True)
    destination = ROOT / "data/aliases/aliases-d2-reviewed.csv"
    if destination.exists():
        raise ValueError("修正版已存在；不覆盖审核和标签历史。")
    report_path = ROOT / "eval/reports/d2-ai-preaudit/aliases-review.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    original = ROOT / "data/aliases/aliases.csv"
    if digest(original) != report["input_sha256"]["data/aliases/aliases.csv"]:
        raise ValueError("当前草稿与用户确认的预审材料摘要不同，不能套用。")
    by_id = {row["id"]: row for row in report["rows"]}
    with original.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    status_map = {"建议直接使用": "approved", "仅作为条件候选": "approved_candidate", "证据不足": "pending"}
    for row in rows:
        row["review_status"] = status_map[by_id[row["alias_id"]]["alias_disposition"]]
        row["reviewer"] = "user-attested-D2-audit" if row["review_status"] != "pending" else ""
    with destination.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=ALIAS_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    settings, catalog = get_settings(), load_catalog(get_settings().catalog_path)
    sql_review = json.loads((ROOT / "eval/reports/d2-ai-preaudit/sql-review.json").read_text(encoding="utf-8"))
    reference_status = {row["id"]: row["reference_status"] for row in sql_review["rows"]}
    results, changes, files, holdout = [], [], [], 0
    for source_name in ["nl2sql_chinook_d2.jsonl", "robust.jsonl"]:
        source = ROOT / "eval/datasets" / source_name
        selected = []
        for line in source.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["split"] != "dev":
                holdout += 1
                continue
            before = {key: item[key] for key in ["question", "gold_sql"]}
            if item["id"] == "sql-38":
                item["gold_sql"] = item["gold_sql"].replace("bytes DESC,", "bytes DESC NULLS LAST,")
            if item["id"] == "robust-23":
                item["question"] = "全部曲目的平均长度是几毫秒？"
            changed = before != {key: item[key] for key in before}
            query = validate_sql(item["gold_sql"], catalog).sql
            actual = execute_sql(query, settings.db_url, settings.statement_timeout_ms, settings.max_rows)
            if actual.truncated:
                raise ValueError("gold 返回被截断，不能作为完整标签。")
            item["gold_result"] = actual.table
            item["gold_columns"] = actual.columns
            item["revision"] = "d2-user-audit-fix-v1"
            item["original_dataset"] = source.relative_to(ROOT).as_posix()
            item["original_dataset_sha256"] = digest(source)
            item["audit_attestation"] = {
                "type": "user_statement", "statement": "我们审计了和你的这个意见一样",
                "original_ai_status": reference_status[item["id"]],
                "acceptance_scope": "原版本AI通过项；新版条件修正仍待最终检查" if changed else "原版本参考答案AI通过项"}
            item["gold_review"] = {"status": "needs_human_review" if changed else "accepted",
                                    "reviewer": None if changed else "user-attested-D2-audit",
                                    "content_sha256": review_hash(item)}
            selected.append(item)
            results.append({"id": item["id"], "sql": query, "result": actual.table,
                            "columns": actual.columns, "read_only": True, "timeout_ms": settings.statement_timeout_ms})
            if changed:
                changes.append({"id": item["id"], "before": before,
                                "after": {key: item[key] for key in before}, "human_review": "pending"})
        output = directory / ("sql-dev-v1.jsonl" if source_name.startswith("nl2sql") else "robust-dev-v1.jsonl")
        output.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in selected), encoding="utf-8")
        files.append({"path": output.relative_to(ROOT).as_posix(), "count": len(selected), "sha256": digest(output)})
    (directory / "gold-readonly-results.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results), encoding="utf-8")
    audit = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(), "attestation_source": "current user message",
             "statement": "我们审计了和你的这个意见一样，你做完这个任务",
             "scope": "用户确认原AI结论；不代填A/B签名；修正版另外等待检查",
             "aliases": {"direct": 54, "candidate_only": 25, "insufficient_disabled": 2,
                         "original_sha256": digest(original), "new_path": destination.relative_to(ROOT).as_posix(),
                         "new_sha256": digest(destination)}, "datasets": files, "changes": changes,
             "sql_robust_holdout_content_skipped": holdout, "holdout_predictions": 0}
    (directory / "user-attestation-and-revisions.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
