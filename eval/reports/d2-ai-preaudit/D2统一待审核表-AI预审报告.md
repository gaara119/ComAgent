# D2统一待审核表 AI预审报告

本报告为AI建议，不代替A/B人工审核；原表和所有业务材料保持原样。

## 范围、实际可访问材料与隔离

原表195行：81别名＋50 SQL＋30鲁棒＋30 RAG＋4既有口径。本轮内容预审162行，其中158待审条目、4既有口径依据；已有系统输出77条。

当前会话承接开发工作，无法隔离保留集，因此33道保留题仅记编号和进度，不展开题目、答案或来源，不生成系统预测或成绩。

数据库核验：READ_ONLY_MATERIALS_VERIFIED；角色qa_reader，事务只读，statement_timeout=5s。访问及查询详情见下列新证据。

[材料访问登记](../../artifacts/d2-ai-preaudit/material-access.json) · [数据库实际材料与查询](../../artifacts/d2-ai-preaudit/database-materials.json) · [77条原输出及13文档来源一致性](../../artifacts/d2-ai-preaudit/evidence-integrity.json) · [原文件保持原样核验](../../artifacts/d2-ai-preaudit/protected-inputs-after.json)

新核验与旧运行记录分开保存。49条数据库材料查询、130条标准/已有预测SQL及辅助查询均为只读SELECT；后者不是重新向问答系统生成预测。RAG实际读10个开发题相关原文、提取并渲染15个完整PDF物理页，逐题检查已有引用；别名的外部来源仅核对译名用法，不用于补足限定文档的RAG答案。

[别名独立分报告](aliases-review.md) · [SQL/鲁棒独立分报告](sql-review.md) · [四项口径独立分报告](metrics-review.md) · [RAG独立分报告](rag-review.md) · [新SQL核验命令](../../artifacts/d2-ai-preaudit/sql-command-record.json) · [130条SQL与实际结果](../../artifacts/d2-ai-preaudit/sql-verification.jsonl)

## 数量汇总

| 审核对象或维度 | 已核验 | AI建议通过 | AI建议有条件通过 | AI发现错误 | 证据不足 |
|---|---:|---:|---:|---:|---:|
| 别名关系 | 81 | 54 | 25 | 0 | 2 |
| SQL与鲁棒题参考答案 | 56 | 54 | 2 | 0 | 0 |
| SQL与鲁棒题已有系统回答 | 56 | 54 | 1 | 0 | 1 |
| RAG参考答案 | 21 | 21 | 0 | 0 | 0 |
| RAG完整回答正确性 | 21 | 20 | 1 | 0 | 0 |
| RAG引用语义支持 | 21 | 20 | 1 | 0 | 0 |
| RAG引用定位 | 21 | 11 | 0 | 10 | 0 |
| 既有已确认业务口径与本次材料一致性 | 4 | 4 | 0 | 0 | 0 |

这些维度不能相加作为题数。77条已有回答的整体判断为65条建议通过、11条有条件通过、1条证据不足；其中10条RAG整体有条件通过的题，引用定位维度明确标为“AI发现错误”，共涉及13个引用条目。整体条件通过不等于引用定位正确。

162个内容核验条目中，157个有足够明确材料，5个存在材料或语境缺口：铁处女、齐柏林飞艇仅取得部分外部命名证据；金属→Metallica和节奏摇滚→Rock And Roll缺少充分别名依据；robust-23缺少“这批曲目”的范围定义。前两项仍可作有条件候选，后两项别名关系标记证据不足；robust-23的实际回答暂不能确定。

42个条目带有问题、适用条件或限制，其中10个条目存在明确引用定位错误。42不是错误题数；33道保留题因未隔离跳过，与材料不足分开统计。

### 机器可读汇总

```json
{
  "original_rows": 195,
  "pending_rows": 191,
  "reviewed_pending_rows": 158,
  "reviewed_confirmed_basis_rows": 4,
  "total_rows_content_reviewed": 162,
  "skipped_holdout_rows": 33,
  "actual_development_outputs_reviewed": 77,
  "reference_status_counts": {
    "AI建议通过": 133,
    "AI建议有条件通过": 27,
    "AI发现错误": 0,
    "证据不足": 2
  },
  "actual_status_counts": {
    "AI建议通过": 65,
    "AI建议有条件通过": 11,
    "AI发现错误": 0,
    "证据不足": 1
  },
  "rows_with_explicit_material_evidence": 157,
  "rows_with_incomplete_material_evidence": 5,
  "incomplete_material_review_ids": [
    "alias:a-e36bfe04cba29de8",
    "alias:a-751d38c444555de2",
    "alias:a-0c47392129d13dd6",
    "alias:a-c748b229db869a4e",
    "robust:robust-23"
  ],
  "rows_with_issues_or_restrictions": 42,
  "issue_or_restriction_review_ids": [
    "alias:a-3a8a1d5195e9c6a0",
    "alias:a-e36bfe04cba29de8",
    "alias:a-f6304e1cde119b8f",
    "alias:a-751d38c444555de2",
    "alias:a-9ab23063254419e0",
    "alias:a-0c47392129d13dd6",
    "alias:a-7d3693714ee37b46",
    "alias:a-2ad4affe6af89ef4",
    "alias:a-9f5bb5a79e3b2818",
    "alias:a-c43d08f9e0effe4d",
    "alias:a-439ce0734774f114",
    "alias:a-f637ff312a6fead6",
    "alias:a-10514461292c596d",
    "alias:a-cb69b4bf22161e6e",
    "alias:a-5972cabfe64bae77",
    "alias:a-0e44ca874f4ba96f",
    "alias:a-c748b229db869a4e",
    "alias:a-b5ca3e94894dee8d",
    "alias:a-9eb72fa09563fb7e",
    "alias:a-604796b76eb1cd3b",
    "alias:a-9d6edadfda3e46a9",
    "alias:a-6799bc523f9e8693",
    "alias:a-7b241be59eef3bbb",
    "alias:a-0c3df10756626f4a",
    "alias:a-a653ead69db804b0",
    "alias:a-14625e480dd8676e",
    "alias:a-d2-plan-rock-and-roll",
    "nl2sql:sql-38",
    "robust:robust-13",
    "robust:robust-23",
    "robust:robust-26",
    "rag:rag-05",
    "rag:rag-06",
    "rag:rag-07",
    "rag:rag-08",
    "rag:rag-10",
    "rag:rag-11",
    "rag:rag-13",
    "rag:rag-15",
    "rag:rag-16",
    "rag:rag-18",
    "rag:rag-19"
  ],
  "error_rows": 10,
  "error_review_ids": [
    "rag:rag-05",
    "rag:rag-06",
    "rag:rag-07",
    "rag:rag-08",
    "rag:rag-11",
    "rag:rag-13",
    "rag:rag-15",
    "rag:rag-16",
    "rag:rag-18",
    "rag:rag-19"
  ],
  "alias_disposition_counts": {
    "建议直接使用": 54,
    "仅作为条件候选": 25,
    "建议拒绝": 0,
    "证据不足": 2
  },
  "rag_answer_correctness_counts": {
    "AI建议通过": 20,
    "AI建议有条件通过": 1
  },
  "rag_citation_support_counts": {
    "AI建议通过": 20,
    "AI建议有条件通过": 1
  },
  "rag_citation_location_counts": {
    "AI建议通过": 11,
    "AI发现错误": 10
  },
  "rag_source_question_type_counts": {
    "OHR原题": 14,
    "自编": 7
  },
  "original_files_unchanged": 825
}
```

问题数量按有问题或限制的条目去重计算，不将同题的参考与实际问题重复算成两道题；错误、条件限制、材料不足和保留题跳过分别列示。

## 优先处理事项

- **robust:robust-23**：参考=AI建议有条件通过；实际=证据不足。[
  {
    "object": "question",
    "problem": "“全部”改成“这批”新增无前文的指代范围，鲁棒变体未严格保持基题范围。",
    "severity": "conditional"
  },
  {
    "object": "reference",
    "problem": "AVG全表是未声明的全集假设；只有确认“这批=全部曲目”后参考才可接受。",
    "severity": "conditional"
  },
  {
    "object": "actual",
    "problem": "范围不明仍直接全表AVG，原输出缺少范围澄清，最终正确性证据不足。",
    "severity": "insufficient_evidence"
  }
] 建议：人工确认指代集合；若目标为保持基题语义，应将变体范围说清楚，或补充合法上下文再独立核对。不能通过改参考平均值来使系统过关。
- **rag:rag-19**：参考=AI建议通过；实际=AI建议有条件通过。[
  {
    "object": "actual_answer.补充提升数值",
    "problem": "SST-2比较采用Vanilla 5-shot基线，EmoC采用Vanilla 1-shot基线；回答未说明两者不同。单个数字正确不等于比较语义完整。",
    "severity": "需人工确认"
  },
  {
    "object": "actual_evidence.E1.bbox; E5.section_path",
    "problem": "E1 bbox=[70.87,486.56,152.06,499.36]在原第6页裁到左栏“In this equation, βi”方程说明，不覆盖右栏3.1.3核心支持句。E5章节路径“0 role that anchors play in ICL.”是前页续句/公式残片，原文位置是第7页Table 1。",
    "severity": "error",
    "category": "citation_location"
  }
] 建议：保留gold的SST-2和EmoC。人审可按原题只保留数据集名称；若保留数值，逐项注明Vanilla 1-shot/5-shot→Anchor 1-shot及GPT2-XL、五随机种子平均的实验范围。不得在本次审核中静默改答案。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。
- **alias:a-0c47392129d13dd6**：参考=证据不足；实际=不适用（别名配置审核，未生成预测）。[
  "未取得“金属”作为Metallica简称的独立用法证据。",
  "与 genre.name=Metal 同形且可能泛指金属音乐/材料。"
] 建议：暂不作为可直接使用的艺人别名；补充真实简称来源后仍须限定艺人语境，不得剥夺流派候选。
- **alias:a-c748b229db869a4e**：参考=证据不足；实际=不适用（别名配置审核，未生成预测）。[
  "没有独立来源证明“节奏摇滚”专指Rock And Roll。",
  "加入“节奏”的意图可能只是人为区分类别，非真实译名依据。"
] 建议：暂不启用该译名；补充可信音乐术语来源或明确人审定义后再评估，保留Rock/Rock And Roll本来的分类差异。
- **nl2sql:sql-38**：参考=AI建议有条件通过；实际=AI建议有条件通过。[
  {
    "object": "reference",
    "problem": "track.bytes可NULL且ORDER BY bytes DESC默认NULLS FIRST，缺少未知文件大小处理规则；现存NULL=0，未发现本次实际三行值错误。",
    "severity": "conditional"
  },
  {
    "object": "actual",
    "problem": "track.bytes可NULL且ORDER BY bytes DESC默认NULLS FIRST，缺少未知文件大小处理规则；现存NULL=0，未发现本次实际三行值错误。",
    "severity": "conditional"
  }
] 建议：人工决定最大字节数排行是否仅针对当前无NULL快照，或应规定排除NULL/NULLS LAST；仅提出修订建议，不改gold或系统SQL。
- **rag:rag-05**：参考=AI建议通过；实际=AI建议有条件通过。[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "原地质扫描PDF隐藏文字层的bbox=[22.92,516.71,233.1,577.03]可裁出西侧河流文字，但Poppler真实可视页红框落在更低的Don/Derwent及南侧分水岭段落，不覆盖可视Tame/Etherow原句。原页MediaBox=CropBox且无旋转，不能用裁切原点偏移解释。",
    "severity": "error",
    "category": "citation_location"
  }
] 建议：保留当前gold及回答；引文定位保持物理第1页。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。
- **rag:rag-06**：参考=AI建议通过；实际=AI建议有条件通过。[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "bbox=[36.12,245.41,246.9,381.44]在隐藏文字层能取出作物段，真实扫描页红框却落在Table of Formations说明段，不覆盖页面上方Coal Measures作物原句。文字层命中不等于视觉坐标准确。",
    "severity": "error",
    "category": "citation_location"
  }
] 建议：保留列表gold；人工解释宜保留原文perhaps，不扩展为现代农业普遍结论。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。
- **rag:rag-07**：参考=AI建议通过；实际=AI建议有条件通过。[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "bbox=[40.68,403.4,250.62,475.17]在隐藏文字层能取出450至550 feet句，真实扫描页红框位于更低的砂岩特征/Grindslow Shales段，不覆盖可视Shale Grit厚度句。原页和答案正确，但框选定位错位。",
    "severity": "error",
    "category": "citation_location"
  }
] 建议：保留当前gold和回答；人审检查feet与Sheet南部限定。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。
- **rag:rag-08**：参考=AI建议通过；实际=AI建议有条件通过。[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "bbox=[37.68,383.95,247.98,534.78]在隐藏文字层能取出四组图例说明，真实扫描页红框却位于Superficial/Solid Formations表，不覆盖上方可视四组列举句。原文字层与图像坐标不齐。",
    "severity": "error",
    "category": "citation_location"
  }
] 建议：保留当前gold和回答，不把图例组数理解为地质总层数。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。
- **rag:rag-11**：参考=AI建议通过；实际=AI建议有条件通过。[
  {
    "object": "reference_text; actual_evidence.E1.text",
    "problem": "引用描述与应用名的归属依赖原页卡片布局；线性提取与iPhoto交错，已用原页视觉补足核验。",
    "severity": "提示"
  },
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "E1 bbox=[27.21,99.39,325.38,117.81]；考虑原PDF CropBox偏移(129,219)后，仅框到iMovie/iPhoto网址与Help行，未覆盖Create and share movies in minutes描述。section_path=[]只是未登记章节，本身不判错。",
    "severity": "error",
    "category": "citation_location"
  }
] 建议：保留iMovie；人工审核随附原页PNG，对照左上卡片。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。
- **rag:rag-13**：参考=AI建议通过；实际=AI建议有条件通过。[
  {
    "object": "actual_evidence.E1/E2.section_path",
    "problem": "“4 Follow the onscreen instructions.”是Network Diagnostics步骤4，而非共享IP段落的章节标题；字段把步骤文本误登记为章节。PDF物理第52页正确，CropBox偏移后bbox能包含支持句，不据MediaBox未平移裁切结果误判坐标。",
    "severity": "error",
    "category": "citation_location"
  }
] 建议：保留当前设备gold与回答，勿把只有一个IP的条件外推到所有ISP配置。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。
- **rag:rag-15**：参考=AI建议通过；实际=AI建议有条件通过。[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "E1 bbox=[432.28,50.71,534.6,66.45]在原第11页只框到EYE ON QUALITY页眉，不覆盖五能力正文。E3第10页物理页/Elements of Success定位正确，故回答语义仍可获充分支持。",
    "severity": "error",
    "category": "citation_location"
  }
] 建议：保留清单和回答；人审据第10页完整句，记录E1截断但E3补足。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。
- 其余 30 个有问题或限制的条目，在下方按原编号完整列出。

## 逐项AI预审

### metric:sales_revenue

- 分组：metric；划分：不适用

**审核对象：** 发票销售额

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（已确认口径依据）

**参考判断理由：**

发票销售额在invoice粒度SUM(total)，期间依据invoice_date半开范围，示例2024年返回477.53。按曲目/艺术家另用invoice_line.unit_price*quantity，不能明细JOIN后重复SUM发票总额；全库发票与明细对账均2328.60、差0.00。空期间SUM为NULL，不能无声改0。金额仅数据库金额单位，源数据未声明币种或支付状态。

**实际回答判断理由：**

本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。

**建议处理方式：**

保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。

**仍需人工确认：**

既有用户陈述“A、B已共同核对同意四项口径”；本次不新增/冒填人工审批，不要求重复确认四项已授权口径。

**证据文件及具体位置：**

- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=metrics.sales_revenue; general; sql_examples.revenue_invoice
- [eval/artifacts/d2/source/metric-human-review.json](../../artifacts/d2/source/metric-human-review.json) — section=method; statement; scope; proposal_sha256; reviewed_at_utc; note=原既有人工共同确认记录，仅核实留存、不代填新审批
- [eval/artifacts/d2/source/metric-sql-checks.json](../../artifacts/d2/source/metric-sql-checks.json) — section=records.id=revenue_invoice; note=既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=114; note=本次只读重执行既有SQL示例
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=invoice; invoice_line; track; invoice_date_range
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; invoice_dates; identity; privileges
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=125; note=empty-amount-semantics
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=118; note=发票与明细金额对账

### metric:average_invoice_amount

- 分组：metric；划分：不适用

**审核对象：** 平均每张发票金额

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（已确认口径依据）

**参考判断理由：**

平均每张发票金额为AVG(invoice.total)，示例先平均再保留两位得到2024年5.75；平均每位购买客户金额SUM(total)/COUNT(DISTINCT customer_id)是另一个指标。空期间AVG为NULL。已确认的短标签提案“客单价”不应使未指明对象的其他问题自动获得默认口径，runtime_defaults_enabled仍false。

**实际回答判断理由：**

本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。

**建议处理方式：**

保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。

**仍需人工确认：**

既有用户陈述“A、B已共同核对同意四项口径”；本次不新增/冒填人工审批，不要求重复确认四项已授权口径。

**证据文件及具体位置：**

- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=metrics.average_invoice_amount; general; sql_examples.average_invoice
- [eval/artifacts/d2/source/metric-human-review.json](../../artifacts/d2/source/metric-human-review.json) — section=method; statement; scope; proposal_sha256; reviewed_at_utc; note=原既有人工共同确认记录，仅核实留存、不代填新审批
- [eval/artifacts/d2/source/metric-sql-checks.json](../../artifacts/d2/source/metric-sql-checks.json) — section=records.id=average_invoice; note=既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=115; note=本次只读重执行既有SQL示例
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=invoice; invoice_line; track; invoice_date_range
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; invoice_dates; identity; privileges
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=125; note=empty-amount-semantics

### metric:repeat_customer_count

- 分组：metric；划分：不适用

**审核对象：** 期间内复购客户数

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（已确认口径依据）

**参考判断理由：**

期间内复购客户数先将明确期间[2024-01-01,2025-01-01)的invoice按customer_id分组，HAVING COUNT(*)>=2，再计合格客户数，示例27位并有逐客户明细支持；不是发票条数、客户历史跨期次数或付款成功次数。没有合格客户时COUNT返回0，缺少期间不能自动填年。

**实际回答判断理由：**

本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。

**建议处理方式：**

保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。

**仍需人工确认：**

既有用户陈述“A、B已共同核对同意四项口径”；本次不新增/冒填人工审批，不要求重复确认四项已授权口径。

**证据文件及具体位置：**

- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=metrics.repeat_customer_count; general; sql_examples.repeat_customers
- [eval/artifacts/d2/source/metric-human-review.json](../../artifacts/d2/source/metric-human-review.json) — section=method; statement; scope; proposal_sha256; reviewed_at_utc; note=原既有人工共同确认记录，仅核实留存、不代填新审批
- [eval/artifacts/d2/source/metric-sql-checks.json](../../artifacts/d2/source/metric-sql-checks.json) — section=records.id=repeat_customers; note=既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=116; note=本次只读重执行既有SQL示例
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=invoice; invoice_line; track; invoice_date_range
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; invoice_dates; identity; privileges
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=127; note=repeat-customer-check

### metric:popular_tracks

- 分组：metric；划分：不适用

**审核对象：** 热门曲目

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（已确认口径依据）

**参考判断理由：**

明确期间内热门曲目按SUM(invoice_line.quantity)的实际购买数量，关联invoice_date过滤；不是目录单价、金额或播放列表成员数。数量降序后track_id升序作并列规则，再LIMIT 5；2024年示例3/9/15/21/30均购买1，补充前10行也并列1，稳定次排序必要。客户“谁买得最多”的金额口径与曲目热门不同，主语省略且无期间的问题仍需澄清。

**实际回答判断理由：**

本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。

**建议处理方式：**

保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。

**仍需人工确认：**

既有用户陈述“A、B已共同核对同意四项口径”；本次不新增/冒填人工审批，不要求重复确认四项已授权口径。

**证据文件及具体位置：**

- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=metrics.popular_tracks; general; sql_examples.popular_tracks
- [eval/artifacts/d2/source/metric-human-review.json](../../artifacts/d2/source/metric-human-review.json) — section=method; statement; scope; proposal_sha256; reviewed_at_utc; note=原既有人工共同确认记录，仅核实留存、不代填新审批
- [eval/artifacts/d2/source/metric-sql-checks.json](../../artifacts/d2/source/metric-sql-checks.json) — section=records.id=popular_tracks; note=既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=117; note=本次只读重执行既有SQL示例
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=invoice; invoice_line; track; invoice_date_range
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; invoice_dates; identity; privileges
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=128; note=popular-quantity-ties

### alias:a-3a8a1d5195e9c6a0

- 分组：alias；划分：不适用

**审核对象：** 铁娘子 → artist.name = Iron Maiden

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 artist.name 字段与标准值 Iron Maiden 均存在，完整DISTINCT与既有标准值索引一致。本地简介与唱片公司中文资料均支持 Iron Maiden 的该中文乐队名。裸词还可作人物称号、作品名或刑具名，真实库仅有该艺人并不能消除库外语义；须先确认音乐艺人语境。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "裸词跨领域多义；不能仅因 artist 表中恰有一个匹配就对任意输入唯一绑定。"
]

**建议处理方式：**

明确“铁娘子乐队”、曲目/专辑或artist字段上下文时保留 Iron Maiden 候选；否则澄清指称。

**仍需人工确认：**

确认默认中文乐队名及裸词歧义处理；不要照抄既有建议作为人审结论。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=2
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[113]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-26903b3204f3eef20547; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=461
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/iron-maiden.html](../../../data/docs/raw/d2/iron-maiden.html) — section=公开背景第1段/标准名称页脚; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material; line=4
- [https://www.sonymusic.com.tw/?p=21566](https://www.sonymusic.com.tw/?p=21566) — section=专辑简介首段; title=索尼音乐：早晨後的配樂 十周年紀念版; supports=唱片公司中文简介将 Iron Maiden 与“铁娘子”的繁体字形并列；简繁转换为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://zh.wikipedia.org/wiki/%E9%90%B5%E8%99%95%E5%A5%B3](https://zh.wikipedia.org/wiki/%E9%90%B5%E8%99%95%E5%A5%B3) — section=条目首段; title=维基百科：铁处女; supports=同一词形也用于刑具；只作为跨领域歧义佐证。; kind=external_source; access=搜索工具返回可读条目正文；未在本轮打开完整页; source_strength=secondary

### alias:a-e36bfe04cba29de8

- 分组：alias；划分：不适用

**审核对象：** 铁处女 → artist.name = Iron Maiden

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 artist.name 字段与标准值 Iron Maiden 均存在，完整DISTINCT与既有标准值索引一致。本地简介只支持“铁娘子”；外部百科可读条目正文另外列出“铁处女”为该乐团译名，因此现有材料不足以断言此词错误。该词同时明确指刑具，且完整原页未成功访问、未找到同等级唱片公司中文证据；仅能暂列音乐艺人语境下的条件候选。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "同词刑具义明显。",
  "译名依据为外部二手百科可读节选；完整原页访问失败，证据链仍需补强。"
]

**建议处理方式：**

禁止对裸词自动唯一绑定；仅在用户明确讨论乐队且人审补充可信译名证据后考虑候选。

**仍需人工确认：**

核实完整中文译名来源，选择地域译法与条件检索范围；既有“拒绝”建议也不是证据。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=3
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[113]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-26903b3204f3eef20547; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=461
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/iron-maiden.html](../../../data/docs/raw/d2/iron-maiden.html) — section=公开背景第1段/标准名称页脚; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material; line=4
- [https://www.sonymusic.com.tw/?p=21566](https://www.sonymusic.com.tw/?p=21566) — section=专辑简介首段; title=索尼音乐：早晨後的配樂 十周年紀念版; supports=唱片公司中文简介将 Iron Maiden 与“铁娘子”的繁体字形并列；简繁转换为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://zh.wikipedia.org/wiki/%E9%90%B5%E5%A8%98%E5%AD%90%E6%A8%82%E5%9C%98](https://zh.wikipedia.org/wiki/%E9%90%B5%E5%A8%98%E5%AD%90%E6%A8%82%E5%9C%98) — section=条目首段与英文名信息框; title=维基百科：铁娘子乐团; supports=可读搜索正文列出另一中文译名“铁处女”，支持其作为候选；不证明项目默认译名。; kind=external_source; access=搜索工具返回可读条目正文；open完整页返回 Internal Error，未取得完整原页; source_strength=secondary
- [https://zh.wikipedia.org/wiki/%E9%90%B5%E8%99%95%E5%A5%B3](https://zh.wikipedia.org/wiki/%E9%90%B5%E8%99%95%E5%A5%B3) — section=条目首段; title=维基百科：铁处女; supports=同一词形也用于刑具；只作为跨领域歧义佐证。; kind=external_source; access=搜索工具返回可读条目正文；未在本轮打开完整页; source_strength=secondary

### alias:a-7a0187a2e65d10ae

- 分组：alias；划分：不适用

**审核对象：** Iron Maiden乐队 → artist.name = Iron Maiden

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 artist.name 字段与标准值 Iron Maiden 均存在，完整DISTINCT与既有标准值索引一致。“Iron Maiden乐队”完整保留标准名称 Iron Maiden，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 Iron Maiden。

**仍需人工确认：**

人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=4
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[113]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-26903b3204f3eef20547; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=461
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/iron-maiden.html](../../../data/docs/raw/d2/iron-maiden.html) — section=公开背景第1段/标准名称页脚; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material; line=4
- [https://www.sonymusic.com.tw/?p=21566](https://www.sonymusic.com.tw/?p=21566) — section=专辑简介首段; title=索尼音乐：早晨後的配樂 十周年紀念版; supports=唱片公司中文简介将 Iron Maiden 与“铁娘子”的繁体字形并列；简繁转换为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-f6304e1cde119b8f

- 分组：alias；划分：不适用

**审核对象：** 齐柏林飞船 → artist.name = Led Zeppelin

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 artist.name 字段与标准值 Led Zeppelin 均存在，完整DISTINCT与既有标准值索引一致。本地公开简介明确把该译名与 Led Zeppelin 并列，外部中文艺人条目旁证。该裸词又是飞船通名，翻译对应成立仅限音乐艺人语境；数据库标准对象存在不证明用户一定在问乐队。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "乐队译名与航空器名称多义。"
]

**建议处理方式：**

明确“乐队/乐团”、音乐作品或artist字段后保留 Led Zeppelin 候选；航空器语境不绑定。

**仍需人工确认：**

确认接受飞船/飞艇两个地区用名及音乐上下文约束；需要时补读完整外部变体原页。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=5
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[136]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-962f8d82d2343d62bf1f; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=484
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/source/led-zeppelin-summary.html](../../../data/docs/raw/d2/source/led-zeppelin-summary.html) — section=公开背景第1段/标准名称页脚; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material; line=4
- [https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29](https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29) — section=条目标题、首段与英文名信息; title=维基百科：齐柏林飞船（乐团）; supports=中文艺人条目与 Led Zeppelin 对应，并区分飞船等其他含义。; kind=external_source; access=搜索工具返回可读条目正文; source_strength=secondary

### alias:a-751d38c444555de2

- 分组：alias；划分：不适用

**审核对象：** 齐柏林飞艇 → artist.name = Led Zeppelin

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 artist.name 字段与标准值 Led Zeppelin 均存在，完整DISTINCT与既有标准值索引一致。本地简介使用“齐柏林飞船”；另有州旅游官网活动中文节选使用“齐柏林飞艇”且路径对应 Led Zeppelin，支持该译名变体。飞船/飞艇也有航空器语义；不能把这种词形变体作一般实体的固定替换。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "音乐乐队与航空器多义。",
  "外部变体来源完整页open失败，仅取得官方搜索节选。"
]

**建议处理方式：**

明确“乐队/乐团”、音乐作品或artist字段后保留 Led Zeppelin 候选；航空器语境不绑定。

**仍需人工确认：**

