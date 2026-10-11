# V2 专项03逐项语义AI预审

Rejected V2 trial archive; not Final runtime。逐项重读30道原题、标准SQL和存档结果、50份原始响应及74份原provider，本版本响应与checkpoint全部一致。没有新API或数据库调用，没有修改业务、prompt、标签、controller、scorer或人工记录。

原自动分数：专项03 **5/23**，全部 **18/49**。分对象AI结论不是重新计算的EX，原49可评分/11待标签审核以及本组23可评分/7排除保持。

| 对象 | AI建议通过 | AI建议有条件通过 | AI发现错误 | 证据不足 |
|---|---:|---:|---:|---:|
| 参考答案、分类与控制器依据 | 16 | 7 | 7 | 0 |
| 本版本系统实际完整行为 | 14 | 6 | 10 | 0 |

[eval/experiments/after_d2_01_03/reports/v2-task03-semantic-review.json](v2-task03-semantic-review.json)包含原标准SQL、每轮实际SQL/表/意图/卡片、原评分、controller事件及所有证据SHA。

**V2试验边界：** 22合法等价百分比语法被拒绝、27此前真实中文绑定来源未继承；都没有执行结果，不能称分母算错或运行通过。V2已经不作为Final。

| 原编号 | 原分类/可评分 | 参考AI判断 | 实际系统AI判断 | 本版本结局 |
|---|---|---|---|---|
| sp03-01 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-02 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-03 | L0 / 可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-04 | L1 / 可评分 | AI建议有条件通过 | AI建议有条件通过 | finished |
| sp03-05 | L1 / 原排除 | AI建议有条件通过 | AI建议通过 | finished |
| sp03-06 | L2 / 原排除 | AI建议有条件通过 | AI建议通过 | finished |
| sp03-07 | L2 / 可评分 | AI建议通过 | AI发现错误 | controller_unanswered |
| sp03-08 | L2 / 可评分 | AI建议有条件通过 | AI建议有条件通过 | controller_unanswered |
| sp03-09 | L2 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-10 | L2 / 原排除 | AI发现错误 | AI发现错误 | finished |
| sp03-11 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-12 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-13 | L0 / 可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-14 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-15 | L0 / 原排除 | AI发现错误 | AI建议通过 | finished |
| sp03-16 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-17 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-18 | L1 / 可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-19 | L1 / 可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-20 | L1 / 原排除 | AI发现错误 | AI建议通过 | finished |
| sp03-21 | L2 / 可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-22 | L2 / 可评分 | AI建议通过 | AI发现错误 | api_failed |
| sp03-23 | L2 / 原排除 | AI建议有条件通过 | AI发现错误 | finished |
| sp03-24 | L2 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-25 | L2 / 原排除 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-26 | L2 / 可评分 | AI建议通过 | AI发现错误 | controller_unanswered |
| sp03-27 | L2 / 可评分 | AI建议通过 | AI发现错误 | api_failed |
| sp03-28 | L2 / 可评分 | AI建议有条件通过 | AI发现错误 | post_completion_incomplete |
| sp03-29 | L2 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-30 | L2 / 可评分 | AI建议有条件通过 | AI发现错误 | finished |

## sp03-01

原题：Chinook 里2020年全年的发票销售额是多少？如果那一年没有发票记录，请直接说没有可用记录，不要用0代替。

**参考：AI建议通过。** 2020年、发票SUM(total)、无记录保留NULL均明确；存档gold为NULL。

**系统实际：AI建议通过。** 真实2020全年SUM(total)=NULL、L0；CAST DATE边界与timestamp列范围一致，未改0。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-01/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-01/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `e8227649f520c9b831441d33364956787753db90f4830483e29edee9db035183`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-01/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-01/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `86bdb38603528e56abe4f71797efd4a596edbded3fcf35df9c03cf1b4ede2a31`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/ce32406d7d1346c48f6937a9e7caebae.json](../runtime_eval/provider-captures/V2-001/ce32406d7d1346c48f6937a9e7caebae.json)；request.messages/response.choices[0].message.content；SHA256 `919e51263083a467d9b7d67d4f3a8527dee3fc11dc4d4c6b58a18181995a2592`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/b445d2c69bf4403f97835a8279cfc7d8.json](../runtime_eval/provider-captures/V2-001/b445d2c69bf4403f97835a8279cfc7d8.json)；request.messages/response.choices[0].message.content；SHA256 `6f51d23fa30cfc203cdbf35f6e55ea87ee01f445517e37b4e994f3636a494fd7`。

需人工确认：确认NULL展示措辞即可。 状态 `pending_human_review`。

## sp03-02

原题：How many customers reside in France?

**参考：AI建议通过。** reside明确customer.country=France，客户COUNT正确，存档5。

**系统实际：AI建议通过。** 真实France客户所在地COUNT5、L0直接执行。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-02/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-02/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `b10cc9044332a1367008949efeb5e2f77687e58d5b172d6abe373fbf8bb8a657`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-02/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-02/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `7ff3ae216b4ffca496f582f141651d44d3aa97f98e77e3ef1f8f7aae497d7362`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/e10aad1926e840b89f07aeee49dc52c5.json](../runtime_eval/provider-captures/V2-001/e10aad1926e840b89f07aeee49dc52c5.json)；request.messages/response.choices[0].message.content；SHA256 `0c4517a8a8f31d983d1c05eab1c4316a3bf9e2164aa0440c1b0c9f41266911bb`。

需人工确认：无新增口径事项。 状态 `pending_human_review`。

## sp03-03

原题：2024年巴西的销售额同比2023年增长了多少？

**参考：AI发现错误。** 题目仅‘巴西销售额’，未给客户所在地/账单国；固定L0和唯一customer.country gold缺业务依据。gold在明确客户归属条件下计算本身正确，不能据当前两国字段相等证明唯一。

**系统实际：AI建议有条件通过。** 真实L2地区口径澄清保留2024/2023增长任务；controller无地区补充止步。国家销售额归属参考不足，不能把合法澄清视为模型凭空填条件。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-03/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-03/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `9ccfde5cbbc28d0e0ec571f18e7593eeb6127eedee8d128a25d3dc45ecffcb79`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-03/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-03/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `e4054f990406dabccf5b0668b59934954dd8dd81f4d46c33c6d8e1dbf7dbda9c`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/c85f0084913a4255bc6bea59561c45a0.json](../runtime_eval/provider-captures/V2-001/c85f0084913a4255bc6bea59561c45a0.json)；request.messages/response.choices[0].message.content；SHA256 `377ac84e794db3f928284fe3618ba07a4f8e4fe1295214b270b821913cb3d970`。

需人工确认：明确这类国家销售额是否必须问归属；既有材料没有国家默认。独立单案例报告保留。 状态 `pending_human_review`。

## sp03-04

原题：2023年按销售额排名最高的曲目。

**参考：AI建议有条件通过。** 曲目明细金额、2023、Top10登记默认与gold匹配；L1默认实际是条数，输入已经明确销售额。‘最高的’是否接受默认10及开关应对应条数，需要明确，不能因L1强行把显式销售额当缺失指标。

