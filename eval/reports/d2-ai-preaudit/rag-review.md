# D2 RAG开发集逐题AI预审

本报告实际审核21条RAG开发题。9条保留题仅计数跳过，没有展开题目、答案或作出建议。已读10个原始文档，完整提取、渲染并视觉核对15个相关PDF物理页，直接视觉读取Led Zeppelin原PNG；原DOCX正文和表格由python-docx按原顺序读取，HTML与MD直接全文核对。14个OHR原题的question、answer、doc_entry和0-based转physical 1-based页号均匹配；30条实际引用均精确对应既有索引片段。

参考答案21条均AI建议通过；实际审核11条AI建议通过、10条AI建议有条件通过。10条发现引用定位元数据错误（rag-05/06/07/08/11/13/15/16/18/19）；rag-19还存在新增提升数值未区分1-shot/5-shot基线的问题。核心gold没有因这些问题被更改。

所有结论仅为AI预审建议。没有调用问答API或模型，没有修改原题、标准、实际答案、索引、业务代码、prompt、.env或人工审核字段；人审签名和日期仍由人审人员完成。

| review_id | 题来源 | 参考答案 | 实际总评 | 回答正确性 | 引用语义支持 | 引用定位 |
|---|---|---|---|---|---|---|
| rag:rag-02 | OHR原题 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-03 | OHR原题 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-05 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-06 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-07 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-08 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-10 | OHR原题 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-11 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-12 | OHR原题 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-13 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-15 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-16 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-18 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议通过 | AI建议通过 | AI发现错误 |
| rag:rag-19 | OHR原题 | AI建议通过 | AI建议有条件通过 | AI建议有条件通过 | AI建议有条件通过 | AI发现错误 |
| rag:rag-21 | 自编 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-22 | 自编 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-24 | 自编 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-25 | 自编 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-26 | 自编 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-27 | 自编 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |
| rag:rag-28 | 自编 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 | AI建议通过 |

## 逐题依据

### rag:rag-02

题目：How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published?

标准答案：45 days

实际（SUCCEEDED）：PSS must publish the financial results of post-Merger combined operations within 45 days after the end of the first fiscal quarter of PSS containing the required period of post-Merger combined operations. [E1]

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-law-affiliate。

参考核验：原OHR问题和45 days答案精确相同。原PDF物理第1页第2条先限定PSS与GSMS合并经营财务结果，再约定在包含所需合并经营期间的PSS首个财政季度结束后45天内发布；不是从合并日直接起算45天。题问天数，gold对象、起算期间和单位均正确。

实际核验：实际回答保留包含所需合并经营期间的财政季度这一限制，并正确回答within 45 days。E1为该页第2条完整有关段落，既有发布对象又有45天及起算点，能完整支撑回答。

建议处理：保留当前gold；人审时确认财政季度起算限制随题目和答案一起保存。

人审确认：请确认45 days是该特定财政季度结束后的上限，并据原页作最终人工签核。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf>)：物理页 1；2. Initial Restriction on Disposition。来源摘录/记录：PSS agrees that it will publish such results as promptly as practicable following the Merger ... within 45 days after the end of the first fiscal quarter of PSS containing the required period of post-Merger combined operations
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p1.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p1.txt>)：物理页 1；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p1.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p1.png>)：物理页 1；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=2868c76b-7a94-4483-a8ce-122009b12bc9。来源摘录/记录：questions=How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published? | answers=45 days | evidence_page_no=0
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:2>)：原文件行 2；rag-02 / dev。来源摘录/记录：How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published? | gold=45 days
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:1>)：原文件行 1；rag-02 / dev / response。来源摘录/记录：SUCCEEDED | PSS must publish the financial results of post-Merger combined operations within 45 days after the end of the first fiscal quarter of PSS containing the required period of post-Merger combined operations. [E1]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-02。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-02。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-02-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-02-E1-cropbox-outline.png>)：物理页 1；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：原doc_id与物理页/非PDF章节匹配；已读取原文并核对段落。bbox存在时另按真实渲染图检查。没有登记bbox或章节时不宣称它们已被精确证明。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-03

题目：For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934?

标准答案：three years

实际（SUCCEEDED）：PSS agrees to file all reports required by Section 13 of the Securities Exchange Act of 1934 for a period of three years after the effective date of the Merger [E1][E5].

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-law-affiliate。

参考核验：原OHR question/answer和本题精确一致。原PDF物理第2页第6条规定PSS在Merger effective date后为期three years及时提交1934年法案Section 13要求的报告；gold三年对应报告义务期限，不是股票限制交易的另一期限。

实际核验：实际答案正确说明合并生效日后三年。E5保留第6条标题行及three years，E1保留紧接的effective date、报告内容和Section 13；两条在同一物理页、同一条款，合读足够支持回答。E1单独不含three years，但回答同时引用E5，未据孤立片段判断。

建议处理：保留标准和当前回答；展示引用时使E1、E5的同条款关系可见。

人审确认：请核实E1和E5合起来覆盖three years、effective date和Section 13。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf>)：物理页 2；6. Filing of Reports by PSS。来源摘录/记录：6. Filing of Reports by PSS. PSS agrees, for a period of three years ... after the effective date of the Merger, to file on a timely basis all reports ... pursuant to Section 13 of the Securities Exchange Act of 1934
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p2.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p2.txt>)：物理页 2；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p2.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p2.png>)：物理页 2；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=28805c5d-ad1b-4f60-89e4-dab20edc6d2b。来源摘录/记录：questions=For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934? | answers=three years | evidence_page_no=1
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:3>)：原文件行 3；rag-03 / dev。来源摘录/记录：For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934? | gold=three years
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:2>)：原文件行 2；rag-03 / dev / response。来源摘录/记录：SUCCEEDED | PSS agrees to file all reports required by Section 13 of the Securities Exchange Act of 1934 for a period of three years after the effective date of the Merger [E1][E5].
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-03。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-03。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-03-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-03-E1-cropbox-outline.png>)：物理页 2；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：原doc_id与物理页/非PDF章节匹配；已读取原文并核对段落。bbox存在时另按真实渲染图检查。没有登记bbox或章节时不宣称它们已被精确证明。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-03-E5-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-03-E5-cropbox-outline.png>)：物理页 2；E5 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：原doc_id与物理页/非PDF章节匹配；已读取原文并核对段落。bbox存在时另按真实渲染图检查。没有登记bbox或章节时不宣称它们已被精确证明。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-05

题目：Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop?

标准答案：Tame and Etherow

实际（SUCCEEDED）：On the western side of the primary watershed, the drainage is to the Mersey by the rivers Tame and Etherow [E1].

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-textbook-geology。

参考核验：原OHR问题、Tame and Etherow答案和物理页转换均匹配。完整第1页先定义North Sea与Irish Sea之间的primary watershed，再说明该线西侧经Tame、Etherow流入Mersey；东侧Calder、Don等及南侧Trent另有说明，不能混为答案。

实际核验：实际回答准确给出Tame and Etherow并指出排向Mersey。E1为原页西侧排水完整句，与前段分水岭上下文对应，支持两个河名及流向。 原文定位复核：原地质扫描PDF隐藏文字层的bbox=[22.92,516.71,233.1,577.03]可裁出西侧河流文字，但Poppler真实可视页红框落在更低的Don/Derwent及南侧分水岭段落，不覆盖可视Tame/Etherow原句。原页MediaBox=CropBox且无旋转，不能用裁切原点偏移解释。

