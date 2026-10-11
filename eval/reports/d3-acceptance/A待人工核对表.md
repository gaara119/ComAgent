# D3 A 待人工核对表

人工状态均为pending_human_review；没有A/B签名和人工确认日期。先集中处理目录5个表说明有条件、19个列说明有条件和1个列证据不足，再核对21道开发题gold。目录其它63表/436列通过两遍AI检查，可按方案抽查，AI不代替签字。

这里不展开9道保留题内容，不运行它们的模型预测，也不把保留标签传给调参任务。

证据均使用项目内相对路径。对应目录第二遍完整报告：[catalog-pass2](../d3-ai-review/catalog-pass2.md)。

## AW-CAT-T-person.person

AW中文目录表说明；AI建议有条件通过。

目标：person.person

现有说明：AdventureWorks 人员表，存储个人（如客户、员工等）的姓名、称谓、联系方式及人口统计等相关信息，每行对应一个人员实体，主键为 businessentityid。

AI依据：表与列结构基本一致，但部分枚举业务含义缺少字典证据。

人工需要检查：核对用途/粒度与事实依据，未知枚举/币种不补造；可以批准基础说明并保留限制。

人工状态：pending_human_review。

## AW-CAT-C-person.person.persontype

AW中文目录列说明；AI建议有条件通过。

目标：person.person.persontype

现有说明：人员类型代码，示例值包括 EM、GC、IN，用于区分该人员的业务角色类别。

实际类型：character(2)；可空：False。

AI依据：char(2)非空且样例EM等，但枚举含义未提供证据。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-person.person.namestyle

AW中文目录列说明；AI建议有条件通过。

目标：person.person.namestyle

现有说明：布尔标志，表示姓名的显示/称谓样式偏好。

实际类型：boolean；可空：False。

AI依据：boolean非空，说明称显示样式偏好，但true/false含义未证实。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-person.person.emailpromotion

AW中文目录列说明；AI建议有条件通过。

目标：person.person.emailpromotion

现有说明：整数标志，表示人员对电子邮件促销的偏好取值。

实际类型：integer；可空：False。

AI依据：integer非空样例0,1,2，但枚举促销偏好含义未证实。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-T-production.document

AW中文目录表说明；AI建议有条件通过。

目标：production.document

现有说明：该表存储 AdventureWorks 虚构自行车业务中与产品相关的文档元数据及内容，例如装配说明、曲柄臂与轮胎维护指南等。每行代表一份文档或文档文件夹节点，owner 指向负责该文档的员工（humanresources.employee），documentnode 以路径形式表示文档在层级结构中的位置，并作为主键唯一标识该节点。

AI依据：列结构与主外键同实时一致，但文档层级路径等业务语义仅部分由结构支持。

人工需要检查：核对用途/粒度与事实依据，未知枚举/币种不补造；可以批准基础说明并保留限制。

人工状态：pending_human_review。

## AW-CAT-C-production.document.status

AW中文目录列说明；证据不足。

目标：production.document.status

现有说明：文档的状态标识，为 smallint 类型；由于缺少字典证据，无法确定其具体枚举含义。

实际类型：smallint；可空：False。

AI依据：smallint非空但无字典证据，说明未定义状态枚举，无法批准业务解释。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-production.document.documentnode

AW中文目录列说明；AI建议有条件通过。

目标：production.document.documentnode

现有说明：文档在层级结构中的节点路径（如 /、/1/、/1/1/），作为主键唯一标识该文档节点。

实际类型：character varying；可空：False。

AI依据：varchar主键与样例路径一致，但层级结构语义缺少完整证据。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-T-production.transactionhistoryarchive

AW中文目录表说明；AI建议有条件通过。

目标：production.transactionhistoryarchive

现有说明：AdventureWorks 自行车业务中的生产交易历史归档表，用于留存产品库存或成本交易的归档记录。该表与生产交易明细结构一致，但存放历史归档数据，不代表当前有效的交易记录。每行记录一次产品级交易，包含交易类型、数量、实际成本和关联的订单行信息。

