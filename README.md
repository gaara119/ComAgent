## 本轮 D2 收尾、D3 与专项交付（2026-10-11）

D2、D3 的实施和实际开发验收均已完成，人工待核事项及保留集按原计划保留。专项已生成60条synthetic dev（49可评分、11原标签待确认），实际运行V0/V1/V2各60条，固定评分均18/49。最终保留V1的条件补丁prompt修正；V2因误拒合法比例表达和多轮来源而撤回，全部试验证据保留，无V3。

- [D2原清单九项验收](eval/reports/d2-final/D2原清单九项逐项验收与证据.html)。
- [D3原清单八项验收](eval/reports/d3-acceptance/D3原清单八项逐项验收与证据.html)和[D3统一待人工审核表](eval/reports/d3-acceptance/D3统一待人工审核表.html)。
- [专项十项验收](eval/experiments/after_d2_01_03/reports/acceptance/①③专项造题与提示词优化-逐项验收与证据.html)和[专项60条统一待人工审核表](eval/experiments/after_d2_01_03/reports/manual-review/①③专项统一待人工审核表.html)。
- [实际采用及回退决定](eval/experiments/after_d2_01_03/reports/version-decisions.md)、[剩余问题](eval/experiments/after_d2_01_03/reports/remaining-feature-gaps.md)、[复现与恢复说明](eval/experiments/after_d2_01_03/reports/restore-instructions.md)。
- [运行时system prompt原文清单](eval/experiments/after_d2_01_03/reports/acceptance/runtime-system-prompts/inventory.json)：实际业务模板和已归档provider完整system消息分开，模型接口及JSON Schema动态约束按原请求保留。

最终V1全模块实际415项通过。最终D2开发集实际回归77条：SQL35/35、鲁棒20/21；RAG金标Hit@5为20/20，实际19成功/1失败/1证据不足。详见[当前回归说明](eval/experiments/after_d2_01_03/reports/d2-final-regression-summary.md)。这些为开发集自动/AI探索结果；未作独立保留评测或补写人工签字。

各阶段ZIP在项目父目录，完整解压后打开各验收HTML，其证据使用相对路径。真实.env、密钥、虚拟环境、模型权重及保留题不包含在附件中。

# 赛题八：D1 / D2 / D3 问数问答项目

当前沿用 Python 3.12.10、已验证的 deepseek-flash、FastAPI 与 Streamlit，同一系统已接入 Chinook 和完整 AdventureWorks。D1 历史验收证据保留；D2 收尾与 D3 的新证据使用独立目录。

D2 收尾已实测 SQL 35/35、鲁棒 20/21；RAG 为19成功、1真实失败、1正确拒答，引用定位23条通过，答案支持仍有1项条件限制。模块296通过，五个真实浏览器场景和两个API探针通过。见 [D2原清单九项逐项验收与证据](eval/reports/d2-final/D2原清单九项逐项验收与证据.html)。54直接别名、25仅候选依用户共同审计意见启用关系，2证据不足继续停用；候选不能自动唯一绑定。

D3 已接入完整 AW（68表、456列、90FK）、中文目录、双路Schema Linking、RRF与Steiner、分级澄清、版本化意图补丁及页面交互。AW21开发题实际API首轮EX为21/21，复测为20/21；“产品编号”可指productid或productnumber的参考歧义已保留待人工核对，未强制提示词选gold字段。澄清开发集初始分级/询问行为21/21，不等同全部回答EX；真实多轮条件/金额/失效18项与地区来源2项共20/20，年份按钮增量4/4，最终真实页面10/10检查及7张截图通过。模块415通过；各轮源码SHA、失败、中止及增量采集区别见 [D3原清单八项逐项验收与证据](eval/reports/d3-acceptance/D3原清单八项逐项验收与证据.html)。目录两遍AI审查不代替人工签字；币种、枚举、字段单位和增长率展示形式存在的证据限制均保留。D2的33道保留与新D3的18道保留未预测，仍在D5冻结后运行。

页面 http://127.0.0.1:8501/，API http://127.0.0.1:8000/docs。在system目录启动本机已有服务：

```powershell
pwsh -NoProfile -File scripts/restart_services.ps1
```

