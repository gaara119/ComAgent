"""Prepare a narrow boundary-normalization candidate without changing runtime."""
from pathlib import Path
from hashlib import sha256
import json
import difflib

ROOT = Path(__file__).resolve().parents[3]
directory = Path(__file__).resolve().parent / "ratio"
directory.mkdir(exist_ok=True)
source = ROOT / "qa_agent/sql/ratio_guard.py"
before = source.read_text(encoding="utf-8")
helper = '''
def _period_literal_date(node):
    """Prove a static date or timezone-free exact midnight boundary.

    Never truncate non-midnight timestamps, strip timezone offsets, or evaluate
    dynamic expressions. Cast types remain visible during this proof.
    """
    while isinstance(node, (exp.Paren, exp.Alias, exp.Cast)):
        if isinstance(node, exp.Cast):
            kind = node.args["to"].sql(dialect="postgres").upper()
            if not re.fullmatch(r"DATE|TIMESTAMP(?:\\(\\d+\\))?(?: WITHOUT TIME ZONE)?", kind):
                return None
        node = node.this
    if not isinstance(node, exp.Literal) or not node.is_string:
        return None
    value = str(node.this)
    if not re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}(?:[ T]00:00:00(?:\\.0+)?)?", value):
        return None
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None

'''
after = before.replace("\ndef validate_invoice_share(", "\n" + helper + "\ndef validate_invoice_share(", 1)
old = '''                literal = _unparen(node.right)
                if isinstance(literal, exp.Cast):
                    literal = literal.this
                pair = (">=" if isinstance(node, exp.GTE) else "<", str(literal.this) if isinstance(literal, exp.Literal) else None)'''
new = '''                pair = (">=" if isinstance(node, exp.GTE) else "<", _period_literal_date(node.right))'''
if old not in after:
    raise RuntimeError("Candidate base no longer matches")
after = after.replace(old, new, 1)
(directory / "ratio_guard_candidate.py").write_text(after, encoding="utf-8")
(directory / "candidate.patch").write_text("".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile="a/qa_agent/sql/ratio_guard.py", tofile="b/qa_agent/sql/ratio_guard.py")), encoding="utf-8")
(directory / "candidate-source.json").write_text(json.dumps({"base_sha256": sha256(source.read_bytes()).hexdigest(), "candidate_sha256": sha256(after.encode()).hexdigest(), "runtime_modified": False}, indent=2), encoding="utf-8")
print("Isolated ratio timestamp candidate prepared")
