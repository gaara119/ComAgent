"""Aggregation, pairing and assessment boundaries; no models or network."""
from copy import deepcopy
from hashlib import sha256
import json

import pytest

from benchmarks.rag.compare import compare_runs
from benchmarks.rag.report import aggregate, paired
from benchmarks.rag.review import apply_assessments


def seal(row):
    row = deepcopy(row)
    row.pop("prediction_sha256", None)
    row["prediction_sha256"] = sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return row


def row(id="q1", strategy="bm25", recall=1, answerable=True, generation=False, **changes):
    value = {"id": id, "strategy": strategy, "repeat": 1,
             "question": "What is the Cedar budget?", "retrieval_question": "What is the Cedar budget?",
             "allowed_doc_ids": ["cedar"], "answerable": answerable, "category": "numeric",
             "retrieval": {key: recall for key in ("recall@5", "hit@5", "mrr@5", "ndcg@5", "precision@5", "evidence_coverage@5")},
             "latency_ms": 10, "retrieval_trace": {"retrieval_timing_ms": {"total": 2}},
             "error": None, "error_categories": []}
    if generation:
        value["generation"] = {"answer": "The Cedar budget is 120 dollars. [E1]", "status": "SUCCEEDED", "latency_ms": 8,
                               "usage": {"physical_calls": 0, "input_tokens": 0, "output_tokens": 0,
                                         "usage_complete": True, "cache_usage_complete": True,
                                         "cache_hit_input_tokens": 0, "cache_miss_input_tokens": 0,
                                         "missing_usage_attempts": 0}}
    value.update(changes)
    return seal(value)


def assessment(prediction, reviewer_kind="ai", answer_correctness=1.0):
    return {"id": prediction["id"], "strategy": prediction["strategy"], "repeat": prediction["repeat"],
            "prediction_sha256": prediction["prediction_sha256"], "reviewer_kind": reviewer_kind,
            "reviewer": "Explicit test reviewer", "answer_correctness": answer_correctness,
            "faithfulness": None, "citation_support": None, "fact_completeness": None,
            "notes": "The full response was compared against the cited source.", "review_status": "assessed"}


def test_failure_stays_in_retrieval_denominator_and_unanswerable_is_excluded():
    values = [row(), row(id="failed", retrieval={}, error="retrieval failed", error_categories=["execution_failure"]),
              row(id="no-answer", answerable=False, retrieval={})]
    result = aggregate(values)["bm25"]
    assert result["logical_questions"] == 3
    assert result["answerable_metric_denominator"] == 2
    assert result["failures"] == 1
    assert result["recall@5"] == .5
    assert result["semantic_answer_correctness"] is None


def test_missing_provider_usage_is_unknown_and_physical_attempts_still_count():
    value = row(generation=True)
    value["generation"]["usage"] = {"physical_calls": 2, "input_tokens": None, "output_tokens": None,
                                     "usage_complete": False, "cache_usage_complete": False,
                                     "cache_hit_input_tokens": None, "cache_miss_input_tokens": None,
                                     "missing_usage_attempts": 1}
    result = aggregate([value])["bm25"]
    assert result["physical_calls"] == 2
    assert result["input_tokens"] is None and result["output_tokens"] is None
    assert result["cache_hit_input_tokens"] is None and result["cache_miss_input_tokens"] is None
    assert result["missing_usage_attempts"] == 1
    assert result["money_usd"] is None


def test_known_token_usage_does_not_invent_cache_accounting():
    value = row(generation=True)
    value["generation"]["usage"].update(physical_calls=1, input_tokens=100, output_tokens=15,
                                         cache_usage_complete=False, cache_hit_input_tokens=None,
                                         cache_miss_input_tokens=None)
    result = aggregate([value])["bm25"]
    assert result["input_tokens"] == 100 and result["output_tokens"] == 15
    assert result["cache_hit_input_tokens"] is None and result["cache_miss_input_tokens"] is None


def test_missing_key_refusal_uses_condition_answerability_not_original_label():
    missing = row(generation=True, evidence_condition_answerable=False)
    missing["generation"]["status"] = "EMPTY_RESULT"
    result = aggregate([missing])["bm25"]
    assert result["unanswerable_refusal_recall"] == 1
    assert result["answerable_false_refusal_rate"] is None
    # The same EMPTY_RESULT is a false refusal with sufficient evidence.
    sufficient = row(generation=True, evidence_condition_answerable=True)
    sufficient["generation"]["status"] = "EMPTY_RESULT"
    result = aggregate([sufficient])["bm25"]
    assert result["unanswerable_refusal_recall"] is None
    assert result["answerable_false_refusal_rate"] == 1


def test_pairing_keeps_negative_effect_and_transition_counts():
    result = paired([row(), row(strategy="hybrid_rerank", recall=0)])["hybrid_rerank"]
    assert result["recall_at_5_delta"] == -1
    assert result["pass_to_fail"] == 1 and result["fail_to_pass"] == 0
    assert result["pairs"] == 1


