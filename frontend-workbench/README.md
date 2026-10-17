# ComAgent 白色立体数据工作台

本前端按提供的白色立体模板实现，使用现有 React、Ant Design 和 esbuild，继续接入项目 FastAPI 的 `ChatRequest` / `AnswerEnvelope`。没有新增运行依赖、外部 CDN 或后端业务协议。保留 ComAgent 文字名称，不显示品牌图形标志、C 头像或品牌 favicon。

## 五个页面与数据边界

主导航为：**数据概览、数据分析、问答工作台、数据与文档、运行记录**。

- **数据概览**默认空态，不预置销售额、客户数或五等分业务数据。可以加载最近一次实际 `AnswerEnvelope.table`，选择单一指标，以立体环形、柱状或序列图查看，支持选择、旋转、重置。
- **数据分析**支持本地粘贴／导入 CSV、TSV、JSON、TXT，选择分类列、单一数值列以及求和、平均值或记录计数。最多 2MB、20,000 行、100 列，超限会提示，不静默截取输入；可预览原始行、查看分类统计、导出完整本地 JSON。
- **问答工作台**保留原有自动综合、数据库、单文档、Chinook 跨源、会话正文、澄清卡、默认切换、真实证据和结果导出，不用模板演示问答替代已有流程。
- **数据与文档、运行记录**承接原来的资源、文档及运行证据入口，与浏览器内的本地表格分析分开。

图表仅作近似可视化，原始返回表和查询范围是权威依据。不修改原始 Decimal 字符串、NULL、零值或原始行；NULL、空白、布尔值不会变成数字 0。负数保留于柱状和序列图，不能绘制占比环。ID、年份不自动当金额或求和指标；多指标需要明确选择一列，比例、均值和单个数值不重新归一成 100%。图示最多取前 8 个有值类别，预览及分类列表的显示上限会标注，完整结果仍可导出。

本地求和采用十进制整数运算；不能精确写成有限小数的均值会标近似。JSON 数字保留原数字字面值，避免大整数、长小数提前舍入。不同列不会自动混合量纲；指标含义和统计口径由使用者确认。

### 本地分析何时会发送数据

本地文件读取、粘贴、统计、图表和导出在当前浏览器内进行，不自动上传文件、调用模型或发送全量记录。清空或刷新页面可清除这些临时分析数据。

“整理为草稿”仅把**明确标记为摘要、不是全量上传**的有限分类统计填入工作台，不自动发送。之后使用者若手动点击发送，该摘要文本会随正常问答请求进入后端，并可能进入模型输入；这不等于文件或全量原始记录已上传，也不足以重新核验全部数据。后端文档上传是另一个显式入口，不属于本地分析。

## 启动：8501

从 `system` 目录运行统一启动脚本 `启动项目.cmd`，访问 `http://127.0.0.1:8501/`。也可以在两个终端分别执行：

```powershell
# 均在 system 目录
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe frontend-workbench/run_ui.py --port 8501 --api-url http://127.0.0.1:8000
```

预构建页面位于 `dist/`，日常启动前端只需 Python 标准库，不需要 Node 或 CDN。代理只连接配置的本机回环 API；模型密钥仍由后端 `.env` 管理，不放进浏览器。启动器不会替使用者停止其他 API 或 Streamlit 进程。

- `/ui-health`：前端自身健康；可区分前端启动与后端离线。
- `/health`：代理后端健康检查，可能包含真实只读数据库连通探测。

## 原有来源、正文与结果合同

自动综合入口保留所选 Chinook 或 AdventureWorks 和实际文档范围。数据库入口只读；指定文档入口保持单文档范围；混合入口使用 Chinook，保留文档定义影响 SQL、数据库对象关联资料等已有流程。允许入口的 `doc_ids=[]` 表示已登记范围，不宣称实际使用了全部资料；未扩展为任意数据库之间的通用代理。

普通提问仍限 4,000 字符。长正文通过“保存会话正文”独立 `POST /api/context` 完整提交，上限 120,000 字符，保存响应显示版本、字符数和 SHA-256；后续问答携带实际 `context_id`。编辑正文不自动保存或调用模型，正文是用户会话约定，不自动成为公司政策。保存新版本、切换来源／数据库／文档或新建会话时，沿用原会话绑定与失效规则，避免串用旧上下文。

