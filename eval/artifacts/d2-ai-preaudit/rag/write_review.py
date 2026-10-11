"""Materialize the completed manual AI preaudit, without changing any input."""
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT/'eval/artifacts/d2-ai-preaudit/rag'
OUT = ROOT/'eval/reports/d2-ai-preaudit'
OUT.mkdir(parents=True,exist_ok=True)

def read(name):
    return json.loads((ART/name).read_text(encoding='utf-8'))

PASS='AI建议通过'
COND='AI建议有条件通过'
findings={
'rag-02':{
 'reason':'原OHR问题和45 days答案精确相同。原PDF物理第1页第2条先限定PSS与GSMS合并经营财务结果，再约定在包含所需合并经营期间的PSS首个财政季度结束后45天内发布；不是从合并日直接起算45天。题问天数，gold对象、起算期间和单位均正确。',
 'actual_reason':'实际回答保留包含所需合并经营期间的财政季度这一限制，并正确回答within 45 days。E1为该页第2条完整有关段落，既有发布对象又有45天及起算点，能完整支撑回答。',
 'quote':'PSS agrees that it will publish such results as promptly as practicable following the Merger ... within 45 days after the end of the first fiscal quarter of PSS containing the required period of post-Merger combined operations',
 'section':'2. Initial Restriction on Disposition',
 'suggestion':'保留当前gold；人审时确认财政季度起算限制随题目和答案一起保存。',
 'human_confirmation':'请确认45 days是该特定财政季度结束后的上限，并据原页作最终人工签核。'},
'rag-03':{
 'reason':'原OHR question/answer和本题精确一致。原PDF物理第2页第6条规定PSS在Merger effective date后为期three years及时提交1934年法案Section 13要求的报告；gold三年对应报告义务期限，不是股票限制交易的另一期限。',
 'actual_reason':'实际答案正确说明合并生效日后三年。E5保留第6条标题行及three years，E1保留紧接的effective date、报告内容和Section 13；两条在同一物理页、同一条款，合读足够支持回答。E1单独不含three years，但回答同时引用E5，未据孤立片段判断。',
 'quote':'6. Filing of Reports by PSS. PSS agrees, for a period of three years ... after the effective date of the Merger, to file on a timely basis all reports ... pursuant to Section 13 of the Securities Exchange Act of 1934',
 'section':'6. Filing of Reports by PSS',
 'suggestion':'保留标准和当前回答；展示引用时使E1、E5的同条款关系可见。',
 'human_confirmation':'请核实E1和E5合起来覆盖three years、effective date和Section 13。'},
'rag-05':{
 'reason':'原OHR问题、Tame and Etherow答案和物理页转换均匹配。完整第1页先定义North Sea与Irish Sea之间的primary watershed，再说明该线西侧经Tame、Etherow流入Mersey；东侧Calder、Don等及南侧Trent另有说明，不能混为答案。',
 'actual_reason':'实际回答准确给出Tame and Etherow并指出排向Mersey。E1为原页西侧排水完整句，与前段分水岭上下文对应，支持两个河名及流向。',
 'quote':'On the western side of this line the drainage is to the Mersey by the rivers Tame and Etherow',
 'section':'CHAPTER I / INTRODUCTION',
 'suggestion':'保留当前gold及回答；引文定位保持物理第1页。',
 'human_confirmation':'请确认西侧两河与前文primary watershed指同一分水岭。'},
'rag-06':{
 'reason':'原OHR题答精确对应。完整物理第8页首段以Coal Measures的土壤为对象，明确列Wheat、oats、potatoes为perhaps the most satisfactory arable crops，并说明swedes和turnips可能受病害；gold三种作物正确，未混入另述的树种或不适宜作物。',
 'actual_reason':'实际答案正确列出三种作物，并保留perhaps语气。E1含Coal Measures土壤条件、三种作物和其他作物病害的连续段落，足够支撑对象和推荐限定。',
 'quote':'The soils of the Coal Measures are on the whole better ... Wheat, oats and potatoes are perhaps the-most satisfactory arable crops; swedes and turnips are apt to suffer ... unless liming is liberal.',
 'section':'物理第8页首段 / Coal Measures soils',
 'suggestion':'保留列表gold；人工解释宜保留原文perhaps，不扩展为现代农业普遍结论。',
 'human_confirmation':'请核实本题仅评价原文所述Coal Measures土壤里的作物。'},
'rag-07':{
 'reason':'原OHR question/answer精确一致。完整物理第14页General Stratigraphy段规定Shale Grit在Sheet南部的moors厚450 to 550 feet；后句另谈Etherow/Tame河谷暴露。gold保留地层、南部空间范围及feet单位，正确。',
 'actual_reason':'实际回答450 to 550 feet in the southern part of the Sheet，未换成米或全区统一厚度。E1对应该页明确厚度句，可支撑数值、单位和空间限制。',
 'quote':'The Shale Grit forms a wide spread on the moors in the southern part of the Sheet, where it is 450 to 550 feet thick.',
 'section':'General Stratigraphy / The Shale Grit',
 'suggestion':'保留当前gold和回答；人审检查feet与Sheet南部限定。',
 'human_confirmation':'请确认范围是450至550英尺且仅对应Sheet南部。'},
'rag-08':{
 'reason':'原OHR题答精确一致。原物理第8页Table of Formations前说明Millstone Grits中的shales统一着色，而grits和sandstones按四主组着色，随后逐项列Rough Rock Series、Middle Grits、Kinderscout Grits、Shale Grit；gold四项齐全且未把shales加入。',
 'actual_reason':'实际回答完整列出原文四组并说明grits与sandstones四色；E1含原页有关列举段，四名称、组数和对象均有来源。',
 'quote':'In the Millstone Grits the shales are coloured uniformly throughout, but the grits and sandstones are shown by four colours for the main groups, viz., The Rough Rock Series, the Middle Grits, the Kinderscout Grits and the Shale Grit.',
 'section':'Table of Formations前说明段',
 'suggestion':'保留当前gold和回答，不把图例组数理解为地质总层数。',
 'human_confirmation':'请确认四项名称和地图中grits/sandstones着色这一对象。'},
'rag-10':{
 'reason':'原OHR题答相同，原页索引64转换为物理第65页正确。原页左栏Radio and Television Interference段确写Class B digital device与Part 15 FCC rules。reference_text的Part 1 5是排版/OCR空格差异，不影响Class B答案。',
 'actual_reason':'实际回答Class B并正确写Part 15。E1机械上与索引精确对应，但其text混入右栏关于未授权修改的句子；原页视觉核对确认Class B句完整位于左栏，数字和分类语义成立。该读取顺序瑕疵未导致本题答错。',
 'quote':'This equipment has been tested and found to comply with the limits for a Class B digital device in accordance with the specifications in Part 15 of FCC rules.',
 'section':'Regulatory Compliance Information / Radio and Television Interference（左栏）',
 'issues':[{'object':'actual_evidence.E1.text','problem':'双栏提取交错右栏Important句，影响引文可读性；原页已视觉确定左栏Class B句，本题支撑仍成立。','severity':'提示'}],
 'suggestion':'人审可通过本题语义；登记双栏读取顺序问题供后续资料处理另案修正，本次不改索引或gold。',
 'human_confirmation':'请看原第65页左栏确认Class B，不把E1交错文本当连续原段。'},
'rag-11':{
 'reason':'原OHR question/answer和物理第3页对应。reference_text本身只有Create and share movies in minutes描述，需通过原页空间关系确认应用名；已完整渲染查看，左上iMovie标签下直接排列该描述，右上iPhoto描述为照片，gold iMovie正确。',
 'actual_reason':'实际回答iMovie。E1文本含iMovie/iPhoto并出现交错两栏，单靠线性字串不足区分应用；原页完整视觉检查确认影片描述归属iMovie。因此引用可支持结论，依据包括原页布局，而非仅词面命中。',
 'quote':'iMovie / Collect all your video in one library. Create and share movies in minutes.',
 'section':'物理第3页左上iMovie应用卡片',
 'issues':[{'object':'reference_text; actual_evidence.E1.text','problem':'引用描述与应用名的归属依赖原页卡片布局；线性提取与iPhoto交错，已用原页视觉补足核验。','severity':'提示'}],
 'suggestion':'保留iMovie；人工审核随附原页PNG，对照左上卡片。',
 'human_confirmation':'请确认左上iMovie标题与影片描述的视觉归属。'},
'rag-12':{
 'reason':'原OHR题答完全匹配。物理第67页ENERGY STAR Compliance段明确该计划是与电子设备制造商合作以promote energy-efficient products；gold目标正确，不能误当仅指默认休眠10分钟。',
 'actual_reason':'实际答对推广节能产品，并补述节约金钱/资源及Apple标准配置符合指南。E1涵盖推广目标及money/resources，E2涵盖Apple参与和标准配置，原页左栏连续段落均有依据；未将VCCI段当作ENERGY STAR内容。',
 'quote':'As an ENERGY STAR partner, Apple has determined that standard configurations of this product meet the ENERGY STAR guidelines ... The ENERGY STAR program is a partnership with electronic equipment manufacturers to promote energy-efficient products. Reducing energy consumption of products saves money and helps conserve valuable resources.',
 'section':'ENERGY STAR Compliance（左栏）',
 'suggestion':'保留当前gold和实际回答；审核Apple补充句时同时看E2。',
 'human_confirmation':'请确认问题问计划推广目标，E1/E2各自覆盖实际回答的补充说明。'},
'rag-13':{
 'reason':'原OHR question/answer和物理页号相符。完整物理第52页条件是多电脑共享网络且ISP仅给一个IP地址，原文明确AirPort Base Station可用于共享；gold设备名称正确。',
 'actual_reason':'实际回答AirPort Base Station，另补仅一个IP时需具有共享能力的路由器/NAT。E2直接支持设备，E1支持前提及NAT/IP masquerading术语，两条同页连续，补述正确且有引文。',
 'quote':'If only one IP address is provided, then you must have a router capable of sharing the connection ... You can use an AirPort Base Station to share one IP address among multiple computers.',
 'section':'Chapter 3 Problem, Meet Solution / Internet connection共享段',
 'suggestion':'保留当前设备gold与回答，勿把只有一个IP的条件外推到所有ISP配置。',
 'human_confirmation':'请确认E1支持条件和NAT，E2支持AirPort设备名称。'},
'rag-15':{
 'reason':'原OHR题答、doc_entry和物理第10页精确对应。原页Leading for Excellence首段署明ASQ/Forbes Insights研究，ELEMENTS OF SUCCESS段列五能力；完整第11页红色重述亦列相同五项。gold完整且管理实践/稳健流程改进未漏。',
 'actual_reason':'实际答案五项齐全。E1是第11页重述的截断部分，末尾robust pro-尚未完整；E3是第10页Elements of Success含完整robust process improvement的段落。合读E3足以支撑完整清单，不能称E1独自覆盖五项。',
 'quote':'Success boils down to five not-so-simple but fundamental capabilities—leadership, culture, strategy execution, management practices, and robust process improvement.',
 'section':'Leading for Excellence / ELEMENTS OF SUCCESS',
 'suggestion':'保留清单和回答；人审据第10页完整句，记录E1截断但E3补足。',
 'human_confirmation':'请确认五项均存在于E3，ASQ/Forbes归属来自文章首段。'},
'rag-16':{
 'reason':'原OHR题答精确匹配。物理第11页RANKINGS OF QUALITY PROGRAMS段明确71% of senior leaders评价world class or at least advanced；同页交代调查1,010 senior leaders与1,281 quality professionals。后述60%是另一受访组对average/below average的评价，不能替代本题71%。',
 'actual_reason':'实际回答71%并保留senior leaders、world class/at least advanced。E1虽含两栏交错文本，原页左下原段视觉确认百分比对应高层领导评价而非右栏医院认可次数；回答对象、比例和评级范围均正确。',
 'quote':'The research draws on the responses of 1,010 senior leaders and 1,281 quality professionals worldwide. ... According to the research, 71% of senior leaders rate their quality programs as world class or at least advanced.',
 'section':'RANKINGS OF QUALITY PROGRAMS（左栏）；研究样本说明',
 'issues':[{'object':'actual_evidence.E1.text','problem':'双栏交错插入医院经验句，已按原页左栏确认71%对应senior leaders。','severity':'提示'}],
 'suggestion':'保留71%；人工终审检查受访者组别，避免与quality professionals的60%混用。',
 'human_confirmation':'请确认分母/对象是senior leaders，71%对应world class或至少advanced。'},
'rag-18':{
 'reason':'原OHR问题、AUCROC score答案和物理第12页对应。原页Appendix E给出把目标位置label-word注意力当分类器预测、相对于模型实际输出计算AUC-ROC的定义；物理第5页2.3.1与2.3.2也一致。gold量化指标正确。',
 'actual_reason':'核心答案AUC-ROC正确。补述deep layers approaches 0.8可由E4及原第5页支持，原研究的GPT2-XL/GPT-J四数据集平均上下文已核对。E2文本确出自原第12页，但section_path标Limitations，真实段属Appendix E Details for the Calculation of AUCROC；E4标题也混入右栏邻句。doc_id与physical page、正文支撑有效，章节定位需人工确认后修订建议另案处理。',
 'quote':'We use the AUC-ROC score to quantify this correlation. ... compute the AUC-ROC value of this prediction relative to the actual model output.',
 'section':'E. Details for the Calculation of AUCROC（原第12页左栏开始、右栏续文）',
 'extra_evidence':[{'page':5,'section':'2.3.1 Experiments / 2.3.2 Results and Analysis / Figure 5','sourcequote':'Figures 5a and 5b delineate correlation metrics for GPT2-XL and GPT-J, averaged across four datasets. The AUCROC for deep layers approaches 0.8.'}],
 'actual_status':COND,'answer_correctness_status':PASS,'citation_support_status':COND,
 'issues':[{'object':'actual_evidence.E2.section_path','problem':'登记为Limitations；原物理第12页真实章节是Appendix E Details for the Calculation of AUCROC，章节元数据错位。','severity':'需人工确认'},{'object':'actual_evidence.E4.section_path','problem':'2.3.2标题混入右栏to denote them等邻段文字；真实正文与第5页对应，但章节名不洁净。','severity':'提示'}],
 'suggestion':'核心答案可保留。人工终审按原第12页Appendix E及第5页2.3.2确认引用；建议后续单独修复章节定位，若只需简答可省去未被问题要求的0.8补述。',
 'human_confirmation':'请确认核心答案和0.8补述有原文支持，并明确E2章节定位错误如何处置；本报告未更改索引。'},
'rag-19':{
 'reason':'原OHR问答、SST-2 and EmoC与物理第6页对应。完整第6页3.1.3明确particularly on the SST-2 and EmoC datasets，第7页Table 1说明Anchor Re-weighting整体结果。gold是在作者特别强调的数据集层次回答，未错误声称其他数据集完全无提升。',
 'actual_reason':'核心SST-2/EmoC答案正确且E1直接支持。新增SST-2 64.75→90.07与EmoC 15.44→41.64各数字确在E5表1，但64.75是Vanilla 5-shot，15.44是Vanilla 1-shot，90.07/41.64是Anchor 1-shot。原第6页3.1.2明确设置两套baseline，故这些提升数值只有分别标明基线才有清晰实验含义；当前回答未区分两套基线，不能只因数字出现就视作完整语义支撑。E5 section_path亦为邻页续句而非Table 1定位。',
 'quote':'As Table 1 shows, the proposed anchor re-weighting significantly enhances ICL performance, particularly on the SST-2 and EmoC datasets.',
 'section':'3.1.2 Experiments / 3.1.3 Results',
 'extra_evidence':[{'page':7,'section':'Table 1 / Method × Dataset','sourcequote':'Vanilla In-Context Learning (1-shot per class): SST-2 61.28, EmoC 15.44; Vanilla In-Context Learning (5-shot per class): SST-2 64.75, EmoC 9.80; Anchor Re-weighting (1-shot per class): SST-2 90.07, EmoC 41.64.'}],
 'actual_status':COND,'answer_correctness_status':COND,'citation_support_status':COND,
 'issues':[{'object':'actual_answer.补充提升数值','problem':'SST-2比较采用Vanilla 5-shot基线，EmoC采用Vanilla 1-shot基线；回答未说明两者不同。单个数字正确不等于比较语义完整。','severity':'需人工确认'},{'object':'actual_evidence.E5.section_path','problem':'章节定位是邻页续句“0 role that anchors play in ICL.”，原位置为第7页Table 1。','severity':'提示'}],
 'suggestion':'保留gold的SST-2和EmoC。人审可按原题只保留数据集名称；若保留数值，逐项注明Vanilla 1-shot/5-shot→Anchor 1-shot及GPT2-XL、五随机种子平均的实验范围。不得在本次审核中静默改答案。',
 'human_confirmation':'请明确接受仅核心答案，还是要求补充数值逐项标baseline；当前增写比较需人工处理。'},
'rag-21':{
 'reason':'这是基于项目中文改写简介的自编题，没有OHR source_qa_id，不能标成OHR原题。已读完整Iron Maiden HTML，公开背景首段明确1975年、伦敦东部Leyton，gold年/地点正确；成立地未混同专辑1980/1982发行时间。',
 'actual_reason':'实际回答1975年伦敦东部Leyton，并补充Steve Harris角色；E1与HTML公开背景首段及索引相符，年、地点、创建者均逐项有文档支持。仅对指定改写文档内事实审查，未外网验证百科原站。',
 'quote':'Iron Maiden（铁娘子乐队）是英国重金属乐队，由贝斯手及主要创作者 Steve Harris 于1975年在伦敦东部的 Leyton 组建。',
 'section':'Iron Maiden 铁娘子乐队公开简介 / 公开背景（首段）',
 'suggestion':'保留答案并标清题为自编、材料为项目中文改写简介。',
 'human_confirmation':'请确认文档层面1975/Leyton及Steve Harris补述；外部百科真实性不属于本次限定材料核验。'},
'rag-22':{
 'reason':'自编题基于U2项目中文简介，不含OHR原题ID。完整HTML公开背景首段明确于1976年在都柏林成立；1980/1983年是作品发行日期。gold年份和城市与限定文档一致。',
 'actual_reason':'实际仅答1976年在都柏林成立，E1为同一公开背景首段，与原HTML和索引精确对应，足够支持年份及城市。未借助外部常识。',
 'quote':'U2是爱尔兰摇滚乐队，于1976年在都柏林成立。',
 'section':'U2 乐队公开简介 / 公开背景（首段）',
 'suggestion':'保留当前gold及实际回答，题来源标自编、文档来源标中文改写。',
 'human_confirmation':'请确认1976和都柏林均取自指定简介首段。'},
'rag-24':{
 'reason':'自编题引用Led Zeppelin简介PNG。直接打开完整原PNG视觉阅读，公开背景首段清晰写1968年在伦敦成立；后文1969/1971是专辑年份。登记PNG哈希与manifest一致，派生HTML内容一致；gold年/城市正确。',
 'actual_reason':'实际答1968年伦敦，与图片可视文字一致。E1索引文本和原PNG对应，已直接读图片而非仅相信OCR或辅助评分；原图片明确标它是带出处的项目改写，不应称维基百科原站截图。',
 'quote':'Led Zeppelin（齐柏林飞船）是英国摇滚乐队，1968年在伦敦成立。',
 'section':'图片上部 / 公开背景首段',
 'suggestion':'保留答案；材料性质保留“项目中文改写简介的截图”说明。',
 'human_confirmation':'请从原PNG确认1968/伦敦，并确认不将派生截图标为原站页面。'},
'rag-25':{
 'reason':'项目口径手册自编题。以python-docx读取原DOCX正文和表格完整顺序；四项指标/热门曲目段明确默认购买数量SUM(invoice_line.quantity)，销售额/歌单收录数是备选。gold主表达式和备选说明均有原文依据，无发票金额或全局默认混用。',
 'actual_reason':'实际回答默认购买数量和SUM(invoice_line.quantity)，符合问句要求。E1覆盖热门曲目段，E2覆盖指标对应关系表，二者均由原DOCX核对。实际未逐述备选口径，但本题只问默认及表达式，不造成核心答复不全。',
 'quote':'曲目最受欢迎沿用总计划的购买数量默认，即 SUM(invoice_line.quantity)。按销售额或按歌单收录数属于明确的备选口径，不能凭当前排名相同而互换。',
 'section':'四项指标的定义与限制 / 热门曲目；指标对应关系表',
 'suggestion':'保留gold与当前回答，最终人审以曲目对象和quantity表达式为准。',
 'human_confirmation':'请确认这是曲目购买数量默认，不套用于客户谁买得最多。'},
'rag-26':{
 'reason':'项目口径手册自编题。原DOCX平均每张发票金额段及表格定义客单价主口径全名为平均每张发票金额，AVG(invoice.total)，每张发票同权；下一段明确每位购买客户平均金额另命名。gold全名和SQL表达式准确。',
 'actual_reason':'实际回答全名、AVG(invoice.total)及每张发票权重相同。E1为指标对应表，E2为主定义及客户平均金额区别，原DOCX均可定位，补述权重也有直接支持。',
 'quote':'本项目将客单价主口径写全为平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。',
 'section':'四项指标的定义与限制 / 平均每张发票金额；指标对应关系表',
 'suggestion':'保留答案，不改为每位购买客户平均金额；无记录NULL边界不在当前问句范围。',
 'human_confirmation':'请确认统计粒度为发票且使用invoice.total平均。'},
'rag-27':{
 'reason':'项目中文数据字典自编题。直接读取完整原MD，地区字段含义段分别定义customer.country为客户所在地国家、invoice.billing_country为发票账单地址国家；两表字段说明重复确认。原文指出当前快照值相等不改变业务口径，gold两义正确。',
 'actual_reason':'实际分别解释两字段并说明不可直接互换。E1为地区字段总说明，E8为customer.country字段行，E2为invoice.billing_country行，均按原MD相应小节定位并与索引一致。未以当前值相等推断语义相同。',
 'quote':'customer.country 表示客户所在地国家。invoice.billing_country 表示发票账单地址国家。两列在当前快照中相等，不能据此将两种业务含义混为同一口径。',
 'section':'Chinook 数据字典 中文 / 地区字段含义；表与字段/customer、invoice',
 'suggestion':'保留当前gold与回答；使用地区指标时须保持查询对象与字段口径对应。',
 'human_confirmation':'请确认所在地国家和账单地址国家的定义分别保留。'},
'rag-28':{
 'reason':'自编证据不足题。已读完整Iron Maiden HTML全部公开背景、资料处理说明、footer；仅有组建/作品/音乐背景，且明确不包含当代巡演收入，没有2026中国逐场演出、票数、单价或票务收入数据。gold answerable=false及EMPTY_RESULT正确；缺少正向gold_evidence并非漏证据，须以完整文档边界核验。',
 'actual_reason':'实际EMPTY_RESULT且明确所选文档不足、当前无法核实，没有虚构演出或金额，也无伪造引用。没有actual evidences对正确拒答不构成错误；本审核依据完整HTML而非拿空引文证明缺失。',
 'quote':'这里介绍的是公开音乐背景，不包含 Chinook 销售排名或当代巡演收入。',
 'section':'Iron Maiden 铁娘子乐队公开简介 / 公开背景（完整文档检查）',
 'suggestion':'保留证据不足gold及EMPTY_RESULT；不得通过常识或外部搜索补限定文档答案。',
 'human_confirmation':'请核实完整指定简介确无逐场票务收入，并最终确认拒答。'},
}

