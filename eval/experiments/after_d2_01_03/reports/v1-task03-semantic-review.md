# V1 专项03逐项语义AI预审

Final selected V1 snapshot。逐项重读30道原题、标准SQL和存档结果、53份原始响应及71份原provider，本版本响应与checkpoint全部一致。没有新API或数据库调用，没有修改业务、prompt、标签、controller、scorer或人工记录。

原自动分数：专项03 **4/23**，全部 **18/49**。分对象AI结论不是重新计算的EX，原49可评分/11待标签审核以及本组23可评分/7排除保持。

| 对象 | AI建议通过 | AI建议有条件通过 | AI发现错误 | 证据不足 |
|---|---:|---:|---:|---:|
| 参考答案、分类与控制器依据 | 16 | 7 | 7 | 0 |
| 本版本系统实际完整行为 | 11 | 6 | 13 | 0 |

[eval/experiments/after_d2_01_03/reports/v1-task03-semantic-review.json](v1-task03-semantic-review.json)包含原标准SQL、每轮实际SQL/表/意图/卡片、原评分、controller事件及所有证据SHA。

**Final V1实际风险：** 14“每年”误当国家值；18SQL两年正确但持久意图仅2022；22漏已给分子而反问；23/26/27部分合法追问fresh路由丢旧条件；28实体替换未完成；30中文对象ID绕过必问期间。03/13/21地区标签依据与Top1/缺N默认边界单列待人工。

| 原编号 | 原分类/可评分 | 参考AI判断 | 实际系统AI判断 | 本版本结局 |
|---|---|---|---|---|
| sp03-01 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-02 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-03 | L0 / 可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-04 | L1 / 可评分 | AI建议有条件通过 | AI发现错误 | finished |
| sp03-05 | L1 / 原排除 | AI建议有条件通过 | AI建议通过 | finished |
| sp03-06 | L2 / 原排除 | AI建议有条件通过 | AI建议有条件通过 | controller_unanswered |
| sp03-07 | L2 / 可评分 | AI建议通过 | AI发现错误 | controller_unanswered |
| sp03-08 | L2 / 可评分 | AI建议有条件通过 | AI建议有条件通过 | controller_unanswered |
| sp03-09 | L2 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-10 | L2 / 原排除 | AI发现错误 | AI发现错误 | finished |
| sp03-11 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-12 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-13 | L0 / 可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-14 | L0 / 可评分 | AI建议通过 | AI发现错误 | controller_unanswered |
| sp03-15 | L0 / 原排除 | AI发现错误 | AI发现错误 | finished |
| sp03-16 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-17 | L0 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-18 | L1 / 可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-19 | L1 / 可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-20 | L1 / 原排除 | AI发现错误 | AI建议通过 | finished |
| sp03-21 | L2 / 可评分 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-22 | L2 / 可评分 | AI建议通过 | AI发现错误 | controller_unanswered |
| sp03-23 | L2 / 原排除 | AI建议有条件通过 | AI发现错误 | finished |
| sp03-24 | L2 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-25 | L2 / 原排除 | AI发现错误 | AI建议有条件通过 | controller_unanswered |
| sp03-26 | L2 / 可评分 | AI建议通过 | AI发现错误 | finished |
| sp03-27 | L2 / 可评分 | AI建议通过 | AI发现错误 | post_completion_incomplete |
| sp03-28 | L2 / 可评分 | AI建议有条件通过 | AI发现错误 | post_completion_incomplete |
| sp03-29 | L2 / 可评分 | AI建议通过 | AI建议通过 | finished |
| sp03-30 | L2 / 可评分 | AI建议有条件通过 | AI发现错误 | finished |

## sp03-01

原题：Chinook 里2020年全年的发票销售额是多少？如果那一年没有发票记录，请直接说没有可用记录，不要用0代替。

**参考：AI建议通过。** 2020年、发票SUM(total)、无记录保留NULL均明确；存档gold为NULL。

**系统实际：AI建议通过。** L0真实执行2020半开期间SUM(total)=NULL；未替成0，回答按无可用记录处理。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-01/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-01/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `8ae96cae16e1a7d92c97aeb89d8430594019d15a1207fabd182fd953b69ffd74`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-01/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-01/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `71167e430607e54fafacdc9f9c937fdcd0871532583c331e60a624c0dcd77f7d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/df0a74de953145da8e79b0a93e823d72.json](../runtime_eval/provider-captures/V1-001/df0a74de953145da8e79b0a93e823d72.json)；request.messages/response.choices[0].message.content；SHA256 `153c2e7c2cccba2cbc0c4218787c08a80f0e1598aca06def46e67f484da6685c`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/13001a2c1f1a4321aadc423b37357304.json](../runtime_eval/provider-captures/V1-001/13001a2c1f1a4321aadc423b37357304.json)；request.messages/response.choices[0].message.content；SHA256 `36b73bbf0a0cab6b69df73303d380b677f7d4618fc9acd14aea35043e264299f`。

需人工确认：确认NULL展示措辞即可。 状态 `pending_human_review`。

## sp03-02

原题：How many customers reside in France?

**参考：AI建议通过。** reside明确customer.country=France，客户COUNT正确，存档5。

**系统实际：AI建议通过。** reside France明确客户所在地；真实customer.country=France COUNT=5，L0直接执行。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-02/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-02/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `081a1e21abf14d2cd7174a554ddd5c26504e415edf60f18bdbc9d6bda88268be`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-02/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-02/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `9d30501c49c6d67a5925414471cbda50b4cb91516795a82bfde0f1244dea5d93`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/1b13ede79aaf4f69adb4b3508751868a.json](../runtime_eval/provider-captures/V1-001/1b13ede79aaf4f69adb4b3508751868a.json)；request.messages/response.choices[0].message.content；SHA256 `d936a29a6eda57c64fd88fcb515bc9ab68d235ecd2ef13a0db439f5c6b0777c7`。

需人工确认：无新增口径事项。 状态 `pending_human_review`。

## sp03-03

原题：2024年巴西的销售额同比2023年增长了多少？

**参考：AI发现错误。** 题目仅‘巴西销售额’，未给客户所在地/账单国；固定L0和唯一customer.country gold缺业务依据。gold在明确客户归属条件下计算本身正确，不能据当前两国字段相等证明唯一。

**系统实际：AI建议有条件通过。** 实际L2只问地区归属，保留2024/2023、发票金额与同比；国家金额缺客户/账单归属，澄清有依据。controller没有合法region补充，最终SQL未运行；参考唯一归属仍不能确定。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-03/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-03/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `5ff563ede36bb450c5b60ceee999d21318df212eca9559ddb3deccb56ad5f8d4`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-03/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-03/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `e9049a4277f23780f916276754bbbf5731409f58c99343abbba1a572b69cc8b6`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/9f6327e14354489396a91b4dfd834cee.json](../runtime_eval/provider-captures/V1-001/9f6327e14354489396a91b4dfd834cee.json)；request.messages/response.choices[0].message.content；SHA256 `b18b9367b39406fb1f997fafd4115149a15db51353656b5e0fa74d08f23eae22`。

需人工确认：明确这类国家销售额是否必须问归属；既有材料没有国家默认。独立单案例报告保留。 状态 `pending_human_review`。

## sp03-04

原题：2023年按销售额排名最高的曲目。

**参考：AI建议有条件通过。** 曲目明细金额、2023、Top10登记默认与gold匹配；L1默认实际是条数，输入已经明确销售额。‘最高的’是否接受默认10及开关应对应条数，需要明确，不能因L1强行把显式销售额当缺失指标。

**系统实际：AI发现错误。** 真实Top10明细金额/2023/track_id稳定排序、核心结果符合gold；额外track_name是展示列。但L1仅TopN默认声明，switch=null，没有该默认的切换控件。本轮未实际点击L1开关，不能据评分列数fail称金额错误。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-04/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-04/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `aaa82ee8163cc9ffee4d2b483d09558d5824e8d03513a644afd990f746e0778d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-04/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-04/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `3f2a5b04b40ede0c96c28e67648fa5cdb23a33edb918ab3a4064db829197cc24`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/9586717a0cef4f51b5b445acf20ee2c9.json](../runtime_eval/provider-captures/V1-001/9586717a0cef4f51b5b445acf20ee2c9.json)；request.messages/response.choices[0].message.content；SHA256 `ca1879ee5774afe031ad3d99aae11ddb28bbaf99f1ae4a96b3f8e724eed670fe`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/f9b865af3daf48db89bdc18d575997a0.json](../runtime_eval/provider-captures/V1-001/f9b865af3daf48db89bdc18d575997a0.json)；request.messages/response.choices[0].message.content；SHA256 `0515b0a370931113120f454fd2f9e680009e8eac2eb5067808edcb3c9b9d24d4`。

