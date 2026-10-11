# D2 RAG 实际回答待人工复核

逐题核对答案完整性、事实对应引用的对象/年度/单位与页码或章节；机器没有代替人工接受。

## rag-02

How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published?

标准答案：45 days

实际回答：Within 45 days after the end of the first fiscal quarter of PSS containing the required period of post-Merger combined operations. [E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-law-affiliate",
    "doc_title": "Gulf South Medical Supply Affiliate Agreement (1997)",
    "page": 1,
    "section_path": [],
    "text": "understands that ASR 130 and 135 relate to publication of financial results of\npost-Merger combined operations of PSS and GSMS. PSS agrees that it will publish\nsuch results as promptly as practicable following the Merger in the sole\ndiscretion of PSS, but in any event within 45 days after the end of the first\nfiscal quarter of PSS containing the required period of post-Merger combined\noperations and that it will notify the undersigned promptly following such\npublication.",
    "bbox": [
      13.44,
      389.46,
      357.14,
      496.86
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-03

For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934?

标准答案：three years

实际回答：答案中的数字、正负号、百分比、币种或显式单位不能在该句引用的证据中核实。

实际证据：

```json
[]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-05

Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop?

标准答案：Tame and Etherow

实际回答：On the western side of the primary watershed, the drainage is to the Mersey by the rivers Tame and Etherow [E2]。

实际证据：

```json
[
  {
    "evidence_id": "E2",
    "doc_id": "ohr-textbook-geology",
    "doc_title": "The Geology of the Country Around Holmfirth and Glossop (excerpt)",
    "page": 1,
    "section_path": [],
    "text": "On the western side of this line the drainage is to the Mersey\nby the rivers Tame and Etherow; the basin of the latter forms a\nsalient projecting some seven miles east of the general run of\nthe North Sea-Irish Sea divide (see map, Fig. 1).",
    "bbox": [
      31.5,
      443.5,
      349.0,
      491.5
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-06

What are the most satisfactory arable crops grown in the soils of the Coal Measures?

标准答案：Wheat, oats, and potatoes

实际回答：Wheat, oats and potatoes are perhaps the most satisfactory arable crops in the soils of the Coal Measures [E1].

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-textbook-geology",
    "doc_title": "The Geology of the Country Around Holmfirth and Glossop (excerpt)",
    "page": 8,
    "section_path": [],
    "text": "Wheat,\noats and potatoes are perhaps the·most satisfactory arable crops ;\nswedes and turnips are apt to suffer from ‘ finger and toe ′ disease,\nunless liming is liberal.f\nTheCoalMeasures arebetterwooded\nthan the Milistone Grits, oak and elm being prevalent instead of\nbirch,and the fields are often divided by hedgerows, in contrast\nwith thie dry stone walls of the Grits.On the latter the older\nbuildings are of local gritstone, roofed with the more fissile fag-",
    "bbox": [
      52.5,
      83.5,
      368.5,
      175.0
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-07

What is the thickness range of the Shale Grit in the southern part of the Sheet?

标准答案：450 to 550 feet

实际回答：The Shale Grit in the southern part of the Sheet is 450 to 550 feet thick. [E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-textbook-geology",
    "doc_title": "The Geology of the Country Around Holmfirth and Glossop (excerpt)",
    "page": 14,
    "section_path": [],
    "text": "GENERAL STRATIGRAPHY\nThe Shale Grit forms a wide spread on the moors in the\nsouthern part of the Sheet, where it is 450 to 550 feet'thick.It is\nalso cxposed in the valleys of the Etherow and Tame. In the\nsouth it consists of grits and sandstones with frcquent thin sandy\nshale beds and less frequent thicker shale beds; in Longdendale\nthe exposed part of the series consists of thicker and more massivc\ngrits, but theexposures in the Tame valley show the beds to be more\nlike those in the south.",
    "bbox": [
      59.0,
      271.5,
      375.0,
      381.0
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-08

In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map?

标准答案：The Rough Rock Series, the Middle Grits, the Kinderscout Grits, and the Shale Grit

实际回答：The four main groups distinguished by colour on the map are the Rough Rock Series, the Middle Grits, the Kinderscout Grits and the Shale Grit. [E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-textbook-geology",
    "doc_title": "The Geology of the Country Around Holmfirth and Glossop (excerpt)",
    "page": 8,
    "section_path": [],
    "text": "In the Millstone Grits the shales are coloured uniformly\nthroughout, but the grits and sandstones are shown by four\ncolours for the main groups, vis., The Rough Rock Series, the\nMiddle Grits,the Kinderscout Grits and the Shale Grit.These\nagain are individually distinguished by letters.\nSUPERFICIAL FORMATIONS\nAlluvium\nRecent:-\nPeat\nlGravel\nPleistocene :-\nSand and Gravel\nBoulder Clay\nSOLID FORMATIONS\nUpper Carboniferous:\nMiddle Coal Measures :(top of division not prcsent).",
    "bbox": [
      54.0,
      322.0,
      370.0,
      467.5
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-10

What type of digital device classification is specified for the equipment in accordance with the FCC rules?

标准答案：Class B

实际回答：The equipment is classified as a Class B digital device in accordance with Part 15 of the FCC rules. [E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-manual-macbook-air",
    "doc_title": "MacBook Air User Guide (archival edition)",
    "page": 65,
    "section_path": [
      "Radio and Television Interference"
    ],
    "text": "This equipment has been tested and found to comply \nwith the limits for a Class B digital device in accordance \nwith the specifications in Part 15 of FCC rules. These \nspecifications are designed to provide reasonable \nprotection against such interference in a residential \ninstallation. However, there is no guarantee that \ninterference will not occur in a particular installation.",
    "bbox": [
      39.84,
      211.19,
      176.2,
      265.19
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-11

Which application allows you to create and share movies in minutes?

标准答案：iMovie

实际回答：iMovie allows you to create and share movies in minutes. [E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-manual-macbook-air",
    "doc_title": "MacBook Air User Guide (archival edition)",
    "page": 3,
    "section_path": [
      "iMovie"
    ],
    "text": "iMovie\nCollect all your video in \none library. Create and \nshare movies in minutes.",
    "bbox": [
      27.04,
      60.72,
      103.24,
      95.21
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-12

What is the primary goal of the ENERGY STAR program in which Apple participates?

标准答案：To promote energy-efficient products.

实际回答：The ENERGY STAR® program is a partnership with electronic equipment manufacturers to promote energy-efficient products, and reducing energy consumption of products saves money and helps conserve valuable resources [E1].

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-manual-macbook-air",
    "doc_title": "MacBook Air User Guide (archival edition)",
    "page": 67,
    "section_path": [
      "ENERGY STAR® Compliance"
    ],
    "text": "As an ENERGY STAR® partner, Apple has determined \nthat standard configurations of this product meet the \nENERGY STAR® guidelines for energy efficiency. The \nENERGY STAR® program is a partnership with electronic \nequipment manufacturers to promote energy-efficient \nproducts. Reducing energy consumption of products \nsaves money and helps conserve valuable resources.",
    "bbox": [
      39.83,
      199.29,
      175.93,
      253.29
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-13

Which device can be used to share one IP address among multiple computers?

标准答案：AirPort Base Station

实际回答：You can use an AirPort Base Station to share one IP address among multiple computers. [E1][E2]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-manual-macbook-air",
    "doc_title": "MacBook Air User Guide (archival edition)",
    "page": 52,
    "section_path": [],
    "text": "If only one IP address is provided, then you must have a router capable of sharing the \nconnection, also known as network address translation (NAT) or “IP masquerading.” \nFor setup information, check the documentation provided with your router or ask the \nperson who set up your network. You can use an AirPort Base Station to share one \nIP address among multiple computers.",
    "bbox": [
      39.84,
      170.98,
      319.07,
      244.98
    ]
  },
  {
    "evidence_id": "E2",
    "doc_id": "ohr-manual-macbook-air",
    "doc_title": "MacBook Air User Guide (archival edition)",
    "page": 52,
    "section_path": [],
    "text": "You can use an AirPort Base Station to share one \nIP address among multiple computers. For information about using an AirPort Base \nStation, check Mac Help or visit the Apple AirPort website at \nwww.apple.com/support/airport.",
    "bbox": [
      39.84,
      170.98,
      319.07,
      244.98
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-15

What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture?

标准答案：leadership,culture,strategy execution,management practices,robust process improvement

实际回答：The five fundamental capabilities identified by ASQ and Forbes Insights are: leadership, culture, strategy execution, management practices, and robust process improvement [E2][E4].

实际证据：

```json
[
  {
    "evidence_id": "E2",
    "doc_id": "ohr-news-executive-insight",
    "doc_title": "Executive Insight Healthcare Magazine (archival excerpt)",
    "page": 11,
    "section_path": [],
    "text": "Success boils down to five not-so-sim-\nple but fundamental capabilities—\nleadership, culture, strategy execution, \nmanagement practices, and robust pro-\ncess improvement.",
    "bbox": [
      36.0,
      77.2,
      279.91,
      164.56
    ]
  },
  {
    "evidence_id": "E4",
    "doc_id": "ohr-news-executive-insight",
    "doc_title": "Executive Insight Healthcare Magazine (archival excerpt)",
    "page": 10,
    "section_path": [
      "ELEMENTS OF SUCCESS"
    ],
    "text": "ELEMENTS OF SUCCESS\nSuccess boils down to five not-so-simple but \nfundamental capabilities—leadership, culture, \nstrategy execution, management practices, and \nrobust process improvement.",
    "bbox": [
      239.62,
      244.42,
      420.33,
      307.52
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-16

What percentage of senior leaders rate their quality programs as world class or advanced according to the research?

标准答案：71%

实际回答：According to the research, 71% of senior leaders rate their quality programs as world class or at least advanced. [E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "ohr-news-executive-insight",
    "doc_title": "Executive Insight Healthcare Magazine (archival excerpt)",
    "page": 11,
    "section_path": [
      "RANKINGS OF QUALITY PROGRAMS"
    ],
    "text": "RANKINGS OF QUALITY PROGRAMS \nAccording to the research, 71% of senior leaders rate their qual-\nity programs as world class or at least advanced. In comparison, \n60% of quality professional respondents instead rank their quality \nprogram as average or below average. This conclusion would not \nsurprise Mark Chassin, MD, president and CEO of The Joint Com-\nmission and co-author of recent analysis of why healthcare organi-\nzations have failed to break through and close the high reliability \ngap.",
    "bbox": [
      36.0,
      556.42,
      282.3,
      715.52
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-18

What is the correlation between attention distributions on label words and the model's final prediction quantified by?

标准答案：AUCROC score

实际回答：The correlation is quantified using the AUC-ROC score, denoted AUCROC_l [E3].

实际证据：

```json
[
  {
    "evidence_id": "E3",
    "doc_id": "ohr-academic-label-words",
    "doc_title": "Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning",
    "page": 12,
    "section_path": [],
    "text": "tween the attention distributions on the label words\nof the target position (Al(q, p1), ..., Al(q, pC)) and\nthe model’s final prediction. We use the AUC-\nROC score to quantify this correlation. We re-\ngard (Al(q, p1), ..., Al(q, pC)) as a classifier’s pre-\ndiction for the model output label (that is, Al(q, pi)\nis equivalent to the probability of model outputting\nlabel i), and compute the AUC-ROC value of this\nprediction relative to the actual model output. We\ndenote this as AUCROCl.",
    "bbox": [
      306.14,
      195.82,
      526.22,
      356.57
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-19

Which datasets showed significant performance enhancement with the proposed anchor reweighting method?

标准答案：SST-2 and EmoC

实际回答：The proposed anchor re-weighting method significantly enhanced ICL performance particularly on the SST-2 and EmoC datasets [E2].

实际证据：

```json
[
  {
    "evidence_id": "E2",
    "doc_id": "ohr-academic-label-words",
    "doc_title": "Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning",
    "page": 6,
    "section_path": [
      "3.1.3 Results"
    ],
    "text": "3.1.3\nResults\nAs Table 1 shows, the proposed anchor re-\nweighting significantly enhances ICL performance,\nparticularly on the SST-2 and EmoC datasets. Be-\nsides, adding more demonstrations for vanilla ICL\nmay not bring a stable accuracy boost due to the po-\ntential noise introduced, as discussed in Zhao et al.\n(2021). Different from vanilla ICL which utilizes\nthe extra examples to form a demonstration, we\ntrain a re-weighting vector β to modulate label an-\nchor contributions.",
    "bbox": [
      305.75,
      427.67,
      526.32,
      657.92
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-21

根据这份简介，Iron Maiden 是哪一年在什么地方组建的？

标准答案：1975年，英国伦敦东部的 Leyton。

实际回答：Iron Maiden（铁娘子乐队）于1975年在伦敦东部的 Leyton 组建。[E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "artist-iron-maiden",
    "doc_title": "Iron Maiden 铁娘子乐队公开简介",
    "page": null,
    "section_path": [
      "Iron Maiden 铁娘子乐队公开简介",
      "公开背景"
    ],
    "text": "公开背景\nIron Maiden（铁娘子乐队）是英国重金属乐队，由贝斯手及主要创作者 Steve Harris 于1975年在伦敦东部的 Leyton 组建。\n乐队是英国重金属新浪潮的重要代表。其音乐和歌词涉及历史、文学、战争、神话及科幻等题材。\n同名首张录音室专辑于1980年发行；1982年的 The Number of the Beast 是其早期重要作品。这里介绍的是公开音乐背景，不包含 Chinook 销售排名或当代巡演收入。",
    "bbox": null
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-22

只根据 U2 简介，U2 于哪一年在哪座城市成立？

标准答案：1976年在都柏林成立。

实际回答：U2 于 1976 年在都柏林成立。[E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "artist-u2",
    "doc_title": "U2 乐队公开简介",
    "page": null,
    "section_path": [
      "U2 乐队公开简介",
      "公开背景"
    ],
    "text": "公开背景\nU2是爱尔兰摇滚乐队，于1976年在都柏林成立。其四位核心成员为 Bono、The Edge、Adam Clayton 和 Larry Mullen Jr.。\n乐队的音乐以摇滚为基础，也探索过电子音乐等风格。人权及社会议题常出现在其创作与公共活动中。\nU2于1980年发行首张录音室专辑 Boy，1983年发行 War。这份背景简介不提供未来演出合同、客户数据或实时销售信息。",
    "bbox": null
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-24

根据这张简介图片，Led Zeppelin 于哪一年在哪座城市成立？

标准答案：1968年在伦敦成立。

实际回答：Led Zeppelin（齐柏林飞船）于1968年在伦敦成立。[E1]

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "artist-led-zeppelin",
    "doc_title": "Led Zeppelin 齐柏林飞船乐队公开简介",
    "page": null,
    "section_path": [
      "图像 OCR"
    ],
    "text": "Led Zeppelin齐柏林飞船乐队公开简介\n公开背景\nLed Zeppelin（齐柏林飞船）是英国摇滚乐队，1968年在伦敦成立。乐队成员包括吉他手\nJimmy Page、主唱 Robert Plant、贝斯兼键盘手 John Paul Jones 和鼓手 John Bonham。\n其早期音乐扎根于蓝调摇滚与迷幻摇滚，也与硬摇滚和重金属的发展密切相关。\n首张同名专辑于1969年发行，1971年的第四张专辑收录了StairwaytoHeaven。此网页是带出\n处的简短项目改写，不是维基百科原站页面截图。\n资料来源与处理说明\n由项目根据公开百科条目改写为中文简介。用于研究检索和来源定位，不声称它是原站完整页\n面。\n百科原文作者为对应维基百科条目贡献者；本文进行了精简、中文改写与排版，按CCBY-SA4.0\n共享。未复制外部照片。\n来源\nhttps://zh.wikipedia.0rg/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9%E4%B9%90%E9%98%9F",
    "bbox": [
      127.0,
      57.0,
      1067.0,
      832.0
    ]
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-25

根据口径手册，曲目最受欢迎的默认口径是什么，对应哪个汇总表达式？

标准答案：默认按购买数量，使用 SUM(invoice_line.quantity)；销售额与歌单收录数是明确的备选口径。

实际回答：曲目最受欢迎的默认口径是沿用总计划的购买数量默认，即 SUM(invoice_line.quantity) [E1][E2]。热门曲目的核心表达式为 SUM(invoice_line.quantity) [E2]。

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "project-metric-manual",
    "doc_title": "Chinook 业务指标口径手册 项目自编",
    "page": null,
    "section_path": [
      "四项指标的定义与限制",
      "热门曲目"
    ],
    "text": "热门曲目\n曲目最受欢迎沿用总计划的购买数量默认，即 SUM(invoice_line.quantity)。按销售额或按歌单收录数属于明确的备选口径，不能凭当前排名相同而互换。\n附录中的客户谁买得最多保留金额口径；没有查询对象的短语不套同一个全局默认。并列时以 track_id 升序稳定排序。D2登记口径，不提前实现 D3 完整澄清分级或口径切换。",
    "bbox": null
  },
  {
    "evidence_id": "E2",
    "doc_id": "project-metric-manual",
    "doc_title": "Chinook 业务指标口径手册 项目自编",
    "page": null,
    "section_path": [
      "指标对应关系"
    ],
    "text": "指标对应关系\n指标全名 | 统计粒度 | 核心表达式\n发票销售额 | 发票 | SUM(invoice.total)\n平均每张发票金额 | 发票 | AVG(invoice.total)\n期间内复购客户数 | 期间内客户 | 发票数至少2张的客户数\n热门曲目 | 期间内曲目 | SUM(invoice_line.quantity)\n机器可读规则保存在 data/rules/metric_definitions.json。口径审核与每一道评测题的 gold 人工审核分别记录，互不替代。",
    "bbox": null
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-26

按口径手册，客单价的主口径全名是什么，对应哪个 SQL 表达式？

标准答案：平均每张发票金额，AVG(invoice.total)。

实际回答：客单价的主口径全名为“平均每张发票金额”，对应 SQL 表达式为 AVG(invoice.total)。[E2]

实际证据：

```json
[
  {
    "evidence_id": "E2",
    "doc_id": "project-metric-manual",
    "doc_title": "Chinook 业务指标口径手册 项目自编",
    "page": null,
    "section_path": [
      "四项指标的定义与限制",
      "平均每张发票金额"
    ],
    "text": "平均每张发票金额\n本项目将客单价主口径写全为平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。\n平均每位购买客户金额另命名为 SUM(invoice.total) / COUNT(DISTINCT invoice.customer_id)，不与每张发票平均金额混用。无发票或零分母时保留 NULL。",
    "bbox": null
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-27

根据中文数据字典，customer.country 和 invoice.billing_country 分别表示什么？

标准答案：customer.country 是客户所在地国家；invoice.billing_country 是发票账单地址国家，两个业务含义应分别保留。

实际回答：customer.country 表示客户所在地国家[E1]；invoice.billing_country 表示发票账单地址国家[E1]。两者是不同字段，不可直接互换[E1][E2]。

实际证据：

```json
[
  {
    "evidence_id": "E1",
    "doc_id": "project-chinook-dictionary",
    "doc_title": "Chinook 数据字典 中文 项目自编",
    "page": null,
    "section_path": [
      "Chinook 数据字典 中文",
      "地区字段含义"
    ],
    "text": "## 地区字段含义\ncustomer.country 表示客户所在地国家。invoice.billing_country 表示发票账单地址国家。两列在当前快照中相等，不能据此将两种业务含义混为同一口径。",
    "bbox": null
  },
  {
    "evidence_id": "E2",
    "doc_id": "project-chinook-dictionary",
    "doc_title": "Chinook 数据字典 中文 项目自编",
    "page": null,
    "section_path": [
      "Chinook 数据字典 中文",
      "表与字段",
      "invoice"
    ],
    "text": "### invoice\n销售发票，含客户、开票时间、账单地址及发票总额\n| 字段 | 数据类型 | 可为空 | 中文说明 |\n|---|---|---|---|\n| invoice_id | integer | 否 | 发票编号 |\n| customer_id | integer | 否 | 客户编号 |\n| invoice_date | timestamp without time zone | 否 | 开票时间，不是客户创建时间 |\n| billing_address | character varying(70) | 是 | 发票账单街道地址 |\n| billing_city | character varying(40) | 是 | 发票账单城市 |\n| billing_state | character varying(40) | 是 | 发票账单州或省，可为空 |\n| billing_country | character varying(40) | 是 | 发票账单地址国家，与 customer.country 是不同字段，不可直接互换 |",
    "bbox": null
  }
]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。

## rag-28

只依据这份 Iron Maiden 简介，列出该乐队2026年在中国每场演出的门票收入。

标准答案：当前指定简介不包含所问的逐场中国演出票务收入，证据不足，应明确说明不能据此回答。

实际回答：所选文档未提供足以直接支持此问题的证据，当前无法核实。

实际证据：

```json
[]
```

- [ ] 答案正确且完整。
- [ ] 每个事实由所引用片段支持。
- [ ] 页码/章节与原文件一致。
