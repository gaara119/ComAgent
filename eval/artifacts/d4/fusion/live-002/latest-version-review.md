# 最新 API007 的六题跨源回归核对

2026-10-13（America/Chicago）执行，原始UTC时间见 `report.json`。这是共享SQL生成prompt及当前合同守卫更新后的必要开发正确性回归；没有改动融合planner、源文、gold或原 `live-001` 结果，没有读取保留题，没有重拍页面。

实际命令为 `.venv/Scripts/python.exe -B scripts/run_d4_fusion.py --output eval/artifacts/d4/fusion/live-002`，退出码0；六题、七次现有API调用，6/6预期检查通过。自动标签比较与完整答案／引用的AI核对分别记录，六道新题仍为 `pending_human_review`。

| 编号 | 新真实行为 | 完整答案AI判断 | 引用语义AI判断 | 原始证据 |
|---|---|---|---|---|
| cross-01 | 实际FK明细销售额排名为ID90、Iron Maiden、138.60；再传ID/名检索。新回答的重金属、Steve Harris、1975年Leyton、重金属新浪潮、歌词题材、1980/1982作品均由原HTML三段支持。 | AI建议通过 | AI建议通过；正确文档E1公开背景支持每句，销售额由本次SQL支持。 | `cross-01.json` 的 `turns[0].response` |
| cross-02 | 发票日期2024左闭右开区间，实际Iron Maiden33.66；背景仍检索ID90对应文档，未将一般背景冒充2024变化。 | AI建议通过 | AI建议通过；E1与已读原文一致，年份销售额由SQL支持。 | `cross-02.json` 的SQL、结果、E1与metadata |
| cross-03 | 只允许U2文档时第一名仍为Iron Maiden138.60；返回EMPTY_RESULT、保留排名及SQL、没有错误介绍或引用，完成阶段数为1。 | AI建议通过；正确的文档不足分支，不能计成音乐介绍回答完成。 | AI建议通过；没有应当被支持却缺引用的背景陈述，音乐介绍引用应为空。 | `cross-03.json` 的scope／answer／evidences／fusion |
| cross-04 | 真实手册定义AVG(invoice.total)进入生成，按customer.country=USA及2024区间得到6.0942857142857143；未用账单国家或客户粒度。 | AI建议通过 | AI建议通过；E1支持发票等权定义，数值由SQL支持。 | `cross-04.json` 及下列真实provider文件 |
| cross-05 | 同一定义按2023年Canada客户所在地重算，实际5.0400000000000000，未偷用文档2024示例或USA。 | AI建议通过 | AI建议通过；定义引文与源DOCX一致，5.04由SQL支持。 | `cross-05.json` 及下列真实provider文件 |
| cross-06 | 首轮真实NEEDS_CLARIFICATION、无SQL；同session及卡片/version补2024年后版本1→2、USA保留、AVG发票定义保留、结果6.0942857142857143；续问走fusion_resume，没有重复检索。 | AI建议通过 | AI建议通过；复用先前真实E1及哈希，期间由用户补充。 | `cross-06.json` 的两轮request/response |

直接读取的新模型生成请求确实包含 `verified_fusion_context`，不是仅依赖metadata声明：cross-04为 `eval/artifacts/d4/provider-api-007/d4715c4c1e9b42b1b026a96a33e3739c.json`；cross-05为 `eval/artifacts/d4/provider-api-007/3787a00d2ba5402ca8564adee1c3b416.json`；cross-06续问为 `eval/artifacts/d4/provider-api-007/d3c361511741424db5b057fcb00b54e1.json`。三者实际发送逐字定义、AVG、invoice粒度及源哈希，各自真实响应生成相应期间和customer国家的AVG查询；随后出现 `sql_current_contract_validate`、原SQL/期间/绑定校验、`fusion_plan_validate`及 `sql_exec`。source docx的定义与原人工已确认四项口径一致。

本轮再次计算源哈希：Iron Maiden HTML为 `4f071c465c5417f5867e8571fb4ea37098dd8829d86b9b253ac26184a145b270`；手册DOCX为 `b50f5683e735baa3ca6fe08bde3b437377d810732357e2a4898d6820b0456a9a`；六题DEV源为 `9d8c5af4dccf3ee9306968a83bc678bf2906d7c968f0e4a033b98a16378464f4`，都与先前直接读取的版本相同。

API007健康记录位于 `eval/artifacts/d4/runtime-007/health.json`。当前生成prompt文件SHA是 `1b27c6a7e75d1443f998227e8cc0e3d9345ca380598708aa40d31d9804feed60`；cross-04供应商记录的实际system文本以这个文件文本完整开头，后附统一LLM客户端的419字符JSON Schema约束。完整发送文本SHA因此是 `832aaa2734ebadafbc32445d31b32c537347ebf07877a63ddb86f261c4af4a38`，不应误判为文件版本不一致。融合planner SHA仍为 `0a37dc73d12c489194a479d84bc1f1864ebfa25663dd62eac4e269daae29f16d`；pipeline现文件SHA为 `e36e7fe9e5e8a8ffb24439733f76e02ce46ffbb780add9ebfd84c94bd8089cad`。

这里只证明本次真实请求中的新生成输入和已观察到的执行步骤，不声称远程加载模块的完整证明。该批与多轮开发正确性回归并行，不作为速度实验；不据这六题扩大为任意跨源问题的可靠性结论。AI判断不填A/B签名，不改人工审核状态。
