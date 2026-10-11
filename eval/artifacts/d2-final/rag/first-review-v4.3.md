# D2 RAG 最终 v4.3 第一遍 AI 逐题核验

21道开发题；原文来源、参考答案、系统实际回答分开；本轮未读保留题题意或答案，未运行保留题。

原文判断、参考答案和系统输出分开。实际运行21题：19个SUCCEEDED、1个FAILED、1个EMPTY_RESULT；Hit@5为20/20，不能据此称所有答案或引用完全正确。

本轮实际引用23条，其中PDF物理页/块框15条，非PDF来源8条。未知章节9条，不计作精确章节定位通过。

| 原编号 | 来源类型 | 参考答案 | 完整系统回答 | 引用语义 | 报告中的定位 | 实际状态 |
|---|---|---|---|---|---|---|
|rag-02|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议有条件通过|SUCCEEDED|
|rag-03|OHR原题|AI建议通过|AI发现错误|AI发现错误|证据不足|FAILED|
|rag-05|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议有条件通过|SUCCEEDED|
|rag-06|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议有条件通过|SUCCEEDED|
|rag-07|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议有条件通过|SUCCEEDED|
|rag-08|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议有条件通过|SUCCEEDED|
|rag-10|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-11|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-12|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-13|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议有条件通过|SUCCEEDED|
|rag-15|OHR原题|AI建议通过|AI建议有条件通过|AI建议有条件通过|AI建议有条件通过|SUCCEEDED|
|rag-16|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-18|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议有条件通过|SUCCEEDED|
|rag-19|OHR原题|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-21|自编|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-22|自编|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-24|自编|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-25|自编|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-26|自编|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-27|自编|AI建议通过|AI建议通过|AI建议通过|AI建议通过|SUCCEEDED|
|rag-28|自编|AI建议通过|AI建议通过|AI建议通过|AI建议通过|EMPTY_RESULT|

## rag-02

题目：How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published?

参考：45 days

参考判断：AI建议通过。原OHR问题和45 days答案精确相同。原PDF物理第1页第2条先限定PSS与GSMS合并经营财务结果，再约定在包含所需合并经营期间的PSS首个财政季度结束后45天内发布；不是从合并日直接起算45天。题问天数，gold对象、起算期间和单位均正确。

