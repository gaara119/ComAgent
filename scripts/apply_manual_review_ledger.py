"""Apply explicitly submitted human decisions to a new immutable ledger.

Historical review files and actual model responses remain unchanged. This
records the user's submitted choices; it does not turn insufficient evidence
or conditional candidate approval into unconditional acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHOICES = {"通过": "accepted", "有条件通过": "accepted_with_conditions",
           "拒绝/发现错误": "rejected", "证据不足": "insufficient_evidence",
           "历史归档，不启用": "archived"}


def merge_decisions(original: dict, submitted: dict, authorization: dict) -> dict:
    indexed = {r["review_key"]: r for r in original["rows"]}
    received = {r["key"]: r for r in submitted["rows"]}
    if len(indexed) != len(original["rows"]) or len(received) != len(submitted["rows"]):
        raise ValueError("Duplicate review IDs")
    if set(indexed) != set(received):
        raise ValueError("Submitted review IDs differ from original")
    if not authorization.get("explicit_application_requested"):
        raise ValueError("Explicit application authorization is required")
    rows = []
    for key, source in indexed.items():
        human = received[key]
        if human["hash"] != source["content_sha256"]:
            raise ValueError("Stale review hash: " + key)
        versions = {v["content_sha256"] for v in source.get("system_versions", [])}
        objects = {o["object"] for o in source.get("decision_objects", [])}
        expected = {(o,) for o in objects}
        expected |= {(v,) for v in versions}
        expected |= {(v["content_sha256"], d) for v in source.get("system_versions", [])
                     for d in v.get("review_dimensions", []) if d != "整体回答"}
        actual, decisions = set(), []
        for choice in human["decisions"]:
            attrs = choice["attrs"]
            if not choice.get("explicit_selected") or choice["choice"] not in CHOICES:
                raise ValueError("Missing or unknown decision: " + key)
            if "data-version" in attrs:
                version = attrs["data-version"]
                if version not in versions:
                    raise ValueError("Unknown actual response version: " + key)
                slot = (version, attrs["data-version-object"]) if "data-version-object" in attrs else (version,)
                kind = "actual_citation_dimension" if len(slot) == 2 else "actual_response_version"
            elif attrs.get("data-object") in objects:
                slot, kind = (attrs["data-object"],), "reference_or_review_object"
            else:
                raise ValueError("Unknown decision object: " + key)
            if slot in actual or slot not in expected:
                raise ValueError("Duplicate or unexpected decision slot: " + key)
            actual.add(slot)
            decisions.append({"scope": kind, "attrs": attrs, "human_choice": choice["choice"],
                              "resolution": CHOICES[choice["choice"]]})
        if actual != expected:
            raise ValueError("Missing decision slots: " + key)
        fields = human["fields"]
        if any(not str(fields.get(k, "")).strip() for k in ("question", "label", "notes")):
            raise ValueError("Missing required submitted field: " + key)
        rows.append({"review_key": key, "original_ids": source["original_ids"], "group": source["group"],
                     "submitted_source_content_sha256": human["hash"],
                     "application_status": "decisions_formally_recorded", "decisions": decisions,
                     "submitted_fields": fields,
                     "previous_question_or_description": source["title"],
                     "source_material_locations": [{"path": v["source"], "id": v["original_id"]}
                                                   for v in source.get("source_materials", [])],
                     "actual_version_locations": [{"content_sha256": v["content_sha256"],
                                                   "evidence": v.get("evidence", [])}
                                                  for v in source.get("system_versions", [])],
                     "human_signatures": None, "human_confirmation_date": None})
    total = sum(len(r["decisions"]) for r in rows)
    return {"version": "manual-applied-20261013-v1", "authorization": authorization,
            "summary": {"rows": len(rows), "decision_slots": total, "unprocessed_decisions": 0,
                        "group_counts": dict(Counter(r["group"] for r in rows)),
                        "choice_counts": dict(Counter(d["human_choice"] for r in rows for d in r["decisions"])),
                        "historical_actual_responses_changed": 0, "manual_signatures_fabricated": False,
                        "human_confirmation_dates_fabricated": False},
            "rows": rows}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, default=ROOT / "eval/reports/oct12/manual-review/全部待人工审核统一入口.json")
    p.add_argument("--submitted", type=Path, default=ROOT / "eval/artifacts/d4/review-input/submitted-review-extracted.json")
    p.add_argument("--authorization", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Choose a new ledger path; historical decisions cannot be overwritten")
    result = merge_decisions(json.loads(args.original.read_text("utf-8")),
                             json.loads(args.submitted.read_text("utf-8")),
                             json.loads(args.authorization.read_text("utf-8")))
    result.update(applied_at_utc=datetime.now(timezone.utc).isoformat(),
                  original_review_sha256=sha256(args.original.read_bytes()).hexdigest(),
                  submitted_review_sha256=sha256(args.submitted.read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    rows = []
    for r in result["rows"]:
        e = html.escape
        decisions = "；".join(e(str(d["attrs"])) + "：" + e(d["human_choice"]) for d in r["decisions"])
        rows.append(f'<details><summary>{e(r["review_key"])} · {e(r["group"])}</summary>'
                    f'<p><strong>正式题面／说明：</strong>{e(r["submitted_fields"]["question"])}</p>'
                    f'<p><strong>正式标签：</strong>{e(r["submitted_fields"]["label"])}</p>'
                    f'<p><strong>逐对象决定：</strong>{decisions}</p>'
                    f'<pre>{e(r["submitted_fields"].get("gold_sql", ""))}</pre>'
                    f'<details><summary>原提交备注（保留历史草稿措辞）</summary><pre>{e(r["submitted_fields"]["notes"])}</pre></details></details>')
    document = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>735项审核正式处理记录</title>'
                '<style>body{max-width:1100px;margin:35px auto;padding:0 20px;font:16px/1.7 "Microsoft YaHei",sans-serif}details{border:1px solid #d5dfea;margin:10px 0;padding:10px}summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}</style>'
                '<h1>735项审核正式处理记录</h1><p>按用户提交及本次明确应用授权登记。条件通过保留限制，证据不足与拒绝不自动启用；历史回答及成绩不追改。实际题库、目录和索引的版本化应用清单见同目录验收报告。</p>'
                + ''.join(rows) + '</html>')
    args.output.with_suffix(".html").write_text(document, "utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
