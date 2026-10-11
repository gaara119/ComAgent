# V0-001 / sp03-03 单案例独立语义观察

本次实际地区追问有业务和运行时指令依据，不能判为模型凭空增加地区归属条件。固定参考标签将客户所在地当成唯一地区解释，原题及已确认材料没有给出足以排除账单国家的依据；这一点应单独列为标签问题，不能为了系统通过在V0中改分。

本报告只读核对已完成的一个合成开发案例。原题、标准、controller、原始score、业务源码和prompt均未修改；本报告没有额外问答预测或数据库查询，也不推断尚未完成的V0总体成绩。

## 原材料与实际输出

- 固定题库 `data/cases-v6-reviewed.jsonl`，第13行、`id=sp03-03`：原题“2024年巴西的销售额同比2023年增长了多少？”，L0/execute，地区reference为`customer.country=Brazil`，history为空、missing_conditions为空、controller=null。
- 实际请求 `runtime_eval/runs/V0-001/cases/sp03-03/turns/000/request.json` 只有原题、sql/chinook来源和独立会话；没有传入参考地区、gold或期望L0。
- 实际响应 `turns/000/response.raw.json`，body.trace_id=`e714819b-b5b0-48d4-a3ee-0668800bc6c5`：NEEDS_CLARIFICATION/L2，问“国家按客户所在地还是发票账单国家？”，只有region_scope未决，SQL/table为空；2024当前期和2023基期已正确保存，并未因为比较任务就一概要求补年份。
- 实际ValueLinker为mention_count=0、bindings=[]，没有先自动确定客户国家。原始P2返回了Brazil及泛country说明，但未选真实字段；程序以verified bindings覆盖filters后仍为空，尚未执行查询。
- 已直接读取原provider `runtime_eval/provider-captures/V0-001/4b3903bd79964cbaafb76637f2d4254e.json`：system明确写“发票销售额+国家但未明确归属时region_ambiguous=true、region_scope=null”，动态user的verified_value_bindings为空；模型实际输出region_scope=null、region_ambiguous=true、time_ambiguous=false，没有凭空选customer.country或billing_country。一次真实模型尝试5468 tokens。

## 三个对象分别判断

| 审核对象 | AI判断 | 依据与限制 |
|---|---|---|
| 模型是否凭空补选地区字段 | AI建议通过 | 原provider没有填唯一地区字段，原题没有客户所在地/账单国家文字；真实catalog两个字段不同，模型遵循实际system保留歧义。该结论仅针对地区追问依据。 |
| 地区L2是否具有业务依据 | AI建议有条件通过 | 已确认general.region明确字段含义不同；销售额SUM(invoice.total)定义只决定金额粒度，不决定哪个国家字段。缺少泛称“某国销售额默认客户所在地”的登记规则，暂停选择合理；最终归属默认是否存在仍需团队确认。 |
| 固定参考L0/唯一客户国家 | AI发现错误 | 同比当前期/基期齐全不能消除独立地区自由度。reference_intent直接补customer.country，但input/history没有该限定；原两遍AI预审只重点解释同比可推导基期，遗漏地区唯一性。该结论不改本次冻结成绩。 |
| 该解释下标准SQL | AI建议有条件通过 | 明确采用客户所在地后，gold的客户JOIN、2024/2023半开CASE SUM和NULLIF基期符合该解释；本轮未重跑SQL，既有gold 1.7不得改称本轮实测。 |
| 控制器未答 | AI建议通过 | controller=null、允许补充为空；控制器不能从reference/gold偷取客户所在地来替用户做选择。当前region_scope本身是支持的键，未答来自标签未提供允许补充，并非匹配能力错误。 |

已确认口径来源：`data/rules/metric_definitions.json` 的general.region及sales_revenue；生成侧副本 `materials/generation_materials.json` 含相同口径。`data/aliases/aliases-d2-reviewed.csv` 第16–17行批准的是`巴西/巴西联邦共和国→Brazil`的customer.country别名关系。别名关系说明该词在该字段的候选值，不能单独替代当前问题需要的业务地区归属决定；数据快照两字段碰巧相同也不能合并语义。

## 证据归档限制

`turns/000/provider-evidence.json`记capture_path_rejected，checkpoint记provider_captures_archived=0。该原provider文件确实存在、trace一致并已读取，因此本轮语义观察有原始模型证据；旧归档拒绝记录仍保留。此为归档观察路径限制，与模型地区判断和冻结score分别处理，不能把旧归档事件改写成功。各证据文件实际SHA及具体JSON位置保存于同名JSON，避免只看到“有provider证据”标题就宣称已读。

## 后续条件建议

先完成V0并保留所有原分。若后续要测试“无歧义完整同比L0”，应在独立新版本显式写客户所在地国家或账单国家；若要测试地区L2，应在独立新版本给该字段合法模拟补充。若团队确认泛称地区的对象限定默认，则先记录该业务决定再评估prompt表达，不能为这一个冻结题的分数取消现有地区规则。

暂不能声称prompt-only V1能修复该案例。标签归属依据、程序字段范围下没有抽取巴西、真实用户补充后的国家保留，是不同审核对象；本轮只观察初始暂停，没有预测补充后结果。人工状态保持pending_human_review，不填写签名或日期。
