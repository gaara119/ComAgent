"""Independent regression of review counterexamples against staged v2 only."""
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

candidate_path = ROOT / "notes/oct12/staging/sql19/extractor_candidate-v2.py"
spec = importlib.util.spec_from_file_location("sql19_v2_independent_review", candidate_path)
candidate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)
candidate.PROMPT_PATH = ROOT / "qa_agent/clarify/prompts/intent_extract.txt"


class ReviewModel:
    """Declared intent fixture, not a provider answer."""
    def __init__(self, rank_object="customer"):
        self.rank_object = rank_object

    def complete_json(self, *args, **kwargs):
        return SemanticIntent(task_type="ranking", metric=None, rank_object=self.rank_object, top_n=5,
                              order={"field": "last_name", "direction": "desc"})


catalog = load_catalog(ROOT / "data/catalog/chinook.yaml")
cases = [
    ("按姓氏降序取前5位客户，返回编号、名字和姓氏。", "customer", "lookup"),
    ("按姓氏降序取前5位客户，统计营收总和。", "customer", "ranking"),
    ("按姓氏降序取前5位客户，按 revenue 再排名。", "customer", "ranking"),
    ("按姓氏降序取前5位客户的支出。", "customer", "ranking"),
    ("按姓氏降序取前5位客户。", "artist", "ranking"),
    ("按姓氏降序取前5位客户，返回编号、未知字段。", "customer", "ranking"),
    ("按姓氏降序取前5位客户，返回编号；姓氏相同时按客户编号升序。", "客户", "lookup"),
]
rows = []
for question, rank_object, expected in cases:
    semantic = candidate.extract_intent(question, catalog, ReviewModel(rank_object))
    decision = RuleEngine().evaluate(question, semantic)
    rows.append({"question": question, "fixture_rank_object": rank_object,
                 "expected_task": expected, "actual_task": semantic.task_type,
                 "pass": semantic.task_type == expected,
                 "intent_after": semantic.model_dump(mode="json"),
                 "decision_level": decision.level,
                 "issues": [asdict(issue) for issue in decision.issues]})

report = {"state": "PASS" if all(row["pass"] for row in rows) else "FAIL",
          "candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
          "purpose": "AI第二审核新候选独立实际fixture探针；不代表真实模型成绩",
          "checks": len(rows), "model_requests": 0, "holdout_predictions": 0,
          "business_files_modified": False, "probes": rows}
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["state"] == "PASS" else 1)
