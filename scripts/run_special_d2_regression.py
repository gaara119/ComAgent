"""Run sequential D2 corrected DEV regressions after Special V2 has finished.

Without --execute, this script only verifies fixed DEV views and prints the
exact future commands. It never reads mixed/held datasets, creates predictions,
modifies the evaluator, changes gold, or marks any human review approved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EXP = "eval/experiments/after_d2_01_03"
VIEWS = {
    "sql": {"suite": "nl2sql", "count": 35,
            "dataset": "eval/artifacts/d2-final/review/sql-dev-v1.jsonl",
            "sha256": "7b4c18f203ce0d88f38837f0c788cbcff142b559dc70d3f281990a2d47175f35"},
    "robust": {"suite": "robust", "count": 21,
               "dataset": "eval/artifacts/d2-final/review/robust-dev-v1.jsonl",
               "sha256": "1d6c7732b5196e7146e3b3f01fe4f9ccb24ad354c6b20776631192c605d213f7"},
    "rag": {"suite": "rag", "count": 21,
            "dataset": "eval/artifacts/d2-final/review/rag-dev-view.jsonl",
            "sha256": "12b8cc7de87ea73bc60a2e9b7d527d0721956ef1bf4256ccf6a70331a7f57f63"},
}
EVALUATOR_SOURCES = ["eval/run_eval.py", "eval/dataset.py", "eval/metrics.py",
                     "eval/d2_rag_eval.py", "eval/rag_dataset.py", "eval/rag_metrics.py"]
SCORING_POLICY = {
    "sql_robust": "Original D2 draft-gold result EX: global column mapping, duplicates preserved, declared ordering, continuous numbers 2dp, integer exact; failures/timeout/clarification remain in 35/21 denominators. Not Special exact-Decimal/AST score.",
    "rag": "Original D2 mechanical metrics separate: 20 answerable gold page/snippet Hit@5 and quote diagnostics; 1 unavailable-evidence case; 21 citation/index authenticity checks. Answer-surface matching and citation authenticity do not prove complete answer correctness or semantic faithfulness.",
    "human_review": "Keep pending labels and human answer/citation review pending; draft regression is exploratory, not a formal held score.",
}


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def views() -> dict:
    checked = {}
    for name, spec in VIEWS.items():
        path = ROOT / spec["dataset"]
        actual_sha = sha(path)
        if actual_sha != spec["sha256"]:
            raise ValueError("Corrected immutable DEV view changed: " + spec["dataset"])
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        if (len(rows) != spec["count"] or any(row.get("split") != "dev" for row in rows)
                or len({row["id"] for row in rows}) != len(rows)):
            raise ValueError("Expected unique DEV-only 35/21/21 view: " + spec["dataset"])
        checked[name] = {**spec, "actual_count": len(rows), "actual_sha256": actual_sha,
                         "split": "dev", "human_review_not_changed": True}
    return checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, choices=["V0", "V1", "V2"], help="Actual selected final version label")
    parser.add_argument("--run-id-prefix", required=True, help="Fresh unique ID; each suite appends -sql/-robust/-rag")
    parser.add_argument("--output", required=True, help="Fresh project-relative directory under Special regression/")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--execute", action="store_true", help="Execute the three actual suites sequentially; omit to verify inputs only")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", args.run_id_prefix):
        raise ValueError("Use a simple unique run-id prefix")
    api = urlparse(args.base_url)
    if api.scheme != "http" or api.hostname not in {"127.0.0.1", "localhost", "::1"} or api.username or api.password:
        raise ValueError("This local regression wrapper only targets the existing loopback API")
    if args.timeout <= 0:
        raise ValueError("Timeout must be positive")
    output = (ROOT / args.output).resolve()
    regression_root = (ROOT / EXP / "regression").resolve()
    if not output.is_relative_to(regression_root) or output == regression_root:
        raise ValueError("Use a fresh directory below Special regression/")
    if output.exists():
        raise ValueError("Output already exists; preserve all earlier logs and use a new path")
    checked = views()
    source_before = {name: sha(ROOT / name) for name in EVALUATOR_SOURCES}
    commands = {}
    for group, spec in VIEWS.items():
        run_id = args.run_id_prefix + "-" + group
        group_output = (output / group).relative_to(ROOT).as_posix()
        commands[group] = [sys.executable, "-B", "-m", "eval.run_eval", "--suite", spec["suite"],
                           "--dataset", spec["dataset"], "--split", "dev", "--draft-gold", "--run-id", run_id,
                           "--base-url", args.base_url, "--timeout", str(args.timeout), "--output", group_output]
    manifest = {"purpose": "Sequential actual corrected DEV regressions; no held predictions",
                "version_label": args.version, "created_at_utc": stamp(), "status": "INPUTS_VERIFIED_NOT_RUN",
                "command": [sys.executable, "-B", *sys.argv], "cwd": "system",
                "views": checked, "commands": commands, "evaluator_sources_before": source_before,
                "scoring_policy": SCORING_POLICY, "results": {}, "holdout_prediction_count": 0,
                "human_review_status": "pending_human_review"}
    if not args.execute:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    output.mkdir(parents=True, exist_ok=False)
    manifest["status"] = "RUNNING"
    write(output / "regression-run-manifest.json", manifest)
    for group, command in commands.items():
        command_path = output / (group + "-command.json")
        write(command_path, {"cwd": "system", "command": command, "started_at_utc": stamp(),
                             "dataset": checked[group], "draft_gold": True, "split": "dev"})
        log_path = output / (group + "-stdout-stderr.log")
        with log_path.open("w", encoding="utf-8") as logfile:
            process = subprocess.run(command, cwd=ROOT, stdout=logfile, stderr=subprocess.STDOUT, check=False)
        report_path = output / group / "report.json"
        report = json.loads(report_path.read_text(encoding="utf-8-sig")) if report_path.is_file() else {}
        dataset = report.get("provenance", {}).get("dataset")
        draft_provenance = report.get("provenance", {}).get("gold_review") == "draft"
        complete = (process.returncode == 0 and report.get("status") == "COMPLETED"
                    and report.get("suite") == checked[group]["suite"]
                    and report.get("split") == "dev" and draft_provenance
                    and report.get("selected_count") == checked[group]["count"]
                    and report.get("prediction_count") == checked[group]["count"]
                    and report.get("holdout_prediction_count") == 0
                    and dataset == checked[group]["dataset"]
                    and report.get("provenance", {}).get("dataset_sha256") == checked[group]["sha256"])
        summary_keys = ["status", "suite", "split", "draft_gold", "selected_count", "prediction_count", "holdout_prediction_count",
                        "correct", "exploratory_ex", "failure_categories", "status_counts", "metrics", "gold_pending_ids",
                        "hit_at_5", "exact_gold_quote_hit_at_5", "insufficient_handling", "mechanical_metrics",
                        "gold_human_accepted_count", "answer_human_review_count"]
        manifest["results"][group] = {"returncode": process.returncode, "execution_completed": complete,
                                      "finished_at_utc": stamp(), "original_report": report_path.relative_to(ROOT).as_posix(),
                                      "original_report_sha256": sha(report_path) if report_path.is_file() else None,
                                      "command_file": command_path.relative_to(ROOT).as_posix(),
                                      "command_sha256": sha(command_path), "stdout_stderr": log_path.relative_to(ROOT).as_posix(),
                                      "stdout_stderr_sha256": sha(log_path),
                                      "actual_report_summary_unchanged": {key: report[key] for key in summary_keys if key in report},
                                      "completion_is_not_a_semantic_pass": True}
        manifest["evaluator_sources_after"] = {name: sha(ROOT / name) for name in EVALUATOR_SOURCES}
        manifest["evaluators_unchanged"] = manifest["evaluator_sources_after"] == source_before
        manifest["dev_views_unchanged"] = all(sha(ROOT / item["dataset"]) == item["sha256"] for item in checked.values())
        if not manifest["evaluators_unchanged"] or not manifest["dev_views_unchanged"]:
            manifest["status"] = "FAILED_SOURCE_OR_VIEW_CHANGED"
            write(output / "regression-run-manifest.json", manifest)
            return 2
        write(output / "regression-run-manifest.json", manifest)
        if not complete:
            # Retain the failed suite and do not invent or silently continue future runs.
            manifest["status"] = "INCOMPLETE_ACTUAL_REGRESSION"
            manifest["stopped_after"] = group
            manifest["remaining_not_run"] = [name for name in commands if name not in manifest["results"]]
            write(output / "regression-run-manifest.json", manifest)
            print(json.dumps({"status": manifest["status"], "stopped_after": group,
                              "report": str(report_path), "remaining_not_run": manifest["remaining_not_run"]}, ensure_ascii=False))
            return 2
    manifest["status"] = "COMPLETED_ALL_THREE_ACTUAL_DEV_SUITES"
    manifest["finished_at_utc"] = stamp()
    manifest["actual_prediction_count"] = sum(result["actual_report_summary_unchanged"]["prediction_count"] for result in manifest["results"].values())
    write(output / "regression-run-manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "actual_prediction_count": manifest["actual_prediction_count"],
                      "holdout_prediction_count": 0, "manifest": (output / "regression-run-manifest.json").relative_to(ROOT).as_posix()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print("Regression evidence preparation failed: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
