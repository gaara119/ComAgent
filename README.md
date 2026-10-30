# ComAgent

**用自然语言查询数据库和文档，并给出可核查的结果与来源。**

用户可以连接 PostgreSQL、上传文档或补充文字，再用日常语言提问。系统选择 SQL 查询、文档检索或跨源处理，返回答案、查询结果、原文引用和执行记录。

## 功能

- **数据库问数**：把问题转换为 SQL，检查表、字段和查询约束后只读执行。支持已有示例库，也可在界面登记新的 PostgreSQL 连接并读取目录。
- **文档问答**：上传 PDF、Word、TXT、Markdown，或粘贴文字，在本地解析和建立索引，回答附带原文引用。
- **多轮问答**：保存已确认条件，用户修改年份、对象或指标时更新相关条件；关键歧义通过澄清卡片确认。
- **跨源查询**：用数据库结果定位文档，或先检索指标定义，再据此生成和检查 SQL。
- **结果核查**：查看 SQL、原始结果、文档出处、采用的假设和工具执行步骤。

## 设计思路

模型负责理解问题和提出结构化计划，程序负责状态管理、来源约束、SQL 校验和实际执行。

```text
用户问题 + 会话条件 + 允许使用的数据源
                    ↓
          意图理解、要素链接、必要澄清
                    ↓
              选择处理路径
          ┌─────────┼──────────┐
       SQL 查询   文档检索    跨源处理
          └─────────┼──────────┘
                    ↓
         答案 + 查询结果 + 引用 + 执行记录
```

数据库侧使用 SQLGlot 检查 SQL，并用只读账号、只读事务、超时和行数限制约束执行。文档侧使用 BGE-M3 向量检索与 BM25 关键词检索，通过 RRF 合并候选，再做本地重排和相邻片段补全。

## 技术栈

| 部分 | 技术 |
|---|---|
| 页面 | React、Ant Design、esbuild，随项目提供预编译页面 |
| 接口与协议 | Python 3.12、FastAPI、Pydantic |
| 模型调用 | OpenAI 兼容 API，当前模型字符串为 deepseek-flash |
| 数据库 | PostgreSQL、psycopg、SQLGlot |
| 文档处理 | PyMuPDF、pdfplumber、python-docx；扫描件可使用本地 RapidOCR |
| 检索 | BGE-M3、ONNX Runtime INT8、BM25、RRF |
| 表定位与实体链接 | NetworkX 外键图、Steiner 近似补全、RapidFuzz、拼音及向量候选 |

## 本地启动

需要 Python **3.12**。使用本地示例数据库时，还需启动 Docker Desktop；已有远程 PostgreSQL 也可以直接配置使用。

在项目目录打开 PowerShell：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

编辑本地 `.env`，填入 `LLM_API_KEY` 和数据库只读连接。示例配置使用新的本地知识库路径，第一次上传会创建清单和索引；使用已有知识库时，再将 `RAG_MANIFEST_PATH`、`RAG_INDEX_PATH` 指向自己的资源。需要语义检索时，准备 `BGE_MODEL_PATH` 对应的本地模型。不要提交真实密钥和数据库口令。

双击 **启动项目.cmd**。默认入口为 [问答工作台](http://127.0.0.1:8501/)，接口说明为 [API 文档](http://127.0.0.1:8000/docs)。启动器复用已有数据库，不自动重建或重新导入业务库。

也可分别启动：

```powershell
# 终端一
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
# 终端二
.\.venv\Scripts\python.exe frontend-workbench/run_ui.py --port 8501 --api-url http://127.0.0.1:8000
```

**Git 仓库不包含大型模型权重、原始文档、向量索引和数据库卷。** 使用完整资源目录，或通过 `scripts/download_embeddings.py`、`scripts/ingest_docs.py` 等工具准备资源。前端已构建，日常运行不需要 Node.js；修改前端后才需在 `frontend-workbench` 中执行 `pnpm install --frozen-lockfile` 和 `pnpm run build`。

## 上传文档与文字

在工作台点击“上传文档”或“添加文字”：

- 文件支持 PDF、DOCX、TXT、Markdown，单个不超过 **8 MB**；新上传 PDF 不超过 **100 页**，TXT/Markdown 使用 UTF-8。
- **知识库（长期保存）**：资料进入本地知识库，建好索引后可选择该文档提问。仅新增资料进行解析和编码，复用已验证的旧片段与向量。
- **仅本次会话**：文字只绑定当前会话，不建立知识库索引；正文最多 **120000 字符**，服务端默认 24 小时过期。

后台通过任务编号报告进度。等待成功提示后再提问；失败会保留错误记录，原知识库不被替换。

## 主要目录

```text
api/                   HTTP 接口
qa_agent/
  pipeline.py          问答调度
  nlu/                 要素识别、候选链接与有据改写
  clarify/             语义校验、澄清与多轮状态
  sql/                 表定位、SQL 生成、校验与执行
  rag/                 文档入库、检索、回答与引用检查
  fusion/              跨源计划与结果传递
frontend-workbench/    页面源码与预编译资源
data/                  数据目录、业务规则和本地知识资源
scripts/               启动、资源准备和检查工具
tests/                 自动化测试
```

上传链路检查命令如下。它复制当前知识库建立隔离测试索引，使用真实本地向量模型及 HTTP 接口，不调用收费模型 API，不修改当前正式文档清单。

```powershell
.\.venv\Scripts\python.exe scripts/check_document_uploads.py
```

## 当前边界

当前面向本机单实例演示，上传和数据库连接管理仅允许本机访问。尚未实现面向公网的用户认证、多租户权限和分布式任务队列。新数据库可接入目录和只读查询，但业务指标、别名和歧义规则仍需结合实际数据配置。SQL 与引用检查能够降低错误风险，不能替代业务人员核对答案。
