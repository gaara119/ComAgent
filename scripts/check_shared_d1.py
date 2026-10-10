"""Read-only D1 shared-work audit; writes documentation, never edits schemas."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# The user's 2026-10-10 confirmation applies to this exact content, not to a
# future file encountered when somebody reruns the evidence command.
APPROVED_LF_SHA256 = "60b2816559f347dd60734f80563ae75fb453ab3903b528ed2d6075316b190445"

from qa_agent import schemas


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True, encoding="utf-8").strip()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: str, value: str) -> None:
    output = ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(value, encoding="utf-8", newline="\n")


def row(path: str, stage: str, detail: str, status: str | None = None) -> dict:
    present = (ROOT / path).exists()
    return {"path": path, "exists": present, "stage": stage,
            "status": status or ("IMPLEMENTED_D1" if present else "NOT_IMPLEMENTED_FUTURE"),
            "detail": detail}


def main() -> None:
    raw = (ROOT / "qa_agent/schemas.py").read_bytes()
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    raw_sha, lf_sha = sha(raw), sha(normalized)
    if lf_sha != APPROVED_LF_SHA256:
        raise SystemExit("Shared schema differs from the user-confirmed version. Obtain both members' agreement; no agreement records were refreshed.")
    head = git("rev-parse", "HEAD")
    source = ROOT / "notes/references/项目方案.md"
    repository = json.loads((ROOT / "notes/github-repository.json").read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / ".runtime/github-publish.json").read_text(encoding="utf-8"))
    remote = urlsplit(git("remote", "get-url", "origin"))
    # Never serialize a credential-bearing URL if a user later changes remote configuration.
    remote_public = urlunsplit((remote.scheme, remote.hostname or "", remote.path, "", ""))
    definitions = {}
    for name in ("SourceScope", "ChatRequest", "Step", "Evidence", "IntentContract",
                 "ErrorDetail", "AnswerEnvelope", "SQLGeneration"):
        cls = getattr(schemas, name)
        definitions[name] = {"fields": list(cls.model_fields), "json_schema": cls.model_json_schema()}

    directories = [row(name, "D1", "已建立并含实际 D1 文件", "DIRECTORY_READY") for name in
                   ("scripts", "data/db", "data/docs", "data/catalog", "qa_agent", "qa_agent/sql",
                    "qa_agent/rag", "api", "ui", "eval", "eval/datasets", "eval/reports", "notes", "notes/screenshots")]
    directories += [row(name, stage, "仅 README 说明后续工作；没有功能实现", "DIRECTORY_ONLY_FUTURE")
                    for name, stage in (("qa_agent/nlu", "D2"), ("qa_agent/clarify", "D3"),
                                        ("qa_agent/fusion", "D4"), ("data/aliases", "D2"), ("data/rules", "D3"))]
    files = [row("README.md", "D1", "环境、资料准备、启动和评测命令"),
             row("docker-compose.yml", "D1 / D3", "D1 已实作 chinook-pg；aw-pg 尚未建立，属于 D3", "PARTIAL_D1_COMPLETE"),
             row(".env.example", "D1", "无真实 key 的配置模板"),
             row("requirements.txt", "D1", "当前环境依赖版本已锁定"),
             row("scripts/start_demo.sh", "D1 / D5", "启动已准备环境；D5 冷环境一键准备尚未验收", "PARTIAL_D1_COMPLETE"),
             row("scripts/build_catalog.py", "D1", "从真实库构建 Chinook 目录"),
             row("scripts/build_value_index.py", "D2", "值索引、别名、拼音和向量"),
             row("scripts/ingest_docs.py", "D1", "真实 PDF 解析、切片、BGE-M3 索引"),
             row("scripts/scale_data.py", "D4", "标注扩容副本，效率实验"),
             row("data/db/Chinook_PostgreSql.sql", "D1", "官方 Chinook 源脚本"),
             row("data/db/chinook_schema.sql", "D1", "真实数据库 schema 导出"),
             row("data/docs/manifest.csv", "D1 / D2", "D1 六领域 6 份 PDF；最终 ≥10 份不同格式属于 D2 补齐", "PARTIAL_D1_COMPLETE"),
             row("data/catalog/chinook.yaml", "D1", "实际表列、外键、中文说明与示例"),
             row("data/catalog/aw.yaml", "D3", "AdventureWorks 目录"),
             row("data/aliases/aliases.csv", "D2", "别名配置"),
             row("data/rules/clarify_rules.yaml", "D3", "澄清规则配置")]
    files += [row(f"qa_agent/{name}.py", "D1", "共享 D1 实现") for name in
              ("config", "llm", "trace", "schemas", "pipeline")]
    files += [row(f"qa_agent/nlu/{name}.py", "D2 / D4", "后续 NLU / 要素链接 / 改写") for name in
              ("extract", "linker", "rewrite")]
    files += [row(f"qa_agent/clarify/{name}.py", "D3 / D4", "后续澄清规则 / 会话状态") for name in ("rules", "state")]
    files += [row(f"qa_agent/sql/{name}.py", "D1", "实际单表 SQL 链路") for name in
              ("catalog", "generator", "validator", "executor")]
    files += [row("qa_agent/sql/schema_linker.py", "D3 / D4", "后续精准表定位与外键补全")]
    files += [row(f"qa_agent/rag/{name}.py", "D1", "实际单文档 RAG 链路") for name in
              ("parsers", "chunker", "index", "retriever", "answer")]
    files += [row("qa_agent/fusion/planner.py", "D4", "后续两类跨源计划")]
    files += [row("api/main.py", "D1", "共享 FastAPI /api/chat 与健康检查"),
              row("ui/app.py", "D1 / D5", "D1 问答、来源和折叠面板已实作；完整评测看板 D5", "PARTIAL_D1_COMPLETE"),
              row("eval/run_eval.py", "D1", "通过 API 计算真实 SQL EX"),
              row("eval/metrics.py", "D1", "执行结果比较指标"),
              row("notes/dev-log.md", "D1", "开发日志与真实数值"),
              row("notes/screenshots/D1-sql.png", "D1", "真实界面 SQL 演示"),
              row("notes/screenshots/D1-rag.png", "D1", "真实界面文档与引用演示"),
              row("notes/screenshots/D1-rag-trace.png", "D1", "实际步骤展开图")]
    agreement = {"status": "AGREED_USER_CONFIRMED", "confirmed_on": "2026-10-10",
                 "timezone": "America/Chicago", "confirmation_source": "用户在本次验收明确确认 A 和 B 已核对并同意当前协议",
                 "confirmation_quote": "双方已核对并同意当前协议",
                 "scope": "当前 schemas.py 全部字段、Evidence.page 从 1 开始且封面计页；同意该项相对计划 0 起示意的调整",
                 "independent_signatures_verified": False, "coauthorship_verified": False,
                 "raw_sha256": raw_sha, "lf_normalized_sha256": lf_sha}
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "date_local": "2026-10-10",
              "timezone": "America/Chicago", "source_plan": "notes/references/项目方案.md",
              "source_plan_sha256": sha(source.read_bytes()),
              "git": {"inside_work_tree": git("rev-parse", "--is-inside-work-tree") == "true",
                      "root": git("rev-parse", "--show-toplevel"), "head_at_check": head,
                      "initial_commits": git("rev-list", "--max-parents=0", "HEAD").splitlines(),
                      "origin": remote_public, "repository_metadata": repository,
                      "last_upload_receipt": receipt, "receipt_is_prior_publication": True,
                      "private_verified_by_prior_receipt": receipt.get("private") is True,
                      "fresh_remote_probe_performed": False},
              "schemas": {"path": "qa_agent/schemas.py", "raw_sha256": raw_sha,
                          "lf_normalized_sha256": lf_sha, "models": definitions,
                          "agreement": agreement, "schema_edited_by_this_audit": False,
                          "page_contract": {"minimum": 1, "pdf_physical_page": True,
                                            "cover_counts": True, "plan_example_minimum": 0,
                                            "ohr_zero_based_page_conversion": "convert once while building evaluation records; UI adds nothing"}},
              "directory_audit": {"directories": directories, "files": files,
                                  "all_planned_directories_present": all(x["exists"] for x in directories),
                                  "future_implementation_is_not_claimed": True},
              "shared_requirements": [
                  {"id": "shared-01", "status": "PASS_D1_WITH_FUTURE_SCOPE_EXPLICIT",
                   "requirement": "git init、私有远程仓库、§3.7 目录", "evidence": "valid Git worktree + prior verified private remote receipt + per-path directory audit"},
                  {"id": "shared-02", "status": "AGREED_USER_CONFIRMED",
                   "requirement": "共享 schemas.py 已建立，A/B 同意当前版本；后续改动双方同意",
                   "evidence": "actual fields + raw/LF hashes + exact user confirmation; co-writing history is not asserted"}]}
    write("eval/reports/d1-acceptance/requested-shared-evidence.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    table = "| 方案路径 | 存在 | 状态 | 计划阶段与说明 |\n|---|---|---|---|\n"
    for item in directories + files:
        table += f"| `{item['path']}` | {'是' if item['exists'] else '否'} | `{item['status']}` | {item['stage']}：{item['detail']} |\n"
    write("notes/D1目录对照.md", f"""# D1 与方案 §3.7 目录逐项对照

