"""Evaluate /api/chat without exposing holdout or inventing unrun accuracy."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from eval.dataset import DEFAULT_DATASET, ROOT, load_dataset, require_run_permission, reviewed
from eval.metrics import compare_results, compare_plan_results
from qa_agent.config import get_settings, sanitize_error
from qa_agent.schemas import AnswerEnvelope, ChatRequest


def _git(*arguments: str) -> str | None:
    result = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip() if result.returncode == 0 else None


def validate_frozen_tag(tag: str) -> None:
    if tag.startswith("-") or not tag.strip():
        raise ValueError("冻结 tag 无效")
    tagged_commit = _git("rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    current_commit = _git("rev-parse", "HEAD")
    if not tagged_commit or tagged_commit != current_commit:
        raise ValueError("--frozen-tag 必须是当前 HEAD 的真实 Git tag")
    if _git("status", "--porcelain"):
        raise ValueError("保留集评测要求冻结版本工作目录干净，请先提交代码和标注")


def _write_report(directory: Path, report: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    title = "D2" if report.get("run_id") else "D1"
    lines = [f"# {title} SQL 评测记录", "", f"状态：{report['status']}",
             f"题集：{report['split']}；选中 {report['selected_count']} 题；实际预测 {report['prediction_count']} 题。",
             "保留题预测：" + ("本次显式授权冻结评测" if report["split"] == "holdout" and report["prediction_count"] else "本次未运行"),
             f"模型：{report['provenance']['configured_model']}；Git commit：{report['provenance']['git_commit'] or '尚未提交'}。", ""]
    if report["status"] == "READINESS_ONLY":
        lines += ["未运行模型预测，不计算 EX。", "", "需要处理："]
        lines += [f"- {item}" for item in report["blockers"]]
    else:
        key = "exploratory_ex" if report["draft_gold"] else "ex"
        label = "草稿 gold 开发集探索值，等待人工核验" if report["draft_gold"] else "EX"
        lines += [f"{label}：正确 {report['correct']}/{report['selected_count']}；{report[key]:.2%}。", "",
                  "全部失败、超时、误澄清和格式错误均计入分母。", "", "错误分类："]
        lines += [f"- {name}：{count}" for name, count in report["failure_categories"].items()] or ["- 无"]
        lines += ["", "逐题详情见 responses.jsonl；其中保留原请求、响应、SQL、步骤和判断。"]
    lines += ["", "## 溯源", "", "```json", json.dumps(report["provenance"], ensure_ascii=False, indent=2), "```", ""]
    (directory / "report.md").write_text("\n".join(lines), encoding="utf-8")


def evaluate(args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    items = load_dataset(args.dataset)
    # Protect holdout before readiness handling as well as before API calls.
    if args.split == "holdout":
        if not args.allow_holdout or not args.frozen_tag:
            raise ValueError("保留集需要 --allow-holdout 和 --frozen-tag")
        if args.draft_gold:
            raise ValueError("--draft-gold 只允许开发集")
        validate_frozen_tag(args.frozen_tag)
    selected = [item for item in items if item["split"] == args.split]
    if not selected:
        raise ValueError("选定题集为空")
    settings = get_settings()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory = args.output or ROOT / "eval/reports" / f"{args.split}_{stamp}"
    if getattr(args, "run_id", None) and (directory / "report.json").exists():
        raise ValueError("此 D2 运行目录已有结果，请使用新的 --run-id / --output-dir，保留原错误记录")
    provenance = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git("rev-parse", "HEAD"),
        "working_tree_dirty": bool(_git("status", "--porcelain")),
        "frozen_tag": args.frozen_tag,
        "dataset": (args.dataset.resolve().relative_to(ROOT).as_posix()
                    if args.dataset.resolve().is_relative_to(ROOT) else str(args.dataset.resolve())),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "source_sha256": sorted({item.get("source_sha256", "unknown") for item in selected}),
        "configured_model": settings.llm_model,
        "api_base_url": args.base_url,
        "run_id": getattr(args, "run_id", None),
        "comparison_policy": "oct12-plan-ex-v1: global column mapping, proven descriptive extras allowed, duplicates and requested row order preserved; declared continuous numbers 2dp, integers exact; legacy comparison separately retained",
        "actual_models": [],
        "gold_review": ("draft" if args.draft_gold else
                        "human_accepted" if all(reviewed(item) for item in selected) else "pending_human_review"),
    }
    blockers: list[str] = []
    if not settings.llm_configured:
        blockers.append("本地 LLM_API_KEY 尚未配置；未调用模型，不能生成真实基线。")
    pending = [item["id"] for item in selected if not reviewed(item)]
    if pending and not args.draft_gold:
        blockers.append("gold 等待人工复核：" + ", ".join(pending))
    if any("gold_result" not in item for item in selected):
        blockers.append("部分题目缺少数据库实际 gold_result。")
    # Querying health never sends benchmark questions to the model.
    try:
        with httpx.Client(timeout=5, trust_env=False) as client:
            response = client.get(args.base_url.rstrip("/") + "/health")
            response.raise_for_status()
            health = response.json()
            provenance["health"] = health
            if health.get("llm_configured") is False:
                blockers.append("运行中的 API 未配置 LLM key。")
            if health.get("database_ready") is False or health.get("db_ready") is False:
                blockers.append("运行中的 API 数据库尚未就绪。")
    except (httpx.HTTPError, ValueError) as exc:
        blockers.append("API /health 不可用：" + sanitize_error(exc, settings))
    report: dict[str, Any] = {
        "status": "READINESS_ONLY" if blockers else "COMPLETED",
        "split": args.split, "draft_gold": args.draft_gold,
        "selected_count": len(selected), "prediction_count": 0,
        "holdout_prediction_count": 0, "blockers": blockers,
        "gold_pending_ids": pending, "provenance": provenance,
        "suite": getattr(args, "suite", None), "run_id": getattr(args, "run_id", None),
    }
    if blockers:
        _write_report(directory, report)
        return report, directory

    # Manual review is checked again immediately before predictions.
    selected = require_run_permission(items, split=args.split, draft_gold=args.draft_gold,
                                      allow_holdout=args.allow_holdout, frozen_tag=args.frozen_tag)
    directory.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    from qa_agent.sql.catalog import load_catalog
    try:
        comparison_catalog = load_catalog(settings.catalog_path)
    except (AttributeError, ValueError, OSError):
        comparison_catalog = None
    with httpx.Client(timeout=args.timeout, trust_env=False) as client, (directory / "responses.jsonl").open("w", encoding="utf-8") as stream:
        for item in selected:
            request = ChatRequest(session_id=f"eval-{stamp}-{item['id']}", message=item["question"],
                                  scope={"route": "sql", "db_id": "chinook", "doc_ids": []})
            record: dict[str, Any] = {"id": item["id"], "split": item["split"],
                                      "category": item["category"], "request": request.model_dump(),
                                      "expected_result": item["gold_result"], "response": None,
                                      "matched": False, "failure_category": None}
            record.update(base_id=item.get("base_id"), variant_type=item.get("variant_type"),
                          is_d1_common=item.get("exposure_history",{}).get("d1_model_exposed",False))
            started = time.perf_counter()
            try:
                response = client.post(args.base_url.rstrip("/") + "/api/chat", json=request.model_dump())
                record["http_status"] = response.status_code
                response.raise_for_status()
                envelope = AnswerEnvelope.model_validate(response.json())
                record["response"] = envelope.model_dump(mode="json")
                for step in envelope.steps:
                    actual_model = step.output_summary.get("model") if step.name == "llm" else None
                    if actual_model and actual_model not in provenance["actual_models"]:
                        provenance["actual_models"].append(actual_model)
                # Preserve the existing D1 response contract. Real D2 calls
                # prefer the model returned by the traced LLM response;
                # legacy envelopes may expose it only in response metadata.
                legacy_model = envelope.metadata.get("model")
                if not any(step.name == "llm" and step.output_summary.get("model") for step in envelope.steps):
                    if legacy_model and legacy_model not in provenance["actual_models"]:
                        provenance["actual_models"].append(legacy_model)
                if envelope.status not in {"SUCCEEDED", "EMPTY_RESULT"}:
                    record["failure_category"] = envelope.error.code if envelope.error else envelope.status.lower()
                elif envelope.table is None:
                    record["failure_category"] = "missing_result_table"
                else:
                    types = item["column_types"]
                    comparison_options = dict(
                        ordered=item["ordered"],
                        expected_columns=item["gold_columns"],
                        actual_columns=envelope.metadata.get("result_columns"),
                        monetary_columns=item.get("monetary_columns", []),
                        numeric_columns=[i for i, value in enumerate(types) if value == "number"],
                        temporal_columns=[i for i, value in enumerate(types) if value == "temporal"],
                        round_numeric_columns=[i for i, value in enumerate(types)
                                               if value == "number" and i not in item.get("integer_columns",[])]
                                              if getattr(args,"suite",None) else [],
                    )
                    legacy = compare_results(item["gold_result"], envelope.table, **comparison_options)
                    comparison = compare_plan_results(item["gold_result"], envelope.table,
                                                      actual_sql=envelope.sql, catalog=comparison_catalog,
                                                      **comparison_options)
                    record["legacy_comparison"] = legacy.as_dict()
                    record["comparison"] = comparison.as_dict()
                    record["matched"] = comparison.matched
                    if not comparison.matched:
                        record["failure_category"] = "result_mismatch"
            except httpx.TimeoutException as exc:
                record["failure_category"] = "api_timeout"
                record["error"] = sanitize_error(exc, settings)
            except httpx.HTTPError as exc:
                record["failure_category"] = "http_error"
                record["error"] = sanitize_error(exc, settings)
            except (ValueError, TypeError, KeyError) as exc:
                record["failure_category"] = "response_format_error"
                record["error"] = sanitize_error(exc, settings)
            record["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
            code = record.get("failure_category") or ""
            record["error_type"] = ("value_link" if "binding" in code or "value_link" in code else
                                    "clarify_wrong" if "clarification" in code else
                                    "timeout" if "timeout" in code else
                                    "format" if "format" in code or "missing_result" in code else
                                    "schema" if code in {"sql_rejected","catalog_error"} else
                                    "sql_logic" if code else None)
            records.append(record)
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            print(f"{item['id']} {'通过' if record['matched'] else record['failure_category']}", flush=True)
    correct = sum(bool(record["matched"]) for record in records)
    report.update({"prediction_count": len(records), "correct": correct,
                   "legacy_correct": sum(bool(row.get("legacy_comparison", {}).get("matched")) for row in records),
                   "holdout_prediction_count": len(records) if args.split == "holdout" else 0,
                   "exploratory_ex" if args.draft_gold else "ex": correct / len(selected),
                   "failure_categories": dict(Counter(record["failure_category"] for record in records if not record["matched"])),
                   "average_latency_ms": sum(record["latency_ms"] for record in records) / len(records)})
    report["error_types"] = dict(Counter(r["error_type"] for r in records if r["error_type"]))
    report["segments"] = {label:{"correct":sum(bool(r["matched"]) for r in group), "denominator":len(group)}
                          for label, group in {"d1_common":[r for r in records if r["is_d1_common"]],
                                               "new_dev":[r for r in records if not r["is_d1_common"]]}.items()}
    report["gold_human_accepted_count"] = len(selected) - len(pending)
    _write_report(directory, report)
    return report, directory


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset", type=Path)
    result.add_argument("--suite", choices=["nl2sql", "robust", "rag"], help="D2 suites; omitting preserves the D1 entry")
    result.add_argument("--run-id", help="Unique D2 run identifier, recorded in provenance")
    result.add_argument("--base-url", default="http://127.0.0.1:8000")
    result.add_argument("--split", choices=["dev", "holdout"], default="dev")
    result.add_argument("--draft-gold", action="store_true", help="仅开发集草稿探索，不能作为正式成绩")
    result.add_argument("--allow-holdout", action="store_true")
    result.add_argument("--frozen-tag", help="保留集要求当前 HEAD 的冻结 Git tag 和干净工作目录")
    result.add_argument("--timeout", type=float, default=240)
    result.add_argument("--output", "--output-dir", dest="output", type=Path)
    return result


def main() -> int:
    args = parser().parse_args()
    if args.dataset is None:
        args.dataset = ROOT / "eval/datasets" / {"nl2sql":"nl2sql_chinook_d2.jsonl", "robust":"robust.jsonl", "rag":"rag_single.jsonl"}.get(args.suite, DEFAULT_DATASET.name)
    if args.run_id and not args.output:
        args.output = ROOT / "eval/artifacts/d2" / (args.suite or "nl2sql") / args.run_id
    try:
        if args.suite == "rag":
            from eval.d2_rag_eval import evaluate_rag
            report, directory = evaluate_rag(args)
        else:
            report, directory = evaluate(args)
    except (ValueError, OSError) as exc:
        print(sanitize_error(exc, get_settings()), file=sys.stderr)
        return 2
    print(f"{report['status']}；预测 {report['prediction_count']} 题；报告：{directory / 'report.md'}")
    return 0 if report["status"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
