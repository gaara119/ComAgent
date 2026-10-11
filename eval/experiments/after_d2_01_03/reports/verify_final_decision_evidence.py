"""Offline final-report evidence verification; never imports or calls the QA system."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
EXP = PROJECT / "eval/experiments/after_d2_01_03"
REPORTS = EXP / "reports"
READ_FILES: dict[str, dict] = {}


def read(path: Path) -> bytes:
    data = path.read_bytes()
    READ_FILES[path.relative_to(PROJECT).as_posix()] = {
        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)
    }
    return data


def obj(path: str) -> dict:
    return json.loads(read(EXP / path).decode("utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(read(path)).hexdigest()


def main() -> None:
    docs = {}
    links = []
    for name in ["version-decisions.md", "remaining-feature-gaps.md", "restore-instructions.md",
                 "V2-target-guard-terminology-clarification.md"]:
        f = REPORTS / name
        docs[name] = read(f).decode("utf-8")
        for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", docs[name]):
            if target.startswith(("http", "mailto", "#")):
                continue
            destination = (f.parent / target.split("#")[0]).resolve()
            links.append({"document": f.relative_to(PROJECT).as_posix(), "label": label,
                          "target": target, "exists": destination.exists(),
                          "resolves_within_project": destination.is_relative_to(PROJECT)})

    comparison = obj("runtime_eval/runs/V0-V1-V2-frozen-score-comparison.json")
    scores = {v: obj(f"runtime_eval/runs/{v}-001-scores.json") for v in ["V0", "V1", "V2"]}
    labels_path = EXP / "data/cases-v6-reviewed.jsonl"
    labels = [json.loads(line) for line in read(labels_path).decode("utf-8").splitlines() if line.strip()]
    snapshots = {v: obj(f"runtime_eval/{v}-code-snapshot.json") for v in ["V0", "V1"]}
    final_snapshot = obj("runtime_eval/V1-final-code-snapshot.json")
    file_mismatches = []
    for name, expected in final_snapshot["files"].items():
        # No held-set content is included in this runtime manifest.
        assert not any(term in name.lower() for term in ["holdout", "heldout", "protected_hold"])
        f = PROJECT / name
        if not f.exists() or sha(f) != expected:
            file_mismatches.append(name)
    changed_v1 = sorted(name for name in set(snapshots["V0"]["files"]) | set(snapshots["V1"]["files"])
                        if snapshots["V0"]["files"].get(name) != snapshots["V1"]["files"].get(name))

    cohort = {}
    score_hash_mismatches = []
    comparison_group_mismatches = []
    all_unknowns = {}
    for v, score in scores.items():
        group = score["summary"]["groups"]["all"]
        measurement = score["summary"]
        cohort[v] = {
            "total_tasks": group["total_tasks"], "scorable_tasks": group["scorable_tasks"],
            "pending_annotation": group["pending_annotation"], "confirmed_correct": group["confirmed_correct"],
            "automatic_failed": group["automatic_failed"], "semantic_AI_pending": group["semantic_AI_pending"],
            "api_post_requests": measurement["api_post_requests"],
            "provider_attempts": measurement["provider_attempts_observed_in_api_steps"],
            "tokens": measurement["provider_token_usage_observed"]["total_tokens"],
            "api_ambiguous_delivery_requests": measurement["api_ambiguous_delivery_requests"],
            "prepared_requests_without_response": measurement["prepared_requests_without_response"],
            "task03_automatic": score["summary"]["groups"]["task:03"]["correct_over_scorable_tasks"],
            "l2_complete": score["summary"]["groups"]["task:03"]["metrics"]["clarification_effectiveness"]["positive_over_task_denominator"],
        }
        if comparison["score_sha256"][v] != sha(EXP / f"runtime_eval/runs/{v}-001-scores.json"):
            score_hash_mismatches.append(v)
        if comparison["groups"][v] != score["summary"]["groups"]:
            comparison_group_mismatches.append(v)
        all_unknowns[v] = {
            "pending_annotation": group["pending_annotation"], "semantic_AI_pending": group["semantic_AI_pending"],
            "metric_unresolved": {k: m["unresolved"] for k, m in group["metrics"].items()},
            "fee": measurement["cost"],
        }

    target = obj("runtime_eval/runs/V2-001-target-guard-observations.json")
    target_hash_failures = []
    target_turns = 0
    provider_entries = 0
    for case in target["targets"]:
        for turn in case["turns"]:
            target_turns += 1
            for field in ["request", "response"]:
                f = PROJECT / turn[field]
                if sha(f) != turn[field + "_sha256"]:
                    target_hash_failures.append(turn[field])
            raw = json.loads(read(PROJECT / turn["response"]))
            if "body" in raw:
                raw = json.loads(raw["body"]) if isinstance(raw["body"], str) else raw["body"]
            if raw["status"] != turn["status"] or raw.get("sql") != turn.get("sql"):
                target_hash_failures.append(case["id"] + ":turn-summary")
            for provider in turn["providers"]:
                provider_entries += 1
                for field in ["source", "copy"]:
                    if sha(PROJECT / provider[field]) != provider[field + "_sha256"]:
                        target_hash_failures.append(provider[field])

    prompt_chars = {}
    for part in ["before", "after"]:
        data = read(EXP / f"runtime_eval/version-changes/V1/intent_patch.{part}.txt")
        prompt_chars[part] = {"characters": len(data.decode("utf-8")), "sha256": hashlib.sha256(data).hexdigest()}
    restoration = obj("runtime_eval/version-changes/V2/actual-restore-to-V1.json")
    restart = obj("runtime_eval/V1-final-restart-record.json")
    modules = obj("regression/final/modules-final-V1-001/command.json")
    modules_stdout = read(EXP / "regression/final/modules-final-V1-001/pytest.stdout.txt").decode("utf-8")
    probe = obj("regression/final/ratio-live-001/report.json")
    probe_request = obj("regression/final/ratio-live-001/request.json")
    probe_response = obj("regression/final/ratio-live-001/response.raw.json")
    reviews = {v: obj(f"reports/{v.lower()}-task03-semantic-review.json") for v in ["V1", "V2"]}
    review_statuses = {v: dict(Counter(c["human_review_status"] for c in d["cases"])) for v, d in reviews.items()}
    # Read selected task01 originals cited by the remaining-gaps summary, independently of AI conclusions.
    selected_task01 = {}
    for case_id in ["sp01-04", "sp01-17", "sp01-05", "sp01-18", "sp01-27"]:
        checkpoint = obj(f"runtime_eval/runs/V1-001/cases/{case_id}/checkpoint.json")
        selected_task01[case_id] = [{"status": t["response"]["status"], "sql": t["response"].get("sql"),
                                     "rewritten_question": t["response"].get("rewritten_question")}
                                    for t in checkpoint["turns"]]

    result = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": ".\\.venv\\Scripts\\python.exe -B eval/experiments/after_d2_01_03/reports/verify_final_decision_evidence.py",
        "operation": "offline reads and hashes only; zero API/DB/model calls; no runtime/prompt/labels/human-state mutations",
        "document_links": links, "missing_links": [x for x in links if not x["exists"]],
        "out_of_project_links": [x for x in links if not x["resolves_within_project"]],
        "cohort": cohort, "totals": {
            "POST": sum(v["api_post_requests"] for v in cohort.values()),
            "provider_attempts": sum(v["provider_attempts"] for v in cohort.values()),
            "prediction_tokens": sum(v["tokens"] for v in cohort.values()),
        },
        "immutable": {
            "labels_sha256": sha(labels_path), "label_count": len(labels),
            "human_statuses": dict(Counter(x["human_review_status"] for x in labels)),
            "score_hash_mismatches": score_hash_mismatches,
            "comparison_group_mismatches": comparison_group_mismatches,
            "same_scoring_files": scores["V0"]["scoring_files_sha256"] == scores["V1"]["scoring_files_sha256"] == scores["V2"]["scoring_files_sha256"],
        },
        "all_unknowns_preserved": all_unknowns,
        "V1_prompt_only_changed_files": changed_v1, "V1_prompt_chars": prompt_chars,
        "runtime_files_checked": len(final_snapshot["files"]), "runtime_hash_mismatches": file_mismatches,
        "V1_final_same_manifest": final_snapshot["files"] == snapshots["V1"]["files"],
        "V1_final_same_safe_config": final_snapshot["safe_config"] == snapshots["V1"]["safe_config"],
        "V2_helper_present": (PROJECT / "qa_agent/sql/ratio_guard.py").exists(),
        "V2_active_test_present": (PROJECT / "tests/test_special_v2_ratio_scope.py").exists(),
        "restoration": restoration, "loaded_restart_record": restart,
        "final_modules": {"exit_code": modules["exit_code"], "last_line": modules_stdout.strip().splitlines()[-1],
                          "recorded_source_sha256": modules["source_sha256"]},
        "target_artifacts": {"turns_checked": target_turns, "provider_entries_checked": provider_entries,
                             "hash_or_content_mismatches": target_hash_failures},
        "independent_probe_observation": {"request": probe_request, "status": probe_response["status"],
                                          "sql": probe_response["sql"], "table": probe_response["table"],
                                          "report": probe},
        "task03_ai_reviews_human_status": review_statuses, "selected_task01_originals": selected_task01,
        "materials_read": READ_FILES,
        "boundaries": ["No current HTTP health check or new query was performed; service claim is historical restart evidence.",
                       "ZIP has not been inspected by this audit; packaging/secret/held-content checks belong to the delivery builder.",
                       "D2 Final regression completion is not inferred; report at this audit time treats it separately.",
                       "Auditor implemented D3/V2; this is independent final decision/document cross-check, not a blind implementer-independent code audit."],
    }
    out = REPORTS / "final-decision-evidence-check.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": out.relative_to(PROJECT).as_posix(), "totals": result["totals"],
                      "links": len(links), "missing_links": len(result["missing_links"]),
                      "runtime_files": result["runtime_files_checked"], "runtime_mismatches": len(file_mismatches),
                      "target_turns": target_turns, "target_provider_entries": provider_entries,
                      "target_mismatches": len(target_hash_failures)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
