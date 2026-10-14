# D4 跨源六题 AI 复核（第二遍材料核对）

2026-10-13。范围仅为6道新增开发题；本轮重新读取实际原文、索引片段、实体清单和只读结果，不重新审核已提交735项。**参考语义与流程分别核对；6题系统实际回答均未运行。没有人工签名、确认日期或 approved 状态。**

依据：[六题原清单](../../eval/datasets/d4/cross_source_dev.jsonl)、[实际检索原件](../../eval/artifacts/d4/fusion/source-retrieval-001/source-retrieval.json)、[只读参考结果](../../eval/artifacts/d4/fusion/reference-only-001/report.json)、[第二遍语义探针与SHA](../../eval/artifacts/d4/fusion/second-review-001/material-checks.json)、[47项模块回归](../../eval/artifacts/d4/fusion/commands/20261013T164250991023Z-fusion-frozen-module-v8.txt)。模块含模拟模型，不能替代真实跨源联调。

| 原编号／题义 | 参考与原文判断 | 应发生的步骤及本轮发现 | 系统实际回答 |
|---|---|---|---|
| **cross-01** 全库销售冠军及音乐风格 | **AI建议通过。** 艺术家销售额按明细单价×数量汇总，不重复加发票总额。参考第一名 Iron Maiden，ID90，138.60；第二名U2为105.93，当前快照冠军唯一。 | 原SQL生成→校验→只读执行→将真实ID/名称传值→精确匹配 `artist-iron-maiden`→检索与引用回答。实际简介“公开背景”支持英国重金属、英国重金属新浪潮及歌词题材，不支持巡演收入。冠军和风格须分别追溯SQL和原文。[参考](../../eval/artifacts/d4/fusion/reference-only-001/cross-01-reference.json) | **未运行。** 不能把参考查询或名称匹配fixture当作模型已完成。 |
| **cross-02** 2024年冠军及风格，自动路由 | **AI建议通过。** 以 `invoice.invoice_date` 的 `[2024-01-01,2025-01-01)` 筛选对应明细。第一名Iron Maiden 33.66；第二名U2 27.72。 | auto→SQL→文档，仍由查询结果决定文档。与01同冠军是当前数据事实，不能单靠这两个相同名字证明程序没有写死；生产guard另检查真实字段、Top1、明细聚合及禁止固定艺术家过滤。[参考](../../eval/artifacts/d4/fusion/reference-only-001/cross-02-reference.json) | **未运行。** 待核对实际SQL期间、路由、传值与引用。 |
| **cross-03** 同一排名，只允许U2文档 | **AI建议通过。** 仍应查询全库冠军Iron Maiden；`doc_ids`仅限制文档阶段，不能把SQL先改成U2排名。清单中U2关联ID150，与冠军ID90不符。 | SQL执行→实体匹配→明确文档不足；保存排名与SQL，不能引用U2补风格。`EMPTY_RESULT`此处表示文档不足，界面应说明数据库已完成。[参考](../../eval/artifacts/d4/fusion/reference-only-001/cross-03-reference.json) | **未运行。** 缺失文档fixture通过，尚不等于这道真实请求通过。 |
| **cross-04** 手册定义，2024年USA客户客单价 | **AI建议通过。** 原文明确逐发票等权 `AVG(invoice.total)`；客户所在地为 `customer.country`。21张发票总额127.98，均额 **6.0942857142857143**；13名购买客户的均额9.8446…是另一指标。 | 检索→逐字定义/字段提取→参与原生成prompt→执行前校验→只读执行→返回数值与定义引用。不是从手册抄SQL直接执行，也不能只附引用。[参考](../../eval/artifacts/d4/fusion/reference-only-001/cross-04-reference.json) | **未运行。** 本地SUM÷COUNT复核与guard通过，模型是否实际遵循尚待实跑。 |
| **cross-05** 手册定义，2023年Canada客户客单价，自动路由 | **AI建议通过。** 11张发票总额55.44，逐发票均额 **5.0400000000000000**；6名购买客户口径为9.24，不能混用。 | auto→文档定义→SQL，用户2023年优先于手册示例2024年。须核对实际SQL而非只看意图；现有模块不能单独证明模型不会套示例年份。[参考](../../eval/artifacts/d4/fusion/reference-only-001/cross-05-reference.json) | **未运行。** 真实期间、字段和答案待验证。 |
| **cross-06** USA“某年”，再补充2024年 | **AI建议通过（参考语义）；流程待实测。** 首轮不能代填年；第二轮保留USA及每张发票均额，2024年参考与04相同。 | 首轮检索定义→③询问期间；续问同session/scope、只set期间、版本递增→重新校验/执行→定义引用。**静态代码中“某年”的 `time_ambiguous` 仍依赖语义提取输出；已通过的resume fixture预置了卡片，不能证明首轮实际触发。** 不据此先改题或代码。[参考](../../eval/artifacts/d4/fusion/reference-only-001/cross-06-reference.json) | **未运行。** 必须同时记录首轮NEEDS_CLARIFICATION和补充后的完整请求，不能只计第二轮。 |

原文定位：手册 `ca07b3c089c99383c97a3600`／“四项指标的定义与限制→平均每张发票金额”有逐字定义；`2474f826ae5902ce07131fca`／“范围与通用约定”规定期间、两种地区字段、无发票AVG为NULL及不推断币种。艺术家风格定位在 Iron Maiden 的 `1954ca3e92aa9467282b5de6`／“公开背景”。这些是DOCX/HTML章节，不虚构PDF页码。

实体与源SHA已复核：[manifest](../../data/docs/manifest.csv) 中 Iron Maiden=`chinook:artist:90:Iron Maiden`（`4f071c…5b270`）、U2=`chinook:artist:150:U2`（`b2390c…3757e`）、手册=`chinook:business-metrics`（`b50f56…56a9a`）；完整SHA及四条额外只读语义探针在第二遍原始记录。**6题参考计划guard通过；4条探针核验唯一冠军及逐发票均值；0模型、0HTTP问答、0保留预测。**

仍需人工确认：6道新增题的题义/预期步骤/参考语义；实际模型回答出来后分别核对完整回答和引用支持。本页不填A/B签字，不修改原题、gold、别名或已提交审核记录。真正6题API及两类问答截图仍待具体外发授权；入口截图和fixture不能算完成这一验收。
