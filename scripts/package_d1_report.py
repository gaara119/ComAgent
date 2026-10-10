"""Build a senior-facing D1 report and an offline evidence bundle from a frozen commit."""
from __future__ import annotations

import hashlib
import html
import io
import json
import posixpath
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, unquote
import zipfile

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7"
REPO_URL = "https://github.com/gaara119/china-electronics-cup-task8-comagent"
REPORT_DIR = ROOT / "notes/汇报"
OUT_DIR = ROOT / "output/handoff"
PACKAGE_ROOT = "D1-2026-10-10-ccf4c49"
LINK = re.compile(r'(!?\[[^\]\n]*\])\((?:<([^>\n]+)>|([^\)\n]+))\)')
MAIN_REPORT = "eval/reports/d1-acceptance/requested-d1-evidence.md"
PYTEST_LOG = "eval/reports/d1-acceptance/engineering-20261010T134438489202Z-pytest.txt"
RELATED = {
    MAIN_REPORT: "D1逐项验收证据-GitHub版.md",
    "eval/reports/d1-acceptance/requested-a-evidence.md": "A验收证据-GitHub版.md",
    "eval/reports/d1-acceptance/requested-b-evidence.md": "B验收证据-GitHub版.md",
    "eval/reports/d1-acceptance/requested-shared-evidence.md": "共同事项证据-GitHub版.md",
}
SHORT_FACTS = [
    "私有仓库已建立并上传；19 个计划目录齐全。D2–D4 目录仅保留计划说明。",
    "共享 schemas.py 已供两条链路使用；用户已确认 A/B 同意当前协议。PDF 物理页从 1 开始、封面计页。",
    "Chinook PostgreSQL 16.15 已启动；qa_reader 只读；11 表、64 列、11 外键；数据年份 2021–2025。",
    "真实 /models 查询确认 deepseek-flash；JSON 输出探测成功；真实凭据保留在本机。",
    "统一 LLM 调用具备超时、重试与 token 记录；@traced 已实现并接入 SQL 执行。",
    "目录→生成→SQLGlot 校验→只读执行已连通；修正版开发集探索 EX 为 21/21。",
    "30 道单表题及 gold 执行结果已保存；21 dev / 9 holdout；正式成绩等待人工 gold 确认。",
    "Top 艺术家查询和 Top10 名单已保存至 A/B 共享仓库；可用于后续跨源文档准备。",
    "412 张发票两种国家口径差异为 0；已决定改用其他澄清示例，正式澄清功能按 D3 排期。",
    "六域各一份 PDF，均为英文；hf-mirror 下载的六份文件与原件哈希一致；QA 使用固定官方 GitHub 版本。",
    "PDF 解析、分块、真实 BGE-M3 int8 CPU + BM25 检索及编号引用已实现；索引为 1527×1024。",
    "Streamlit 提问框、来源选择和三个常驻折叠面板已完成。",
    "20 道 OHR 原始 text 题已整理，14 dev / 6 holdout；人工 gold 接受尚待记录。",
    "界面实问 SQL 和文档题，8/8 浏览器检查通过；最新截图与数字已写入日志。",
]


