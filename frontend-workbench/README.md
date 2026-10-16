# ComAgent 问答工作台

采用提供的 React + Ant Design UI 风格，接入现有 FastAPI 的 `ChatRequest` / `AnswerEnvelope`，不改变后端业务协议。已移除独立安装包中的人工复审导航、审核页面、审核导入及旧打包程序。

## 启动

从 `system` 目录运行项目统一启动脚本 `启动项目.cmd`，浏览器访问 `http://127.0.0.1:8501/`。

也可分别启动后端与本前端：

```powershell
# 在 system 目录，两个终端分别执行
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe frontend-workbench/run_ui.py --port 8501 --api-url http://127.0.0.1:8000
```

预构建页面位于 `dist/`，日常启动只需要 Python 标准库，无需 Node、安装前端依赖或访问 CDN。模型密钥沿用后端 `.env`，不放入前端。

- `/ui-health`：本前端服务独立健康信息，API离线时仍返回前端自身状态。
- `/health`：代理后端健康检查，反映数据库、模型配置等实际状态。

## 支持的入口

- 数据库问数：Chinook、AdventureWorks，只读查询。
- 指定文档：选择已就绪文档，严格单文档范围。
- 数据库与文档：固定 Chinook，支持艺术家销售排名→艺术家介绍及指标手册定义→SQL。默认 `doc_ids=[]` 表示使用已登记的允许文档，也可以指定一个文档范围。未扩展成通用跨源数据库代理。

切换来源、数据库、文档会创建新会话，普通续问保持当前会话。澄清和默认切换提交服务返回的 `clarification_id`、`intent_version`、`choice_id`；界面不自行构造或更新版本。

结果区保留 NULL、空集、大精度金额字符串、截断提示。百分比仅按 `metadata.result_format` 展示，导出的表格与回答对象仍包含原始值。证据面板展示 SQL、原文页或章节、假设、真实trace、表定位理由、断连警告与跨源步骤和中间传值。

## 重新构建与测试

在本目录使用已安装的 Node 与 pnpm：

```powershell
pnpm install --frozen-lockfile
node scripts/build.mjs
node --test tests/contract.test.mjs
..\.venv\Scripts\python.exe -m unittest discover -s tests -p test_proxy.py -v
```

浏览器测试使用 Playwright 和本机 Chromium/Chrome。先运行 `tests/serve_fixture.py`，再运行 `node tests/browser-check.cjs`。可通过 `COMAGENT_QA_NODE_MODULES` 指定 Playwright 所在目录，`COMAGENT_QA_CHROME` 指定浏览器路径；使用受控本机服务，不产生模型调用或数据库查询。

本次环境 pnpm 将 esbuild 的安装脚本标记为未批准并返回 `ERR_PNPM_IGNORED_BUILDS`；其锁定原生二进制包已下载，实际 `node scripts/build.mjs` 成功。没有修改用户全局安装策略，亦未把 `node_modules` 纳入交付。

## 本轮验证边界

`docs/` 保存本轮重新执行的构建、8项代理测试、10项展示合同测试、25项浏览器检查、4档响应式宽度及3张截图；这些是接入与展示测试，不是模型准确率实测。浏览器日志中一次HTTP 422是主动测试后端错误恢复，`page_errors=[]`。早期定位器同时匹配定义与SQL的失败日志保留，限定到定义面板后最终回归通过。

诊断详情通过 `safeDiagnostics` 隐藏凭据、完整提示词与catalog，遮盖内嵌API key、Bearer与PostgreSQL连接，并限制列表、字符串、字段数及层级。导出采用不截断业务行的 `safeExport`：脱敏敏感内容，保持普通数值、精确金额字符串与原始比例。前端仅建立显示/导出副本，不改后端响应对象。

刷新修复：refresh仅更新健康与文档清单，不修改所选doc_id。浏览器验证hybrid全部登记范围在刷新后仍为doc_ids=[]、session不变；文档移除时警告并禁发，恢复后重新就绪。刷新按钮回归使用DOM click事件；早期指针/键盘脚本的waitForResponse超时保留于browser-tests-refresh-attempt.txt，不将该自动化手势认定为稳定通过。