具体问题：

- actual_evidence.E1.bbox：原地质扫描PDF隐藏文字层的bbox=[22.92,516.71,233.1,577.03]可裁出西侧河流文字，但Poppler真实可视页红框落在更低的Don/Derwent及南侧分水岭段落，不覆盖可视Tame/Etherow原句。原页MediaBox=CropBox且无旋转，不能用裁切原点偏移解释。（error）

建议处理：保留当前gold及回答；引文定位保持物理第1页。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请确认西侧两河与前文primary watershed指同一分水岭。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf>)：物理页 1；CHAPTER I / INTRODUCTION。来源摘录/记录：On the western side of this line the drainage is to the Mersey by the rivers Tame and Etherow
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p1.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p1.txt>)：物理页 1；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p1.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p1.png>)：物理页 1；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=9c546b13-f581-4c4c-bdb3-784510aac204。来源摘录/记录：questions=Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop? | answers=Tame and Etherow | evidence_page_no=0
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:5>)：原文件行 5；rag-05 / dev。来源摘录/记录：Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop? | gold=Tame and Etherow
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:3>)：原文件行 3；rag-05 / dev / response。来源摘录/记录：SUCCEEDED | On the western side of the primary watershed, the drainage is to the Mersey by the rivers Tame and Etherow [E1].
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-05。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-05。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-05-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-05-E1-cropbox-outline.png>)：物理页 1；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：原地质扫描PDF隐藏文字层的bbox=[22.92,516.71,233.1,577.03]可裁出西侧河流文字，但Poppler真实可视页红框落在更低的Don/Derwent及南侧分水岭段落，不覆盖可视Tame/Etherow原句。原页MediaBox=CropBox且无旋转，不能用裁切原点偏移解释。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-06

题目：What are the most satisfactory arable crops grown in the soils of the Coal Measures?

标准答案：Wheat, oats, and potatoes

实际（SUCCEEDED）：Wheat, oats and potatoes are perhaps the most satisfactory arable crops grown in the soils of the Coal Measures [E1].

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-textbook-geology。

参考核验：原OHR题答精确对应。完整物理第8页首段以Coal Measures的土壤为对象，明确列Wheat、oats、potatoes为perhaps the most satisfactory arable crops，并说明swedes和turnips可能受病害；gold三种作物正确，未混入另述的树种或不适宜作物。

实际核验：实际答案正确列出三种作物，并保留perhaps语气。E1含Coal Measures土壤条件、三种作物和其他作物病害的连续段落，足够支撑对象和推荐限定。 原文定位复核：bbox=[36.12,245.41,246.9,381.44]在隐藏文字层能取出作物段，真实扫描页红框却落在Table of Formations说明段，不覆盖页面上方Coal Measures作物原句。文字层命中不等于视觉坐标准确。 section_path使用本页running header，属于粗粒度页眉提示；不将页眉当作真实细分章节。上述bbox错误按真实渲染图判断，不能被隐藏文字层的裁切文字覆盖。

具体问题：

- actual_evidence.E1.bbox：bbox=[36.12,245.41,246.9,381.44]在隐藏文字层能取出作物段，真实扫描页红框却落在Table of Formations说明段，不覆盖页面上方Coal Measures作物原句。文字层命中不等于视觉坐标准确。（error）

建议处理：保留列表gold；人工解释宜保留原文perhaps，不扩展为现代农业普遍结论。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请核实本题仅评价原文所述Coal Measures土壤里的作物。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf>)：物理页 8；物理第8页首段 / Coal Measures soils。来源摘录/记录：The soils of the Coal Measures are on the whole better ... Wheat, oats and potatoes are perhaps the-most satisfactory arable crops; swedes and turnips are apt to suffer ... unless liming is liberal.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.txt>)：物理页 8；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.png>)：物理页 8；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=9c6725b2-7765-4a0a-95a6-ee8b3ced1be5。来源摘录/记录：questions=What are the most satisfactory arable crops grown in the soils of the Coal Measures? | answers=Wheat, oats, and potatoes | evidence_page_no=7
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:6>)：原文件行 6；rag-06 / dev。来源摘录/记录：What are the most satisfactory arable crops grown in the soils of the Coal Measures? | gold=Wheat, oats, and potatoes
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:4>)：原文件行 4；rag-06 / dev / response。来源摘录/记录：SUCCEEDED | Wheat, oats and potatoes are perhaps the most satisfactory arable crops grown in the soils of the Coal Measures [E1].
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-06。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-06。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-06-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-06-E1-cropbox-outline.png>)：物理页 8；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：bbox=[36.12,245.41,246.9,381.44]在隐藏文字层能取出作物段，真实扫描页红框却落在Table of Formations说明段，不覆盖页面上方Coal Measures作物原句。文字层命中不等于视觉坐标准确。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-07

题目：What is the thickness range of the Shale Grit in the southern part of the Sheet?

标准答案：450 to 550 feet

实际（SUCCEEDED）：The Shale Grit is 450 to 550 feet thick in the southern part of the Sheet. [E1]

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-textbook-geology。

参考核验：原OHR question/answer精确一致。完整物理第14页General Stratigraphy段规定Shale Grit在Sheet南部的moors厚450 to 550 feet；后句另谈Etherow/Tame河谷暴露。gold保留地层、南部空间范围及feet单位，正确。

实际核验：实际回答450 to 550 feet in the southern part of the Sheet，未换成米或全区统一厚度。E1对应该页明确厚度句，可支撑数值、单位和空间限制。 原文定位复核：bbox=[40.68,403.4,250.62,475.17]在隐藏文字层能取出450至550 feet句，真实扫描页红框位于更低的砂岩特征/Grindslow Shales段，不覆盖可视Shale Grit厚度句。原页和答案正确，但框选定位错位。 section_path使用本页running header，属于粗粒度页眉提示；不将页眉当作真实细分章节。上述bbox错误按真实渲染图判断，不能被隐藏文字层的裁切文字覆盖。

具体问题：

- actual_evidence.E1.bbox：bbox=[40.68,403.4,250.62,475.17]在隐藏文字层能取出450至550 feet句，真实扫描页红框位于更低的砂岩特征/Grindslow Shales段，不覆盖可视Shale Grit厚度句。原页和答案正确，但框选定位错位。（error）

建议处理：保留当前gold和回答；人审检查feet与Sheet南部限定。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请确认范围是450至550英尺且仅对应Sheet南部。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf>)：物理页 14；General Stratigraphy / The Shale Grit。来源摘录/记录：The Shale Grit forms a wide spread on the moors in the southern part of the Sheet, where it is 450 to 550 feet thick.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p14.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p14.txt>)：物理页 14；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p14.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p14.png>)：物理页 14；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=9c7b49ee-0599-4b64-890a-58b48b8f0f0d。来源摘录/记录：questions=What is the thickness range of the Shale Grit in the southern part of the Sheet? | answers=450 to 550 feet | evidence_page_no=13
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:7>)：原文件行 7；rag-07 / dev。来源摘录/记录：What is the thickness range of the Shale Grit in the southern part of the Sheet? | gold=450 to 550 feet
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:5>)：原文件行 5；rag-07 / dev / response。来源摘录/记录：SUCCEEDED | The Shale Grit is 450 to 550 feet thick in the southern part of the Sheet. [E1]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-07。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-07。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-07-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-07-E1-cropbox-outline.png>)：物理页 14；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：bbox=[40.68,403.4,250.62,475.17]在隐藏文字层能取出450至550 feet句，真实扫描页红框位于更低的砂岩特征/Grindslow Shales段，不覆盖可视Shale Grit厚度句。原页和答案正确，但框选定位错位。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-08

