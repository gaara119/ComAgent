# V0 任务①：未自动确认条目的独立AI语义预审

本轮实际读取冻结开发题、原始评分、真实API响应/SQL/结果、补充归档provider请求、目录主键/外键、已确认业务规则和当前别名表。只读核验，不调用模型/API/数据库，不改评分器、题库、prompt、别名或人工记录。

原始任务①30题：26可评分、4标签待确认；原自动确认14/26、失败8、语义AI待定4。下面审读16条未自动确认记录，AI意见单独列出，不重写原分数。全部人工状态仍pending。

|原编号|原自动complete|原可评分|参考AI判断|实际系统AI判断|
|---|---|---|---|---|
|sp01-02|None|True|AI建议通过|AI建议通过|
|sp01-05|False|True|AI建议有条件通过|AI发现错误|
|sp01-06|None|False|AI发现错误|AI发现错误|
|sp01-07|False|True|AI建议通过|AI发现错误|
|sp01-10|False|True|AI建议通过|AI发现错误|
|sp01-12|False|True|AI建议有条件通过|AI建议有条件通过|
|sp01-13|None|False|AI建议有条件通过|AI建议通过|
|sp01-14|None|False|AI建议有条件通过|证据不足|
|sp01-16|None|True|AI建议通过|AI建议通过|
|sp01-18|False|True|AI建议有条件通过|AI发现错误|
|sp01-20|False|True|AI建议有条件通过|AI发现错误|
|sp01-22|False|True|AI建议通过|AI发现错误|
|sp01-25|None|True|AI发现错误|证据不足|
|sp01-27|False|True|AI建议通过|AI建议通过|
|sp01-28|None|False|AI发现错误|AI建议有条件通过|
|sp01-30|None|True|AI发现错误|证据不足|

独立参考判断统计：{"AI建议通过": 6, "AI建议有条件通过": 6, "AI发现错误": 4}。实际系统判断统计：{"AI建议通过": 4, "AI发现错误": 7, "AI建议有条件通过": 2, "证据不足": 3}。这些是16条审读记录的建议分布，不是重算的系统成绩。

优先事项：02/16由PK/FK证明COUNT等价；27实际保留两候选，原集合表示判据误判；12/25地区默认依据需确认；30原题明确12/31左闭右开却参考扩展到翌年1/1，先保留新增争议，不靠COUNT0同值通过。

## 逐项材料与判断

### sp01-02 · alias

**题目**：Iron Maiden乐队一共有多少张专辑？

**参考AI判断**：AI建议通过。**系统AI判断**：AI建议通过。

