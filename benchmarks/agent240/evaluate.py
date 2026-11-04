"""Re-score saved 40+200 development predictions. No API, SQL or model judge.

Usage: python -m benchmarks.agent240.evaluate --bundle benchmarks/agent240/data
       --output .runtime/agent240/new-report
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

from benchmarks.agent240.metrics import percentile, provider_totals, rate, table_scores, text_scores
from benchmarks.agent240.checks import inspect_record, summarize_checks, seven_dimensions


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_bundle(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text("utf-8"))
    if not {"dataset.json", "records.jsonl"}.issubset(manifest.get("files", {})):
        raise ValueError("Manifest must hash both dataset.json and records.jsonl")
    for name, expected in manifest["files"].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()) or sha(path) != expected:
            raise ValueError("Evidence hash/path mismatch: " + name)
    dataset = json.loads((directory / "dataset.json").read_text("utf-8"))
    cases = {row["id"]: row for row in dataset["cases"]}
    if len(cases) != len(dataset["cases"]) or len(cases) != 240:
        raise ValueError("Expected exactly 240 distinct namespaced original IDs")
    suite_counts = Counter(c["suite"] for c in cases.values())
    if sorted(suite_counts.values()) != [40, 200]:
        raise ValueError("Original 40+200 scope changed")
    rows = [json.loads(s) for s in (directory / "records.jsonl").read_text("utf-8").splitlines() if s.strip()]
    seen = set()
    for row in rows:
        pair = row["id"], row["arm"]
        if row["id"] not in cases or pair in seen:
            raise ValueError("Unknown/duplicate prediction ID")
        seen.add(pair)
    return manifest, cases, rows


def score(case, record):
    reference = case.get("reference")
    sql_eligible = bool(case.get("sql_eligible") or (reference or {}).get("sql"))
    if record is None:
        return {"id": case["id"], "suite": case["suite"], "observed": False,
                "accuracy": None, "external_success": None, "exact_match": None,
                "row_f1": None, "text_em": None, "text_f1": None, "error": None,
                "elapsed_ms": None, "attempts": [], "sql_eligible": sql_eligible,
                "expected_route": case.get("expected_route"),
                "reference_available": isinstance(reference, dict) and reference.get("available", True)}
    review = record.get("review") or {}
    response_digest = hashlib.sha256(json.dumps(record.get("raw_response"), ensure_ascii=False,
                                                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    verified = review.get("binding_verified") is True and review.get("response_sha256") == response_digest
    attempts = record.get("attempts", [])
    durations = [a.get("elapsed_ms") for a in attempts if a.get("kind") != "context"]
    elapsed = (sum(durations) if durations and all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in durations) else None)
    status = record.get("final_status")
    table = table_scores(reference, record.get("result"), ordered=(reference or {}).get("ordered") is True,
                         successful=status in {"SUCCEEDED", "EMPTY_RESULT"}) if sql_eligible else {"exact_match": None, "row_f1": None, "reason": "not_SQL"}
    full_reference = case.get("reference_answer") if case.get("reference_answer_scope") == "full_text" else None
    lexical = text_scores(full_reference, record.get("answer"))
    outcome = {"id": case["id"], "suite": case["suite"], "group": case.get("group"),
               "arm": record["arm"], "configuration": record.get("configuration"), "observed": True,
               "expected_route": case.get("expected_route"),
               "accuracy": review.get("business_correct") if verified else None,
               "external_success": review.get("external_task_success") if verified else None,
               **table, **lexical, "sql_eligible": sql_eligible,
               "reference_available": isinstance(reference, dict) and reference.get("available", True),
               "status": status, "route": (record.get("raw_response") or {}).get("metadata", {}).get("route"),
               "error": any(a.get("status") == "FAILED" or (type(a.get("http_status")) is int and a["http_status"] >= 400) for a in attempts),
               "final_failed": status == "FAILED",
               "elapsed_ms": elapsed, "attempts": attempts, "source": record.get("source"),
               "reviewer_kind": review.get("reviewer_kind") if verified else None}
    outcome["checks"] = inspect_record(case, record)
    # Only actual failed public attempts followed by success count here.
    # A clarification turn is not a transport/tool failure.
    failures = [i for i, a in enumerate(attempts) if a.get("status") == "FAILED" or
                (type(a.get("http_status")) is int and a["http_status"] >= 400)]
    outcome["failure_recovery_eligible"] = bool(failures) and len(attempts) > failures[0] + 1
    outcome["recovery_attempt_observed"] = outcome["failure_recovery_eligible"]
    outcome["recovered"] = (any(a.get("status") in {"SUCCEEDED", "EMPTY_RESULT"} for a in attempts[failures[0] + 1:])
                            if outcome["failure_recovery_eligible"] else None)
    return outcome


def summarize(rows):
    values = [r["elapsed_ms"] for r in rows if r["elapsed_ms"] is not None]
    sql = [r for r in rows if r.get("sql_eligible")]
    f1 = [r["row_f1"] for r in sql if r["row_f1"] is not None]
    lexical = [r["text_f1"] for r in rows if r["text_f1"] is not None]
    recovery = [r["recovered"] for r in rows if r.get("failure_recovery_eligible")]
    return {"logical_tasks": len(rows), "observed": sum(r["observed"] for r in rows),
            "accuracy": rate(r["accuracy"] for r in rows),
            "external_task_success": rate(r["external_success"] for r in rows),
            "SQL_exact_match": rate(r["exact_match"] for r in sql),
            "SQL_row_F1": {"mean": sum(f1) / len(f1) if f1 else None, "known": len(f1), "eligible": len(sql)},
            "text_EM": rate(r["text_em"] for r in rows if r["text_em"] is not None),
            "text_F1": {"mean": sum(lexical) / len(lexical) if lexical else None, "known": len(lexical)},
            "latency_ms": {"p50": percentile(values, 50), "p90": percentile(values, 90), "known": len(values)},
            "error_rate": rate(r["error"] for r in rows),
            "final_failed_rate": rate(r.get("final_failed") for r in rows),
            "failure_recovery": rate(recovery),
            "usage": provider_totals(a for r in rows for a in r.get("attempts", [])),
            "statuses": dict(Counter(r.get("status", "not_observed") for r in rows)),
            "reviewer_kinds": dict(Counter(r.get("reviewer_kind", "unknown") for r in rows)),
            "seven_dimension_checks": summarize_checks(rows)}


def _pct(value):
    return "未核验" if value is None else f"{value * 100:.2f}%"


def _rate(value):
    if value["total"] == 0:
        return "未核验（无适用分母）"
    text = f"{value['passed']}/{value['total']}"
    return text + (f"（{_pct(value['full_rate'])}）" if value["full_rate"] is not None else f"；{value['failed']}失败、{value['unknown']}未核验")


def markdown(summary):
    lines = ["# 原240道综合开发题评测", "",
             "本次重新核验历史真实回答并计算指标，未重新调用问答系统、模型API或数据库。32道后补合成RAG题已退役，不参与本报告。", "",
             "240是原40题与原200题的协议条目数。两批有内容重合、多轮依赖及不同源码快照，分批报告；不把它们称为240个独立RAG问题，也不宣称当前同一版本在240题上实跑。增强配置按各批实际配置保留，不以组名代替功能开关。", "",
             "## 1 原题范围与证据", "",
             "| 原始批次 | 题数 | 预测记录 | 配置 |", "|---|---:|---:|---|"]
    for suite, group in summary["groups"].items():
        configs = ", ".join(sorted({c for s in group.values() for c in s.get("configurations", []) if c}))
        lines.append(f"| {suite} | {next(iter(group.values()))['logical_tasks']} | {sum(s['observed'] for s in group.values())} | {configs} |")
    lines += ["", "源文件哈希、数据集与导出协议见manifest.json；逐题结果见scored.jsonl。保留未知项，AI审核不代替人工签字。", "",
              "## 2 准确性与外部任务", "",
              "| 批次/配置 | 业务Accuracy（已有证据绑定AI审核） | SQL结果EM | SQL行集合F1 | 外部任务成功 |", "|---|---|---|---|---|"]
    for suite, group in summary["groups"].items():
        for arm, s in group.items():
            label = "/".join(s.get("configurations", [])) or arm
            lines.append(f"| {suite}/{label} | {_rate(s['accuracy'])} | {_rate(s['SQL_exact_match'])} | {_pct(s['SQL_row_F1']['mean'])}（{s['SQL_row_F1']['known']}/{s['SQL_row_F1']['eligible']}可算） | {_rate(s['external_task_success'])} |")
    lines += ["", "SQL结果EM沿用严格原始数值、完整列数、全表一致的列映射与重复行计数；参考SQL要求排序时检查行序。没有金额四舍五入、比例缩放、删列或NULL填充。它衡量结果相等，不是SQL文本完全相同。", "",
              "本轮将已观测、但未交付成功结果表的SQL题计为结果EM不匹配；旧报告对其中部分保留未知。这里只改变重评分的交付判定，未改Gold，也未将其业务语义未知改为错误。未观测预测或无效参考仍保留未知。", "",
              "SQL行集合F1是完整结果行的多重集精确率与召回率的调和平均；沿用同一全局列映射，忽略行序，保留重复行。这是本轮新增的部分结果诊断，不是开放答案语义F1。没有规范短答案Gold的题目，文本EM/F1保持未核验，不能用隐藏目标或SQL自动编造标准文本。", "",
              "### 文本指标", "", "| 批次/配置 | 文本EM | 文本F1（词面诊断） |", "|---|---|---|"]
    for suite, group in summary["groups"].items():
        for arm, s in group.items():
            label = "/".join(s.get("configurations", [])) or arm
            lines.append(f"| {suite}/{label} | {_rate(s['text_EM'])} | {_pct(s['text_F1']['mean'])}（{s['text_F1']['known']}条完整文本Gold） |")
    lines += ["", "文本指标仅比较原Gold中声明的完整文本答案，适用范围为6道RAG与6道会话正文题；228道SQL/跨源题的局部文字子任务不能拿来与整篇答案直接比较。中文按字、其他语言按词及符号作机械匹配；正确改述可能EM为0，故文本F1/EM与业务审核Accuracy分开解释。", "",
              "## 3 效率与鲁棒性", "",
              "| 批次/配置 | 响应P50/P90秒 | 物理调用 | 输入/输出token | Error Rate | Failure Recovery |", "|---|---|---:|---|---|---|"]
    for suite, group in summary["groups"].items():
        for arm, s in group.items():
            l, u = s["latency_ms"], s["usage"]
            latency = f"{l['p50']/1000:.2f}/{l['p90']/1000:.2f}" if l["p50"] is not None else "未核验"
            label = "/".join(s.get("configurations", [])) or arm
            lines.append(f"| {suite}/{label} | {latency} | {u['physical_calls']} | {u['input_tokens']} / {u['output_tokens']} | {_rate(s['error_rate'])} | {_rate(s['failure_recovery'])} |")
    lines += ["", "Response Time是同一逻辑题初次请求与实际补充请求的HTTP耗时之和；正文登记另列，不含用户思考时间。P50/P90用(n−1)线性插值。不同历史批次不合并成新的性能对照。", "",
              "Token Usage根据保存的物理provider记录去重，包括失败和重试；缓存命中/未命中及缺失usage另见summary.json。usage缺失保持null并提供已观测子和，金额未核验。", "",
              "Error Rate只计实际FAILED或HTTP错误，不能与1−业务准确率混为一谈。Failure Recovery只在同题有实际失败、随后有真实恢复尝试时统计；没有故障实验就显示无可用分母。NEEDS_CLARIFICATION不是故障，也不拿后续任意问题成功充当恢复。", "",
              seven_dimensions(summary, _rate), "## 5 边界与下一步", "",
              "- 这是开发集历史回答的重新计分，非新一轮模型预测、正式保留集或盲测。",
              "- 各批实际配置与源码哈希单列。不同源码的历史版本对照不当作仅开关一个变量的同源消融。",
              "- 仅对真实进入文档工具的题目分析RAG链路；原题没有逐片段相关性标签，故不捏造240题Recall/MRR/nDCG。",
              "- 开放答案质量、引用语义支持及故障注入恢复，需要对应Gold/独立审核或实际故障证据；当前缺失的保持not_verified。",
              "- 当前API/数据库是否可运行与本报告重计分相互独立；未完成的当前版本在线回放不能标为已完成。", ""]
    return "\n".join(lines)


def evaluate(bundle, output):
    output = Path(output)
    if output.exists():
        raise ValueError("Output exists; choose a new directory")
    manifest, cases, records = load_bundle(bundle)
    by_key = {(r["id"], r["arm"]): r for r in records}
    arms = sorted({r["arm"] for r in records})
    scored = []
    grouped = defaultdict(dict)
    for suite in sorted({c["suite"] for c in cases.values()}):
        selected = [c for c in cases.values() if c["suite"] == suite]
        for arm in arms:
            rows = [score(case, by_key.get((case["id"], arm))) for case in selected]
            for row in rows:
                row["arm"] = arm
            value = summarize(rows)
            value["configurations"] = sorted({r.get("configuration") for r in rows if r.get("configuration")})
            value["by_task_type"] = {route: summarize([r for r in rows if r.get("expected_route") == route])
                                     for route in sorted({c.get("expected_route", "unknown") for c in selected})}
            grouped[suite][arm] = value
            scored += rows
    summary = {"created_utc": datetime.now(timezone.utc).isoformat(),
               "mode": "offline_rescoring_of_historical_predictions", "new_model_calls": 0,
               "original_logical_cases": len(cases), "saved_predictions": len(records),
               "deprecated_synthetic_cases_included": 0, "groups": dict(grouped),
               "seven_dimension_checks": summarize_checks(scored),
               "all_saved_provider_usage": provider_totals([*[a for r in records for a in r.get("attempts", [])],
                     *manifest.get("context_ack_usage", {}).get("records", [])]),
               "bundle_manifest_sha256": sha(Path(bundle) / "manifest.json"),
               "evaluator_source_files": {p.name: sha(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
               "command": sys.argv, "source_manifest": manifest}
    output.mkdir(parents=True)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (output / "scored.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in scored), "utf-8")
    (output / "report.md").write_text(markdown(summary), "utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = evaluate(args.bundle, args.output)
    print(json.dumps({k: summary[k] for k in ("mode", "original_logical_cases", "saved_predictions", "new_model_calls")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
