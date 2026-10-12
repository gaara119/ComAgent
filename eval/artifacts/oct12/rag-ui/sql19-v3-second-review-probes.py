"""Independent staged v3 proof; fixture only, no measured system call."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from qa_agent.clarify.rules import SemanticIntent, RuleEngine
from qa_agent.sql.catalog import load_catalog

candidate_path = ROOT / "notes/oct12/staging/sql19/extractor_candidate-v3.py"
spec = importlib.util.spec_from_file_location("sql19_v3_independent_review", candidate_path)
candidate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)
candidate.PROMPT_PATH = ROOT / "qa_agent/clarify/prompts/intent_extract.txt"


class ReviewModel:
    def __init__(self, intent):
        self.intent = intent

    def complete_json(self, *args, **kwargs):
        return self.intent.model_copy(deep=True)


catalog = load_catalog(ROOT / "data/catalog/chinook.yaml")
question = "按姓氏降序取前5位客户，返回编号、名字和姓氏；姓氏相同时按客户编号升序。"
good = {"field": "last_name", "direction": "desc", "tie_breaker": {"field": "customer_id", "direction": "asc"}}
cases = [
    ("pure_fields_and_tie", question, "customer", 5, good, "lookup"),
    ("missing_model_n", question, "customer", None, good, "ranking"),
    ("wrong_model_n", question, "customer", 7, good, "ranking"),
    ("missing_model_order", question, "customer", 5, None, "ranking"),
    ("empty_model_order", question, "customer", 5, {}, "ranking"),
    ("wrong_model_primary_field", question, "customer", 5, {"field": "first_name", "direction": "desc"}, "ranking"),
    ("wrong_model_direction", question, "customer", 5, {"field": "last_name", "direction": "asc"}, "ranking"),
    ("other_rank_object", question, "artist", 5, good, "ranking"),
    ("business_revenue_clause", "按姓氏降序取前5位客户，统计营收总和。", "customer", 5, good, "ranking"),
    ("business_english_clause", "按姓氏降序取前5位客户，按 revenue 再排名。", "customer", 5, good, "ranking"),
    ("business_expense_suffix", "按姓氏降序取前5位客户的支出。", "customer", 5, good, "ranking"),
    ("qualified_real_primary", question, "客户", 5, {"field": "customer.last_name", "direction": "DESC"}, "lookup"),
]
rows = []
for name, text, owner, n, order, expected in cases:
    original = SemanticIntent(task_type="ranking", metric=None, rank_object=owner, top_n=n, order=order)
    result = candidate.extract_intent(text, catalog, ReviewModel(original))
    decision = RuleEngine().evaluate(text, result)
    unchanged = result.top_n == original.top_n and result.order == original.order and result.metric is None
    rows.append({"id": name, "question": text, "fixture_intent": original.model_dump(mode="json"),
                 "expected_task": expected, "actual_task": result.task_type,
                 "explicit_n_order_metric_preserved": unchanged,
                 "pass": result.task_type == expected and unchanged,
                 "decision_level": decision.level,
                 "issues": [asdict(issue) for issue in decision.issues]})

report = {"state": "PASS" if all(row["pass"] for row in rows) else "FAIL",
          "candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
          "purpose": "AI独立第二审核第三候选；实际本地fixture结果，不是provider/system成绩",
          "checks": len(rows), "model_requests": 0, "holdout_predictions": 0,
          "business_files_modified": False, "probes": rows}
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["state"] == "PASS" else 1)
