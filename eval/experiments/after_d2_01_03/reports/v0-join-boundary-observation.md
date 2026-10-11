# V0 三道已完成开发题：关联边界独立观察

本次只读审查既有响应、provider原文件、冻结gold、真实目录及原只读事实；没有调用API、模型或数据库，也没有改动代码、提示词、题库或人工记录。V0整轮当时尚在进行，本文件不是完整V0成绩。

三题共9次SQL生成均实际`allow_joins=false`，三次候选各自被跨表限制拦截，SQL执行次数为0。原runner自动provider归档为0，本次从响应明确记录的同trace原始provider路径核验9条SQL调用；补充归档由主流程另保存，不覆盖原rejected记录。

|编号|参考SQL候选判断|实际系统|关联关系|
|---|---|---|
|sp01-05|AI建议有条件通过，人工pending|FAILED／执行前被拒|album → artist|
|sp01-07|AI建议通过，人工pending|FAILED／执行前被拒|track → media_type|
|sp01-10|AI建议通过，人工pending|FAILED／执行前被拒|track → genre|

## sp01-05

**用户问题**：Metallcia 有多少张专辑？

**独立判断**：专辑表只有artist_id，名称在artist.name；按真实PK/FK关联再COUNT专辑不会因该维度连接重复计数。当前实体识别没有产出Metallica绑定，模型三次仍过滤Metallcia，所以即使放行关联也不足以证明修复该题。参考拼写恢复仍按冻结标签、程序和两遍AI候选依据，人工未签字。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Metallica';
```

**实际SQL与guard**：

1. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE ar."name" = 'Metallcia'
```

2. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE LOWER(ar."name") = LOWER('Metallcia')
```

3. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) AS album_count FROM "public"."album" AS a JOIN "public"."artist" AS ar ON a."artist_id" = ar."artist_id" WHERE LOWER(ar."name") = LOWER('Metallcia')
```

3次guard均为：`该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。`。未进入SQL执行，实际table为null。

**建议**：V0整轮结束后以通用真实目录/业务关系推导关联需求；局部修复需单独版本、两遍审读及原D2回归，不按这些case编号硬编码，也不改冻结gold。拼写漏识别与关联模式判断分别追踪。

**证据**：
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-05/checkpoint.json>)
- [raw_response](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/response.raw.json>)
- [original_provider_evidence](<../runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider-evidence.json>)
- [frozen_labels](<../data/cases-v6-reviewed.jsonl>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [source_facts](<../materials/readonly_live_facts.json>)

## sp01-07

**用户问题**：Chinook 里 Protected AAC audio file 这种 format 有多少首曲目？

**独立判断**：用户明确查询Protected AAC audio file格式的曲目数量；track存media_type_id而名称在media_type.name。5条原只读媒体记录给出唯一实际ID=2；gold按真实FK关联、名称等值、COUNT曲目，字段/对象一致。三次候选SQL保持该值和FK，不新增期间或聚合口径；当前在执行前被跨表策略拦截，不能把未执行SQL记为正确回答。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'Protected AAC audio file';
```

**实际SQL与guard**：

1. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) FROM "public"."track" t JOIN "public"."media_type" mt ON mt."media_type_id" = t."media_type_id" WHERE mt."name" = 'Protected AAC audio file'
```

2. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) AS track_count FROM "public"."media_type" AS mt JOIN "public"."track" AS t ON t."media_type_id" = mt."media_type_id" WHERE mt."name" = 'Protected AAC audio file'
```

3. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" AS t JOIN "public"."media_type" AS mt ON t."media_type_id" = mt."media_type_id" WHERE mt."name" = 'Protected AAC audio file'
```

3次guard均为：`该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。`。未进入SQL执行，实际table为null。

**建议**：V0整轮结束后以通用真实目录/业务关系推导关联需求；局部修复需单独版本、两遍审读及原D2回归，不按这些case编号硬编码，也不改冻结gold。拼写漏识别与关联模式判断分别追踪。

**证据**：
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-07/checkpoint.json>)
- [raw_response](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/response.raw.json>)
- [original_provider_evidence](<../runtime_eval/runs/V0-001/cases/sp01-07/turns/000/provider-evidence.json>)
- [frozen_labels](<../data/cases-v6-reviewed.jsonl>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [source_facts](<../materials/readonly_live_facts.json>)

## sp01-10

**用户问题**：查询 genre 为 Vaporwave 的曲目数量；如果数据库里根本没有这个流派，请直接报告没有记录。

**独立判断**：用户明确按不存在的Vaporwave字面查、无记录即报告，不允许替换相近流派；完整25个genre原只读值没有Vaporwave。track.genre_id与genre的真实主键关联后按名称精确COUNT应保留零结果。当前实体状态unmatched且无绑定，候选SQL没有偷换成附近流派，但三次在执行前被关联策略拦截。

**冻结参考SQL**：

```sql
SELECT COUNT(*) AS track_count FROM public.track t JOIN public.genre g ON t.genre_id = g.genre_id WHERE g.name = 'Vaporwave';
```

**实际SQL与guard**：

1. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" t JOIN "public"."genre" g ON t."genre_id" = g."genre_id" WHERE g."name" = 'Vaporwave'
```

2. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) AS track_count FROM "public"."track" AS t JOIN "public"."genre" AS g ON t."genre_id" = g."genre_id" WHERE g."name" = 'Vaporwave'
```

3. 实际单表system共1359字符，trace匹配；SQL为：

```sql
SELECT COUNT(*) AS track_count FROM "public"."genre" AS g JOIN "public"."track" AS t ON t."genre_id" = g."genre_id" WHERE g."name" = 'Vaporwave'
```

3次guard均为：`该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。`。未进入SQL执行，实际table为null。

**建议**：V0整轮结束后以通用真实目录/业务关系推导关联需求；局部修复需单独版本、两遍审读及原D2回归，不按这些case编号硬编码，也不改冻结gold。拼写漏识别与关联模式判断分别追踪。

**证据**：
- [checkpoint](<../runtime_eval/runs/V0-001/cases/sp01-10/checkpoint.json>)
- [raw_response](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/response.raw.json>)
- [original_provider_evidence](<../runtime_eval/runs/V0-001/cases/sp01-10/turns/000/provider-evidence.json>)
- [frozen_labels](<../data/cases-v6-reviewed.jsonl>)
- [catalog](<../../../../data/catalog/chinook.yaml>)
- [source_facts](<../materials/readonly_live_facts.json>)

## 源码与隔离边界

`qa_agent/pipeline.py:197`关联模式由数据库、ranking/growth/ratio、多个绑定、特定地区发票请求和艺术家/流派/格式的成功绑定触发。三题均为Chinook lookup、无成功绑定，故条件值为false。此边界没有根据原问题的对象/名称维度实际关系独立判定；当实体漏识别或明确不存在时，就把业务必要关系一起关闭。

不能一概放开任意多表；也不能用常量0或擅自补真实ID绕过字段/来源验证。后续若选择修复，必须用通用目录和真实FK判断，并保留绑定、来源、安全只读和超时守卫。

完整原始路径、SHA、actual source与V0快照一致性及每次provider SQL见 [机器记录](v0-join-boundary-observation.json)。所有AI意见仍待人工核对。