澄清和默认切换只提交服务真实返回的 `clarification_id`、`intent_version`、`choice_id`，界面不自行构造或递增版本。结果继续区分 NULL、空集、零分母、截断、来源不足和失败。

业务表头使用实际 `metadata.column_labels`，金额／百分比按显式 `metadata.result_format` 展示，不能凭别名或值大小猜百分数。原始键、数值和大精度字符串在响应与导出副本中保留。SQL、原文页／章节、假设、trace、选表依据和跨源步骤继续在独立证据区供核对，不用图表替代原始结果。

诊断副本使用 `safeDiagnostics` 遮盖凭据、完整提示词和目录，并限制深度与长度；导出使用不截断业务行的 `safeExport`。二者不反向修改后端响应对象。

## 构建

在 `frontend-workbench` 目录执行。依赖尚未就绪时先按现有锁文件安装；本轮没有增加包：

```powershell
pnpm install --frozen-lockfile
node scripts/build.mjs
```

产物为 `dist/index.html` 和本地 `dist/assets/`，无 CDN 运行依赖。若 pnpm 构建策略阻止 esbuild 安装脚本，应核查明确错误和本地包状态，不能把安装失败写成构建成功，也不要擅改全局安装策略。实际构建结果以本轮接入验收记录为准。

## 测试命令与验证边界

下面是维护的测试入口，**不是所有测试已通过的声明**。不沿用旧界面的测试数量或历史截图作为本轮结果。

在 `frontend-workbench` 目录运行本地分析与合同测试。下面的合集也含两个真实 DOM 下拉列表测试，需要先让 Node 能找到已有 Playwright，并按需设置 `COMAGENT_QA_NODE_MODULES` 和 `COMAGENT_QA_CHROME`：

```powershell
node --test tests/contract.test.mjs tests/client-precision-independent.test.mjs tests/analysis.test.mjs tests/browser-real-smoke-checks.test.cjs tests/browser-output-contract-checks.test.cjs tests/browser-context-sql-focus.test.cjs tests/real-request-control.test.cjs tests/browser-white-analytics-checks.test.cjs
..\.venv\Scripts\python.exe -m unittest discover -s tests -p test_proxy.py -v
```

分析测试覆盖解析、十进制、NULL／0／负值、字段选择、单比例不归一、原数据不变、安全文本、输入上限与 SVG 几何。代理、纯函数和受控模拟测试通过，不等于真实模型业务准确率通过。

### 模拟接口浏览器检查

使用已有 Playwright 和本机 Chrome／Chromium，不是新增的前端运行依赖。`COMAGENT_QA_NODE_MODULES` 可指向已有 Playwright 包目录，`COMAGENT_QA_CHROME` 可指定本机浏览器。先在一个终端启动受控 fixture：

```powershell
# 在 frontend-workbench 目录
..\.venv\Scripts\python.exe tests/serve_fixture.py --api-port 35170 --ui-port 35171
```

另一个终端运行；显式设置 URL，避免脚本默认端口不同：

```powershell
$env:COMAGENT_QA_UI_URL = 'http://127.0.0.1:35171'
$env:COMAGENT_QA_API_URL = 'http://127.0.0.1:35170'
node tests/browser-check.cjs
node tests/browser-context.cjs
node tests/browser-white-analytics.cjs
```

这些脚本只连接受控本机模拟接口。新的分析脚本核对五项文字导航、无品牌图标／favicon、模拟返回表取值、本地 CSV／NULL／0／负数、无自动问答外发及多档窄屏。fixture 数据与截图不能冒充真实数据库或模型预测。每次使用新的证据目录；默认生成不同目录，若设置 `COMAGENT_QA_OUTPUT_DIR`，每个脚本、每次运行也必须指定新的空目录。

### 真实接口检查

`tests/browser-real-smoke.cjs` 默认只输出 `prepared_not_run`，不发请求。只有明确授权、服务就绪、原文输入和 STOP 设置核对后，才可按本轮记录显式启用。真实检查可能调用模型、执行后端只读查询并产生费用，不能与 fixture 混称“零 API／零数据库”；局部 focus、完整 smoke 与页面检查范围应分列。

本轮最终的构建、代理、纯函数、浏览器、响应式、截图及真实接口验证统一见 **[白色立体版接入验收](docs/white-ui/接入验收.md)**。该文档由实际验证完成后封存；本 README 不预写尚在进行的浏览器或真实接口检查为通过，也不拿旧界面历史结果充当本轮成功。
