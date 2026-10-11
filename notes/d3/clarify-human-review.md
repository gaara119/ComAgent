# D3 B 待人工统一审核输入

这里只包含21道开发题和4项公共待核事项；9道隔离保留题不展开、预测为0。以下AI结论不是人工签字。逐题先核对参考判定，再打开真实raw核对系统业务输出；初始分级通过不能自动推出完整SQL和答案正确。

| 编号 | 题目 | 参考级别 | 二遍AI参考建议 | 系统实际级别/状态 | 具体材料 |
|---|---|---|---|---|---|
| clarify-01 | 巴西有多少客户？ | L0 | AI建议通过 | L0 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-01.json` |
| clarify-02 | genre.name 明确为 Rock 的曲目有多少首？ | L0 | AI建议通过 | L0 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-02.json` |
| clarify-04 | 2024年全部发票的平均每张发票金额是多少？ | L0 | AI建议通过 | L0 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-04.json` |
| clarify-05 | 数据库一共有多少个音乐流派？ | L0 | AI建议通过 | L0 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-05.json` |
| clarify-07 | 2024年账单国家为Brazil的发票金额占同年所有发票金额的比例是多少？ | L0 | AI建议通过 | L0 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-07.json` |
| clarify-08 | 2024年账单国家为USA的发票销售额同比增长率是多少？ | L0 | AI建议通过 | L0 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-08.json` |
| clarify-10 | 2024年全部发票按总额从高到低列出前5张，相同金额按invoice_id升序。 | L0 | AI建议通过 | L0 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-10.json` |
| clarify-11 | 2024年最受欢迎的5首曲目是哪些？ | L1 | AI建议通过 | L1 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-11.json` |
| clarify-13 | 2022年卖得最好的2首歌有哪些？ | L1 | AI建议通过 | L1 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-13.json` |
| clarify-14 | 2024年客户中谁买得最多？请列前3名。 | L1 | AI建议通过 | L1 / SUCCEEDED | `eval/artifacts/d3/b/clarify-dev-v4/clarify-14.json` |
| clarify-16 | 账单国家为USA的发票销售额同比增长多少？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-16.json` |
| clarify-17 | 2024年同比增长多少？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-17.json` |
| clarify-19 | 2024年Brazil账单发票销售额占比是多少？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-19.json` |
| clarify-20 | 2024年哪些记录的金额占全部发票金额的比例？我还没确定分子范围。 | L2 | AI建议有条件通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-20.json` |
| clarify-22 | 2024年谁买得最多？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-22.json` |
| clarify-23 | 摇滚歌曲有多少首？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-23.json` |
| clarify-25 | 这批曲目的平均时长是多少？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-25.json` |
| clarify-26 | 有多少复购客户？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-26.json` |
| clarify-27 | 2024年全部发票销售额环比增长率是多少？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-27.json` |
| clarify-28 | 统计2024年的发票销售额，但日期必须从2023年1月1日到2023年12月31日。 | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-28.json` |
| clarify-30 | 摇滚乐曲目的平均时长是多少？ | L2 | AI建议通过 | L2 / NEEDS_CLARIFICATION | `eval/artifacts/d3/b/clarify-dev-v4/clarify-30.json` |

clarify-20的分母2024年范围表达为二遍AI有条件通过，请优先检查该题句意。完整reference_semantics、理由、真实材料具体位置在同名JSON逐项保存，人工状态均保持pending_human_review。

## 公共待核事项

### d3-b-protocol：公共接口与会话

新增可选 ChatRequest.clarification_id/intent_version/choice_id 和 AnswerEnvelope.intent；IntentContract 延续 extra=forbid，卡片恢复需ID与版本同时匹配，PDF物理页从1开始的既有约定不改。

AI建议通过：新增字段兼容旧首次请求；原协议与新协议的具体源码版本需双方最后核对。真实陈旧卡在模型/SQL前拒绝，年份选择不会清掉独立缺指标问题。

证据：`qa_agent/schemas.py`；`qa_agent/clarify/state.py`；`eval/artifacts/d3/b/shared-regression-v13/command.json`；`eval/artifacts/d3/b/clarify-flow-v6/stale-card-rejected.json`；`eval/artifacts/d3/b/button-api-v1/missing-metric-after.json`。

### d3-b-defaults：声明的对象限定假设

热门曲目缺指标采用已共同确认的购买数量口径；客户谁买得最多缺指标采用已共同确认金额；缺Top-N数量按方案默认10并声明；缺关键期间/对象不得猜。

AI建议有条件通过：已确认四项指标不改。缺数量的10条假设和仅明确最近有记录年份的解释，需核对适用对象及声明；“数据中最近一年”不自动装成最大年份。数量→金额→数量真实切换均通过。

证据：`qa_agent/clarify/clarify_rules.yaml`；`qa_agent/clarify/rules.py`；`data/rules/metric_definitions.json`；`eval/artifacts/d3/b/ui-live-v4/popular-default-raw.json`；`eval/artifacts/d3/b/ui-live-v4/switch-revenue-raw.json`；`eval/artifacts/d3/b/ui-live-v4/switch-back-quantity-raw.json`。

### d3-b-growth-display：增长率显示单位

人工决定增长率结果表及文字采用fraction还是percent，以及统一舍入/单位说明方式；在决定前不修改原始输出。

AI建议有条件通过：真实 valid-year-after 返回 ROUND(*100,2) 的24.24，free-year-resumed/UI返回0.24240365…；数学增长可一致，但同一列名不足以证明同一显示单位。技术恢复成功不替代该显示规范审核。

证据：`eval/artifacts/d3/b/button-api-v1/valid-year-after.json`；`eval/artifacts/d3/b/clarify-flow-v6/free-year-resumed.json`；`eval/artifacts/d3/b/ui-live-v4/clarification-after-raw.json`；`eval/artifacts/d3/b/ui-live-v4/free-input-after-raw.json`。

### d3-b-measurement-scope：测试结论范围

21/21仅初始分级与执行门；7请求20/20为具体状态链；7UI请求10/10为控件连线。全部21题的澄清交互最终答案正确率尚未实测。

AI建议通过：保留9题预测0；D4的5段每段6轮、完整自动路由/混合跨源和复杂SQL数据流不提前声明完成。人工审核应分别检查参考判定与系统真实业务回答。

证据：`eval/reports/d3/b/handoff-summary.json`；`eval/datasets/d3/clarify/manifest.json`；`eval/artifacts/d3/b/clarify-dev-v4/report.json`；`eval/artifacts/d3/b/clarify-flow-v6/report.json`；`eval/artifacts/d3/b/ui-live-v4/report.json`。

AW目录条件与证据不足具体条目另见 `eval/reports/d3-ai-review/catalog-pass2.json`，本输入不复制改写该独立二遍记录。A负责合并AW21开发题、B21开发题、目录具体条件、协议与显示待核为最终统一表。

未填写A/B签字、人工确认日期，未修改题库、启用别名、业务口径、原始数据或既有人工记录。