需人工确认：确认TopN默认的切换交互和该题自然语言条数含义；不改原评分。 状态 `pending_human_review`。

## sp03-05

原题：2007年最受欢迎的10首爵士曲目是哪些？

**参考：AI建议有条件通过。** 2007明确且无数据应空结果；登记热门数量默认支持L1。旧两遍争议导致原scorable=false，仍保留；空结果不意味着应该补最近年份。

**系统实际：AI建议通过。** 实际L1、Jazz曲目数量、2007范围、Top10及track_id稳定并列键均保持，返回空；LOWER(genre.name)=jazz在当前目录Jazz对象下可定位对应流派，不按空结果单独证明逻辑。switch有元数据但未点击。原排除保留。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-05/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-05/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `890207ddffa695c4c85ea95666fa3fdebbc76b66ab9873e46feab827d67fa57a`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-05/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-05/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `256de699047a1beb7576708e7c5ef35f7e5a9e3efe0b1fda8bcf1b47cae811ab`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/1414a9e0705f4cf3a3ac195502ff548a.json](../runtime_eval/provider-captures/V1-001/1414a9e0705f4cf3a3ac195502ff548a.json)；request.messages/response.choices[0].message.content；SHA256 `53a5f3fb1fdf86803b4a57baae7584cca06f3bd07c22e3866fe104a70403bec7`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/2eeac737bb8d42ed98b2b82b68b769f9.json](../runtime_eval/provider-captures/V1-001/2eeac737bb8d42ed98b2b82b68b769f9.json)；request.messages/response.choices[0].message.content；SHA256 `837b5b5f08d444d4dbb49821e0348bf6dc2d9ed8775567d876088724d46eefe8`。

需人工确认：保留原待确认；确认当前空年是否仍作为有效题，稳定ID排序不能靠空结果认定通过。 状态 `pending_human_review`。

## sp03-06

原题：销售额同比增长多少？

**参考：AI建议有条件通过。** 销售额与同比已明确，只缺当前期间；gold在补2024后合理。离线回答含current与base，与逐key控制器及重复time标志卡粒度失配；旧排除仍保留。

**系统实际：AI建议有条件通过。** 初始L2缺期间正确，额外time_ambiguous/current两条同域问题；controller在提交前因bundled补充拒绝，只有初始请求。没有最终SQL，不能把V2的实际年份按钮与percent结果写到V1。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-06/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-06/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `d056fd5150dff0bfc44153b88536880acfce94e2a7be799571feddd0d100d9c7`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-06/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-06/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `45ed2fb48076de0ded853817bcbb7758d73fbe9a55540f68cbd231fc61bf1f42`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/684d1cf4347e45928c257ea17ab769f3.json](../runtime_eval/provider-captures/V1-001/684d1cf4347e45928c257ea17ab769f3.json)；request.messages/response.choices[0].message.content；SHA256 `794f57733827a548efc7fe1dce9a5e102cbe19595fb05f821a5239d0abf4b63a`。

需人工确认：确认一次补充同一时间条件是否可以包含明示基期；冻结controller本轮不动。 状态 `pending_human_review`。

## sp03-07

原题：2024年账单国是美国的发票销售额占比是多少？

**参考：AI建议通过。** ‘账单国是美国’明确billing_country；分母仍缺，应问分母。补全库2024后gold FILTER分子/同期间全库分母正确。

**系统实际：AI发现错误。** provider已识别账单国家USA，程序仍覆盖为region歧义；实际先问地区和分母，真实补全球2024分母后仍反问地区。两轮均无SQL，不能写成V0只问地区或V2猜分母；题面已明确地区却重复追问是真实错误。

真实请求 2 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-07/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-07/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `e767d4aa7c0a47be666b87d86a42c071700eab05f1c8513db2205e70c17bce5b`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-07/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-07/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `37715caaef845f2eb2fd8bd00a3f7a32874a726cfd4d0863da252c95ca666e04`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/c39a35dc98a44de995522a8f17568eac.json](../runtime_eval/provider-captures/V1-001/c39a35dc98a44de995522a8f17568eac.json)；request.messages/response.choices[0].message.content；SHA256 `5739ccd83a299450e9d16a37b4328987e07566e6a559fcbacd9477d576e8fb05`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-07/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-07/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `c5504233651ced1292657a179f6ba34d172dcc45bbf919409d04999a098e24dd`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/4742c0c1a6544ef3986a467708c24cba.json](../runtime_eval/provider-captures/V1-001/4742c0c1a6544ef3986a467708c24cba.json)；request.messages/response.choices[0].message.content；SHA256 `8ac17e8c19118fcbd01d0e4f7d5896376509c980181dc6197143ceb4673d6f4d`。

需人工确认：保留分子/分母区分；不能通过取消所有地区澄清规避短语覆盖问题。 状态 `pending_human_review`。

## sp03-08

原题：2023年谁买得最多？

**参考：AI建议有条件通过。** L2缺对象正确；客户/花钱补充后发票金额、2023、Top1 gold正确。补充同含object与metric，当前卡两项均问，单key控制器却拒绝整条；这是离线控制器适配争议。

**系统实际：AI建议有条件通过。** 初始问metric和rank_object合理，不强选谁为客户。离线补充同时回答同卡两项，却被单key控制器称another unasked而拒绝；没有把补充发送系统，最终未运行。Top1/Top10属于后续参考边界，不改原评分。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-08/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-08/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `62179a431c4bf13aba0ff1248bd348e36904a4bf2d13432813efe9770455e6d7`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-08/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-08/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `f8575a4482990ef99c314e4b1886c61fbad202b25c3995c90d2872e99ce75249`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/5d9eecf7bc204bf68f441a50bf4acbb2.json](../runtime_eval/provider-captures/V1-001/5d9eecf7bc204bf68f441a50bf4acbb2.json)；request.messages/response.choices[0].message.content；SHA256 `3e5f8cdde84994b694bb25c154932354fe05c8c370f72ed57bf8b6e2ba518c49`。

需人工确认：确认控制器只准一个issue还是允许一次回答卡内多个问题；原版本标签/score不动。 状态 `pending_human_review`。

## sp03-09

原题：2024年摇滚曲目卖了多少张？

**参考：AI建议通过。** 摇滚两候选关系非自动绑定；用户选择Rock后2024销售数量SUM(quantity) gold164正确。

**系统实际：AI建议通过。** 初次摇滚两候选L2；真实稳定choice选择Rock后按2024明细数量求和164，字段与期间正确。SQL使用COALESCE，当前非空结果不受影响，不能据此安装所有SUM空集=0的默认。