题目：In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map?

标准答案：The Rough Rock Series, the Middle Grits, the Kinderscout Grits, and the Shale Grit

实际（SUCCEEDED）：In the Millstone Grits, the grits and sandstones are shown by four colours for the main groups, namely: The Rough Rock Series, the Middle Grits, the Kinderscout Grits and the Shale Grit [E1]。

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-textbook-geology。

参考核验：原OHR题答精确一致。原物理第8页Table of Formations前说明Millstone Grits中的shales统一着色，而grits和sandstones按四主组着色，随后逐项列Rough Rock Series、Middle Grits、Kinderscout Grits、Shale Grit；gold四项齐全且未把shales加入。

实际核验：实际回答完整列出原文四组并说明grits与sandstones四色；E1含原页有关列举段，四名称、组数和对象均有来源。 原文定位复核：bbox=[37.68,383.95,247.98,534.78]在隐藏文字层能取出四组图例说明，真实扫描页红框却位于Superficial/Solid Formations表，不覆盖上方可视四组列举句。原文字层与图像坐标不齐。 section_path使用本页running header，属于粗粒度页眉提示；不将页眉当作真实细分章节。上述bbox错误按真实渲染图判断，不能被隐藏文字层的裁切文字覆盖。

具体问题：

- actual_evidence.E1.bbox：bbox=[37.68,383.95,247.98,534.78]在隐藏文字层能取出四组图例说明，真实扫描页红框却位于Superficial/Solid Formations表，不覆盖上方可视四组列举句。原文字层与图像坐标不齐。（error）

建议处理：保留当前gold和回答，不把图例组数理解为地质总层数。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请确认四项名称和地图中grits/sandstones着色这一对象。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf>)：物理页 8；Table of Formations前说明段。来源摘录/记录：In the Millstone Grits the shales are coloured uniformly throughout, but the grits and sandstones are shown by four colours for the main groups, viz., The Rough Rock Series, the Middle Grits, the Kinderscout Grits and the Shale Grit.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.txt>)：物理页 8；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.png>)：物理页 8；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=9c6a4f19-6165-4ec6-b91d-55c727357c1d。来源摘录/记录：questions=In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map? | answers=The Rough Rock Series, the Middle Grits, the Kinderscout Grits, and the Shale Grit | evidence_page_no=7
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:8>)：原文件行 8；rag-08 / dev。来源摘录/记录：In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map? | gold=The Rough Rock Series, the Middle Grits, the Kinderscout Grits, and the Shale Grit
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:6>)：原文件行 6；rag-08 / dev / response。来源摘录/记录：SUCCEEDED | In the Millstone Grits, the grits and sandstones are shown by four colours for the main groups, namely: The Rough Rock Series, the Middle Grits, the Kinderscout Grits and the Shale Grit [E1]。
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-08。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-08。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-08-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-08-E1-cropbox-outline.png>)：物理页 8；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：bbox=[37.68,383.95,247.98,534.78]在隐藏文字层能取出四组图例说明，真实扫描页红框却位于Superficial/Solid Formations表，不覆盖上方可视四组列举句。原文字层与图像坐标不齐。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-10

题目：What type of digital device classification is specified for the equipment in accordance with the FCC rules?

标准答案：Class B

实际（SUCCEEDED）：The equipment is specified as a Class B digital device in accordance with the specifications in Part 15 of FCC rules [E1].

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-manual-macbook-air。

参考核验：原OHR题答相同，原页索引64转换为物理第65页正确。原页左栏Radio and Television Interference段确写Class B digital device与Part 15 FCC rules。reference_text的Part 1 5是排版/OCR空格差异，不影响Class B答案。

实际核验：实际回答Class B并正确写Part 15。E1机械上与索引精确对应，但其text混入右栏关于未授权修改的句子；原页视觉核对确认Class B句完整位于左栏，数字和分类语义成立。该读取顺序瑕疵未导致本题答错。

具体问题：

- actual_evidence.E1.text：双栏提取交错右栏Important句，影响引文可读性；原页已视觉确定左栏Class B句，本题支撑仍成立。（提示）

建议处理：人审可通过本题语义；登记双栏读取顺序问题供后续资料处理另案修正，本次不改索引或gold。

人审确认：请看原第65页左栏确认Class B，不把E1交错文本当连续原段。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/manual/Macbook_air.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/manual/Macbook_air.pdf>)：物理页 65；Regulatory Compliance Information / Radio and Television Interference（左栏）。来源摘录/记录：This equipment has been tested and found to comply with the limits for a Class B digital device in accordance with the specifications in Part 15 of FCC rules.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p65.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p65.txt>)：物理页 65；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p65.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p65.png>)：物理页 65；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=3ff0b97a-a1f9-4f23-ae4e-8052329d0a1d。来源摘录/记录：questions=What type of digital device classification is specified for the equipment in accordance with the FCC rules? | answers=Class B | evidence_page_no=64
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:10>)：原文件行 10；rag-10 / dev。来源摘录/记录：What type of digital device classification is specified for the equipment in accordance with the FCC rules? | gold=Class B
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:7>)：原文件行 7；rag-10 / dev / response。来源摘录/记录：SUCCEEDED | The equipment is specified as a Class B digital device in accordance with the specifications in Part 15 of FCC rules [E1].
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-10。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-10。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-11

题目：Which application allows you to create and share movies in minutes?

标准答案：iMovie

实际（SUCCEEDED）：iMovie allows you to create and share movies in minutes. [E1]

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-manual-macbook-air。

参考核验：原OHR question/answer和物理第3页对应。reference_text本身只有Create and share movies in minutes描述，需通过原页空间关系确认应用名；已完整渲染查看，左上iMovie标签下直接排列该描述，右上iPhoto描述为照片，gold iMovie正确。

实际核验：实际回答iMovie。E1文本含iMovie/iPhoto并出现交错两栏，单靠线性字串不足区分应用；原页完整视觉检查确认影片描述归属iMovie。因此引用可支持结论，依据包括原页布局，而非仅词面命中。 原文定位复核：E1 bbox=[27.21,99.39,325.38,117.81]；考虑原PDF CropBox偏移(129,219)后，仅框到iMovie/iPhoto网址与Help行，未覆盖Create and share movies in minutes描述。section_path=[]只是未登记章节，本身不判错。

具体问题：

- reference_text; actual_evidence.E1.text：引用描述与应用名的归属依赖原页卡片布局；线性提取与iPhoto交错，已用原页视觉补足核验。（提示）
- actual_evidence.E1.bbox：E1 bbox=[27.21,99.39,325.38,117.81]；考虑原PDF CropBox偏移(129,219)后，仅框到iMovie/iPhoto网址与Help行，未覆盖Create and share movies in minutes描述。section_path=[]只是未登记章节，本身不判错。（error）