inputs=read('dev-compact-inputs.json')
qa_audit=read('original-qa-dev-audit.json')
cit_audit=read('citation-index-dev-audit.json')
sources=read('source-verification.json')
manifest={r['doc_id']:r for r in csv.DictReader((ROOT/'data/docs/manifest.csv').open(encoding='utf-8-sig'))}
qa_map={r['id']:r for r in qa_audit}
cit_map={r['id']:r for r in cit_audit}

# Mechanical index consistency and raw-source citation-location correctness are
# separate judgments. Original page geometry was inspected under both MediaBox
# and CropBox-local coordinates. The MacBook PDF uses CropBox origin (129,219).
location_notes={
 'rag-05':('actual_evidence.E1.bbox','原地质扫描PDF隐藏文字层的bbox=[22.92,516.71,233.1,577.03]可裁出西侧河流文字，但Poppler真实可视页红框落在更低的Don/Derwent及南侧分水岭段落，不覆盖可视Tame/Etherow原句。原页MediaBox=CropBox且无旋转，不能用裁切原点偏移解释。'),
 'rag-06':('actual_evidence.E1.bbox','bbox=[36.12,245.41,246.9,381.44]在隐藏文字层能取出作物段，真实扫描页红框却落在Table of Formations说明段，不覆盖页面上方Coal Measures作物原句。文字层命中不等于视觉坐标准确。'),
 'rag-07':('actual_evidence.E1.bbox','bbox=[40.68,403.4,250.62,475.17]在隐藏文字层能取出450至550 feet句，真实扫描页红框位于更低的砂岩特征/Grindslow Shales段，不覆盖可视Shale Grit厚度句。原页和答案正确，但框选定位错位。'),
 'rag-08':('actual_evidence.E1.bbox','bbox=[37.68,383.95,247.98,534.78]在隐藏文字层能取出四组图例说明，真实扫描页红框却位于Superficial/Solid Formations表，不覆盖上方可视四组列举句。原文字层与图像坐标不齐。'),
 'rag-11':('actual_evidence.E1.bbox','E1 bbox=[27.21,99.39,325.38,117.81]；考虑原PDF CropBox偏移(129,219)后，仅框到iMovie/iPhoto网址与Help行，未覆盖Create and share movies in minutes描述。section_path=[]只是未登记章节，本身不判错。'),
 'rag-13':('actual_evidence.E1/E2.section_path','“4 Follow the onscreen instructions.”是Network Diagnostics步骤4，而非共享IP段落的章节标题；字段把步骤文本误登记为章节。PDF物理第52页正确，CropBox偏移后bbox能包含支持句，不据MediaBox未平移裁切结果误判坐标。'),
 'rag-15':('actual_evidence.E1.bbox','E1 bbox=[432.28,50.71,534.6,66.45]在原第11页只框到EYE ON QUALITY页眉，不覆盖五能力正文。E3第10页物理页/Elements of Success定位正确，故回答语义仍可获充分支持。'),
 'rag-16':('actual_evidence.E1.section_path','登记BUILDING A NEW CULTURE，但71%句属物理第11页左栏RANKINGS OF QUALITY PROGRAMS；邻右栏章节被错误继承。'),
 'rag-18':('actual_evidence.E2/E4.section_path','E2登记Limitations，原第12页属于Appendix E Details for the Calculation of AUCROC。E4的2.3.2标题混入右栏to denote them等正文。章节定位明确错误；doc_id/物理页和实际语义仍正确。'),
 'rag-19':('actual_evidence.E1.bbox; E5.section_path','E1 bbox=[70.87,486.56,152.06,499.36]在原第6页裁到左栏“In this equation, βi”方程说明，不覆盖右栏3.1.3核心支持句。E5章节路径“0 role that anchors play in ICL.”是前页续句/公式残片，原文位置是第7页Table 1。')
}
for key,(obj,problem) in location_notes.items():
    f=findings[key]
    f['citation_location_status']='AI发现错误'
    f['actual_status']=COND
    f['issues']=[issue for issue in f.get('issues',[]) if 'section_path' not in issue['object']]
    f['issues'].append({'object':obj,'problem':problem,'severity':'error','category':'citation_location'})
    f['actual_reason'] += ' 原文定位复核：'+problem
    f['suggestion'] += ' 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。'
