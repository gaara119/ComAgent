# D2 SQL与鲁棒开发集AI预审

35条nl2sql dev + 21条robust dev；只读审核原题、参考与已存在系统输出；AI建议不等于人工确认

当前为开发会话，未提供独立保留集隔离机制；保留题仅统计跳过数量，不审核题干、参考或答案。跳过nl2sql 15条、robust 9条。

本次以题意为先逐行审查，重读原始开发responses；112条已有gold/actual SQL及6个口径示例、11条补充SELECT、1条只读身份查询共130条全部完成。112条已有SQL实际值均与原记录一致，但执行成功/EX相同不是语义通过依据。没有调用问答API或模型，没有生成新的系统预测。

参考建议：{"AI建议通过": 54, "AI建议有条件通过": 2}；实际输出建议：{"AI建议通过": 54, "AI建议有条件通过": 1, "证据不足": 1}。

sql-38当前快照bytes没有NULL，当前结果正确，但可空列DESC默认NULL先排需确认规则。robust-23“这批”范围未定义，实际答全库平均暂不能确定。robust-26最终回答正确，改写吞掉请求词单独记为rewrite质量问题；robust-13值链接trace未匹配但最终SQL正确，不把最终正确当作NLU阶段成功证据。

|review_id|参考|实际|证据完整|主要问题|
|---|---|---|---|---|
|nl2sql:sql-01|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-02|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-04|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-05|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-06|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-07|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-09|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-10|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-11|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-13|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-14|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-15|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-17|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-18|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-19|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-21|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-22|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-24|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-26|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-27|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-29|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-31|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-32|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-33|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-34|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-35|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-36|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-37|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-38|AI建议有条件通过|AI建议有条件通过|是|reference: track.bytes可NULL且ORDER BY bytes DESC默认NULLS FIRST，缺少未知文件大小处理规则；现存NULL=0，未发现本次实际三行值错误。；actual: track.bytes可NULL且ORDER BY bytes DESC默认NULLS FIRST，缺少未知文件大小处理规则；现存NULL=0，未发现本次实际三行值错误。|
|nl2sql:sql-39|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-40|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-41|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-42|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-43|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|nl2sql:sql-44|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-01|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-02|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-03|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-06|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-07|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-08|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-11|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-12|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-13|AI建议通过|AI建议通过|是|nlu_trace: 原NLU把jia na da标为unmatched且bindings为空，但后续已有SQL筛选Canada。最终国家值和计数正确，本次不能据此宣称NLU绑定阶段完成了拼音对齐。|
|robust:robust-16|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-17|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-18|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-19|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-21|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-22|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-23|AI建议有条件通过|证据不足|否|question: “全部”改成“这批”新增无前文的指代范围，鲁棒变体未严格保持基题范围。；reference: AVG全表是未声明的全集假设；只有确认“这批=全部曲目”后参考才可接受。；actual: 范围不明仍直接全表AVG，原输出缺少范围澄清，最终正确性证据不足。|
|robust:robust-24|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-26|AI建议通过|AI建议通过|是|rewrite: 原mention跨度[4,13]包含“帮忙查一下来自巴西”，整体替换Brazil后改写为“你好，请Brazil的客户有多少位，谢谢。”，吞掉了请求词与来自关系。最终已有SQL仍筛选customer.country=Brazil且结果5位正确。|
|robust:robust-27|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-28|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|
|robust:robust-29|AI建议通过|AI建议通过|是|逐项审核未发现本次输出的语义错误|

## nl2sql:sql-01

题目：客户表共有多少位客户？

参考：AI建议通过。对象为客户表全体记录，customer_id 是非空主键；COUNT(*) 每客户计一次，不受其他可空列影响，不加期间或国家过滤。参考结果为59位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：59。”准确陈述标量59，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer;
```

已有系统SQL：

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer"
```

已有系统自然语言：查询结果：59。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-01：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第1行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第1行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第2行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第3行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-02

题目：来自巴西的客户有多少位？

参考：AI建议通过。“来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Brazil'
```

已有系统自然语言：查询结果：5。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-02：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第2行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第2行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第4行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第5行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-04

题目：列出来自巴西的客户编号、名字、姓氏和城市，按客户编号升序。

参考：AI建议通过。客户国家Brazil筛选，投影customer_id、first_name、last_name、city四列，名字和姓氏分开；customer_id主键升序能确定全部5行次序。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回5行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT customer_id, first_name, last_name, city FROM customer WHERE country = 'Brazil' ORDER BY customer_id;
```

已有系统SQL：

```sql
SELECT "customer_id", "first_name", "last_name", "city" FROM "public"."customer" WHERE "country" = 'Brazil' ORDER BY "customer_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 5 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-04：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第4行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第3行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第6行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第7行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-05

题目：列出来自美国的客户编号、城市和州，按客户编号升序。

参考：AI建议通过。美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 13 行，详细数据见结果表。”与结果表13行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回13行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;
```

已有系统SQL：

```sql
SELECT "customer_id", "city", "state" FROM "public"."customer" WHERE "country" = 'USA' ORDER BY "customer_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 13 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-05：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第5行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第4行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第8行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第9行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-06

题目：列出单价高于 0.99 的前 10 首曲目的编号、名称和单价，按曲目编号升序。

参考：AI建议通过。比较track.unit_price > 0.99是严格大于，属于目录单价，不能用发票总额；按track_id升序再LIMIT 10，准确返回首10行编号、名称、单价。数据未声明币种。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 10 行，详细数据见结果表。”与结果表10行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT track_id, name, unit_price FROM track WHERE unit_price > 0.99 ORDER BY track_id LIMIT 10;
```

