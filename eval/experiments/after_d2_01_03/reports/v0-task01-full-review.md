# V0 任务①30题逐项完整AI预审

实际逐题读取原始input、冻结gold、已有SQL/返回表/绑定/改写、trace匹配的provider归档、真实目录/PK/FK、已确认规则与当前别名。此前16题报告保持原文件，本次额外独立核对14题automatic_complete=true并合并成30题索引。没有新模型/API/数据库调用，不改任何代码、提示词、数据、评分或人工记录。

原始成绩仍为26可评分、4标签待定；自动确认14/26、8失败、4语义待定。表内AI建议分布不替代原分数。原60候选、49可评分、11标签待定保持冻结；新增03/12/25/30参考争议另外等待人工核对。

|原编号|原自动complete|原可评分|参考AI判断|实际系统AI判断|
|---|---|---|---|---|
|sp01-01|True|True|AI建议通过|AI建议通过|
|sp01-02|None|True|AI建议通过|AI建议通过|
|sp01-03|True|True|AI建议有条件通过|AI建议有条件通过|
|sp01-04|True|True|AI建议有条件通过|AI建议有条件通过|
|sp01-05|False|True|AI建议有条件通过|AI发现错误|
|sp01-06|None|False|AI发现错误|AI发现错误|
|sp01-07|False|True|AI建议通过|AI发现错误|
|sp01-08|True|True|AI建议通过|AI建议通过|
|sp01-09|True|True|AI建议通过|AI建议通过|
|sp01-10|False|True|AI建议通过|AI发现错误|
|sp01-11|True|True|AI建议通过|AI建议通过|
|sp01-12|False|True|AI建议有条件通过|AI建议有条件通过|
|sp01-13|None|False|AI建议有条件通过|AI建议通过|
|sp01-14|None|False|AI建议有条件通过|证据不足|
|sp01-15|True|True|AI建议通过|AI建议通过|
|sp01-16|None|True|AI建议通过|AI建议通过|
|sp01-17|True|True|AI建议有条件通过|AI发现错误|
|sp01-18|False|True|AI建议有条件通过|AI发现错误|
|sp01-19|True|True|AI建议有条件通过|AI建议通过|
|sp01-20|False|True|AI建议有条件通过|AI发现错误|
|sp01-21|True|True|AI建议通过|AI建议通过|
|sp01-22|False|True|AI建议通过|AI发现错误|
|sp01-23|True|True|AI建议通过|AI建议通过|
|sp01-24|True|True|AI建议通过|AI建议通过|
|sp01-25|None|True|AI发现错误|证据不足|
|sp01-26|True|True|AI建议通过|AI建议通过|
|sp01-27|False|True|AI建议通过|AI建议通过|
|sp01-28|None|False|AI发现错误|AI建议有条件通过|
|sp01-29|True|True|AI建议通过|AI建议有条件通过|
|sp01-30|None|True|AI发现错误|证据不足|

参考AI建议分布：{"AI建议通过": 16, "AI建议有条件通过": 10, "AI发现错误": 4}；系统AI建议分布：{"AI建议通过": 14, "AI建议有条件通过": 5, "AI发现错误": 8, "证据不足": 3}。

不能默认自动成功就是整个链路成功：04/17的SQL/result正确但绑定链路缺失；17未声明纠正。09是正确初始候选澄清，没有执行SQL。19有接口改写/patch信息，UI源码具备在答案前展示能力，但本题没有新增浏览器实测。29精确保留不存在字面值并返回COUNT0，明确“没有记录”的展示措辞待人工核对。

## sp01-01 · standard

**题目**：How many customers are from France?

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：题面customers明确客户对象，France真实country值。COUNT(*)按customer.country等值计数，未加账单国、时间或金额条件，主键记录粒度正确；NULL country不满足等值，COUNT仍记录数。实际binding来自exact索引、SQL/结果5、列别名count不改语义。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'France';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'France'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[5]], "table": [{"customer_count": 5}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 5}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": false, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-01/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-01/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-01/turns/000/provider/61444056c5834c7aa8b8a85c9a8ba06f.json>)（SHA `52941fa3f15100124bbee769cca3aac55b977050c732d879d5278c2134251bd1`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-02 · alias

**题目**：Iron Maiden乐队一共有多少张专辑？

**原自动complete**：`None`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：专辑album_id是不可空主键，每张专辑通过artist_id关联至artist唯一主键；WHERE artist.name限定Iron Maiden。该多对一连接每个专辑至多保留一行，COUNT(*)与COUNT(DISTINCT album_id)等价。SELECT别名不改变语义。该判断依靠约束与过滤，不只依据结果21相同。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(DISTINCT a.album_id) AS album_count FROM public.album AS a JOIN public.artist AS ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden'
```

**原参考结果**：`{"columns": ["album_count"], "rows": [[21]], "table": [{"album_count": 21}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"album_count": 21}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-02/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-02/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-02/turns/000/provider/063925f848234e299c983739f6243874.json>)（SHA `118623086870f935147cdac5ba8a709d0db8c8b24c21c5a86e07317a41bb0f72`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-03 · alias

**题目**：德国的发票一共开了多少钱？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI建议有条件通过。

