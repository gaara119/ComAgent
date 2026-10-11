"""Validate the separate AI report, its attachments and holdout redaction."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = Path(__file__).resolve().parent
REPORT = ROOT / "eval/reports/d2-ai-preaudit/D2统一待审核表-AI预审报告"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(value for name, value in attrs if name == "href")


def main():
    report = json.loads(REPORT.with_suffix(".json").read_text(encoding="utf-8"))
    original = json.loads((ROOT / "eval/reports/d2-acceptance/unified-review.json").read_text(encoding="utf-8"))
    rows = report["rows"]
    original_ids = {row["review_id"] for row in original["rows"]}
    actual_ids = [row["review_id"] for row in rows]
    held = [row for row in rows if row["review_scope"] == "skipped_holdout_not_isolated"]
    no_labels = all(row["subject"] == "保留题内容本轮未审核"
                    and row["actual_status"] == "未运行"
                    and not any(name in row for name in ["expected", "gold_sql", "gold_result", "answer", "actual", "question", "source_qa_id"])
                    for row in held)
    aliases = [row for row in rows if row["group"] == "alias"]
    checks = {
        "all_original_ids_preserved_once": len(actual_ids) == len(set(actual_ids)) == 195 and set(actual_ids) == original_ids,
        "content_reviewed_162_holdout_skipped_33": len(held) == 33 and len(rows) - len(held) == 162,
        "holdout_rows_only_contain_progress_no_labels_or_predictions": no_labels,
        "actual_development_rows_77": sum(row["split"] == "dev" for row in rows) == 77,
        "no_new_human_signatures_or_approval_fields": all(not any(key in row for key in ["reviewer_A", "reviewer_B", "reviewed_at", "approved", "review_status"]) for row in rows),
        "every_reviewed_row_has_reference_actual_reasons_and_evidence": all(
            row.get("reference_status") and row.get("actual_status") and row.get("reason") and row.get("evidence")
            for row in rows if row["split"] != "holdout"),
        "original_files_preserved": report["preservation"]["status"] == "PASS",
        "all_81_aliases_have_four_way_usage_disposition": len(aliases) == 81 and all(row.get("alias_disposition") in {
            "建议直接使用", "仅作为条件候选", "建议拒绝", "证据不足"} for row in aliases),
    }
    parser = Links()
    parser.feed(REPORT.with_suffix(".html").read_text(encoding="utf-8"))
    missing = []
    local = 0
    for target in parser.links:
        parsed = urlparse(target)
        if parsed.scheme or not parsed.path:
            continue
        local += 1
        if not (REPORT.parent / unquote(parsed.path)).resolve().exists():
            missing.append(target)
    checks["all_local_relative_evidence_links_exist"] = not missing
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
              "local_relative_links_checked": local, "missing_links": missing,
              "group_counts": dict(Counter(row["group"] for row in rows))}
    (ARTIFACTS / "report-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
