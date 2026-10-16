# 本轮前端改造实测记录

本目录记录均由当前新增前端重新执行，不沿用原安装包的报告。0次真实模型调用，0次真实数据库查询，未读取保留题。浏览器页顶明确显示“接口模拟验证”。

| 验证 | 实际命令 | 结果 | 原始记录 |
| --- | --- | --- | --- |
| 生产构建 | `node scripts/build.mjs` | 通过，重新产生dist | `build.txt` |
| 展示与来源合同 | `node --test tests/contract.test.mjs` | 10通过、0失败 | `contract-tests.txt` |
| Python本机代理 | `python -m unittest discover -s tests -p test_proxy.py -v` | 8通过、0失败 | `proxy-tests.txt` |
| 浏览器回归 | `node tests/browser-check.cjs`，连接`tests/serve_fixture.py` | 25检查通过，JS页面异常0 | `browser-tests.txt`、`browser-verification.json` |
| 响应式 | 1440、1024、736、320像素宽 | 均无页面横向溢出 | `browser-verification.json` |

覆盖真实请求字段透传、版本化澄清、授权默认切换、来源切换新会话、百分比与原始值导出、金额精度、NULL/空集、结果key隔离、截断、HTML转义、schema理由/断连、trace详情、两类跨源中间传值、资料不足仍保留SQL结果。

代理只监听127.0.0.1，只允许本机API目标及业务接口白名单；路径穿越被拒绝，不跟随上游重定向。`/ui-health`与后端`/health`分离，并已测试后端离线时前端仍健康。

原始定位器错误见 `browser-tests-initial-failure.txt`；原因是同一文本同时出现于定义和SQL，修正测试定位器后完整重跑通过。`browser-tests.txt`中的HTTP422为故意构造的错误恢复检查。

截图：`frontend-desktop.png`、`frontend-hybrid-sql-to-doc.png`、`frontend-hybrid-doc-to-sql.png`。均为明确标识的受控接口截图，不作为模型业务效果证明。

未验证项：本轮未新增真实模型答案质量评测；正式数据库与模型端到端联调由现有后端及项目启动流程另行记录。

追加保护验证：递归敏感键、内嵌凭据、诊断长度/层级限制、导出脱敏与35行完整精确数值的4项合同测试通过；浏览器同时验证NLU和trace展开后不出现测试凭据、导出无凭据且原始比例/金额保留。新dist已重新构建。

刷新修复：refresh仅更新健康与文档清单，不修改所选doc_id。浏览器验证hybrid全部登记范围在刷新后仍为doc_ids=[]、session不变；文档移除时警告并禁发，恢复后重新就绪。刷新按钮回归使用DOM click事件；早期指针/键盘脚本的waitForResponse超时保留于browser-tests-refresh-attempt.txt，不将该自动化手势认定为稳定通过。