**系统实际：AI建议有条件通过。** 本轮P2把“排名最高”解释Top1、L0，实际明细金额2023 winner2821/1.99正确；参考登记缺N应Top10/L1与最高单数理解存在边界，不只展示列数差异，人工需确定条数。没有L1默认或开关点击，本轮不能照抄V0 Top10。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-04/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-04/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `68aeef297e9bf100bf0947228afd0218e68433b226445dde8fc45e6bcb5c976a`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-04/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-04/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `71787a4920a31140d40223f4115ae2cd6ac75b4b723b5c577f86f07eded19c63`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/0ae672b81de7482d83c1deab0587fc68.json](../runtime_eval/provider-captures/V2-001/0ae672b81de7482d83c1deab0587fc68.json)；request.messages/response.choices[0].message.content；SHA256 `d386b52d9434d905f4a2d8a6431f845cf9ea0ea8d0508f0be3fb055a1b6cc3cd`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/cbdd29ca1df64217b8676a04d8f76ea6.json](../runtime_eval/provider-captures/V2-001/cbdd29ca1df64217b8676a04d8f76ea6.json)；request.messages/response.choices[0].message.content；SHA256 `042ae79535e9a5f742bbfe7959ce270f92690a1714dacc67b57f178f6b0f35ec`。

需人工确认：确认TopN默认的切换交互和该题自然语言条数含义；不改原评分。 状态 `pending_human_review`。

## sp03-05

原题：2007年最受欢迎的10首爵士曲目是哪些？

**参考：AI建议有条件通过。** 2007明确且无数据应空结果；登记热门数量默认支持L1。旧两遍争议导致原scorable=false，仍保留；空结果不意味着应该补最近年份。

**系统实际：AI建议通过。** 真实L1 Jazz曲目数量/2007/Top10/track_id并列键均正确，空结果和switch元数据有原文；不以空结果掩盖V0曾用name排序，本轮实际已使用ID。原排除保留。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-05/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-05/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `c247a038ecbe1c334375363593ddaab003cc444a2142b810c50c2acc011c2503`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-05/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-05/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `9d26ad18e42c3f0d544ff3c93ab628737b124f6c209764eb6f4ef2a55a515f6b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/390f3f0c5d78406c85b0e5c28b38adf1.json](../runtime_eval/provider-captures/V2-001/390f3f0c5d78406c85b0e5c28b38adf1.json)；request.messages/response.choices[0].message.content；SHA256 `41ef3cd12a7dd1fc5d93eb36048d7650f2af43c04eb061f74af976918e7c1fa3`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/ed24c36475064b87a19c691847e3c139.json](../runtime_eval/provider-captures/V2-001/ed24c36475064b87a19c691847e3c139.json)；request.messages/response.choices[0].message.content；SHA256 `78f0fb5b17215b5970c57d4665aab22aa3dbad3e6d8ac16a762c7110324e9626`。

需人工确认：保留原待确认；确认当前空年是否仍作为有效题，稳定ID排序不能靠空结果认定通过。 状态 `pending_human_review`。

## sp03-06

原题：销售额同比增长多少？

**参考：AI建议有条件通过。** 销售额与同比已明确，只缺当前期间；gold在补2024后合理。离线回答含current与base，与逐key控制器及重复time标志卡粒度失配；旧排除仍保留。

**系统实际：AI建议通过。** 本轮初次只问current，真实year2024 choice成功，基期推导2023；SQL真实金额469.58/477.53及ROUND同比percent1.69正确。这是原排除题的一次真实新闭环，不自动纳评分；percent与gold fraction展示差别明示、不能据同列名错判。

真实请求 2 轮；已执行SQL轮号 [1]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-06/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-06/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `326d197175121e381d2b1963005c68afebbba1c844522b1ee7b2184390efaf76`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-06/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-06/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `2da89fbd41f911184102f040a0f66609d7234272be8b8a52d5d33b0d185e14c1`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/a7b018d2cf2e4b9ca62f59a8225581db.json](../runtime_eval/provider-captures/V2-001/a7b018d2cf2e4b9ca62f59a8225581db.json)；request.messages/response.choices[0].message.content；SHA256 `888bda9150796ac1b976bf40cef15e5b0303123ee26aa6cb6d0f1b306e1b0f29`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-06/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-06/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `feb3d36c0424cbbc44cb3753c0964e368c95bc4a3273a34d8f2cadc38f9cdee8`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/1afd45486bcf46c4a175ce323b4bdff7.json](../runtime_eval/provider-captures/V2-001/1afd45486bcf46c4a175ce323b4bdff7.json)；request.messages/response.choices[0].message.content；SHA256 `1cbd1c2fed0af1fb310a0de33889278b04e9caa1948643b4ad103e9aba0adf85`。

需人工确认：确认一次补充同一时间条件是否可以包含明示基期；冻结controller本轮不动。 状态 `pending_human_review`。

## sp03-07

原题：2024年账单国是美国的发票销售额占比是多少？

**参考：AI建议通过。** ‘账单国是美国’明确billing_country；分母仍缺，应问分母。补全库2024后gold FILTER分子/同期间全库分母正确。

**系统实际：AI发现错误。** 本轮P2正确标billing USA但猜全库2024分母；程序仍把明确“账单国”覆盖为歧义，实际只问region而非denom，controller无地区补充停止、无SQL。正确国家澄清规则不能因本题短语覆盖失败整体取消。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-07/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-07/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `e392bff54a4771ce4ef855dc3f9776d39dc2d79fd14381f99be4f30b7d37f07e`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-07/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-07/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `a032509b5a7993ab4f6b026cd2911bb26ba41918322ce99a0bae619e7bfb0556`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/f1c88ff9478343ebbd5a1f9f71724716.json](../runtime_eval/provider-captures/V2-001/f1c88ff9478343ebbd5a1f9f71724716.json)；request.messages/response.choices[0].message.content；SHA256 `0cd39fa635988977e3aa701d9cac8737e82d00a3909c8aeed119e3d4f922b698`。

需人工确认：保留分子/分母区分；不能通过取消所有地区澄清规避短语覆盖问题。 状态 `pending_human_review`。

## sp03-08

原题：2023年谁买得最多？

**参考：AI建议有条件通过。** L2缺对象正确；客户/花钱补充后发票金额、2023、Top1 gold正确。补充同含object与metric，当前卡两项均问，单key控制器却拒绝整条；这是离线控制器适配争议。

**系统实际：AI建议有条件通过。** 真实L2同时问metric/rank_object，controller离线答同卡两项被逐key拒绝。没有用户补充POST或最终SQL；不能以模型先猜customer后被程序清除当已合法选对象。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-08/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-08/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `82aa570e95dd2b2ed0ec867909853bc7ad05123073b316cb0d9aa2e05fea45e3`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-08/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-08/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `ee4c91ff2294941115d43cea6379ae1059e5e4a08b70e646e2f912e00253a611`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/45cac4c3dc154f0b8e70e513f1c74471.json](../runtime_eval/provider-captures/V2-001/45cac4c3dc154f0b8e70e513f1c74471.json)；request.messages/response.choices[0].message.content；SHA256 `cfa4fc5a56766a237f89fd6fa36acfcfe5a6428b5430473b05221e9cfd430dd7`。

需人工确认：确认控制器只准一个issue还是允许一次回答卡内多个问题；原版本标签/score不动。 状态 `pending_human_review`。

## sp03-09

原题：2024年摇滚曲目卖了多少张？

**参考：AI建议通过。** 摇滚两候选关系非自动绑定；用户选择Rock后2024销售数量SUM(quantity) gold164正确。

**系统实际：AI建议通过。** 真实Rock稳定choice后2024 SUM(quantity)=164、流派与日期正确。

真实请求 2 轮；已执行SQL轮号 [1]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-09/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-09/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `a76d34b58e9f4f0f7eb25417f85f07f3dddea7a34144af0d5900e3cb85263400`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-09/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-09/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `9691d042c3ea07314dddbd338c1072d7492c0239dbc21c49447cdc1c73da33e1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-09/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-09/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `a27a54bbd66a4dfc93255668ddec3215aaf5b865bdf1dd2534628a8f4103a3f5`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/1a0dd35536474502a97bc092c9d94059.json](../runtime_eval/provider-captures/V2-001/1a0dd35536474502a97bc092c9d94059.json)；request.messages/response.choices[0].message.content；SHA256 `dfcb1d598f591963ded6b63c0f5027e2bec9873d1d23bb7facb20a2dd499ce1c`。