真实请求 2 轮；已执行SQL轮号 [1]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-09/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-09/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `c2a3c328d16a3e16ed36f74288ac2502f116479c979347199de7607ad08c290d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-09/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-09/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `6fb17b765b7337c680401ce4164863ab19d321af422b75b04c71a4938e169d17`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-09/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-09/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `a01dd8d6cf7f9e7c105ece03e3af7af890da6680c2c8e010fa6dac83c9679e9c`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/408d20ff643941dfb5d4c66893063cec.json](../runtime_eval/provider-captures/V1-001/408d20ff643941dfb5d4c66893063cec.json)；request.messages/response.choices[0].message.content；SHA256 `8dd966b79304d7db4986a92ccfbebb464ee8e3ecc706cf1a0b222f327e8e15d0`。

需人工确认：无新增业务事项；此题是实际按钮闭环，不能与自由补充混称。 状态 `pending_human_review`。

## sp03-10

原题：2024年巴西的客户有多少？

**参考：AI发现错误。** ‘2024年巴西客户数’未明确在2024购买的活跃客户、年末存量或新增客户；customer表无创建日期。gold擅加年度购买活动定义，不能从复购规则推广一般客户数。旧排除保留。

**系统实际：AI发现错误。** 实际customer.country=Brazil COUNT5完全不使用题面2024，而intent记录2024；真实期间语义被忽略。参考活跃客户4定义也未获一般客户数口径批准，不能强称5必错或4唯一，应先确认时间对应客户活动还是存量。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-10/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-10/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `b02b7748b687f79fcf0ee7d761505c3a1c590868c5ef5724f5b81f411adc5b0b`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-10/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-10/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `8e407fb66097157cad652df2869d6da2a73569d30a61e67d0fa1c153e85d1be6`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/7241306c797346f89b2c30606b5c0690.json](../runtime_eval/provider-captures/V1-001/7241306c797346f89b2c30606b5c0690.json)；request.messages/response.choices[0].message.content；SHA256 `a5464f4dfc46b68bf49bc1d21c4f5a8737de53b51353ecc05bf7a7a8a4699c11`。

需人工确认：优先确认客户数的时间语义；不增全局活跃客户默认。 状态 `pending_human_review`。

## sp03-11

原题：How many customers reside in the USA?

**参考：AI建议通过。** reside USA明确客户所在地，COUNT客户gold13正确。

**系统实际：AI建议通过。** 真实reside USA→customer.country COUNT13、L0，未用账单国家。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-11/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-11/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `7032f5ad855949d06972575d0c1ab1fb56c83ed34be3c0cf97e7cbe218dc9237`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-11/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-11/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `4553e93cdd5f9e174c9ca10d6a4111a1e8631c7344409a395af2d551c2990feb`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/e7b1c7bd086648ffbe3d573466ab2484.json](../runtime_eval/provider-captures/V1-001/e7b1c7bd086648ffbe3d573466ab2484.json)；request.messages/response.choices[0].message.content；SHA256 `a86697a1147c7c01217965370fe7e8f0d7b522dd6954c73cfb275f57430f7115`。

需人工确认：无新增业务事项。 状态 `pending_human_review`。

## sp03-12

原题：意大利有多少客户？

**参考：AI建议通过。** 明确问客户，Italy客户所在地COUNT1，未问金额或账单。

**系统实际：AI建议通过。** 真实Italy客户所在地COUNT1、L0，未引入金额或发票活动。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-12/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-12/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `42a9534e57c1522b20548dac8a472e2be089610f4ad91e85b3c6451737649ecc`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-12/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-12/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `91a0142a747986122783725a3f2fc1db80eb7f19ec40b8a786fb7e070a11fd6b`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/eb014ee398e0495a91b39e8a88144654.json](../runtime_eval/provider-captures/V1-001/eb014ee398e0495a91b39e8a88144654.json)；request.messages/response.choices[0].message.content；SHA256 `24b9267b7cccc84c302a8b3b618755a40da72a036843c027ae40c219d5539c41`。

需人工确认：无新增业务事项。 状态 `pending_human_review`。

## sp03-13

原题：What was the total invoice revenue for Canada in 2024?

**参考：AI发现错误。** invoice revenue确定金额粒度但‘for Canada’未明确地理归属；唯一billing_country和L0缺已登记依据。该gold在明确账单国后正确，不能由快照同值证明题意唯一。

**系统实际：AI建议有条件通过。** 真实L2问地区归属，保留2024/发票金额；invoice revenue限定金额粒度，不等于Canada已经选账单国家。controller无region来源，最终未运行；参考新争议单列。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-13/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-13/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `630eb49cfc17ee52bf45dcd16f800fc7908dd885ff4746d11c95d92a7368e519`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-13/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-13/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `0c7599823449ffc80d6639f35f417cae4a04502c650511f9441b290f78a12905`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/d6cef0430da34631be8c63cc1c42a22a.json](../runtime_eval/provider-captures/V1-001/d6cef0430da34631be8c63cc1c42a22a.json)；request.messages/response.choices[0].message.content；SHA256 `2d751cd817fc92d9e7c813b3c042f06650d3a2aeb3ef7cce7711d5b777dcac91`。

需人工确认：与03统一确认国家金额口径，不因英语invoice上下文自行安装默认。 状态 `pending_human_review`。

## sp03-14

原题：2022年和2023年，Chinook 每年的发票销售额分别是多少？

**参考：AI建议通过。** 两年逐年SUM invoice.total，2022至2024半开范围、year排序gold481.45/469.58正确。

**系统实际：AI发现错误。** 本轮value_adjudication原provider将“每年”判ambiguous，候选竟为USA/Italy等账单国；实际L2反问“每年具体哪个对象”，无SQL。题意已经明确两年逐年发票金额，这是真实值提取/候选裁决误澄清，不是合法地区口径歧义。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-14/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-14/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `a5c7c5f65658d66d66a73ce6f2cc62a266a09139863a2538070d8c8105f9ebd3`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-14/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-14/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `a7b8f48f975bff415624059aa721c0bc9fb851607a2211c1c3f189c80e65cb3a`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/49044919abeb4a8caef9cc81548529eb.json](../runtime_eval/provider-captures/V1-001/49044919abeb4a8caef9cc81548529eb.json)；request.messages/response.choices[0].message.content；SHA256 `42ab3eeb095250d668412fa9d44a38608f614398e3cb76f842eefac3ff5cf12e`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/8f5ee85f06104b14bf4e1e766faa1ddd.json](../runtime_eval/provider-captures/V1-001/8f5ee85f06104b14bf4e1e766faa1ddd.json)；request.messages/response.choices[0].message.content；SHA256 `17ae0b393d77ed9bfed338eee7944e4d38abe5dd500fb0d922cde0c2023a6dcb`。

需人工确认：可确认年份展示类型；不改scorer或gold类型。 状态 `pending_human_review`。

## sp03-15

原题：2009 年和 2010 年之间，哪首曲目最受欢迎？

**参考：AI发现错误。** 热门购买数量使用登记默认应L1，标签L0与business_basis‘默认使L0’错误，原source guard已指出并排除；SQL数量/2009–2010/Top1自身正确。

**系统实际：AI发现错误。** 真实数量默认L1和2009–2010期间正确，但provider没提取“哪首”为Top1，程序补Top10、SQL LIMIT10；实际空结果掩盖单数排名差异。原分类L0错误仍排除，不能把空结果等同完整题意通过；与最高/缺N默认边界交人工确认。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-15/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-15/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `2255bcc5365d004fa6fa221ae18572a608d4f6c392129a82a723bff53b7eedbc`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-15/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-15/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `f7ad30f4b0ac479728aa500075753dcbd0a152e3fc92627c61949d7be91db773`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/b880888ffc544f9caeae01aa92248e7d.json](../runtime_eval/provider-captures/V1-001/b880888ffc544f9caeae01aa92248e7d.json)；request.messages/response.choices[0].message.content；SHA256 `7ac9d55b01db56a80bf34e22aeec369c1886516f5e70474dea1e4ff26f05c4e0`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/17fe08a7663341f5bc7d5ea4612588bd.json](../runtime_eval/provider-captures/V1-001/17fe08a7663341f5bc7d5ea4612588bd.json)；request.messages/response.choices[0].message.content；SHA256 `82be42e2ae414c03307f6030cdf0764506857f70b536c5296f497cdfbff2153a`。

需人工确认：原分类争议待人工，继续保持原排除，不新计成绩。 状态 `pending_human_review`。

## sp03-16

原题：Chinook 里 Jazz 流派的曲目有多少首？

**参考：AI建议通过。** Jazz明确流派，曲目COUNT JOIN genre正确，gold130。

**系统实际：AI建议通过。** 真实Jazz目录曲目COUNT130，track→genre关联和字段过滤正确。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-16/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-16/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `ae07a98094eb0f456fb0baba77ed9c2f55fb176c30c0771069e5cb1e8c93a585`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-16/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-16/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `e5216424300a597498143d958c274c90528f9826bb405a8c4ae8743e059d2c7d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/56e94708326f455fa81a77e8178bfc78.json](../runtime_eval/provider-captures/V1-001/56e94708326f455fa81a77e8178bfc78.json)；request.messages/response.choices[0].message.content；SHA256 `c873a31eab819ff9061327802e9ac8fb5cc5f38ecdc94f301a373550d1963bf2`。

