"""Check preservation of day filters with unrelated business predicates."""
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
path = ROOT / "notes/oct12/staging/sql22/rules_candidate-v3.py"
source = path.read_bytes()
candidate = ModuleType("sql22_v3_day_scope_review")
candidate.__file__ = str(path)
sys.modules[candidate.__name__] = candidate
exec(compile(source, str(path), "exec"), candidate.__dict__)
cases = [
    ("2004年1月1日，列出金额大于5的记录。", {"start": "2004-01-01", "end": "2004-01-02", "grain": "custom"}),
    ("列出2004年1月1日未支付的发票。", {"start": "2004-01-01", "end": "2004-01-02", "grain": "custom"}),
    ("2004年1月1日之前入职的员工，工资大于5。", {"end": "2004-01-01", "grain": "before"}),
]
rows = []
for question, expected in cases:
    actual = candidate.explicit_period(question)
    normalized = {k: v for k, v in actual["current"].items() if k != "label"} if actual else None
    rows.append({"question": question, "expected": expected, "actual": actual, "pass": normalized == expected})
print(json.dumps({"state": "AI发现错误" if not all(r["pass"] for r in rows) else "PASS",
                  "candidate_sha256": hashlib.sha256(source).hexdigest(), "source_unchanged_during_probe": source == path.read_bytes(),
                  "kind": "local parser regression; business examples probe date scope only, not database labels",
                  "checks": len(rows), "passed": sum(r["pass"] for r in rows),
                  "model_requests": 0, "database_queries": 0, "holdout_predictions": 0,
                  "business_files_modified": False, "probes": rows}, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(r["pass"] for r in rows) else 1)
