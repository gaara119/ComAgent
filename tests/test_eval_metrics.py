from copy import deepcopy
from datetime import datetime
from decimal import Decimal

import pytest

from eval.dataset import load_dataset, require_run_permission, reviewed, review_hash
from eval.metrics import compare_results


def test_aliases_and_one_global_column_permutation_are_accepted():
    expected = [{"name": "a", "n": 2}, {"name": "b", "n": 3}]
    actual = [{"count_alias": 3, "label_alias": "b"}, {"count_alias": 2, "label_alias": "a"}]
    result = compare_results(expected, actual)
    assert result.matched
    assert result.column_mapping == (1, 0)


def test_per_row_column_sorting_is_not_a_valid_mapping():
    # Each row individually contains the same values, but the second row swaps
    # columns while the first does not. No consistent mapping makes these equal.
    assert not compare_results([[1, 2], [3, 4]], [[1, 2], [4, 3]]).matched


def test_matching_column_marginals_still_require_correct_row_relationships():
    expected = [[1, "a"], [1, "a"], [2, "b"], [2, "b"]]
    actual = [[1, "a"], [1, "b"], [2, "a"], [2, "b"]]
    assert not compare_results(expected, actual).matched


def test_multisets_keep_duplicate_rows():
    assert compare_results([[1], [1], [2]], [[2], [1], [1]]).matched
    assert not compare_results([[1], [1], [2]], [[2], [2], [1]]).matched


def test_ordered_comparison_preserves_row_order():
    assert compare_results([[1, "a"], [2, "b"]], [["a", 1], ["b", 2]], ordered=True).matched
    assert not compare_results([[1], [2]], [[2], [1]], ordered=True).matched


def test_empty_null_zero_and_empty_string_are_distinct():
    assert compare_results([], []).matched
    assert not compare_results([], [[0]]).matched
    assert not compare_results([[None]], [[0]]).matched
    assert not compare_results([[None]], [[""]]).matched
    assert not compare_results([[0]], [[False]]).matched
    assert compare_results([[None]], [[None]]).matched


def test_money_rounding_only_applies_to_declared_gold_columns():
    expected = [{"amount": Decimal("9.995"), "milliseconds": Decimal("12.345") }]
    actual = [{"duration": "12.345", "money": "10.00"}]
    assert compare_results(expected, actual, monetary_columns=["amount"]).matched
    assert not compare_results(expected, [{"duration": "12.35", "money": "10.00"}], monetary_columns=["amount"]).matched


def test_json_decimal_strings_require_numeric_schema_and_text_is_preserved():
    assert compare_results([["1.00"]], [[1]], numeric_columns=[0]).matched
    assert not compare_results([["001"]], [[1]]).matched
    assert not compare_results([[True]], [[1]]).matched


def test_timestamp_iso_serialization_is_normalized():
    expected = [[datetime(2021, 1, 1, 0, 0)]]
    assert compare_results(expected, [["2021-01-01 00:00:00"]]).matched
    assert not compare_results(expected, [["2021-01-02T00:00:00"]]).matched


def test_empty_tables_can_check_available_column_metadata():
    assert compare_results([], [], expected_columns=["a"], actual_columns=["alias"]).matched
    assert not compare_results([], [], expected_columns=["a"], actual_columns=["a", "b"]).matched


def _item(split="dev"):
    return {"id": "sql-test", "question": "题目", "gold_sql": "SELECT 1;",
            "gold_result": [{"n": 1}], "gold_columns": ["n"], "column_types": ["number"],
            "monetary_columns": [], "ordered": False, "split": split,
            "family_id": "test-family", "source_sha256": "hash",
            "gold_review": {"status": "needs_human_review"}}


def test_human_review_is_invalidated_when_gold_changes():
    item = _item()
    item["gold_review"] = {"status": "accepted", "reviewer": "A", "content_sha256": review_hash(item)}
    assert reviewed(item)
    changed = deepcopy(item)
    changed["gold_result"] = [{"n": 2}]
    assert not reviewed(changed)


def test_unreviewed_gold_requires_explicit_dev_only_exploration():
    items = [_item()]
    with pytest.raises(ValueError, match="人工接受"):
        require_run_permission(items)
    assert require_run_permission(items, draft_gold=True) == items


@pytest.mark.parametrize("kwargs", [
    {}, {"allow_holdout": True}, {"frozen_tag": "d5-frozen"},
    {"allow_holdout": True, "frozen_tag": "d5-frozen", "draft_gold": True},
])
def test_holdout_cannot_be_run_by_default_or_with_draft_gold(kwargs):
    with pytest.raises(ValueError):
        require_run_permission([_item("holdout")], split="holdout", **kwargs)