需人工确认：无新增业务事项。 状态 `pending_human_review`。

## sp03-17

原题：2020年全年复购（至少开2张发票）的客户有多少位？如果没有，请如实输出0。

**参考：AI建议通过。** 明确期间至少两张发票，按客户GROUP HAVING COUNT>=2，再外COUNT；无符合客户输出0，gold符合已确认复购定义。

**系统实际：AI建议通过。** 真实2020期间每客户至少2发票HAVING，再外COUNT=0，符合已确认复购口径与COUNT空集行为。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-17/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-17/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `b1fd46775bb9f8175949124393401a6a36d79e0e469b29dadd34a956997984fa`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-17/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-17/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `951af32ee6cc8725dffc76716be59f47cc8100ad16a38ba7c22d9b10707f90af`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/f57471d244d24a03996e7f7bb04f8786.json](../runtime_eval/provider-captures/V1-001/f57471d244d24a03996e7f7bb04f8786.json)；request.messages/response.choices[0].message.content；SHA256 `867bdca78b5f214b7e4a328e84313ea436ba715fc987682310127b7cba487177`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/06c242b7a91a489486b43436fbe32693.json](../runtime_eval/provider-captures/V1-001/06c242b7a91a489486b43436fbe32693.json)；request.messages/response.choices[0].message.content；SHA256 `9e52e30084d43ee601dd0bf41a32241b12fed57175a66d356218a77d0d5ab783`。

需人工确认：无新增业务事项。 状态 `pending_human_review`。

## sp03-18

原题：2021到2022年最受欢迎的曲目有哪些？

**参考：AI建议通过。** 2021到2022两年范围、数量默认和Top10默认、track_id排序，gold包含两年正确。

**系统实际：AI发现错误。** 本轮实际SQL覆盖2021–2022两年、数量/Top10/track_id排序正确，核心结果符合参考；但Intent.current仍被日期覆盖为仅2022。当前答案可正确，持久意图存在真实期间丢失，不能照抄V0实际SQL仅2022，也不能仅金额一致批准完整状态。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-18/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-18/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `08de7b3c8a3e515ab65517d2773114b3e22ccbf164dc9916593ba052f690c39c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-18/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-18/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `80d702d59da743cddad585e3f86e492c951bd2b37762a29bd3c37a9552c1d929`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/eb8563b6729e4c239e1697c43d613d24.json](../runtime_eval/provider-captures/V1-001/eb8563b6729e4c239e1697c43d613d24.json)；request.messages/response.choices[0].message.content；SHA256 `0feb4a09d45de2862e9bc75a5bc1b997cbbc4a1a6f46252bdb3173c10c262703`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/f9254ab4c7bf4068a5b4846c4ad254c8.json](../runtime_eval/provider-captures/V1-001/f9254ab4c7bf4068a5b4846c4ad254c8.json)；request.messages/response.choices[0].message.content；SHA256 `94addba15175701351f3330eaf05fbb0d2c0ccdee022894d03c1cdd4ffe10d04`。

需人工确认：日期解析改动需后续另立代码任务，不能让prompt输出绕过程序覆盖。 状态 `pending_human_review`。

## sp03-19

原题：2022年买得最多的客户是谁？

**参考：AI建议通过。** 对象客户明确，已确认金额默认、2022按customer_id合计取金额最高一位，gold45/32.75正确。

**系统实际：AI发现错误。** 真实2022客户发票金额Top1=45/32.75正确，多姓名列不改变客户粒度；L1金额默认声明却switch=null，未提供切换控件。题目SQL正确和完整默认交互缺口分别记录。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-19/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-19/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `73c94e1b743fd6425f2f957bcb26b507bf22f56eb78f70e875dc3a24d8e2a10e`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-19/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-19/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `e75d030d47fc98aa299dfce8c9a784120e6f499eee7606fcae6fcc1dc0959323`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/729811cfda3c4325a73ac53bd19c1995.json](../runtime_eval/provider-captures/V1-001/729811cfda3c4325a73ac53bd19c1995.json)；request.messages/response.choices[0].message.content；SHA256 `f3a89eb53ab246393e84e01fb64b982a1e892b0ce1abe386c836b85f9dd81722`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/e86cd7a3d5a54928b784d32b0c6c38b5.json](../runtime_eval/provider-captures/V1-001/e86cd7a3d5a54928b784d32b0c6c38b5.json)；request.messages/response.choices[0].message.content；SHA256 `67c866a980ba6813a811b09dbdf9406ce483e5dcc790a04a194d0f54304092a8`。

需人工确认：确认客户金额默认可切换的备选指标是否登记；不能凭空加新业务默认。 状态 `pending_human_review`。

## sp03-20

原题：2023年按销售额排名最高的艺术家，取前10名。

**参考：AI发现错误。** 输入明确2023、艺术家、销售额、前10名，没有待应用的登记默认；L1标签不成立，原source guard已排除。gold金额/排序自身正确。

**系统实际：AI建议通过。** 实际L0、2023艺术家明细金额Top10及artist_id稳定并列排序正确，无默认待应用。原L1标签已排除仍保留，name附列不改变对象粒度。

真实请求 1 轮；已执行SQL轮号 [0]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-20/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-20/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `c0d7d7d70a21072409b7d1bf65945de70ec035abb34919ecb7c73ee47edc758a`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-20/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-20/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `fbeea0bb50ad8e5fee8ed1a5e191ec98f1a394771b39667fd2573907bee8b1c2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/1b129b31cc7646bdbb308cdbe90b7a46.json](../runtime_eval/provider-captures/V1-001/1b129b31cc7646bdbb308cdbe90b7a46.json)；request.messages/response.choices[0].message.content；SHA256 `fa9bcbda51b7d4671ce5a3084da655cd9becb2b0d8baa69004b822a3dae870fb`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/5ead2e3e9452478ba6eb9c047bbc058d.json](../runtime_eval/provider-captures/V1-001/5ead2e3e9452478ba6eb9c047bbc058d.json)；request.messages/response.choices[0].message.content；SHA256 `0171a72d56676bf5ba355bb5cb31844b112a5617bc6657ad071b916ed3b959e9`。

需人工确认：保留分类人审，不按运行结果将scorable改true。 状态 `pending_human_review`。

