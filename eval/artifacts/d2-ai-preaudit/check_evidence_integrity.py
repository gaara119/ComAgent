"""Check actual accessible evidence for development rows, never holdout content."""
from __future__ import annotations

from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    table = load("eval/reports/d2-acceptance/unified-review.json")
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Integrity checks only; semantic decisions are recorded in individual AI reviews",
              "material_hash_checks": [], "development_record_checks": [], "document_checks": [],
              "review_status_checks": {}, "issues": []}
    for row in table["rows"]:
        if row["split"] == "holdout":
            continue
        for evidence in row["evidence_files"]:
            name = evidence["path"]
            if any(item["path"] == name for item in report["material_hash_checks"]):
                continue
            path = ROOT / name
            actual_hash = digest(path) if path.is_file() else None
            entry = {"path": name, "exists": path.is_file(), "recorded_sha256": evidence.get("sha256"),
                     "actual_sha256": actual_hash, "matches": actual_hash == evidence.get("sha256")}
            report["material_hash_checks"].append(entry)
            if not entry["matches"]:
                report["issues"].append({"object": "evidence_hash", "path": name})
    for group in ["nl2sql", "robust", "rag"]:
        provenance = table["provenance"][group]
        raw_file = provenance["actual_run"]["path"]
        records = [json.loads(line) for line in (ROOT / raw_file).read_text(encoding="utf-8").splitlines() if line.strip()]
        id_counts = Counter(item["id"] for item in records)
        record_map = {item["id"]: (line, item) for line, item in enumerate(records, 1)}
        dataset = {item["id"]: item for item in (json.loads(line) for line in
                   (ROOT / provenance["dataset"]["path"]).read_text(encoding="utf-8").splitlines() if line.strip())
                   if item["split"] == "dev"}
        for row in table["rows"]:
            if row["group"] != group or row["split"] != "dev":
                continue
            pair = record_map.get(row["id"])
            entry = {"review_id": row["review_id"], "raw_output_path": raw_file,
                     "unique_output": id_counts[row["id"]] == 1}
            if pair is None:
                entry["matches"] = False
            else:
                line, record = pair
                response = record.get("response", {})
                core_fields = ["status", "answer", "sql", "table", "rewritten_question", "trace_id"]
                differences = [name for name in core_fields if response.get(name) != row["actual"].get(name)]
                case = dataset.get(row["id"], {})
                question = case.get("question", case.get("q"))
                request = record.get("request", {})
                request_question = request.get("message", request.get("question"))
                entry.update({"line": line, "core_differences": differences,
                    "question_matches_dataset": question == row["title"],
                    "raw_request_question_matches": request_question == row["title"],
                    "response_step_count": len(response.get("steps", [])),
                    "response_trace_id": response.get("trace_id"),
                    "matches": not differences and question == row["title"] and request_question == row["title"]})
            report["development_record_checks"].append(entry)
            if not entry.get("matches") or not entry["unique_output"]:
                report["issues"].append({"object": "actual_output_provenance", "review_id": row["review_id"]})
    with (ROOT / "data/docs/manifest.csv").open(encoding="utf-8-sig", newline="") as source:
        for line, item in enumerate(csv.DictReader(source), 2):
            path = ROOT / item["path"]
            actual_hash = digest(path) if path.is_file() else None
            entry = {"doc_id": item["doc_id"], "manifest_line": line, "path": item["path"],
                     "exists": path.is_file(), "actual_sha256": actual_hash,
                     "recorded_sha256": item["content_hash"], "matches": actual_hash == item["content_hash"]}
            report["document_checks"].append(entry)
            if not entry["matches"]:
                report["issues"].append({"object": "document_hash", "doc_id": item["doc_id"]})
    with (ROOT / "data/aliases/aliases.csv").open(encoding="utf-8-sig", newline="") as source:
        statuses = Counter(row["review_status"] for row in csv.DictReader(source))
    report["review_status_checks"] = {"actual_alias_status_counts": dict(statuses),
        "original_table_nonmetric_status_counts": dict(Counter(row["review"]["status"] for row in table["rows"] if row["group"] != "metric")),
        "original_nonmetric_A_B_or_dates_nonempty": sum(bool(row["review"].get("reviewer_A") or row["review"].get("reviewer_B") or row["review"].get("reviewed_at"))
                                                       for row in table["rows"] if row["group"] != "metric")}
    report["status"] = "PASS" if not report["issues"] else "FINDINGS"
    (OUT / "evidence-integrity.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "material_files": len(report["material_hash_checks"]),
                      "development_outputs": len(report["development_record_checks"]), "documents": len(report["document_checks"]),
                      "review_states": report["review_status_checks"], "issues": report["issues"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