def test_reviewed_holdout_requires_explicit_flag_and_tag():
    item = _item("holdout")
    item["gold_review"] = {"status": "accepted", "reviewer": "A", "content_sha256": review_hash(item)}
    assert require_run_permission([item], split="holdout", allow_holdout=True, frozen_tag="d5-frozen") == [item]


def test_same_family_cannot_leak_between_splits(tmp_path):
    import json
    first = _item()
    second = _item("holdout")
    second["id"] = "sql-test-two"
    path = tmp_path / "dataset.jsonl"
    path.write_text(json.dumps(first) + "\n" + json.dumps(second), encoding="utf-8")
    with pytest.raises(ValueError, match="同源题"):
        load_dataset(path)


def test_no_key_creates_readiness_report_without_predictions_or_accuracy(tmp_path, monkeypatch):
    import argparse
    import json
    import eval.run_eval as runner
    from types import SimpleNamespace

    path = tmp_path / "dataset.jsonl"
    path.write_text(json.dumps(_item(), ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(runner, "get_settings", lambda: SimpleNamespace(
        llm_configured=False, llm_model="test-model", llm_api_key="", db_url=""))
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url):
            class Response:
                def raise_for_status(self):
                    pass

                def json(self):
                    return {"llm_configured": False}
            return Response()

        def post(self, *args, **kwargs):
            calls.append(args)
            raise AssertionError("readiness must not predict")

    monkeypatch.setattr(runner.httpx, "Client", FakeClient)
    args = argparse.Namespace(dataset=path, split="dev", draft_gold=True, allow_holdout=False,
                              frozen_tag=None, output=tmp_path / "report", base_url="http://127.0.0.1:8000", timeout=10)
    report, directory = runner.evaluate(args)
    assert report["status"] == "READINESS_ONLY"
    assert report["prediction_count"] == 0
    assert "ex" not in report and "exploratory_ex" not in report
    assert calls == []
    assert (directory / "report.json").exists()
    assert not (directory / "responses.jsonl").exists()


def test_runner_sends_only_dev_questions_and_preserves_real_api_output(tmp_path, monkeypatch):
    import argparse
    import json
    import eval.run_eval as runner
    from types import SimpleNamespace

    dev = _item()
    dev["category"] = "count"
    dev["gold_review"] = {"status": "accepted", "reviewer": "A", "content_sha256": review_hash(dev)}
    holdout = _item("holdout")
    holdout.update(id="holdout-test", family_id="holdout-family", question="禁止发送的保留题")
    path = tmp_path / "dataset.jsonl"
    path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in [dev, holdout]), encoding="utf-8")
    monkeypatch.setattr(runner, "get_settings", lambda: SimpleNamespace(
        llm_configured=True, llm_model="fixture-model", llm_api_key="fixture", db_url=""))
    requests = []

    class Response:
        def __init__(self, body):
            self.body = body
            self.status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return self.body

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, url):
            return Response({"llm_configured": True, "db_ready": True})

        def post(self, url, json):
            requests.append(json)
            return Response({"trace_id": "fixture-trace", "status": "SUCCEEDED", "answer": "1",
                             "sql": "SELECT 1 AS alias;", "table": [{"alias": 1}],
                             "steps": [{"name": "execute", "latency_ms": 2}],
                             "metadata": {"model": "fixture-response-model", "result_columns": ["alias"]}})

    monkeypatch.setattr(runner.httpx, "Client", FakeClient)
    args = argparse.Namespace(dataset=path, split="dev", draft_gold=False, allow_holdout=False,
                              frozen_tag=None, output=tmp_path / "report", base_url="http://127.0.0.1:8000", timeout=10)
    report, directory = runner.evaluate(args)
    assert len(requests) == 1 and requests[0]["message"] == dev["question"]
    assert "gold_sql" not in requests[0] and "gold_result" not in requests[0]
    assert report["selected_count"] == 1 and report["correct"] == 1 and report["ex"] == 1.0
    assert report["holdout_prediction_count"] == 0
    saved = json.loads((directory / "responses.jsonl").read_text(encoding="utf-8"))
    assert saved["response"]["trace_id"] == "fixture-trace"
    assert saved["response"]["steps"][0]["latency_ms"] == 2
    assert report["provenance"]["actual_models"] == ["fixture-response-model"]


def test_frozen_tag_must_point_at_current_head_and_have_clean_source(monkeypatch):
    import eval.run_eval as runner

    monkeypatch.setattr(runner, "_git", lambda *args: "tagged" if args[0] == "rev-parse" and "--verify" in args else "head")
    with pytest.raises(ValueError, match="HEAD"):
        runner.validate_frozen_tag("d5-frozen")
    monkeypatch.setattr(runner, "_git", lambda *args: " M qa_agent/config.py" if args[0] == "status" else "same-commit")
    with pytest.raises(ValueError, match="干净"):
        runner.validate_frozen_tag("d5-frozen")