已有系统SQL：

```sql
SELECT "track_id", "name", "unit_price" FROM "public"."track" WHERE "unit_price" > 0.99 ORDER BY "track_id" ASC LIMIT 10
```

已有系统自然语言：查询返回 10 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-06：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第6行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第5行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第10行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第11行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-07

题目：列出职位为 Sales Support Agent 的员工编号、名字和姓氏，按员工编号升序。

参考：AI建议通过。员工职位字段employee.title精确筛选Sales Support Agent；返回employee_id、first_name、last_name且编号升序，对应3名员工，没有拼接fullname。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 3 行，详细数据见结果表。”与结果表3行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回3行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT employee_id, first_name, last_name FROM employee WHERE title = 'Sales Support Agent' ORDER BY employee_id;
```

已有系统SQL：

```sql
SELECT "employee_id", "first_name", "last_name" FROM "public"."employee" WHERE "title" = 'Sales Support Agent' ORDER BY "employee_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 3 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-07：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第7行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第6行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第12行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第13行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-09

题目：全部发票的总金额是多少？

参考：AI建议通过。题目明确“全部发票”，对invoice.total在发票粒度SUM，不连接invoice_line导致重复金额，不增加默认期间、支付状态或币种。参考总额2328.60（数据库金额单位）。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：2328.60。”准确陈述标量2328.60，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT SUM(total) AS total_amount FROM invoice;
```

已有系统SQL：

```sql
SELECT SUM("total") FROM "public"."invoice"
```

已有系统自然语言：查询结果：2328.60。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-09：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第9行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第7行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第14行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第15行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-10

题目：全部曲目的平均时长是多少毫秒？

参考：AI建议通过。题目明确全部曲目及毫秒，AVG(track.milliseconds)为每条曲目等权平均，没有除1000转秒或按销售数量加权；milliseconds非空，结果393599.212103910933毫秒。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：393599.212103910933。”准确陈述标量393599.212103910933，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT AVG(milliseconds) AS average_milliseconds FROM track;
```

已有系统SQL：

```sql
SELECT AVG("milliseconds") AS avg_ms FROM "public"."track"
```

已有系统自然语言：查询结果：393599.212103910933。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-10：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第10行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第8行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第16行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第17行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-11

题目：全部发票的平均总额是多少？请保留两位小数。

参考：AI建议通过。题目要求发票平均总额与两位小数，ROUND(AVG(invoice.total),2)先按每张发票平均再四舍五入；不是按购买客户均额。参考5.65，数据未声明货币名称。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5.65。”准确陈述标量5.65，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT ROUND(AVG(total), 2) AS average_total FROM invoice;
```

已有系统SQL：

```sql
SELECT ROUND(CAST(AVG("total") AS DECIMAL), 2) AS "avg_total" FROM "public"."invoice"
```

已有系统自然语言：查询结果：5.65。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-11：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第11行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第9行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第18行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第19行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-13

题目：按客户所在国家统计客户数，先按客户数降序，并列时按国家名称升序。

参考：AI建议通过。按customer.country分组COUNT(*)统计客户数，主排序客户数降序、次排序国家名升序；24个国家组完整，数量相等时已有次排序，不将客户国家替换为账单国家。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 24 行，详细数据见结果表。”与结果表24行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回24行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT country, COUNT(*) AS customer_count FROM customer GROUP BY country ORDER BY customer_count DESC, country ASC;
```

已有系统SQL：

```sql
SELECT "country", COUNT(*) AS "customer_count" FROM "public"."customer" GROUP BY "country" ORDER BY COUNT(*) DESC, "country" ASC LIMIT 200
```

已有系统自然语言：查询返回 24 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-13：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第13行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第10行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第20行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第21行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-14

题目：按流派编号统计曲目数，先按曲目数降序，并列时按流派编号升序。

参考：AI建议通过。按track.genre_id分组COUNT(*)统计曲目条数，数量降序、genre_id升序；genre_id可NULL但当前快照NULL数为0，SQL不会擅自删除NULL组。25组完整。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 25 行，详细数据见结果表。”与结果表25行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回25行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT genre_id, COUNT(*) AS track_count FROM track GROUP BY genre_id ORDER BY track_count DESC, genre_id ASC;
```

已有系统SQL：

```sql
SELECT "genre_id", COUNT(*) AS "track_count" FROM "public"."track" GROUP BY "genre_id" ORDER BY "track_count" DESC, "genre_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 25 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-14：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第14行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第11行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第22行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第23行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-15

题目：按发票的账单国家统计销售总额，先按销售总额降序，并列时按国家名称升序。

