# D1：A + B 共用接口与实现交接

A 的 SQL 与 B 的单文档 RAG 已接入统一 API，Streamlit 只通过 HTTP 调用该 API。模型可用性、实际索引方式、工程验证和题库结果以具体实跑记录为准。

## 1. 实际入口和模块

| 入口／模块 | 用途 |
|---|---|
| `POST /api/chat` | SQL／指定文档共用问答 |
| `GET /health` | 进程、真实数据库连接与共享配置 |
| `GET /api/documents` | 受控清单，含标题、物理页数、哈希及 ready |
| `GET /api/documents/{doc_id}/file` | 清单登记的原 PDF |
| `GET /api/documents/{doc_id}/pages/{page}` | PDF 指定物理页 PNG，页从 1 起 |
| `qa_agent/schemas.py` | 共享请求、来源、响应、意图、证据与步骤 |
| `config.py`／`llm.py`／`trace.py` | 共享设置、JSON 模型调用／错误、真实步骤／计时 |
| `qa_agent/rag/service.py` | 实现指定文档加载、检索、证据回答与共享响应 |
| `rag/parsers.py`／`chunker.py`／`index.py` | 原 PDF 抽取、保留物理页切片、带来源哈希的索引 |
| `rag/embeddings.py`／`retriever.py` | CPU BGE-M3 QInt8 ONNX、单文档 BM25／dense 排名融合 |
| `ui/app.py` | 来源选择、答案、SQL／表、引用／原页、步骤 |

默认 API 8000、页面 8501，`RAG_HANDLER=qa_agent.rag.service:run_doc_qa`。实际函数关键字参数契约为：

```python
def run_doc_qa(*, question: str, doc_id: str, trace_id: str,
               intent: IntentContract) -> AnswerEnvelope:
    ...
```

这里说明签名，实际函数体已在源码中实现。A 统一本次 trace_id、追加 B 的实际步骤，并检查证据来自指定文档、编号唯一和响应结构正确。

## 2. 请求与 D1 范围

SQL 请求：

```json
{"session_id":"A-B-sql-demo","message":"来自巴西的客户有多少位？","scope":{"route":"sql","db_id":"chinook","doc_ids":[]}}
```

使用真实清单 doc_id 的文档请求示例：

```json
{"session_id":"A-B-doc-demo","message":"What does the document say about built-in microphones?","scope":{"route":"doc","db_id":null,"doc_ids":["ohr-manual-macbook-air"]}}
```

该例仅说明结构，不预先声明答案／成功。文档必须恰好一个已登记 doc_id；BM25 和 dense 候选都先按此范围筛选。`llm` 模式中文问题查询英文 PDF 会真实调用模型生成英文检索问题，保留数字、年份、单位和实体；dense 可以编码原中文问题，trace 记录实际方式。

D1 显式选来源，不把 `session_id` 当成多轮状态合并。`auto`／`hybrid`、多文档、AdventureWorks、跨来源和完整澄清按后续计划推进。SQL 通道只允许一张真实业务表；资料准备的多表 Top10 不代表多表 NL2SQL。

共享模型使用 `extra="forbid"`，字段不一致会失败；扩展放 `metadata` 或协调 schema。不要给 Evidence 增加未声明的 url，也不要用资料目录中的另一份协议覆盖当前 A 协议。

## 3. 响应与引用页码

保留 `AnswerEnvelope` 的 `trace_id`、`status`、`answer`、`rewritten_question`、`sql`、`table`、`evidences`、`clarification`、`intent`、`steps`、`error`、`metadata`。状态支持 `SUCCEEDED`／`EMPTY_RESULT`／`NEEDS_CLARIFICATION`／`UNSUPPORTED`／`FAILED`；HTTP 200 不等于业务成功。

证据字段为 `evidence_id`、`doc_id`、`doc_title`、`page`、`section_path`、`text`、`bbox`：

