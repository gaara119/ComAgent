# sql-19 staging候选独立第二审核

结论：第一版候选存在指标缺口旁路，暂不建议应用。第一版候选SHA256为 `e2d6f2760cb5558a1f8376ebd197e1633ed15a198310e58a9ef25e755d121590`。原始独立探针见 [ai-review-pass-2-probes.json](ai-review-pass-2-probes.json)，脚本见 `eval/artifacts/oct12/rag-ui/sql19-second-review-probes.py`。

核验范围是已冻结业务源码以外的 `extractor_candidate.py` 和 `candidate.patch`，以及原有18个隔离测试。没有修改业务源码、提示词、别名、gold或审核签名。四个实际本地探针采用明确声明的固定模型fixture，模型调用0次、保留题0次，不能计作实跑模型成绩。

正向纯属性取数句“按姓氏降序取前5位客户，返回编号、名字和姓氏。”正确转为lookup且保留N和order。另三句“统计营收总和”“按 revenue 再排名”“前5位客户的支出”也被第一版规则匹配，将原fixture ranking/metric=None转为lookup，RuleEngine给L0且不再报告业务指标缺口。这证明有限业务词黑名单不能证明余文只有属性取数。

建议将可恢复的范围改为完整纯属性查阅句式，允许真实客户名字、姓氏、编号的明确方向和TopN，以及纯字段投影或相同值的明确属性tie-breaker；任意未识别余文继续走模型原业务任务。调用端还应排除明确的其它rank_object，避免覆盖另一对象的任务。新候选需保留原版证据并重新独立核验，不能把第一版现有18项通过视作无条件证明。

以上为AI代码预审意见，没有A/B人工签字或批准日期。