## sp03-21

原题：德国的销售额同比增长多少？

**参考：AI发现错误。** L2缺年份正确但参考声称仅缺期间、默认customer.country德国缺依据；controller只有time补充，没有合法地区补充，最终唯一客户归属gold条件不完整。

**系统实际：AI建议有条件通过。** 实际问期间与地区有依据，未猜最近年；controller因time同域补充bundling停止，只有初始请求。参考只缺期间并指定customer德国缺依据，不能把未发送补充后的结果写成错误金额。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-21/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-21/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `a5889c1ba4fb9f7594f77da03ec6920be4d8fb340b4da84b9fab13d88a5e7e68`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-21/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-21/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `57115937dfee0dab164b3232ae0423f84f8f8b2f0098f87471e408b79be39377`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/efc2f72907cc4bd58f9ec47634f6f7e7.json](../runtime_eval/provider-captures/V1-001/efc2f72907cc4bd58f9ec47634f6f7e7.json)；request.messages/response.choices[0].message.content；SHA256 `7f9a2add6be4ac7f1021150d39277d433a5e470db8c8213f9846387fa061e154`。

需人工确认：确认地区归属并补合法controller来源后需统一新标签评测；本轮不更改。 状态 `pending_human_review`。

## sp03-22

原题：2024年法国居住客户的销售额占比是多少？

**参考：AI建议通过。** 法国居住客户明确分子；分母补2024所有发票后应全库分母，gold0.0767700458609930正确且防零。

**系统实际：AI发现错误。** 本轮P2漏掉题面明确“法国居住客户的销售额”的numerator，虽country绑定正确，却同时问num/den；真实补2024所有发票分母后仍反问分子，controller无多余num补充而止步。全轮无SQL；V0的错误100和V2的守卫拒绝都不能移植为本轮实测。

真实请求 2 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-22/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-22/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `6be0674e83610a2e452b5f06a189c3fb8bb9d873215d2e698378772f39c852ae`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-22/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-22/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `9a0e84547e481747eb3b29a32adb8f69d6684b761240c8d2b26611ee18f7dda3`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/c00f628343ea4aec9cb9a479d3be6432.json](../runtime_eval/provider-captures/V1-001/c00f628343ea4aec9cb9a479d3be6432.json)；request.messages/response.choices[0].message.content；SHA256 `1baa07a2ca8eb6cde0421e04187e07810862e39050726d1aa96b666c57a3d579`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-22/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-22/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `c6d366a7da59db4d2fc5c10f3853a6ffe566f06ef3ab5d01641459bdb7cd27e5`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/5151f0316b8c406aa388c4ce2119c9ca.json](../runtime_eval/provider-captures/V1-001/5151f0316b8c406aa388c4ce2119c9ca.json)；request.messages/response.choices[0].message.content；SHA256 `7b885c816a6671818e3f916ef7e0c234ee151887e9b9345304a867aaede56ee7`。

需人工确认：优先处理比例范围模型与SQL绑定校验职责；不能为通过关闭其它问题全局筛选守卫。 状态 `pending_human_review`。

## sp03-23

原题：2023年谁买得最多？

**参考：AI建议有条件通过。** 与08重复初始输入，原scorable=false保留；客户2023金额及改2024目标合理，但重复题不能重新纳入分母。

**系统实际：AI发现错误。** 初始选客户后2023客户金额winner46/32.75正确；随后真实“改看2024年”被路由成fresh lookup，执行2024全83张发票SELECT*，丢客户排名对象/指标。原重复题排除保留，未把V2全库汇总SQL说成V1。

真实请求 3 轮；已执行SQL轮号 [1, 2]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-23/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-23/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `4a89ace772bf9fa39ce1a703f5262ebd65a5c141d51a376a14fd46ebd60369c8`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-23/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-23/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `63ffd1e856b65c344aced0bc192c7ea975820ed1f2400e71d37a99656e7da00e`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/ee09111aba0b475180b96d430253ef1b.json](../runtime_eval/provider-captures/V1-001/ee09111aba0b475180b96d430253ef1b.json)；request.messages/response.choices[0].message.content；SHA256 `9ff500df80138c592500b4f48d4d5ba8ff6b953805ba5e3e0ad7bef8ddd39fc9`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-23/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-23/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `aa8b5e3492c6fd8944debd2f05235770ec4773d910e994132c61ce249623a9c3`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/dcf42f3dd3844c99bfdc8f727f041340.json](../runtime_eval/provider-captures/V1-001/dcf42f3dd3844c99bfdc8f727f041340.json)；request.messages/response.choices[0].message.content；SHA256 `30aa8053e5d656ef48d16c5f11c4bfcfd07998795f1b7fb6214244da6af3b6f9`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/f78bf42c9b4b48b8980c4d6b452d0c7d.json](../runtime_eval/provider-captures/V1-001/f78bf42c9b4b48b8980c4d6b452d0c7d.json)；request.messages/response.choices[0].message.content；SHA256 `ca00e452922be3f628bc60149beb982e4bfc258214b71edeb5a5b2d0542b4df5`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-23/turns/002/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-23/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `4aef62c945b8fa9ee4d0485ac81b9fb1b01993f282cd9ceb62344049f2888780`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/f8e1ae0063494d1087275aad77a8e5d1.json](../runtime_eval/provider-captures/V1-001/f8e1ae0063494d1087275aad77a8e5d1.json)；request.messages/response.choices[0].message.content；SHA256 `7058d71ed909df784a7547912d10e194be5e8d615bda6d40c9eda631c23adcc0`。

需人工确认：后续路由代码任务应覆盖合法改动表达；本轮prompt-only不伪装修复。 状态 `pending_human_review`。

## sp03-24

原题：2022年澳大利亚的发票销售额是多少？

**参考：AI建议通过。** 国家金额未明归属先L2，用户选customer.country后SUM total/2022/Australia，再改billing_country保值，gold均正确。

**系统实际：AI建议通过。** 真实地区choice选客户归属后2022 Australia金额0.99；真实改账单归属后invoice.billing_country SQL仍保2022/Australia、0.99。通过依据是两段字段来源及范围，非同金额巧合。

真实请求 3 轮；已执行SQL轮号 [1, 2]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-24/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-24/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `cc7dc0d077c051db4fd2425ed90c9f7c42af91642e29e5dc7ad80d4b11c9ef34`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-24/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-24/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `72fca761e75d6486554106e085b21902a832ce2681a87ce200c8759096ea5724`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/4c87094bf744451983cae37f90f49bea.json](../runtime_eval/provider-captures/V1-001/4c87094bf744451983cae37f90f49bea.json)；request.messages/response.choices[0].message.content；SHA256 `7e2440541020a028c4cc6c3527ceab9384a6275dc5efd655c76df2bf658076ff`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-24/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-24/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `c7128a867bdfd01be6d8b55d2f31a2c3c5bff63cea57beabf03e69855ae72d30`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/460eda7337a2486da482478b523d2964.json](../runtime_eval/provider-captures/V1-001/460eda7337a2486da482478b523d2964.json)；request.messages/response.choices[0].message.content；SHA256 `adcaa6aa7fc79d5c413c76b0ce45b893eb1e2125aeefb708ebf9630acc7c0bbe`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-24/turns/002/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-24/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `6a94dcc594237071ce7df77383fa839ba7b9d2233845cb4b8c1303b493c83892`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/d92fb8f9f072481c864ed7cbf70df593.json](../runtime_eval/provider-captures/V1-001/d92fb8f9f072481c864ed7cbf70df593.json)；request.messages/response.choices[0].message.content；SHA256 `7b2f39f7eee484cffd275ce69b0dae94cac0b7ebe25169e8b0446465d1a554b2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/ec7726b4a1bb4c428143547a1a4b2f62.json](../runtime_eval/provider-captures/V1-001/ec7726b4a1bb4c428143547a1a4b2f62.json)；request.messages/response.choices[0].message.content；SHA256 `776fac31cc3fbdc2653a3c4ef8df87ddf364e71d8a40ca78f587f76aceb7abfd`。

需人工确认：无新增业务事项；这是实际国家归属迁移闭环。 状态 `pending_human_review`。

## sp03-25

原题：2024年摇滚曲目的销售额是多少？

**参考：AI发现错误。** 两个允许补充分别指Rock和Rock And Roll，但唯一final gold=Rock，原source guard已指出冲突并排除。value补充还缺column，不能从candidate label强猜字段。

**系统实际：AI建议有条件通过。** 真实摇滚两候选L2正确；controller离线value缺column且允许Rock/RockAndRoll与唯一gold冲突，不能唯一匹配而停止。没有选择、最终SQL或口径切换，原排除保留。

真实请求 1 轮；已执行SQL轮号 无；生成未执行SQL轮号 无；计划后续未执行 1 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-25/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-25/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `acf3a9f68acdd070a38f71bcb29c711c0f74fbfcf61d65899c8d70f7e84c4a1c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-25/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-25/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `10e1a444ed27334c1baa94c376f39b8b88dbd1cfba550ae86d911ef3a33f4964`。