**判断依据**：专辑album_id是不可空主键，每张专辑通过artist_id关联至artist唯一主键；WHERE artist.name限定Iron Maiden。该多对一连接每个专辑至多保留一行，COUNT(*)与COUNT(DISTINCT album_id)等价。SELECT别名不改变语义。该判断依靠约束与过滤，不只依据结果21相同。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden';
```

**真实最终状态与SQL**：`SUCCEEDED`，controller结果`finished`。

```sql
SELECT COUNT(DISTINCT a.album_id) AS album_count FROM public.album AS a JOIN public.artist AS ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden'
```

**原准备阶段gold结果**：`{"columns": ["album_count"], "rows": [[21]], "table": [{"album_count": 21}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`[{"album_count": 21}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-02/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-02/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-02/turns/000/provider/063925f848234e299c983739f6243874.json>)（SHA `118623086870f935147cdac5ba8a709d0db8c8b24c21c5a86e07317a41bb0f72`）。

**仍需人工核对**：
- AI意见不代替人工验收；保持pending_human_review

### sp01-05 · typo

**题目**：Metallcia 有多少张专辑？

**参考AI判断**：AI建议有条件通过。**系统AI判断**：AI发现错误。

**判断依据**：冻结参考把Metallcia恢复为Metallica，再按album→artist真实FK统计专辑，已有原只读标准结果10；恢复依据仍需人工确认。当前NLU没有成功绑定且生成SQL仍筛Metallcia，没有恢复原意；实际allow_joins=false三次拒绝，未执行。放开关联本身不能修复拼写解析。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Metallica';
```

**真实最终状态与SQL**：`FAILED`，controller结果`api_failed`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE LOWER(ar."name") = LOWER('Metallcia')
```

**原准备阶段gold结果**：`{"columns": ["album_count"], "rows": [[10]], "table": [{"album_count": 10}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`null`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-05/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/0b9a859981c04fe580c54d892283391c.json>)（SHA `b48f24b2bbcd399d448c55ce1de36b9b64bd107fc16b8855de0100db6b178989`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/4346b559dd5141e3b66d897b24e5ae51.json>)（SHA `54190dd1ac3c66162680a556168b30e4e43c194c7fe247aaef17308ace405708`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/fa1b4a7aaa1b4fc29efced7c79ff1c8f.json>)（SHA `b26ccdf6a0f1df52e3bacf25e6cda092ae70744a6cac1d72de6e88a593d61f41`）。

**仍需人工核对**：
- 确认拼写恢复候选的业务接受规则

### sp01-06 · pinyin

**题目**：Deguo 有多少张专辑？

**参考AI判断**：AI发现错误。**系统AI判断**：AI发现错误。

**判断依据**：题面Deguo查询专辑，canonical_input却写加拿大；controller补充又改为Iron Maiden，冻结材料不能构成唯一可执行参考，且仍scorable=false。当前实际直接COUNT全部347张专辑，完全丢弃Deguo约束，没有声明假设或澄清，这是可独立观察的条件丢失。正式按参考计分仍暂不能确定，不能把347或任何近似艺术家当gold。

**冻结参考SQL**：

```sql
无唯一标准SQL；保留原状态
```

**真实最终状态与SQL**：`SUCCEEDED`，controller结果`finished`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album"
```

**原准备阶段gold结果**：`null`。

**本次既有真实返回**：`[{"album_count": 347}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-06/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-06/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-06/turns/000/provider/5f19d602514d4d789d45d271c9462f52.json>)（SHA `243dd2e44ca478563dae99d79dd88dd85d0557d0f81bbe33fcb6bbac2b12d1ef`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-06/turns/000/provider/d18462a1fa484d17ba5e8b6dec581cf3.json>)（SHA `2f51ac34265ed1b7b320df23f487e8d27aa5634b17695029b0026fec9bc5af26`）。

**仍需人工核对**：
- 重审原题/改写/controller对应关系；保持当前不可评分状态

### sp01-07 · mixed_language

**题目**：Chinook 里 Protected AAC audio file 这种 format 有多少首曲目？

**参考AI判断**：AI建议通过。**系统AI判断**：AI发现错误。

**判断依据**：明确格式Protected AAC audio file对应media_type.name；完整媒体枚举给出唯一真实media_type_id=2，track持外键引用其主键。参考按名称等值和COUNT曲目无重复粒度问题；三次实际SQL保留格式与FK，但单表模式拒绝，table=null，不能把候选SQL语义正确写成实际回答已成功。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'Protected AAC audio file';
```

**真实最终状态与SQL**：`FAILED`，controller结果`api_failed`。

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" AS t JOIN "public"."media_type" AS mt ON t."media_type_id" = mt."media_type_id" WHERE mt."name" = 'Protected AAC audio file'
```

**原准备阶段gold结果**：`{"columns": ["track_count"], "rows": [[237]], "table": [{"track_count": 237}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`null`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-07/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/provider/0562181de4954732b774b0d6d047faf1.json>)（SHA `7c8d60cdf3c98e9795fc403563a3d050cb09108edbb5a2bc04cadec5b22e5a65`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/provider/cca2ab7396244837a8ddf8ea7d0a47ff.json>)（SHA `5119bedf2378ec15e9e1df7fd9904ce49c72627a898588c0ec3370e1d439f09f`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/provider/e00b4b02d3a04b8f87f444136c48c325.json>)（SHA `77d1d53ca1fdf39a6c48ed747823d80e9e4cb4c2014ec622d54d146b5e85840d`）。

**仍需人工核对**：
- AI意见不代替人工验收；保持pending_human_review

### sp01-10 · explicit_absent

**题目**：查询 genre 为 Vaporwave 的曲目数量；如果数据库里根本没有这个流派，请直接报告没有记录。

**参考AI判断**：AI建议通过。**系统AI判断**：AI发现错误。

**判断依据**：用户明确要求按Vaporwave字面查，无记录即报告，禁止替换附近流派。完整25流派无该值，按track→genre真实FK及名称等值COUNT返回0符合语义。实际没有替换Vaporwave，但三次关联策略拒绝，未执行也未给出真实计数回答。INNER JOIN交换左右表不改变本查询语义；仍不能把未执行候选当成功。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.genre g ON t.genre_id = g.genre_id WHERE g.name = 'Vaporwave';
```