def frozen_files() -> dict[str, bytes]:
    archive = subprocess.check_output(["git", "archive", "--format=zip", SOURCE_COMMIT], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        if zf.testzip() is not None:
            raise RuntimeError("Git source archive failed its CRC check")
        return {item.filename: zf.read(item) for item in zf.infolist() if not item.is_dir()}


def target_path(target: str, origin: str, sources: dict[str, bytes]) -> tuple[str, int | None] | None:
    target = unquote(target.strip()).replace("\\", "/")
    if target.startswith(("https://", "http://", "mailto:", "#", "codex:", "app:")):
        return None
    line = None
    match = re.search(r":(\d+)$", target)
    if match:
        line = int(match.group(1))
        target = target[:match.start()]
    target = target.partition("#")[0]
    local_prefix = ROOT.as_posix() + "/"
    if target.lstrip("/").casefold().startswith(local_prefix.casefold()):
        target = target.lstrip("/")[len(local_prefix):]
    elif re.match(r"/?[A-Za-z]:/", target):
        # An old local source-plan reference can be resolved to its archived copy.
        if target.endswith("/方案.md"):
            target = "notes/references/项目方案.md"
        elif target.endswith("/8 赛题八：网信产业应用赛道-多模态数据驱动的可解释精准问数问答智能体（中电云计算技术有限公司）.pdf"):
            target = "notes/references/赛题八准则.pdf"
        else:
            return None
    else:
        relative = posixpath.normpath(posixpath.join(posixpath.dirname(origin), target))
        target = relative if relative in sources else target
    return (target, line) if target in sources else None


def rewrite(content: str, origin: str, sources: dict[str, bytes], mode: str, output: str) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        label, target = match.group(1), match.group(2) or match.group(3)
        resolved = target_path(target, origin, sources)
        if resolved is None:
            # Preserve non-file URLs. Unpackaged machine-specific paths become plain labels.
            if re.match(r"/?[A-Za-z]:[/\\]", target):
                return label.lstrip("!")[1:-1] + "（原记录本机文件，未纳入交付包）"
            return match.group(0)
        path, line = resolved
        if line is not None and line > len(sources[path].splitlines()):
            raise RuntimeError(f"Evidence line is outside the frozen file: {path}:{line}")
        count += 1
        if mode == "github":
            if path in RELATED and path != origin:
                destination = quote(RELATED[path])
            else:
                destination = REPO_URL + "/blob/" + SOURCE_COMMIT + "/" + quote(path, safe="/")
                if line:
                    destination += f"#L{line}"
        else:
            destination_path = ("阅读版/" if path.endswith(".md") else "system/") + path
            destination = posixpath.relpath(destination_path, posixpath.dirname(output))
            if line:
                label = label[:-1] + f" · 第 {line} 行]"
        return f"{label}(<{destination}>)"

    return LINK.sub(replace, content), count


def github_link(path: str) -> str:
    return REPO_URL + "/blob/" + SOURCE_COMMIT + "/" + quote(path, safe="/")


def summary(sources: dict[str, bytes], mode: str) -> str:
    def link(label: str, path: str) -> str:
        if mode == "github":
            target = RELATED[path] if path in RELATED else github_link(path)
        else:
            target = ("阅读版/" if path.endswith(".md") else "system/") + path
        return f"[{label}](<{target}>)"

    evidence_link = "D1逐项验收证据-GitHub版.md" if mode == "github" else "02-D1逐项验收证据.md"
    record = json.loads(sources[MAIN_REPORT.replace(".md", ".json")])
    rows = record["rows"]
    if len(rows) != len(SHORT_FACTS):
        raise RuntimeError("The frozen checklist no longer has fourteen items")
    table = "\n".join(f"| {row['id']} | {row['owner']} | {fact} |" for row, fact in zip(rows, SHORT_FACTS))
    screenshots = [
        ("SQL 联调：巴西客户数量为 5", "notes/screenshots/D1-验收-sql.png"),
        ("文档联调：iMovie 答案与编号引用", "notes/screenshots/D1-验收-rag.png"),
        ("文档处理步骤与耗时", "notes/screenshots/D1-验收-rag-trace.png"),
    ]
    images = "\n\n".join(
        f"{label}\n\n![{label}](<{github_link(path) + '?raw=true' if mode == 'github' else 'system/' + path}>)\n\n" + link("查看截图文件", path)
        for label, path in screenshots
    )
    return f"""# D1 阶段汇报｜2026-10-10

本日目标：按学长方案完成问数和问答智能体的基础工程、数据准备与联调。共同事项、A、B、晚上联调共 **14 项已完成工程验收**；数据来源调整与后续人工审核单列。D2–D4 功能继续按排期实施。

汇报代码及证据固定在提交 `{SOURCE_COMMIT}`。此后的代码修改不改变本次证据。原始记录及历史草稿完整保留；本文件汇总现有验收数据，本次打包未重新运行模型评测。

## 本日交付与验收结果

| 验收内容 | 本日结果 | 证据 |
|---|---|---|
| 当前代码回归 | 159 项通过，0 跳过 | {link('pytest 原始记录', PYTEST_LOG)} |
| 工程检查 | 53/53 通过 | {link('当前工程检查 JSON', 'eval/reports/d1-acceptance/requested-engineering.json')} |
| 新界面联调 | 8/8 浏览器检查通过；SQL / 文档各实问一道 | {link('浏览器实跑记录', 'eval/reports/d1-acceptance/requested-ui-smoke.json')} |
| NL2SQL 修正版开发集 | 21/21 执行结果匹配，平均约 3.406 秒；探索成绩 | {link('SQL 结果与请求记录', 'eval/reports/d1-acceptance/sql-dev/report.json')} |
| RAG 开发集 | 14/14 请求成功；引用结构、来源真实性及 gold 页命中检查均通过；表层答案匹配 10/14；独立 AI 语义/证据支持复核 14/14；平均约 3.184 秒 | {link('RAG 实跑记录', 'eval/reports/d1-acceptance/rag-dev/report.json')}；{link('独立复核记录', 'eval/reports/d1-acceptance/b-review-final.md')} |
| 标准答案人工确认 | SQL 0/30、RAG 0/20；正式模型成绩待发布 | {link('逐项技术验收', MAIN_REPORT)} |
| 保留集保护 | SQL 9 题、RAG 6 题模型预测均为 0 | {link('逐项技术验收', MAIN_REPORT)} |

上述 159 项回归与 53 项工程检查为最新记录；历史的 149 项回归和 57 项工程检查仍保留。旧 57 项包含 4 条真实模型边界题，本轮未重跑。SQL 原 19/21 与修正版 21/21 使用的题集不同，不能直接当作同题集准确率提升。RAG 表层匹配仅作字符串诊断；AI 复核尚需人工审核，正式正确率和证据支持成绩未发布。

## 按方案逐项对照

| 编号 | 分工 | 已交付内容及边界 |
|---|---|---|
{table}

逐项源码、数据、测试日志及行号见 [十四项完整证据附件](<{evidence_link}>)。

## 已确认的调整与待学长审阅事项

1. SQL 的 `sql-11` 按题意保留两位小数；`sql-22`、`sql-24` 明确只取 `first_name`。已保存原题集、修正版及修订说明，待人工确认业务口径。
2. 共享协议已由用户确认 A/B 同意：PDF 页码从 1 开始、封面计页。当前协议的后续实质修改仍须双方同意。
3. OHR 的 hf-mirror QA 根地址返回 404，QA 改取固定官方 GitHub 版本；六份 PDF 实际从镜像下载，并与原件 SHA256 一致。六份语料覆盖六域、均为英文；14 道开发题覆盖五域，金融题留在保留集。
4. 实际 Chinook 外键为 11 条。412 张发票的客户国家与账单国家无数值差异，后续澄清演示需换成年度缺失、热门定义或类型歧义示例。

希望学长重点审阅：题意与 gold SQL 的业务口径、RAG 标准答案与引用页的支持关系、上述来源及协议调整是否适合后续比赛演示。

下一步先完成 30 道 SQL / 20 道 RAG 标准答案人工确认并记录，再运行正式开发集评测；随后按原方案推进 D2。学校确认的截止日期、具体时刻与提交入口目前暂无。

## 联调截图及复现入口

{images}

{link('完整验收报告与操作手册 PDF', 'output/pdf/D1验收报告与操作手册.pdf')}；{link('项目启动与依赖说明', 'README.md')}；{link('学长原方案归档', 'notes/references/项目方案.md')}。

源码包包含此固定提交的全部 Git 跟踪文件，保留评测原始输出和历史草稿。真实 API 密钥、本机环境、模型权重、六份语料原 PDF、向量索引与数据库运行状态不在包内。换电脑复现时需按 README 配置环境、下载资料并生成索引。
"""


def readme_html(sources: dict[str, bytes]) -> str:
    rows = json.loads(sources[MAIN_REPORT.replace(".md", ".json")])["rows"]
    table_rows = []
    for row, fact in zip(rows, SHORT_FACTS):
        links = []
        for evidence in row["evidence"]:
            resolved = target_path(evidence["path"], MAIN_REPORT, sources)
            if resolved is None:
                raise RuntimeError("An evidence file cannot be resolved in the frozen source archive")
            path, _ = resolved
            destination = ("阅读版/" if path.endswith(".md") else "system/") + path
            label = posixpath.basename(path)
            if evidence.get("line"):
                label += f" · 第 {evidence['line']} 行"
            links.append(f'<a href="{html.escape(destination, quote=True)}">{html.escape(label)}</a>')
        table_rows.append(f"<tr><td>{html.escape(row['id'])}</td><td>{html.escape(fact)}</td><td>{'<br>'.join(links)}</td></tr>")
    table = "".join(table_rows)
    return f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>D1 汇报与证据阅读入口</title><style>body{{max-width:1080px;margin:40px auto;padding:0 24px;font-family:system-ui,'Microsoft YaHei',sans-serif;line-height:1.8;color:#182333}}a{{color:#125aa0}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #d8dfe7;padding:8px 12px;text-align:left}}code{{overflow-wrap:anywhere}}img{{max-width:100%;border:1px solid #d8dfe7;margin:12px 0 28px}}.notice{{background:#eff4fa;padding:16px;border-radius:8px}}</style>
<h1>D1 阶段汇报与证据</h1><p>日期：2026-10-10；代码与证据版本：<code>{SOURCE_COMMIT}</code></p>
<p class="notice">请先将 ZIP 完整解压，再打开本页。工程验收已完成；SQL / RAG 的标准答案人工确认与正式模型成绩仍待完成。包内原始 JSON 中的 E:/ 路径是验收来源元数据，阅读版链接已改为包内相对路径。</p>
<ul><li><a href="01-D1阶段汇报.md">阶段汇报 Markdown：结果、十四项对照和待审阅事项</a></li><li><a href="02-D1逐项验收证据.md">完整证据附件 Markdown：逐项源码、数据与日志</a></li><li><a href="system/output/pdf/D1验收报告与操作手册.pdf">已验收的操作手册 PDF</a></li><li><a href="阅读版/README.md">项目启动与复现说明</a></li><li><a href="SHA256清单.json">文件 SHA256 清单与包检查结果</a></li></ul>
<h2>主要验收结果</h2><p>159 项回归通过、0 跳过；53/53 工程检查；8/8 浏览器检查。修正版 SQL 开发集探索 EX：21/21；RAG：14/14 请求成功，引用结构、来源真实性及 gold 页命中检查均通过，表层答案匹配 10/14，独立 AI 语义及支持复核 14/14。人工 gold 接受：SQL 0/30、RAG 0/20。保留题 15 道均未预测。</p>
<h2>需学长审阅与下一步</h2><p>请重点审阅 SQL 标准答案的业务口径、RAG 答案与引用页的支持关系，以及资料来源和页码协议调整。sql-11 修正为两位小数，sql-22/24 明确只取 first_name。QA 镜像根地址返回 404，使用同一固定官方 GitHub 版本；六份镜像 PDF 与原件哈希均一致。原 19/21 与修正版 21/21 不能按同题集比较。</p><p>下一步先记录 30 道 SQL / 20 道 RAG 标准答案人工确认，再运行正式开发集评测，随后按方案推进 D2。学校截止日期、具体时刻和提交入口目前暂无。</p>
<h2>十四项交付及可点击证据</h2><table><tr><th>编号</th><th>内容</th><th>文件证据</th></tr>{table}</table>
<h2>联调截图</h2><p>SQL：巴西客户数量 5</p><img src="system/notes/screenshots/D1-验收-sql.png" alt="SQL 联调结果">
<p>文档：iMovie 编号引用与 PDF 物理页</p><img src="system/notes/screenshots/D1-验收-rag.png" alt="RAG 联调结果">
<p>文档处理步骤与耗时</p><img src="system/notes/screenshots/D1-验收-rag-trace.png" alt="RAG 处理步骤">
<p>此包适合审阅与留档。新电脑复现需自行配置 .env、准备模型/语料/索引及 PostgreSQL，详见 README。本次打包未重新运行模型评测。</p></html>"""


def main() -> None:
    sources = frozen_files()
    required = [PYTEST_LOG, MAIN_REPORT]
    for path in required:
        if path not in sources:
            raise RuntimeError(f"Required frozen evidence is missing: {path}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for origin, name in RELATED.items():
        rendered, _ = rewrite(sources[origin].decode("utf-8-sig"), origin, sources, "github", name)
        header = f"> 汇报阅读版；原始验收记录和源码固定于 `{SOURCE_COMMIT}`。证据链接需具有私有仓库访问权限。\n\n"
        (REPORT_DIR / name).write_text(header + rendered, encoding="utf-8")
    (REPORT_DIR / "D1阶段汇报-学长版.md").write_text(summary(sources, "github"), encoding="utf-8")

    members = {"system/" + name: content for name, content in sources.items()}
    rewritten_links = 0
    for origin, content in sources.items():
        if origin.endswith(".md"):
            output = "阅读版/" + origin
            rendered, count = rewrite(content.decode("utf-8-sig"), origin, sources, "offline", output)
            members[output] = rendered.encode("utf-8")
            rewritten_links += count
    appendix, main_links = rewrite(sources[MAIN_REPORT].decode("utf-8-sig"), MAIN_REPORT, sources, "offline", "02-D1逐项验收证据.md")
    members["02-D1逐项验收证据.md"] = appendix.encode("utf-8")
    members["01-D1阶段汇报.md"] = summary(sources, "offline").encode("utf-8")
    members["00-先读我.html"] = readme_html(sources).encode("utf-8")

    forbidden = []
    for name in members:
        parts = name.split("/")
        if posixpath.normpath(name) != name or name.startswith("/") or ".." in parts:
            forbidden.append(name)
        if any(part in {".git", ".venv", ".runtime", "__pycache__"} for part in parts):
            forbidden.append(name)
        if any(part == ".env" or (part.startswith(".env.") and part != ".env.example") for part in parts):
            forbidden.append(name)
        if name.startswith(("system/data/raw/", "system/data/docs/raw/", "system/data/processed/", "system/data/models/", "system/models/")):
            forbidden.append(name)
    values = dotenv_values(ROOT / ".env")
    secrets = [value.encode("utf-8") for key, value in values.items() if value and (key.endswith("PASSWORD") or key.endswith("API_KEY") or key == "DB_URL" or key.endswith("_DB_URL"))]
    matches = [name for name, content in members.items() if any(secret in content for secret in secrets)]
    broken = []
    local_links_checked = 0
    for name, content in members.items():
        if not (name.startswith("阅读版/") or name in {"01-D1阶段汇报.md", "02-D1逐项验收证据.md"}) or not name.endswith(".md"):
            continue
        for match in LINK.finditer(content.decode("utf-8")):
            target = unquote(match.group(2) or match.group(3)).partition("#")[0]
            if target.startswith(("http://", "https://", "mailto:", "codex:", "app:")) or not target:
                continue
            path = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
            # Report source examples that are not actual local file links separately.
            if path in members:
                local_links_checked += 1
            else:
                broken.append({"from": name, "target": target})
    if forbidden or matches or broken:
        raise RuntimeError(json.dumps({"forbidden_paths": forbidden, "credential_match_files": matches, "unresolved_local_links": broken}, ensure_ascii=False))
    manifest = {
        "source_repository": REPO_URL, "source_commit": SOURCE_COMMIT,
        "source_file_count": len(sources), "source_total_bytes": sum(map(len, sources.values())),
        "source_files_equal_frozen_git_archive": True,
        "main_evidence_links_rewritten": main_links,
        "reading_copy_links_rewritten": rewritten_links,
        "offline_local_links_checked": local_links_checked,
        "forbidden_paths": [], "configured_credential_match_files": [], "unresolved_local_links": [],
        "credential_scan_scope": "Exact matches of this machine's configured API keys, database passwords and URLs; no values recorded",
        "excluded": [".env", ".git", ".venv", ".runtime", "model weights", "raw corpus PDFs", "derived indexes", "database runtime state"],
        "model_evaluation_rerun_for_packaging": False,
        "files": {name: {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()} for name, content in sorted(members.items())},
        "manifest_self_hash_excluded": True,
    }
    members["SHA256清单.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output = OUT_DIR / f"{PACKAGE_ROOT}-汇报与证据.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, content in sorted(members.items()):
            zf.writestr(PACKAGE_ROOT + "/" + name, content)
    with zipfile.ZipFile(output) as zf:
        if zf.testzip() is not None:
            raise RuntimeError("The final delivery ZIP failed its CRC check")
        for name, content in members.items():
            if zf.read(PACKAGE_ROOT + "/" + name) != content:
                raise RuntimeError("The final delivery ZIP does not match its manifest")
    receipt = {key: value for key, value in manifest.items() if key != "files"}
    receipt.update({"zip_path": output.relative_to(ROOT).as_posix(), "zip_bytes": output.stat().st_size, "zip_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "package_file_count": len(members), "zip_crc_and_all_member_bytes_verified": True})
    (OUT_DIR / "package-check.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORT_DIR / "离线交付校验.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
