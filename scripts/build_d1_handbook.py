"""Build the D1 handbook from recorded acceptance evidence, without running QA.

Run with a Python environment containing ReportLab. The PDF skill's artifact
operation marker must be run once immediately before the first PDF build.
This script only reads local reports and writes the requested handbook files.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from html import escape
import json
from pathlib import Path
import re
import subprocess
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "eval/reports/d1-acceptance"
MARKDOWN = ROOT / "notes/D1验收报告与操作手册.md"
PDF = ROOT / "output/pdf/D1验收报告与操作手册.pdf"
STATES = {
    "PASS": "通过", "PASS_FOR_MACHINE_PREPARATION": "机器准备通过",
    "PASS_AS_DRAFT": "草稿基线通过", "PASS_FOR_D1": "D1 范围通过",
    "PASS_WITH_FINAL_SCAN_PENDING": "已有扫描，待终检",
    "IMPLEMENTED_WITH_RECORDED_ADJUSTMENT": "已实现并记录调整",
    "IN_PROGRESS": "正在收口", "PARTIAL": "本机通过，远机待核",
    "REVIEW_PENDING": "人工审核待完成", "EXTERNAL_PENDING": "外部待确认",
    "PASS_USER_CONFIRMED": "通过，双方已确认",
    "PASS_WITH_SOURCE_ADJUSTMENT": "通过，来源调整已记录",
    "NOT_D1": "后续排期",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Missing required evidence: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Evidence must be a JSON object: {path.relative_to(ROOT)}")
    return value


def value_text(value: Any) -> str:
    if value is None:
        return "未记录"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def local_link(path: str | Path, label: str | None = None) -> str:
    target = Path(path)
    if not target.is_absolute():
        target = ROOT / target
    return f"[{label or target.name}](<{target.as_posix()}>)"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def cell(value: Any) -> str:
        return value_text(value).replace("|", "／").replace("\n", " ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(cell(x) for x in row) + " |" for row in rows),
    ])


def code_block(text: str) -> str:
    return "```powershell\n" + text.strip() + "\n```"


def find_first(value: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in value:
            return value[name]
    return None


def engineering_counts(engineering: dict[str, Any]) -> dict[str, Any]:
    test = find_first(engineering, "pytest", "tests", "regression")
    if not isinstance(test, dict):
        test = next((check.get("details") for check in engineering.get("checks", [])
                     if check.get("id") == "pytest_full"), None)
    if not isinstance(test, dict):
        test = engineering
    result = {name: find_first(test, name, f"{name}_count") for name in ("passed", "failed", "skipped")}
    actual_output = "\n".join(str(test.get(name, "")) for name in ("output", "stdout", "summary", "output_tail"))
    for name in result:
        if result[name] is None:
            match = re.search(r"\b(\d+) " + name + r"\b", actual_output)
            if match:
                result[name] = int(match.group(1))
    result["exit_code"] = find_first(test, "exit_code", "returncode")
    # Missing failed/skipped counters remain unrecorded: no fabricated zeroes.
    if result["passed"] is None:
        raise ValueError("engineering.json must contain actual pytest passed count or test summary")
    return result


def load_evidence(usage_path: Path) -> dict[str, Any]:
    if not usage_path.is_absolute():
        usage_path = ROOT / usage_path
    paths = {
        "checklist": ACCEPTANCE / "checklist.json",
        "sql": ACCEPTANCE / "sql-dev/report.json",
        "rag": ACCEPTANCE / "rag-dev/report.json",
        "a_review": ACCEPTANCE / "a-review.json",
        "revision_manifest": ROOT / "eval/datasets/nl2sql_chinook_d1_acceptance.manifest.json",
        "b_review": ACCEPTANCE / "b-review-final.json",
        "engineering": ACCEPTANCE / ("requested-engineering.json" if (ACCEPTANCE / "requested-engineering.json").exists() else "engineering.json"),
        "ui": ACCEPTANCE / ("requested-ui-smoke.json" if (ACCEPTANCE / "requested-ui-smoke.json").exists() else "ui-smoke.json"),
        "secrets": ACCEPTANCE / ("requested-secret-scan.json" if (ACCEPTANCE / "requested-secret-scan.json").exists() else "secret-scan.json"),
        "repository": ROOT / "notes/github-repository.json",
        "usage": usage_path,
        "original_sql": ROOT / "eval/reports/d1-dev-draft/report.json",
    }
    data = {name: read_json(path) for name, path in paths.items()}
    exact_path = ACCEPTANCE / "requested-d1-evidence.json"
    if exact_path.exists():
        data["requested_d1"] = read_json(exact_path)
        paths["requested_d1"] = exact_path
    data["paths"] = paths
    for name, expected in (("sql", 21), ("rag", 14)):
        report = data[name]
        if report.get("status") != "COMPLETED" or report.get("prediction_count") != expected:
            raise ValueError(f"{name} actual completed prediction count must be {expected}")
        if report.get("split") != "dev" or report.get("draft_gold") is not True:
            raise ValueError(f"{name} must retain actual dev draft-gold provenance")
    if not all(key in data["sql"] for key in ("correct", "exploratory_ex", "average_latency_ms")):
        raise ValueError("SQL report missing actual measured EX or latency")
    if "mean_latency_ms" not in data["rag"]:
        raise ValueError("RAG report missing actual measured latency")
    data["test_counts"] = engineering_counts(data["engineering"])
    meta = data["rag"]["provenance"]["index_metadata"]
    chunk_path = ROOT / "data/processed/rag/ohr/chunks.jsonl"
    chunk_bytes = chunk_path.read_bytes()
    if hashlib.sha256(chunk_bytes).hexdigest() != meta["chunks_sha256"]:
        raise ValueError("Current chunks differ from the actual RAG run's recorded index")
    chunks = [json.loads(line) for line in chunk_bytes.decode("utf-8").splitlines() if line.strip()]
    vector_check = next((check.get("details", {}) for check in data["engineering"].get("checks", [])
                         if check.get("id") == "dense_index_v2_all_sources"), {})
    data["corpus"] = {
        "source": "new RAG report provenance.index_metadata + verified chunks + engineering dense check",
        "documents": len(meta["documents"]),
        "physical_pages": sum(doc["page_count"] for doc in meta["documents"]),
        "text_pages": sum(doc["text_page_count"] for doc in meta["documents"]),
        "chunks": meta["chunk_count"],
        "chunks_with_block_bbox": sum(bool(chunk.get("bbox")) for chunk in chunks),
        "max_chunk_chars": max(len(chunk["text"]) for chunk in chunks),
        "incomplete_sentence_start": sum(bool(chunk.get("incomplete_sentence_start")) for chunk in chunks),
        "incomplete_sentence_end": sum(bool(chunk.get("incomplete_sentence_end")) for chunk in chunks),
        "incomplete_chunk_count": meta["chunking"]["incomplete_chunk_count"],
        "vector_shape": vector_check.get("shape"),
        "finite_vectors": vector_check.get("all_finite"),
        "retrieval_method": meta["retrieval_method"],
    }
    data["paths"]["index_snapshot"] = ACCEPTANCE / "rag-dev/report.json"
    for label, path in (("SQL", ROOT / "eval/datasets/nl2sql_chinook_d1_acceptance.jsonl"),
                        ("RAG", ROOT / "eval/datasets/rag_ohr.jsonl")):
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        data[label.lower() + "_gold_count"] = len(rows)
        data[label.lower() + "_human_accepted"] = sum(
            row.get("gold_review", {}).get("status") == "accepted" for row in rows)
    data["generated_at"] = datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds")
    data["generation_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return data


def metric(report: dict[str, Any], name: str) -> str:
    item = report.get("mechanical_metrics", {}).get(name)
    if not isinstance(item, dict):
        return "未记录"
    return f"{item.get('passed', '未记录')}/{item.get('denominator', '未记录')}"


def review_summary(data: dict[str, Any]) -> dict[str, Any]:
    review = data["b_review"]
    return review.get("summary", review.get("final_summary", {}))


def metric_rows(data: dict[str, Any]) -> list[list[Any]]:
    sql, rag, tests, corpus = data["sql"], data["rag"], data["test_counts"], data["corpus"]
    return [
        ["工程回归", f"{tests['passed']} 项通过；退出码 {value_text(tests['exit_code'])}", "工程行为，非自然语言准确率"],
        ["SQL 修正版开发集", f"{sql['correct']}/{sql['prediction_count']}；{sql['exploratory_ex']:.2%}", "独立修正版，gold 尚待人工接受"],
        ["SQL 平均 HTTP 耗时", f"{sql['average_latency_ms'] / 1000:.3f} 秒", "本次实际 21 条请求"],
        ["RAG 开发集", f"{rag['prediction_count']} 条实际请求；成功 {metric(rag, 'status_succeeded')}", "引用机械检查与语义复核分开"],
        ["RAG 原文真实性", metric(rag, "all_evidence_text_authentic"), "引用可在指定 PDF 物理页找到"],
        ["RAG 平均 HTTP 耗时", f"{rag['mean_latency_ms'] / 1000:.3f} 秒", "本次实际 14 条请求"],
        ["知识库", f"{corpus['documents']} 份，{corpus['physical_pages']} 页，{corpus['chunks']} 片段", "六域原生 PDF；向量和哈希有记录"],
        ["人工 gold 接受", f"SQL {data['sql_human_accepted']}/{data['sql_gold_count']}；RAG {data['rag_human_accepted']}/{data['rag_gold_count']}", "AI 复核没有签署团队人工审核"],
    ]


def fix_rows(data: dict[str, Any]) -> list[list[Any]]:
    revisions = {item["id"]: item for item in data["revision_manifest"]["changes"]}
    rounding = revisions["sql-11"]
    before = rounding["before"]
    after = rounding["after"]
    return [
        ["sql-11", rounding["reason"],
         "原 SQL：" + before["gold_sql"] + "；原结果：" + value_text(before["gold_result"]) +
         "。修正版：" + after["gold_sql"] + "；真实结果：" + value_text(after["gold_result"])],
        ["sql-22 / sql-24", "“名字”含义可歧义，原 gold 只取 first_name", "独立修正版明确 first_name 名字段；团队仍需确认业务口径"],
        ["RAG 片段上下文", "原草稿 rag-16/19 引用上下文与回答存在缺口", "自然句界/表格行切片及不完整边界标记已改进；新模型在完整证据上实际回答，经逐项 AI 复核；未修改回答 prompt"],
        ["协议与旧文档", "旧指南 Python3.11、0起页码、Top8 与实现不同", "指南改 Python3.12、1起物理页、Top-K5；原官方页索引仍0起"],
        ["仓库协作", "原工程只有本地 Git", "已创建私有仓库；推送验证以 repository 记录为准"],
    ]


LOCAL_START = r"""Set-Location -LiteralPath 'E:\中国电子杯-赛题八\system'
.\.venv\Scripts\python.exe --version
docker compose --project-name comagent-d1 ps
.\scripts\start_demo.ps1"""
DIAGNOSTIC = r"""Invoke-RestMethod 'http://127.0.0.1:8000/health'
Invoke-RestMethod 'http://127.0.0.1:8000/api/documents'
Invoke-WebRequest 'http://127.0.0.1:8501/_stcore/health'
.\.venv\Scripts\python.exe scripts/check_db.py
.\.venv\Scripts\python.exe -m pip check"""
NEW_PC = r"""git clone 'https://github.com/gaara119/china-electronics-cup-task8-comagent.git' 'E:\中国电子杯-赛题八\system'
Set-Location -LiteralPath 'E:\中国电子杯-赛题八\system'
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
# 在本地编辑 .env，再执行后面的准备命令。
.\.venv\Scripts\python.exe scripts/bootstrap_db.py
.\.venv\Scripts\python.exe scripts/check_db.py
.\.venv\Scripts\python.exe scripts/build_catalog.py
.\.venv\Scripts\python.exe scripts/prepare_rag_data.py --selected-d1
.\.venv\Scripts\python.exe scripts/download_embeddings.py
.\.venv\Scripts\python.exe scripts/check_embeddings.py
.\.venv\Scripts\python.exe scripts/ingest_docs.py
.\scripts\start_demo.ps1"""
ACCEPT_SQL = r"""# 仅在实际核对以下题目之后记录；替换真实审核人。
.\.venv\Scripts\python.exe scripts/review_gold.py `
  --dataset eval/datasets/nl2sql_chinook_d1_acceptance.jsonl `
  --output eval/datasets/review_d1_acceptance `
  --accept sql-01,sql-02 --reviewer '实际审核人'
# 全部21道开发gold有效接受后，运行此修正版的正式评测。
.\.venv\Scripts\python.exe -m eval.run_eval `
  --dataset eval/datasets/nl2sql_chinook_d1_acceptance.jsonl"""
ACCEPT_RAG = r"""# 仅记录实际已核对的题目。
.\.venv\Scripts\python.exe scripts/review_rag_gold.py `
  --dataset eval/datasets/rag_ohr.jsonl `
  --accept rag-02,rag-03 --reviewer '实际审核人'
