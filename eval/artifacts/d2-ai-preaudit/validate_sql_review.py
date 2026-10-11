"""Validate new audit reports and locatable original evidence; no model/DB calls."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ART = Path(__file__).resolve().parent
REPORT = ROOT / "eval/reports/d2-ai-preaudit"
REQUIRED = {"review_id", "id", "group", "split", "reference_status", "actual_status", "reason", "actual_reason", "issues", "suggestion", "human_confirmation", "evidence", "evidence_complete"}
STATES = {"AI建议通过", "AI建议有条件通过", "AI发现错误", "证据不足"}

sql = json.loads((REPORT / "sql-review.json").read_text(encoding="utf-8"))
metrics = json.loads((REPORT / "metrics-review.json").read_text(encoding="utf-8"))
verification = [json.loads(s) for s in (ART / "sql-verification.jsonl").read_text(encoding="utf-8").splitlines()]
original = json.loads((ROOT / "eval/reports/d2-acceptance/unified-review.json").read_text(encoding="utf-8"))
expected_ids = {r["review_id"] for r in original["rows"] if r["group"] in {"nl2sql", "robust"} and r["split"] == "dev"}
assert len(sql["rows"]) == 56 and {r["review_id"] for r in sql["rows"]} == expected_ids
assert Counter(r["group"] for r in sql["rows"]) == {"nl2sql": 35, "robust": 21}
assert len(metrics["rows"]) == 4 and {r["review_id"] for r in metrics["rows"]} == {r["review_id"] for r in original["rows"] if r["group"] == "metric"}
checks = []
for row in sql["rows"] + metrics["rows"]:
    assert REQUIRED <= set(row), row["review_id"]
    assert row["reference_status"] in STATES
    assert row["actual_status"] in STATES or row["group"] == "metric" and row["actual_status"] == "不适用（已确认口径依据）"
    assert row["human_fields_modified"] is False
    assert row["evidence"] and isinstance(row["evidence_complete"], bool)
    for ev in row["evidence"]:
        path = ROOT / ev["path"]
        assert path.is_file(), (row["review_id"], ev)
        if "line" in ev:
            lines = path.read_text(encoding="utf-8").splitlines()
            assert 1 <= ev["line"] <= len(lines), (row["review_id"], ev)
            if path.suffix == ".jsonl":
                item = json.loads(lines[ev["line"] - 1])
                if "split" in item:
                    assert item["split"] == "dev", (row["review_id"], ev)
                if ev["path"].endswith("responses.jsonl") or ev["path"].startswith("eval/datasets/"):
                    assert item["id"] == row["id"], (row["review_id"], ev)
    checks.append({"review_id": row["review_id"], "required_fields": True, "evidence_paths_and_lines": True, "human_fields_not_modified": True})
assert len(verification) == 130
assert all(item["status"] == "executed" and item.get("truncated") is not True for item in verification)
assert sum(item.get("matches_stored_values") is True for item in verification) == 112
assert all(item.get("matches_stored_values") is not False for item in verification)
assert verification[0]["rows"] == [["chinook", "qa_reader", "on", "5s"]]
assert [r["review_id"] for r in sql["rows"] if not r["evidence_complete"]] == ["robust:robust-23"]
assert all(item.get("split") in {None, "dev"} for item in verification)

# Verify only hashes, never expose or review holdout question/answer contents.
baseline = json.loads((ART / "protected-inputs-before.json").read_text(encoding="utf-8"))["file_sha256"]
source_paths = {"eval/reports/d2-acceptance/unified-review.json", "eval/datasets/nl2sql_chinook_d2.jsonl", "eval/datasets/robust.jsonl", "eval/artifacts/d2/nl2sql/final/responses.jsonl", "eval/artifacts/d2/robust/final/responses.jsonl", "data/catalog/chinook.yaml", "data/rules/metric_definitions.json", "eval/artifacts/d2/source/metric-human-review.json", "eval/artifacts/d2/source/metric-sql-checks.json"}
for path in source_paths:
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == baseline[path], path
output = {"status": "VALIDATED", "sql_rows": 56, "metrics_rows": 4, "select_queries": 130, "reexecuted_existing_sql_values_match": 112,
          "source_hashes_unchanged": len(source_paths), "skipped_holdout_counts": {"nl2sql": 15, "robust": 9},
          "checks": checks,
          "artifact_hashes": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in
                              (REPORT / "sql-review.json", REPORT / "sql-review.md", REPORT / "metrics-review.json", REPORT / "metrics-review.md", ART / "sql-verification.jsonl", ART / "verify_sql.py")}}
(ART / "sql-review-validation.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({key: value for key, value in output.items() if key not in {"checks", "artifact_hashes"}}, ensure_ascii=False))
