# D3 AW 开发集 gold 第一遍 AI 预审（待人工复核）

保留9题只核验程序标签；这里不展开保留题。

## aw-01

AdventureWorks 数据库共有多少张销售订单？请统计订单头记录数。

AI建议通过；理由：销售而非采购；每张销售订单头是一条订单记录，不按明细计数。

```sql
SELECT COUNT(*) AS order_count FROM sales.salesorderheader
```

标准表：sales.salesorderheader

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-01.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-02

采购订单一共有多少张？按采购订单头计数。

AI建议通过；理由：采购订单头计数，与销售订单头同名近似对象区分。

```sql
SELECT COUNT(*) AS order_count FROM purchasing.purchaseorderheader
```

标准表：purchasing.purchaseorderheader

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-02.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-03

员工档案中共有多少名员工？包括 currentflag 为 false 的档案。

AI建议通过；理由：统计完整员工档案；用户明确不做在职过滤。

```sql
SELECT COUNT(*) AS employee_count FROM humanresources.employee
```

标准表：humanresources.employee

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-03.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-04

销售人员表中共有多少名销售人员？

AI建议通过；理由：销售人员只是员工的一部分；统计 salesperson。

```sql
SELECT COUNT(*) AS salesperson_count FROM sales.salesperson
```

标准表：sales.salesperson

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-04.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-05

产品目录中共有多少个产品？不要用产品型号数替代。

AI建议通过；理由：产品记录计数，型号表是干扰项。

```sql
SELECT COUNT(*) AS product_count FROM production.product
```

标准表：production.product

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-05.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-06

产品颜色有多少种？未填写颜色的不计入。

AI建议通过；理由：DISTINCT 颜色，NULL 排除，不将未填写视为一种颜色。

```sql
SELECT COUNT(DISTINCT color) AS color_count FROM production.product WHERE color IS NOT NULL
```

标准表：production.product

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-06.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-07

列出目录售价最高的五个产品，给出产品编号、名称和售价；同价时按产品编号从小到大。

AI建议通过；理由：现行目录售价 listprice；不是历史价格或 standardcost。

```sql
SELECT productid, name, listprice FROM production.product ORDER BY listprice DESC NULLS LAST, productid ASC LIMIT 5
```

标准表：production.product

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-07.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-08

每个产品大类下面有多少个产品？只统计已分到子类别的产品，输出大类名称和数量，按数量降序、名称升序。

AI建议通过；理由：必须经过子类别桥接；NULL 子类别产品按题意排除。

```sql
SELECT c.name AS category_name, COUNT(*) AS product_count FROM production.product AS p JOIN production.productsubcategory AS s ON p.productsubcategoryid = s.productsubcategoryid JOIN production.productcategory AS c ON s.productcategoryid = c.productcategoryid GROUP BY c.productcategoryid, c.name ORDER BY product_count DESC, c.name ASC LIMIT 200
```

标准表：production.product, production.productsubcategory, production.productcategory

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-08.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-09

供应商档案一共有多少条？不按客户或门店计数。

AI建议通过；理由：供应商实体在 purchasing.vendor，与客户门店分开。

```sql
SELECT COUNT(*) AS vendor_count FROM purchasing.vendor
```

标准表：purchasing.vendor

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-09.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-10

各员工职位有多少人？列人数最多的十个职位，按人数降序、职位名称升序。

AI建议通过；理由：jobtitle 是职位；部门名称不能替代职位。

```sql
SELECT jobtitle, COUNT(*) AS employee_count FROM humanresources.employee GROUP BY jobtitle ORDER BY employee_count DESC, jobtitle ASC LIMIT 10
```

标准表：humanresources.employee

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-10.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-11

2013 年销售订单头的 subtotal 合计是多少？仅算这个字段，不含 taxamt 和 freight。

AI建议通过；理由：完整2013自然年半开区间；明确 subtotal 而非 totaldue，币种不另行宣称。

```sql
SELECT SUM(subtotal) AS subtotal_sum FROM sales.salesorderheader WHERE orderdate >= CAST('2013-01-01' AS DATE) AND orderdate < CAST('2014-01-01' AS DATE)
```

标准表：sales.salesorderheader

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-11.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-12

2013 年采购订单头的 subtotal 合计是多少？不含税与运费。

AI建议通过；理由：采购头金额，避免明细 JOIN 重复累计。

```sql
SELECT SUM(subtotal) AS subtotal_sum FROM purchasing.purchaseorderheader WHERE orderdate >= CAST('2013-01-01' AS DATE) AND orderdate < CAST('2014-01-01' AS DATE)
```

标准表：purchasing.purchaseorderheader

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-12.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-13

地址档案里哪个城市的地址记录最多？列出前五名城市和记录数，按记录数降序、城市名升序。

AI建议通过；理由：按地址记录而不是人数/客户数；相同城市文字归为一组。

```sql
SELECT city, COUNT(*) AS address_count FROM person.address GROUP BY city ORDER BY address_count DESC, city ASC LIMIT 5
```

标准表：person.address

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-13.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-14

2013 年每个月有多少张销售订单？输出月份数字和订单数，按月份从小到大。

AI建议通过；理由：按订单日期自然月，固定2013范围，订单头数量。