# 全部14道开发gold有效接受后运行。
.\.venv\Scripts\python.exe -m eval.rag_run_eval `
  --dataset eval/datasets/rag_ohr.jsonl"""


def screenshot_paths(data: dict[str, Any]) -> list[Path]:
    paths = []
    for raw in data["ui"].get("screenshots", []):
        if isinstance(raw, dict):
            raw = raw.get("path")
        if not raw:
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = ROOT / path
        if path.is_file():
            paths.append(path)
    if not paths:
        paths = sorted((ACCEPTANCE / "screenshots").glob("*.png"))
    return paths


def build_markdown(data: dict[str, Any]) -> str:
    sql, rag, original, repo = data["sql"], data["rag"], data["original_sql"], data["repository"]
    summary = review_summary(data)
    lines = [
        "# D1 验收报告与操作手册", "",
        f"任务日期：2026-10-10。生成时间：{data['generated_at']}（America/Chicago）。生成时 Git HEAD：`{data['generation_commit']}`。",
        "",
        "本手册依据已保存的实际验收 JSON、原始请求响应、数据库检查和浏览器记录生成。生成器不发起模型调用，不运行保留题，不写入人工接受状态。",
        "",
        "**D1 的 SQL 与指定文档 RAG 工程已经具备实际运行证据。工程验收、AI 语义复核、人工 gold 接受及学校外部确认分别记录。正式开发集成绩只有在 gold 经实际人工确认后才成立。**",
        "",
        "## 1. 今天的范围与总体结果", "",
        "D1 目标为同一界面完成一道库题与一道指定文档题，并展示真实 SQL/结果或引用原文，留存可复查基线。当前支持显式 sql/doc、单业务表和单份原生 PDF。",
        "",
        md_table(["检查项", "实际结果", "解释与限制"], metric_rows(data)), "",
        "初赛最终所需中级任务、不同格式至少十份文档、跨源、多轮、正式技术文档和 ZIP 按 D2-D9 排期推进。本次 D1 验收不代表最终参赛材料已齐备。",
        "",
        "新索引实际检查：", "", "```json", json.dumps(data["corpus"], ensure_ascii=False, indent=2), "```", "",
        "本次片段优先在自然句界或表格行边界结束，最长600字符、目标重叠80、不跨物理页。仍有长句及物理页末的残片，已明确记录不完整边界，不宣称每个片段都是完整句。旧1381片段记录保留为历史，不替代本次索引。",
        "",
        "## 2. 逐项验收及补齐内容", "",
        md_table(["项目", "发现", "处理"], fix_rows(data)), "",
        "以下清单来自计划 D1 对照表。状态反映对应检查记录；外部事项及人工签字不能由工程测试替代。", "",
        md_table(["编号", "负责人", "要求", "验收状态", "证据/剩余步骤"], [
            [r["id"], r["owner"], r["requirement"], STATES.get(r["status"], r["status"]),
             "；".join(r["evidence"]) + ("；" + r["gap"] if r.get("gap") else "")]
            for r in data["checklist"]["requirements"] if r["phase"] == "D1"
        ]), "",
        "完整机器记录：" + local_link("eval/reports/d1-acceptance/checklist.json") + "。",
        "",
        *([
            "### 2.1 用户本次原清单的十四项证据", "",
            "本轮按上午共同2项、A7项、B4项、晚上联调1项重新核对，并补齐@traced、三个固定折叠面板、未来目录说明和镜像PDF下载实证。原标准答案与历史评测保留。",
            "",
            md_table(["编号", "分工", "要求", "状态", "实际事实", "证据"], [
                [row["id"], row["owner"], row["requirement"], row["status"], row["facts"],
                 "；".join(local_link(item["path"]) for item in row["evidence"])]
                for row in data["requested_d1"]["rows"]]), "",
            "当前协议双方同意由用户明确确认并绑定文件SHA256，之后修改必须A/B对具体版本均同意。镜像PDF六份实下载且哈希一致；镜像qas_v2.json独立地址404，保留同一固定官方GitHub QA。历史共同手写没有被当成已验证事实。", "",
            f"本轮工程 {data['engineering']['passed_count']}/{data['engineering']['check_count']}，pytest {data['test_counts']['passed']} passed、{data['test_counts']['skipped']} skipped；另有两道新页面实问，不纳入原35题开发基准。之前57项工程包含4条live边界题，本轮53项未再调用这些题。", "",
            local_link("eval/reports/d1-acceptance/requested-d1-evidence.md", "十四项完整证据表") + "；" + local_link("notes/共享协议确认.md") + "；" + local_link("notes/D1目录对照.md") + "。", "",
        ] if "requested_d1" in data else []),
        "## 3. 真实模型开发集与历史记录", "",
        f"SQL 本次使用独立修正版 `nl2sql_chinook_d1_acceptance.jsonl`，实际预测 {sql['prediction_count']} 道开发题，结果 {sql.get('correct')}/{sql['prediction_count']}，草稿 exploratory_ex={sql.get('exploratory_ex'):.2%}。平均 HTTP 耗时 {sql['average_latency_ms']/1000:.3f} 秒。",
        "",
        f"原 30 题及其旧报告保持不变：原开发草稿 {original.get('correct')}/{original['prediction_count']}，exploratory_ex={original.get('exploratory_ex'):.2%}。新版本改动 sql-11、sql-22、sql-24 的题意/gold 口径，**不能把两次差值称为同一题集的模型准确率提升**。所有保留题不用于调试。",
        "",
        f"RAG 本次实际运行 {rag['prediction_count']} 道开发题，平均 HTTP 耗时 {rag['mean_latency_ms']/1000:.3f} 秒；机械检查如下。页命中、原文真实性及字符串匹配不能单独作为答案语义准确率。",
        "",
        md_table(["机械指标", "实际结果"], [[name, f"{v.get('passed')}/{v.get('denominator')}；unknown={v.get('unknown')}"]
            for name, v in rag.get("mechanical_metrics", {}).items() if isinstance(v, dict)]),
        "",
        "本次模型/数据/索引版本及请求开始时 Git 状态直接保存在两份 report.json 的 provenance 中。离线建索引与首次加载不混成稳定热请求耗时。",
        "",
        local_link("eval/reports/d1-acceptance/sql-dev/report.md", "SQL 新开发报告") + "；" + local_link("eval/reports/d1-acceptance/rag-dev/report.md", "RAG 新开发报告") + "。",
        "",
        "## 4. AI 复核与人工签字的边界", "",
        "A 独立审计执行原 30 条标准 SQL，保存真实只读权限、行值、NULL、排序和字段语义核对。原记录中 27 项语义吻合、1 项平均值未按题意保留两位小数、2 项需澄清名字口径；改动另建版本。该审计未运行模型，也没有把审核人填写为 A。",
        "",
        "B 对新 14 条实际回答逐项核对题意、原页证据和事实支持。以下为独立 AI 审阅汇总，**不等同于团队人工签字或正式 groundedness 结论**。",
        "",
        md_table(["AI 审阅字段", "实际记录"], [[k, value_text(v)] for k, v in summary.items()]),
        "",
        f"当前人工 gold 接受记录：SQL {data['sql_human_accepted']}/{data['sql_gold_count']}，RAG {data['rag_human_accepted']}/{data['rag_gold_count']}。个人真正逐项核对后，才使用第 9 节的脚本记录，不自动署名。",
        "",
        local_link("eval/reports/d1-acceptance/a-review.md", "A 独立审计") + "；" + local_link("eval/reports/d1-acceptance/b-review-final.md", "B 新回答 AI 复核") + "。",
        "",
        "## 5. 调用用量与凭据检查", "",
        "下面完整用量汇总直接读自验收 JSON，仅包含本次 21 SQL＋14 RAG＝35 条开发预测，不含之前草稿、模型探测、浏览器演示或工程边界调用。具体范围以汇总 scope 为准。接口 token 用量不是实际扣费金额，未提供账单时不计算或虚构费用。", "",
        "```json", json.dumps(data["usage"], ensure_ascii=False, indent=2), "```", "",
        "提交候选和历史凭据检查直接读取 secret-scan.json：", "",
        md_table(["字段", "实际记录"], [[k, value_text(v)] for k, v in data["secrets"].items()]), "",
        "真实凭据仅存在本机 `.env`。私有仓库仍需执行忽略和扫描，不能把私有属性当成可以上传 key 的理由。",
        "",
        "## 6. 本机启动、页面验收与重启", "",
        "本机已有数据库、模型和索引时，使用已创建环境；不要重复创建 .venv。打开 Docker Desktop，确认 Linux 引擎，再执行：", "",
        code_block(LOCAL_START), "",
        "- 页面：[http://127.0.0.1:8501](http://127.0.0.1:8501)。",
        "- API 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)。",
        "- 数据库：127.0.0.1:55432；应用角色 qa_reader。", "",
        "逐项演示：选择 Chinook，询问“来自巴西的客户有多少位？”，核对实际 SQL、数值结果和步骤；再选一份登记 PDF，使用其开发题，核对回答、证据归属、物理页和原文。点击引用只改变展示，不重复问模型。切换来源后不显示旧来源答案。", "",
        "当前工程 `Evidence.page` 从 1 起，封面计入；前端直接展示。官方 OHR 原 `evidence_page_no` 从 0 起，仅转换到内部物理页时加 1 一次。bbox 为实际可可靠映射的文字块区域；页面显示原页不等于逐字高亮。", "",
        "修改 .env 或配置后重启自己的 API。脚本复用健康 API，不会自动替换旧配置；Ctrl+C 停止前台 Streamlit，后台 API 保持运行。陌生端口占用只提示；停止进程前核对启动方式与 PID，不根据陈旧 PID 结束不明服务。", "",
        "本次浏览器实际检查记录：", "",
        "```json", json.dumps(data["ui"], ensure_ascii=False, indent=2), "```", "",
    ]
    for path in screenshot_paths(data):
        lines += [local_link(path), ""]
    lines += [
        "## 7. API 与故障排查", "",
        code_block(DIAGNOSTIC), "",
        "`llm_configured=true` 仅表示配置读到 key，真实可用性看 model-check 和实际模型响应；HTTP 200 不等于业务成功，检查 status/error/SQL/证据/steps。",
        "",
        md_table(["症状", "核查", "处理"], [
            ["页面无法打开", "8501/_stcore/health、端口及Streamlit终端", "页面未启动就重新启动；已有服务直接打开，不结束陌生进程"],
            ["数据库未就绪", "Docker Desktop Linux引擎、compose ps、check_db", "开启引擎/启动本人Compose；保留命名卷，不盲删数据"],
            ["配置改后无效", "API进程是否仍为旧实例", "核对本人进程并重启API；仅刷新页面不重载服务配置"],
            ["文档不在列表/ready=false", "manifest、PDF哈希、index_meta及索引路径", "按固定来源准备PDF/模型并重新ingest；下载模型不会自动升级旧索引"],
            ["认证/余额/网络失败", "真实error与model-check；不打印key", "在本地修正key或账户/网络；失败保留，不用固定答案掩盖"],
            ["EMPTY_RESULT", "所选文档是否含答案、所引用片段", "明确证据不足；不会偷偷切换到另一文档"],
            ["UNSUPPORTED", "是否请求多表/多文档/跨源/auto", "按D1单表单文档范围验收，后续能力按计划实现"],
            ["正式评测READINESS_ONLY", "目标数据集的人工审核及服务条件", "完成实际审核后再运行；只就绪检查预测0，不产生成绩"],
        ]), "",
        "SQL 请求样例：", "",
        "```json", '{"session_id":"d1-acceptance-demo","message":"来自巴西的客户有多少位？","scope":{"route":"sql","db_id":"chinook","doc_ids":[]}}', "```", "",
        "文档请求使用 scope.route=doc、db_id=null、doc_ids 只含所选登记 ID；接口字段以 schemas.py 和 B接口交接为准。页面仅通过 HTTP 调 API。",
        "",
        "## 8. 私有仓库与另一台电脑准备", "",
        f"私有仓库：[gaara119/china-electronics-cup-task8-comagent]({repo['html_url']})。private 实测字段={value_text(repo.get('private'))}，上传记录={value_text(repo.get('upload_status'))}。最终分支/远程 commit 以 {local_link('notes/github-repository.json')} 为准。",
        "",
        "B 的私有仓库权限已添加，依据用户在 2026-10-10 的确认。另一台电脑的登录、克隆及环境准备尚未实际验证。通过正常 Git 认证，不把 token 放进 clone URL。",
        "",
        "当前 Git 忽略本地 PDF缓存/模型/索引/.env/.venv；仓库提供源码、清单、固定来源与准备脚本。克隆不等于已取得可用向量；新电脑自己下载六 PDF 和约587MB的固定模型，独立创建数据库和环境。命令适用于目标目录尚不存在的另一台 Windows电脑：", "",
        code_block(NEW_PC), "",
        "在新机本地编辑 .env，填写模型 key、POSTGRES_PASSWORD、DB_READER_PASSWORD 与匹配的 CHINOOK_DB_URL，保留 CPU/int8/TopK5 默认值。不要覆盖 A 现有 .env。仓库已有固定 gold，日常启动无需重建题库。", "",
        "127.0.0.1 指当前运行电脑，不表示可以直接访问 A 的电脑。另一台电脑尚未实际接入，本手册给准备步骤，不把它写成从零复现通过；D8 再按计划真正从零复现并留证。",
        "",
        "## 9. 人工审核与正式评测操作", "",
        "SQL 推荐团队审阅独立修正版审核表。sql-11 为全部发票平均总额保留两位小数，原 AVG(total) 返回 5.6519417475728155，修正版 ROUND(AVG(total),2) 的真实结果为5.65；sql-22/sql-24明确 first_name。原版仍可追溯；不要把接受记录写到原版后却对修正版报告正式成绩。", "",
        local_link("eval/datasets/review_d1_acceptance/gold_review.md", "SQL 修正版审核表") + "。", "",
        code_block(ACCEPT_SQL), "",
        "RAG 对照每题原 PDF 的物理页，确认答案及原文，重点注意限定词、时间/对象/数字范围。gold 接受与实际回答复核是两项工作。审核表打勾仅是笔记，接受脚本才写入绑定内容哈希的记录；题意/gold/split改变会使旧记录失效。", "",
        local_link("eval/datasets/rag_review/rag_gold_review.md", "RAG gold 审核表") + "；" + local_link("eval/reports/d1-acceptance/rag-dev/human_review.md", "本次实际答案复核表") + "。", "",
        code_block(ACCEPT_RAG), "",
        "默认评测创建新目录，保留旧报告；不能覆盖已使用目录。没有实际人工接受时，只能显式 --draft-gold 进行开发探索。D1 不预测 SQL9道及RAG6道保留题；冻结后才按要求评测，不把保留题和扰动变体用于调试。",
        "",
        "## 10. 外部待确认与 D2 任务", "",
        "学校截止日期及具体时刻、提交平台和额外PPT目前暂无正式通知，保持外部待确认。计划按D9倒排不是学校确定时刻。当前共享协议已获A/B同意（用户确认），后续修改须双方明确同意具体版本；B私有仓库权限已添加（用户确认），另一台电脑实际准备仍待验证。", "",
        "D2 的重点：A做值索引/别名/链接级联/改写，扩到50SQL和30鲁棒题；B完善片段上下文和数值/事实支持检查，补DOCX/HTML/MD/OCR，知识库至少十份不同格式，编口径手册并扩到30RAG。新指标继续使用真实请求及固定分母；本次观察到的问题进入开发集错误分析。", "",
        md_table(["阶段", "后续要求"], [[r["phase"], r["requirement"]] for r in data["checklist"]["requirements"] if r["phase"] != "D1"]), "",
        "## 11. 证据索引与生成复现", "",
    ]
    for name, path in data["paths"].items():
        lines.append(f"- {name}：{local_link(path)}")
    lines += [
        "", "- 原始请求、响应、trace、判定分别位于 sql-dev 和 rag-dev 子目录；历史报告保持原目录。",
        "- 截图在本次验收 screenshots；源PDF/模型/索引的哈希另见清单和rag-index-check。",
        "- 生成器只读报告和题库状态，不调用模型、不接受gold、不上传远程。", "",
        "使用含 ReportLab 的 Python 重建手册，输入任一关键实跑报告缺失会直接报错，不填推测数字：", "",
        code_block(r"python scripts/build_d1_handbook.py --usage eval/reports/d1-acceptance/model-usage.json"), "",
        "PDF重新生成后须渲染逐页检查；此步骤与手册生成本身分开记录。最终验收源 JSON 更新时，重新生成 Markdown 和 PDF，保持事实一致。", "",
    ]
    return "\n".join(lines)


def build_pdf(data: dict[str, Any], output: Path) -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font_path = Path("C:/Windows/Fonts/simhei.ttf")
    if not font_path.is_file():
        raise ValueError("Chinese PDF font missing: C:/Windows/Fonts/simhei.ttf")
    pdfmetrics.registerFont(TTFont("D1Chinese", str(font_path)))
    pdfmetrics.registerFontFamily("D1Chinese", normal="D1Chinese", bold="D1Chinese", italic="D1Chinese", boldItalic="D1Chinese")
    navy, teal, muted = colors.HexColor("#17364D"), colors.HexColor("#147E8C"), colors.HexColor("#556674")
    body = ParagraphStyle("body", fontName="D1Chinese", fontSize=10.2, leading=16, textColor=navy, spaceAfter=7, wordWrap="CJK")
    small = ParagraphStyle("small", parent=body, fontSize=8.2, leading=12, spaceAfter=4)
    heading = ParagraphStyle("heading", parent=body, fontSize=17, leading=24, textColor=teal, spaceAfter=13)
    title = ParagraphStyle("title", parent=heading, fontSize=27, leading=38, textColor=navy, spaceAfter=16)
    code_style = ParagraphStyle("code", parent=small, fontSize=8.2, leading=12, leftIndent=7, rightIndent=7, spaceAfter=4)
    table_style = ParagraphStyle("cell", parent=small, fontSize=8.5, leading=12, spaceAfter=0)
    width, height = A4
    content_width = width - 82
    story = []

    def para(text: str, style=body):
        story.append(Paragraph(escape(text).replace("\n", "<br/>"), style))

    def section(text: str):
        para(text, heading)

    def table(headers: list[str], rows: list[list[Any]], col_widths: list[float]):
        header_style = ParagraphStyle("headercell", parent=table_style, textColor=colors.white)
        cells = [[Paragraph(escape(value_text(x)), header_style if index == 0 else table_style)
                  for x in row] for index, row in enumerate([headers, *rows])]
        element = Table(cells, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        element.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F1F5F7")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, 0), 0.7, teal), ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#D7E2E7")),
        ]))
        story.append(element)
        story.append(Spacer(1, 9))

    def code(text: str):
        lines = []
        for line in text.strip().splitlines():
            if not line:
                lines.append("")
                continue
            current = ""
            for char in line:
                if current and pdfmetrics.stringWidth(current + char, "D1Chinese", 8.2) > content_width - 30:
                    lines.append(current)
                    current = "    " + char
                else:
                    current += char
            lines.append(current)
        item = Paragraph("<br/>".join(escape(line).replace(" ", "&#160;") for line in lines), code_style)
        box = Table([[item]], colWidths=[content_width])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF0F4")),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(box)
        story.append(Spacer(1, 10))

    def page():
        story.append(PageBreak())

    tests, sql, rag, corpus, repo = data["test_counts"], data["sql"], data["rag"], data["corpus"], data["repository"]
    summary = review_summary(data)
    # 1 - outcome and measurement boundaries.
    para("中国电子杯 · 赛题八", heading)
    para("D1 验收报告\n与操作手册", title)
    para("2026-10-10  |  A：后端 / SQL  ·  B：文档 / 页面", body)
    para("同一页面已接入真实 SQL 与指定文档问答。工程实测、AI 审阅、人工接受和外部确认各有独立记录。", body)
    table(["验收项", "本次实测", "解释"], metric_rows(data), [112, 185, content_width - 297])
    para("SQL 使用另建的修正版；与旧 19/21 不是完全相同题集，不能把差值描述成模型提分。RAG 引用机械通过与 AI 复核都不替代人工签字。", small)
    para("生成时间：" + data["generated_at"], small)
    para("生成时提交：" + data["generation_commit"], small)
    page()
    # 2 - A and shared requirements.
    section("01  D1 范围与 A 线逐项验收")
    para("D1 目标：同一界面可回答一道库题、一份指定文档的问题，展示实际 SQL 或原文，并保存第一份可复查基线。D2-D9 能力不混入今日工程验收。")
    selected = [r for r in data["checklist"]["requirements"] if r["id"].startswith(("S", "A"))]
    table(["编号", "计划要求", "记录状态"], [[r["id"], r["requirement"], STATES.get(r["status"], r["status"])] for r in selected], [40, 335, content_width - 375])
    para("标准 SQL 的只读独立执行是 gold 审计；它没有预测保留题。原表名为 snake_case，发票日期2021-2025；只读账号、5秒 SQL 超时、200行展示边界已有实际记录。", small)
    page()
    # 3 - B and integration.
    section("02  B 线与晚上联调验收")
    selected = [r for r in data["checklist"]["requirements"] if r["id"].startswith(("B", "I"))]
    table(["编号", "计划要求", "记录状态"], [[r["id"], r["requirement"], STATES.get(r["status"], r["status"])] for r in selected], [40, 335, content_width - 375])
    para(f"六域原生 PDF 共{corpus['physical_pages']}物理页，{corpus['text_pages']}页有原生文字，索引{corpus['chunks']}片段。实际BM25+BGE-M3 RRF，CPU/int8、1024维、Top-K5；不是仅有配置。", small)
    para(f"{corpus['chunks_with_block_bbox']}/{corpus['chunks']}片段有可靠块坐标；{corpus['incomplete_chunk_count']}片段存在不完整句界。最大600字符、目标重叠80、不跨页；长句或物理页末不宣称完整。", small)
    para("当前页面显示原文与完整原页；未声明逐字高亮或 OCR。内部物理页从1起，OHR原始0起仅转换一次。跨电脑从零复现按D8计划实际执行，今天不冒称已通过。", small)
    page()
    # 4 - new real runs and review.
    section("03  新开发集、修复与 AI 复核")
    table(["修订项", "发现及处理"], [[row[0], row[1] + "；" + row[2]] for row in fix_rows(data)], [95, content_width - 95])
    para(f"SQL修正版：{sql.get('correct')}/{sql['prediction_count']}，exploratory_ex={sql.get('exploratory_ex'):.2%}，平均{sql['average_latency_ms']/1000:.3f}秒。原19/21报告不覆盖。新版本改3条开发题的口径，不能作同题集提分比较。")
    table(["RAG机械检查", "本次结果"], [[name, metric(rag, name)] for name in ("status_succeeded", "all_evidence_from_selected_doc", "all_evidence_text_authentic", "retrieval_gold_page_hit", "evidence_gold_page_hit", "answer_has_known_evidence_id")], [365, content_width - 365])
    para("B 新回答 AI 审阅汇总：" + value_text(summary), small)
    para(f"人工 gold 接受：SQL {data['sql_human_accepted']}/{data['sql_gold_count']}，RAG {data['rag_human_accepted']}/{data['rag_gold_count']}。没有自动署名 A 或 B。正式EX/忠实度仍需真实人工流程。", small)
    page()
    # 5 - browser evidence and recorded use.
    section("04  页面演示与记录检查")
    checks = data["ui"].get("checks", {})
    if isinstance(checks, dict):
        if len(checks) == 8:
            groups = [
                ("SQL回答/查询显示、文档回答/证据显示", ("sql_answer_and_query_rendered", "doc_answer_and_evidence_rendered")),
                ("引用点击、原PDF物理页展示", ("citation_button_clicked", "original_pdf_page_rendered")),
                ("SQL、文档回答各有三个固定面板", ("sql_three_panels", "doc_three_panels")),
                ("未提问、切换来源各有三个固定面板", ("idle_three_panels", "scope_switch_three_panels")),
            ]
            table(["实际浏览器检查（8项分组）", "结果"],
                  [[label, f"{sum(checks.get(key) is True for key in keys)}/{len(keys)}"] for label, keys in groups],
                  [380, content_width - 380])
        else:
            table(["实际浏览器检查", "结果"], [[k, v] for k, v in checks.items()], [380, content_width - 380])
    para("浏览器异常：" + value_text(data["ui"].get("page_errors", data["ui"].get("errors"))), small)
    photos = screenshot_paths(data)
    chosen = []
    for needle in ("sql", "rag"):
        candidate = next((p for p in photos if needle in p.name.lower() and "trace" not in p.name.lower()), None)
        if candidate and candidate not in chosen:
            chosen.append(candidate)
    if chosen:
        images = []
        for path in chosen:
            img = Image(str(path))
            scale = min((content_width / len(chosen) - 10) / img.imageWidth, 180 / img.imageHeight)
            img.drawWidth = img.imageWidth * scale
            img.drawHeight = img.imageHeight * scale
            images.append(img)
        story.append(Table([images], colWidths=[content_width / len(chosen)] * len(chosen)))
        story.append(Spacer(1, 9))
        para("上图为实际浏览器截图缩略图，完整PNG与请求编号见notes/screenshots及最新requested-ui-smoke.json；旧版本截图与记录保留。", small)
    para("本次21SQL＋14RAG为35条开发预测，接口token来自实际用量；该汇总不含旧草稿、探测、页面演示和工程边界调用。未提供账单，不虚构费用。")
    combined = data["usage"].get("combined", {})
    para("本次35条开发请求用量：" + value_text(combined), small)
    para("实际用量证据：eval/reports/d1-acceptance/model-usage.json。Markdown版本展示完整汇总JSON。", small)
    scan = data["secrets"]
    table(["凭据检查", "实测"], [[k, v] for k, v in scan.items() if k in ("env_ignored", "env_tracked", "candidate_files_scanned", "candidate_credential_hits", "history_blobs_scanned", "history_credential_hits", "oversized_files")], [310, content_width - 310])
    page()
    # 6 - local operation.
    section("05  本机启动与操作")
    para("本机已准备数据库、模型和索引，直接复用.venv。打开Docker Desktop的Linux引擎后，在项目目录执行：")
    code(LOCAL_START)
    table(["服务", "入口"], [["问数问答页面", "http://127.0.0.1:8501"], ["API文档", "http://127.0.0.1:8000/docs"], ["数据库", "127.0.0.1:55432 / qa_reader"]], [125, content_width - 125])
    para("1. 选择Chinook，问“来自巴西的客户有多少位？”，核对答案、实际SQL、结果及步骤。")
    para("2. 选择一份登记PDF，使用它的开发题；核对答案、原文归属和物理页。点击引用只切换展示，不再调用模型。")
    para("3. 切换来源后不会显示旧来源答案；没有证据时如实EMPTY_RESULT，未实现能力为UNSUPPORTED，真实执行错误为FAILED。")
    para("修改.env或公共配置后重启自己的API。页面刷新不会重载服务配置；脚本复用健康API。Ctrl+C停止前台页面，后台API保持运行。端口被占用时先核对本人进程，不结束陌生PID。")
    para("Evidence.page与原页API均从1起，封面计页。页面不再加1；原OHR的0起索引只在转换入口加1一次。")
    page()
    # 7 - diagnostics and failures.
    section("06  API诊断与错误排查")
    code(DIAGNOSTIC)
    table(["现象", "核查与处理"], [
        ["8501无法访问", "检查Streamlit终端与_stcore/health；已有页面服务直接打开。"],
        ["database_ready=false", "检查Docker Linux引擎、compose ps和check_db；保留数据库命名卷。"],
        ["旧配置仍生效", "核对本人API启动进程并重启；仅刷新页面无效。"],
        ["文档ready=false", "核对manifest/PDF哈希/索引；按固定来源准备并重新ingest。"],
        ["认证、余额或网络错误", "读取真实error与model-check，在本地修正；不打印key，不用固定答案代替失败。"],
        ["EMPTY_RESULT", "所选文档证据不足；不偷偷切换来源。"],
        ["UNSUPPORTED", "请求可能超出单表、单文档范围；按后续计划实现。"],
        ["READINESS_ONLY", "正式评测条件不足，预测0；完成实际审核与服务准备后再运行。"],
    ], [112, content_width - 112])
    para("HTTP 200不等于业务成功，核对status/error/steps；llm_configured=true只表明读取到配置，真实可用性以实际调用为准。SQL结果的COUNT 0、零行和SUM NULL分开表达。")
    para("SQL 请求结构：session_id、message、scope={route:sql,db_id:chinook,doc_ids:[]}。文档请求route=doc、db_id=null、doc_ids恰好一个登记ID；UI只通过HTTP调用统一API。", small)
    page()
    # 8 - second computer and private repository.
    section("07  私有协作与新电脑准备")
    para("私有仓库：gaara119/china-electronics-cup-task8-comagent。private字段=" + value_text(repo.get("private")) + "；上传状态=" + value_text(repo.get("upload_status")), small)
    para("B的私有仓库权限已添加，依据用户在2026-10-10的确认；另一台电脑的登录、克隆及环境准备尚未实际验证。源码及清单通过Git同步，本地.env/.venv/PDF缓存/模型/索引按忽略规则独立准备。")
    code(NEW_PC)
    para(".env在新机编辑：模型key、管理员及只读数据库口令、匹配的CHINOOK_DB_URL；保留CPU/int8/TopK5。模型约587MB，索引必须实际CPU编码。不要复制对方.venv或覆盖现有.env。", small)
    para("127.0.0.1指当前电脑；另一台电脑尚未实际复现。准备流程不是远机通过记录，D8真正从零操作后留版本、截图及检查证据。", small)
    page()
    # 9 - actual human review and official dev assessment.
    section("08  人工接受与正式评测")
    para("先看SQL修正版审核表eval/datasets/review_d1_acceptance/gold_review.md。sql-11要求平均总额保留两位小数，修正版ROUND(AVG(total),2)实际5.65；sql-22/24仅first_name。原版接受记录不能代替修正版审核。")
    code(ACCEPT_SQL)
    para("RAG gold审核对照原PDF物理页核题意、答案和证据；实际回答再核正确、完整及每项事实支持。两项审核分开。")
    code(ACCEPT_RAG)
    para("示例--accept仅在实际已核对这些ID时使用，--reviewer填真实审核人。Markdown勾选是笔记，脚本写入内容哈希绑定的接受记录；题意、gold或split变更使原接受失效。", small)
    para("默认创建新评测目录，历史报告不覆盖。没有真实人工接受时只能--draft-gold探索；D1不预测SQL9道与RAG6道保留题，冻结后按既定纪律评测。", small)
    page()
    # 10 - remaining outside confirmations and evidence index.
    section("09  外部事项、D2计划与证据索引")
    para("学校截止时刻、提交平台和额外PPT目前暂无正式通知，保持外部待确认；计划D9倒排不是学校已确认期限。当前协议已获双方同意（用户确认），后续修改须双方同意具体版本；B私有仓库权限已添加（用户确认），远机准备仍待实际验证。")
    table(["后续阶段", "范围"], [[r["phase"], r["requirement"]] for r in data["checklist"]["requirements"] if r["phase"] != "D1"], [70, content_width - 70])
    para("证据全部保存在system；查数字看JSON，查单题看原始responses/predictions，查引用回原PDF。报告生成不会调用模型或接受gold。", small)
    index = [
        "eval/reports/d1-acceptance/checklist.{md,json}",
        "eval/reports/d1-acceptance/{engineering,secret-scan,ui-smoke}.json",
        "eval/reports/d1-acceptance/sql-dev/report.{md,json}",
        "eval/reports/d1-acceptance/rag-dev/report.{md,json}",
        "eval/reports/d1-acceptance/a-review.{md,json}",
        "eval/reports/d1-acceptance/b-review-final.{md,json}",
        "eval/reports/d1-acceptance/model-usage.json",
        "notes/{github-repository,rag-corpus-check,rag-index-check}.json",
        "notes/D1协作交接.md；notes/D1执行指导书.md",
        "scripts/build_d1_handbook.py；README.md",
    ]
    for line in index:
        para(line, small)

    if "requested_d1" in data:
        page()
        section("10  原清单证据：上午共同与A")
        para("本页逐条对应用户10/10清单。详细源代码行号、数据库原始值和链接见requested-d1-evidence.md/json，保持原始测试与旧评测记录。", small)
        selected = [r for r in data["requested_d1"]["rows"] if r["owner"] in {"上午共同", "A"}]
        table(["编号", "要求与状态", "证据入口"], [
            [r["id"], r["requirement"] + "；" + r["status"],
             "requested-shared-evidence.json" if r["owner"] == "上午共同" else "requested-a-evidence.json"]
            for r in selected], [53, 318, content_width - 371])
        para("数据库实测11表、64列、11外键，invoice 2021-2025，qa_reader默认只读on/5s。旧文本13外键已按真实pg_constraint和原审计JSON更正为11。", small)
        para("当前schemas文件未修改，双方同意绑定SHA256：" + data["requested_d1"]["current_schema_sha256"] + "。未来变更须双方同意新版本。", small)
        para("@traced已接入真实sql_exec，避免重复计时且不记录DSN。最新工程53/53，pytest159/0skip；旧57项含4个live边界题，本轮未重跑它们。", small)
        para("Top艺术家前三：Iron Maiden 138.60、U2 105.93、Metallica 90.09。地区比较412张发票、差异0，决定更换澄清演示；原03设计正文没有冒称已改写。", small)
        page()
        section("11  原清单证据：B与晚上联调")
        selected = [r for r in data["requested_d1"]["rows"] if r["owner"] in {"B", "晚上联调"}]
        table(["编号", "要求与状态", "证据入口"], [
            [r["id"], r["requirement"] + "；" + r["status"], "requested-b-evidence.json"]
            for r in selected], [70, 301, content_width - 371])
        para("六份PDF本轮经hf-mirror真实下载，CRC/SHA256均与原资料一致，原PDF和索引未变。镜像独立qas_v2.json返回404，QA继续取固定官方GitHub版本；不是更换题库。", small)
        para("原qas_v2共8498条；20道原始text题逐条来源核验通过，14dev/6holdout。六域各一份全英文PDF，共261物理页、1527×1024混合索引。", small)
        para("三固定面板：SQL与结果、引用来源、处理步骤与耗时；空态、SQL、切换来源、文档四种实际页面状态均确认3个。最新浏览器8/8检查、无page error。", small)
        para("新SQL实答巴西客户5；新文档实答iMovie [E1]、物理第3页。两个实际UI问题观察3个LLM步骤，不纳入原35题基准，不预测保留题。", small)
        para("新三图：notes/screenshots/D1-验收-sql.png、D1-验收-rag.png、D1-验收-rag-trace.png。图像SHA与trace在D1-evidence.json；旧截图原样保留。", small)
        para("最新工程：eval/reports/d1-acceptance/requested-engineering.json；页面：requested-ui-smoke.json；下载：requested-mirror-pdfs.json及requested-download-route.json；目录：notes/D1目录对照.md；协议：notes/共享协议确认.md。", small)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D4E0E6"))
        canvas.line(41, height - 32, width - 41, height - 32)
        canvas.setFont("D1Chinese", 8)
        canvas.setFillColor(muted)
        canvas.drawString(41, height - 23, "中国电子杯 · 赛题八  |  D1 实测验收")
        canvas.drawString(41, 22, "2026-10-10  |  工程实测与 AI 复核，人工签字状态独立记录")
        canvas.drawRightString(width - 41, 22, f"{doc.page}")
        canvas.restoreState()

    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=41, leftMargin=41,
                                topMargin=48, bottomMargin=42, title="D1验收报告与操作手册",
                                author="中国电子杯赛题八项目组", pageCompression=1)
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usage", type=Path, default=ACCEPTANCE / "model-usage.json")
    parser.add_argument("--check-inputs", action="store_true", help="Read and validate evidence only; write no artifacts")
    parser.add_argument("--markdown-only", action="store_true", help="Generate Markdown without authoring PDF")
    args = parser.parse_args()
    data = load_evidence(args.usage)
    if args.check_inputs:
        print(json.dumps({"ready": True, "sql_predictions": data["sql"]["prediction_count"],
                          "rag_predictions": data["rag"]["prediction_count"],
                          "pytest": data["test_counts"]}, ensure_ascii=False))
        return
    MARKDOWN.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN.write_text(build_markdown(data), encoding="utf-8")
    if not args.markdown_only:
        build_pdf(data, PDF)
    print(json.dumps({"markdown": str(MARKDOWN), "pdf": None if args.markdown_only else str(PDF)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