确认接受飞船/飞艇两个地区用名及音乐上下文约束；需要时补读完整外部变体原页。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=6
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[136]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-962f8d82d2343d62bf1f; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=484
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/source/led-zeppelin-summary.html](../../../data/docs/raw/d2/source/led-zeppelin-summary.html) — section=公开背景第1段/标准名称页脚; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material; line=4
- [https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29](https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29) — section=条目标题、首段与英文名信息; title=维基百科：齐柏林飞船（乐团）; supports=中文艺人条目与 Led Zeppelin 对应，并区分飞船等其他含义。; kind=external_source; access=搜索工具返回可读条目正文; source_strength=secondary
- [https://www.visitnsw.com/cn/destinations/central-coast/gosford-area/avoca-beach/events/the-life-times-led-zeppelin-featuring-zepplin-orchestral-strings](https://www.visitnsw.com/cn/destinations/central-coast/gosford-area/avoca-beach/events/the-life-times-led-zeppelin-featuring-zepplin-orchestral-strings) — section=活动标题与简介; title=新南威尔士州旅游官网：齐柏林飞艇乐队的生平与时代; supports=官方旅游活动中文页使用“齐柏林飞艇”，页面路径标明 Led Zeppelin；只支持中文名用法，不审核演出时效。; kind=external_source; access=搜索工具返回标题与正文节选；open完整页返回 Internal Error; source_strength=primary

### alias:a-e7baa0eb0389f85e

- 分组：alias；划分：不适用

**审核对象：** Led Zeppelin乐队 → artist.name = Led Zeppelin

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 artist.name 字段与标准值 Led Zeppelin 均存在，完整DISTINCT与既有标准值索引一致。“Led Zeppelin乐队”完整保留标准名称 Led Zeppelin，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 Led Zeppelin。

**仍需人工确认：**

人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=7
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[136]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-962f8d82d2343d62bf1f; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=484
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/source/led-zeppelin-summary.html](../../../data/docs/raw/d2/source/led-zeppelin-summary.html) — section=公开背景第1段/标准名称页脚; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material; line=4
- [https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29](https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29) — section=条目标题、首段与英文名信息; title=维基百科：齐柏林飞船（乐团）; supports=中文艺人条目与 Led Zeppelin 对应，并区分飞船等其他含义。; kind=external_source; access=搜索工具返回可读条目正文; source_strength=secondary

### alias:a-9ab23063254419e0

- 分组：alias；划分：不适用

**审核对象：** 金属乐队 → artist.name = Metallica

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 artist.name 字段与标准值 Metallica 均存在，完整DISTINCT与既有标准值索引一致。本地 DOCX 标题使用此专名，文化部演出批复把它与 Metallica 并列，已取得独立中文名证据。它也可指任意演奏金属音乐的乐队；用户问“有哪些金属乐队”是一个类别问题，不能改成只查 Metallica。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "专名与音乐类别组合短语同形；类别查询可能包含多位artist。"
]

**建议处理方式：**

专名或 Metallica 指称明确时作候选；泛指一类乐队时按流派/作品分析并澄清，不强制唯一艺人。

**仍需人工确认：**

确认专名使用情形与类别问句的识别边界。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=8
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[158]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-8cfcf0e35bfb7532e28a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=506
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/metallica-introduction.docx](../../../data/docs/raw/d2/metallica-introduction.docx) — section=word/document.xml：段落1标题、段落3与5; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material
- [https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html](https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html) — section=批复正文，第36行；文市函〔2013〕689号; title=文化部关于同意美国金属乐队到上海市演出的批复; supports=文化部演出许可正文将中文乐队名与 Metallica 并列；证明专名“金属乐队”的对应关系。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-0c47392129d13dd6

- 分组：alias；划分：不适用

**审核对象：** 金属 → artist.name = Metallica

**别名或参考答案判断：** 证据不足

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

证据不足

**参考判断理由：**

实查 artist.name 字段与标准值 Metallica 均存在，完整DISTINCT与既有标准值索引一致。Metallica 是真实 artist，文化部支持其完整中文名“金属乐队”，但已读本地与外部资料没有把裸词“金属”独立作为该乐队简称的证据。相同词形在待审CSV另指 genre.name=Metal，真实流派库还包含 Heavy Metal；删去“乐队”是有歧义的AI猜测，不能据熟悉程度批准。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "未取得“金属”作为Metallica简称的独立用法证据。",
  "与 genre.name=Metal 同形且可能泛指金属音乐/材料。"
]

**建议处理方式：**

暂不作为可直接使用的艺人别名；补充真实简称来源后仍须限定艺人语境，不得剥夺流派候选。

**仍需人工确认：**

提供可信简称用例并确认优先级；找不到依据时不启用该裸词艺人映射。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=9
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[158]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-8cfcf0e35bfb7532e28a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=506
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/metallica-introduction.docx](../../../data/docs/raw/d2/metallica-introduction.docx) — section=word/document.xml：段落1标题、段落3与5; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material
- [https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html](https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html) — section=批复正文，第36行；文市函〔2013〕689号; title=文化部关于同意美国金属乐队到上海市演出的批复; supports=文化部演出许可正文将中文乐队名与 Metallica 并列；证明专名“金属乐队”的对应关系。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul](https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul) — section=metal noun (MUSIC)及Synonym; title=剑桥英语辞典：metal; supports=辞典列出音乐义并将 heavy metal 视作同义词，支持真实分类间的语义歧义检查。; kind=external_source; access=搜索工具返回可读词条正文; source_strength=primary
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.text_values["genre.name"].values：Metal和Heavy Metal; supports=真实类别并存，提供歧义候选; kind=local_material

### alias:a-713e91edadb5f817

- 分组：alias；划分：不适用

**审核对象：** Metallica乐队 → artist.name = Metallica

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 artist.name 字段与标准值 Metallica 均存在，完整DISTINCT与既有标准值索引一致。“Metallica乐队”完整保留标准名称 Metallica，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 Metallica。

**仍需人工确认：**

人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=10
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[158]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-8cfcf0e35bfb7532e28a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=506
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/metallica-introduction.docx](../../../data/docs/raw/d2/metallica-introduction.docx) — section=word/document.xml：段落1标题、段落3与5; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material
- [https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html](https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html) — section=批复正文，第36行；文市函〔2013〕689号; title=文化部关于同意美国金属乐队到上海市演出的批复; supports=文化部演出许可正文将中文乐队名与 Metallica 并列；证明专名“金属乐队”的对应关系。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-a04cacbc074e2ac6

- 分组：alias；划分：不适用

**审核对象：** U2乐队 → artist.name = U2

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 artist.name 字段与标准值 U2 均存在，完整DISTINCT与既有标准值索引一致。“U2乐队”完整保留标准名称 U2，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 U2。

**仍需人工确认：**

人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=11
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[258]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-7050c980bcdbcadd0509; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=606
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/u2.html](../../../data/docs/raw/d2/u2.html) — section=公开背景第1段/标准名称页脚; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material; line=4
- [https://www.u2.com/pages/band](https://www.u2.com/pages/band) — section=页面标题与成员/建团首段; title=U2 官网：THE BAND; supports=官网确认 U2 是乐队；“乐队/乐团”为同类中文限定语的AI语言判断，不采纳网页当前活动信息。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-5875ecf83bb89913

- 分组：alias；划分：不适用

**审核对象：** U2乐团 → artist.name = U2

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 artist.name 字段与标准值 U2 均存在，完整DISTINCT与既有标准值索引一致。“U2乐团”完整保留标准名称 U2，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 U2。

**仍需人工确认：**

人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=12
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[artist].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=59
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 artist.name; $.text_values["artist.name"].values[258]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-7050c980bcdbcadd0509; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=606
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### artist; supports=字典中的字段范围说明; kind=local_material; line=31
- [data/docs/raw/d2/u2.html](../../../data/docs/raw/d2/u2.html) — section=公开背景第1段/标准名称页脚; supports=本地项目改写艺人材料确认对象背景；不是LLM别名草稿; kind=local_material; line=4
- [https://www.u2.com/pages/band](https://www.u2.com/pages/band) — section=页面标题与成员/建团首段; title=U2 官网：THE BAND; supports=官网确认 U2 是乐队；“乐队/乐团”为同类中文限定语的AI语言判断，不采纳网页当前活动信息。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-b36489cadceee749

- 分组：alias；划分：不适用

**审核对象：** 澳大利亚 → customer.country = Australia

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。“澳大利亚”由外交部国家概况的国名与页面名称支持，对应真实标准值 Australia。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Australia；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=13
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[1]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-08ebc61e3f77af84be3d; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=746
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/) — section=页面标题、国名段及英/本国语国名; title=外交部：澳大利亚国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-7d3693714ee37b46

- 分组：alias；划分：不适用

**审核对象：** 澳洲 → customer.country = Australia

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 customer.country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。教育部译名索引直接将“澳洲”与 Australia 对应，国家用法有独立依据。该词在用户表达中也可能作大陆/广域地区用语；不能仅因当前国家库无洲级值就把地区意图压成一个国家。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "国家简称与大陆/广域地区意图可能混淆。"
]

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Australia；保留另一国家字段的独立口径。 用户谈大陆、洲或多个国家时先澄清范围。

**仍需人工确认：**

确认本项目接受该地区用名，并规定国别/洲别澄清方式。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=14
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[1]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-08ebc61e3f77af84be3d; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=746
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/) — section=页面标题、国名段及英/本国语国名; title=外交部：澳大利亚国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dict.revised.moe.edu.tw/appendix.jsp?ID=28&la=1&page=14&powerMode=0&ver=4](https://dict.revised.moe.edu.tw/appendix.jsp?ID=28&la=1&page=14&powerMode=0&ver=4) — section=澳洲—Australia条目; title=教育部重编国语辞典：西文译名索引表; supports=辞典索引将“澳洲”与 Australia 对应；未证明一切大陆/洲语境都能作国家筛选。; kind=external_source; access=搜索工具返回可读索引节选; source_strength=primary

### alias:a-840245fad126ae71

- 分组：alias；划分：不适用

**审核对象：** 澳大利亚联邦 → customer.country = Australia

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。“澳大利亚联邦”由外交部国家概况的国名与页面名称支持，对应真实标准值 Australia。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Australia；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=15
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[1]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-08ebc61e3f77af84be3d; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=746
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/) — section=页面标题、国名段及英/本国语国名; title=外交部：澳大利亚国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-cf1b483ec6900d1a

- 分组：alias；划分：不适用

**审核对象：** 巴西 → customer.country = Brazil

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Brazil 均存在，完整DISTINCT与既有标准值索引一致。“巴西”由外交部国家概况的国名与页面名称支持，对应真实标准值 Brazil。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Brazil；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=16
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-95ff10c443473368bada; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=749
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/) — section=页面标题、国名段及英/本国语国名; title=外交部：巴西国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-48667df2696e251c

- 分组：alias；划分：不适用

**审核对象：** 巴西联邦共和国 → customer.country = Brazil

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Brazil 均存在，完整DISTINCT与既有标准值索引一致。“巴西联邦共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Brazil。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Brazil；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=17
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-95ff10c443473368bada; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=749
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/) — section=页面标题、国名段及英/本国语国名; title=外交部：巴西国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-3cc0be84e1794908

- 分组：alias；划分：不适用

**审核对象：** 加拿大 → customer.country = Canada

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Canada 均存在，完整DISTINCT与既有标准值索引一致。“加拿大”由外交部国家概况的国名与页面名称支持，对应真实标准值 Canada。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Canada；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=18
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[5]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-f357d4a9aa3228c9d69b; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=750
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/bmz_679954/1206_680426/1206x0_680428/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/bmz_679954/1206_680426/1206x0_680428/) — section=页面标题、国名段及英/本国语国名; title=外交部：加拿大国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-b25098af9fa5b17a

- 分组：alias；划分：不适用

**审核对象：** 法国 → customer.country = France

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。“法国”由外交部国家概况的国名与页面名称支持，对应真实标准值 France。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 France；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=19
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[10]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-352185818871f006e648; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=755
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/](https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/) — section=页面标题、国名段及英/本国语国名; title=外交部：法国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-2ad4affe6af89ef4

- 分组：alias；划分：不适用

**审核对象：** 法兰西 → customer.country = France

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 customer.country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表独立支持“法兰西”这一国家用名，不能按“正式国名截短”猜出。法兰西也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "历史政体、民族/文化形容语与现代国家指称须区分。"
]

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 France；保留另一国家字段的独立口径。 历史/民族语境需澄清，不把历史国家自动改成现代值。

**仍需人工确认：**

确认支持该地区/历史用名，并限制于本快照国家语境。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=20
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[10]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-352185818871f006e648; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=755
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/](https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/) — section=页面标题、国名段及英/本国语国名; title=外交部：法国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4](https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4) — section=欧洲地区：法兰西、德意志、义大利各条目; title=教育部重编国语辞典：世界各国国名表及附图; supports=国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-ca229f69098da675

- 分组：alias；划分：不适用

**审核对象：** 法兰西共和国 → customer.country = France

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。“法兰西共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 France。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 France；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=21
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[10]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-352185818871f006e648; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=755
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/](https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/) — section=页面标题、国名段及英/本国语国名; title=外交部：法国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-e4d835eae26ef07e

- 分组：alias；划分：不适用

**审核对象：** 德国 → customer.country = Germany

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。“德国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Germany。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Germany；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=22
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[11]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5d7a3cd6809395578682; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=756
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/) — section=页面标题、国名段及英/本国语国名; title=外交部：德国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-9f5bb5a79e3b2818

- 分组：alias；划分：不适用

**审核对象：** 德意志 → customer.country = Germany

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 customer.country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表独立支持“德意志”这一国家用名，不能按“正式国名截短”猜出。德意志也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "历史政体、民族/文化形容语与现代国家指称须区分。"
]

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Germany；保留另一国家字段的独立口径。 历史/民族语境需澄清，不把历史国家自动改成现代值。

**仍需人工确认：**

确认支持该地区/历史用名，并限制于本快照国家语境。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=23
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[11]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5d7a3cd6809395578682; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=756
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/) — section=页面标题、国名段及英/本国语国名; title=外交部：德国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4](https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4) — section=欧洲地区：法兰西、德意志、义大利各条目; title=教育部重编国语辞典：世界各国国名表及附图; supports=国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-fc51077551e79ac3

- 分组：alias；划分：不适用

**审核对象：** 德意志联邦共和国 → customer.country = Germany

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。“德意志联邦共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Germany。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Germany；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=24
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[11]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5d7a3cd6809395578682; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=756
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/) — section=页面标题、国名段及英/本国语国名; title=外交部：德国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-94e30cebbc64041f

- 分组：alias；划分：不适用

**审核对象：** 印度 → customer.country = India

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 India 均存在，完整DISTINCT与既有标准值索引一致。“印度”由外交部国家概况的国名与页面名称支持，对应真实标准值 India。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 India；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=25
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[13]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ab913411df755fcf0331; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=758
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：印度国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-4aca00f05bc3cd6c

- 分组：alias；划分：不适用

**审核对象：** 印度共和国 → customer.country = India

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 India 均存在，完整DISTINCT与既有标准值索引一致。“印度共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 India。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 India；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=26
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[13]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ab913411df755fcf0331; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=758
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：印度国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-cbef6f7b472f48eb

- 分组：alias；划分：不适用

**审核对象：** 美国 → customer.country = USA

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。“美国”由外交部国家概况的国名与页面名称支持，对应真实标准值 USA。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 USA；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=27
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[22]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5d60ecf4270e9f86054a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=767
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：美国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-c43d08f9e0effe4d

- 分组：alias；划分：不适用

**审核对象：** 老美 → customer.country = USA

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 customer.country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。该口语词可以指美国人或以人员/政府借指美国；语言讨论支持俚语人员指称，外交部国名并不把它登记为标准国家名称。从“美国人”到所在地/账单国家不是等价关系：国籍、所在地、账单地址必须区分。只有用户明确用它表示国家地理筛选时，USA才可暂作候选。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "俚语人员/政府指称与国家地理实体不等价。",
  "可能把国籍意图误改为customer.country或invoice.billing_country。"
]

**建议处理方式：**

明确国别地理语境且所需字段为 customer.country 时才提议 USA；人员、国籍或政治指称应澄清，不直接生成字段过滤。

**仍需人工确认：**

确认俚语是否应纳入检索及其地理筛选约束，不能把语体偏好误作事实错误。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=28
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[22]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5d60ecf4270e9f86054a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=767
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：美国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://languagelog.ldc.upenn.edu/nll/?p=11626](https://languagelog.ldc.upenn.edu/nll/?p=11626) — section=关于老美/美国人的讨论段; title=Language Log：Laowai: the old furriner; supports=语言研究者讨论此词的俚语与人员指称；由该词推至国家是语境推断，不是地理字段的字面等价。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-fab280bc88aa1682

- 分组：alias；划分：不适用

**审核对象：** 美利坚合众国 → customer.country = USA

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。“美利坚合众国”由外交部国家概况的国名与页面名称支持，对应真实标准值 USA。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 USA；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=29
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[22]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5d60ecf4270e9f86054a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=767
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：美国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-9a9f0da60f84554c

- 分组：alias；划分：不适用

**审核对象：** 英国 → customer.country = United Kingdom

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。“英国”由外交部国家概况的国名与页面名称支持，对应真实标准值 United Kingdom。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=30
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[23]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ab0ca67796ef4a666592; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=768
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/) — section=页面标题、国名段及英/本国语国名; title=外交部：英国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-b507c7d7ee1c26e7

- 分组：alias；划分：不适用

**审核对象：** 联合王国 → customer.country = United Kingdom

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。剑桥中英词条直接支持此中文短名与 United Kingdom 对应；外交部全称提供完整国家对象，不会缩成英格兰。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=31
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[23]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ab0ca67796ef4a666592; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=768
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/) — section=页面标题、国名段及英/本国语国名; title=外交部：英国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dictionary.cambridge.org/zht/%E8%A9%9E%E5%85%B8/%E6%BC%A2%E8%AA%9E-%E7%B0%A1%E9%AB%94-%E8%8B%B1%E8%AA%9E/%E8%81%94%E5%90%88%E7%8E%8B%E5%9B%BD](https://dictionary.cambridge.org/zht/%E8%A9%9E%E5%85%B8/%E6%BC%A2%E8%AA%9E-%E7%B0%A1%E9%AB%94-%E8%8B%B1%E8%AA%9E/%E8%81%94%E5%90%88%E7%8E%8B%E5%9B%BD) — section=联合王国主词条; title=剑桥中文简体—英语辞典：联合王国; supports=中英词条直接支持 United Kingdom 的中文短名。; kind=external_source; access=搜索工具返回可读词条正文；open完整页返回 Internal Error; source_strength=primary

### alias:a-1f08c5b75168548d

- 分组：alias；划分：不适用

**审核对象：** 大不列颠及北爱尔兰联合王国 → customer.country = United Kingdom

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。“大不列颠及北爱尔兰联合王国”由外交部国家概况的国名与页面名称支持，对应真实标准值 United Kingdom。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=32
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[23]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ab0ca67796ef4a666592; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=768
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/) — section=页面标题、国名段及英/本国语国名; title=外交部：英国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-6f2b17a026a9ef9b

- 分组：alias；划分：不适用

**审核对象：** 古典 → genre.name = Classical

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 genre.name 字段与标准值 Classical 均存在，完整DISTINCT与既有标准值索引一致。“古典”有剑桥 classical/ classical music 音乐义支持，目标为真实流派 Classical。在已明确 genre.name 的查询中，省略“音乐”不会改成艺术家或年代；不将它限制为字典列举的某个作曲年代。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

音乐流派语境中可用于 Classical；艺术/建筑等其他古典义不得绑定。

**仍需人工确认：**

确认项目Classical分类使用范围，避免把语言词典时代定义当成数据库分类规则。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=33
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-e60d201656eb15032b4e; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1163
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical) — section=classical adjective (ART, MUSIC ETC); title=剑桥英汉辞典：classical; supports=词典支持古典义；结合数据库流派字段选取音乐义。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical-music](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical-music) — section=主词条; title=剑桥英汉辞典：classical-music; supports=词典支持 classical music 的中文音乐流派译法。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-fb76d9986e52aa10

- 分组：alias；划分：不适用

**审核对象：** 古典音乐 → genre.name = Classical

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 genre.name 字段与标准值 Classical 均存在，完整DISTINCT与既有标准值索引一致。“古典音乐”有剑桥 classical/ classical music 音乐义支持，目标为真实流派 Classical。在已明确 genre.name 的查询中，省略“音乐”不会改成艺术家或年代；不将它限制为字典列举的某个作曲年代。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

音乐流派语境中可用于 Classical；艺术/建筑等其他古典义不得绑定。

**仍需人工确认：**

确认项目Classical分类使用范围，避免把语言词典时代定义当成数据库分类规则。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=34
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-e60d201656eb15032b4e; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1163
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical) — section=classical adjective (ART, MUSIC ETC); title=剑桥英汉辞典：classical; supports=词典支持古典义；结合数据库流派字段选取音乐义。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical-music](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical-music) — section=主词条; title=剑桥英汉辞典：classical-music; supports=词典支持 classical music 的中文音乐流派译法。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-ae481372f2653475

- 分组：alias；划分：不适用

**审核对象：** 爵士 → genre.name = Jazz

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 genre.name 字段与标准值 Jazz 均存在，完整DISTINCT与既有标准值索引一致。词典的音乐义支持“爵士”与 Jazz 对应；真实库有Jazz。省略“乐”可在音乐流派语境成立，不能把爵位称号或品牌等非音乐义当作genre过滤。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

genre明确时可用Jazz；若“爵士”指人名/爵位/品牌则澄清。

**仍需人工确认：**

确认只接受音乐流派语境。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=35
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[11]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5394ef0bac37e993f465; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1170
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/jazz](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/jazz) — section=jazz noun [U] 音乐义; title=剑桥英汉辞典：jazz; supports=词典支持爵士音乐义，也列出非音乐品牌义；须限 genre.name。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-f3ab57aac4760fac

- 分组：alias；划分：不适用

**审核对象：** 爵士乐 → genre.name = Jazz

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 genre.name 字段与标准值 Jazz 均存在，完整DISTINCT与既有标准值索引一致。词典的音乐义支持“爵士乐”与 Jazz 对应；真实库有Jazz。省略“乐”可在音乐流派语境成立，不能把爵位称号或品牌等非音乐义当作genre过滤。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

genre明确时可用Jazz；若“爵士”指人名/爵位/品牌则澄清。

**仍需人工确认：**

确认只接受音乐流派语境。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=36
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[11]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5394ef0bac37e993f465; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1170
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/jazz](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/jazz) — section=jazz noun [U] 音乐义; title=剑桥英汉辞典：jazz; supports=词典支持爵士音乐义，也列出非音乐品牌义；须限 genre.name。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-439ce0734774f114

- 分组：alias；划分：不适用

**审核对象：** 金属 → genre.name = Metal

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 genre.name 字段与标准值 Metal 均存在，完整DISTINCT与既有标准值索引一致。“金属”在音乐上下文可表达Metal，字典有metal音乐义和对应金属音乐术语；但真实genre同时有Metal和Heavy Metal，词典还把两者列为一般语言同义。因此能作Metal候选不代表数据库分类可合并或唯一绑定。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "真实数据库Metal与Heavy Metal是不同标准分类，泛称可能覆盖两者。",
  "同一裸词在待审CSV还候选artist.name=Metallica，且另有材料义。"
]

**建议处理方式：**

明确用户指数据库Metal分类时选Metal；泛称金属音乐时展示Metal/Heavy Metal范围并澄清；艺人语境保留独立候选。

**仍需人工确认：**

确定泛称金属音乐的业务范围；多候选许可不是自动将标准值合并或唯一绑定。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=37
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[13]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-bf1c51869eccaa9deddc; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1172
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul](https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul) — section=metal noun (MUSIC)及Synonym; title=剑桥英语辞典：metal; supports=辞典列出音乐义并将 heavy metal 视作同义词，支持真实分类间的语义歧义检查。; kind=external_source; access=搜索工具返回可读词条正文; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/heavy-metal](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/heavy-metal) — section=heavy metal noun (MUSIC); title=剑桥英汉辞典：heavy-metal; supports=词典支持重金属音乐义；此值与数据库 Metal 类别同列并存。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-f637ff312a6fead6

- 分组：alias；划分：不适用

**审核对象：** 金属乐 → genre.name = Metal

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 genre.name 字段与标准值 Metal 均存在，完整DISTINCT与既有标准值索引一致。“金属乐”在音乐上下文可表达Metal，字典有metal音乐义和对应金属音乐术语；但真实genre同时有Metal和Heavy Metal，词典还把两者列为一般语言同义。因此能作Metal候选不代表数据库分类可合并或唯一绑定。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "真实数据库Metal与Heavy Metal是不同标准分类，泛称可能覆盖两者。"
]

**建议处理方式：**

明确用户指数据库Metal分类时选Metal；泛称金属音乐时展示Metal/Heavy Metal范围并澄清；艺人语境保留独立候选。

**仍需人工确认：**

确定泛称金属音乐的业务范围；多候选许可不是自动将标准值合并或唯一绑定。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=38
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[13]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-bf1c51869eccaa9deddc; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1172
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul](https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul) — section=metal noun (MUSIC)及Synonym; title=剑桥英语辞典：metal; supports=辞典列出音乐义并将 heavy metal 视作同义词，支持真实分类间的语义歧义检查。; kind=external_source; access=搜索工具返回可读词条正文; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/heavy-metal](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/heavy-metal) — section=heavy metal noun (MUSIC); title=剑桥英汉辞典：heavy-metal; supports=词典支持重金属音乐义；此值与数据库 Metal 类别同列并存。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-10514461292c596d

- 分组：alias；划分：不适用

**审核对象：** 流行 → genre.name = Pop

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 genre.name 字段与标准值 Pop 均存在，完整DISTINCT与既有标准值索引一致。剑桥 Pop 的音乐义支持“流行”；标准对象真实存在。中文“流行”还可表示受欢迎程度，“最流行的曲目”不是genre=Pop的同义改写，必须识别这是分类请求。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "流派短名与受欢迎程度形容词多义。"
]

**建议处理方式：**

明确请求Pop流派时可用；热度/销量/流行程度比较不自动改成Pop过滤。

**仍需人工确认：**

确认分类语义与流行程度指标分开处理。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=39
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[15]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-d458c8175a18de796e8c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1174
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/pop](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/pop) — section=pop noun (MUSIC); title=剑桥英汉辞典：pop; supports=词典支持 Pop 的音乐义，不能把普通形容词“流行”当作热度排序指标。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-34701ceea8df41eb

- 分组：alias；划分：不适用

**审核对象：** 流行音乐 → genre.name = Pop

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 genre.name 字段与标准值 Pop 均存在，完整DISTINCT与既有标准值索引一致。剑桥 Pop 的音乐义支持“流行音乐”；标准对象真实存在。中文“流行”还可表示受欢迎程度，“最流行的曲目”不是genre=Pop的同义改写，必须识别这是分类请求。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

明确请求Pop流派时可用；热度/销量/流行程度比较不自动改成Pop过滤。

**仍需人工确认：**

确认分类语义与流行程度指标分开处理。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=40
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[15]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-d458c8175a18de796e8c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1174
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/pop](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/pop) — section=pop noun (MUSIC); title=剑桥英汉辞典：pop; supports=词典支持 Pop 的音乐义，不能把普通形容词“流行”当作热度排序指标。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-cb69b4bf22161e6e

- 分组：alias；划分：不适用

**审核对象：** 摇滚 → genre.name = Rock

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 genre.name 字段与标准值 Rock 均存在，完整DISTINCT与既有标准值索引一致。独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“摇滚”可表达 Rock，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "同字段同中文词形存在Rock/Rock And Roll两候选。"
]

**建议处理方式：**

保留 Rock 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。

**仍需人工确认：**

确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=41
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[18]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5abaeb142337ce5b27ed; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1177
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock) — section=rock noun (MUSIC); title=剑桥英汉辞典：rock; supports=词典支持 Rock 的中文音乐义。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll) — section=主词条音乐义; title=剑桥英汉辞典：rock-and-roll; supports=词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。; kind=external_source; access=搜索工具返回可读词条正文；Rock And Roll完整页open为403; source_strength=primary

### alias:a-5972cabfe64bae77

- 分组：alias；划分：不适用

**审核对象：** 摇滚乐 → genre.name = Rock

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 genre.name 字段与标准值 Rock 均存在，完整DISTINCT与既有标准值索引一致。独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“摇滚乐”可表达 Rock，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "同字段同中文词形存在Rock/Rock And Roll两候选。"
]

**建议处理方式：**

保留 Rock 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。

**仍需人工确认：**

