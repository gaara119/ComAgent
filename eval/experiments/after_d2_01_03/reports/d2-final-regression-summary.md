# 最终 V1 的 D2 开发集实际回归

最终源码与 safe_config 已核对为 V1，并以新 PID 实际装载。三套原评分入口顺序运行，固定独立开发视图和 evaluator SHA 均未变。原 D1/D2报告不覆盖，保留集预测0。

|测试|真实预测|实际结果|审核/解释|
|---|---:|---|---|
|SQL|35|35/35，探索EX 100%|gold人工接受34/35；仍draft|
|鲁棒|21|20/21，探索EX 95.24%|gold人工接受20/21；一题追问仍占分母|
|RAG|21|金标Hit@5 20/20，完整金标quote 14/20；证据不足处理1/1|19 SUCCEEDED、1 FAILED、1 EMPTY_RESULT；完整答案人审0|

历史D2同视图记录也为35/35、20/21、RAG 19成功/1失败/1证据不足；本次最终代码包含D3链路与V1 P3，历史记录不构成同一代码的正式统计对照。不据相同汇总宣称所有输出语义均未变化。SQL/鲁棒的结果EX也不证明所有NLU绑定和业务SQL逻辑正确。

RAG机械指标验证检索命中及真实索引片段，不能代替完整答案正确性、引用语义支持或人工验收。原问题rag-03的unfaithful失败、鲁棒待核口径单列，不删除失败题。

- [sql原始报告](../regression/final/V1-001/sql/report.md)、[JSON](../regression/final/V1-001/sql/report.json)、[实际命令](../regression/final/V1-001/sql-command.json)、[原始日志](../regression/final/V1-001/sql-stdout-stderr.log)。
- [robust原始报告](../regression/final/V1-001/robust/report.md)、[JSON](../regression/final/V1-001/robust/report.json)、[实际命令](../regression/final/V1-001/robust-command.json)、[原始日志](../regression/final/V1-001/robust-stdout-stderr.log)。
- [rag原始报告](../regression/final/V1-001/rag/report.md)、[JSON](../regression/final/V1-001/rag/report.json)、[实际命令](../regression/final/V1-001/rag-command.json)、[原始日志](../regression/final/V1-001/rag-stdout-stderr.log)。

- [三套串行执行manifest](../regression/final/V1-001/regression-run-manifest.json)、[最终源码装载](../runtime_eval/V1-final-restart-record.json)、[最终415项模块命令](../regression/final/modules-final-V1-001/command.json)、[pytest原始输出](../regression/final/modules-final-V1-001/pytest.stdout.txt)。

真实命令由manifest及各套command文件保存：Python3.12、eval.run_eval、显式dataset、split dev、draft-gold、独立run-id与新output。可复现执行器为 scripts/run_special_d2_regression.py，默认只核验输入，--execute 才发起预测。

全部人审状态保持原值，没有补写A/B签名、审核日期或正式保留集成绩。