需人工确认：无新增业务事项；此题是实际按钮闭环，不能与自由补充混称。 状态 `pending_human_review`。

## sp03-10

原题：2024年巴西的客户有多少？

**参考：AI发现错误。** ‘2024年巴西客户数’未明确在2024购买的活跃客户、年末存量或新增客户；customer表无创建日期。gold擅加年度购买活动定义，不能从复购规则推广一般客户数。旧排除保留。

**系统实际：AI发现错误。** 首provider擅选2024活跃客户定义，旧绑定守卫repair后真实SQL变全部Brazil客户COUNT5，完全丢2024。标准活跃客户4定义仍有争议；当前SQL忽略期间是真实问题，非V2新比例守卫作用类别。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-10/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-10/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `ddfa9445fe1865aa29b24251d9153a1b0be258e56f6cbf4637a02e524d4038eb`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-10/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-10/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `3b23a8605a7d98a7a493b97b50ec74295381bad70f041c7c95035ef420d9ab2b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/4ac0ed3890e3481ca649f12be26af1a8.json](../runtime_eval/provider-captures/V2-001/4ac0ed3890e3481ca649f12be26af1a8.json)；request.messages/response.choices[0].message.content；SHA256 `ce9121b7576dc19b9c91d342a61f49f3394e822b14ab4afccfd6d7a534d5a8e1`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/499ab076cb404225bf60d355516c2bff.json](../runtime_eval/provider-captures/V2-001/499ab076cb404225bf60d355516c2bff.json)；request.messages/response.choices[0].message.content；SHA256 `6c59fb6c6d300a4f8e9da3e659d0e6629281b13f3cffa69fe0507d8962a054e1`。

需人工确认：优先确认客户数的时间语义；不增全局活跃客户默认。 状态 `pending_human_review`。

## sp03-11

原题：How many customers reside in the USA?

**参考：AI建议通过。** reside USA明确客户所在地，COUNT客户gold13正确。

**系统实际：AI建议通过。** 真实customer.country=USA COUNT13、L0。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-11/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-11/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `6bbd22deb059f92c7cc020465d33b16a96fe83a2b804cfff9eb27db336803e7e`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-11/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-11/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `7ab49178ae7e1121b550041c914045b7602da3717795d65df22ac26d5f9c3754`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/6b40cde0402945b88c320c447804e0c3.json](../runtime_eval/provider-captures/V2-001/6b40cde0402945b88c320c447804e0c3.json)；request.messages/response.choices[0].message.content；SHA256 `0437e686bc223ed3bfc7587acbe96ad66cbb5f5a39d840e93ceaabe21e2dcfe1`。

需人工确认：无新增业务事项。 状态 `pending_human_review`。

## sp03-12

原题：意大利有多少客户？

**参考：AI建议通过。** 明确问客户，Italy客户所在地COUNT1，未问金额或账单。

**系统实际：AI建议通过。** 真实customer.country=Italy COUNT1、L0。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-12/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-12/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `72c58ff6913ad7f47e89791a49bfa1c01d134ca23160ee9d4c07f8cce4697458`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-12/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-12/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `25031132f1df89a621548480935db227db2de562100a00b04f2c1b941d94ffd2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/d1cd3ccee703430795c9ffdc6560e3d1.json](../runtime_eval/provider-captures/V2-001/d1cd3ccee703430795c9ffdc6560e3d1.json)；request.messages/response.choices[0].message.content；SHA256 `024bab10638ee54d32517b3f65b4839faac4d3328775ce85b097eeff53e70145`。

需人工确认：无新增业务事项。 状态 `pending_human_review`。

## sp03-13

原题：What was the total invoice revenue for Canada in 2024?

**参考：AI发现错误。** invoice revenue确定金额粒度但‘for Canada’未明确地理归属；唯一billing_country和L0缺已登记依据。该gold在明确账单国后正确，不能由快照同值证明题意唯一。

**系统实际：AI建议有条件通过。** 真实L2问Canada客户/账单归属，2024和发票金额保留；controller无补充，最终未运行。参考唯一billing口径缺依据仍单列。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-13/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-13/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `d1a121c2cbd6a439a91f1c4423fcce6427625302fec977bd08a2b7c4880251be`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-13/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-13/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `8302425a58441572fd4e76fda94fe2d119f63179a6ae1b3784a32221bd99899d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/648e7fbf39e8452fbacf62ba880a0ac6.json](../runtime_eval/provider-captures/V2-001/648e7fbf39e8452fbacf62ba880a0ac6.json)；request.messages/response.choices[0].message.content；SHA256 `91d51babf29755af6edb4864d8e7f9100a0c2ffab12b373b04984cf5a4c956ec`。

需人工确认：与03统一确认国家金额口径，不因英语invoice上下文自行安装默认。 状态 `pending_human_review`。

## sp03-14

原题：2022年和2023年，Chinook 每年的发票销售额分别是多少？

**参考：AI建议通过。** 两年逐年SUM invoice.total，2022至2024半开范围、year排序gold481.45/469.58正确。

**系统实际：AI建议通过。** 本轮“每年”裁决unmatched，没有国家误绑定；实际2022/2023逐年SUM481.45/469.58、范围和排序正确。不能将V1的误澄清转写为V2结果。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-14/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-14/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `6e52165dd5ef52337e46ccc79f2a4d12274c3a48e6027baa9882767d213ba561`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-14/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-14/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `89a954f3243ade4034ae2b868b75c142851fe869d8e8f50b3818fa4e0b8a34aa`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/aad043de45024998a41f8f9d22edf03c.json](../runtime_eval/provider-captures/V2-001/aad043de45024998a41f8f9d22edf03c.json)；request.messages/response.choices[0].message.content；SHA256 `5cfd1e4744e1e33d2c72ea67b5fa2669c4b4dd63fb6e1f417cbe1992d15c46b1`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/c5e41f739585495d9b1c37e695d62534.json](../runtime_eval/provider-captures/V2-001/c5e41f739585495d9b1c37e695d62534.json)；request.messages/response.choices[0].message.content；SHA256 `073a255092223958000ebb0575319f25cf8114c240d028b583720af8ba2bd75f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/1e034652a0f54c0ea0d61f68a2bdfef2.json](../runtime_eval/provider-captures/V2-001/1e034652a0f54c0ea0d61f68a2bdfef2.json)；request.messages/response.choices[0].message.content；SHA256 `cad65442ea7831eb9fa9099b2e3fd6b2ca54400ae21b2a8385a3ac10685d8e2f`。

需人工确认：可确认年份展示类型；不改scorer或gold类型。 状态 `pending_human_review`。

## sp03-15

原题：2009 年和 2010 年之间，哪首曲目最受欢迎？

**参考：AI发现错误。** 热门购买数量使用登记默认应L1，标签L0与business_basis‘默认使L0’错误，原source guard已指出并排除；SQL数量/2009–2010/Top1自身正确。

