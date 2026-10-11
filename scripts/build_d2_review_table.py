"""Build one offline D2 human-review table from existing gold and actual runs.

Read only: no LLM calls, database access, dataset approval, or holdout evaluation.
The JSON is the common data source for the Markdown and self-contained HTML.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.dataset import review_hash as sql_review_hash, reviewed as sql_reviewed
from eval.rag_dataset import review_hash as rag_review_hash, reviewed as rag_reviewed

GROUPS = {"metric": "已共同确认的四项业务口径", "alias": "别名候选（81 项）",
          "nl2sql": "单表 SQL 标准与实际回答（50 题）",
          "robust": "鲁棒变体及语义保持（30 题）", "rag": "RAG 标准与实际回答（30 题）"}
DATASETS = {"nl2sql": "eval/datasets/nl2sql_chinook_d2.jsonl",
            "robust": "eval/datasets/robust.jsonl", "rag": "eval/datasets/rag_single.jsonl"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf8")).hexdigest()


def load_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8-sig"))


def load_jsonl(relative: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / relative).read_text(encoding="utf-8-sig").splitlines()
            if line.strip()]


def csv_rows(relative: str) -> list[dict]:
    with (ROOT / relative).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def reference(relative: str, *, line: int | None = None) -> dict:
    path = ROOT / relative
    result = {"path": relative, "sha256": digest(path), "exists": True}
    if line is not None:
        result["line"] = line
    return result


def actual_runs(suite: str, items: list[dict]) -> tuple[dict[str, dict], dict]:
    selected = next((f"eval/artifacts/d2/{suite}/{phase}/responses.jsonl"
                     for phase in ("final", "initial")
                     if (ROOT / f"eval/artifacts/d2/{suite}/{phase}/responses.jsonl").is_file()), None)
    if selected is None:
        return {}, {"path": None, "phase": "not_run", "row_count": 0}
    rows = load_jsonl(selected)
    permitted = {item["id"] for item in items if item["split"] == "dev"}
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate response ID in {selected}")
    if unexpected := set(ids) - permitted:
        raise ValueError(f"Non-dev/unknown predictions in {selected}: {sorted(unexpected)}")
    source = reference(selected)
    source.update(phase=selected.split("/")[-2], row_count=len(rows))
    return {row["id"]: {"record": row, "source": reference(selected, line=i)}
            for i, row in enumerate(rows, 1)}, source


def document_evidences(values: list[dict], documents: dict[str, dict]) -> list[dict]:
    result = []
    for evidence in values:
        evidence = dict(evidence)
        doc = documents.get(evidence.get("doc_id"))
        if doc:
            path = doc.get("relative_path") or doc["path"]
            evidence["source_file"] = reference(path)
            evidence["source_url"] = doc.get("source_url_or_dataset_id") or doc.get("source_url")
            evidence["registered_source_sha256"] = doc.get("content_sha256") or doc.get("content_hash")
        result.append(evidence)
    return result


def blank_review(gold_accepted: bool = False) -> dict:
    return {"status": "accepted" if gold_accepted else "pending_human_review",
            "gold_semantics": "accepted" if gold_accepted else "pending_human_review",
            "actual_answer_correctness": "pending_human_review",
            "actual_answer_faithfulness": "pending_human_review",
            "reviewer_A": "", "reviewer_B": "", "reviewed_at": "", "comments": ""}


def build_payload() -> dict:
    documents = {row["doc_id"]: row for row in csv_rows("data/docs/manifest.csv")}
    rows: list[dict] = []
    provenance: dict[str, Any] = {"documents": reference("data/docs/manifest.csv")}
    definitions = load_json("data/rules/metric_definitions.json")
    confirmation = load_json("eval/artifacts/d2/source/metric-human-review.json")
    if definitions.get("review_status") != "approved" or confirmation.get("review_status") != "approved":
        raise ValueError("The four metric definitions lack the recorded explicit approval")
    metric_examples = {row["id"]: row for row in load_json("eval/artifacts/d2/source/metric-sql-checks.json")["records"]}
    examples = {"sales_revenue": "revenue_invoice", "average_invoice_amount": "average_invoice",
                "repeat_customer_count": "repeat_customers", "popular_tracks": "popular_tracks"}
    for metric in definitions["metrics"]:
        example = metric_examples[examples[metric["id"]]]
        rows.append({"review_id": f"metric:{metric['id']}", "group": "metric", "id": metric["id"],
                     "split": None, "title": metric["name"],
                     "review_focus": "已有明确共同确认记录；留存口径与 SQL 只读执行证据，不要求重复审核。",
                     "expected": {"definition": metric, "general_rules": definitions["general"],
                                  "readonly_sql_example": example},
                     "actual": None, "actual_run_status": "not_applicable",
                     "machine_checks": {"sql_example_status": example["status"],
                                        "runtime_defaults_enabled": definitions["runtime_defaults_enabled"]},
                     "evidence_files": [reference("data/rules/metric_definitions.json"),
                                        reference("eval/artifacts/d2/source/metric-human-review.json"),
                                        reference("eval/artifacts/d2/source/metric-sql-checks.json")],
                     "hashes": {"content_sha256": content_hash(metric),
                                "confirmed_proposal_sha256": confirmation["proposal_sha256"]},
                     "review": {"status": "approved", "gold_semantics": "not_applicable",
                                "actual_answer_correctness": "not_applicable",
                                "actual_answer_faithfulness": "not_applicable",
                                "reviewer_A": definitions["reviewer_a"], "reviewer_B": definitions["reviewer_b"],
                                "reviewed_at": definitions["reviewed_at_utc"],
                                "comments": confirmation["statement"]}})

    alias_path = "data/aliases/aliases.csv"
    aliases = csv_rows(alias_path)
    selection = load_json("eval/artifacts/d2/aliases-review-selection.json")
    selection_matches = digest(ROOT / alias_path) == selection["expected_sha256"]
    propose_yes, propose_no = set(selection["approve_ids"]), set(selection["reject_ids"])
    reject_notes = {("Metallica", "金属"): "泛称“金属”不能唯一代表 Metallica。",
                    ("Iron Maiden", "铁处女"): "不作为本项目默认中文乐队名。",
                    ("Rock And Roll", "节奏摇滚"): "不足以唯一对应 Rock And Roll。"}
    provenance["aliases"] = reference(alias_path)
    provenance["alias_selection"] = reference("eval/artifacts/d2/aliases-review-selection.json")
    for line, alias in enumerate(aliases, 2):
        suggestion = "建议通过" if alias["alias_id"] in propose_yes else "建议拒绝" if alias["alias_id"] in propose_no else "未给建议"
        note = reject_notes.get((alias["standard_value"], alias["alias"]),
                                "匹配必须限定字段；同一别名对应多个标准值时保留候选并澄清。")
        review = blank_review()
        review["gold_semantics"] = "not_applicable"
        review["actual_answer_correctness"] = review["actual_answer_faithfulness"] = "not_applicable"
        rows.append({"review_id": f"alias:{alias['alias_id']}", "group": "alias", "id": alias["alias_id"],
                     "split": None, "title": f"{alias['alias']} → {alias['column']} = {alias['standard_value']}",
                     "review_focus": "核对别名是否确实对应这个字段下的真实标准值，以及多义候选是否合理。",
                     "expected": {"alias": alias["alias"], "column": alias["column"],
                                  "standard_value": alias["standard_value"], "source": alias["source"],
                                  "registered_review_status": alias["review_status"]},
                     "actual": None, "actual_run_status": "not_applicable",
                     "machine_checks": {"recommendation_only": suggestion, "recommendation_reason": note,
                                        "selection_csv_hash_matches": selection_matches,
                                        "human_approval": False},
                     "evidence_files": [reference(alias_path, line=line),
                                        reference("notes/d2-alias-review.md"),
                                        reference("eval/artifacts/d2/aliases-review-selection.json")],
                     "hashes": {"content_sha256": content_hash(alias), "csv_sha256": digest(ROOT / alias_path),
                                "recommendation_expected_csv_sha256": selection["expected_sha256"]}, "review": review})

    for suite, dataset_path in DATASETS.items():
        items = load_jsonl(dataset_path)
        prediction_map, run_source = actual_runs(suite, items)
        provenance[suite] = {"dataset": reference(dataset_path), "actual_run": run_source}
        for line, item in enumerate(items, 1):
            holdout = item["split"] == "holdout"
            registered = prediction_map.get(item["id"])
            response = (registered["record"].get("response") or {}) if registered else {}
            record = registered["record"] if registered else {}
            hash_fn, reviewed_fn = (rag_review_hash, rag_reviewed) if suite == "rag" else (sql_review_hash, sql_reviewed)
            review = blank_review(reviewed_fn(item))
            if holdout:
                review["actual_answer_correctness"] = review["actual_answer_faithfulness"] = "deferred_until_D5"
            actual = None
            files = [reference(dataset_path, line=line)]
            if registered:
                files.append(registered["source"])
                actual = {"http_status": record.get("http_status"), "trace_id": response.get("trace_id"),
                          "status": response.get("status"), "answer": response.get("answer"),
                          "rewritten_question": response.get("rewritten_question"),
                          "sql": response.get("sql"), "table": response.get("table"),
                          "evidences": document_evidences(response.get("evidences") or [], documents),
                          "clarification": response.get("clarification"), "intent": response.get("intent"),
                          "error": response.get("error"), "latency_ms": record.get("latency_ms"),
                          "error_type": record.get("error_type"), "error_code": record.get("error_code"),
                          "metadata": response.get("metadata") or {}}
            if suite == "rag":
                expected = {"answer": item["answer"], "answerable": item.get("answerable", True),
                            "expected_status": item.get("expected_status", "SUCCEEDED"),
                            "doc_id": item["doc_id"], "doc_title": item["doc_title"],
                            "source_type": item.get("source_type"), "source_scope": item.get("source_scope"),
                            "reference_text": item["reference_text"], "physical_pages": item["physical_pages"],
                            "page_numbering": item["page_numbering"],
                            "gold_evidence": document_evidences(item.get("gold_evidence", []), documents),
                            "source_qa_id": item.get("source_qa_id"), "source_qa_url": item.get("source_qa_url")}
                checks = {"gold_source_checks": item.get("machine_verification"),
                          "actual_metrics": record.get("metrics"), "actual_failure": record.get("failure"),
                          "human_acceptance": False}
                focus = "合并核对题意/标准答案/来源定位；开发集还需核对实际回答正确性、引用支持范围与忠实度。"
            else:
                expected = {key: item.get(key) for key in ("gold_sql", "gold_result", "gold_columns", "column_types",
                            "ordered", "monetary_columns", "integer_columns", "expected_status", "category",
                            "base_id", "variant_type", "family_id", "db_id", "gold_generated_at_utc")}
                checks = {"automatic_EX_matched": record.get("matched"), "comparison": record.get("comparison"),
                          "failure_category": record.get("failure_category"),
                          "human_acceptance": False}
                focus = "核对题意、标准 SQL 和已执行 gold 结果；开发集还需核对实际 SQL/结果是否满足题意。"
                if suite == "robust":
                    focus += "同时确认改写与 base_id 题语义保持一致。"
            rows.append({"review_id": f"{suite}:{item['id']}", "group": suite, "id": item["id"],
                         "split": item["split"], "title": item["question"], "review_focus": focus,
                         "expected": expected, "actual": actual,
                         "actual_run_status": "D5待测（保留集未调用模型）" if holdout else
                                              f"已实跑（{run_source['phase']}）" if registered else "未找到实际预测记录",
                         "machine_checks": checks, "evidence_files": files,
                         "hashes": {"gold_content_sha256": hash_fn(item),
                                    "registered_review_sha256": item.get("gold_review", {}).get("content_sha256"),
                                    "source_sha256": item.get("source_sha256"),
                                    "source_qa_sha256": item.get("source_qa_sha256"),
                                    "actual_response_sha256": content_hash(record) if registered else None},
                         "review": review})

    counts = Counter(row["group"] for row in rows)
    if dict(counts) != {"metric": 4, "alias": 81, "nl2sql": 50, "robust": 30, "rag": 30}:
        raise ValueError(f"Unexpected D2 review scope: {dict(counts)}")
    cases = [row for row in rows if row["group"] in DATASETS]
    holds = [row for row in cases if row["split"] == "holdout"]
    if len(holds) != 33 or any(row["actual"] is not None for row in holds):
        raise ValueError("The 33 holdout cases must not contain actual model predictions")
    return {"title": "D2 统一待审核表", "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "原清单对应的别名、SQL、鲁棒及 RAG 审核材料；四项已确认口径仅保留原确认记录。",
            "counts": {"total_rows": len(rows), "pending_rows": sum(row["review"]["status"] == "pending_human_review" for row in rows),
                       "previously_approved_metrics": 4, "by_group": dict(counts), "gold_cases": len(cases),
                       "human_gold_accepted": sum(row["review"]["gold_semantics"] == "accepted" for row in cases),
                       "actual_dev_predictions": sum(row["actual"] is not None for row in cases),
                       "human_actual_predictions_accepted": 0, "holdout_cases": len(holds), "holdout_predictions": 0},
            "provenance": provenance, "rows": rows}


def readable_details(row: dict) -> list[tuple[str, Any]]:
    return [("需要核对", row["review_focus"]), ("题目 / 别名 / 口径", row["title"]),
            ("标准材料（SQL 的 gold 结果为已实际执行保存结果）", row["expected"]),
            ("实际运行状态", row["actual_run_status"]),
            ("实际回答、SQL、结果及引用（保留集此栏为空）", row["actual"]),
            ("机器核对 / 建议（不等于人工审核）", row["machine_checks"]),
            ("审核内容绑定 SHA-256", row["hashes"]), ("人工审核记录", row["review"])]


def text_value(value: Any) -> str:
    if value is None:
        return "无实际预测；保留集 D5 冻结后测试。"
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)


def href(path: str, output_dir: Path) -> str:
    return quote(os.path.relpath(ROOT / path, output_dir).replace("\\", "/"), safe="/.-_")


def anchor(row: dict) -> str:
    return row["review_id"].replace(":", "-")


def render_markdown(payload: dict, output_dir: Path) -> str:
    count = payload["counts"]
    lines = ["# D2 统一待审核表", "", f"生成时间：{payload['generated_at_utc']}（UTC）。", "",
             f"共 **{count['pending_rows']} 项待审**：81 别名、50 SQL、30 鲁棒、30 RAG；另列 4 项已有共同确认的业务口径。",
             f"110 道 gold 人工接受 **{count['human_gold_accepted']}**；{count['actual_dev_predictions']} 条开发集真实预测人工语义接受 **0**；33 道保留题实际预测 **0**，D5 待测。", "",
             "自动 EX、字面匹配、引用结构校验和建议取舍均为机器信息。A、B、日期、意见留空；本文件不改变数据集和别名的审核状态。",
             "PDF 页码从 1 起，封面计页；非 PDF 的 page=null，以 section_path/text/bbox 定位。HTML 与此文档来自同一 JSON，离线可查看完整内嵌材料。", "",
             "实跑记录优先 final；没有 final 时标注 initial。每条链接按此文档所在目录计算相对路径，标签为项目内路径。", "",
             "## 目录", ""]
    for group, title in GROUPS.items():
        lines.append(f"- [{title}](#{group})")
    lines.extend(["", "## 本次实际记录来源", "", "```json", json.dumps(payload["provenance"], ensure_ascii=False, indent=2), "```", ""])
    for group, title in GROUPS.items():
        lines.extend([f'<a id="{group}"></a>', "", f"## {title}", "",
                      "| 编号 | 分组 | 问题 / 候选 | 状态 |", "| --- | --- | --- | --- |"])
        selected = [row for row in payload["rows"] if row["group"] == group]
        for row in selected:
            short = row["title"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| [{row['id']}](#{anchor(row)}) | {row['split'] or '—'} | {short} | {row['review']['status']} |")
        lines.append("")
        for row in selected:
            lines.extend([f'<a id="{anchor(row)}"></a>', "", f"### {row['id']} · {row['split'] or '记录'}", ""])
            for title_, value in readable_details(row):
                lines.extend([f"**{title_}**", "", "```text", text_value(value).replace("```", "` ` `"), "```", ""])
            lines.extend(["**证据文件（项目相对路径、文件 SHA-256、行号）**", ""])
            for evidence in row["evidence_files"]:
                location = f"；第 {evidence['line']} 行" if "line" in evidence else ""
                lines.append(f"- [{evidence['path']}]({href(evidence['path'], output_dir)}){location}；SHA-256 `{evidence['sha256']}`")
            if group != "metric":
                lines.extend(["", "A：________　B：________　日期：________　意见：________", ""])
    return "\n".join(lines)


def render_html(payload: dict, output_dir: Path) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    counts = payload["counts"]
    sections = []
    for group, title in GROUPS.items():
        body = []
        for row in [row for row in payload["rows"] if row["group"] == group]:
            fields = "".join(f"<h4>{esc(label)}</h4><pre>{esc(text_value(value))}</pre>" for label, value in readable_details(row))
            links = "".join(f'<li><a href="{esc(href(e["path"], output_dir))}">{esc(e["path"])}</a>'
                            + (f'；第 {e["line"]} 行' if "line" in e else "")
                            + f'<br>SHA-256 <code>{esc(e["sha256"])}</code></li>' for e in row["evidence_files"])
            blanks = "" if group == "metric" else '<p class="review-blank">A：________　B：________　日期：________<br>意见：________________________________</p>'
            body.append(f'<tr id="{esc(anchor(row))}" class="review-row" data-group="{group}" data-split="{row["split"] or ""}">'
                        f'<td><code>{esc(row["id"])}</code><br>{esc(row["split"] or "记录")}</td>'
                        f'<td><div class="question">{esc(row["title"])}</div><details><summary>展开标准材料、真实回答和证据</summary>'
                        f'{fields}<h4>证据文件（项目相对路径）</h4><ul>{links}</ul>{blanks}</details></td>'
                        f'<td>{esc(row["review"]["status"])}<br><small>{esc(row["actual_run_status"])}</small></td></tr>')
        sections.append(f'<section id="{group}"><h2>{esc(title)}</h2><table><thead><tr><th>编号 / 分组</th><th>核对内容</th><th>状态</th></tr></thead><tbody>{"".join(body)}</tbody></table></section>')
    nav = " · ".join(f'<a href="#{g}">{esc(t)}</a>' for g, t in GROUPS.items())
    css = """body{font:15px/1.6 system-ui,'Microsoft YaHei',sans-serif;color:#202830;max-width:1220px;margin:24px auto;padding:0 18px}h1{font-size:27px}h2{font-size:22px;margin-top:36px}h4{margin-bottom:8px}a{color:#075eb1;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #ccd3da;padding:12px;vertical-align:top;text-align:left}th:nth-child(1){width:140px}th:nth-child(3){width:180px}th{background:#f2f5f8}.question{font-weight:600;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7f9;padding:12px;font:13px/1.6 Consolas,'Microsoft YaHei',monospace}code{font-size:13px;overflow-wrap:anywhere}summary{cursor:pointer;color:#075eb1;padding-top:8px}.review-blank{border-top:1px solid #ccd3da;padding-top:12px}small{display:inline-block;color:#5c6670;margin-top:10px}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}.toolbar input,.toolbar select,.toolbar button{padding:8px;font:inherit;border:1px solid #abb8c6;border-radius:4px}.toolbar input{width:350px;max-width:100%}.notice{border-left:4px solid #527ca2;background:#f2f5f8;padding:10px 16px}[hidden]{display:none!important}@media(max-width:650px){body{padding:0 8px}th,td{padding:6px}th:nth-child(1){width:85px}th:nth-child(3){width:100px}pre{padding:7px;font-size:12px}}@media print{.toolbar{display:none}body{max-width:none;font-size:11px}pre{font-size:9px}details{display:block}table{table-layout:auto}}"""
    script = """const q=document.querySelector('#query'),s=document.querySelector('#split');function filter(){for(const r of document.querySelectorAll('.review-row'))r.hidden=!(r.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!s.value||r.dataset.split===s.value));}q.addEventListener('input',filter);s.addEventListener('change',filter);document.querySelector('#expand').addEventListener('click',()=>document.querySelectorAll('.review-row:not([hidden]) details').forEach(d=>d.open=true));document.querySelector('#collapse').addEventListener('click',()=>document.querySelectorAll('details').forEach(d=>d.open=false));"""
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>D2 统一待审核表</title><style>{css}</style></head><body>' \
        f'<h1>D2 统一待审核表</h1><p>生成时间：{esc(payload["generated_at_utc"])}（UTC）。共 <strong>{counts["pending_rows"]} 项待审</strong>，另有 4 项已共同确认口径。</p>' \
        f'<p>110 道 gold 人工接受 <strong>{counts["human_gold_accepted"]}</strong>；{counts["actual_dev_predictions"]} 条开发集真实预测人工语义接受 <strong>0</strong>；33 道保留题实际预测 <strong>0</strong>，D5 待测。</p>' \
        '<div class="notice">自动 EX、字面匹配、引用校验与建议取舍均为机器信息，不能当作人工审核。待审记录的 A、B、日期和意见为空；本表不改变题库或别名状态。PDF 页码从 1 起，封面计页；非 PDF 以 section_path/text/bbox 定位。正文内嵌标准材料与真实回答，无需联网。证据附件链接按报告目录计算相对路径，解压后保留项目目录即可打开。</div>' \
        f'<p>{nav}</p><div class="toolbar"><input id="query" aria-label="搜索" placeholder="搜索编号、题目、SQL、实际回答或证据"><select id="split" aria-label="分组"><option value="">全部分组</option><option value="dev">仅开发集</option><option value="holdout">仅保留集（D5 待测）</option></select><button id="expand">展开可见条目</button><button id="collapse">收起全部条目</button></div>' \
        f'<details id="provenance"><summary>本次实际记录来源与文件 SHA-256</summary><pre>{esc(json.dumps(payload["provenance"], ensure_ascii=False, indent=2))}</pre></details>' \
        f'{"".join(sections)}<script>{script}</script></body></html>'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "eval/reports/d2-acceptance")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(ROOT)
    payload = build_payload()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "unified-review.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output_dir / "unified-review.md").write_text(render_markdown(payload, output_dir), encoding="utf8")
    (output_dir / "unified-review.html").write_text(render_html(payload, output_dir), encoding="utf8")
    print(json.dumps({"output_dir": output_dir.relative_to(ROOT).as_posix(), "counts": payload["counts"],
                      "selected_run_phases": {key: value["actual_run"]["phase"] for key, value in payload["provenance"].items()
                                              if isinstance(value, dict) and "actual_run" in value}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