参考：AI建议通过。题目明确发票账单国家，字段invoice.billing_country；在invoice粒度SUM(total)，金额降序、国家名升序，24组完整且并列次序确定。不能因当前客户地区与账单地区一致而替换字段。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 24 行，详细数据见结果表。”与结果表24行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回24行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT billing_country, SUM(total) AS sales_total FROM invoice GROUP BY billing_country ORDER BY sales_total DESC, billing_country ASC;
```

已有系统SQL：

```sql
SELECT "billing_country", SUM("total") AS "sales_total" FROM "public"."invoice" GROUP BY "billing_country" ORDER BY "sales_total" DESC, "billing_country" ASC LIMIT 200
```

已有系统自然语言：查询返回 24 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-15：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第15行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第12行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第24行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第25行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-17

题目：找出时长最长的 5 首曲目，返回编号、名称和毫秒时长；按时长降序，并列按编号升序。

参考：AI建议通过。最长5首按非空track.milliseconds降序，track_id升序作并列规则，然后LIMIT 5；只返回track_id、name、milliseconds，保留毫秒单位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT track_id, name, milliseconds FROM track ORDER BY milliseconds DESC, track_id ASC LIMIT 5;
```

已有系统SQL：

```sql
SELECT "track_id", "name", "milliseconds" FROM "public"."track" ORDER BY "milliseconds" DESC, "track_id" ASC LIMIT 5
```

已有系统自然语言：查询返回 5 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-17：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第17行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第13行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第26行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第27行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-18

题目：找出总额最高的 5 张发票，返回编号和总额；按总额降序，并列按编号升序。

参考：AI建议通过。最高5张发票按invoice.total降序、invoice_id升序确定并列，再LIMIT 5；21.86并列的96和194号先后正确，金额是发票总额。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT invoice_id, total FROM invoice ORDER BY total DESC, invoice_id ASC LIMIT 5;
```

已有系统SQL：

```sql
SELECT "invoice_id", "total" FROM "public"."invoice" ORDER BY "total" DESC, "invoice_id" ASC LIMIT 5
```

已有系统自然语言：查询返回 5 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-18：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第18行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第14行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第28行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第29行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-19

题目：按姓氏降序取前 5 位客户，返回编号、名字和姓氏；姓氏相同时按客户编号升序。

参考：AI建议通过。客户last_name按数据库当前文本排序规则降序，再customer_id升序并列，LIMIT 5；投影编号、first_name、last_name，未误用first_name排序或fullname。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT customer_id, first_name, last_name FROM customer ORDER BY last_name DESC, customer_id ASC LIMIT 5;
```

已有系统SQL：

```sql
SELECT "customer_id", "first_name", "last_name" FROM "public"."customer" ORDER BY "last_name" DESC, "customer_id" ASC LIMIT 5
```

已有系统自然语言：查询返回 5 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-19：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第19行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第15行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第30行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第31行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-21

题目：列出 2021 年的前 10 张发票，返回编号、日期和总额，按发票编号升序。

参考：AI建议通过。2021年依据invoice.invoice_date，范围[2021-01-01,2022-01-01)，再按invoice_id升序LIMIT 10；返回编号、原始日期和总额，未混用客户创建日期或最近10张。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 10 行，详细数据见结果表。”与结果表10行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT invoice_id, invoice_date, total FROM invoice WHERE invoice_date >= '2021-01-01' AND invoice_date < '2022-01-01' ORDER BY invoice_id LIMIT 10;
```

已有系统SQL：

```sql
SELECT "invoice_id", "invoice_date", "total" FROM "public"."invoice" WHERE "invoice_date" >= '2021-01-01' AND "invoice_date" < '2022-01-01' ORDER BY "invoice_id" ASC LIMIT 10
```

已有系统自然语言：查询返回 10 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-21：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第21行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第16行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第32行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第33行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-22

题目：列出 2004 年 1 月 1 日之前入职的员工编号、名字（仅 first_name，不包含姓氏 last_name）和入职日期，按员工编号升序。

参考：AI建议通过。入职时间取employee.hire_date，严格早于2004-01-01；名字明确仅first_name，不含last_name/fullname；按employee_id升序返回6行，当前hire_date无NULL。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 6 行，详细数据见结果表。”与结果表6行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回6行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT employee_id, first_name, hire_date FROM employee WHERE hire_date < '2004-01-01' ORDER BY employee_id;
```

已有系统SQL：

```sql
SELECT "employee_id", "first_name", "hire_date" FROM "public"."employee" WHERE "hire_date" < '2004-01-01' ORDER BY "employee_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 6 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-22：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第22行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第17行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第34行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第35行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-24

题目：列出邮箱以 @gmail.com 结尾的客户编号、名字（仅 first_name，不包含姓氏 last_name）和邮箱，按客户编号升序。

参考：AI建议通过。邮箱以@gmail.com结尾用LIKE '%@gmail.com'，不是包含gmail.com或错用公司名；题目名字明确仅first_name，返回编号、first_name、email并按编号升序，8行完整。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 8 行，详细数据见结果表。”与结果表8行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回8行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT customer_id, first_name, email FROM customer WHERE email LIKE '%@gmail.com' ORDER BY customer_id;
```

已有系统SQL：

```sql
SELECT "customer_id", "first_name", "email" FROM "public"."customer" WHERE "email" LIKE '%@gmail.com' ORDER BY "customer_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 8 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-24：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第24行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第18行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第36行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第37行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-26

题目：有多少位客户没有填写公司名称（company 为 NULL）？

参考：AI建议通过。题目明确定义company为NULL，使用IS NULL而非等于NULL、空串或COUNT(company)；COUNT(*)得到49位，实库company空字符串为0，未改变NULL语义。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：49。”准确陈述标量49，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE company IS NULL;
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "company" IS NULL
```

已有系统自然语言：查询结果：49。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-26：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第26行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第19行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第38行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第39行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-27