**系统实际：AI建议通过。** 本轮P2明确Top1、真实数量默认L1，SQL2009–2010/track_id稳定排序LIMIT1，空结果正确。原L0错误标签仍排除，未实际点击L1开关。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-15/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-15/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `6d1a113e2d430cc692945a1bf8b56dc737cb8bca95b24b4d4816a7f8d6612659`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-15/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-15/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `f0ba73bfb87bfa2f8c0e59c07fae47a659cd49f731ca25164ba45f377ec7f155`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/208609471fea4a748ef2bbe8c1c73e91.json](../runtime_eval/provider-captures/V2-001/208609471fea4a748ef2bbe8c1c73e91.json)；request.messages/response.choices[0].message.content；SHA256 `b1946cba894ef7efe4c676d75c186ddb8a5e805e883b4e07e8206b45e735930d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/d810f82c6dd349a9becaa49fdce4e9e7.json](../runtime_eval/provider-captures/V2-001/d810f82c6dd349a9becaa49fdce4e9e7.json)；request.messages/response.choices[0].message.content；SHA256 `6a79850b97ada9f7d71ae74e9760cd1c6463810fa036bb7b5e49ee4d4090290a`。

需人工确认：原分类争议待人工，继续保持原排除，不新计成绩。 状态 `pending_human_review`。

## sp03-16

原题：Chinook 里 Jazz 流派的曲目有多少首？

**参考：AI建议通过。** Jazz明确流派，曲目COUNT JOIN genre正确，gold130。

**系统实际：AI建议通过。** 真实Jazz曲目目录COUNT130，track/genre关联正确。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-16/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-16/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `d2a58d1bb0a56c5eb74193e8da67135a6d4b338a8f6d7729744345586b2cb98a`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-16/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-16/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `1cf82e0886b2a506413bbf0aedc7693bdf52b7703012df66186772e69d2ce02b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/674150558a874ce5b84cd27bf907f895.json](../runtime_eval/provider-captures/V2-001/674150558a874ce5b84cd27bf907f895.json)；request.messages/response.choices[0].message.content；SHA256 `84a85a9353616e874fae10cf2bcbc4a2e60b2bd4119eeac869410b3310eb1a65`。

需人工确认：无新增业务事项。 状态 `pending_human_review`。

## sp03-17

原题：2020年全年复购（至少开2张发票）的客户有多少位？如果没有，请如实输出0。

**参考：AI建议通过。** 明确期间至少两张发票，按客户GROUP HAVING COUNT>=2，再外COUNT；无符合客户输出0，gold符合已确认复购定义。

**系统实际：AI建议通过。** 真实2020期间至少两发票客户COUNT0，外COUNT与SUM空集区分正确。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-17/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-17/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `5031e84b073c9da283c2236577f71bf686ff7195cd744496d8eccf09d690c4ec`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-17/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-17/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `5e196f42dc12cdccb776840abc70c70040f6b5c5b934a809431814715184c97e`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/545cdbb173c045c799ae4275311ecb63.json](../runtime_eval/provider-captures/V2-001/545cdbb173c045c799ae4275311ecb63.json)；request.messages/response.choices[0].message.content；SHA256 `14943323bad95a7a0d86d00db9a4b558bff62b419a015735c5a4a409f9a0c8ba`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/b984d48ce29f46f2b1622fd2f5bafd7d.json](../runtime_eval/provider-captures/V2-001/b984d48ce29f46f2b1622fd2f5bafd7d.json)；request.messages/response.choices[0].message.content；SHA256 `956944d1aba1a1640cc1f50af8cf266c683dd1ba12a9db39fe6bfd297686163d`。

需人工确认：无新增业务事项。 状态 `pending_human_review`。

## sp03-18

原题：2021到2022年最受欢迎的曲目有哪些？

**参考：AI建议通过。** 2021到2022两年范围、数量默认和Top10默认、track_id排序，gold包含两年正确。

**系统实际：AI发现错误。** 本轮SQL及核心结果真实覆盖2021–2022两年、数量Top10正确；Intent.current仍被程序日期覆盖为2022，仅当前SQL偶然从原文恢复两年。真实持久状态错，不能称实际SQL缩短为一年，也不能据正确表结果宣布完整意图通过。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-18/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-18/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `b694496b9cf321bf4822d4156809e73bd4cff76ba5d2b5ecac1b0ff625a22e59`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-18/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-18/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `fd1df9fc0b5e6118d236333c4e9b4ca183b5499b919f1b74ab7cdce0cfbcb913`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/d87f76505c6045a491dd13a025a425f5.json](../runtime_eval/provider-captures/V2-001/d87f76505c6045a491dd13a025a425f5.json)；request.messages/response.choices[0].message.content；SHA256 `c7f525af8edf96f229d8de2ff249f4c6a694d878a0980e1e9d0c56da93ad87dd`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/1b1097717cd7476bb04404d864aacdb9.json](../runtime_eval/provider-captures/V2-001/1b1097717cd7476bb04404d864aacdb9.json)；request.messages/response.choices[0].message.content；SHA256 `722e18aa83e8f9e6ce44820d1d57bdce7a1fd845f79e5d0f53b5562261a6cd1d`。

需人工确认：日期解析改动需后续另立代码任务，不能让prompt输出绕过程序覆盖。 状态 `pending_human_review`。

## sp03-19

原题：2022年买得最多的客户是谁？

**参考：AI建议通过。** 对象客户明确，已确认金额默认、2022按customer_id合计取金额最高一位，gold45/32.75正确。

**系统实际：AI发现错误。** 真实2022 customer金额winner45/32.75正确、姓名额外列合理；L1金额默认switch仍null，未有实际可切换控件，未点击。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-19/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-19/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `666d839fd17a20aa03f06080ea6f710161e9c33c1546a97814e8dc943bcd8cf2`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-19/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-19/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `4f2952071a61c291d57e58d267485096b2e407c5cce2765f6eea770cf91a258a`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/d49dfd9c5bea4640ae5e17c2727c584a.json](../runtime_eval/provider-captures/V2-001/d49dfd9c5bea4640ae5e17c2727c584a.json)；request.messages/response.choices[0].message.content；SHA256 `c9b762626a654816263ed1d42e99529c6e6f3304bb2a492a523a60f4d900ac22`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/ce1eb063182a498381c948b49a2e0374.json](../runtime_eval/provider-captures/V2-001/ce1eb063182a498381c948b49a2e0374.json)；request.messages/response.choices[0].message.content；SHA256 `d5ae8c582a7735d987b5d93c8ba05ad08871d434f4e3e28a699ac1f060788330`。

需人工确认：确认客户金额默认可切换的备选指标是否登记；不能凭空加新业务默认。 状态 `pending_human_review`。

## sp03-20

原题：2023年按销售额排名最高的艺术家，取前10名。

**参考：AI发现错误。** 输入明确2023、艺术家、销售额、前10名，没有待应用的登记默认；L1标签不成立，原source guard已排除。gold金额/排序自身正确。

**系统实际：AI建议通过。** 真实L0艺术家2023明细金额Top10、artist_id并列排序正确；原错误L1标签排除不改变。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-20/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-20/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `f7ca96e35c4dab849dd23970759b68679da1684d320f66922ecb5d863f8f7723`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-20/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-20/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `dee1c3079b500d976eb92342e94a1e00862d8aa447209782f597c33430c04301`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/f12e6396b89648989d3c9ff72a3db15e.json](../runtime_eval/provider-captures/V2-001/f12e6396b89648989d3c9ff72a3db15e.json)；request.messages/response.choices[0].message.content；SHA256 `127382f385370ad1e2f4fadf4d3183f8c3457276141cbf42a438a434d69320dd`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/a917216502ff4a0697bd430b358d8717.json](../runtime_eval/provider-captures/V2-001/a917216502ff4a0697bd430b358d8717.json)；request.messages/response.choices[0].message.content；SHA256 `21494160cd298843a17e43ea532389ffea750ae9e79baa9b55adad6d40b63f3c`。

需人工确认：保留分类人审，不按运行结果将scorable改true。 状态 `pending_human_review`。

## sp03-21

原题：德国的销售额同比增长多少？

**参考：AI发现错误。** L2缺年份正确但参考声称仅缺期间、默认customer.country德国缺依据；controller只有time补充，没有合法地区补充，最终唯一客户归属gold条件不完整。

