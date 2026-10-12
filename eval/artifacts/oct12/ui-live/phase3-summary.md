# 10月12日 Phase3 最终真实界面验收记录

最终冻结服务 `run-004` 实际完成5个场景，保存5张真实截图、5份DOM和5份API请求/响应，33/33观察检查通过、浏览器错误0，命令退出0。所有截图都已使用view_image逐张核对字体、结果、可读改写和引用页。保留题预测0，未填写任何人工签字或批准状态。

```powershell
.\.venv\Scripts\python.exe -B scripts/capture_oct12_demo.py --run --api-records eval/artifacts/oct12/api-records/live-003 --output eval/artifacts/oct12/ui-live/run-004
```

命令原始日志为 `eval/artifacts/oct12/rag-ui/ui-live-run-004-command.log`。[原始报告](run-004/report.json)、[逐张视觉记录](run-004/visual-review.json)、[机器可读汇总](phase3-summary.json)均保留实际状态。

| 场景 | 本轮实际结果 | 截图、raw及DOM |
| --- | --- | --- |
| 艺术家JOIN | Metallica有10张专辑，实际album.artist_id=artist.artist_id JOIN | [截图](run-004/artist-join.png)、[raw](run-004/artist-join-raw.json)、[DOM](run-004/artist-join-dom.txt) |
| 巴稀改写 | 巴稀→Brazil（拼音匹配1.00），真实候选score=1.0，客户数5；主流程无候选ID | [截图](run-004/pinyin-rewrite.png)、[raw](run-004/pinyin-rewrite-raw.json)、[DOM](run-004/pinyin-rewrite-dom.txt) |
| 2024发票金额占比 | 答案及表格11.20%；raw保留0.11195108160743827613，scale=100 | [截图](run-004/invoice-ratio.png)、[raw](run-004/invoice-ratio-raw.json)、[DOM](run-004/invoice-ratio-dom.txt) |
| 2024发票销售额同比 | 答案及表格24.24%；raw保留0.24240365013105523736，scale=100 | [截图](run-004/invoice-growth.png)、[raw](run-004/invoice-growth-raw.json)、[DOM](run-004/invoice-growth-dom.txt) |
| rag-03 | 首次生成即[E6][E1]，数字校验passed、重生成0次；物理第2页完整PDF预览可见；语义仍pending_human_review | [截图](run-004/rag-03.png)、[raw](run-004/rag-03-raw.json)、[DOM](run-004/rag-03-dom.txt) |

所有SQL场景均为实际SUCCEEDED响应。占比分母是同年全部发票总额，Brazil国家限定仅在分子CASE，本轮SQL使用ISO日期字符串。Phase2午夜TIMESTAMP失败证据保持在 `run-003/invoice-ratio-raw.json`；午夜等价的窄证明另有模块/隔离探针，不把本轮日期字符串形式误写为午夜TIMESTAMP实际执行。

本轮API PID25108、UI PID55064，API capture与Provider capture均为live-003。运行记录覆盖42个文件SHA，与 `eval/artifacts/oct12/runtime-snapshot-003/manifest.json` 的66个文件有41个交集，全部相等、无差异；额外的观察文件为 `scripts/d2_capture_api.py`。服务启动时间与项目进程归属检查也通过。这是磁盘源码及项目进程证据，不等同于运行时逐模块内存加载证明。

本轮rag-03 trace为 `0cfa4de2-673a-443d-be43-cacdbe34d2f4`，实际Provider响应是 `eval/artifacts/oct12/provider-captures/live-003/2ff1534ad6914f7884c4c47bf3aafc11.json`。E6支持three years，E1补足生效日期和Section13/1934上下文，数字及身份/编号校验通过；`semantic_faithfulness=pending_human_review`说明自动校验没有代替完整语义人工判断。本轮没有触发未核实分支。

真实未核实分支的历史证据为Phase2 `run-003/rag-03-raw.json`，trace `d77bb9e7-290b-4aa3-b14c-8950dea8cc2d`。两次数字核验失败后返回黄色警示与【未核实】标记，semantic_faithfulness=not_verified。比较run-003与run-004证明 `qa_agent/rag/answer.py`、`qa_agent/rag/service.py`、`ui/app.py`三个组件源码SHA完全一致；历史证据仍明确标作Phase2，不计作本轮新请求或忠实度通过。

run-001的绘制等待缺陷、run-002的实际结果、run-003占比失败以及各轮原始图片和回答均保留。最终展示采用run-004，修复过程与失败依据可从前面版本追溯。