**判断理由**：按发票账单国解释时，approved德国→invoice.billing_country Germany、SUM(invoice.total)、发票粒度和实际156.48均正确，无明细连接重复累加，也没有推断币种或支付状态。但德国的发票没有明说账单国；已确认规则仅区分客户国/账单国而无全局默认。本题与12英文、25口语的地区归属需统一人工判定；不能因自动AST相同就批准隐含地区语义。

**标准SQL（冻结，未改）**：

```sql
SELECT SUM(i.total) AS revenue FROM public.invoice i WHERE i.billing_country = 'Germany';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT SUM("total") FROM "public"."invoice" WHERE "billing_country" = 'Germany'
```

**原参考结果**：`{"columns": ["revenue"], "rows": [["156.48"]], "table": [{"revenue": "156.48"}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"sum": "156.48"}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": true, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**接口实际改写**：Germany的发票一共开了多少钱？。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-03/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-03/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-03/turns/000/provider/d62034143c3c4c0d91d9aaea8b3d7385.json>)（SHA `0b95cdec71434612d3f2b7303770f7b25f2757d1361cf23bb5e58fa5a8bfa02c`）。

**人工待核**：
- 核对发票+国名这一语境能否作为账单国家的获准字段限定；与12/14/25保持一致

## sp01-04 · typo

**题目**：Frnace 有多少客户？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI建议有条件通过。

**判断理由**：题面Frnace拼写候选France在客户国家中真实存在；标准customer.country France计数逻辑正确。实际SQL/结果5也符合该恢复解释，但value_link没有mention、intent.filters为空、rewritten_question=null，没有可追踪的受限纠错绑定或前端修改依据。SQL结果正确与实体绑定链路正确必须分开，原binding=false不改。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'France';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'France'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[5]], "table": [{"customer_count": 5}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 5}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": false, "rewritten_question_available": false, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-04/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-04/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-04/turns/000/provider/d445c8d060874f25833a3a5fc916ecea.json>)（SHA `da225291dbb798f448316b881479a998a42c07cb87cdc4aee97dd2a79bd16ca4`）。

**人工待核**：
- 确认字面拼写恢复策略；NLU/声明缺项不标完整链路通过

## sp01-05 · typo

**题目**：Metallcia 有多少张专辑？

**原自动complete**：`False`；**原可评分**：`True`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI发现错误。

**判断理由**：冻结参考把Metallcia恢复为Metallica，再按album→artist真实FK统计专辑，已有原只读标准结果10；恢复依据仍需人工确认。当前NLU没有成功绑定且生成SQL仍筛Metallcia，没有恢复原意；实际allow_joins=false三次拒绝，未执行。放开关联本身不能修复拼写解析。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Metallica';
```

**既有实际最终状态/SQL**：`FAILED`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE LOWER(ar."name") = LOWER('Metallcia')
```

**原参考结果**：`{"columns": ["album_count"], "rows": [[10]], "table": [{"album_count": 10}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`null`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-05/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/0b9a859981c04fe580c54d892283391c.json>)（SHA `b48f24b2bbcd399d448c55ce1de36b9b64bd107fc16b8855de0100db6b178989`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/4346b559dd5141e3b66d897b24e5ae51.json>)（SHA `54190dd1ac3c66162680a556168b30e4e43c194c7fe247aaef17308ace405708`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/fa1b4a7aaa1b4fc29efced7c79ff1c8f.json>)（SHA `b26ccdf6a0f1df52e3bacf25e6cda092ae70744a6cac1d72de6e88a593d61f41`）。

**人工待核**：
- 确认拼写恢复候选的业务接受规则

## sp01-06 · pinyin

**题目**：Deguo 有多少张专辑？

**原自动complete**：`None`；**原可评分**：`False`。

**参考AI判断**：AI发现错误；**系统AI判断**：AI发现错误。

**判断理由**：题面Deguo查询专辑，canonical_input却写加拿大；controller补充又改为Iron Maiden，冻结材料不能构成唯一可执行参考，且仍scorable=false。当前实际直接COUNT全部347张专辑，完全丢弃Deguo约束，没有声明假设或澄清，这是可独立观察的条件丢失。正式按参考计分仍暂不能确定，不能把347或任何近似艺术家当gold。

**标准SQL（冻结，未改）**：

```sql
无唯一gold SQL
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album"
```

**原参考结果**：`null`。

**既有实际结果**：`[{"album_count": 347}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-06/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-06/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-06/turns/000/provider/5f19d602514d4d789d45d271c9462f52.json>)（SHA `243dd2e44ca478563dae99d79dd88dd85d0557d0f81bbe33fcb6bbac2b12d1ef`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-06/turns/000/provider/d18462a1fa484d17ba5e8b6dec581cf3.json>)（SHA `2f51ac34265ed1b7b320df23f487e8d27aa5634b17695029b0026fec9bc5af26`）。

**人工待核**：
- 重审原题/改写/controller对应关系；保持当前不可评分状态

## sp01-07 · mixed_language

**题目**：Chinook 里 Protected AAC audio file 这种 format 有多少首曲目？

**原自动complete**：`False`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI发现错误。

**判断理由**：明确格式Protected AAC audio file对应media_type.name；完整媒体枚举给出唯一真实media_type_id=2，track持外键引用其主键。参考按名称等值和COUNT曲目无重复粒度问题；三次实际SQL保留格式与FK，但单表模式拒绝，table=null，不能把候选SQL语义正确写成实际回答已成功。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'Protected AAC audio file';
```

