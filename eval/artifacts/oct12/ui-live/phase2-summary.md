# 10月12日 Phase2 真实界面验证记录

本记录对应 `run-003`，是 Phase2 实测证据，不能移作后续 Phase3 或最终源码版本的通过证据。前三轮原始报告、截图和响应保持原状。本轮真实提交5个问题，保存5张截图，4个场景符合观察检查、1个场景功能失败；36项自动观察检查中33项通过、3项失败。未运行任何保留题，浏览器未记录异常。

实际命令：

```powershell
.\.venv\Scripts\python.exe -B scripts/capture_oct12_demo.py --run --api-records eval/artifacts/oct12/api-records/live-002 --output eval/artifacts/oct12/ui-live/run-003
```

命令退出码为1。日志见 `eval/artifacts/oct12/rag-ui/ui-live-run-003-command.log`。原始报告见 [run-003/report.json](run-003/report.json)，逐张AI视觉检查见 [run-003/visual-review.json](run-003/visual-review.json)。这些记录没有人工签字。

| 场景 | 实际状态与结果 | 证据 |
| --- | --- | --- |
| 艺术家JOIN | SUCCEEDED，Metallica有10张专辑，实际JOIN可见 | [截图](run-003/artist-join.png)、[原始请求/响应](run-003/artist-join-raw.json) |
| 拼音改写 | SUCCEEDED，巴稀→Brazil（拼音匹配1.00），客户数5，主流程无候选ID | [截图](run-003/pinyin-rewrite.png)、[原始请求/响应](run-003/pinyin-rewrite-raw.json) |
| 发票占比 | FAILED，未执行SQL，没有比例结果，不记通过 | [截图](run-003/invoice-ratio.png)、[原始请求/响应](run-003/invoice-ratio-raw.json) |
| 同比增长率 | SUCCEEDED，答案和表格显示24.24%，raw保留0.24240365013105523736 | [截图](run-003/invoice-growth.png)、[原始请求/响应](run-003/invoice-growth-raw.json) |
| rag-03数字回退 | SUCCEEDED表示返回回答；两次数字核验失败后明显标注未核实，semantic_faithfulness=not_verified，不记忠实度通过 | [截图](run-003/rag-03.png)、[原始请求/响应](run-003/rag-03-raw.json) |

本次 API PID 为23744、UI PID 为83684。观察脚本校验了服务启动时间晚于所覆盖源码修改时间，并记录42个文件的SHA256。与 `eval/artifacts/oct12/runtime-snapshot-002/manifest.json` 的66个文件比较，41个交集文件全部一致；观察脚本额外记录了快照未列入的 `scripts/d2_capture_api.py`。这证明了被比较磁盘文件的一致性与本项目进程归属，不能替代运行中Python每个模块的加载哈希证明。Provider原始输出实际仍写在 `eval/artifacts/oct12/provider-captures/live-001/`，不能按目录名假定为旧请求；本轮trace与API记录一一匹配。

占比失败的trace为 `3245a54a-a841-4f83-8855-ce63aa1e29f7`。标准SQL校验成功，但绑定校验拒绝了三次相同的期间边界。原SQL和两次修复都使用2024-01-01/2025-01-01午夜TIMESTAMP常量，分子为Brazil条件CASE、分母为无条件发票总額；全局WHERE没有国家筛选。Phase2的 `qa_agent/sql/ratio_guard.py` 的 `boundary()` 直接将解包常量文本与ISO日期文本比较，因此等效的 `2024-01-01 00:00:00` 未通过 `2024-01-01` 检查。全部模型响应JSON合法，没有网络异常。问题已反馈根代理；本次仅核验、保存证据，未修改业务代码。

rag-03 trace为 `d77bb9e7-290b-4aa3-b14c-8950dea8cc2d`。返回E6原文物理第2页支持three years，但其短片段未包含同句Section13/1934；故数字核验失败，自动重生成一次后仍失败，界面黄色警示和【未核实】均可见。PDF图像已加载，截图显示上部，未覆盖整页，仍可用原PDF链接查看完整页。后续验收需要将“已返回且警告正确”和“完整引用语义支持正确”分别记录。

待根代理完成窄修复、回归、重启与新快照后再验证下一轮；不覆盖本次失败。