**真实最终状态与SQL**：`FAILED`，controller结果`api_failed`。

```sql
SELECT COUNT(*) AS track_count FROM "public"."genre" AS g JOIN "public"."track" AS t ON t."genre_id" = g."genre_id" WHERE g."name" = 'Vaporwave'
```

**原准备阶段gold结果**：`{"columns": ["track_count"], "rows": [[0]], "table": [{"track_count": 0}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`null`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-10/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider/2149524392eb4bc7bd058c9ccd042941.json>)（SHA `cc4844df571dbbc9e6647caabb0124b2d1b51180b1aa53b2eecbf5aef22632e8`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider/99831a454eae4c509df631cdb642274e.json>)（SHA `e0da2346d71c68321cc90046b0fdc27ad7cf3a7bcaf5983db7384138a187ca71`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider/b54055942eeb484e9bb0844cec0761b2.json>)（SHA `5c334b9b57a30ff7a5c960987cf81d2d86f77af92b9503d13237b8bbb6c04a1d`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider/fed00224f20b4285adec985dbb28abcf.json>)（SHA `83fe7e546508bab6dac610986c37681610c064863f8685d385e4eb9a23aa7f93`）。

**仍需人工核对**：
- AI意见不代替人工验收；保持pending_human_review

### sp01-12 · standard

**题目**：What was the total invoice revenue for France in 2022?

**参考AI判断**：AI建议有条件通过。**系统AI判断**：AI建议有条件通过。

**判断依据**：英文total invoice revenue for France in 2022明确SUM(invoice.total)和2022半开年度，未明确France是账单国还是客户所在地。已确认general.region只区分两字段，无全局默认；参考billing SQL在该解释下逻辑正确，但直接L0唯一选择仍需确认。系统实际L2询问地区字段具有业务依据；controller没有这项补充，终止无SQL，不能仅凭固定direct标签认定误问，也不能称已完成回答。

**冻结参考SQL**：

```sql
SELECT SUM(total) AS revenue FROM public.invoice WHERE billing_country = 'France' AND invoice_date >= DATE '2022-01-01' AND invoice_date < DATE '2023-01-01';
```

**真实最终状态与SQL**：`NEEDS_CLARIFICATION`，controller结果`controller_unanswered`。

```sql
未生成实际SQL
```

**原准备阶段gold结果**：`{"columns": ["revenue"], "rows": [["39.60"]], "table": [{"revenue": "39.60"}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`null`。

**实际候选选项**：`[{"id": "billing_country", "label": "按发票账单国家"}, {"id": "customer_country", "label": "按客户所在地国家"}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-12/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-12/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-12/turns/000/provider/72a25f23220748cbb91e141ad264637f.json>)（SHA `3623b427a56248b5a136096e9922007ffc998ce7d9098afbc27485039f189e79`）。

**仍需人工核对**：
- 确认invoice+for国家是否有团队批准的默认地区口径，或应要求澄清

### sp01-13 · alias

**题目**：Iron Maiden乐队一共有多少张专辑？

**参考AI判断**：AI建议有条件通过。**系统AI判断**：AI建议通过。

**判断依据**：参考内容与实际查询均按已准Iron Maiden乐队别名、album→artist FK及名称等值计数；实际21、NLU绑定完整。与sp01-02原始题面完全重复，已有scorable=false是题库质量问题。AI可判断本次回答语义正确，但不能把重复题重新加入原评分分母或当新的独立覆盖。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS album_count FROM public.album al JOIN public.artist ar ON al.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden';
```

**真实最终状态与SQL**：`SUCCEEDED`，controller结果`finished`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE ar."name" = 'Iron Maiden'
```

**原准备阶段gold结果**：`{"columns": ["album_count"], "rows": [[21]], "table": [{"album_count": 21}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`[{"album_count": 21}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-13/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-13/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-13/turns/000/provider/a6a058f2bc73461a9a8fdef06f9ac656.json>)（SHA `6ed982f612a6450fd45a2293dd8cef030788c4347a1a8c8683f2278ebba597d9`）。

**仍需人工核对**：
- 是否保留重复作一致性样本；不改当前不可评分标记

### sp01-14 · alias

**题目**：法兰西共和国的发票一共开了多少张？

**参考AI判断**：AI建议有条件通过。**系统AI判断**：证据不足。

**判断依据**：冻结材料允许customer.country或invoice.billing_country两种解释，却gold唯一选customer.country，题面法兰西共和国的发票没有给出客户居住地。已确认规则不合并两者。系统选择账单国并得到35，当前同值不能证明客户国参考正确，也不能证明系统错误；原标签已不可评分，等待明确口径。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS invoice_count FROM public.invoice i JOIN public.customer c ON i.customer_id = c.customer_id WHERE c.country = 'France';
```

**真实最终状态与SQL**：`SUCCEEDED`，controller结果`finished`。

```sql
SELECT COUNT(*) AS invoice_count FROM "public"."invoice" WHERE "billing_country" = 'France'
```

**原准备阶段gold结果**：`{"columns": ["invoice_count"], "rows": [[35]], "table": [{"invoice_count": 35}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`[{"invoice_count": 35}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-14/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-14/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-14/turns/000/provider/9c9281cb9bc44d009d6f9be2c5e56fa5.json>)（SHA `744a04b4127de402eb775575a1632be5c65c47cfe0c3772a4dd63855ab51f22e`）。

**仍需人工核对**：
- 确认题面所需的地区字段或澄清策略

### sp01-16 · alias

**题目**：U2乐队一共有多少张专辑？

**参考AI判断**：AI建议通过。**系统AI判断**：AI建议通过。

**判断依据**：U2乐队别名已approved，真实artist=U2。参考COUNT(DISTINCT album_id)，实际COUNT(*)；album主键不可空且album→artist为多对一真实FK，没有JOIN明细或其他可重复来源，过滤/范围一致，所以等价。实际10相同是附加执行证据，不是等价证明本身。

**冻结参考SQL**：

```sql
SELECT COUNT(DISTINCT a.album_id) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'U2';
```

**真实最终状态与SQL**：`SUCCEEDED`，controller结果`finished`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE ar."name" = 'U2'
```

**原准备阶段gold结果**：`{"columns": ["album_count"], "rows": [[10]], "table": [{"album_count": 10}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`[{"album_count": 10}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-16/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-16/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-16/turns/000/provider/47f0cecca8b946ae8d456a2ff2a3bfa9.json>)（SHA `4b01221e203b903b29b5ec4935a233102c69518ad4515a5c755ad1257579f69b`）。

**仍需人工核对**：
- AI意见不代替人工验收；保持pending_human_review

### sp01-18 · typo

**题目**：Led Zepelin 有多少张专辑？

**参考AI判断**：AI建议有条件通过。**系统AI判断**：AI发现错误。

**判断依据**：参考恢复Led Zepelin→Led Zeppelin并按album→artist真实FK计数，已存原只读gold14；恢复接受规则仍需人工核对。实际最终只SELECT artist_id并保留错误拼写、返回空表，查询对象和COUNT专辑目标丢失，也未声明纠正，不能用EMPTY_RESULT当正确答案。

**冻结参考SQL**：

```sql
SELECT COUNT(DISTINCT a.album_id) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Led Zeppelin';
```

**真实最终状态与SQL**：`EMPTY_RESULT`，controller结果`finished`。

```sql
SELECT "artist_id" FROM "public"."artist" WHERE LOWER("name") = LOWER('Led Zepelin') LIMIT 200
```

**原准备阶段gold结果**：`{"columns": ["album_count"], "rows": [[14]], "table": [{"album_count": 14}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`[]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-18/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-18/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/d1ccb2b86f914827a044d7089bbb6be7.json>)（SHA `3a78db742d27a389f55e08656f6e3613fb04ccd70d0870675bc0c08c06768b50`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/d9599e21191f4877992421a19b4a5db9.json>)（SHA `aef7e45fe49df99a59fc2e8195177ceba8cbb04ed72ee3810ca41ac7ff8ae3a3`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/fd278ffb120f47809d78c1c0a0e61925.json>)（SHA `2cd64c3ad2307f66720fd9d66806aa71597da21e769932f0d189167dcce4502a`）。

**仍需人工核对**：
- 确认拼写恢复策略，但当前对象/计数丢失有直接证据

### sp01-20 · typo

**题目**：MPEG adiou file 有多少首曲目？

**参考AI判断**：AI建议有条件通过。**系统AI判断**：AI发现错误。

**判断依据**：参考MPEG adiou file恢复为MPEG audio file，经真实media_type主键关联COUNT曲目，原只读结果3034。实际最终IN子查询已使用正确格式名，track.media_type_id IN (SELECT唯一主键...)在此等同对应INNER JOIN计数；但被跨表限制拒绝，未执行，没有返回计数或声明纠正。不能只改报告让API失败通过。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'MPEG audio file';
```

**真实最终状态与SQL**：`FAILED`，controller结果`api_failed`。

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" WHERE "media_type_id" IN (SELECT "media_type_id" FROM "public"."media_type" WHERE "name" = 'MPEG audio file')
```

**原准备阶段gold结果**：`{"columns": ["track_count"], "rows": [[3034]], "table": [{"track_count": 3034}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`null`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-20/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-20/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-20/turns/000/provider/c0c11ce530d841ff9135588f32c7a288.json>)（SHA `4d8b13fd3b1786d787ac69a2ae2d26fbd6ae5b9124fd3d50fcfa8330cc1c1fde`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-20/turns/000/provider/ceec9200792f473981348fb15b16899f.json>)（SHA `69f471dcd5d07828e8e28bb62a0729a50de1545206328a2724bec881aedb6209`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-20/turns/000/provider/f3c134048942450ba9258153e0e4c2e2.json>)（SHA `367878107edfe8b041e300251b1edc548b0b28fe0bac34891f757138259d01e2`）。

**仍需人工核对**：
- 确认该拼写恢复可接受；区别候选SQL等价与实际系统失败

### sp01-22 · pinyin

**题目**：Gudian 这个流派的曲目有多少首？

**参考AI判断**：AI建议通过。**系统AI判断**：AI发现错误。

**判断依据**：古典→Classical在当前别名表为approved，Gudian是其拼音；题面限定流派，参考track→genre按Classical计数，字段、对象、粒度正确。实际仍筛genre.name=Gudian，未还原拼音并被关联限制拒绝；无成功结果。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.genre g ON t.genre_id = g.genre_id WHERE g.name = 'Classical';
```

**真实最终状态与SQL**：`FAILED`，controller结果`api_failed`。

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" AS t JOIN "public"."genre" AS g ON t."genre_id" = g."genre_id" WHERE g."name" = 'Gudian'
```

**原准备阶段gold结果**：`{"columns": ["track_count"], "rows": [[74]], "table": [{"track_count": 74}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`null`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-22/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-22/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-22/turns/000/provider/38bbf1225b78404285afa5163e365db7.json>)（SHA `61569cad31d49458049074785def7705eb279382039cbed9d69e20649654f7f1`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-22/turns/000/provider/7b51d6cda1534d93b79709fa7df41780.json>)（SHA `b61fa40aa084631a86352ec090d4c1623dbc0c0d19ade1de1fb394e1b47cf1bb`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-22/turns/000/provider/f2330292cf9047fcbedd0830c507cc0b.json>)（SHA `5f168a21b43c9c443f6594e0c86018977ae6fbc6b2bae170734c0e23ccc21c6c`）。

**仍需人工核对**：
- 人工可核对拼音大小写/分词接受边界

### sp01-25 · colloquial

**题目**：意大利那边的发票总共开了多少钱？

**参考AI判断**：AI发现错误。**系统AI判断**：证据不足。

**判断依据**：题面意大利那边的发票总金额未明确地区字段；当前别名同时批准Italy映射customer.country及invoice.billing_country。参考expected_behavior声称已确认口径以客户居住地为准，但实际general.region/human_confirmation没有批准这种默认。gold在客户国解释下SQL逻辑可执行，不能证明该题唯一应选客户国。实际选择账单国同37.62不能证明两字段等价，按参考正式判分暂不能确定。

**冻结参考SQL**：

```sql
SELECT SUM(i.total) AS revenue FROM public.invoice i JOIN public.customer c ON i.customer_id = c.customer_id WHERE c.country = 'Italy';
```

**真实最终状态与SQL**：`SUCCEEDED`，controller结果`finished`。

```sql
SELECT SUM("total") AS total_invoice_amount FROM "public"."invoice" WHERE "billing_country" = 'Italy'
```

**原准备阶段gold结果**：`{"columns": ["revenue"], "rows": [["37.62"]], "table": [{"revenue": "37.62"}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`[{"total_invoice_amount": "37.62"}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-25/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-25/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-25/turns/000/provider/614447ac8b1849f3b013c0ecfeb0ee7e.json>)（SHA `3b199b0559cc0a60c5eba3f287c2c42240ae1eddb930d797c4cbc1ba0ccd796c`）。

**仍需人工核对**：
- 核对参考声称的客户所在地默认依据；目前禁止自动补该默认

### sp01-27 · multi_candidate

**题目**：Chinook 里摇滚曲目有多少首？

**参考AI判断**：AI建议通过。**系统AI判断**：AI建议通过。

**判断依据**：当前已准候选关系摇滚→Rock和Rock And Roll；两个均真实流派。实际L2列出两个同字段候选，未绑定任何一个、未执行SQL，符合请求的候选澄清行为。原scorer把expected的IN集合元组与retained的两个等值元组直接比subset，因此标false；这个观察是表示差异，不改冻结评分器/标签或原8失败数。

**冻结参考SQL**：

```sql
无唯一标准SQL；保留原状态
```

**真实最终状态与SQL**：`NEEDS_CLARIFICATION`，controller结果`candidate_only_clarification`。

```sql
未生成实际SQL
```

**原准备阶段gold结果**：`null`。

**本次既有真实返回**：`null`。

**实际候选选项**：`[{"id": "value:issue-fbaa1127c30ea0e7:v-5abaeb142337ce5b27ed", "label": "Rock（genre.name）"}, {"id": "value:issue-fbaa1127c30ea0e7:v-10facd793602b59518e7", "label": "Rock And Roll（genre.name）"}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-27/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-27/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)

**仍需人工核对**：
- 确认候选集合标准表示及下轮评分器版本；本轮只附独立AI意见

### sp01-28 · multi_candidate

**题目**：Chinook 里金属流派的曲目有多少首？

**参考AI判断**：AI发现错误。**系统AI判断**：AI建议有条件通过。

**判断依据**：题面明确金属流派，参考却把artist.name=Metallica列为候选；该金属艺术家别名实际pending，且artist候选与genre范围冲突，原scorable=false应保留。系统实际仅保留genre Metal的approved_candidate选项并追问，未绑定/执行，未使用禁用artist别名；这是符合范围及候选不得自动绑定的保守行为。是否还应提供Heavy Metal须人工确认对应候选关系，不能靠邻近值存在就批准。

**冻结参考SQL**：

```sql
无唯一标准SQL；保留原状态
```

**真实最终状态与SQL**：`NEEDS_CLARIFICATION`，controller结果`candidate_only_clarification`。

```sql
未生成实际SQL
```

**原准备阶段gold结果**：`null`。

**本次既有真实返回**：`null`。

**实际候选选项**：`[{"id": "value:issue-e5d51e4bda1a9a15:v-bf1c51869eccaa9deddc", "label": "Metal（genre.name）"}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-28/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-28/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)

**仍需人工核对**：
- 拒绝未经批准的Metallica artist候选；确认Heavy Metal是否有获准关系

### sp01-30 · explicit_absent

**题目**：统计 invoice_date 在 2030-01-01 到 2030-12-31（左闭右开）之间的发票张数；如果那段时间没有发票，就按这个时间范围查询并报告没有记录。

**参考AI判断**：AI发现错误。**系统AI判断**：证据不足。

**判断依据**：用户明确写2030-01-01到2030-12-31（左闭右开），应按字面上界<2030-12-31；参考SQL、allowed_interpretations和两遍AI却扩展为<2031-01-01，两遍原AI意见漏读了题面。实际SQL也采用<2031-01-01，未保持用户明确上界；当前无2030数据所以两者COUNT均0，结果同值无力区分期间错误。DATE CAST与同一字面串在invoice_date timestamp without time zone比较可解释为同一午夜，但这只能说明实际与错误参考的类型差异，不证明用户期间正确。参考不可靠，正式系统分数暂不能确定，冻结原结果/标签不改。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS invoice_count FROM public.invoice WHERE invoice_date >= DATE '2030-01-01' AND invoice_date < DATE '2031-01-01';
```

**真实最终状态与SQL**：`SUCCEEDED`，controller结果`finished`。

```sql
SELECT COUNT(*) AS invoice_count FROM "public"."invoice" WHERE "invoice_date" >= '2030-01-01' AND "invoice_date" < '2031-01-01'
```

**原准备阶段gold结果**：`{"columns": ["invoice_count"], "rows": [[0]], "table": [{"invoice_count": 0}], "row_count": 1, "truncated": false}`。

**本次既有真实返回**：`[{"invoice_count": 0}]`。

**证据位置**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-30/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-30/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-30/turns/000/provider/2640ac0e76d54cc3b817b63f45ccc6e7.json>)（SHA `80d534daae530fc7c1227b386dd67ce3cbcfdb8bed1391c36e91df9e86bdcf8e`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-30/turns/000/provider/4342a38189b741b383f7b75ca2c1d6bc.json>)（SHA `5864f23e141256ec9e27c2bdad7617baccb0bb247efa2b68589a60190019c74d`）。
- [已核验trace的provider原始请求与返回](<../runtime_eval/runs/V0-001/cases/sp01-30/turns/000/provider/a205b131ddc7464592134b1dcd2679fe.json>)（SHA `d857f68f847f83e12cb1db2830e70cd4b6a60bd24117686a686b4310456dea3f`）。

**仍需人工核对**：
- 优先确认用户原句是否本意整年，或必须保持12/31左闭右开；另存修订版只在人工决定后实施

## 另列绑定链路维度

以下不是16条未自动确认主表的一部分。sp01-04和sp01-17的SQL/result自动complete=true，但绑定指标false：实际intent.filters为空，不能将问题文本被SQL模型纠正与前置显式实体绑定混为一项通过。原绑定分数不改。

```json
[
  {
    "id": "sp01-04",
    "original_automatic_complete": true,
    "original_binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "extra": []
    },
    "actual_sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'France'",
    "actual_table": [
      {
        "count": 5
      }
    ],
    "observation": "SQL/result自动通过与显式绑定链路正确是不同维度；这两题没有产生所需France的intent绑定，不因为SQL碰巧纠正拼写就把binding指标改成通过。",
    "evidence_file": "eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-04/checkpoint.json"
  },
  {
    "id": "sp01-17",
    "original_automatic_complete": true,
    "original_binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "extra": []
    },
    "actual_sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'France'",
    "actual_table": [
      {
        "customer_count": 5
      }
    ],
    "observation": "SQL/result自动通过与显式绑定链路正确是不同维度；这两题没有产生所需France的intent绑定，不因为SQL碰巧纠正拼写就把binding指标改成通过。",
    "evidence_file": "eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-17/checkpoint.json"
  }
]
```

## 原始结果保护与审核边界

所有新增意见独立保存，原14/26、8失败、4语义待定、4标签待定及60候选/49原可评分/11原标签争议不重写。12/25/30为新增参考问题候选，需与原49可评分标签区别展示；本轮不据此重划分、重造题或重跑。同值不能证明两地区字段等价，也不能证明2030区间正确。

完整逐项原评分、实际SQL/结果、PK/FK等价依据、文件SHA见 [机器报告](v0-task01-semantic-review.json)。此报告没有A/B签字或人工日期。