验收日期：2026-10-10（America/Chicago）。代码仓库根目录为 `E:\\中国电子杯-赛题八\\system`。依据 `notes/references/项目方案.md` §3.7、§4.1、§4.2。

§3.7 展示整个九天工程的目录。D1 必需文件已有实际实现；各计划目录均已建立。D2–D4 功能文件仍按原计划实施，仅添加 README 保留对应目录，不能把目录存在说成功能已完成。

目录状态中，`IMPLEMENTED_D1` 表示实际 D1 文件已存在；`PARTIAL_D1_COMPLETE` 表示该路径的 D1 范围已实现、后续扩展尚未实现；`DIRECTORY_ONLY_FUTURE` 仅表示目录已建立；`NOT_IMPLEMENTED_FUTURE` 表示未来文件尚未实现。

{table}

## 根目录资料位置与后续范围

方案中的 `comagent/` 父目录是组织示意；本机对应 `E:\\中国电子杯-赛题八`，代码在其 `system/` 内初始化 Git。原设计库 Markdown 留在父目录；实际计划与官方赛题副本位于 `notes/references/项目方案.md`、`notes/references/赛题八准则.pdf`，供仓库内核对来源。

六份 OHR 原 PDF、原 QA 下载缓存、BGE-M3 权重和派生索引保留在本地并通过脚本准备，不随 Git 克隆自动存在。目录对照不能代替资料 SHA、模型编码和索引的工程验收；对应结果见 D1 工程报告及资料清单。

