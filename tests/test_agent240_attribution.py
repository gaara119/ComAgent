"""Small unit fixtures test attribution boundaries, not additional benchmark tasks."""
from hashlib import sha256
import json

import pytest

from benchmarks.agent240.attribution import analyze, summarize


def canonical(payload):
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode()).hexdigest()


def record(steps=(), *, status="SUCCEEDED", business=True, external=True, reason=""):
    payload = {"status": status, "steps": list(steps), "metadata": {}, "trace_id": "unit"}
    return {"arm": "BASE", "raw_response": payload,
            "review": {"binding_verified": True, "response_sha256": canonical(payload),
                       "business_correct": business, "external_task_success": external, "reason": reason}}


def case(**kwargs):
    return {"id": "unit:q", "suite": "unit", "group": "A", "case_id": "a", "turn_index": 1,
            "reference_provenance": {"gold_human_review_status": "pending"}, **kwargs}


def scored(**kwargs):
    return {"accuracy": True, "external_success": True, "exact_match": None,
            "error": False, "checks": {}, **kwargs}


def tool(step_id, tool_name, deps=(), supplied=None, status="SUCCEEDED"):
    return {"name": "composed_tool", "status": "ok", "input_summary": {
        "step": {"step_id": step_id, "tool": tool_name, "question": "unit input",
                 "depends_on": list(deps)}, "dependency_results": supplied or {}},
        "output_summary": {"status": status}}


def trace(row, attempts):
    return {"prediction_sha256": canonical(row["raw_response"]), "attempts": attempts}


def test_reasonable_alternative_plan_is_not_failed_for_different_route_or_ids():
    row = record([tool("different-id", "sql")])
    result = analyze(case(expected_route="rag"), row, scored())
    assert result["primary_failure_family"] == "no_failure_observed"
    assert result["dimensions"] == []
    assert result["process_checks"]["rag_entered"] is False
    assert any("do not score retriever failure" in x for x in result["uncertainties"])


def test_bound_review_source_selection_failure_is_agent_not_retriever():
    row = record([tool("s1", "sql")], business=False, external=False,
                 reason="应读U2资料给成员，实际只查数据库artist，没有回答成员。")
    result = analyze(case(expected_route="rag"), row, scored(accuracy=False, external_success=False))
    assert result["primary_failure_family"] == "routing_or_source_selection"
    assert "agent_process" in result["dimensions"]
    assert "rag_retrieval" not in result["dimensions"]
    assert result["primary_basis"] == "bound_historical_AI_review"


def test_missing_final_quote_does_not_prove_retrieval_failure():
    row = record([tool("s1", "doc")], business=False, external=False)
    result = analyze(case(expected_route="rag"), row, scored(accuracy=False, external_success=False))
    assert result["primary_failure_family"] == "business_semantics_unlocalized"
    assert result["process_checks"]["rag_entered"] is True
    assert "rag_retrieval" not in result["dimensions"]


def test_unbound_ai_note_is_not_consumed_as_causal_evidence():
    row = record([tool("s1", "sql")], business=False, reason="未先问期间")
    row["review"]["response_sha256"] = "0" * 64
    result = analyze(case(), row, scored(accuracy=None, external_success=None))
    assert result["primary_failure_family"] == "unresolved"
    assert result["review_coverage"]["business"] is False
    assert not any(f["basis"] == "bound_historical_AI_review" for f in result["finding_evidence"])


def test_actual_dependency_parameters_and_prior_step_proof():
    row = record([tool("actual-a", "sql"), tool("actual-b", "doc", ["actual-a"], {"actual-a": {"status": "SUCCEEDED"}})])
    result = analyze(case(), row, scored())
    assert result["process_checks"]["dependency_transfer_structurally_valid"] is True
    assert result["process_checks"]["actual_tool_types"] == ["doc", "sql"]


def test_dependency_failure_keeps_exact_step_locator():
    row = record([tool("s1", "doc", ["missing-step"], {})], business=False)
    result = analyze(case(), row, scored(accuracy=False))
    assert result["primary_failure_family"] == "step_dependencies"
    finding = next(f for f in result["finding_evidence"] if f["family"] == "step_dependencies")
    assert finding["step_index"] == 0 and finding["path"] == "$.raw_response.steps[0]"


def test_repaired_intermediate_error_is_not_an_extra_failed_task():
    row = record([{"name": "sql_validate", "status": "error", "output_summary": {"error": "temporary invalid SQL"}},
                  {"name": "sql_validate", "status": "ok"}, {"name": "sql_exec", "status": "ok", "input_summary": {"sql": "SELECT 1"}}])
    result = analyze(case(), row, scored(exact_match=True))
    assert result["failed_prediction"] is False
    assert result["primary_failure_family"] == "no_failure_observed"
    assert len(result["intermediate_error_events"]) == 1


def test_missing_internal_state_in_baseline_is_not_a_failure():
    result = analyze(case(group="B"), record(), scored())
    assert result["primary_failure_family"] == "no_failure_observed"
    assert result["process_checks"]["state_snapshots_observed"] == 0
    assert result["process_checks"]["multi_turn_condition_correctness"] is None


def test_actual_clarification_close_is_separate_from_necessity_correctness():
    row = record()
    phases = [{"kind": "initial", "status": "NEEDS_CLARIFICATION", "steps": [],
               "request": {"session_id": "same"}},
              {"kind": "supplement_01", "status": "SUCCEEDED", "steps": [],
               "request": {"session_id": "same"}}]
    result = analyze(case(), row, scored(), trace(row, phases))
    assert result["process_checks"]["clarification_completed"] is True
    assert result["process_checks"]["clarification_supplement_requests"] == 1
    assert result["process_checks"]["clarification_necessity_correctness"] is None
    assert result["process_checks"]["same_question_session_preserved"] is True


