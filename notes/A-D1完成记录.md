# A 的 D1 实现与验收状态

## 2026-10-10 本轮最终技术验收状态

**本机技术验收 PASS；工程 57/57，其中全量 pytest 149 passed／0 skipped，5.71 秒。** A 的原 30 gold 重新实际执行为 30/30 逐字一致；独立 AI 语义审核发现 `sql-11` 的两位小数问题和 `sql-22`／`sql-24` 的名字歧义。已另建修正版，只改变这三道开发题：SQL 使用 `ROUND(AVG(total), 2)` 实算 `5.65`，两道题明确只返回 `first_name`。原题集、原人工状态和原 19/21 报告均保留。

修正版通过真实 API 实跑 **21/21，平均 3405.886 ms**，开始版本 `379bfdf` 且工作区干净。此项仍为待人工接受 gold 上的草稿探索，正式 EX 尚未发布。B 的本轮 14 题机械检查全部 14/14，平均 3184.143 ms，开始版本 `596214c` 且工作区干净；独立 AI 的语义、断言支持与联合复核均为 14/14，仍非人工签字。

两组 benchmark 共 35 请求／35 次模型调用／107751 total_tokens，不含 UI、历史草稿和额外 live。额外四道真实边界问答使用 5 个 LLM 步骤，均验证通过；SQL 空表、COUNT 0、SUM NULL 分别返回正确表达，无法回答的文档问题没有捏造证据。SQL 9 + RAG 6 保留题预测均为 0。

共同资料为六域六 PDF、261 物理页／255 文字页；RAG 开发题实际覆盖五域。当前 v2 dense 索引为 1527 × 1024，有限归一化，1402 个可靠 bbox，226 个不完整边界标志保留。私有仓库首推 `a967f4d` 已核验私有状态及本地／远端提交一致；最终报告手册上传以最后交付记录为准。

- [A 原 30 题独立 AI 验收](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/a-review.md)
- [修正版 30 题人工审核表](E:/中国电子杯-赛题八/system/eval/datasets/review_d1_acceptance/gold_review.md)、[修订前后差异与来源](E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.manifest.json)
- [修正版 21 题草稿实跑](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/sql-dev/report.md)
- [共同工程验收](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/engineering.json)、[本轮实际用量](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/model-usage.json)

剩余团队工作：人工逐题接受 gold（目前 0）、正式成绩和校内截止时间／提交入口的外部确认。AI 审核与工程 PASS 不替代上述确认；使用修正版审核和评测时需明确传入其 `--dataset`，避免误操作原题集。

## A 首次实现与草稿记录（历史快照）

以下保留原 A 阶段的 91 项测试、19/21 和 3.217 秒及当时状态，不作为本轮修正版实跑数字。新增验收与当前版本以本文上节及 `eval/reports/d1-acceptance/` 为准。

| 指导书任务 | 实际产物与核验 | 状态 |
|---|---|---|
| 3.1 Chinook 与只读角色 | Compose、校验下载、安全导入、权限初始化；真实数据库可用，ACL 拒绝零行写入 | 完成 |
| 3.2 共享配置与模型调用 | config、JsonLLM、JSON/Pydantic 校验、总调用预算；账号模型发现、Flash 真实 JSON 检查成功 | 完成 |
| 3.3 真实结构目录 | 11 表/64 列/13 外键、中文描述、实际示例和日期范围 | 已生成；A 可审阅语义 |
| 3.4 SQL 最小链路 | 生成→AST/表列核验→单表范围→只读执行→结果模板；5 秒超时、200 行展示上限、真实 trace；自然语言客户计数返回 59 | 完成并实测 |
| 3.5 API 与公共协议 | `/api/chat`、`/health`、请求/响应模型、SQL/RAG 分流、B 接口交接 | SQL/API 与 B RAG 均已接入；同页演示已有实跑记录，D1 全项验收进行中 |
| 3.6 30 题与开发集 EX | 21 开发/9 保留、真实 gold、审核表、确定性比较和 HTTP 评测；草稿实跑 19/21（90.48%） | 草稿基线完成；人工审核与正式成绩待完成 |
| 3.7 B 数据准备交接 | 真实艺术家 Top10、统计口径和 SQL；国家字段差异核验 | 完成 |
| 复现与记录 | requirements、启动脚本、README、开发日志、本地 Git、凭据忽略与检查 | 完成；两台电脑同步待团队联调 |

