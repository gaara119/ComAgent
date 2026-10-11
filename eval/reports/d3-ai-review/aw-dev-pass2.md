# D3 AW 开发题第二遍 AI 预审

实际逐项核验 21 题；人工状态仍待审核。9道保留内容未展开或预测。

- **aw-01 — AI建议通过**：明确销售订单头记录数；COUNT全sales.salesorderheader，不误用采购头或明细行。
- **aw-02 — AI建议通过**：明确采购订单头；COUNT purchasing.purchaseorderheader，不误用销售头。
- **aw-03 — AI建议通过**：员工档案包含currentflag=false，COUNT employee全档案，没有偷偷只统计当前或salesperson。
- **aw-04 — AI建议通过**：明确销售人员表记录数，COUNT sales.salesperson，不按employee职位或全员工替代。
- **aw-05 — AI建议通过**：产品记录数，COUNT product，不按productmodel的型号数替代。
- **aw-06 — AI建议通过**：不同颜色数且NULL排除；COUNT DISTINCT color和WHERE非NULL一致，不将空缺作为颜色。
- **aw-07 — AI建议通过**：当前目录标价listprice，降序NULLS LAST并productid升序LIMIT5，不用成本或价格历史。
- **aw-08 — AI建议通过**：按类别统计已归子类别的产品；product→subcategory→category真实外键内连接，COUNT产品行；按数量降序名称升序。
- **aw-09 — AI建议通过**：供应商档案COUNT purchasing.vendor，避免客户/门店干扰。
- **aw-10 — AI建议通过**：employee.jobtitle分组COUNT，降序人数升序职位LIMIT10；未增加currentflag筛选。
- **aw-11 — AI建议通过**：2013销售头subtotal SUM，半开2013年筛选，无税运费；实际无匹配返回NULL，保留明确请求年份而不换年。
- **aw-12 — AI建议通过**：2024采购头subtotal SUM，半开明确年，不含taxamt/freight；2024是首次预测前修订的题面，并非修改数据库或评分答案。
- **aw-13 — AI建议通过**：地址档案按city分组COUNT地址记录，并非客户人数；降序记录数升序城市LIMIT5。
- **aw-14 — AI建议通过**：2024 sales.orderdate限定后按MONTH分组COUNT订单头，月份数字INT与升序符合题意；没有任意补零月。
- **aw-15 — AI建议通过**：原因字典salesreason按reasontype分组COUNT字典条目，不统计订单-原因桥表关联数。
- **aw-16 — AI建议通过**：personid和storeid各自COUNT非NULL，独立计数可重叠；无错误互斥筛选。
- **aw-17 — AI建议通过**：所有库存地点quantity聚合，inventory→product真实外键，按产品分组；数量降序productid升序LIMIT5，未用销量或工单数量。
- **aw-18 — AI建议通过**：2024销售头期间，salesdetail.orderqty聚合；5表真实FK路径到产品大类；内连接按题面仅有子类别，避免采购数量/库存量替代。
- **aw-19 — AI建议通过**：采购头关联shipmethod，COUNT订单头按运输方式分组；不统计销售头次数，真实FK无连接放大。
- **aw-20 — AI建议通过**：2024销售订单头subtotal按territory分组，内连接排除空区域；金额降序NULLS LAST名称升序，无税费/收货地址区域混淆。
- **aw-21 — AI建议通过**：currentflag=true且部门history.enddate为空是题面显式定义，按部门COUNT DISTINCT员工实体，排除历史任职重复行而非计salesperson。

标准SQL独立只读重跑的完整结果、实际目录与题集摘要见同名JSON。首次预测之前已保留2013空边界，并将其他4道日期题另存2024开发修正版以验证非空关联。
