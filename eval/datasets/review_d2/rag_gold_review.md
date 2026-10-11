# D2 RAG 三十题人工审核表

OHR20题保持原D1分组；新增10题含3道证据不足题。开发21题、保留9题，D2不运行保留集。机器仅核对字串来源；题意、期望答案及忠实度全部待人工审核。

保留题如需避免提前审题，统一安排D5解封后审核；本表不代表已经运行保留题。

## rag-01 holdout

审核状态：待人工审核。

问题：Did the company have any commercial paper outstanding as of December 31, 2022?

文档：AMD 2022 Form 10-K；可回答：True；物理PDF页：[51]。

期望：No

```text
As of December 31, 2022, we had
no commercial paper outstanding
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-02 dev

审核状态：待人工审核。

问题：How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published?

文档：Gulf South Medical Supply Affiliate Agreement (1997)；可回答：True；物理PDF页：[1]。

期望：45 days

```text
but in any event within 45 days after the end of the first
fiscal quarter of PSS containing the required period of post-Merger combined
operations and that it will notify the undersigned promptly following such
publication
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-03 dev

审核状态：待人工审核。

问题：For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934?

文档：Gulf South Medical Supply Affiliate Agreement (1997)；可回答：True；物理PDF页：[2]。

期望：three years

```text
PSS agrees, for a period of three years
         ------------------------                                          
after the effective date of the Merger, to file on a timely basis all reports
required to be filed by it pursuant to Section 13 of the Securities Exchange Act
of 1934, as amended, so that the public information provisions of Rule 145(d)
promulgated by the SEC as the same are presently in effect will be available to
the undersigned in the event the undersigned desires to transfer any shares of
PSS Common Stock issued to the undersigned pursuant to the Merger
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-04 holdout

审核状态：待人工审核。

问题：What is the par value of the common stock of Gulf South Medical Supply, Inc. that will be converted in the merger with Physician Sales & Service, Inc.?

文档：Gulf South Medical Supply Affiliate Agreement (1997)；可回答：True；物理PDF页：[1]。

期望：$.01

```text
and the shares of
the $.01 par value common stock of GSMS ("GSMS Common Stock") will be converted
into and exchanged for shares of the $.01 par value common stock of PSS ("PSS
Common Stock
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-05 dev

审核状态：待人工审核。

问题：Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop?

文档：The Geology of the Country Around Holmfirth and Glossop (excerpt)；可回答：True；物理PDF页：[1]。

期望：Tame and Etherow

```text
On the western side of this line the drainage is to the Mersey 
by the rivers Tame and Etherow; the basin of the latter forms a 
salient projecting some seven miles east of the general run of 
the North Sea—Irish Sea divide (see map, Fig. 1
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-06 dev

审核状态：待人工审核。

问题：What are the most satisfactory arable crops grown in the soils of the Coal Measures?

文档：The Geology of the Country Around Holmfirth and Glossop (excerpt)；可回答：True；物理PDF页：[8]。

期望：Wheat, oats, and potatoes

```text
Wheat, 
oats and potatoes are perhaps the-most satisfactory arable crops; 
swedes and turnips are apt to suffer from ‘ finger and toe ’ disease, 
unless liming is liberal
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-07 dev

审核状态：待人工审核。

问题：What is the thickness range of the Shale Grit in the southern part of the Sheet?

文档：The Geology of the Country Around Holmfirth and Glossop (excerpt)；可回答：True；物理PDF页：[14]。

期望：450 to 550 feet

```text
The Shale Grit forms a wide spread on the moors in the 
southern part of the Sheet, where it is 450 to 550 feet thick
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-08 dev

审核状态：待人工审核。

问题：In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map?

文档：The Geology of the Country Around Holmfirth and Glossop (excerpt)；可回答：True；物理PDF页：[8]。

期望：The Rough Rock Series, the Middle Grits, the Kinderscout Grits, and the Shale Grit

```text
In the Millstone Grits the shales are coloured uniformly 
throughout, but the grits and sandstones are shown by four 
colours for the main groups, viz., The Rough Rock Series, the 
Middle Grits, the Kinderscout Grits and the Shale Grit
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-09 holdout

审核状态：待人工审核。

问题：What is the thickness of the peat that largely covers the moors in the Millstone Grits area?

文档：The Geology of the Country Around Holmfirth and Glossop (excerpt)；可回答：True；物理PDF页：[4]。

期望：8 ft

```text
Apart from the exposures of bare rock mentioned above the 
moors are largely covered with peat, up to 8 ft. in thickness, con¬ 
sisting mainly of cotton-grass (Eriophorum) which flourishes 
exceedingly on the ill-drained ground, almost to the exclusion of 
sphagnum mosses
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-10 dev

审核状态：待人工审核。

问题：What type of digital device classification is specified for the equipment in accordance with the FCC rules?

文档：MacBook Air User Guide (archival edition)；可回答：True；物理PDF页：[65]。

期望：Class B

```text
This equipment has been tested and found to comply 
with the limits for a Class B digital device in accordance 
with the specifications in Part 1 5 of FCC rules
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-11 dev

审核状态：待人工审核。

问题：Which application allows you to create and share movies in minutes?

文档：MacBook Air User Guide (archival edition)；可回答：True；物理PDF页：[3]。

期望：iMovie

```text
Collect all your video in 
one library. Create and 
share movies in minutes
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-12 dev

审核状态：待人工审核。

问题：What is the primary goal of the ENERGY STAR program in which Apple participates?

文档：MacBook Air User Guide (archival edition)；可回答：True；物理PDF页：[67]。

期望：To promote energy-efficient products.

```text
The 
ENERGY STAR® program is a partnership with electronic 
equipment manufacturers to promote energy-efficient 
products
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-13 dev

审核状态：待人工审核。

问题：Which device can be used to share one IP address among multiple computers?

文档：MacBook Air User Guide (archival edition)；可回答：True；物理PDF页：[52]。

期望：AirPort Base Station

```text
You can use an AirPort Base Station to share one 
IP address among multiple computers
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-14 holdout

审核状态：待人工审核。

问题：What is the maximum angle to which the built-in display of a computer is meant to open?

文档：MacBook Air User Guide (archival edition)；可回答：True；物理PDF页：[64]。

期望：125 degrees

```text
The display is not meant 
to open past 1 25 degrees
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-15 dev

审核状态：待人工审核。

问题：What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture?

文档：Executive Insight Healthcare Magazine (archival excerpt)；可回答：True；物理PDF页：[10]。

期望：leadership,culture,strategy execution,management practices,robust process improvement

```text
Success boils down to five not-so-simple but 
fundamental capabilities—leadership, culture, 
strategy execution, management practices, and 
robust process improvement
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-16 dev

审核状态：待人工审核。

问题：What percentage of senior leaders rate their quality programs as world class or advanced according to the research?

文档：Executive Insight Healthcare Magazine (archival excerpt)；可回答：True；物理PDF页：[11]。

期望：71%

```text
According to the research, 71% of senior leaders rate their qual-
ity programs as world class or at least advanced
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-17 holdout

审核状态：待人工审核。

问题：Who is the Chief Marketing Officer of B. E. Smith, Inc and what is their location?

文档：Executive Insight Healthcare Magazine (archival excerpt)；可回答：True；物理PDF页：[8]。

期望：Christine Ricci, RN, BSN, MBA, Lenexa, KS

```text
CHRISTINE RICCI, RN, BSN, MBA
Chief Marketing Officer, 
B. E. Smith, Inc.
Lenexa, KS
www.besmith.com
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-18 dev

审核状态：待人工审核。

问题：What is the correlation between attention distributions on label words and the model's final prediction quantified by?

文档：Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning；可回答：True；物理PDF页：[12]。

期望：AUCROC score

```text
We use the AUC-
ROC score to quantify this correlation
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-19 dev

审核状态：待人工审核。

问题：Which datasets showed significant performance enhancement with the proposed anchor reweighting method?

文档：Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning；可回答：True；物理PDF页：[6]。

期望：SST-2 and EmoC

```text
As Table 1 shows, the proposed anchor re-
weighting significantly enhances ICL performance,
particularly on the SST-2 and EmoC datasets
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-20 holdout

审核状态：待人工审核。

问题：What is the average accuracy boost achieved by the anchor re-weighting method compared to standard ICL baselines?

文档：Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning；可回答：True；物理PDF页：[2]。

期望：16.7%

```text
An anchor re-weighting method
is introduced, which employs a learnable vector to
adjust the significance of different label words in
demonstrations, leading to a 16.7% average accu-
racy boost compared to standard ICL baselines
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-21 dev

审核状态：待人工审核。

问题：根据这份简介，Iron Maiden 是哪一年在什么地方组建的？

文档：Iron Maiden 铁娘子乐队公开简介；可回答：True；物理PDF页：[]。

期望：1975年，英国伦敦东部的 Leyton。

```text
1975年在伦敦东部的 Leyton 组建。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-22 dev

审核状态：待人工审核。

问题：只根据 U2 简介，U2 于哪一年在哪座城市成立？

文档：U2 乐队公开简介；可回答：True；物理PDF页：[]。

期望：1976年在都柏林成立。

```text
于1976年在都柏林成立。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-23 holdout

审核状态：待人工审核。

问题：根据这份 DOCX 介绍，Metallica 于哪一年在哪座城市由哪两位成员组建？

文档：Metallica 金属乐队公开简介；可回答：True；物理PDF页：[]。

期望：1981年在洛杉矶，由 James Hetfield 和 Lars Ulrich 组建。

```text
1981年在洛杉矶由主唱兼吉他手 James Hetfield 和鼓手 Lars Ulrich 组建。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-24 dev

审核状态：待人工审核。

问题：根据这张简介图片，Led Zeppelin 于哪一年在哪座城市成立？

文档：Led Zeppelin 齐柏林飞船乐队公开简介；可回答：True；物理PDF页：[]。

期望：1968年在伦敦成立。

```text
1968年在伦敦成立。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-25 dev

审核状态：待人工审核。

问题：根据口径手册，曲目最受欢迎的默认口径是什么，对应哪个汇总表达式？

文档：Chinook 业务指标口径手册 项目自编；可回答：True；物理PDF页：[]。

期望：默认按购买数量，使用 SUM(invoice_line.quantity)；销售额与歌单收录数是明确的备选口径。

```text
曲目最受欢迎沿用总计划的购买数量默认，即 SUM(invoice_line.quantity)。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-26 dev

审核状态：待人工审核。

问题：按口径手册，客单价的主口径全名是什么，对应哪个 SQL 表达式？

文档：Chinook 业务指标口径手册 项目自编；可回答：True；物理PDF页：[]。

期望：平均每张发票金额，AVG(invoice.total)。

```text
本项目将客单价主口径写全为平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-27 dev

审核状态：待人工审核。

问题：根据中文数据字典，customer.country 和 invoice.billing_country 分别表示什么？

文档：Chinook 数据字典 中文 项目自编；可回答：True；物理PDF页：[]。

期望：customer.country 是客户所在地国家；invoice.billing_country 是发票账单地址国家，两个业务含义应分别保留。

```text
customer.country 表示客户所在地国家。invoice.billing_country 表示发票账单地址国家。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-28 dev

审核状态：待人工审核。

问题：只依据这份 Iron Maiden 简介，列出该乐队2026年在中国每场演出的门票收入。

文档：Iron Maiden 铁娘子乐队公开简介；可回答：False；物理PDF页：[]。

期望：当前指定简介不包含所问的逐场中国演出票务收入，证据不足，应明确说明不能据此回答。

```text
无gold事实片段；应说明当前文档证据不足。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-29 holdout

审核状态：待人工审核。

问题：只依据这份 U2 简介，说明该乐队2027年巡演合同里的违约金具体金额。

文档：U2 乐队公开简介；可回答：False；物理PDF页：[]。

期望：当前指定简介不包含未来巡演合同及违约金条款，证据不足。

```text
无gold事实片段；应说明当前文档证据不足。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。

## rag-30 holdout

审核状态：待人工审核。

问题：只依据这份数据字典，customer_id 等于1的客户最喜欢哪首歌？

文档：Chinook 数据字典 中文 项目自编；可回答：False；物理PDF页：[]。

期望：字段字典没有该客户的音乐偏好事实，不能据此回答。

```text
无gold事实片段；应说明当前文档证据不足。
```

- [ ] 题意与范围正确。
- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。
- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。