AI依据：结构与主键相符，归档语义已注明；transacttype枚举与币种缺证据。

人工需要检查：核对用途/粒度与事实依据，未知枚举/币种不补造；可以批准基础说明并保留限制。

人工状态：pending_human_review。

## AW-CAT-C-production.transactionhistoryarchive.transactiontype

AW中文目录列说明；AI建议有条件通过。

目标：production.transactionhistoryarchive.transactiontype

现有说明：单字符交易类型标志，示例值包括 P、S、W；其具体枚举含义需参考源系统定义。

实际类型：character(1)；可空：False。

AI依据：bpchar(1)非空，P/S/W枚举含义未证实，已注明需参考源系统。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-production.transactionhistoryarchive.actualcost

AW中文目录列说明；AI建议有条件通过。

目标：production.transactionhistoryarchive.actualcost

现有说明：该次交易的实际成本金额，不是销售价格。

实际类型：numeric；可空：False。

AI依据：numeric非空，说明非销售价；币种未证实但已注明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-production.workorderrouting.actualresourcehrs

AW中文目录列说明；AI建议有条件通过。

目标：production.workorderrouting.actualresourcehrs

现有说明：实际资源工时，表示该工序实际消耗的资源小时数，可为空。

实际类型：numeric(9,4)；可空：True。

AI依据：numeric(9,4)可空，单位小时未证实，已列限制。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-production.workorderrouting.plannedcost

AW中文目录列说明；AI建议有条件通过。

目标：production.workorderrouting.plannedcost

现有说明：计划成本，表示该工单工序按计划计算的生产成本金额。

实际类型：numeric；可空：False。

AI依据：numeric非空，计划成本为金额，币种未说明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-production.workorderrouting.actualcost

AW中文目录列说明；AI建议有条件通过。

目标：production.workorderrouting.actualcost

现有说明：实际成本，表示该工单工序实际发生的生产成本金额，可为空。

实际类型：numeric；可空：True。

AI依据：numeric可空，实际成本为金额，币种未说明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.productvendor.averageleadtime

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.productvendor.averageleadtime

现有说明：该供应商供应此产品的平均交货提前期天数。

实际类型：integer；可空：False。

AI依据：integer非空，按天说明未由字典证实，已列限制。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.productvendor.standardprice

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.productvendor.standardprice

现有说明：该供应商针对此产品的标准采购单价（成本口径），区别于销售价格。

实际类型：numeric；可空：False。

AI依据：numeric非空，成本口径合理；币种未说明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.productvendor.lastreceiptcost

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.productvendor.lastreceiptcost

现有说明：最近一次收货时该产品的实际单位成本，可为空表示尚无收货记录。

实际类型：numeric；可空：True。

AI依据：numeric可空，最近收货成本；币种未说明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.purchaseorderdetail.unitprice

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.purchaseorderdetail.unitprice

现有说明：该明细行产品的单价（采购单位价格），为数值类型。

实际类型：numeric；可空：False。

AI依据：numeric非空，采购单价合理；币种未说明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-T-purchasing.purchaseorderheader

AW中文目录表说明；AI建议有条件通过。

目标：purchasing.purchaseorderheader

现有说明：采购订单头表，记录向供应商采购商品时每笔采购订单的汇总信息，包括负责采购的员工、供应商、发货方式、下单与发货日期以及订单级金额（小计、税额、运费）。与销售订单不同，此表用于采购业务。

AI依据：采购订单头结构与PK/FK一致；status枚举缺证据。

人工需要检查：核对用途/粒度与事实依据，未知枚举/币种不补造；可以批准基础说明并保留限制。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.purchaseorderheader.status

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.purchaseorderheader.status

现有说明：采购订单当前处理状态的代码，示例值 1、2、3。

实际类型：smallint；可空：False。

