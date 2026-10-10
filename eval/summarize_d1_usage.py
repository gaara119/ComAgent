"""Summarize saved real D1 benchmark traces; never send a model request."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "eval/reports/d1-acceptance"
TOKEN_KEYS = ("prompt_tokens", "completion_tokens", "total_tokens",
              "prompt_cache_hit_tokens", "prompt_cache_miss_tokens")


def summarize(directory: Path, expected_count: int) -> dict:
    path = directory / "responses.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf8").splitlines() if line.strip()]
    if len(rows) != expected_count:
        raise ValueError(f"Incomplete benchmark in {directory.name}: {len(rows)}/{expected_count}")
    calls = [step for row in rows for step in (row.get("response") or {}).get("steps", [])
             if step.get("name") == "llm"]
    with_usage = [step for step in calls if isinstance(step.get("output_summary", {}).get("usage"), dict)]
    latency = sorted(row["latency_ms"] for row in rows)
    return {
        "questions": len(rows), "llm_attempts": len(calls), "llm_calls_with_usage": len(with_usage),
        "token_totals": {key: sum((step["output_summary"]["usage"].get(key) or 0) for step in with_usage)
                         for key in TOKEN_KEYS},
        "mean_latency_ms": statistics.mean(latency), "median_latency_ms": statistics.median(latency),
        "p95_nearest_rank_ms": latency[math.ceil(len(latency) * .95) - 1],
        "min_latency_ms": min(latency), "max_latency_ms": max(latency),
        "actual_models": sorted({step["output_summary"]["model"] for step in with_usage
                                 if step["output_summary"].get("model")}),
        "responses_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "report": directory.relative_to(ROOT).as_posix(),
    }


def main() -> None:
    sql = summarize(REPORTS / "sql-dev", 21)
    rag = summarize(REPORTS / "rag-dev", 14)
    record = {
        "scope": "These two saved development runs only; excludes previous drafts, probes, UI demos and boundary tests",
        "sql": sql, "rag": rag,
        "combined": {"questions": 35, "holdout_predictions": 0,
                     "llm_attempts": sql["llm_attempts"] + rag["llm_attempts"],
                     "llm_calls_with_usage": sql["llm_calls_with_usage"] + rag["llm_calls_with_usage"],
                     "token_totals": {key: sql["token_totals"][key] + rag["token_totals"][key] for key in TOKEN_KEYS}},
        "calculated_from_saved_traces_only": True, "additional_model_requests": 0,
    }
    (REPORTS / "model-usage.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
