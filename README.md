# 赛题八 D1：A 的后端、数据库与 SQL 问数

本目录落实你授权的“完成 A 剩余 D1 工作”：真实 Chinook 数据库、共享配置和模型调用层、数据库目录、单表 NL2SQL、SQL 校验与只读执行、统一 FastAPI、单表题库和评测工具，以及交给 B 的接口和取数文件。

B 的 PDF 解析、单文档检索、引用回答和 Streamlit 页面由 B 继续实现。当前目录提供 RAG 接入位置；不能把这个接入位置当成文档问答已完成。模型真实调用需要 A 在本地填写自己的可用凭据，gold 的业务含义需要 A 人工核验。最新运行记录以 `notes` 和 `eval/reports` 的实际文件为准，本说明给出复现操作。

## 1. 先认识项目

| 路径 | 用途 |
|---|---|
| `.venv/` | 已建立的 Python 3.12 项目环境；命令显式使用其中的 Python |
| `.env` | 本机真实模型 key、数据库口令和配置；不提交 Git |
| `.env.example` | 给另一台电脑看的配置字段模板，不含真实凭据 |
| `requirements.txt` | 本项目依赖版本，供迁移或重新建立环境 |
| `docker-compose.yml` | A 的独立 PostgreSQL 服务与持久化数据卷 |
| `qa_agent/config.py`、`llm.py`、`schemas.py`、`trace.py` | A/B 共用配置、JSON 模型调用、请求响应协议和真实步骤 |
| `qa_agent/sql/` | 数据库目录加载、SQL 生成、结构校验及只读执行 |
| `qa_agent/pipeline.py`、`api/main.py` | 显式来源路由与 `/api/chat` |
| `qa_agent/rag/` | 留给 B 的文档问答模块，默认入口为 `service:run_doc_qa` |
| `data/db/` | 官方原始 SQL、安全导入 SQL、许可证、来源哈希、实际 schema 和数据库检查 |
| `data/catalog/chinook.yaml` | 从真实数据库生成的结构目录与字段含义，不含 gold |
| `data/handoff/` | 艺术家 Top10 和地区字段口径，供 B 后续选材 |
| `eval/datasets/` | 30 题 gold；21 道开发题、9 道保留题 |
| `eval/reports/` | 逐次评测报告、实际请求响应和判题结果 |
| `tests/` | SQL 边界、序列化、接口、模型层与评测比较测试 |
| `notes/B接口交接.md` | B 的接入协议、文档范围、引用与前端展示要求 |

当前使用官方 Chinook **1.4.5**。表和列为 `public` schema 下的 snake_case。发票实际日期范围为 **2021-01-01 至 2025-12-22**，年份为 **2021–2025**；旧 Chinook 示例的 2009–2013 不适用于本次导入。此处是数据源事实，不代表模型评测成绩；需要时重新运行数据库检查获取最新记录。

## 2. 打开正确的 PowerShell 与 Python

在 PowerShell 输入：

```powershell
Set-Location -LiteralPath 'E:\中国电子杯-赛题八\system'
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
```

这台电脑已有 `.venv`，不需要反复重建，也不必激活环境。后面的每条命令都明确使用项目里的 Python。如果以后在 B 的另一台电脑建立环境，先使用与 A 一致的 Python 3.12 创建自己的 `.venv`，再执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

不要把 A 的 `.venv` 目录直接复制给 B。

## 3. 数据库启动、检查和结构导出

先打开 Docker Desktop，等待 Linux 引擎正常。然后在项目目录执行：

```powershell
docker info --format '{{.ServerVersion}}'
.\.venv\Scripts\python.exe scripts/bootstrap_db.py
.\.venv\Scripts\python.exe scripts/check_db.py
.\.venv\Scripts\python.exe scripts/build_catalog.py
docker compose --project-name comagent-d1 ps
```

`bootstrap_db.py` 会校验固定版本的官方 SQL 和许可证、生成安全导入文件、启动本项目服务、配置 `qa_reader` 并导出 schema。原始官方 SQL 含删除数据库的前言，实际初始化使用派生的 `Chinook_PostgreSql.import.sql`，不能拿原始文件手工重跑。重复执行脚本会保留业务数据和命名卷，不会重复导入或删除卷。

`check_db.py` 使用只读账号获取实际行数、国家值和发票日期，验证其没有写权限，并导出 B 的选材结果。`build_catalog.py` 用真实表列和主外键生成中文目录。检查记录见 `data/db/db_check.json`，来源与 SHA256 见 `data/db/source_manifest.json`。

连接规则：本机程序使用 `127.0.0.1:55432`；Compose 服务名是 `chinook-pg`、容器内端口是 `5432`。应用的 `CHINOOK_DB_URL` 使用 `qa_reader`，也兼容旧字段 `DB_URL`，优先读取非空的 `CHINOOK_DB_URL`。管理账号只用于初始化。此服务与已有其他 Docker 项目分开。

