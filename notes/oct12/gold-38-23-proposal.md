# sql-38、robust-23 新 gold 定稿提案

这两题都属于开发集。下面是具体提案，尚未替你签字，也没有修改任何现有题库、人工状态或历史分数。你需要确认的是题意和边界处理；SQL 跑出来与旧答案相同不能代替这个决定。

## sql-38：最大文件字节数的前三首

旧题：找出文件字节数最大的 3 首曲目，返回编号、名称和字节数；按字节数降序，并列按曲目编号升序。

旧 gold 使用 `ORDER BY bytes DESC, track_id ASC LIMIT 3`。`track.bytes` 在 schema 中允许 NULL。PostgreSQL 的降序排序默认把 NULL 放最前面；所以未知文件大小可能占据“最大”的名额，旧 SQL 的一般语义不完整。[PostgreSQL 16 排序与 NULL 规则](https://www.postgresql.org/docs/16/queries-order.html)

已有待审修正版增加 `NULLS LAST`。这能保证已知大小优先，但已知大小不足三首时，仍会用未知大小补到三首。定新 gold 时应先决定这些未知值是否参加排名。

建议采用 A：**只排名文件大小已知的曲目；不足三首时返回实际已知数量。** 题面建议定为：

> 找出文件大小已记录的曲目中，字节数最大的前 3 首，返回曲目编号、名称和字节数；按字节数降序，并列按曲目编号升序。文件大小未知的曲目不参与排名；符合条件不足 3 首时返回全部符合条件的曲目。

对应 gold：

```sql
SELECT track_id, name, bytes
FROM public.track
WHERE bytes IS NOT NULL
ORDER BY bytes DESC, track_id ASC
LIMIT 3;
```

这是业务边界说明，可以留在标签规范中；若想保持自然题面简短，用户题面只保留第一句，将“未知值不参加、不足三首不补齐”放进 `reference_semantics`。不需要在题面要求模型使用 `WHERE`、指定数据库字段名或暗示标准 SQL。

备选 B：保留当前 `NULLS LAST` gold，同时明确“未知大小放在已知大小之后；已知不足三首时可包含未知记录”。如果你的业务并不想给未知文件排出最大名次，不建议选择 B。**A 与 B 在当前历史快照结果相同，也仍是两个不同口径。**

本次恢复容器后，以 `qa_reader`、只读事务、5 秒超时真实重跑，三种 SQL 在当前快照下都得到：

| 顺序 | track_id | 名称 | bytes |
|---|---:|---|---:|
| 1 | 3224 | Through a Looking Glass | 1059546140 |
| 2 | 2820 | Occupation / Precipice | 1054423946 |
| 3 | 3236 | The Young Lords | 587051735 |

当前共 3503 条曲目，3503 个 bytes 都已知，NULL 数为 0。所以本次结果一致不能独立证明 NULL 边界规则正确。只读 `VALUES` 反例验证了默认降序把未知值放前面，以及不足三条已知值时 `NULLS LAST` 会补未知、`IS NOT NULL` 不补。原容器未启动导致首轮 13 条查询连接失败，失败记录见 [首轮只读验证](../../eval/artifacts/oct12/review-gold/readonly-verification.json)；原容器恢复后，新目录保存 [13/13 成功实测](../../eval/artifacts/oct12/review-gold/readonly-rerun/readonly-verification.json)，未覆盖失败记录。

## robust-23：明确“全部曲目”的范围

基题 `sql-10` 要求全部曲目的平均毫秒时长。旧鲁棒变体为“这批曲目的平均长度是几毫秒？”，但单条请求没有提供“这批”的集合或前文，不能直接假定它等于全库。旧 SQL 的数值正确不能证明它回答了这个有指代歧义的问题。

建议保留鲁棒题的原意，选择 A：**将范围说清楚，继续作为可直接执行的口语改写题。** 自然题面可用：

> 库里所有曲目的平均长度是多少毫秒？

现有待审修正版“全部曲目的平均长度是几毫秒？”也满足同一范围。对应 gold 无需换公式：

```sql
SELECT AVG(milliseconds) AS average_milliseconds
FROM public.track;
```

对象是每条曲目，逐曲目等权平均；单位是毫秒。不是按购买数量加权，不乘或除 1000，不因为存在视频曲目自行排除视频。PostgreSQL `AVG` 忽略 NULL 输入；没有非 NULL 输入时返回 NULL，而不是 0。[PostgreSQL 16 聚合函数](https://www.postgresql.org/docs/16/functions-aggregate.html)

本次真实结果为 `393599.212103910933` 毫秒；3503 个 milliseconds 均非 NULL，总和为 `1378778040` 毫秒，独立分子／分母与 AVG 一致。gold 保存完整数据库精度；页面可另做合理显示，不能把显示舍入值反写到原始结果。`VALUES` 查询另证实非空值等权、NULL 不计入分母、空集合结果为 NULL。

备选 B：保留“这批曲目”，将该题另立为“缺少集合范围、需要澄清”的题，gold 应是澄清行为与合法后续，不再使用唯一全库平均值标签。它会改变基题语义，不宜继续标为保持语义的 `colloquial` 鲁棒题。要这样做需新建版本、重新定类别、控制器和评分合同，不能单纯替换平均数让旧回答通过。

## 你具体如何确认

推荐你确认：“sql-38 采用已知文件大小排名，未知不参加、不足三首不补齐；robust-23 改为库里所有曲目的平均毫秒时长，按每条曲目等权平均。”确认后再以新版本保存题面、gold SQL、只读结果、列类型、单位、排序、NULL 行为和内容摘要；保留旧版本，重新跑这两道开发题，旧成绩不回填。

本提案的依据与证据：

- [原 AI 逐题审核](../../eval/reports/d2-ai-preaudit/sql-review.json)，`rows[id=sql-38]` 与 `rows[id=robust-23]`：原题、旧 gold、已有输出和问题理由。
- [D2 修订授权及两处待审变更](../../eval/artifacts/d2-final/review/user-attestation-and-revisions.json)，`changes`：授权原文与明确待审范围。
- [当前 sql-38 待审开发视图](../../eval/artifacts/d2-final/review/sql-dev-v1.jsonl)，第 29 行。
- [当前 robust-23 待审开发视图](../../eval/artifacts/d2-final/review/robust-dev-v1.jsonl)，第 16 行。
- [历史 56 条标准 SELECT 实跑](../../eval/artifacts/d2-final/review/gold-readonly-results.jsonl)，按 `id` 查两题；[Chinook schema](../../data/catalog/chinook.yaml)，`tables.track.columns`。
- [本次只读验证源码](../../scripts/verify_oct12_gold.py)与 [成功重跑的 13 条查询](../../eval/artifacts/oct12/review-gold/readonly-rerun/queries.sql)：仅 SELECT、只读事务、原有 5 秒超时，模型请求 0、保留题预测 0。

人工决定：**待你确认**。A/B 签名、人工确认日期均未填写。
