# D1：A → B 接口与数据交接

本项目按用户“完成 A 剩余 D1 工作”的授权实现了 A 的数据库、单表 SQL 通道、共享模型调用与统一 API。本文给 B 接入 PDF 问答和 Streamlit 的具体契约；**B 的解析、索引、检索、证据回答和前端仍由 B 实现**。A 的 RAG 适配入口已存在，不代表 RAG 已经可用。

## 1. 共用入口与源码

共用入口是 `POST http://127.0.0.1:8000/api/chat`。本机接口文档在 `/docs`；API 启动方法见 `README.md`。B 的 Streamlit 可以作为 API 客户端展示 SQL 和文档通道，避免在前端另写一套 SQL 执行逻辑。

| 文件 | B 的用途 |
|---|---|
| `qa_agent/schemas.py` | 导入 `ChatRequest`、`SourceScope`、`AnswerEnvelope`、`IntentContract`、`Evidence`、`Step`、`ErrorDetail` |
| `qa_agent/config.py` | `get_settings()` 读取同一个本地 `.env`；字段 `.llm_*` 与 `.rag_handler` |
| `qa_agent/llm.py` | `JsonLLM.complete_json()`，共享超时、总调用预算、结构检查及错误分类 |
| `qa_agent/trace.py` | `TraceRecorder` 记录 B 实际发生的阶段，不编造步骤 |
| `qa_agent/pipeline.py` | 分派 SQL/doc、调用 B handler、验证共享响应 |
| `data/handoff/A_to_B_chinook.json`、`.md` | 艺术家实际 Top10、查询 SQL、收入和国家字段口径 |

Pydantic 协议使用 `extra="forbid"`：字段名不一致或在模型上塞额外字段会报错。添加新字段前 A/B 先协调；检索模式、评分、文档来源等扩展信息可放 `metadata`，不能擅自给 `Evidence` 添加 `url`。

## 2. 请求格式与路由边界

文档请求为：

```json
{
  "session_id": "B-d1-doc-demo",
  "message": "用户针对当前文档提出的实际问题",
  "scope": {
    "route": "doc",
    "db_id": null,
    "doc_ids": ["B真实清单中的doc_id"]
  }
}
```

这个 JSON 的 `doc_id` 是字段位置说明，必须换成 B 清单中的真实值。D1 文档通道要求且仅允许一个 `doc_ids`；没有选择或多选会返回 `UNSUPPORTED`。SQL 请求为 `route: sql`、`db_id: chinook`、空 `doc_ids`。`auto`、`hybrid`、跨来源链路和多文档比较是后续工作，当前入口会明确拒绝。

`session_id` 目前用于请求协议，不能据此宣称已实现多轮意图状态合并。D1 路由来自用户在界面的显式选择；`IntentContract` 也不代表中级题的完整语义识别和澄清已完成。

## 3. B 的 handler：模块位置、签名和返回值

默认配置：

```dotenv
RAG_HANDLER=qa_agent.rag.service:run_doc_qa
```

B 创建 `qa_agent/rag/service.py` 并实现以下关键字参数签名：

```python
def run_doc_qa(*, question: str, doc_id: str, trace_id: str,
               intent: IntentContract) -> AnswerEnvelope:
    # 在这里接 B 的实际检索、生成与核验实现。
    ...
```

上面是签名说明，`...` 不是完整实现，不应部署。`async def` 和相同的关键字参数也受支持。函数可以返回 `AnswerEnvelope`，也可以返回可通过 `AnswerEnvelope.model_validate()` 的 dict；A 的同步 FastAPI 路由会等待 awaitable。

可以用其他函数名和文件名，但 `.env` 的 `RAG_HANDLER` 必须同步修改，模块需要位于 `qa_agent.rag.` 下。保存配置后重启 API。B handler 不能再把请求递归发回 `/api/chat`，应直接调用自己的文档服务和共享模型调用层。

A 传给 B 的 `question` 是本次用户原问题；`doc_id` 是本次显式指定文档；`trace_id` 由 A 创建；`intent` 初始为 `IntentContract(route="doc", task_type="doc_qa")`。B 返回的 `trace_id` 会被 A 统一为当前值；B 的 `steps` 会追加在 A 的真实路由/调用记录后，`metadata.latency_ms` 会写成整个请求的时间。

A 已做的适配层检查包括：返回字段通过 Pydantic 验证；证据全部来自本次 `doc_id`；证据编号不重复。B 仍需自己校验原文、页码、答案引用及证据支持关系。不能把适配层检查当作引用忠实度已经核验。

如果 handler 未提供，返回 `UNSUPPORTED`，说明 B 的 RAG 入口尚未接入。已有模块缺依赖或发生导入错误时，返回 `FAILED / rag_dependency`；handler 抛异常或响应不合格时，返回 `FAILED / rag_failed`。错误会经过脱敏。B 可以主动返回有含义的 `ErrorDetail`，不要将异常转换成伪造成功答案。

## 4. `AnswerEnvelope`：前端展示与评测共用