如果容器异常，先查看本项目日志：

```powershell
docker compose --project-name comagent-d1 logs --tail 80 chinook-pg
```

初始化 SQL 只在空 PostgreSQL 数据卷中运行。已有表结构与固定数据源不符时，脚本会停止，让你检查已有数据；不要用删除卷作为日常修复方式。停止数据库而保留数据可用：

```powershell
docker compose --project-name comagent-d1 stop chinook-pg
```

## 4. 在本地填写模型 key 并验证

用编辑器打开本机 `system/.env`，填写这三项：

```dotenv
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-flash
LLM_API_KEY=在本机编辑器内填写真实key
```

上面的 key 文本是说明占位，不能原样使用。`LLM_MODEL` 以你账号实际支持的模型 ID 为准。已有 `.env` 中的数据库口令由本机配置生成，保留它们；不要用 `.env.example` 覆盖现有文件，不要把 key 发到聊天、写进源码、截图或提交 Git。

你给出的共享字段已经纳入配置：`CHINOOK_DB_URL` 连接当前只读库；`SQL_STATEMENT_TIMEOUT_MS=5000` 控制 SQL 超时并优先于旧字段 `STATEMENT_TIMEOUT_MS`；`AW_DB_URL` 留作后续 AdventureWorks 配置。RAG 清单/索引/模型路径、Top-K、512 长度、2 批次、CPU/int8 与 `RAG_ANSWER_MODE=llm` 可由 B 通过 `get_settings()` 读取。这些是配置值；RAG 数据、模型和实际检索仍须 B 准备，配置本身不会自动建立索引。

保存后运行：

```powershell
.\.venv\Scripts\python.exe scripts/check_llm.py
```

脚本先读取账号的模型列表，再用配置模型做一次真实 JSON 调用；检查输出能否解析和满足结构，并记录耗时、实际模型和 token 用量。结果写入 `notes/model-check.json`。只有脚本实测成功，才能说模型接入已经完成；字段里有 key 并不意味着 key 有效。

认证、权限、余额、网络或模型 ID 不可用时，按脚本的具体原因修正本地配置。不要通过换成固定答案来绕过失败。**修改 `.env` 后需要重启 API**：配置在服务进程内缓存，已经运行的 API 不会自动读取新 key；检查脚本是新的 Python 进程，会读取当前文件。

## 5. 启动 API：一个终端运行，另一个终端请求

终端 1 保持在 `system` 目录，用以下命令启动：

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

该命令会一直运行，日志里显示服务地址。不要为了继续输入命令而关闭它。也可以使用 `scripts/start_api.ps1`；直接 Python 命令不依赖 PowerShell 脚本执行策略。

打开终端 2，在同一目录检查：

```powershell
Set-Location -LiteralPath 'E:\中国电子杯-赛题八\system'
Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:8000/health' | ConvertTo-Json -Depth 10
```

健康检查会返回进程状态、`database_ready`、`llm_configured`、`catalog_exists` 等。`database_ready` 来自真实只读 `SELECT 1`；`llm_configured` 只表示读取到 key，真实模型是否可用仍需 `check_llm.py` 验证。HTTP 200 或 `status: ok` 也不表示后面每一道问数都正确。

