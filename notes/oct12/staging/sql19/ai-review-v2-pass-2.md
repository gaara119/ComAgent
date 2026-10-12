# sql-19第二版候选独立复审

AI建议有条件通过句式收窄，暂不直接应用第二版；需再限定模型top_n与主句明示N一致。候选SHA256为 `eef79cdcf2066118c7548940616d65d6206413bc9f310cec86b5c3da8408ddab`，对应 `extractor_candidate-v2.py` 和 `candidate-v2.patch`。

已读取完整白名单逻辑、调用条件、字段schema检查和43项候选测试。新逻辑对每个非空分句使用fullmatch，主句仅含真实客户属性、明确方向和前N客户，余句仅允许真实姓名/编号的投影或属性tie-breaker，不识别的余文回到原业务任务。调用限定ranking/metric=None、rank_object属于空或客户；其它对象与已有指标保持原值。并未自动安装业务指标。

实际独立7项fixture探针全部通过。第一版的营收、revenue、支出三种旁路在第二版都保持ranking，并由RuleEngine返回L2、missing:metric；artist对象与未知投影也不被覆盖，纯字段投影及tie-breaker可恢复lookup。原始结果见 [ai-review-v2-pass-2-probes-retry.json](ai-review-v2-pass-2-probes-retry.json)。这是本地固定模型fixture结果，模型请求0、保留题0，不是实际模型成绩。

第一次探针运行因审核脚本将dataclass ClarificationIssue当作Pydantic对象序列化而失败，原因与修复独立保存为 [ai-review-v2-probe-error.json](ai-review-v2-probe-error.json)，保留原空stdout文件，不将该错误误记为候选业务失败。

仍存在边界：白名单能证明题面明确N，但当前调用没有证明模型top_n同一个N。若模型提取错N或未提取，仍转lookup并保留错误/缺失N；故建议第三版只在模型N与主句N一致时纠偏，其它保留原任务，不自动改N。此窄修复还不独立证明模型order全部正确；原始明确题面、SQL校验与端到端结果需继续共同核验。新候选需要独立证据，第二版文件和报告保持原状。