本次补齐 `qa_agent/nlu/`、`qa_agent/clarify/`、`qa_agent/fusion/`、`data/aliases/`、`data/rules/` 的说明文件，没有伪造 `extract.py`、`state.py`、`planner.py` 等实现。AdventureWorks、别名/澄清配置、扩容实验、≥10 份不同格式知识库和完整评测看板均属于后续计划。

只读复核命令：`python scripts/check_shared_d1.py`。命令会刷新共享项与目录文档，读取当前协议，不修改 `qa_agent/schemas.py`，不调用模型，不改变人工 gold 审核状态。
""")
    field_table = "| 模型 | 实际字段 |\n|---|---|\n"
    for name, model in definitions.items():
        field_table += f"| `{name}` | {', '.join('`' + key + '`' for key in model['fields'])} |\n"
    write("notes/共享协议确认.md", f"""# D1 共享协议确认与后续修改约定

确认日期：2026-10-10（America/Chicago）。协议路径：`qa_agent/schemas.py`。当前状态：**`AGREED_USER_CONFIRMED`**。

## 当前版本确认

用户在本次验收明确回复：**“双方已核对并同意当前协议”**。问题明确包含当前 `Evidence.page` 从 1 开始、封面计页，以及相对方案 §3.5 的 0 起示意调整，因此本记录将 A、B 对当前协议的共同确认记为已完成。

| 确认项 | 状态 | 依据 |
|---|---|---|
| A 核对并同意当前版本 | 用户确认完成 | 上述用户回复 |
| B 核对并同意当前版本 | 用户确认完成 | 上述用户回复 |
| 页码约定及相对计划的调整 | 用户确认同意 | 本次确认问题明确包含此项 |
| 两人是否曾共同手写文件 | 未核查 | 用户确认代表当前协议同意，不提供历史共同编写证据 |
| A、B 是否独立电子签名 | 未核查 | 方案未要求额外签字；没有伪造签名 |

确认绑定以下内容版本：

- 原始文件字节 SHA256：`{raw_sha}`。
- 将 CRLF / CR 统一为 LF 后的 SHA256：`{lf_sha}`。
- 审计开始时 Git HEAD：`{head}`。这是检查时源码版本，不宣称为本次报告最终上传提交。

LF 归一化哈希用于两台电脑之间核对同一文本内容；Git 行尾转换可能让原始字节哈希不同。任何实质内容变化都会改变 LF 哈希，必须重新取得双方同意。上述哈希由本机实际文件计算，本次审计没有修改协议文件。

## 实际模型与字段

{field_table}

所有模型继承 `ContractModel`，其 `extra="forbid"` 拒绝未约定字段。`AnswerEnvelope.status` 为 `SUCCEEDED / EMPTY_RESULT / NEEDS_CLARIFICATION / UNSUPPORTED / FAILED`。完整字段类型、默认值和约束由实际 Pydantic `model_json_schema()` 导出到 `eval/reports/d1-acceptance/requested-shared-evidence.json`。

计划 §3.5 展示 Step、Evidence、IntentContract、AnswerEnvelope 四个主要协议；实际额外建立了 SourceScope、ChatRequest、ErrorDetail、SQLGeneration，供输入验证、错误返回和模型 JSON 验证共用。公共 schema 的存在不表示多轮澄清或跨源能力已经实现。

