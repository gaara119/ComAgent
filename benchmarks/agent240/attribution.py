"""Evidence-bounded Agent failure attribution over existing saved executions.

One prediction receives one primary family and a set of affected dimensions.
Structural findings, historical AI-review findings and unknown semantic state
are deliberately separate. No route is failed merely for differing from a
reference plan. Nothing here invokes a model or reads held-out examples.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
import json
import re


DIMENSIONS = ("result", "rag_retrieval", "evidence", "agent_process",
              "stability", "cost_efficiency", "safety")


def _canonical(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode()).hexdigest()


def _bound_review(record):
    review = record.get("review") or {}
    return (review.get("binding_verified") is True
            and review.get("response_sha256") == _canonical(record.get("raw_response")))


def _instant(value):
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return instant if instant.tzinfo is not None else None
    except (AttributeError, ValueError, TypeError):
        return None


def _review_family(reason, rag_entered):
    """Classify an already bound review note; never create a new semantic score."""
    if re.search(r"(?:丢失|丢了|未保留|没有保留|未继承|忘记|遗失).{0,25}(?:条件|年份|国家|期间|原问题|前轮|续问|状态)"
                 r"|(?:条件|年份|国家|期间|原问题|前轮|续问|状态).{0,25}(?:丢失|丢了|未保留|没有保留|未继承|忘记|遗失)", reason):
        return "state_management", {"agent_process"}
    if re.search(r"未先问|未澄清|未经.{0,20}澄清|未收到.{0,20}确认|未确认.{0,15}(?:歧义|口径)"
                 r"|不必要.{0,15}澄清|重复.{0,15}澄清|多余.{0,15}反问|误澄清", reason):
        return "clarification_protocol", {"agent_process"}
    if rag_entered is False and re.search(r"应读|应检索|应查文档|只查数据库|仅查数据库|未进入.{0,10}文档|未执行.{0,10}文档", reason):
        return "routing_or_source_selection", {"agent_process"}
    if re.search(r"引用.{0,25}(?:不支持|错误|不存在|未支持|不能支持)|(?:不支持|错误).{0,15}引用", reason):
        return "evidence_support", {"evidence"}
    return None, set()


def analyze(case, record, scored, trace=None):
    """Analyze one existing prediction; optional trace must bind to that payload.

    ``trace`` is the verified sidecar produced/loaded by agent240.traces. In its
    absence only the final payload's steps are available. A missing intermediate
    state does not fail BASE configurations with no state by design.
    """
    identity = {"id": case.get("id"), "suite": case.get("suite"),
                "group": case.get("group"), "case_id": case.get("case_id"),
                "turn_index": case.get("turn_index"),
                "arm": record.get("arm") if record else scored.get("arm")}
    from benchmarks.agent240.review_status import current_status
    gold_status = current_status(case)
    if record is None:
        return {**identity, "observed": False, "primary_failure_family": "not_observed",
                "primary_basis": "not_verified", "dimensions": [], "finding_evidence": [],
                "uncertainties": ["prediction_not_observed"], "process_checks": {},
                "gold_review_status": gold_status, "review_coverage": {"business": False, "external": False},
                "failed_prediction": None}
    payload = record.get("raw_response") or {}
    if trace is not None and trace.get("prediction_sha256") != _canonical(payload):
        raise ValueError("Attribution trace is not bound to this actual prediction")
    findings, uncertainties, dimensions = [], [], set()
    verified_review = _bound_review(record)
    if gold_status not in {"approved", "accepted", "human_reviewed"}:
        uncertainties.append("gold_not_human_approved; scores and review-attribution remain exploratory")
    if not verified_review:
        uncertainties.append("business_review_not_bound_to_actual_prediction")

    attempts = trace["attempts"] if trace is not None else [{
        "kind": "final_only", "status": payload.get("status"), "steps": payload.get("steps", []),
        "intent": payload.get("intent"), "clarification": payload.get("clarification"),
        "state_metadata": {"clarify": payload.get("metadata", {}).get("clarify")}}]
    complete_attempts = trace is not None
    if not complete_attempts:
        uncertainties.append("intermediate_attempt_traces_unavailable; final_steps_only")
    tools, parameter_checks, dependency_checks = set(), [], []
    step_errors = []
    state_versions, patch_events, state_snapshots = [], 0, 0
    context_checks = []
    source_text = (case.get("source_context") or {}).get("text")
    prior_tool_ids = set()
    requests = []

    def finding(family, dimension, basis, path, detail, *, phase=None, step=None):
        findings.append({"family": family, "dimension": dimension, "basis": basis,
                         "path": path, "attempt_index": phase,
                         "step_index": step, "detail": detail})
        dimensions.add(dimension)

    for phase_index, attempt in enumerate(attempts):
        request = attempt.get("request") or {}
        if request:
            requests.append(request)
        state = (attempt.get("state_metadata") or {}).get("clarify") or {}
        if isinstance(state.get("semantic_contract"), dict):
            state_snapshots += 1
        if type(state.get("intent_version")) is int:
            state_versions.append(state["intent_version"])
        patch_events += len(state.get("patch_history") or [])
        context_meta = (attempt.get("state_metadata") or {}).get("session_context") or {}
        if isinstance(source_text, str) and context_meta.get("content_sha256"):
            context_ok = (context_meta["content_sha256"] == sha256(source_text.encode()).hexdigest()
                          and context_meta.get("characters") == len(source_text)
                          and context_meta.get("truncated") is False)
            context_checks.append(context_ok)
            if not context_ok:
                finding("state_management", "agent_process", "program",
                        f"$.attempts[{phase_index}].state_metadata.session_context",
                        "Observed session context hash/length/truncation differs from the full declared source text",
                        phase=phase_index)
        steps = attempt.get("steps") or []
        allowed = next((s.get("output_summary", {}).get("allowed_tools") for s in steps
                        if s.get("name") == "source_scope" and s.get("status") == "ok"), None)
        prior_tool_ids = set()
        for step_index, step in enumerate(steps):
            path = f"$.attempts[{phase_index}].steps[{step_index}]" if complete_attempts else f"$.raw_response.steps[{step_index}]"
            name, status = step.get("name"), step.get("status")
            inp, out = step.get("input_summary") or {}, step.get("output_summary") or {}
            if status in {"error", "failed"}:
                step_errors.append({"attempt_index": phase_index, "step_index": step_index,
                                    "name": name, "path": path, "error": out.get("error")})
            if name == "sql_exec":
                tools.add("sql")
                valid = isinstance(inp.get("sql"), str) and bool(inp["sql"].strip())
                expected_db = (request.get("scope") or {}).get("db_id")
                actual_db = inp.get("db_id")
                if expected_db and actual_db is not None:
                    valid = valid and expected_db == actual_db
                parameter_checks.append(valid)
                if isinstance(allowed, list) and "sql" not in allowed and status == "ok":
                    finding("tool_permission_violation", "safety", "program", path,
                            "Successful SQL execution is outside the actual caller tool permission set", phase=phase_index, step=step_index)
                if not valid:
                    finding("tool_parameters", "agent_process", "program", path,
                            "SQL execution missing SQL text or uses a different explicitly selected database", phase=phase_index, step=step_index)
            elif name == "rag_generate":
                # This proves entry into the RAG pipeline, not the retriever's recall.
                tools.add("doc")
            elif name == "composed_tool":
                call = inp.get("step") or {}
                tool, step_id = call.get("tool"), call.get("step_id")
                if isinstance(tool, str):
                    tools.add(tool)
                valid = (tool in {"sql", "doc", "context"} and isinstance(call.get("question"), str)
                         and bool(call["question"].strip()) and isinstance(step_id, str) and bool(step_id))
                parameter_checks.append(valid)
                if not valid:
                    finding("tool_parameters", "agent_process", "program", path,
                            "Actual tool input violates the recorded public tool-plan structure", phase=phase_index, step=step_index)
                deps, supplied = call.get("depends_on", []), inp.get("dependency_results")
                if isinstance(deps, list) and all(isinstance(d, str) for d in deps) and isinstance(supplied, dict):
                    dependency_ok = set(deps) <= prior_tool_ids and set(deps) == set(supplied)
                else:
                    dependency_ok = False
                dependency_checks.append(dependency_ok)
                if not dependency_ok:
                    finding("step_dependencies", "agent_process", "program", path,
                            "Recorded dependencies lack prior actual steps or supplied dependency keys differ", phase=phase_index, step=step_index)
                if isinstance(step_id, str):
                    prior_tool_ids.add(step_id)
                if isinstance(allowed, list) and tool not in allowed and out.get("status") in {"SUCCEEDED", "EMPTY_RESULT"}:
                    finding("tool_permission_violation", "safety", "program", path,
                            "Successful actual tool output is outside the caller's allowed tool set", phase=phase_index, step=step_index)
                scope_docs = (request.get("scope") or {}).get("doc_ids")
                selected_docs = call.get("doc_ids")
                # Only explicit caller restrictions are authoritative. Gold's
                # preferred source plan is not an exclusive permission list.
                if tool == "doc" and scope_docs and isinstance(selected_docs, list) and not set(selected_docs) <= set(scope_docs) and out.get("status") == "SUCCEEDED":
                    finding("source_scope_violation", "safety", "program", path,
                            "Actual document tool parameters exceed the nonempty caller document restriction", phase=phase_index, step=step_index)

    rag_entered = "doc" in tools if any(a.get("steps") for a in attempts) else None
    process_checks = {
        "trace_scope": "all_actual_attempts" if complete_attempts else "final_payload_only",
        "tool_parameters_structurally_valid": all(parameter_checks) if parameter_checks else None,
        "dependency_transfer_structurally_valid": all(dependency_checks) if dependency_checks else None,
        "actual_tool_types": sorted(tools), "rag_entered": rag_entered,
        "state_snapshots_observed": state_snapshots, "state_versions_observed": state_versions,
        "patch_events_observed": patch_events,
        "multi_turn_condition_correctness": None,
        "multi_turn_semantic_status": "not_verified: no independently approved structured per-turn expected state in this bundle",
        "clarification_initial_observed": any(a.get("status") == "NEEDS_CLARIFICATION" for a in attempts[:-1]) if complete_attempts else None,
        "clarification_supplement_requests": sum(str(a.get("kind", "")).startswith("supplement") for a in attempts) if complete_attempts else None,
        "clarification_completed": (payload.get("status") in {"SUCCEEDED", "EMPTY_RESULT"}) if complete_attempts and any(str(a.get("kind", "")).startswith("supplement") for a in attempts) else None,
        "clarification_necessity_correctness": None,
        "tool_parameter_semantic_correctness": None,
        "full_source_context_preserved": all(context_checks) if context_checks else None,
        "full_source_context_checks": len(context_checks),
        "first_request_sent_utc": attempts[0].get("sent_utc") if complete_attempts and attempts else None,
    }
    if requests:
        sessions = {r.get("session_id") for r in requests if r.get("session_id")}
        contexts = {r.get("context_id") for r in requests if r.get("context_id")}
        process_checks["same_question_session_preserved"] = len(sessions) == 1
        process_checks["same_question_context_preserved"] = len(contexts) <= 1
        # Store identity only for grouping continuity checks, never as a score.
        process_checks["session_ids"] = sorted(sessions)
        process_checks["context_ids"] = sorted(contexts)
        expected_time = _instant(case.get("reference_datetime"))
        if expected_time is not None and all(_instant(r.get("reference_datetime")) is not None and r.get("timezone") for r in requests):
            process_checks["reference_clock_preserved"] = all(
                _instant(r.get("reference_datetime")) == expected_time and r.get("timezone") == case.get("timezone")
                for r in requests)
        else:
            process_checks["reference_clock_preserved"] = None
        process_checks["initial_question_preserved"] = requests[0].get("message") == case.get("question") if case.get("question") else None
        if len(sessions) > 1:
            finding("session_binding", "agent_process", "program", "$.attempts[*].request.session_id",
                    "Initial and supplement requests use different session IDs")
        if len(contexts) > 1:
            uncertainties.append("context_binding_changed_between_actual_attempts; task switch/refresh must be reviewed")
    if case.get("group") == "B":
        uncertainties.append("condition_retention_semantics_requires_per_turn_expected_state_review")
    if rag_entered is False and case.get("expected_route") in {"rag", "hybrid"}:
        uncertainties.append("reference_document_path_not_observed; inspect Agent source selection, do not score retriever failure")
    if rag_entered:
        uncertainties.append("retrieval_quality_requires_matched_EvalScope_rank/qrel_result; final_citations_are_not_rankings")
    uncertainties.append("citation_semantic_support_not_inferred_from_ID_or_quote_match")

    review = record.get("review") or {}
    review_reason = review.get("reason") or ""
    result_failure = any(scored.get(key) is False for key in ("accuracy", "external_success", "exact_match")) or payload.get("status") == "FAILED"
    if result_failure:
        dimensions.add("result")
    if verified_review and (review.get("business_correct") is False or review.get("external_task_success") is False):
        family, affected = _review_family(review_reason, rag_entered)
        if family:
            for dimension in affected:
                finding(family, dimension, "bound_historical_AI_review", "$.review.reason", review_reason)
        elif review.get("business_correct") is True and review.get("external_task_success") is False:
            finding("task_delivery_incomplete", "result", "bound_historical_AI_review", "$.review.reason", review_reason)
    if scored.get("error") is True or payload.get("status") == "FAILED":
        dimensions.add("stability")

    checks = scored.get("checks") or {}
    if checks.get("citation_id_integrity") is False:
        finding("citation_reference_invalid", "evidence", "program", "$.raw_response.answer/evidences",
                "Answer references an evidence ID absent from the actual evidence list")
    if checks.get("sql_readonly_ast") is False:
        finding("non_readonly_SQL_shape", "safety", "program", "$.raw_response.steps[sql_exec]",
                "An actual SQL execution trace contains a non-readonly statement shape")
    if payload.get("status") == "FAILED":
        code = (payload.get("error") or {}).get("code")
        family = {"sql_rejected": "SQL_validation_or_contract_block",
                  "sql_execution": "SQL_execution_failure", "llm_format": "model_output_contract",
                  "composed_plan_failed": "planning_or_completion_failure",
                  "clarification_conflict": "clarification_protocol"}.get(code, "execution_failure")
        if family in {"planning_or_completion_failure", "clarification_protocol", "model_output_contract"}:
            dimensions.add("agent_process")
        path = "$.raw_response.error"
        last = step_errors[-1] if step_errors else None
        finding(family, "stability", "observed_final_failure", path,
                {"error_code": code, "last_failed_step": last})
    # A repaired intermediate validation error is retained as an event, not
    # promoted to another failed task or an automatic final failure.
    priorities = ("non_readonly_SQL_shape", "tool_permission_violation", "source_scope_violation",
                  "session_binding", "tool_parameters", "step_dependencies", "state_management",
                  "routing_or_source_selection", "clarification_protocol", "citation_reference_invalid",
                  "evidence_support", "model_output_contract", "SQL_execution_failure",
                  "SQL_validation_or_contract_block", "planning_or_completion_failure", "execution_failure",
                  "task_delivery_incomplete")
    eligible_findings = [f for f in findings if result_failure or f["dimension"] == "safety" or f["basis"] == "observed_final_failure"]
    selected = min(eligible_findings, key=lambda f: priorities.index(f["family"]) if f["family"] in priorities else len(priorities)) if eligible_findings else None
    if selected:
        primary, basis = selected["family"], selected["basis"]
    elif scored.get("exact_match") is False:
        primary, basis = "result_table_mismatch_unlocalized", "program_result_comparison"
    elif scored.get("accuracy") is False:
        primary, basis = "business_semantics_unlocalized", "bound_historical_AI_review" if verified_review else "not_verified"
    elif scored.get("external_success") is False:
        primary, basis = "task_delivery_incomplete", "bound_historical_AI_review" if verified_review else "not_verified"
    elif any(scored.get(k) is None for k in ("accuracy", "external_success")):
        primary, basis = "unresolved", "not_verified"
    else:
        primary, basis = "no_failure_observed", "existing_result_and_review"
    unresolved_axes = [name for name, key in (("business_correctness", "accuracy"),
                                             ("external_task_success", "external_success"))
                       if scored.get(key) is None]
    if scored.get("sql_eligible") and scored.get("exact_match") is None:
        unresolved_axes.append("SQL_result_match")
    return {**identity, "observed": True, "primary_failure_family": primary, "primary_basis": basis,
            "dimensions": sorted(dimensions), "finding_evidence": findings,
            "uncertainties": list(dict.fromkeys(uncertainties)), "process_checks": process_checks,
            "intermediate_error_events": step_errors,
            "gold_review_status": gold_status,
            "unresolved_axes": unresolved_axes,
            "review_coverage": {"business": verified_review and type(review.get("business_correct")) is bool,
                                "external": verified_review and type(review.get("external_task_success")) is bool},
            "failed_prediction": result_failure,
            "attribution_boundary": "One primary diagnostic family per prediction, not proof of an exclusive root cause; dimensions overlap and must not be summed as independent questions. Historical AI notes remain AI notes. No model internal reasoning is judged."}


def summarize(rows):
    """Aggregate either attribution outputs or scored rows with attribution."""
    items = [r.get("attribution", r) for r in rows]
    n = len(items)
    primary = Counter(r.get("primary_failure_family", "unresolved") for r in items)
    dimensions = Counter(d for r in items for d in set(r.get("dimensions", [])))
    groups = defaultdict(list)
    for row in items:
        if row.get("group") == "B" and row.get("case_id"):
            groups[(row.get("suite"), row.get("arm"), row["case_id"])].append(row)
    sessions_known, sessions_consistent, order_known, order_consistent = 0, 0, 0, 0
    timed_dialogues, chronological_dialogues = 0, 0
    for group in groups.values():
        identities = [r.get("process_checks", {}).get("session_ids") for r in group]
        if all(isinstance(ids, list) and ids for ids in identities):
            sessions_known += 1
            sessions_consistent += len({x for ids in identities for x in ids}) == 1
        turns = [r.get("turn_index") for r in group]
        if all(type(t) is int for t in turns):
            order_known += 1
            order_consistent += len(set(turns)) == len(turns)
            ordered = sorted(group, key=lambda r: r["turn_index"])
            times = [_instant(r.get("process_checks", {}).get("first_request_sent_utc")) for r in ordered]
            if all(t is not None for t in times):
                timed_dialogues += 1
                chronological_dialogues += all(later >= earlier for earlier, later in zip(times, times[1:]))
    gold_status_by_id = defaultdict(set)
    for row in items:
        gold_status_by_id[row.get("id")].add(row.get("gold_review_status", "not_recorded"))
    unique_gold_statuses = Counter(next(iter(values)) if len(values) == 1 else "conflicting_status"
                                  for values in gold_status_by_id.values())
    approved_gold = sum(count for status, count in unique_gold_statuses.items()
                        if status in {"approved", "accepted", "human_reviewed"})
    return {"predictions": n, "unique_protocol_cases": len({r.get("id") for r in items}),
            "primary_family_counts": dict(primary), "affected_dimension_counts_overlapping": dict(dimensions),
            "failed_predictions": sum(r.get("failed_prediction") is True for r in items),
            "business_review_known": sum(r.get("review_coverage", {}).get("business") is True for r in items),
            "external_review_known": sum(r.get("review_coverage", {}).get("external") is True for r in items),
            "business_review_coverage": sum(r.get("review_coverage", {}).get("business") is True for r in items) / n if n else None,
            "external_review_coverage": sum(r.get("review_coverage", {}).get("external") is True for r in items) / n if n else None,
            "gold_review_statuses": dict(Counter(r.get("gold_review_status", "not_recorded") for r in items)),
            "gold_unique_case_statuses": dict(unique_gold_statuses),
            "gold_human_approved_cases": approved_gold,
            "gold_human_review_coverage": approved_gold / len(gold_status_by_id) if gold_status_by_id else None,
            "unresolved_axis_counts": dict(Counter(axis for row in items for axis in row.get("unresolved_axes", []))),
            "B_dialogue_session_binding": {"known_dialogues": sessions_known, "consistent_dialogues": sessions_consistent},
            "B_turn_identifiers": {"known_dialogues": order_known, "unique_turn_identifiers": order_consistent,
                                   "boundary": "Unique turn IDs only; chronological order is checked separately from actual timestamps."},
            "B_initial_request_order": {"known_dialogues": timed_dialogues, "chronological_dialogues": chronological_dialogues,
                                        "boundary": "Actual initial-request timestamps monotonic in declared turn order; not a semantic condition-retention score."},
            "full_source_context_preserved": {"known_predictions": sum(r.get("process_checks", {}).get("full_source_context_preserved") is not None for r in items),
                                                "matched_predictions": sum(r.get("process_checks", {}).get("full_source_context_preserved") is True for r in items)},
            "semantic_condition_retention": None,
            "boundary": "One prediction per primary bucket; overlapping dimensions are diagnostic, never added to the task denominator."}