**系统实际：AI建议有条件通过。** 实际期间和国家归属L2有依据，controller time同域补充拒绝未发送。参考only time缺项及唯一德国客户归属不完整，最终SQL未运行。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-21/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-21/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `653e486ff8aaa29a2c32a647cc57d86f7a0c1878aac61e1aef4f87f4f3fbf0d7`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-21/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-21/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `27e61b63e13a250533e4e80bc4dbb946d7ff92889bace03359f49dbb6cc9f8bc`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/0af48b32ac954493a20732430259e380.json](../runtime_eval/provider-captures/V2-001/0af48b32ac954493a20732430259e380.json)；request.messages/response.choices[0].message.content；SHA256 `d23c36f86312ce1784d93e68a2ded7c9f727211305481a51119d4037b101daec`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/ed0ebcf31f7b4ac390f365ba6f0c1ddc.json](../runtime_eval/provider-captures/V2-001/ed0ebcf31f7b4ac390f365ba6f0c1ddc.json)；request.messages/response.choices[0].message.content；SHA256 `cd44b21e01a0d1b19c049c35c32de2a414c5cbfc24d44910be2a058be9f44992`。

需人工确认：确认地区归属并补合法controller来源后需统一新标签评测；本轮不更改。 状态 `pending_human_review`。

## sp03-22

原题：2024年法国居住客户的销售额占比是多少？

**参考：AI建议通过。** 法国居住客户明确分子；分母补2024所有发票后应全库分母，gold0.0767700458609930正确且防零。

**系统实际：AI发现错误。** 真实P3补2024全库分母正确；随后3个provider SQL均为法国CASE分子/全库SUM分母，WHERE只有2024日期、无country，CASE零保护+ROUND((SUMCASE/SUMtotal)*100,2)数学正确。V2守卫仅接受(SUMCASE*100)/SUMtotal，三次误拒合法等价百分比，最终FAILED/table=null，没有执行结果；这是新增语法覆盖不足，不是分母错误或已改善EX。

真实请求 2 轮；已执行SQL轮号 无；生成未执行SQL轮号 [1]；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-22/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-22/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `c619e07ac5afa3bcf5fe4450bc68099aebb540a86680857bf2c8836759a7fe05`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-22/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-22/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `1f38edf5dd37958c0f7f443ea1a051e4d67f585246a7400ca8f18ead1ec0a04a`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/a5337b3b6e14458e9f59fde1df7952a2.json](../runtime_eval/provider-captures/V2-001/a5337b3b6e14458e9f59fde1df7952a2.json)；request.messages/response.choices[0].message.content；SHA256 `d562bd155cb57240a107891730985bc9bcf6898d251d6cc940e39bea8ba7934e`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-22/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-22/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `f6604c092cf58f61798cbc133252b4706a7f55a610b1e065bd8618a0e9734e6e`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/2ce2681aa4a5474cb7e5634bf5f0fcc6.json](../runtime_eval/provider-captures/V2-001/2ce2681aa4a5474cb7e5634bf5f0fcc6.json)；request.messages/response.choices[0].message.content；SHA256 `8cd8b3a71b373377f902bfed8bb96c02f1fa516ee1fc8b08c4bdd97c403064f2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/cba30d135b99471b8a16b6df4bfadfac.json](../runtime_eval/provider-captures/V2-001/cba30d135b99471b8a16b6df4bfadfac.json)；request.messages/response.choices[0].message.content；SHA256 `1d7f0abfde74aa17b085ab1bd7dd08596192c8ed3e0a6c5c89a53c136022a23b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/8859f523cba14ee7ae8e75d12b0388f9.json](../runtime_eval/provider-captures/V2-001/8859f523cba14ee7ae8e75d12b0388f9.json)；request.messages/response.choices[0].message.content；SHA256 `61580427a03fcc1980e3052ab748ea40e94c3f30c995e68a6c4389400ac36baf`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/7e007faff956462cb0db57a9e01718cb.json](../runtime_eval/provider-captures/V2-001/7e007faff956462cb0db57a9e01718cb.json)；request.messages/response.choices[0].message.content；SHA256 `df3f2a1337dbcf47615be8bab14d0308967f44cde81fff002d4005fafad84f18`。

需人工确认：优先处理比例范围模型与SQL绑定校验职责；不能为通过关闭其它问题全局筛选守卫。 状态 `pending_human_review`。

## sp03-23

原题：2023年谁买得最多？

**参考：AI建议有条件通过。** 与08重复初始输入，原scorable=false保留；客户2023金额及改2024目标合理，但重复题不能重新纳入分母。

**系统实际：AI发现错误。** 真实客户选择后2023 winner46/32.75正确；“改看2024”fresh路由后执行全库年度发票83/总额477.53，丢customer排名目标。原重复题排除保持。

真实请求 3 轮；已执行SQL轮号 [1, 2]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-23/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-23/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `108bc97eef6306e984bb6c617e65d71c7bed1e3b7cf1b1d14095ad5eece66f23`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-23/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-23/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `0eebd2a7af6d94e885f06d19344142279d2bf5f6698c88c3a6266b9c33bb3cf4`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/f73ef3e40bf242478575b1139ee8f072.json](../runtime_eval/provider-captures/V2-001/f73ef3e40bf242478575b1139ee8f072.json)；request.messages/response.choices[0].message.content；SHA256 `0fcd055c0e4bd7d77cbb7fd27815996b88cf60b3858dbc2825bfb40237987f06`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-23/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-23/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `dc6c7f223e9dcfaac6c914fe80deac43d211ddfdc5f12ea2f34392e9faeb68f4`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/62b9cf4141f148468afea29dbbd2c01b.json](../runtime_eval/provider-captures/V2-001/62b9cf4141f148468afea29dbbd2c01b.json)；request.messages/response.choices[0].message.content；SHA256 `3914d56578caea75dcf5f0260e5ecdee3cb0af9627caa27952706c305dec4ff3`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/94c7209e66584d0e8c29ca4226cfbac0.json](../runtime_eval/provider-captures/V2-001/94c7209e66584d0e8c29ca4226cfbac0.json)；request.messages/response.choices[0].message.content；SHA256 `3c47c0d27068618b4eaf3c542f039bb224b1caadf185a38c9c6e842667f901cb`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-23/turns/002/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-23/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `ace3454164418682ae56688382620f74aac2a69ba6813f43e5d37989e912dccd`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/832559a58d0d48f9b48471c59374114a.json](../runtime_eval/provider-captures/V2-001/832559a58d0d48f9b48471c59374114a.json)；request.messages/response.choices[0].message.content；SHA256 `ec755b151f5f6e5712e95cfa93d9037602e87c5efd54127ca78d5b45dfb10af8`。

需人工确认：后续路由代码任务应覆盖合法改动表达；本轮prompt-only不伪装修复。 状态 `pending_human_review`。

## sp03-24

原题：2022年澳大利亚的发票销售额是多少？

**参考：AI建议通过。** 国家金额未明归属先L2，用户选customer.country后SUM total/2022/Australia，再改billing_country保值，gold均正确。

**系统实际：AI建议通过。** 真实customer归属choice及随后billing归属修改均保2022/Australia，SQL来源字段正确；金额0.99相同不能替代字段证明。

