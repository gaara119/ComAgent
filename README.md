# ComAgent

**用自然语言查询 PostgreSQL 和文档，并给出可核查的结果、SQL 与原文引用。**

项目将数据库问数、文档检索和多轮交互接到同一工作台，并提供独立的 RAG 评测入口，记录证据、回答、引用、耗时及同题对照结果。

[下载版本](https://github.com/gaara119/ComAgent/releases) · [容器包](https://github.com/gaara119/ComAgent/pkgs/container/comagent) · [构建与发布状态](https://github.com/gaara119/ComAgent/actions) · [RAG评测报告](benchmarks/rag/RAG评测与优化报告.md)

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
  - [3.1 第十二章如何对应本项目](#31-第十二章如何对应本项目)
  - [3.2 评测数据与隔离](#32-评测数据与隔离)
  - [3.3 评什么与怎么判](#33-评什么与怎么判)
  - [3.4 已有实测结果](#34-已有实测结果)
  - [3.5 可执行的评测命令](#35-可执行的评测命令)
  - [3.6 下一轮优化顺序](#36-下一轮优化顺序)
  - [3.7 回归验收与项目经历](#37-回归验收与项目经历)

## 1. 数据来源与环境要求

### 1.1 数据来源与版本

**项目使用过公开数据库与 OHR-Bench 文档；当前仓库公开展示的32题 RAG 对照成绩来自原创开发样本。两者的来源、审核状态和成绩分别记录。**

| 资料 | 公开来源与项目版本 | 项目用途 | 当前仓库提供什么 |
|---|---|---|---|
| Chinook 示例数据库 | [Chinook](https://github.com/lerocha/chinook-database)，`v1.4.5` PostgreSQL SQL | 音乐商店的客户、发票、曲目问数及跨源演示 | 初始化SQL、MIT许可、目录与[来源哈希](data/db/source_manifest.json)；运行时需已有数据库或在新环境初始化 |
| AdventureWorks 示例数据库 | 微软 AdventureWorks 2014 OLTP；[PostgreSQL迁移版](https://github.com/lorint/AdventureWorks-for-Postgres)固定修订 `b474991f0df1c4bf55ca4735eb0254ca0709eed2` | 多表问数、外键图及表定位 | 目录、准备脚本与[来源清单](data/db/aw_source_manifest.json)；原始数据另行准备 |
| OHR-Bench 文档与QA | [OpenDataLab官方项目](https://github.com/opendatalab/OHR-Bench) / [Hugging Face数据集](https://huggingface.co/datasets/opendatalab/OHR-Bench)；历史QA修订 `1f421eb428f9f5b8ac0bc8064d6ad1f13fab7af7`，PDF修订 `7f833e3eda9a571a9ea545a8f6d476fa1685033d` | 历史PDF解析、检索及问答开发；下一轮真实公开语料评测的优先来源 | [文档登记表](data/docs/manifest.csv)与[下载/哈希清单](data/docs/source_manifest.json)；原PDF和完整QA不随当前源码提供 |
| 艺术家介绍与业务口径 | 文档登记表中的Wikipedia来源/改编记录，以及项目自编指标手册 | 实体介绍、SQL→文档及文档→SQL演示 | 来源与派生标记；业务定义不是OHR官方答案，原件按登记资料另行准备 |
| 当前可直接复现的RAG开发样本 | 项目原创虚构语料 `rag-fixtures-v1`；10份MD/HTML，32题，35条必要证据 | 无API回归、检索消融与工具链诊断 | [原文](data/benchmark_fixtures/rag/)、[题目与证据](benchmarks/rag/fixtures/dataset.json)、[来源说明](benchmarks/rag/fixtures/provenance.json)；仅此批原创资料声明CC0-1.0，标签仍待人工审核 |
| 向量模型资源 | [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)，实际使用[Xenova ONNX转换](https://huggingface.co/Xenova/bge-m3/tree/4de13258303883538bd53b696b452bf8099f0858)固定修订，CPU/INT8、1024维 | Dense召回，与BM25通过RRF融合 | [模型版本与哈希](data/model_manifest/bge-m3.json)、下载脚本；权重不上传GitHub |

OHR的Hugging Face卡片标注CC-BY-4.0，官方仓库对收集的PDF另有研究用途、非商业使用声明；本项目保留两者的来源记录，未把第三方原文一并重新授权。用户上传文件属于用户自己的资料，不作为公开评测语料自动发布。OHR的原题、翻译题、项目改写题和原创样本应分别标记。

首次克隆可以从空知识库上传自己的文档，也可直接运行随源码提供的32题开发样本。登记表中的历史资料路径不代表文件已经包含在仓库；不要把“历史来源已登记”当作“新电脑的知识库已就绪”。原200道Agent综合题主要含SQL、多轮和路由任务，不属于200道独立RAG检索题。

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

### 3.1 第十二章如何对应本项目

参考 [Hello-Agents第十二章《智能体性能评估》](https://github.com/datawhalechina/hello-agents/blob/main/docs/chapter12/第十二章%20智能体性能评估.md) 的任务分层、结构化核验、相对比较和人工验证方法。下表是针对ComAgent的工程映射，并非该教程自带的RAG基准；没有运行BFCL、GAIA官方榜单，也不需要安装教程整套评测框架或改动项目依赖版本。

| 章节关注点 | 对本项目的落地方式 | 当前状态 |
|---|---|---|
| 12.1 评估对象与效率 | 检索、固定证据、完整RAG工具链分开测；同时保存质量、耗时、token和失败 | 已有三条运行入口、配置/源码/数据哈希和实际记录 |
| 12.2 BFCL的工具调用核验 | 借鉴结构化判定：核对允许文档范围、检索策略、证据ID、引用与实际输入；不靠输出文本看起来合理判通过 | 已有来源与引用契约回归；完整Agent路由/参数成功率仍需另外标注测量 |
| 12.3 GAIA的完整任务观 | 文档范围→实际检索→生成→引用逐步追踪；短答案检查对象/期间/单位，开放答案核对必要事实 | 已实跑检索和摘录链路；生成式任务正确率未核验 |
| 12.4 LLM Judge、Win Rate与人工验证 | 对答案正确性、忠实性、引用支持、要点完整性分别判分；同题盲化比较并记录胜/负/平，再人工校准 | 已有预测哈希绑定的审核导入；模型裁判、盲评Win Rate尚未运行 |

项目要形成的闭环是：**明确要验证的能力 → 冻结数据与配置 → 跑真实预测 → 分层判分 → 按错误家族修改 → 同题回归 → 记录收益和代价**。评测通过率、检索召回率和答案正确率分别报告。

### 3.2 评测数据与隔离

现有32题用于快速开发回归，全部是原创虚构资料上的 `dev`，不冒充OHR官方题或最终测试集。其29道可回答题、3道无答案题覆盖单事实、多证据、跨文档、数字期间、同名实体及续问；续问提供作者写好的有效检索问题，尚未验证Agent自动状态合并。

**下一轮建议建立OHR公开语料专项集，以下为实施方案，尚未完成和计分：**

1. 固定OHR的QA与PDF版本，优先选 `evidence_source=text`，覆盖财务、手册、法律、教材等不同领域。首版目标约100题、至少20份独立文档；实际数量以证据质量和可获得资料为准，不为凑题数放宽标准。
2. 保存原QA的 `ID`、`doc_name`、原题、参考答案及原始页码；核对 `evidence_page_no` 与真实PDF物理页的对应关系后再映射到本项目。不要因另一字段名为page_idx就默认所有页码都加1。对翻译/改写单独留来源对应关系。
3. 按文档/同源版本/问题家族分组，约70%开发、30%最终测试；先分组再分题，允许比例因整组隔离略有变化。旧D5保留集不参与。公开答案也不能用于针对最终测试调参。
4. 开发集增加同名实体、相近年份/单位和无答案样本。由正例删去必要来源构造无答案时，必须核查整个允许范围确实没有答案；不能只删一个chunk便认为无答案。
5. 每题仍标注允许来源、必要原文证据、答案要点和审核状态。全库模式给全部允许文档，不提前告诉系统正确文档；单文档成绩单列。人工确认标签后，才能报告正式质量指标。

当前CLI只支持运行dev，没有 `--split test`；独立最终测试需要另增受控执行入口。新OHR数据还需完成字段适配、原文定位核验和标签审核。真实生成问答、独立最终测试和模型裁判均不属于已有32题成绩。

### 3.3 评什么与怎么判

| 层次 | 指标/检查 | 解释与判分边界 |
|---|---|---|
| 解析与切片 | 原文/页码/章节核验，必要证据是否完整落入片段 | 找不到完整证据先区分解析遗漏与切片切散，不直接归咎检索器 |
| 检索覆盖 | Hit@5、必要证据Recall@5 | 来源、位置和完整引句同时匹配；重复命中同一必要证据不重复加分 |
| 排序 | MRR@5、chunk-qrels nDCG@5 | nDCG的理想排序来自全部允许片段的二元qrels；与原文证据覆盖率分开解释 |
| 答案 | 答案正确性、要点完整性；适用时做严格规范化短答案比较 | 保留正负号、币种、比例、年份与对象；词面匹配仅作机械诊断，不能证明开放答案语义正确 |
| 忠实性与引用 | 事实是否被输入证据支持，引用是否支持对应句子 | 引用ID存在不等于引用支持结论；答案正确、忠实和引用正确分开审核 |
| 无答案 | 无答案拒答召回率、可回答题误拒率 | 依照真实状态与独立语义审核；摘录模式有相关片段就返回成功，不能据此评价DeepSeek拒答能力 |
| 效率与稳定 | 检索/重排/生成/端到端P50/P90、失败、重试、调用和token | 冷/热缓存分开；未知usage保持空，核验单价前不报费用；重复运行不扩充独立样本数 |

已实现的判分优先使用程序和原始证据。后续LLM Judge应固定提示词、模型和rubric，并用一批人工判定样本校准，按分歧复核。Win Rate应对同题、同证据条件下的两份真实生成答案匿名展示，交换A/B位置复评；分别报告胜率、败率、平局率及分母，不把排序指标的提升叫成答案胜率。这些语义与盲评步骤当前均为待实施方案。

### 3.4 已有实测结果

已完成同一份BGE-M3 INT8索引上的四组对照：32道原创开发题、10份文档、40个片段，每组3次，共384个题次。正证据指标按29道可回答题计算，3道无答案题单列；所有语义标签仍待人工审核。完整结果见 [RAG评测与优化报告](benchmarks/rag/RAG评测与优化报告.md) 与 [逐题原始记录](benchmarks/rag/results/retrieval-v1/predictions.jsonl)。

| 检索策略 | 必要证据Recall@5 | MRR@5 | chunk-qrels nDCG@5 | 检索P50 / P90 |
|---|---:|---:|---:|---:|
| BM25-only | 100% | 0.9483 | 0.9591 | 50.44 / 61.03 ms |
| BGE Dense-only | 100% | 0.9828 | 0.9873 | 71.44 / 82.06 ms |
| BM25＋Dense＋RRF | 100% | 0.9655 | 0.9745 | 82.34 / 100.47 ms |
| 混合＋轻量覆盖率重排＋邻居补全 | 100% | 1.0000 | 1.0000 | 83.21 / 104.12 ms |

混合检索＋轻量重排＋邻居补全的组合配置相对BM25，MRR增加0.0517、nDCG增加0.0409，Recall未提高，延迟增加；现有实验不能把收益单独归因于重排。Dense在本开发样本上优于未重排的Hybrid。全体Recall达到上限说明这套小样本不足以区分召回能力，下一步应增加真实公开文档与难例，而不是继续在32题上调出更好看数字。当前重排是词项/短语覆盖率与融合分数的轻量实现，不是Cross-Encoder。

此外已完成128个“检索→摘录回答”题次和三类固定证据诊断各32题，总计608个逻辑题次；原记录中的失败、零收益和负收益全部保留。没有调用收费生成模型，答案正确率、人工忠实度、引用语义支持率和盲评Win Rate尚未核验。实际命令、源码身份、环境、数据哈希见各批次manifest；这些历史结果不是本次文档更新后新跑出的成绩。

### 3.5 可执行的评测命令

评测源码位于当前 `main`；较早的 `v0.5.0` 镜像和下载包不包含新增评测入口，请先克隆或更新仓库。以下命令在项目根目录执行，详细参数见 [评测使用说明](benchmarks/rag/README.md)。每次使用新的输出目录，程序拒绝覆盖旧记录。

```powershell
$py = ".\.venv\Scripts\python.exe"

# 1. 无收费API：BM25检索与摘录引用链路，不需数据库或Docker
& $py -m benchmarks.rag.run_end_to_end --embedding none --strategies bm25 --output .runtime/rag-eval/first-run

# 2. 需要真实本地BGE时，先联网下载并校验固定版本权重
& $py scripts/download_embeddings.py

# 3. 四组检索对照：冻结配置，三次重复，输出实际排名与耗时
& $py -m benchmarks.rag.run_retrieval --config benchmarks/rag/configs/retrieval-v1.json --output .runtime/rag-eval/four-strategies

# 4. 固定证据诊断：另可选reference_noise、missing_key
& $py -m benchmarks.rag.run_generation --condition reference --answer-mode extractive --output .runtime/rag-eval/reference
```

模型权重下载不等于调用生成式API。`extractive`只展示原文，不能用它的成功状态充当生成质量。真实生成式评测须配置本地模型key后，显式添加 `--answer-mode llm` 和 `--max-model-calls`；默认调用预算为零。每题发送前保守预留2次物理调用，单次60秒，请求最多2次；剩余预算或截止时间不足时不发送新请求。

审核时复制输出中的 `review-template.json`，逐条填写审核身份、理由和各维度分数，再通过 `benchmarks.rag.review`导入；预测内容哈希不一致会被拒绝。该流程不会自动批准题库标签。正式比较两个批次用 `benchmarks.rag.compare`，它会检查题目、来源、配置和配对关系；代码变化的前后对照须显式声明并保留补丁。

### 3.6 下一轮优化顺序

以下是根据已有失败和第十二章评估方法制定的优化路线，尚未新增实现或宣称取得收益。每轮先复现受影响案例、修复同类边界，再进行小范围验证；通过后才跑整套开发集。最终测试在冻结后一次性启用。

| 顺序 | 要验证的假设与改动 | 受控对照 | 验收依据 |
|---|---|---|---|
| 1. 先补真实公开样本与标签 | 32题Recall已达上限，需识别真实长文档中的解析/召回/排序瓶颈 | OHR原始文档全库检索与单文档控制分开，先审核证据再冻结开发/最终分组 | 来源、问题、证据可追溯；分组无泄漏；每类错误有真实案例 |
| 2. 定位证据利用与生成拒答 | 先判断证据充分时是否仍答错，再决定应改检索还是改生成 | 真实检索证据、经确认参考证据、参考＋干扰、缺必要证据；真实生成模型参数一致 | 正确性、要点完整性、忠实性、引用支持及拒答/误拒分开审核，不使用题号或实体特判 |
| 3. 校准切片完整性 | 长段落、表头或跨片证据可能在切片时损失 | 同语料比较350/50、500/80、800/120三组字符长度/重叠；Top-K与检索器固定 | 必要证据完整覆盖、Recall/nDCG、片段数与检索/生成成本共同变化 |
| 4. 验证融合和重排是否值得 | 当前Hybrid弱于Dense，不能默认加组件就更好 | 同索引比较BM25、Dense、RRF和现有轻量重排；固定每通道候选预算并记录总候选数 | 同题由错变对/由对变错、MRR/nDCG和P90；零/负收益也保留。神经重排仅在另设组后评估 |

比较时固定语料与模型版本、题面、允许范围、时钟、Top-K、评分规则和共同代码；每次只改变声明的变量。切片变化应重建独立索引，并继续以原文标签判分，不修改Gold适配预测。先用规则做全量低成本检查，再对开放答案做语义审核；LLM裁判和大批API运行保持显式预算与手动启动。

现有 `compare.py` 要求两批索引与切片条件一致，`--allow-code-change` 也不会放开这一约束。因此跨切片实验需要另补按原文证据对齐的比较入口；当前不能把它描述成已有的一条消融命令。

### 3.7 回归验收与项目经历

采用三档验收：日常修改运行无API的结构/指标/引用回归；版本候选运行完整开发集及必要语义抽审；来源、参数、标签和代码冻结后再启用独立最终测试。开发集反复调参得到的提升与最终测试成绩分别报告。

[RAG CI](.github/workflows/rag-eval.yml) 已运行无收费API的指标、来源定位、引用、预测审核绑定及摘录工具链回归；它目前不是开放答案语义质量门禁。后续增加质量门禁时，应先冻结审核后的开发基线和允许回退幅度，不能将“程序没有报错”写成“答案准确率未下降”。当前实测 [123项本地相关回归通过](benchmarks/rag/results/local-test-receipt.json)，仅代表该记录对应的测试范围。

| 状态 | 内容 |
|---|---|
| 已实现并实跑 | 三条评测入口、32题原创开发样本、来源哈希和原文证据核验、真实BGE四组检索、分阶段耗时、逐题结果、摘录链路、无API CI |
| 已实现，待填审核 | 预测哈希绑定的语义审核导入；答案正确性、忠实性、引用支持和完整性的分开统计 |
| 待实施/未验证 | OHR专项集适配与人工标注、独立最终测试、真实生成式质量评测、模型裁判校准、盲评Win Rate、神经Cross-Encoder、质量回退门禁 |

适合当前项目经历的表述：**实现评测驱动的RAG系统，将原文证据标注、检索/回答分层诊断、同题消融、质量与时延统计及持续回归串成闭环；在32题原创开发样本上实跑四种检索策略，记录轻量重排的排序收益和成本。**

完成后续公开语料与语义评测后，再补“公开数据集规模、独立测试结果、语义审核方式、净改善和代价”。当前不能写成“公开OHR准确率100%”“200道RAG题”“已完成人工忠实度评估”或“复现BFCL/GAIA榜单”。参考方法的采用范围和真实限制见 [主报告](benchmarks/rag/RAG评测与优化报告.md)。
