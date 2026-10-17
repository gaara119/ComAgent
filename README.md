# ComAgent 可解释问数问答智能体

项目通过 DeepSeek 理解问题，复用 PostgreSQL、文档检索和执行约束，返回答案、真实 SQL、查询结果、引用和处理步骤。

## 打开项目

本机双击 **启动项目.cmd**，浏览器进入 **http://127.0.0.1:8501/**。API 文档在 **http://127.0.0.1:8000/docs**。

默认界面采用本仓库 `frontend-workbench/` 的白色立体数据分析工作台，提供数据概览、数据分析、问答工作台、数据与文档、运行记录五个文字导航；已移除品牌图形与品牌 favicon。静态构建已包含在 `dist/`，日常运行无需 Node、npm 或 CDN。Python 静态服务仅代理本机 FastAPI。

启动脚本复用本工作区的 API 和现有数据库容器；数据库未就绪时显示实际状态，不删除数据卷，不重新导入业务库。旧 Streamlit 仅保留兼容与历史测试，不是默认入口。

## 功能

- 数据库问数：Chinook、AdventureWorks，SQL 生成、校验和只读执行。
- 指定文档问答：引用原文、物理页预览、来源下载及资料不足提示。
- 数据库与文档：Chinook 艺术家销售排名→介绍；口径手册定义→SQL计算。
- 多轮：保留会话和结构化条件，支持版本化澄清与授权口径切换。
- 完整会话正文：独立 `/api/context` 接收原文，按会话与版本保存；普通问题仍限制4000字符，正文最多120000字符。支持带时区的统一参考时钟。
- 自动综合：使用有界工具步骤组合数据库、已登记文档及会话正文；真实步骤间传值，定义不足、引用越界或条件不一致会阻断。
- 解释面板：SQL、原始结果、要素改写、选表与剪枝理由、跨源步骤及 trace。
- 立体数据可视化：使用真实返回表或本地 CSV／TSV／JSON，提供环形、柱状、序列三种视图，保留原始精度、NULL 与 0 的区别。默认没有虚构统计；本地分析不会自动调用模型。详见 [白色立体 UI 接入验收](frontend-workbench/docs/white-ui/接入验收.md)。

文档检索在原 BGE-M3 + BM25 + RRF 上增加本地候选重排和同来源邻片补全；每片保留独立原文位置与引用。它是可解释的词项覆盖重排，不是额外的神经重排模型。已验证索引、范围内BM25和查询向量使用有界缓存，源文件或索引变化会失效并重新校验。

本机及示例配置使用 `RAG_RETRIEVAL_STRATEGY=hybrid_rerank`、`RAG_CACHE_ENABLED=true`。需要原排序时设为 `hybrid`；只做向量对照时设为 `dense`。修改配置后重启API。保持单文档问答和现有两类跨源范围。

`scripts/ingest_docs.py`已支持增量入库：内容、解析参数与模型不变时复用片段及向量；旧索引第一次显式重建后才有新的增量指纹。正常问答不会自动重建索引。

检索对照入口为 `eval/rag_retrieval_benchmark.py`，默认只读当前已登记的开发集。结果中的页命中、参考片段覆盖和MRR是检索诊断，不能当作答案忠实度。实际改动与前后测试见 [RAG检索提升验收](eval/artifacts/rag-improvement-20261016/RAG检索提升验收.txt)。

## 首次部署

### 会话正文与参考时间

在工作台选择“自动综合”，展开“本会话正文”保存完整约定，再继续提问。正文只对当前会话有效，不会自动升级为公司政策。切换来源或新建会话会清除界面绑定；服务端正文24小时后失效，可通过删除接口清除。

API方式：先向 `POST /api/context` 提交 `session_id`、`text`，可选 `reference_datetime`（ISO8601且带偏移）、`timezone`（IANA时区）；响应给出 `context_id`、版本、原文SHA256和字符数。之后 `POST /api/chat` 使用同一 `session_id`，带上 `context_id`、原始问题和来源范围。无需把长正文拼进每轮 `message`，也不需要截断或摘要替代。

①使用真实候选及字段角色做链接，③区分显式条件、已确认历史和授权默认，④保留真实外键关系、显式表列并在必要时从合法草稿补回遗漏字段。`SCHEMA_RECALL_ENHANCED` 的软词项通道在当前开发集上没有收益，默认关闭；这与保留显式字段保护是两件事。

实验开关只用于独立对照：`NLU_ENABLED=false`关闭值链接；`AGENT_GROUNDING_ENABLED=false`关闭新增语义来源与完整性增强，但仍保留正文与时钟输入、既有澄清及SQL安全；`AW_SCHEMA_MODE=full`提供全量目录。正式默认保留增强与子图模式，不能将关闭安全保护当作消融。

需要 Python **3.12** 与 Docker Desktop。首次配置必须在新机器或独立目录操作，不要在已经恢复的业务库上重复导入。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

在本机编辑 `.env`，填入自己的模型密钥及数据库只读连接。实际 model 配置使用 `deepseek-flash`。不要上传 `.env`、口令、虚拟环境或 `.runtime/`。

GitHub 保存源码、前端构建、目录与必要评测资料；本机的模型权重、向量索引、原始文档和数据库运行卷不会随 Git 自动迁移。新机器需要使用完整项目交付资源，或根据 `data/docs/manifest.csv`、模型清单与保留的构建工具准备资源。具体见 [项目入口与换电脑运行说明](项目入口与换电脑运行说明.md)。

## 单独启动与构建

```powershell
# 终端一：已有业务库与本机配置就绪后启动 API
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
# 终端二：启动新工作台
.\.venv\Scripts\python.exe frontend-workbench/run_ui.py --port 8501 --api-url http://127.0.0.1:8000
```

前端源码修改后，在 `frontend-workbench` 中执行 `pnpm install --frozen-lockfile`、`pnpm run build`。安装依赖仅用于构建；`node_modules` 不提交。

## 主要目录

| 目录 | 内容 |
|---|---|
| `frontend-workbench/` | 默认 UI 源码、预编译资源、许可证与接口/浏览器测试 |
| `api/`、`qa_agent/` | FastAPI、共享协议、SQL、RAG、澄清与跨源实现 |
| `data/` | 目录、别名、业务口径和资料清单；模型、索引与原始资料按本地资源规则准备 |
| `eval/` | 当前题库、判分、运行结果与历史证据 |
| `tests/` | 后端与兼容 UI 回归 |
| `scripts/` | 启动、数据库准备、索引构建与必要评测工具 |
| `notes/submission-20261016/` | 本轮清理范围、检查与交接说明 |

## 题库与当前状态

`eval/datasets/current.json` 指向 `manual-applied-20261013-v3` 开发题库；审核落地与两道新 gold 已保存。历史开发成绩、修复补测和后续失败分开保留，见 [按截图逐条验收报告](eval/reports/screenshot-acceptance/按截图逐条验收报告.md)。

本轮工作是界面整合和提交目录整理，不代表 D5 已冻结、保留集正式评测已完成，也不覆盖已有业务失败。没有用前端模拟测试替代真实模型准确率。

## 清理与恢复

已完成的造数器、一次性修改/审核/打包脚本及旧审核 HTML 移到仓库外的本地备份，已生成数据与运行依赖保留。具体见 [清理范围与版本说明](notes/submission-20261016/清理范围与版本说明.md) 和 [清理清单](notes/submission-20261016/cleanup-manifest.json)。

不要因为文件名含 `review`、`build` 或 `experiments` 就继续批量删除：部分原始来源、测试辅助函数和专项评测器仍有真实依赖。