需人工确认：先统一允许补充与目标来源，未来统一新版标签重评；本轮保持原排除。 状态 `pending_human_review`。

## sp03-26

原题：同比增长多少？

**参考：AI建议通过。** 同比缺metric/current先L2；补发票金额/2024后计算2024对2023，改2025再换AVG时应保留增长任务及2025/2024，gold正确。

**系统实际：AI发现错误。** 实际metric补丁+年份按钮后2024/2023增长fraction0.016930正确；改2025后当前450.58/基期477.53/-0.056436也正确，额外基期列只是投影差异。但“指标换成平均每张发票金额”真实fresh路由、执行全库AVG5.65194，丢2025/2024与growth，完整任务失败。

真实请求 5 轮；已执行SQL轮号 [2, 3, 4]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-26/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-26/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `c796470ef58360ea756d5cd21c6fea20b7acc55fdf12644ff99e738ce1dd9fe4`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-26/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-26/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `38d93312a6364a96c10f4ce21ef7cacf2995281bf9fd081994f07443880e2a46`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/4fcd1284fa71435d9e7e53ac6b616c00.json](../runtime_eval/provider-captures/V1-001/4fcd1284fa71435d9e7e53ac6b616c00.json)；request.messages/response.choices[0].message.content；SHA256 `cd07ac6cd5c8f46c2e3cdbcd065c8b3055e052c0e1afdff40cc43837345b445d`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-26/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-26/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `beacb17c8ce324863526b485ea4b3a7cb8c0b7f469f23c337ce6d6f9524e3efd`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/61ec66d71c5646589380916683114ce8.json](../runtime_eval/provider-captures/V1-001/61ec66d71c5646589380916683114ce8.json)；request.messages/response.choices[0].message.content；SHA256 `9307b17dbab8f75aca3d970b1c31b372f526ba1f0f3232976c97843370b4a825`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-26/turns/002/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-26/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `ed39786f5192e493576a897193e3b6d722695d74e393a9575e5e03a1903f6f6a`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/eb329d7abb94457aaae72e24bd7677bf.json](../runtime_eval/provider-captures/V1-001/eb329d7abb94457aaae72e24bd7677bf.json)；request.messages/response.choices[0].message.content；SHA256 `d9c247890397c9febc33252198faea545f2599f8ca765bb4ff2265b63e193483`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-26/turns/003/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-26/turns/003/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `cb446391c16d34641445f5c900e46c4d8b4361d843a90631ea267f7c838dcd43`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/6afb6c0ac2524cf6a6342578822c0911.json](../runtime_eval/provider-captures/V1-001/6afb6c0ac2524cf6a6342578822c0911.json)；request.messages/response.choices[0].message.content；SHA256 `f9af7253ba70da8b87778956b7b9955aa37dc86b1615c03bff0b2dad8821e1c9`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/0dbd148234044132ae872bf5b3484d93.json](../runtime_eval/provider-captures/V1-001/0dbd148234044132ae872bf5b3484d93.json)；request.messages/response.choices[0].message.content；SHA256 `3031ae8234629b1feaa41b0cd72847d3479c4484a11de11efcec20128250d90a`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-26/turns/004/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-26/turns/004/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `ef0763a7cd717a8da70a011836dbf2f3d6a847468911033c0478a66a4269f5b3`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/b30f0918768045028e729967ef2b21cf.json](../runtime_eval/provider-captures/V1-001/b30f0918768045028e729967ef2b21cf.json)；request.messages/response.choices[0].message.content；SHA256 `5285f77b3b53289e10da8cf4de525253ac5f9788af85e5012f000dd4c80e0270`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/f92190817ff241ecb358908210e19232.json](../runtime_eval/provider-captures/V1-001/f92190817ff241ecb358908210e19232.json)；request.messages/response.choices[0].message.content；SHA256 `4108525e07affb5204e2ad724366218cf60c889a3c9ef674a1f932c2e042a7dd`。

需人工确认：代码路由不能由patch prompt补偿；保留前面实际正确子轮与最终真实失败，不混成全程通过。 状态 `pending_human_review`。

## sp03-27

原题：2023年销售额占比是多少？

**参考：AI建议通过。** 2023比例缺分子/分母，补客户所在地Brazil分子和全库同年分母后的CASE gold正确；后续修改应分别保持局部范围。

**系统实际：AI发现错误。** V1真实P3只set numerator，未提升全局filter/region；补2023全库分母后真实CASE Brazil / SUM(all total) fraction0.0421653392执行正确，局部职责改善有证据。但后续“分子换成德国…”fresh路由、原2023和已确认全库分母丢失，再问分母；后续2024未执行，不能称整题完成或V1整体提分。

真实请求 4 轮；已执行SQL轮号 [2]；生成未执行SQL轮号 无；计划后续未执行 1 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-27/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-27/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `d476b1352e59567b2fd051f919dc0e48a4f69af387ceb38a41dd087edb611e6a`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-27/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-27/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `10dfef3d4ddd2404b1eff3cd9690aac3f72cdf493059edcfc2eed4e07e8adb44`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/34d7c7ac629f48998a3d12ac010be440.json](../runtime_eval/provider-captures/V1-001/34d7c7ac629f48998a3d12ac010be440.json)；request.messages/response.choices[0].message.content；SHA256 `eeeb88f10142677e8210f56aadca055e3549839e4b8cdb02f3dea6ffaf7f5eff`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-27/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-27/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `2228c7f41bcb1321975f774b76e13da69c37163bfff5b9e8865669c6c2cc0470`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/101c6d82f1424605956744ffdd5f05dc.json](../runtime_eval/provider-captures/V1-001/101c6d82f1424605956744ffdd5f05dc.json)；request.messages/response.choices[0].message.content；SHA256 `9b709c380a62259fd16462ef2e8b57f0f3be063de8b1553d1a20103daa7ea317`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-27/turns/002/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-27/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `c9e3daca4cd5785586300e29f75bc6db17cad06170768d7e937168c5340db2ae`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/73b64e723c274382b49c0762466c82de.json](../runtime_eval/provider-captures/V1-001/73b64e723c274382b49c0762466c82de.json)；request.messages/response.choices[0].message.content；SHA256 `ff96c89f81c346aebbfedc6bb8c836c235af442ea6a1d66a855a7dae21ee9799`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/4b746fb15f9c4150baa10f5aef9b5363.json](../runtime_eval/provider-captures/V1-001/4b746fb15f9c4150baa10f5aef9b5363.json)；request.messages/response.choices[0].message.content；SHA256 `427d3a1e5f4612ef1fcf54bedeecd0ab1c1151a45d61d6ed16613d2ef6dd5a55`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/490fb0aa9d3a477c85cee8b163100665.json](../runtime_eval/provider-captures/V1-001/490fb0aa9d3a477c85cee8b163100665.json)；request.messages/response.choices[0].message.content；SHA256 `4ee6caf7cc9ffd6408665abaa520a15f3906c58f54efba22627d56dce8a87d4c`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-27/turns/003/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-27/turns/003/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `2a57040d986888f6d320bedf68752f0a90117c253341a88a45dc338e22154e10`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/bf4a8f428f504e7cb6f88ff8230e1ff8.json](../runtime_eval/provider-captures/V1-001/bf4a8f428f504e7cb6f88ff8230e1ff8.json)；request.messages/response.choices[0].message.content；SHA256 `49ae05336d8bcd2341dd09c6ad602939558f000bfe2224504efc5310915674eb`。