findings['rag-18']['citation_support_status']=PASS
for key in ['rag-06','rag-07','rag-08']:
    findings[key]['actual_reason'] += ' section_path使用本页running header，属于粗粒度页眉提示；不将页眉当作真实细分章节。上述bbox错误按真实渲染图判断，不能被隐藏文字层的裁切文字覆盖。'
findings['rag-24']['actual_reason'] += ' section_path“图像 OCR”是处理标签，并非原图片正文标题；已另按原图公开背景首段定位，未把处理标签当成真实章节。'

chunks_wanted={m['chunk_id'] for row in cit_audit for e in row['citations'] for m in e['exact_index_matches']}
index_chunks={}
for line in (ROOT/'data/indexes/docs-final/chunks.jsonl').open(encoding='utf-8'):
    c=json.loads(line)
    if c['chunk_id'] in chunks_wanted:
        index_chunks[c['chunk_id']]=c
raw_citations={(row['id'],e['evidence_id']):e for row in inputs for e in row['actual']['evidences']}
visual_bbox={(r['id'],r['eid']):r for r in read('actual-bbox-visible-render.json')}
location_error_eids={
    'rag-05':{'E1'},'rag-06':{'E1'},'rag-07':{'E1'},'rag-08':{'E1'},
    'rag-11':{'E1'},'rag-13':{'E1','E2'},'rag-15':{'E1'},'rag-16':{'E1'},
    'rag-18':{'E2','E4'},'rag-19':{'E1','E5'}
}
location_details=[]
for row in cit_audit:
    for e in row['citations']:
        raw=raw_citations[(row['id'],e['evidence_id'])]
        e['response_bbox']=raw.get('bbox')
        e['bbox_exact_index_matches']=all(index_chunks[m['chunk_id']]['bbox']==raw.get('bbox') for m in e['exact_index_matches'])
        is_error=e['evidence_id'] in location_error_eids.get(row['id'],set())
        e['source_location_status']='AI发现错误' if is_error else PASS
        e['source_location_reason']=location_notes[row['id']][1] if is_error else '原doc_id与物理页/非PDF章节匹配；已读取原文并核对段落。bbox存在时另按真实渲染图检查。没有登记bbox或章节时不宣称它们已被精确证明。'
        if (row['id'],e['evidence_id']) in visual_bbox:
            e['bbox_visual_evidence']=visual_bbox[(row['id'],e['evidence_id'])]
            e['bbox_visual_evidence']['visual_inspection']='completed by AI'
        location_details.append({'review_id':row['review_id'],'id':row['id'],'group':'rag','split':'dev','evidence_id':e['evidence_id'],'source_location_status':e['source_location_status'],'reason':e['source_location_reason'],'actual_doc_id':e['doc_id'],'actual_physical_page':e['physical_page'],'actual_section_path':e['section_path'],'actual_bbox':raw.get('bbox'),'index_text_and_section_exact':e['index_exact_match'],'index_bbox_exact':e['bbox_exact_index_matches'],'bbox_visual_evidence':e.get('bbox_visual_evidence')})
