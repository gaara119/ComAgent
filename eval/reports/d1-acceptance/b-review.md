# D1B 独立 AI 复核报告

本报告逐项核对原有 20 道官方 gold 与原有 14 条真实开发集响应。没有新增模型请求，没有运行 6 道保留题预测，也没有修改任何人工审核状态。AI 复核不替代团队人工签字。

## 结论

- 20/20：官方来源记录、题目与标准答案原样保留、0 基页码转为 1 基物理页、PDF 哈希、证据原页文字定位均通过独立复查。
- 原有 14 条回答的 AI 语义复核：13 条 correct，1 条 incomplete（rag-19）。
- 对已陈述事实的引用支持复核：13 条 complete，1 条 incomplete（rag-16）。
- 同时满足回答完整正确和引用支持充分：12/14。这是 AI 复核观察值，不是人工确认的正式准确率或忠实度。
- 原先 14/14 的接口成功、原文真实性、页码命中可以保留；这些条件与语义/忠实度分别统计。

## 实际回答逐题验收

| 题号 | 原页/引用页 | AI 语义结论 | 已陈述事实引用支持 | 依据及处理 |
|---|---|---|---|---|
| rag-02 | E1→p1 | correct | complete | 45 天、计时起点和含所需合并后经营期间的季度限定均与原页一致；E1 虽末尾截断 operations，但同片段上文已含该词组，核心依据可完整识别。 |
| rag-03 | E1→p2 | correct | complete | 三年期限、合并生效日起算与 Section 13 范围均在 E1 中。 |
| rag-05 | E2→p1 | correct | complete | E2 明确 western side → Mersey → Tame/Etherow；回答完整。 |
| rag-06 | E1→p8 | correct | complete | 三种作物与 E1 一致；建议保留原文 perhaps 的谨慎语气，不影响本题列表匹配。 |
| rag-07 | E1→p14 | correct | complete | E1 原句同时包含南部范围和 450-550 feet；没有漏单位。 |
| rag-08 | E2→p8 | correct | complete | E2 中四组名称完整，回答没有加入旁边地层表项目。 |
| rag-10 | E1→p65, E3→p66 | correct | complete | 所问 Class B/Part 15 由 E1 支持；额外加拿大规定由 E3 支持，虽可精简但未虚构。 |
| rag-11 | E1→p3 | correct | complete | E1 标题与栏内 Create/share movies 对应；已结合原页双栏版面核对，不仅依赖串行文字。 |
| rag-12 | E1→p67, E2→p67 | correct | complete | 主目标由 E1 支持，节能带来的节省费用和资源保护由 E2 补全；两片段合起来支持整句。 |
| rag-13 | E1→p52 | correct | complete | E1 原句直接支持 AirPort Base Station 共享 IP 的回答。 |
| rag-15 | E1→p11, E2→p10 | correct | complete | 五项能力全部列出；E1/E2 的栏目、列表及 ASQ/Forbes 研究上下文可以支持。 |
| rag-16 | E3→p11 | correct | incomplete | 答案 71% 在原页是正确的，但实际唯一引用 E3 截断于 qual-，未包含 world class / at least advanced 分类条件。同页真实性和金标页命中不能证明该引用支持整句。 |
| rag-18 | E1→p12, E3→p5 | correct | complete | E1/E3 明确注意力分布与模型预测相关性由 AUC-ROC 量化；拼写变体等价。 |
| rag-19 | E2→p6, E4→p7 | incomplete | complete | 所列四个评测集及 overall tasks 表述都受到表 1/E4 支持；但没有回答原页特别突出哪些数据集这一重点，遗漏 particularly on SST-2 and EmoC，因此按题意判 incomplete，而非把所有陈述判虚构。 |

## 标准答案及来源逐题复核

保留题仅复查标准标注来源，不向运行系统提交问题。以下页码均为原 PDF 的 1 基物理页。