建议处理：保留iMovie；人工审核随附原页PNG，对照左上卡片。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请确认左上iMovie标题与影片描述的视觉归属。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/manual/Macbook_air.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/manual/Macbook_air.pdf>)：物理页 3；物理第3页左上iMovie应用卡片。来源摘录/记录：iMovie / Collect all your video in one library. Create and share movies in minutes.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p3.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p3.txt>)：物理页 3；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p3.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p3.png>)：物理页 3；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=401f8134-c3e5-4827-82bc-0550dfeddf7e。来源摘录/记录：questions=Which application allows you to create and share movies in minutes? | answers=iMovie | evidence_page_no=2
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:11>)：原文件行 11；rag-11 / dev。来源摘录/记录：Which application allows you to create and share movies in minutes? | gold=iMovie
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:8>)：原文件行 8；rag-11 / dev / response。来源摘录/记录：SUCCEEDED | iMovie allows you to create and share movies in minutes. [E1]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-11。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-11。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-11-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-11-E1-cropbox-outline.png>)：物理页 3；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：E1 bbox=[27.21,99.39,325.38,117.81]；考虑原PDF CropBox偏移(129,219)后，仅框到iMovie/iPhoto网址与Help行，未覆盖Create and share movies in minutes描述。section_path=[]只是未登记章节，本身不判错。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-12

题目：What is the primary goal of the ENERGY STAR program in which Apple participates?

标准答案：To promote energy-efficient products.

实际（SUCCEEDED）：The ENERGY STAR program is a partnership with electronic equipment manufacturers to promote energy-efficient products; reducing energy consumption of products saves money and helps conserve valuable resources [E1]. As an ENERGY STAR partner, Apple has determined that standard configurations of this product meet the ENERGY STAR guidelines for energy efficiency [E2].

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-manual-macbook-air。

参考核验：原OHR题答完全匹配。物理第67页ENERGY STAR Compliance段明确该计划是与电子设备制造商合作以promote energy-efficient products；gold目标正确，不能误当仅指默认休眠10分钟。

实际核验：实际答对推广节能产品，并补述节约金钱/资源及Apple标准配置符合指南。E1涵盖推广目标及money/resources，E2涵盖Apple参与和标准配置，原页左栏连续段落均有依据；未将VCCI段当作ENERGY STAR内容。

建议处理：保留当前gold和实际回答；审核Apple补充句时同时看E2。

人审确认：请确认问题问计划推广目标，E1/E2各自覆盖实际回答的补充说明。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/manual/Macbook_air.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/manual/Macbook_air.pdf>)：物理页 67；ENERGY STAR Compliance（左栏）。来源摘录/记录：As an ENERGY STAR partner, Apple has determined that standard configurations of this product meet the ENERGY STAR guidelines ... The ENERGY STAR program is a partnership with electronic equipment manufacturers to promote energy-efficient products. Reducing energy consumption of products saves money and helps conserve valuable resources.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p67.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p67.txt>)：物理页 67；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p67.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p67.png>)：物理页 67；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=406b40fe-fcde-40fe-bf9f-52c728a96c64。来源摘录/记录：questions=What is the primary goal of the ENERGY STAR program in which Apple participates? | answers=To promote energy-efficient products. | evidence_page_no=66
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:12>)：原文件行 12；rag-12 / dev。来源摘录/记录：What is the primary goal of the ENERGY STAR program in which Apple participates? | gold=To promote energy-efficient products.
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:9>)：原文件行 9；rag-12 / dev / response。来源摘录/记录：SUCCEEDED | The ENERGY STAR program is a partnership with electronic equipment manufacturers to promote energy-efficient products; reducing energy consumption of products saves money and helps conserve valuable resources [E1]. As an ENERGY STAR partner, Apple has determined that standard configurations of this product meet the ENERGY STAR guidelines for energy efficiency [E2].
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-12。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-12。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-12-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-12-E1-cropbox-outline.png>)：物理页 67；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：原doc_id与物理页/非PDF章节匹配；已读取原文并核对段落。bbox存在时另按真实渲染图检查。没有登记bbox或章节时不宣称它们已被精确证明。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-12-E2-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-12-E2-cropbox-outline.png>)：物理页 67；E2 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：原doc_id与物理页/非PDF章节匹配；已读取原文并核对段落。bbox存在时另按真实渲染图检查。没有登记bbox或章节时不宣称它们已被精确证明。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-13

题目：Which device can be used to share one IP address among multiple computers?

标准答案：AirPort Base Station

实际（SUCCEEDED）：You can use an AirPort Base Station to share one IP address among multiple computers. A router capable of sharing the connection, also known as network address translation (NAT) or "IP masquerading," is required if the ISP provides only one IP address. [E1][E2]

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-manual-macbook-air。

参考核验：原OHR question/answer和物理页号相符。完整物理第52页条件是多电脑共享网络且ISP仅给一个IP地址，原文明确AirPort Base Station可用于共享；gold设备名称正确。

实际核验：实际回答AirPort Base Station，另补仅一个IP时需具有共享能力的路由器/NAT。E2直接支持设备，E1支持前提及NAT/IP masquerading术语，两条同页连续，补述正确且有引文。 原文定位复核：“4 Follow the onscreen instructions.”是Network Diagnostics步骤4，而非共享IP段落的章节标题；字段把步骤文本误登记为章节。PDF物理第52页正确，CropBox偏移后bbox能包含支持句，不据MediaBox未平移裁切结果误判坐标。

具体问题：

- actual_evidence.E1/E2.section_path：“4 Follow the onscreen instructions.”是Network Diagnostics步骤4，而非共享IP段落的章节标题；字段把步骤文本误登记为章节。PDF物理第52页正确，CropBox偏移后bbox能包含支持句，不据MediaBox未平移裁切结果误判坐标。（error）

建议处理：保留当前设备gold与回答，勿把只有一个IP的条件外推到所有ISP配置。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请确认E1支持条件和NAT，E2支持AirPort设备名称。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/manual/Macbook_air.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/manual/Macbook_air.pdf>)：物理页 52；Chapter 3 Problem, Meet Solution / Internet connection共享段。来源摘录/记录：If only one IP address is provided, then you must have a router capable of sharing the connection ... You can use an AirPort Base Station to share one IP address among multiple computers.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p52.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p52.txt>)：物理页 52；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p52.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p52.png>)：物理页 52；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=410616bd-66bf-45f8-9cbe-3e7a74e0da1e。来源摘录/记录：questions=Which device can be used to share one IP address among multiple computers? | answers=AirPort Base Station | evidence_page_no=51
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:13>)：原文件行 13；rag-13 / dev。来源摘录/记录：Which device can be used to share one IP address among multiple computers? | gold=AirPort Base Station
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:10>)：原文件行 10；rag-13 / dev / response。来源摘录/记录：SUCCEEDED | You can use an AirPort Base Station to share one IP address among multiple computers. A router capable of sharing the connection, also known as network address translation (NAT) or "IP masquerading," is required if the ISP provides only one IP address. [E1][E2]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-13。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-13。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-13-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-13-E1-cropbox-outline.png>)：物理页 52；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：“4 Follow the onscreen instructions.”是Network Diagnostics步骤4，而非共享IP段落的章节标题；字段把步骤文本误登记为章节。PDF物理第52页正确，CropBox偏移后bbox能包含支持句，不据MediaBox未平移裁切结果误判坐标。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-13-E2-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-13-E2-cropbox-outline.png>)：物理页 52；E2 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：“4 Follow the onscreen instructions.”是Network Diagnostics步骤4，而非共享IP段落的章节标题；字段把步骤文本误登记为章节。PDF物理第52页正确，CropBox偏移后bbox能包含支持句，不据MediaBox未平移裁切结果误判坐标。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-15