题目：列出没有作曲者信息（composer 为 NULL）的前 10 首曲目编号和名称，按曲目编号升序。

参考：AI建议通过。缺少作曲者明确定义composer IS NULL；按track_id升序再LIMIT 10，返回编号和名称，既不将NULL与空串混同，也不把作曲者名称误当艺术家字段。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 10 行，详细数据见结果表。”与结果表10行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT track_id, name FROM track WHERE composer IS NULL ORDER BY track_id LIMIT 10;
```

已有系统SQL：

```sql
SELECT "track_id", "name" FROM "public"."track" WHERE "composer" IS NULL ORDER BY "track_id" ASC LIMIT 10
```

已有系统自然语言：查询返回 10 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-27：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第27行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第20行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第40行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第41行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-29

题目：列出国家字段为 Antarctica 的客户编号、名字和姓氏，按客户编号升序。

参考：AI建议通过。原值Antarctica在customer.country实际值中不存在，仍保留精确筛选，不猜测其他国家；返回所要求的编号、first_name、last_name及编号排序，空列表表示没有匹配客户，不是标量0或NULL。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“按原问题条件未查到记录。”正确说明原条件无记录，没有将空列表当作NULL聚合或零值。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回0行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT customer_id, first_name, last_name FROM customer WHERE country = 'Antarctica' ORDER BY customer_id;
```

已有系统SQL：

```sql
SELECT "customer_id", "first_name", "last_name" FROM "public"."customer" WHERE "country" = 'Antarctica' ORDER BY "customer_id" ASC LIMIT 200
```

已有系统自然语言：按原问题条件未查到记录。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-29：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第29行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第21行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第42行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第43行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-31

题目：客户所在国家为 Italy 的客户有多少位？

参考：AI建议通过。客户所在国家Italy精确匹配customer.country；COUNT(*)得到1位，未改用invoice账单国家或新增日期条件。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1。”准确陈述标量1，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Italy'
```

已有系统自然语言：查询结果：1。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-31：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第31行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第22行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第44行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第45行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-32

题目：客户所在国家为 Canada 的客户有多少位？

参考：AI建议通过。客户所在国家Canada精确匹配customer.country；COUNT(*)得到8位，区分客户国家与账单国家，未新增发票期间。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：8。”准确陈述标量8，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Canada'
```

已有系统自然语言：查询结果：8。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-32：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第32行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第23行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第46行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第47行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-33

题目：账单国家为 Canada 的全部发票总额是多少？

参考：AI建议通过。题目明确账单国家Canada，筛选invoice.billing_country而非customer.country；SUM(invoice.total)统计全部匹配发票，结果303.96（数据库金额单位），不做明细JOIN重复计额。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：303.96。”准确陈述标量303.96，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Canada';
```

已有系统SQL：

```sql
SELECT SUM("total") AS "total_amount" FROM "public"."invoice" WHERE "billing_country" = 'Canada'
```

已有系统自然语言：查询结果：303.96。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-33：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第33行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第24行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第48行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第49行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-34

题目：曲目表中最短的时长是多少毫秒？

参考：AI建议通过。最短时长取MIN(track.milliseconds)，milliseconds非空，得到1071毫秒；题目只要最短值，标量聚合正确，无需返回任意一首同长曲目的姓名或编号。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1071。”准确陈述标量1071，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT MIN(milliseconds) AS minimum_milliseconds FROM track;
```

已有系统SQL：

```sql
SELECT MIN("milliseconds") AS min_milliseconds FROM "public"."track"
```

已有系统自然语言：查询结果：1071。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-34：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第34行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第25行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第50行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第51行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-35

题目：曲目表中最高的单价是多少？

参考：AI建议通过。最高目录单价取MAX(track.unit_price)，非空numeric列得到1.99；不把发票总额或明细实际成交价当曲目目录单价，也不推断美元/人民币。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1.99。”准确陈述标量1.99，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT MAX(unit_price) AS maximum_unit_price FROM track;
```

已有系统SQL：

```sql
SELECT MAX("unit_price") AS max_unit_price FROM "public"."track"
```

已有系统自然语言：查询结果：1.99。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-35：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第35行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第26行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第52行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第53行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-36

题目：按发票账单城市统计发票数，先按数量降序，并列按城市名称升序，返回前 10 个城市。

参考：AI建议通过。按invoice.billing_city分组COUNT(*)统计发票条数，数量降序、城市名升序，再LIMIT 10；数量14及7的并列均按城市升序，未使用客户城市或销售金额。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 10 行，详细数据见结果表。”与结果表10行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT billing_city, COUNT(*) AS invoice_count FROM invoice GROUP BY billing_city ORDER BY invoice_count DESC, billing_city ASC LIMIT 10;
```

已有系统SQL：

```sql
SELECT "billing_city", COUNT(*) AS "invoice_count" FROM "public"."invoice" GROUP BY "billing_city" ORDER BY "invoice_count" DESC, "billing_city" ASC LIMIT 10
```

已有系统自然语言：查询返回 10 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-36：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第36行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第27行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第54行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第55行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-37

题目：按媒体类型编号统计曲目数，按媒体类型编号升序。

参考：AI建议通过。按track.media_type_id分组统计曲目条数，媒体类型编号升序；5种媒体类型完整，统计不是流派或媒体文件字节和。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 5 行，详细数据见结果表。”与结果表5行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回5行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT media_type_id, COUNT(*) AS track_count FROM track GROUP BY media_type_id ORDER BY media_type_id;
```

已有系统SQL：

```sql
SELECT "media_type_id", COUNT(*) AS "track_count" FROM "public"."track" GROUP BY "media_type_id" ORDER BY "media_type_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 5 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-37：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第37行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第28行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第56行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第57行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-38

