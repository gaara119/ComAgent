# 12号任务：RAG与界面第二遍代码审查

本记录是实现后单独进行的第二遍代码核对，不是人工签字，也不声称由独立模型完成事实审核。第一遍模块回归82项通过；第二遍发现并修正两处问题后，新回归83项通过。两次日志分别保留，未覆盖。

| 核对点 | 第二遍判断与依据 | 处理 |
| --- | --- | --- |
| 重生成次数 | `answer_from_chunks` 使用固定2次生成循环，只有第一次核验异常写入 `rag_retry`。第二次数字异常没有再次调用模型。 | 符合方案§3.6.6“重生成一次”。测试检查模型调用数=2。JsonLLM内部的格式、传输重试是另一个层级，应从原始调用日志分别统计。 |
| 真实引用边界 | 返回未核实回答前，再次调用 `validate_citations`；引用必须属于实际检索证据，内文编号与清单一致；仍运行现有 `validate_attributions`。 | 伪造E99和不支持的Forbes归属均保持失败，未因数字异常降级而放行。 |
| 未核实可见性 | 回答正文前置固定“【未核实】”；接口返回 `validation_status=unverified`、`faithfulness_uncertain=true`、`warnings`、`semantic_faithfulness=not_verified`；界面显示提醒。 | SUCCEEDED表示回答已返回，不表示事实全部审核通过。验收和评测须同时读取核验元数据，不能把这些回答计为已确认忠实。 |
| 模型不能制造核验通过记录 | 核验告警存于Pydantic `PrivateAttr`，不在DocumentAnswer的模型JSON schema、模型输出字段或model_dump中。 | 由服务程序生成核验状态；测试检查模型可见schema不包含该属性。 |
| 数字核验的语义限度 | 本次沿用逐句引用、数字、正负号、百分号、币种和显式单位核对。数字出现在同一片段，不证明对象、期间、因果及完整语义正确；研究归属核验也只是有限文字模式。 | 即使低成本核验passed，仍标 `semantic_faithfulness=pending_human_review`。不把数字核验当成语义忠实度人工结论。 |
| 第二遍发现：覆盖诊断误计固定提醒 | 程序添加的“未核实”提醒没有文档引用，会被旧启发式算成未标引用正文。 | `citation_coverage_diagnostics`仅剔除本地固定前缀；新增回归证明真实未标引用正文仍然被计数。 |
| 第二遍发现：旧输出百分比缩放不明 | 仅凭ratio列名乘100，会把旧SQL已乘100的结果再次放大；缺SQL时也无法判断单位。 | 复用 `qa_agent.sql.result_format.percentage_formats`读取SQL AST缩放；metadata仍优先；缺SQL或不支持投影时保留原值，不猜单位。 |
| 金额与百分比区别 | UI仅格式化副本，原始`result.table`不变；旧响应推断同时检查任务、投影和明确比例列名。 | 金额、计数、NULL等保持原值；测试覆盖分数值、SQL已乘100、负增长、金额与缺SQL。根任务负责新metadata产生端的指标语义。 |
| 改写依据 | UI读取实际选中候选的匹配分数，并用中文匹配名称显示。 | 没有实际分数时不填造0.97；主流程不展示候选ID，诊断面板保留真实工具记录。 |
| 真实截图与版本归属 | 新脚本在发问答请求之前，校验保存PID属于项目服务、服务启动时间晚于当前运行源码修改时间，并记录源码哈希。 | 这是启动时间及磁盘源码证据，不是远程已加载模块证明。根任务应另保存统一重启与冻结记录。脚本的prepare模式只有计划，0模型请求、0截图。 |

第二遍实际命令：

```powershell
./.venv/Scripts/python.exe -B -m pytest tests/test_oct12_rag_ui.py tests/test_d2_rag.py tests/test_rag_core.py tests/test_d2_ui.py tests/test_d3_clarify_ui.py tests/test_ui_app.py -q --junitxml=eval/artifacts/oct12/rag-ui/module-tests-v2.xml
```

实际输出：`83 passed in 6.05s`。其中模型和HTTP夹具是模块及界面测试，未将其写成真实模型结果。运行日志：[module-tests-v2.log](module-tests-v2.log)，JUnit：[module-tests-v2.xml](module-tests-v2.xml)。第一次记录：[verification-record.json](verification-record.json)。截图步骤计划：[plan.json](../ui-live/preparation/plan.json)。

真实rag-03若直接通过、重生成后纠正、或返回证据不足，必须如实记录这次观察；不能为了生成“未核实”截图而篡改原文、检索结果或给模型答案指令。没有实际触发该分支时，只能依据模块回归证明降级行为，并在真实界面报告中写“本次未观察到该分支”。
