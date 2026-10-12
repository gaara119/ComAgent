"""Independent review probes; staged module only, no system or model calls."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from qa_agent.clarify.rules import SemanticIntent, RuleEngine
from qa_agent.sql.catalog import load_catalog

candidate_path = ROOT / "notes/oct12/staging/sql19/extractor_candidate.py"
spec = importlib.util.spec_from_file_location("sql19_independent_review", candidate_path)
candidate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = candidate
spec.loader.exec_module(candidate)
candidate.PROMPT_PATH = ROOT / "qa_agent/clarify/prompts/intent_extract.txt"


class ReviewModel:
    """A declared fixture, never a provider response."""
    def complete_json(self, *args, **kwargs):
        return SemanticIntent(task_type="ranking", metric=None, rank_object="customer", top_n=5,
                              order={"field": "last_name", "direction": "desc"})


catalog = load_catalog(ROOT / "data/catalog/chinook.yaml")
questions = [
    "按姓氏降序取前5位客户，返回编号、名字和姓氏。",
    "按姓氏降序取前5位客户，统计营收总和。",
    "按姓氏降序取前5位客户，按 revenue 再排名。",
    "按姓氏降序取前5位客户的支出。",
]
rows = []
for question in questions:
    semantic = candidate.extract_intent(question, catalog, ReviewModel())
    decision = RuleEngine().evaluate(question, semantic)
    rows.append({
        "question": question,
        "attribute_rule_matches": candidate.explicit_customer_attribute_top(question, catalog),
        "fixture_intent_before": {"task_type": "ranking", "metric": None, "rank_object": "customer"},
        "intent_after": semantic.model_dump(mode="json"),
        "decision_level": decision.level,
        "issues": [item.model_dump(mode="json") for item in decision.issues],
    })

report = {
    "state": "ACTUAL_LOCAL_PROBE",
    "candidate_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    "purpose": "AI独立第二审核；纯模型fixture验证是否误绕过指标缺口，不能计作真实模型成绩",
    "model_requests": 0,
    "holdout_predictions": 0,
    "business_files_modified": False,
    "probes": rows,
}
print(json.dumps(report, ensure_ascii=False, indent=2))
