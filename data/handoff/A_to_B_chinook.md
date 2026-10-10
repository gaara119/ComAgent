# A → B：Chinook 实际查询交接

取数时间（UTC）：2026-10-10T11:26:05.641940+00:00

数据源：官方 Chinook 1.4.5；本文件由只读账号执行实际 SQL 产生，供后续文档选材。

销售额口径：汇总发票明细的单价 × 数量，覆盖全部已导入年份；原数据未声明币种，金额不擅自标注币种。

| 排名 | artist_id | 艺术家英文名 | 销售额 |
|---|---|---|---|
| 1 | 90 | Iron Maiden | 138.60 |
| 2 | 150 | U2 | 105.93 |
| 3 | 50 | Metallica | 90.09 |
| 4 | 22 | Led Zeppelin | 86.13 |
| 5 | 149 | Lost | 81.59 |
| 6 | 156 | The Office | 49.75 |
| 7 | 113 | Os Paralamas Do Sucesso | 44.55 |
| 8 | 58 | Deep Purple | 43.56 |
| 9 | 82 | Faith No More | 41.58 |
| 10 | 81 | Eric Clapton | 39.60 |

```sql
SELECT ar.artist_id, ar.name,
       SUM(il.unit_price * il.quantity) AS revenue
FROM public.invoice_line il
JOIN public.track t ON il.track_id = t.track_id
JOIN public.album al ON t.album_id = al.album_id
JOIN public.artist ar ON al.artist_id = ar.artist_id
GROUP BY ar.artist_id, ar.name
ORDER BY revenue DESC, ar.artist_id ASC
LIMIT 10;
```

客户国家与账单国家分别是不同业务字段，不能互换。

非空国家不同的发票数：0；包括 NULL 的不同数：0；含 NULL 国家数：0。

```sql
SELECT
  COUNT(*) FILTER (WHERE i.billing_country <> c.country) AS non_null_difference_count,
  COUNT(*) FILTER (WHERE i.billing_country IS DISTINCT FROM c.country) AS null_aware_difference_count,
  COUNT(*) FILTER (WHERE i.billing_country IS NULL OR c.country IS NULL) AS rows_with_null_country,
  COUNT(*) AS compared_invoice_count
FROM public.invoice i
JOIN public.customer c USING (customer_id);
```

发票实际日期范围：2021-01-01T00:00:00 至 2025-12-22T00:00:00。

本次原始数据如果差异为 0，不能据此声称演示已展示两种地区口径的数值差异；后续可解释字段含义或使用单独标明的补充数据。

来源、原始文件 SHA256 与 MIT 许可证见 data/db/source_manifest.json 和 data/db/LICENSE.md。
