# ComAgent

**用自然语言查询 PostgreSQL 和文档，并给出可核查的结果、SQL 与原文引用。**

[下载版本](https://github.com/gaara119/ComAgent/releases) · [容器包](https://github.com/gaara119/ComAgent/pkgs/container/comagent) · [构建与发布状态](https://github.com/gaara119/ComAgent/actions)

## 1. 可以做什么

| 功能 | 使用方式 | 得到什么 |
|---|---|---|
| 数据库问数 | 连接 PostgreSQL，用中文提问 | 经过校验和只读执行的 SQL、真实结果表 |
| 文档问答 | 上传 PDF、Word、TXT、Markdown，或粘贴文字 | 基于选定资料的回答、原文引用及位置 |
| 多轮问答 | 继续修改对象、期间或指标 | 保留有效条件；关键歧义通过卡片确认 |
| 跨源查询 | 一个问题同时需要数据库与文档 | 前一步真实结果参与后一步检索或计算 |
| 结果核查 | 展开依据与执行步骤 | SQL、数据、引用、假设和实际工具记录 |
| 本地表格分析 | 在数据分析页导入 CSV/JSON 等 | 浏览器内的统计、图表和导出 |

示例问题：

- 数据库：“各国家客户的发票总金额是多少？”
- 文档：“这份服务说明规定的响应时间是多少？”
- 多轮：“换成加拿大，其他条件不变。”
- 跨源：“销售额最高的艺术家是谁？再介绍他的音乐风格。”

这些是使用示例，不是预置答案。SQL 需要可访问的数据库；文档问答需要已经入库的资料；跨源还需要实体和文档之间的登记关系或可核验的指标定义。新增数据库不自动获得全部业务规则。

## 2. 选择哪种安装方式

| 方式 | 需要安装 | 默认工作台 | 适合谁 |
|---|---|---|---|
| Docker 源码构建，推荐 | Docker Desktop / Docker Engine、Compose v2；Git 可选 | http://127.0.0.1:18501/ | 想直接运行，不想手动安装 Python 依赖 |
| 已发布镜像 | Docker；拉取私有包时还需相应权限 | http://127.0.0.1:18501/ | 已能访问 GitHub Packages 的用户 |
| Windows 原生源码 | Python 3.12；需要本地数据库时再准备 Docker | http://127.0.0.1:8501/ | 想改代码或调试 |

前端已经预编译，正常使用无需 Node.js。首次构建需要联网下载基础镜像与 Python 依赖，建议为 Docker 分配至少 4 GB 内存并留出约 5 GB 磁盘；加载本地向量模型时需要更多资源。发布容器目标为 Linux/amd64，请在 Docker Desktop 中使用 **Linux containers**。

项目不附带模型 API 密钥、BGE 权重、原始业务库或历史知识库。默认可以从空知识库上传自己的文件；未提供本地 BGE 时使用 BM25 关键词检索，配置本地 BGE 并重建索引后才是混合检索。

## 3. Docker 源码启动：一步步操作

以下命令在 Windows PowerShell 中执行。macOS/Linux 可使用同样的 Docker 命令，将 `Copy-Item` 换成 `cp`。

### 第一步：取得源码

有 Git：

```powershell
git clone https://github.com/gaara119/ComAgent.git
cd ComAgent
```

没有 Git：从上方 Releases 下载 `ComAgent-版本号-source.zip`，完整解压，进入含 `Dockerfile`、`compose.app.yml` 和 `README.md` 的目录，在地址栏输入 `powershell` 打开终端。不要只单独取出启动脚本。

### 第二步：确认 Docker 可用

尚未安装时，按 [Docker Desktop 官方 Windows 安装说明](https://docs.docker.com/desktop/setup/install/windows-install/)下载并安装，按安装器提示启用 WSL 2、完成必要的系统重启。项目运行的是 Linux 容器，不要切换为 Windows containers。Docker 方式不需要另装 Python、Node 或本机 PostgreSQL。

打开 Docker Desktop，等待引擎运行，再在源码目录的 PowerShell 中执行：

```powershell
docker version
docker compose version
```

`docker version` 应同时出现 Client 和 Server。只有 Client、提示找不到 `dockerDesktopLinuxEngine`，说明引擎尚未启动，先处理 Docker Desktop，不能继续当成项目故障。

### 第三步：创建配置文件

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

### 第四步：构建并启动

```powershell
docker compose --env-file .env.docker -f compose.app.yml up -d --build
docker compose --env-file .env.docker -f compose.app.yml ps
```

首次需要下载依赖，等待构建完成和服务健康。该配置只启动 ComAgent 应用，不创建或重建数据库。

### 第五步：打开入口

- 工作台：http://127.0.0.1:18501/
- API 文档：http://127.0.0.1:18501/docs
- 健康状态：http://127.0.0.1:18501/health

容器内部 API 为 8000，工作台为 8501；对宿主机仅映射本机回环地址的 18501，不需要再额外开放 8000。

### 已发布镜像的启动方式

镜像名为 `ghcr.io/gaara119/comagent:0.5.0`。在已具备访问权限时：

```powershell
docker pull ghcr.io/gaara119/comagent:0.5.0
docker compose --env-file .env.docker -f compose.app.yml up -d --no-build
```

GitHub Packages 的首次发布可能默认私有，是否可匿名拉取以包页面实际可见性为准。遇到 `denied` 时，可以先使用上面的 **源码构建**，不必为运行项目把 GitHub 凭据写进 `.env.docker`。仓库所有者可在 Package settings 中将包设为 Public；私有包拉取需使用具备 `read:packages` 的凭据。

## 4. Docker 数据保存、重启与更新

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

## 5. 连接 PostgreSQL

项目连接已有 PostgreSQL，以只读方式发现目录和查询。数据库服务不是大模型，填了模型 key 不会自动生成数据库。

### 方式 A：在界面添加新数据库

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

### 方式 B：配置已有示例库连接

在 `.env.docker` 或原生 `.env` 中填写 `CHINOOK_DB_URL` / `AW_DB_URL`，格式例如：

```dotenv
CHINOOK_DB_URL=postgresql://只读用户名:经URL编码的密码@可达主机:端口/chinook
```

URL 中的特殊字符需要编码；如果不熟悉，优先使用界面分字段填写。这里的路径、目录定义和业务规则针对对应示例库，不能只改库名就假定任意业务库同样适用。

本项目包含 Chinook 的初始化 SQL 和准备脚本。**仅在明确的新环境**、已配置本地 `.env` 管理员与只读口令后，可运行原生 `scripts/bootstrap_db.py` 初始化独立示例数据库；已有业务库不要重复导入。AdventureWorks 和大型索引需另外准备资源，不属于首次上传文档的前置条件。

## 6. 上传文件、添加文字和提问

### 长期知识库

1. 点击“上传文档”，选择文件并填写标题；或点击“添加文字”，选择“知识库（长期保存）”。
2. 等待后台解析、切片和索引状态完成。请求已接收不等于资料已可查询。
3. 成功后页面切换到该资料，输入问题。
4. 在答案旁查看引用原文；PDF 可核对物理页位置。

支持 PDF、DOCX、TXT、Markdown。单文件最多 8 MB，新上传 PDF 最多 100 页；TXT/Markdown 使用 UTF-8。相同内容不重复登记。加密文件、没有可提取文字且 OCR 不可用的扫描件会明确失败。

### 仅本次会话的文字

点击“添加文字”，选择“仅本次会话”。它不建立长期知识库索引，最多 120000 字符，默认 24 小时后不再接受该正文绑定。切换来源或新建会话后重新保存；它不会自动升级成系统政策。

### 选择范围

- 自动综合问答：按问题选择可用工具或受约束的跨源流程。
- 数据库问数：选择目标数据库。
- 指定文档问答：选择一份资料，或允许查询登记文档范围。

扩大文档范围只扩大可检索来源，不应自动把介绍意图改成 SQL。遇到关键歧义按卡片确认；确认实体之后继续原问题。

## 7. 可选：启用本地 BGE 混合检索

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

## 8. Windows 原生源码运行

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

## 9. 常见问题

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

## 10. 设计与目录

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
