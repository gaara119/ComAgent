"""Verify the delivered D2 work without running models or holdout questions."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import httpx

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "D2 completion verification; no model calls or holdout predictions",
              "checks": {}, "details": {}}
    audit = load("eval/reports/d2-acceptance/package-audit.json")
    archive = ROOT.parent / audit["zip"]
    report["checks"]["final_zip_matches_recorded_sha256"] = sha(archive) == audit["zip_sha256"]
    with zipfile.ZipFile(archive) as bundle:
        report["checks"]["zip_crc"] = bundle.testzip() is None
        names = set(bundle.namelist())
        manifest_name = "eval/reports/d2-acceptance/bundle-file-manifest.json"
        manifest = json.loads(bundle.read(manifest_name))
        mismatches = []
        for item in manifest["files"]:
            if item["path"] not in names:
                mismatches.append(item["path"])
                continue
            content = bundle.read(item["path"])
            if len(content) != item["size"] or hashlib.sha256(content).hexdigest() != item["sha256"]:
                mismatches.append(item["path"])
        expected = {item["path"] for item in manifest["files"]} | {manifest_name}
        report["checks"]["all_packaged_files_match_manifest"] = not mismatches and names == expected
        required = ["D2 原清单九项逐项验收与证据.html",
                    "eval/reports/d2-acceptance/unified-review.html",
                    "eval/artifacts/d2/package-check/report.json"]
        report["checks"]["reports_review_table_and_independent_check_packaged"] = all(p in names for p in required)
        excluded = [name for name in names if ".env" in Path(name).parts
                    or any(part in {".venv", ".git", "models"} for part in Path(name).parts)]
        report["checks"]["no_real_env_venv_git_or_model_weights_packaged"] = not excluded
        report["details"]["zip"] = {"sha256": sha(archive), "files": len(names),
                                         "bytes": archive.stat().st_size, "mismatches": mismatches,
                                         "unexpected_sensitive_paths": excluded}
    snapshot = load("eval/artifacts/d2/delivery-code-snapshot.json")
    changed = [name for name, digest in snapshot["file_sha256"].items()
               if not (ROOT / name).is_file() or sha(ROOT / name) != digest]
    report["checks"]["delivered_source_unchanged_since_final_checks"] = not changed
    report["details"]["source"] = {"files": len(snapshot["file_sha256"]), "changed": changed}
    baseline = load("eval/artifacts/d2/preflight-initial.json")
    d1_changed = [name for name, digest in baseline["d1_evidence_hashes"].items()
                  if not (ROOT / name).is_file() or sha(ROOT / name) != digest]
    report["checks"]["d1_evidence_still_unchanged"] = not d1_changed
    report["details"]["d1"] = {"files": len(baseline["d1_evidence_hashes"]), "changed": d1_changed}
    results = load("eval/reports/d2-acceptance/requested-d2-evidence.json")
    report["checks"]["engineering_and_test_records_complete"] = (
        results["engineering"] == {"passed": 58, "total": 58}
        and results["modules"]["passed"] == 281
        and results["ui"]["status"] == "PASSED" and results["ui"]["case_count"] == 5
        and results["sql"]["correct"] == results["sql"]["count"] == 35
        and results["robust"]["correct"] == results["robust"]["count"] == 21)
    module = load(results["modules"]["command_record"])
    log = (ROOT / module["output"]).read_text(encoding="utf-8")
    report["checks"]["final_module_command_success_and_raw_log_present"] = module["exit_code"] == 0 and "281 passed" in log
    review = results["review"]
    report["checks"]["human_review_pending_and_holdouts_unrun"] = (
        review["pending_rows"] == 191 and review["previously_approved_metrics"] == 4
        and review["human_gold_accepted"] == 0
        and review["human_actual_predictions_accepted"] == 0
        and review["holdout_cases"] == 33 and review["holdout_predictions"] == 0)
    report["details"]["review"] = review
    for label, url in [("api", "http://127.0.0.1:8000/health"),
                       ("ui", "http://127.0.0.1:8501/")]:
        try:
            response = httpx.get(url, timeout=5, trust_env=False)
            detail = {"http_status": response.status_code}
            ok = response.status_code == 200
            if label == "api":
                detail["health"] = response.json()
                ok = ok and detail["health"].get("status") == "ok" and detail["health"].get("database_ready") is True
            report["checks"][label + "_currently_running"] = ok
        except (httpx.HTTPError, ValueError) as exc:
            report["checks"][label + "_currently_running"] = False
            detail = {"error_type": type(exc).__name__}
        report["details"][label] = detail
    report["status"] = "PASS" if all(report["checks"].values()) else "PARTIAL"
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