接口说明和可操作请求页面在 [本机 Swagger](http://127.0.0.1:8000/docs)。以下 PowerShell 请求不依赖前端：

```powershell
$requestPayload = @{
    session_id = 'A-d1-demo'
    message = '来自巴西的客户有多少位？'
    scope = @{
        route = 'sql'
        db_id = 'chinook'
        doc_ids = @()
    }
} | ConvertTo-Json -Depth 10

$answerResult = Invoke-RestMethod -Method Post `
    -Uri 'http://127.0.0.1:8000/api/chat' `
    -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($requestPayload))

$answerResult | ConvertTo-Json -Depth 20
```

核对返回中的 `status`、`answer`、实际 `sql`、`table` 和 `steps`。不要只看回答句子。`trace_id` 用于关联这一请求；返回的步骤来自代码实际执行，包含输入输出摘要与耗时。

当前 SQL 通道覆盖计数、筛选、聚合、分组、Top-N、日期、模糊匹配、NULL 和无匹配等单表题。请求必须显式选 `route: sql`、`db_id: chinook`、空 `doc_ids`。生成 SQL 必须引用真实业务表，**D1 拒绝跨业务表查询和用常量冒充数据库查询**；`auto`、`hybrid`、AdventureWorks、多轮改写等按照后续计划推进。文档通道必须显式选 `doc` 和一份文档，等待 B 实现后再验证。

只读执行之外，SQL 校验会检查语句类型、实际表列、危险函数和结果上限。没有 LIMIT 的普通列表会在外层限制默认 200 行，显式 Top-N 的 SQL 会保留；超过返回上限时通过 `metadata.truncated` 提示。金额以字符串保留精度，NULL 保留为 JSON null；空结果、COUNT 的 0 和 SUM 的 NULL 分开表达。

接口业务失败也使用统一响应，例如 `FAILED` 配合 `error.code`；不能因为 HTTP 为 200 就当成正确。缺 key、认证失败、SQL 被拒绝、数据库执行失败和超时要根据错误字段处理。停止或重启 API 时，在终端 1 按 `Ctrl+C`，再运行同一启动命令。

如果 8000 已被本项目服务占用，直接在终端 2 请求现有服务；修改配置后先停止旧进程。需要换端口时将启动命令末尾改为 `8001`，同时更改所有请求地址和评测 `--base-url`，不要混用两个服务。

## 6. 运行工程验证

数据库启动并建立目录后，在终端 2 运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check_secrets.py
```

测试包括 SQL 校验边界、金额和 NULL 等结果保真、只读事务、数据库超时、接口协议以及 EX 比较。真实数据库不可连接时，有些集成检查会明确跳过；出现跳过不能说真实链路已全部验证。测试中的脚本化模型只验证工程链路，不是自然语言模型准确率，不能作为 EX。真实模型问数和开发集评测需要继续执行下一部分。

## 7. 从 gold 审核到开发集评测

30 题已经固定为 21 道开发题、9 道保留题。D1 仅运行开发题的系统预测。标注 SQL 读取真实数据库建立标准结果，这与把问题发送给模型预测是两件不同的操作。

只有需要重新建立标注时才运行第一条；它会重新执行标准 SQL 并重写题库结果，随后要核对审核状态。第二条可随时导出当前审核表：

```powershell
.\.venv\Scripts\python.exe -m eval.build_gold
.\.venv\Scripts\python.exe scripts/review_gold.py
```

打开 `eval/datasets/review/gold_review.md` 或 UTF-8 CSV，对照每道题的自然语言、gold SQL 和实际结果，确认筛选值、时间边界、单位、排序、并列处理、NULL 和无匹配语义。A 真正核对完成后，按已核对的 ID 记录审核；下面只是接受两题的命令示例：

```powershell
.\.venv\Scripts\python.exe scripts/review_gold.py --accept sql-01,sql-02 --reviewer A
```

不能仅为获得分数而批量标记未核对的题。接受记录含内容哈希，修改问题、SQL、标准结果或划分会令旧记录失效。评测工具的详细口径见 `eval/README.md`。

如果模型配置完成、API 正常，但人工审核尚未完成，可以先探索 **21 道开发题**：

```powershell
.\.venv\Scripts\python.exe -m eval.run_eval --draft-gold
```

它会通过真实 `/api/chat` 调用当前系统，名称为 `exploratory_ex`，明确表示 gold 草稿，不能作为已人工核验的正式基线。此操作会产生模型调用费用，应在模型最小调用成功后运行。

21 道开发题的 gold 都经 A 实际审核后，运行正式开发集基线：

```powershell
.\.venv\Scripts\python.exe -m eval.run_eval
```

自定义端口时使用：

```powershell
.\.venv\Scripts\python.exe -m eval.run_eval --base-url 'http://127.0.0.1:8001'
```

结果写入 `eval/reports/dev_时间戳/`。先看 `report.md` 的实际预测数和状态，再看正确数/21、EX、失败分类和耗时；`responses.jsonl` 记录真正发出的请求、返回 SQL、答案、步骤及逐题判定。模型或数据库超时、错误状态和不正确结果都计入分母，不丢弃失败题。

如果 key 未配置、API 不可用、数据库不就绪或正式模式缺人工审核，报告为 `READINESS_ONLY`，预测数为 0，不填 EX。这是待处理条件的记录，不是性能成绩。文件不存在、准备检查通过或单题演示成功也不能当作 21 题评测已经完成。

**D1 不运行 9 道保留题的系统预测。** 后续 D5 冻结评测有独立参数、冻结 tag 与干净工作目录保护，操作见 `eval/README.md`。模型生成代码和目录不读取 `eval/datasets`，gold 不进入模型提示。

## 8. A 给 B 的交接和 D1 收尾

A 的交接文件是 `notes/B接口交接.md`、`qa_agent/schemas.py` 与 `data/handoff/A_to_B_chinook.{json,md}`。Top10 按实际发票明细单价 × 数量计算；其中还有电视类 artist 条目，B 选音乐风格资料前应复核实体类型。客户国家和账单国家是两个含义不同的字段，但本次数据源差异数为 0，不能声称已经展示它们的数值差异。

D1 收尾时，A 需要看实际文件确认这些结果：数据库检查和目录可复现；自己账号模型最小调用成功；自然语言 SQL 请求能返回真实结果、SQL 和步骤；21 题开发报告写清 draft/已审核、实际分母与失败；B 收到实际资料和接口。B 完成文档链路与页面后，再共同做同一页面上的 SQL/指定文档演示。本项目不以占位内容代替未接入的模型、文档链路或评测成绩。
