# D1 RAG 20 道官方 QA 人工审核表

题目与答案保留官方英文；引用取自本地原始 PDF 文字层。页码为物理 PDF 页，1 起。
机器核对仅证明引用确实位于该页，不代表答案语义已被人工确认。
请核对题意、答案、原文、页码；实际回答是否完整、是否由引用支持，仍需逐项人工查看。

全集 20 题；开发 14 题；保留 6 题。保留题审核允许，D1 模型预测禁止默认运行。

开发集覆盖 law/textbook/manual/news/academic 五域；唯一入选 finance 文本题放在保留集。

## rag-01 · finance · holdout

审核状态：needs_human_review；官方 QA ID：`07d8ab49-76e2-44c4-b1a5-621012fdd312`。
文档：**AMD 2022 Form 10-K**（`ohr-finance-amd-2022`）；物理页：[51]。

**问题**：Did the company have any commercial paper outstanding as of December 31, 2022?

**标准答案**：No

**PDF 原文**：

```text
As of December 31, 2022, we had
no commercial paper outstanding
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-02 · law · dev

审核状态：needs_human_review；官方 QA ID：`2868c76b-7a94-4483-a8ce-122009b12bc9`。
文档：**Gulf South Medical Supply Affiliate Agreement (1997)**（`ohr-law-affiliate`）；物理页：[1]。

**问题**：How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published?

**标准答案**：45 days

**PDF 原文**：

```text
but in any event within 45 days after the end of the first
fiscal quarter of PSS containing the required period of post-Merger combined
operations and that it will notify the undersigned promptly following such
publication
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-03 · law · dev

审核状态：needs_human_review；官方 QA ID：`28805c5d-ad1b-4f60-89e4-dab20edc6d2b`。
文档：**Gulf South Medical Supply Affiliate Agreement (1997)**（`ohr-law-affiliate`）；物理页：[2]。

**问题**：For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934?

**标准答案**：three years

**PDF 原文**：

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

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-04 · law · holdout

审核状态：needs_human_review；官方 QA ID：`2866365a-fb4d-4ca6-b540-fe0246245efc`。
文档：**Gulf South Medical Supply Affiliate Agreement (1997)**（`ohr-law-affiliate`）；物理页：[1]。

**问题**：What is the par value of the common stock of Gulf South Medical Supply, Inc. that will be converted in the merger with Physician Sales & Service, Inc.?

**标准答案**：$.01

**PDF 原文**：