真实请求 3 轮；已执行SQL轮号 [1, 2]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-24/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-24/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `0310659cefd9be7573622aa758f20889f6b2e3ef6d5b4997fba3d2a6a40a5dbb`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-24/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-24/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `9ed0ccef9a967bd04c06146dc03c00148bc7d8445ee77a465e65e5fd837a1e52`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/cb37e56c9c1e433bb297a42093b2d225.json](../runtime_eval/provider-captures/V2-001/cb37e56c9c1e433bb297a42093b2d225.json)；request.messages/response.choices[0].message.content；SHA256 `8090eb154836c6e22ec3b06be3da0484fdd1959bdce144745b21e0b55716fd9f`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-24/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-24/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `c08be16f664ec382aa5485578684c072d7b424a02bdbc6d2984e8fef14cb9d22`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/f10f179e86e348b9bb4a6bc024e9793b.json](../runtime_eval/provider-captures/V2-001/f10f179e86e348b9bb4a6bc024e9793b.json)；request.messages/response.choices[0].message.content；SHA256 `f1be4160c2236a724a26d16efa788cccfd3ddd6e81ab7dad96fc75e7874d732c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-24/turns/002/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-24/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `0bd28eb1b3071060b6cef7e566798041b389306b02d599b599409c56926b2ed8`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/71d7734dae8d4372a817627405c5ea2d.json](../runtime_eval/provider-captures/V2-001/71d7734dae8d4372a817627405c5ea2d.json)；request.messages/response.choices[0].message.content；SHA256 `93208feab90833bbfda17937e2e9e8743bd3e1841ce8e49d59a55884e9697c13`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/222595d5787541a7bb3e027d61f7fe53.json](../runtime_eval/provider-captures/V2-001/222595d5787541a7bb3e027d61f7fe53.json)；request.messages/response.choices[0].message.content；SHA256 `b5b8128459e708964e794e4beb2da671c5224dd61cc34b1a671ce590335ae069`。

需人工确认：无新增业务事项；这是实际国家归属迁移闭环。 状态 `pending_human_review`。

## sp03-25

原题：2024年摇滚曲目的销售额是多少？

**参考：AI发现错误。** 两个允许补充分别指Rock和Rock And Roll，但唯一final gold=Rock，原source guard已指出冲突并排除。value补充还缺column，不能从candidate label强猜字段。

**系统实际：AI建议有条件通过。** 真实Rock/RockAndRoll候选保留，controller value/column不唯一而止步；无选择、无SQL，原允许补充/唯一gold冲突排除保持。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 1 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-25/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-25/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `b42941fdcdd72cf18a8025d8d36f2088b10e6cd457510ed28b7a17ddf97a4fdf`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-25/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-25/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `a1bf3948cd7a5ca84e4f15eef413925811797d8966dd381472c7d053aa2396db`。

需人工确认：先统一允许补充与目标来源，未来统一新版标签重评；本轮保持原排除。 状态 `pending_human_review`。

## sp03-26

原题：同比增长多少？

**参考：AI建议通过。** 同比缺metric/current先L2；补发票金额/2024后计算2024对2023，改2025再换AVG时应保留增长任务及2025/2024，gold正确。

**系统实际：AI发现错误。** 本轮P2无原文依据标scope_missing=true，初始卡却问“这批/这些”范围，题面根本无指代。真实2024补充、发票金额补充后仍scope_missing，controller无合法补充停止，无SQL/后续year或metric修改。不是V1已执行后fresh路由bug的本轮复现。

真实请求 3 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 2 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-26/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-26/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `8e97b3905dcb64dfb04dd54b2c9f6c6b2c81bfc5f47d3877ee708c74d345be76`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-26/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-26/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `1c10a30c8485adb397b71d76fac459e6101a3ca023be7fa2b225f82f8a06e46f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/c0838a81207f403d990b62463b5efa29.json](../runtime_eval/provider-captures/V2-001/c0838a81207f403d990b62463b5efa29.json)；request.messages/response.choices[0].message.content；SHA256 `a5e027a2afd70cafad63ab495485c4fea5a09fee2abacb10f58b6197b0d4a52f`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-26/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-26/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `34ec8570d32f65e9d637e693f73ff855a2398fee25f5875d2d307add49feea6d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/3fbf0b1f7aa341ee870882fda53c86af.json](../runtime_eval/provider-captures/V2-001/3fbf0b1f7aa341ee870882fda53c86af.json)；request.messages/response.choices[0].message.content；SHA256 `707fd14f798da0625199a6311f4dc73a33acff1ce8f69e33c9d7323572d94d95`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-26/turns/002/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-26/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `878f42b9a71a3942a1a5d038c6969872e2e36946853867928e40c4cd89be292d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/2eca380343cf4f4283702b7fa1c12118.json](../runtime_eval/provider-captures/V2-001/2eca380343cf4f4283702b7fa1c12118.json)；request.messages/response.choices[0].message.content；SHA256 `c6114f371e5cbe3ccc2a44a13114bb4a73445b8c8d5fa0404e5fddd4c899b895`。

需人工确认：代码路由不能由patch prompt补偿；保留前面实际正确子轮与最终真实失败，不混成全程通过。 状态 `pending_human_review`。

## sp03-27

原题：2023年销售额占比是多少？

**参考：AI建议通过。** 2023比例缺分子/分母，补客户所在地Brazil分子和全库同年分母后的CASE gold正确；后续修改应分别保持局部范围。

**系统实际：AI发现错误。** 真实P3set numerator并额外set customer.country filters；当时value_link真实核验巴西→Brazil、补丁获接受。下一denom请求无巴西mention，过滤字典已丢evidence_ref，V2无法恢复之前中文已核验surface，三次误拒“无实际用户原文证据”。原用户明文和先前绑定确有证据；最终INNER JOIN CASE fraction数学正确，前两LEFT也能保全分母，但未执行/table=null。这是新增来源继承覆盖不足，不能说模型无分子或分母错。

真实请求 3 轮；已执行SQL轮号 无；生成未执行SQL轮号 [2]；计划后续未执行 2 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-27/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `e11e30cfbb80be58367a74e7e20094db86b4530690e7cf6f36d4dc8c90f9135f`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-27/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `1f136538917a5de4662343f5ea1f95786a98a45cf4043de686970589e0f45602`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/d10671c74d454c25927a9cabb171b8d1.json](../runtime_eval/provider-captures/V2-001/d10671c74d454c25927a9cabb171b8d1.json)；request.messages/response.choices[0].message.content；SHA256 `214e1a13e0a9c60c4236a6c4303ddfcce292bdd453640215166902821c80c90b`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-27/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `92785f1bbb853af3d8828e3a15a1cb9f7e3459f88f0b529eb78e07a9cef072a7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/791bbdf0fce644e1b0287000a6e08273.json](../runtime_eval/provider-captures/V2-001/791bbdf0fce644e1b0287000a6e08273.json)；request.messages/response.choices[0].message.content；SHA256 `27c281e22b78c1345faeace2e562af598497dedf6f7602810ae5a772a51a4267`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/002/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-27/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `6c6fb535169332112ae5d21e2099d0f00afa293f2c29160729249cdcc0dbc720`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/7f380fea516541eb87c89c0311ad545a.json](../runtime_eval/provider-captures/V2-001/7f380fea516541eb87c89c0311ad545a.json)；request.messages/response.choices[0].message.content；SHA256 `dfa3e056b6a3984d3b223cb854cdb0929bc6fd4548a885d721d106dd1f169d21`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/8e3dd585051e40aaba32f27fb309a28f.json](../runtime_eval/provider-captures/V2-001/8e3dd585051e40aaba32f27fb309a28f.json)；request.messages/response.choices[0].message.content；SHA256 `ef00286a9d3d9d08ae795b615b8cfea719eeb43e89d28e996d8494a66f608314`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/7ebd46eeb5124ad5aff798ff0d7b5969.json](../runtime_eval/provider-captures/V2-001/7ebd46eeb5124ad5aff798ff0d7b5969.json)；request.messages/response.choices[0].message.content；SHA256 `c38c7a3345c0d9f573a9f2bb97c17999ad0e92b70ebe380a982e3e2da2ec6d91`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/179ef75cc176407d98cc887500f14359.json](../runtime_eval/provider-captures/V2-001/179ef75cc176407d98cc887500f14359.json)；request.messages/response.choices[0].message.content；SHA256 `5ed051b3a9ed09152ce88aab39ad40538b78e26d10258e06c90603d6dfe6b2e7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/230e641d5d384f139e671d3448285b61.json](../runtime_eval/provider-captures/V2-001/230e641d5d384f139e671d3448285b61.json)；request.messages/response.choices[0].message.content；SHA256 `8a767a9f542fa1407ddf48a532bd6632fa330345439ad4805f40a43e34a0e92a`。