需人工确认：建议仅patch prompt界定局部分子/分母string及global条件边界；正确patch之后能否生成合规比例SQL仍需真实验证。 状态 `pending_human_review`。

## sp03-28

原题：2022年金属乐队的销售额是多少？

**参考：AI建议有条件通过。** 初始‘金属乐队’Metallica候选需用户确认，gold明细2022正确；business_basis含‘Metal与Metallic在artist与genre均有候选’不符合当前别名表，需更正依据。L2实际应为候选确认，不必凭band字眼强造genre初始歧义。

**系统实际：AI发现错误。** 真实单候选Metallica确认后2022明细额22.77正确；“改成流派Metal”P3本轮set filters只保Metal，原防丢条件守卫要求明确remove而拒绝。旧artist撤销没有完成，后一2023/Germany未执行；与V0 remove词限制不同的实际补丁形状已分开记录。

真实请求 3 轮；已执行SQL轮号 [1]；生成未执行SQL轮号 无；计划后续未执行 1 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-28/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-28/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `a34a1655df0e3e49cbc2c59b8ae9661ad036103e7290e7096e6d0ad59043d2f0`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-28/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-28/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `9a7468084fbb5a91e66f02252cdf2d51023110f807ea2fe594a12f180f197820`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-28/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-28/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `1090ab434cb146a0fbc437ace9cf079c4f929076db8c37c2834c4d42795d5091`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/4cb93a81406b4b858213ea4630542844.json](../runtime_eval/provider-captures/V1-001/4cb93a81406b4b858213ea4630542844.json)；request.messages/response.choices[0].message.content；SHA256 `b76ddc83a9d9d0015f5c8f642117d47ea60c32215c0a8d7688b47f9f23662339`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-28/turns/002/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-28/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `9845ca150f64bc17bf5725e21f18cd092a8a8e70483af9ff48e477cc44793c5c`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/830be9c887904b6c86c9bfc9fc930d52.json](../runtime_eval/provider-captures/V1-001/830be9c887904b6c86c9bfc9fc930d52.json)；request.messages/response.choices[0].message.content；SHA256 `fae4fbdcf4b231cdbd59520d170224f1892cd47ff5c3dd7bf03a812d7172f92d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/02bd7e32348849deb8b25e3cb0d23c6f.json](../runtime_eval/provider-captures/V1-001/02bd7e32348849deb8b25e3cb0d23c6f.json)；request.messages/response.choices[0].message.content；SHA256 `d91f15015a63f7bc971dde8799e1a85351781623c32690c954e5c74f5b3f42c9`。

需人工确认：确认替换对象是否应撤销原对象过滤，程序应做可证明且只删目标的迁移；本轮prompt-only不放宽guard。 状态 `pending_human_review`。

## sp03-29

原题：最受欢迎的10首曲目是哪些？

**参考：AI建议通过。** 热门10首缺期间先L2，数量登记默认；补2023、改2024、改明细销售额，三段gold语义正确。

**系统实际：AI建议通过。** 实际年份按钮2023→自由改2024→自由换明细销售额三段SQL均保track/Top10/期间/稳定排序，核心ID及金额数量符合gold；显式换metric后旧数量默认清除。附track_name导致原列数fail属于评分契约；未点击L1口径按钮。

真实请求 4 轮；已执行SQL轮号 [1, 2, 3]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-29/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-29/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `bb755afaf97424f047d070535b389cb5ced1a8fd79ff5988d4d9497b54397a72`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-29/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-29/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `877f5e1386162b02f31f7c00256019623c6def02d7093601c4977e8ad5468141`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/43ee7af795b540b3aa749eb7f6cbd5da.json](../runtime_eval/provider-captures/V1-001/43ee7af795b540b3aa749eb7f6cbd5da.json)；request.messages/response.choices[0].message.content；SHA256 `417afbbf400a4d88f057061880d6f39914c3a9277153a474fab057b5e7dcdff7`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-29/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-29/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `3e0d2deee90e2ab53f040ea3b72fe2a8c228612df2caa818eba6de61da4cd119`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/5e81b4be3e1e4228a3fb59c9ec338c38.json](../runtime_eval/provider-captures/V1-001/5e81b4be3e1e4228a3fb59c9ec338c38.json)；request.messages/response.choices[0].message.content；SHA256 `ed887740da6441c38e29a3a513faf05b39f1970cc5f9680c019ce10c30f2ebf7`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-29/turns/002/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-29/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `ee289d95beb15cba3f72539086e531e15bf1561c41be0fcc9ded37ddf1aac199`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/f31b1e808fd643cbb53fb6096fda7cb3.json](../runtime_eval/provider-captures/V1-001/f31b1e808fd643cbb53fb6096fda7cb3.json)；request.messages/response.choices[0].message.content；SHA256 `006fa531c043ef60b08bd7f3d15e752a84002b43eac823ca2b196d3a538c9bd6`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/9ef6510eea18473da343388599ab4828.json](../runtime_eval/provider-captures/V1-001/9ef6510eea18473da343388599ab4828.json)；request.messages/response.choices[0].message.content；SHA256 `8ef123b3d606528ead3b639ae3019245be540d2bcc5c2288ec005bb90f68c79b`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-29/turns/003/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-29/turns/003/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `e07228e8738a01e604687c917ccedf653a0fc39c3eb60aade78e6d6f91d721b2`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/84c58e9ad5b84e97bc8ca3751d50d4d0.json](../runtime_eval/provider-captures/V1-001/84c58e9ad5b84e97bc8ca3751d50d4d0.json)；request.messages/response.choices[0].message.content；SHA256 `14e411f21693137747103f9b1af538535b6d16f1a1427d2809339506cfe1bd2d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/58ccef649080428381f33de37a035b7a.json](../runtime_eval/provider-captures/V1-001/58ccef649080428381f33de37a035b7a.json)；request.messages/response.choices[0].message.content；SHA256 `ca2be88cc171325c8df8baeb12e65d149bcfb570c2a811849fa040cc2ff2b425`。

需人工确认：确认评分输出契约是否允许解释性附加列；不要因此修改参考业务答案。 状态 `pending_human_review`。

## sp03-30

原题：谁买得最多？

**参考：AI建议有条件通过。** 对象/时期澄清后2023客户发票金额SQL正确；ranking.required仅metric/object，但现有rules对canonical customer+invoice_revenue另要求期间。原hidden goal Top1并未出现在用户补充，登记缺TopN默认10与“谁最多”的条数语义需确认。不能把隐藏2023当已向系统发送；参考Top1边界保持有条件，不改原标签。