**既有实际最终状态/SQL**：`FAILED`。

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" AS t JOIN "public"."media_type" AS mt ON t."media_type_id" = mt."media_type_id" WHERE mt."name" = 'Protected AAC audio file'
```

**原参考结果**：`{"columns": ["track_count"], "rows": [[237]], "table": [{"track_count": 237}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`null`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-07/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/provider/0562181de4954732b774b0d6d047faf1.json>)（SHA `7c8d60cdf3c98e9795fc403563a3d050cb09108edbb5a2bc04cadec5b22e5a65`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/provider/cca2ab7396244837a8ddf8ea7d0a47ff.json>)（SHA `5119bedf2378ec15e9e1df7fd9904ce49c72627a898588c0ec3370e1d439f09f`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/provider/e00b4b02d3a04b8f87f444136c48c325.json>)（SHA `77d1d53ca1fdf39a6c48ed747823d80e9e4cb4c2014ec622d54d146b5e85840d`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-08 · colloquial

**题目**：意大利那边现在有多少客户？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：意大利那边明确客户对象，对应已准customer.country Italy，COUNT1符合真实客户记录。现在按当前导入客户快照统计，不凭缺失创建/活跃日期捏造时段。实际approved alias binding和rewritten保留那边现在语境，SQL没有换成账单国或添加日期条件。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Italy';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Italy'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[1]], "table": [{"customer_count": 1}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 1}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": true, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**接口实际改写**：Italy那边现在有多少客户？。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-08/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-08/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-08/turns/000/provider/5e20bad6df4b410996daef7b78669fe5.json>)（SHA `580d9ec5346d06751e390def09fb4ca2239ae94dba2ba6ec8efa769b5489ad20`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-09 · multi_candidate

**题目**：Chinook 里有多少首摇滚歌曲？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：摇滚获准的是Rock与Rock And Roll两genre候选关系，并非唯一绑定。实际NEEDS_CLARIFICATION/L2提供这两个真实选项、intent.filters空、没有SQL/结果，符合该题的初始候选澄清目标。gold_sql/gold_result均无唯一值，不能把它们解读成NULL聚合或0，也不能误称本题实际SQL已成功执行。

**标准SQL（冻结，未改）**：

```sql
无唯一gold SQL
```

**既有实际最终状态/SQL**：`NEEDS_CLARIFICATION`。

```sql
没有实际SQL，按对应澄清/失败状态判断
```

**原参考结果**：`null`。

**既有实际结果**：`null`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": false, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**接口实际选项**：`[{"id": "value:issue-cef0fa76c70939e5:v-5abaeb142337ce5b27ed", "label": "Rock（genre.name）"}, {"id": "value:issue-cef0fa76c70939e5:v-10facd793602b59518e7", "label": "Rock And Roll（genre.name）"}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-09/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-09/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-10 · explicit_absent

**题目**：查询 genre 为 Vaporwave 的曲目数量；如果数据库里根本没有这个流派，请直接报告没有记录。

**原自动complete**：`False`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI发现错误。

**判断理由**：用户明确要求按Vaporwave字面查，无记录即报告，禁止替换附近流派。完整25流派无该值，按track→genre真实FK及名称等值COUNT返回0符合语义。实际没有替换Vaporwave，但三次关联策略拒绝，未执行也未给出真实计数回答。INNER JOIN交换左右表不改变本查询语义；仍不能把未执行候选当成功。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.genre g ON t.genre_id = g.genre_id WHERE g.name = 'Vaporwave';
```

**既有实际最终状态/SQL**：`FAILED`。

```sql
SELECT COUNT(*) AS track_count FROM "public"."genre" AS g JOIN "public"."track" AS t ON t."genre_id" = g."genre_id" WHERE g."name" = 'Vaporwave'
```

**原参考结果**：`{"columns": ["track_count"], "rows": [[0]], "table": [{"track_count": 0}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`null`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-10/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider/2149524392eb4bc7bd058c9ccd042941.json>)（SHA `cc4844df571dbbc9e6647caabb0124b2d1b51180b1aa53b2eecbf5aef22632e8`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider/99831a454eae4c509df631cdb642274e.json>)（SHA `e0da2346d71c68321cc90046b0fdc27ad7cf3a7bcaf5983db7384138a187ca71`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider/b54055942eeb484e9bb0844cec0761b2.json>)（SHA `5c334b9b57a30ff7a5c960987cf81d2d86f77af92b9503d13237b8bbb6c04a1d`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider/fed00224f20b4285adec985dbb28abcf.json>)（SHA `83fe7e546508bab6dac610986c37681610c064863f8685d385e4eb9a23aa7f93`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-11 · standard

