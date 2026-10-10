# D1 开发日志：A 后端与 SQL

日期：2026-10-10。实现目录：`E:\中国电子杯-赛题八\system`。

## 本次实现

保留用户已经创建的 Python 3.12.10 虚拟环境，在其中安装并固定依赖。实现共享 Pydantic 协议、项目本地配置、JSON 模型调用、请求级步骤记录、FastAPI 入口、Chinook 单表 SQL 链路、标注和执行结果评测工具。

数据库采用官方 Chinook 1.4.5，来源及 SHA256 记录在 `data/db/source_manifest.json`。PostgreSQL 16.15 通过 Compose 运行，仅绑定本机 `127.0.0.1:55432`，独立命名卷持久化。应用连接使用 qa_reader；已在 READ WRITE 事务中以零行 UPDATE 验证权限拒绝，数据修改数为 0。初始化重复运行后行数保持一致。

实际数据：11 张表、64 列、13 条外键；customer 59、track 3503、invoice 412、invoice_line 2240。发票日期为 2021-01-01 至 2025-12-22，不采用旧版本示例年份。艺术家销售额 Top10 已导出给 B，第一名为 Iron Maiden，金额 138.60；原数据未声明币种。客户所在国与账单国家在当前 412 张发票中的差异为 0，仍是不同业务字段。

## 已执行的验证

- `python -m pytest -q --tb=short`：91 passed，2.53 秒；包含真实 PostgreSQL 只读、超时、结果上限、NULL/零/空表和 API 接线测试，以及 JSON 调用预算、AST 校验、结果比较和共享配置兼容测试。Starlette TestClient 有一条 httpx 弃用提示，不影响本次通过。
- `python -m pip check`：No broken requirements found。
- `python scripts/check_secrets.py`：本地 `.env` 被 Git 忽略，待提交文件没有匹配到本机真实凭据；输出只显示匹配数和文件名。
- 30 条 gold SQL 在真实数据库中建立标准结果，又通过运行时 AST 校验器和只读执行器独立核对，30/30 与标注结果一致。这是标注验证，不是模型准确率。
- 模型真实接入成功：账号模型列表包含 `deepseek-flash` 与 `deepseek-v4-pro`，按用户选择使用 `deepseek-flash`。JSON 调用成功并保存实际模型、耗时和 token 用量；记录在 `notes/model-check.json`。
- API 已启动于 `127.0.0.1:8000`；实际 `/health` 返回 `database_ready=true` 和 `llm_configured=true`，`/docs` 可访问。真实模型对“客户表共有多少位客户？”生成 SELECT COUNT 并返回 59；完整请求、实际 SQL、结果及步骤在 `notes/api-smoke.json`。缺少 key 的失败路径也已经验证，没有伪造成功。
- 直接请求保留集评测被保护逻辑拒绝。保留集系统预测数为 0。

## 当前评测状态

30 道题固定为 21 开发题、9 保留题，题型按指导书分配。全部 gold 保留 `needs_human_review`；A 的逐题业务审核尚未记录。审核表位于 `eval/datasets/review/gold_review.md` 和 `.csv`。

已通过统一 API 唯一一次运行 21 道开发题的 `--draft-gold` 探索：19/21，`exploratory_ex=90.48%`，平均 HTTP 端到端耗时 3.217 秒/题。没有模型、数据库执行或接口格式失败。21 次模型调用实际累计输入 87,447、输出 1,565、合计 89,012 tokens；这些数值仅指本次 21 题，不含模型探测和独立 API 演示。完整报告、逐题原始响应和用量见 `eval/reports/d1-dev-draft/`，运行时代码版本为 `fe4c4b9bddc3dbc5e23aa1d0a7089f879e2be335`，启动评测时工作目录干净。

两项结果不一致为 `sql-22` 和 `sql-24`：问题写“名字”，gold 只取 first_name，模型另外取了 last_name，按严格列数口径判错。要求列的行值、条件和次序一致。已记录为人工审核时要明确的题意问题，没有删列提高原始成绩、改题或重跑。30 题仍待 A 人工接受，正式 EX 未发布；`eval/reports/d1-readiness/` 是正式模式的前置检查，本次不执行预测，只记录尚未人工确认的 gold，不代表项目从未运行草稿预测。

按用户追加配置，已在本地 `.env` 填好真实只读 `CHINOOK_DB_URL`、5000ms 的 `SQL_STATEMENT_TIMEOUT_MS`，保持兼容旧字段；AW_DB_URL 留空。已保存 RAG 清单/索引/BGE 路径、Top-K 5、长度 512、批次 2、CPU/int8 和 llm 模式，共享 Settings 可读取。RAG 数据、模型加载和量化仍由 B 实现，配置不代表相应能力已完成。

## 接下来

1. A 对照审核表逐题确认问题、标准 SQL、时间和单位、排序与结果，特别明确 sql-22/sql-24 的“名字”，然后记录接受的 ID。自动 SQL 核验不能代替此项确认。
2. 完成人工确认后，通过统一 API 运行正式 21 题开发集，保存 EX、错误类别和耗时；保留题留到 D5 冻结后。
3. B 按 `notes/B接口交接.md` 实现 RAG 函数与 UI，再合并两条链路并截图。B 的 RAG、文档下载与页面不属于本次 A 实现。
4. 双方确定私有远程仓库及同步方式；本次仅初始化本地 Git。校内截止时间与提交入口仍需团队向学校核实。

D2 待处理：中文国家别名及更完整的值链接、五级要素链接、意图细化和澄清、多表查询以及 B 文档检索。当前 AST 和业务表来源检查保证执行边界；查询是否忠实于题意仍需人工 gold 和真实评测判断。