| 字段 | 类型与用途 |
|---|---|
| `trace_id` | 必需字符串，本次请求关联编号 |
| `status` | 必需：`SUCCEEDED`、`EMPTY_RESULT`、`NEEDS_CLARIFICATION`、`UNSUPPORTED` 或 `FAILED` |
| `answer` | 必需字符串，真实答案或不足依据/失败说明 |
| `rewritten_question` | 可空；只有实际进行了改写才填写 |
| `sql` | 可空；SQL 通道的实际被校验并执行的 SQL，文档通常为 null |
| `table` | 可空；SQL 通道的结果行对象，文档通常为 null |
| `evidences` | `Evidence` 列表；B 实际使用的证据 |
| `clarification` | 可空 dict；真正需要澄清时才填写 |
| `intent` | 可空 `IntentContract`，可保留 A 传入的文档意图 |
| `steps` | `Step` 列表，来自实际阶段 |
| `error` | 可空 `ErrorDetail`，包含 `code`、`message`、`retryable` |
| `metadata` | 扩展 dict，可记录真实检索模式、候选数、模型/用量、来源定位等 |

SQL 的无记录状态为 `EMPTY_RESULT`；COUNT 返回 0 仍是有返回行的正常查询；SUM 的 NULL 保留 null。金额为精确字符串，B 的前端不能先转换为浮点再写回结果或伪造单位。

文档问答找不到足够证据时，可返回 `EMPTY_RESULT`、`answer="文档未提供足够依据……"` 并说明缺什么；接口不强制 B 采用这个业务约定，但 A/B 应统一前端文案。只有确实完成的证据回答才使用 `SUCCEEDED`。需要用户补充范围时使用 `NEEDS_CLARIFICATION`，有结构化补充问题；未实现能力使用 `UNSUPPORTED`；实际执行失败使用 `FAILED`。

前端必须按 `status` 展示状态，HTTP 200 不是业务成功。失败时展示安全的原因和可操作建议，仍可保留真实步骤帮助排查。

## 5. `IntentContract`：保留现有字段和边界

结构字段为 `intent_version`（默认 1）、`route`、`task_type`、`metric`、`time_scope`、`filters`、`grouping`、`order`、`assumptions`、`unresolved`。

- `route` 允许 `sql/doc/hybrid/chitchat`，实际 D1 入口只运行显式 `sql/doc`。
- `metric/time_scope/order` 可以为 null；其他列表字段默认空列表。
- D1 文档任务使用 `route="doc"`、`task_type="doc_qa"`。没有真正识别的年份、指标和筛选条件保持空或 null，不能补猜。
- `assumptions` 只记录实际采用的约定，`unresolved` 记录真实未解决项；填了结构字段不表示澄清模块已经实现。

## 6. `Evidence`：文档隔离、页码和引用可点击

| 字段 | 要求 |
|---|---|
| `evidence_id` | 本次响应唯一，例如 `E1`、`E2`；答案使用 `[E1]` 等相同编号 |
| `doc_id` | 必须严格等于请求指定值，不跨文档 |
| `doc_title` | 清单中的真实文档标题 |
| `page` | 可空整数；PDF 证据交接约定为物理页从 1 开始。模型允许 0，但 B 必须自行核验且不要把 0 当展示页码 |
| `section_path` | 实际识别到的章节路径列表；未识别就空，不编造 |
| `text` | 能在原文找到的证据片段，不能用模型总结代替引用原文 |
| `bbox` | 可空浮点列表；有定位数据才填，B 应记录坐标顺序、单位和页面尺寸 |

B 在解析产物中同时保存稳定 `doc_id`、来源文件/URL、文档标题、实际 PDF 页号与章节路径。引用的每个编号都要有对应 Evidence；每条 Evidence 都要能回到指定 PDF 的原文。答案中的数字和判断要由该片段支持，证据不足直接说明。

**检索必须先按 `doc_id` 限定候选集合，再做 BM25/dense 排名或融合。** 不可先从全库取 Top8 再删除其他文档。若 BM25 和向量索引分别实现，两侧都要执行这个范围约束；索引键和查询缓存键也应带 `doc_id`，不能复用另一份文档的结果。

引用可点击由 B 的前端实现：维护 `doc_id → 可信来源/PDF查看器` 的文档清单，点击 `[E1]` 时定位该文档的 `page`，展开原文证据、标题和章节路径。如果实现 bbox 高亮，同时核对页面坐标。来源清单由已下载资料生成，不能使用模型任意生成的链接。

`Evidence` 当前没有 URL 字段。B 可让前端读取自己的文档清单，或与 A 约定在 `metadata.document_sources` 保存该清单的引用；这属于推荐扩展，现有 API 没有提供 PDF 静态文件/查看器接口，B 需要自己实现访问和渲染。公开 URL 可以追加 `#page=N`；本地 PDF 要通过实际的 Streamlit 展示/下载或受控文件服务使用，不能承诺仅在答案后写页码就已可点击。