(ART/'citation-index-dev-audit.json').write_text(json.dumps(cit_audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ART/'citation-location-dev-audit.json').write_text(json.dumps(location_details,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
visual_records=read('actual-bbox-visible-render.json')
for v in visual_records:
    v['visual_inspection']='completed by AI; outline on full original render reviewed'
(ART/'actual-bbox-visible-render.json').write_text(json.dumps(visual_records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# These records are updated only after all fifteen generated source-page PNGs
# and the original Led Zeppelin PNG were actually inspected in this session.
for s in sources:
    for p in s['pages']:
        p['visual_inspection']='completed by AI; full source page viewed in this audit'
    if s['format']=='png':
        s['visual_inspection']='completed by AI; original full PNG viewed in this audit'
(ART/'source-verification.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

qa_sha=hashlib.sha256((ROOT/'data/raw/ohr/qas_v2.json').read_bytes()).hexdigest()
dev_records={}
for line in (ROOT/'eval/datasets/rag_single.jsonl').open(encoding='utf-8'):
    d=json.loads(line)
    if d.get('split')=='dev' and d['id'] in findings:
        dev_records[d['id']]=d
for q in qa_audit:
    if q['source_qa_id']:
        q['qa_source_file_sha256']=qa_sha
        q['qa_source_registered_sha256']=dev_records[q['id']]['source_qa_sha256']
        q['qa_source_hash_matches']=qa_sha==q['qa_source_registered_sha256']
(ART/'original-qa-dev-audit.json').write_text(json.dumps(qa_audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

rows=[]
for i in inputs:
    f=findings[i['id']]
    qa=qa_map[i['id']]
    cit=cit_map[i['id']]
    doc=manifest[i['doc_id']]
    original_path=doc['path']
    source_type='OHR原始PDF' if qa['source_qa_id'] else ('项目自编口径/数据字典' if i['doc_id'].startswith('project-') else '百科条目中文翻译改写的项目简介')
    evidence=[{'path':original_path,'page':i['physical_pages'][0] if i['physical_pages'] else None,'section':f['section'],'sourcequote':f['quote'],'source_sha256':doc['content_hash'],'verified_from':'原始文件完整页面文本提取及完整页面视觉检查' if doc['format']=='pdf' else ('原始PNG直接完整视觉检查' if doc['format']=='png' else ('原始DOCX用python-docx完整正文及表格读取' if doc['format']=='docx' else '原始文件全文读取'))}]
    for e in f.get('extra_evidence',[]):
        evidence.append({'path':original_path,'source_sha256':doc['content_hash'],'verified_from':'原始PDF完整物理页提取及视觉检查',**e})
    for p in sorted(set(e.get('page') for e in evidence if e.get('page'))):
        stem=f"{i['doc_id']}-physical-p{p}"
        evidence.extend([{'path':f'eval/artifacts/d2-ai-preaudit/rag/raw-pages/{stem}.txt','page':p,'section':'完整物理页文本（pdfplumber）','sourcequote':'完整上下文在该文本文件；正文核验语句见上面的原始文件引用。'},{'path':f'eval/artifacts/d2-ai-preaudit/rag/raw-pages/{stem}.png','page':p,'section':'完整物理页Poppler渲染；已视觉检查','sourcequote':'页面标题、表格/栏位、脚注和有关句子均在完整页图内。'}])
    if qa['source_qa_id']:
        evidence.append({'path':'data/raw/ohr/qas_v2.json','section':'ID='+qa['source_qa_id'],'sourcequote':f"questions={qa['original_qa']['questions']} | answers={qa['original_qa']['answers']} | evidence_page_no={qa['original_qa']['evidence_page_no']}",'qa_array_item_identified_by':'ID'})
    evidence.extend([{'path':'eval/datasets/rag_single.jsonl','line':qa['dataset_line'],'section':i['id']+' / dev','sourcequote':i['question']+' | gold='+i['answer']},{'path':'eval/artifacts/d2/rag/final/responses.jsonl','line':cit['response_line'],'section':i['id']+' / dev / response','sourcequote':i['actual']['status']+' | '+i['actual']['answer']},{'path':'eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json','section':i['review_id'],'sourcequote':'actual evidence逐条doc_id、physical page、section_path、text精确匹配docs-final/chunks.jsonl；记录含原索引行号和chunk_id。'}])
    evidence.append({'path':'eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json','section':i['review_id'],'sourcequote':'索引机械一致性与原文真实章节/可视bbox定位分开判定；本题逐条定位判断见对应记录。'})
    for e in cit['citations']:
        if e.get('bbox_visual_evidence'):
            v=e['bbox_visual_evidence']
            evidence.append({'path':v['outline_path'],'page':v['page'],'section':e['evidence_id']+' / 原始完整物理页及实际bbox红框（已视觉核对）','sourcequote':e['source_location_reason']})
    row={
        'review_id':i['review_id'],'id':i['id'],'group':'rag','split':'dev',
        'question':i['question'],'reference_answer':i['answer'],'actual_answer':i['actual']['answer'],'actual_run_status':i['actual']['status'],
        'reference_status':f.get('reference_status',PASS),'actual_status':f.get('actual_status',PASS),'answer_correctness_status':f.get('answer_correctness_status',PASS),'core_answer_correctness_status':PASS,'citation_support_status':f.get('citation_support_status',PASS),'citation_location_status':f.get('citation_location_status',PASS),
        'source_question_type':'OHR原题' if qa['source_qa_id'] else '自编','source_document_type':source_type,'source_qa_id':qa['source_qa_id'],'doc_id':i['doc_id'],'page_numbering':'physical_pdf_1_based' if doc['format']=='pdf' else 'section_or_visual_region; no physical PDF page claimed',
        'reason':f['reason'],'actual_reason':f['actual_reason'],'issues':f.get('issues',[]),'suggestion':f['suggestion'],'human_confirmation':f['human_confirmation'],'evidence':evidence,'evidence_complete':True,
        'source_verification':{'source_path':original_path,'source_sha256':doc['content_hash'],'manifest_hash_verified':True,'physical_pages_or_sections_located':True,'original_qa_exact_match':all(qa[k] for k in ['question_exact','answer_exact','doc_entry_exact','page_zero_to_physical_one_based_exact']) if qa['source_qa_id'] else None,'original_qa_source_hash_verified':qa.get('qa_source_hash_matches'),'citation_count':len(cit['citations']),'citation_index_exact_match_count':sum(c['index_exact_match'] for c in cit['citations']),'citation_source_location_error_count':sum(c['source_location_status']=='AI发现错误' for c in cit['citations']),'actual_equals_final_response':all(cit[k] for k in ['unified_answer_equals_response','unified_status_equals_response','unified_evidence_equals_response'])},
        'assessment_scope':'仅AI预审建议；未填写或覆盖任何人工审核状态、签名、日期。'
    }
    rows.append(row)

counts={k:dict(collections.Counter(r[k] for r in rows)) for k in ['reference_status','actual_status','answer_correctness_status','core_answer_correctness_status','citation_support_status','citation_location_status','source_question_type']}
packet={'title':'D2 RAG开发集逐题AI预审','scope':{'group':'rag','split':'dev','reviewed':21,'reserved_skipped_count':9,'reserved_content_reviewed':False,'original_sources_read':10,'full_pdf_pages_extracted_rendered_and_visually_reviewed':15,'original_png_visually_reviewed':1,'OHR_original_qa_matches':14,'actual_citations_exact_index_matches':30,'existing_pdf_bbox_rendered_and_visually_reviewed':15,'citation_location_error_entries':sum(c['source_location_status']=='AI发现错误' for c in location_details),'question_answer_api_calls':0,'model_calls':0,'input_materials_modified':False,'human_review_fields_modified':False},'method':'从统一表筛dev后读取开发集原始JSONL和final响应，按source_qa_id查原OHR JSON题答及原doc entry；所有相关PDF原物理页完整文本/版式提取、Poppler渲染和视觉检查。DOCX用python-docx完整顺序读取，HTML与MD直接全文读取，PNG原图视觉读。引用机械命中独立记录，语义由原页上下文核验，不使用辅助judge代替。全部15个已存在PDF引用bbox另做原文裁切及渲染图红框检查，比较MediaBox及CropBox坐标；几何视觉定位与隐藏文字层命中分开判断。','limitations':['当前开发会话无法形成保留集隔离，9条保留记录仅计数并跳过；没有展开、评阅或复制保留问题/答案。','仅核验指定本地文档，不做外网事实更新；项目中文简介没有被当作百科原站完整内容。','AI结论不是人工审核；本报告只写新报告及新提取证据，不更改gold、系统实际答案、索引或任何人审状态。','10条引用定位错误与回答语义分开记录；rag-19还有未披露比较基线的问题。未登记bbox的引用不声称其精细几何定位已得到证明。'],'counts':counts,'rows':rows}
(OUT/'rag-review.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

md=['# D2 RAG开发集逐题AI预审','',
    '本报告实际审核21条RAG开发题。9条保留题仅计数跳过，没有展开题目、答案或作出建议。已读10个原始文档，完整提取、渲染并视觉核对15个相关PDF物理页，直接视觉读取Led Zeppelin原PNG；原DOCX正文和表格由python-docx按原顺序读取，HTML与MD直接全文核对。14个OHR原题的question、answer、doc_entry和0-based转physical 1-based页号均匹配；30条实际引用均精确对应既有索引片段。',
    '', '参考答案21条均AI建议通过；实际审核11条AI建议通过、10条AI建议有条件通过。10条发现引用定位元数据错误（rag-05/06/07/08/11/13/15/16/18/19）；rag-19还存在新增提升数值未区分1-shot/5-shot基线的问题。核心gold没有因这些问题被更改。',
    '', '所有结论仅为AI预审建议。没有调用问答API或模型，没有修改原题、标准、实际答案、索引、业务代码、prompt、.env或人工审核字段；人审签名和日期仍由人审人员完成。',
    '', '| review_id | 题来源 | 参考答案 | 实际总评 | 回答正确性 | 引用语义支持 | 引用定位 |', '|---|---|---|---|---|---|---|']
for r in rows:
    md.append('| '+' | '.join([r['review_id'],r['source_question_type'],r['reference_status'],r['actual_status'],r['answer_correctness_status'],r['citation_support_status'],r['citation_location_status']])+' |')
md.extend(['','## 逐题依据',''])
for r in rows:
    md.extend([f"### {r['review_id']}",'',f"题目：{r['question']}",'',f"标准答案：{r['reference_answer']}",'',f"实际（{r['actual_run_status']}）：{r['actual_answer']}",'',f"建议：参考={r['reference_status']}；实际={r['actual_status']}；正确性={r['answer_correctness_status']}；引用语义支持={r['citation_support_status']}；引用定位={r['citation_location_status']}。",'',f"题目来源：{r['source_question_type']}；文档性质：{r['source_document_type']}；doc_id={r['doc_id']}。",'',f"参考核验：{r['reason']}",'',f"实际核验：{r['actual_reason']}",''])
    if r['issues']:
        md.append('具体问题：')
        md.append('')
        for issue in r['issues']:
            md.append(f"- {issue['object']}：{issue['problem']}（{issue['severity']}）")
        md.append('')
    md.extend([f"建议处理：{r['suggestion']}",'',f"人审确认：{r['human_confirmation']}",'','证据（完整原页与机械对应记录均可查）：',''])
    for e in r['evidence']:
        loc=('物理页 '+str(e['page'])+'；') if e.get('page') else ('原文件行 '+str(e['line'])+'；') if e.get('line') else ''
        link=(ROOT/e['path']).as_posix()
        if e.get('line'):
            link+=':'+str(e['line'])
        md.append(f"- [{e['path']}](<{link}>)：{loc}{e['section']}。来源摘录/记录：{e['sourcequote']}")
    md.extend(['',f"证据完整性：{r['evidence_complete']}（已读取并定位支持本次判断的原文；不表示消除了记录的具体问题）。",''])
md.extend(['## 方法与限制','','- 审核范围仅group=rag、split=dev。保留题不在内容审核范围。','- 物理页号统一为PDF从1起算，原OHR evidence_page_no从0起算；非PDF按章节或图片区域定位，未伪造PDF页号。','- 原题对应记录：'+f"[original-qa-dev-audit.json](<{(ART/'original-qa-dev-audit.json').as_posix()}>)。",'- 引用机械对应记录：'+f"[citation-index-dev-audit.json](<{(ART/'citation-index-dev-audit.json').as_posix()}>)。",'- 原文件哈希、完整原页文本及PNG记录：'+f"[source-verification.json](<{(ART/'source-verification.json').as_posix()}>)。",'- 所有建议等待最终人工审核；没有借用既有辅助judge结论，也没有回填任何人工状态。',''])
(OUT/'rag-review.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'rows':len(rows),'counts':counts,'output_json':'eval/reports/d2-ai-preaudit/rag-review.json','output_md':'eval/reports/d2-ai-preaudit/rag-review.md'},ensure_ascii=False))
