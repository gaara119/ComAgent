"""Small shared D4 measurements; raw traces remain the source of each number."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def quantile(values, fraction):
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * fraction
    lower, upper = int(index), min(int(index) + 1, len(values) - 1)
    return round(values[lower] + (values[upper] - values[lower]) * (index - lower), 3)


def p50_p90(values):
    return {"p50_ms": quantile(values, .5), "p90_ms": quantile(values, .9), "n": len(values)}


def trace_cost(envelope):
    durations = Counter()
    tokens = Counter()
    calls = Counter()
    parent = "other"
    models = set()
    for step in envelope.get("steps", []):
        name = step["name"]
        durations[name] += step.get("latency_ms", 0)
        if name != "llm":
            parent = name
            continue
        usage = step.get("output_summary", {}).get("usage", {})
        owner = "schema_selection" if parent in {"schema_link", "schema_prune"} else (
            "sql_generation" if parent == "sql_gen" else "other")
        calls[owner] += 1
        calls["all"] += 1
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            tokens[key] += usage.get(key, 0)
            tokens[f"{owner}_{key}"] += usage.get(key, 0)
        model = step.get("output_summary", {}).get("model")
        if model:
            models.add(model)
    # Current pipeline completes recall's schema_link BEFORE opening the
    # independent schema_prune step. Add these two disjoint stages, but never
    # add their nested llm child durations a second time.
    stages = {"model_calls": durations["llm"],
        "nlu": durations["clarification_gate"], "value_link": durations["value_link"],
        "schema_selection": durations["schema_link"] + durations["schema_prune"],
        "sql_generation": durations["sql_gen"], "sql_execution": durations["sql_exec"],
        "retrieval": durations["retrieve"] or durations["rag_retrieve"],
        "answer_generation": durations["doc_answer"] or durations["answer"] or durations["rag_answer"]}
    return {"raw_step_ms": dict(durations), "stages_ms": stages, "model_attempts": dict(calls),
            "usage": dict(tokens), "actual_models": sorted(models),
            "duration_warning": "嵌套步骤有重叠；端到端实测独立计时，不将所有step相加"}


def summarize(records):
    names = {key for record in records for key in record.get("cost", {}).get("stages_ms", {})}
    tokens = Counter()
    attempts = Counter()
    for record in records:
        tokens.update(record.get("cost", {}).get("usage", {}))
        attempts.update(record.get("cost", {}).get("model_attempts", {}))
    return {"requests": len(records), "correct": sum(record.get("matched", False) for record in records),
        "ex": sum(record.get("matched", False) for record in records) / len(records) if records else None,
        "all_failures_in_denominator": True,
        "legacy_correct": sum(record.get("legacy_matched", False) for record in records),
        "end_to_end": p50_p90([record["elapsed_ms"] for record in records]),
        # A runner exception has no usable trace: never turn that missing
        # measurement into a fabricated zero-latency stage.
        "stages": {name: p50_p90([record["cost"]["stages_ms"][name]
                    for record in records if name in record.get("cost", {}).get("stages_ms", {})])
                    for name in sorted(names)},
        "trace_available_requests": sum("cost" in record for record in records),
        "model_zero_call_requests": sum(record.get("cost", {}).get("model_attempts", {}).get("all", 0) == 0
                                       for record in records if "cost" in record),
        "response_statuses": dict(Counter(record.get("response", {}).get("status", "NO_RESPONSE")
                                           for record in records)),
        "usage_total": dict(tokens), "model_attempts_total": dict(attempts),
        "failures": dict(Counter(record.get("failure_category") for record in records
                    if not record.get("matched", False)))}


def provenance(root: Path, settings, files):
    return {"created_at_utc": datetime.now(timezone.utc).isoformat(),
        "configured_model": settings.llm_model, "configured_llm_base_url": settings.llm_base_url,
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip(),
        "holdout_predictions": 0,
        "source_sha256": {Path(path).relative_to(root).as_posix(): hashlib.sha256(Path(path).read_bytes()).hexdigest()
                          for path in files},
        "credential_capture": False}


def runtime_source_files(root: Path):
    """Hash runtime source and text prompts, without credentials or datasets."""
    return sorted(path for path in (root / "qa_agent").rglob("*")
                  if path.is_file() and path.suffix in {".py", ".txt", ".md"}
                  and "__pycache__" not in path.parts)


def compare_case(case, envelope, catalog, gold):
    from eval.metrics import compare_plan_results, compare_results
    kwargs = {"ordered": case.get("ordered", False), "expected_columns": gold.columns,
        "actual_columns": (envelope.get("metadata") or {}).get("result_columns"),
        "monetary_columns": case.get("monetary_columns", []),
        "numeric_columns": [i for i, kind in enumerate(case.get("column_types", [])) if kind == "number"],
        "temporal_columns": [i for i, kind in enumerate(case.get("column_types", [])) if kind == "temporal"],
        "round_numeric_columns": [i for i, kind in enumerate(case.get("column_types", []))
                                  if kind == "number" and i not in case.get("integer_columns", [])]}
    if envelope.get("status") not in {"SUCCEEDED", "EMPTY_RESULT"} or envelope.get("table") is None:
        return {"matched": False, "legacy_matched": False,
                "failure_category": (envelope.get("error") or {}).get("code") or envelope.get("status", "missing_status")}
    current = compare_plan_results(gold.rows, envelope["table"], actual_sql=envelope.get("sql"), catalog=catalog, **kwargs)
    legacy_kwargs = {key: value for key, value in kwargs.items() if key != "round_numeric_columns"}
    # The historical comparator rounds declared money but keeps other
    # continuous quantities exact. Keep that result alongside plan §5.2 EX.
    legacy = compare_results(gold.rows, envelope["table"], **legacy_kwargs)
    return {"matched": current.matched, "legacy_matched": legacy.matched,
            "comparison": current.as_dict(), "legacy_comparison": legacy.as_dict(),
            "failure_category": None if current.matched else "result_mismatch"}