## 7. 真实 `Step` 与共享模型调用

`Step` 字段为 `name`、`status`（`ok/warn/error/skipped`）、`input_summary`、`output_summary`、`latency_ms`。B 应记录实际在线检索、生成和引用校验阶段；PDF 解析、离线索引构建和首次模型加载单独记录，不混成在线热请求耗时。

可以直接使用共享记录器，生成 B 自己的步骤再返回：

```python
from qa_agent.config import get_settings
from qa_agent.trace import TraceRecorder

trace = TraceRecorder(trace_id=trace_id, settings=get_settings())
with trace.step("retrieval", {"doc_id": doc_id, "question": question}) as step:
    # 这里执行真实的、按 doc_id 限定的检索。
    # step.output_summary 写实际候选数、实际模式和片段编号。
    ...

# B 返回 AnswerEnvelope(..., steps=trace.steps)。
```

这是使用方式说明，不是现成检索器。`TraceRecorder` 自动计时并在异常时记录错误；摘要里不要放 key、密码或完整连接串，不要编造“思考”轨迹。真实检索模式是 BM25 就写 BM25，只有 BGE-M3 成功加载且实际检索才记录 dense/混合模式。

模型调用复用 `JsonLLM(get_settings()).complete_json(system_prompt, user_prompt, response_model, trace)`。`response_model` 是 B 为生成结果定义的 Pydantic 结构，例如答案文本和证据编号。prompt 必须只给本次允许的证据，回答证据不足时不使用外部知识补齐。

共享调用层按一次请求维护总尝试预算，默认最多 3 次；JSON/网络重试共用预算。B 使用同一个 `trace`，不要在循环里不断新建记录器重置预算。无需另建一套 key、模型客户端或隐藏重试。模型配置更改后重启 API；本机真实模型可用性用 `scripts/check_llm.py` 验证。

## 8. SQL 数据和 Top10 交接

A 数据库为官方 Chinook 1.4.5，物理表列 `public` + snake_case；实际年份 2021–2025。读接口有 `qa_agent.sql.catalog.load_catalog()`、`validator.validate_sql()` 和 `executor.execute_sql()`，但 B 前端展示问数优先调用统一 `/api/chat`，不能把用户生成 SQL 直接送执行器而绕过校验。

D1 SQL pipeline 只允许一张真实业务表，不允许常量查询假装问数、多表 JOIN、跨来源或 AdventureWorks。Top 艺术家选择需要多表，它是 A 事先审查并直接执行的资料准备 SQL，**不代表 D1 NL2SQL 已支持多表**。

实际取数文件：

- `data/handoff/A_to_B_chinook.json`：可供 B 程序读取的英文名、artist_id、销售额、SQL、日期和字段口径。
- `data/handoff/A_to_B_chinook.md`：人读版本，含 Top10 排名和完整 SQL。
- `data/db/source_manifest.json`：固定来源、许可证、文件 SHA256 与镜像；`db_check.json` 是实际数据和权限。

Top10 第一名是 Iron Maiden，销售额 138.60，口径为所有发票明细 `unit_price * quantity`。榜单包含 Lost、The Office 等电视类内容条目，不能将所有 artist 自动当作乐队。B 后续准备“音乐风格”文档时要先核对实体类型并保持英文名和 artist_id 的映射；本次文件只是后续选材准备，不应把 D1 演示范围扩成跨源问答。

`customer.country` 是客户所在地，`invoice.billing_country` 是账单地址所在地，两者含义不同；原始数据的不同记录数为 0。文案可以讲含义，不能宣称已有数值差异，也不能未经标注地修改原始数据制造差异。原数据未在字段上声明币种，前端展示收入不得擅自加币种符号。

## 9. B 接入后的共同验收顺序

1. B 整理真实文档清单、PDF 页码、切片和索引，确定一个可回答问题及其真实原文。
2. 实现 handler 并设置 `.env`；重启 A 的 API，选择本次单文档 `doc_id` 调用 `/api/chat`。
3. 核对响应状态、证据全部同一文档、编号唯一、页码和原文正确、答案确实引用且被证据支持，步骤与耗时来自实际运行。
4. 使用另一份文档提出相同问题，确认检索范围确实隔离；对文档没提供答案的问题返回不足依据。
5. 在 Streamlit 通过同一 API 展示 SQL 答案、实际 SQL/表格、文档答案、可点击引用和实际步骤，记录真实页面体验。
6. B 的 RAG 开发集采用真实标签、逐题输出和人工证据核验，复用共享外层评测思路；当前 `eval.run_eval` 仅实现 A 的 SQL 评测，B 需要继续接文档题输入和文档判题，不能宣称它已评估 RAG。

B 本机独立配置自己的 `.env`，不要复制 A 的真实 key 或数据库管理口令到聊天和仓库。A/B 两台电脑如果需要联网访问 API，需要单独明确地址、访问范围与部署方式；默认 A 服务只绑定 `127.0.0.1`，本文不假设 B 的另一台机器已经能远程连接。
