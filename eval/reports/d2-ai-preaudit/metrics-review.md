# D2四项已确认口径AI依据核验

仅依据核验，不再审批既有口径，不扩大用户确认到题库gold或别名；actual不适用

既有用户确认：A、B已共同核对同意四项口径。AI核验只保留该原记录，不能代替/扩大人工确认到题库答案或别名。所有金额使用数据库金额单位，没有推断币种。

|指标|参考建议|实际|2024年只读示例|
|---|---|---|---|
|发票销售额|AI建议通过|不适用（已确认口径依据）|[["477.53"]]|
|平均每张发票金额|AI建议通过|不适用（已确认口径依据）|[["5.75"]]|
|期间内复购客户数|AI建议通过|不适用（已确认口径依据）|[[27]]|
|热门曲目|AI建议通过|不适用（已确认口径依据）|[[3, 1], [9, 1], [15, 1], [21, 1], [30, 1]]|

## metric:sales_revenue

发票销售额在invoice粒度SUM(total)，期间依据invoice_date半开范围，示例2024年返回477.53。按曲目/艺术家另用invoice_line.unit_price*quantity，不能明细JOIN后重复SUM发票总额；全库发票与明细对账均2328.60、差0.00。空期间SUM为NULL，不能无声改0。金额仅数据库金额单位，源数据未声明币种或支付状态。

本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。

保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。

证据：
- `data/rules/metric_definitions.json`，metrics.sales_revenue; general; sql_examples.revenue_invoice：
- `eval/artifacts/d2/source/metric-human-review.json`，method; statement; scope; proposal_sha256; reviewed_at_utc：原既有人工共同确认记录，仅核实留存、不代填新审批
- `eval/artifacts/d2/source/metric-sql-checks.json`，records.id=revenue_invoice：既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第114行：本次只读重执行既有SQL示例
- `data/catalog/chinook.yaml`，invoice; invoice_line; track; invoice_date_range：
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; invoice_dates; identity; privileges：
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第125行：empty-amount-semantics
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第118行：发票与明细金额对账

## metric:average_invoice_amount

平均每张发票金额为AVG(invoice.total)，示例先平均再保留两位得到2024年5.75；平均每位购买客户金额SUM(total)/COUNT(DISTINCT customer_id)是另一个指标。空期间AVG为NULL。已确认的短标签提案“客单价”不应使未指明对象的其他问题自动获得默认口径，runtime_defaults_enabled仍false。

本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。

保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。

证据：
- `data/rules/metric_definitions.json`，metrics.average_invoice_amount; general; sql_examples.average_invoice：
- `eval/artifacts/d2/source/metric-human-review.json`，method; statement; scope; proposal_sha256; reviewed_at_utc：原既有人工共同确认记录，仅核实留存、不代填新审批
- `eval/artifacts/d2/source/metric-sql-checks.json`，records.id=average_invoice：既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第115行：本次只读重执行既有SQL示例
- `data/catalog/chinook.yaml`，invoice; invoice_line; track; invoice_date_range：
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; invoice_dates; identity; privileges：
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第125行：empty-amount-semantics

## metric:repeat_customer_count

期间内复购客户数先将明确期间[2024-01-01,2025-01-01)的invoice按customer_id分组，HAVING COUNT(*)>=2，再计合格客户数，示例27位并有逐客户明细支持；不是发票条数、客户历史跨期次数或付款成功次数。没有合格客户时COUNT返回0，缺少期间不能自动填年。

本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。

保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。

证据：
- `data/rules/metric_definitions.json`，metrics.repeat_customer_count; general; sql_examples.repeat_customers：
- `eval/artifacts/d2/source/metric-human-review.json`，method; statement; scope; proposal_sha256; reviewed_at_utc：原既有人工共同确认记录，仅核实留存、不代填新审批
- `eval/artifacts/d2/source/metric-sql-checks.json`，records.id=repeat_customers：既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第116行：本次只读重执行既有SQL示例
- `data/catalog/chinook.yaml`，invoice; invoice_line; track; invoice_date_range：
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; invoice_dates; identity; privileges：
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第127行：repeat-customer-check

## metric:popular_tracks

明确期间内热门曲目按SUM(invoice_line.quantity)的实际购买数量，关联invoice_date过滤；不是目录单价、金额或播放列表成员数。数量降序后track_id升序作并列规则，再LIMIT 5；2024年示例3/9/15/21/30均购买1，补充前10行也并列1，稳定次排序必要。客户“谁买得最多”的金额口径与曲目热门不同，主语省略且无期间的问题仍需澄清。

本行是四项已确认业务口径的依据核验，actual原本null；本次仅重执行既有口径示例SELECT，未产生问答系统新预测。

保留既有四项确认记录；执行该口径时仍明确对象、期间、字段和单位，不把确认范围扩大到题库gold或别名。

证据：
- `data/rules/metric_definitions.json`，metrics.popular_tracks; general; sql_examples.popular_tracks：
- `eval/artifacts/d2/source/metric-human-review.json`，method; statement; scope; proposal_sha256; reviewed_at_utc：原既有人工共同确认记录，仅核实留存、不代填新审批
- `eval/artifacts/d2/source/metric-sql-checks.json`，records.id=popular_tracks：既有只读例SQL材料；其早期pending状态早于单独共同确认记录，不视为撤销确认
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第117行：本次只读重执行既有SQL示例
- `data/catalog/chinook.yaml`，invoice; invoice_line; track; invoice_date_range：
- `eval/artifacts/d2-ai-preaudit/database-materials.json`，schema; invoice_dates; identity; privileges：
- `eval/artifacts/d2-ai-preaudit/sql-verification.jsonl`，第128行：popular-quantity-ties