题目：What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture?

标准答案：leadership,culture,strategy execution,management practices,robust process improvement

实际（SUCCEEDED）：ASQ and Forbes Insights identified five fundamental capabilities essential for building a successful organizational culture: leadership, culture, strategy execution, management practices, and robust process improvement [E1][E3].

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-news-executive-insight。

参考核验：原OHR题答、doc_entry和物理第10页精确对应。原页Leading for Excellence首段署明ASQ/Forbes Insights研究，ELEMENTS OF SUCCESS段列五能力；完整第11页红色重述亦列相同五项。gold完整且管理实践/稳健流程改进未漏。

实际核验：实际答案五项齐全。E1是第11页重述的截断部分，末尾robust pro-尚未完整；E3是第10页Elements of Success含完整robust process improvement的段落。合读E3足以支撑完整清单，不能称E1独自覆盖五项。 原文定位复核：E1 bbox=[432.28,50.71,534.6,66.45]在原第11页只框到EYE ON QUALITY页眉，不覆盖五能力正文。E3第10页物理页/Elements of Success定位正确，故回答语义仍可获充分支持。

具体问题：

- actual_evidence.E1.bbox：E1 bbox=[432.28,50.71,534.6,66.45]在原第11页只框到EYE ON QUALITY页眉，不覆盖五能力正文。E3第10页物理页/Elements of Success定位正确，故回答语义仍可获充分支持。（error）

建议处理：保留清单和回答；人审据第10页完整句，记录E1截断但E3补足。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请确认五项均存在于E3，ASQ/Forbes归属来自文章首段。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf>)：物理页 10；Leading for Excellence / ELEMENTS OF SUCCESS。来源摘录/记录：Success boils down to five not-so-simple but fundamental capabilities—leadership, culture, strategy execution, management practices, and robust process improvement.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p10.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p10.txt>)：物理页 10；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p10.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p10.png>)：物理页 10；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=864962b3-e99e-4364-a7da-a98e470a03a9。来源摘录/记录：questions=What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture? | answers=leadership,culture,strategy execution,management practices,robust process improvement | evidence_page_no=9
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:15>)：原文件行 15；rag-15 / dev。来源摘录/记录：What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture? | gold=leadership,culture,strategy execution,management practices,robust process improvement
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:11>)：原文件行 11；rag-15 / dev / response。来源摘录/记录：SUCCEEDED | ASQ and Forbes Insights identified five fundamental capabilities essential for building a successful organizational culture: leadership, culture, strategy execution, management practices, and robust process improvement [E1][E3].
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-15。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-15。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-15-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-15-E1-cropbox-outline.png>)：物理页 11；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：E1 bbox=[432.28,50.71,534.6,66.45]在原第11页只框到EYE ON QUALITY页眉，不覆盖五能力正文。E3第10页物理页/Elements of Success定位正确，故回答语义仍可获充分支持。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-16

题目：What percentage of senior leaders rate their quality programs as world class or advanced according to the research?

标准答案：71%

实际（SUCCEEDED）：According to the research, 71% of senior leaders rate their quality programs as world class or at least advanced. [E1]

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-news-executive-insight。

参考核验：原OHR题答精确匹配。物理第11页RANKINGS OF QUALITY PROGRAMS段明确71% of senior leaders评价world class or at least advanced；同页交代调查1,010 senior leaders与1,281 quality professionals。后述60%是另一受访组对average/below average的评价，不能替代本题71%。

实际核验：实际回答71%并保留senior leaders、world class/at least advanced。E1虽含两栏交错文本，原页左下原段视觉确认百分比对应高层领导评价而非右栏医院认可次数；回答对象、比例和评级范围均正确。 原文定位复核：登记BUILDING A NEW CULTURE，但71%句属物理第11页左栏RANKINGS OF QUALITY PROGRAMS；邻右栏章节被错误继承。

具体问题：

- actual_evidence.E1.text：双栏交错插入医院经验句，已按原页左栏确认71%对应senior leaders。（提示）
- actual_evidence.E1.section_path：登记BUILDING A NEW CULTURE，但71%句属物理第11页左栏RANKINGS OF QUALITY PROGRAMS；邻右栏章节被错误继承。（error）

建议处理：保留71%；人工终审检查受访者组别，避免与quality professionals的60%混用。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请确认分母/对象是senior leaders，71%对应world class或至少advanced。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf>)：物理页 11；RANKINGS OF QUALITY PROGRAMS（左栏）；研究样本说明。来源摘录/记录：The research draws on the responses of 1,010 senior leaders and 1,281 quality professionals worldwide. ... According to the research, 71% of senior leaders rate their quality programs as world class or at least advanced.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p11.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p11.txt>)：物理页 11；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p11.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p11.png>)：物理页 11；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=864cce95-3e97-4b9e-a362-bc243927e72b。来源摘录/记录：questions=What percentage of senior leaders rate their quality programs as world class or advanced according to the research? | answers=71% | evidence_page_no=10
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:16>)：原文件行 16；rag-16 / dev。来源摘录/记录：What percentage of senior leaders rate their quality programs as world class or advanced according to the research? | gold=71%
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:12>)：原文件行 12；rag-16 / dev / response。来源摘录/记录：SUCCEEDED | According to the research, 71% of senior leaders rate their quality programs as world class or at least advanced. [E1]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-16。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-16。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-18

题目：What is the correlation between attention distributions on label words and the model's final prediction quantified by?

标准答案：AUCROC score

实际（SUCCEEDED）：The correlation between attention distributions on the label words of the target position and the model's final prediction is quantified using the AUC-ROC score. [E2] The AUCROC for deep layers approaches 0.8, illustrating a strong correlation between the attention distributions on label words of the target position and the model's final prediction. [E4]

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-academic-label-words。

参考核验：原OHR问题、AUCROC score答案和物理第12页对应。原页Appendix E给出把目标位置label-word注意力当分类器预测、相对于模型实际输出计算AUC-ROC的定义；物理第5页2.3.1与2.3.2也一致。gold量化指标正确。

实际核验：核心答案AUC-ROC正确。补述deep layers approaches 0.8可由E4及原第5页支持，原研究的GPT2-XL/GPT-J四数据集平均上下文已核对。E2文本确出自原第12页，但section_path标Limitations，真实段属Appendix E Details for the Calculation of AUCROC；E4标题也混入右栏邻句。doc_id与physical page、正文支撑有效，章节定位需人工确认后修订建议另案处理。 原文定位复核：E2登记Limitations，原第12页属于Appendix E Details for the Calculation of AUCROC。E4的2.3.2标题混入右栏to denote them等正文。章节定位明确错误；doc_id/物理页和实际语义仍正确。

具体问题：

- actual_evidence.E2/E4.section_path：E2登记Limitations，原第12页属于Appendix E Details for the Calculation of AUCROC。E4的2.3.2标题混入右栏to denote them等正文。章节定位明确错误；doc_id/物理页和实际语义仍正确。（error）

