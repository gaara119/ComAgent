"""Offline, read-only extraction of original V1 evidence for the AI review.

No API, database, scoring, label or business-source mutations. The original
provider files are read even when the runtime archiver rejected their path.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "eval/experiments/after_d2_01_03"


def read(path):
    data = path.read_bytes()
    return json.loads(data), {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(data).hexdigest()}


labels_path = EXP / "data/cases-v6-reviewed.jsonl"
labels_bytes = labels_path.read_bytes()
labels = [json.loads(x) for x in labels_bytes.decode("utf-8").splitlines()]
score_path = EXP / "runtime_eval/runs/V1-001-scores.json"
score, score_ref = read(score_path) if score_path.exists() else ({"cases": []}, None)
scores = {x["id"]: x for x in score["cases"]}
cases = []
for line, label in enumerate(labels, 1):
    if label["task"] != "03":
        continue
    case_id = label["id"]
    cp_path = EXP / f"runtime_eval/runs/V1-001/cases/{case_id}/checkpoint.json"
    if not cp_path.exists():
        continue
    cp, cp_ref = read(cp_path)
    if cp.get("outcome") == "running":
        continue
    refs = [dict(path=labels_path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(labels_bytes).hexdigest(), location=f"line {line}: {case_id}"), cp_ref] + ([score_ref] if score_ref else [])
    turns = []
    for t in cp["turns"]:
        tp = EXP / f"runtime_eval/runs/V1-001/cases/{case_id}/turns/{t['index']:03d}"
        request, req_ref = read(tp / "request.json")
        raw, raw_ref = read(tp / "response.raw.json")
        body = json.loads(raw["body"]) if isinstance(raw.get("body"), str) else raw.get("body", raw)
        archive, archive_ref = read(tp / "provider-evidence.json")
        refs += [req_ref, raw_ref, archive_ref]
        providers = []
        for st in body.get("steps", []):
            cap = st.get("output_summary", {}).get("provider_capture")
            if not cap:
                continue
            pf = ROOT / cap
            if not pf.exists():
                providers.append({"path": cap, "missing": True})
                continue
            provider, pf_ref = read(pf)
            refs.append(pf_ref)
            messages = provider["request"].get("messages", [])
            users = []
            for m in messages:
                if m["role"] != "user":
                    continue
                try:
                    u = json.loads(m["content"])
                except (ValueError, TypeError):
                    u = m["content"]
                if isinstance(u, dict):
                    u = {k: v for k, v in u.items() if k not in {"catalog", "catalog_yaml", "schema"}}
                users.append(u)
            providers.append({"path": cap, "sha256": pf_ref["sha256"], "trace_id": provider.get("trace_id"), "user_context_without_repeated_catalog": users, "response_content": provider["response"]["choices"][0]["message"]["content"], "system_sha256": hashlib.sha256(messages[0]["content"].encode()).hexdigest(), "usage": provider["response"].get("usage")})
        gate = [s for s in body.get("steps", []) if s["name"] in {"clarification_gate", "value_link", "value_link_adjudication", "sql_validate", "sql_generate", "sql_repair", "readonly_execute", "sql_execute", "execute"}]
        turns.append({"index": t["index"], "phase": t["phase"], "asked_key": t.get("asked_key"), "supplement_key": t.get("supplement_key"), "request": request, "status": body.get("status"), "answer": body.get("answer"), "sql": body.get("sql"), "table": body.get("table"), "intent": body.get("intent"), "clarification": body.get("clarification"), "metadata": body.get("metadata"), "gate_and_execution_steps": gate, "providers": providers, "archive_observation": archive, "raw_matches_checkpoint": body == t.get("response")})
    cases.append({"id": case_id, "reference": {k: label.get(k) for k in ["input", "category", "scorable", "expected_behavior", "allowed_interpretations", "expected_bindings", "missing_conditions", "business_basis", "gold_sql", "gold_result", "controller", "final_source_guard_issues"]}, "automatic_score": scores.get(case_id), "outcome": cp["outcome"], "controller_events": cp["controller_events"], "turns": turns, "evidence": refs})
out = {"purpose": "Offline original-evidence extraction; no predictions or scoring", "all_original_files_fully_read": True, "task03_count": len(cases), "labels_sha256": hashlib.sha256(labels_bytes).hexdigest(), "score_sha256": score_ref["sha256"] if score_ref else None, "score_complete": score_ref is not None, "cases": cases}
dest = EXP / "reports/v1-task03-evidence-read.json"
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"output": dest.relative_to(ROOT).as_posix(), "cases": len(cases), "turns": sum(len(c["turns"]) for c in cases), "original_provider_count": sum(len(t["providers"]) for c in cases for t in c["turns"]), "mismatched_raw": [(c["id"], t["index"]) for c in cases for t in c["turns"] if not t["raw_matches_checkpoint"]]}, ensure_ascii=False))