确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=42
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[18]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-5abaeb142337ce5b27ed; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1177
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock) — section=rock noun (MUSIC); title=剑桥英汉辞典：rock; supports=词典支持 Rock 的中文音乐义。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll) — section=主词条音乐义; title=剑桥英汉辞典：rock-and-roll; supports=词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。; kind=external_source; access=搜索工具返回可读词条正文；Rock And Roll完整页open为403; source_strength=primary

### alias:a-0e44ca874f4ba96f

- 分组：alias；划分：不适用

**审核对象：** 摇滚乐 → genre.name = Rock And Roll

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 genre.name 字段与标准值 Rock And Roll 均存在，完整DISTINCT与既有标准值索引一致。独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“摇滚乐”可表达 Rock And Roll，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "同字段同中文词形存在Rock/Rock And Roll两候选。"
]

**建议处理方式：**

保留 Rock And Roll 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。

**仍需人工确认：**

确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=43
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[19]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-10facd793602b59518e7; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1178
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock) — section=rock noun (MUSIC); title=剑桥英汉辞典：rock; supports=词典支持 Rock 的中文音乐义。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll) — section=主词条音乐义; title=剑桥英汉辞典：rock-and-roll; supports=词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。; kind=external_source; access=搜索工具返回可读词条正文；Rock And Roll完整页open为403; source_strength=primary

### alias:a-c748b229db869a4e

- 分组：alias；划分：不适用

**审核对象：** 节奏摇滚 → genre.name = Rock And Roll

**别名或参考答案判断：** 证据不足

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

证据不足

**参考判断理由：**

实查 genre.name 字段与标准值 Rock And Roll 均存在，完整DISTINCT与既有标准值索引一致。目标 Rock And Roll 在真实库存在，但已读本地字典仅说明流派字段，没有给出“节奏摇滚”译名。独立英汉词条支持一般摇滚译法，未支持加入“节奏”后能专指这一数据库分类；本轮检索没有取得该译名的可信来源。不能因为它能人为避开Rock歧义就认定翻译正确，也不能用未搜到断言该词绝不存在。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "没有独立来源证明“节奏摇滚”专指Rock And Roll。",
  "加入“节奏”的意图可能只是人为区分类别，非真实译名依据。"
]

**建议处理方式：**

暂不启用该译名；补充可信音乐术语来源或明确人审定义后再评估，保留Rock/Rock And Roll本来的分类差异。

**仍需人工确认：**

补证据并确认术语；不要仅依照既有“拒绝”建议盖章。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=44
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[19]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-10facd793602b59518e7; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1178
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock) — section=rock noun (MUSIC); title=剑桥英汉辞典：rock; supports=词典支持 Rock 的中文音乐义。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll) — section=主词条音乐义; title=剑桥英汉辞典：rock-and-roll; supports=词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。; kind=external_source; access=搜索工具返回可读词条正文；Rock And Roll完整页open为403; source_strength=primary

### alias:a-4c5e26e87ffb2aa2

- 分组：alias；划分：不适用

**审核对象：** 澳大利亚 → invoice.billing_country = Australia

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。“澳大利亚”由外交部国家概况的国名与页面名称支持，对应真实标准值 Australia。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Australia；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=45
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[1]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-30a35165311e0978a54c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1297
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/) — section=页面标题、国名段及英/本国语国名; title=外交部：澳大利亚国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-b5ca3e94894dee8d

- 分组：alias；划分：不适用

**审核对象：** 澳洲 → invoice.billing_country = Australia

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。教育部译名索引直接将“澳洲”与 Australia 对应，国家用法有独立依据。该词在用户表达中也可能作大陆/广域地区用语；不能仅因当前国家库无洲级值就把地区意图压成一个国家。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "国家简称与大陆/广域地区意图可能混淆。"
]

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Australia；保留另一国家字段的独立口径。 用户谈大陆、洲或多个国家时先澄清范围。

**仍需人工确认：**

确认本项目接受该地区用名，并规定国别/洲别澄清方式。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=46
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[1]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-30a35165311e0978a54c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1297
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/) — section=页面标题、国名段及英/本国语国名; title=外交部：澳大利亚国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dict.revised.moe.edu.tw/appendix.jsp?ID=28&la=1&page=14&powerMode=0&ver=4](https://dict.revised.moe.edu.tw/appendix.jsp?ID=28&la=1&page=14&powerMode=0&ver=4) — section=澳洲—Australia条目; title=教育部重编国语辞典：西文译名索引表; supports=辞典索引将“澳洲”与 Australia 对应；未证明一切大陆/洲语境都能作国家筛选。; kind=external_source; access=搜索工具返回可读索引节选; source_strength=primary

### alias:a-f2ecb45e404feda1

- 分组：alias；划分：不适用

**审核对象：** 澳大利亚联邦 → invoice.billing_country = Australia

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。“澳大利亚联邦”由外交部国家概况的国名与页面名称支持，对应真实标准值 Australia。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Australia；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=47
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[1]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-30a35165311e0978a54c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1297
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/) — section=页面标题、国名段及英/本国语国名; title=外交部：澳大利亚国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-bfc3cf35431dcceb

- 分组：alias；划分：不适用

**审核对象：** 巴西 → invoice.billing_country = Brazil

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Brazil 均存在，完整DISTINCT与既有标准值索引一致。“巴西”由外交部国家概况的国名与页面名称支持，对应真实标准值 Brazil。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Brazil；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=48
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-035a5fa9bd5fc4b4175e; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1300
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/) — section=页面标题、国名段及英/本国语国名; title=外交部：巴西国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-e8e5e4fe2d99ff1b

- 分组：alias；划分：不适用

**审核对象：** 巴西联邦共和国 → invoice.billing_country = Brazil

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Brazil 均存在，完整DISTINCT与既有标准值索引一致。“巴西联邦共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Brazil。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Brazil；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=49
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-035a5fa9bd5fc4b4175e; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1300
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/) — section=页面标题、国名段及英/本国语国名; title=外交部：巴西国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-b33ce127772f748d

- 分组：alias；划分：不适用

**审核对象：** 加拿大 → invoice.billing_country = Canada

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Canada 均存在，完整DISTINCT与既有标准值索引一致。“加拿大”由外交部国家概况的国名与页面名称支持，对应真实标准值 Canada。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Canada；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=50
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[5]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ed13ace46d49a0165890; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1301
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/bmz_679954/1206_680426/1206x0_680428/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/bmz_679954/1206_680426/1206x0_680428/) — section=页面标题、国名段及英/本国语国名; title=外交部：加拿大国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-1146eff0ef203810

- 分组：alias；划分：不适用

**审核对象：** 法国 → invoice.billing_country = France

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。“法国”由外交部国家概况的国名与页面名称支持，对应真实标准值 France。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 France；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=51
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[10]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-da1995626f6b421035ba; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1306
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/](https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/) — section=页面标题、国名段及英/本国语国名; title=外交部：法国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-9eb72fa09563fb7e

- 分组：alias；划分：不适用

**审核对象：** 法兰西 → invoice.billing_country = France

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表独立支持“法兰西”这一国家用名，不能按“正式国名截短”猜出。法兰西也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "历史政体、民族/文化形容语与现代国家指称须区分。"
]

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 France；保留另一国家字段的独立口径。 历史/民族语境需澄清，不把历史国家自动改成现代值。

**仍需人工确认：**

确认支持该地区/历史用名，并限制于本快照国家语境。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=52
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[10]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-da1995626f6b421035ba; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1306
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/](https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/) — section=页面标题、国名段及英/本国语国名; title=外交部：法国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4](https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4) — section=欧洲地区：法兰西、德意志、义大利各条目; title=教育部重编国语辞典：世界各国国名表及附图; supports=国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-99f7789e108299a0

- 分组：alias；划分：不适用

**审核对象：** 法兰西共和国 → invoice.billing_country = France

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。“法兰西共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 France。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 France；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=53
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[10]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-da1995626f6b421035ba; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1306
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/](https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/) — section=页面标题、国名段及英/本国语国名; title=外交部：法国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-3414db81951a6279

- 分组：alias；划分：不适用

**审核对象：** 德国 → invoice.billing_country = Germany

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。“德国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Germany。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Germany；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=54
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[11]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-475210ef4e08328852ec; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1307
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/) — section=页面标题、国名段及英/本国语国名; title=外交部：德国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-604796b76eb1cd3b

- 分组：alias；划分：不适用

**审核对象：** 德意志 → invoice.billing_country = Germany

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表独立支持“德意志”这一国家用名，不能按“正式国名截短”猜出。德意志也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "历史政体、民族/文化形容语与现代国家指称须区分。"
]

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Germany；保留另一国家字段的独立口径。 历史/民族语境需澄清，不把历史国家自动改成现代值。

**仍需人工确认：**

确认支持该地区/历史用名，并限制于本快照国家语境。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=55
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[11]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-475210ef4e08328852ec; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1307
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/) — section=页面标题、国名段及英/本国语国名; title=外交部：德国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4](https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4) — section=欧洲地区：法兰西、德意志、义大利各条目; title=教育部重编国语辞典：世界各国国名表及附图; supports=国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-43165309220a1f56

- 分组：alias；划分：不适用

**审核对象：** 德意志联邦共和国 → invoice.billing_country = Germany

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。“德意志联邦共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Germany。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Germany；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=56
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[11]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-475210ef4e08328852ec; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1307
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/](https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/) — section=页面标题、国名段及英/本国语国名; title=外交部：德国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-9c79948752527793

- 分组：alias；划分：不适用

**审核对象：** 印度 → invoice.billing_country = India

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 India 均存在，完整DISTINCT与既有标准值索引一致。“印度”由外交部国家概况的国名与页面名称支持，对应真实标准值 India。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 India；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=57
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[13]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-989037d188e20fe3ee6c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1309
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：印度国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-5819628db78075fb

- 分组：alias；划分：不适用

**审核对象：** 印度共和国 → invoice.billing_country = India

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 India 均存在，完整DISTINCT与既有标准值索引一致。“印度共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 India。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 India；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=58
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[13]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-989037d188e20fe3ee6c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1309
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：印度国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-dca9d898c8a31e37

- 分组：alias；划分：不适用

**审核对象：** 美国 → invoice.billing_country = USA

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。“美国”由外交部国家概况的国名与页面名称支持，对应真实标准值 USA。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 USA；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=59
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[22]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ab7ca55351c9f4bae96b; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1318
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：美国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-9d6edadfda3e46a9

- 分组：alias；划分：不适用

**审核对象：** 老美 → invoice.billing_country = USA

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。该口语词可以指美国人或以人员/政府借指美国；语言讨论支持俚语人员指称，外交部国名并不把它登记为标准国家名称。从“美国人”到所在地/账单国家不是等价关系：国籍、所在地、账单地址必须区分。只有用户明确用它表示国家地理筛选时，USA才可暂作候选。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "俚语人员/政府指称与国家地理实体不等价。",
  "可能把国籍意图误改为customer.country或invoice.billing_country。"
]

**建议处理方式：**

明确国别地理语境且所需字段为 invoice.billing_country 时才提议 USA；人员、国籍或政治指称应澄清，不直接生成字段过滤。

**仍需人工确认：**

确认俚语是否应纳入检索及其地理筛选约束，不能把语体偏好误作事实错误。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=60
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[22]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ab7ca55351c9f4bae96b; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1318
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：美国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://languagelog.ldc.upenn.edu/nll/?p=11626](https://languagelog.ldc.upenn.edu/nll/?p=11626) — section=关于老美/美国人的讨论段; title=Language Log：Laowai: the old furriner; supports=语言研究者讨论此词的俚语与人员指称；由该词推至国家是语境推断，不是地理字段的字面等价。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-6d34332b7a54aaa8

- 分组：alias；划分：不适用

**审核对象：** 美利坚合众国 → invoice.billing_country = USA

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。“美利坚合众国”由外交部国家概况的国名与页面名称支持，对应真实标准值 USA。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 USA；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=61
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[22]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ab7ca55351c9f4bae96b; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1318
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml](https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml) — section=页面标题、国名段及英/本国语国名; title=外交部：美国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-a51a0dfa5111c6b0

- 分组：alias；划分：不适用

**审核对象：** 英国 → invoice.billing_country = United Kingdom

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。“英国”由外交部国家概况的国名与页面名称支持，对应真实标准值 United Kingdom。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=62
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[23]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-9b20c6c3e4caad1de69a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1319
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/) — section=页面标题、国名段及英/本国语国名; title=外交部：英国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-7528c8542cbf31a0

- 分组：alias；划分：不适用

**审核对象：** 联合王国 → invoice.billing_country = United Kingdom

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。剑桥中英词条直接支持此中文短名与 United Kingdom 对应；外交部全称提供完整国家对象，不会缩成英格兰。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=63
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[23]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-9b20c6c3e4caad1de69a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1319
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/) — section=页面标题、国名段及英/本国语国名; title=外交部：英国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dictionary.cambridge.org/zht/%E8%A9%9E%E5%85%B8/%E6%BC%A2%E8%AA%9E-%E7%B0%A1%E9%AB%94-%E8%8B%B1%E8%AA%9E/%E8%81%94%E5%90%88%E7%8E%8B%E5%9B%BD](https://dictionary.cambridge.org/zht/%E8%A9%9E%E5%85%B8/%E6%BC%A2%E8%AA%9E-%E7%B0%A1%E9%AB%94-%E8%8B%B1%E8%AA%9E/%E8%81%94%E5%90%88%E7%8E%8B%E5%9B%BD) — section=联合王国主词条; title=剑桥中文简体—英语辞典：联合王国; supports=中英词条直接支持 United Kingdom 的中文短名。; kind=external_source; access=搜索工具返回可读词条正文；open完整页返回 Internal Error; source_strength=primary

### alias:a-8fd10b20a82508de

- 分组：alias；划分：不适用

**审核对象：** 大不列颠及北爱尔兰联合王国 → invoice.billing_country = United Kingdom

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。“大不列颠及北爱尔兰联合王国”由外交部国家概况的国名与页面名称支持，对应真实标准值 United Kingdom。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=64
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[23]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-9b20c6c3e4caad1de69a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1319
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/) — section=页面标题、国名段及英/本国语国名; title=外交部：英国国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-6799bc523f9e8693

- 分组：alias；划分：不适用

**审核对象：** AAC音频文件 → media_type.name = AAC audio file

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 media_type.name 字段与标准值 AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“AAC音频文件”保留AAC与audio的普通译义，未带Protected/Purchased修饰，适合作为数据库普通AAC类别的译名候选。但真实media_type还有Protected AAC与Purchased AAC；用户泛称AAC音频/文件可能指格式家族，不能自动只筛普通AAC。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "AAC格式泛称可能覆盖普通、Protected、Purchased三个真实枚举值。"
]

**建议处理方式：**

用户明确普通AAC类别时选AAC audio file；泛问AAC格式先澄清是否包含三个AAC类别。

**仍需人工确认：**

确认“普通类别”与“AAC格式总范围”的区别，禁止把父类说法直接绑定单个子类。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=65
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[0]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-48a78d9abfb7317315e9; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1400
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-7b241be59eef3bbb

- 分组：alias；划分：不适用

**审核对象：** AAC音频 → media_type.name = AAC audio file

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 media_type.name 字段与标准值 AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“AAC音频”保留AAC与audio的普通译义，未带Protected/Purchased修饰，适合作为数据库普通AAC类别的译名候选。但真实media_type还有Protected AAC与Purchased AAC；用户泛称AAC音频/文件可能指格式家族，不能自动只筛普通AAC。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "AAC格式泛称可能覆盖普通、Protected、Purchased三个真实枚举值。"
]

**建议处理方式：**

用户明确普通AAC类别时选AAC audio file；泛问AAC格式先澄清是否包含三个AAC类别。

**仍需人工确认：**

确认“普通类别”与“AAC格式总范围”的区别，禁止把父类说法直接绑定单个子类。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=66
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[0]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-48a78d9abfb7317315e9; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1400
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-623dcb996bdf111b

- 分组：alias；划分：不适用

**审核对象：** MPEG音频文件 → media_type.name = MPEG audio file

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 media_type.name 字段与标准值 MPEG audio file 均存在，完整DISTINCT与既有标准值索引一致。“MPEG音频文件”保持MPEG格式缩写及audio音频类型，中文组合翻译不涉及缩写展开。真实库另有Protected MPEG-4 video file，但其中video与本行audio不同；不能仅匹配MPEG词段忽略音频/视频限定。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

media_type字段和音频语境明确时可用该枚举；省略音频只说MPEG时重新澄清，不延伸本别名。

**仍需人工确认：**

确认保留音频限定，避免MPEG音频与MPEG-4视频的词段匹配冲突。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=67
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[1]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-e30ed9ffef5d9f1c3079; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1401
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-283ad9fbc2d748a9

- 分组：alias；划分：不适用

**审核对象：** MPEG音频 → media_type.name = MPEG audio file

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 media_type.name 字段与标准值 MPEG audio file 均存在，完整DISTINCT与既有标准值索引一致。“MPEG音频”保持MPEG格式缩写及audio音频类型，中文组合翻译不涉及缩写展开。真实库另有Protected MPEG-4 video file，但其中video与本行audio不同；不能仅匹配MPEG词段忽略音频/视频限定。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

media_type字段和音频语境明确时可用该枚举；省略音频只说MPEG时重新澄清，不延伸本别名。

**仍需人工确认：**

确认保留音频限定，避免MPEG音频与MPEG-4视频的词段匹配冲突。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=68
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[1]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-e30ed9ffef5d9f1c3079; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1401
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-bfc4b2a75ae6d393

- 分组：alias；划分：不适用

**审核对象：** 受保护AAC音频文件 → media_type.name = Protected AAC audio file

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 media_type.name 字段与标准值 Protected AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“受保护AAC音频文件”保留标准名称 Protected AAC audio file 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

媒体类型字段明确时可用；精确映射 Protected AAC audio file 并保留Protected，不能推断保护机制或客户付款状态。

**仍需人工确认：**

确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=69
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[2]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-df2c0ee6493160aa791a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1402
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected) — section=一般形容词义; title=剑桥英汉辞典：protected; supports=词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-e6995d2d188f2d9e

- 分组：alias；划分：不适用

**审核对象：** 受保护AAC音频 → media_type.name = Protected AAC audio file

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 media_type.name 字段与标准值 Protected AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“受保护AAC音频”保留标准名称 Protected AAC audio file 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

媒体类型字段明确时可用；精确映射 Protected AAC audio file 并保留Protected，不能推断保护机制或客户付款状态。

**仍需人工确认：**

确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=70
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[2]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-df2c0ee6493160aa791a; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1402
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected) — section=一般形容词义; title=剑桥英汉辞典：protected; supports=词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-f1475c651575231c

- 分组：alias；划分：不适用

**审核对象：** 受保护MPEG-4视频文件 → media_type.name = Protected MPEG-4 video file

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 media_type.name 字段与标准值 Protected MPEG-4 video file 均存在，完整DISTINCT与既有标准值索引一致。“受保护MPEG-4视频文件”保留标准名称 Protected MPEG-4 video file 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

媒体类型字段明确时可用；精确映射 Protected MPEG-4 video file 并保留Protected，不能推断保护机制或客户付款状态。

**仍需人工确认：**

确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=71
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[3]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-063294056fde53d4a70e; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1403
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected) — section=一般形容词义; title=剑桥英汉辞典：protected; supports=词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-546993461dc3354d

- 分组：alias；划分：不适用

**审核对象：** 受保护MPEG-4视频 → media_type.name = Protected MPEG-4 video file

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 media_type.name 字段与标准值 Protected MPEG-4 video file 均存在，完整DISTINCT与既有标准值索引一致。“受保护MPEG-4视频”保留标准名称 Protected MPEG-4 video file 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

媒体类型字段明确时可用；精确映射 Protected MPEG-4 video file 并保留Protected，不能推断保护机制或客户付款状态。

**仍需人工确认：**

确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=72
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[3]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-063294056fde53d4a70e; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1403
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected) — section=一般形容词义; title=剑桥英汉辞典：protected; supports=词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-4fbad68319f9e10e

- 分组：alias；划分：不适用

**审核对象：** 已购买AAC音频文件 → media_type.name = Purchased AAC audio file

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 media_type.name 字段与标准值 Purchased AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“已购买AAC音频文件”对应标准 Purchased AAC audio file 的中文组合，保留购买相关修饰与AAC音频。Purchased在此是真实媒体类型名称，不是“某客户已成功付款”的数据库事实；不能用media_type替代invoice或支付状态。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

只按媒体类型枚举 Purchased AAC audio file 使用；客户购买行为需销售关联与业务口径，付款状态无本字段证据。

**仍需人工确认：**

确认Purchased命名翻译及媒体类型/购买行为/支付状态边界。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=73
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-d0ff7c80f8657fcfd77c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1404
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase) — section=purchase verb / noun (BUYING); title=剑桥英汉辞典：purchase; supports=词典支持购买语义；Purchased 的完成态中文表达为AI语法组合判断。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-0c3df10756626f4a

- 分组：alias；划分：不适用

**审核对象：** 购买AAC音频文件 → media_type.name = Purchased AAC audio file

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 media_type.name 字段与标准值 Purchased AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“购买AAC音频文件”对应标准 Purchased AAC audio file 的中文组合，保留购买相关修饰与AAC音频。Purchased在此是真实媒体类型名称，不是“某客户已成功付款”的数据库事实；不能用media_type替代invoice或支付状态。该词形未明确完成态，还可能是“购买一个AAC文件”的动作请求；必须先确认是在问类型标签。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "未标“已”，类型标签与购买动作请求多义。"
]

**建议处理方式：**

只按媒体类型枚举 Purchased AAC audio file 使用；客户购买行为需销售关联与业务口径，付款状态无本字段证据。 若为购买行为或动作请求，先澄清，不据该词形唯一选择Purchased类型。

**仍需人工确认：**

确认Purchased命名翻译及媒体类型/购买行为/支付状态边界。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=74
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-d0ff7c80f8657fcfd77c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1404
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase) — section=purchase verb / noun (BUYING); title=剑桥英汉辞典：purchase; supports=词典支持购买语义；Purchased 的完成态中文表达为AI语法组合判断。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-a974e81df263a782

- 分组：alias；划分：不适用

**审核对象：** 已购买AAC音频 → media_type.name = Purchased AAC audio file

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 media_type.name 字段与标准值 Purchased AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“已购买AAC音频”对应标准 Purchased AAC audio file 的中文组合，保留购买相关修饰与AAC音频。Purchased在此是真实媒体类型名称，不是“某客户已成功付款”的数据库事实；不能用media_type替代invoice或支付状态。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

只按媒体类型枚举 Purchased AAC audio file 使用；客户购买行为需销售关联与业务口径，付款状态无本字段证据。

**仍需人工确认：**

确认Purchased命名翻译及媒体类型/购买行为/支付状态边界。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=75
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[media_type].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=545
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 media_type.name; $.text_values["media_type.name"].values[4]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-d0ff7c80f8657fcfd77c; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1404
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### media_type; supports=字典中的字段范围说明; kind=local_material; line=131
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio) — section=audio adjective / audio noun; title=剑桥英汉辞典：audio; supports=词典支持音频用语；格式缩写保持数据库原词形。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase) — section=purchase verb / noun (BUYING); title=剑桥英汉辞典：purchase; supports=词典支持购买语义；Purchased 的完成态中文表达为AI语法组合判断。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary

### alias:a-d0e9fad30baaded8

- 分组：alias；划分：不适用

**审核对象：** 意大利 → customer.country = Italy

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。“意大利”由外交部国家概况的国名与页面名称支持，对应真实标准值 Italy。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=76
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[15]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ec3f5c892a21c72c35e1; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=760
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/) — section=页面标题、国名段及英/本国语国名; title=外交部：意大利国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-97a541d02a9d6f5b

- 分组：alias；划分：不适用

**审核对象：** 义大利 → customer.country = Italy

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 customer.country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表使用繁体“義大利”并对应意大利国家，地域译名有独立依据；本别名转为简体“义大利”是通常字形转换。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=77
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[15]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ec3f5c892a21c72c35e1; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=760
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/) — section=页面标题、国名段及英/本国语国名; title=外交部：意大利国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4](https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4) — section=欧洲地区：法兰西、德意志、义大利各条目; title=教育部重编国语辞典：世界各国国名表及附图; supports=国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-a653ead69db804b0

- 分组：alias；划分：不适用

**审核对象：** 意国 → customer.country = Italy

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 customer.country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。日本国立国会图书馆参考库的中文国名答复明确列出该简称，不能仅因它少见就判断为错。材料未证明本项目用户高频使用，短词也需限定国家语境；作为保守候选比直接唯一匹配合适。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "简称来源属于图书馆参考答复；本项目真实用法和频率未提供。"
]

**建议处理方式：**

先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

**仍需人工确认：**

确认目标用户地域/语体是否需要此简称；没有真实用例也不自动扩大映射范围。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=78
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[customer].columns[country]; supports=实际目录中的字段与业务含义; kind=local_material; line=131
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 customer.country; $.text_values["customer.country"].values[15]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-ec3f5c892a21c72c35e1; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=760
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### customer; supports=字典中的字段范围说明; kind=local_material; line=42
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/) — section=页面标题、国名段及英/本国语国名; title=外交部：意大利国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://crd.ndl.go.jp/reference/entry/reference/show?asc=desc&fi=5_%E7%A4%BE%E4%BC%9A%E4%BA%BA+8_22+3_%E6%96%87%E7%8C%AE%E7%B4%B9%E4%BB%8B&id=1000203470&lsmp=1&mcmd=25&page=ref_view&rnk=1&st=ref_cnt_all](https://crd.ndl.go.jp/reference/entry/reference/show?asc=desc&fi=5_%E7%A4%BE%E4%BC%9A%E4%BA%BA+8_22+3_%E6%96%87%E7%8C%AE%E7%B4%B9%E4%BB%8B&id=1000203470&lsmp=1&mcmd=25&page=ref_view&rnk=1&st=ref_cnt_all) — section=回答第85–87行：中国语表记; title=日本国立国会图书馆参考协同数据库：主要国家汉字表记; supports=图书馆参考答复列出意大利中文国名的该简称；未证明中国大陆当代查询中的频率。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-97f75d30b3bcab32

- 分组：alias；划分：不适用

**审核对象：** 意大利 → invoice.billing_country = Italy

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。“意大利”由外交部国家概况的国名与页面名称支持，对应真实标准值 Italy。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=79
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[15]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-f00a4dabb94dd7295e40; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1311
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/) — section=页面标题、国名段及英/本国语国名; title=外交部：意大利国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-477276f0186e7f07

- 分组：alias；划分：不适用

**审核对象：** 义大利 → invoice.billing_country = Italy

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

建议直接使用

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表使用繁体“義大利”并对应意大利国家，地域译名有独立依据；本别名转为简体“义大利”是通常字形转换。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

**仍需人工确认：**

确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=80
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[15]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-f00a4dabb94dd7295e40; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1311
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/) — section=页面标题、国名段及英/本国语国名; title=外交部：意大利国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4](https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4) — section=欧洲地区：法兰西、德意志、义大利各条目; title=教育部重编国语辞典：世界各国国名表及附图; supports=国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-14625e480dd8676e

- 分组：alias；划分：不适用

**审核对象：** 意国 → invoice.billing_country = Italy

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 invoice.billing_country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。日本国立国会图书馆参考库的中文国名答复明确列出该简称，不能仅因它少见就判断为错。材料未证明本项目用户高频使用，短词也需限定国家语境；作为保守候选比直接唯一匹配合适。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "简称来源属于图书馆参考答复；本项目真实用法和频率未提供。"
]

**建议处理方式：**

先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

**仍需人工确认：**

