"""Before baseline, add nonempty-year coverage while retaining v1 evidence."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql


def main():
    directory = ROOT / "eval/datasets/d3"
    source = directory / "aw_schema_link.dev.jsonl"
    output = directory / "aw_schema_link.dev.v2.jsonl"
    if output.exists():
        raise RuntimeError("v2 already exists; do not silently overwrite the reviewed label revision")
    settings = get_settings()
    catalog = load_catalog(ROOT / "data/catalog/adventureworks.yaml")
    changed = {"aw-12", "aw-14", "aw-18", "aw-20"}
    records = []
    evidence = ROOT / "eval/artifacts/d3/a/gold/dev-v2"
    evidence.mkdir(parents=True, exist_ok=True)
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        item["dataset_version"] = "d3-aw-v2-prebaseline"
        item["ai_review"]["pass_2"] = "pending"
        if item["id"] in changed:
            item["question"] = item["question"].replace("2013", "2024")
            item["gold_sql"] = item["gold_sql"].replace("2013-", "2024-").replace("2014-", "2025-")
            item["semantic_rationale"] = item["semantic_rationale"].replace("2013", "2024")
            item["ai_review"]["pass_1_reason"] = item["semantic_rationale"]
            item["label_revision"] = {"prior_version": "aw_schema_link.dev.jsonl", "reason": "扩大非空多表及期间测试覆盖；修订发生在首次系统预测前，非结果刷分。", "human_status": "pending_human_review"}
        checked = validate_sql(item["gold_sql"], catalog)
        if set(checked.tables_used) != set(item["gold_tables"]):
            raise ValueError("Gold table/SQL AST mismatch")
        result = execute_sql(checked.sql, settings.aw_db_url, settings.statement_timeout_ms, 200)
        item["gold_sql"] = checked.sql
        item["gold_result"] = result.rows
        item["gold_columns"] = result.columns
        item["auto_review"]["executed_at"] = datetime.now(timezone.utc).isoformat()
        (evidence / (item["id"]+".json")).write_text(json.dumps({"id":item["id"], "sql":checked.sql, "columns":result.columns, "rows":result.rows, "tables":checked.tables_used}, ensure_ascii=False, indent=2), encoding="utf-8")
        records.append(item)
    output.write_text("".join(json.dumps(item, ensure_ascii=False)+"\n" for item in records), encoding="utf-8")
    # Existing protected labels are copied byte-for-byte; their contents are
    # not printed, transformed, or supplied to a model by this script.
    combined = directory / "aw_schema_link.v2.jsonl"
    combined.write_bytes(output.read_bytes()+(directory / "aw_schema_link.holdout.jsonl").read_bytes())
    manifest = {"version": "d3-aw-v2-prebaseline", "created_at":datetime.now(timezone.utc).isoformat(),
                "dataset": "eval/datasets/d3/aw_schema_link.v2.jsonl", "development": "eval/datasets/d3/aw_schema_link.dev.v2.jsonl",
                "dev_count":21, "holdout_count":9, "total_count":30,
                "changed_dev_ids":sorted(changed), "retained_empty_period_boundary": "aw-11",
                "old_version_preserved":True, "holdout_labels_unchanged_sha256":hashlib.sha256((directory / "aw_schema_link.holdout.jsonl").read_bytes()).hexdigest(),
                "development_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
                "combined_sha256":hashlib.sha256(combined.read_bytes()).hexdigest(),
                "holdout_predictions":0, "gold_review":"pending_human_review",
                "revision_reason":"扩大非空多表测试覆盖，非结果刷分，尚未基线"}
    (directory / "aw_schema_link_v2_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
