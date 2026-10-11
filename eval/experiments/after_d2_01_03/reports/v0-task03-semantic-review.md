# V0 专项03逐项语义AI预审

本报告只审核 V0-001 原始材料。30 道均为本轮合成开发题，其中原可评分 23 道、原排除 7 道；已实际读取 51 份响应原文及 69 份原始 provider 记录，全部响应与 checkpoint 一致。没有调用问答 API、没有新增数据库查询，也没有修改业务源码、prompt、规则、别名、题库、控制器、scorer 或人工记录。

原自动分数保持 **专项03：4/23；全部：18/49（18通过、22失败、9 AI_pending）**。下方是分开审核参考与实际行为的 AI 判断，不能将这些判断当成重新算出的EX，也不能把原未评分题重新纳入。

| 审核对象 | AI建议通过 | AI建议有条件通过 | AI发现错误 | 证据不足 |
|---|---:|---:|---:|---:|
| 参考答案、分类及控制器依据 | 16 | 7 | 7 | 0 |
| 系统已有真实行为 | 12 | 7 | 11 | 0 |

证据齐全不等于所有最终问答已运行：控制器中止、API失败后的依赖步骤按实际未运行记录。每项的完整原始文件SHA、JSON位置、原评分和控制器事件见 [JSON明细](v0-task03-semantic-review.json)；可复查紧凑原始材料 [已读证据摘录](v0-task03-evidence-read.json)。

## 先处理的真实问题与证据边界

- **22：比例分母被修复链缩成分子。** 首SQL已经正确使用France CASE分子和全库分母，守卫要求全局WHERE France后得到100.00，正确参考约7.677%。这是业务错误，不能当百分数格式问题。
- **18：程序把两年变成一年。** provider抽取2021–2022正确，日期规则覆盖为仅2022。
- **23、26：合法追问转成新任务。** ‘改看2024’及‘指标换成平均每张发票金额’未路由patch，丢掉旧对象/期间/增长任务。
- **28：明确替换对象被取消词守卫拒绝。** 用户改成流派Metal，不能继续保留Metallica条件以凑通过。
- **27：patch职责错位。** 只回答分子却修改全局国家和filters，不set numerator；这是本轮有直接依据的prompt-only候选。
- **03、13、21：参考地区范围新争议。** 未明示客户/账单归属，标签却固定唯一范围；不能为标签通过撤掉有依据的澄清。
- **04、19、26、29：原列数评分的限制。** 核心值或已正确子轮可能只是多出名称/基期列；但18的日期丢失、26的最终追问失败、30的Top1/Top10条数差别仍是真实独立问题。

## 逐项结果

| 原编号 | 原分类 / 评分状态 | 参考AI判断 | 实际行为AI判断 | 原V0结局 |
|---|---|---|---|---|
| sp03-01 | L0 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-02 | L0 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-03 | L0 / 原可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-04 | L1 / 原可评分 | AI建议有条件通过 | AI发现错误 | finished |
| sp03-05 | L1 / 原排除 | AI建议有条件通过 | AI发现错误 | finished |
| sp03-06 | L2 / 原排除 | AI建议有条件通过 | AI建议有条件通过 | controller_unanswered |
| sp03-07 | L2 / 原可评分 | AI建议通过 | AI发现错误 | controller_unanswered |
| sp03-08 | L2 / 原可评分 | AI建议有条件通过 | AI建议有条件通过 | controller_unanswered |
| sp03-09 | L2 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-10 | L2 / 原排除 | AI发现错误 | AI发现错误 | finished |
| sp03-11 | L0 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-12 | L0 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-13 | L0 / 原可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-14 | L0 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-15 | L0 / 原排除 | AI发现错误 | AI建议通过 | finished |
| sp03-16 | L0 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-17 | L0 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-18 | L1 / 原可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-19 | L1 / 原可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-20 | L1 / 原排除 | AI发现错误 | AI建议通过 | finished |
| sp03-21 | L2 / 原可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-22 | L2 / 原可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-23 | L2 / 原排除 | AI建议有条件通过 | AI发现错误 | finished |
| sp03-24 | L2 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-25 | L2 / 原排除 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-26 | L2 / 原可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-27 | L2 / 原可评分 | AI建议通过 | AI发现错误 | api_failed |
| sp03-28 | L2 / 原可评分 | AI建议有条件通过 | AI发现错误 | post_completion_incomplete |
| sp03-29 | L2 / 原可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-30 | L2 / 原可评分 | AI建议有条件通过 | AI建议有条件通过 | finished |

### sp03-01

原题：Chinook 里2020年全年的发票销售额是多少？如果那一年没有发票记录，请直接说没有可用记录，不要用0代替。

**参考：AI建议通过。** 2020年、发票SUM(total)、无记录保留NULL均明确；存档gold为NULL。

