# D1 A 验收与 30 题独立 AI 复核

验收时间（UTC）：2026-10-10T12:42:22.678231+00:00。审核类型：**AI**；审核者：Codex / d1_a_acceptance。

**工程与数据检查通过；原 gold 的语义检查发现 1 项错误和 2 项需明确口径。独立修正版已生成，原题集及原人工审核记录未覆盖。** 本报告的 `accepted` 仅表示 AI 语义结论，不表示团队人工接受。

- 原题集：30 题（21 dev / 9 holdout）；30 条标准 SQL 均经过真实执行，**30/30 结果与原记录逐字一致**，30/30 标注内容哈希有效。
- 本审核与修正版生成均为标准 SQL 核验，**模型预测 0 次，保留题模型预测 0 次**。
- 原题集语义结论：27 项 `accepted`、2 项 `needs_clarification`、1 项 `error`。
- 新修正版仅改 3 道开发题，保持分割和题族；9 道保留题与原题集完全一致；30 题仍为 `needs_human_review`。

## 1. D1 A 工程逐项验收

| 项目 | 实际证据 | 结论 |
|---|---|---|
| Chinook PG 和只读账号 | PostgreSQL 16.15；11 表、64 列、13 外键；SELECT-only ACL 与零行写入拒绝通过 | 通过 |
| 表名和年份 | public 中表名为 snake_case；invoice 为 2021-01-01T00:00:00 至 2025-12-22T00:00:00 | 通过 |
| DeepSeek JSON 接入 | notes/model-check.json 为真实 deepseek-flash 接入、JSON 校验及用量/链路记录；本次不重复请求 | 已有真实证据 |
| 统一调用与 trace | qa_agent/llm.py、qa_agent/trace.py；TraceRecorder.step 为请求内工具留痕实现 | 已实现，集成回归见总报告 |
| NL2SQL v0 | catalog→generator→SQLGlot→只读 executor；本次 30 gold 完成表列验证和执行；5000 ms 超时、200 行上限 | 数据链路通过；自然语言实跑见开发集 |
| 30 单表题与 EX | 9 类题，21/9 固定分割；eval/run_eval.py；原 19/21 草稿不覆盖 | 3 项已形成独立修正版；正式 EX 待人工接受 |
| Top 艺术家交接 | 实算 Top10 与交接记录一致；第一名 Iron Maiden，销售额 138.60 | 通过 |
| 地区口径检查 | 412 张发票中客户与账单国家差异 0；字段含义仍不同 | 通过；原数据不适合演示口径数值差异 |
| 真实目录 | 表名、列名、行数与列可空性均与数据库一致 | 通过 |

## 2. 30 题逐项语义审核

逐项核对题意、筛选、单位、日期边界、投影、NULL、排序与并列。保留题只执行既有标准 SQL，不向模型提供问题。
字符排序的数据库实测设置：`{'datcollate': 'en_US.utf8', 'datctype': 'en_US.utf8'}`；金额保持数据本身的单位，不凭空添加币种。

