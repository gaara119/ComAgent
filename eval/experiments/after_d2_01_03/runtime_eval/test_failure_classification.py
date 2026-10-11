"""Fabricated saved-evidence tests: no models, API requests or database queries."""
from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import HERE, digest, load_cases, write_new
from classify_failures import classify_case, main, review_entries, turn_evidence


def fixture():
    case = {"id": "fixture", "task": "03", "category": "L2", "input": "真实用户原文",
            "gold_sql": "SELECT COUNT(*) FROM public.customer", "expected_final_intent": {"metric": "customer_count"}}
    score = {"automatic_complete": False, "scorable": True, "query": {"semantic_preservation": {}, "result": {}},
             "binding_correctness": {}, "post_completion": []}
    ref = {"path": "fixture-saved-score.json", "exists": False}
    return case, score, ref


def evidence(error=None, status="FAILED"):
    ref = {"path": "fixture-saved-response.raw.json", "exists": False}
    return [{"index": 0, "phase": "initial", "error": error, "status": status, "transport_error": None,
             "failed_steps": [], "provider_records": [], "integrity_notes": [], "api_response": ref,
             "provider_manifest": ref, "_response": {"status": status}}]


class FailureClassificationChecks(unittest.TestCase):
    def test_failed_status_alone_does_not_invent_model_or_env_cause(self):
        case, score, ref = fixture()
        result = classify_case(case, score, {"outcome": "api_failed"}, evidence(), ref)
        self.assertEqual({item["category"] for item in result["findings"]}, {"annotation_scoring"})
        self.assertTrue(all(item["root_cause_confirmed"] is False for item in result["findings"]))

    def test_actual_format_error_locates_observed_boundary(self):
        case, score, ref = fixture()
        result = classify_case(case, score, {}, evidence({"code": "llm_format"}), ref)
        found = [item for item in result["findings"] if item["category"] == "model"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["certainty"], "observed_failure_boundary")
        self.assertFalse(found[0]["root_cause_confirmed"])

    def test_semantic_pending_preserved_even_if_actual_result_equal(self):
        case, score, ref = fixture()
        score["automatic_complete"] = None
        score["query"] = {"semantic_preservation": {"status": "AI_pending", "correct": None, "reason": "AST differs"},
                          "result": {"correct": True}}
        turn = {**evidence(status="SUCCEEDED")[0], "actual_sql": "SELECT COUNT(customer_id) FROM public.customer", "trace_id": "fixture-trace"}
        result = classify_case(case, score, {}, [turn], ref)
        reviews = review_entries(case, score, [turn], ref)
        self.assertIsNone(result["automatic_complete_unchanged"])
        self.assertEqual(reviews[0]["status"], "AI_pending")
        self.assertIsNone(reviews[0]["review_verdict"])
        self.assertEqual(reviews[0]["actual_trace_id"], "fixture-trace")

    def test_pending_label_never_gets_binary_correctness(self):
        case, score, ref = fixture()
        score.update(scorable=False, automatic_complete=None)
        result = classify_case(case, score, {}, [], ref)
        self.assertIsNone(result["automatic_complete_unchanged"])
        self.assertTrue(any(item["category"] == "annotation_scoring" for item in result["findings"]))

    def test_raw_response_and_provider_file_are_concretely_indexed(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            case_dir = Path(directory)
            turn_dir = case_dir / "turns/000"
            response = {"trace_id": "fixture-trace", "status": "FAILED", "error": {"code": "llm_format"}, "steps": []}
            write_new(turn_dir / "request.json", {"index": 0, "phase": "initial", "request": {"message": "原文"}})
            write_new(turn_dir / "response.raw.json", {"http_status": 200, "body": json.dumps(response)})
            capture = turn_dir / "provider/fixture.json"
            write_new(capture, {"trace_id": "fixture-trace", "request": {"model": "fixture"}, "response": {"choices": []}, "validation_error": "ValidationError"})
            write_new(turn_dir / "provider-evidence.json", {"records": [{"step": 2, "status": "archived", "copy": "provider/fixture.json", "copy_sha256": digest(capture)}]})
            result = turn_evidence(case_dir, {"index": 0, "phase": "initial", "response": response})
            self.assertTrue(result["api_response"]["exists"])
            self.assertTrue(result["provider_records"][0]["copy"]["exists"])
            self.assertTrue(result["provider_records"][0]["copy_hash_matches_archive"])
            self.assertTrue(result["provider_records"][0]["trace_matches_response"])
            self.assertEqual(result["provider_records"][0]["validation_error"], "ValidationError")

    def test_evidence_path_cannot_escape_case_dir(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            with self.assertRaises(ValueError):
                turn_evidence(Path(directory), {"index": 0, "response_raw_file": "../../../outside.json"})

    def test_cli_indexes_all_sixty_without_predicting_or_rescoring(self):
        labels = HERE.parent / "data/cases-v6-reviewed.jsonl"
        cases = load_cases(labels)
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            base = Path(directory)
            run = base / "fabricated-run"
            run.mkdir()
            write_new(run / "run-manifest.json", {"labels_sha256": digest(labels), "fixture_only": True})
            scores = base / "fabricated-scores.json"
            records = [{"id": item["id"], "task": item["task"], "category": item["category"], "scorable": item["scorable"],
                        "automatic_complete": None, "query": {}, "post_completion": [], "binding_correctness": {}} for item in cases]
            write_new(scores, {"labels_sha256": digest(labels), "version": "offline-fabricated-fixture", "cases": records})
            original_hash = digest(scores)
            output = base / "classification"
            with patch.object(sys, "argv", ["classify_failures.py", "--cases", str(labels), "--scores", str(scores),
                                             "--run-dir", str(run), "--output-dir", str(output)]), redirect_stdout(StringIO()):
                main()
            result = json.loads((output / "failure-classification.json").read_text(encoding="utf-8"))
            self.assertEqual(result["total_cases"], 60)
            self.assertEqual(result["scorable_cases"], 49)
            self.assertEqual(result["pending_annotation_cases"], 11)
            self.assertEqual(result["qa_API_calls"], 0)
            self.assertEqual(result["model_calls"], 0)
            self.assertEqual(result["DB_queries"], 0)
            self.assertEqual(digest(scores), original_hash)
            self.assertEqual(len((output / "pending-label-review.jsonl").read_text(encoding="utf-8").splitlines()), 11)


if __name__ == "__main__":
    unittest.main(verbosity=2)
