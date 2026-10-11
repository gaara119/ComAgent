# AW第二轮开发回归：新增AI观察

实际严格EX：20/21（95.24%）；原run1的21/21保持原文件。

**aw-07参考答案：AI建议有条件通过。系统业务答案：暂不能确定。**

产品编号在实际目录中可能指productid主键，也可能指productnumber业务编号。原gold选productid，run2真实回答选productnumber并按该列处理同价顺序。两种字段在本题结果并不相同；题面没有明确字段，因此严格EX保留不匹配，但不能据此直接断言系统业务答案错误。

两遍AI审读漏检该字段歧义；原意见原文件保留，不反写成当时已经发现。当前不改题面、标准SQL、标准结果、别名、prompt或系统代码。

人工需明确productid还是productnumber及同价排序字段，修订决定另行记录。strict20/21先如实保存，不能将两种编号偷偷视为等价或仅为通过改gold。

[实际run2报告](../d3-aw-live-dev-run2/report.json)、[真实请求/回答](../d3-aw-live-dev-run2/responses.jsonl)、[目录](../../../data/catalog/adventureworks.yaml)、[新增判断机器记录](aw-run2-additional-observation.json)。

候选gold表覆盖21/21，实际AW执行21/21，schema阶段平均178.0ms。

本观察仅读取已保存文件；没有发起新模型预测或只读SQL，没有保留题内容，没有人工签字或确认日期。