建议处理：核心答案可保留。人工终审按原第12页Appendix E及第5页2.3.2确认引用；建议后续单独修复章节定位，若只需简答可省去未被问题要求的0.8补述。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请确认核心答案和0.8补述有原文支持，并明确E2章节定位错误如何处置；本报告未更改索引。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/academic/2305.14160v4.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/academic/2305.14160v4.pdf>)：物理页 12；E. Details for the Calculation of AUCROC（原第12页左栏开始、右栏续文）。来源摘录/记录：We use the AUC-ROC score to quantify this correlation. ... compute the AUC-ROC value of this prediction relative to the actual model output.
- [data/docs/raw/academic/2305.14160v4.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/academic/2305.14160v4.pdf>)：物理页 5；2.3.1 Experiments / 2.3.2 Results and Analysis / Figure 5。来源摘录/记录：Figures 5a and 5b delineate correlation metrics for GPT2-XL and GPT-J, averaged across four datasets. The AUCROC for deep layers approaches 0.8.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p5.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p5.txt>)：物理页 5；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p5.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p5.png>)：物理页 5；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p12.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p12.txt>)：物理页 12；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p12.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p12.png>)：物理页 12；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=5710c060-2ea2-4ca2-9fda-de0ea9b0a8ae。来源摘录/记录：questions=What is the correlation between attention distributions on label words and the model's final prediction quantified by? | answers=AUCROC score | evidence_page_no=11
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:18>)：原文件行 18；rag-18 / dev。来源摘录/记录：What is the correlation between attention distributions on label words and the model's final prediction quantified by? | gold=AUCROC score
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:13>)：原文件行 13；rag-18 / dev / response。来源摘录/记录：SUCCEEDED | The correlation between attention distributions on the label words of the target position and the model's final prediction is quantified using the AUC-ROC score. [E2] The AUCROC for deep layers approaches 0.8, illustrating a strong correlation between the attention distributions on label words of the target position and the model's final prediction. [E4]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-18。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-18。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-19

题目：Which datasets showed significant performance enhancement with the proposed anchor reweighting method?

标准答案：SST-2 and EmoC

实际（SUCCEEDED）：根据表1，所提出的锚点重加权方法在SST-2和EmoC数据集上显著提升了ICL性能，尤其在SST-2（从64.75提升至90.07）和EmoC（从15.44提升至41.64）数据集上表现突出 [E1][E5]。

建议：参考=AI建议通过；实际=AI建议有条件通过；正确性=AI建议有条件通过；引用语义支持=AI建议有条件通过；引用定位=AI发现错误。

题目来源：OHR原题；文档性质：OHR原始PDF；doc_id=ohr-academic-label-words。

参考核验：原OHR问答、SST-2 and EmoC与物理第6页对应。完整第6页3.1.3明确particularly on the SST-2 and EmoC datasets，第7页Table 1说明Anchor Re-weighting整体结果。gold是在作者特别强调的数据集层次回答，未错误声称其他数据集完全无提升。

实际核验：核心SST-2/EmoC答案正确且E1直接支持。新增SST-2 64.75→90.07与EmoC 15.44→41.64各数字确在E5表1，但64.75是Vanilla 5-shot，15.44是Vanilla 1-shot，90.07/41.64是Anchor 1-shot。原第6页3.1.2明确设置两套baseline，故这些提升数值只有分别标明基线才有清晰实验含义；当前回答未区分两套基线，不能只因数字出现就视作完整语义支撑。E5 section_path亦为邻页续句而非Table 1定位。 原文定位复核：E1 bbox=[70.87,486.56,152.06,499.36]在原第6页裁到左栏“In this equation, βi”方程说明，不覆盖右栏3.1.3核心支持句。E5章节路径“0 role that anchors play in ICL.”是前页续句/公式残片，原文位置是第7页Table 1。

具体问题：

- actual_answer.补充提升数值：SST-2比较采用Vanilla 5-shot基线，EmoC采用Vanilla 1-shot基线；回答未说明两者不同。单个数字正确不等于比较语义完整。（需人工确认）
- actual_evidence.E1.bbox; E5.section_path：E1 bbox=[70.87,486.56,152.06,499.36]在原第6页裁到左栏“In this equation, βi”方程说明，不覆盖右栏3.1.3核心支持句。E5章节路径“0 role that anchors play in ICL.”是前页续句/公式残片，原文位置是第7页Table 1。（error）

建议处理：保留gold的SST-2和EmoC。人审可按原题只保留数据集名称；若保留数值，逐项注明Vanilla 1-shot/5-shot→Anchor 1-shot及GPT2-XL、五随机种子平均的实验范围。不得在本次审核中静默改答案。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

人审确认：请明确接受仅核心答案，还是要求补充数值逐项标baseline；当前增写比较需人工处理。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/academic/2305.14160v4.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/academic/2305.14160v4.pdf>)：物理页 6；3.1.2 Experiments / 3.1.3 Results。来源摘录/记录：As Table 1 shows, the proposed anchor re-weighting significantly enhances ICL performance, particularly on the SST-2 and EmoC datasets.
- [data/docs/raw/academic/2305.14160v4.pdf](<E:/中国电子杯-赛题八/system/data/docs/raw/academic/2305.14160v4.pdf>)：物理页 7；Table 1 / Method × Dataset。来源摘录/记录：Vanilla In-Context Learning (1-shot per class): SST-2 61.28, EmoC 15.44; Vanilla In-Context Learning (5-shot per class): SST-2 64.75, EmoC 9.80; Anchor Re-weighting (1-shot per class): SST-2 90.07, EmoC 41.64.
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p6.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p6.txt>)：物理页 6；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p6.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p6.png>)：物理页 6；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p7.txt](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p7.txt>)：物理页 7；完整物理页文本（pdfplumber）。来源摘录/记录：完整上下文在该文本文件；正文核验语句见上面的原始文件引用。
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p7.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p7.png>)：物理页 7；完整物理页Poppler渲染；已视觉检查。来源摘录/记录：页面标题、表格/栏位、脚注和有关句子均在完整页图内。
- [data/raw/ohr/qas_v2.json](<E:/中国电子杯-赛题八/system/data/raw/ohr/qas_v2.json>)：ID=571aa4f6-40a2-4015-8a40-a3799a1ab357。来源摘录/记录：questions=Which datasets showed significant performance enhancement with the proposed anchor reweighting method? | answers=SST-2 and EmoC | evidence_page_no=5
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:19>)：原文件行 19；rag-19 / dev。来源摘录/记录：Which datasets showed significant performance enhancement with the proposed anchor reweighting method? | gold=SST-2 and EmoC
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:14>)：原文件行 14；rag-19 / dev / response。来源摘录/记录：SUCCEEDED | 根据表1，所提出的锚点重加权方法在SST-2和EmoC数据集上显著提升了ICL性能，尤其在SST-2（从64.75提升至90.07）和EmoC（从15.44提升至41.64）数据集上表现突出 [E1][E5]。
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-19。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-19。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-19-E1-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-19-E1-cropbox-outline.png>)：物理页 6；E1 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：E1 bbox=[70.87,486.56,152.06,499.36]在原第6页裁到左栏“In this equation, βi”方程说明，不覆盖右栏3.1.3核心支持句。E5章节路径“0 role that anchors play in ICL.”是前页续句/公式残片，原文位置是第7页Table 1。
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-19-E5-cropbox-outline.png](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-19-E5-cropbox-outline.png>)：物理页 7；E5 / 原始完整物理页及实际bbox红框（已视觉核对）。来源摘录/记录：E1 bbox=[70.87,486.56,152.06,499.36]在原第6页裁到左栏“In this equation, βi”方程说明，不覆盖右栏3.1.3核心支持句。E5章节路径“0 role that anchors play in ICL.”是前页续句/公式残片，原文位置是第7页Table 1。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-21