- `evidence_id` 本次唯一，答案 `[E1]` 必须对应实际证据；编号可能不连续。
- doc_id 严格等于请求，text 是实际原 PDF 证据文字，不能以模型摘要代替。
- **page 为从 1 起的 PDF 物理页，封面计页。** OHR 原页索引从 0 起，仅解析／标注转换时加 1，前端不再加 1。
- 章节仅填写实际识别到的路径；没有可靠坐标保持 bbox=null。页面显示原页与原文，不把未实现的框选高亮当成定位结果。

页面点击引用展示标题、实际原文和物理页，受控 API 返回对应页 PNG；打开原 PDF 附 `#page=N` 并可下载。文件服务只接收清单 doc_id、核对源哈希，不接收任意磁盘路径或模型生成网址。引用按钮仅切换展示，不再次调用模型；换来源不显示另一来源旧答案。

缺 key、模型失败、索引不一致等如实 `FAILED`，证据不足明确说明，不用固定演示答案替代失败。SQL 的空表、COUNT 0 和 SUM NULL 分开表达，金额保持精确字符串。

## 4. 六份真实 PDF 和索引

固定 PDF 修订为 `7f833e3eda9a571a9ea545a8f6d476fa1685033d`；清单／哈希在 `data/docs/manifest.csv`、`source_manifest.json`。来源许可说明见 `data/docs/README.md`。

| doc_id | 领域 | 资料 | 物理页 |
|---|---|---|---:|
| `ohr-finance-amd-2022` | finance | AMD 2022 Form 10-K | 121 |
| `ohr-law-affiliate` | law | Gulf South Medical Supply Affiliate Agreement | 8 |
| `ohr-textbook-geology` | textbook | Holmfirth and Glossop 地质节选 | 20 |
| `ohr-manual-macbook-air` | manual | MacBook Air 存档指南 | 76 |
| `ohr-news-executive-insight` | news | Executive Insight Healthcare 存档节选 | 20 |
| `ohr-academic-label-words` | academic | Label Words are Anchors 论文 | 16 |

合计 261 页、255 页可抽取原生文字。6 个空白／图片页保留页号，不虚构 OCR。存档资料答案按指定文件，不当成当前设备／行业信息。

准备／迁移顺序：

```powershell
Set-Location -LiteralPath 'E:\中国电子杯-赛题八\system'
.\.venv\Scripts\python.exe scripts/prepare_rag_data.py --selected-d1
.\.venv\Scripts\python.exe -m eval.rag_build_gold
.\.venv\Scripts\python.exe scripts/download_embeddings.py
.\.venv\Scripts\python.exe scripts/check_embeddings.py
.\.venv\Scripts\python.exe scripts/ingest_docs.py
```

已有 PDF 以 SHA256 验证后复用；新机未带模型需下载。BGE-M3 固定 QInt8 ONNX、CPU、1024 维 CLS／L2，Top-K 5、max length 512、batch size 2。来源／修订／哈希在 `data/model_manifest/bge-m3.json`；模型和处理产物不依赖 Git 迁移。

真实编码检查使用 `scripts/check_embeddings.py`。PDF 核心使用 PyMuPDF 文字块与字体，兼容原文由 pdfplumber 保留；bbox 反映实际文字块／联合范围，不冒充逐字坐标。中文 BM25 已用 jieba 分词。

**下载模型不会自动改变旧索引**，必须完成真实 dense 编码。`index_meta.json` 记录 `dense_embedding.enabled`、模型和向量哈希，enabled 后才使用 `bm25+bge-m3_dense_rrf`；仅 BM25 如实记录 bm25。源 PDF、清单、模型或索引改变后重建，拒绝哈希不一致。

运行时只读清单、原 PDF chunks 和索引，不读取 gold，不索引官方 QA 或 OCR ground truth。

## 5. 模型、步骤和启动

B 复用 A 的 `JsonLLM.complete_json` 与同请求 `TraceRecorder`；翻译、回答及网络／JSON 重试共享默认最多 3 次总尝试。真实阶段为 `doc_scope`、可能的 `query_translate`、`retrieve`、`doc_answer` 和模型调用，摘要记录候选、分数、证据页、实际模式／模型／token。

