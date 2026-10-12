"""Review literal-before parsing in an isolated source snapshot; no predictions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
candidate_path = ROOT / "notes/oct12/staging/sql22/rules_candidate.py"
candidate_bytes = candidate_path.read_bytes()
candidate = ModuleType("sql22_independent_review")
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
    ("2003年12月1日到2004年1月1日入职。", {"start": "2003-12-01", "end": "2004-01-02", "grain": "custom"}),
]
rows = []
for question, expected in cases:
    actual = candidate.explicit_period(question)
    normalized = ({k: v for k, v in actual["current"].items() if k != "label"} if actual else None)
    rows.append({"question": question, "expected": expected, "actual": actual,
                 "pass": normalized == expected})
report = {"state": "PASS" if all(row["pass"] for row in rows) else "AI发现错误",
          "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
          "source_unchanged_during_probe": candidate_bytes == candidate_path.read_bytes(),
          "checks": len(rows), "passed": sum(row["pass"] for row in rows),
          "kind": "Actual local literal-parser probes; no provider, system prediction, or database execution",
          "model_requests": 0, "holdout_predictions": 0, "business_files_modified": False,
          "probes": rows}
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if report["state"] == "PASS" else 1)
