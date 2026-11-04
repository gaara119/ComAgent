# 评测驱动的 RAG 智能问答系统

**用自然语言查询 PostgreSQL 和文档，并给出可核查的结果、SQL 与原文引用。**

项目将数据库问数、文档检索和多轮交互接到同一工作台，并提供可复现的评测入口，按结果、检索、证据、Agent过程、稳定性、成本效率及安全七个维度记录表现。

[下载版本](https://github.com/gaara119/ComAgent/releases) · [容器包](https://github.com/gaara119/ComAgent/pkgs/container/comagent) · [构建与发布状态](https://github.com/gaara119/ComAgent/actions) · [原240题评测报告](benchmarks/agent240/results/240-seven-dimensions-v1/report.md)

## 目录

- [1. 数据来源与环境要求](#1-数据来源与环境要求)
  - [1.1 数据来源与版本](#11-数据来源与版本)
  - [1.2 环境与安装方式](#12-环境与安装方式)
- [2. 使用指南](#2-使用指南)
  - [2.1 可以做什么](#21-可以做什么)
  - [2.2 Docker源码启动](#22-docker源码启动)
  - [2.3 Docker数据保存与更新](#23-docker数据保存与更新)
  - [2.4 连接PostgreSQL](#24-连接postgresql)
  - [2.5 上传文件与添加文字](#25-上传文件与添加文字)
  - [2.6 启用本地BGE混合检索](#26-启用本地bge混合检索)
  - [2.7 Windows原生运行](#27-windows原生运行)
  - [2.8 常见问题](#28-常见问题)
  - [2.9 系统设计与目录](#29-系统设计与目录)
- [3. RAG评测与优化](#3-rag评测与优化)
  - [3.1 评测范围与数据隔离](#31-评测范围与数据隔离)
  - [3.2 七个维度分别检查](#32-七个维度分别检查)
  - [3.3 指标定义与分母](#33-指标定义与分母)
  - [3.4 真实历史结果](#34-真实历史结果)
  - [3.5 运行评测](#35-运行评测)
  - [3.6 产物与持续回归](#36-产物与持续回归)
  - [3.7 当前缺口与优化顺序](#37-当前缺口与优化顺序)

## 1. 数据来源与环境要求

### 1.1 数据来源与版本

**系统使用公开示例数据库与登记文档；当前评测采用原有40题和200题，共240个综合开发题条目。后补32道合成题、配套虚构文档和旧结果已从当前仓库删除，不再作为评测依据。**

| 资料 | 公开来源与项目版本 | 用途与仓库内容 |
|---|---|---|
| Chinook示例数据库 | [Chinook](https://github.com/lerocha/chinook-database)，`v1.4.5` PostgreSQL SQL | 音乐商店客户、发票、曲目问数；含初始化SQL、MIT许可及[来源哈希](data/db/source_manifest.json)，需连接实际数据库 |
| AdventureWorks示例数据库 | 微软AdventureWorks 2014 OLTP；[PostgreSQL迁移版](https://github.com/lorint/AdventureWorks-for-Postgres)修订`b474991f0df1c4bf55ca4735eb0254ca0709eed2` | 多表问数、外键图与表定位；含目录、准备脚本及[来源清单](data/db/aw_source_manifest.json)，原始数据另行准备 |
| OHR-Bench文档与QA | [官方项目](https://github.com/opendatalab/OHR-Bench) / [公开数据集](https://huggingface.co/datasets/opendatalab/OHR-Bench)；历史QA修订`1f421eb428f9f5b8ac0bc8064d6ad1f13fab7af7`，PDF修订`7f833e3eda9a571a9ea545a8f6d476fa1685033d` | 历史PDF解析、检索与问答开发；保留[登记表](data/docs/manifest.csv)及[来源清单](data/docs/source_manifest.json)，原PDF与完整QA不随源码提供；240题成绩不是OHR官方成绩 |
| 艺术家介绍与业务口径 | 登记表中的Wikipedia来源、改编记录及项目自编指标手册 | 实体介绍、SQL→文档和文档→SQL演示；项目业务定义与OHR官方答案分开管理 |
| 原240道综合开发题 | 原40题与原200题的用户提供题库，保留原题、Gold、批次和会话关系 | 204道SQL、24道跨源、6道RAG、6道会话正文题；[题目与参考](benchmarks/agent240/data/dataset.json)、[480条历史预测](benchmarks/agent240/data/records.jsonl)、[版本与哈希清单](benchmarks/agent240/data/manifest.json) |
| 向量模型 | [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)，实际使用[Xenova ONNX转换](https://huggingface.co/Xenova/bge-m3/tree/4de13258303883538bd53b696b452bf8099f0858)固定修订，CPU/INT8、1024维 | Dense召回，与BM25通过RRF融合；含[模型版本与哈希](data/model_manifest/bge-m3.json)及下载脚本，权重不上传GitHub |

OHR的Hugging Face卡片标注CC-BY-4.0，官方仓库对收集的PDF另有研究用途、非商业使用声明；本项目保留来源记录，未把第三方原文重新授权。用户上传资料不自动发布为公开评测语料。

240是协议条目数，两批有35道相同题面，并含连续对话，不能视为240道相互独立的未见题或240道RAG题。参考标签的人工审核状态保持原样。当前报告重新计算历史记录，不代表当前版本新跑一轮240题。首次克隆可从空知识库上传自己的文档；登记路径不代表原文、模型或数据库已经就绪。

### 1.2 环境与安装方式

| 方式 | 需要安装 | 默认工作台 | 适合谁 |
|---|---|---|---|
| Docker 源码构建，推荐 | Docker Desktop / Docker Engine、Compose v2；Git 可选 | http://127.0.0.1:18501/ | 想直接运行，不想手动安装 Python 依赖 |
| 已发布镜像 | Docker；拉取私有包时还需相应权限 | http://127.0.0.1:18501/ | 已能访问 GitHub Packages 的用户 |
| Windows 原生源码 | Python 3.12；需要本地数据库时再准备 Docker | http://127.0.0.1:8501/ | 想改代码或调试 |

前端已经预编译，正常使用无需 Node.js。首次构建需要联网下载基础镜像与 Python 依赖，建议为 Docker 分配至少 4 GB 内存并留出约 5 GB 磁盘；加载本地向量模型时需要更多资源。发布容器目标为 Linux/amd64，请在 Docker Desktop 中使用 **Linux containers**。

项目不附带模型 API 密钥、BGE 权重或可直接连接的数据库实例。Chinook初始化SQL随源码提供，AdventureWorks原始数据和历史文档另行准备。默认可以从空知识库上传自己的文件；未提供本地BGE时使用BM25关键词检索，配置本地BGE并重建索引后才是混合检索。

| 组件 | 实际要求与配置位置 |
|---|---|
| Python后端与离线评测 | Python 3.12；运行依赖及精确版本见 [requirements-runtime.txt](requirements-runtime.txt)，完整开发依赖见 [requirements.txt](requirements.txt) |
| 核心依赖 | FastAPI/Pydantic、psycopg/SQLGlot、PyMuPDF/python-docx、BM25、ONNX Runtime；版本以依赖文件为准 |
| Docker演示 | Docker Desktop或Docker Engine＋Compose v2；Linux容器，发布镜像为linux/amd64 |
| 前端 | 随仓库提供预编译资源，日常运行不需Node；改前端时再安装Node/pnpm |
| 本地检索 | 默认可用BM25；真实Dense/Hybrid评测需先下载并校验BGE权重，当前实现使用CPU/INT8，无需GPU |
| 生成模型 | 本地配置 `LLM_BASE_URL`、`LLM_MODEL=deepseek-flash`、`LLM_API_KEY`；密钥只放本地配置，不上传 |
| 最短评测环境 | Python＋运行依赖即可跑BM25与摘录链路，无需Docker、数据库、GPU或收费API；执行pytest时另装测试依赖 |

## 2. 使用指南

### 2.1 可以做什么

| 功能 | 使用方式 | 得到什么 |
|---|---|---|
| 数据库问数 | 连接 PostgreSQL，用中文提问 | 经过校验和只读执行的 SQL、真实结果表 |
| 文档问答 | 上传 PDF、Word、TXT、Markdown，或粘贴文字 | 基于选定资料的回答、原文引用及位置 |
| 多轮问答 | 继续修改对象、期间或指标 | 保留有效条件；关键歧义通过卡片确认 |
| 跨源查询 | 一个问题同时需要数据库与文档 | 前一步真实结果参与后一步检索或计算 |
| 结果核查 | 展开依据与执行步骤 | SQL、数据、引用、假设和实际工具记录 |
| 本地表格分析 | 在数据分析页导入 CSV/JSON 等 | 浏览器内的统计、图表和导出 |
| 独立 RAG 评测 | 用版本化文档和证据标签运行检索、固定证据与端到端评测 | 同题对照、错误归因、质量与时延报告、可复现原始记录 |

示例问题：

- 数据库：“各国家客户的发票总金额是多少？”
- 文档：“这份服务说明规定的响应时间是多少？”
- 多轮：“换成加拿大，其他条件不变。”
- 跨源：“销售额最高的艺术家是谁？再介绍他的音乐风格。”

这些是使用示例，不是预置答案。SQL 需要可访问的数据库；文档问答需要已经入库的资料；跨源还需要实体和文档之间的登记关系或可核验的指标定义。新增数据库不自动获得全部业务规则。

### 2.2 Docker源码启动

以下命令在 Windows PowerShell 中执行。macOS/Linux 可使用同样的 Docker 命令，将 `Copy-Item` 换成 `cp`。

#### 第一步：取得源码

有 Git：

```powershell
git clone https://github.com/gaara119/ComAgent.git
cd ComAgent
```

没有 Git：从上方 Releases 下载 `ComAgent-版本号-source.zip`，完整解压，进入含 `Dockerfile`、`compose.app.yml` 和 `README.md` 的目录，在地址栏输入 `powershell` 打开终端。不要只单独取出启动脚本。

#### 第二步：确认 Docker 可用

尚未安装时，按 [Docker Desktop 官方 Windows 安装说明](https://docs.docker.com/desktop/setup/install/windows-install/)下载并安装，按安装器提示启用 WSL 2、完成必要的系统重启。项目运行的是 Linux 容器，不要切换为 Windows containers。Docker 方式不需要另装 Python、Node 或本机 PostgreSQL。

打开 Docker Desktop，等待引擎运行，再在源码目录的 PowerShell 中执行：

```powershell
docker version
docker compose version
```

`docker version` 应同时出现 Client 和 Server。只有 Client、提示找不到 `dockerDesktopLinuxEngine`，说明引擎尚未启动，先处理 Docker Desktop，不能继续当成项目故障。

#### 第三步：创建配置文件

```powershell
Copy-Item deployment/docker.env.example .env.docker
notepad .env.docker
```

已有 `.env.docker` 时直接编辑，不要重新复制覆盖自己的配置。至少填入：

```dotenv
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-flash
LLM_API_KEY=在本地填写自己的API密钥
COMAGENT_UI_PORT=18501
CHINOOK_DB_URL=
AW_DB_URL=
```

保存并关闭记事本。不要把密钥发到聊天、截图或提交 Git。只做文档问答时，两个数据库连接留空即可。未配置模型密钥时可以检查页面、上传和资源状态，正常界面中的生成式问答需配置完成后使用。

#### 第四步：构建并启动

```powershell
docker compose --env-file .env.docker -f compose.app.yml up -d --build
docker compose --env-file .env.docker -f compose.app.yml ps
```

首次需要下载依赖，等待构建完成和服务健康。该配置只启动 ComAgent 应用，不创建或重建数据库。

#### 第五步：打开入口

- 工作台：http://127.0.0.1:18501/
- API 文档：http://127.0.0.1:18501/docs
- 健康状态：http://127.0.0.1:18501/health

容器内部 API 为 8000，工作台为 8501；对宿主机仅映射本机回环地址的 18501，不需要再额外开放 8000。

#### 已发布镜像的启动方式

镜像名为 `ghcr.io/gaara119/comagent:0.5.0`。在已具备访问权限时：

```powershell
docker pull ghcr.io/gaara119/comagent:0.5.0
docker compose --env-file .env.docker -f compose.app.yml up -d --no-build
```

GitHub Packages 的首次发布可能默认私有，是否可匿名拉取以包页面实际可见性为准。遇到 `denied` 时，可以先使用上面的 **源码构建**，不必为运行项目把 GitHub 凭据写进 `.env.docker`。仓库所有者可在 Package settings 中将包设为 Public；私有包拉取需使用具备 `read:packages` 的凭据。

### 2.3 Docker数据保存与更新

`compose.app.yml` 使用两个命名卷：

| 卷 | 容器目录 | 内容 |
|---|---|---|
| `app-data` | `/app/data` | 上传文件、清单、索引、模型与目录定义 |
| `app-runtime` | `/app/.runtime` | 会话、任务、连接登记及其加密密钥 |

Linux 容器中的连接信息使用认证加密，自动生成的密钥保存在权限受限的 runtime 卷中。备份或迁移时需要同时保存 data 和 runtime，不能只复制密文登记文件。若自行设置了 `COMAGENT_CREDENTIAL_KEY`，恢复时还必须提供相同的外部密钥配置。

常用操作：

```powershell
# 查看日志
docker compose --env-file .env.docker -f compose.app.yml logs --tail 100 app
# 停止，保留命名卷
docker compose --env-file .env.docker -f compose.app.yml stop
# 重新启动
docker compose --env-file .env.docker -f compose.app.yml up -d
# 修改 .env.docker 后重建容器，使配置生效
docker compose --env-file .env.docker -f compose.app.yml up -d --force-recreate
# 修改源码后重新构建
docker compose --env-file .env.docker -f compose.app.yml up -d --build
```

普通停止、重建容器会保留命名卷。**不要用 `down -v` 作为日常重启命令**，它会删除命名卷中的上传内容、索引和连接密钥。

端口冲突时，在 `.env.docker` 中修改 `COMAGENT_UI_PORT`，例如 `18502`，然后执行 `up -d --force-recreate`，访问对应端口。配置会同时更新映射和同源检查，不要只改 Docker 映射的一端。

### 2.4 连接PostgreSQL

项目连接已有 PostgreSQL，以只读方式发现目录和查询。数据库服务不是大模型，填了模型 key 不会自动生成数据库。

#### 方式 A：在界面添加新数据库

进入问答工作台，点击“添加数据库”，填写名称、主机、端口、库名、只读账号、密码和允许访问的 schema。保存成功后选择新来源，再提问。Linux 容器已经支持加密保存连接；原生 Windows 默认使用当前用户 DPAPI。

连接地址按运行位置区分：

| PostgreSQL 在哪里 | 应用运行位置 | 数据库主机填写 |
|---|---|---|
| Windows/macOS 宿主机 | Docker 容器 | `host.docker.internal` |
| 同一个 Docker network 的数据库容器 | Docker 容器 | 该容器的服务名，端口通常 5432 |
| 其他服务器 | 原生或 Docker | 服务器可达 IP/域名及实际端口 |
| 本机 | Windows 原生 | `127.0.0.1` 和实际映射端口 |

容器内的 `127.0.0.1` 指容器自己，不是 Windows 宿主机。原生 Linux 的 host 地址请使用实际可达地址或自行配置 host-gateway，不假定所有平台都内置 `host.docker.internal`。

账号需要目标数据库的连接权限、业务 schema 的使用权限，以及查询表的 SELECT 权限。不要为了问数使用管理员账号。网络、防火墙与 PostgreSQL 的访问控制也必须允许连接。

#### 方式 B：配置已有示例库连接

在 `.env.docker` 或原生 `.env` 中填写 `CHINOOK_DB_URL` / `AW_DB_URL`，格式例如：

```dotenv
CHINOOK_DB_URL=postgresql://只读用户名:经URL编码的密码@可达主机:端口/chinook
```

URL 中的特殊字符需要编码；如果不熟悉，优先使用界面分字段填写。这里的路径、目录定义和业务规则针对对应示例库，不能只改库名就假定任意业务库同样适用。

本项目包含 Chinook 的初始化 SQL 和准备脚本。**仅在明确的新环境**、已配置本地 `.env` 管理员与只读口令后，可运行原生 `scripts/bootstrap_db.py` 初始化独立示例数据库；已有业务库不要重复导入。AdventureWorks 和大型索引需另外准备资源，不属于首次上传文档的前置条件。

### 2.5 上传文件与添加文字

#### 长期知识库

1. 点击“上传文档”，选择文件并填写标题；或点击“添加文字”，选择“知识库（长期保存）”。
2. 等待后台解析、切片和索引状态完成。请求已接收不等于资料已可查询。
3. 成功后页面切换到该资料，输入问题。
4. 在答案旁查看引用原文；PDF 可核对物理页位置。

支持 PDF、DOCX、TXT、Markdown。单文件最多 8 MB，新上传 PDF 最多 100 页；TXT/Markdown 使用 UTF-8。相同内容不重复登记。加密文件、没有可提取文字且 OCR 不可用的扫描件会明确失败。

#### 仅本次会话的文字

点击“添加文字”，选择“仅本次会话”。它不建立长期知识库索引，最多 120000 字符，默认 24 小时后不再接受该正文绑定。切换来源或新建会话后重新保存；它不会自动升级成系统政策。

#### 选择范围

- 自动综合问答：按问题选择可用工具或受约束的跨源流程。
- 数据库问数：选择目标数据库。
- 指定文档问答：选择一份资料，或允许查询登记文档范围。

扩大文档范围只扩大可检索来源，不应自动把介绍意图改成 SQL。遇到关键歧义按卡片确认；确认实体之后继续原问题。

### 2.6 启用本地BGE混合检索

默认镜像没有附带数百 MB 的 BGE 权重，首次使用可先验证关键词检索。需要混合检索时，在运行容器内准备模型：

```powershell
docker compose --env-file .env.docker -f compose.app.yml exec app python scripts/download_embeddings.py
```

这会下载并验证固定版本的公开模型，需要网络、额外磁盘和内存。若下载源不可达，应先解决网络或按来源清单提供完整资源，不要关闭哈希校验。

如果已经上传过文档，**在没有其他上传/问答任务时**重建当前索引，再重启服务：

```powershell
docker compose --env-file .env.docker -f compose.app.yml exec app python scripts/ingest_docs.py --audit-output .runtime/rag-ingest.json
docker compose --env-file .env.docker -f compose.app.yml restart app
```

没有任何文档时先上传一份再执行重建。新增模型不会让旧 BM25 索引自动变成向量索引。镜像默认未安装可用的 OCR 模型；扫描件支持还需要相应解析资源，不能仅凭文件后缀保证识别成功。

### 2.7 Windows原生运行

适合开发调试，默认工作台 8501、API 8000。无需为了普通页面安装 Node。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
Copy-Item .env.example .env
notepad .env
```

已有 `.env` 时不要覆盖。填写自己的模型 key；只用文档时将 `CHINOOK_DB_URL`、`DB_URL`、`AW_DB_URL` 清空。保留新的本地清单/索引路径即可从第一次上传开始。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_project.ps1 -SkipDatabaseStart
```

访问 http://127.0.0.1:8501/。本机已有项目数据库时也可双击 `启动项目.cmd`，启动器复用属于当前工作区的容器，不删除原卷或重复导入。

需要独立启动或调试时，分别开两个终端：

```powershell
# 终端一
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
# 终端二
.\.venv\Scripts\python.exe frontend-workbench/run_ui.py --port 8501 --api-url http://127.0.0.1:8000
```

修改原生 `.env` 后重启 API。源码里的完整 `requirements.txt` 还包含开发、历史兼容 UI 和测试工具；仅运行当前工作台优先使用较小的 `requirements-runtime.txt`。修改前端源码时，再安装 Node/pnpm，并在 `frontend-workbench` 中执行 `pnpm install --frozen-lockfile`、`pnpm run build`。

### 2.8 常见问题

| 现象 | 先检查什么 |
|---|---|
| Docker 找不到 Linux engine | Docker Desktop 是否真正启动、是否为 Linux 容器模式 |
| `denied` 拉不到 GHCR 镜像 | 包是否 Public、当前账号是否有包权限；也可直接源码构建 |
| 页面打不开 | Compose 是否启动成功、日志是否报错、端口是否一致 |
| 修改 key 后仍提示未配置 | Docker 用 force-recreate；原生重启 API；检查编辑的是对应配置文件 |
| 文档能上传但不能正常生成回答 | API key、模型账户、网络和模型字符串；上传本身不调用生成模型 |
| 数据库连接失败 | 主机地址是从容器还是宿主机观察，端口、只读账号、防火墙和 schema 权限 |
| 新增数据库提示无法解密 | runtime 卷和密钥是否一起保留，是否错误更换了 COMAGENT_CREDENTIAL_KEY |
| 上传长期停在处理中 | 查看导入任务和应用日志；不要连续重复上传 |
| 某些原文找不到 | 资料是否 ready、范围是否允许、是否已经建立对应索引 |
| 扫描 PDF 无文字 | 当前 OCR 资源是否可用；可先用含文字层的 PDF/Word 验证 |
| 表定位/别名增强缺资源 | 示例库值索引、目录索引与模型是否准备，不能把连接成功当成业务配置完成 |

不要向日志、Issue 或截图附上完整 `.env`、口令、真实用户资料或含敏感行的查询结果。

### 2.9 系统设计与目录

模型负责理解问题和提出结构化候选；程序负责有效条件、来源范围、SQL 校验、真实执行和证据传递。

```text
用户问题 + 会话条件 + 允许来源
        ↓
理解、要素链接、必要澄清
        ↓
SQL 查询 / 文档检索 / 有界跨源计划
        ↓
答案 + 结果表 + SQL + 原文引用 + 执行步骤
```

主要技术：Python 3.12、FastAPI、Pydantic、PostgreSQL/psycopg、SQLGlot、BGE-M3/ONNX、BM25/RRF、NetworkX、React/Ant Design。

```text
api/                   HTTP 接口
qa_agent/pipeline.py    调度
qa_agent/nlu/           对象识别、候选链接与有据改写
qa_agent/clarify/       语义校验、多轮状态与澄清
qa_agent/sql/           表定位、SQL 生成、校验和只读执行
qa_agent/rag/           入库、检索、回答和引用检查
qa_agent/fusion/        跨源计划与结果传递
frontend-workbench/    页面源码、预编译资源与本机代理
deployment/            容器启动和配置模板
scripts/               资源准备、启动和检查工具
tests/                 自动化测试
data/                  必需定义和本地资源位置
.github/workflows/     容器检查、Packages 与 Release 发布
```

当前面向本机、单实例使用，未提供面向公网的完整账号认证与多租户权限。SQL 和引用检查降低错误风险，但不能证明任意业务答案完全正确。

发布工作流会先执行容器内回归和真实工具链检查，再推送镜像、生成 Release 源码与校验和。具体结果以 Actions 为准，程序测试通过数不能替代真实模型问答准确率。学习指南、历史评测、真实密钥、上传内容与模型权重不进入源码发布包。

## 3. RAG评测与优化

### 3.1 评测范围与数据隔离

评测使用原有两批综合开发题：原200题按历史`BASE/FULL`比较，原40题按历史`BASE/C1`比较，共保留480条真实预测。`FULL`与`C1`的功能配置不同，各自的源码、开关、模型与证据来源记录在[manifest](benchmarks/agent240/data/manifest.json)，不合并成一个当前版本准确率，也不当作仅改变一个开关的同源消融。

| 批次 | SQL | 跨源 | RAG | 会话正文 | 题数 | 历史预测 |
|---|---:|---:|---:|---:|---:|---:|
| 原200题 | 170 | 20 | 5 | 5 | 200 | 400 |
| 原40题 | 34 | 4 | 1 | 1 | 40 | 80 |
| 合计 | 204 | 24 | 6 | 6 | 240 | 480 |

原题、Gold与人工审核记录不随重计分改动。预测中的SQL结果按原参考比较；答案业务含义使用与实际响应哈希绑定的已有AI审核。程序通过、AI建议通过和人工批准分别记录。保留集不载入，不生成新题。

### 3.2 七个维度分别检查

| 维度 | 已有证据与本次检查 | 解释边界 |
|---|---|---|
| 结果 | 业务Accuracy、SQL结果EM/行集合F1、文本EM/F1、外部任务成功 | 严格数值相等、业务含义正确、任务完整交付是不同判定 |
| RAG检索召回 | 最终返回证据对参考文档的覆盖为40/68 | 仅为返回覆盖诊断；缺完整Top-K排名与完备相关性标签，Recall@K/MRR/nDCG为`not_verified` |
| 证据正确性 | 引用ID结构34/34；参考引句字面覆盖53/88；位置字段结构31/34 | ID合法与有位置字段均不证明引用支持答案；语义支持、PDF原页定位未核验 |
| Agent过程 | trace可追溯480/480；计划DAG结构48/48；所需工具类型出现383/406 | 检查实际工具及依赖结构；不把有trace、调用了工具当作计划语义正确 |
| 稳定性与异常 | 记录Error Rate、最终失败率、状态及真实恢复尝试 | 澄清不是技术故障；无故障恢复尝试时Failure Recovery无适用分母 |
| 成本效率 | HTTP响应P50/P90、755次历史物理调用、token及缓存用量 | 包括失败/重试和正文登记；本轮离线计算新增调用0次，不宣称当前并发或吞吐 |
| 安全 | 415次执行记录中413条SQL可进行只读AST检查，413/413满足；413/413存在执行前校验 | 静态检查不证明实际数据库权限或抗攻击能力；另有66项本地安全与工具权限回归，分母独立 |

原240记录的来源范围均为`unrestricted`，不能据此计算受限来源越权防御率。参考文档清单也不一定完备，例如一条多乐队题的参考来源未覆盖题面所有对象；它只用于诊断，不充当完整相关性Gold。

### 3.3 指标定义与分母

| 类别 | 指标 | 本项目的计算方式 |
|---|---|---|
| 准确性 | Accuracy | 与真实响应哈希绑定的已有AI业务审核；分别报告正确、错误、未知。未知不按通过处理，不从总题数中隐藏 |
| 准确性 | SQL结果Exact Match | 比较完整结果表，保留重复行；使用全表一致列映射，按参考要求检查行序；不舍入、缩放、删列或填NULL。不是SQL字符串相同 |
| 准确性 | SQL行集合F1 | 对完整结果行计算多重集精确率与召回率的调和平均；同一全局列映射，忽略行序，保留重复行 |
| 准确性 | 文本EM/F1 | 仅对6道RAG和6道会话正文题的完整文本Gold计算；中文按字、其他语言按词及符号匹配，是词面诊断，不替代语义正确性 |
| 效率 | Response Time | 同题初次与实际补充请求HTTP耗时之和；正文登记单列，不含用户思考时间；P50/P90采用`(n−1)×p`线性插值 |
| 效率 | Token Usage | 按真实物理调用去重，输入/输出及缓存命中/未命中分开；缺usage保留未知和已观测子和，不填0 |
| 鲁棒性 | Error Rate | 出现实际FAILED或HTTP错误的逻辑题比例；最终失败率另列，不等于`1−Accuracy` |
| 鲁棒性 | Failure Recovery | 同题确有失败且随后有真实恢复尝试才纳入分母；当前无适用分母，保持未核验 |

SQL适用题共228道，即204道纯SQL和24道跨源题；按批次分别使用190和38的分母。已观察但未交付成功结果表计为SQL结果不匹配；缺预测或无效参考保持未知。文本子任务答案不能拿来与整篇SQL/跨源回答直接计算EM。

### 3.4 真实历史结果

以下来自[逐题重计分报告](benchmarks/agent240/results/240-seven-dimensions-v1/report.md)和[summary.json](benchmarks/agent240/results/240-seven-dimensions-v1/summary.json)。这是历史开发记录的重新核验，未重新调用API或数据库。

| 批次/实际配置 | 业务审核：正确 / 错误 / 未核验 | SQL结果EM | SQL行集合F1 | 外部任务：成功 / 失败 / 未核验 |
|---|---|---:|---:|---|
| 原200 / BASE | 133 / 63 / 4 | 90/190，47.37% | 47.37% | 72 / 128 / 0 |
| 原200 / FULL | 123 / 73 / 4 | 86/190，45.26% | 45.53% | 88 / 111 / 1 |
| 原40 / BASE | 25 / 15 / 0，62.50% | 20/38，52.63% | 53.35% | 19 / 21 / 0，47.50% |
| 原40 / C1 | 26 / 14 / 0，65.00% | 21/38，55.26% | 55.98% | 20 / 20 / 0，50.00% |

原40题的历史C1相对BASE，业务正确率增加2.50个百分点，SQL结果EM增加2.63个百分点，外部任务成功率增加2.50个百分点。原200题的FULL则出现业务正确数减少10题、SQL结果EM下降2.11个百分点；虽然已确认外部任务成功数由72增至88，仍不能称为整体准确率提高。两批不同版本与调试历史限制了因果解释，正收益、负收益和未知项均保留。

| 批次/实际配置 | HTTP P50 / P90 | 历史物理调用 | 输入 / 输出token | Error Rate |
|---|---:|---:|---:|---:|
| 原200 / BASE | 6.76 / 14.25秒 | 251 | 2,282,141 / 43,352 | 8/200，4.00% |
| 原200 / FULL | 11.00 / 19.56秒 | 401 | 4,444,290 / 108,055 | 23/200，11.50% |
| 原40 / BASE | 3.95 / 6.70秒 | 51 | 423,138 / 8,381 | 0/40，0.00% |
| 原40 / C1 | 4.06 / 7.48秒 | 52 | 442,856 / 8,463 | 0/40，0.00% |

包含正文登记在内，历史物理调用合计755次，输入7,592,425 token、输出168,251 token；其中缓存命中输入3,451,008、未命中输入4,141,417。表中四行按问答归属列示，正文登记独立记录。当前没有可靠费用单价，不报告金额。

完整文本Gold的词面EM均为0：原200两配置各10道，原40两配置各2道。对应文本F1依次为31.36%、34.10%、76.37%、76.18%。自由改述与参考句可能表达同一事实，文本EM为0不能独立推出答案全错；也不能因F1较高认定整题正确。

### 3.5 运行评测

复用原生环境的Python 3.12与依赖；已创建`.venv`时直接复用。在项目根目录运行：

```powershell
$py = ".\.venv\Scripts\python.exe"
& $py -m benchmarks.agent240.evaluate --bundle benchmarks/agent240/data --output .runtime/agent240/my-run
```

这条命令读取已保存的240题与480条历史预测，校验题库、记录和审核绑定后重新计算七维指标。**无需Docker、数据库或模型密钥，不发送收费API请求，也不会重放问答。** 输出目录必须不存在；再次执行换新目录，防止覆盖旧证据。

若要评估当前源码的新预测，需要数据库、文档和模型就绪后另建在线回放，固定模型、正文、时钟、允许来源、评分规则与功能开关，并为A题独立会话、B题保留顺序和完整正文。当前Docker未就绪，当前版本在线240题未完成，不能将上述离线命令写成新一轮真实模型实跑。

通用RAG模块仍保留检索、固定证据与端到端工具接口；只有明确提供另一个已核验的来源型数据集时，才能显式传入`--dataset`。已删除的32题及其复制版本会被拒绝，见[入口说明](benchmarks/rag/README.md)。

### 3.6 产物与持续回归

| 产物 | 内容 |
|---|---|
| [data/dataset.json](benchmarks/agent240/data/dataset.json) | 原240条目、批次命名空间、来源类型、原Gold与参考结果，不覆盖原题 |
| [data/records.jsonl](benchmarks/agent240/data/records.jsonl) | 480条历史预测、实际请求/响应、SQL与引用、trace、物理调用和审核绑定 |
| [data/manifest.json](benchmarks/agent240/data/manifest.json) | 原文件与导出文件哈希、历史源码/配置、上下文登记用量及重复题面信息 |
| [report.md](benchmarks/agent240/results/240-seven-dimensions-v1/report.md) | 分批成绩、七维检查、指标定义与未核验事项 |
| [summary.json](benchmarks/agent240/results/240-seven-dimensions-v1/summary.json) | 机器可读汇总、各任务类型分项、状态分布及完整成本记录 |
| [scored.jsonl](benchmarks/agent240/results/240-seven-dimensions-v1/scored.jsonl) | 逐题结果、F1/EM、证据与过程结构诊断及未知原因 |

[RAG与评测CI](.github/workflows/rag-eval.yml)执行指标、来源、引用、权限边界等无API回归，并用同一240题证据包重算结果。它不调用模型、不制造新预测，也不是开放答案语义质量门禁；云端是否通过以Actions实际状态为准。[评测使用说明](benchmarks/agent240/README.md)给出命令、文件结构及指标边界。

### 3.7 当前缺口与优化顺序

1. **先完成当前版本在线回放。** 恢复数据库与文档环境，冻结来源与模型参数，保留真实失败、重试和费用，再与历史结果分别报告。
2. **补RAG排名与相关性证据。** 在现有RAG/跨源题上保存实际Top-K列表，人工补全必要证据及相关片段标签；完成前不报告Recall@K、MRR或nDCG。
3. **分开审核答案与引用。** 核对对象、期间、单位、结论及引句语义支持；ID合法、原句出现与正确引用分开计分，不自动批准Gold。
4. **按错误家族回归。** 先复现条件丢失、错误路由、引用缺漏等真实失败，验证受影响题及多轮前缀，再决定是否扩大运行；不为更好看分数修改题意或Gold。
5. **补鲁棒性与安全专项。** 另设可核验的超时、断连、空证据及越权对抗，记录降级和恢复。现有静态安全回归不等于攻击测试完成。

当前可据实介绍的工程成果是：**建立原240道综合开发题、480条历史预测的七维评测链路，以来源哈希、响应绑定审核、严格结果比较和分项成本统计定位问题；明确区分检索、引用、任务交付与安全检查，保留退步和未核验项。**
