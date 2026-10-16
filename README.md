# ComAgent 可解释问数问答智能体

项目通过 DeepSeek 理解问题，复用 PostgreSQL、文档检索和执行约束，返回答案、真实 SQL、查询结果、引用和处理步骤。

## 打开项目

本机双击 **启动项目.cmd**，浏览器进入 **http://127.0.0.1:8501/**。API 文档在 **http://127.0.0.1:8000/docs**。

默认界面采用本仓库 `frontend-workbench/` 的 React + Ant Design 工作台。静态构建已包含在 `dist/`，日常运行无需 Node、npm 或 CDN。Python 静态服务仅代理本机 FastAPI。

启动脚本复用本工作区的 API 和现有数据库容器；数据库未就绪时显示实际状态，不删除数据卷，不重新导入业务库。旧 Streamlit 仅保留兼容与历史测试，不是默认入口。

## 功能

- 数据库问数：Chinook、AdventureWorks，SQL 生成、校验和只读执行。
- 指定文档问答：引用原文、物理页预览、来源下载及资料不足提示。
- 数据库与文档：Chinook 艺术家销售排名→介绍；口径手册定义→SQL计算。
- 多轮：保留会话和结构化条件，支持版本化澄清与授权口径切换。
- 解释面板：SQL、原始结果、要素改写、选表与剪枝理由、跨源步骤及 trace。

## 首次部署

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
