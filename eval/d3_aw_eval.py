"""Live AW /api/chat development EX, raw outputs and schema recall.

This runner accepts a development-only file and never sends gold material to
the API. Gold is still pending human review: all resulting figures are
exploratory development measurements, not official heldout scores.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
from eval.metrics import compare_results
from qa_agent.config import get_settings, sanitize_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "eval/datasets/d3/aw_schema_link.dev.v2.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    cases = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(cases) != 21 or any(case.get("split") != "dev" for case in cases):
        raise ValueError("AW runner requires exactly the 21 development cases, without any protected holdout content")
    if args.output.exists():
        raise ValueError("Choose a fresh output directory; raw previous runs must remain unchanged")
    args.output.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    provenance = {"created_at":datetime.now(timezone.utc).isoformat(), "configured_model":settings.llm_model,
                  "configured_llm_base_url":settings.llm_base_url, "dataset":str(args.dataset.relative_to(ROOT)),
                  "dataset_sha256":hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                  "git_commit":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True).stdout.strip(),
                  "working_tree_dirty":bool(subprocess.run(["git","status","--porcelain"],cwd=ROOT,capture_output=True,text=True).stdout.strip()),
                  "base_url":args.base_url, "gold_human_status":"pending_human_review"}
    records = []
    with httpx.Client(timeout=args.timeout, trust_env=False) as client:
        health = client.get(args.base_url.rstrip("/")+"/health")
        health.raise_for_status()
        provenance["actual_health"] = health.json()
        with (args.output / "responses.jsonl").open("w", encoding="utf-8") as stream:
            for case in cases:
                # Request contains only the user-visible question and allowed source.
                request = {"session_id":f"d3-aw-{stamp}-{case['id']}", "message":case["question"],
                           "scope":{"route":"sql","db_id":"adventureworks","doc_ids":[]}}
                record = {"id":case["id"], "split":"dev", "request":request,
                          "expected_result":case["gold_result"], "gold_tables":case["gold_tables"],
                          "response":None, "matched":False,"failure_category":None}
                started = perf_counter()
                try:
                    response = client.post(args.base_url.rstrip("/")+"/api/chat",json=request)
                    record["http_status"] = response.status_code
                    response.raise_for_status()
                    envelope = response.json()
                    record["response"] = envelope
                    if envelope.get("status") not in {"SUCCEEDED","EMPTY_RESULT"}:
                        record["failure_category"] = (envelope.get("error") or {}).get("code") or envelope.get("status") or "missing_status"
                    elif envelope.get("table") is None:
                        record["failure_category"] = "missing_result_table"
                    else:
                        types = case["column_types"]
                        comparison = compare_results(case["gold_result"],envelope["table"],ordered=case["ordered"],
                            expected_columns=case["gold_columns"],actual_columns=(envelope.get("metadata") or {}).get("result_columns"),
                            monetary_columns=case.get("monetary_columns",[]), numeric_columns=[i for i,t in enumerate(types) if t=="number"],
                            temporal_columns=[i for i,t in enumerate(types) if t=="temporal"],
                            round_numeric_columns=[i for i,t in enumerate(types) if t=="number" and i not in case.get("integer_columns",[])])
                        record["comparison"] = comparison.as_dict()
                        record["matched"] = comparison.matched
                        if not comparison.matched:
                            record["failure_category"] = "result_mismatch"
                    meta = envelope.get("metadata") or {}
                    schema = meta.get("schema_linker") or meta.get("schema_bundle") or meta.get("schema_linking") or {}
                    if isinstance(schema,dict) and "selected_tables" in schema:
                        selected = set(schema["selected_tables"])
                        gold = set(case["gold_tables"])
                        record["actual_schema_recall"] = len(selected & gold)/len(gold)
                        record["actual_schema_precision"] = len(selected & gold)/len(selected) if selected else 0
                    record["model_calls"] = [{"model":step.get("output_summary",{}).get("model"), "usage":step.get("output_summary",{}).get("usage",{})}
                                              for step in envelope.get("steps",[]) if step.get("name")=="llm"]
                except Exception as exc:
                    record["failure_category"] = "api_exception"
                    record["error"] = sanitize_error(exc,settings)
                record["elapsed_ms"] = round((perf_counter()-started)*1000)
                records.append(record)
                stream.write(json.dumps(record,ensure_ascii=False)+"\n")
                stream.flush()
                print(case["id"], "correct" if record["matched"] else record["failure_category"], record["elapsed_ms"], flush=True)
    calls = [call for row in records for call in row.get("model_calls",[])]
    summary = {"status":"ACTUALLY_RUN_DEV_EXPLORATORY", "prediction_count":len(records), "holdout_predictions":0,
               "correct":sum(r["matched"] for r in records), "exploratory_ex":sum(r["matched"] for r in records)/len(records),
               "all_failures_in_denominator":True,"failure_categories":dict(Counter(r["failure_category"] for r in records if r["failure_category"])),
               "actual_model_attempts":len(calls),"actual_models":sorted({c["model"] for c in calls if c["model"]}),
               "usage":{name:sum(c["usage"].get(name,0) for c in calls) for name in ("prompt_tokens","completion_tokens","total_tokens")},
               "average_latency_ms":sum(r["elapsed_ms"] for r in records)/len(records),
               "gold_review":"pending_human_review", "provenance":provenance,
               "interpretation":"本项目合成开发集自动结果，非正式成绩；原始失败完整保留，不读取保留内容、不预测保留。"}
    (args.output / "report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    (args.output / "report.md").write_text("# D3 AW 开发集真实问答评测\n\n"+"```json\n"+json.dumps(summary,ensure_ascii=False,indent=2)+"\n```\n\n原始请求、真实响应、SQL、步骤、usage及失败见 responses.jsonl。gold待人工最终审核，EX为探索值。\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
