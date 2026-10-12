# 12号任务真实界面验证记录

两轮均使用现有Python 3.12、DeepSeek `deepseek-flash`、真实隐藏Edge、Streamlit和项目API中间件。API保存PID41412，UI保存PID65332；启动时间与源码哈希见各轮report。两轮业务源码哈希一致，没有mock回答、保留题预测或人工签字。

第一轮5项请求、5张截图，程序行为检查36/36通过；PNG视觉检查发现艺术家表格、比例SQL/结果表、RAG PDF预览的捕获绘制时序问题，原report与原图均保留，另写[第一轮视觉检查](run-001/visual-review.json)标记PARTIAL_RENDER_RACE。仅修改观察脚本等待真实绘制，再用5个新session生成第二轮请求，不能把两轮当同一回答。

第二轮5项请求、5张截图，程序行为检查33/33通过，浏览器错误0。5张PNG经view_image逐张检查，主结果、中文字体、比例单位及PDF预览可读。原始值、完整SQL、调用步骤和请求编号均保存在对应raw；截图只捕获实际浏览器，不拼接或修改图像。

| 项目 | 第二轮实际观察 | 真实截图与原始输出 |
| --- | --- | --- |
| 艺术家JOIN | Metallica有10张专辑；实际SQL连接album与artist。结果表10已绘制。 | [图](run-002/artist-join.png)、[raw](run-002/artist-join-raw.json) |
| 巴稀链接依据 | 客户数5；“巴稀 → Brazil（拼音匹配1.00）”使用本次真实分数，未显示候选ID。 | [图](run-002/pinyin-rewrite.png)、[raw](run-002/pinyin-rewrite-raw.json) |
| 2024年Brazil账单国家金额占同期全部发票金额 | 答案及表格11.20%，原始数据库分数值单独保存；未再次乘100。 | [图](run-002/invoice-ratio.png)、[raw](run-002/invoice-ratio-raw.json) |
| 2024年USA账单国家发票销售额同比增长率 | 答案及表格24.24%，当前年与上一年条件见实际SQL。 | [图](run-002/invoice-growth.png)、[raw](run-002/invoice-growth-raw.json) |
| rag-03重生成纠正 | 第二轮首次数字核验失败，重生成一次后同时引用E6（三年）与E1（期间及法规上下文），低成本核验passed；物理第2页原文和PDF预览可见。完整语义仍pending_human_review。 | [图](run-002/rag-03.png)、[raw](run-002/rag-03-raw.json) |

第一轮rag-03确实触发“重生成一次仍未通过”分支：请求编号`246d4c4a-92cd-4162-a4c3-7249118969ac`，`validation_retries=1`、`validation_status=unverified`、`faithfulness_uncertain=true`、`semantic_faithfulness=not_verified`，界面实际显示黄色提醒和【未核实】前缀。它只引用E6，法规数字未在该引用片段中核实；这份回答不计为忠实度通过。[真实原始输出](run-001/rag-03-raw.json)、[实际提醒截图](run-001/rag-03.png)。该图PDF预览尚未完成绘制的局限已在第一轮视觉检查中登记。

第二轮rag-03请求编号`ceffef9e-a80a-4f3a-aafe-f7598fafbcf2`，是另一次真实预测，重生成后补齐E1和E6，不再带未核实标记。不会把第一轮告警状态套到第二轮，也不会将低成本核验passed写成人工事实审核通过。

实际运行命令（两轮命令和原始stdout分别另存）：

```powershell
./.venv/Scripts/python.exe -B scripts/capture_oct12_demo.py --run --api-records eval/artifacts/oct12/api-records/live-001 --output eval/artifacts/oct12/ui-live/run-001
./.venv/Scripts/python.exe -B scripts/capture_oct12_demo.py --run --api-records eval/artifacts/oct12/api-records/live-001 --output eval/artifacts/oct12/ui-live/run-002
```

记录入口：[summary.json](summary.json)、[第二轮程序检查](run-002/report.json)、[第二轮逐张视觉检查](run-002/visual-review.json)、[第一轮实际命令日志](../rag-ui/ui-live-run-001-command.log)、[第二轮实际命令日志](../rag-ui/ui-live-run-002-command.log)。首次未运行的[步骤计划](preparation/plan.json)也保留原状态。