def test_pairing_excludes_unanswerable_cases_but_keeps_execution_failures():
    values = [row(), row(strategy="hybrid_rerank", recall=0, error="failed", error_categories=["execution_failure"]),
              row(id="unanswerable", answerable=False),
              row(id="unanswerable", strategy="hybrid_rerank", answerable=False, recall=0)]
    result = paired(values)["hybrid_rerank"]
    assert result["pairs"] == 1 and result["pass_to_fail"] == 1


@pytest.mark.parametrize("values", [
    [row(), row(), row(strategy="hybrid")],
    [row(), row(id="different", strategy="hybrid")],
    [row(), row(strategy="hybrid", question="A different question")],
    [row(), row(strategy="hybrid", allowed_doc_ids=["another-source"])],
    [row(), row(strategy="hybrid", answerable=False)],
])
def test_pairing_rejects_duplicate_or_changed_comparison_objects(values):
    with pytest.raises(ValueError):
        paired(values)


def make_run(path, predictions, **changes):
    path.mkdir()
    manifest = {"dataset_sha256": "a" * 64, "top_k": 5, "candidate_k_per_channel": 20,
                "cache_protocol": "cold", "mode": "retrieval", "condition": "reference", "repeat": 1,
                "model": {"requested": None}, "answer_mode": "extractive", "code_sha256": {"metrics.py": "m", "retriever.py": "r"},
                "index": {"chunks_sha256": "c" * 64, "chunking": {"max_chars": 500, "overlap": 80},
                          "dense_embedding": {"enabled": True, "model_sha256": "d" * 64}}}
    manifest.update(changes)
    (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (path / "predictions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in predictions), encoding="utf-8")
    return path


def test_compare_runs_reports_loss_without_cherry_picking(tmp_path):
    before = make_run(tmp_path / "before", [row()])
    after = make_run(tmp_path / "after", [row(strategy="hybrid", recall=0)])
    result = compare_runs(before, after, after_strategy="hybrid")
    assert result["comparison"]["after"]["recall_at_5_delta"] == -1
    assert result["code_change_allowed"] is False


@pytest.mark.parametrize("change", [
    {"dataset_sha256": "changed"}, {"top_k": 10},
    {"candidate_k_per_channel": 30}, {"code_sha256": {"metrics.py": "changed"}},
    {"index": {"chunks_sha256": "different", "chunking": {}, "dense_embedding": {}}},
])
def test_compare_refuses_uncontrolled_experiment_changes(tmp_path, change):
    before = make_run(tmp_path / "before", [row()])
    after = make_run(tmp_path / "after", [row(strategy="hybrid")], **change)
    with pytest.raises(ValueError):
        compare_runs(before, after, after_strategy="hybrid")


def test_compare_refuses_changed_question_even_when_manifest_is_unchanged(tmp_path):
    before = make_run(tmp_path / "before", [row()])
    after = make_run(tmp_path / "after", [row(strategy="hybrid", retrieval_question="Different effective question")])
    with pytest.raises(ValueError, match="question/scope"):
        compare_runs(before, after, after_strategy="hybrid")


def test_wrong_prediction_hash_cannot_reuse_an_assessment():
    prediction = row(generation=True)
    review = assessment(prediction);review["prediction_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="hash"):
        apply_assessments([prediction], [review])


def test_changed_prediction_body_cannot_keep_old_hash_and_review():
    prediction = row(generation=True)
    review = assessment(prediction)
    prediction["generation"]["answer"] = "A different prediction under an old hash"
    with pytest.raises(ValueError, match="hash"):
        apply_assessments([prediction], [review])


def test_review_refuses_ambiguous_duplicate_prediction_keys():
    prediction = row(generation=True)
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        apply_assessments([prediction, deepcopy(prediction)], [assessment(prediction)])


def test_ai_and_human_reviews_are_separate_and_missing_metrics_remain_unknown():
    first, second = row(generation=True), row(id="q2", generation=True)
    result = apply_assessments([first, second], [assessment(first), assessment(second, "human", .5)])
    assert result["summary"]["ai"]["answer_correctness"] == {"mean": 1.0, "denominator": 1}
    assert result["summary"]["human"]["answer_correctness"] == {"mean": .5, "denominator": 1}
    assert result["summary"]["ai"]["faithfulness"] == {"mean": None, "denominator": 0}
    assert all(a["review_status"] == "assessed" for a in result["assessments"])


def test_empty_or_pending_assessments_are_not_zero_accuracy():
    prediction = row(generation=True)
    for reviews in ([], [{"id": prediction["id"], "strategy": "bm25", "repeat": 1,
                         "prediction_sha256": prediction["prediction_sha256"]}]):
        result = apply_assessments([prediction], reviews)
        for kind in ("ai", "human"):
            assert result["summary"][kind]["assessed_records"] == 0
            assert result["summary"][kind]["answer_correctness"] == {"mean": None, "denominator": 0}


def test_retrieval_only_cannot_be_reviewed_as_an_answer():
    prediction = row()
    with pytest.raises(ValueError, match="retrieval-only"):
        apply_assessments([prediction], [assessment(prediction)])