确认目标用户地域/语体是否需要此简称；没有真实用例也不自动扩大映射范围。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=81
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[invoice].columns[billing_country]; supports=实际目录中的字段与业务含义; kind=local_material; line=418
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[15]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-f00a4dabb94dd7295e40; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1311
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### invoice; supports=字典中的字段范围说明; kind=local_material; line=99
- [https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/](https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/) — section=页面标题、国名段及英/本国语国名; title=外交部：意大利国家概况; supports=官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary
- [https://crd.ndl.go.jp/reference/entry/reference/show?asc=desc&fi=5_%E7%A4%BE%E4%BC%9A%E4%BA%BA+8_22+3_%E6%96%87%E7%8C%AE%E7%B4%B9%E4%BB%8B&id=1000203470&lsmp=1&mcmd=25&page=ref_view&rnk=1&st=ref_cnt_all](https://crd.ndl.go.jp/reference/entry/reference/show?asc=desc&fi=5_%E7%A4%BE%E4%BC%9A%E4%BA%BA+8_22+3_%E6%96%87%E7%8C%AE%E7%B4%B9%E4%BB%8B&id=1000203470&lsmp=1&mcmd=25&page=ref_view&rnk=1&st=ref_cnt_all) — section=回答第85–87行：中国语表记; title=日本国立国会图书馆参考协同数据库：主要国家汉字表记; supports=图书馆参考答复列出意大利中文国名的该简称；未证明中国大陆当代查询中的频率。; kind=external_source; access=浏览工具已返回可读正文; source_strength=primary

### alias:a-d2-plan-rock-and-roll

- 分组：alias；划分：不适用

**审核对象：** 摇滚 → genre.name = Rock And Roll

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 不适用（别名配置审核，未生成预测）

**别名使用建议：**

仅作为条件候选

**参考判断理由：**

实查 genre.name 字段与标准值 Rock And Roll 均存在，完整DISTINCT与既有标准值索引一致。独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“摇滚”可表达 Rock And Roll，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

**发现的问题或限制：**

[
  "同字段同中文词形存在Rock/Rock And Roll两候选。"
]

**建议处理方式：**

保留 Rock And Roll 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。

**仍需人工确认：**

确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。

**证据文件及具体位置：**

- [data/aliases/aliases.csv](../../../data/aliases/aliases.csv) — section=待审行；LLM草稿仅作对象/来源登记，不作译名证明; supports=原待审别名、字段、标准值、pending配置; kind=local_material; line=82
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables[genre].columns[name]; supports=实际目录中的字段与业务含义; kind=local_material; line=354
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=$.schema中的 genre.name; $.text_values["genre.name"].values[19]; 原始queries内该列SELECT DISTINCT; supports=qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断; kind=local_material
- [data/indexes/values/records.jsonl](../../../data/indexes/values/records.jsonl) — section=kind=standard; candidate_id=v-10facd793602b59518e7; supports=既有标准值索引旁证；未重建索引; kind=local_material; line=1178
- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — section=### genre; supports=字典中的字段范围说明; kind=local_material; line=88
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock) — section=rock noun (MUSIC); title=剑桥英汉辞典：rock; supports=词典支持 Rock 的中文音乐义。; kind=external_source; access=搜索工具返回可读词条正文；本轮未单独open完整页; source_strength=primary
- [https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll](https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll) — section=主词条音乐义; title=剑桥英汉辞典：rock-and-roll; supports=词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。; kind=external_source; access=搜索工具返回可读词条正文；Rock And Roll完整页open为403; source_strength=primary

### nl2sql:sql-01

- 分组：nl2sql；划分：dev