**系统实际：AI建议通过。** 实际半开2020期间SUM返回NULL，说明没有可汇总的值，没有变为0。别名、字符串日期与DATE常量不改变此timestamp列的边界含义。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 11: sp03-01；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-01/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-01/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `1e0f47a3804ad7c6d06e5eb2de11a327f08c134a796090d8982aeee0520ee69a`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-01/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-01/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `4693a2039ab3f7d57e6cd0392610a46875fa61e54d536172d227e16df4c15f90`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/f065dd572cbd41f98e5cfb520c17680c.json](../runtime_eval/provider-captures/V0-001/f065dd572cbd41f98e5cfb520c17680c.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `497cc85cbbe0240754bc9775563ee9b95f57a47c05acf3cb4b2863127a23244c`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/dd293c8395564e0a823769e03a509fd7.json](../runtime_eval/provider-captures/V0-001/dd293c8395564e0a823769e03a509fd7.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `5e90bab73cff73e1d530de65b9b68f89afe6fb6713116cdfc3d30e0e400e72ae`。

需人工确认：确认NULL展示措辞即可。 人工状态保持 `pending_human_review`。

### sp03-02

原题：How many customers reside in France?

**参考：AI建议通过。** reside明确customer.country=France，客户COUNT正确，存档5。

**系统实际：AI建议通过。** 实际customer.country=France COUNT(*)=5，L0直接执行，没有账单国家替代。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 12: sp03-02；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-02/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-02/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `f83e0bdb100f6bfc91b580fe382b0838ee5403172e0118e9634cec3179ad0f92`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-02/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-02/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `b6a2e6a95350378a490934a1a7fa5e3d57cd577aed1514349e5ec752297f264c`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/d9d2bc6833ef4eeb9284846e6d07fdc5.json](../runtime_eval/provider-captures/V0-001/d9d2bc6833ef4eeb9284846e6d07fdc5.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `23118f70bcaf05b4a1049639875312ca23f32465de5f8d42d832364b7fae6917`。

需人工确认：无新增口径事项。 人工状态保持 `pending_human_review`。

### sp03-03

原题：2024年巴西的销售额同比2023年增长了多少？

**参考：AI发现错误。** 题目仅‘巴西销售额’，未给客户所在地/账单国；固定L0和唯一customer.country gold缺业务依据。gold在明确客户归属条件下计算本身正确，不能据当前两国字段相等证明唯一。

**系统实际：AI建议有条件通过。** 实际仅问region_scope，保留2024/2023且没有SQL；这是有依据的业务澄清。controller无合法地区补充，无法完成；不能按唯一gold确定系统金额错误。

实际请求轮数 1；执行SQL轮号：未执行；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 13: sp03-03；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-03/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-03/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `ac9a5b4a4e0e569de261e8de4c4b03e094cf693824ba139a91fafba93506745d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-03/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-03/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `00d730ab57d7e90293075edf1fbda0ddb894716f44677a320bbdbc91de5d05a7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/4b3903bd79964cbaafb76637f2d4254e.json](../runtime_eval/provider-captures/V0-001/4b3903bd79964cbaafb76637f2d4254e.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `4880c7d1a554957d3504ca44a3f03d01c9d00f85aac0b4ce9f05eaf31541c4ae`。

需人工确认：明确这类国家销售额是否必须问归属；既有材料没有国家默认。独立单案例报告保留。 人工状态保持 `pending_human_review`。

### sp03-04

原题：2023年按销售额排名最高的曲目。

**参考：AI建议有条件通过。** 曲目明细金额、2023、Top10登记默认与gold匹配；L1默认实际是条数，输入已经明确销售额。‘最高的’是否接受默认10及开关应对应条数，需要明确，不能因L1强行把显式销售额当缺失指标。

**系统实际：AI发现错误。** SQL/核心10个track_id与1.99逐项符合gold，多加track_name合理；自动列数fail不是金额错误。但metadata.clarify.switch=null，没有该L1默认的可切换控件；本轮没有真正点击开关。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 14: sp03-04；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-04/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-04/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `2143c6733663048a96168420c8ec8d45e5deba5517b2c928333ae6b803db33f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-04/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-04/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `039dc19fddf4f599116b501caffb72fdcdbecb5ffed50427583da1ac23bcc279`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/fdef97271348481c87e39523eff3fe50.json](../runtime_eval/provider-captures/V0-001/fdef97271348481c87e39523eff3fe50.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `7a74a2d86a91876a0fced128d66ecfe9ce3702d3c0f2c86855914c88f7e23f0f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/f8a3f7b5960a403ea0be9395cc5892d6.json](../runtime_eval/provider-captures/V0-001/f8a3f7b5960a403ea0be9395cc5892d6.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `2c0eeae1d3cca1b2e83e3e725815bf22f47cd0bfdb7cd030955814b9747e3683`。

需人工确认：确认TopN默认的切换交互和该题自然语言条数含义；不改原评分。 人工状态保持 `pending_human_review`。

### sp03-05

原题：2007年最受欢迎的10首爵士曲目是哪些？

**参考：AI建议有条件通过。** 2007明确且无数据应空结果；登记热门数量默认支持L1。旧两遍争议导致原scorable=false，仍保留；空结果不意味着应该补最近年份。

**系统实际：AI发现错误。** EMPTY_RESULT及默认声明正确、Jazz和2007均保留，开关可用性有元数据；SQL并列键实际track.name，而已确认规则是track_id。空数据掩盖该排序差异；未实际点击开关。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 15: sp03-05；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-05/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-05/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `082300f8aa26bc99da62be7d8f4e9b777550532cd8ff7c52c97676b2c727a0fa`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-05/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-05/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `4768e37d62e80afebe9051ed69ccb42db42ca335fc79b5e2fbda5c8ea8a79771`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/8f9cc3393cd441c693dfd46fb9f0868d.json](../runtime_eval/provider-captures/V0-001/8f9cc3393cd441c693dfd46fb9f0868d.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `054444708fdc56b526ccaaa87ad4bbd04e022db6cc70dfda41f5455bc0c00df2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/bc7b4bde95d149c0a48051d20ad3ef8b.json](../runtime_eval/provider-captures/V0-001/bc7b4bde95d149c0a48051d20ad3ef8b.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `33c731f66655311022ef8f534c1d8d87d6ba75aab131fe57bacfa671f6164e3a`。

需人工确认：保留原待确认；确认当前空年是否仍作为有效题，稳定ID排序不能靠空结果认定通过。 人工状态保持 `pending_human_review`。

### sp03-06

原题：销售额同比增长多少？

**参考：AI建议有条件通过。** 销售额与同比已明确，只缺当前期间；gold在补2024后合理。离线回答含current与base，与逐key控制器及重复time标志卡粒度失配；旧排除仍保留。

**系统实际：AI建议有条件通过。** 初次L2缺期间正确，附加time_ambiguous及current两条近重复；controller在发送前因bundled拒绝，实际只有初始请求，无最终SQL。不能将未发送的补充写成系统实测失败回答。

实际请求轮数 1；执行SQL轮号：未执行；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 16: sp03-06；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-06/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-06/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `6ed68915580ce6060e4294cb1e24acb60ff634f96eb762f1b9056dcc4472b0b9`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-06/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-06/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `0dbef0e6e0b64bece84832da8afcec2cad56b6fc641da63317a717fb7e2b0cfd`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/0646f9d4c2994b65862649a84876de09.json](../runtime_eval/provider-captures/V0-001/0646f9d4c2994b65862649a84876de09.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `4863363599a06c90f54f1f47723a93aded3db7d931ebd5825cd841173d7ffc2e`。

需人工确认：确认一次补充同一时间条件是否可以包含明示基期；冻结controller本轮不动。 人工状态保持 `pending_human_review`。

### sp03-07

原题：2024年账单国是美国的发票销售额占比是多少？

**参考：AI建议通过。** ‘账单国是美国’明确billing_country；分母仍缺，应问分母。补全库2024后gold FILTER分子/同期间全库分母正确。

**系统实际：AI发现错误。** 实际问region_scope而未问denominator。原provider正确billing scope却程序explicit_region_scope不识别‘账单国’，覆盖为歧义；provider还先猜全部发票分母，虽然程序后续清掉。controller没有地区补充而止步，未执行。

实际请求轮数 1；执行SQL轮号：未执行；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 17: sp03-07；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-07/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-07/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `a4189a50ddc5f950133df2c13d29b717006f75575cca98a41d6bac00fd481af0`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-07/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-07/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `be5088e9bd2426f07ca6c61ab5620a8c3859a474bbe9bbefdcb434e6193ba621`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/bc63572d0228412d9e61013453d86abf.json](../runtime_eval/provider-captures/V0-001/bc63572d0228412d9e61013453d86abf.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `6a69a3c200589d84e189712992cf66a97152031b31a9521f78b97a743aaeb858`。

需人工确认：保留分子/分母区分；不能通过取消所有地区澄清规避短语覆盖问题。 人工状态保持 `pending_human_review`。

### sp03-08

原题：2023年谁买得最多？

**参考：AI建议有条件通过。** L2缺对象正确；客户/花钱补充后发票金额、2023、Top1 gold正确。补充同含object与metric，当前卡两项均问，单key控制器却拒绝整条；这是离线控制器适配争议。

**系统实际：AI建议有条件通过。** 初次实际L2问metric和rank_object；没有凭‘谁’强选客户，符合无全局默认。controller把另一当前卡字段称unasked并拒绝，未向系统提交任何补充；最终正确性未运行。

实际请求轮数 1；执行SQL轮号：未执行；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 18: sp03-08；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-08/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-08/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `dce60421aec2bf2b8021cf7217d85e4cc32d9153ccd3fd68f91d0a4111955945`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-08/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-08/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `eb4ce44d192e0b311311aa587025663788cab12fa90616b0cf76b55fc1e73ca4`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/8d52d1bf6b4f439fa121f4b496f7b6e5.json](../runtime_eval/provider-captures/V0-001/8d52d1bf6b4f439fa121f4b496f7b6e5.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `0cdfce81692237daf22261f6c29b5b20d4f35656119c3fe760e737aac88eb555`。

需人工确认：确认控制器只准一个issue还是允许一次回答卡内多个问题；原版本标签/score不动。 人工状态保持 `pending_human_review`。

### sp03-09

原题：2024年摇滚曲目卖了多少张？

**参考：AI建议通过。** 摇滚两候选关系非自动绑定；用户选择Rock后2024销售数量SUM(quantity) gold164正确。

**系统实际：AI建议通过。** 初始保留Rock/Rock And Roll两候选L2；实际稳定choice_id选择Rock后SQL关联genre且2024半开日期，数量164。DATE/字符串AST区别不改变语义。

实际请求轮数 2；执行SQL轮号：[1]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 19: sp03-09；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-09/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-09/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `40bf414b8dfc3b50d548ee309d114a6436958a3a99553d48464b6de963bb449d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-09/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-09/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `ab8db7f8e908d23f74c9690bd49211a8366b514b7f365d6e5adac65f1c92be69`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-09/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-09/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `19345b435e96821faa7e1ccc15d8af4d5807d5ccf84d3e277b157707410da32d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/157a4c0aeaf4428390b94c9d552781e0.json](../runtime_eval/provider-captures/V0-001/157a4c0aeaf4428390b94c9d552781e0.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `d49ee0a556e5c7d7aa3340d18ae5914aaa6f4956902c295ecfaa0a3757970e3a`。

需人工确认：无新增业务事项；此题是实际按钮闭环，不能与自由补充混称。 人工状态保持 `pending_human_review`。

### sp03-10

原题：2024年巴西的客户有多少？

**参考：AI发现错误。** ‘2024年巴西客户数’未明确在2024购买的活跃客户、年末存量或新增客户；customer表无创建日期。gold擅加年度购买活动定义，不能从复购规则推广一般客户数。旧排除保留。

**系统实际：AI发现错误。** 实际只COUNT全部Brazil客户=5，SQL完全不使用2024，intent却显示2024；未经解释就忽略显式日期。正确值究竟5/4不能确定，应先澄清日期含义，不能把gold活跃客户4强作唯一。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 20: sp03-10；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-10/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-10/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `2596b3c8a33715da165b5477d7cd871bea87dc99985c3428f248e6b368e33b1c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-10/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-10/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `67c13c12669711a6d3d65e17f4d30a7b49fa4feca7a1ac4cede14a7ee064fd2b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/987aa97603d94c92a815e17ec97e1b31.json](../runtime_eval/provider-captures/V0-001/987aa97603d94c92a815e17ec97e1b31.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `9fe6f9d4347c9b7dc6a227ad29e61d0155d5ba7a2c054be1200dacd058c248cc`。

需人工确认：优先确认客户数的时间语义；不增全局活跃客户默认。 人工状态保持 `pending_human_review`。

### sp03-11

原题：How many customers reside in the USA?

**参考：AI建议通过。** reside USA明确客户所在地，COUNT客户gold13正确。

**系统实际：AI建议通过。** 实际country=USA COUNT13，直接L0，与字段含义一致。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 41: sp03-11；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-11/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-11/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `2e241e97e540ec39f679ddda0197c92342cd48cf6aa25d7608bc88714d744c11`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-11/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-11/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `2deb03bdfefe0c8dea1de4b7e8608fab169aaa11717b0e954fb13680a35a1162`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/2d2db0ca76d84f0596943daeb00fa88e.json](../runtime_eval/provider-captures/V0-001/2d2db0ca76d84f0596943daeb00fa88e.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `7e3e85f747b05ec5af38792ebb2ac73d74434ae2439af2e3e288d47a2bfa3626`。

需人工确认：无新增业务事项。 人工状态保持 `pending_human_review`。

### sp03-12

原题：意大利有多少客户？

**参考：AI建议通过。** 明确问客户，Italy客户所在地COUNT1，未问金额或账单。

**系统实际：AI建议通过。** 意大利唯一在客户字段链接Italy，COUNT1，L0符合业务。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 42: sp03-12；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-12/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-12/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `cfc4f02fa1ae3a23cf57b973ed12071c8594ad4f3bb7943deae76de8c518a7ae`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-12/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-12/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `9145754b470297be15f6575889b189fe13ec5ec5f33280416b74f612b23683d7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/22796aac77004558b7adff5d0072cac2.json](../runtime_eval/provider-captures/V0-001/22796aac77004558b7adff5d0072cac2.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `4e437d6ee1064bd8dd289101d696e324d6b6e5c928fd5ea743bd218c3761b2bf`。

需人工确认：无新增业务事项。 人工状态保持 `pending_human_review`。

### sp03-13

原题：What was the total invoice revenue for Canada in 2024?

**参考：AI发现错误。** invoice revenue确定金额粒度但‘for Canada’未明确地理归属；唯一billing_country和L0缺已登记依据。该gold在明确账单国后正确，不能由快照同值证明题意唯一。

**系统实际：AI建议有条件通过。** 程序要求region_scope澄清有业务依据且没有SQL；即使模型先选billing，不能据模型选择反过来批准默认。controller没有region补充，最终未运行。

实际请求轮数 1；执行SQL轮号：未执行；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 43: sp03-13；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-13/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-13/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `0b7427823a96226c655d041bec0a1fd98d03b9489aa27634beb80512183261db`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-13/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-13/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `e7fadcbfa1e5dd5387226e1376d68836046c7164537342e3d9c1908e6790ad50`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/9e7937117fc2440f898e6e622f66c197.json](../runtime_eval/provider-captures/V0-001/9e7937117fc2440f898e6e622f66c197.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `c2a1d849fc3f21a38f3e8b080c5d0fba3bc5c08e453fd578e40dacdbfad8ecb1`。

需人工确认：与03统一确认国家金额口径，不因英语invoice上下文自行安装默认。 人工状态保持 `pending_human_review`。

### sp03-14

原题：2022年和2023年，Chinook 每年的发票销售额分别是多少？

**参考：AI建议通过。** 两年逐年SUM invoice.total，2022至2024半开范围、year排序gold481.45/469.58正确。

**系统实际：AI建议通过。** 实际两行2022=481.45、2023=469.58，逐年SUM；EXTRACT numeric年份与gold cast int、自动上限200不会截断两年结果。AST差别需独立语义判断，已读全部原SQL。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 44: sp03-14；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-14/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-14/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `eb49fc80ee9c9a7c93eb1cacd1256e91f0f3960a4f1aee5d6feb485f1ec247c7`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-14/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-14/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `e1acb161e4999f3e3128ce03028836a0a34505fd68a32842a5ff686ad159cbb1`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/43cf0224f0cd4f31b3d6894539e1e42b.json](../runtime_eval/provider-captures/V0-001/43cf0224f0cd4f31b3d6894539e1e42b.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `ae8be7203549ae885b45a926275eaf8b43cdf2c83da2b8bc4a1b49f4fc600804`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/a87d683949b54482bd5a673548e91329.json](../runtime_eval/provider-captures/V0-001/a87d683949b54482bd5a673548e91329.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `2e8705f8e2331ef093eb28255a07bd7725bc57fa551644f12494d58aac2094d0`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/2409507a008d4456b44f19e15439a618.json](../runtime_eval/provider-captures/V0-001/2409507a008d4456b44f19e15439a618.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `79e7878af96ebe657c52429dffc4bffe0db0736cc0e3d437c1ddea1bc532af4c`。

需人工确认：可确认年份展示类型；不改scorer或gold类型。 人工状态保持 `pending_human_review`。

### sp03-15

原题：2009 年和 2010 年之间，哪首曲目最受欢迎？

**参考：AI发现错误。** 热门购买数量使用登记默认应L1，标签L0与business_basis‘默认使L0’错误，原source guard已指出并排除；SQL数量/2009–2010/Top1自身正确。

**系统实际：AI建议通过。** 实际声明购买数量默认、L1执行，范围2009至2011、track_id稳定排序LIMIT1，真实空结果；没有最近年补填。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 45: sp03-15；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-15/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-15/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `aee6b4b765b91a1cada9d9b808334309767c755f3c87f2c0795ec3ba50bd39ab`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-15/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-15/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `cf1954136ce1708ff96b1324aecaa857a2e30b08078939f8b51f1bc8e885209a`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/63adcb233bad4355bfa4a89e4543a915.json](../runtime_eval/provider-captures/V0-001/63adcb233bad4355bfa4a89e4543a915.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `39bee575a4f76edb60b4e4782287657583153421332cecc46240fc7b551a9af4`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/1e741bf6b84445008d27bb98463ee6e8.json](../runtime_eval/provider-captures/V0-001/1e741bf6b84445008d27bb98463ee6e8.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `d6c6e02c09ee2861cbdfdffa2254e5a03e0364a24d553f7833e763c2c929f412`。

需人工确认：原分类争议待人工，继续保持原排除，不新计成绩。 人工状态保持 `pending_human_review`。

### sp03-16

原题：Chinook 里 Jazz 流派的曲目有多少首？

**参考：AI建议通过。** Jazz明确流派，曲目COUNT JOIN genre正确，gold130。

**系统实际：AI建议通过。** 实际genre.name=Jazz、track JOIN genre COUNT130，L0；没有按购买张数代替曲目目录数。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 46: sp03-16；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-16/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-16/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `f29765ec96c5a21e7d86efa874f2d8509aadb23e5394f1a75f8645240bbdff95`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-16/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-16/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `1d59895b600d3d071421cc36728eed6b4029d541c0736bb28eae59168382bbcd`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/e569524ef2d44e40816aed1324d2f54e.json](../runtime_eval/provider-captures/V0-001/e569524ef2d44e40816aed1324d2f54e.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `c41901760e4faa5538aacfbc99f4a6f48bcb76f574759944d06fffee22f2c81e`。

需人工确认：无新增业务事项。 人工状态保持 `pending_human_review`。

### sp03-17

原题：2020年全年复购（至少开2张发票）的客户有多少位？如果没有，请如实输出0。

**参考：AI建议通过。** 明确期间至少两张发票，按客户GROUP HAVING COUNT>=2，再外COUNT；无符合客户输出0，gold符合已确认复购定义。

**系统实际：AI建议通过。** 实际2020半开范围、每客户至少2张、外COUNT0，与SUM NULL行为不同且保持正确。AST别名/日期常量差别无业务改动。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 47: sp03-17；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-17/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-17/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `35c715581b73d81c380222010b4b1913acda211d644d8e4ca21286d88a607080`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-17/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-17/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `8e9804e25f7d5ac4863882230faa753f6badb4ecb0a073de2d0c57dd567623f7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/4af4da241f4e4e88a31de5461e749465.json](../runtime_eval/provider-captures/V0-001/4af4da241f4e4e88a31de5461e749465.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `02daef89b1d44a0e5ec118eb9519463450b956cb963e50203231234daf921cce`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/f6fa8cf6ceed41f5955a356346d6e30b.json](../runtime_eval/provider-captures/V0-001/f6fa8cf6ceed41f5955a356346d6e30b.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `74667c253c99cfefc3166b4a7191d0b7e99de53e72cf445283a372c20dd7c34d`。

需人工确认：无新增业务事项。 人工状态保持 `pending_human_review`。

### sp03-18

原题：2021到2022年最受欢迎的曲目有哪些？

**参考：AI建议通过。** 2021到2022两年范围、数量默认和Top10默认、track_id排序，gold包含两年正确。

**系统实际：AI发现错误。** 原semantic provider明确2021-01-01至2023-01-01，程序explicit_period只匹配带‘年’的2022，覆盖为仅2022；实际SQL和结果只2022，是真实期间丢失。额外name列不应掩盖这项错误。开关只证明可用性，未点击。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 48: sp03-18；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-18/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-18/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `21fd659e604daadc095fb903b996cbe16563bb9c3e0498c258df0d0bbbd97a2d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-18/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-18/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `05547f03a28b622c43fa4772487b03025f308076172540eeec18babdf56f887b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/c44c8968ae154a26a835e3ed0ab23ebe.json](../runtime_eval/provider-captures/V0-001/c44c8968ae154a26a835e3ed0ab23ebe.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `94f4cc60eac35ad2e857074b38e26a38f2e94e384bb264a8a4a3a7e7726de6ac`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/d7b4d54a9c544c0698c43763bb78ad00.json](../runtime_eval/provider-captures/V0-001/d7b4d54a9c544c0698c43763bb78ad00.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `1b0fd1d74da8ade96c1e42ca02af47328e264968eee0d48dc0e2b2f568d1a2cb`。

需人工确认：日期解析改动需后续另立代码任务，不能让prompt输出绕过程序覆盖。 人工状态保持 `pending_human_review`。

### sp03-19

原题：2022年买得最多的客户是谁？

**参考：AI建议通过。** 对象客户明确，已确认金额默认、2022按customer_id合计取金额最高一位，gold45/32.75正确。

**系统实际：AI发现错误。** 实际查询核心及winner45/32.75正确、额外姓名/company不会改变客户粒度；原列数fail不能当金额错。但登记L1金额默认只有声明，switch=null，未提供替代口径控件，实际切换未运行。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 49: sp03-19；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-19/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-19/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `a5dd73d861a172de10f83bb4f20a7835bd166645a7817fa1f179fda6ec4b9b20`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-19/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-19/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `9dfaeb48d7793a5244d15b132d24d4c3026a85d309d5c62d749ef2e8d1be8409`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/5bb5aac2ae8c432aba2833de0010555f.json](../runtime_eval/provider-captures/V0-001/5bb5aac2ae8c432aba2833de0010555f.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `cea5ad5d213dc18a34438d64c9805f191e649e92001c040a1d58b25ed522ee32`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/4620b7a8ac8149908768ee5d348f376f.json](../runtime_eval/provider-captures/V0-001/4620b7a8ac8149908768ee5d348f376f.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `814a485ff49478be354e14fd9b9ca4cefba8086daf5c9e35f95b5fd817a06ef5`。

需人工确认：确认客户金额默认可切换的备选指标是否登记；不能凭空加新业务默认。 人工状态保持 `pending_human_review`。

### sp03-20

原题：2023年按销售额排名最高的艺术家，取前10名。

**参考：AI发现错误。** 输入明确2023、艺术家、销售额、前10名，没有待应用的登记默认；L1标签不成立，原source guard已排除。gold金额/排序自身正确。

**系统实际：AI建议通过。** 实际L0无默认声明且正确取10位艺术家；name附加列合理，明细金额不重复SUM发票头。原排除仍保留。

实际请求轮数 1；执行SQL轮号：[0]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 50: sp03-20；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-20/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-20/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `17b8bc41e6a70178d7d61c82ae445a9287214d82a0e606c4a00c307463daf54d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-20/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-20/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `f830ffcc072131413e102f9dacea908794152e271101bd67dd1e8600b4248408`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/5db26f5f287b4ffd80e7675ae04b5564.json](../runtime_eval/provider-captures/V0-001/5db26f5f287b4ffd80e7675ae04b5564.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `84e99c8a44200186306eaf2502beb08fc317696df31501b0d36357229a7cb310`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/4f24d494ceb547bdb9a2215e2eb880fe.json](../runtime_eval/provider-captures/V0-001/4f24d494ceb547bdb9a2215e2eb880fe.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `5a5f9e9112de04b886693a0f14a2df92bdcc0cbd453a45ce4f59fb3c17f6898c`。

需人工确认：保留分类人审，不按运行结果将scorable改true。 人工状态保持 `pending_human_review`。

### sp03-21

原题：德国的销售额同比增长多少？

**参考：AI发现错误。** L2缺年份正确但参考声称仅缺期间、默认customer.country德国缺依据；controller只有time补充，没有合法地区补充，最终唯一客户归属gold条件不完整。

**系统实际：AI建议有条件通过。** 实际问期间和地区合理，未填最近年或国家字段；controller还因time_ambiguous/current重复字段bundling停止。既未发送年份也未执行SQL，不能断言补年份后会自动正确。

实际请求轮数 1；执行SQL轮号：未执行；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 51: sp03-21；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-21/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-21/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `dcccd6447b7026ebc5b20db04771c3957ba9a8ccf2d1fe1e82b0af627168c5ce`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-21/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-21/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `9d805e2177938c3180c524b0b4adb7489faf8e2e04bd09846f3ed7ef57425d15`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/f372e0d7586746fdba6ef3f5703aded2.json](../runtime_eval/provider-captures/V0-001/f372e0d7586746fdba6ef3f5703aded2.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `5b284628a50a938c1b4f50c4386cb99d7d943b11a91244216209ba9f3ee02646`。

需人工确认：确认地区归属并补合法controller来源后需统一新标签评测；本轮不更改。 人工状态保持 `pending_human_review`。

### sp03-22

原题：2024年法国居住客户的销售额占比是多少？

**参考：AI建议通过。** 法国居住客户明确分子；分母补2024所有发票后应全库分母，gold0.0767700458609930正确且防零。

**系统实际：AI发现错误。** 初次L2问denominator正确，patch set分母正确。首个SQL CASE France分子/全库分母正确；绑定守卫要求全局WHERE France，repair实际加入c.country=France，结果100.00，分母被错误缩为France。不是百分数/小数显示差异。

实际请求轮数 2；执行SQL轮号：[1]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 52: sp03-22；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-22/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-22/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `27a5a4cfc2fcfc09a883a687cf2274693663033790c74dd29eaa23bf6f4864ff`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-22/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-22/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `925917211f222cbc853fbf112aa116c7391354b9a8de474fa6ad39743d00559a`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/8c095fc13fc04192a054be9aa41aaa22.json](../runtime_eval/provider-captures/V0-001/8c095fc13fc04192a054be9aa41aaa22.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `7b8a8c306a367762326af76cb5fea4ae9353bac2431053c6cc4f657bea929907`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-22/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-22/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `b25366178860c622e2dabc38d0ef3b9b704db7cabfe0ba5006da8e2a98d0a100`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/902a90ee817a43eea8cbef5bf2803ce1.json](../runtime_eval/provider-captures/V0-001/902a90ee817a43eea8cbef5bf2803ce1.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `ea87ff8157333387a94f60735d31d39c6e27bb2dea40140a656780a967e37c50`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/e676bb4ea8c141849cfb13e567d6a579.json](../runtime_eval/provider-captures/V0-001/e676bb4ea8c141849cfb13e567d6a579.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `b090a2826d858e3cc7e7f8490d7ba44e5e10184e3bc9334325322617ff75d878`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/c2f80095c35742f790872aff7e2c8076.json](../runtime_eval/provider-captures/V0-001/c2f80095c35742f790872aff7e2c8076.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `ecf9ca77af0451795aa2aba0953092b9a946bce18efc54fe9b84e5f34ca6c519`。

需人工确认：优先处理比例范围模型与SQL绑定校验职责；不能为通过关闭其它问题全局筛选守卫。 人工状态保持 `pending_human_review`。

### sp03-23

原题：2023年谁买得最多？

**参考：AI建议有条件通过。** 与08重复初始输入，原scorable=false保留；客户2023金额及改2024目标合理，但重复题不能重新纳入分母。

**系统实际：AI发现错误。** 选择客户后的2023 winner46/32.75查询核心正确；‘改看2024年’不匹配followup路由，转fresh lookup，全库2024总额477.53/83张，丢客户排名对象及金额默认。额外姓名投影不是真实错误来源。

实际请求轮数 3；执行SQL轮号：[1, 2]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 53: sp03-23；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-23/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-23/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `3ca07f8cac1907119f9e34087a84590ce1797f719d11b117dcad59fe18f98729`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-23/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-23/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `aba77402aab9767dfc42f0a587034b4824f6a644a226a660d680a527e8376f10`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/9728698f81604299b9526a0c93d81850.json](../runtime_eval/provider-captures/V0-001/9728698f81604299b9526a0c93d81850.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `6b00ed3f08cdd7e0e71c799b88e395a67af79fa774197e1aeff94c428ffba288`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-23/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-23/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `d8ac8e82bea1dddb9d958b1cd89964759abc54d7dec3cacdd89503015848ae89`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/0afa7150bfe74594b7d4667b625f4854.json](../runtime_eval/provider-captures/V0-001/0afa7150bfe74594b7d4667b625f4854.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `15d1d902cd28f38cb2e455eedbef00839f1ba8f01e86754f6ffe0d5845321df2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/b17be86fbc6b4175a1de3853969d7fc8.json](../runtime_eval/provider-captures/V0-001/b17be86fbc6b4175a1de3853969d7fc8.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `f0e29beab9c9a657a8a34907ddaff5ddf98377a95f7e680e838162038d31ea5e`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-23/turns/002/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-23/turns/002/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `38de471107540fb99b0e694479b80aaf6181f9e00e0a7b6f9bd4891ebfd0a5c7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/df8d15c88af744c393aca062f19f5332.json](../runtime_eval/provider-captures/V0-001/df8d15c88af744c393aca062f19f5332.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `d604cab396dde68596f9dd91e23c4fa8be5ed06b336eb13532fa4d4be363fb4b`。

需人工确认：后续路由代码任务应覆盖合法改动表达；本轮prompt-only不伪装修复。 人工状态保持 `pending_human_review`。

### sp03-24

原题：2022年澳大利亚的发票销售额是多少？

**参考：AI建议通过。** 国家金额未明归属先L2，用户选customer.country后SUM total/2022/Australia，再改billing_country保值，gold均正确。

**系统实际：AI建议通过。** 真实choice客户归属→0.99，随后真实普通用户改账单归属→0.99；两段实际SQL来源字段分别c.country和billing_country正确且2022未丢。通过依据是字段与范围，不是金额碰巧相等。

实际请求轮数 3；执行SQL轮号：[1, 2]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 54: sp03-24；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-24/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-24/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `7a0a6200dc5128db99eb862fedfdef76a22cdd303067461636d3d37c9f1794c0`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-24/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-24/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `050148d963f015697883a9062836d4c818686b7c9f44b34a46342d3a34035fad`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/8f492aabbe8341d9a895d15745ff0c94.json](../runtime_eval/provider-captures/V0-001/8f492aabbe8341d9a895d15745ff0c94.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `37b0656c065cfa239b1a4557be518da94089a9b41816fd66041f8de7d732687b`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-24/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-24/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `14f8ccf2658caf78ab7390a824fd017fe13651d7209f4bec703f7139a5da1fd7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/ce0bfa7907c447679a5057cef50822c3.json](../runtime_eval/provider-captures/V0-001/ce0bfa7907c447679a5057cef50822c3.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `b815a067fceafa569544adba7d304ca02f7029c696ae3b93e559f13d78e3eb35`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-24/turns/002/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-24/turns/002/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `9030986ba730e8ac6fc5d7fc87c0e95e7cb7f108085b157de9284b7de6ff6413`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/68b5160ccd23420a966f4a81dfdf83e3.json](../runtime_eval/provider-captures/V0-001/68b5160ccd23420a966f4a81dfdf83e3.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `a4ca13005e702cf127f88b974f63969164fe01edac9414666b42abde376140e7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/28d740876a084b0f8b39509af7ffa90b.json](../runtime_eval/provider-captures/V0-001/28d740876a084b0f8b39509af7ffa90b.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `22aec47b4aa81d0ac40959bde2bfe512a032aa0860f2fd10476c150c5571a0c7`。

需人工确认：无新增业务事项；这是实际国家归属迁移闭环。 人工状态保持 `pending_human_review`。

### sp03-25

原题：2024年摇滚曲目的销售额是多少？

**参考：AI发现错误。** 两个允许补充分别指Rock和Rock And Roll，但唯一final gold=Rock，原source guard已指出冲突并排除。value补充还缺column，不能从candidate label强猜字段。

**系统实际：AI建议有条件通过。** 实际保留两候选正确；controller因离线value/column不能唯一匹配停止，没有用户选择及最终SQL。未测的金额与购买数量切换不补写实测。

实际请求轮数 1；执行SQL轮号：未执行；未执行的计划后续追问数量：1。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 55: sp03-25；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-25/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-25/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `1fdac1689ac104f602120f1e1ebe90f8e2e3010f0aef17cf17f6517c7fd76e5d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-25/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-25/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `af6832263a9548c272acf9b8c6020d255908f7bffc581b5822402e89cdd8cabf`。

需人工确认：先统一允许补充与目标来源，未来统一新版标签重评；本轮保持原排除。 人工状态保持 `pending_human_review`。

### sp03-26

原题：同比增长多少？

**参考：AI建议通过。** 同比缺metric/current先L2；补发票金额/2024后计算2024对2023，改2025再换AVG时应保留增长任务及2025/2024，gold正确。

**系统实际：AI发现错误。** metric/年份真实两次补充后增长0.016930正确，多输出469.58/477.53被列数规则误判；改2025增长-0.056436也正确。最后‘指标换成…’转fresh extractor，user上下文没有旧intent，time/comparison丢失并执行全库AVG5.65194，是真实路由错误。

实际请求轮数 5；执行SQL轮号：[2, 3, 4]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 56: sp03-26；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-26/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `a6132e4a6762705e5b75ffb1a7f0380fde725cf9c755e5207e622e081de54475`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-26/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `1251b680d465212eecdede31c76f9b2463d3f41d56b3c760e913b43264af34dc`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/24f1f91d36cd4390ac25c3f29af223da.json](../runtime_eval/provider-captures/V0-001/24f1f91d36cd4390ac25c3f29af223da.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `2f43bc2a58037cb2e46797bcda568946a7c7670201309e84accbff8a1a6717c4`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-26/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `d8956ac1be966aedc9c90652c7598c64b395c5cf0e17221b1ba6a36ec842f54f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/29ac21cb5f1d46b684d64ac70d1b64e9.json](../runtime_eval/provider-captures/V0-001/29ac21cb5f1d46b684d64ac70d1b64e9.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `7ad33863ff89e20a688f193c1b5edc5e5f8c8c613a62edc929328d3818e122ab`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/turns/002/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-26/turns/002/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `cfef886da7a5be05767bc819810bc703a0b6bebca081ff836e4470406f80c3f0`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/e448da6c25784992af0fde658d6f1610.json](../runtime_eval/provider-captures/V0-001/e448da6c25784992af0fde658d6f1610.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `c133189e68fe46556691877b173218fd0c5f46e4797bbbfb256084b45527cbb8`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/turns/003/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-26/turns/003/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `65b1b6af305ea789cda2b814c9404d53d396bc94ac92131583407257333ed482`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/da9c6dfae3e74075984c70f25c6a2c0b.json](../runtime_eval/provider-captures/V0-001/da9c6dfae3e74075984c70f25c6a2c0b.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `d57d5f64988e6625e2af52bc80c2e0793c739e7776f633660cafee636f2cdfa2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/e11e733f2eb04ec4a781b3fa448e35e6.json](../runtime_eval/provider-captures/V0-001/e11e733f2eb04ec4a781b3fa448e35e6.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `7603085e90484f14ec3163b7559efef2deefa0663b702ca66ed0dd03744c913b`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/turns/004/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-26/turns/004/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `35660d10c99f5a449c819ab7176cf838ca7a21336731ddbf18208b54edd70c17`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/9c9dff70c1814ba793b96ed58af5e211.json](../runtime_eval/provider-captures/V0-001/9c9dff70c1814ba793b96ed58af5e211.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `28c04dd97c27a8a61e7dc5f2f1d81a36e4faf536edba28b38aa80b7d41b4bcac`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/cbb150285108478ba8e1406155ccda5d.json](../runtime_eval/provider-captures/V0-001/cbb150285108478ba8e1406155ccda5d.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `3f6931536671bae8f61bd4d9e7531de85edd3890b972f55484c6be16c41456f5`。

需人工确认：代码路由不能由patch prompt补偿；保留前面实际正确子轮与最终真实失败，不混成全程通过。 人工状态保持 `pending_human_review`。

### sp03-27

原题：2023年销售额占比是多少？

**参考：AI建议通过。** 2023比例缺分子/分母，补客户所在地Brazil分子和全库同年分母后的CASE gold正确；后续修改应分别保持局部范围。

**系统实际：AI发现错误。** 真实补充只答numerator，provider却仅set region_scope+addfilters且不setnumerator，并用field/op错误键；程序地区证据守卫拦下FAILED。没有执行denominator补充或两条post，不能写后续实测。

实际请求轮数 2；执行SQL轮号：未执行；未执行的计划后续追问数量：2。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 57: sp03-27；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-27/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-27/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `b792fea5e0d9cf1f4a38189a7d2e600901462b38ebf238ba01423fd7ae4da419`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-27/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-27/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `5864f0e95310681a196d5ab205b601e66b033484743ac518f51f8fae2342fca4`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/a133c52dc94642b6b1058829885d17f4.json](../runtime_eval/provider-captures/V0-001/a133c52dc94642b6b1058829885d17f4.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `48ffff9c3c0fce073f7125300e33bb6db35be89284e3283ffd1cc68d78047224`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-27/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-27/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `01c41d17015dfd5cb84077321c6d76b56843a5972b71e0e238f2c1619d6df6d2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/434e7099872f4d48b4e967476d1722d1.json](../runtime_eval/provider-captures/V0-001/434e7099872f4d48b4e967476d1722d1.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `27c7571074e9967b10dbf9e4184aa95389d6c62274a514527c71c5b40be534ce`。

需人工确认：建议仅patch prompt界定局部分子/分母string及global条件边界；正确patch之后能否生成合规比例SQL仍需真实验证。 人工状态保持 `pending_human_review`。

### sp03-28

原题：2022年金属乐队的销售额是多少？

**参考：AI建议有条件通过。** 初始‘金属乐队’Metallica候选需用户确认，gold明细2022正确；business_basis含‘Metal与Metallic在artist与genre均有候选’不符合当前别名表，需更正依据。L2实际应为候选确认，不必凭band字眼强造genre初始歧义。

**系统实际：AI发现错误。** 候选按钮Metallica后22.77正确；用户明确‘改成流派Metal’，provider正确remove旧artist/add真实Metal，程序却只认取消词，不接受对象替换语义，FAILED，后一2023/Germany步骤未执行。不能保留旧artist交集假称完成。

实际请求轮数 3；执行SQL轮号：[1]；未执行的计划后续追问数量：1。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 58: sp03-28；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-28/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-28/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `ec290a1e8b0e1c6611306bcf46acf30b64a313bd54daf7a69743350421477289`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-28/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-28/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `d2a27f4046cc0d4687c4d8cecff03932774420daaf72e499cfbb93e0f4e7f75b`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-28/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-28/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `affa4cd6f2fc8ee7bf924d76563a599c98e568796acd6f127550f0d50093676b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/961dfb7ab9ec4a05a9717d450a54eb97.json](../runtime_eval/provider-captures/V0-001/961dfb7ab9ec4a05a9717d450a54eb97.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `8e548765fcca0d5d4796a9489bb84b1d694ea9fad69721e25a02004df5e557c6`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-28/turns/002/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-28/turns/002/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `3712c2796c6e095cceec36f2fbf736a9302d038710368dc10f5b86d7f0576416`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/32cc9e2de3e24eb799576ff0f1ee85f4.json](../runtime_eval/provider-captures/V0-001/32cc9e2de3e24eb799576ff0f1ee85f4.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `5cffb40e870e60c48f9aecfd458d46a2746ef0a3a57499e93502f5c792b7a7a4`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/9592be9ab8414255bc710e11b166a48d.json](../runtime_eval/provider-captures/V0-001/9592be9ab8414255bc710e11b166a48d.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `f961d397455b409979971c6359ff43da120150578ce8308ac9991fd8d7cc1f20`。

需人工确认：确认替换对象是否应撤销原对象过滤，程序应做可证明且只删目标的迁移；本轮prompt-only不放宽guard。 人工状态保持 `pending_human_review`。

### sp03-29

原题：最受欢迎的10首曲目是哪些？

**参考：AI建议通过。** 热门10首缺期间先L2，数量登记默认；补2023、改2024、改明细销售额，三段gold语义正确。

**系统实际：AI建议通过。** 实际三个已执行SQL逐项保持正确期间、对象、Top10、track_id排序，最后只换metric，旧默认声明清掉；结果核心ID/指标与参考相符。均多track_name导致原列数判fail，是展示投影差异；只测自由补充修改，未点击L1口径开关。

实际请求轮数 4；执行SQL轮号：[1, 2, 3]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 59: sp03-29；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-29/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-29/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `f661f0fe47a4d2c9326a1880e3ed04abaf3ebd645180f1c8587d1e7ff2aee402`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-29/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-29/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `f7aa715c482a5473dce5906b97ee314d5fcc72fd3b3df6c3e182efacdeda34c7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/c0f817c37066472abff4a971e8fd11d7.json](../runtime_eval/provider-captures/V0-001/c0f817c37066472abff4a971e8fd11d7.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `1a1099b1e9efe53820baa51af08d0cf143c93956b4629d83f6a4b6f65c5bd3c4`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-29/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-29/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `c6d471cdd550c3d6144adf176c8d2664feb539e92bc198a420a8a9ac0de3a520`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/63f3687a2b9848cbaf239b9ed1312c7b.json](../runtime_eval/provider-captures/V0-001/63f3687a2b9848cbaf239b9ed1312c7b.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `850e6fa9b8bb2b4c4476b2b925edf77aa8536f6d39a95bdbe3cdf520e55e2876`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-29/turns/002/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-29/turns/002/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `4bfdd230e3f7cbe62e2b642ce059ebfa9cf15b585a35a6b3f7fb2f23b4f2026c`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/d8e16bf18fd7467d8b70bada8d7a54a8.json](../runtime_eval/provider-captures/V0-001/d8e16bf18fd7467d8b70bada8d7a54a8.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `2b8e87cf02a0d3e1fe84ea2bb27c5e9ba3677b42b4dd3de3351603f68b23975f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/54e67a420acd433588fc1fae7066bcc8.json](../runtime_eval/provider-captures/V0-001/54e67a420acd433588fc1fae7066bcc8.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `4c9e7ccdd9a7f1310f29f0408441109f27bf10b62a1765a859ff300b2e3b7a0d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-29/turns/003/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-29/turns/003/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `47cd086df6a3b3936281669cf85b499e57fac5285be41f6f25733b03d6c0a624`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/c40a30a2da9144bc8dfa39b317bc6424.json](../runtime_eval/provider-captures/V0-001/c40a30a2da9144bc8dfa39b317bc6424.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `1cae3934969f6a9754de964ed1ebc3aab6e1b4d985f80e61093285b12d6aba5f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/f794cc3017db46c1b349c0cce442eeee.json](../runtime_eval/provider-captures/V0-001/f794cc3017db46c1b349c0cce442eeee.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `44dd76f009cbf44d696ecf8ea8458091a1c75e77ace37f5d91f5b9236623fac4`。

需人工确认：确认评分输出契约是否允许解释性附加列；不要因此修改参考业务答案。 人工状态保持 `pending_human_review`。

### sp03-30

原题：谁买得最多？

**参考：AI建议有条件通过。** L2缺对象/时期成立，补金额/客户/2023后的发票聚合正确；参考隐藏goal固定Top1，但实际补充没明确条数，而登记缺TopN默认10。‘谁最多’是否语义自带Top1或按默认10，是参考与规则边界待人审，不能把期望写入prompt强制。

**系统实际：AI建议有条件通过。** 实际三次补充保留metric/customer/year，改2024、改track数量也保留未改条件，Top10延续登记默认。与Top1 gold不同是真实条数差异，不能仅加展示列解释；直到人审确定‘谁’条数口径，不能确定完整语义通过。

实际请求轮数 6；执行SQL轮号：[3, 4, 5]；未执行的计划后续追问数量：0。

证据：
- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](../data/cases-v6-reviewed.jsonl)；位置：line 60: sp03-30；SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/checkpoint.json](../runtime_eval/runs/V0-001/cases/sp03-30/checkpoint.json)；位置：turns[] and controller_events[]; cross-checked against original response.raw.json；SHA256 `f0ffa7ba716edb733a34edaa779f118e879281ac1cf3f0ebb52bf15a3a987676`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/000/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-30/turns/000/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `2f2f90a9afa7c828db23815d576e659d6e415d6178eca802b9f34be57253f7d8`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/61bdc2ec40d6403293eb9f2e24eb4132.json](../runtime_eval/provider-captures/V0-001/61bdc2ec40d6403293eb9f2e24eb4132.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `48097a4642b559c0fcbfd379951016042cfd5719112890954a2583bb86be6521`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/001/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-30/turns/001/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `d00e19b2492b8176efe3e291d2f31befc38e3681cac5683fe297606308a3191b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/c5e739c0cc4d43cab50a08951219ca08.json](../runtime_eval/provider-captures/V0-001/c5e739c0cc4d43cab50a08951219ca08.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `ca6019d19ba87c18f945dc40b6ee9647201f6780560529dccd7e353bead2132c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/002/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-30/turns/002/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `b920fd593ecc28ce030b5f4374dbb89a1bde001263103dcdcbfa06f61966a5c4`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/d0858aa6f8dc43008a68a009caf7f80d.json](../runtime_eval/provider-captures/V0-001/d0858aa6f8dc43008a68a009caf7f80d.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `6e3a6e8040435b9505e17734aa584c28a4662c35accf1a68d18c8ab0e24ec67c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/003/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-30/turns/003/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `3d40d3a8fb56d8f7ae555929aabc7e88ea9c0da1fb639108414a165c2b642f31`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/d70e5ed9b12746fea7637cd0303197bc.json](../runtime_eval/provider-captures/V0-001/d70e5ed9b12746fea7637cd0303197bc.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `b8948b9ce57f093e1b850beb98f133b4bd5fe359fa62e5b5b5edb6389ffc562e`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/004/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-30/turns/004/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `628e0e7e0e8d87cd1d3a4bd3e90ad14b630d46abd69359f2e0d8e232c8b7655c`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/16cec36e592e4776ae2cbbceded12365.json](../runtime_eval/provider-captures/V0-001/16cec36e592e4776ae2cbbceded12365.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `a5a29334976525e959e95bd912ba22c5b9b9c12c843a132022eea4f344f94694`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/da2351df6e4346aaa52d63cc4957181f.json](../runtime_eval/provider-captures/V0-001/da2351df6e4346aaa52d63cc4957181f.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `8a97fab3a675b4d2f81589d739f1b5deb53e56c271d0fe12316e683819369401`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/005/response.raw.json](../runtime_eval/runs/V0-001/cases/sp03-30/turns/005/response.raw.json)；位置：body JSON: status/sql/table/intent/clarification/metadata/steps；SHA256 `c398286d72569935bd97107e6fd3e9ef35147adeb575eb31e93b5e43eb5bb3fe`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/5e562af085c343d5917db5a6cd9e37c7.json](../runtime_eval/provider-captures/V0-001/5e562af085c343d5917db5a6cd9e37c7.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `0872007e9b3a6a664ae8466a647d3c5002ab9e53d43bfb3632c6adbc91d27f07`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-001/60912ea5c21c4d4bad0d0a95cc923c34.json](../runtime_eval/provider-captures/V0-001/60912ea5c21c4d4bad0d0a95cc923c34.json)；位置：request.messages and response.choices[0].message.content; actual trace_id；SHA256 `5368769b3b9f084f5ee7ba83765df26a032601d63bfdb764d1dbf7747bdeeff5`。