| 题号 | 集合 | 文档/页码 | 官方来源及证据校验 | AI 标注审阅备注 |
|---|---|---|---|---|
| rag-01 | holdout | ohr-finance-amd-2022 / p51 | 通过，原文片段可定位 | 原文明确是 2022-12-31 无未偿商业票据；不能推广到其他日期。 |
| rag-02 | dev | ohr-law-affiliate / p1 | 通过，原文片段可定位 | 45 天起点是含有所需合并后经营期间的首个财政季度结束；不是简单从合并日起算。 |
| rag-03 | dev | ohr-law-affiliate / p2 | 通过，原文片段可定位 | 三年自合并生效日开始，限定 Section 13 所需报告。 |
| rag-04 | holdout | ohr-law-affiliate / p1 | 通过，原文片段可定位 | 原文 GSMS 普通股面值 $.01；币种及小数位明确，题意匹配。 |
| rag-05 | dev | ohr-textbook-geology / p1 | 通过，原文片段可定位 | 西侧汇入 Mersey 的河流是 Tame 和 Etherow；不能混用东侧 Humber 支流。 |
| rag-06 | dev | ohr-textbook-geology / p8 | 通过，原文片段可定位 | 列举正确；原文有 perhaps，完整自然语言回答宜保留其谨慎语气。 |
| rag-07 | dev | ohr-textbook-geology / p14 | 通过，原文片段可定位 | 450 至 550 英尺限定 Sheet 南部，不是所有地区统一厚度。 |
| rag-08 | dev | ohr-textbook-geology / p8 | 通过，原文片段可定位 | 四项与原文 viz. 列举一一对应；不把旁边地层表加入答案。 |
| rag-09 | holdout | ohr-textbook-geology / p4 | 通过，原文片段可定位 | 金标数字匹配，但原文 up to 8 ft 是上限；验收应接受“最多/可达 8 英尺”，不能解读为处处固定 8 英尺。 |
| rag-10 | dev | ohr-manual-macbook-air / p65 | 通过，原文片段可定位 | FCC Part 15 对应 Class B；加拿大规定属于附加信息。 |
| rag-11 | dev | ohr-manual-macbook-air / p3 | 通过，原文片段可定位 | 原文证据片段未包含应用标题，必须结合同页 iMovie 栏标题；版面核对后答案成立。 |
| rag-12 | dev | ohr-manual-macbook-air / p67 | 通过，原文片段可定位 | ENERGY STAR 的目标是推广节能产品，不是以节省费用等结果替代目标。 |
| rag-13 | dev | ohr-manual-macbook-air / p52 | 通过，原文片段可定位 | 原文明确 AirPort Base Station 可在多台电脑之间共享一个 IP 地址。 |
| rag-14 | holdout | ohr-manual-macbook-air / p64 | 通过，原文片段可定位 | 125 度是原档案版手册规定的最大打开角度，不作为其他版本机型的建议。 |
| rag-15 | dev | ohr-news-executive-insight / p10 | 通过，原文片段可定位 | 五种能力与 ELEMENTS OF SUCCESS 列表一致，ASQ/Forbes 研究归属可由同页上下文核对。 |
| rag-16 | dev | ohr-news-executive-insight / p11 | 通过，原文片段可定位 | 71% 对应高级管理者 world class 或至少 advanced；旁边 60% 是另一受访群体及另一评价范围。 |
| rag-17 | holdout | ohr-news-executive-insight / p8 | 通过，原文片段可定位 | 姓名、职务和 Lenexa, KS 同属档案页的一个署名块；回答应按该档案时点，不当作现任信息。 |
| rag-18 | dev | ohr-academic-label-words / p12 | 通过，原文片段可定位 | AUCROC 与 AUC-ROC 是同一指标写法，原文直接量化所问相关性。 |
| rag-19 | dev | ohr-academic-label-words / p6 | 通过，原文片段可定位 | 原文 particularly 明确突出 SST-2 和 EmoC；表 1 的四个评测数据集不能直接替代题目所问重点。 |
| rag-20 | holdout | ohr-academic-label-words / p2 | 通过，原文片段可定位 | 原文写 16.7% average accuracy boost，金标忠于原文；不要自行改写成相对增幅或 16.7 倍。 |

## 具体缺陷与修复验收

1. 切片在完整句子结束之前中断，会把限定条件分隔出去。需按通用句界处理，并保留表格整行和原页来源。
2. `validate_answer` 当前只证明模型引用了允许的编号，尚不能独立证明每一句事实受该引用支持。报告必须保留人工复核入口。
3. 多数值金融/ICL 数据行不应进入章节路径。

本报告记录的是原草稿。根任务会保存修复后新索引和新开发集报告，并再次复核；原记录不覆盖。

## 可追溯记录

- 原响应文件 SHA-256：`6e6e86f473e13ce647ca9a2c494d5b896d8b0ba8d2f59d38608463e819da926e`
- 原 gold 文件 SHA-256：`f52197dcdd031bdbab51ad2b74da8dce0b0777cbcdad3f7803934fbeb00cfd98`
- 复核时本地代码提交：`5c522a48c48e11378c4b4283cc26b90c7bb4d66a`
- 逐题原文上下文、实际回答、引用文字、trace_id 和机器校验布尔值见同目录 `b-review.json`。
- 团队人工审核仍使用 `eval/datasets/rag_review/rag_gold_review.md` 和原报告目录 `human_review.md`，本报告不填写审核人、不接受 gold。

## 已完成的通用修复及本地回归

- 切片优先完整句界、章节行与数字表格整行，保持 600 字符硬上限、目标 80 字符重叠和物理页隔离。完整句比固定重叠更优先，实际重叠量写入片段。
- 超长句或物理页末不得默认为完整证据；片段记录首尾边界及不完整标志。没有改写或去连字符处理原文，字符偏移、内容哈希和真实 bbox 仍可追溯。
- 数字密集的金融/ICL 表行，即使字号较大，也不当成章节路径。索引协议版本已升为 2，要求统一重建。
- 新增 7 个泛化回归，涵盖逗号后的限定条件、连字符续行、超长句不丢字、完整句重叠持续推进、数字整行/标题过滤、前导空白的实际偏移及大字号数据行误判。
- `tests/test_rag_core.py`：34/34 通过，0 失败。未新增模型调用。
- 实际原页离线核对：新闻 p11 的 71% 与其分类条件已在同一新片段中；学术 p6 的提升陈述与特别突出的数据集条件已在同一新片段中。新真实模型表现由根任务单独保存和复核，不用离线修复推测成绩。

## 版面核对图片

以下是原 PDF 直接渲染的页面，已逐张核读。它们没有更改原 PDF。

- [新闻物理页 11](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/b-review-assets/news-p11.png)：71% 条件完整位于左栏 RANKINGS OF QUALITY PROGRAMS。
- [学术物理页 6](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/b-review-assets/academic-p6.png)：3.1.3 Results 完整句位于右栏。
- [学术物理页 7](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/b-review-assets/academic-p7.png)：Table 1 四个数据集及表述可读，用于区分“评测集全部列表”与“重点提升”。
- [手册物理页 3](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/b-review-assets/manual-p3.png)：iMovie 应用标题与对应说明位于左上，避免把双栏文字归属读错。