既有 Chinook 不需重新导入或重建。AW初次安装见 scripts/bootstrap_aw.py --help 与 docker-compose.aw.yml，导入脚本检查已有库，不重复导入完整表。真实 .env 仅保留本机，新的机器从 .env.example 填写自己的只读连接和密钥；虚拟环境、模型权重和数据库卷不随证据ZIP提供。

当前RAG索引 data/indexes/docs-d2-final-v4.3，值索引 data/indexes/values-d2-reviewed，AW结构索引 data/indexes/schema-aw-d3-v2。需在新机器重建索引时沿用各build脚本，不使用未经审核的别名或业务默认。每次模型逻辑调用最多3尝试，每条API请求总预算12，数据库只读5秒超时、最多展示200行。

①③专项实验全部为本轮合成开发数据，独立目录 `eval/experiments/after_d2_01_03/`；不等同官方题库或独立泛化成绩。新成绩仅引用实际报告、原始输出与被冻结版本，待人审项不会自动改成已审核。

以下为D1历史记录，旧题量、旧索引和旧成绩仅描述当时版本。

## D1 历史验收记录

**2026-10-10 原清单最新复查已完成：159项pytest、0skip、6.22秒；53/53项工程检查通过。** 本轮补齐真实`@traced`及固定三个折叠面板；用户确认当前协议双方同意。六份PDF本轮经hf-mirror实下载且SHA一致，QA镜像404而保留官方固定GitHub来源。数据库外键实数为11。新UI两题/3个LLM步骤/8项浏览器检查通过，详见 [十四项证据表](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/requested-d1-evidence.md)。原35题benchmark和下面前一轮57项工程/149项测试记录保持，不能把新UI耗时替换原均值。


A 的 Chinook 单表问数和 B 的单文档问答已接入同一个 FastAPI，Streamlit 页面显式选择数据库或一份 PDF。答案、SQL、结果表、引用原文、PDF 对应页和处理步骤均来自实际请求。

**2026-10-10 本轮 D1 本机技术验收：PASS。** 工程逐项检查 **57/57**；其中完整 pytest **149 passed、0 skipped，5.71 秒**，依赖与当前／Git 历史凭据检查通过。额外四道真实边界问答均通过，空表、COUNT 0、SUM NULL 以及无法回答的文档问题均保持正确状态。

| 本轮实际记录 | 结果与口径 |
|---|---|
| SQL 开发集 | 独立修正版 **21/21，草稿探索值 100%**；平均 3405.886 ms；开始版本 `379bfdf`，工作区干净 |
| RAG 开发集 | 实际 14 题，调用与引用机械检查均 **14/14**；平均 3184.143 ms；开始版本 `596214c`，工作区干净 |
| RAG 独立 AI 复核 | 答案语义正确 14/14、断言支持完整 14/14、联合通过 14/14；审核类型为 AI，仍非人工签字 |
| 当前索引 | v2、**1527 × 1024** 真实有限归一化向量；1402/1527 片段有可靠 bbox；226 个句子边界不完整标志如实保留 |
| 资料与分割 | 六域六份 PDF，261 物理页／255 文字页；RAG 14 dev 覆盖五域；SQL 9 + RAG 6 保留题均未预测 |
| 本轮开发集用量 | 35 个 benchmark 请求／35 次模型调用，107751 total_tokens；不含额外 live、UI、探测与历史草稿 |
| 额外 live 验证 | 4 个真实请求、5 个模型步骤；独立记录，不并入 35 题开发集分母 |

完整证据见 [D1 验收清单](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/checklist.md)、[工程报告](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/engineering.json)、[SQL 修正版实跑](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/sql-dev/report.md)、[RAG 实跑](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/rag-dev/report.md) 和 [RAG 独立 AI 复核](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/b-review-final.md)。原 A 的 19/21 与 B 的 1381 片段／141 测试／首轮 14 题报告均保留为历史，不以新结果覆盖。

