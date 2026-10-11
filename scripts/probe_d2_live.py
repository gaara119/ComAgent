"""Check the existing model configuration and both real API routes into D2 files."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
from qa_agent.config import get_settings, sanitize_error
from qa_agent.llm import JsonLLM
from qa_agent.schemas import AnswerEnvelope
from qa_agent.trace import TraceRecorder
from scripts.check_llm import ProbeAnswer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--phase", default="D2")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite an existing live probe record")
    settings = get_settings()
    trace = TraceRecorder(settings=settings)
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "phase": args.phase,
              "model": settings.llm_model, "checks": {}, "requests": [], "errors": []}
    try:
        llm = JsonLLM(settings)
        report["available_model_ids"] = llm.list_models()
        report["checks"]["configured_model_is_real"] = settings.llm_model in report["available_model_ids"]
        probe = llm.complete_json("你是接口检查助手。", "返回 JSON：ok 为 true，message 为 接入成功。",
                                  ProbeAnswer, trace)
        report["json_probe"] = probe.model_dump()
        report["probe_steps"] = [step.model_dump() for step in trace.steps]
        report["checks"]["json_output"] = probe.ok
    except Exception as exc:
        report["errors"].append(sanitize_error(exc, settings))
        report["checks"]["json_output"] = False
    examples = [("sql", "来自巴西的客户有多少位？", {"route": "sql", "db_id": "chinook", "doc_ids": []}),
                ("doc", "Which application lets you create and share movies in minutes?",
                 {"route": "doc", "db_id": None, "doc_ids": ["ohr-manual-macbook-air"]})]
    with httpx.Client(timeout=240, trust_env=False) as client:
        for kind, question, scope in examples:
            record = {"kind": kind, "request": {"session_id": f"d2-preflight-{kind}",
                                               "message": question, "scope": scope}}
            start = time.perf_counter()
            try:
                response = client.post(args.base_url + "/api/chat", json=record["request"])
                response.raise_for_status()
                envelope = AnswerEnvelope.model_validate(response.json())
                record["response"] = envelope.model_dump(mode="json")
                report["checks"][f"{kind}_api"] = envelope.status == "SUCCEEDED"
                if kind == "sql":
                    report["checks"]["sql_real_result"] = any(5 in row.values() for row in envelope.table or [])
                else:
                    report["checks"]["rag_selected_document_citations"] = bool(envelope.evidences) and all(
                        e.doc_id == "ohr-manual-macbook-air" for e in envelope.evidences)
            except Exception as exc:
                record["error"] = sanitize_error(exc, settings)
                report["checks"][f"{kind}_api"] = False
            record["latency_ms"] = round((time.perf_counter() - start) * 1000)
            report["requests"].append(record)
            print(f"{kind}: {record.get('response', {}).get('status', 'FAILED')}", flush=True)
    report["status"] = "PASS" if all(report["checks"].values()) else "FAIL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps({"status": report["status"], "checks": report["checks"]}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
