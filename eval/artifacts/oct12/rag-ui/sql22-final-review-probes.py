"""Isolated date candidate review with accumulated independent regressions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from qa_agent.clarify import extractor
from qa_agent.clarify.rules import SemanticIntent
from qa_agent.sql.catalog import load_catalog

parser = argparse.ArgumentParser()
parser.add_argument("--candidate", required=True)
args = parser.parse_args()
candidate_path = (ROOT / args.candidate).resolve()
if candidate_path.parent != (ROOT / "notes/oct12/staging/sql22").resolve():
    raise ValueError("Review candidate must be in the isolated SQL22 staging directory")
candidate_bytes = candidate_path.read_bytes()
candidate = ModuleType("sql22_final_independent_review")
candidate.__file__ = str(candidate_path)
sys.modules[candidate.__name__] = candidate
exec(compile(candidate_bytes, str(candidate_path), "exec"), candidate.__dict__)

prior = json.loads((ROOT / "notes/oct12/staging/sql22/ai-review-v3-pass-2-probes.json").read_text(encoding="utf-8"))
day = json.loads((ROOT / "notes/oct12/staging/sql22/ai-review-v3-day-scope-probes.json").read_text(encoding="utf-8"))
cases = [(row["question"], row["expected"]) for row in prior["probes"] if "question" in row and "expected" in row]
cases += [(row["question"], row["expected"]) for row in day["probes"]]
cases += [
    ("2004年1月1日之前未支付的发票。", {"end": "2004-01-01", "grain": "before"}),
    ("未支付且早于2004年1月1日的发票。", {"end": "2004-01-01", "grain": "before"}),
]
rows = []
for question, expected in cases:
    actual = candidate.explicit_period(question)
    normalized = ({k: v for k, v in actual["current"].items() if k != "label"} if actual else None)
    rows.append({"question": question, "expected": expected, "actual": actual, "pass": normalized == expected})

diagnosis = json.loads((ROOT / "eval/artifacts/oct12/sql22-diagnosis-004/readonly-diagnosis.json").read_text(encoding="utf-8"))
extractor.explicit_period = candidate.explicit_period


class ReplayModel:
    def complete_json(self, *args, **kwargs):
        return SemanticIntent.model_validate(diagnosis["actual_provider_semantic"])


replayed = extractor.extract_intent(diagnosis["gold_question"], load_catalog(ROOT / "data/catalog/chinook.yaml"), ReplayModel())
decision = candidate.RuleEngine(ROOT / "qa_agent/clarify/clarify_rules.yaml").evaluate(diagnosis["gold_question"], replayed)
current = replayed.time_scope["current"]
rows.append({"id": "actual_provider_response_local_replay", "actual_intent": replayed.model_dump(mode="json"),
             "decision": decision.as_dict(), "pass": current["end"] == "2004-01-01" and current["grain"] == "before" and
             "start" not in current and decision.level == "L0" and not decision.issues})
scope = candidate.explicit_period("2004年1月1日之前销售额同比增长多少？")
growth = candidate.RuleEngine(ROOT / "qa_agent/clarify/clarify_rules.yaml").evaluate(
    "2004年1月1日之前销售额同比增长多少？",
    candidate.SemanticIntent(task_type="growth", metric="invoice_revenue", time_scope=scope, comparison={"type": "yoy"}))
rows.append({"id": "open_before_does_not_invent_growth_base", "decision": growth.as_dict(),
             "pass": growth.level == "L2" and any(issue.field == "time_scope.base" for issue in growth.issues)
                     and not (growth.analysis.time_scope or {}).get("base")})
passed = all(row["pass"] for row in rows)
unchanged = candidate_bytes == candidate_path.read_bytes()
report = {"state": "PASS" if passed and unchanged else "AI发现错误", "passed": passed and unchanged,
          "candidate_path": args.candidate, "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
          "source_unchanged_during_probe": unchanged, "checks": len(rows), "passed_count": sum(row["pass"] for row in rows),
          "kind": "actual local date parser and archived-provider replay; not a system prediction",
          "fixture_complete_json_calls": 1, "real_model_requests": 0, "database_executions": 0,
          "holdout_predictions": 0, "business_files_modified": False, "human_approval": False, "probes": rows}
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["passed"] else 1)