```text
and the shares of
the $.01 par value common stock of GSMS ("GSMS Common Stock") will be converted
into and exchanged for shares of the $.01 par value common stock of PSS ("PSS
Common Stock
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-05 · textbook · dev

审核状态：needs_human_review；官方 QA ID：`9c546b13-f581-4c4c-bdb3-784510aac204`。
文档：**The Geology of the Country Around Holmfirth and Glossop (excerpt)**（`ohr-textbook-geology`）；物理页：[1]。

**问题**：Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop?

**标准答案**：Tame and Etherow

**PDF 原文**：

```text
On the western side of this line the drainage is to the Mersey 
by the rivers Tame and Etherow; the basin of the latter forms a 
salient projecting some seven miles east of the general run of 
the North Sea—Irish Sea divide (see map, Fig. 1
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-06 · textbook · dev

审核状态：needs_human_review；官方 QA ID：`9c6725b2-7765-4a0a-95a6-ee8b3ced1be5`。
文档：**The Geology of the Country Around Holmfirth and Glossop (excerpt)**（`ohr-textbook-geology`）；物理页：[8]。

**问题**：What are the most satisfactory arable crops grown in the soils of the Coal Measures?

**标准答案**：Wheat, oats, and potatoes

**PDF 原文**：

```text
Wheat, 
oats and potatoes are perhaps the-most satisfactory arable crops; 
swedes and turnips are apt to suffer from ‘ finger and toe ’ disease, 
unless liming is liberal
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-07 · textbook · dev

审核状态：needs_human_review；官方 QA ID：`9c7b49ee-0599-4b64-890a-58b48b8f0f0d`。
文档：**The Geology of the Country Around Holmfirth and Glossop (excerpt)**（`ohr-textbook-geology`）；物理页：[14]。

**问题**：What is the thickness range of the Shale Grit in the southern part of the Sheet?

**标准答案**：450 to 550 feet

**PDF 原文**：

```text
The Shale Grit forms a wide spread on the moors in the 
southern part of the Sheet, where it is 450 to 550 feet thick
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-08 · textbook · dev

审核状态：needs_human_review；官方 QA ID：`9c6a4f19-6165-4ec6-b91d-55c727357c1d`。
文档：**The Geology of the Country Around Holmfirth and Glossop (excerpt)**（`ohr-textbook-geology`）；物理页：[8]。

**问题**：In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map?

**标准答案**：The Rough Rock Series, the Middle Grits, the Kinderscout Grits, and the Shale Grit

**PDF 原文**：

```text
In the Millstone Grits the shales are coloured uniformly 
throughout, but the grits and sandstones are shown by four 
colours for the main groups, viz., The Rough Rock Series, the 
Middle Grits, the Kinderscout Grits and the Shale Grit
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-09 · textbook · holdout

审核状态：needs_human_review；官方 QA ID：`ecee26b3-1a3b-4354-aff7-6887110eb69f`。
文档：**The Geology of the Country Around Holmfirth and Glossop (excerpt)**（`ohr-textbook-geology`）；物理页：[4]。

**问题**：What is the thickness of the peat that largely covers the moors in the Millstone Grits area?

**标准答案**：8 ft

**PDF 原文**：

```text
Apart from the exposures of bare rock mentioned above the 
moors are largely covered with peat, up to 8 ft. in thickness, con¬ 
sisting mainly of cotton-grass (Eriophorum) which flourishes 
exceedingly on the ill-drained ground, almost to the exclusion of 
sphagnum mosses
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-10 · manual · dev

审核状态：needs_human_review；官方 QA ID：`3ff0b97a-a1f9-4f23-ae4e-8052329d0a1d`。
文档：**MacBook Air User Guide (archival edition)**（`ohr-manual-macbook-air`）；物理页：[65]。

**问题**：What type of digital device classification is specified for the equipment in accordance with the FCC rules?

**标准答案**：Class B

**PDF 原文**：

```text
This equipment has been tested and found to comply 
with the limits for a Class B digital device in accordance 
with the specifications in Part 1 5 of FCC rules
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-11 · manual · dev

审核状态：needs_human_review；官方 QA ID：`401f8134-c3e5-4827-82bc-0550dfeddf7e`。
文档：**MacBook Air User Guide (archival edition)**（`ohr-manual-macbook-air`）；物理页：[3]。

**问题**：Which application allows you to create and share movies in minutes?

**标准答案**：iMovie

**PDF 原文**：

```text
Collect all your video in 
one library. Create and 
share movies in minutes
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-12 · manual · dev

审核状态：needs_human_review；官方 QA ID：`406b40fe-fcde-40fe-bf9f-52c728a96c64`。
文档：**MacBook Air User Guide (archival edition)**（`ohr-manual-macbook-air`）；物理页：[67]。

**问题**：What is the primary goal of the ENERGY STAR program in which Apple participates?

**标准答案**：To promote energy-efficient products.

**PDF 原文**：

```text
The 
ENERGY STAR® program is a partnership with electronic 
equipment manufacturers to promote energy-efficient 
products
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-13 · manual · dev

审核状态：needs_human_review；官方 QA ID：`410616bd-66bf-45f8-9cbe-3e7a74e0da1e`。
文档：**MacBook Air User Guide (archival edition)**（`ohr-manual-macbook-air`）；物理页：[52]。

**问题**：Which device can be used to share one IP address among multiple computers?

**标准答案**：AirPort Base Station

**PDF 原文**：

```text
You can use an AirPort Base Station to share one 
IP address among multiple computers
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-14 · manual · holdout

审核状态：needs_human_review；官方 QA ID：`40a2f403-fbb8-4582-b919-64532aff2792`。
文档：**MacBook Air User Guide (archival edition)**（`ohr-manual-macbook-air`）；物理页：[64]。

**问题**：What is the maximum angle to which the built-in display of a computer is meant to open?

**标准答案**：125 degrees

**PDF 原文**：

```text
The display is not meant 
to open past 1 25 degrees
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-15 · news · dev

审核状态：needs_human_review；官方 QA ID：`864962b3-e99e-4364-a7da-a98e470a03a9`。
文档：**Executive Insight Healthcare Magazine (archival excerpt)**（`ohr-news-executive-insight`）；物理页：[10]。

**问题**：What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture?

**标准答案**：leadership,culture,strategy execution,management practices,robust process improvement

**PDF 原文**：

```text
Success boils down to five not-so-simple but 
fundamental capabilities—leadership, culture, 
strategy execution, management practices, and 
robust process improvement
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-16 · news · dev

审核状态：needs_human_review；官方 QA ID：`864cce95-3e97-4b9e-a362-bc243927e72b`。
文档：**Executive Insight Healthcare Magazine (archival excerpt)**（`ohr-news-executive-insight`）；物理页：[11]。

**问题**：What percentage of senior leaders rate their quality programs as world class or advanced according to the research?

**标准答案**：71%

**PDF 原文**：

```text
According to the research, 71% of senior leaders rate their qual-
ity programs as world class or at least advanced
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-17 · news · holdout

审核状态：needs_human_review；官方 QA ID：`86480bbe-9f76-49fa-a5a6-b8997f6bb6fb`。
文档：**Executive Insight Healthcare Magazine (archival excerpt)**（`ohr-news-executive-insight`）；物理页：[8]。

**问题**：Who is the Chief Marketing Officer of B. E. Smith, Inc and what is their location?

**标准答案**：Christine Ricci, RN, BSN, MBA, Lenexa, KS

**PDF 原文**：

```text
CHRISTINE RICCI, RN, BSN, MBA
Chief Marketing Officer, 
B. E. Smith, Inc.
Lenexa, KS
www.besmith.com
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-18 · academic · dev

审核状态：needs_human_review；官方 QA ID：`5710c060-2ea2-4ca2-9fda-de0ea9b0a8ae`。
文档：**Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning**（`ohr-academic-label-words`）；物理页：[12]。

**问题**：What is the correlation between attention distributions on label words and the model's final prediction quantified by?

**标准答案**：AUCROC score

**PDF 原文**：

```text
We use the AUC-
ROC score to quantify this correlation
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-19 · academic · dev

审核状态：needs_human_review；官方 QA ID：`571aa4f6-40a2-4015-8a40-a3799a1ab357`。
文档：**Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning**（`ohr-academic-label-words`）；物理页：[6]。

**问题**：Which datasets showed significant performance enhancement with the proposed anchor reweighting method?

**标准答案**：SST-2 and EmoC

**PDF 原文**：

```text
As Table 1 shows, the proposed anchor re-
weighting significantly enhances ICL performance,
particularly on the SST-2 and EmoC datasets
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。

## rag-20 · academic · holdout

审核状态：needs_human_review；官方 QA ID：`57446b2d-ddb3-48ee-af8b-6cbeb759f3ec`。
文档：**Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning**（`ohr-academic-label-words`）；物理页：[2]。

**问题**：What is the average accuracy boost achieved by the anchor re-weighting method compared to standard ICL baselines?

**标准答案**：16.7%

**PDF 原文**：

```text
An anchor re-weighting method
is introduced, which employs a learnable vector to
adjust the significance of different label words in
demonstrations, leading to a 16.7% average accu-
racy boost compared to standard ICL baselines
```

- [ ] 问题含义明确，标准答案符合原文。
- [ ] 已打开原 PDF 核对物理页码、版面与引用。
- [ ] 已记录审核人；正式评测前用审核脚本接受该题。