题目：根据这份简介，Iron Maiden 是哪一年在什么地方组建的？

标准答案：1975年，英国伦敦东部的 Leyton。

实际（SUCCEEDED）：Iron Maiden（铁娘子乐队）由贝斯手及主要创作者 Steve Harris 于1975年在伦敦东部的 Leyton 组建。[E1]

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：自编；文档性质：百科条目中文翻译改写的项目简介；doc_id=artist-iron-maiden。

参考核验：这是基于项目中文改写简介的自编题，没有OHR source_qa_id，不能标成OHR原题。已读完整Iron Maiden HTML，公开背景首段明确1975年、伦敦东部Leyton，gold年/地点正确；成立地未混同专辑1980/1982发行时间。

实际核验：实际回答1975年伦敦东部Leyton，并补充Steve Harris角色；E1与HTML公开背景首段及索引相符，年、地点、创建者均逐项有文档支持。仅对指定改写文档内事实审查，未外网验证百科原站。

建议处理：保留答案并标清题为自编、材料为项目中文改写简介。

人审确认：请确认文档层面1975/Leyton及Steve Harris补述；外部百科真实性不属于本次限定材料核验。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/d2/iron-maiden.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/iron-maiden.html>)：Iron Maiden 铁娘子乐队公开简介 / 公开背景（首段）。来源摘录/记录：Iron Maiden（铁娘子乐队）是英国重金属乐队，由贝斯手及主要创作者 Steve Harris 于1975年在伦敦东部的 Leyton 组建。
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:21>)：原文件行 21；rag-21 / dev。来源摘录/记录：根据这份简介，Iron Maiden 是哪一年在什么地方组建的？ | gold=1975年，英国伦敦东部的 Leyton。
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:15>)：原文件行 15；rag-21 / dev / response。来源摘录/记录：SUCCEEDED | Iron Maiden（铁娘子乐队）由贝斯手及主要创作者 Steve Harris 于1975年在伦敦东部的 Leyton 组建。[E1]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-21。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-21。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-22

题目：只根据 U2 简介，U2 于哪一年在哪座城市成立？

标准答案：1976年在都柏林成立。

实际（SUCCEEDED）：U2 于1976年在都柏林成立。[E1]

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：自编；文档性质：百科条目中文翻译改写的项目简介；doc_id=artist-u2。

参考核验：自编题基于U2项目中文简介，不含OHR原题ID。完整HTML公开背景首段明确于1976年在都柏林成立；1980/1983年是作品发行日期。gold年份和城市与限定文档一致。

实际核验：实际仅答1976年在都柏林成立，E1为同一公开背景首段，与原HTML和索引精确对应，足够支持年份及城市。未借助外部常识。

建议处理：保留当前gold及实际回答，题来源标自编、文档来源标中文改写。

人审确认：请确认1976和都柏林均取自指定简介首段。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/d2/u2.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/u2.html>)：U2 乐队公开简介 / 公开背景（首段）。来源摘录/记录：U2是爱尔兰摇滚乐队，于1976年在都柏林成立。
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:22>)：原文件行 22；rag-22 / dev。来源摘录/记录：只根据 U2 简介，U2 于哪一年在哪座城市成立？ | gold=1976年在都柏林成立。
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:16>)：原文件行 16；rag-22 / dev / response。来源摘录/记录：SUCCEEDED | U2 于1976年在都柏林成立。[E1]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-22。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-22。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-24

题目：根据这张简介图片，Led Zeppelin 于哪一年在哪座城市成立？

标准答案：1968年在伦敦成立。

实际（SUCCEEDED）：Led Zeppelin（齐柏林飞船）于1968年在伦敦成立。[E1]

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：自编；文档性质：百科条目中文翻译改写的项目简介；doc_id=artist-led-zeppelin。

参考核验：自编题引用Led Zeppelin简介PNG。直接打开完整原PNG视觉阅读，公开背景首段清晰写1968年在伦敦成立；后文1969/1971是专辑年份。登记PNG哈希与manifest一致，派生HTML内容一致；gold年/城市正确。

实际核验：实际答1968年伦敦，与图片可视文字一致。E1索引文本和原PNG对应，已直接读图片而非仅相信OCR或辅助评分；原图片明确标它是带出处的项目改写，不应称维基百科原站截图。 section_path“图像 OCR”是处理标签，并非原图片正文标题；已另按原图公开背景首段定位，未把处理标签当成真实章节。

建议处理：保留答案；材料性质保留“项目中文改写简介的截图”说明。

人审确认：请从原PNG确认1968/伦敦，并确认不将派生截图标为原站页面。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/d2/led-zeppelin.png](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/led-zeppelin.png>)：图片上部 / 公开背景首段。来源摘录/记录：Led Zeppelin（齐柏林飞船）是英国摇滚乐队，1968年在伦敦成立。
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:24>)：原文件行 24；rag-24 / dev。来源摘录/记录：根据这张简介图片，Led Zeppelin 于哪一年在哪座城市成立？ | gold=1968年在伦敦成立。
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:17>)：原文件行 17；rag-24 / dev / response。来源摘录/记录：SUCCEEDED | Led Zeppelin（齐柏林飞船）于1968年在伦敦成立。[E1]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-24。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-24。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-25

题目：根据口径手册，曲目最受欢迎的默认口径是什么，对应哪个汇总表达式？

标准答案：默认按购买数量，使用 SUM(invoice_line.quantity)；销售额与歌单收录数是明确的备选口径。

实际（SUCCEEDED）：曲目最受欢迎的默认口径是沿用总计划的购买数量默认，即 SUM(invoice_line.quantity) [E1]。汇总表达式中，热门曲目（统计粒度为期间内曲目）的核心表达式为 SUM(invoice_line.quantity) [E2]。

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：自编；文档性质：项目自编口径/数据字典；doc_id=project-metric-manual。

参考核验：项目口径手册自编题。以python-docx读取原DOCX正文和表格完整顺序；四项指标/热门曲目段明确默认购买数量SUM(invoice_line.quantity)，销售额/歌单收录数是备选。gold主表达式和备选说明均有原文依据，无发票金额或全局默认混用。

实际核验：实际回答默认购买数量和SUM(invoice_line.quantity)，符合问句要求。E1覆盖热门曲目段，E2覆盖指标对应关系表，二者均由原DOCX核对。实际未逐述备选口径，但本题只问默认及表达式，不造成核心答复不全。

建议处理：保留gold与当前回答，最终人审以曲目对象和quantity表达式为准。

人审确认：请确认这是曲目购买数量默认，不套用于客户谁买得最多。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/d2/Chinook业务指标口径手册.docx](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/Chinook业务指标口径手册.docx>)：四项指标的定义与限制 / 热门曲目；指标对应关系表。来源摘录/记录：曲目最受欢迎沿用总计划的购买数量默认，即 SUM(invoice_line.quantity)。按销售额或按歌单收录数属于明确的备选口径，不能凭当前排名相同而互换。
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:25>)：原文件行 25；rag-25 / dev。来源摘录/记录：根据口径手册，曲目最受欢迎的默认口径是什么，对应哪个汇总表达式？ | gold=默认按购买数量，使用 SUM(invoice_line.quantity)；销售额与歌单收录数是明确的备选口径。
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:18>)：原文件行 18；rag-25 / dev / response。来源摘录/记录：SUCCEEDED | 曲目最受欢迎的默认口径是沿用总计划的购买数量默认，即 SUM(invoice_line.quantity) [E1]。汇总表达式中，热门曲目（统计粒度为期间内曲目）的核心表达式为 SUM(invoice_line.quantity) [E2]。
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-25。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-25。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-26