| ID | 分割 | AI 结论 | 真实 gold 核验 | 理由 |
|---|---|---|---|---|
| sql-01 | dev | accepted | 结果一致；1 行 | COUNT(*) 对客户行计数，结果 59；不受可空字段影响，无需 JOIN。 |
| sql-02 | dev | accepted | 结果一致；1 行 | 巴西映射为真实 country 标准值 Brazil，COUNT(*) 结果为 5。 |
| sql-03 | holdout | accepted | 结果一致；1 行 | 5 分钟等于 300000 毫秒，严格‘超过’使用 >，数量 1069。 |
| sql-04 | dev | accepted | 结果一致；5 行 | Brazil 筛选、四个指定投影及 customer_id 升序吻合；名字/姓氏分别为 first_name/last_name。 |
| sql-05 | dev | accepted | 结果一致；13 行 | 美国原始标准值为 USA，返回编号、城市、州，按客户编号升序。 |
| sql-06 | dev | accepted | 结果一致；10 行 | 高于 0.99 使用 >，按曲目编号升序 LIMIT 10，并返回单价；未擅自标注币种。 |
| sql-07 | dev | accepted | 结果一致；3 行 | 精确匹配职位 Sales Support Agent，返回编号、first_name、last_name，按员工编号升序。 |
| sql-08 | holdout | accepted | 结果一致；10 行 | 不少于 10 使用 >=，编号升序取前 10 张发票，并保留日期和总额。 |
| sql-09 | dev | accepted | 结果一致；1 行 | invoice.total 求和，无明细连接造成重复计数；真实结果 2328.60。 |
| sql-10 | dev | accepted | 结果一致；1 行 | AVG(milliseconds) 保持题面要求的毫秒单位，没有转换成秒或分钟。 |
| sql-11 | dev | error | 结果一致；1 行 | 题面要求两位小数，但原 SQL 为 AVG(total)，真实标准结果是 5.6519417475728155；金额比较量化可匹配 5.65，但原 SQL/结果展示精度仍不符。 |
| sql-12 | holdout | accepted | 结果一致；1 行 | COUNT(DISTINCT country) 统计国家种类；数据 country 无 NULL，真实结果 24。 |
| sql-13 | dev | accepted | 结果一致；24 行 | country 为客户所在地，分组计数后按人数降序、国家升序，未误用 billing_country。 |
| sql-14 | dev | accepted | 结果一致；25 行 | 按 genre_id 统计曲目数量，数量降序、编号升序处理并列；无需查流派名称。 |
| sql-15 | dev | accepted | 结果一致；24 行 | 明确账单国家，使用 billing_country；SUM(total) 按发票统计收入，不擅自标注币种。 |
| sql-16 | holdout | accepted | 结果一致；5 行 | 按员工职位 title 分组计数、职位名称升序，并非按员工名字分组。 |
| sql-17 | dev | accepted | 结果一致；5 行 | milliseconds 降序、track_id 升序 LIMIT 5，与题意一致；Chinook track 包含视频条目，这里按该表的曲目口径排序。 |
| sql-18 | dev | accepted | 结果一致；5 行 | invoice.total 降序、invoice_id 升序 LIMIT 5，满足题面与并列次序。 |
| sql-19 | dev | accepted | 结果一致；5 行 | last_name 降序、customer_id 升序，投影编号、名字、姓氏；字符排序采用实测 PostgreSQL 数据库排序口径。 |
| sql-20 | holdout | accepted | 结果一致；5 行 | artist.name 升序、artist_id 升序 LIMIT 5，满足名称及并列编号排序，沿用数据库排序口径。 |
| sql-21 | dev | accepted | 结果一致；10 行 | 2021 年采用 >= 2021-01-01 且 < 2022-01-01，避免时间分量导致年末漏算；编号升序取 10 张。 |
| sql-22 | dev | needs_clarification | 结果一致；6 行 | hire_date < 2004-01-01、编号排序及结果正确；‘名字’可能被理解为完整姓名，而原 gold 只投影 first_name，需明确字段。 |
| sql-23 | holdout | accepted | 结果一致；1 行 | 2025 年采用 [2025-01-01,2026-01-01) 半开区间，COUNT(*) 实测 80。 |
| sql-24 | dev | needs_clarification | 结果一致；8 行 | 邮箱结尾使用 LIKE '%@gmail.com'，编号排序正确；‘名字’可能被理解为完整姓名，需明确只返回 first_name。 |
| sql-25 | holdout | accepted | 结果一致；10 行 | 含 love 且不区分大小写使用 ILIKE，按编号升序 LIMIT 10；不是仅匹配独立单词。 |
| sql-26 | dev | accepted | 结果一致；1 行 | 题面明确 company 为 NULL，采用 IS NULL，不混同空字符串；真实计数 49。 |
| sql-27 | dev | accepted | 结果一致；10 行 | composer 为 NULL 使用 IS NULL，编号升序 LIMIT 10；未将 NULL 与空字符串混同。 |
| sql-28 | holdout | accepted | 结果一致；1 行 | reports_to 为 NULL 表示无直属上级，返回编号、first_name、last_name，编号升序。 |
| sql-29 | dev | accepted | 结果一致；0 行 | Antarctica 无匹配，标准结果是零行空表，不能替换为零或一行 NULL。 |
| sql-30 | holdout | accepted | 结果一致；1 行 | Atlantis 无发票，SUM(total) 返回一行 NULL，满足题面；不能 COALESCE 成 0。 |

## 3. 已完成的独立修正版

[修正版题集](E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.jsonl)；[前后变更与来源 manifest](E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.manifest.json)。

1. `sql-11`：SQL 改为 `SELECT ROUND(AVG(total), 2) AS average_total FROM invoice;`，真实重算结果 `5.65`。原 SQL 和结果保留在父题集及 manifest。
2. `sql-22`：题面明确‘名字（仅 first_name，不包含姓氏 last_name）’，保持原投影与日期条件；实算结果与原一致。
3. `sql-24`：同样明确 first_name，保持邮箱结尾筛选与原投影；实算结果与原一致。

三个修订均完成 AI 复核，仍待人工接受；它们形成新的评测版本，修正版成绩不能替换原 19/21 历史。不因旧模型多返回姓氏而放宽列数比较。

首次可复现生成命令（文件存在时需明确加 `--overwrite`，只替换独立修正版）：

```powershell
.\.venv\Scripts\python.exe -m eval.revise_d1_gold
```

本审核可重跑：

```powershell
.\.venv\Scripts\python.exe -m eval.a_acceptance_audit
```

## 4. 仍需团队完成的验收

A 对照原审核表及修正版清单逐题确认业务含义。正式评测要求实际人工接受与内容哈希一致；修正版 21 题的 `--draft-gold` 只能用于开发探索，不能代签。保留题不运行预测。

值链接、题库扩容、OCR/其他格式、AdventureWorks、澄清、多轮与跨源属于原计划 D2–D5，不列作今天遗漏。共同任务的私有远程仓库及最终集成回归由主验收流程记录。

## 5. 证据与溯源

- [结构化检查结果](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/a-review.json)：完整 30 条实际 gold SQL、列、结果、逐项结论及数据库 ACL。
- [原始 19/21 草稿](E:/中国电子杯-赛题八/system/eval/reports/d1-dev-draft/report.md)：历史保持不变。
- [原 30 题审核表](E:/中国电子杯-赛题八/system/eval/datasets/review/gold_review.md)：人工状态未改。
- 原题集 SHA256：`14ab118f0d325c8ab796a2802da78385c34619df809d13a2ad70d518943e4cfa`，审核后不变。
- 原数据库 SQL SHA256：`e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e`。
- 检查时 Git commit：`5c522a48c48e11378c4b4283cc26b90c7bb4d66a`；最终集成 commit 以主验收报告为准。
- 报告未包含 .env、API key、数据库 DSN 或口令。