```sql
SELECT CAST(EXTRACT(MONTH FROM orderdate) AS INT) AS month, COUNT(*) AS order_count FROM sales.salesorderheader WHERE orderdate >= CAST('2013-01-01' AS DATE) AND orderdate < CAST('2014-01-01' AS DATE) GROUP BY EXTRACT(MONTH FROM orderdate) ORDER BY month ASC LIMIT 200
```

标准表：sales.salesorderheader

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-14.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-15

销售原因字典里每个 reasontype 分别有多少条原因？按类型名称排序。

AI建议通过；理由：统计字典定义项数量，不统计订单使用原因次数。

```sql
SELECT reasontype, COUNT(*) AS reason_count FROM sales.salesreason GROUP BY reasontype ORDER BY reasontype ASC LIMIT 200
```

标准表：sales.salesreason

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-15.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-16

客户档案中 personid 非空的有多少条，storeid 非空的有多少条？两个条件分别计数，不要求互斥。

AI建议通过；理由：COUNT(列)排除NULL；不凭分类推断互斥或转换为人口数。

```sql
SELECT COUNT(personid) AS person_linked_count, COUNT(storeid) AS store_linked_count FROM sales.customer
```

标准表：sales.customer

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-16.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-17

汇总每个产品在所有库存地点的 quantity，列库存总量最高的五个产品编号、名称和数量；数量相同按编号升序。

AI建议通过；理由：所有库位 quantity 加总，非订单销量；同编号聚合。

```sql
SELECT p.productid, p.name, SUM(i.quantity) AS total_quantity FROM production.productinventory AS i JOIN production.product AS p ON i.productid = p.productid GROUP BY p.productid, p.name ORDER BY total_quantity DESC, p.productid ASC LIMIT 5
```

标准表：production.productinventory, production.product

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-17.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-18

2013 年各产品大类的销售购买数量分别是多少？按 salesorderdetail.orderqty 加总，只统计有子类别的产品，输出大类名和数量，按数量降序、名称升序。

AI建议通过；理由：销售明细数量、销售头日期、大类维度；产品→子类别→大类须真实外键桥接。

```sql
SELECT c.name AS category_name, SUM(d.orderqty) AS order_quantity FROM sales.salesorderdetail AS d JOIN sales.salesorderheader AS h ON d.salesorderid = h.salesorderid JOIN production.product AS p ON d.productid = p.productid JOIN production.productsubcategory AS s ON p.productsubcategoryid = s.productsubcategoryid JOIN production.productcategory AS c ON s.productcategoryid = c.productcategoryid WHERE h.orderdate >= CAST('2013-01-01' AS DATE) AND h.orderdate < CAST('2014-01-01' AS DATE) GROUP BY c.productcategoryid, c.name ORDER BY order_quantity DESC, c.name ASC LIMIT 200
```

标准表：sales.salesorderdetail, sales.salesorderheader, production.product, production.productsubcategory, production.productcategory

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-18.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-19

每种运输方式被多少张采购订单使用？输出运输方式名称和采购订单数，按订单数降序、名称升序。

AI建议通过；理由：题意采购订单；未使用方式不要求补0，运输方式FK链接。

```sql
SELECT s.name AS ship_method, COUNT(*) AS order_count FROM purchasing.purchaseorderheader AS h JOIN purchasing.shipmethod AS s ON h.shipmethodid = s.shipmethodid GROUP BY s.shipmethodid, s.name ORDER BY order_count DESC, s.name ASC LIMIT 200
```

标准表：purchasing.purchaseorderheader, purchasing.shipmethod

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-19.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-20

2013 年每个销售区域的销售订单 subtotal 合计是多少？不计 territoryid 为空的订单，输出区域名和合计，按金额降序、名称升序。

AI建议通过；理由：销售组织区域不是地址州省；明确排除未分配区域且只累加订单头。

```sql
SELECT t.name AS territory_name, SUM(h.subtotal) AS subtotal_sum FROM sales.salesorderheader AS h JOIN sales.salesterritory AS t ON h.territoryid = t.territoryid WHERE h.orderdate >= CAST('2013-01-01' AS DATE) AND h.orderdate < CAST('2014-01-01' AS DATE) GROUP BY t.territoryid, t.name ORDER BY subtotal_sum DESC NULLS LAST, t.name ASC LIMIT 200
```

标准表：sales.salesorderheader, sales.salesterritory

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-20.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。

## aw-21

currentflag 为 true 的员工中，各部门目前分配了多少人？以部门历史记录 enddate 为空表示目前分配，输出部门名和人数，按人数降序、部门名升序。

AI建议通过；理由：在职标志和当前部门分配是两个显式条件；部门内按员工编号去重。

```sql
SELECT d.name AS department_name, COUNT(DISTINCT e.businessentityid) AS employee_count FROM humanresources.employee AS e JOIN humanresources.employeedepartmenthistory AS h ON e.businessentityid = h.businessentityid JOIN humanresources.department AS d ON h.departmentid = d.departmentid WHERE e.currentflag = TRUE AND h.enddate IS NULL GROUP BY d.departmentid, d.name ORDER BY employee_count DESC, d.name ASC LIMIT 200
```

标准表：humanresources.employee, humanresources.employeedepartmenthistory, humanresources.department

证据：[实际只读结果](../../artifacts/d3/a/gold/dev/aw-21.json)

人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。