题目：找出文件字节数最大的 3 首曲目，返回编号、名称和字节数；按字节数降序，并列按曲目编号升序。

参考：AI建议有条件通过。对象为文件字节数最大的3首曲目，字段track.bytes单位字节，排序bytes降序、track_id升序再LIMIT 3，投影编号、名称、字节数。当前bytes为NULL的行数为0，结果与当前题意一致；但bytes在schema可NULL，而PostgreSQL DESC默认NULLS FIRST，未知大小会排在真实最大值之前。需明确本题仅针对无NULL的固定快照，或补充非NULL筛选/NULLS LAST规则后再确认一般语义。

实际：AI建议有条件通过。已有SQL和结果在当前bytes无NULL快照下满足最大字节数3首、字节单位、bytes降序和track_id并列升序；自然语言及3行表忠实。actual同样缺少NULLS LAST/bytes IS NOT NULL，故当前值正确而可空字段的一般排序语义需条件确认。

已有参考SQL：

```sql
SELECT track_id, name, bytes FROM track ORDER BY bytes DESC, track_id ASC LIMIT 3;
```

已有系统SQL：

```sql
SELECT "track_id", "name", "bytes" FROM "public"."track" ORDER BY "bytes" DESC, "track_id" ASC LIMIT 3
```

已有系统自然语言：查询返回 3 行，详细数据见结果表。

建议：人工决定最大字节数排行是否仅针对当前无NULL快照，或应规定排除NULL/NULLS LAST；仅提出修订建议，不改gold或系统SQL。

人工待确认：需要确认bytes为NULL时的排行规则，以及本题验收是否限定当前无NULL快照。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-38：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第38行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第29行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第58行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第59行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第121行：nullable-columns
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第120行：postgres-desc-null-order

## nl2sql:sql-39

题目：2023 年一共开了多少张发票？

参考：AI建议通过。2023年开票数以invoice.invoice_date范围[2023-01-01,2024-01-01)过滤，再COUNT(*)；实库2023年83张，与当前日期无关，不把发票行数当发票数。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：83。”准确陈述标量83，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."invoice" WHERE "invoice_date" >= CAST('2023-01-01' AS DATE) AND "invoice_date" < CAST('2024-01-01' AS DATE)
```

已有系统自然语言：查询结果：83。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-39：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第39行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第30行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第60行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第61行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-40

题目：2022 年 7 月 1 日（含）到 2022 年 10 月 1 日（不含）的发票总额是多少？

参考：AI建议通过。题目给定起日含、止日不含，invoice_date >=2022-07-01且<2022-10-01准确实现半开区间；SUM(invoice.total)得到111.87（数据库金额单位），未扩大到全年或改用付款日期。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：111.87。”准确陈述标量111.87，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT SUM(total) AS total_amount FROM invoice WHERE invoice_date >= '2022-07-01' AND invoice_date < '2022-10-01';
```

已有系统SQL：

```sql
SELECT SUM("total") AS invoice_total FROM "public"."invoice" WHERE "invoice_date" >= CAST('2022-07-01 00:00:00' AS TIMESTAMP) AND "invoice_date" < CAST('2022-10-01 00:00:00' AS TIMESTAMP)
```

已有系统自然语言：查询结果：111.87。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-40：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第40行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第31行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第62行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第63行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-41

题目：列出名称以 The 开头的前 8 位艺术家，区分大小写，返回编号和名称，按艺术家编号升序。

参考：AI建议通过。艺术家名称以The开头且区分大小写，用artist.name LIKE 'The%'而非ILIKE或包含The；按artist_id升序再LIMIT 8，投影编号和名称，空name不匹配。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 8 行，详细数据见结果表。”与结果表8行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT artist_id, name FROM artist WHERE name LIKE 'The%' ORDER BY artist_id LIMIT 8;
```

已有系统SQL：

```sql
SELECT "artist_id", "name" FROM "public"."artist" WHERE "name" LIKE 'The%' ORDER BY "artist_id" ASC LIMIT 8
```

已有系统自然语言：查询返回 8 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-41：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第41行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第32行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第64行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第65行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-42

题目：列出名称恰好为 U2 的艺术家编号和名称，按编号升序。

参考：AI建议通过。艺术家artist.name恰好为U2用等号，不用模糊/包含匹配；编号升序返回150号U2，没有将艺术家名称误作专辑/曲目名称。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 1 行，详细数据见结果表。”与结果表1行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回1行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT artist_id, name FROM artist WHERE name = 'U2' ORDER BY artist_id;
```

已有系统SQL：

```sql
SELECT "artist_id", "name" FROM "public"."artist" WHERE "name" = 'U2' ORDER BY "artist_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 1 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-42：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第42行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第33行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第66行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第67行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-43

题目：没有填写州信息（state 为 NULL）的客户有多少位？

参考：AI建议通过。题目将未填写州信息明确定义state IS NULL，COUNT(*)为29位；不等同空字符串、未知州名，且没有误用invoice.billing_state。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：29。”准确陈述标量29，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE state IS NULL;
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "state" IS NULL
```