需人工确认：建议仅patch prompt界定局部分子/分母string及global条件边界；正确patch之后能否生成合规比例SQL仍需真实验证。 状态 `pending_human_review`。

## sp03-28

原题：2022年金属乐队的销售额是多少？

**参考：AI建议有条件通过。** 初始‘金属乐队’Metallica候选需用户确认，gold明细2022正确；business_basis含‘Metal与Metallic在artist与genre均有候选’不符合当前别名表，需更正依据。L2实际应为候选确认，不必凭band字眼强造genre初始歧义。

**系统实际：AI发现错误。** 本轮真实Metallica确认后22.77正确；对象改Metal的P3 set filters丢oldartist，被原守卫要求explicit remove而拒绝。无后一2023/Germany运行；与V1同形状限制，非V2比例守卫修复范围。

真实请求 3 轮；已执行SQL轮号 [1]；生成未执行SQL轮号 无；计划后续未执行 1 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-28/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-28/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `78554471a5fa5ee5333e5f62faf828eefe39211fadedfa81a8217c2218961b62`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-28/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-28/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `75f08b11aee10267078c5f702ca2245084d4ceb260f804714a411370c4b5eebc`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-28/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-28/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `d13de956d5cebead6f7b0d59ce4ea8162f56d9372b07b0bc520c64c7ca293094`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/1b1136b3d3f54ce38292c92ee3f03cd9.json](../runtime_eval/provider-captures/V2-001/1b1136b3d3f54ce38292c92ee3f03cd9.json)；request.messages/response.choices[0].message.content；SHA256 `604b03f40806245fc3b2205716ebcf59a13c9a46e47cbaef14790fc74b807258`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-28/turns/002/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-28/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `d4b7a0fd81657d1b753f7487d20f1c69b017396db9561c8c57eaee5aaf978b2f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/f75e2c5372b447358c8541ac53e7104d.json](../runtime_eval/provider-captures/V2-001/f75e2c5372b447358c8541ac53e7104d.json)；request.messages/response.choices[0].message.content；SHA256 `20943bccceafd964ad98e7a1333b2500e0977a606c78c03437647d5ce39cbb76`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/dc612b04e76443aeb2f9b1e7b69dbf67.json](../runtime_eval/provider-captures/V2-001/dc612b04e76443aeb2f9b1e7b69dbf67.json)；request.messages/response.choices[0].message.content；SHA256 `ed6c0d5e71e377fd78cd65b67b1f337bd4bc0b3511f1905f70f732a27ad59947`。

需人工确认：确认替换对象是否应撤销原对象过滤，程序应做可证明且只删目标的迁移；本轮prompt-only不放宽guard。 状态 `pending_human_review`。

## sp03-29

原题：最受欢迎的10首曲目是哪些？

**参考：AI建议通过。** 热门10首缺期间先L2，数量登记默认；补2023、改2024、改明细销售额，三段gold语义正确。

**系统实际：AI建议通过。** 真实2023按钮、自由改2024、换明细额三段保track/Top10/期间/ID排序、旧默认被清；各核心结果符合gold。额外name列是原评分契约限制；L1开关元数据不是实际点击。

真实请求 4 轮；已执行SQL轮号 [1, 2, 3]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-29/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-29/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `58104498f4484fa48e80c4b7533caa617ef664c21b2fc150ecaa7741cc2cb831`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-29/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-29/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `d26b43422a48e6604ce51d108545bfb35a7b85b9110dd1924523a5cb981e6fab`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/6be8fcdd76c4415d9422c49b35ece604.json](../runtime_eval/provider-captures/V2-001/6be8fcdd76c4415d9422c49b35ece604.json)；request.messages/response.choices[0].message.content；SHA256 `01f75b02695ed98080a145987ca67bcbbe6343226a8a7d760510ea8d1f3ffd6d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-29/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-29/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `ff49114d98fb472060fc0118ad8e8499c13fc8078bbc0da2bc0dcfdba5d1ad33`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/28ec67031ef04fa98778e43c3d4aa11d.json](../runtime_eval/provider-captures/V2-001/28ec67031ef04fa98778e43c3d4aa11d.json)；request.messages/response.choices[0].message.content；SHA256 `1636050a1f8caee99e854e9ec82848876907157e84498a9dd5e479c5248ddaeb`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-29/turns/002/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-29/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `43c4bdf65fbe43154aab154fe8996cc2c4ee7fb2eedfed91df53fd643df737b0`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/63ca1828e8db49f797f28936c556f3f5.json](../runtime_eval/provider-captures/V2-001/63ca1828e8db49f797f28936c556f3f5.json)；request.messages/response.choices[0].message.content；SHA256 `121cc9d2059fec27dbe4937ef157661d676dfa59eb568d2d2bddbba93b463ef7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/12491b11df94404381dccf6e07edf9e5.json](../runtime_eval/provider-captures/V2-001/12491b11df94404381dccf6e07edf9e5.json)；request.messages/response.choices[0].message.content；SHA256 `d3ea0ef32f02be68d954d09e8b0b556c7724566e58d53656de1c1249a05782ff`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-29/turns/003/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-29/turns/003/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `ae4b67e7c69452f802b9545158a838bdc25a45c263b2f8abc61cbcda55208946`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/c96b2e3e472a4190997eec4d5305339d.json](../runtime_eval/provider-captures/V2-001/c96b2e3e472a4190997eec4d5305339d.json)；request.messages/response.choices[0].message.content；SHA256 `b53dc4abbcd76061559bfd6748ab133351bbab1251a624552ef2a5fab8f67813`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/eb5271072a6248dba5ce711154027958.json](../runtime_eval/provider-captures/V2-001/eb5271072a6248dba5ce711154027958.json)；request.messages/response.choices[0].message.content；SHA256 `d8c6908eb86a0cf1e03de38b5fd0c3efe7d8d948e11b05f165ed0b4ffe449f77`。

需人工确认：确认评分输出契约是否允许解释性附加列；不要因此修改参考业务答案。 状态 `pending_human_review`。

## sp03-30

原题：谁买得最多？

**参考：AI建议有条件通过。** 对象/时期澄清后2023客户发票金额SQL正确；ranking.required仅metric/object，但现有rules对canonical customer+invoice_revenue另要求期间。原hidden goal Top1并未出现在用户补充，登记缺TopN默认10与“谁最多”的条数语义需确认。不能把隐藏2023当已向系统发送；参考Top1边界保持有条件，不改原标签。

**系统实际：AI发现错误。** 本轮P3同样rank_object=中文客户，绕过canonical customer金额排名必问期间规则，只有metric/customer补充便执行全库Top10、未收到2023。后续2024/track数量修改实际保持未改条件；参考Top1争议另列，不把hidden2023送模型。

真实请求 5 轮；已执行SQL轮号 [2, 3, 4]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-30/checkpoint.json](../runtime_eval/runs/V2-001/cases/sp03-30/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `d75e518cb5e862733c4737bc349341f5fe86bae038b9aa823447489617750073`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-30/turns/000/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-30/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `f979cb93e15e8f4e19472f3fc41d6c3e210adcd35ebda21fc515af26634e91a9`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/967b79596a1e402ea1ca7b34412307ce.json](../runtime_eval/provider-captures/V2-001/967b79596a1e402ea1ca7b34412307ce.json)；request.messages/response.choices[0].message.content；SHA256 `78b6bee7b5c629aea900c7f433c68629b3279c11586a19f507c64cc88038574c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-30/turns/001/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-30/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `bc5d6f1f77b64331dddaa41002e59afd449d1c4b5d93350435ae5acd18b249d4`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/766cb30b96134dfe8a54e398a6524f54.json](../runtime_eval/provider-captures/V2-001/766cb30b96134dfe8a54e398a6524f54.json)；request.messages/response.choices[0].message.content；SHA256 `fb1a14dec5cccd0760c3bcf924e21b62274389cecbef43eec133a5ac6098114c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-30/turns/002/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-30/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `7c1fdc2b10b1e99fa7e40838e9e1f8bbcb075fb6cbbb5a71e8d87dcd3bba2536`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/2c3200fd06b14c4fae5219fd9c9335a5.json](../runtime_eval/provider-captures/V2-001/2c3200fd06b14c4fae5219fd9c9335a5.json)；request.messages/response.choices[0].message.content；SHA256 `8b985d936ecaa628b008ac321f6b42e019c07567da0a6b51d933b7d47c9ac6cb`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/0129dd1d9e1f49c5ba2c811877a29ae0.json](../runtime_eval/provider-captures/V2-001/0129dd1d9e1f49c5ba2c811877a29ae0.json)；request.messages/response.choices[0].message.content；SHA256 `e1469508d3345b8a3abdf1c0862597ee03b17aec188044886620ac54a20d09aa`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-30/turns/003/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-30/turns/003/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `1c188d697faff973f86109546431eb2bbf16cbcf856e9d9660eea16dc19b2ec2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/445ed65c3e8744eda6618a16e3d3e7e6.json](../runtime_eval/provider-captures/V2-001/445ed65c3e8744eda6618a16e3d3e7e6.json)；request.messages/response.choices[0].message.content；SHA256 `8ec856f39939016311f40c3ffbb62453374b939ff4c92b42a9ec658426e6e09a`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/9dad764dafd040eb95938bfa3738ccd8.json](../runtime_eval/provider-captures/V2-001/9dad764dafd040eb95938bfa3738ccd8.json)；request.messages/response.choices[0].message.content；SHA256 `2aae5e5ca66cc69ea295840d60a076a54ee0d200666f67e72eed40d76d1884b2`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-30/turns/004/response.raw.json](../runtime_eval/runs/V2-001/cases/sp03-30/turns/004/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `7ce5d8a31aa7d87a65c960a3d2510fca83118494ff0fcd9eabd32f85d6cfb71b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/10c4efba338f4c50961bfdddb5adcb97.json](../runtime_eval/provider-captures/V2-001/10c4efba338f4c50961bfdddb5adcb97.json)；request.messages/response.choices[0].message.content；SHA256 `8027087927d32031d77f2ce0d9e99b5b37f4043e1bca89624ee6137b00358f3f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V2-001/99dc94abc79c4d8eb1ff46b2fa807220.json](../runtime_eval/provider-captures/V2-001/99dc94abc79c4d8eb1ff46b2fa807220.json)；request.messages/response.choices[0].message.content；SHA256 `500d271e915c0f2981b6fd9fbd92a6553f0ada875932f73914dcdf8b3af0c114`。

