"""Run only materially affected, formally reviewed special DEV scenarios.

Reuses the existing run_case/controller without the historical 60-case freeze
CLI. Gold, review attachments and labels never enter API request payloads.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RUNTIME = ROOT / "eval/experiments/after_d2_01_03/runtime_eval"
sys.path.insert(0, str(RUNTIME))
from common import safe, write_new
from runner import run_case
from scorer import semantic_check
from eval.dataset import reviewed
from eval.metrics import compare_plan_results, compare_results
from qa_agent.sql.catalog import load_catalog

SOURCE = "eval/datasets/manual-applied-20261013-v3/special-dev.jsonl"
SELECTED = {
    "sp01-09", "sp01-10", "sp01-14", "sp01-25", "sp01-27", "sp01-29", "sp01-30",
    "sp03-01", "sp03-03", "sp03-04", "sp03-05", "sp03-06", "sp03-07", "sp03-08",
    "sp03-13", "sp03-15", "sp03-17", "sp03-19", "sp03-20", "sp03-21", "sp03-22",
    "sp03-23", "sp03-24", "sp03-25", "sp03-26", "sp03-27", "sp03-28", "sp03-29", "sp03-30",
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def typed_options(reference, gold):
    evidence = reference.get("gold_verification_evidence")
    raw = json.loads((ROOT / evidence).read_text(encoding="utf-8")) if evidence else {}
    names = gold["columns"]
    types = raw.get("postgres_column_types", [])
    numeric = [index for index, kind in enumerate(types) if kind in {"int2", "int4", "int8", "numeric", "float4", "float8"}]
    integers = [index for index, kind in enumerate(types) if kind in {"int2", "int4", "int8"}]
    if not types:
        numeric = [index for index, kind in enumerate(reference.get("column_types", [])) if kind == "number"]
        integers = reference.get("integer_columns", [])
    from sqlglot import parse_one
    ordered = bool(parse_one(reference["gold_sql"], read="postgres").args.get("order"))
    return dict(ordered=ordered, expected_columns=names, numeric_columns=numeric,
                round_numeric_columns=[index for index in numeric if index not in integers],
                monetary_columns=reference.get("monetary_columns", []))


def query_score(reference, response, catalog):
    gold = reference.get("gold_result")
    if not reference.get("gold_sql") or not isinstance(gold, dict):
        return {"executed": bool(response), "matched": False, "reason": "No SQL gold at this stage", "semantic_check": None}
    if response.get("status") not in {"SUCCEEDED", "EMPTY_RESULT"} or response.get("table") is None:
        return {"executed": bool(response), "matched": False, "reason": "No successful SQL result", "status": response.get("status"),
                "error": response.get("error"), "semantic_check": semantic_check(reference["gold_sql"], response, gold)}
    options = typed_options(reference, gold)
    options["actual_columns"] = response.get("metadata", {}).get("result_columns")
    strict = compare_results(gold["table"], response["table"], **options)
    comparison = compare_plan_results(gold["table"], response["table"], actual_sql=response.get("sql"), catalog=catalog, **options)
    return {"executed": True, "matched": comparison.matched, "comparison": comparison.as_dict(),
            "legacy_comparison": strict.as_dict(), "semantic_check": semantic_check(reference["gold_sql"], response, gold)}


def candidate_score(case, response):
    candidates = []
    intent = response.get("intent") or {}
    for unresolved in intent.get("unresolved") or []:
        candidates.extend(unresolved.get("candidates") or [])
        for option in unresolved.get("options") or []:
            patch = option.get("patch") or {}
            if patch.get("op") == "resolve_value":
                candidates.append({"column": patch.get("column"), "value": patch.get("value")})
    nlu = response.get("metadata", {}).get("nlu") or {}
    for ambiguous in nlu.get("ambiguous") or [mention for mention in nlu.get("mentions", []) if mention.get("status") == "ambiguous"]:
        candidates.extend(ambiguous.get("candidates") or [])
    for issue in (response.get("clarification") or {}).get("issues") or []:
        for option in issue.get("options") or []:
            patch = option.get("patch") or {}
            if patch.get("op") == "resolve_value":
                candidates.append({"column": patch.get("column"), "value": patch.get("value")})
    retained = {(value.get("column"), value.get("standard_value", value.get("canonical_value", value.get("value")))) for value in candidates}
    expected = {(value["column"], value["value"]) for value in case["expected_candidates"]}
    bindings = intent.get("filters") or []
    return {"matched": response.get("status") == "NEEDS_CLARIFICATION" and not bindings and expected <= retained,
            "expected_candidates": sorted(expected), "retained_candidates": sorted(retained), "actual_bindings": bindings}


def score_case(case, state, catalog):
    turns = state.get("turns", [])
    initial = next((turn["response"] for turn in turns if turn["phase"] == "initial"), {})
    final = next((turn["response"] for turn in reversed(turns) if turn["phase"] in {"initial", "clarification"}), {})
    expected_level = case["category"] if case["task"] == "03" else None
    clarify = initial.get("metadata", {}).get("clarify") or initial.get("metadata", {}).get("clarification") or {}
    actual_level = clarify.get("level") or initial.get("metadata", {}).get("level")
    level_correct = actual_level == expected_level if expected_level else None
    initial_status_correct = initial.get("status") == "NEEDS_CLARIFICATION" if expected_level == "L2" else initial.get("status") in {"SUCCEEDED", "EMPTY_RESULT"} if expected_level else None
    candidates = candidate_score(case, initial) if case.get("expected_candidates") else None
    query = query_score(case, final, catalog) if case.get("gold_sql") else None
    expected_posts = (case.get("controller") or {}).get("post_completion_turns", [])
    actual_posts = [turn for turn in turns if turn["phase"] == "post_completion"]
    posts = []
    for index, post in enumerate(expected_posts):
        response = actual_posts[index]["response"] if index < len(actual_posts) else {}
        posts.append({"index": index, "message": post["message"], **query_score(post, response, catalog)})
    complete = bool(state.get("outcome") in {"finished", "candidate_only_clarification"}
                    and (candidates["matched"] if candidates is not None else query and query["matched"])
                    and all(post["matched"] for post in posts)
                    and (level_correct is not False) and (initial_status_correct is not False))
    assumptions = initial.get("intent", {}).get("assumptions") or clarify.get("assumptions")
    return {"id": case["id"], "task": case["task"], "category": case["category"], "turn_count": len(turns),
            "initial_status": initial.get("status"), "observed_initial_level": actual_level,
            "initial_level_correct": level_correct, "initial_status_correct": initial_status_correct,
            "declared_default_observed": bool(assumptions) if expected_level == "L1" else None,
            "outcome": state.get("outcome"), "candidate_contract": candidates, "query": query,
            "post_completion": posts, "whole_dialogue_success": complete,
            "controller_events": state.get("controller_events", [])}


def archive_referenced_providers(state, output):
    references = []
    allowed = (ROOT / "eval/artifacts/manual-applied-20261013-v1").resolve()
    for turn in state.get("turns", []):
        response = turn["response"]
        for step in response.get("steps") or []:
            reference = (step.get("output_summary") or {}).get("provider_capture")
            if not reference:
                continue
            path = (ROOT / reference).resolve()
            if not path.is_relative_to(allowed) or not path.is_file():
                references.append({"reference": reference, "status": "referenced_only; outside this run authorized evidence root"})
                continue
            value = json.loads(path.read_text(encoding="utf-8"))
            if value.get("trace_id") != response.get("trace_id"):
                raise ValueError("Provider trace does not match actual response")
            target = output / "provider" / path.name
            if not target.exists():
                write_new(target, safe(value))
            references.append({"reference": reference, "sha256": digest(path), "copy": target.relative_to(ROOT).as_posix(), "status": "archived"})
    return references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="eval/artifacts/manual-applied-20261013-v1/special-live-001")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=240)
    args = parser.parse_args()
    from urllib.parse import urlparse
    endpoint = urlparse(args.base_url)
    if endpoint.scheme != "http" or endpoint.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("Only existing loopback API")
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError("Use a new project-local evidence directory")
    source = ROOT / SOURCE
    values = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    selected = sorted([value for value in values if value["id"] in SELECTED], key=lambda value: value["id"])
    if len(selected) != len(SELECTED) or any(value.get("split") != "dev" or not value.get("enabled") or not reviewed(value) for value in selected):
        raise ValueError("Only accepted, enabled final v3 DEV cases")
    catalog = load_catalog(ROOT / "data/catalog/chinook.yaml")
    code = [Path(__file__), RUNTIME / "runner.py", RUNTIME / "controller.py", RUNTIME / "scorer.py", ROOT / "eval/metrics.py"]
    hashes = {path.relative_to(ROOT).as_posix(): digest(path) for path in code}
    manifest = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "invocation": list(sys.orig_argv),
                "dataset": SOURCE, "dataset_sha256": digest(source), "selected_ids": [value["id"] for value in selected],
                "selected_count": len(selected), "code_sha256": hashes, "purpose": "Affected formally applied DEV regression; not D5 freeze or holdout score",
                "http_retries": 0, "holdout_predictions": 0, "labels_or_gold_sent_to_api": False,
                "runtime_adaptations": [], "historical_runner_cli_invoked": False}
    write_new(output / "command.json", manifest)
    results, states, providers = [], [], []
    import httpx
    with httpx.Client(timeout=args.timeout, trust_env=False, transport=httpx.HTTPTransport(retries=0)) as client:
        health = client.get(args.base_url + "/health")
        health.raise_for_status()
        write_new(output / "health.json", safe(health.json()))
        for original in selected:
            case = deepcopy(original)
            if case.get("post_completion_turns"):
                case.setdefault("controller", {}).setdefault("post_completion_turns", []).extend(case["post_completion_turns"])
                manifest["runtime_adaptations"].append({"id": case["id"], "change": "existing top-level post_completion_turns copied into runner controller; exact messages and SQL unchanged"})
            write_new(output / "cases" / case["id"] / "reference.json", case)
            state = run_case(client, args.base_url, case, output, "reviewed-dev-v3")
            score = score_case(case, state, catalog)
            write_new(output / "cases" / case["id"] / "current-score.json", score)
            providers.extend(archive_referenced_providers(state, output))
            results.append(score)
            states.append(state)
            print(case["id"], state["outcome"], "dialogue_pass=" + str(score["whole_dialogue_success"]), "turns=" + str(len(state["turns"])), flush=True)
    if digest(source) != manifest["dataset_sha256"] or hashes != {path.relative_to(ROOT).as_posix(): digest(path) for path in code}:
        raise ValueError("Evaluated dataset or harness changed during run")
    query_scores = [score for result in results for score in ([result["query"]] if result["query"] else []) + result["post_completion"]]
    task03 = [row for row in results if row["task"] == "03"]
    candidates = [row for row in results if row["candidate_contract"]]
    summary = {"finished_at_utc": datetime.now(timezone.utc).isoformat(), "scenario_count": len(results),
               "api_request_count": sum(len(state["turns"]) for state in states), "holdout_prediction_count": 0,
               "whole_dialogue_correct": sum(row["whole_dialogue_success"] for row in results),
               "initial_level_correct": sum(row["initial_level_correct"] is True for row in task03), "initial_level_denominator": len(task03),
               "initial_status_correct": sum(row["initial_status_correct"] is True for row in task03),
               "sql_result_correct": sum(score["matched"] for score in query_scores), "sql_result_denominator": len(query_scores),
               "unexecuted_sql_checks": sum(not score["executed"] for score in query_scores),
               "candidate_contract_correct": sum(row["candidate_contract"]["matched"] for row in candidates),
               "candidate_contract_denominator": len(candidates), "outcomes": dict(Counter(row["outcome"] for row in results)),
               "failed_ids": [row["id"] for row in results if not row["whole_dialogue_success"]],
               "semantic_sql_proof": dict(Counter(str((score.get("semantic_check") or {}).get("correct")) for score in query_scores)),
               "semantic_review_note": "Plan EX is result equality, not business semantic proof; unproved alternative ASTs remain explicit review items",
               "runtime_adaptations": manifest["runtime_adaptations"], "provider_records": providers}
    write_new(output / "report.json", {"summary": summary, "cases": results, "manifest": manifest})
    lines = ["# 已正式应用审核后的专项DEV补测", "", f"活动场景 {len(results)}；实际API请求 {summary['api_request_count']}；保留题预测0。",
             f"初轮等级 {summary['initial_level_correct']}/{len(task03)}；整段对话 {summary['whole_dialogue_correct']}/{len(results)}。",
             f"方案EX {summary['sql_result_correct']}/{len(query_scores)}（包含未执行后续，不排除失败）；候选保留 {summary['candidate_contract_correct']}/{len(candidates)}。",
             "结果相等与SQL语义证明分别保存；旧Gold/原结果不改。", "",
             "|编号|初轮期望/实测|状态|整段成功|真实请求数|", "|---|---|---|---|---|"]
    lines.extend(f"|{row['id']}|{row['category']}/{row['observed_initial_level']}|{row['outcome']}|{row['whole_dialogue_success']}|{row['turn_count']}|" for row in results)
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "provider_records"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