已有系统自然语言：查询结果：29。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-43：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第43行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第34行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第68行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第69行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## nl2sql:sql-44

题目：客户所在国家为 Wakanda 的客户有多少位？保留原筛选值，没匹配时返回 0。

参考：AI建议通过。明确保留Wakanda原值，country = 'Wakanda'在实库无匹配；COUNT(*)自然返回0，未纠错到真实国家、未返回空列表或NULL。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：0。”准确陈述标量0，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Wakanda';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Wakanda'
```

已有系统自然语言：查询结果：0。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-44：仅dev题干、参考和已有输出
- `eval/datasets/nl2sql_chinook_d2.jsonl`，第44行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/nl2sql/final/responses.jsonl`，第35行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第70行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第71行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则

## robust:robust-01

题目：来自巴稀的客户有多少位？

参考：AI建议通过。“巴稀”在国家语境是“巴西”的单字错写，指向Brazil；除错字外查询对象和计数口径未变化。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Brazil'
```

已有系统自然语言：查询结果：5。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-01：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第1行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第1行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第72行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第73行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-02：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-02

题目：列出来自美囯的客户编号、城市和州，按客户编号升序。

参考：AI建议通过。“美囯”是“美国”的字形错写，指向USA；编号、城市、州投影与升序保持不变。 美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 13 行，详细数据见结果表。”与结果表13行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回13行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;
```

已有系统SQL：

```sql
SELECT "customer_id", "city", "state" FROM "public"."customer" WHERE "country" = 'USA' ORDER BY "customer_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 13 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-02：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第2行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第2行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第74行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第75行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-05：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-03

题目：列出职位为 Sales Suport Agent 的员工编号、名字和姓氏，按员工编号升序。

参考：AI建议通过。Sales Suport Agent缺少一个p，实库employee.title真实值Sales Support Agent可唯一支持职位纠错；不新增岗位或员工范围。 员工职位字段employee.title精确筛选Sales Support Agent；返回employee_id、first_name、last_name且编号升序，对应3名员工，没有拼接fullname。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 3 行，详细数据见结果表。”与结果表3行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回3行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT employee_id, first_name, last_name FROM employee WHERE title = 'Sales Support Agent' ORDER BY employee_id;
```

已有系统SQL：

```sql
SELECT "employee_id", "first_name", "last_name" FROM "public"."employee" WHERE "title" = 'Sales Support Agent' ORDER BY "employee_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 3 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-03：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第3行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第3行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第76行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第77行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-07：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-06

题目：列出来自老美的客户编号、城市和州，按客户编号升序。

参考：AI建议通过。“老美”在来自某国家的客户语境为美国俗称USA，仍查询客户所在国家；没有把俗称扩张为北美或其他地区。 美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 13 行，详细数据见结果表。”与结果表13行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回13行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;
```

已有系统SQL：

```sql
SELECT "customer_id", "city", "state" FROM "public"."customer" WHERE "country" = 'USA' ORDER BY "customer_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 13 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-06：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第6行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第4行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第78行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第79行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-05：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-07

题目：来自意大利的客户有多少位？

参考：AI建议通过。意大利为Italy的中文国家名称；译名不改变customer.country计数条件。 客户所在国家Italy精确匹配customer.country；COUNT(*)得到1位，未改用invoice账单国家或新增日期条件。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1。”准确陈述标量1，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';
```

已有系统SQL：

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer" WHERE "country" = 'Italy'
```

已有系统自然语言：查询结果：1。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-07：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第7行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第5行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第80行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第81行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-31：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-08

题目：来自加拿大的客户有多少位？

参考：AI建议通过。加拿大为Canada的中文国家名称；译名不改变customer.country计数条件。 客户所在国家Canada精确匹配customer.country；COUNT(*)得到8位，区分客户国家与账单国家，未新增发票期间。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：8。”准确陈述标量8，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Canada'
```

已有系统自然语言：查询结果：8。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-08：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第8行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第6行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第82行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第83行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-32：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-11

题目：来自 ba xi 的客户有多少位？

参考：AI建议通过。ba xi按国家语境读作“巴西”，保留Brazil客户计数；未增加时间、国家并集或账单条件。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Brazil'
```

已有系统自然语言：查询结果：5。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-11：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第11行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第7行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第84行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第85行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-02：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-12

题目：客户所在国家为 yi da li 的客户有多少位？

参考：AI建议通过。yi da li按国家语境读作“意大利”，保留Italy客户计数；未因候选相似度将其改成India。 客户所在国家Italy精确匹配customer.country；COUNT(*)得到1位，未改用invoice账单国家或新增日期条件。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1。”准确陈述标量1，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Italy'
```

已有系统自然语言：查询结果：1。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-12：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第12行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第8行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第86行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第87行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-31：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-13

题目：客户所在国家为 jia na da 的客户有多少位？

参考：AI建议通过。jia na da按国家语境读作“加拿大”，保留Canada客户计数；国家对象明确，发音变体未增加题意歧义。 客户所在国家Canada精确匹配customer.country；COUNT(*)得到8位，区分客户国家与账单国家，未新增发票期间。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：8。”准确陈述标量8，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 原值链接trace显示unmatched/无bindings，最终SQL仍正确采用Canada；结果正确性与值链接阶段成功应分开记录。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';
```

已有系统SQL：

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer" WHERE "country" = 'Canada'
```

