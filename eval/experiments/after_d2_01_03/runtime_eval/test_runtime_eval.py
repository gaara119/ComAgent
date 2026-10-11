"""Safety and scorer checks with fabricated fixtures only; zero system predictions."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from common import HERE, request_payload, write_new
from controller import next_answer
from runner import recover_case, run_case
from scorer import aggregate, case_score, score_query, semantic_check, sql_contract

SCOPE = {"route": "sql", "db_id": "chinook", "doc_ids": []}


def card(keys, version=1, ident=None):
    issues = [{"id": "missing:" + key, "field": key, "options": []} for key in keys]
    return {"status": "NEEDS_CLARIFICATION", "intent": {"intent_version": version, "filters": []},
            "clarification": {"clarification_id": ident or "card-" + str(version), "intent_version": version,
                              "resume_supported": True, "issues": issues, "options": []}, "steps": []}


def base_case():
    return {"id": "fixture", "input": "查某年指标", "scope": SCOPE, "history": [], "task": "03", "category": "L2",
            "scorable": True, "controller": {"allowed_user_supplements": {
                "metric": {"answer": "销售额。", "value": {"metric": "sales_revenue"}},
                "year": {"answer": "2024年。", "value": {"year": 2024}}}, "max_clarification_followups": 3}}


class FakeResponse:
    status_code = 200
    headers = {"content-type": "application/json"}

    def __init__(self, body):
        self.text = json.dumps(body)


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def post(self, url, json):
        self.requests.append(copy.deepcopy(json))
        if not self.responses:
            raise AssertionError("Unexpected duplicate API trigger")
        return FakeResponse(self.responses.pop(0))


class RuntimeEvalChecks(unittest.TestCase):
    def test_no_label_keys_in_actual_request(self):
        payload = request_payload("fixture-session", "真实用户问题", SCOPE)
        self.assertEqual(set(payload), {"session_id", "message", "scope"})

    def test_only_one_asked_key_per_turn(self):
        answer = next_answer(base_case(), card(["metric", "time_scope.current"]), "fixture-session", [], None)
        self.assertEqual(answer.asked_key, "metric")
        self.assertEqual(answer.request["message"], "销售额。")
        self.assertNotIn("2024", json.dumps(answer.request))

    def test_unknown_ask_is_unanswered(self):
        answer = next_answer(base_case(), card(["unimplemented_fancy_field"]), "fixture-session", [], None)
        self.assertEqual(answer.outcome, "controller_unanswered")

    def test_stale_card_is_not_reused(self):
        self.assertEqual(next_answer(base_case(), card(["metric"], 1), "session", [], 1).outcome, "controller_unanswered")
        self.assertEqual(next_answer(base_case(), card(["metric"], 2, "old"), "session", [], 1, ["old"]).outcome, "controller_unanswered")

    def test_candidate_column_not_forced(self):
        case = base_case()
        case["controller"]["allowed_user_supplements"] = {"value": {"answer": "USA。", "value": "USA"}}
        response = card(["filters"])
        response["clarification"]["issues"][0]["options"] = [
            {"id": "one", "label": "USA（customer.country）", "patch": {"column": "customer.country", "value": "USA"}},
            {"id": "two", "label": "USA（invoice.billing_country）", "patch": {"column": "invoice.billing_country", "value": "USA"}}]
        self.assertEqual(next_answer(case, response, "session", [], None).outcome, "controller_unanswered")
        case["controller"]["allowed_user_supplements"]["value"]["value"] = {"column": "customer.country", "value": "USA"}
        answer = next_answer(case, response, "session", [], None)
        self.assertEqual(answer.request["choice_id"], "one")
        self.assertEqual(answer.request["message"], "USA（customer.country）")

    def test_bundled_missing_conditions_are_rejected(self):
        case = base_case()
        case["controller"]["allowed_user_supplements"] = {"rank_object": {"answer": "客户，按销售额。", "value": {"object": "customer", "metric": "sales_revenue"}}}
        self.assertEqual(next_answer(case, card(["rank_object", "metric"]), "session", [], None).outcome, "controller_unanswered")

    def test_actual_multi_turn_requests_and_resume_do_not_repost(self):
        case = base_case()
        completed = {"status": "SUCCEEDED", "intent": {"intent_version": 3}, "table": [{"revenue": 5}], "steps": []}
        client = FakeClient([card(["metric", "time_scope.current"], 1), card(["time_scope.current"], 2), completed])
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory)
            result = run_case(client, "http://offline.invalid", case, path, "fixture")
            self.assertEqual(result["outcome"], "finished")
            self.assertEqual(len(client.requests), 3)
            self.assertEqual([item["message"] for item in client.requests], [case["input"], "销售额。", "2024年。"])
            restored = run_case(client, "http://offline.invalid", case, path, "fixture")
            self.assertEqual(restored["outcome"], "finished")
            self.assertEqual(len(client.requests), 3)

    def test_saved_raw_response_recovers_without_repost(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory)
            write_new(path / "turns/000/request.json", {"index": 0, "phase": "initial", "request": {"message": "old"}})
            write_new(path / "turns/000/response.raw.json", {"http_status": 200, "body": json.dumps(card(["metric"])), "latency_ms": 4})
            state = recover_case(path, {"turns": [], "outcome": "running"})
            self.assertEqual(len(state["turns"]), 1)
            self.assertEqual(state["turns"][0]["response"]["status"], "NEEDS_CLARIFICATION")

    def test_unconfirmed_delivery_blocks_automatic_replay(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory)
            write_new(path / "turns/000/request.json", {"index": 0, "phase": "initial", "request": {"message": "old"}})
            state = recover_case(path, {"turns": [], "outcome": "running"})
            self.assertEqual(state["outcome"], "ambiguous_delivery")

    def test_equal_results_do_not_prove_country_scope(self):
        gold = "SELECT SUM(i.total) FROM public.invoice i JOIN public.customer c ON i.customer_id=c.customer_id WHERE c.country='USA'"
        wrong = "SELECT SUM(i.total) FROM public.invoice i JOIN public.customer c ON i.customer_id=c.customer_id WHERE i.billing_country='USA'"
        result = semantic_check(gold, {"sql": wrong, "metadata": {}, "table": [{"revenue": 10}]}, {"row_count": 1})
        self.assertIsNone(result["correct"])
        self.assertEqual(result["status"], "AI_pending")
        self.assertFalse(result["predicate_match"])

    def test_qualified_sql_alias_equivalence_is_proven(self):
        gold = "SELECT SUM(i.total) AS revenue FROM public.invoice i WHERE i.billing_country='France'"
        actual = "SELECT SUM(total) AS amount FROM public.invoice WHERE billing_country='France'"
        result = semantic_check(gold, {"sql": actual, "metadata": {}}, {"row_count": 1})
        self.assertIs(result["correct"], True, result)

    def test_pending_labels_keep_total_and_have_no_binary_score(self):
        case = base_case()
        case["scorable"] = False
        scored = case_score(case, {"turns": [], "outcome": "api_failed"})
        self.assertIsNone(scored["automatic_complete"])
        result = aggregate([scored], [{"turns": []}])
        self.assertEqual(result["groups"]["all"]["total_tasks"], 1)
        self.assertEqual(result["groups"]["all"]["pending_annotation"], 1)

    def test_missing_post_gold_result_does_not_fall_back_to_main(self):
        case = base_case()
        case["gold_sql"] = "SELECT COUNT(*) FROM public.customer"
        case["gold_result"] = {"columns": ["n"], "rows": [[59]], "row_count": 1}
        actual = {"status": "SUCCEEDED", "sql": case["gold_sql"], "table": [{"n": 59}], "metadata": {}}
        result = score_query(case, actual, gold_sql=case["gold_sql"], gold_result=None)
        self.assertIsNone(result["result"]["correct"])
        self.assertIsNone(result["complete"])

    def test_clarification_three_turn_cap_and_no_hidden_post(self):
        case = base_case()
        case["controller"]["allowed_user_supplements"].update({"numerator": {"answer": "法国客户。", "value": "France"},
                                                            "denominator": {"answer": "同期全库。", "value": "all"}})
        case["controller"]["post_completion_turns"] = [{"message": "不应提交隐藏修改"}]
        client = FakeClient([card(["metric"], 1), card(["time_scope.current"], 2), card(["numerator"], 3), card(["denominator"], 4)])
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            result = run_case(client, "http://offline.invalid", case, Path(directory), "fixture")
        self.assertEqual(result["outcome"], "clarification_limit")
        self.assertEqual(result["clarification_count"], 3)
        self.assertEqual(len(client.requests), 4)
        self.assertNotIn("不应提交隐藏修改", [item["message"] for item in client.requests])

    def test_real_history_is_executed_before_target(self):
        case = base_case()
        case["history"] = [{"role": "user", "content": "原先的真实用户查询"}]
        successful = {"status": "SUCCEEDED", "steps": []}
        client = FakeClient([successful, successful])
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            result = run_case(client, "http://offline.invalid", case, Path(directory), "fixture")
        self.assertEqual(result["outcome"], "finished")
        self.assertEqual([item["message"] for item in client.requests], ["原先的真实用户查询", case["input"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