def test_state_changes_are_observations_not_inferred_correctness():
    row = record()
    phases = [{"kind": "initial", "steps": [], "state_metadata": {"clarify": {
        "intent_version": 1, "semantic_contract": {"country": "USA"}}}},
        {"kind": "supplement_01", "steps": [], "state_metadata": {"clarify": {
            "intent_version": 2, "semantic_contract": {"country": "Canada"}, "patch_history": [{}]}}}]
    result = analyze(case(group="B"), row, scored(), trace(row, phases))
    assert result["process_checks"]["state_versions_observed"] == [1, 2]
    assert result["process_checks"]["patch_events_observed"] == 1
    assert result["process_checks"]["multi_turn_condition_correctness"] is None


def test_trace_must_match_exact_response():
    row = record()
    with pytest.raises(ValueError, match="not bound"):
        analyze(case(), row, scored(), {"prediction_sha256": "wrong", "attempts": []})


def test_successful_tool_scope_violation_is_not_hidden_by_correct_answer():
    scope = {"name": "source_scope", "status": "ok", "output_summary": {"allowed_tools": ["doc"]}}
    row = record([scope, {"name": "sql_exec", "status": "ok", "input_summary": {"sql": "SELECT 1"}}])
    result = analyze(case(), row, scored())
    assert result["primary_failure_family"] == "tool_permission_violation"
    assert "safety" in result["dimensions"]


def test_permission_block_is_not_reported_as_successful_violation():
    scope = {"name": "source_scope", "status": "ok", "output_summary": {"allowed_tools": ["doc"]}}
    row = record([scope, tool("s1", "sql", status="UNSUPPORTED")], status="UNSUPPORTED")
    result = analyze(case(), row, scored())
    assert not any(f["family"] == "tool_permission_violation" for f in result["finding_evidence"])


def test_pending_gold_and_review_coverage_are_explicit():
    row = record(business=None, external=True)
    result = analyze(case(), row, scored(accuracy=None))
    summary = summarize([result])
    assert result["gold_review_status"] == "pending"
    assert summary["business_review_known"] == 0
    assert summary["external_review_known"] == 1
    assert summary["gold_review_statuses"] == {"pending": 1}


def test_dimension_counts_never_inflate_prediction_denominator():
    result = {"id": "a", "primary_failure_family": "one", "dimensions": ["result", "result", "evidence"],
              "failed_prediction": True, "review_coverage": {}}
    summary = summarize([result])
    assert summary["predictions"] == 1
    assert sum(summary["primary_family_counts"].values()) == 1
    assert summary["affected_dimension_counts_overlapping"] == {"result": 1, "evidence": 1}


def test_review_reported_condition_loss_has_review_basis_not_program_proof():
    row = record(business=False, reason="续问丢失了原来的国家筛选条件")
    result = analyze(case(group="B"), row, scored(accuracy=False))
    assert result["primary_failure_family"] == "state_management"
    assert result["primary_basis"] == "bound_historical_AI_review"
    assert result["process_checks"]["multi_turn_condition_correctness"] is None


def test_final_failure_and_prior_errors_are_distinct():
    row = record([{"name": "sql_exec", "status": "error", "input_summary": {"sql": "SELECT 1"},
                   "output_summary": {"error": "timeout"}}], status="FAILED", business=None, external=False)
    row["raw_response"]["error"] = {"code": "sql_execution"}
    row["review"]["response_sha256"] = canonical(row["raw_response"])
    result = analyze(case(), row, scored(accuracy=None, external_success=False, error=True))
    assert result["primary_failure_family"] == "SQL_execution_failure"
    assert result["failed_prediction"] is True
    assert result["finding_evidence"][-1]["detail"]["last_failed_step"]["step_index"] == 0


def test_absent_prediction_is_unobserved_not_a_success():
    result = analyze(case(), None, scored(arm="BASE"))
    assert result["observed"] is False
    assert result["primary_failure_family"] == "not_observed"
    assert result["failed_prediction"] is None


def test_full_B_context_is_checked_by_actual_hash_length_and_truncation():
    source = "完整正文" * 5
    row = record(business=False)
    phases = [{"steps": [], "state_metadata": {"session_context": {
        "content_sha256": sha256(source.encode()).hexdigest(), "characters": len(source), "truncated": False}}}]
    result = analyze(case(group="B", source_context={"text": source}), row, scored(accuracy=False), trace(row, phases))
    assert result["process_checks"]["full_source_context_preserved"] is True
    phases[0]["state_metadata"]["session_context"]["truncated"] = True
    result = analyze(case(group="B", source_context={"text": source}), row, scored(accuracy=False), trace(row, phases))
    assert result["process_checks"]["full_source_context_preserved"] is False
    assert result["primary_failure_family"] == "state_management"


def test_B_turn_order_uses_actual_timestamps_and_not_file_order():
    rows = [{"id": "one", "suite": "unit", "arm": "BASE", "group": "B", "case_id": "b", "turn_index": 2,
             "process_checks": {"first_request_sent_utc": "2026-11-01T00:00:02+00:00"}},
            {"id": "two", "suite": "unit", "arm": "BASE", "group": "B", "case_id": "b", "turn_index": 1,
             "process_checks": {"first_request_sent_utc": "2026-11-01T00:00:01+00:00"}}]
    assert summarize(rows)["B_initial_request_order"]["chronological_dialogues"] == 1
    rows[0]["process_checks"]["first_request_sent_utc"] = "2026-11-01T00:00:00+00:00"
    assert summarize(rows)["B_initial_request_order"]["chronological_dialogues"] == 0