实际回答：Within 45 days after the end of the first fiscal quarter of PSS containing the required period of post-Merger combined operations. [E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议有条件通过。45天、特定首个财季结束后的起算限制与合并经营结果对象均被实际片段支持，物理第1页实框包含正文。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第1行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-law-affiliate`，物理页1，章节`[]`，框`[13.44, 389.46, 357.14, 496.86]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-02-E1-p1.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-03

题目：For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934?

参考：three years

参考判断：AI建议通过。原OHR question/answer和本题精确一致。原PDF物理第2页第6条规定PSS在Merger effective date后为期three years及时提交1934年法案Section 13要求的报告；gold三年对应报告义务期限，不是股票限制交易的另一期限。

实际回答：答案中的数字、正负号、百分比、币种或显式单位不能在该句引用的证据中核实。

实际判断：AI发现错误；引用语义：AI发现错误；定位：证据不足。最终状态为FAILED/rag_number_invalid。模型两次仅引E6（只含three years），却重复Section13与1934；本句缺E1支持。参考答案three years仍由原第2页第6条支持；不得把门禁拒绝当成正确系统回答。

建议：优先核对模型仅引E6却复述Section13/1934的失败，保留严格拒绝与真实失败，不改gold。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第2行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-05

题目：Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop?

参考：Tame and Etherow

参考判断：AI建议通过。原OHR问题、Tame and Etherow答案和物理页转换均匹配。完整第1页先定义North Sea与Irish Sea之间的primary watershed，再说明该线西侧经Tame、Etherow流入Mersey；东侧Calder、Don等及南侧Trent另有说明，不能混为答案。

实际回答：On the western side of the primary watershed, the drainage is to the Mersey by the rivers Tame and Etherow [E2]。

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议有条件通过。原扫描第1页框内明确写西侧流域经Tame与Etherow流向Mersey；真实渲染OCR坐标取代隐藏OCR假定位。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第3行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E2：`ohr-textbook-geology`，物理页1，章节`[]`，框`[31.5, 443.5, 349.0, 491.5]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-05-E2-p1.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-06

题目：What are the most satisfactory arable crops grown in the soils of the Coal Measures?

参考：Wheat, oats, and potatoes

参考判断：AI建议通过。原OHR题答精确对应。完整物理第8页首段以Coal Measures的土壤为对象，明确列Wheat、oats、potatoes为perhaps the most satisfactory arable crops，并说明swedes和turnips可能受病害；gold三种作物正确，未混入另述的树种或不适宜作物。

实际回答：Wheat, oats and potatoes are perhaps the most satisfactory arable crops in the soils of the Coal Measures [E1].

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议有条件通过。扫描第8页上方正文明确列Wheat、oats、potatoes，并保留perhaps限定；对象是Coal Measures土壤，非随后岩层表。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第4行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-textbook-geology`，物理页8，章节`[]`，框`[52.5, 83.5, 368.5, 175.0]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-06-E1-p8.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-07

题目：What is the thickness range of the Shale Grit in the southern part of the Sheet?

参考：450 to 550 feet

参考判断：AI建议通过。原OHR question/answer精确一致。完整物理第14页General Stratigraphy段规定Shale Grit在Sheet南部的moors厚450 to 550 feet；后句另谈Etherow/Tame河谷暴露。gold保留地层、南部空间范围及feet单位，正确。

实际回答：The Shale Grit in the southern part of the Sheet is 450 to 550 feet thick. [E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议有条件通过。扫描第14页GENERAL STRATIGRAPHY正文中的南部Shale Grit厚度为450至550feet，单位与区域范围均正确。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第5行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-textbook-geology`，物理页14，章节`[]`，框`[59.0, 271.5, 375.0, 381.0]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-07-E1-p14.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-08

题目：In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map?

参考：The Rough Rock Series, the Middle Grits, the Kinderscout Grits, and the Shale Grit

参考判断：AI建议通过。原OHR题答精确一致。原物理第8页Table of Formations前说明Millstone Grits中的shales统一着色，而grits和sandstones按四主组着色，随后逐项列Rough Rock Series、Middle Grits、Kinderscout Grits、Shale Grit；gold四项齐全且未把shales加入。

实际回答：The four main groups distinguished by colour on the map are the Rough Rock Series, the Middle Grits, the Kinderscout Grits and the Shale Grit. [E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议有条件通过。扫描第8页地层表前正文明确列四组、四色，四组名称齐全；框是实际区域外包框，并非四个词的精确高亮。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第6行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-textbook-geology`，物理页8，章节`[]`，框`[54.0, 322.0, 370.0, 467.5]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-08-E1-p8.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-10

题目：What type of digital device classification is specified for the equipment in accordance with the FCC rules?

参考：Class B

参考判断：AI建议通过。原OHR题答相同，原页索引64转换为物理第65页正确。原页左栏Radio and Television Interference段确写Class B digital device与Part 15 FCC rules。reference_text的Part 1 5是排版/OCR空格差异，不影响Class B答案。

实际回答：The equipment is classified as a Class B digital device in accordance with Part 15 of the FCC rules. [E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。第65页Radio and Television Interference左栏正文为ClassB/Part15；框与原文一致，正文与章节均可核验。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第7行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-manual-macbook-air`，物理页65，章节`['Radio and Television Interference']`，框`[39.84, 211.19, 176.2, 265.19]`；章节判断AI建议通过；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-10-E1-p65.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-11

题目：Which application allows you to create and share movies in minutes?

参考：iMovie

参考判断：AI建议通过。原OHR question/answer和物理第3页对应。reference_text本身只有Create and share movies in minutes描述，需通过原页空间关系确认应用名；已完整渲染查看，左上iMovie标签下直接排列该描述，右上iPhoto描述为照片，gold iMovie正确。

实际回答：iMovie allows you to create and share movies in minutes. [E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。第3页左上iMovie卡片在实际可见CropBox中，create/share movies文字位于红框内；不存在旧的129/219原点偏移。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第8行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-manual-macbook-air`，物理页3，章节`['iMovie']`，框`[27.04, 60.72, 103.24, 95.21]`；章节判断AI建议通过；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-11-E1-p3.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-12

题目：What is the primary goal of the ENERGY STAR program in which Apple participates?

参考：To promote energy-efficient products.

参考判断：AI建议通过。原OHR题答完全匹配。物理第67页ENERGY STAR Compliance段明确该计划是与电子设备制造商合作以promote energy-efficient products；gold目标正确，不能误当仅指默认休眠10分钟。

实际回答：The ENERGY STAR® program is a partnership with electronic equipment manufacturers to promote energy-efficient products, and reducing energy consumption of products saves money and helps conserve valuable resources [E1].

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。第67页ENERGY STAR Compliance段明确推广节能产品，并写减少能耗可省钱和节约资源；混合强调商标标题已核验，未沿用上方USBModem标题。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第9行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-manual-macbook-air`，物理页67，章节`['ENERGY STAR® Compliance']`，框`[39.83, 199.29, 175.93, 253.29]`；章节判断AI建议通过；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-12-E1-p67.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-13

题目：Which device can be used to share one IP address among multiple computers?

参考：AirPort Base Station

参考判断：AI建议通过。原OHR question/answer和物理页号相符。完整物理第52页条件是多电脑共享网络且ISP仅给一个IP地址，原文明确AirPort Base Station可用于共享；gold设备名称正确。

实际回答：You can use an AirPort Base Station to share one IP address among multiple computers. [E1][E2]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议有条件通过。第52页NAT独立正文明确AirPortBaseStation共享一个IP给多台电脑；两个片段来自同一真实段落框。程序To use与第4步均不再作为其章节，章节未知被明示。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第10行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-manual-macbook-air`，物理页52，章节`[]`，框`[39.84, 170.98, 319.07, 244.98]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-13-E1-p52.png`。
- E2：`ohr-manual-macbook-air`，物理页52，章节`[]`，框`[39.84, 170.98, 319.07, 244.98]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-13-E2-p52.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-15

题目：What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture?

参考：leadership,culture,strategy execution,management practices,robust process improvement

参考判断：AI建议通过。原OHR题答、doc_entry和物理第10页精确对应。原页Leading for Excellence首段署明ASQ/Forbes Insights研究，ELEMENTS OF SUCCESS段列五能力；完整第11页红色重述亦列相同五项。gold完整且管理实践/稳健流程改进未漏。

实际回答：The five fundamental capabilities identified by ASQ and Forbes Insights are: leadership, culture, strategy execution, management practices, and robust process improvement [E2][E4].

实际判断：AI建议有条件通过；引用语义：AI建议有条件通过；定位：AI建议有条件通过。五种能力与完整原文均正确；实际只引第11页能力摘要E2与第10页ELEMENTS OF SUCCESS列表E4。ASQ/Forbes归属虽在同一原文第10页左侧正文，但不在当前所引片段中，因此完整引用语义仅有条件通过。题干和文档其他未引用段落不能替代本句引用。

建议：归属句需要补实际检索到的E1引用或删去未由当前引用支持的归属；现字面门禁未覆盖所有被动表达，保留有条件状态。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第11行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E2：`ohr-news-executive-insight`，物理页11，章节`[]`，框`[36.0, 77.2, 279.91, 164.56]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-15-E2-p11.png`。
- E4：`ohr-news-executive-insight`，物理页10，章节`['ELEMENTS OF SUCCESS']`，框`[239.62, 244.42, 420.33, 307.52]`；章节判断AI建议通过；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-15-E4-p10.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-16

题目：What percentage of senior leaders rate their quality programs as world class or advanced according to the research?

参考：71%

参考判断：AI建议通过。原OHR题答精确匹配。物理第11页RANKINGS OF QUALITY PROGRAMS段明确71% of senior leaders评价world class or at least advanced；同页交代调查1,010 senior leaders与1,281 quality professionals。后述60%是另一受访组对average/below average的评价，不能替代本题71%。

实际回答：According to the research, 71% of senior leaders rate their quality programs as world class or at least advanced. [E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。第11页左栏RANKINGS段写71%seniorleaders/worldclassoratleastadvanced，未误用60%质量专业人士群体或右栏文化章节。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第12行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`ohr-news-executive-insight`，物理页11，章节`['RANKINGS OF QUALITY PROGRAMS']`，框`[36.0, 556.42, 282.3, 715.52]`；章节判断AI建议通过；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-16-E1-p11.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-18

题目：What is the correlation between attention distributions on label words and the model's final prediction quantified by?

参考：AUCROC score

参考判断：AI建议通过。原OHR问题、AUCROC score答案和物理第12页对应。原页Appendix E给出把目标位置label-word注意力当分类器预测、相对于模型实际输出计算AUC-ROC的定义；物理第5页2.3.1与2.3.2也一致。gold量化指标正确。

实际回答：The correlation is quantified using the AUC-ROC score, denoted AUCROC_l [E3].

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议有条件通过。第12页右栏AppendixE续文明确使用AUCROC量化指定注意分布与最终输出相关性；当前答案只答量化指标，不额外给无条件范围的0.8。跨栏章节与跨页标题留空。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第13行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E3：`ohr-academic-label-words`，物理页12，章节`[]`，框`[306.14, 195.82, 526.22, 356.57]`；章节判断证据不足；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-18-E3-p12.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-19

题目：Which datasets showed significant performance enhancement with the proposed anchor reweighting method?

参考：SST-2 and EmoC

参考判断：AI建议通过。原OHR问答、SST-2 and EmoC与物理第6页对应。完整第6页3.1.3明确particularly on the SST-2 and EmoC datasets，第7页Table 1说明Anchor Re-weighting整体结果。gold是在作者特别强调的数据集层次回答，未错误声称其他数据集完全无提升。

实际回答：The proposed anchor re-weighting method significantly enhanced ICL performance particularly on the SST-2 and EmoC datasets [E2].

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。第6页右栏3.1.3Results明确SST2与EmoC；当前只答所问数据集，不添加跨shot或基线不明的提升百分比；框未落在左栏公式。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第14行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E2：`ohr-academic-label-words`，物理页6，章节`['3.1.3 Results']`，框`[305.75, 427.67, 526.32, 657.92]`；章节判断AI建议通过；原图/文字证据`eval/artifacts/d2-final/rag/location-check-v4.3/rag-19-E2-p6.png`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-21

题目：根据这份简介，Iron Maiden 是哪一年在什么地方组建的？

参考：1975年，英国伦敦东部的 Leyton。

参考判断：AI建议通过。这是基于项目中文改写简介的自编题，没有OHR source_qa_id，不能标成OHR原题。已读完整Iron Maiden HTML，公开背景首段明确1975年、伦敦东部Leyton，gold年/地点正确；成立地未混同专辑1980/1982发行时间。

实际回答：Iron Maiden（铁娘子乐队）于1975年在伦敦东部的 Leyton 组建。[E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。已读取原HTML简介，原文1975年、伦敦东部Leyton支持答案；按简介问答而非外部百科补全。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第15行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`artist-iron-maiden`，物理页不适用，章节`['Iron Maiden 铁娘子乐队公开简介', '公开背景']`，框`None`；章节判断AI建议通过；原图/文字证据`见对应原始HTML/DOCX/Markdown/PNG及JSON来源表`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-22

题目：只根据 U2 简介，U2 于哪一年在哪座城市成立？

参考：1976年在都柏林成立。

参考判断：AI建议通过。自编题基于U2项目中文简介，不含OHR原题ID。完整HTML公开背景首段明确于1976年在都柏林成立；1980/1983年是作品发行日期。gold年份和城市与限定文档一致。

实际回答：U2 于 1976 年在都柏林成立。[E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。已读取原HTML简介，1976年和都柏林均为该简介原文。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第16行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`artist-u2`，物理页不适用，章节`['U2 乐队公开简介', '公开背景']`，框`None`；章节判断AI建议通过；原图/文字证据`见对应原始HTML/DOCX/Markdown/PNG及JSON来源表`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-24

题目：根据这张简介图片，Led Zeppelin 于哪一年在哪座城市成立？

参考：1968年在伦敦成立。

参考判断：AI建议通过。自编题引用Led Zeppelin简介PNG。直接打开完整原PNG视觉阅读，公开背景首段清晰写1968年在伦敦成立；后文1969/1971是专辑年份。登记PNG哈希与manifest一致，派生HTML内容一致；gold年/城市正确。

实际回答：Led Zeppelin（齐柏林飞船）于1968年在伦敦成立。[E1]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。已视觉读取原PNG：1968年伦敦成立。该图明确为项目改写排版，非维基百科原站截图；框使用原图像素，不能称为PDF点。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第17行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`artist-led-zeppelin`，物理页不适用，章节`['图像 OCR']`，框`[127.0, 57.0, 1067.0, 832.0]`；章节判断AI建议通过；原图/文字证据`见对应原始HTML/DOCX/Markdown/PNG及JSON来源表`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-25

题目：根据口径手册，曲目最受欢迎的默认口径是什么，对应哪个汇总表达式？

参考：默认按购买数量，使用 SUM(invoice_line.quantity)；销售额与歌单收录数是明确的备选口径。

参考判断：AI建议通过。项目口径手册自编题。以python-docx读取原DOCX正文和表格完整顺序；四项指标/热门曲目段明确默认购买数量SUM(invoice_line.quantity)，销售额/歌单收录数是备选。gold主表达式和备选说明均有原文依据，无发票金额或全局默认混用。

实际回答：曲目最受欢迎的默认口径是沿用总计划的购买数量默认，即 SUM(invoice_line.quantity) [E1][E2]。热门曲目的核心表达式为 SUM(invoice_line.quantity) [E2]。

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。已读取口径DOCX正文及表，默认购买数量与SUM(invoice_line.quantity)相符；金额与歌单数仅为明确备选，不混换。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第18行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`project-metric-manual`，物理页不适用，章节`['四项指标的定义与限制', '热门曲目']`，框`None`；章节判断AI建议通过；原图/文字证据`见对应原始HTML/DOCX/Markdown/PNG及JSON来源表`。
- E2：`project-metric-manual`，物理页不适用，章节`['指标对应关系']`，框`None`；章节判断AI建议通过；原图/文字证据`见对应原始HTML/DOCX/Markdown/PNG及JSON来源表`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-26

题目：按口径手册，客单价的主口径全名是什么，对应哪个 SQL 表达式？

参考：平均每张发票金额，AVG(invoice.total)。

参考判断：AI建议通过。项目口径手册自编题。原DOCX平均每张发票金额段及表格定义客单价主口径全名为平均每张发票金额，AVG(invoice.total)，每张发票同权；下一段明确每位购买客户平均金额另命名。gold全名和SQL表达式准确。

实际回答：客单价的主口径全名为“平均每张发票金额”，对应 SQL 表达式为 AVG(invoice.total)。[E2]

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。已读取口径DOCX：主口径平均每张发票金额、AVG(invoice.total)，每发票等权；非平均每位客户金额。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第19行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E2：`project-metric-manual`，物理页不适用，章节`['四项指标的定义与限制', '平均每张发票金额']`，框`None`；章节判断AI建议通过；原图/文字证据`见对应原始HTML/DOCX/Markdown/PNG及JSON来源表`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-27

题目：根据中文数据字典，customer.country 和 invoice.billing_country 分别表示什么？

参考：customer.country 是客户所在地国家；invoice.billing_country 是发票账单地址国家，两个业务含义应分别保留。

参考判断：AI建议通过。项目中文数据字典自编题。直接读取完整原MD，地区字段含义段分别定义customer.country为客户所在地国家、invoice.billing_country为发票账单地址国家；两表字段说明重复确认。原文指出当前快照值相等不改变业务口径，gold两义正确。

实际回答：customer.country 表示客户所在地国家[E1]；invoice.billing_country 表示发票账单地址国家[E1]。两者是不同字段，不可直接互换[E1][E2]。

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。已读取中文数据字典全文：customer.country客户所在地、invoice.billing_country账单地址国家，实际回答保留不同含义；现快照相等不能授权互换。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第20行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。
- E1：`project-chinook-dictionary`，物理页不适用，章节`['Chinook 数据字典 中文', '地区字段含义']`，框`None`；章节判断AI建议通过；原图/文字证据`见对应原始HTML/DOCX/Markdown/PNG及JSON来源表`。
- E2：`project-chinook-dictionary`，物理页不适用，章节`['Chinook 数据字典 中文', '表与字段', 'invoice']`，框`None`；章节判断AI建议通过；原图/文字证据`见对应原始HTML/DOCX/Markdown/PNG及JSON来源表`。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## rag-28

题目：只依据这份 Iron Maiden 简介，列出该乐队2026年在中国每场演出的门票收入。

参考：当前指定简介不包含所问的逐场中国演出票务收入，证据不足，应明确说明不能据此回答。

参考判断：AI建议通过。自编证据不足题。已读完整Iron Maiden HTML全部公开背景、资料处理说明、footer；仅有组建/作品/音乐背景，且明确不包含当代巡演收入，没有2026中国逐场演出、票数、单价或票务收入数据。gold answerable=false及EMPTY_RESULT正确；缺少正向gold_evidence并非漏证据，须以完整文档边界核验。

实际回答：所选文档未提供足以直接支持此问题的证据，当前无法核实。

实际判断：AI建议通过；引用语义：AI建议通过；定位：AI建议通过。已读取指定IronMaiden简介全文，其中没有2026年中国逐场门票收入；实际EMPTY_RESULT明确不能核实、无伪造引用。

建议：保留当前已核验答案与来源；未知章节需人审或继续保持未知。

实际原始证据：`eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl` 第21行。JSON保留原文位置、原OHR对应ID、具体引用文本和哈希。

请核对当前原文、参考题意与实际系统输出；AI判断不代替人工签字。

## 汇总与边界

{"reference_status": {"AI建议通过": 21}, "actual_status": {"AI建议通过": 19, "AI发现错误": 1, "AI建议有条件通过": 1}, "core_answer_correctness_status": {"AI建议通过": 20, "AI发现错误": 1}, "citation_support_status": {"AI建议通过": 19, "AI发现错误": 1, "AI建议有条件通过": 1}, "citation_location_status": {"AI建议有条件通过": 8, "证据不足": 1, "AI建议通过": 12}}

原始响应SHA256：`34fabf1d4a918d0aa57abcce9ee6954c66f39b9947a202ed4e1438265534d880`；索引元数据SHA256：`bdbf9c842e7b412310cc28d35acb071fef3c08e173e45d15c6ac3fd303b2d478`。

待优先人工确认：rag03严格门禁下的实际失败与rag15归属句引用不足；所有未知章节不填虚构值。没有填写A/B签名、人工日期或approved。

## 全套之后的单题probe（单独记录，不混入21题成绩）

增加通用数量/期限直接作答且不复述题干法律编号/年份规则后，仅实跑rag03，仍FAILED/rag_number_invalid。完整原始请求、命令、响应与重试被拒回答保存在 `eval/artifacts/d2-final/rag/probe-v4.4-rag03/`。由于probe没有通过，未运行v4.4全套；不称v4.3全套是这次提示改动后的成绩。该结果不改变上述21题实测统计，不覆盖旧输出，也不放松门禁或修改gold。因候选未改善，已仅回退这两条候选提示，当前源码恢复为v4.3最终21题实际测试状态；候选完整提示、小差异和回退说明独立保存在probe目录。