**题目**：How many customers are from Canada?

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：客户国家Canada明确；COUNT(*)统计customer记录并等值country过滤，实际标准值exact binding、SQL和8行计数一致。别名count/customer_count只改变输出名称，无期间、排序、金额或NULL填值偏差。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Canada';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Canada'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[8]], "table": [{"customer_count": 8}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 8}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": false, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-11/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-11/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-11/turns/000/provider/9ab16fae47d14c13b9a74f4c3fefa863.json>)（SHA `5b6f1872f29fb54f7ac31c870d33483f73d857595a014712b03f6588cadb0f22`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-12 · standard

**题目**：What was the total invoice revenue for France in 2022?

**原自动complete**：`False`；**原可评分**：`True`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI建议有条件通过。

**判断理由**：英文total invoice revenue for France in 2022明确SUM(invoice.total)和2022半开年度，未明确France是账单国还是客户所在地。已确认general.region只区分两字段，无全局默认；参考billing SQL在该解释下逻辑正确，但直接L0唯一选择仍需确认。系统实际L2询问地区字段具有业务依据；controller没有这项补充，终止无SQL，不能仅凭固定direct标签认定误问，也不能称已完成回答。

**标准SQL（冻结，未改）**：

```sql
SELECT SUM(total) AS revenue FROM public.invoice WHERE billing_country = 'France' AND invoice_date >= DATE '2022-01-01' AND invoice_date < DATE '2023-01-01';
```

**既有实际最终状态/SQL**：`NEEDS_CLARIFICATION`。

```sql
没有实际SQL，按对应澄清/失败状态判断
```

**原参考结果**：`{"columns": ["revenue"], "rows": [["39.60"]], "table": [{"revenue": "39.60"}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`null`。

**接口实际选项**：`[{"id": "billing_country", "label": "按发票账单国家"}, {"id": "customer_country", "label": "按客户所在地国家"}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-12/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-12/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-12/turns/000/provider/72a25f23220748cbb91e141ad264637f.json>)（SHA `3623b427a56248b5a136096e9922007ffc998ce7d9098afbc27485039f189e79`）。

**人工待核**：
- 确认invoice+for国家是否有团队批准的默认地区口径，或应要求澄清

## sp01-13 · alias

**题目**：Iron Maiden乐队一共有多少张专辑？

**原自动complete**：`None`；**原可评分**：`False`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI建议通过。

**判断理由**：参考内容与实际查询均按已准Iron Maiden乐队别名、album→artist FK及名称等值计数；实际21、NLU绑定完整。与sp01-02原始题面完全重复，已有scorable=false是题库质量问题。AI可判断本次回答语义正确，但不能把重复题重新加入原评分分母或当新的独立覆盖。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS album_count FROM public.album al JOIN public.artist ar ON al.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE ar."name" = 'Iron Maiden'
```

**原参考结果**：`{"columns": ["album_count"], "rows": [[21]], "table": [{"album_count": 21}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"album_count": 21}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-13/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-13/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-13/turns/000/provider/a6a058f2bc73461a9a8fdef06f9ac656.json>)（SHA `6ed982f612a6450fd45a2293dd8cef030788c4347a1a8c8683f2278ebba597d9`）。

**人工待核**：
- 是否保留重复作一致性样本；不改当前不可评分标记

## sp01-14 · alias

**题目**：法兰西共和国的发票一共开了多少张？

**原自动complete**：`None`；**原可评分**：`False`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：证据不足。

**判断理由**：冻结材料允许customer.country或invoice.billing_country两种解释，却gold唯一选customer.country，题面法兰西共和国的发票没有给出客户居住地。已确认规则不合并两者。系统选择账单国并得到35，当前同值不能证明客户国参考正确，也不能证明系统错误；原标签已不可评分，等待明确口径。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS invoice_count FROM public.invoice i JOIN public.customer c ON i.customer_id = c.customer_id WHERE c.country = 'France';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) AS invoice_count FROM "public"."invoice" WHERE "billing_country" = 'France'
```

**原参考结果**：`{"columns": ["invoice_count"], "rows": [[35]], "table": [{"invoice_count": 35}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"invoice_count": 35}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-14/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-14/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-14/turns/000/provider/9c9281cb9bc44d009d6f9be2c5e56fa5.json>)（SHA `744a04b4127de402eb775575a1632be5c65c47cfe0c3772a4dd63855ab51f22e`）。

**人工待核**：
- 确认题面所需的地区字段或澄清策略

## sp01-15 · alias