离线解析、建索引与首次加载不混成稳定热请求耗时。`RAG_ANSWER_MODE=extractive` 返回原文，适合排查且不调用回答模型；演示使用 llm，不将抽取模式记为生成式成绩。key／模式修改后重启 API，真实最小调用用 `scripts/check_llm.py`。

准备好数据库与索引后运行 `.\scripts\start_demo.ps1`。脚本复用健康项目 API，空闲端口时隐藏启动 API，日志／PID 在 `.runtime`；前台 Streamlit 用 Ctrl+C 停止，API 保持可用，不结束陌生进程。修改配置需显式重启旧 API。页面默认 8501、API 8000，只绑定本机；跨电脑需实际网络配置。

也可分别用项目 `.venv\Scripts\python.exe` 启动 `-m uvicorn api.main:app --host 127.0.0.1 --port 8000` 和 `-m streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false`。Bash 入口 `scripts/start_demo.sh`。UI 严格走共享 API，不直接调用 SQL 执行器。

## 6. Gold 和开发集评测

SQL 固定 30 题＝21 dev／9 holdout，A 核对 `eval/datasets/review/gold_review.md`。RAG 固定 20 官方 QA＝14 dev／6 holdout，保持问题、答案和原 ID，均单页 `evidence_source=text`，引用已机器定位实际 PDF。

RAG 全集数量 finance 1、law 3、textbook 5、manual 5、news 3、academic 3，各文档 1 保留题。全文和题库覆盖六域，14 dev 覆盖五域；唯一入选金融题在保留集，不描述为六域开发准确率。

**机器定位不代替人工接受。** B 打开 `eval/datasets/rag_review/rag_gold_review.md` 对照原页、答案和证据，仅记录实际审核的 ID：

```powershell
.\.venv\Scripts\python.exe scripts/review_rag_gold.py --accept rag-02,rag-03 --reviewer B
```

审核绑定内容哈希，题意、答案、文档、页码或 split 改变后失效。仅 Markdown 打勾不改题库状态，手写备注另存。SQL 对应命令为 `scripts/review_gold.py --accept sql-01,sql-02 --reviewer A`。

真实开发运行：

```powershell
# gold 未人工确认的开发探索。
.\.venv\Scripts\python.exe -m eval.run_eval --draft-gold
.\.venv\Scripts\python.exe -m eval.rag_run_eval --draft-gold

# 开发题 gold 有效人工接受后。
.\.venv\Scripts\python.exe -m eval.run_eval
.\.venv\Scripts\python.exe -m eval.rag_run_eval
```

SQL 比较执行结果 EX；草稿记 exploratory_ex。RAG 自动检查状态、指定文档、原文子串、金标页候选／引用命中和答案字符串，**属于机械诊断，不是语义准确率或 groundedness**。每次 RAG 的 `human_review.md` 还需人工判断实际回答正确完整、每项事实受引用支持。gold 审核和实际回答审核是两项工作。

准备不足产生 `READINESS_ONLY`、预测 0、不填成绩。实际运行保留请求、响应、引用、步骤、耗时和版本，失败计入分母，不覆盖既有目录。D1 不运行任何 holdout；后续冻结要求真实 tag、干净 Git、已接受 gold 和显式开关。

## 7. 取数与共同验收

`data/handoff/A_to_B_chinook.{json,md}` 保存实际 Top10，收入为所有发票明细 `unit_price * quantity`，Iron Maiden 第一、138.60。榜单含电视内容，后续音乐资料需核对实体类型；原数据未声明币种，不擅加货币符号。客户国和账单国含义不同，本次数据差异数为 0，不声称存在实际数值差异。

共同验收同一页面 SQL／表格与所选 PDF，引用能回到指定原页、换文档范围隔离、无依据和失败明确、步骤和耗时真实、审核状态清楚、未预测保留题。依赖在 `requirements.txt`，工程命令 `-m pytest -q --tb=short`、`-m pip check`、`scripts/check_secrets.py`；总通过数和实跑成绩以当次记录为准。
