# D1B 修复后开发集独立 AI 复核

本报告复核根任务在新索引上已生成的 14 条真实开发集响应。复核过程没有新增模型请求，没有提交保留题，也没有填写人工审核人或接受 gold。原 `b-review.md/json` 完整保留。

## 当前结论

- AI 语义复核：{'correct': 14, 'incomplete': 0}。
- 对实际陈述事实的引用支持复核：{'complete': 14, 'incomplete': 0}。
- 两项同时通过：**14/14**。该数字是 AI 复核观察值，正式成绩仍等待人工确认。
- 实测平均请求耗时：3.184 秒，原始耗时逐题保留。
- 索引版本 2，1527 个真实片段，检索方式 `bm25+bge-m3_dense_rrf`。
- 20 道 gold 的来源复核沿用原报告，当前 gold 文件哈希未改变，人工签字仍全部待完成。

## 逐题实际回答验收

| 题号 | 实际引用页 | AI 语义结论 | 断言引用支持 | 复核依据 |
|---|---|---|---|---|
| rag-02 | E1→p1 | correct | complete | E1 本次包含完整 45 天期限、含所需合并后经营期间的首个财政季度及其结束时间；回答与完整原句一致，没有将起点改为合并日。 |
| rag-03 | E1→p2 | correct | complete | E1 本次完整保留三年、合并生效日起算、Section 13 和 1934 法名范围，支持整句回答。 |
| rag-05 | E2→p1 | correct | complete | 所问两条河流 Tame/Etherow 完整列出；附加西侧汇入 Mersey、Etherow 盆地突出约七英里的事实均来自 E2，latter 指向 Etherow 正确。 |
| rag-06 | E1→p8 | correct | complete | E1 直接包含 Coal Measures、wheat/oats/potatoes，回答本次保留 perhaps，避免把原文谨慎评价强化为确定事实。 |
| rag-07 | E1→p14 | correct | complete | E1 同时包含 southern part of the Sheet、450 to 550 和 feet，地点范围、数值及单位均未改变。 |
| rag-08 | E1→p8 | correct | complete | 四组名称与 E1 的 viz. 列表一一对应，回答指明 grits/sandstones 四色分组，没有误把同段的页岩统一着色混入。 |
| rag-10 | E1→p65, E2→p66 | correct | complete | E1 明确 Class B digital device 与 FCC Part 15，足以支持主回答；E2 加拿大 Class B 规定属于冗余引用，不能单独证明 FCC，但本题主断言有完整 E1 支持。 |
| rag-11 | E1→p3 | correct | complete | E1 包含 iMovie 标题及对应 Create/share movies in minutes 文字；已结合原页左上版面确认归属，未把 iPhoto 栏说明混入。 |
| rag-12 | E1→p67, E2→p67 | correct | complete | 推广 energy-efficient products 是所问首要目标，E1/E2 均含完整目标句及制造商合作关系，回答没有以附加节省成本结果替代目标。 |
| rag-13 | E1→p52, E2→p52 | correct | complete | 首句 AirPort Base Station 共享单个 IP 由 E2 直接支持；第二句只在单 IP 条件下要求 NAT router，E1 有对应条件。建议精简 also required 措辞，以免读者误以为必须额外购买另一台路由器；回答并未明确声称另一个独立设备。 |
| rag-15 | E1→p10, E2→p11 | correct | complete | E1 本次完整包含 ASQ and Forbes Insights 来源及五项能力，E2 同页段落补充；列表完整、研究归属正确。 |
| rag-16 | E1→p11 | correct | complete | 本次实际 E1 在同一片段包含 71%、senior leaders、world class / at least advanced；原草稿 qual- 截断缺口已由真实新片段消除，整句得到支持。 |
| rag-18 | E1→p12, E2→p5 | correct | complete | AUC-ROC/AUCROC 是等价指标写法；E1 直接回答相关性量化指标，E2 支持 l-th layer 及 A_l(q,p_i) 的附加说明。 |
| rag-19 | E1→p6, E2→p7 | correct | complete | 首句本次明确回答 particularly on SST-2 and EmoC，实际 E1 保留该限定；E2 表 1 支持附加的 90.07/60.92/81.94/41.64/68.64 及 best performance overall tasks 原文。五个数值和列对应正确，原草稿未突出重点的问题已修复。 |

## 与原草稿的比较

| 指标 | 原草稿 AI 复核 | 当前新草稿 AI 复核 |
|---|---|---|
| 回答完整正确 | 13/14 | 14/14 |
| 实际引用支持已陈述事实 | 13/14 | 14/14 |
| 两项同时通过 | 12/14 | 14/14 |

这些题属于已使用的开发集。通用修复后的改善属于开发验证，不代表未见保留题上的泛化成绩。

## 使用范围与下一步

- 开发集覆盖法律、教材、手册、新闻、学术五个领域。金融题保留在 holdout，不能声称金融问答已参加本轮模型实测。
- 接口成功、文档隔离、引用编号、原页文字真实性、检索页命中，与语义完整性和支持充分性分别判断。
- 六份 PDF 知识库真实存在；超长句、页边界或复杂版面的文字顺序仍需原页复核。数字核验和更完整忠实度自动验证留待后续阶段。
- 团队需要逐题人工审核 20 道 gold 和 14 条实际回答；完成审核记录后才按评测脚本要求进入正式评测。

## 可追溯记录

- 新响应 SHA-256：`4900d9de36c932480c0380c47242b99dfdb38defff33f98c7c5241fa44fe9156`
- 本轮实际索引 SHA-256：`3af77dcca0b2938b2493cd68e849e86c247c45a4a8462d5a7bd457f6a37031b9`
- gold SHA-256：`f52197dcdd031bdbab51ad2b74da8dce0b0777cbcdad3f7803934fbeb00cfd98`

逐题实际回答、trace_id、引用原文、真实片段完整性、机械指标和 AI 判断均保存在同名 JSON。

本轮实跑代码提交：`596214c95eb2736b2e74efac244a7e177d8c6482`；开始评测时工作区干净；实际模型为 `deepseek-flash`。复核报告是评测完成后的新增记录。