**题目**：受保护AAC音频文件这种媒体格式有多少首曲目？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：受保护AAC音频文件在当前表为approved media_type.name别名，真实标准值Protected AAC audio file。track.media_type_id关联media_type唯一主键，每条曲目只计一次，COUNT237正确。实际binding字段/值、FK连接、改写与patch证据齐全，未混用相邻MPEG格式或把格式对象替成歌曲名称。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'Protected AAC audio file';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."track" AS t JOIN "public"."media_type" AS mt ON t."media_type_id" = mt."media_type_id" WHERE mt."name" = 'Protected AAC audio file'
```

**原参考结果**：`{"columns": ["track_count"], "rows": [[237]], "table": [{"track_count": 237}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 237}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": true, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**接口实际改写**：Protected AAC audio file这种媒体格式有多少首曲目？。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-15/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-15/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-15/turns/000/provider/4d72516207244dc69ad5308bf6c9d5c6.json>)（SHA `839c69697561eafae81c046cc1ff806bc07054f2cb72ee4fd0bf22710768974f`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-16 · alias

**题目**：U2乐队一共有多少张专辑？

**原自动complete**：`None`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：U2乐队别名已approved，真实artist=U2。参考COUNT(DISTINCT album_id)，实际COUNT(*)；album主键不可空且album→artist为多对一真实FK，没有JOIN明细或其他可重复来源，过滤/范围一致，所以等价。实际10相同是附加执行证据，不是等价证明本身。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(DISTINCT a.album_id) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'U2';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE ar."name" = 'U2'
```

**原参考结果**：`{"columns": ["album_count"], "rows": [[10]], "table": [{"album_count": 10}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"album_count": 10}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-16/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-16/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-16/turns/000/provider/47f0cecca8b946ae8d456a2ff2a3bfa9.json>)（SHA `4b01221e203b903b29b5ec4935a233102c69518ad4515a5c755ad1257579f69b`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-17 · typo

**题目**：Fracne 有多少客户？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI发现错误。

**判断理由**：参考Fracne→France后COUNT客户的SQL逻辑/真实值正确，恢复策略仍待人工。实际SQL和5计数正确，但NLU binding/intent.filters均空、rewritten_question=null，answer只说查询结果5。冻结目标要求顶部声明纠正，API没有提供改写/patch、UI的有条件渲染也无法展示本次改动。故不把查询自动通过当整个①受限纠错/声明链路通过；原数值和binding分数原样保留。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'France';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer" WHERE "country" = 'France'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[5]], "table": [{"customer_count": 5}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"customer_count": 5}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": false, "rewritten_question_available": false, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-17/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-17/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-17/turns/000/provider/250eecee78e8430e98884f783ab80d96.json>)（SHA `71ea35d56cf9930aa1fea4919cf87b318047418e0d0e4ef0ef995bee875a61a7`）。

**人工待核**：
- 核对拼写候选接受规则及声明展示要求；不据此改自动分数

## sp01-18 · typo

**题目**：Led Zepelin 有多少张专辑？

**原自动complete**：`False`；**原可评分**：`True`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI发现错误。

**判断理由**：参考恢复Led Zepelin→Led Zeppelin并按album→artist真实FK计数，已存原只读gold14；恢复接受规则仍需人工核对。实际最终只SELECT artist_id并保留错误拼写、返回空表，查询对象和COUNT专辑目标丢失，也未声明纠正，不能用EMPTY_RESULT当正确答案。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(DISTINCT a.album_id) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Led Zeppelin';
```

**既有实际最终状态/SQL**：`EMPTY_RESULT`。

```sql
SELECT "artist_id" FROM "public"."artist" WHERE LOWER("name") = LOWER('Led Zepelin') LIMIT 200
```

**原参考结果**：`{"columns": ["album_count"], "rows": [[14]], "table": [{"album_count": 14}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-18/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-18/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/d1ccb2b86f914827a044d7089bbb6be7.json>)（SHA `3a78db742d27a389f55e08656f6e3613fb04ccd70d0870675bc0c08c06768b50`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/d9599e21191f4877992421a19b4a5db9.json>)（SHA `aef7e45fe49df99a59fc2e8195177ceba8cbb04ed72ee3810ca41ac7ff8ae3a3`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/fd278ffb120f47809d78c1c0a0e61925.json>)（SHA `2cd64c3ad2307f66720fd9d66806aa71597da21e769932f0d189167dcce4502a`）。

**人工待核**：
- 确认拼写恢复策略，但当前对象/计数丢失有直接证据

## sp01-19 · typo

**题目**：Canda 的客户有多少？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI建议通过。

**判断理由**：Canda在客户语境恢复Canada，原国家事实及已准加拿大别名有依据，实际fuzzy受限候选绑定到customer.country Canada，SQL COUNT8准确。rewritten_question和patch真实存在；UI源码在answer之前显示原问题/改写后/修改依据，接口具备纠正声明信息。本题未单独运行浏览器或截图，展示能力只按源码与响应核对，不冒称本题UI实跑。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Canada';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Canada'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[8]], "table": [{"customer_count": 8}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 8}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": true, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**接口实际改写**：Canada 的客户有多少？。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-19/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-19/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-19/turns/000/provider/9f2a3bcb253249b2a28da28055302f48.json>)（SHA `c20f47ee6d11fcd2ba7695cc4f3ff65321a46cd955dcbeabeac8bee4fe893290`）。

**人工待核**：
- 确认拼写恢复的业务接受边界；若需界面逐题截图另执行独立开发验证

## sp01-20 · typo

**题目**：MPEG adiou file 有多少首曲目？

**原自动complete**：`False`；**原可评分**：`True`。

**参考AI判断**：AI建议有条件通过；**系统AI判断**：AI发现错误。