**系统实际：AI发现错误。** 真实只补metric和客户后P3把rank_object保存为中文“客户”，未规范成customer，绕过rules中customer+invoice_revenue缺期间必问规则，尚未收到2023即执行全库Top10。随后改2024、换track数量确实保持已改条件；最初漏问期间是真实对象规范问题。Top1/Top10默认边界另需人工，不以隐藏2023强补输入。

真实请求 5 轮；已执行SQL轮号 [2, 3, 4]；生成未执行SQL轮号 无；计划后续未执行 0 轮。

证据：
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-30/checkpoint.json](../runtime_eval/runs/V1-001/cases/sp03-30/checkpoint.json)；checkpoint.turns/controller_events；SHA256 `a4e28b265c7767a9952c5dc173ea4bc32690ce6fcab913c99d9d360fb31b8323`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-30/turns/000/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-30/turns/000/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `4943a220ee95e3a913ffe5167b1e2babdb679075146adcb93c78a82aba6f1f71`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/094e84e5beb841038ad714277a5a6d69.json](../runtime_eval/provider-captures/V1-001/094e84e5beb841038ad714277a5a6d69.json)；request.messages/response.choices[0].message.content；SHA256 `7bffeb1428438dd733dec4a275884d9b0327802397288b4775f02d8e5b62b6fd`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-30/turns/001/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-30/turns/001/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `72b76ca635f25948e4d5f00d8b1a6d6d0c34c6cdce59c58dbdeef4694088e86f`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/59fd8d7e64574cf5b59c10a70746398e.json](../runtime_eval/provider-captures/V1-001/59fd8d7e64574cf5b59c10a70746398e.json)；request.messages/response.choices[0].message.content；SHA256 `451f6faecfeb10bb511f8bef40855d2bb0b3e5a3b99c524c1adb3ba63ee37bd1`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-30/turns/002/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-30/turns/002/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `73a704d8d966e3a26a8b8616682077bb370ed55fdf0539b979613e1a6e60ad4d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/38e2b2a4f6504aaeaaf4c151fa121811.json](../runtime_eval/provider-captures/V1-001/38e2b2a4f6504aaeaaf4c151fa121811.json)；request.messages/response.choices[0].message.content；SHA256 `0c6e5f6af7ca7e86a6ec870e7476e8e5d876777f907e91b09dfab1c9124ea1cc`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/fe120f3610e146a599db83e8df1de67d.json](../runtime_eval/provider-captures/V1-001/fe120f3610e146a599db83e8df1de67d.json)；request.messages/response.choices[0].message.content；SHA256 `97d5a89a1916405e9838ff6b746378b01430a78a62094c4e5a676ff774d411ad`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-30/turns/003/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-30/turns/003/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `86f50005322d0503abade2b3b4eb4a8a60fa0f1974ac78555a4d51f8ac24834e`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/69c427d5be0e4ac782a2379f055f469c.json](../runtime_eval/provider-captures/V1-001/69c427d5be0e4ac782a2379f055f469c.json)；request.messages/response.choices[0].message.content；SHA256 `c903f460e741f9a4ba9a6697b43def1af509ba971a2664621469b18b93f6d74d`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/d92d5f76ece345909f0752988f749034.json](../runtime_eval/provider-captures/V1-001/d92d5f76ece345909f0752988f749034.json)；request.messages/response.choices[0].message.content；SHA256 `a60cd4be98a174636c22401a2e4eb8d533b0870ab707a0190ddb99d630c5a54f`。
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp03-30/turns/004/response.raw.json](../runtime_eval/runs/V1-001/cases/sp03-30/turns/004/response.raw.json)；body JSON status/sql/table/intent/clarification/metadata/steps；SHA256 `ba5a20730a2de9c772301f08b7aa5212cbe6d6d9b222051c7d5d3fc1b562d2be`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/c559f8652d684079940c792584535a76.json](../runtime_eval/provider-captures/V1-001/c559f8652d684079940c792584535a76.json)；request.messages/response.choices[0].message.content；SHA256 `6d32c63e5db962618d1225b6dc14ee397edb71a6cf2aedfd125d20d7403e2a7e`。
- [eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V1-001/a1b4180cef6043db90af9014245bcf76.json](../runtime_eval/provider-captures/V1-001/a1b4180cef6043db90af9014245bcf76.json)；request.messages/response.choices[0].message.content；SHA256 `3832c13b91edff7ee20a81a9f004589eb557d66710a8c1764b33059ee5b73aef`。

需人工确认：优先确定最高一位与Top10默认的适用范围；本轮不强制Top1，不改49分母。 核对实体对象ID规范及由此漏问期间；不补写隐藏2023。 状态 `pending_human_review`。

## 材料与限制

- [data/catalog/chinook.yaml](../../../../data/catalog/chinook.yaml)；SHA256 `4d97a3f7fdfd0c684b544f162e20d2253c4f9c0cd572ba1fcaf40fe439a391b8`。
- [data/aliases/aliases-d2-reviewed.csv](../../../../data/aliases/aliases-d2-reviewed.csv)；SHA256 `aa699e8ef59f5185a0626ed2a9aefb36a1e292bfa2e3c0efd4b0ba5b1ddaef04`。
- [data/rules/metric_definitions.json](../../../../data/rules/metric_definitions.json)；SHA256 `2a0df8d29a4fb5401fd0a5b33a0f44932e00ab005bc674eaaa8b8a33f1df5efc`。
- [qa_agent/clarify/clarify_rules.yaml](../../../../qa_agent/clarify/clarify_rules.yaml)；SHA256 `345b5abeaf858cd3628fcc08c6280a7d6c08517bd9dae0e0677cf0b256e8e7c8`。
- [eval/experiments/after_d2_01_03/materials/generation_materials.json](../materials/generation_materials.json)；SHA256 `8bb7b1b403972e6b2ae910823842ac3480079e291e5d1b35b24e3dc7de856cf0`。
- [eval/experiments/after_d2_01_03/materials/readonly_live_facts.json](../materials/readonly_live_facts.json)；SHA256 `391487ffea9c12f21f5444369dd2b87b48897ac363a032a6ea107e5507df7b8f`。
- [eval/experiments/after_d2_01_03/runtime_eval/V1-freeze.json](../runtime_eval/V1-freeze.json)；SHA256 `7e71ee5cb430bd4d15cafad4ce3fccb1b3ef74f07c1c073cf7a365ff6d3a21f4`。
- [eval/experiments/after_d2_01_03/runtime_eval/V1-code-snapshot.json](../runtime_eval/V1-code-snapshot.json)；SHA256 `13c8063f2c04e8762128aba22480088f2d4e96676e075f1a81ab89a1a8a9a7e8`。
- [eval/experiments/after_d2_01_03/reports/scoring-protocol-draft.md](scoring-protocol-draft.md)；SHA256 `b8f6b7d1d1d531d810a2244f6662db767d9654bc14e1bafa7a10637f918b480e`。

- gold标准SQL和此前只读结果存档完整读取，本次0数据库查询，未宣称重新实跑标签。
- 原可评分23/排除7，全部固定49/60分母与原评分保留；AI分对象判断不能转换成新EX。
- source当前已回退V1时，V2使用修改后字节档案和版本snapshot证据；不拿当前源码冒充旧运行。
- L1 switch元数据仅为可用性证据；没有实际choice请求时不写完成口径按钮切换。
- FAILED仍可能包含生成SQL字符串；只有实际SUCCEEDED/EMPTY_RESULT且有结果表才列入已执行SQL，误拒的SQL为未执行。
- 本审计者曾负责D3澄清代码及V2守卫，不能宣称角色盲审；父任务独立二遍与真实版本运行另外保存。
- 未填写A/B签字或人工确认日期，pending_human_review保持。

原标签及该版本score SHA前后相同，证明记录见JSON。没有A/B签字或人工确认日期。
