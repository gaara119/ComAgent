"""Read-only integrity audit of the preparation handoff; no DB or model access."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proposal = read_json(BASE / "data/freeze-proposal.json")
    label_file = BASE / proposal["label_file"]
    cases = [json.loads(line) for line in label_file.read_text(encoding="utf-8").splitlines() if line]
    assert sha256(label_file) == proposal["label_sha256"], "Label bytes changed"
    assert sha256(BASE / "materials/source_manifest.json") == proposal["source_manifest_sha256"]
    assert sha256(BASE / proposal["scoring_protocol"]) == proposal["scoring_protocol_sha256"]
    assert len(cases) == 60 and len({c["id"] for c in cases}) == 60
    assert all(c["split"] == "dev" and c["dataset_label"] == "本轮合成开发数据" for c in cases)
    assert all(c["human_review_status"] == "pending_human_review" for c in cases)
    assert all(c["scope"] == {"route": "sql", "db_id": "chinook", "doc_ids": []} for c in cases)
    assert all(c["history"] == [] for c in cases)
    assert sum(bool(c["scorable"]) for c in cases) == proposal["scorable"] == 49
    assert sum(not c["scorable"] for c in cases) == proposal["pending_confirmation"] == 11
    assert len({"".join(c["input"].casefold().split()) for c in cases}) == proposal["unique_inputs"] == 58
    observed_categories = {
        task: dict(Counter(c["category"] for c in cases if c["task"] == task))
        for task in ("01", "03")
    }
    assert observed_categories == proposal["intended_categories"]

    review_index = {
        pass_id: {r["id"]: r for r in read_json(BASE / f"checks/ai-pass-{pass_id}.json")["reviews"]}
        for pass_id in (1, 2)
    }
    for pass_id in (1, 2):
        assert set(review_index[pass_id]) == {c["id"] for c in cases}
    for case in cases:
        assert case["ai_reviews"] == [review_index[1][case["id"]], review_index[2][case["id"]]]
        if case["scorable"]:
            assert case["auto_status"] == "passed" and not case["final_source_guard_issues"]
            assert all(
                review["verdict"] == "pass" and not review["issues"] and all(
                    review[field] in {"pass", "not_applicable"}
                    for field in ("semantic_sql_check", "classification_check", "binding_check", "controller_check")
                ) for review in case["ai_reviews"]
            )

    metadata = read_json(BASE / "data/family-metadata.json")["families"]
    assert {c["id"]: c["family_id"] for c in metadata} == {c["id"]: c["family_id"] for c in cases}
    assert all(c["split"] == "dev" for c in metadata)

    checks = read_json(BASE / "checks/program-normalized-v4.json")["checks"]
    assert {c["id"] for c in checks} == {c["id"] for c in cases}
    sql_checks = [s for check in checks for s in check["sql_checks"]]
    executed = sum(s.get("status") == "executed_readonly" for s in sql_checks)
    assert len(sql_checks) == 77 and executed == 76

    prompt_versions = {sha256(p) for p in (BASE / "prompts").glob("*.txt")}
    attempts = []
    call_count = 0
    for request_file in sorted((BASE / "calls").glob("*/request.json")):
        call_count += 1
        request = read_json(request_file)
        assert request["prompt_sha256"] in prompt_versions, f"Missing actual prompt bytes: {request_file.parent.name}"
        if "system_prompt" in request:
            assert hashlib.sha256(request["system_prompt"].encode("utf-8")).hexdigest() == request["prompt_sha256"]
        provider = read_json(request_file.parent / "provider_attempts.json")
        assert 1 <= len(provider) <= 3, f"Attempt cap violated: {request_file.parent.name}"
        attempts.extend(provider)
    usage = read_json(BASE / "reports/preparation-usage.json")
    actual_tokens = {
        key: sum(a.get("usage", {}).get(key, 0) for a in attempts)
        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
    }
    assert call_count == usage["logical_calls"] == 40
    assert len(attempts) == usage["provider_requests"] == 45
    assert actual_tokens == usage["actual_tokens"]
    assert sum(a["latency_ms"] for a in attempts) == usage["provider_latency_ms_sum"]
    assert Counter(a["model"] for a in attempts) == {"deepseek-flash": 45}

    print(json.dumps({
        "status": "passed", "label_file": proposal["label_file"],
        "label_sha256": proposal["label_sha256"], "candidates": 60,
        "unique_inputs": 58, "scorable": 49, "pending": 11,
        "human_pending": 60, "readonly_sql_checks": len(sql_checks),
        "readonly_sql_executed": executed, "logical_model_calls": call_count,
        "provider_requests": len(attempts), "actual_tokens": actual_tokens,
        "historical_prompt_bytes_available": True, "family_metadata_matches_final": True,
        "network_or_database_access": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