**判断理由**：参考MPEG adiou file恢复为MPEG audio file，经真实media_type主键关联COUNT曲目，原只读结果3034。实际最终IN子查询已使用正确格式名，track.media_type_id IN (SELECT唯一主键...)在此等同对应INNER JOIN计数；但被跨表限制拒绝，未执行，没有返回计数或声明纠正。不能只改报告让API失败通过。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'MPEG audio file';
```

**既有实际最终状态/SQL**：`FAILED`。

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" WHERE "media_type_id" IN (SELECT "media_type_id" FROM "public"."media_type" WHERE "name" = 'MPEG audio file')
```

**原参考结果**：`{"columns": ["track_count"], "rows": [[3034]], "table": [{"track_count": 3034}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`null`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-20/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-20/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-20/turns/000/provider/c0c11ce530d841ff9135588f32c7a288.json>)（SHA `4d8b13fd3b1786d787ac69a2ae2d26fbd6ae5b9124fd3d50fcfa8330cc1c1fde`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-20/turns/000/provider/ceec9200792f473981348fb15b16899f.json>)（SHA `69f471dcd5d07828e8e28bb62a0729a50de1545206328a2724bec881aedb6209`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-20/turns/000/provider/f3c134048942450ba9258153e0e4c2e2.json>)（SHA `367878107edfe8b041e300251b1edc548b0b28fe0bac34891f757138259d01e2`）。

**人工待核**：
- 确认该拼写恢复可接受；区别候选SQL等价与实际系统失败

## sp01-21 · pinyin

**题目**：Deguo 的客户有多少个？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：Deguo在客户对象范围对已准德国别名做拼音还原Germany，不将它塞进艺术家/专辑领域。实际method=pinyin，字段customer.country和值Germany正确，改写与patch存在；COUNT4，无任意日期、账单国或NULL补零。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Germany';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Germany'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[4]], "table": [{"customer_count": 4}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 4}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": true, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**接口实际改写**：Germany 的客户有多少个？。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-21/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-21/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-21/turns/000/provider/1977e18873cd434dba7fa187abdea799.json>)（SHA `3c595e47d9195baa4707c1a072a000e1095c3f790d65fda335f6f3d7054106fb`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-22 · pinyin

**题目**：Gudian 这个流派的曲目有多少首？

**原自动complete**：`False`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI发现错误。

**判断理由**：古典→Classical在当前别名表为approved，Gudian是其拼音；题面限定流派，参考track→genre按Classical计数，字段、对象、粒度正确。实际仍筛genre.name=Gudian，未还原拼音并被关联限制拒绝；无成功结果。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.genre g ON t.genre_id = g.genre_id WHERE g.name = 'Classical';
```

**既有实际最终状态/SQL**：`FAILED`。

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" AS t JOIN "public"."genre" AS g ON t."genre_id" = g."genre_id" WHERE g."name" = 'Gudian'
```

**原参考结果**：`{"columns": ["track_count"], "rows": [[74]], "table": [{"track_count": 74}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`null`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-22/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-22/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-22/turns/000/provider/38bbf1225b78404285afa5163e365db7.json>)（SHA `61569cad31d49458049074785def7705eb279382039cbed9d69e20649654f7f1`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-22/turns/000/provider/7b51d6cda1534d93b79709fa7df41780.json>)（SHA `b61fa40aa084631a86352ec090d4c1623dbc0c0d19ade1de1fb394e1b47cf1bb`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-22/turns/000/provider/f2330292cf9047fcbedd0830c507cc0b.json>)（SHA `5f168a21b43c9c443f6594e0c86018977ae6fbc6b2bae170734c0e23ccc21c6c`）。

**人工待核**：
- 人工可核对拼音大小写/分词接受边界

## sp01-23 · mixed_language

**题目**：Canada 那边一共有多少 customers？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：中英混合Canada/customers明确客户国家+计数对象，实际exact索引绑定和COUNT customer过滤Canada一致，返回8。查询为当前客户记录计数，无聚合金额/期间歧义，别名不改变结果语义。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Canada';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Canada'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[8]], "table": [{"customer_count": 8}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 8}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": false, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-23/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-23/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-23/turns/000/provider/d0c41fb267c94d73a7f7ebbc67227ec4.json>)（SHA `28e067c9b534e2725a000aaa1b1a4bcf790e85e3d533fbf201045f00c6c1cac5`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-24 · mixed_language

