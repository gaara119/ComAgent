"""Public, offline regression for the original-panel metrics and evidence gate."""
import hashlib
import json

import pytest

from benchmarks.agent240.evaluate import load_bundle, score, summarize
from benchmarks.agent240.metrics import provider_totals, rate, table_scores, text_scores
from benchmarks.agent240.checks import inspect_record, readonly_ast, summarize_checks


def table(rows, columns=("amount",)):
    return {"columns": list(columns), "rows": rows, "available": True}


def test_exact_values_do_not_round_scale_or_impute():
    assert not table_scores(table([["0.125"]]), table([["12.5"]]))["exact_match"]
    assert not table_scores(table([["1.234"]]), table([["1.23"]]))["exact_match"]
    assert not table_scores(table([[None]]), table([[0]]))["exact_match"]
    assert not table_scores(table([[False]]), table([[0]]))["exact_match"]


def test_global_column_mapping_and_duplicate_multiplicity():
    gold = table([["A", 1], ["B", 2]], ("name", "n"))
    actual = table([[2, "B"], [1, "A"]], ("count", "title"))
    assert table_scores(gold, actual)["exact_match"] is True
    assert table_scores(gold, actual, ordered=True)["exact_match"] is False
    assert table_scores(gold, actual, ordered=True)["row_f1"] == 1
    assert table_scores(table([[1], [1]]), table([[1]]))["row_f1"] == pytest.approx(2 / 3)
    assert table_scores(table([[1]]), table([[1], [1]]))["exact_match"] is False


@pytest.mark.parametrize("field", ["available", "truncated"])
def test_invalid_or_incomplete_reference_is_unknown(field):
    reference = table([[1]])
    reference[field] = field == "truncated"
    assert table_scores(reference, table([[1]]))["exact_match"] is None


def test_missing_sql_prediction_stays_in_denominator():
    case = {"id": "s:q", "suite": "s", "reference": {**table([[1]]), "sql": "select 1"}}
    row = score(case, None)
    summary = summarize([row])
    assert summary["SQL_exact_match"]["total"] == 1
    assert summary["SQL_exact_match"]["unknown"] == 1
    assert summary["SQL_row_F1"]["eligible"] == 1


def test_business_review_is_bound_to_actual_payload():
    raw = {"answer": "one", "status": "SUCCEEDED"}
    digest = hashlib.sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    case = {"id": "s:q", "suite": "s"}
    record = {"arm": "X", "final_status": "SUCCEEDED", "raw_response": raw,
              "review": {"binding_verified": True, "response_sha256": digest,
                         "business_correct": True}, "attempts": []}
    assert score(case, record)["accuracy"] is True
    record["raw_response"]["answer"] = "two"
    assert score(case, record)["accuracy"] is None


def test_missing_provider_capture_is_not_free():
    usage = provider_totals([{"kind": "initial"}])
    assert usage["physical_calls"] is None
    assert usage["input_tokens"] is None
    assert usage["collection_gap_requests"] == 1


def test_missing_usage_and_duplicate_captures():
    provider = {"capture_id": "x", "input_tokens": 10, "output_tokens": None,
                "cache_hit_tokens": None, "cache_miss_tokens": None}
    attempt = {"provider_attempts": [provider], "provider_collection_complete": True}
    result = provider_totals([attempt, attempt])
    assert result["physical_calls"] == 1
    assert result["input_tokens"] == 10
    assert result["output_tokens"] is None
    assert result["cache_hit_tokens"] is None


def test_unicode_text_f1_and_no_reference():
    assert text_scores("あ", "い")["text_f1"] == 0
    assert text_scores("响应5分钟", "响应5分钟")["text_f1"] == 1
    assert text_scores(None, "looks correct")["text_em"] is None
    assert text_scores("5%", "5")["text_f1"] < 1
    assert text_scores("_", "__")["text_f1"] < 1


def test_clarification_is_not_failure_recovery():
    row = score({"id": "x", "suite": "s"}, {
        "arm": "X", "final_status": "SUCCEEDED", "raw_response": {}, "attempts": [
            {"kind": "initial", "status": "NEEDS_CLARIFICATION", "http_status": 200, "elapsed_ms": 2},
            {"kind": "supplement", "status": "SUCCEEDED", "http_status": 200, "elapsed_ms": 3}]})
    assert not row["error"]
    assert not row["failure_recovery_eligible"]
    assert row["elapsed_ms"] == 5