**审核对象：** 客户表共有多少位客户？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer;",
  "result": [
    {
      "customer_count": 59
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\"",
  "table": [
    {
      "customer_count": 59
    }
  ],
  "answer": "查询结果：59。",
  "rewritten_question": null,
  "trace_id": "e036e073-7e34-48ae-9e70-3593d1fc34c6",
  "truncated": false
}
```

**参考判断理由：**

对象为客户表全体记录，customer_id 是非空主键；COUNT(*) 每客户计一次，不受其他可空列影响，不加期间或国家过滤。参考结果为59位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：59。”准确陈述标量59，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-01; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=1; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=1; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=2; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=3; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-02

- 分组：nl2sql；划分：dev

**审核对象：** 来自巴西的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';",
  "result": [
    {
      "customer_count": 5
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Brazil'",
  "table": [
    {
      "count": 5
    }
  ],
  "answer": "查询结果：5。",
  "rewritten_question": "来自Brazil的客户有多少位？",
  "trace_id": "f303167f-9f2e-404c-b496-3f12bc0c0af4",
  "truncated": false
}
```

**参考判断理由：**

“来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-02; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=2; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=2; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=4; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=5; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-03

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-04

- 分组：nl2sql；划分：dev

**审核对象：** 列出来自巴西的客户编号、名字、姓氏和城市，按客户编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT customer_id, first_name, last_name, city FROM customer WHERE country = 'Brazil' ORDER BY customer_id;",
  "result": [
    {
      "customer_id": 1,
      "first_name": "Luís",
      "last_name": "Gonçalves",
      "city": "São José dos Campos"
    },
    {
      "customer_id": 10,
      "first_name": "Eduardo",
      "last_name": "Martins",
      "city": "São Paulo"
    },
    {
      "customer_id": 11,
      "first_name": "Alexandre",
      "last_name": "Rocha",
      "city": "São Paulo"
    },
    {
      "customer_id": 12,
      "first_name": "Roberto",
      "last_name": "Almeida",
      "city": "Rio de Janeiro"
    },
    {
      "customer_id": 13,
      "first_name": "Fernanda",
      "last_name": "Ramos",
      "city": "Brasília"
    }
  ],
  "ordered": true,
  "columns": [
    "customer_id",
    "first_name",
    "last_name",
    "city"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"customer_id\", \"first_name\", \"last_name\", \"city\" FROM \"public\".\"customer\" WHERE \"country\" = 'Brazil' ORDER BY \"customer_id\" ASC LIMIT 200",
  "table": [
    {
      "customer_id": 1,
      "first_name": "Luís",
      "last_name": "Gonçalves",
      "city": "São José dos Campos"
    },
    {
      "customer_id": 10,
      "first_name": "Eduardo",
      "last_name": "Martins",
      "city": "São Paulo"
    },
    {
      "customer_id": 11,
      "first_name": "Alexandre",
      "last_name": "Rocha",
      "city": "São Paulo"
    },
    {
      "customer_id": 12,
      "first_name": "Roberto",
      "last_name": "Almeida",
      "city": "Rio de Janeiro"
    },
    {
      "customer_id": 13,
      "first_name": "Fernanda",
      "last_name": "Ramos",
      "city": "Brasília"
    }
  ],
  "answer": "查询返回 5 行，详细数据见结果表。",
  "rewritten_question": "列出来自Brazil的客户编号、名字、姓氏和城市，按客户编号升序。",
  "trace_id": "b084231c-84cc-4919-a6f4-2a9a823952ed",
  "truncated": false
}
```

**参考判断理由：**

客户国家Brazil筛选，投影customer_id、first_name、last_name、city四列，名字和姓氏分开；customer_id主键升序能确定全部5行次序。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回5行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-04; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=4; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=3; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=6; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=7; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-05

- 分组：nl2sql；划分：dev

**审核对象：** 列出来自美国的客户编号、城市和州，按客户编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;",
  "result": [
    {
      "customer_id": 16,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 17,
      "city": "Redmond",
      "state": "WA"
    },
    {
      "customer_id": 18,
      "city": "New York",
      "state": "NY"
    },
    {
      "customer_id": 19,
      "city": "Cupertino",
      "state": "CA"
    },
    {
      "customer_id": 20,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 21,
      "city": "Reno",
      "state": "NV"
    },
    {
      "customer_id": 22,
      "city": "Orlando",
      "state": "FL"
    },
    {
      "customer_id": 23,
      "city": "Boston",
      "state": "MA"
    },
    {
      "customer_id": 24,
      "city": "Chicago",
      "state": "IL"
    },
    {
      "customer_id": 25,
      "city": "Madison",
      "state": "WI"
    },
    {
      "customer_id": 26,
      "city": "Fort Worth",
      "state": "TX"
    },
    {
      "customer_id": 27,
      "city": "Tucson",
      "state": "AZ"
    },
    {
      "customer_id": 28,
      "city": "Salt Lake City",
      "state": "UT"
    }
  ],
  "ordered": true,
  "columns": [
    "customer_id",
    "city",
    "state"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"customer_id\", \"city\", \"state\" FROM \"public\".\"customer\" WHERE \"country\" = 'USA' ORDER BY \"customer_id\" ASC LIMIT 200",
  "table": [
    {
      "customer_id": 16,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 17,
      "city": "Redmond",
      "state": "WA"
    },
    {
      "customer_id": 18,
      "city": "New York",
      "state": "NY"
    },
    {
      "customer_id": 19,
      "city": "Cupertino",
      "state": "CA"
    },
    {
      "customer_id": 20,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 21,
      "city": "Reno",
      "state": "NV"
    },
    {
      "customer_id": 22,
      "city": "Orlando",
      "state": "FL"
    },
    {
      "customer_id": 23,
      "city": "Boston",
      "state": "MA"
    },
    {
      "customer_id": 24,
      "city": "Chicago",
      "state": "IL"
    },
    {
      "customer_id": 25,
      "city": "Madison",
      "state": "WI"
    },
    {
      "customer_id": 26,
      "city": "Fort Worth",
      "state": "TX"
    },
    {
      "customer_id": 27,
      "city": "Tucson",
      "state": "AZ"
    },
    {
      "customer_id": 28,
      "city": "Salt Lake City",
      "state": "UT"
    }
  ],
  "answer": "查询返回 13 行，详细数据见结果表。",
  "rewritten_question": "列出来自USA的客户编号、城市和州，按客户编号升序。",
  "trace_id": "a067a585-6d11-4108-895e-8f285a48bbfc",
  "truncated": false
}
```

**参考判断理由：**

美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 13 行，详细数据见结果表。”与结果表13行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回13行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-05; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=5; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=4; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=8; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=9; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-06

- 分组：nl2sql；划分：dev

**审核对象：** 列出单价高于 0.99 的前 10 首曲目的编号、名称和单价，按曲目编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT track_id, name, unit_price FROM track WHERE unit_price > 0.99 ORDER BY track_id LIMIT 10;",
  "result": [
    {
      "track_id": 2819,
      "name": "Battlestar Galactica: The Story So Far",
      "unit_price": "1.99"
    },
    {
      "track_id": 2820,
      "name": "Occupation / Precipice",
      "unit_price": "1.99"
    },
    {
      "track_id": 2821,
      "name": "Exodus, Pt. 1",
      "unit_price": "1.99"
    },
    {
      "track_id": 2822,
      "name": "Exodus, Pt. 2",
      "unit_price": "1.99"
    },
    {
      "track_id": 2823,
      "name": "Collaborators",
      "unit_price": "1.99"
    },
    {
      "track_id": 2824,
      "name": "Torn",
      "unit_price": "1.99"
    },
    {
      "track_id": 2825,
      "name": "A Measure of Salvation",
      "unit_price": "1.99"
    },
    {
      "track_id": 2826,
      "name": "Hero",
      "unit_price": "1.99"
    },
    {
      "track_id": 2827,
      "name": "Unfinished Business",
      "unit_price": "1.99"
    },
    {
      "track_id": 2828,
      "name": "The Passage",
      "unit_price": "1.99"
    }
  ],
  "ordered": true,
  "columns": [
    "track_id",
    "name",
    "unit_price"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"track_id\", \"name\", \"unit_price\" FROM \"public\".\"track\" WHERE \"unit_price\" > 0.99 ORDER BY \"track_id\" ASC LIMIT 10",
  "table": [
    {
      "track_id": 2819,
      "name": "Battlestar Galactica: The Story So Far",
      "unit_price": "1.99"
    },
    {
      "track_id": 2820,
      "name": "Occupation / Precipice",
      "unit_price": "1.99"
    },
    {
      "track_id": 2821,
      "name": "Exodus, Pt. 1",
      "unit_price": "1.99"
    },
    {
      "track_id": 2822,
      "name": "Exodus, Pt. 2",
      "unit_price": "1.99"
    },
    {
      "track_id": 2823,
      "name": "Collaborators",
      "unit_price": "1.99"
    },
    {
      "track_id": 2824,
      "name": "Torn",
      "unit_price": "1.99"
    },
    {
      "track_id": 2825,
      "name": "A Measure of Salvation",
      "unit_price": "1.99"
    },
    {
      "track_id": 2826,
      "name": "Hero",
      "unit_price": "1.99"
    },
    {
      "track_id": 2827,
      "name": "Unfinished Business",
      "unit_price": "1.99"
    },
    {
      "track_id": 2828,
      "name": "The Passage",
      "unit_price": "1.99"
    }
  ],
  "answer": "查询返回 10 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "8f8bc309-bdc8-4422-8ff1-4b5e7b2b72a7",
  "truncated": false
}
```

**参考判断理由：**

比较track.unit_price > 0.99是严格大于，属于目录单价，不能用发票总额；按track_id升序再LIMIT 10，准确返回首10行编号、名称、单价。数据未声明币种。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 10 行，详细数据见结果表。”与结果表10行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-06; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=6; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=5; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=10; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=11; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-07

- 分组：nl2sql；划分：dev

**审核对象：** 列出职位为 Sales Support Agent 的员工编号、名字和姓氏，按员工编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT employee_id, first_name, last_name FROM employee WHERE title = 'Sales Support Agent' ORDER BY employee_id;",
  "result": [
    {
      "employee_id": 3,
      "first_name": "Jane",
      "last_name": "Peacock"
    },
    {
      "employee_id": 4,
      "first_name": "Margaret",
      "last_name": "Park"
    },
    {
      "employee_id": 5,
      "first_name": "Steve",
      "last_name": "Johnson"
    }
  ],
  "ordered": true,
  "columns": [
    "employee_id",
    "first_name",
    "last_name"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"employee_id\", \"first_name\", \"last_name\" FROM \"public\".\"employee\" WHERE \"title\" = 'Sales Support Agent' ORDER BY \"employee_id\" ASC LIMIT 200",
  "table": [
    {
      "employee_id": 3,
      "first_name": "Jane",
      "last_name": "Peacock"
    },
    {
      "employee_id": 4,
      "first_name": "Margaret",
      "last_name": "Park"
    },
    {
      "employee_id": 5,
      "first_name": "Steve",
      "last_name": "Johnson"
    }
  ],
  "answer": "查询返回 3 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "99a10609-ca97-49a9-af86-29184314328a",
  "truncated": false
}
```

**参考判断理由：**

员工职位字段employee.title精确筛选Sales Support Agent；返回employee_id、first_name、last_name且编号升序，对应3名员工，没有拼接fullname。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 3 行，详细数据见结果表。”与结果表3行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回3行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-07; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=7; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=6; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=12; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=13; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-08

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-09

- 分组：nl2sql；划分：dev

**审核对象：** 全部发票的总金额是多少？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT SUM(total) AS total_amount FROM invoice;",
  "result": [
    {
      "total_amount": "2328.60"
    }
  ],
  "ordered": false,
  "columns": [
    "total_amount"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT SUM(\"total\") FROM \"public\".\"invoice\"",
  "table": [
    {
      "sum": "2328.60"
    }
  ],
  "answer": "查询结果：2328.60。",
  "rewritten_question": null,
  "trace_id": "5f5099b7-136c-4c0c-a30c-8b5ec834f598",
  "truncated": false
}
```

**参考判断理由：**

题目明确“全部发票”，对invoice.total在发票粒度SUM，不连接invoice_line导致重复金额，不增加默认期间、支付状态或币种。参考总额2328.60（数据库金额单位）。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：2328.60。”准确陈述标量2328.60，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-09; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=9; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=7; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=14; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=15; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-10

- 分组：nl2sql；划分：dev

**审核对象：** 全部曲目的平均时长是多少毫秒？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT AVG(milliseconds) AS average_milliseconds FROM track;",
  "result": [
    {
      "average_milliseconds": "393599.212103910933"
    }
  ],
  "ordered": false,
  "columns": [
    "average_milliseconds"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT AVG(\"milliseconds\") AS avg_ms FROM \"public\".\"track\"",
  "table": [
    {
      "avg_ms": "393599.212103910933"
    }
  ],
  "answer": "查询结果：393599.212103910933。",
  "rewritten_question": null,
  "trace_id": "135cb36e-d3cc-4b56-a749-bfd4d868d5e2",
  "truncated": false
}
```

**参考判断理由：**

题目明确全部曲目及毫秒，AVG(track.milliseconds)为每条曲目等权平均，没有除1000转秒或按销售数量加权；milliseconds非空，结果393599.212103910933毫秒。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：393599.212103910933。”准确陈述标量393599.212103910933，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-10; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=10; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=8; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=16; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=17; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-11

- 分组：nl2sql；划分：dev

**审核对象：** 全部发票的平均总额是多少？请保留两位小数。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT ROUND(AVG(total), 2) AS average_total FROM invoice;",
  "result": [
    {
      "average_total": "5.65"
    }
  ],
  "ordered": false,
  "columns": [
    "average_total"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT ROUND(CAST(AVG(\"total\") AS DECIMAL), 2) AS \"avg_total\" FROM \"public\".\"invoice\"",
  "table": [
    {
      "avg_total": "5.65"
    }
  ],
  "answer": "查询结果：5.65。",
  "rewritten_question": null,
  "trace_id": "ebac63ed-b3c4-4b38-b3d1-a7ea89f32223",
  "truncated": false
}
```

**参考判断理由：**

题目要求发票平均总额与两位小数，ROUND(AVG(invoice.total),2)先按每张发票平均再四舍五入；不是按购买客户均额。参考5.65，数据未声明货币名称。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5.65。”准确陈述标量5.65，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-11; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=11; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=9; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=18; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=19; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-12

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-13

- 分组：nl2sql；划分：dev

**审核对象：** 按客户所在国家统计客户数，先按客户数降序，并列时按国家名称升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT country, COUNT(*) AS customer_count FROM customer GROUP BY country ORDER BY customer_count DESC, country ASC;",
  "result": [
    {
      "country": "USA",
      "customer_count": 13
    },
    {
      "country": "Canada",
      "customer_count": 8
    },
    {
      "country": "Brazil",
      "customer_count": 5
    },
    {
      "country": "France",
      "customer_count": 5
    },
    {
      "country": "Germany",
      "customer_count": 4
    },
    {
      "country": "United Kingdom",
      "customer_count": 3
    },
    {
      "country": "Czech Republic",
      "customer_count": 2
    },
    {
      "country": "India",
      "customer_count": 2
    },
    {
      "country": "Portugal",
      "customer_count": 2
    },
    {
      "country": "Argentina",
      "customer_count": 1
    },
    {
      "country": "Australia",
      "customer_count": 1
    },
    {
      "country": "Austria",
      "customer_count": 1
    },
    {
      "country": "Belgium",
      "customer_count": 1
    },
    {
      "country": "Chile",
      "customer_count": 1
    },
    {
      "country": "Denmark",
      "customer_count": 1
    },
    {
      "country": "Finland",
      "customer_count": 1
    },
    {
      "country": "Hungary",
      "customer_count": 1
    },
    {
      "country": "Ireland",
      "customer_count": 1
    },
    {
      "country": "Italy",
      "customer_count": 1
    },
    {
      "country": "Netherlands",
      "customer_count": 1
    },
    {
      "country": "Norway",
      "customer_count": 1
    },
    {
      "country": "Poland",
      "customer_count": 1
    },
    {
      "country": "Spain",
      "customer_count": 1
    },
    {
      "country": "Sweden",
      "customer_count": 1
    }
  ],
  "ordered": true,
  "columns": [
    "country",
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"country\", COUNT(*) AS \"customer_count\" FROM \"public\".\"customer\" GROUP BY \"country\" ORDER BY COUNT(*) DESC, \"country\" ASC LIMIT 200",
  "table": [
    {
      "country": "USA",
      "customer_count": 13
    },
    {
      "country": "Canada",
      "customer_count": 8
    },
    {
      "country": "Brazil",
      "customer_count": 5
    },
    {
      "country": "France",
      "customer_count": 5
    },
    {
      "country": "Germany",
      "customer_count": 4
    },
    {
      "country": "United Kingdom",
      "customer_count": 3
    },
    {
      "country": "Czech Republic",
      "customer_count": 2
    },
    {
      "country": "India",
      "customer_count": 2
    },
    {
      "country": "Portugal",
      "customer_count": 2
    },
    {
      "country": "Argentina",
      "customer_count": 1
    },
    {
      "country": "Australia",
      "customer_count": 1
    },
    {
      "country": "Austria",
      "customer_count": 1
    },
    {
      "country": "Belgium",
      "customer_count": 1
    },
    {
      "country": "Chile",
      "customer_count": 1
    },
    {
      "country": "Denmark",
      "customer_count": 1
    },
    {
      "country": "Finland",
      "customer_count": 1
    },
    {
      "country": "Hungary",
      "customer_count": 1
    },
    {
      "country": "Ireland",
      "customer_count": 1
    },
    {
      "country": "Italy",
      "customer_count": 1
    },
    {
      "country": "Netherlands",
      "customer_count": 1
    },
    {
      "country": "Norway",
      "customer_count": 1
    },
    {
      "country": "Poland",
      "customer_count": 1
    },
    {
      "country": "Spain",
      "customer_count": 1
    },
    {
      "country": "Sweden",
      "customer_count": 1
    }
  ],
  "answer": "查询返回 24 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "741e9d6d-fb36-4cd5-bfeb-46a03423c07e",
  "truncated": false
}
```

**参考判断理由：**

按customer.country分组COUNT(*)统计客户数，主排序客户数降序、次排序国家名升序；24个国家组完整，数量相等时已有次排序，不将客户国家替换为账单国家。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 24 行，详细数据见结果表。”与结果表24行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回24行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-13; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=13; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=10; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=20; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=21; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-14

- 分组：nl2sql；划分：dev

**审核对象：** 按流派编号统计曲目数，先按曲目数降序，并列时按流派编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT genre_id, COUNT(*) AS track_count FROM track GROUP BY genre_id ORDER BY track_count DESC, genre_id ASC;",
  "result": [
    {
      "genre_id": 1,
      "track_count": 1297
    },
    {
      "genre_id": 7,
      "track_count": 579
    },
    {
      "genre_id": 3,
      "track_count": 374
    },
    {
      "genre_id": 4,
      "track_count": 332
    },
    {
      "genre_id": 2,
      "track_count": 130
    },
    {
      "genre_id": 19,
      "track_count": 93
    },
    {
      "genre_id": 6,
      "track_count": 81
    },
    {
      "genre_id": 24,
      "track_count": 74
    },
    {
      "genre_id": 21,
      "track_count": 64
    },
    {
      "genre_id": 14,
      "track_count": 61
    },
    {
      "genre_id": 8,
      "track_count": 58
    },
    {
      "genre_id": 9,
      "track_count": 48
    },
    {
      "genre_id": 10,
      "track_count": 43
    },
    {
      "genre_id": 23,
      "track_count": 40
    },
    {
      "genre_id": 17,
      "track_count": 35
    },
    {
      "genre_id": 15,
      "track_count": 30
    },
    {
      "genre_id": 13,
      "track_count": 28
    },
    {
      "genre_id": 16,
      "track_count": 28
    },
    {
      "genre_id": 20,
      "track_count": 26
    },
    {
      "genre_id": 12,
      "track_count": 24
    },
    {
      "genre_id": 22,
      "track_count": 17
    },
    {
      "genre_id": 11,
      "track_count": 15
    },
    {
      "genre_id": 18,
      "track_count": 13
    },
    {
      "genre_id": 5,
      "track_count": 12
    },
    {
      "genre_id": 25,
      "track_count": 1
    }
  ],
  "ordered": true,
  "columns": [
    "genre_id",
    "track_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"genre_id\", COUNT(*) AS \"track_count\" FROM \"public\".\"track\" GROUP BY \"genre_id\" ORDER BY \"track_count\" DESC, \"genre_id\" ASC LIMIT 200",
  "table": [
    {
      "genre_id": 1,
      "track_count": 1297
    },
    {
      "genre_id": 7,
      "track_count": 579
    },
    {
      "genre_id": 3,
      "track_count": 374
    },
    {
      "genre_id": 4,
      "track_count": 332
    },
    {
      "genre_id": 2,
      "track_count": 130
    },
    {
      "genre_id": 19,
      "track_count": 93
    },
    {
      "genre_id": 6,
      "track_count": 81
    },
    {
      "genre_id": 24,
      "track_count": 74
    },
    {
      "genre_id": 21,
      "track_count": 64
    },
    {
      "genre_id": 14,
      "track_count": 61
    },
    {
      "genre_id": 8,
      "track_count": 58
    },
    {
      "genre_id": 9,
      "track_count": 48
    },
    {
      "genre_id": 10,
      "track_count": 43
    },
    {
      "genre_id": 23,
      "track_count": 40
    },
    {
      "genre_id": 17,
      "track_count": 35
    },
    {
      "genre_id": 15,
      "track_count": 30
    },
    {
      "genre_id": 13,
      "track_count": 28
    },
    {
      "genre_id": 16,
      "track_count": 28
    },
    {
      "genre_id": 20,
      "track_count": 26
    },
    {
      "genre_id": 12,
      "track_count": 24
    },
    {
      "genre_id": 22,
      "track_count": 17
    },
    {
      "genre_id": 11,
      "track_count": 15
    },
    {
      "genre_id": 18,
      "track_count": 13
    },
    {
      "genre_id": 5,
      "track_count": 12
    },
    {
      "genre_id": 25,
      "track_count": 1
    }
  ],
  "answer": "查询返回 25 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "7fe045de-946e-44b3-9eaa-0ab971584b93",
  "truncated": false
}
```

**参考判断理由：**

按track.genre_id分组COUNT(*)统计曲目条数，数量降序、genre_id升序；genre_id可NULL但当前快照NULL数为0，SQL不会擅自删除NULL组。25组完整。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 25 行，详细数据见结果表。”与结果表25行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回25行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-14; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=14; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=11; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=22; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=23; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-15

- 分组：nl2sql；划分：dev

**审核对象：** 按发票的账单国家统计销售总额，先按销售总额降序，并列时按国家名称升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT billing_country, SUM(total) AS sales_total FROM invoice GROUP BY billing_country ORDER BY sales_total DESC, billing_country ASC;",
  "result": [
    {
      "billing_country": "USA",
      "sales_total": "523.06"
    },
    {
      "billing_country": "Canada",
      "sales_total": "303.96"
    },
    {
      "billing_country": "France",
      "sales_total": "195.10"
    },
    {
      "billing_country": "Brazil",
      "sales_total": "190.10"
    },
    {
      "billing_country": "Germany",
      "sales_total": "156.48"
    },
    {
      "billing_country": "United Kingdom",
      "sales_total": "112.86"
    },
    {
      "billing_country": "Czech Republic",
      "sales_total": "90.24"
    },
    {
      "billing_country": "Portugal",
      "sales_total": "77.24"
    },
    {
      "billing_country": "India",
      "sales_total": "75.26"
    },
    {
      "billing_country": "Chile",
      "sales_total": "46.62"
    },
    {
      "billing_country": "Hungary",
      "sales_total": "45.62"
    },
    {
      "billing_country": "Ireland",
      "sales_total": "45.62"
    },
    {
      "billing_country": "Austria",
      "sales_total": "42.62"
    },
    {
      "billing_country": "Finland",
      "sales_total": "41.62"
    },
    {
      "billing_country": "Netherlands",
      "sales_total": "40.62"
    },
    {
      "billing_country": "Norway",
      "sales_total": "39.62"
    },
    {
      "billing_country": "Sweden",
      "sales_total": "38.62"
    },
    {
      "billing_country": "Argentina",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Australia",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Belgium",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Denmark",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Italy",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Poland",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Spain",
      "sales_total": "37.62"
    }
  ],
  "ordered": true,
  "columns": [
    "billing_country",
    "sales_total"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"billing_country\", SUM(\"total\") AS \"sales_total\" FROM \"public\".\"invoice\" GROUP BY \"billing_country\" ORDER BY \"sales_total\" DESC, \"billing_country\" ASC LIMIT 200",
  "table": [
    {
      "billing_country": "USA",
      "sales_total": "523.06"
    },
    {
      "billing_country": "Canada",
      "sales_total": "303.96"
    },
    {
      "billing_country": "France",
      "sales_total": "195.10"
    },
    {
      "billing_country": "Brazil",
      "sales_total": "190.10"
    },
    {
      "billing_country": "Germany",
      "sales_total": "156.48"
    },
    {
      "billing_country": "United Kingdom",
      "sales_total": "112.86"
    },
    {
      "billing_country": "Czech Republic",
      "sales_total": "90.24"
    },
    {
      "billing_country": "Portugal",
      "sales_total": "77.24"
    },
    {
      "billing_country": "India",
      "sales_total": "75.26"
    },
    {
      "billing_country": "Chile",
      "sales_total": "46.62"
    },
    {
      "billing_country": "Hungary",
      "sales_total": "45.62"
    },
    {
      "billing_country": "Ireland",
      "sales_total": "45.62"
    },
    {
      "billing_country": "Austria",
      "sales_total": "42.62"
    },
    {
      "billing_country": "Finland",
      "sales_total": "41.62"
    },
    {
      "billing_country": "Netherlands",
      "sales_total": "40.62"
    },
    {
      "billing_country": "Norway",
      "sales_total": "39.62"
    },
    {
      "billing_country": "Sweden",
      "sales_total": "38.62"
    },
    {
      "billing_country": "Argentina",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Australia",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Belgium",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Denmark",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Italy",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Poland",
      "sales_total": "37.62"
    },
    {
      "billing_country": "Spain",
      "sales_total": "37.62"
    }
  ],
  "answer": "查询返回 24 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "7896e6ae-a3c6-4c6f-af38-440d95e36238",
  "truncated": false
}
```

**参考判断理由：**

题目明确发票账单国家，字段invoice.billing_country；在invoice粒度SUM(total)，金额降序、国家名升序，24组完整且并列次序确定。不能因当前客户地区与账单地区一致而替换字段。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 24 行，详细数据见结果表。”与结果表24行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回24行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-15; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=15; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=12; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=24; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=25; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-16

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-17

- 分组：nl2sql；划分：dev

**审核对象：** 找出时长最长的 5 首曲目，返回编号、名称和毫秒时长；按时长降序，并列按编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT track_id, name, milliseconds FROM track ORDER BY milliseconds DESC, track_id ASC LIMIT 5;",
  "result": [
    {
      "track_id": 2820,
      "name": "Occupation / Precipice",
      "milliseconds": 5286953
    },
    {
      "track_id": 3224,
      "name": "Through a Looking Glass",
      "milliseconds": 5088838
    },
    {
      "track_id": 3244,
      "name": "Greetings from Earth, Pt. 1",
      "milliseconds": 2960293
    },
    {
      "track_id": 3242,
      "name": "The Man With Nine Lives",
      "milliseconds": 2956998
    },
    {
      "track_id": 3227,
      "name": "Battlestar Galactica, Pt. 2",
      "milliseconds": 2956081
    }
  ],
  "ordered": true,
  "columns": [
    "track_id",
    "name",
    "milliseconds"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"track_id\", \"name\", \"milliseconds\" FROM \"public\".\"track\" ORDER BY \"milliseconds\" DESC, \"track_id\" ASC LIMIT 5",
  "table": [
    {
      "track_id": 2820,
      "name": "Occupation / Precipice",
      "milliseconds": 5286953
    },
    {
      "track_id": 3224,
      "name": "Through a Looking Glass",
      "milliseconds": 5088838
    },
    {
      "track_id": 3244,
      "name": "Greetings from Earth, Pt. 1",
      "milliseconds": 2960293
    },
    {
      "track_id": 3242,
      "name": "The Man With Nine Lives",
      "milliseconds": 2956998
    },
    {
      "track_id": 3227,
      "name": "Battlestar Galactica, Pt. 2",
      "milliseconds": 2956081
    }
  ],
  "answer": "查询返回 5 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "67f084ca-e594-4cda-8b79-819c67f49cb0",
  "truncated": false
}
```

**参考判断理由：**

最长5首按非空track.milliseconds降序，track_id升序作并列规则，然后LIMIT 5；只返回track_id、name、milliseconds，保留毫秒单位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-17; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=17; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=13; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=26; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=27; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-18

- 分组：nl2sql；划分：dev

**审核对象：** 找出总额最高的 5 张发票，返回编号和总额；按总额降序，并列按编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT invoice_id, total FROM invoice ORDER BY total DESC, invoice_id ASC LIMIT 5;",
  "result": [
    {
      "invoice_id": 404,
      "total": "25.86"
    },
    {
      "invoice_id": 299,
      "total": "23.86"
    },
    {
      "invoice_id": 96,
      "total": "21.86"
    },
    {
      "invoice_id": 194,
      "total": "21.86"
    },
    {
      "invoice_id": 89,
      "total": "18.86"
    }
  ],
  "ordered": true,
  "columns": [
    "invoice_id",
    "total"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"invoice_id\", \"total\" FROM \"public\".\"invoice\" ORDER BY \"total\" DESC, \"invoice_id\" ASC LIMIT 5",
  "table": [
    {
      "invoice_id": 404,
      "total": "25.86"
    },
    {
      "invoice_id": 299,
      "total": "23.86"
    },
    {
      "invoice_id": 96,
      "total": "21.86"
    },
    {
      "invoice_id": 194,
      "total": "21.86"
    },
    {
      "invoice_id": 89,
      "total": "18.86"
    }
  ],
  "answer": "查询返回 5 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "13b61f6c-6c2b-475e-b9c7-f5aa2060f2e6",
  "truncated": false
}
```

**参考判断理由：**

最高5张发票按invoice.total降序、invoice_id升序确定并列，再LIMIT 5；21.86并列的96和194号先后正确，金额是发票总额。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-18; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=18; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=14; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=28; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=29; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-19

- 分组：nl2sql；划分：dev

**审核对象：** 按姓氏降序取前 5 位客户，返回编号、名字和姓氏；姓氏相同时按客户编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT customer_id, first_name, last_name FROM customer ORDER BY last_name DESC, customer_id ASC LIMIT 5;",
  "result": [
    {
      "customer_id": 37,
      "first_name": "Fynn",
      "last_name": "Zimmermann"
    },
    {
      "customer_id": 49,
      "first_name": "Stanisław",
      "last_name": "Wójcik"
    },
    {
      "customer_id": 5,
      "first_name": "František",
      "last_name": "Wichterlová"
    },
    {
      "customer_id": 48,
      "first_name": "Johannes",
      "last_name": "Van der Berg"
    },
    {
      "customer_id": 3,
      "first_name": "François",
      "last_name": "Tremblay"
    }
  ],
  "ordered": true,
  "columns": [
    "customer_id",
    "first_name",
    "last_name"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"customer_id\", \"first_name\", \"last_name\" FROM \"public\".\"customer\" ORDER BY \"last_name\" DESC, \"customer_id\" ASC LIMIT 5",
  "table": [
    {
      "customer_id": 37,
      "first_name": "Fynn",
      "last_name": "Zimmermann"
    },
    {
      "customer_id": 49,
      "first_name": "Stanisław",
      "last_name": "Wójcik"
    },
    {
      "customer_id": 5,
      "first_name": "František",
      "last_name": "Wichterlová"
    },
    {
      "customer_id": 48,
      "first_name": "Johannes",
      "last_name": "Van der Berg"
    },
    {
      "customer_id": 3,
      "first_name": "François",
      "last_name": "Tremblay"
    }
  ],
  "answer": "查询返回 5 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "548ddd4a-6df6-4346-9a90-da4c7e0d5d31",
  "truncated": false
}
```

**参考判断理由：**

客户last_name按数据库当前文本排序规则降序，再customer_id升序并列，LIMIT 5；投影编号、first_name、last_name，未误用first_name排序或fullname。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-19; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=19; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=15; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=30; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=31; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-20

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-21

- 分组：nl2sql；划分：dev

**审核对象：** 列出 2021 年的前 10 张发票，返回编号、日期和总额，按发票编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT invoice_id, invoice_date, total FROM invoice WHERE invoice_date >= '2021-01-01' AND invoice_date < '2022-01-01' ORDER BY invoice_id LIMIT 10;",
  "result": [
    {
      "invoice_id": 1,
      "invoice_date": "2021-01-01T00:00:00",
      "total": "1.98"
    },
    {
      "invoice_id": 2,
      "invoice_date": "2021-01-02T00:00:00",
      "total": "3.96"
    },
    {
      "invoice_id": 3,
      "invoice_date": "2021-01-03T00:00:00",
      "total": "5.94"
    },
    {
      "invoice_id": 4,
      "invoice_date": "2021-01-06T00:00:00",
      "total": "8.91"
    },
    {
      "invoice_id": 5,
      "invoice_date": "2021-01-11T00:00:00",
      "total": "13.86"
    },
    {
      "invoice_id": 6,
      "invoice_date": "2021-01-19T00:00:00",
      "total": "0.99"
    },
    {
      "invoice_id": 7,
      "invoice_date": "2021-02-01T00:00:00",
      "total": "1.98"
    },
    {
      "invoice_id": 8,
      "invoice_date": "2021-02-01T00:00:00",
      "total": "1.98"
    },
    {
      "invoice_id": 9,
      "invoice_date": "2021-02-02T00:00:00",
      "total": "3.96"
    },
    {
      "invoice_id": 10,
      "invoice_date": "2021-02-03T00:00:00",
      "total": "5.94"
    }
  ],
  "ordered": true,
  "columns": [
    "invoice_id",
    "invoice_date",
    "total"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"invoice_id\", \"invoice_date\", \"total\" FROM \"public\".\"invoice\" WHERE \"invoice_date\" >= '2021-01-01' AND \"invoice_date\" < '2022-01-01' ORDER BY \"invoice_id\" ASC LIMIT 10",
  "table": [
    {
      "invoice_id": 1,
      "invoice_date": "2021-01-01T00:00:00",
      "total": "1.98"
    },
    {
      "invoice_id": 2,
      "invoice_date": "2021-01-02T00:00:00",
      "total": "3.96"
    },
    {
      "invoice_id": 3,
      "invoice_date": "2021-01-03T00:00:00",
      "total": "5.94"
    },
    {
      "invoice_id": 4,
      "invoice_date": "2021-01-06T00:00:00",
      "total": "8.91"
    },
    {
      "invoice_id": 5,
      "invoice_date": "2021-01-11T00:00:00",
      "total": "13.86"
    },
    {
      "invoice_id": 6,
      "invoice_date": "2021-01-19T00:00:00",
      "total": "0.99"
    },
    {
      "invoice_id": 7,
      "invoice_date": "2021-02-01T00:00:00",
      "total": "1.98"
    },
    {
      "invoice_id": 8,
      "invoice_date": "2021-02-01T00:00:00",
      "total": "1.98"
    },
    {
      "invoice_id": 9,
      "invoice_date": "2021-02-02T00:00:00",
      "total": "3.96"
    },
    {
      "invoice_id": 10,
      "invoice_date": "2021-02-03T00:00:00",
      "total": "5.94"
    }
  ],
  "answer": "查询返回 10 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "f94f936c-67ba-45ab-af05-f38fc600c4af",
  "truncated": false
}
```

**参考判断理由：**

2021年依据invoice.invoice_date，范围[2021-01-01,2022-01-01)，再按invoice_id升序LIMIT 10；返回编号、原始日期和总额，未混用客户创建日期或最近10张。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 10 行，详细数据见结果表。”与结果表10行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-21; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=21; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=16; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=32; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=33; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-22

- 分组：nl2sql；划分：dev

**审核对象：** 列出 2004 年 1 月 1 日之前入职的员工编号、名字（仅 first_name，不包含姓氏 last_name）和入职日期，按员工编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT employee_id, first_name, hire_date FROM employee WHERE hire_date < '2004-01-01' ORDER BY employee_id;",
  "result": [
    {
      "employee_id": 1,
      "first_name": "Andrew",
      "hire_date": "2002-08-14T00:00:00"
    },
    {
      "employee_id": 2,
      "first_name": "Nancy",
      "hire_date": "2002-05-01T00:00:00"
    },
    {
      "employee_id": 3,
      "first_name": "Jane",
      "hire_date": "2002-04-01T00:00:00"
    },
    {
      "employee_id": 4,
      "first_name": "Margaret",
      "hire_date": "2003-05-03T00:00:00"
    },
    {
      "employee_id": 5,
      "first_name": "Steve",
      "hire_date": "2003-10-17T00:00:00"
    },
    {
      "employee_id": 6,
      "first_name": "Michael",
      "hire_date": "2003-10-17T00:00:00"
    }
  ],
  "ordered": true,
  "columns": [
    "employee_id",
    "first_name",
    "hire_date"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"employee_id\", \"first_name\", \"hire_date\" FROM \"public\".\"employee\" WHERE \"hire_date\" < '2004-01-01' ORDER BY \"employee_id\" ASC LIMIT 200",
  "table": [
    {
      "employee_id": 1,
      "first_name": "Andrew",
      "hire_date": "2002-08-14T00:00:00"
    },
    {
      "employee_id": 2,
      "first_name": "Nancy",
      "hire_date": "2002-05-01T00:00:00"
    },
    {
      "employee_id": 3,
      "first_name": "Jane",
      "hire_date": "2002-04-01T00:00:00"
    },
    {
      "employee_id": 4,
      "first_name": "Margaret",
      "hire_date": "2003-05-03T00:00:00"
    },
    {
      "employee_id": 5,
      "first_name": "Steve",
      "hire_date": "2003-10-17T00:00:00"
    },
    {
      "employee_id": 6,
      "first_name": "Michael",
      "hire_date": "2003-10-17T00:00:00"
    }
  ],
  "answer": "查询返回 6 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "9ef7f456-51ed-40e1-861c-d429ff81c274",
  "truncated": false
}
```

**参考判断理由：**

入职时间取employee.hire_date，严格早于2004-01-01；名字明确仅first_name，不含last_name/fullname；按employee_id升序返回6行，当前hire_date无NULL。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 6 行，详细数据见结果表。”与结果表6行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回6行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-22; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=22; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=17; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=34; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=35; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-23

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-24

- 分组：nl2sql；划分：dev

**审核对象：** 列出邮箱以 @gmail.com 结尾的客户编号、名字（仅 first_name，不包含姓氏 last_name）和邮箱，按客户编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT customer_id, first_name, email FROM customer WHERE email LIKE '%@gmail.com' ORDER BY customer_id;",
  "result": [
    {
      "customer_id": 3,
      "first_name": "François",
      "email": "ftremblay@gmail.com"
    },
    {
      "customer_id": 6,
      "first_name": "Helena",
      "email": "hholy@gmail.com"
    },
    {
      "customer_id": 22,
      "first_name": "Heather",
      "email": "hleacock@gmail.com"
    },
    {
      "customer_id": 24,
      "first_name": "Frank",
      "email": "fralston@gmail.com"
    },
    {
      "customer_id": 28,
      "first_name": "Julia",
      "email": "jubarnett@gmail.com"
    },
    {
      "customer_id": 31,
      "first_name": "Martha",
      "email": "marthasilk@gmail.com"
    },
    {
      "customer_id": 40,
      "first_name": "Dominique",
      "email": "dominiquelefebvre@gmail.com"
    },
    {
      "customer_id": 53,
      "first_name": "Phil",
      "email": "phil.hughes@gmail.com"
    }
  ],
  "ordered": true,
  "columns": [
    "customer_id",
    "first_name",
    "email"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"customer_id\", \"first_name\", \"email\" FROM \"public\".\"customer\" WHERE \"email\" LIKE '%@gmail.com' ORDER BY \"customer_id\" ASC LIMIT 200",
  "table": [
    {
      "customer_id": 3,
      "first_name": "François",
      "email": "ftremblay@gmail.com"
    },
    {
      "customer_id": 6,
      "first_name": "Helena",
      "email": "hholy@gmail.com"
    },
    {
      "customer_id": 22,
      "first_name": "Heather",
      "email": "hleacock@gmail.com"
    },
    {
      "customer_id": 24,
      "first_name": "Frank",
      "email": "fralston@gmail.com"
    },
    {
      "customer_id": 28,
      "first_name": "Julia",
      "email": "jubarnett@gmail.com"
    },
    {
      "customer_id": 31,
      "first_name": "Martha",
      "email": "marthasilk@gmail.com"
    },
    {
      "customer_id": 40,
      "first_name": "Dominique",
      "email": "dominiquelefebvre@gmail.com"
    },
    {
      "customer_id": 53,
      "first_name": "Phil",
      "email": "phil.hughes@gmail.com"
    }
  ],
  "answer": "查询返回 8 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "90fcb03a-92dd-402b-8135-5937bbe720e8",
  "truncated": false
}
```

**参考判断理由：**

邮箱以@gmail.com结尾用LIKE '%@gmail.com'，不是包含gmail.com或错用公司名；题目名字明确仅first_name，返回编号、first_name、email并按编号升序，8行完整。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 8 行，详细数据见结果表。”与结果表8行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回8行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-24; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=24; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=18; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=36; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=37; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-25

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-26

- 分组：nl2sql；划分：dev

**审核对象：** 有多少位客户没有填写公司名称（company 为 NULL）？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE company IS NULL;",
  "result": [
    {
      "customer_count": 49
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"company\" IS NULL",
  "table": [
    {
      "count": 49
    }
  ],
  "answer": "查询结果：49。",
  "rewritten_question": null,
  "trace_id": "9354a768-f85e-4e42-ae9e-bc01d031caa6",
  "truncated": false
}
```

**参考判断理由：**

题目明确定义company为NULL，使用IS NULL而非等于NULL、空串或COUNT(company)；COUNT(*)得到49位，实库company空字符串为0，未改变NULL语义。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：49。”准确陈述标量49，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-26; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=26; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=19; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=38; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=39; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-27

- 分组：nl2sql；划分：dev

**审核对象：** 列出没有作曲者信息（composer 为 NULL）的前 10 首曲目编号和名称，按曲目编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT track_id, name FROM track WHERE composer IS NULL ORDER BY track_id LIMIT 10;",
  "result": [
    {
      "track_id": 63,
      "name": "Desafinado"
    },
    {
      "track_id": 64,
      "name": "Garota De Ipanema"
    },
    {
      "track_id": 65,
      "name": "Samba De Uma Nota Só (One Note Samba)"
    },
    {
      "track_id": 66,
      "name": "Por Causa De Você"
    },
    {
      "track_id": 67,
      "name": "Ligia"
    },
    {
      "track_id": 68,
      "name": "Fotografia"
    },
    {
      "track_id": 69,
      "name": "Dindi (Dindi)"
    },
    {
      "track_id": 70,
      "name": "Se Todos Fossem Iguais A Você (Instrumental)"
    },
    {
      "track_id": 71,
      "name": "Falando De Amor"
    },
    {
      "track_id": 72,
      "name": "Angela"
    }
  ],
  "ordered": true,
  "columns": [
    "track_id",
    "name"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"track_id\", \"name\" FROM \"public\".\"track\" WHERE \"composer\" IS NULL ORDER BY \"track_id\" ASC LIMIT 10",
  "table": [
    {
      "track_id": 63,
      "name": "Desafinado"
    },
    {
      "track_id": 64,
      "name": "Garota De Ipanema"
    },
    {
      "track_id": 65,
      "name": "Samba De Uma Nota Só (One Note Samba)"
    },
    {
      "track_id": 66,
      "name": "Por Causa De Você"
    },
    {
      "track_id": 67,
      "name": "Ligia"
    },
    {
      "track_id": 68,
      "name": "Fotografia"
    },
    {
      "track_id": 69,
      "name": "Dindi (Dindi)"
    },
    {
      "track_id": 70,
      "name": "Se Todos Fossem Iguais A Você (Instrumental)"
    },
    {
      "track_id": 71,
      "name": "Falando De Amor"
    },
    {
      "track_id": 72,
      "name": "Angela"
    }
  ],
  "answer": "查询返回 10 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "ad46b4b1-1584-4355-afc4-1f80367d83fe",
  "truncated": false
}
```

**参考判断理由：**

缺少作曲者明确定义composer IS NULL；按track_id升序再LIMIT 10，返回编号和名称，既不将NULL与空串混同，也不把作曲者名称误当艺术家字段。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 10 行，详细数据见结果表。”与结果表10行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-27; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=27; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=20; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=40; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=41; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-28

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-29

- 分组：nl2sql；划分：dev

**审核对象：** 列出国家字段为 Antarctica 的客户编号、名字和姓氏，按客户编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT customer_id, first_name, last_name FROM customer WHERE country = 'Antarctica' ORDER BY customer_id;",
  "result": [],
  "ordered": true,
  "columns": [
    "customer_id",
    "first_name",
    "last_name"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "EMPTY_RESULT",
  "sql": "SELECT \"customer_id\", \"first_name\", \"last_name\" FROM \"public\".\"customer\" WHERE \"country\" = 'Antarctica' ORDER BY \"customer_id\" ASC LIMIT 200",
  "table": [],
  "answer": "按原问题条件未查到记录。",
  "rewritten_question": null,
  "trace_id": "49df40a2-3e55-4590-9ecb-6e17c14c288c",
  "truncated": false
}
```

**参考判断理由：**

原值Antarctica在customer.country实际值中不存在，仍保留精确筛选，不猜测其他国家；返回所要求的编号、first_name、last_name及编号排序，空列表表示没有匹配客户，不是标量0或NULL。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“按原问题条件未查到记录。”正确说明原条件无记录，没有将空列表当作NULL聚合或零值。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回0行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-29; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=29; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=21; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=42; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=43; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-30

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-31

- 分组：nl2sql；划分：dev

**审核对象：** 客户所在国家为 Italy 的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';",
  "result": [
    {
      "customer_count": 1
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Italy'",
  "table": [
    {
      "count": 1
    }
  ],
  "answer": "查询结果：1。",
  "rewritten_question": null,
  "trace_id": "e30dcf79-f6df-4add-b865-5064764aff4b",
  "truncated": false
}
```

**参考判断理由：**

客户所在国家Italy精确匹配customer.country；COUNT(*)得到1位，未改用invoice账单国家或新增日期条件。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1。”准确陈述标量1，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-31; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=31; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=22; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=44; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=45; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-32

- 分组：nl2sql；划分：dev

**审核对象：** 客户所在国家为 Canada 的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';",
  "result": [
    {
      "customer_count": 8
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Canada'",
  "table": [
    {
      "count": 8
    }
  ],
  "answer": "查询结果：8。",
  "rewritten_question": null,
  "trace_id": "8649d37b-8276-4d0a-a0c7-50690a29c681",
  "truncated": false
}
```

**参考判断理由：**

客户所在国家Canada精确匹配customer.country；COUNT(*)得到8位，区分客户国家与账单国家，未新增发票期间。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：8。”准确陈述标量8，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-32; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=32; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=23; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=46; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=47; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-33

- 分组：nl2sql；划分：dev

**审核对象：** 账单国家为 Canada 的全部发票总额是多少？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Canada';",
  "result": [
    {
      "total_amount": "303.96"
    }
  ],
  "ordered": false,
  "columns": [
    "total_amount"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT SUM(\"total\") AS \"total_amount\" FROM \"public\".\"invoice\" WHERE \"billing_country\" = 'Canada'",
  "table": [
    {
      "total_amount": "303.96"
    }
  ],
  "answer": "查询结果：303.96。",
  "rewritten_question": null,
  "trace_id": "738d8fd7-087d-4f19-842e-2190a9c83758",
  "truncated": false
}
```

**参考判断理由：**

题目明确账单国家Canada，筛选invoice.billing_country而非customer.country；SUM(invoice.total)统计全部匹配发票，结果303.96（数据库金额单位），不做明细JOIN重复计额。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：303.96。”准确陈述标量303.96，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-33; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=33; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=24; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=48; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=49; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-34

- 分组：nl2sql；划分：dev

**审核对象：** 曲目表中最短的时长是多少毫秒？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT MIN(milliseconds) AS minimum_milliseconds FROM track;",
  "result": [
    {
      "minimum_milliseconds": 1071
    }
  ],
  "ordered": false,
  "columns": [
    "minimum_milliseconds"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT MIN(\"milliseconds\") AS min_milliseconds FROM \"public\".\"track\"",
  "table": [
    {
      "min_milliseconds": 1071
    }
  ],
  "answer": "查询结果：1071。",
  "rewritten_question": null,
  "trace_id": "3aee4e89-e37f-40eb-b43e-7283a28611d7",
  "truncated": false
}
```

**参考判断理由：**

最短时长取MIN(track.milliseconds)，milliseconds非空，得到1071毫秒；题目只要最短值，标量聚合正确，无需返回任意一首同长曲目的姓名或编号。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1071。”准确陈述标量1071，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-34; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=34; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=25; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=50; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=51; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-35

- 分组：nl2sql；划分：dev

**审核对象：** 曲目表中最高的单价是多少？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT MAX(unit_price) AS maximum_unit_price FROM track;",
  "result": [
    {
      "maximum_unit_price": "1.99"
    }
  ],
  "ordered": false,
  "columns": [
    "maximum_unit_price"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT MAX(\"unit_price\") AS max_unit_price FROM \"public\".\"track\"",
  "table": [
    {
      "max_unit_price": "1.99"
    }
  ],
  "answer": "查询结果：1.99。",
  "rewritten_question": null,
  "trace_id": "a3565347-4f63-45e2-9398-ec5c3ee8c114",
  "truncated": false
}
```

**参考判断理由：**

最高目录单价取MAX(track.unit_price)，非空numeric列得到1.99；不把发票总额或明细实际成交价当曲目目录单价，也不推断美元/人民币。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1.99。”准确陈述标量1.99，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-35; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=35; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=26; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=52; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=53; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-36

- 分组：nl2sql；划分：dev

**审核对象：** 按发票账单城市统计发票数，先按数量降序，并列按城市名称升序，返回前 10 个城市。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT billing_city, COUNT(*) AS invoice_count FROM invoice GROUP BY billing_city ORDER BY invoice_count DESC, billing_city ASC LIMIT 10;",
  "result": [
    {
      "billing_city": "Berlin",
      "invoice_count": 14
    },
    {
      "billing_city": "London",
      "invoice_count": 14
    },
    {
      "billing_city": "Mountain View",
      "invoice_count": 14
    },
    {
      "billing_city": "Paris",
      "invoice_count": 14
    },
    {
      "billing_city": "Prague",
      "invoice_count": 14
    },
    {
      "billing_city": "São Paulo",
      "invoice_count": 14
    },
    {
      "billing_city": "Amsterdam",
      "invoice_count": 7
    },
    {
      "billing_city": "Bordeaux",
      "invoice_count": 7
    },
    {
      "billing_city": "Boston",
      "invoice_count": 7
    },
    {
      "billing_city": "Brasília",
      "invoice_count": 7
    }
  ],
  "ordered": true,
  "columns": [
    "billing_city",
    "invoice_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"billing_city\", COUNT(*) AS \"invoice_count\" FROM \"public\".\"invoice\" GROUP BY \"billing_city\" ORDER BY \"invoice_count\" DESC, \"billing_city\" ASC LIMIT 10",
  "table": [
    {
      "billing_city": "Berlin",
      "invoice_count": 14
    },
    {
      "billing_city": "London",
      "invoice_count": 14
    },
    {
      "billing_city": "Mountain View",
      "invoice_count": 14
    },
    {
      "billing_city": "Paris",
      "invoice_count": 14
    },
    {
      "billing_city": "Prague",
      "invoice_count": 14
    },
    {
      "billing_city": "São Paulo",
      "invoice_count": 14
    },
    {
      "billing_city": "Amsterdam",
      "invoice_count": 7
    },
    {
      "billing_city": "Bordeaux",
      "invoice_count": 7
    },
    {
      "billing_city": "Boston",
      "invoice_count": 7
    },
    {
      "billing_city": "Brasília",
      "invoice_count": 7
    }
  ],
  "answer": "查询返回 10 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "bc6949e7-28ac-42a1-b29c-a6d9cb2e5e66",
  "truncated": false
}
```

**参考判断理由：**

按invoice.billing_city分组COUNT(*)统计发票条数，数量降序、城市名升序，再LIMIT 10；数量14及7的并列均按城市升序，未使用客户城市或销售金额。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 10 行，详细数据见结果表。”与结果表10行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-36; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=36; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=27; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=54; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=55; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-37

- 分组：nl2sql；划分：dev

**审核对象：** 按媒体类型编号统计曲目数，按媒体类型编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT media_type_id, COUNT(*) AS track_count FROM track GROUP BY media_type_id ORDER BY media_type_id;",
  "result": [
    {
      "media_type_id": 1,
      "track_count": 3034
    },
    {
      "media_type_id": 2,
      "track_count": 237
    },
    {
      "media_type_id": 3,
      "track_count": 214
    },
    {
      "media_type_id": 4,
      "track_count": 7
    },
    {
      "media_type_id": 5,
      "track_count": 11
    }
  ],
  "ordered": true,
  "columns": [
    "media_type_id",
    "track_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"media_type_id\", COUNT(*) AS \"track_count\" FROM \"public\".\"track\" GROUP BY \"media_type_id\" ORDER BY \"media_type_id\" ASC LIMIT 200",
  "table": [
    {
      "media_type_id": 1,
      "track_count": 3034
    },
    {
      "media_type_id": 2,
      "track_count": 237
    },
    {
      "media_type_id": 3,
      "track_count": 214
    },
    {
      "media_type_id": 4,
      "track_count": 7
    },
    {
      "media_type_id": 5,
      "track_count": 11
    }
  ],
  "answer": "查询返回 5 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "dc4ef1b0-9939-493b-96ca-70b1a9090c96",
  "truncated": false
}
```

**参考判断理由：**

按track.media_type_id分组统计曲目条数，媒体类型编号升序；5种媒体类型完整，统计不是流派或媒体文件字节和。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回5行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-37; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=37; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=28; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=56; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=57; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-38

- 分组：nl2sql；划分：dev

**审核对象：** 找出文件字节数最大的 3 首曲目，返回编号、名称和字节数；按字节数降序，并列按曲目编号升序。

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** AI建议有条件通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT track_id, name, bytes FROM track ORDER BY bytes DESC, track_id ASC LIMIT 3;",
  "result": [
    {
      "track_id": 3224,
      "name": "Through a Looking Glass",
      "bytes": 1059546140
    },
    {
      "track_id": 2820,
      "name": "Occupation / Precipice",
      "bytes": 1054423946
    },
    {
      "track_id": 3236,
      "name": "The Young Lords",
      "bytes": 587051735
    }
  ],
  "ordered": true,
  "columns": [
    "track_id",
    "name",
    "bytes"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"track_id\", \"name\", \"bytes\" FROM \"public\".\"track\" ORDER BY \"bytes\" DESC, \"track_id\" ASC LIMIT 3",
  "table": [
    {
      "track_id": 3224,
      "name": "Through a Looking Glass",
      "bytes": 1059546140
    },
    {
      "track_id": 2820,
      "name": "Occupation / Precipice",
      "bytes": 1054423946
    },
    {
      "track_id": 3236,
      "name": "The Young Lords",
      "bytes": 587051735
    }
  ],
  "answer": "查询返回 3 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "1e6d1383-7e83-4997-a6e3-045501bbd398",
  "truncated": false
}
```

**参考判断理由：**

对象为文件字节数最大的3首曲目，字段track.bytes单位字节，排序bytes降序、track_id升序再LIMIT 3，投影编号、名称、字节数。当前bytes为NULL的行数为0，结果与当前题意一致；但bytes在schema可NULL，而PostgreSQL DESC默认NULLS FIRST，未知大小会排在真实最大值之前。需明确本题仅针对无NULL的固定快照，或补充非NULL筛选/NULLS LAST规则后再确认一般语义。

**实际回答判断理由：**

已有SQL和结果在当前bytes无NULL快照下满足最大字节数3首、字节单位、bytes降序和track_id并列升序；自然语言及3行表忠实。actual同样缺少NULLS LAST/bytes IS NOT NULL，故当前值正确而可空字段的一般排序语义需条件确认。

**发现的问题或限制：**

[
  {
    "object": "reference",
    "problem": "track.bytes可NULL且ORDER BY bytes DESC默认NULLS FIRST，缺少未知文件大小处理规则；现存NULL=0，未发现本次实际三行值错误。",
    "severity": "conditional"
  },
  {
    "object": "actual",
    "problem": "track.bytes可NULL且ORDER BY bytes DESC默认NULLS FIRST，缺少未知文件大小处理规则；现存NULL=0，未发现本次实际三行值错误。",
    "severity": "conditional"
  }
]

**建议处理方式：**

人工决定最大字节数排行是否仅针对当前无NULL快照，或应规定排除NULL/NULLS LAST；仅提出修订建议，不改gold或系统SQL。

**仍需人工确认：**

需要确认bytes为NULL时的排行规则，以及本题验收是否限定当前无NULL快照。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-38; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=38; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=29; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=58; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=59; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=121; note=nullable-columns
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=120; note=postgres-desc-null-order

### nl2sql:sql-39

- 分组：nl2sql；划分：dev

**审核对象：** 2023 年一共开了多少张发票？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01';",
  "result": [
    {
      "invoice_count": 83
    }
  ],
  "ordered": false,
  "columns": [
    "invoice_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"invoice\" WHERE \"invoice_date\" >= CAST('2023-01-01' AS DATE) AND \"invoice_date\" < CAST('2024-01-01' AS DATE)",
  "table": [
    {
      "count": 83
    }
  ],
  "answer": "查询结果：83。",
  "rewritten_question": null,
  "trace_id": "77fef77a-69cc-4130-b091-29e93f6e0414",
  "truncated": false
}
```

**参考判断理由：**

2023年开票数以invoice.invoice_date范围[2023-01-01,2024-01-01)过滤，再COUNT(*)；实库2023年83张，与当前日期无关，不把发票行数当发票数。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：83。”准确陈述标量83，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-39; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=39; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=30; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=60; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=61; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-40

- 分组：nl2sql；划分：dev

**审核对象：** 2022 年 7 月 1 日（含）到 2022 年 10 月 1 日（不含）的发票总额是多少？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT SUM(total) AS total_amount FROM invoice WHERE invoice_date >= '2022-07-01' AND invoice_date < '2022-10-01';",
  "result": [
    {
      "total_amount": "111.87"
    }
  ],
  "ordered": false,
  "columns": [
    "total_amount"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT SUM(\"total\") AS invoice_total FROM \"public\".\"invoice\" WHERE \"invoice_date\" >= CAST('2022-07-01 00:00:00' AS TIMESTAMP) AND \"invoice_date\" < CAST('2022-10-01 00:00:00' AS TIMESTAMP)",
  "table": [
    {
      "invoice_total": "111.87"
    }
  ],
  "answer": "查询结果：111.87。",
  "rewritten_question": null,
  "trace_id": "80c520ad-d4d8-4cdf-8427-223beb56e079",
  "truncated": false
}
```

**参考判断理由：**

题目给定起日含、止日不含，invoice_date >=2022-07-01且<2022-10-01准确实现半开区间；SUM(invoice.total)得到111.87（数据库金额单位），未扩大到全年或改用付款日期。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：111.87。”准确陈述标量111.87，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-40; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=40; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=31; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=62; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=63; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-41

- 分组：nl2sql；划分：dev

**审核对象：** 列出名称以 The 开头的前 8 位艺术家，区分大小写，返回编号和名称，按艺术家编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT artist_id, name FROM artist WHERE name LIKE 'The%' ORDER BY artist_id LIMIT 8;",
  "result": [
    {
      "artist_id": 137,
      "name": "The Black Crowes"
    },
    {
      "artist_id": 138,
      "name": "The Clash"
    },
    {
      "artist_id": 139,
      "name": "The Cult"
    },
    {
      "artist_id": 140,
      "name": "The Doors"
    },
    {
      "artist_id": 141,
      "name": "The Police"
    },
    {
      "artist_id": 142,
      "name": "The Rolling Stones"
    },
    {
      "artist_id": 143,
      "name": "The Tea Party"
    },
    {
      "artist_id": 144,
      "name": "The Who"
    }
  ],
  "ordered": true,
  "columns": [
    "artist_id",
    "name"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"artist_id\", \"name\" FROM \"public\".\"artist\" WHERE \"name\" LIKE 'The%' ORDER BY \"artist_id\" ASC LIMIT 8",
  "table": [
    {
      "artist_id": 137,
      "name": "The Black Crowes"
    },
    {
      "artist_id": 138,
      "name": "The Clash"
    },
    {
      "artist_id": 139,
      "name": "The Cult"
    },
    {
      "artist_id": 140,
      "name": "The Doors"
    },
    {
      "artist_id": 141,
      "name": "The Police"
    },
    {
      "artist_id": 142,
      "name": "The Rolling Stones"
    },
    {
      "artist_id": 143,
      "name": "The Tea Party"
    },
    {
      "artist_id": 144,
      "name": "The Who"
    }
  ],
  "answer": "查询返回 8 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "6f26c4b5-daf0-4c14-aa58-b8266e7a795d",
  "truncated": false
}
```

**参考判断理由：**

艺术家名称以The开头且区分大小写，用artist.name LIKE 'The%'而非ILIKE或包含The；按artist_id升序再LIMIT 8，投影编号和名称，空name不匹配。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 8 行，详细数据见结果表。”与结果表8行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-41; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=41; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=32; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=64; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=65; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-42

- 分组：nl2sql；划分：dev

**审核对象：** 列出名称恰好为 U2 的艺术家编号和名称，按编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT artist_id, name FROM artist WHERE name = 'U2' ORDER BY artist_id;",
  "result": [
    {
      "artist_id": 150,
      "name": "U2"
    }
  ],
  "ordered": true,
  "columns": [
    "artist_id",
    "name"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"artist_id\", \"name\" FROM \"public\".\"artist\" WHERE \"name\" = 'U2' ORDER BY \"artist_id\" ASC LIMIT 200",
  "table": [
    {
      "artist_id": 150,
      "name": "U2"
    }
  ],
  "answer": "查询返回 1 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "386e0fc3-6c1c-410a-bfbf-94a66ea8598f",
  "truncated": false
}
```

**参考判断理由：**

艺术家artist.name恰好为U2用等号，不用模糊/包含匹配；编号升序返回150号U2，没有将艺术家名称误作专辑/曲目名称。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 1 行，详细数据见结果表。”与结果表1行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回1行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-42; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=42; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=33; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=66; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=67; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-43

- 分组：nl2sql；划分：dev

**审核对象：** 没有填写州信息（state 为 NULL）的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE state IS NULL;",
  "result": [
    {
      "customer_count": 29
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"state\" IS NULL",
  "table": [
    {
      "count": 29
    }
  ],
  "answer": "查询结果：29。",
  "rewritten_question": null,
  "trace_id": "0301d7bb-6146-4c08-9448-9aeeb8d29cbd",
  "truncated": false
}
```

**参考判断理由：**

题目将未填写州信息明确定义state IS NULL，COUNT(*)为29位；不等同空字符串、未知州名，且没有误用invoice.billing_state。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：29。”准确陈述标量29，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-43; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=43; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=34; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=68; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=69; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-44

- 分组：nl2sql；划分：dev

**审核对象：** 客户所在国家为 Wakanda 的客户有多少位？保留原筛选值，没匹配时返回 0。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Wakanda';",
  "result": [
    {
      "customer_count": 0
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Wakanda'",
  "table": [
    {
      "count": 0
    }
  ],
  "answer": "查询结果：0。",
  "rewritten_question": null,
  "trace_id": "7e1edced-a0af-4b2e-8a55-a70e6f15c814",
  "truncated": false
}
```

**参考判断理由：**

明确保留Wakanda原值，country = 'Wakanda'在实库无匹配；COUNT(*)自然返回0，未纠错到真实国家、未返回空列表或NULL。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：0。”准确陈述标量0，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-44; note=仅dev题干、参考和已有输出
- [eval/datasets/nl2sql_chinook_d2.jsonl](../../datasets/nl2sql_chinook_d2.jsonl) — line=44; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/nl2sql/final/responses.jsonl](../../artifacts/d2/nl2sql/final/responses.jsonl) — line=35; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=70; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=71; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则

### nl2sql:sql-45

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-46

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-47

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-48

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-49

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### nl2sql:sql-50

- 分组：nl2sql；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-01

- 分组：robust；划分：dev

**审核对象：** 来自巴稀的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';",
  "result": [
    {
      "customer_count": 5
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Brazil'",
  "table": [
    {
      "count": 5
    }
  ],
  "answer": "查询结果：5。",
  "rewritten_question": "来自Brazil的客户有多少位？",
  "trace_id": "ca2b7547-df99-46b7-a868-22da378aa53b",
  "truncated": false
}
```

**参考判断理由：**

“巴稀”在国家语境是“巴西”的单字错写，指向Brazil；除错字外查询对象和计数口径未变化。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-01; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=1; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=1; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=72; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=73; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-02; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-02

- 分组：robust；划分：dev

**审核对象：** 列出来自美囯的客户编号、城市和州，按客户编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;",
  "result": [
    {
      "customer_id": 16,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 17,
      "city": "Redmond",
      "state": "WA"
    },
    {
      "customer_id": 18,
      "city": "New York",
      "state": "NY"
    },
    {
      "customer_id": 19,
      "city": "Cupertino",
      "state": "CA"
    },
    {
      "customer_id": 20,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 21,
      "city": "Reno",
      "state": "NV"
    },
    {
      "customer_id": 22,
      "city": "Orlando",
      "state": "FL"
    },
    {
      "customer_id": 23,
      "city": "Boston",
      "state": "MA"
    },
    {
      "customer_id": 24,
      "city": "Chicago",
      "state": "IL"
    },
    {
      "customer_id": 25,
      "city": "Madison",
      "state": "WI"
    },
    {
      "customer_id": 26,
      "city": "Fort Worth",
      "state": "TX"
    },
    {
      "customer_id": 27,
      "city": "Tucson",
      "state": "AZ"
    },
    {
      "customer_id": 28,
      "city": "Salt Lake City",
      "state": "UT"
    }
  ],
  "ordered": true,
  "columns": [
    "customer_id",
    "city",
    "state"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"customer_id\", \"city\", \"state\" FROM \"public\".\"customer\" WHERE \"country\" = 'USA' ORDER BY \"customer_id\" ASC LIMIT 200",
  "table": [
    {
      "customer_id": 16,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 17,
      "city": "Redmond",
      "state": "WA"
    },
    {
      "customer_id": 18,
      "city": "New York",
      "state": "NY"
    },
    {
      "customer_id": 19,
      "city": "Cupertino",
      "state": "CA"
    },
    {
      "customer_id": 20,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 21,
      "city": "Reno",
      "state": "NV"
    },
    {
      "customer_id": 22,
      "city": "Orlando",
      "state": "FL"
    },
    {
      "customer_id": 23,
      "city": "Boston",
      "state": "MA"
    },
    {
      "customer_id": 24,
      "city": "Chicago",
      "state": "IL"
    },
    {
      "customer_id": 25,
      "city": "Madison",
      "state": "WI"
    },
    {
      "customer_id": 26,
      "city": "Fort Worth",
      "state": "TX"
    },
    {
      "customer_id": 27,
      "city": "Tucson",
      "state": "AZ"
    },
    {
      "customer_id": 28,
      "city": "Salt Lake City",
      "state": "UT"
    }
  ],
  "answer": "查询返回 13 行，详细数据见结果表。",
  "rewritten_question": "列出来自USA的客户编号、城市和州，按客户编号升序。",
  "trace_id": "c03412cd-259a-4818-b188-01ce740db8e6",
  "truncated": false
}
```

**参考判断理由：**

“美囯”是“美国”的字形错写，指向USA；编号、城市、州投影与升序保持不变。 美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 13 行，详细数据见结果表。”与结果表13行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回13行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-02; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=2; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=2; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=74; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=75; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-05; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-03

- 分组：robust；划分：dev

**审核对象：** 列出职位为 Sales Suport Agent 的员工编号、名字和姓氏，按员工编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT employee_id, first_name, last_name FROM employee WHERE title = 'Sales Support Agent' ORDER BY employee_id;",
  "result": [
    {
      "employee_id": 3,
      "first_name": "Jane",
      "last_name": "Peacock"
    },
    {
      "employee_id": 4,
      "first_name": "Margaret",
      "last_name": "Park"
    },
    {
      "employee_id": 5,
      "first_name": "Steve",
      "last_name": "Johnson"
    }
  ],
  "ordered": true,
  "columns": [
    "employee_id",
    "first_name",
    "last_name"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"employee_id\", \"first_name\", \"last_name\" FROM \"public\".\"employee\" WHERE \"title\" = 'Sales Support Agent' ORDER BY \"employee_id\" ASC LIMIT 200",
  "table": [
    {
      "employee_id": 3,
      "first_name": "Jane",
      "last_name": "Peacock"
    },
    {
      "employee_id": 4,
      "first_name": "Margaret",
      "last_name": "Park"
    },
    {
      "employee_id": 5,
      "first_name": "Steve",
      "last_name": "Johnson"
    }
  ],
  "answer": "查询返回 3 行，详细数据见结果表。",
  "rewritten_question": "列出职位为 Sales Support Agent 的员工编号、名字和姓氏，按员工编号升序。",
  "trace_id": "36ef2468-46e7-4f57-8293-736cd33e3025",
  "truncated": false
}
```

**参考判断理由：**

Sales Suport Agent缺少一个p，实库employee.title真实值Sales Support Agent可唯一支持职位纠错；不新增岗位或员工范围。 员工职位字段employee.title精确筛选Sales Support Agent；返回employee_id、first_name、last_name且编号升序，对应3名员工，没有拼接fullname。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 3 行，详细数据见结果表。”与结果表3行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回3行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-03; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=3; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=3; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=76; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=77; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-07; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-04

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-05

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-06

- 分组：robust；划分：dev

**审核对象：** 列出来自老美的客户编号、城市和州，按客户编号升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;",
  "result": [
    {
      "customer_id": 16,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 17,
      "city": "Redmond",
      "state": "WA"
    },
    {
      "customer_id": 18,
      "city": "New York",
      "state": "NY"
    },
    {
      "customer_id": 19,
      "city": "Cupertino",
      "state": "CA"
    },
    {
      "customer_id": 20,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 21,
      "city": "Reno",
      "state": "NV"
    },
    {
      "customer_id": 22,
      "city": "Orlando",
      "state": "FL"
    },
    {
      "customer_id": 23,
      "city": "Boston",
      "state": "MA"
    },
    {
      "customer_id": 24,
      "city": "Chicago",
      "state": "IL"
    },
    {
      "customer_id": 25,
      "city": "Madison",
      "state": "WI"
    },
    {
      "customer_id": 26,
      "city": "Fort Worth",
      "state": "TX"
    },
    {
      "customer_id": 27,
      "city": "Tucson",
      "state": "AZ"
    },
    {
      "customer_id": 28,
      "city": "Salt Lake City",
      "state": "UT"
    }
  ],
  "ordered": true,
  "columns": [
    "customer_id",
    "city",
    "state"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"customer_id\", \"city\", \"state\" FROM \"public\".\"customer\" WHERE \"country\" = 'USA' ORDER BY \"customer_id\" ASC LIMIT 200",
  "table": [
    {
      "customer_id": 16,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 17,
      "city": "Redmond",
      "state": "WA"
    },
    {
      "customer_id": 18,
      "city": "New York",
      "state": "NY"
    },
    {
      "customer_id": 19,
      "city": "Cupertino",
      "state": "CA"
    },
    {
      "customer_id": 20,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 21,
      "city": "Reno",
      "state": "NV"
    },
    {
      "customer_id": 22,
      "city": "Orlando",
      "state": "FL"
    },
    {
      "customer_id": 23,
      "city": "Boston",
      "state": "MA"
    },
    {
      "customer_id": 24,
      "city": "Chicago",
      "state": "IL"
    },
    {
      "customer_id": 25,
      "city": "Madison",
      "state": "WI"
    },
    {
      "customer_id": 26,
      "city": "Fort Worth",
      "state": "TX"
    },
    {
      "customer_id": 27,
      "city": "Tucson",
      "state": "AZ"
    },
    {
      "customer_id": 28,
      "city": "Salt Lake City",
      "state": "UT"
    }
  ],
  "answer": "查询返回 13 行，详细数据见结果表。",
  "rewritten_question": "列出来自USA的客户编号、城市和州，按客户编号升序。",
  "trace_id": "f1345e19-b84a-432f-9028-1e6fcb480004",
  "truncated": false
}
```

**参考判断理由：**

“老美”在来自某国家的客户语境为美国俗称USA，仍查询客户所在国家；没有把俗称扩张为北美或其他地区。 美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 13 行，详细数据见结果表。”与结果表13行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回13行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-06; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=6; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=4; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=78; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=79; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-05; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-07

- 分组：robust；划分：dev

**审核对象：** 来自意大利的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';",
  "result": [
    {
      "customer_count": 1
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Italy'",
  "table": [
    {
      "customer_count": 1
    }
  ],
  "answer": "查询结果：1。",
  "rewritten_question": "来自Italy的客户有多少位？",
  "trace_id": "058fa77e-0f77-402f-985a-3da5dd09c1b0",
  "truncated": false
}
```

**参考判断理由：**

意大利为Italy的中文国家名称；译名不改变customer.country计数条件。 客户所在国家Italy精确匹配customer.country；COUNT(*)得到1位，未改用invoice账单国家或新增日期条件。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1。”准确陈述标量1，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-07; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=7; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=5; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=80; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=81; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-31; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-08

- 分组：robust；划分：dev

**审核对象：** 来自加拿大的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';",
  "result": [
    {
      "customer_count": 8
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Canada'",
  "table": [
    {
      "count": 8
    }
  ],
  "answer": "查询结果：8。",
  "rewritten_question": "来自Canada的客户有多少位？",
  "trace_id": "3659f041-6485-4220-ad24-0b02205735a4",
  "truncated": false
}
```

**参考判断理由：**

加拿大为Canada的中文国家名称；译名不改变customer.country计数条件。 客户所在国家Canada精确匹配customer.country；COUNT(*)得到8位，区分客户国家与账单国家，未新增发票期间。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：8。”准确陈述标量8，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-08; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=8; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=6; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=82; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=83; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-32; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-09

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-10

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-11

- 分组：robust；划分：dev

**审核对象：** 来自 ba xi 的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';",
  "result": [
    {
      "customer_count": 5
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Brazil'",
  "table": [
    {
      "count": 5
    }
  ],
  "answer": "查询结果：5。",
  "rewritten_question": "来自 Brazil 的客户有多少位？",
  "trace_id": "1181ca69-ef19-4dc1-9c57-fa930bf6a0be",
  "truncated": false
}
```

**参考判断理由：**

ba xi按国家语境读作“巴西”，保留Brazil客户计数；未增加时间、国家并集或账单条件。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-11; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=11; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=7; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=84; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=85; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-02; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-12

- 分组：robust；划分：dev

**审核对象：** 客户所在国家为 yi da li 的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';",
  "result": [
    {
      "customer_count": 1
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Italy'",
  "table": [
    {
      "count": 1
    }
  ],
  "answer": "查询结果：1。",
  "rewritten_question": "客户所在国家为 Italy 的客户有多少位？",
  "trace_id": "7b432a80-e7dc-44d2-a2de-f301492e85fc",
  "truncated": false
}
```

**参考判断理由：**

yi da li按国家语境读作“意大利”，保留Italy客户计数；未因候选相似度将其改成India。 客户所在国家Italy精确匹配customer.country；COUNT(*)得到1位，未改用invoice账单国家或新增日期条件。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1。”准确陈述标量1，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-12; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=12; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=8; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=86; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=87; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-31; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-13

- 分组：robust；划分：dev

**审核对象：** 客户所在国家为 jia na da 的客户有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';",
  "result": [
    {
      "customer_count": 8
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Canada'",
  "table": [
    {
      "customer_count": 8
    }
  ],
  "answer": "查询结果：8。",
  "rewritten_question": null,
  "trace_id": "9c120068-a919-47b3-a2f1-72cb5ca88620",
  "truncated": false
}
```

**参考判断理由：**

jia na da按国家语境读作“加拿大”，保留Canada客户计数；国家对象明确，发音变体未增加题意歧义。 客户所在国家Canada精确匹配customer.country；COUNT(*)得到8位，区分客户国家与账单国家，未新增发票期间。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：8。”准确陈述标量8，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 原值链接trace显示unmatched/无bindings，最终SQL仍正确采用Canada；结果正确性与值链接阶段成功应分开记录。

**发现的问题或限制：**

[
  {
    "object": "nlu_trace",
    "problem": "原NLU把jia na da标为unmatched且bindings为空，但后续已有SQL筛选Canada。最终国家值和计数正确，本次不能据此宣称NLU绑定阶段完成了拼音对齐。",
    "severity": "informational"
  }
]

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。 若评估特定NLU阶段，人工应单独确认拼音对齐由哪一步完成；不改变最终答案建议。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-13; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=13; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=9; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=88; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=89; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-32; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-14

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-15

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-16

- 分组：robust；划分：dev

**审核对象：** country 是 Brazil 的 customer 有多少位？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';",
  "result": [
    {
      "customer_count": 5
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Brazil'",
  "table": [
    {
      "customer_count": 5
    }
  ],
  "answer": "查询结果：5。",
  "rewritten_question": null,
  "trace_id": "e9aba1bd-96f2-40bb-bbdf-d0d0344942dc",
  "truncated": false
}
```

**参考判断理由：**

中英混合显式给出country、Brazil、customer，查询customer.country='Brazil'的人数，语义与基题一致。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-16; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=16; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=10; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=90; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=91; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-02; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-17

- 分组：robust；划分：dev

**审核对象：** 列出 country 为 USA 的客户编号 customer_id、城市 city 和州 state，按 customer_id 升序。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;",
  "result": [
    {
      "customer_id": 16,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 17,
      "city": "Redmond",
      "state": "WA"
    },
    {
      "customer_id": 18,
      "city": "New York",
      "state": "NY"
    },
    {
      "customer_id": 19,
      "city": "Cupertino",
      "state": "CA"
    },
    {
      "customer_id": 20,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 21,
      "city": "Reno",
      "state": "NV"
    },
    {
      "customer_id": 22,
      "city": "Orlando",
      "state": "FL"
    },
    {
      "customer_id": 23,
      "city": "Boston",
      "state": "MA"
    },
    {
      "customer_id": 24,
      "city": "Chicago",
      "state": "IL"
    },
    {
      "customer_id": 25,
      "city": "Madison",
      "state": "WI"
    },
    {
      "customer_id": 26,
      "city": "Fort Worth",
      "state": "TX"
    },
    {
      "customer_id": 27,
      "city": "Tucson",
      "state": "AZ"
    },
    {
      "customer_id": 28,
      "city": "Salt Lake City",
      "state": "UT"
    }
  ],
  "ordered": true,
  "columns": [
    "customer_id",
    "city",
    "state"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT \"customer_id\", \"city\", \"state\" FROM \"public\".\"customer\" WHERE \"country\" = 'USA' ORDER BY \"customer_id\" ASC LIMIT 200",
  "table": [
    {
      "customer_id": 16,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 17,
      "city": "Redmond",
      "state": "WA"
    },
    {
      "customer_id": 18,
      "city": "New York",
      "state": "NY"
    },
    {
      "customer_id": 19,
      "city": "Cupertino",
      "state": "CA"
    },
    {
      "customer_id": 20,
      "city": "Mountain View",
      "state": "CA"
    },
    {
      "customer_id": 21,
      "city": "Reno",
      "state": "NV"
    },
    {
      "customer_id": 22,
      "city": "Orlando",
      "state": "FL"
    },
    {
      "customer_id": 23,
      "city": "Boston",
      "state": "MA"
    },
    {
      "customer_id": 24,
      "city": "Chicago",
      "state": "IL"
    },
    {
      "customer_id": 25,
      "city": "Madison",
      "state": "WI"
    },
    {
      "customer_id": 26,
      "city": "Fort Worth",
      "state": "TX"
    },
    {
      "customer_id": 27,
      "city": "Tucson",
      "state": "AZ"
    },
    {
      "customer_id": 28,
      "city": "Salt Lake City",
      "state": "UT"
    }
  ],
  "answer": "查询返回 13 行，详细数据见结果表。",
  "rewritten_question": null,
  "trace_id": "61e31999-fef7-47d4-9234-131013bb71eb",
  "truncated": false
}
```

**参考判断理由：**

中英混合显式给出USA、customer_id/city/state及customer_id升序，字段与排序要求未改变。 美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 13 行，详细数据见结果表。”与结果表13行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回13行且未截断，本次建议限于已有快照及输出。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-17; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=17; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=11; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=92; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=93; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-05; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-18

- 分组：robust；划分：dev

**审核对象：** 全部 invoice 的 total 加起来是多少？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT SUM(total) AS total_amount FROM invoice;",
  "result": [
    {
      "total_amount": "2328.60"
    }
  ],
  "ordered": false,
  "columns": [
    "total_amount"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT SUM(\"total\") AS total_sum FROM \"public\".\"invoice\"",
  "table": [
    {
      "total_sum": "2328.60"
    }
  ],
  "answer": "查询结果：2328.60。",
  "rewritten_question": null,
  "trace_id": "5331df61-42e6-48c7-a8e6-812176c7653f",
  "truncated": false
}
```

**参考判断理由：**

中英混合显式要求全部invoice的total求和，即发票粒度SUM(total)，没有新增指标或期间。 题目明确“全部发票”，对invoice.total在发票粒度SUM，不连接invoice_line导致重复金额，不增加默认期间、支付状态或币种。参考总额2328.60（数据库金额单位）。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：2328.60。”准确陈述标量2328.60，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-18; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=18; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=12; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=94; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=95; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-09; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-19

- 分组：robust；划分：dev

**审核对象：** billing_country 为 Canada 的全部 invoice 的 total 总和是多少？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Canada';",
  "result": [
    {
      "total_amount": "303.96"
    }
  ],
  "ordered": false,
  "columns": [
    "total_amount"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT SUM(\"total\") FROM \"public\".\"invoice\" WHERE \"billing_country\" = 'Canada'",
  "table": [
    {
      "sum": "303.96"
    }
  ],
  "answer": "查询结果：303.96。",
  "rewritten_question": null,
  "trace_id": "b8d933b5-49eb-43b0-9fb7-8948cb00e8b1",
  "truncated": false
}
```

**参考判断理由：**

显式给出billing_country=Canada、invoice及total，保留发票账单国家字段和全量SUM口径，不借当前地区值一致替换customer.country。 题目明确账单国家Canada，筛选invoice.billing_country而非customer.country；SUM(invoice.total)统计全部匹配发票，结果303.96（数据库金额单位），不做明细JOIN重复计额。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：303.96。”准确陈述标量303.96，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-19; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=19; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=13; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=96; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=97; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-33; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-20

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-21

- 分组：robust；划分：dev

**审核对象：** 咱们客户表一共有几个人？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer;",
  "result": [
    {
      "customer_count": 59
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\"",
  "table": [
    {
      "customer_count": 59
    }
  ],
  "answer": "查询结果：59。",
  "rewritten_question": null,
  "trace_id": "fdb6cf76-668d-4ab4-a305-fbe07c84be49",
  "truncated": false
}
```

**参考判断理由：**

“客户表”“一共几个人”明确指客户记录总数，COUNT(*)口径不变。 对象为客户表全体记录，customer_id 是非空主键；COUNT(*) 每客户计一次，不受其他可空列影响，不加期间或国家过滤。参考结果为59位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：59。”准确陈述标量59，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-21; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=21; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=14; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=98; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=99; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-01; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-22

- 分组：robust；划分：dev

**审核对象：** 帮我数数，来自巴西的客户有几位呀？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';",
  "result": [
    {
      "customer_count": 5
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Brazil'",
  "table": [
    {
      "customer_count": 5
    }
  ],
  "answer": "查询结果：5。",
  "rewritten_question": "帮我数数，来自Brazil的客户有几位呀？",
  "trace_id": "34ebfc90-ce4b-41d8-84f9-4a14527e5f90",
  "truncated": false
}
```

**参考判断理由：**

“帮我数数/几位呀”只是请求语气，巴西客户国家筛选及人数计数均未变化。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-22; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=22; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=15; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=100; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=101; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-02; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-23

- 分组：robust；划分：dev

**审核对象：** 这批曲目的平均长度是几毫秒？

**别名或参考答案判断：** AI建议有条件通过

**系统实际回答判断：** 证据不足

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT AVG(milliseconds) AS average_milliseconds FROM track;",
  "result": [
    {
      "average_milliseconds": "393599.212103910933"
    }
  ],
  "ordered": false,
  "columns": [
    "average_milliseconds"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT AVG(\"milliseconds\") AS average_milliseconds FROM \"public\".\"track\"",
  "table": [
    {
      "average_milliseconds": "393599.212103910933"
    }
  ],
  "answer": "查询结果：393599.212103910933。",
  "rewritten_question": null,
  "trace_id": "56428dad-9b1c-4aa3-9756-86464ff0c59c",
  "truncated": false
}
```

**参考判断理由：**

基题明确“全部曲目”，变体改为“这批曲目”引入未定义的指代范围；原始请求是该单条消息，scope仅指数据库，已有证据没有提供曲目批次或集合。gold直接AVG全track只在“这批=全库曲目”另行确认时成立，不能用base_id或EX相同替代用户范围证据。 基题明确全部曲目及毫秒，基题对应的全库AVG(track.milliseconds)为每条曲目等权平均，没有除1000转秒或按销售数量加权；milliseconds非空，基题的全库结果为393599.212103910933毫秒。该全库结果不能独立证明变体中未定义的“这批”范围。

**实际回答判断理由：**

已有SQL、数值393599.212103910933和自然语言确实对应全库track平均毫秒；但系统未澄清“这批”指哪个集合，也未在intent.assumptions中声明全集假设。缺少范围证据，不能确定全库平均是否回答了用户请求，即使gold和EX相同也暂不能判定正确。

**发现的问题或限制：**

[
  {
    "object": "question",
    "problem": "“全部”改成“这批”新增无前文的指代范围，鲁棒变体未严格保持基题范围。",
    "severity": "conditional"
  },
  {
    "object": "reference",
    "problem": "AVG全表是未声明的全集假设；只有确认“这批=全部曲目”后参考才可接受。",
    "severity": "conditional"
  },
  {
    "object": "actual",
    "problem": "范围不明仍直接全表AVG，原输出缺少范围澄清，最终正确性证据不足。",
    "severity": "insufficient_evidence"
  }
]

**建议处理方式：**

人工确认指代集合；若目标为保持基题语义，应将变体范围说清楚，或补充合法上下文再独立核对。不能通过改参考平均值来使系统过关。

**仍需人工确认：**

需要确认“这批”具体指哪些曲目；该确认到位前，实际回答暂不能确定。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-23; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=23; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=16; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=102; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=103; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-10; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-24

- 分组：robust；划分：dev

**审核对象：** 曲目里最短的一首有几毫秒呀？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT MIN(milliseconds) AS minimum_milliseconds FROM track;",
  "result": [
    {
      "minimum_milliseconds": 1071
    }
  ],
  "ordered": false,
  "columns": [
    "minimum_milliseconds"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT MIN(\"milliseconds\") AS \"min_milliseconds\" FROM \"public\".\"track\"",
  "table": [
    {
      "min_milliseconds": 1071
    }
  ],
  "answer": "查询结果：1071。",
  "rewritten_question": null,
  "trace_id": "b79d1209-362e-4424-af3f-2aa71143bb5f",
  "truncated": false
}
```

**参考判断理由：**

“曲目里最短的一首有几毫秒呀”请求最短时长值，语气变化不引入期间、销量或指定曲目集合；MIN(milliseconds)与基题一致。 最短时长取MIN(track.milliseconds)，milliseconds非空，得到1071毫秒；题目只要最短值，标量聚合正确，无需返回任意一首同长曲目的姓名或编号。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1071。”准确陈述标量1071，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-24; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=24; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=17; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=104; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=105; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-34; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-25

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### robust:robust-26

- 分组：robust；划分：dev

**审核对象：** 你好，请帮忙查一下来自巴西的客户有多少位，谢谢。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';",
  "result": [
    {
      "customer_count": 5
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Brazil'",
  "table": [
    {
      "count": 5
    }
  ],
  "answer": "查询结果：5。",
  "rewritten_question": "你好，请Brazil的客户有多少位，谢谢。",
  "trace_id": "2eda7ea4-1bb3-4c01-a128-6db68a305939",
  "truncated": false
}
```

**参考判断理由：**

“你好/请帮忙/谢谢”属于礼貌冗词，来自巴西的客户人数条件完整且与基题一致，没有新增约束。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 中间rewritten_question吞掉请求词，单独标记改写质量问题；最终SQL仍保留客户国家Brazil的条件和5位计数，不能因此误判最终答案错误。

**发现的问题或限制：**

[
  {
    "object": "rewrite",
    "problem": "原mention跨度[4,13]包含“帮忙查一下来自巴西”，整体替换Brazil后改写为“你好，请Brazil的客户有多少位，谢谢。”，吞掉了请求词与来自关系。最终已有SQL仍筛选customer.country=Brazil且结果5位正确。",
    "severity": "rewrite_quality"
  }
]

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。 人工单独核对改写跨度及语句通顺程度；保留最终输出正确性的独立判断。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-26; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=26; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=18; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=106; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=107; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-02; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-27

- 分组：robust；划分：dev

**审核对象：** 麻烦帮我看看，有多少位客户没有填写公司名称，也就是 company 为 NULL 呢？谢谢。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE company IS NULL;",
  "result": [
    {
      "customer_count": 49
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"company\" IS NULL",
  "table": [
    {
      "count": 49
    }
  ],
  "answer": "查询结果：49。",
  "rewritten_question": null,
  "trace_id": "f36616a2-7155-40eb-87bc-0de2cb0ff913",
  "truncated": false
}
```

**参考判断理由：**

礼貌冗词之外明确重申company为NULL，仍用IS NULL统计客户，不将NULL变成空串。 题目明确定义company为NULL，使用IS NULL而非等于NULL、空串或COUNT(company)；COUNT(*)得到49位，实库company空字符串为0，未改变NULL语义。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：49。”准确陈述标量49，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-27; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=27; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=19; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=108; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=109; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-26; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-28

- 分组：robust；划分：dev

**审核对象：** 请帮我查一查，2023 年一共开了多少张发票，非常感谢。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01';",
  "result": [
    {
      "invoice_count": 83
    }
  ],
  "ordered": false,
  "columns": [
    "invoice_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) AS invoice_count FROM \"public\".\"invoice\" WHERE \"invoice_date\" >= '2023-01-01' AND \"invoice_date\" < '2024-01-01'",
  "table": [
    {
      "invoice_count": 83
    }
  ],
  "answer": "查询结果：83。",
  "rewritten_question": null,
  "trace_id": "f26717a4-88bc-4f8d-b074-6787350cecad",
  "truncated": false
}
```

**参考判断理由：**

礼貌冗词之外保留2023年开票数量，半开年度范围及COUNT(*)均不变。 2023年开票数以invoice.invoice_date范围[2023-01-01,2024-01-01)过滤，再COUNT(*)；实库2023年83张，与当前日期无关，不把发票行数当发票数。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：83。”准确陈述标量83，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-28; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=28; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=20; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=110; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=111; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-39; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-29

- 分组：robust；划分：dev

**审核对象：** 麻烦查一下客户所在国家为 Wakanda 的客户有多少位，保留原值，没匹配返回 0，谢谢。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**参考SQL与保存结果：**

```json
{
  "sql": "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Wakanda';",
  "result": [
    {
      "customer_count": 0
    }
  ],
  "ordered": false,
  "columns": [
    "customer_count"
  ]
}
```

**已有系统SQL、表格与回答：**

```json
{
  "status": "SUCCEEDED",
  "sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Wakanda'",
  "table": [
    {
      "customer_count": 0
    }
  ],
  "answer": "查询结果：0。",
  "rewritten_question": null,
  "trace_id": "e4ebcd08-1d74-4d68-aa72-db21dabf4e8d",
  "truncated": false
}
```

**参考判断理由：**

礼貌冗词之外保留客户国家Wakanda、原值保护和无匹配返回0，COUNT(*)口径不变。 明确保留Wakanda原值，country = 'Wakanda'在实库无匹配；COUNT(*)自然返回0，未纠错到真实国家、未返回空列表或NULL。

**实际回答判断理由：**

已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：0。”准确陈述标量0，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

**建议处理方式：**

保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

**仍需人工确认：**

待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

**证据文件及具体位置：**

- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=robust:robust-29; note=仅dev题干、参考和已有输出
- [eval/datasets/robust.jsonl](../../datasets/robust.jsonl) — line=29; note=原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- [eval/artifacts/d2/robust/final/responses.jsonl](../../artifacts/d2/robust/final/responses.jsonl) — line=21; note=原请求、SQL、结果表、答案、intent和步骤
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=112; note=重执行已有参考SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/sql-verification.jsonl](../../artifacts/d2-ai-preaudit/sql-verification.jsonl) — line=113; note=重执行已有系统SELECT，真实结果与耗时
- [eval/artifacts/d2-ai-preaudit/database-materials.json](../../artifacts/d2-ai-preaudit/database-materials.json) — section=schema; row_counts; text_values; note=真实字段/可空性/英文值，不以别名候选本身证明题意
- [data/catalog/chinook.yaml](../../../data/catalog/chinook.yaml) — section=tables; note=结构、外键、字段含义与单位
- [data/rules/metric_definitions.json](../../../data/rules/metric_definitions.json) — section=general; metrics; note=已确认项目口径、半开期间、金额单位及NULL规则
- [eval/reports/d2-acceptance/unified-review.json](../d2-acceptance/unified-review.json) — section=nl2sql:sql-44; note=基题也属于dev；逐项对照变体是否改变题意

### robust:robust-30

- 分组：robust；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-01

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-02

- 分组：rag；划分：dev

**审核对象：** How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

45 days

**RAG已有系统回答：**

PSS must publish the financial results of post-Merger combined operations within 45 days after the end of the first fiscal quarter of PSS containing the required period of post-Merger combined operations. [E1]

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

原OHR问题和45 days答案精确相同。原PDF物理第1页第2条先限定PSS与GSMS合并经营财务结果，再约定在包含所需合并经营期间的PSS首个财政季度结束后45天内发布；不是从合并日直接起算45天。题问天数，gold对象、起算期间和单位均正确。

**实际回答判断理由：**

实际回答保留包含所需合并经营期间的财政季度这一限制，并正确回答within 45 days。E1为该页第2条完整有关段落，既有发布对象又有45天及起算点，能完整支撑回答。

**建议处理方式：**

保留当前gold；人审时确认财政季度起算限制随题目和答案一起保存。

**仍需人工确认：**

请确认45 days是该特定财政季度结束后的上限，并据原页作最终人工签核。

**证据文件及具体位置：**

- [data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf](../../../data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf) — page=1; section=2. Initial Restriction on Disposition; source_sha256=a4a646e9e36567c91424c29b05790d04b780df57f05342758f4a63e2b2bdbeef; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p1.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p1.txt) — page=1; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p1.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p1.png) — page=1; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=2868c76b-7a94-4483-a8ce-122009b12bc9; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=2; section=rag-02 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=1; section=rag-02 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-02
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-02
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-02-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-02-E1-cropbox-outline.png) — page=1; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-03

- 分组：rag；划分：dev

**审核对象：** For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

three years

**RAG已有系统回答：**

PSS agrees to file all reports required by Section 13 of the Securities Exchange Act of 1934 for a period of three years after the effective date of the Merger [E1][E5].

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

原OHR question/answer和本题精确一致。原PDF物理第2页第6条规定PSS在Merger effective date后为期three years及时提交1934年法案Section 13要求的报告；gold三年对应报告义务期限，不是股票限制交易的另一期限。

**实际回答判断理由：**

实际答案正确说明合并生效日后三年。E5保留第6条标题行及three years，E1保留紧接的effective date、报告内容和Section 13；两条在同一物理页、同一条款，合读足够支持回答。E1单独不含three years，但回答同时引用E5，未据孤立片段判断。

**建议处理方式：**

保留标准和当前回答；展示引用时使E1、E5的同条款关系可见。

**仍需人工确认：**

请核实E1和E5合起来覆盖three years、effective date和Section 13。

**证据文件及具体位置：**

- [data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf](../../../data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf) — page=2; section=6. Filing of Reports by PSS; source_sha256=a4a646e9e36567c91424c29b05790d04b780df57f05342758f4a63e2b2bdbeef; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p2.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p2.txt) — page=2; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p2.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-law-affiliate-physical-p2.png) — page=2; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=28805c5d-ad1b-4f60-89e4-dab20edc6d2b; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=3; section=rag-03 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=2; section=rag-03 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-03
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-03
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-03-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-03-E1-cropbox-outline.png) — page=2; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-03-E5-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-03-E5-cropbox-outline.png) — page=2; section=E5 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-04

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-05

- 分组：rag；划分：dev

**审核对象：** Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

Tame and Etherow

**RAG已有系统回答：**

On the western side of the primary watershed, the drainage is to the Mersey by the rivers Tame and Etherow [E1].

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR问题、Tame and Etherow答案和物理页转换均匹配。完整第1页先定义North Sea与Irish Sea之间的primary watershed，再说明该线西侧经Tame、Etherow流入Mersey；东侧Calder、Don等及南侧Trent另有说明，不能混为答案。

**实际回答判断理由：**

实际回答准确给出Tame and Etherow并指出排向Mersey。E1为原页西侧排水完整句，与前段分水岭上下文对应，支持两个河名及流向。 原文定位复核：原地质扫描PDF隐藏文字层的bbox=[22.92,516.71,233.1,577.03]可裁出西侧河流文字，但Poppler真实可视页红框落在更低的Don/Derwent及南侧分水岭段落，不覆盖可视Tame/Etherow原句。原页MediaBox=CropBox且无旋转，不能用裁切原点偏移解释。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "原地质扫描PDF隐藏文字层的bbox=[22.92,516.71,233.1,577.03]可裁出西侧河流文字，但Poppler真实可视页红框落在更低的Don/Derwent及南侧分水岭段落，不覆盖可视Tame/Etherow原句。原页MediaBox=CropBox且无旋转，不能用裁切原点偏移解释。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留当前gold及回答；引文定位保持物理第1页。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请确认西侧两河与前文primary watershed指同一分水岭。

**证据文件及具体位置：**

- [data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf](../../../data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf) — page=1; section=CHAPTER I / INTRODUCTION; source_sha256=e7be7af7c911cccf6d391934ef062db94d10b1496659828d649af36201616612; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p1.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p1.txt) — page=1; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p1.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p1.png) — page=1; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=9c546b13-f581-4c4c-bdb3-784510aac204; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=5; section=rag-05 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=3; section=rag-05 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-05
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-05
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-05-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-05-E1-cropbox-outline.png) — page=1; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-06

- 分组：rag；划分：dev

**审核对象：** What are the most satisfactory arable crops grown in the soils of the Coal Measures?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

Wheat, oats, and potatoes

**RAG已有系统回答：**

Wheat, oats and potatoes are perhaps the most satisfactory arable crops grown in the soils of the Coal Measures [E1].

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR题答精确对应。完整物理第8页首段以Coal Measures的土壤为对象，明确列Wheat、oats、potatoes为perhaps the most satisfactory arable crops，并说明swedes和turnips可能受病害；gold三种作物正确，未混入另述的树种或不适宜作物。

**实际回答判断理由：**

实际答案正确列出三种作物，并保留perhaps语气。E1含Coal Measures土壤条件、三种作物和其他作物病害的连续段落，足够支撑对象和推荐限定。 原文定位复核：bbox=[36.12,245.41,246.9,381.44]在隐藏文字层能取出作物段，真实扫描页红框却落在Table of Formations说明段，不覆盖页面上方Coal Measures作物原句。文字层命中不等于视觉坐标准确。 section_path使用本页running header，属于粗粒度页眉提示；不将页眉当作真实细分章节。上述bbox错误按真实渲染图判断，不能被隐藏文字层的裁切文字覆盖。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "bbox=[36.12,245.41,246.9,381.44]在隐藏文字层能取出作物段，真实扫描页红框却落在Table of Formations说明段，不覆盖页面上方Coal Measures作物原句。文字层命中不等于视觉坐标准确。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留列表gold；人工解释宜保留原文perhaps，不扩展为现代农业普遍结论。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请核实本题仅评价原文所述Coal Measures土壤里的作物。

**证据文件及具体位置：**

- [data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf](../../../data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf) — page=8; section=物理第8页首段 / Coal Measures soils; source_sha256=e7be7af7c911cccf6d391934ef062db94d10b1496659828d649af36201616612; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.txt) — page=8; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.png) — page=8; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=9c6725b2-7765-4a0a-95a6-ee8b3ced1be5; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=6; section=rag-06 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=4; section=rag-06 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-06
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-06
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-06-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-06-E1-cropbox-outline.png) — page=8; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-07

- 分组：rag；划分：dev

**审核对象：** What is the thickness range of the Shale Grit in the southern part of the Sheet?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

450 to 550 feet

**RAG已有系统回答：**

The Shale Grit is 450 to 550 feet thick in the southern part of the Sheet. [E1]

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR question/answer精确一致。完整物理第14页General Stratigraphy段规定Shale Grit在Sheet南部的moors厚450 to 550 feet；后句另谈Etherow/Tame河谷暴露。gold保留地层、南部空间范围及feet单位，正确。

**实际回答判断理由：**

实际回答450 to 550 feet in the southern part of the Sheet，未换成米或全区统一厚度。E1对应该页明确厚度句，可支撑数值、单位和空间限制。 原文定位复核：bbox=[40.68,403.4,250.62,475.17]在隐藏文字层能取出450至550 feet句，真实扫描页红框位于更低的砂岩特征/Grindslow Shales段，不覆盖可视Shale Grit厚度句。原页和答案正确，但框选定位错位。 section_path使用本页running header，属于粗粒度页眉提示；不将页眉当作真实细分章节。上述bbox错误按真实渲染图判断，不能被隐藏文字层的裁切文字覆盖。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "bbox=[40.68,403.4,250.62,475.17]在隐藏文字层能取出450至550 feet句，真实扫描页红框位于更低的砂岩特征/Grindslow Shales段，不覆盖可视Shale Grit厚度句。原页和答案正确，但框选定位错位。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留当前gold和回答；人审检查feet与Sheet南部限定。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请确认范围是450至550英尺且仅对应Sheet南部。

**证据文件及具体位置：**

- [data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf](../../../data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf) — page=14; section=General Stratigraphy / The Shale Grit; source_sha256=e7be7af7c911cccf6d391934ef062db94d10b1496659828d649af36201616612; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p14.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p14.txt) — page=14; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p14.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p14.png) — page=14; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=9c7b49ee-0599-4b64-890a-58b48b8f0f0d; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=7; section=rag-07 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=5; section=rag-07 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-07
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-07
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-07-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-07-E1-cropbox-outline.png) — page=14; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-08

- 分组：rag；划分：dev

**审核对象：** In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

The Rough Rock Series, the Middle Grits, the Kinderscout Grits, and the Shale Grit

**RAG已有系统回答：**

In the Millstone Grits, the grits and sandstones are shown by four colours for the main groups, namely: The Rough Rock Series, the Middle Grits, the Kinderscout Grits and the Shale Grit [E1]。

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR题答精确一致。原物理第8页Table of Formations前说明Millstone Grits中的shales统一着色，而grits和sandstones按四主组着色，随后逐项列Rough Rock Series、Middle Grits、Kinderscout Grits、Shale Grit；gold四项齐全且未把shales加入。

**实际回答判断理由：**

实际回答完整列出原文四组并说明grits与sandstones四色；E1含原页有关列举段，四名称、组数和对象均有来源。 原文定位复核：bbox=[37.68,383.95,247.98,534.78]在隐藏文字层能取出四组图例说明，真实扫描页红框却位于Superficial/Solid Formations表，不覆盖上方可视四组列举句。原文字层与图像坐标不齐。 section_path使用本页running header，属于粗粒度页眉提示；不将页眉当作真实细分章节。上述bbox错误按真实渲染图判断，不能被隐藏文字层的裁切文字覆盖。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "bbox=[37.68,383.95,247.98,534.78]在隐藏文字层能取出四组图例说明，真实扫描页红框却位于Superficial/Solid Formations表，不覆盖上方可视四组列举句。原文字层与图像坐标不齐。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留当前gold和回答，不把图例组数理解为地质总层数。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请确认四项名称和地图中grits/sandstones着色这一对象。

**证据文件及具体位置：**

- [data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf](../../../data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf) — page=8; section=Table of Formations前说明段; source_sha256=e7be7af7c911cccf6d391934ef062db94d10b1496659828d649af36201616612; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.txt) — page=8; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-textbook-geology-physical-p8.png) — page=8; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=9c6a4f19-6165-4ec6-b91d-55c727357c1d; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=8; section=rag-08 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=6; section=rag-08 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-08
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-08
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-08-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-08-E1-cropbox-outline.png) — page=8; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-09

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-10

- 分组：rag；划分：dev

**审核对象：** What type of digital device classification is specified for the equipment in accordance with the FCC rules?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

Class B

**RAG已有系统回答：**

The equipment is specified as a Class B digital device in accordance with the specifications in Part 15 of FCC rules [E1].

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

原OHR题答相同，原页索引64转换为物理第65页正确。原页左栏Radio and Television Interference段确写Class B digital device与Part 15 FCC rules。reference_text的Part 1 5是排版/OCR空格差异，不影响Class B答案。

**实际回答判断理由：**

实际回答Class B并正确写Part 15。E1机械上与索引精确对应，但其text混入右栏关于未授权修改的句子；原页视觉核对确认Class B句完整位于左栏，数字和分类语义成立。该读取顺序瑕疵未导致本题答错。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E1.text",
    "problem": "双栏提取交错右栏Important句，影响引文可读性；原页已视觉确定左栏Class B句，本题支撑仍成立。",
    "severity": "提示"
  }
]

**建议处理方式：**

人审可通过本题语义；登记双栏读取顺序问题供后续资料处理另案修正，本次不改索引或gold。

**仍需人工确认：**

请看原第65页左栏确认Class B，不把E1交错文本当连续原段。

**证据文件及具体位置：**

- [data/docs/raw/manual/Macbook_air.pdf](../../../data/docs/raw/manual/Macbook_air.pdf) — page=65; section=Regulatory Compliance Information / Radio and Television Interference（左栏）; source_sha256=d99de99131b4d8a5471d3e3d96befaa1e6152560d12a93f854c5dd95e54225aa; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p65.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p65.txt) — page=65; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p65.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p65.png) — page=65; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=3ff0b97a-a1f9-4f23-ae4e-8052329d0a1d; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=10; section=rag-10 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=7; section=rag-10 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-10
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-10

### rag:rag-11

- 分组：rag；划分：dev

**审核对象：** Which application allows you to create and share movies in minutes?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

iMovie

**RAG已有系统回答：**

iMovie allows you to create and share movies in minutes. [E1]

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR question/answer和物理第3页对应。reference_text本身只有Create and share movies in minutes描述，需通过原页空间关系确认应用名；已完整渲染查看，左上iMovie标签下直接排列该描述，右上iPhoto描述为照片，gold iMovie正确。

**实际回答判断理由：**

实际回答iMovie。E1文本含iMovie/iPhoto并出现交错两栏，单靠线性字串不足区分应用；原页完整视觉检查确认影片描述归属iMovie。因此引用可支持结论，依据包括原页布局，而非仅词面命中。 原文定位复核：E1 bbox=[27.21,99.39,325.38,117.81]；考虑原PDF CropBox偏移(129,219)后，仅框到iMovie/iPhoto网址与Help行，未覆盖Create and share movies in minutes描述。section_path=[]只是未登记章节，本身不判错。

**发现的问题或限制：**

[
  {
    "object": "reference_text; actual_evidence.E1.text",
    "problem": "引用描述与应用名的归属依赖原页卡片布局；线性提取与iPhoto交错，已用原页视觉补足核验。",
    "severity": "提示"
  },
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "E1 bbox=[27.21,99.39,325.38,117.81]；考虑原PDF CropBox偏移(129,219)后，仅框到iMovie/iPhoto网址与Help行，未覆盖Create and share movies in minutes描述。section_path=[]只是未登记章节，本身不判错。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留iMovie；人工审核随附原页PNG，对照左上卡片。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请确认左上iMovie标题与影片描述的视觉归属。

**证据文件及具体位置：**

- [data/docs/raw/manual/Macbook_air.pdf](../../../data/docs/raw/manual/Macbook_air.pdf) — page=3; section=物理第3页左上iMovie应用卡片; source_sha256=d99de99131b4d8a5471d3e3d96befaa1e6152560d12a93f854c5dd95e54225aa; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p3.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p3.txt) — page=3; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p3.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p3.png) — page=3; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=401f8134-c3e5-4827-82bc-0550dfeddf7e; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=11; section=rag-11 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=8; section=rag-11 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-11
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-11
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-11-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-11-E1-cropbox-outline.png) — page=3; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-12

- 分组：rag；划分：dev

**审核对象：** What is the primary goal of the ENERGY STAR program in which Apple participates?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

To promote energy-efficient products.

**RAG已有系统回答：**

The ENERGY STAR program is a partnership with electronic equipment manufacturers to promote energy-efficient products; reducing energy consumption of products saves money and helps conserve valuable resources [E1]. As an ENERGY STAR partner, Apple has determined that standard configurations of this product meet the ENERGY STAR guidelines for energy efficiency [E2].

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

原OHR题答完全匹配。物理第67页ENERGY STAR Compliance段明确该计划是与电子设备制造商合作以promote energy-efficient products；gold目标正确，不能误当仅指默认休眠10分钟。

**实际回答判断理由：**

实际答对推广节能产品，并补述节约金钱/资源及Apple标准配置符合指南。E1涵盖推广目标及money/resources，E2涵盖Apple参与和标准配置，原页左栏连续段落均有依据；未将VCCI段当作ENERGY STAR内容。

**建议处理方式：**

保留当前gold和实际回答；审核Apple补充句时同时看E2。

**仍需人工确认：**

请确认问题问计划推广目标，E1/E2各自覆盖实际回答的补充说明。

**证据文件及具体位置：**

- [data/docs/raw/manual/Macbook_air.pdf](../../../data/docs/raw/manual/Macbook_air.pdf) — page=67; section=ENERGY STAR Compliance（左栏）; source_sha256=d99de99131b4d8a5471d3e3d96befaa1e6152560d12a93f854c5dd95e54225aa; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p67.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p67.txt) — page=67; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p67.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p67.png) — page=67; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=406b40fe-fcde-40fe-bf9f-52c728a96c64; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=12; section=rag-12 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=9; section=rag-12 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-12
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-12
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-12-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-12-E1-cropbox-outline.png) — page=67; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-12-E2-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-12-E2-cropbox-outline.png) — page=67; section=E2 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-13

- 分组：rag；划分：dev

**审核对象：** Which device can be used to share one IP address among multiple computers?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

AirPort Base Station

**RAG已有系统回答：**

You can use an AirPort Base Station to share one IP address among multiple computers. A router capable of sharing the connection, also known as network address translation (NAT) or "IP masquerading," is required if the ISP provides only one IP address. [E1][E2]

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR question/answer和物理页号相符。完整物理第52页条件是多电脑共享网络且ISP仅给一个IP地址，原文明确AirPort Base Station可用于共享；gold设备名称正确。

**实际回答判断理由：**

实际回答AirPort Base Station，另补仅一个IP时需具有共享能力的路由器/NAT。E2直接支持设备，E1支持前提及NAT/IP masquerading术语，两条同页连续，补述正确且有引文。 原文定位复核：“4 Follow the onscreen instructions.”是Network Diagnostics步骤4，而非共享IP段落的章节标题；字段把步骤文本误登记为章节。PDF物理第52页正确，CropBox偏移后bbox能包含支持句，不据MediaBox未平移裁切结果误判坐标。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E1/E2.section_path",
    "problem": "“4 Follow the onscreen instructions.”是Network Diagnostics步骤4，而非共享IP段落的章节标题；字段把步骤文本误登记为章节。PDF物理第52页正确，CropBox偏移后bbox能包含支持句，不据MediaBox未平移裁切结果误判坐标。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留当前设备gold与回答，勿把只有一个IP的条件外推到所有ISP配置。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请确认E1支持条件和NAT，E2支持AirPort设备名称。

**证据文件及具体位置：**

- [data/docs/raw/manual/Macbook_air.pdf](../../../data/docs/raw/manual/Macbook_air.pdf) — page=52; section=Chapter 3 Problem, Meet Solution / Internet connection共享段; source_sha256=d99de99131b4d8a5471d3e3d96befaa1e6152560d12a93f854c5dd95e54225aa; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p52.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p52.txt) — page=52; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p52.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-manual-macbook-air-physical-p52.png) — page=52; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=410616bd-66bf-45f8-9cbe-3e7a74e0da1e; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=13; section=rag-13 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=10; section=rag-13 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-13
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-13
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-13-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-13-E1-cropbox-outline.png) — page=52; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-13-E2-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-13-E2-cropbox-outline.png) — page=52; section=E2 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-14

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-15

- 分组：rag；划分：dev

**审核对象：** What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

leadership,culture,strategy execution,management practices,robust process improvement

**RAG已有系统回答：**

ASQ and Forbes Insights identified five fundamental capabilities essential for building a successful organizational culture: leadership, culture, strategy execution, management practices, and robust process improvement [E1][E3].

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR题答、doc_entry和物理第10页精确对应。原页Leading for Excellence首段署明ASQ/Forbes Insights研究，ELEMENTS OF SUCCESS段列五能力；完整第11页红色重述亦列相同五项。gold完整且管理实践/稳健流程改进未漏。

**实际回答判断理由：**

实际答案五项齐全。E1是第11页重述的截断部分，末尾robust pro-尚未完整；E3是第10页Elements of Success含完整robust process improvement的段落。合读E3足以支撑完整清单，不能称E1独自覆盖五项。 原文定位复核：E1 bbox=[432.28,50.71,534.6,66.45]在原第11页只框到EYE ON QUALITY页眉，不覆盖五能力正文。E3第10页物理页/Elements of Success定位正确，故回答语义仍可获充分支持。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E1.bbox",
    "problem": "E1 bbox=[432.28,50.71,534.6,66.45]在原第11页只框到EYE ON QUALITY页眉，不覆盖五能力正文。E3第10页物理页/Elements of Success定位正确，故回答语义仍可获充分支持。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留清单和回答；人审据第10页完整句，记录E1截断但E3补足。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请确认五项均存在于E3，ASQ/Forbes归属来自文章首段。

**证据文件及具体位置：**

- [data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf](../../../data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf) — page=10; section=Leading for Excellence / ELEMENTS OF SUCCESS; source_sha256=48981bbfdaf170bfc2ffceae813f17b49e528cb3cde75bac3b48b532b30e4274; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p10.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p10.txt) — page=10; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p10.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p10.png) — page=10; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=864962b3-e99e-4364-a7da-a98e470a03a9; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=15; section=rag-15 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=11; section=rag-15 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-15
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-15
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-15-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-15-E1-cropbox-outline.png) — page=11; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-16

- 分组：rag；划分：dev

**审核对象：** What percentage of senior leaders rate their quality programs as world class or advanced according to the research?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

71%

**RAG已有系统回答：**

According to the research, 71% of senior leaders rate their quality programs as world class or at least advanced. [E1]

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR题答精确匹配。物理第11页RANKINGS OF QUALITY PROGRAMS段明确71% of senior leaders评价world class or at least advanced；同页交代调查1,010 senior leaders与1,281 quality professionals。后述60%是另一受访组对average/below average的评价，不能替代本题71%。

**实际回答判断理由：**

实际回答71%并保留senior leaders、world class/at least advanced。E1虽含两栏交错文本，原页左下原段视觉确认百分比对应高层领导评价而非右栏医院认可次数；回答对象、比例和评级范围均正确。 原文定位复核：登记BUILDING A NEW CULTURE，但71%句属物理第11页左栏RANKINGS OF QUALITY PROGRAMS；邻右栏章节被错误继承。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E1.text",
    "problem": "双栏交错插入医院经验句，已按原页左栏确认71%对应senior leaders。",
    "severity": "提示"
  },
  {
    "object": "actual_evidence.E1.section_path",
    "problem": "登记BUILDING A NEW CULTURE，但71%句属物理第11页左栏RANKINGS OF QUALITY PROGRAMS；邻右栏章节被错误继承。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留71%；人工终审检查受访者组别，避免与quality professionals的60%混用。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请确认分母/对象是senior leaders，71%对应world class或至少advanced。

**证据文件及具体位置：**

- [data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf](../../../data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf) — page=11; section=RANKINGS OF QUALITY PROGRAMS（左栏）；研究样本说明; source_sha256=48981bbfdaf170bfc2ffceae813f17b49e528cb3cde75bac3b48b532b30e4274; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p11.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p11.txt) — page=11; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p11.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-news-executive-insight-physical-p11.png) — page=11; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=864cce95-3e97-4b9e-a362-bc243927e72b; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=16; section=rag-16 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=12; section=rag-16 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-16
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-16

### rag:rag-17

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-18

- 分组：rag；划分：dev

**审核对象：** What is the correlation between attention distributions on label words and the model's final prediction quantified by?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

AUCROC score

**RAG已有系统回答：**

The correlation between attention distributions on the label words of the target position and the model's final prediction is quantified using the AUC-ROC score. [E2] The AUCROC for deep layers approaches 0.8, illustrating a strong correlation between the attention distributions on label words of the target position and the model's final prediction. [E4]

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR问题、AUCROC score答案和物理第12页对应。原页Appendix E给出把目标位置label-word注意力当分类器预测、相对于模型实际输出计算AUC-ROC的定义；物理第5页2.3.1与2.3.2也一致。gold量化指标正确。

**实际回答判断理由：**

核心答案AUC-ROC正确。补述deep layers approaches 0.8可由E4及原第5页支持，原研究的GPT2-XL/GPT-J四数据集平均上下文已核对。E2文本确出自原第12页，但section_path标Limitations，真实段属Appendix E Details for the Calculation of AUCROC；E4标题也混入右栏邻句。doc_id与physical page、正文支撑有效，章节定位需人工确认后修订建议另案处理。 原文定位复核：E2登记Limitations，原第12页属于Appendix E Details for the Calculation of AUCROC。E4的2.3.2标题混入右栏to denote them等正文。章节定位明确错误；doc_id/物理页和实际语义仍正确。

**发现的问题或限制：**

[
  {
    "object": "actual_evidence.E2/E4.section_path",
    "problem": "E2登记Limitations，原第12页属于Appendix E Details for the Calculation of AUCROC。E4的2.3.2标题混入右栏to denote them等正文。章节定位明确错误；doc_id/物理页和实际语义仍正确。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

核心答案可保留。人工终审按原第12页Appendix E及第5页2.3.2确认引用；建议后续单独修复章节定位，若只需简答可省去未被问题要求的0.8补述。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请确认核心答案和0.8补述有原文支持，并明确E2章节定位错误如何处置；本报告未更改索引。

**证据文件及具体位置：**

- [data/docs/raw/academic/2305.14160v4.pdf](../../../data/docs/raw/academic/2305.14160v4.pdf) — page=12; section=E. Details for the Calculation of AUCROC（原第12页左栏开始、右栏续文）; source_sha256=035b1659c5305a0c8157594cf41446fe72ade8d48efa99eb036dfa522d3431c4; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [data/docs/raw/academic/2305.14160v4.pdf](../../../data/docs/raw/academic/2305.14160v4.pdf) — source_sha256=035b1659c5305a0c8157594cf41446fe72ade8d48efa99eb036dfa522d3431c4; verified_from=原始PDF完整物理页提取及视觉检查; page=5; section=2.3.1 Experiments / 2.3.2 Results and Analysis / Figure 5
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p5.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p5.txt) — page=5; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p5.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p5.png) — page=5; section=完整物理页Poppler渲染；已视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p12.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p12.txt) — page=12; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p12.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p12.png) — page=12; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=5710c060-2ea2-4ca2-9fda-de0ea9b0a8ae; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=18; section=rag-18 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=13; section=rag-18 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-18
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-18

### rag:rag-19

- 分组：rag；划分：dev

**审核对象：** Which datasets showed significant performance enhancement with the proposed anchor reweighting method?

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议有条件通过

**RAG标准答案：**

SST-2 and EmoC

**RAG已有系统回答：**

根据表1，所提出的锚点重加权方法在SST-2和EmoC数据集上显著提升了ICL性能，尤其在SST-2（从64.75提升至90.07）和EmoC（从15.44提升至41.64）数据集上表现突出 [E1][E5]。

**RAG题目来源类型：**

OHR原题

**RAG答案正确性：**

AI建议有条件通过

**RAG引用支撑性：**

AI建议有条件通过

**RAG引用定位正确性：**

AI发现错误

**参考判断理由：**

原OHR问答、SST-2 and EmoC与物理第6页对应。完整第6页3.1.3明确particularly on the SST-2 and EmoC datasets，第7页Table 1说明Anchor Re-weighting整体结果。gold是在作者特别强调的数据集层次回答，未错误声称其他数据集完全无提升。

**实际回答判断理由：**

核心SST-2/EmoC答案正确且E1直接支持。新增SST-2 64.75→90.07与EmoC 15.44→41.64各数字确在E5表1，但64.75是Vanilla 5-shot，15.44是Vanilla 1-shot，90.07/41.64是Anchor 1-shot。原第6页3.1.2明确设置两套baseline，故这些提升数值只有分别标明基线才有清晰实验含义；当前回答未区分两套基线，不能只因数字出现就视作完整语义支撑。E5 section_path亦为邻页续句而非Table 1定位。 原文定位复核：E1 bbox=[70.87,486.56,152.06,499.36]在原第6页裁到左栏“In this equation, βi”方程说明，不覆盖右栏3.1.3核心支持句。E5章节路径“0 role that anchors play in ICL.”是前页续句/公式残片，原文位置是第7页Table 1。

**发现的问题或限制：**

[
  {
    "object": "actual_answer.补充提升数值",
    "problem": "SST-2比较采用Vanilla 5-shot基线，EmoC采用Vanilla 1-shot基线；回答未说明两者不同。单个数字正确不等于比较语义完整。",
    "severity": "需人工确认"
  },
  {
    "object": "actual_evidence.E1.bbox; E5.section_path",
    "problem": "E1 bbox=[70.87,486.56,152.06,499.36]在原第6页裁到左栏“In this equation, βi”方程说明，不覆盖右栏3.1.3核心支持句。E5章节路径“0 role that anchors play in ICL.”是前页续句/公式残片，原文位置是第7页Table 1。",
    "severity": "error",
    "category": "citation_location"
  }
]

**建议处理方式：**

保留gold的SST-2和EmoC。人审可按原题只保留数据集名称；若保留数值，逐项注明Vanilla 1-shot/5-shot→Anchor 1-shot及GPT2-XL、五随机种子平均的实验范围。不得在本次审核中静默改答案。 将定位元数据错误单独登记，最终人审按完整原页定位；本次不改既有索引。

**仍需人工确认：**

请明确接受仅核心答案，还是要求补充数值逐项标baseline；当前增写比较需人工处理。

**证据文件及具体位置：**

- [data/docs/raw/academic/2305.14160v4.pdf](../../../data/docs/raw/academic/2305.14160v4.pdf) — page=6; section=3.1.2 Experiments / 3.1.3 Results; source_sha256=035b1659c5305a0c8157594cf41446fe72ade8d48efa99eb036dfa522d3431c4; verified_from=原始文件完整页面文本提取及完整页面视觉检查
- [data/docs/raw/academic/2305.14160v4.pdf](../../../data/docs/raw/academic/2305.14160v4.pdf) — source_sha256=035b1659c5305a0c8157594cf41446fe72ade8d48efa99eb036dfa522d3431c4; verified_from=原始PDF完整物理页提取及视觉检查; page=7; section=Table 1 / Method × Dataset
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p6.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p6.txt) — page=6; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p6.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p6.png) — page=6; section=完整物理页Poppler渲染；已视觉检查
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p7.txt](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p7.txt) — page=7; section=完整物理页文本（pdfplumber）
- [eval/artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p7.png](../../artifacts/d2-ai-preaudit/rag/raw-pages/ohr-academic-label-words-physical-p7.png) — page=7; section=完整物理页Poppler渲染；已视觉检查
- [data/raw/ohr/qas_v2.json](../../../data/raw/ohr/qas_v2.json) — section=ID=571aa4f6-40a2-4015-8a40-a3799a1ab357; qa_array_item_identified_by=ID
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=19; section=rag-19 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=14; section=rag-19 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-19
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-19
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-19-E1-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-19-E1-cropbox-outline.png) — page=6; section=E1 / 原始完整物理页及实际bbox红框（已视觉核对）
- [eval/artifacts/d2-ai-preaudit/rag/bbox-visual/rag-19-E5-cropbox-outline.png](../../artifacts/d2-ai-preaudit/rag/bbox-visual/rag-19-E5-cropbox-outline.png) — page=7; section=E5 / 原始完整物理页及实际bbox红框（已视觉核对）

### rag:rag-20

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-21

- 分组：rag；划分：dev

**审核对象：** 根据这份简介，Iron Maiden 是哪一年在什么地方组建的？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

1975年，英国伦敦东部的 Leyton。

**RAG已有系统回答：**

Iron Maiden（铁娘子乐队）由贝斯手及主要创作者 Steve Harris 于1975年在伦敦东部的 Leyton 组建。[E1]

**RAG题目来源类型：**

自编

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

这是基于项目中文改写简介的自编题，没有OHR source_qa_id，不能标成OHR原题。已读完整Iron Maiden HTML，公开背景首段明确1975年、伦敦东部Leyton，gold年/地点正确；成立地未混同专辑1980/1982发行时间。

**实际回答判断理由：**

实际回答1975年伦敦东部Leyton，并补充Steve Harris角色；E1与HTML公开背景首段及索引相符，年、地点、创建者均逐项有文档支持。仅对指定改写文档内事实审查，未外网验证百科原站。

**建议处理方式：**

保留答案并标清题为自编、材料为项目中文改写简介。

**仍需人工确认：**

请确认文档层面1975/Leyton及Steve Harris补述；外部百科真实性不属于本次限定材料核验。

**证据文件及具体位置：**

- [data/docs/raw/d2/iron-maiden.html](../../../data/docs/raw/d2/iron-maiden.html) — page=; section=Iron Maiden 铁娘子乐队公开简介 / 公开背景（首段）; source_sha256=4f071c465c5417f5867e8571fb4ea37098dd8829d86b9b253ac26184a145b270; verified_from=原始文件全文读取
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=21; section=rag-21 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=15; section=rag-21 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-21
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-21

### rag:rag-22

- 分组：rag；划分：dev

**审核对象：** 只根据 U2 简介，U2 于哪一年在哪座城市成立？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

1976年在都柏林成立。

**RAG已有系统回答：**

U2 于1976年在都柏林成立。[E1]

**RAG题目来源类型：**

自编

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

自编题基于U2项目中文简介，不含OHR原题ID。完整HTML公开背景首段明确于1976年在都柏林成立；1980/1983年是作品发行日期。gold年份和城市与限定文档一致。

**实际回答判断理由：**

实际仅答1976年在都柏林成立，E1为同一公开背景首段，与原HTML和索引精确对应，足够支持年份及城市。未借助外部常识。

**建议处理方式：**

保留当前gold及实际回答，题来源标自编、文档来源标中文改写。

**仍需人工确认：**

请确认1976和都柏林均取自指定简介首段。

**证据文件及具体位置：**

- [data/docs/raw/d2/u2.html](../../../data/docs/raw/d2/u2.html) — page=; section=U2 乐队公开简介 / 公开背景（首段）; source_sha256=b2390ce8d232a9030e6dea5a7f43650b843108be0e26c876ed2d9572a653757e; verified_from=原始文件全文读取
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=22; section=rag-22 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=16; section=rag-22 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-22
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-22

### rag:rag-23

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-24

- 分组：rag；划分：dev

**审核对象：** 根据这张简介图片，Led Zeppelin 于哪一年在哪座城市成立？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

1968年在伦敦成立。

**RAG已有系统回答：**

Led Zeppelin（齐柏林飞船）于1968年在伦敦成立。[E1]

**RAG题目来源类型：**

自编

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

自编题引用Led Zeppelin简介PNG。直接打开完整原PNG视觉阅读，公开背景首段清晰写1968年在伦敦成立；后文1969/1971是专辑年份。登记PNG哈希与manifest一致，派生HTML内容一致；gold年/城市正确。

**实际回答判断理由：**

实际答1968年伦敦，与图片可视文字一致。E1索引文本和原PNG对应，已直接读图片而非仅相信OCR或辅助评分；原图片明确标它是带出处的项目改写，不应称维基百科原站截图。 section_path“图像 OCR”是处理标签，并非原图片正文标题；已另按原图公开背景首段定位，未把处理标签当成真实章节。

**建议处理方式：**

保留答案；材料性质保留“项目中文改写简介的截图”说明。

**仍需人工确认：**

请从原PNG确认1968/伦敦，并确认不将派生截图标为原站页面。

**证据文件及具体位置：**

- [data/docs/raw/d2/led-zeppelin.png](../../../data/docs/raw/d2/led-zeppelin.png) — page=; section=图片上部 / 公开背景首段; source_sha256=950e7d66df1a0ca64bb7770420f919a3665a254ee0429c7fe8d9194d8a97ec19; verified_from=原始PNG直接完整视觉检查
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=24; section=rag-24 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=17; section=rag-24 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-24
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-24

### rag:rag-25

- 分组：rag；划分：dev

**审核对象：** 根据口径手册，曲目最受欢迎的默认口径是什么，对应哪个汇总表达式？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

默认按购买数量，使用 SUM(invoice_line.quantity)；销售额与歌单收录数是明确的备选口径。

**RAG已有系统回答：**

曲目最受欢迎的默认口径是沿用总计划的购买数量默认，即 SUM(invoice_line.quantity) [E1]。汇总表达式中，热门曲目（统计粒度为期间内曲目）的核心表达式为 SUM(invoice_line.quantity) [E2]。

**RAG题目来源类型：**

自编

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

项目口径手册自编题。以python-docx读取原DOCX正文和表格完整顺序；四项指标/热门曲目段明确默认购买数量SUM(invoice_line.quantity)，销售额/歌单收录数是备选。gold主表达式和备选说明均有原文依据，无发票金额或全局默认混用。

**实际回答判断理由：**

实际回答默认购买数量和SUM(invoice_line.quantity)，符合问句要求。E1覆盖热门曲目段，E2覆盖指标对应关系表，二者均由原DOCX核对。实际未逐述备选口径，但本题只问默认及表达式，不造成核心答复不全。

**建议处理方式：**

保留gold与当前回答，最终人审以曲目对象和quantity表达式为准。

**仍需人工确认：**

请确认这是曲目购买数量默认，不套用于客户谁买得最多。

**证据文件及具体位置：**

- [data/docs/raw/d2/Chinook业务指标口径手册.docx](../../../data/docs/raw/d2/Chinook业务指标口径手册.docx) — page=; section=四项指标的定义与限制 / 热门曲目；指标对应关系表; source_sha256=b50f5683e735baa3ca6fe08bde3b437377d810732357e2a4898d6820b0456a9a; verified_from=原始DOCX用python-docx完整正文及表格读取
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=25; section=rag-25 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=18; section=rag-25 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-25
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-25

### rag:rag-26

- 分组：rag；划分：dev

**审核对象：** 按口径手册，客单价的主口径全名是什么，对应哪个 SQL 表达式？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

平均每张发票金额，AVG(invoice.total)。

**RAG已有系统回答：**

客单价的主口径全名为「平均每张发票金额」，对应 SQL 表达式为 AVG(invoice.total)，每张发票权重相同。[E1][E2]

**RAG题目来源类型：**

自编

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

项目口径手册自编题。原DOCX平均每张发票金额段及表格定义客单价主口径全名为平均每张发票金额，AVG(invoice.total)，每张发票同权；下一段明确每位购买客户平均金额另命名。gold全名和SQL表达式准确。

**实际回答判断理由：**

实际回答全名、AVG(invoice.total)及每张发票权重相同。E1为指标对应表，E2为主定义及客户平均金额区别，原DOCX均可定位，补述权重也有直接支持。

**建议处理方式：**

保留答案，不改为每位购买客户平均金额；无记录NULL边界不在当前问句范围。

**仍需人工确认：**

请确认统计粒度为发票且使用invoice.total平均。

**证据文件及具体位置：**

- [data/docs/raw/d2/Chinook业务指标口径手册.docx](../../../data/docs/raw/d2/Chinook业务指标口径手册.docx) — page=; section=四项指标的定义与限制 / 平均每张发票金额；指标对应关系表; source_sha256=b50f5683e735baa3ca6fe08bde3b437377d810732357e2a4898d6820b0456a9a; verified_from=原始DOCX用python-docx完整正文及表格读取
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=26; section=rag-26 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=19; section=rag-26 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-26
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-26

### rag:rag-27

- 分组：rag；划分：dev

**审核对象：** 根据中文数据字典，customer.country 和 invoice.billing_country 分别表示什么？

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

customer.country 是客户所在地国家；invoice.billing_country 是发票账单地址国家，两个业务含义应分别保留。

**RAG已有系统回答：**

customer.country 表示客户所在地国家 [E1][E8]；invoice.billing_country 表示发票账单地址国家 [E1][E2]。两者是不同字段，不可直接互换 [E2]。

**RAG题目来源类型：**

自编

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

项目中文数据字典自编题。直接读取完整原MD，地区字段含义段分别定义customer.country为客户所在地国家、invoice.billing_country为发票账单地址国家；两表字段说明重复确认。原文指出当前快照值相等不改变业务口径，gold两义正确。

**实际回答判断理由：**

实际分别解释两字段并说明不可直接互换。E1为地区字段总说明，E8为customer.country字段行，E2为invoice.billing_country行，均按原MD相应小节定位并与索引一致。未以当前值相等推断语义相同。

**建议处理方式：**

保留当前gold与回答；使用地区指标时须保持查询对象与字段口径对应。

**仍需人工确认：**

请确认所在地国家和账单地址国家的定义分别保留。

**证据文件及具体位置：**

- [data/docs/raw/d2/chinook-dictionary-zh.md](../../../data/docs/raw/d2/chinook-dictionary-zh.md) — page=; section=Chinook 数据字典 中文 / 地区字段含义；表与字段/customer、invoice; source_sha256=c1a36da359cef886099ffd59e355716a28d0aaaba044834002ee76d49942d2c7; verified_from=原始文件全文读取
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=27; section=rag-27 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=20; section=rag-27 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-27
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-27

### rag:rag-28

- 分组：rag；划分：dev

**审核对象：** 只依据这份 Iron Maiden 简介，列出该乐队2026年在中国每场演出的门票收入。

**别名或参考答案判断：** AI建议通过

**系统实际回答判断：** AI建议通过

**RAG标准答案：**

当前指定简介不包含所问的逐场中国演出票务收入，证据不足，应明确说明不能据此回答。

**RAG已有系统回答：**

所选文档未提供足以直接支持此问题的证据，当前无法核实。

**RAG题目来源类型：**

自编

**RAG答案正确性：**

AI建议通过

**RAG引用支撑性：**

AI建议通过

**RAG引用定位正确性：**

AI建议通过

**参考判断理由：**

自编证据不足题。已读完整Iron Maiden HTML全部公开背景、资料处理说明、footer；仅有组建/作品/音乐背景，且明确不包含当代巡演收入，没有2026中国逐场演出、票数、单价或票务收入数据。gold answerable=false及EMPTY_RESULT正确；缺少正向gold_evidence并非漏证据，须以完整文档边界核验。

**实际回答判断理由：**

实际EMPTY_RESULT且明确所选文档不足、当前无法核实，没有虚构演出或金额，也无伪造引用。没有actual evidences对正确拒答不构成错误；本审核依据完整HTML而非拿空引文证明缺失。

**建议处理方式：**

保留证据不足gold及EMPTY_RESULT；不得通过常识或外部搜索补限定文档答案。

**仍需人工确认：**

请核实完整指定简介确无逐场票务收入，并最终确认拒答。

**证据文件及具体位置：**

- [data/docs/raw/d2/iron-maiden.html](../../../data/docs/raw/d2/iron-maiden.html) — page=; section=Iron Maiden 铁娘子乐队公开简介 / 公开背景（完整文档检查）; source_sha256=4f071c465c5417f5867e8571fb4ea37098dd8829d86b9b253ac26184a145b270; verified_from=原始文件全文读取
- [eval/datasets/rag_single.jsonl](../../datasets/rag_single.jsonl) — line=28; section=rag-28 / dev
- [eval/artifacts/d2/rag/final/responses.jsonl](../../artifacts/d2/rag/final/responses.jsonl) — line=21; section=rag-28 / dev / response
- [eval/artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-index-dev-audit.json) — section=rag:rag-28
- [eval/artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json](../../artifacts/d2-ai-preaudit/rag/citation-location-dev-audit.json) — section=rag:rag-28

### rag:rag-29

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。

### rag:rag-30

- 分组：rag；划分：holdout

**审核对象：** 保留题内容本轮未审核

**别名或参考答案判断：** 本轮跳过（保留集未隔离）

**系统实际回答判断：** 未运行

**参考判断理由：**

本次会话承接开发任务，无法保证审核与后续调参隔离。仅保留编号和进度，不展开题干、答案或来源内容。

**建议处理方式：**

在独立审核环境中审核标签；被测系统预测继续留到D5冻结后运行。

**仍需人工确认：**

需要团队安排独立的保留集标签审核环境。

**证据文件及具体位置：**

本轮按隔离要求跳过内容审核，未展开证据。
