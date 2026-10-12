"""Independent review of the frozen literal-before candidate; fixtures only."""
from __future__ import annotations

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

candidate_path = ROOT / "notes/oct12/staging/sql22/rules_candidate-v3.py"
candidate_bytes = candidate_path.read_bytes()
candidate = ModuleType("sql22_v3_independent_review")
candidate.__file__ = str(candidate_path)
sys.modules[candidate.__name__] = candidate
exec(compile(candidate_bytes, str(candidate_path), "exec"), candidate.__dict__)
cases = [
    ("列出 2004 年 1 月 1 日之前入职的员工。", {"end": "2004-01-01", "grain": "before"}),
    ("2004-01-01之前入职。", {"end": "2004-01-01", "grain": "before"}),
    ("未早于2004年1月1日入职。", None),
    ("并非早于2004年1月1日入职。", None),
    ("不是早于2004年1月1日入职。", None),
    ("早于2004年1月1日12:00:00入职。", None),
    ("2004-01-01T12:00:00之前入职。", None),
    ("2004年1月1日之前（含该日）入职。", None),
    ("早于2004年1月1日中午12点入职。", None),
    ("早于2004-01-01T00:00:00+08:00入职。", None),
    ("早于2004年1月123日入职。", None),
    ("2004年123月1日之前入职。", None),
    ("2004 年 2 月入职。", {"start": "2004-02-01", "end": "2004-03-01", "grain": "month"}),
    ("2003年12月1日到2004年1月1日入职。", {"start": "2003-12-01", "end": "2004-01-02", "grain": "custom"}),
    ("2004年2月29日入职。", {"start": "2004-02-29", "end": "2004-03-01", "grain": "custom"}),
]
rows = []
for question, expected in cases:
    actual = candidate.explicit_period(question)
    normalized = ({k: v for k, v in actual["current"].items() if k != "label"} if actual else None)
    rows.append({"question": question, "expected": expected, "actual": actual,
                 "pass": normalized == expected})

diagnosis = json.loads((ROOT / "eval/artifacts/oct12/sql22-diagnosis-004/readonly-diagnosis.json").read_text(encoding="utf-8"))
extractor.explicit_period = candidate.explicit_period


class ReplayModel:
    def complete_json(self, *args, **kwargs):
        return SemanticIntent.model_validate(diagnosis["actual_provider_semantic"])


replayed = extractor.extract_intent(diagnosis["gold_question"], load_catalog(ROOT / "data/catalog/chinook.yaml"), ReplayModel())
decision = candidate.RuleEngine(ROOT / "qa_agent/clarify/clarify_rules.yaml").evaluate(diagnosis["gold_question"], replayed)
current = replayed.time_scope["current"]
rows.append({"id": "actual_provider_response_local_replay",
             "actual_intent": replayed.model_dump(mode="json"), "decision": decision.as_dict(),
             "pass": current["end"] == "2004-01-01" and current["grain"] == "before" and
                     "start" not in current and decision.level == "L0" and not decision.issues})
scope = candidate.explicit_period("2004年1月1日之前销售额同比增长多少？")
growth = candidate.RuleEngine(ROOT / "qa_agent/clarify/clarify_rules.yaml").evaluate(
    "2004年1月1日之前销售额同比增长多少？",
    candidate.SemanticIntent(task_type="growth", metric="invoice_revenue", time_scope=scope, comparison={"type": "yoy"}))
rows.append({"id": "open_before_does_not_invent_growth_base", "decision": growth.as_dict(),
             "pass": growth.level == "L2" and any(issue.field == "time_scope.base" for issue in growth.issues)
                     and not (growth.analysis.time_scope or {}).get("base")})
report = {"state": "PASS" if all(row["pass"] for row in rows) else "AI发现错误",
          "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
          "source_unchanged_during_probe": candidate_bytes == candidate_path.read_bytes(),
          "checks": len(rows), "passed": sum(row["pass"] for row in rows),
          "kind": "Actual local parser and archived-provider fixture replay; not a new system prediction",
          "fixture_complete_json_calls": 1, "real_model_requests": 0, "database_executions": 0,
          "holdout_predictions": 0, "business_files_modified": False, "probes": rows}
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["state"] == "PASS" else 1)