AI依据：smallint非空，状态代码合理但枚举未证实。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.purchaseorderheader.subtotal

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.purchaseorderheader.subtotal

现有说明：采购订单的小计金额，为订单明细金额汇总，不包含税额与运费。

实际类型：numeric；可空：False。

AI依据：numeric非空，小计口径合理；币种未说明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.purchaseorderheader.taxamt

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.purchaseorderheader.taxamt

现有说明：采购订单的税额。

实际类型：numeric；可空：False。

AI依据：numeric非空，税额合理；币种未说明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.purchaseorderheader.freight

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.purchaseorderheader.freight

现有说明：采购订单的运费。

实际类型：numeric；可空：False。

AI依据：numeric非空，运费合理；币种未说明。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-T-purchasing.shipmethod

AW中文目录表说明；AI建议有条件通过。

目标：purchasing.shipmethod

现有说明：采购模块下的运输方式参考表，记录可用的运输方式及其基础运费与费率信息，供采购订单等单据选择运输方式时引用。

AI依据：运输方式表结构与主键一致；运费费率口径缺证据。

人工需要检查：核对用途/粒度与事实依据，未知枚举/币种不补造；可以批准基础说明并保留限制。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.shipmethod.shipbase

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.shipmethod.shipbase

现有说明：该运输方式的基础运费金额，数值型，示例值如3.9500、8.9900、9.9500。

实际类型：numeric；可空：False。

AI依据：numeric非空，基础运费合理；币种及计算方式未证实。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## AW-CAT-C-purchasing.shipmethod.shiprate

AW中文目录列说明；AI建议有条件通过。

目标：purchasing.shipmethod.shiprate

现有说明：该运输方式的费率数值，数值型，示例值如0.9900、1.2900、1.4900。

实际类型：numeric；可空：False。

AI依据：numeric非空，费率合理；含税及口径未证实。

人工需要检查：核对单位、枚举、解释范围；缺少证明时保留未知，不因SQL能执行就批准具体含义。

人工状态：pending_human_review。

## aw-01

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

AdventureWorks 数据库共有多少张销售订单？请统计订单头记录数。

标准表：sales.salesorderheader

```sql
SELECT COUNT(*) AS order_count FROM sales.salesorderheader
```