已有系统自然语言：查询结果：8。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。 若评估特定NLU阶段，人工应单独确认拼音对齐由哪一步完成；不改变最终答案建议。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-13：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第13行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第9行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第88行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第89行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-32：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-16

题目：country 是 Brazil 的 customer 有多少位？

参考：AI建议通过。中英混合显式给出country、Brazil、customer，查询customer.country='Brazil'的人数，语义与基题一致。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

已有系统SQL：

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer" WHERE "country" = 'Brazil'
```

已有系统自然语言：查询结果：5。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-16：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第16行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第10行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第90行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第91行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-02：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-17

题目：列出 country 为 USA 的客户编号 customer_id、城市 city 和州 state，按 customer_id 升序。

参考：AI建议通过。中英混合显式给出USA、customer_id/city/state及customer_id升序，字段与排序要求未改变。 美国映射真实值USA，筛选customer.country；只返回customer_id、city、state，客户编号升序；13行中state按原值返回，没有把城市或账单地区混入客户字段。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询返回 13 行，详细数据见结果表。”与结果表13行一致，详细值由已有表承载；列、筛选及所要求排序已逐项核对。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 默认LIMIT 200在本快照仅返回13行且未截断，本次建议限于已有快照及输出。

已有参考SQL：

```sql
SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;
```

已有系统SQL：

```sql
SELECT "customer_id", "city", "state" FROM "public"."customer" WHERE "country" = 'USA' ORDER BY "customer_id" ASC LIMIT 200
```

已有系统自然语言：查询返回 13 行，详细数据见结果表。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-17：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第17行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第11行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第92行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第93行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-05：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-18

题目：全部 invoice 的 total 加起来是多少？

参考：AI建议通过。中英混合显式要求全部invoice的total求和，即发票粒度SUM(total)，没有新增指标或期间。 题目明确“全部发票”，对invoice.total在发票粒度SUM，不连接invoice_line导致重复金额，不增加默认期间、支付状态或币种。参考总额2328.60（数据库金额单位）。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：2328.60。”准确陈述标量2328.60，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT SUM(total) AS total_amount FROM invoice;
```

已有系统SQL：

```sql
SELECT SUM("total") AS total_sum FROM "public"."invoice"
```

已有系统自然语言：查询结果：2328.60。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-18：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第18行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第12行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第94行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第95行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-09：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-19

题目：billing_country 为 Canada 的全部 invoice 的 total 总和是多少？

参考：AI建议通过。显式给出billing_country=Canada、invoice及total，保留发票账单国家字段和全量SUM口径，不借当前地区值一致替换customer.country。 题目明确账单国家Canada，筛选invoice.billing_country而非customer.country；SUM(invoice.total)统计全部匹配发票，结果303.96（数据库金额单位），不做明细JOIN重复计额。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：303.96。”准确陈述标量303.96，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Canada';
```

已有系统SQL：

```sql
SELECT SUM("total") FROM "public"."invoice" WHERE "billing_country" = 'Canada'
```

已有系统自然语言：查询结果：303.96。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-19：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第19行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第13行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第96行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第97行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-33：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-21

题目：咱们客户表一共有几个人？

参考：AI建议通过。“客户表”“一共几个人”明确指客户记录总数，COUNT(*)口径不变。 对象为客户表全体记录，customer_id 是非空主键；COUNT(*) 每客户计一次，不受其他可空列影响，不加期间或国家过滤。参考结果为59位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：59。”准确陈述标量59，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer;
```

已有系统SQL：

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer"
```

已有系统自然语言：查询结果：59。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-21：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第21行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第14行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第98行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第99行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-01：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-22

题目：帮我数数，来自巴西的客户有几位呀？

参考：AI建议通过。“帮我数数/几位呀”只是请求语气，巴西客户国家筛选及人数计数均未变化。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

已有系统SQL：

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer" WHERE "country" = 'Brazil'
```

已有系统自然语言：查询结果：5。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-22：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第22行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第15行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第100行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第101行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-02：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-23

题目：这批曲目的平均长度是几毫秒？

参考：AI建议有条件通过。基题明确“全部曲目”，变体改为“这批曲目”引入未定义的指代范围；原始请求是该单条消息，scope仅指数据库，已有证据没有提供曲目批次或集合。gold直接AVG全track只在“这批=全库曲目”另行确认时成立，不能用base_id或EX相同替代用户范围证据。 基题明确全部曲目及毫秒，基题对应的全库AVG(track.milliseconds)为每条曲目等权平均，没有除1000转秒或按销售数量加权；milliseconds非空，基题的全库结果为393599.212103910933毫秒。该全库结果不能独立证明变体中未定义的“这批”范围。

实际：证据不足。已有SQL、数值393599.212103910933和自然语言确实对应全库track平均毫秒；但系统未澄清“这批”指哪个集合，也未在intent.assumptions中声明全集假设。缺少范围证据，不能确定全库平均是否回答了用户请求，即使gold和EX相同也暂不能判定正确。

已有参考SQL：

```sql
SELECT AVG(milliseconds) AS average_milliseconds FROM track;
```

已有系统SQL：

```sql
SELECT AVG("milliseconds") AS average_milliseconds FROM "public"."track"
```

已有系统自然语言：查询结果：393599.212103910933。

建议：人工确认指代集合；若目标为保持基题语义，应将变体范围说清楚，或补充合法上下文再独立核对。不能通过改参考平均值来使系统过关。