需人工确认：优先确定最高一位与Top10默认的适用范围；本轮不强制Top1，不改49分母。 核对实体对象ID规范及由此漏问期间；不补写隐藏2023。 状态 `pending_human_review`。

## 材料与限制

- [data/catalog/chinook.yaml](../../../../data/catalog/chinook.yaml)；SHA256 `4d97a3f7fdfd0c684b544f162e20d2253c4f9c0cd572ba1fcaf40fe439a391b8`。
- [data/aliases/aliases-d2-reviewed.csv](../../../../data/aliases/aliases-d2-reviewed.csv)；SHA256 `aa699e8ef59f5185a0626ed2a9aefb36a1e292bfa2e3c0efd4b0ba5b1ddaef04`。
- [data/rules/metric_definitions.json](../../../../data/rules/metric_definitions.json)；SHA256 `2a0df8d29a4fb5401fd0a5b33a0f44932e00ab005bc674eaaa8b8a33f1df5efc`。
- [qa_agent/clarify/clarify_rules.yaml](../../../../qa_agent/clarify/clarify_rules.yaml)；SHA256 `345b5abeaf858cd3628fcc08c6280a7d6c08517bd9dae0e0677cf0b256e8e7c8`。
- [eval/experiments/after_d2_01_03/materials/generation_materials.json](../materials/generation_materials.json)；SHA256 `8bb7b1b403972e6b2ae910823842ac3480079e291e5d1b35b24e3dc7de856cf0`。
- [eval/experiments/after_d2_01_03/materials/readonly_live_facts.json](../materials/readonly_live_facts.json)；SHA256 `391487ffea9c12f21f5444369dd2b87b48897ac363a032a6ea107e5507df7b8f`。
- [eval/experiments/after_d2_01_03/runtime_eval/V2-freeze.json](../runtime_eval/V2-freeze.json)；SHA256 `3ad25aadb38312a2717b634ff34a61bd813f561f7e114e21e7766df21053f3bf`。
- [eval/experiments/after_d2_01_03/runtime_eval/V2-code-snapshot.json](../runtime_eval/V2-code-snapshot.json)；SHA256 `536a8754beed70fddcc1aa05dc0a5188684568cb6759dd55573eebd2cbe868da`。
- [eval/experiments/after_d2_01_03/reports/scoring-protocol-draft.md](scoring-protocol-draft.md)；SHA256 `b8f6b7d1d1d531d810a2244f6662db767d9654bc14e1bafa7a10637f918b480e`。
- [eval/experiments/after_d2_01_03/runtime_eval/version-changes/V2/after/qa_agent/sql/ratio_guard.py](../runtime_eval/version-changes/V2/after/qa_agent/sql/ratio_guard.py)；SHA256 `949972c28011b2939cdcaab10a79c7ef81c25c294f7feab2ab0505d94aa477aa`。
- [eval/experiments/after_d2_01_03/runtime_eval/version-changes/V2/after/qa_agent/sql/validator.py](../runtime_eval/version-changes/V2/after/qa_agent/sql/validator.py)；SHA256 `6d428203005eac59acd482c3b6c397dae8c3062de7a13d7abf5f74b908e4fb43`。
- [eval/experiments/after_d2_01_03/runtime_eval/version-changes/V2/after/qa_agent/pipeline.py](../runtime_eval/version-changes/V2/after/qa_agent/pipeline.py)；SHA256 `35a179a0e09772b292f68292ddce52f804c358f86442fa13b72f381bec3f3982`。

- gold标准SQL和此前只读结果存档完整读取，本次0数据库查询，未宣称重新实跑标签。
- 原可评分23/排除7，全部固定49/60分母与原评分保留；AI分对象判断不能转换成新EX。
- source当前已回退V1时，V2使用修改后字节档案和版本snapshot证据；不拿当前源码冒充旧运行。
- L1 switch元数据仅为可用性证据；没有实际choice请求时不写完成口径按钮切换。
- FAILED仍可能包含生成SQL字符串；只有实际SUCCEEDED/EMPTY_RESULT且有结果表才列入已执行SQL，误拒的SQL为未执行。
- 本审计者曾负责D3澄清代码及V2守卫，不能宣称角色盲审；父任务独立二遍与真实版本运行另外保存。
- 未填写A/B签字或人工确认日期，pending_human_review保持。

原标签及该版本score SHA前后相同，证明记录见JSON。没有A/B签字或人工确认日期。