```json
{
  "columns": [
    "order_count"
  ],
  "rows": [
    [
      31465
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-01.json)

AI依据：销售而非采购；每张销售订单头是一条订单记录，不按明细计数。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-02

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

采购订单一共有多少张？按采购订单头计数。

标准表：purchasing.purchaseorderheader

```sql
SELECT COUNT(*) AS order_count FROM purchasing.purchaseorderheader
```

```json
{
  "columns": [
    "order_count"
  ],
  "rows": [
    [
      4012
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-02.json)

AI依据：采购订单头计数，与销售订单头同名近似对象区分。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-03

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

员工档案中共有多少名员工？包括 currentflag 为 false 的档案。

标准表：humanresources.employee

```sql
SELECT COUNT(*) AS employee_count FROM humanresources.employee
```

```json
{
  "columns": [
    "employee_count"
  ],
  "rows": [
    [
      290
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-03.json)

AI依据：统计完整员工档案；用户明确不做在职过滤。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-04

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

销售人员表中共有多少名销售人员？

标准表：sales.salesperson

```sql
SELECT COUNT(*) AS salesperson_count FROM sales.salesperson
```

```json
{
  "columns": [
    "salesperson_count"
  ],
  "rows": [
    [
      17
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-04.json)

AI依据：销售人员只是员工的一部分；统计 salesperson。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-05

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

产品目录中共有多少个产品？不要用产品型号数替代。

标准表：production.product

```sql
SELECT COUNT(*) AS product_count FROM production.product
```

```json
{
  "columns": [
    "product_count"
  ],
  "rows": [
    [
      504
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-05.json)

AI依据：产品记录计数，型号表是干扰项。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-06

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

产品颜色有多少种？未填写颜色的不计入。

标准表：production.product

```sql
SELECT COUNT(DISTINCT color) AS color_count FROM production.product WHERE color IS NOT NULL
```

```json
{
  "columns": [
    "color_count"
  ],
  "rows": [
    [
      9
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-06.json)

AI依据：DISTINCT 颜色，NULL 排除，不将未填写视为一种颜色。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-07

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

列出目录售价最高的五个产品，给出产品编号、名称和售价；同价时按产品编号从小到大。

标准表：production.product

```sql
SELECT productid, name, listprice FROM production.product ORDER BY listprice DESC NULLS LAST, productid ASC LIMIT 5
```

```json
{
  "columns": [
    "productid",
    "name",
    "listprice"
  ],
  "rows": [
    [
      749,
      "Road-150 Red, 62",
      "3578.2700"
    ],
    [
      750,
      "Road-150 Red, 44",
      "3578.2700"
    ],
    [
      751,
      "Road-150 Red, 48",
      "3578.2700"
    ],
    [
      752,
      "Road-150 Red, 52",
      "3578.2700"
    ],
    [
      753,
      "Road-150 Red, 56",
      "3578.2700"
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-07.json)

AI依据：现行目录售价 listprice；不是历史价格或 standardcost。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。


**run2新增AI观察**：AI建议有条件通过；以上原两遍通过意见漏检了编号字段歧义。产品编号在实际目录中可能指productid主键，也可能指productnumber业务编号。原gold选productid，run2真实回答选productnumber并按该列处理同价顺序。两种字段在本题结果并不相同；题面没有明确字段，因此严格EX保留不匹配，但不能据此直接断言系统业务答案错误。

人工请优先明确productid/productnumber及同价排序；原gold与raw均未修改。[独立新增观察](../d3-ai-review/aw-run2-additional-observation.md)。

## aw-08

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

每个产品大类下面有多少个产品？只统计已分到子类别的产品，输出大类名称和数量，按数量降序、名称升序。

标准表：production.product, production.productsubcategory, production.productcategory

```sql
SELECT c.name AS category_name, COUNT(*) AS product_count FROM production.product AS p JOIN production.productsubcategory AS s ON p.productsubcategoryid = s.productsubcategoryid JOIN production.productcategory AS c ON s.productcategoryid = c.productcategoryid GROUP BY c.productcategoryid, c.name ORDER BY product_count DESC, c.name ASC LIMIT 200
```

```json
{
  "columns": [
    "category_name",
    "product_count"
  ],
  "rows": [
    [
      "Components",
      134
    ],
    [
      "Bikes",
      97
    ],
    [
      "Clothing",
      35
    ],
    [
      "Accessories",
      29
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-08.json)

AI依据：必须经过子类别桥接；NULL 子类别产品按题意排除。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-09

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

供应商档案一共有多少条？不按客户或门店计数。

标准表：purchasing.vendor

```sql
SELECT COUNT(*) AS vendor_count FROM purchasing.vendor
```

```json
{
  "columns": [
    "vendor_count"
  ],
  "rows": [
    [
      104
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-09.json)

AI依据：供应商实体在 purchasing.vendor，与客户门店分开。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-10

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

各员工职位有多少人？列人数最多的十个职位，按人数降序、职位名称升序。

标准表：humanresources.employee

```sql
SELECT jobtitle, COUNT(*) AS employee_count FROM humanresources.employee GROUP BY jobtitle ORDER BY employee_count DESC, jobtitle ASC LIMIT 10
```

```json
{
  "columns": [
    "jobtitle",
    "employee_count"
  ],
  "rows": [
    [
      "Production Technician - WC40",
      26
    ],
    [
      "Production Technician - WC50",
      26
    ],
    [
      "Production Technician - WC60",
      26
    ],
    [
      "Production Technician - WC30",
      25
    ],
    [
      "Production Technician - WC20",
      22
    ],
    [
      "Production Technician - WC10",
      17
    ],
    [
      "Production Technician - WC45",
      15
    ],
    [
      "Sales Representative",
      14
    ],
    [
      "Buyer",
      9
    ],
    [
      "Marketing Specialist",
      5
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-10.json)

AI依据：jobtitle 是职位；部门名称不能替代职位。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-11

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

2013 年销售订单头的 subtotal 合计是多少？仅算这个字段，不含 taxamt 和 freight。

标准表：sales.salesorderheader

```sql
SELECT SUM(subtotal) AS subtotal_sum FROM sales.salesorderheader WHERE orderdate >= CAST('2013-01-01' AS DATE) AND orderdate < CAST('2014-01-01' AS DATE)
```

```json
{
  "columns": [
    "subtotal_sum"
  ],
  "rows": [
    [
      null
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-11.json)

AI依据：完整2013自然年半开区间；明确 subtotal 而非 totaldue，币种不另行宣称。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-12

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

2024 年采购订单头的 subtotal 合计是多少？不含税与运费。

标准表：purchasing.purchaseorderheader

```sql
SELECT SUM(subtotal) AS subtotal_sum FROM purchasing.purchaseorderheader WHERE orderdate >= CAST('2024-01-01' AS DATE) AND orderdate < CAST('2025-01-01' AS DATE)
```

```json
{
  "columns": [
    "subtotal_sum"
  ],
  "rows": [
    [
      "20315203.2850"
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-12.json)

AI依据：采购头金额，避免明细 JOIN 重复累计。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-13

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

地址档案里哪个城市的地址记录最多？列出前五名城市和记录数，按记录数降序、城市名升序。

标准表：person.address

```sql
SELECT city, COUNT(*) AS address_count FROM person.address GROUP BY city ORDER BY address_count DESC, city ASC LIMIT 5
```

```json
{
  "columns": [
    "city",
    "address_count"
  ],
  "rows": [
    [
      "London",
      434
    ],
    [
      "Paris",
      398
    ],
    [
      "Burien",
      215
    ],
    [
      "Concord",
      214
    ],
    [
      "Beaverton",
      213
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-13.json)

AI依据：按地址记录而不是人数/客户数；相同城市文字归为一组。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-14

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

2024 年每个月有多少张销售订单？输出月份数字和订单数，按月份从小到大。

标准表：sales.salesorderheader

```sql
SELECT CAST(EXTRACT(MONTH FROM orderdate) AS INT) AS month, COUNT(*) AS order_count FROM sales.salesorderheader WHERE orderdate >= CAST('2024-01-01' AS DATE) AND orderdate < CAST('2025-01-01' AS DATE) GROUP BY EXTRACT(MONTH FROM orderdate) ORDER BY month ASC LIMIT 200
```

```json
{
  "columns": [
    "month",
    "order_count"
  ],
  "rows": [
    [
      1,
      400
    ],
    [
      2,
      338
    ],
    [
      3,
      443
    ],
    [
      4,
      426
    ],
    [
      5,
      436
    ],
    [
      6,
      741
    ],
    [
      7,
      1755
    ],
    [
      8,
      1785
    ],
    [
      9,
      1796
    ],
    [
      10,
      1971
    ],
    [
      11,
      2100
    ],
    [
      12,
      2053
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-14.json)

AI依据：按订单日期自然月，固定2024范围，订单头数量。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-15

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

销售原因字典里每个 reasontype 分别有多少条原因？按类型名称排序。

标准表：sales.salesreason

```sql
SELECT reasontype, COUNT(*) AS reason_count FROM sales.salesreason GROUP BY reasontype ORDER BY reasontype ASC LIMIT 200
```

```json
{
  "columns": [
    "reasontype",
    "reason_count"
  ],
  "rows": [
    [
      "Marketing",
      4
    ],
    [
      "Other",
      5
    ],
    [
      "Promotion",
      1
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-15.json)

AI依据：统计字典定义项数量，不统计订单使用原因次数。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-16

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

客户档案中 personid 非空的有多少条，storeid 非空的有多少条？两个条件分别计数，不要求互斥。

标准表：sales.customer

```sql
SELECT COUNT(personid) AS person_linked_count, COUNT(storeid) AS store_linked_count FROM sales.customer
```

```json
{
  "columns": [
    "person_linked_count",
    "store_linked_count"
  ],
  "rows": [
    [
      19119,
      1336
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-16.json)

AI依据：COUNT(列)排除NULL；不凭分类推断互斥或转换为人口数。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-17

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

汇总每个产品在所有库存地点的 quantity，列库存总量最高的五个产品编号、名称和数量；数量相同按编号升序。

标准表：production.productinventory, production.product

```sql
SELECT p.productid, p.name, SUM(i.quantity) AS total_quantity FROM production.productinventory AS i JOIN production.product AS p ON i.productid = p.productid GROUP BY p.productid, p.name ORDER BY total_quantity DESC, p.productid ASC LIMIT 5
```

```json
{
  "columns": [
    "productid",
    "name",
    "total_quantity"
  ],
  "rows": [
    [
      379,
      "Hex Nut 7",
      1911
    ],
    [
      367,
      "Thin-Jam Hex Nut 3",
      1901
    ],
    [
      383,
      "Hex Nut 23",
      1901
    ],
    [
      387,
      "Hex Nut 10",
      1888
    ],
    [
      393,
      "Hex Nut 14",
      1880
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-17.json)

AI依据：所有库位 quantity 加总，非订单销量；同编号聚合。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-18

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

2024 年各产品大类的销售购买数量分别是多少？按 salesorderdetail.orderqty 加总，只统计有子类别的产品，输出大类名和数量，按数量降序、名称升序。

标准表：sales.salesorderdetail, sales.salesorderheader, production.product, production.productsubcategory, production.productcategory

```sql
SELECT c.name AS category_name, SUM(d.orderqty) AS order_quantity FROM sales.salesorderdetail AS d JOIN sales.salesorderheader AS h ON d.salesorderid = h.salesorderid JOIN production.product AS p ON d.productid = p.productid JOIN production.productsubcategory AS s ON p.productsubcategoryid = s.productsubcategoryid JOIN production.productcategory AS c ON s.productcategoryid = c.productcategoryid WHERE h.orderdate >= CAST('2024-01-01' AS DATE) AND h.orderdate < CAST('2025-01-01' AS DATE) GROUP BY c.productcategoryid, c.name ORDER BY order_quantity DESC, c.name ASC LIMIT 200
```

```json
{
  "columns": [
    "category_name",
    "order_quantity"
  ],
  "rows": [
    [
      "Bikes",
      37776
    ],
    [
      "Clothing",
      37208
    ],
    [
      "Accessories",
      32245
    ],
    [
      "Components",
      24707
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-18.json)

AI依据：销售明细数量、销售头日期、大类维度；产品→子类别→大类须真实外键桥接。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-19

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

每种运输方式被多少张采购订单使用？输出运输方式名称和采购订单数，按订单数降序、名称升序。

标准表：purchasing.purchaseorderheader, purchasing.shipmethod

```sql
SELECT s.name AS ship_method, COUNT(*) AS order_count FROM purchasing.purchaseorderheader AS h JOIN purchasing.shipmethod AS s ON h.shipmethodid = s.shipmethodid GROUP BY s.shipmethodid, s.name ORDER BY order_count DESC, s.name ASC LIMIT 200
```

```json
{
  "columns": [
    "ship_method",
    "order_count"
  ],
  "rows": [
    [
      "CARGO TRANSPORT 5",
      1523
    ],
    [
      "OVERNIGHT J-FAST",
      1085
    ],
    [
      "ZY - EXPRESS",
      655
    ],
    [
      "XRQ - TRUCK GROUND",
      589
    ],
    [
      "OVERSEAS - DELUXE",
      160
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-19.json)

AI依据：题意采购订单；未使用方式不要求补0，运输方式FK链接。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-20

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

2024 年每个销售区域的销售订单 subtotal 合计是多少？不计 territoryid 为空的订单，输出区域名和合计，按金额降序、名称升序。

标准表：sales.salesorderheader, sales.salesterritory

```sql
SELECT t.name AS territory_name, SUM(h.subtotal) AS subtotal_sum FROM sales.salesorderheader AS h JOIN sales.salesterritory AS t ON h.territoryid = t.territoryid WHERE h.orderdate >= CAST('2024-01-01' AS DATE) AND h.orderdate < CAST('2025-01-01' AS DATE) GROUP BY t.territoryid, t.name ORDER BY subtotal_sum DESC NULLS LAST, t.name ASC LIMIT 200
```

```json
{
  "columns": [
    "territory_name",
    "subtotal_sum"
  ],
  "rows": [
    [
      "Southwest",
      "9121931.6549"
    ],
    [
      "Canada",
      "6231209.9635"
    ],
    [
      "Northwest",
      "6018432.5760"
    ],
    [
      "Australia",
      "4246450.5549"
    ],
    [
      "France",
      "3816543.3278"
    ],
    [
      "United Kingdom",
      "3641619.7164"
    ],
    [
      "Central",
      "2994225.3834"
    ],
    [
      "Northeast",
      "2631259.5991"
    ],
    [
      "Germany",
      "2570269.3486"
    ],
    [
      "Southeast",
      "2399947.3791"
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-20.json)

AI依据：销售组织区域不是地址州省；明确排除未分配区域且只累加订单头。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。

## aw-21

AW开发题gold；两遍AI建议通过，仍待人工最终核对。

currentflag 为 true 的员工中，各部门目前分配了多少人？以部门历史记录 enddate 为空表示目前分配，输出部门名和人数，按人数降序、部门名升序。

标准表：humanresources.employee, humanresources.employeedepartmenthistory, humanresources.department

```sql
SELECT d.name AS department_name, COUNT(DISTINCT e.businessentityid) AS employee_count FROM humanresources.employee AS e JOIN humanresources.employeedepartmenthistory AS h ON e.businessentityid = h.businessentityid JOIN humanresources.department AS d ON h.departmentid = d.departmentid WHERE e.currentflag = TRUE AND h.enddate IS NULL GROUP BY d.departmentid, d.name ORDER BY employee_count DESC, d.name ASC LIMIT 200
```

```json
{
  "columns": [
    "department_name",
    "employee_count"
  ],
  "rows": [
    [
      "Production",
      179
    ],
    [
      "Sales",
      18
    ],
    [
      "Purchasing",
      12
    ],
    [
      "Finance",
      10
    ],
    [
      "Information Services",
      10
    ],
    [
      "Marketing",
      9
    ],
    [
      "Facilities and Maintenance",
      7
    ],
    [
      "Engineering",
      6
    ],
    [
      "Human Resources",
      6
    ],
    [
      "Production Control",
      6
    ],
    [
      "Quality Assurance",
      6
    ],
    [
      "Shipping and Receiving",
      6
    ],
    [
      "Document Control",
      5
    ],
    [
      "Research and Development",
      4
    ],
    [
      "Tool Design",
      4
    ],
    [
      "Executive",
      2
    ]
  ]
}
```

[实际只读gold结果](../../artifacts/d3/a/gold/dev-v2/aw-21.json)

AI依据：在职标志和当前部门分配是两个显式条件；部门内按员工编号去重。

人工需要检查：逐题确认题意、字段、范围、聚合、单位、排序与NULL；aw11为2013空期SUM=NULL，其他4题修订2024发生在首次预测前，v1保留。

人工状态：pending_human_review。
