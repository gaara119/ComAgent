"""Create the 60-case manual review index from preserved synthetic DEV evidence.

No business imports, HTTP, model calls, SQL, rescoring, or approval mutations.
The original V0 score and frozen 49/11 split remain independent of AI opinions.
Root supplies completed trial paths and explicitly selects the final version.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import html
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
EXP = "eval/experiments/after_d2_01_03"
TITLE = "①③专项统一待人工审核表"
LABEL = EXP + "/data/cases-v6-reviewed.jsonl"
LABEL_SHA = "42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1"
EXPECTED_IDS = {f"sp{task}-{number:02}" for task in ("01", "03") for number in range(1, 31)}
PROTECTED = ["eval/datasets/sql_holdout", "eval/datasets/robust_holdout", "eval/datasets/rag_holdout",
             "eval/datasets/d3/clarify/protected_holdout/", "eval/artifacts/d3/a/gold/holdout/",
             "eval/datasets/d3/aw_schema_link.holdout.jsonl", "eval/datasets/d3/aw_schema_link.jsonl",
             "eval/datasets/d3/aw_schema_link.v2.jsonl", "eval/datasets/nl2sql_chinook.jsonl",
             "eval/datasets/nl2sql_chinook_d2.jsonl", "eval/datasets/robust.jsonl",
             "eval/datasets/rag_single.jsonl", "eval/datasets/rag_ohr.jsonl",
             "scripts/build_d3_aw_dataset.py", "scripts/build_d3_clarify_cases.py"]
UUID_NAME = re.compile(r"(?:[0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\.json", re.I)


def local(name: str) -> Path:
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Evidence must stay inside the project: " + name)
    rel = path.relative_to(ROOT).as_posix().casefold()
    if any(rel.startswith(prefix.casefold()) for prefix in PROTECTED):
        raise ValueError("Protected or mixed evaluation material: " + name)
    if any(part.startswith(".env") and part != ".env.example" for part in path.parts):
        raise ValueError("Private environment material is not review evidence")
    return path


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def read(name: str):
    return json.loads(local(name).read_text(encoding="utf-8-sig"))


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def evidence(name: str, location: str = "") -> dict:
    path = local(name)
    if not path.is_file():
        return {"path": name, "location": location, "exists": False, "judgment": "证据不足"}
    return {"path": relative(path), "location": location, "exists": True, "sha256": digest(path)}


def labels() -> list[dict]:
    path = local(LABEL)
    if digest(path) != LABEL_SHA:
        raise ValueError("Frozen labels changed; this review builder cannot accept a new label version")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if len(rows) != 60 or {row["id"] for row in rows} != EXPECTED_IDS:
        raise ValueError("Expected exactly the frozen 60 original case IDs")
    if sum(row.get("scorable") is True for row in rows) != 49:
        raise ValueError("Frozen 49/11 split changed")
    if any(row.get("split") != "dev" or row.get("human_review_status") != "pending_human_review" for row in rows):
        raise ValueError("Only pending-human synthetic DEV labels are accepted")
    for line, row in enumerate(rows, 1):
        row["_source_line"] = line
    return rows


def review_records(files: list[str], expected_version: str, score_sha: str, run_id: str) -> tuple[dict, list[dict], list[dict]]:
    result, sources, disputes = {}, [], []
    for name in files:
        data = read(name)
        version = data.get("version", data.get("version_reviewed"))
        if version not in {expected_version, run_id}:
            raise ValueError(f"AI review {name} belongs to {version}, not {expected_version}")
        declared_sha = (data.get("original_score_sha256")
                        or data.get("immutable_proof", {}).get("score_sha256")
                        or data.get("immutable_proof", {}).get("score_sha256_after"))
        if declared_sha and declared_sha != score_sha:
            raise ValueError("AI review refers to a different original score: " + name)
        sources.append(evidence(name, "cases[id=原编号]; AI意见不重计自动分数"))
        for item in data.get("cases", []):
            case_id = item.get("id")
            if case_id not in EXPECTED_IDS or case_id in result:
                raise ValueError("Unknown or duplicated AI-review case: " + str(case_id))
            reference = item.get("reference_review", {})
            actual = item.get("actual_system_review", {})
            result[case_id] = {
                "reference_verdict": item.get("reference_ai_verdict", reference.get("verdict", "证据不足")),
                "system_verdict": item.get("system_ai_verdict", actual.get("verdict", "证据不足")),
                "reference_reason": reference.get("reason", item.get("judgment_reason", "")),
                "system_reason": actual.get("reason", item.get("judgment_reason", "")),
                "needs_human_confirmation": item.get("needs_human_confirmation", [item.get("remaining_human_decision", "")]),
                "dimension_results": item.get("dimension_results", {}),
                "controller_review": item.get("controller_review", {}),
                "attribution_tags": item.get("attribution_tags", []),
                "source": evidence(name, f"cases[id={case_id}]"),
                "original_record_unchanged": item,
            }
        for case_id in data.get("reference_issue_candidates_beyond_previous11_annotation_pending", []):
            disputes.append({"ids": [case_id], "dimension": "新增参考争议", "source": name,
                             "finding": "逐题参考审核发现新争议；详见原AI报告中该编号的理由",
                             "action": "保持冻结标签与评分，待人工决定是否修改"})
        for dispute in data.get("new_reference_or_protocol_disputes", []):
            entry = dict(dispute)
            entry["source"] = name
            entry["dimension"] = "控制器或协议争议" if "控制器" in entry.get("finding", "") else "新增参考争议"
            disputes.append(entry)
    return result, sources, disputes


def raw_turns(case_dir: Path, checkpoint: dict) -> tuple[list[dict], list[dict]]:
    turns, issues = [], []
    for saved in checkpoint.get("turns", []):
        number = saved.get("index")
        if not isinstance(number, int) or number < 0:
            raise ValueError("Invalid preserved turn index")
        turn_dir = case_dir / "turns" / f"{number:03}"
        response_path = turn_dir / "response.raw.json"
        actual, raw_verified = {}, False
        raw_ev = evidence(relative(response_path), "body JSON: 真实原始HTTP响应")
        if response_path.is_file():
            raw = json.loads(response_path.read_text(encoding="utf-8-sig"))
            body = raw.get("body")
            actual = json.loads(body) if isinstance(body, str) else (body if isinstance(body, dict) else {})
            raw_verified = actual == saved.get("response")
            if not raw_verified:
                issues.append({"turn": number, "reason": "原始响应与checkpoint不一致；不合并或猜测"})
        else:
            issues.append({"turn": number, "reason": "缺原始响应；checkpoint不能代替未读取的原始HTTP输出"})
        provider = []
        # Read only archived files inside this case/turn, never permissive global capture paths.
        for path in sorted((turn_dir / "provider").glob("*.json")):
            if not UUID_NAME.fullmatch(path.name):
                raise ValueError("Unexpected provider capture filename: " + path.name)
            record = read(relative(path))
            trace_matches = record.get("trace_id") == actual.get("trace_id")
            system_messages = [m.get("content", "") for m in record.get("request", {}).get("messages", [])
                               if m.get("role") == "system"]
            provider.append({**evidence(relative(path), "request.messages/response; 实际provider原文"),
                             "trace_id_matches_actual_response": trace_matches,
                             "system_character_counts": [len(text) for text in system_messages if isinstance(text, str)]})
            if not trace_matches:
                issues.append({"turn": number, "reason": "provider trace_id未匹配该turn原始响应"})
        nlu = actual.get("metadata", {}).get("nlu", {})
        turns.append({
            "index": number, "phase": saved.get("phase"),
            "request": saved.get("request"), "request_evidence": evidence(relative(turn_dir / "request.json")),
            "raw_response_evidence": raw_ev, "raw_checkpoint_match": raw_verified,
            "actual_http_status": saved.get("http_status"), "actual_latency_ms": saved.get("latency_ms"),
            "actual_status": actual.get("status"), "actual_answer": actual.get("answer"),
            "actual_sql": actual.get("sql"), "actual_table": actual.get("table"),
            "actual_intent": actual.get("intent"), "actual_clarification": actual.get("clarification"),
            "actual_rewritten_question": actual.get("rewritten_question"), "actual_nlu": nlu,
            "actual_error": actual.get("error"), "actual_metadata_clarify": actual.get("metadata", {}).get("clarify"),
            "asked_key": saved.get("asked_key"), "supplement_key": saved.get("supplement_key"),
            "original_provider_archive_count": saved.get("provider_captures_archived", 0),
            "provider_evidence": provider,
            "original_archive_evidence": evidence(relative(turn_dir / "provider-evidence.json")),
            "supplement_evidence": [evidence(relative(path)) for path in sorted(turn_dir.glob("provider-evidence-supplement*.json"))],
        })
    return turns, issues


def version_evidence(spec: dict, expected_ids: set[str]) -> dict:
    version = spec["version"]
    score = read(spec["score"])
    if score.get("version") != version or score.get("labels_sha256") != LABEL_SHA:
        raise ValueError("Version or frozen label hash mismatch: " + version)
    cases = {item["id"]: item for item in score.get("cases", [])}
    if len(cases) != 60 or set(cases) != expected_ids:
        raise ValueError("Incomplete preserved original score: " + version)
    score_ev = evidence(spec["score"], "summary.groups.all + cases[id=原编号]；未重新计分")
    manifest_path = local(spec["run_manifest"])
    if not manifest_path.is_file():
        raise FileNotFoundError("Missing actual run manifest: " + spec["run_manifest"])
    manifest = read(spec["run_manifest"])
    run_dir = manifest_path.parent
    reviewed, review_files, disputes = review_records(spec.get("ai_reviews", []), version, score_ev["sha256"], run_dir.name)
    supplements = read(spec["provider_supplement"]) if spec.get("provider_supplement") else None
    version_cases = {}
    for case_id in sorted(expected_ids):
        case_dir = run_dir / "cases" / case_id
        checkpoint_name = relative(case_dir / "checkpoint.json")
        checkpoint = read(checkpoint_name)
        if checkpoint.get("id") != case_id or checkpoint.get("outcome") in {None, "not_started", "running"}:
            raise ValueError("Unfinished actual checkpoint: " + checkpoint_name)
        turns, issues = raw_turns(case_dir, checkpoint)
        ai = reviewed.get(case_id)
        version_cases[case_id] = {
            "version": version, "actual_run_state": "已有真实运行记录", "outcome": checkpoint.get("outcome"),
            "original_automatic_score": cases[case_id],
            "score_evidence": {**score_ev, "location": f"cases[id={case_id}]"},
            "checkpoint_evidence": evidence(checkpoint_name, "turns[] / controller_events[] / outcome"),
            "controller_events": checkpoint.get("controller_events", []),
            "turns": turns, "evidence_issues": issues,
            "ai_review": ai if ai else {"reference_verdict": "尚未AI核验", "system_verdict": "尚未AI核验",
                                       "reason": "已有真实输出，但未提供该版本逐条AI语义核验报告；不由自动分数推断AI通过"},
        }
    return {"version": version, "score_summary_unchanged": score["summary"], "score_evidence": score_ev,
            "run_manifest_evidence": evidence(spec["run_manifest"]), "run_manifest_unchanged": manifest,
            "code_snapshot_evidence": evidence(spec["code_snapshot"]) if spec.get("code_snapshot") else None,
            "freeze_evidence": evidence(spec["freeze"]) if spec.get("freeze") else None,
            "original_provider_archive_count": sum(turn.get("original_provider_archive_count", 0) for item in version_cases.values() for turn in item["turns"]),
            "actual_archived_provider_files_read": sum(len(turn["provider_evidence"]) for item in version_cases.values() for turn in item["turns"]),
            "provider_supplement_evidence": evidence(spec["provider_supplement"]) if supplements else None,
            "provider_supplement_summary_unchanged": supplements,
            "ai_review_sources": review_files, "ai_cases_read": len(reviewed), "disputes": disputes,
            "cases": version_cases}


def collect(config: dict) -> dict:
    source_labels = labels()
    specs = config.get("versions", [])
    if not specs or specs[0].get("version") != "V0":
        raise ValueError("V0 is required as the preserved baseline")
    names = [spec.get("version") for spec in specs]
    if len(names) > 3 or len(set(names)) != len(names) or any(name not in {"V0", "V1", "V2"} for name in names):
        raise ValueError("Only baseline V0 and at most two actual optimization trials V1/V2 are accepted")
    selected = config.get("selected_final_version") or None
    if selected and selected not in names:
        raise ValueError("Selected final version must be an actual supplied version, including a possible rollback")
    versions = [version_evidence(spec, EXPECTED_IDS) for spec in specs]
    baseline = versions[0]
    if baseline["ai_cases_read"] != 60:
        raise ValueError("The unified table requires all60 V0 independent AI opinions")
    frozen_pending = sorted(row["id"] for row in source_labels if row.get("scorable") is not True)
    cases = []
    for row in sorted(source_labels, key=lambda item: item["id"]):
        case_id = row["id"]
        disputes = [d for v in versions for d in v["disputes"] if case_id in d.get("ids", [])]
        original_reference = {key: value for key, value in row.items() if not key.startswith("_")}
        final = next((v["cases"][case_id] for v in versions if v["version"] == selected), None)
        cases.append({
            "id": case_id, "group": "专项①消歧/改写" if row["task"] == "01" else "专项③分级澄清/续问",
            "task": row["task"], "category": row["category"], "original_source_line": row["_source_line"],
            "input": row["input"], "canonical_input_unchanged": row.get("canonical_input"),
            "frozen_label_group": "冻结可评分49项之一" if row.get("scorable") is True else "原待确认11项之一",
            "frozen_scorable": row.get("scorable") is True,
            "frozen_reference_unchanged": original_reference,
            "reference_evidence": evidence(LABEL, f"line {row['_source_line']}: {case_id}"),
            "V0_reference_ai": baseline["cases"][case_id]["ai_review"],
            "trial_observations": [v["cases"][case_id] for v in versions],
            "selected_final_version": selected,
            "selected_final_review": final if final else {"actual_run_state": "最终版本尚未选择",
                                                        "ai_review": {"reference_verdict": "待最终核验", "system_verdict": "待最终核验"}},
            "new_reference_or_protocol_disputes": disputes,
            "human_review": {"status": "pending_human_review", "reference_decision": "待人工审核",
                             "system_answer_decision": "待人工审核", "controller_decision": "待人工审核",
                             "reference_correction_proposal": "", "system_correction_proposal": "",
                             "requested_restore_target": "", "restore_reason": "", "approved_action": ""},
        })
    new_reference_ids = sorted({i for v in versions for d in v["disputes"] if d["dimension"] == "新增参考争议"
                                for i in d.get("ids", []) if i not in frozen_pending})
    new_protocol_ids = sorted({i for v in versions for d in v["disputes"] if d["dimension"] == "控制器或协议争议"
                               for i in d.get("ids", [])})
    final_ai_count = next((v["ai_cases_read"] for v in versions if v["version"] == selected), 0)
    return {
        "title": TITLE, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "统一人工复核/纠错索引；不替代人工签字，不重计评分，不执行修复或恢复",
        "human_review_status": "pending_human_review", "labels_sha256": LABEL_SHA,
        "selected_final_version": selected, "last_trial_version": names[-1],
        "final_selection_note": "选定最终版本独立于最后一次试验；可选择恢复V0/V1。未选择时不生成最终通过结论。",
        "summary": {"original_cases": 60, "frozen_scorable": 49, "original_annotation_pending": 11,
                    "original_pending_ids": frozen_pending, "V0_ai_cases_read": 60,
                    "V0_reference_ai_opinion_counts": dict(Counter(c["V0_reference_ai"]["reference_verdict"] for c in cases)),
                    "V0_system_ai_opinion_counts": dict(Counter(c["V0_reference_ai"]["system_verdict"] for c in cases)),
                    "selected_final_ai_cases_read": final_ai_count,
                    "new_reference_disputes_beyond_original11": new_reference_ids,
                    "new_controller_or_protocol_disputes": new_protocol_ids,
                    "human_pending_cases": 60,
                    "original_V0_automatic_result_unchanged": baseline["score_summary_unchanged"]["groups"]["all"],
                    "AI_counts_are_not_recalculated_scores": True},
        "versions": [{key: value for key, value in v.items() if key != "cases"} for v in versions],
        "version_decisions_evidence": evidence(config["version_decisions"]) if config.get("version_decisions") else None,
        "restore_instructions_evidence": evidence(config["restore_instructions"]) if config.get("restore_instructions") else None,
        "cases": cases,
        "operations": {"new_API_requests": 0, "new_model_calls": 0, "new_SQL_queries": 0,
                       "business_code_changed": False, "system_prompt_changed": False,
                       "labels_changed": False, "scores_recalculated": False,
                       "human_approval_changed": False, "holdout_content_read": False},
        "limits": ["本轮为合成开发数据，不能推断保留集或真实用户总体性能。",
                   "SQL结果相等不能单独证明业务语义；AI判断与冻结自动分数分开。",
                   "原11项标签待确认与新发现的参考/控制器争议分别展示，不静默调整49分母。",
                   "raw/provider/hash证明材料读取和定位，不能替代题意/口径/完整引用的人工审核。",
                   "恢复/纠错栏仅供填写建议，本构建器不执行恢复、修复或批准。"],
    }


def link(ev: dict | None, output: Path, label: str | None = None) -> str:
    if not ev:
        return "未提供"
    if not ev.get("exists"):
        return "证据不足：" + ev.get("path", "")
    path = local(ev["path"])
    target = Path(os.path.relpath(path, output)).as_posix()
    return "[" + (label or ev["path"]) + "](<" + target + ">)"


def auto_label(score: dict) -> str:
    if score.get("scorable") is not True:
        return "原标签待确认；原评分不计入49"
    state = score.get("automatic_complete")
    return "原自动确认" if state is True else "原自动失败" if state is False else "原自动语义AI_pending"


def compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def render_markdown(report: dict, output: Path) -> str:
    s = report["summary"]
    original = s["original_V0_automatic_result_unchanged"]
    lines = ["# " + TITLE, "", report["purpose"], "",
             f"原编号60项；冻结可评分49项，原待确认11项。人工状态全部 `pending_human_review`。",
             f"V0原自动结果仍为 **{original['correct_over_scorable_tasks']}**（确认{original['confirmed_correct']}、失败{original['automatic_failed']}、语义AI_pending {original['semantic_AI_pending']}）；以下AI意见不替换该分数。",
             f"选定最终版本：**{report['selected_final_version'] or '尚未选择'}**；最后试验版本：{report['last_trial_version']}；最终逐题AI读取{s['selected_final_ai_cases_read']}/60。", "",
             "原11项待确认：" + "、".join(s["original_pending_ids"]),
             "新增参考争议（排除原11项）：" + "、".join(s["new_reference_disputes_beyond_original11"]),
             "控制器/协议争议：" + "、".join(s["new_controller_or_protocol_disputes"]), "",
             "| 分组 | AI建议通过 | AI建议有条件通过 | AI发现错误 | 证据不足 |", "|---|---:|---:|---:|---:|"]
    for title, key in (("V0参考答案", "V0_reference_ai_opinion_counts"), ("V0系统回答", "V0_system_ai_opinion_counts")):
        counts = s[key]
        lines.append("| " + title + " | " + " | ".join(str(counts.get(v, 0)) for v in ["AI建议通过", "AI建议有条件通过", "AI发现错误", "证据不足"]) + " |")
    lines += ["", "以上为60项AI意见分布，不是新准确率。", "",
              "版本选择依据：" + link(report["version_decisions_evidence"], output),
              "恢复说明：" + link(report["restore_instructions_evidence"], output), ""]
    for v in report["versions"]:
        lines += [f"- {v['version']}：{link(v['score_evidence'], output, '原评分')}；{link(v['run_manifest_evidence'], output, '真实运行清单')}；原自动provider归档{v['original_provider_archive_count']}，当前逐条读取实际归档{v['actual_archived_provider_files_read']}；补充核验{link(v['provider_supplement_evidence'], output, '独立补充归档记录')}。"]
    for item in report["cases"]:
        ref = item["frozen_reference_unchanged"]
        ai = item["V0_reference_ai"]
        lines += ["", "## " + item["id"] + " · " + item["group"] + " · " + item["category"], "",
                  "冻结分组：" + item["frozen_label_group"] + "；原题：" + item["input"], "",
                  "原参考/控制器标签：" + link(item["reference_evidence"], output, "冻结题库对应行"),
                  "```json", compact({k: ref.get(k) for k in ["gold_sql", "gold_result", "expected_behavior", "expected_bindings", "expected_predicates", "reference_intent", "controller", "allowed_interpretations", "business_basis", "final_source_guard_issues"]}), "```", "",
                  f"V0参考：**{ai['reference_verdict']}**；{ai['reference_reason']}",
                  f"V0系统回答：**{ai['system_verdict']}**；{ai['system_reason']}",
                  "AI逐题原报告：" + link(ai.get("source"), output), ""]
        for issue in item["new_reference_or_protocol_disputes"]:
            lines.append("- " + issue["dimension"] + "：" + issue["finding"] + "；" + issue.get("action", "保持标签，待人审"))
        for observation in item["trial_observations"]:
            version = observation["version"]
            lines += ["", f"### {version}真实记录", "",
                      f"{auto_label(observation['original_automatic_score'])}；真实outcome={observation['outcome']}。",
                      link(observation["score_evidence"], output, "原评分定位") + "；" + link(observation["checkpoint_evidence"], output, "逐轮checkpoint"),
                      f"该版AI参考：{observation['ai_review']['reference_verdict']}；AI系统：{observation['ai_review']['system_verdict']}。"]
            for turn in observation["turns"]:
                lines += ["", f"第{turn['index']}轮（{turn['phase']}），status={turn['actual_status']}；原始响应/checkpoint一致={turn['raw_checkpoint_match']}。",
                          "```json", compact({k: turn[k] for k in ["request", "actual_answer", "actual_sql", "actual_table", "actual_intent", "actual_clarification", "actual_rewritten_question", "actual_nlu", "actual_error"]}), "```",
                          link(turn["raw_response_evidence"], output, "原始HTTP响应") + "；" + link(turn["request_evidence"], output, "实际请求")]
                for provider in turn["provider_evidence"]:
                    lines.append("- " + link(provider, output, "实际provider输入/输出") + "；SHA=" + provider["sha256"] + "；trace匹配=" + str(provider["trace_id_matches_actual_response"]))
            if observation["evidence_issues"]:
                lines += ["证据问题：", "```json", compact(observation["evidence_issues"]), "```"]
        final = item["selected_final_review"]
        lines += ["", "最终选定版AI系统判断：" + final["ai_review"]["system_verdict"],
                  "仍需人工确认：", "```json", compact(ai.get("needs_human_confirmation", [])), "```", "",
                  "人工参考结论：待审核；人工系统回答结论：待审核；人工控制器结论：待审核。",
                  "参考纠错建议：________；系统纠错建议：________；请求恢复版本：________；恢复理由：________。",
                  "人工状态：`pending_human_review`；此表未填写签名或人工确认日期。"]
    lines += ["", "## 使用和证据说明", ""] + ["- " + text for text in report["limits"]]
    return "\n".join(lines) + "\n"


def render_html(report: dict, output: Path) -> str:
    def evlink(ev, label=None):
        if not ev or not ev.get("exists"):
            return '<span class="missing">证据不足／未提供</span>'
        target = Path(os.path.relpath(local(ev["path"]), output)).as_posix()
        return '<a href="' + html.escape(quote(target, safe="/:.-_"), quote=True) + '">' + html.escape(label or ev["path"]) + '</a>'
    def code(value):
        return "<pre>" + html.escape(compact(value)) + "</pre>"
    s = report["summary"]
    original = s["original_V0_automatic_result_unchanged"]
    parts = ["<!doctype html><html lang=zh-CN><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>",
             "<title>" + TITLE + "</title><style>body{font:16px/1.65 system-ui,'Microsoft YaHei',sans-serif;max-width:1200px;margin:32px auto;padding:0 24px;color:#192734}h1,h2,h3{line-height:1.35}article{border:1px solid #bbcbd7;border-radius:8px;padding:20px;margin:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f8;padding:14px;border-radius:5px;font:13px/1.55 Consolas,monospace}details{margin:14px 0}summary{cursor:pointer;font-weight:600}.missing{color:#a33126}.note{padding:16px;background:#edf5fc}input{width:min(100%,650px);padding:10px;font:inherit}a{color:#15558c}.decision{border:1px dashed #879dad;padding:15px}@media print{input{display:none}article{break-inside:avoid}}</style>",
             "<h1>" + TITLE + "</h1><p>" + html.escape(report["purpose"]) + "</p>",
             f"<div class=note>60个原编号，冻结可评分49／原待确认11；人工全部pending。V0原自动分数仍为<strong>{original['correct_over_scorable_tasks']}</strong>：确认{original['confirmed_correct']}、失败{original['automatic_failed']}、语义AI_pending {original['semantic_AI_pending']}。AI分对象意见不替换原分数。<br>选定最终版本：{html.escape(report['selected_final_version'] or '尚未选择')}；最后试验版本：{report['last_trial_version']}；最终逐题AI读取{s['selected_final_ai_cases_read']}/60。</div>",
             "<p>原11项待确认：" + "、".join(s["original_pending_ids"]) + "</p>",
             "<p>新增参考争议（排除原11项）：" + "、".join(s["new_reference_disputes_beyond_original11"]) + "</p>",
             "<p>控制器/协议争议：" + "、".join(s["new_controller_or_protocol_disputes"]) + "</p>",
             "<p>版本选择：" + evlink(report["version_decisions_evidence"]) + "；恢复说明：" + evlink(report["restore_instructions_evidence"]) + "</p>",
             "<details><summary>AI意见分布与各版本原始汇总</summary>" + code(s) + "</details>",
             '<p><input id=filter aria-label="查找编号或题目" placeholder="筛选原编号、题目或类别；例如 sp01-30"></p>']
    for item in report["cases"]:
        ref, ai = item["frozen_reference_unchanged"], item["V0_reference_ai"]
        search = " ".join([item["id"], item["input"], item["category"], ai["reference_verdict"], ai["system_verdict"]])
        parts += [f'<article id="{item["id"]}" data-search="{html.escape(search, quote=True)}">',
                  "<h2>" + html.escape(item["id"] + " · " + item["group"] + " · " + item["category"]) + "</h2>",
                  "<p>" + html.escape(item["frozen_label_group"]) + "；原题：" + html.escape(item["input"]) + "</p>",
                  "<p>原标签：" + evlink(item["reference_evidence"], "冻结题库对应行") + "</p>",
                  "<details><summary>原参考SQL、标准结果、绑定、条件和控制器（实际读取）</summary>" + code({k: ref.get(k) for k in ["gold_sql", "gold_result", "expected_behavior", "expected_bindings", "expected_predicates", "reference_intent", "controller", "allowed_interpretations", "business_basis", "final_source_guard_issues"]}) + "</details>",
                  "<p><strong>V0参考：" + html.escape(ai["reference_verdict"]) + "</strong>；" + html.escape(ai["reference_reason"]) + "</p>",
                  "<p><strong>V0系统回答：" + html.escape(ai["system_verdict"]) + "</strong>；" + html.escape(ai["system_reason"]) + "</p>",
                  "<p>逐题AI原报告：" + evlink(ai.get("source")) + "</p>"]
        if item["new_reference_or_protocol_disputes"]:
            parts.append("<details open><summary>新增争议；保持原标签与评分</summary>" + code(item["new_reference_or_protocol_disputes"]) + "</details>")
        for obs in item["trial_observations"]:
            parts += ["<details><summary>" + obs["version"] + "真实输出与原始评分 · " + auto_label(obs["original_automatic_score"]) + " · " + html.escape(str(obs["outcome"])) + "</summary>",
                      "<p>" + evlink(obs["score_evidence"], "原评分对应编号") + "；" + evlink(obs["checkpoint_evidence"], "实际checkpoint") + "</p>",
                      "<p>该版本AI参考：" + html.escape(obs["ai_review"]["reference_verdict"]) + "；AI系统：" + html.escape(obs["ai_review"]["system_verdict"]) + "</p>",
                      "<details><summary>原自动评分各维度；不重计</summary>" + code(obs["original_automatic_score"]) + "</details>"]
            for turn in obs["turns"]:
                parts += [f"<h3>第{turn['index']}轮 · {html.escape(str(turn['phase']))} · {html.escape(str(turn['actual_status']))}</h3>",
                          "<p>" + evlink(turn["raw_response_evidence"], "原始HTTP响应") + "；" + evlink(turn["request_evidence"], "实际请求") + "；与checkpoint一致=" + str(turn["raw_checkpoint_match"]) + "</p>",
                          code({k: turn[k] for k in ["request", "actual_answer", "actual_sql", "actual_table", "actual_intent", "actual_clarification", "actual_rewritten_question", "actual_nlu", "actual_error"]})]
                for provider in turn["provider_evidence"]:
                    parts.append("<p>" + evlink(provider, "实际provider输入/输出") + "；trace匹配=" + str(provider["trace_id_matches_actual_response"]) + "；SHA=" + provider["sha256"] + "</p>")
            if obs["evidence_issues"]:
                parts.append('<p class=missing>证据不足／定位问题：</p>' + code(obs["evidence_issues"]))
            parts.append("</details>")
        parts += ["<p>最终选定版AI系统判断：<strong>" + html.escape(item["selected_final_review"]["ai_review"]["system_verdict"]) + "</strong></p>",
                  "<details open><summary>仍需人工确认</summary>" + code(ai.get("needs_human_confirmation", [])) + "</details>",
                  '<div class=decision>人工参考结论：待审核；人工系统结论：待审核；人工控制器结论：待审核。<br>参考纠错建议：________；系统纠错建议：________<br>请求恢复版本：________；恢复理由：________<br>人工状态：pending_human_review。此表未填写签名或人工确认日期；建议在随附JSON相应字段记录纠错意见。</div></article>']
    parts += ["<h2>使用和证据说明</h2><ul>" + "".join("<li>" + html.escape(t) + "</li>" for t in report["limits"]) + "</ul>",
              "<script>document.getElementById('filter').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('article').forEach(e=>e.hidden=!e.dataset.search.toLowerCase().includes(q));});</script></html>"]
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, help="Project-relative actual preserved evidence specification")
    parser.add_argument("--output", default=EXP + "/reports/manual-review", help="Project-relative report directory")
    parser.add_argument("--check-inputs", action="store_true", help="Read/verify actual records without writing the review table")
    args = parser.parse_args()
    config = read(args.inputs)
    report = collect(config)
    issues = [issue for item in report["cases"] for obs in item["trial_observations"] for issue in obs["evidence_issues"]]
    final_ready = (bool(report["selected_final_version"])
                   and report["summary"]["selected_final_ai_cases_read"] == 60 and not issues)
    result = {"original_cases_read": 60, "frozen_scorable": 49, "original_pending": 11,
              "V0_AI_cases_read": 60, "selected_final_version": report["selected_final_version"],
              "selected_final_AI_cases_read": report["summary"]["selected_final_ai_cases_read"],
              "ready_for_baseline_review": True, "ready_for_final_review": final_ready,
              "actual_evidence_issues": len(issues), "labels_sha256": LABEL_SHA,
              "original_V0_confirmed_over_scorable": report["summary"]["original_V0_automatic_result_unchanged"]["correct_over_scorable_tasks"],
              "AI_opinions_do_not_replace_original_score": True,
              "new_API_requests": 0, "new_model_calls": 0, "new_SQL_queries": 0, "holdout_content_read": False}
    if args.check_inputs:
        print(compact(result))
        return 0 if final_ready else 2
    if not report["selected_final_version"]:
        raise ValueError("Choose the actual final version before creating the final manual review table")
    output = local(args.output)
    output.mkdir(parents=True, exist_ok=True)
    md, page = render_markdown(report, output), render_html(report, output)
    (output / (TITLE + ".json")).write_text(compact(report) + "\n", encoding="utf-8")
    (output / (TITLE + ".md")).write_text(md, encoding="utf-8")
    (output / (TITLE + ".html")).write_text(page, encoding="utf-8")
    (output / "build-command.txt").write_text("cwd: system\n" + ".\\.venv\\Scripts\\python.exe -B scripts/build_special_review.py --inputs " + args.inputs + " --output " + args.output + "\n", encoding="utf-8")
    print(compact({**result, "output": relative(output), "human_review_status": "pending_human_review"}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        print("Evidence validation failed: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