题目：按口径手册，客单价的主口径全名是什么，对应哪个 SQL 表达式？

标准答案：平均每张发票金额，AVG(invoice.total)。

实际（SUCCEEDED）：客单价的主口径全名为「平均每张发票金额」，对应 SQL 表达式为 AVG(invoice.total)，每张发票权重相同。[E1][E2]

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：自编；文档性质：项目自编口径/数据字典；doc_id=project-metric-manual。

参考核验：项目口径手册自编题。原DOCX平均每张发票金额段及表格定义客单价主口径全名为平均每张发票金额，AVG(invoice.total)，每张发票同权；下一段明确每位购买客户平均金额另命名。gold全名和SQL表达式准确。

实际核验：实际回答全名、AVG(invoice.total)及每张发票权重相同。E1为指标对应表，E2为主定义及客户平均金额区别，原DOCX均可定位，补述权重也有直接支持。

建议处理：保留答案，不改为每位购买客户平均金额；无记录NULL边界不在当前问句范围。

人审确认：请确认统计粒度为发票且使用invoice.total平均。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/d2/Chinook业务指标口径手册.docx](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/Chinook业务指标口径手册.docx>)：四项指标的定义与限制 / 平均每张发票金额；指标对应关系表。来源摘录/记录：本项目将客单价主口径写全为平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:26>)：原文件行 26；rag-26 / dev。来源摘录/记录：按口径手册，客单价的主口径全名是什么，对应哪个 SQL 表达式？ | gold=平均每张发票金额，AVG(invoice.total)。
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:19>)：原文件行 19；rag-26 / dev / response。来源摘录/记录：SUCCEEDED | 客单价的主口径全名为「平均每张发票金额」，对应 SQL 表达式为 AVG(invoice.total)，每张发票权重相同。[E1][E2]
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-26。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-26。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-27

题目：根据中文数据字典，customer.country 和 invoice.billing_country 分别表示什么？

标准答案：customer.country 是客户所在地国家；invoice.billing_country 是发票账单地址国家，两个业务含义应分别保留。

实际（SUCCEEDED）：customer.country 表示客户所在地国家 [E1][E8]；invoice.billing_country 表示发票账单地址国家 [E1][E2]。两者是不同字段，不可直接互换 [E2]。

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：自编；文档性质：项目自编口径/数据字典；doc_id=project-chinook-dictionary。

参考核验：项目中文数据字典自编题。直接读取完整原MD，地区字段含义段分别定义customer.country为客户所在地国家、invoice.billing_country为发票账单地址国家；两表字段说明重复确认。原文指出当前快照值相等不改变业务口径，gold两义正确。

实际核验：实际分别解释两字段并说明不可直接互换。E1为地区字段总说明，E8为customer.country字段行，E2为invoice.billing_country行，均按原MD相应小节定位并与索引一致。未以当前值相等推断语义相同。

建议处理：保留当前gold与回答；使用地区指标时须保持查询对象与字段口径对应。

人审确认：请确认所在地国家和账单地址国家的定义分别保留。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md>)：Chinook 数据字典 中文 / 地区字段含义；表与字段/customer、invoice。来源摘录/记录：customer.country 表示客户所在地国家。invoice.billing_country 表示发票账单地址国家。两列在当前快照中相等，不能据此将两种业务含义混为同一口径。
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:27>)：原文件行 27；rag-27 / dev。来源摘录/记录：根据中文数据字典，customer.country 和 invoice.billing_country 分别表示什么？ | gold=customer.country 是客户所在地国家；invoice.billing_country 是发票账单地址国家，两个业务含义应分别保留。
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:20>)：原文件行 20；rag-27 / dev / response。来源摘录/记录：SUCCEEDED | customer.country 表示客户所在地国家 [E1][E8]；invoice.billing_country 表示发票账单地址国家 [E1][E2]。两者是不同字段，不可直接互换 [E2]。
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-27。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-27。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

### rag:rag-28

题目：只依据这份 Iron Maiden 简介，列出该乐队2026年在中国每场演出的门票收入。

标准答案：当前指定简介不包含所问的逐场中国演出票务收入，证据不足，应明确说明不能据此回答。

实际（EMPTY_RESULT）：所选文档未提供足以直接支持此问题的证据，当前无法核实。

建议：参考=AI建议通过；实际=AI建议通过；正确性=AI建议通过；引用语义支持=AI建议通过；引用定位=AI建议通过。

题目来源：自编；文档性质：百科条目中文翻译改写的项目简介；doc_id=artist-iron-maiden。

参考核验：自编证据不足题。已读完整Iron Maiden HTML全部公开背景、资料处理说明、footer；仅有组建/作品/音乐背景，且明确不包含当代巡演收入，没有2026中国逐场演出、票数、单价或票务收入数据。gold answerable=false及EMPTY_RESULT正确；缺少正向gold_evidence并非漏证据，须以完整文档边界核验。

实际核验：实际EMPTY_RESULT且明确所选文档不足、当前无法核实，没有虚构演出或金额，也无伪造引用。没有actual evidences对正确拒答不构成错误；本审核依据完整HTML而非拿空引文证明缺失。

建议处理：保留证据不足gold及EMPTY_RESULT；不得通过常识或外部搜索补限定文档答案。

人审确认：请核实完整指定简介确无逐场票务收入，并最终确认拒答。

证据（完整原页与机械对应记录均可查）：

- [data/docs/raw/d2/iron-maiden.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/iron-maiden.html>)：Iron Maiden 铁娘子乐队公开简介 / 公开背景（完整文档检查）。来源摘录/记录：这里介绍的是公开音乐背景，不包含 Chinook 销售排名或当代巡演收入。
- [eval/datasets/rag_single.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/rag_single.jsonl:28>)：原文件行 28；rag-28 / dev。来源摘录/记录：只依据这份 Iron Maiden 简介，列出该乐队2026年在中国每场演出的门票收入。 | gold=当前指定简介不包含所问的逐场中国演出票务收入，证据不足，应明确说明不能据此回答。
- [eval/artifacts/d2/rag/final/responses.jsonl](<E:/中国电子杯-赛题八/system/eval/artifacts/d2/rag/final/responses.jsonl:21>)：原文件行 21；rag-28 / dev / response。来源摘录/记录：EMPTY_RESULT | 所选文档未提供足以直接支持此问题的证据，当前无法核实。
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)：rag:rag-28。来源摘录/记录：actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json>)：rag:rag-28。来源摘录/记录：索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。

证据完整性：True（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。

## 方法与限制

- 审核范围仅group=rag、split=dev。保留题不在内容审核范围。
- 物理页号统一为PDF从1起算，原OHR evidence_page_no从0起算；非PDF按章节或图片区域定位，未伪造PDF页号。
- 原题对应记录：[original-qa-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/original-qa-dev-audit.json>)。
- 引用机械对应记录：[citation-index-dev-audit.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json>)。
- 原文件哈希、完整原页文本及PNG记录：[source-verification.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/rag/source-verification.json>)。
- 所有建议等待最终人工审核；没有借用既有辅助judge结论，也没有回填任何人工状态。