人工待确认：需要确认“这批”具体指哪些曲目；该确认到位前，实际回答暂不能确定。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-23：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第23行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第16行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第102行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第103行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-10：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-24

题目：曲目里最短的一首有几毫秒呀？

参考：AI建议通过。“曲目里最短的一首有几毫秒呀”请求最短时长值，语气变化不引入期间、销量或指定曲目集合；MIN(milliseconds)与基题一致。 最短时长取MIN(track.milliseconds)，milliseconds非空，得到1071毫秒；题目只要最短值，标量聚合正确，无需返回任意一首同长曲目的姓名或编号。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：1071。”准确陈述标量1071，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT MIN(milliseconds) AS minimum_milliseconds FROM track;
```

已有系统SQL：

```sql
SELECT MIN("milliseconds") AS "min_milliseconds" FROM "public"."track"
```

已有系统自然语言：查询结果：1071。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-24：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第24行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第17行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第104行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第105行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-34：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-26

题目：你好，请帮忙查一下来自巴西的客户有多少位，谢谢。

参考：AI建议通过。“你好/请帮忙/谢谢”属于礼貌冗词，来自巴西的客户人数条件完整且与基题一致，没有新增约束。 “来自巴西”限定客户所在国家，正确字段是customer.country、真实英文值Brazil；COUNT(*)统计满足筛选的客户，不用invoice.billing_country。参考结果为5位。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：5。”准确陈述标量5，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。 中间rewritten_question吞掉请求词，单独标记改写质量问题；最终SQL仍保留客户国家Brazil的条件和5位计数，不能因此误判最终答案错误。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Brazil'
```

已有系统自然语言：查询结果：5。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。 人工单独核对改写跨度及语句通顺程度；保留最终输出正确性的独立判断。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-26：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第26行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第18行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第106行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第107行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-02：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-27

题目：麻烦帮我看看，有多少位客户没有填写公司名称，也就是 company 为 NULL 呢？谢谢。

参考：AI建议通过。礼貌冗词之外明确重申company为NULL，仍用IS NULL统计客户，不将NULL变成空串。 题目明确定义company为NULL，使用IS NULL而非等于NULL、空串或COUNT(company)；COUNT(*)得到49位，实库company空字符串为0，未改变NULL语义。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：49。”准确陈述标量49，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE company IS NULL;
```

已有系统SQL：

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "company" IS NULL
```

已有系统自然语言：查询结果：49。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-27：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第27行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第19行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第108行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第109行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-26：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-28

题目：请帮我查一查，2023 年一共开了多少张发票，非常感谢。

参考：AI建议通过。礼貌冗词之外保留2023年开票数量，半开年度范围及COUNT(*)均不变。 2023年开票数以invoice.invoice_date范围[2023-01-01,2024-01-01)过滤，再COUNT(*)；实库2023年83张，与当前日期无关，不把发票行数当发票数。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：83。”准确陈述标量83，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01';
```

已有系统SQL：

```sql
SELECT COUNT(*) AS invoice_count FROM "public"."invoice" WHERE "invoice_date" >= '2023-01-01' AND "invoice_date" < '2024-01-01'
```

已有系统自然语言：查询结果：83。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-28：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第28行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第20行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第110行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第111行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-39：基题也属于dev；逐项对照变体是否改变题意

## robust:robust-29

题目：麻烦查一下客户所在国家为 Wakanda 的客户有多少位，保留原值，没匹配返回 0，谢谢。

参考：AI建议通过。礼貌冗词之外保留客户国家Wakanda、原值保护和无匹配返回0，COUNT(*)口径不变。 明确保留Wakanda原值，country = 'Wakanda'在实库无匹配；COUNT(*)自然返回0，未纠错到真实国家、未返回空列表或NULL。

实际：AI建议通过。已有系统SQL的字段、过滤、聚合和排序与上述题意相符。原自然语言“查询结果：0。”准确陈述标量0，没有补造币种、期间或支付含义。 原始response状态SUCCEEDED、sql_exec为ok、metadata.truncated=false；只读重执行现有SQL与原结果值相同，不将执行成功或EX相同单独作为语义通过依据。

已有参考SQL：

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Wakanda';
```

已有系统SQL：

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer" WHERE "country" = 'Wakanda'
```

已有系统自然语言：查询结果：0。

建议：保留现有材料，提交人工核对题意与既有输出；AI预审只提出建议，不写入原人审字段。

人工待确认：待人工确认本题参考与实际输出；本报告没有填入A/B审核人、审核时间或原表审批状态。

证据：
- `eval/reports/d2-acceptance/unified-review.json`，robust:robust-29：仅dev题干、参考和已有输出
- `eval/datasets/robust.jsonl`，第29行：原dev题干、gold SQL/结果、列类型及排序约束，与统一表逐字段一致
- `eval/artifacts/d2/robust/final/responses.jsonl`，第21行：原请求、SQL、结果表、答案、intent和步骤
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第112行：重执行已有参考SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第113行：重执行已有系统SELECT，真实结果与耗时
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; row_counts; text_values：真实字段/可空性/英文值，不以别名候选本身证明题意
- `data/catalog/chinook.yaml`，tables：结构、外键、字段含义与单位
- `data/rules/metric_definitions.json`，general; metrics：已确认项目口径、半开期间、金额单位及NULL规则
- `eval/reports/d2-acceptance/unified-review.json`，nl2sql:sql-44：基题也属于dev；逐项对照变体是否改变题意