A 阶段首次验证记录：91 项测试通过，依赖检查通过，实际数据库健康检查通过；30 条标准 SQL 的运行结果独立核对一致。另以真实 `deepseek-flash` 运行 21 开发题，正确 19/21，平均端到端 3.217 秒/题，9 道保留题预测为 0。该结果基于待审核 gold，因此明确标记 `exploratory_ex`，不等同于人工核验后的正式成绩。

两道不一致为 sql-22 与 sql-24：问题使用“名字”，gold 要求 first_name，模型还返回 last_name。要求列、条件、行值和排序一致，但严格比较将额外列判为不一致。原始 19/21 已保留；人工复核时应明确 first_name 还是全名，不能为提高成绩事后删去模型额外列。

本地 `.env` 已按用户要求配置模型 key、实际只读 CHINOOK_DB_URL、SQL_STATEMENT_TIMEOUT_MS=5000 和给 B 的 RAG 默认参数；AW_DB_URL 留空。所有凭据保持 Git 忽略，共享代码兼容原 DB_URL 和 STATEMENT_TIMEOUT_MS。

当前运行：API `http://127.0.0.1:8000`，交互式接口文档 `http://127.0.0.1:8000/docs`；数据库 `127.0.0.1:55432`。B 页面已接入 `http://127.0.0.1:8501`，同一页面可选 SQL 或指定 PDF；未来重新打开项目时，按 README 预备后运行 `scripts/start_demo.ps1` 启动 API 与页面。修改 `.env` 后重启 API，启动进程会缓存配置。

从以下文件开始：

- `README.md`：复制运行命令和请求样例。
- `eval/datasets/review/gold_review.md`：逐题审核，CSV 可在 Excel 查看。
- `eval/README.md`：草稿探索与正式成绩的区别、审核记录和评测命令。
- `notes/B接口交接.md`：交给 B 的公共接口与接入方法。
- `data/handoff/A_to_B_chinook.md`：交给 B 的真实查询结果。
- `eval/reports/d1-dev-draft/report.md`：真实 21 题草稿报告；原始响应和用量/错误分析位于同一目录。
- `eval/reports/d1-readiness/report.md`：正式模式的前置检查；当前剩余条件为 gold 人工审核，该检查不执行预测。

人工审核来自指导书 3.6 的明确分工：“Codex 起草题目及 gold SQL，A 按业务含义逐题审查。”本次已完成可审阅的全部标准结果，保留人工接受步骤。key 只在本地 `.env` 填写，不需要发送到聊天。

## 同日 B 整合与验收说明

B 的六份 OHR PDF、真实 BGE-M3/BM25 索引、带编号引用的文档问答、文档 API 和 Streamlit 已实现；共享配置/模型/协议继续复用 A，接口页码采用从 1 起的 PDF 物理页。详细产物与 14 题实际开发草稿见 `notes/B-D1完成记录.md`，同页 SQL/文档/原页截图见 `notes/screenshots/D1-*.png`。

本记录中的 91 项测试及 19/21、平均 3.217 秒是原 A 阶段记录，保持原始分母、版本和草稿性质，不作为整合后重跑成绩。当前全项验收和最新回归由 `eval/reports/d1-acceptance/` 单独记录。A/B gold 人工接受、RAG 回答语义复核、团队外部确认分别保留实际状态，B 的工程完成不自动消除这些步骤。