**题目**：Iron Maiden 这个 artist 有多少 albums？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：混合artist/albums明确艺术家专辑关系，Iron Maiden真实artist_id90。album→artist真实FK与唯一artist主键使COUNT(*)每专辑一次；实际exact标准值绑定、SQL和结果21符合题意。没有为获得非空结果增加客户/销售关系，表/列别名不影响业务粒度。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS album_count FROM public.album al JOIN public.artist ar ON al.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE ar."name" = 'Iron Maiden'
```

**原参考结果**：`{"columns": ["album_count"], "rows": [[21]], "table": [{"album_count": 21}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"album_count": 21}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": false, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-24/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-24/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-24/turns/000/provider/d7f0800114904f27bb9dadba7480276c.json>)（SHA `f091f39a45eb35e9f90db02cb302f2e16bfc17ee49611aa313dfed18b081772d`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-25 · colloquial

**题目**：意大利那边的发票总共开了多少钱？

**原自动complete**：`None`；**原可评分**：`True`。

**参考AI判断**：AI发现错误；**系统AI判断**：证据不足。

**判断理由**：题面意大利那边的发票总金额未明确地区字段；当前别名同时批准Italy映射customer.country及invoice.billing_country。参考expected_behavior声称已确认口径以客户居住地为准，但实际general.region/human_confirmation没有批准这种默认。gold在客户国解释下SQL逻辑可执行，不能证明该题唯一应选客户国。实际选择账单国同37.62不能证明两字段等价，按参考正式判分暂不能确定。

**标准SQL（冻结，未改）**：

```sql
SELECT SUM(i.total) AS revenue FROM public.invoice i JOIN public.customer c ON i.customer_id = c.customer_id WHERE c.country = 'Italy';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT SUM("total") AS total_invoice_amount FROM "public"."invoice" WHERE "billing_country" = 'Italy'
```

**原参考结果**：`{"columns": ["revenue"], "rows": [["37.62"]], "table": [{"revenue": "37.62"}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"total_invoice_amount": "37.62"}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-25/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-25/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-25/turns/000/provider/614447ac8b1849f3b013c0ecfeb0ee7e.json>)（SHA `3b199b0559cc0a60c5eba3f287c2c42240ae1eddb930d797c4cbc1ba0ccd796c`）。

**人工待核**：
- 核对参考声称的客户所在地默认依据；目前禁止自动补该默认

## sp01-26 · colloquial

**题目**：加拿大那边现在有多少客户？

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：加拿大那边现在有多少客户中对象customer明确，approved加拿大→Canada且当前快照8个客户。实际exact approved alias绑定、改写patch和SQL条件保留；不把现在解释为虚构客户创建年份或活动期间。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Canada';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) AS customer_count FROM "public"."customer" WHERE "country" = 'Canada'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[8]], "table": [{"customer_count": 8}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"customer_count": 8}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": true, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**接口实际改写**：Canada那边现在有多少客户？。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-26/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-26/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-26/turns/000/provider/5495a9e0f71342f6afff2ff54ffbefe6.json>)（SHA `eb25b983d318c50e7dbd26e926840d2416aa48c381c05b48d3cced6022001250`）。

**人工待核**：
- AI意见不代替人工验收；保持pending_human_review

## sp01-27 · multi_candidate

**题目**：Chinook 里摇滚曲目有多少首？

**原自动complete**：`False`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议通过。

**判断理由**：当前已准候选关系摇滚→Rock和Rock And Roll；两个均真实流派。实际L2列出两个同字段候选，未绑定任何一个、未执行SQL，符合请求的候选澄清行为。原scorer把expected的IN集合元组与retained的两个等值元组直接比subset，因此标false；这个观察是表示差异，不改冻结评分器/标签或原8失败数。

**标准SQL（冻结，未改）**：

```sql
无唯一gold SQL
```

**既有实际最终状态/SQL**：`NEEDS_CLARIFICATION`。

```sql
没有实际SQL，按对应澄清/失败状态判断
```

**原参考结果**：`null`。

**既有实际结果**：`null`。

**接口实际选项**：`[{"id": "value:issue-fbaa1127c30ea0e7:v-5abaeb142337ce5b27ed", "label": "Rock（genre.name）"}, {"id": "value:issue-fbaa1127c30ea0e7:v-10facd793602b59518e7", "label": "Rock And Roll（genre.name）"}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-27/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-27/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。

**人工待核**：
- 确认候选集合标准表示及下轮评分器版本；本轮只附独立AI意见

## sp01-28 · multi_candidate

**题目**：Chinook 里金属流派的曲目有多少首？

**原自动complete**：`None`；**原可评分**：`False`。

**参考AI判断**：AI发现错误；**系统AI判断**：AI建议有条件通过。

**判断理由**：题面明确金属流派，参考却把artist.name=Metallica列为候选；该金属艺术家别名实际pending，且artist候选与genre范围冲突，原scorable=false应保留。系统实际仅保留genre Metal的approved_candidate选项并追问，未绑定/执行，未使用禁用artist别名；这是符合范围及候选不得自动绑定的保守行为。是否还应提供Heavy Metal须人工确认对应候选关系，不能靠邻近值存在就批准。

**标准SQL（冻结，未改）**：

```sql
无唯一gold SQL
```

**既有实际最终状态/SQL**：`NEEDS_CLARIFICATION`。

```sql
没有实际SQL，按对应澄清/失败状态判断
```

**原参考结果**：`null`。

**既有实际结果**：`null`。

**接口实际选项**：`[{"id": "value:issue-e5d51e4bda1a9a15:v-bf1c51869eccaa9deddc", "label": "Metal（genre.name）"}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-28/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-28/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。

**人工待核**：
- 拒绝未经批准的Metallica artist候选；确认Heavy Metal是否有获准关系

## sp01-29 · explicit_absent

**题目**：查一下 customer.country='Atlantis' 的客户数量；如果数据库没有这个国家，就按这个字面值查，直接报告没有记录。

**原自动complete**：`True`；**原可评分**：`True`。

**参考AI判断**：AI建议通过；**系统AI判断**：AI建议有条件通过。

**判断理由**：用户显式指定customer.country Atlantis、即使不存在也按字面查。24个原只读国家值无Atlantis；实际SQL精确保留该值、没有替换相近国家，COUNT返回0正确。该聚合仍有一行，SUCCEEDED与空表/NULL有区别；未知值不产生成功实体索引绑定是合理边界。answer仅查询结果0，数值正确，但用户要求报告没有记录的文字说明尚未明确出现，展示措辞交人工确认。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Atlantis';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) FROM "public"."customer" WHERE "country" = 'Atlantis'
```

**原参考结果**：`{"columns": ["customer_count"], "rows": [[0]], "table": [{"customer_count": 0}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"count": 0}]`。

**分维度核对**：`{"SQL_or_initial_candidate_behavior_correct_under_reference": true, "explicit_binding_chain_correct": true, "rewritten_question_available": false, "whole_pipeline_not_inferred_from_automatic_result": true, "this_case_actual_browser_test": "未运行；仅核对已有响应与UI源码展示顺序"}`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-29/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-29/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [UI_renderer](<../../../../ui/app.py>)（render_result在改写后才展示answer，约第294–315行；仅源码核对）
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-29/turns/000/provider/55d06e093aa047cb967e903f242c683b.json>)（SHA `064bd45bd1af3a040e13165bb578920c7c223019b8d240ae200da04b10662329`）。

**人工待核**：
- 确认COUNT0文字是否足以满足报告没有记录要求，或应明确补一句；本轮不改代码

## sp01-30 · explicit_absent

**题目**：统计 invoice_date 在 2030-01-01 到 2030-12-31（左闭右开）之间的发票张数；如果那段时间没有发票，就按这个时间范围查询并报告没有记录。

**原自动complete**：`None`；**原可评分**：`True`。

**参考AI判断**：AI发现错误；**系统AI判断**：证据不足。

**判断理由**：用户明确写2030-01-01到2030-12-31（左闭右开），应按字面上界<2030-12-31；参考SQL、allowed_interpretations和两遍AI却扩展为<2031-01-01，两遍原AI意见漏读了题面。实际SQL也采用<2031-01-01，未保持用户明确上界；当前无2030数据所以两者COUNT均0，结果同值无力区分期间错误。DATE CAST与同一字面串在invoice_date timestamp without time zone比较可解释为同一午夜，但这只能说明实际与错误参考的类型差异，不证明用户期间正确。参考不可靠，正式系统分数暂不能确定，冻结原结果/标签不改。

**标准SQL（冻结，未改）**：

```sql
SELECT COUNT(*) AS invoice_count FROM public.invoice WHERE invoice_date >= DATE '2030-01-01' AND invoice_date < DATE '2031-01-01';
```

**既有实际最终状态/SQL**：`SUCCEEDED`。

```sql
SELECT COUNT(*) AS invoice_count FROM "public"."invoice" WHERE "invoice_date" >= '2030-01-01' AND "invoice_date" < '2031-01-01'
```

**原参考结果**：`{"columns": ["invoice_count"], "rows": [[0]], "table": [{"invoice_count": 0}], "row_count": 1, "truncated": false}`。

**既有实际结果**：`[{"invoice_count": 0}]`。

**证据**：
- [frozen_label](<../data/cases-v6-reviewed.jsonl>)
- [original_score](<../runtime_eval/runs/V0-001-scores.json>)
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-30/checkpoint.json>)
- [actual_raw_response](<../runtime_eval/runs/V0-001/cases/sp01-30/turns/000/response.raw.json>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [confirmed_business_rules](<../../../../data/rules/metric_definitions.json>)
- [actual_alias_table](<../../../../data/aliases/aliases-d2-reviewed.csv>)
- [此前独立16题原报告](v0-task01-semantic-review.json)（保留未覆盖）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-30/turns/000/provider/2640ac0e76d54cc3b817b63f45ccc6e7.json>)（SHA `80d534daae530fc7c1227b386dd67ce3cbcfdb8bed1391c36e91df9e86bdcf8e`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-30/turns/000/provider/4342a38189b741b383f7b75ca2c1d6bc.json>)（SHA `5864f23e141256ec9e27c2bdad7617baccb0bb247efa2b68589a60190019c74d`）。
- [匹配该trace的provider原始请求/返回](<../runtime_eval/runs/V0-001/cases/sp01-30/turns/000/provider/a205b131ddc7464592134b1dcd2679fe.json>)（SHA `d857f68f847f83e12cb1db2830e70cd4b6a60bd24117686a686b4310456dea3f`）。

**人工待核**：
- 优先确认用户原句是否本意整年，或必须保持12/31左闭右开；另存修订版只在人工决定后实施

## 审核边界

新增参考争议不会在本轮悄悄改变49/11冻结标签、语义评分器或原始自动统计。错误参考下的系统标准计分保留暂不能确定；同时直接指出能从用户原句/实际SQL独立观察的条件丢失。查询结果、受限实体绑定、声明展示、候选保留和UI实跑是分别审核的维度，不合成一个自动通过。

完整逐项原分数、实际输出、独立静态核验、证据SHA见 [机器报告](v0-task01-full-review.json)。所有条目仍pending_human_review，无人工签名或日期。