def test_only_observed_recovery_attempts_have_a_recovery_denominator():
    case = {"id": "x", "suite": "s"}
    record = {"arm": "X", "final_status": "FAILED", "raw_response": {}, "attempts": [
        {"status": "FAILED", "http_status": 200}]}
    assert not score(case, record)["failure_recovery_eligible"]
    record["attempts"].append({"status": "SUCCEEDED", "http_status": 200})
    record["final_status"] = "SUCCEEDED"
    row = score(case, record)
    assert row["error"] and not row["final_failed"]
    assert row["recovered"] is True


def test_hash_manifest_cannot_omit_dataset_or_records(tmp_path):
    (tmp_path / "manifest.json").write_text('{"files":{}}', encoding="utf-8")
    with pytest.raises(ValueError, match="must hash"):
        load_bundle(tmp_path)


def test_unknown_rate_is_not_passing_or_silently_dropped():
    result = rate([True, False, None])
    assert result["total"] == 3 and result["known_rate"] == .5
    assert result["full_rate"] is None and result["unknown"] == 1
    assert result["lower_bound"] == pytest.approx(1 / 3)


def test_missing_prediction_keeps_task_type_and_nonfinite_time_rejected():
    from benchmarks.agent240.metrics import percentile
    assert score({"id": "x", "suite": "s", "expected_route": "rag"}, None)["expected_route"] == "rag"
    with pytest.raises(ValueError, match="finite"):
        percentile([float("inf")], 50)


def test_gold_user_text_is_not_a_document_qrel_or_ranked_recall():
    case = {"reference_provenance": {
        "gold_source_plan": [{"kind": "doc", "source_id": "doc1"}],
        "gold_evidence": [{"source_id": "doc1", "input_path": "/doc_sections/doc1/text", "quote": "fact"},
                          {"source_id": "doc1", "input_path": "/question/user_text", "quote": "question"}]}}
    record = {"raw_response": {"answer": "fact[E1]", "evidences": [
        {"evidence_id": "E1", "doc_id": "doc1", "section_path": ["a"], "text": "fact"}]}}
    result = inspect_record(case, record)
    assert result["returned_gold_quote_obligations"] == 1
    assert result["returned_gold_quote_matches"] == 1
    assert result["retrieval_recall_at_k"] is None
    assert result["citation_id_integrity"] is True
    assert result["citation_semantic_support"] is None


def test_dangling_citation_does_not_pass_id_integrity():
    result = inspect_record({}, {"raw_response": {"answer": "answer[E9]", "evidences": []}})
    assert result["citation_id_integrity"] is False
    assert result["dangling_ids"] == ["E9"]


def test_dag_checks_dependencies_and_uses_actual_plan_trace_when_metadata_missing():
    step = {"name": "composed_plan", "output_summary": {"plan": {"steps": [
        {"step_id": "s1", "tool": "doc", "depends_on": ["s2"]}]}}}
    assert inspect_record({}, {"raw_response": {"steps": [step]}})["dag_structure_valid"] is False
    step["output_summary"]["plan"]["steps"][0]["depends_on"] = []
    assert inspect_record({}, {"raw_response": {"steps": [step]}})["dag_structure_valid"] is True


@pytest.mark.parametrize("sql", ["DELETE FROM t", "SELECT 1; DELETE FROM t", "SELECT * INTO x FROM t", "WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x"])
def test_sql_readonly_shape_rejects_writes_but_is_not_attack_defense(sql):
    assert readonly_ast(sql) is False
    assert inspect_record({}, {"raw_response": {}})["attack_defense_rate"] is None


def test_sql_parse_unknown_is_not_removed_from_security_denominator():
    checks = {"executed_SQL_count": 1, "sql_readonly_ast": None}
    summary = summarize_checks([{"checks": checks}])
    assert summary["sql_readonly_ast"]["unknown"] == 1
    assert summary["sql_readonly_ast"]["full_rate"] is None