## 页码合同

当前 `Evidence.page` 为 `int | None`，数字页码约束 `ge=1`。它表示 PDF 物理页，封面计页，前端直接使用，不再加 1。OHR 原始 0 起证据页仅在题库标注转换时加 1。

方案 §3.5 的示意写的是“物理页，从 0 开始；展示时 +1”，属于已明确记录并获双方同意的调整。实际解析、API、引用展示和原 PDF 页打开统一使用当前 1 起约定。`tests/test_evidence_pages.py` 验证 page=1 可用、page=0 被拒绝，None 保留给无分页证据。

## 后续变更必须双方同意

1. 提议者先说明字段、类型、状态、默认值、页码或验证约束的具体变更及对 API、UI、评测的影响，并附旧版本与拟议新版本内容及 LF 哈希。
2. A、B 各自明确同意具体拟议版本；可在 PR、协作记录或本文件记录确认人、日期与可核对的确认文字。仅有目录、自动测试通过或单方勾选不能代替双方同意。
3. 未取得双方同意，不修改或合并公共协议。双方同意后按同意的版本落实；内容再变时重新确认，再同步消费者、接口示例和必要验证。
4. 更新本记录及版本哈希，两台电脑核对 LF 哈希。不要把今天的同意视为以后任意修改的永久授权。

`.github/pull_request_template.md` 已提供确认栏，作为约定的记录工具。本次没有配置或声称 GitHub 保护分支、强制两人审阅或自动审批策略。

只读核对：`Get-FileHash -LiteralPath 'qa_agent/schemas.py' -Algorithm SHA256`；完整证据刷新：`python scripts/check_shared_d1.py`。刷新只读取实际文件，不修改协议，不记录虚假的人工审核。
""")
    write("eval/reports/d1-acceptance/requested-shared-evidence.md", f"""# 用户要求的 D1 上午共同项证据

验收日期：2026-10-10（America/Chicago）。具体来源：项目方案 §3.5、§3.7、§4.2。

| 共同项 | 结论 | 可核对证据与边界 |
|---|---|---|
| `git init`、私有远程仓库、按 §3.7 建目录 | D1 范围通过 | `git rev-parse --is-inside-work-tree` 实际为 true；Git 根为 `{git('rev-parse', '--show-toplevel')}`；私有属性见此前实际上传回执；计划目录均存在，后续文件逐项明确未实现 |
| 共享 `schemas.py`、之后改动双方同意 | 当前版本已获双方同意 | 用户明确确认“双方已核对并同意当前协议”，包括 1 起页码调整；协议原始字节与 LF 哈希绑定，字段从实际代码导出，之后改动必须重新取得双方同意 |

## Git 与远端

- 远端：`{remote_public}`。
- 仓库 private：最近实际验证回执为 `{receipt.get('private')}`。
- 最近实际远端验证时间：`{receipt.get('verified_at_utc')}`。
- 最近实际上传提交：`{receipt.get('commit')}`，回执记录 API / ls-remote / 本地一致为 `{receipt.get('api_remote_local_heads_match')}`。
- 检查时 HEAD：`{head}`。本次新增文件尚由主验收任务统一提交与上传；不能将上一次回执当成新文件已上传。
- B 权限：用户于 2026-10-10 确认已添加；另一台电脑克隆及环境准备尚未实测。

以上仓库属性复用已保存的真实验证回执，本审计没有重新发起 GitHub 私有属性探测，没有改变远端策略。Git 工作树存在及初始提交证明本地仓库已初始化，不伪造初始化终端截图或历史命令。

## 目录与协议版本

- 逐路径证据：`notes/D1目录对照.md`。
- 当前确认与后续变更约定：`notes/共享协议确认.md`。
- 当前协议原始 SHA256：`{raw_sha}`。
- 当前协议 LF 归一化 SHA256：`{lf_sha}`。
- 全字段与 JSON Schema：同目录 `requested-shared-evidence.json`。
- PR 记录模板：`.github/pull_request_template.md`。模板不是保护分支或自动审阅机制。

两项共同工作已有实际产物与当前确认；“两人一起手写”的历史未提供，记录不作该事实断言。本次只补齐后续目录说明及共同确认文档，没有修改 `schemas.py`、调用模型、修改 gold 审核或扩展 D2–D4 功能。
""")
    assert (ROOT / "qa_agent/schemas.py").read_bytes() == raw, "Audit must not modify shared schema"
    print(json.dumps({"all_planned_directories_present": result["directory_audit"]["all_planned_directories_present"],
                      "schema_status": agreement["status"], "raw_sha256": raw_sha,
                      "lf_normalized_sha256": lf_sha, "schema_edited": False,
                      "audited_directories": len(directories), "audited_files": len(files)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
