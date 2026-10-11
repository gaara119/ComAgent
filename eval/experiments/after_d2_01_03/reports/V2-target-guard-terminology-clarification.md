# V2 观察字段术语补充核验

原 [目标观察 JSON](../runtime_eval/runs/V2-001-target-guard-observations.json) 的 `V2_sp03_27_denominator_guard_rejected=true` 字段名过于笼统。其实际错误为“分子客户归属没有实际用户原文证据”，属于**已核验中文分子来源未被跨轮继承**，不能解读为真实分母缩窄或无用户分子依据。

原 `sp03-27` 的用户已经给出“巴西居住客户的销售额”，当时 value linking 核验 `customer.country=Brazil`；下一轮补分母后，最终 SQL 的国家只在 CASE 分子内，分母为同期间全库 `SUM(total)`。此时新守卫未取得之前的中文 surface 而拒绝。实际最终查询未执行。参见 [V2 该题 checkpoint](../runtime_eval/runs/V2-001/cases/sp03-27/checkpoint.json) 和 [独立逐项 AI 审读](v2-task03-semantic-review.md)。

明确更正解释：`numerator_provenance_guard_rejected=true`，`observed_denominator_country_filter=false`。本补充保留原字段和原始证据字节，没有覆盖 checkpoint、HTTP响应、score 或原观察文件。最终采用 V1，V2 已回退，故该新增拒绝不在当前运行版本中。
