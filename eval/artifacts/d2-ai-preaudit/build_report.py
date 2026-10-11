"""Build separate AI suggestions without editing any human review record."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = Path(__file__).resolve().parent
OUT = ROOT / "eval/reports/d2-ai-preaudit"
STEM = "D2统一待审核表-AI预审报告"
STATUSES = {"AI建议通过", "AI建议有条件通过", "AI发现错误", "证据不足"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stringify(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def relative(name):
    return os.path.relpath(ROOT / name, OUT).replace("\\", "/")


def evidence_markdown(item):
    if isinstance(item, str):
        return item
    name = item.get("path", item.get("url", ""))
    locator = "; ".join(f"{key}={stringify(value)}" for key, value in item.items()
                        if key not in {"path", "url", "sourcequote", "quote", "text"})
    if name.startswith(("https://", "http://")):
        target = name
    elif name and (ROOT / name).exists():
        target = relative(name)
    else:
        return stringify(item)
    return f"[{name}]({target})" + (f" — {locator}" if locator else "")


def read_rows(name):
    data = load(OUT / name)
    return data if isinstance(data, list) else data["rows"]


def materials_markdown(row):
    pieces = []
    for key, label in [("reference", "参考SQL与保存结果"), ("existing_actual", "已有系统SQL、表格与回答"),
                       ("reference_answer", "RAG标准答案"), ("actual_answer", "RAG已有系统回答")]:
        if row.get(key) is not None:
            value = row[key]
            content = stringify(value)
            if not isinstance(value, str):
                content = "```json\n" + content + "\n```"
            pieces.append(f"**{label}：**\n\n{content}")
    return pieces


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original = load(ROOT / "eval/reports/d2-acceptance/unified-review.json")
    original_map = {row["review_id"]: row for row in original["rows"]}
    reviewed = []
    for name, count in [("aliases-review.json", 81), ("sql-review.json", 56),
                        ("metrics-review.json", 4), ("rag-review.json", 21)]:
        segment = read_rows(name)
        if len(segment) != count:
            raise ValueError(f"Expected {count} rows in {name}, got {len(segment)}")
        reviewed.extend(segment)
    if len({row["review_id"] for row in reviewed}) != 162:
        raise ValueError("Repeated or missing review IDs")
    rows = []
    for item in reviewed:
        original_item = original_map[item["review_id"]]
        if original_item["split"] == "holdout":
            raise ValueError("Holdout content appeared in a development-side AI review")
        if item["reference_status"] not in STATUSES:
            raise ValueError(f"Invalid AI status for {item['review_id']}")
        row = dict(item)
        row.update({"id": original_item["id"], "group": original_item["group"],
                    "split": original_item["split"], "subject": original_item["title"],
                    "review_scope": "already_confirmed_basis" if original_item["group"] == "metric" else "reviewed_development_materials"})
        rows.append(row)
    for item in original["rows"]:
        if item["split"] != "holdout":
            continue
        rows.append({"review_id": item["review_id"], "id": item["id"], "group": item["group"], "split": "holdout",
            "subject": "保留题内容本轮未审核", "review_scope": "skipped_holdout_not_isolated",
            "reference_status": "本轮跳过（保留集未隔离）", "actual_status": "未运行",
            "reason": "本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。",
            "issues": [], "suggestion": "在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。",
            "human_confirmation": "需要团队安排独立的保留集标签审核环境。", "evidence": [], "evidence_complete": False})
    order = {row["review_id"]: i for i, row in enumerate(original["rows"])}
    rows.sort(key=lambda row: order[row["review_id"]])
    if len(rows) != 195 or {row["review_id"] for row in rows} != set(original_map):
        raise ValueError("Report must preserve all 195 original review IDs")
    reviewed = [row for row in rows if row["review_scope"] != "skipped_holdout_not_isolated"]
    ref_counts = Counter(row["reference_status"] for row in reviewed)
    actual_counts = Counter(row["actual_status"] for row in reviewed if row.get("split") == "dev")
    incomplete = [row["review_id"] for row in reviewed if not row.get("evidence_complete", False)]
    with_issues = [row["review_id"] for row in reviewed if row.get("issues")]
    error_ids = [row["review_id"] for row in reviewed if row["reference_status"] == "AI发现错误"
                 or row.get("actual_status") == "AI发现错误"
                 or row.get("citation_support_status") == "AI发现错误"
                 or row.get("citation_location_status") == "AI发现错误"]
    checks = load(ARTIFACTS / "evidence-integrity.json")
    access = load(ARTIFACTS / "material-access.json")
    database = load(ARTIFACTS / "database-materials.json")
    baseline = load(ARTIFACTS / "protected-inputs-before.json")
    changed = [name for name, digest in baseline["file_sha256"].items()
               if not (ROOT / name).is_file() or sha(ROOT / name) != digest]
    preservation = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
                    "protected_file_count": len(baseline["file_sha256"]), "changed_paths": changed,
                    "status": "PASS" if not changed else "FAIL"}
    (ARTIFACTS / "protected-inputs-after.json").write_text(json.dumps(preservation, ensure_ascii=False, indent=2), encoding="utf-8")
    if changed:
        raise ValueError("Original protected project files changed; report generation stopped")
    summary = {"original_rows": 195, "pending_rows": 191, "reviewed_pending_rows": 158,
        "reviewed_confirmed_basis_rows": 4, "total_rows_content_reviewed": 162,
        "skipped_holdout_rows": 33, "actual_development_outputs_reviewed": 77,
        "reference_status_counts": {status: ref_counts[status] for status in ["AI建议通过", "AI建议有条件通过", "AI发现错误", "证据不足"]},
        "actual_status_counts": {status: actual_counts[status] for status in ["AI建议通过", "AI建议有条件通过", "AI发现错误", "证据不足"]},
        "rows_with_explicit_material_evidence": 162 - len(incomplete),
        "rows_with_incomplete_material_evidence": len(incomplete), "incomplete_material_review_ids": incomplete,
        "rows_with_issues_or_restrictions": len(with_issues), "issue_or_restriction_review_ids": with_issues,
        "error_rows": len(set(error_ids)), "error_review_ids": sorted(set(error_ids)),
        "alias_disposition_counts": {status: sum(row.get("alias_disposition") == status for row in reviewed if row["group"] == "alias")
                                     for status in ["建议直接使用", "仅作为条件候选", "建议拒绝", "证据不足"]},
        "rag_answer_correctness_counts": dict(Counter(row.get("answer_correctness_status", "未分类") for row in reviewed if row["group"] == "rag")),
        "rag_citation_support_counts": dict(Counter(row.get("citation_support_status", "未分类") for row in reviewed if row["group"] == "rag")),
        "rag_citation_location_counts": dict(Counter(row.get("citation_location_status", "未分类") for row in reviewed if row["group"] == "rag")),
        "rag_source_question_type_counts": dict(Counter(row.get("source_question_type", "未分类") for row in reviewed if row["group"] == "rag")),
        "original_files_unchanged": preservation["protected_file_count"]}
    result = {"title": "D2统一待审核表 AI预审报告", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "AI_SUGGESTIONS_ONLY_HUMAN_REVIEW_UNCHANGED", "summary": summary,
        "policy": {"human_review": "不替代人工签字；原pending_human_review、别名pending、A/B签名和人工日期均未改动。",
                   "modifications": "所有新增文件仅保存在独立AI预审报告和证据目录；没有修改系统、提示词、数据、gold或别名状态。",
                   "holdout": "当前开发会话不能隔离，跳过33道保留题的内容审核；逐项仅记录编号与进度。",
                   "execution": "新查询只读执行已有SQL以核验标签或原预测SQL，未向被测问答系统请求任何新预测。",
                   "evidence": "材料可读/哈希相符只说明来源完整性，不等于语义审核通过；参考答案和实际回答分别判断。"},
        "material_access": access, "evidence_integrity_summary": {"status": checks["status"],
            "development_outputs": len(checks["development_record_checks"]), "documents": len(checks["document_checks"])},
        "database_access": {"status": database["status"], "identity": database.get("identity"),
                            "query_count": len(database["queries"]), "errors": database["errors"]},
        "preservation": preservation, "rows": rows}
    (OUT / f"{STEM}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# D2统一待审核表 AI预审报告", "", "本报告为AI建议，不代替A/B人工审核；原表和所有业务材料保持原样。", "",
        "## 范围、实际可访问材料与隔离", "",
        "原表195行：81别名＋50 SQL＋30鲁棒＋30 RAG＋4既有口径。本轮内容预审162行，其中158待审条目、4既有口径依据；已有系统输出77条。", "",
        "当前会话承接开发工作，无法隔离保留集，因此33道保留题仅记编号和进度，不展开题目、答案或来源，不生成系统预测或成绩。", "",
        f"数据库核验：{database['status']}；角色qa_reader，事务只读，statement_timeout=5s。访问及查询详情见下列新证据。", "",
        f"[材料访问登记]({relative('eval/artifacts/d2-ai-preaudit/material-access.json')}) · "
        f"[数据库实际材料与查询]({relative('eval/artifacts/d2-ai-preaudit/database-materials.json')}) · "
        f"[77条原输出及13文档来源一致性]({relative('eval/artifacts/d2-ai-preaudit/evidence-integrity.json')}) · "
        f"[原文件保持原样核验]({relative('eval/artifacts/d2-ai-preaudit/protected-inputs-after.json')})", "",
        "新核验与旧运行记录分开保存。49条数据库材料查询、130条标准/已有预测SQL及辅助查询均为只读SELECT；后者不是重新向问答系统生成预测。RAG实际读10个开发题相关原文、提取并渲染15个完整PDF物理页，逐题检查已有引用；别名的外部来源仅核对译名用法，不用于补足限定文档的RAG答案。", "",
        "[别名独立分报告](aliases-review.md) · [SQL/鲁棒独立分报告](sql-review.md) · "
        "[四项口径独立分报告](metrics-review.md) · [RAG独立分报告](rag-review.md) · "
        f"[新SQL核验命令]({relative('eval/artifacts/d2-ai-preaudit/sql-command-record.json')}) · "
        f"[130条SQL与实际结果]({relative('eval/artifacts/d2-ai-preaudit/sql-verification.jsonl')})", "",
        "## 数量汇总", "",
        "| 审核对象或维度 | 已核验 | AI建议通过 | AI建议有条件通过 | AI发现错误 | 证据不足 |",
        "|---|---:|---:|---:|---:|---:|",
        "| 别名关系 | 81 | 54 | 25 | 0 | 2 |",
        "| SQL与鲁棒题参考答案 | 56 | 54 | 2 | 0 | 0 |",
        "| SQL与鲁棒题已有系统回答 | 56 | 54 | 1 | 0 | 1 |",
        "| RAG参考答案 | 21 | 21 | 0 | 0 | 0 |",
        "| RAG完整回答正确性 | 21 | 20 | 1 | 0 | 0 |",
        "| RAG引用语义支持 | 21 | 20 | 1 | 0 | 0 |",
        "| RAG引用定位 | 21 | 11 | 0 | 10 | 0 |",
        "| 既有已确认业务口径与本次材料一致性 | 4 | 4 | 0 | 0 | 0 |", "",
        "这些维度不能相加作为题数。77条已有回答的整体判断为65条建议通过、11条有条件通过、1条证据不足；其中10条RAG整体有条件通过的题，引用定位维度明确标为“AI发现错误”，共涉及13个引用条目。整体条件通过不等于引用定位正确。", "",
        "162个内容核验条目中，157个有足够明确材料，5个存在材料或语境缺口：铁处女、齐柏林飞艇仅取得部分外部命名证据；金属→Metallica和节奏摇滚→Rock And Roll缺少充分别名依据；robust-23缺少“这批曲目”的范围定义。前两项仍可作有条件候选，后两项别名关系标记证据不足；robust-23的实际回答暂不能确定。", "",
        "42个条目带有问题、适用条件或限制，其中10个条目存在明确引用定位错误。42不是错误题数；33道保留题因未隔离跳过，与材料不足分开统计。", "",
        "### 机器可读汇总", "", "```json", json.dumps(summary, ensure_ascii=False, indent=2), "```", "",
        "问题数量按有问题或限制的条目去重计算，不将同题的参考与实际问题重复算成两道题；错误、条件限制、材料不足和保留题跳过分别列示。", "",
        "## 优先处理事项", ""]
    def priority(row):
        if row["review_id"] == "robust:robust-23":
            return 0
        if row["review_id"] == "rag:rag-19":
            return 1
        if row["reference_status"] == "证据不足":
            return 2
        if row["review_id"] == "nl2sql:sql-38":
            return 3
        return 4 if row["review_id"] in set(error_ids) else 5

    priorities = sorted([row for row in reviewed if row.get("issues")],
                        key=lambda row: (priority(row), row["review_id"]))
    for row in priorities[:12]:
        lines.append(f"- **{row['review_id']}**：参考={row['reference_status']}；实际={row['actual_status']}。{stringify(row['issues'])} 建议：{stringify(row.get('suggestion'))}")
    if len(priorities) > 12:
        lines.append(f"- 其余 {len(priorities) - 12} 个有问题或限制的条目，在下方按原编号完整列出。")
    if not priorities:
        lines.append("本轮未发现明确错误或条件限制；证据不足仍需补证。")
    lines.extend(["", "## 逐项AI预审", ""])
    for row in rows:
        lines.extend([f"### {row['review_id']}", "", f"- 分组：{row['group']}；划分：{row.get('split') or '不适用'}", "",
            f"**审核对象：** {row['subject']}", "", f"**别名或参考答案判断：** {row['reference_status']}", "",
            f"**系统实际回答判断：** {row['actual_status']}", ""])
        for material in materials_markdown(row):
            lines.extend([material, ""])
        for key, label in [("alias_disposition", "别名使用建议"), ("source_question_type", "RAG题目来源类型"),
                           ("answer_correctness_status", "RAG答案正确性"), ("citation_support_status", "RAG引用支撑性"),
                           ("citation_location_status", "RAG引用定位正确性"),
                           ("reason", "参考判断理由"), ("actual_reason", "实际回答判断理由"),
                           ("issues", "发现的问题或限制"), ("suggestion", "建议处理方式"),
                           ("human_confirmation", "仍需人工确认")]:
            if row.get(key):
                lines.extend([f"**{label}：**", "", stringify(row[key]), ""])
        lines.extend(["**证据文件及具体位置：**", ""])
        evidence = row.get("evidence", [])
        lines.extend(["- " + evidence_markdown(item) for item in evidence] or ["本轮按隔离要求跳过内容审核，未展开证据。"])
        lines.append("")
    markdown = "\n".join(lines)
    (OUT / f"{STEM}.md").write_text(markdown, encoding="utf-8")
    from markdown_it import MarkdownIt
    render = MarkdownIt("commonmark", {"html": False}).enable("table")
    cards = []
    for row in rows:
        body = [f"**对象：** {row['subject']}", f"**参考/别名判断：** {row['reference_status']}",
                f"**系统实际回答判断：** {row['actual_status']}"]
        body.extend(materials_markdown(row))
        for key, label in [("alias_disposition", "别名使用建议"), ("source_question_type", "题目来源"),
                           ("answer_correctness_status", "答案正确性"), ("citation_support_status", "引用支撑性"),
                           ("citation_location_status", "引用定位正确性"),
                           ("reason", "参考判断理由"), ("actual_reason", "实际回答判断理由"),
                           ("issues", "问题或限制"), ("suggestion", "建议处理"), ("human_confirmation", "人工确认事项")]:
            if row.get(key):
                body.append(f"**{label}：**\n\n{stringify(row[key])}")
        body.append("**证据及具体位置：**\n\n" + "\n".join("- " + evidence_markdown(item) for item in row.get("evidence", [])))
        search = html.escape((row["review_id"] + " " + row["subject"] + " " + row["reference_status"] + " " + row["actual_status"] + " " + stringify(row.get("issues"))).lower(), quote=True)
        cards.append(f'<details class="item" data-group="{html.escape(row["group"])}" data-split="{html.escape(row.get("split") or "none")}" data-search="{search}">'
            f'<summary><b>{html.escape(row["review_id"])}</b> · {html.escape(row["reference_status"])} · 实际：{html.escape(row["actual_status"])}</summary>'
            + render.render("\n\n".join(body)) + "</details>")
    overview_markdown = markdown.split("## 逐项AI预审", 1)[0]
    overview_before, overview_remainder = overview_markdown.split("### 机器可读汇总", 1)
    machine_summary, overview_after = overview_remainder.split("## 优先处理事项", 1)
    overview = (render.render(overview_before)
                + '<details><summary>展开机器可读汇总与完整问题编号</summary>'
                + render.render(machine_summary) + '</details>'
                + render.render("## 优先处理事项" + overview_after))
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>D2统一待审核表 AI预审报告</title><style>
body{font-family:"Microsoft YaHei",sans-serif;max-width:1180px;margin:24px auto;padding:0 22px;line-height:1.75;color:#202b3a}h1{font-size:28px}h2{margin-top:30px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f5f8;padding:14px;border-radius:7px}a{color:#1265a8;overflow-wrap:anywhere}.toolbar{position:sticky;top:0;background:#fff;padding:12px 0;border-bottom:1px solid #ccd8e3;display:flex;gap:10px;flex-wrap:wrap;z-index:1}input,select,button{font:inherit;padding:7px 10px;border:1px solid #aebdcb;border-radius:5px}input{flex:1;min-width:220px}.item{border:1px solid #cbd7e3;margin:10px 0;border-radius:7px;padding:10px 14px}.item summary{cursor:pointer;background:#f4f7fa;padding:5px}.item p{overflow-wrap:anywhere}.count{padding:8px 0;color:#556274}table{border-collapse:collapse}td,th{border:1px solid #ccd8e3;padding:6px}
</style><body>''' + overview + '''<h2>逐项AI预审</h2><div class="toolbar"><input id="search" placeholder="搜索题号、对象或判断"><select id="group"><option value="all">全部分组</option><option value="alias">别名</option><option value="nl2sql">SQL</option><option value="robust">鲁棒</option><option value="rag">RAG</option><option value="metric">已确认口径</option></select><select id="split"><option value="all">全部范围</option><option value="dev">开发集</option><option value="holdout">保留集（仅跳过进度）</option><option value="none">别名与口径</option></select><button id="expand">展开筛选项</button><button id="collapse">收起全部</button></div><div class="count" id="count"></div>''' + "\n".join(cards) + '''<script>
const rows=[...document.querySelectorAll('.item')],q=document.getElementById('search'),g=document.getElementById('group'),s=document.getElementById('split');
function filter(){let n=0;rows.forEach(r=>{let show=r.dataset.search.includes(q.value.toLowerCase())&&(g.value==='all'||r.dataset.group===g.value)&&(s.value==='all'||r.dataset.split===s.value);r.hidden=!show;if(show)n++});document.getElementById('count').textContent='显示 '+n+' / '+rows.length+' 行；本报告仅为AI建议。'}
[q,g,s].forEach(e=>e.addEventListener('input',filter));document.getElementById('expand').onclick=()=>rows.filter(r=>!r.hidden).forEach(r=>r.open=true);document.getElementById('collapse').onclick=()=>rows.forEach(r=>r.open=false);filter();
</script></body></html>'''
    (OUT / f"{STEM}.html").write_text(page, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
