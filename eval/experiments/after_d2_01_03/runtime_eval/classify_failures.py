"""Offline evidence indexing and failure triage; never predicts, rescoring or changes labels."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from common import HERE, ROOT, digest, json_hash, load_cases, safe, utcnow, write_new

TAXONOMY = {
    "model": "模型理解或输出格式",
    "linking": "值索引、别名或匹配",
    "rules_catalog": "业务目录或规则",
    "session_state": "会话状态、条件更新或依赖失效",
    "sql": "SQL生成、校验或执行",
    "unimplemented": "尚未实现的功能",
    "annotation_scoring": "标注、评分或尚未证明的语义等价",
    "environment": "环境、凭据、预算或服务错误",
}

ERROR_BOUNDARIES = {
    "llm_format": ("model", "Provider output failed the actual JSON/schema contract"),
    "llm_refused": ("model", "Actual provider response refused the requested output"),
    "sql_rejected": ("sql", "Actual generated SQL was rejected by validation"),
    "sql_execution": ("sql", "Actual SQL execution returned an error; underlying cause needs SQLSTATE/DB evidence"),
    "sql_timeout": ("environment", "Actual database timeout boundary was reached"),
    "session_conflict": ("session_state", "Actual session/card/patch validation rejected the turn"),
    "llm_connection": ("environment", "Actual provider connection/timeout error"),
    "llm_auth": ("environment", "Actual provider authentication/permission rejection"),
    "llm_balance": ("environment", "Actual provider account balance rejection"),
    "llm_rate_limit": ("environment", "Actual provider rate-limit rejection"),
    "llm_provider": ("environment", "Actual provider HTTP error; no semantic cause inferred"),
    "llm_attempt_budget": ("environment", "Actual request attempt budget was exhausted"),
    "missing_llm_key": ("environment", "Actual credential configuration check rejected the request"),
    "http_error": ("environment", "Actual API HTTP error; inspect response.raw for server detail"),
    "invalid_api_json": ("environment", "Saved API body is not a valid expected JSON response"),
}


def reference(path: Path, *, pointer: str | None = None) -> dict:
    value = {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
             "exists": path.is_file()}
    if value["exists"]:
        value["sha256"] = digest(path)
    if pointer:
        value["json_pointer"] = pointer
    return value


def nested_path(directory: Path, value: str) -> Path:
    path = (directory / value).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError("Evidence path escapes its saved case/turn directory")
    return path


def turn_evidence(case_dir: Path, turn: dict):
    index = turn["index"]
    turn_dir = case_dir / "turns" / f"{index:03d}"
    raw_path = nested_path(case_dir, turn.get("response_raw_file", f"turns/{index:03d}/response.raw.json"))
    response = turn.get("response") or {}
    integrity = []
    raw = {}
    if raw_path.is_file():
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        if isinstance(raw.get("body"), str) and raw.get("http_status", 500) < 400:
            try:
                parsed = json.loads(raw["body"])
                if isinstance(parsed, dict):
                    if json_hash(parsed) != json_hash(response):
                        integrity.append("Cached parsed response differs from saved raw API body; raw body used for triage")
                    response = parsed
            except json.JSONDecodeError:
                integrity.append("Saved API body is not JSON")
    else:
        integrity.append("Saved raw API response missing; no response evidence can be reconstructed by prediction")
    manifest_path = turn_dir / "provider-evidence.json"
    captures = []
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("records", []):
            capture_ref = {"step": item.get("step"), "status": item.get("status"), "source": item.get("source"),
                           "source_sha256": item.get("source_sha256")}
            if item.get("copy"):
                path = nested_path(turn_dir, item["copy"])
                capture_ref["copy"] = reference(path)
                capture_ref["copy_hash_matches_archive"] = path.is_file() and digest(path) == item.get("copy_sha256")
                if path.is_file():
                    captured = json.loads(path.read_text(encoding="utf-8"))
                    capture_ref.update(trace_id=captured.get("trace_id"), validation_error=captured.get("validation_error"),
                                       provider_error=captured.get("error"), has_request="request" in captured,
                                       has_response="response" in captured,
                                       trace_matches_response=captured.get("trace_id") == response.get("trace_id"))
            captures.append(capture_ref)
    failed_steps = [{"index": step_index, "name": step.get("name"), "status": step.get("status"),
                     "output_summary": safe(step.get("output_summary") or {}), "latency_ms": step.get("latency_ms")}
                    for step_index, step in enumerate(response.get("steps") or []) if step.get("status") == "error"]
    return {"index": index, "phase": turn.get("phase"), "asked_key": turn.get("asked_key"),
            "trace_id": response.get("trace_id"), "status": response.get("status"), "error": safe(response.get("error")),
            "request": reference(turn_dir / "request.json"), "api_response": reference(raw_path),
            "provider_manifest": reference(manifest_path), "provider_records": captures,
            "failed_steps": failed_steps, "intent_version": (response.get("intent") or {}).get("intent_version"),
            "observed_state": (response.get("metadata", {}).get("clarify") or {}).get("state"),
            "actual_sql": response.get("sql"), "actual_table": response.get("table"),
            "transport_error": raw.get("network_error"), "delivery_uncertain": raw.get("delivery_uncertain", False),
            "integrity_notes": integrity, "_response": response}


def classify_case(case: dict, score: dict, checkpoint: dict, evidence: list[dict], score_reference: dict):
    findings = []
    def finding(category, observation, sources, *, certainty="hypothesis", next_check=None):
        item = {"category": category, "category_label": TAXONOMY[category], "certainty": certainty,
                "observation": observation, "evidence": sources, "next_check": next_check,
                "root_cause_confirmed": False}
        # A boundary is evidence of where it failed, never proof of the ultimate semantic cause.
        findings.append(item)

    if not score.get("scorable"):
        finding("annotation_scoring", "Frozen label is pending; actual output must not receive a binary task correctness score",
                [score_reference], certainty="direct_observation", next_check="Review the existing source/AI disputes without changing gold to fit system output")
    if checkpoint.get("outcome") == "ambiguous_delivery":
        finding("environment", "Actual delivery is uncertain; session is not replayed", [reference(Path(checkpoint["_path"]))] if checkpoint.get("_path") else [score_reference],
                certainty="direct_observation", next_check="Inspect saved request/response and server trace; do not retry the old patch/card automatically")
    for item in evidence:
        sources = [item["api_response"], item["provider_manifest"]]
        error = item.get("error") or {}
        code = error.get("code")
        if code in ERROR_BOUNDARIES:
            category, observation = ERROR_BOUNDARIES[code]
            finding(category, observation + f" (error code={code})", sources, certainty="observed_failure_boundary",
                    next_check="Open the corresponding provider record and failed step; separate initiating cause from downstream errors")
        if item.get("transport_error"):
            finding("environment", f"Saved HTTP transport exception: {item['transport_error']}", [item["api_response"]], certainty="observed_failure_boundary")
        for step in item["failed_steps"]:
            name = str(step.get("name") or "")
            category = ("linking" if any(word in name for word in ("value_link", "nlu", "rewrite")) else
                        "rules_catalog" if any(word in name for word in ("catalog", "rule")) else
                        "session_state" if any(word in name for word in ("clarif", "patch", "semantic")) else
                        "sql" if name.startswith("sql") else None)
            if category:
                finding(category, f"Actual step #{step['index']} '{name}' recorded error; this locates a boundary, not the final root cause",
                        [{**item["api_response"], "json_pointer": f"/body -> /steps/{step['index']}"}], certainty="observed_failure_boundary",
                        next_check="Read step error and adjacent provider request/response before assigning a prompt/code fix")
        for capture in item["provider_records"]:
            if capture.get("validation_error"):
                finding("model", f"Captured provider output validation error: {capture['validation_error']}", [capture.get("copy", item["provider_manifest"])],
                        certainty="observed_failure_boundary", next_check="Inspect the exact response and required JSON schema, including retry context")
            if capture.get("status") != "archived" or capture.get("copy_hash_matches_archive") is False or capture.get("trace_matches_response") is False:
                finding("environment", "Provider observational evidence is missing/unavailable or its SHA/trace check fails",
                        [capture.get("copy", item["provider_manifest"])], certainty="direct_observation",
                        next_check="Locate the original observational record and verify archive linkage; do not infer model success or invent provider usage")
        if item["integrity_notes"]:
            finding("annotation_scoring", "; ".join(item["integrity_notes"]), sources, certainty="direct_observation",
                    next_check="Resolve evidence integrity; retain original score and raw evidence")
    bindings = score.get("binding_correctness") or {}
    if bindings.get("correct") is False:
        finding("linking", "Observed bindings/candidate preservation differ from frozen column/operator/value expectations",
                [score_reference], next_check="Inspect first-turn value_link/mentions/patches and provider extraction; verify labels and approved alias provenance before changing linking")
    if score.get("initial_level_correct") is False or score.get("false_clarification") is True or score.get("l1_default_switch_behavior") is False:
        finding("rules_catalog", "Initial decision/default-switch behavior differs from the frozen action contract",
                [score_reference], next_check="Compare actual extracted intent, issues, rule evidence and default applicability; level/status alone does not prove rule cause")
    if score.get("condition_preservation") is False and any(item.get("phase") in {"clarification", "post_completion"} for item in evidence):
        finding("session_state", "A multi-turn condition preservation failure is recorded by the frozen scorer",
                [score_reference], next_check="Compare every actual version, asked key, patch/invalidation and SQL; first confirm semantic scoring rather than guessing state corruption")
    for event in checkpoint.get("controller_events") or []:
        if event.get("outcome") != "answer":
            finding("session_state", "Controller could not legally answer the current actual card: " + str(event.get("reason", "")),
                    [reference(Path(checkpoint["_path"]), pointer="/controller_events")] if checkpoint.get("_path") else [score_reference],
                    certainty="direct_observation", next_check="Inspect exact current issue/card and allowed supplement; determine unsupported interface versus label/controller disagreement")
    for item in evidence:
        clarification = item["_response"].get("clarification") or {}
        if item.get("status") == "NEEDS_CLARIFICATION" and clarification.get("resume_supported") is False:
            finding("unimplemented", "Actual card explicitly declares resume_supported=false", [item["api_response"]],
                    certainty="observed_failure_boundary", next_check="Confirm which existing clarification resume capability is absent; do not infer from level-only metadata")
        elif item.get("status") == "UNSUPPORTED":
            finding("unimplemented", "Actual API declared unsupported; feature gap versus supported-source restriction is not determined",
                    [item["api_response"]], next_check="Read the explicit source/feature refusal and code boundary before classifying as unimplemented")
    queries = [("main", score.get("query") or {})] + [(f"post_completion_{item['index']}", item) for item in score.get("post_completion") or []]
    for name, query in queries:
        sem = query.get("semantic_preservation") or {}
        result = query.get("result") or {}
        if sem.get("status") == "AI_pending":
            finding("annotation_scoring", f"{name}: SQL equivalence remains AI_pending; it is not automatically correct or automatically a semantic system error",
                    [score_reference], certainty="direct_observation", next_check="Compare frozen/actual qualified AST and exact predicates, grain, dates, CASE, order and limits; retain pending until justified review")
        if result.get("correct") is False:
            finding("sql", f"{name}: saved actual table comparison failed ({result.get('reason', '')})", [score_reference],
                    next_check="Inspect actual SQL/table and frozen gold_result/schema mapping; result mismatch alone does not isolate model, state, SQL or label cause")
        elif result.get("correct") is None and result.get("reason") == "Saved gold_result unavailable":
            finding("annotation_scoring", f"{name}: saved gold_result is unavailable", [score_reference], certainty="direct_observation",
                    next_check="Find the already frozen read-only reference evidence; do not replace it with actual system output")
    needs_attention = score.get("automatic_complete") is not True or bool(findings)
    if needs_attention and not findings:
        finding("annotation_scoring", "Task is unfinished/unresolved but saved status does not identify a cause", [score_reference],
                next_check="Inspect all actual response/provider files; leave cause unassigned until supported")
    return {"id": case["id"], "task": case["task"], "category": case["category"], "scorable": score.get("scorable"),
            "automatic_complete_unchanged": score.get("automatic_complete"), "outcome": checkpoint.get("outcome"),
            "attention_required": needs_attention, "findings": findings,
            "evidence_turns": [{key: value for key, value in item.items() if key != "_response"} for item in evidence],
            "classification_policy": "Observed boundaries and hypotheses only; no status-only root-cause inference; no changes to score/gold"}


def review_entries(case, score, evidence, score_reference):
    output = []
    main_turns = [item for item in evidence if item["phase"] in {"initial", "clarification"}]
    post_turns = [item for item in evidence if item["phase"] == "post_completion"]
    queries = [("main", score.get("query") or {}, main_turns[-1] if main_turns else None,
                case.get("gold_sql"), case.get("expected_final_intent"))]
    expected_posts = (case.get("controller") or {}).get("post_completion_turns") or []
    for index, item in enumerate(score.get("post_completion") or []):
        expected = expected_posts[index] if index < len(expected_posts) else {}
        queries.append((f"post_completion_{index+1}", item, post_turns[index] if index < len(post_turns) else None,
                        expected.get("gold_sql"), expected.get("expected_intent")))
    for name, query, turn, gold_sql, expected_intent in queries:
        sem = query.get("semantic_preservation") or {}
        if sem.get("status") != "AI_pending":
            continue
        output.append({"review_id": case["id"] + "/" + name, "id": case["id"], "phase": name,
                       "scorable": score.get("scorable"), "status": "AI_pending", "review_verdict": None,
                       "reviewer": None, "review_time": None, "reason": sem.get("reason"),
                       "original_user_input": case["input"], "expected_intent": expected_intent, "gold_sql": gold_sql,
                       "actual_sql": turn.get("actual_sql") if turn else None,
                       "qualified_gold_contract": sem.get("gold"), "qualified_actual_contract": sem.get("actual"),
                       "saved_result_comparison": query.get("result"), "score_reference": score_reference,
                       "actual_trace_id": turn.get("trace_id") if turn else None,
                       "actual_api_response": turn.get("api_response") if turn else None,
                       "provider_records": turn.get("provider_records", []) if turn else [],
                       "checks_required": ["Original input plus actual asked-key supplements and ordinary edits",
                                           "Exact physical column/operator/value and candidate-only constraints",
                                           "Metric/grain/joins/CASE numerator versus denominator",
                                           "Current/base periods, inclusive/exclusive boundaries",
                                           "Grouping/order/stable tie breaker/LIMIT/NULL/zero/empty semantics",
                                           "Exact table values and meaningful columns; equal results alone insufficient"],
                       "decision_policy": "Keep AI_pending until justified review; no automatic pass and no silent modification of original score/gold"})
    return output


def markdown_report(report, output_path: Path):
    def link(ref, label):
        path = Path(ref["path"])
        path = path if path.is_absolute() else ROOT / path
        relative = os.path.relpath(path, output_path.parent).replace("\\", "/")
        return f"[{label}](<{relative}>)"
    lines = ["# 专项失败边界与语义核验索引", "", report["claim"], "",
             f"总案例 {report['total_cases']}；可评分 {report['scorable_cases']}；待标注确认 {report['pending_annotation_cases']}。原score完整保留，本文不重算正确率。", "",
             "直接观测包括实际错误码、错误步骤、provider输出格式错误及证据缺口；类别对应失败边界。最终根因仍需读取引用证据确认。hypothesis不可直接作为prompt/代码修改依据。", "",
             "| ID | 原评分 | 类别 / 证据程度 | 实际请求、响应和provider记录 |", "|---|---|---|---|"]
    for item in report["cases"]:
        if not item["attention_required"]:
            continue
        categories = "; ".join(dict.fromkeys(f"{finding['category_label']} ({finding['certainty']})" for finding in item["findings"]))
        refs = []
        for turn in item["evidence_turns"]:
            refs.append(link(turn["api_response"], f"turn{turn['index']} {turn.get('trace_id') or 'no-trace'} response"))
            refs.append(link(turn["request"], f"turn{turn['index']} request"))
            for capture in turn["provider_records"]:
                if capture.get("copy"):
                    refs.append(link(capture["copy"], f"turn{turn['index']} provider-step{capture.get('step')}"))
        result = "pending label" if not item["scorable"] else str(item["automatic_complete_unchanged"])
        lines.append(f"| {item['id']} | {result} / {item.get('outcome')} | {categories} | {'; '.join(refs) or '无已保存响应'} |")
    lines.extend(["", "详见 failure-classification.json 每条finding的observation、evidence及next_check。semantic-review-pending.jsonl保存未证明SQL等价；review_verdict/reviewer/review_time均留空，不伪造审核。pending-label-review.jsonl单列原冻结待确认标签，保持总任务分母。", "",
                  "本脚本调用模型、问答API和数据库的次数均为0；只读取本次已保存证据。"])
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    for path in (args.scores, args.run_dir, args.output_dir):
        if not path.resolve().is_relative_to(HERE):
            parser.error("Score/run/output evidence must stay inside runtime_eval")
    if args.output_dir.exists():
        raise ValueError("A new classification directory is required; original evidence is never overwritten")
    cases = load_cases(args.cases)
    scores = json.loads(args.scores.read_text(encoding="utf-8"))
    manifest = json.loads((args.run_dir / "run-manifest.json").read_text(encoding="utf-8"))
    if scores.get("labels_sha256") != digest(args.cases) or manifest.get("labels_sha256") != digest(args.cases):
        raise ValueError("Labels/score/run manifest hashes disagree")
    by_id = {item["id"]: (index, item) for index, item in enumerate(scores["cases"])}
    if set(by_id) != {case["id"] for case in cases}:
        raise ValueError("All 60 original case IDs must remain in the score evidence")
    records, reviews, pending_labels = [], [], []
    for case in cases:
        score_index, score = by_id[case["id"]]
        case_dir = args.run_dir / "cases" / case["id"]
        checkpoint_path = case_dir / "checkpoint.json"
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8")) if checkpoint_path.is_file() else {"turns": [], "outcome": "not_started"}
        checkpoint["_path"] = str(checkpoint_path)
        evidence = [turn_evidence(case_dir, turn) for turn in checkpoint.get("turns", [])]
        score_ref = reference(args.scores, pointer=f"/cases/{score_index}")
        records.append(classify_case(case, score, checkpoint, evidence, score_ref))
        reviews.extend(review_entries(case, score, evidence, score_ref))
        if not score.get("scorable"):
            pending_labels.append({"id": case["id"], "status": "pending_annotation", "original_human_review_status": case.get("human_review_status"),
                                   "original_auto_issues": case.get("auto_issues"), "original_AI_reviews": case.get("ai_reviews"),
                                   "score_reference": score_ref, "automatic_binary_score": None,
                                   "review_verdict": None, "reviewer": None, "review_time": None})
    report = {"created_at": utcnow(), "version": scores.get("version"),
              "claim": "本轮合成开发集已保存真实API证据的离线失败分类；保留原评分和AI_pending，不宣称已确认最终根因或泛化收益。",
              "total_cases": len(cases), "scorable_cases": sum(case.get("scorable") is True for case in cases),
              "pending_annotation_cases": len(pending_labels), "semantic_review_entries": len(reviews),
              "taxonomy": TAXONOMY, "finding_counts_by_category": dict(Counter(finding["category"] for record in records for finding in record["findings"])),
              "finding_counts_by_certainty": dict(Counter(finding["certainty"] for record in records for finding in record["findings"])),
              "label_sha256": digest(args.cases), "score_sha256": digest(args.scores), "run_manifest_sha256": digest(args.run_dir / "run-manifest.json"),
              "scorer_modified": False, "labels_modified": False, "model_calls": 0, "qa_API_calls": 0, "DB_queries": 0, "cases": records}
    args.output_dir.mkdir(parents=True)
    write_new(args.output_dir / "failure-classification.json", safe(report))
    for name, items in (("semantic-review-pending.jsonl", reviews), ("pending-label-review.jsonl", pending_labels)):
        with (args.output_dir / name).open("x", encoding="utf-8", newline="\n") as handle:
            for item in items:
                handle.write(json.dumps(safe(item), ensure_ascii=False) + "\n")
    markdown_report(report, args.output_dir / "failure-classification.md")
    print(json.dumps({key: value for key, value in report.items() if key != "cases"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
