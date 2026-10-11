"""Record an actual human alias decision against the exact inspected CSV hash.

This tool never decides approval itself. Pass explicit alias IDs approved by
the named reviewer. Unselected rows retain pending status and are not active.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_value_index import ALIAS_FIELDS


def record_review(path: Path, expected_sha256: str, reviewer: str, approved: list[str],
                  rejected: list[str], audit_path: Path, review_note: str = "") -> dict:
    if audit_path.is_file():
        raise ValueError("审核证据已存在，请指定新的 --audit 文件，不能覆盖。")
    before = path.read_bytes()
    digest = sha256(before).hexdigest()
    if digest != expected_sha256:
        raise ValueError("别名表已变化，必须重新检查当前内容，不能把旧审核套到新版。")
    if not reviewer.strip() or not (approved or rejected):
        raise ValueError("必须提供实际审核人和明确审核的 alias_id。")
    if set(approved) & set(rejected):
        raise ValueError("同一别名不能同时通过与拒绝。")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    by_id = {item["alias_id"]: item for item in rows}
    if len(by_id) != len(rows) or not (set(approved) | set(rejected)).issubset(by_id):
        raise ValueError("alias_id 重复或审核引用了不存在的行。")
    for item in rows:
        if item["alias_id"] in approved or item["alias_id"] in rejected:
            item["review_status"] = "approved" if item["alias_id"] in approved else "rejected"
            item["reviewer"] = reviewer.strip()
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=ALIAS_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    audit = {"recorded_at": datetime.now(timezone.utc).isoformat(), "reviewer": reviewer,
             "review_note": review_note, "input_sha256": digest,
             "output_sha256": sha256(path.read_bytes()).hexdigest(),
             "approved": [by_id[identity] for identity in approved],
             "rejected": [by_id[identity] for identity in rejected],
             "pending_count": sum(item["review_status"] == "pending" for item in rows)}
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aliases", type=Path, default=ROOT / "data/aliases/aliases.csv")
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--approve", action="append", default=[])
    parser.add_argument("--reject", action="append", default=[])
    parser.add_argument("--note", default="")
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    audit = record_review(args.aliases, args.expected_sha256, args.reviewer, args.approve,
                          args.reject, args.audit, args.note)
    print(json.dumps({"approved_count": len(audit["approved"]), "rejected_count": len(audit["rejected"]),
                      "pending_count": audit["pending_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