私有仓库已首次推送至 [项目 GitHub](https://github.com/gaara119/china-electronics-cup-task8-comagent)，首推版本 `a967f4d`；已核验私有状态以及本地与远端提交一致。此记录仅指已完成的首次推送，后续报告手册的上传由最终交付记录说明。

**团队 gold 人工接受仍为 0，校内截止时间与提交入口尚未外部确认。** 本轮通过的是本机技术验收和待人工审核 gold 上的开发探索，正式 EX／人工答案质量成绩不自动发布。

D1 范围为显式 `sql`／`doc`。多表 NL2SQL、AdventureWorks、多文档比较、自动来源判断、跨来源和多轮状态合并按后续计划推进。工程验证、模型接入和题库评测分别以 `notes`、`data` 与 `eval/reports` 中的实际记录为准。

## 已接入的数据和代码

| 内容 | 实际实现 |
|---|---|
| A 数据库 | 官方 Chinook 1.4.5，PostgreSQL 只读角色、中文结构目录、单表 SQL 生成／校验／执行 |
| B 文档 | 固定 OHR-Bench 六份 PDF，涵盖 finance、law、textbook、manual、news、academic 六域 |
| PDF 文字 | 261 个物理页，255 页可抽取原生文字；6 个空白／图片页保留页码，不生成虚构文字 |
| 检索 | 两路均先限定 `doc_id`；当前实际 v2 BGE-M3／BM25 RRF 混合索引为 1527 × 1024 |
| 模型 | 共享 DeepSeek JSON 调用；中文问题查询英文 PDF 时记录真实英文检索翻译调用 |
| 页面 | SQL／指定文档、实际答案、SQL／表格、引用原文、原页 PNG、PDF 打开／下载、实际步骤／耗时 |
| SQL gold | 30 题，固定 21 dev／9 holdout，业务含义等待人工审核 |
| RAG gold | 20 条官方 `evidence_source=text` QA，固定 14 dev／6 holdout，等待人工审核 |

六域 PDF 和 20 题全集涵盖六域；**14 道 RAG 开发题涵盖五域**，本次唯一合适的金融文本题固定在保留集。D1 不运行任何保留题预测。

Chinook 发票实际日期为 **2021-01-01 至 2025-12-22**，旧示例的 2009–2013 不适用于本次导入。数据固定来源、修订、许可和哈希见 `data/db/source_manifest.json`、`data/docs/source_manifest.json` 与 `data/docs/README.md`。

| 路径 | 用途 |
|---|---|
| `.env`／`.env.example` | 本机真实配置／不含凭据的模板 |
| `qa_agent/config.py`、`llm.py`、`schemas.py`、`trace.py` | A/B 共用设置、模型、协议和实际步骤 |
| `qa_agent/sql/`／`qa_agent/rag/` | SQL 链路／文档解析、切片、检索与证据回答 |
| `api/`／`ui/app.py` | 统一 API、受控文件服务／只调用 API 的页面 |
| `data/catalog/`／`data/handoff/` | 真实数据库目录／A 给 B 的取数资料 |
| `data/docs/manifest.csv`、`data/docs/raw/` | 六份 PDF 的受控清单／原文件 |
| `data/models/bge-m3/`、`data/model_manifest/bge-m3.json` | 本机模型／固定来源和 SHA256 |
| `data/processed/rag/ohr/` | 原 PDF chunks、索引元数据和实际 dense 向量 |
| `eval/datasets/`、`eval/reports/` | gold 及审核表／逐次真实评测与回答复核表 |

## 1. 环境和模型配置

本机已有 Python 3.12 环境，命令明确使用项目 Python，无需反复激活或重建：

```powershell
Set-Location -LiteralPath 'E:\中国电子杯-赛题八\system'
.\.venv\Scripts\python.exe --version
```

新电脑创建自己的环境并安装依赖，不复制旧 `.venv`。已有 `.env` 保留，不用模板覆盖：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

在本机编辑器填写 `LLM_API_KEY`，模型配置使用 `LLM_BASE_URL=https://api.deepseek.com` 和账号实际支持的 `LLM_MODEL`，当前配置为 `deepseek-flash`。新机还需填写 `POSTGRES_PASSWORD`、`DB_READER_PASSWORD`，使 `CHINOOK_DB_URL` 与 `qa_reader` 口令一致；默认本机端口为 55432，`AW_DB_URL` 在 D1 留空。应用优先读取非空 `CHINOOK_DB_URL`，兼容旧 `DB_URL`；超时优先使用 `SQL_STATEMENT_TIMEOUT_MS=5000`，兼容旧 `STATEMENT_TIMEOUT_MS`。

共享 RAG 配置：

```dotenv
RAG_HANDLER=qa_agent.rag.service:run_doc_qa
RAG_MANIFEST_PATH=data/docs/manifest.csv
RAG_INDEX_PATH=data/processed/rag/ohr
BGE_MODEL_PATH=data/models/bge-m3
RAG_TOP_K=5
RAG_EMBEDDING_MAX_LENGTH=512
RAG_EMBEDDING_BATCH_SIZE=2
RAG_EMBEDDING_DEVICE=cpu
RAG_EMBEDDING_QUANTIZATION=int8
RAG_ANSWER_MODE=llm
```

key 和口令只保留在本机 `.env`，不提交 Git。**修改 `.env` 后重启 API**，运行中的进程不会自动重载设置。真实最小模型验证：

```powershell
.\.venv\Scripts\python.exe scripts/check_llm.py
```

脚本检查账号模型列表并发起真实 JSON 调用，保存 `notes/model-check.json`。`llm_configured=true` 只表示读取到 key，真实可用性以实测为准。

## 2. 准备 A 数据库

打开 Docker Desktop，等待 Linux 引擎正常：

```powershell
.\.venv\Scripts\python.exe scripts/bootstrap_db.py
.\.venv\Scripts\python.exe scripts/check_db.py
.\.venv\Scripts\python.exe scripts/build_catalog.py
docker compose --project-name comagent-d1 ps
```

初始化脚本验证固定来源、生成安全导入 SQL、启动独立服务并配置只读角色，数据保存在命名卷。重复执行不会重复导入或删除卷。原始官方 SQL 有删除数据库的前言，实际使用 `Chinook_PostgreSql.import.sql`，不要手工重跑原始 SQL。

应用账号没有写权限。D1 SQL 还检查类型、真实表列、危险函数、单业务表约束与结果上限，拒绝常量冒充数据查询和多表 JOIN。列表默认限制 200 行，显式 Top-N 保留，超限标记 `metadata.truncated`；金额保持精确字符串，NULL 保持 JSON null，空表、COUNT 0 和 SUM NULL 分别表达。

排查／停止且保留数据：

```powershell
docker compose --project-name comagent-d1 logs --tail 80 chinook-pg
docker compose --project-name comagent-d1 stop chinook-pg
```

实际行数、日期和权限见 `data/db/db_check.json`。`data/handoff/A_to_B_chinook.md` 中 Top10 多表取数用于资料准备，不代表 D1 NL2SQL 支持多表。

## 3. 准备 B 的 PDF、模型和索引

新机准备固定六份 PDF 和官方 QA；已有 PDF 符合 SHA256 时验证后复用：

```powershell
.\.venv\Scripts\python.exe scripts/prepare_rag_data.py --selected-d1
.\.venv\Scripts\python.exe -m eval.rag_build_gold
```

第一条仅定向提取所需 ZIP 条目，无需下载整包。第二条生成文档清单、20 条 gold 和审核表，不调用模型；内容哈希相同的既有人工接受记录保留，内容改变需重新审核。其他可用参数为 `--list` 和可重复的 `--doc-name`；日常复现使用 `--selected-d1` 保持固定范围。

下载验证 CPU/int8 BGE-M3，再**重新构建索引**：

```powershell
.\.venv\Scripts\python.exe scripts/download_embeddings.py
.\.venv\Scripts\python.exe scripts/check_embeddings.py
.\.venv\Scripts\python.exe scripts/ingest_docs.py
```

模型使用固定修订的 BGE-M3 QInt8 ONNX 转换，1024 维 CLS 向量做 L2 归一化，下载约 587 MB。模型和处理产物不随 Git 迁移，新电脑需准备它们。来源、修订和 SHA256 见 `data/model_manifest/bge-m3.json` 及模型目录的 `download_manifest.json`。

`check_embeddings.py` 进行真实 CPU 编码、维度与归一化检查；下载验证和编码检查都不代表问答准确率。PDF 核心解析采用 PyMuPDF 文字块／字体信息，并保留 pdfplumber 兼容原文；实际识别的文字块坐标可用于定位，但当前页面不声称完成逐字框选高亮。中文 BM25 使用实际 jieba 分词。

**下载成功不会自动升级既有 BM25 索引。** 只有 `ingest_docs.py` 实际生成 dense 向量后，元数据 `dense_embedding.enabled` 才为 true，检索模式才为 `bm25+bge-m3_dense_rrf`。仅 BM25 时如实记录 `bm25`。查看实际状态：

```powershell
$indexMetadata = Get-Content -LiteralPath 'data/processed/rag/ohr/index_meta.json' -Raw | ConvertFrom-Json
$indexMetadata | Select-Object retrieval_method, chunk_count, dense_embedding
```

CPU 首次编码会耗时，等待完成后重启 API。源 PDF、清单、模型或索引变化后重建，系统拒绝哈希不一致的文件。`ingest_docs.py` 还支持 `--manifest`、`--index-path`，默认来自 `.env`。

运行时只索引原 PDF 文字，不把官方 QA、gold 答案／页码或 OCR ground truth 放入索引或模型提示。`RAG_ANSWER_MODE=extractive` 可用于不调用回答模型的原文排查；正常演示用 `llm`，不把抽取模式当成生成式问答成绩。

## 4. 启动同一页面与 API

数据库、模型配置和索引准备好后：

```powershell
.\scripts\start_demo.ps1
```

脚本复用健康运行的本项目 API；未运行且端口空闲时隐藏启动 API，日志写入 `.runtime`，随后当前终端运行 Streamlit。陌生端口占用只提示，不停止已有进程。

- 页面：<http://127.0.0.1:8501>
- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

选数据库查看实际 SQL／表格；选指定文档仅查询该 PDF。`[E1]` 和引用按钮显示实际原文、物理页与对应页 PNG，并提供原 PDF `#page=N` 打开和下载。引用按钮不会重发模型请求，切换来源不会混用旧答案。

`Ctrl+C` 停止前台页面，后台 API 保持可用；改 `.env` 后需显式停止旧 API 并重启。一键脚本不会替换仍在运行的服务。自选端口可用 `-ApiPort 8001 -UiPort 8502`，评测地址也要同步。

脚本执行策略受限时，可分两个终端直接运行：

```powershell
# 终端 1。
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

```powershell
# 终端 2。
.\.venv\Scripts\python.exe -m streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

页面只通过 HTTP 调共享 API；服务端 `QA_API_BASE_URL` 默认 8000，页面不提供任意服务地址输入。Bash 用 `bash scripts/start_demo.sh`。默认绑定本机回环，两台电脑远程协作需另行配置实际网络地址。

健康检查含实际只读连接和共享配置；文档就绪状态从 `/api/documents` 获取，实际检索方式从索引元数据及回答 trace 核实。HTTP 200 不等于回答正确；核对 `status`、`error`、SQL／结果／引用及步骤。业务失败也返回统一协议，页面显示未完成或证据不足。

## 5. 工程验证

本轮完整工程验收已保存为 `eval/reports/d1-acceptance/engineering.json`。默认验收脚本不发模型请求，`--live` 才增加三道 SQL 边界题和一道无法回答的文档题；已有报告拒绝覆盖。为新的验收选择独立时间戳输出：

```powershell
$d1AcceptanceStamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
.\.venv\Scripts\python.exe scripts/accept_d1.py --output "eval/reports/d1-acceptance/engineering-$d1AcceptanceStamp.json"

# 需要实际模型边界问答时另运行，输出名称与默认检查分开。
.\.venv\Scripts\python.exe scripts/accept_d1.py --live --output "eval/reports/d1-acceptance/engineering-live-$d1AcceptanceStamp.json"
```

脚本包括全量 pytest、依赖、凭据、服务、六份源 PDF／首末物理页／越界拒绝、来源边界、索引完整性、BGE 三句实际编码和真实 SQL 只读／超时／NULL 语义。测试输出先脱敏再保存，不写出 key 或 DSN。单独检查命令仍可使用：

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check_secrets.py --history
```

覆盖 SQL 权限与边界、结果保真、共享协议、文档隔离、索引完整性、引用和页面。数据库不可连接时有些集成检查明确跳过，跳过不代表实际链路已验证。测试中的替代模型用于工程边界，不计自然语言答案准确率。

## 6. A 的 gold 审核和 SQL 开发集

原 30 题和 [原审核表](E:/中国电子杯-赛题八/system/eval/datasets/review/gold_review.md) 保持不变。本轮独立 AI 审核发现 `sql-11` 未满足两位小数要求，以及 `sql-22`／`sql-24` 的“名字”字段歧义；已另建 [独立修正版](E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.jsonl)，分别使用真实 `ROUND(AVG(total), 2)` 结果 `5.65` 和明确的 `first_name` 题意。只改这三道开发题，分割仍为 **21 dev／9 holdout**，保留题内容不变。

本轮修正版真实实跑 21/21，仍是 gold 待人工接受时的探索值；来源与前后差异见 [修订 manifest](E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.manifest.json)，原 19/21 草稿不覆盖。查看 [修正版 30 题审核表](E:/中国电子杯-赛题八/system/eval/datasets/review_d1_acceptance/gold_review.md)，需要重新导出时明确指定新题集：

```powershell
$d1SqlDataset = 'eval/datasets/nl2sql_chinook_d1_acceptance.jsonl'
.\.venv\Scripts\python.exe scripts/review_gold.py --dataset $d1SqlDataset --output eval/datasets/review_d1_acceptance
```

核对题意、SQL、实际结果、字段、单位、日期、排序及 NULL／零／空表。AI 复核不代替人工接受；只对本人真正核对通过的 ID 记录接受，例如：

```powershell
.\.venv\Scripts\python.exe scripts/review_gold.py --dataset $d1SqlDataset --output eval/datasets/review_d1_acceptance --accept sql-01,sql-02 --reviewer A
```

通过真实 API 运行开发集：

```powershell
# 未人工接受 gold：草稿探索，仅预测 21 dev。
.\.venv\Scripts\python.exe -m eval.run_eval --dataset $d1SqlDataset --draft-gold

# 全部开发题已有效人工接受：正式 EX。
.\.venv\Scripts\python.exe -m eval.run_eval --dataset $d1SqlDataset
```

报告记录正确数／21、EX、失败、耗时和版本，失败保留在分母；草稿标为 `exploratory_ex`。缺 key、API／数据库不就绪或缺人工审核时为 `READINESS_ONLY`，预测 0、不填 EX。历史草稿在 `eval/reports/d1-dev-draft/`，新运行默认创建独立目录。

只有重建标准结果才运行 `python -m eval.build_gold`，之后核对审核状态。比较口径及后续冻结保护见 `eval/README.md`。

## 7. B 的 gold 审核和 RAG 开发集

20 条官方 QA 固定 **14 dev／6 holdout**，保留原问题、答案和 QA ID。gold 引用已机器定位到 PDF 指定页的连续文字；人工仍需确认题意、答案与证据支持。查看 `eval/datasets/rag_review/rag_gold_review.md`，只记录已核对的题，例如：

```powershell
.\.venv\Scripts\python.exe scripts/review_rag_gold.py --accept rag-02,rag-03 --reviewer B
```

两类审核均绑定审核人与内容哈希；题意、gold、文档、页码或 split 改变使旧记录失效。仅 Markdown 打勾不会修改源题库接受状态，手写备注另存。

通过实际 `/api/chat` 运行 14 道开发题：

```powershell
# gold 未人工确认：草稿探索。
.\.venv\Scripts\python.exe -m eval.rag_run_eval --draft-gold

# 开发题 gold 已人工接受：正式标注上的运行。
.\.venv\Scripts\python.exe -m eval.rag_run_eval
```

自动报告包含实际状态、引用、指定文档约束、原文子串真实性、金标页检索／引用命中、答案字符串匹配和耗时。**这些是机械诊断，不是答案语义准确率或 groundedness。** 每次运行的 `human_review.md` 需人工判断实际回答的正确性、完整性及每项事实是否被引用支持；gold 接受与回答审核是不同工作。

结果保存在新 `eval/reports/rag_*` 目录；未就绪为 `READINESS_ONLY` 且不计算运行指标。详见 `eval/datasets/rag_README.md`。**D1 不预测任何 holdout**；后续冻结运行要求实际 tag、干净 Git、已接受 gold 和显式开关，草稿不能绕过。

## 8. A/B 共同验收

在同一页面实际完成 SQL／表格和单文档答案演示；引用可回到指定 PDF 原页；换文档验证范围隔离；证据不足和失败状态明确；步骤与耗时真实；gold 和 RAG 实际回答审核状态清楚；未预测保留题。完整契约和维护交接见 `notes/B接口交接.md`，具体结果以当次实跑报告为准。