需人工确认：优先确定最高一位与Top10默认的适用范围；本轮不强制Top1，不改49分母。 人工状态保持 `pending_human_review`。

## V1 prompt-only 二遍意见

只建议本轮改 `intent_patch.txt` 的同一职责：先看 current_card 实际 issues.field，识别用户本次确实答到哪一项；比例分子、分母是字符串描述。用户只给分子时只set numerator，不把该局部国家提升全局 region_scope/filters、不补分母；反向亦然。filter字典保持column/operator/value协议，evidence必须来自本次原文。sp03-27实际provider支持这项建议。

保持国家默认、规则、别名、模型、controller、标签和scorer不变，交由root完整固定60题V1验证。本报告没有做单题API probe；正确patch仍可能遇到原SQL比例守卫范围限制，不能预写通过。

18、22、23、26、28的已证实问题是程序解析、路由、局部绑定/守卫限制；04/19是控件或登记备选职责。不要用prompt猜旧上下文、保留错误过滤或放宽业务口径掩盖。

## 原始材料与限制

- [data/catalog/chinook.yaml](../../../../data/catalog/chinook.yaml)：SHA256 `4d97a3f7fdfd0c684b544f162e20d2253c4f9c0cd572ba1fcaf40fe439a391b8`。
- [data/aliases/aliases-d2-reviewed.csv](../../../../data/aliases/aliases-d2-reviewed.csv)：SHA256 `aa699e8ef59f5185a0626ed2a9aefb36a1e292bfa2e3c0efd4b0ba5b1ddaef04`。
- [data/rules/metric_definitions.json](../../../../data/rules/metric_definitions.json)：SHA256 `2a0df8d29a4fb5401fd0a5b33a0f44932e00ab005bc674eaaa8b8a33f1df5efc`。
- [eval/experiments/after_d2_01_03/materials/generation_materials.json](../materials/generation_materials.json)：SHA256 `8bb7b1b403972e6b2ae910823842ac3480079e291e5d1b35b24e3dc7de856cf0`。
- [eval/experiments/after_d2_01_03/materials/readonly_live_facts.json](../materials/readonly_live_facts.json)：SHA256 `391487ffea9c12f21f5444369dd2b87b48897ac363a032a6ea107e5507df7b8f`。
- [eval/experiments/after_d2_01_03/materials/source_manifest.json](../materials/source_manifest.json)：SHA256 `5201b756d4e91a8ae5f383ca972740e4afd192997b57751a5a4497b02063b157`。
- [eval/experiments/after_d2_01_03/runtime_eval/V0-freeze.json](../runtime_eval/V0-freeze.json)：SHA256 `8fb2cae0b9cf76973e38b6065d9a3c34a56ea27283f9cdf4631c93eb87eda574`。
- [eval/experiments/after_d2_01_03/runtime_eval/V0-code-snapshot.json](../runtime_eval/V0-code-snapshot.json)：SHA256 `2ccf11827645f0c01c692997c9ef2934a5d08eb9cc76d50679cd22dfb124e280`。
- [eval/experiments/after_d2_01_03/reports/scoring-protocol-draft.md](scoring-protocol-draft.md)：SHA256 `b8f6b7d1d1d531d810a2244f6662db767d9654bc14e1bafa7a10637f918b480e`。
- [qa_agent/clarify/extractor.py](../../../../qa_agent/clarify/extractor.py)：SHA256 `a844301495e785758bc056071b72c921bb29bdd9847cdaaa424abbbe29c5d769`。
- [qa_agent/clarify/rules.py](../../../../qa_agent/clarify/rules.py)：SHA256 `0680480918bf8d0f9448f95a0a0a11481ea3ead2fa04026b37ee9b6f3035ab29`。
- [qa_agent/clarify/service.py](../../../../qa_agent/clarify/service.py)：SHA256 `15b53be775bca2ec3c76a453437ae1568da4c9bba344d02a0a6286389d74cc3d`。
- [qa_agent/sql/validator.py](../../../../qa_agent/sql/validator.py)：SHA256 `ae2e252ddbd2df88c32c60161a851f55a8f190d2b83b4534bfffd00afdbe873a`。
- [eval/experiments/after_d2_01_03/runtime_eval/controller.py](../runtime_eval/controller.py)：SHA256 `04e098fab978fc44c10e560e75b765211653fcc96f10cc679c504202af180fc0`。
- [eval/experiments/after_d2_01_03/runtime_eval/scorer.py](../runtime_eval/scorer.py)：SHA256 `10cc93238b695e194cfaad8627633ad6dc9f989ae4930ba94cfee663c9f9f782`。

- 本轮完全只读原证据，不调用数据库；gold_result是此前只读实跑存档，本轮没有重新执行SQL。
- 本审计核对了schema键/FK/类型及已有结果，不宣称独立实时数据库结果核验。
- V0原provider capture全部直接读到；archiver capture_path_rejected不代表原provider缺失，不能只看归档数量宣布证据不足。
- L1元数据证明选项可用性，不是实际按钮点击试验；本轮03只有09/24/26/29/30相应稳定候选/年份选择真实请求，没有单独L1按钮切换预测。
- 部分参考重新发现争议而原scorable已true：只在本报告单列，原49分母、原分数不变，不据该内容偷偷调标签。
- 所有结论仍是AI建议，A/B签名和人工确认日期未填写。

标签SHA256前后相同：`42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`；V0 score SHA256前后相同：`7f593311e7d4d1a6b3d3d01383b00e95e434d8c681ce029ed240bb8012516cab`。未填A/B签名或人工确认日期。
