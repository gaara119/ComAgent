# 全部待人工审核统一入口

打开同目录HTML逐项展开、填写或导出审核决定JSON；页面保存的是草稿，不会自动改题库、别名或人工记录。

待核735条，分开1052个审核对象；原始题号全部保留。已批准对象另列，不要求你重复批准。

先定sql-38/robust-23；再看专项去重、题面清洗和新口径标签；最后核对D3目录/题意及RAG各版本原文。不同答案版本可以逐个批准、拒绝或归档，不能用新版本成功代签旧版本。

|审核键|原编号|分组|题面/对象|
|---|---|---|---|
|alias:a-0c47392129d13dd6|a-0c47392129d13dd6|D2别名待定|金属 → Metallica（artist.name）|
|alias:a-c748b229db869a4e|a-c748b229db869a4e|D2别名待定|节奏摇滚 → Rock And Roll（genre.name）|
|sql:sql-38|sql-38|D2新gold待定|找出文件字节数最大的 3 首曲目，返回编号、名称和字节数；按字节数降序，并列按曲目编号升序。|
|robust:robust-23|robust-23|D2新gold待定|全部曲目的平均长度是几毫秒？|
|sql:sql-01|sql-01|历史/本轮系统回答（参考已确认）|客户表共有多少位客户？|
|sql:sql-02|sql-02|历史/本轮系统回答（参考已确认）|来自巴西的客户有多少位？|
|sql:sql-04|sql-04|历史/本轮系统回答（参考已确认）|列出来自巴西的客户编号、名字、姓氏和城市，按客户编号升序。|
|sql:sql-05|sql-05|历史/本轮系统回答（参考已确认）|列出来自美国的客户编号、城市和州，按客户编号升序。|
|sql:sql-06|sql-06|历史/本轮系统回答（参考已确认）|列出单价高于 0.99 的前 10 首曲目的编号、名称和单价，按曲目编号升序。|
|sql:sql-07|sql-07|历史/本轮系统回答（参考已确认）|列出职位为 Sales Support Agent 的员工编号、名字和姓氏，按员工编号升序。|
|sql:sql-09|sql-09|历史/本轮系统回答（参考已确认）|全部发票的总金额是多少？|
|sql:sql-10|sql-10|历史/本轮系统回答（参考已确认）|全部曲目的平均时长是多少毫秒？|
|sql:sql-11|sql-11|D1历史待核与归档|全部发票的平均总额是多少？请保留两位小数。|
|sql:sql-13|sql-13|历史/本轮系统回答（参考已确认）|按客户所在国家统计客户数，先按客户数降序，并列时按国家名称升序。|
|sql:sql-14|sql-14|历史/本轮系统回答（参考已确认）|按流派编号统计曲目数，先按曲目数降序，并列时按流派编号升序。|
|sql:sql-15|sql-15|历史/本轮系统回答（参考已确认）|按发票的账单国家统计销售总额，先按销售总额降序，并列时按国家名称升序。|
|sql:sql-17|sql-17|历史/本轮系统回答（参考已确认）|找出时长最长的 5 首曲目，返回编号、名称和毫秒时长；按时长降序，并列按编号升序。|
|sql:sql-18|sql-18|历史/本轮系统回答（参考已确认）|找出总额最高的 5 张发票，返回编号和总额；按总额降序，并列按编号升序。|
|sql:sql-19|sql-19|历史/本轮系统回答（参考已确认）|按姓氏降序取前 5 位客户，返回编号、名字和姓氏；姓氏相同时按客户编号升序。|
|sql:sql-21|sql-21|历史/本轮系统回答（参考已确认）|列出 2021 年的前 10 张发票，返回编号、日期和总额，按发票编号升序。|
|sql:sql-22|sql-22|D1历史待核与归档|列出 2004 年 1 月 1 日之前入职的员工编号、名字和入职日期，按员工编号升序。|
|sql:sql-24|sql-24|D1历史待核与归档|列出邮箱以 @gmail.com 结尾的客户编号、名字和邮箱，按客户编号升序。|
|sql:sql-26|sql-26|历史/本轮系统回答（参考已确认）|有多少位客户没有填写公司名称（company 为 NULL）？|
|sql:sql-27|sql-27|历史/本轮系统回答（参考已确认）|列出没有作曲者信息（composer 为 NULL）的前 10 首曲目编号和名称，按曲目编号升序。|
|sql:sql-29|sql-29|历史/本轮系统回答（参考已确认）|列出国家字段为 Antarctica 的客户编号、名字和姓氏，按客户编号升序。|
|rag:rag-02|rag-02|RAG新回答与引用|How many days after the end of the first fiscal quarter of Physician Sales & Service, Inc. must the financial results of post-Merger combined operations be published?|
|rag:rag-03|rag-03|RAG新回答与引用|For how many years after the effective date of the Merger does PSS agree to file all reports required by Section 13 of the Securities Exchange Act of 1934?|
|rag:rag-05|rag-05|RAG新回答与引用|Which rivers drain the western side of the primary watershed in the area around Holmfirth and Glossop?|
|rag:rag-06|rag-06|RAG新回答与引用|What are the most satisfactory arable crops grown in the soils of the Coal Measures?|
|rag:rag-07|rag-07|RAG新回答与引用|What is the thickness range of the Shale Grit in the southern part of the Sheet?|
|rag:rag-08|rag-08|RAG新回答与引用|In the Millstone Grits, what are the four main groups of grits and sandstones distinguished by color on the map?|
|rag:rag-10|rag-10|RAG新回答与引用|What type of digital device classification is specified for the equipment in accordance with the FCC rules?|
|rag:rag-11|rag-11|RAG新回答与引用|Which application allows you to create and share movies in minutes?|
|rag:rag-12|rag-12|RAG新回答与引用|What is the primary goal of the ENERGY STAR program in which Apple participates?|
|rag:rag-13|rag-13|RAG新回答与引用|Which device can be used to share one IP address among multiple computers?|
|rag:rag-15|rag-15|RAG新回答与引用|What are the five fundamental capabilities identified by ASQ and Forbes Insights as essential for building a successful organizational culture?|
|rag:rag-16|rag-16|RAG新回答与引用|What percentage of senior leaders rate their quality programs as world class or advanced according to the research?|
|rag:rag-18|rag-18|RAG新回答与引用|What is the correlation between attention distributions on label words and the model's final prediction quantified by?|
|rag:rag-19|rag-19|RAG新回答与引用|Which datasets showed significant performance enhancement with the proposed anchor reweighting method?|
|rag:rag-21|rag-21|RAG新回答与引用|根据这份简介，Iron Maiden 是哪一年在什么地方组建的？|
|rag:rag-22|rag-22|RAG新回答与引用|只根据 U2 简介，U2 于哪一年在哪座城市成立？|
|rag:rag-24|rag-24|RAG新回答与引用|根据这张简介图片，Led Zeppelin 于哪一年在哪座城市成立？|
|rag:rag-25|rag-25|RAG新回答与引用|根据口径手册，曲目最受欢迎的默认口径是什么，对应哪个汇总表达式？|
|rag:rag-26|rag-26|RAG新回答与引用|按口径手册，客单价的主口径全名是什么，对应哪个 SQL 表达式？|
|rag:rag-27|rag-27|RAG新回答与引用|根据中文数据字典，customer.country 和 invoice.billing_country 分别表示什么？|
|rag:rag-28|rag-28|RAG新回答与引用|只依据这份 Iron Maiden 简介，列出该乐队2026年在中国每场演出的门票收入。|
|d3:AW-CAT-T-person.person|AW-CAT-T-person.person|AW中文目录表说明|person.person|
|d3:AW-CAT-C-person.person.persontype|AW-CAT-C-person.person.persontype|AW中文目录列说明|person.person.persontype|
|d3:AW-CAT-C-person.person.namestyle|AW-CAT-C-person.person.namestyle|AW中文目录列说明|person.person.namestyle|
|d3:AW-CAT-C-person.person.emailpromotion|AW-CAT-C-person.person.emailpromotion|AW中文目录列说明|person.person.emailpromotion|
|d3:AW-CAT-T-production.document|AW-CAT-T-production.document|AW中文目录表说明|production.document|
|d3:AW-CAT-C-production.document.status|AW-CAT-C-production.document.status|AW中文目录列说明|production.document.status|
|d3:AW-CAT-C-production.document.documentnode|AW-CAT-C-production.document.documentnode|AW中文目录列说明|production.document.documentnode|
|d3:AW-CAT-T-production.transactionhistoryarchive|AW-CAT-T-production.transactionhistoryarchive|AW中文目录表说明|production.transactionhistoryarchive|
|d3:AW-CAT-C-production.transactionhistoryarchive.transactiontype|AW-CAT-C-production.transactionhistoryarchive.transactiontype|AW中文目录列说明|production.transactionhistoryarchive.transactiontype|
|d3:AW-CAT-C-production.transactionhistoryarchive.actualcost|AW-CAT-C-production.transactionhistoryarchive.actualcost|AW中文目录列说明|production.transactionhistoryarchive.actualcost|
|d3:AW-CAT-C-production.workorderrouting.actualresourcehrs|AW-CAT-C-production.workorderrouting.actualresourcehrs|AW中文目录列说明|production.workorderrouting.actualresourcehrs|
|d3:AW-CAT-C-production.workorderrouting.plannedcost|AW-CAT-C-production.workorderrouting.plannedcost|AW中文目录列说明|production.workorderrouting.plannedcost|
|d3:AW-CAT-C-production.workorderrouting.actualcost|AW-CAT-C-production.workorderrouting.actualcost|AW中文目录列说明|production.workorderrouting.actualcost|
|d3:AW-CAT-C-purchasing.productvendor.averageleadtime|AW-CAT-C-purchasing.productvendor.averageleadtime|AW中文目录列说明|purchasing.productvendor.averageleadtime|
|d3:AW-CAT-C-purchasing.productvendor.standardprice|AW-CAT-C-purchasing.productvendor.standardprice|AW中文目录列说明|purchasing.productvendor.standardprice|
|d3:AW-CAT-C-purchasing.productvendor.lastreceiptcost|AW-CAT-C-purchasing.productvendor.lastreceiptcost|AW中文目录列说明|purchasing.productvendor.lastreceiptcost|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.unitprice|AW-CAT-C-purchasing.purchaseorderdetail.unitprice|AW中文目录列说明|purchasing.purchaseorderdetail.unitprice|
|d3:AW-CAT-T-purchasing.purchaseorderheader|AW-CAT-T-purchasing.purchaseorderheader|AW中文目录表说明|purchasing.purchaseorderheader|
|d3:AW-CAT-C-purchasing.purchaseorderheader.status|AW-CAT-C-purchasing.purchaseorderheader.status|AW中文目录列说明|purchasing.purchaseorderheader.status|
|d3:AW-CAT-C-purchasing.purchaseorderheader.subtotal|AW-CAT-C-purchasing.purchaseorderheader.subtotal|AW中文目录列说明|purchasing.purchaseorderheader.subtotal|
|d3:AW-CAT-C-purchasing.purchaseorderheader.taxamt|AW-CAT-C-purchasing.purchaseorderheader.taxamt|AW中文目录列说明|purchasing.purchaseorderheader.taxamt|
|d3:AW-CAT-C-purchasing.purchaseorderheader.freight|AW-CAT-C-purchasing.purchaseorderheader.freight|AW中文目录列说明|purchasing.purchaseorderheader.freight|
|d3:AW-CAT-T-purchasing.shipmethod|AW-CAT-T-purchasing.shipmethod|AW中文目录表说明|purchasing.shipmethod|
|d3:AW-CAT-C-purchasing.shipmethod.shipbase|AW-CAT-C-purchasing.shipmethod.shipbase|AW中文目录列说明|purchasing.shipmethod.shipbase|
|d3:AW-CAT-C-purchasing.shipmethod.shiprate|AW-CAT-C-purchasing.shipmethod.shiprate|AW中文目录列说明|purchasing.shipmethod.shiprate|
|d3:aw-01|aw-01|AW开发题gold|AdventureWorks 数据库共有多少张销售订单？请统计订单头记录数。|
|d3:aw-02|aw-02|AW开发题gold|采购订单一共有多少张？按采购订单头计数。|
|d3:aw-03|aw-03|AW开发题gold|员工档案中共有多少名员工？包括 currentflag 为 false 的档案。|
|d3:aw-04|aw-04|AW开发题gold|销售人员表中共有多少名销售人员？|
|d3:aw-05|aw-05|AW开发题gold|产品目录中共有多少个产品？不要用产品型号数替代。|
|d3:aw-06|aw-06|AW开发题gold|产品颜色有多少种？未填写颜色的不计入。|
|d3:aw-07|aw-07|AW开发题gold|列出目录售价最高的五个产品，给出产品编号、名称和售价；同价时按产品编号从小到大。|
|d3:aw-08|aw-08|AW开发题gold|每个产品大类下面有多少个产品？只统计已分到子类别的产品，输出大类名称和数量，按数量降序、名称升序。|
|d3:aw-09|aw-09|AW开发题gold|供应商档案一共有多少条？不按客户或门店计数。|
|d3:aw-10|aw-10|AW开发题gold|各员工职位有多少人？列人数最多的十个职位，按人数降序、职位名称升序。|
|d3:aw-11|aw-11|AW开发题gold|2013 年销售订单头的 subtotal 合计是多少？仅算这个字段，不含 taxamt 和 freight。|
|d3:aw-12|aw-12|AW开发题gold|2024 年采购订单头的 subtotal 合计是多少？不含税与运费。|
|d3:aw-13|aw-13|AW开发题gold|地址档案里哪个城市的地址记录最多？列出前五名城市和记录数，按记录数降序、城市名升序。|
|d3:aw-14|aw-14|AW开发题gold|2024 年每个月有多少张销售订单？输出月份数字和订单数，按月份从小到大。|
|d3:aw-15|aw-15|AW开发题gold|销售原因字典里每个 reasontype 分别有多少条原因？按类型名称排序。|
|d3:aw-16|aw-16|AW开发题gold|客户档案中 personid 非空的有多少条，storeid 非空的有多少条？两个条件分别计数，不要求互斥。|
|d3:aw-17|aw-17|AW开发题gold|汇总每个产品在所有库存地点的 quantity，列库存总量最高的五个产品编号、名称和数量；数量相同按编号升序。|
|d3:aw-18|aw-18|AW开发题gold|2024 年各产品大类的销售购买数量分别是多少？按 salesorderdetail.orderqty 加总，只统计有子类别的产品，输出大类名和数量，按数量降序、名称升序。|
|d3:aw-19|aw-19|AW开发题gold|每种运输方式被多少张采购订单使用？输出运输方式名称和采购订单数，按订单数降序、名称升序。|
|d3:aw-20|aw-20|AW开发题gold|2024 年每个销售区域的销售订单 subtotal 合计是多少？不计 territoryid 为空的订单，输出区域名和合计，按金额降序、名称升序。|
|d3:aw-21|aw-21|AW开发题gold|currentflag 为 true 的员工中，各部门目前分配了多少人？以部门历史记录 enddate 为空表示目前分配，输出部门名和人数，按人数降序、部门名升序。|
|d3:AW-CAT-T-humanresources.department|AW-CAT-T-humanresources.department|AW中文目录表说明|humanresources.department|
|d3:AW-CAT-C-humanresources.department.departmentid|AW-CAT-C-humanresources.department.departmentid|AW中文目录列说明|humanresources.department.departmentid|
|d3:AW-CAT-C-humanresources.department.name|AW-CAT-C-humanresources.department.name|AW中文目录列说明|humanresources.department.name|
|d3:AW-CAT-C-humanresources.department.groupname|AW-CAT-C-humanresources.department.groupname|AW中文目录列说明|humanresources.department.groupname|
|d3:AW-CAT-C-humanresources.department.modifieddate|AW-CAT-C-humanresources.department.modifieddate|AW中文目录列说明|humanresources.department.modifieddate|
|d3:AW-CAT-T-humanresources.employee|AW-CAT-T-humanresources.employee|AW中文目录表说明|humanresources.employee|
|d3:AW-CAT-C-humanresources.employee.businessentityid|AW-CAT-C-humanresources.employee.businessentityid|AW中文目录列说明|humanresources.employee.businessentityid|
|d3:AW-CAT-C-humanresources.employee.nationalidnumber|AW-CAT-C-humanresources.employee.nationalidnumber|AW中文目录列说明|humanresources.employee.nationalidnumber|
|d3:AW-CAT-C-humanresources.employee.loginid|AW-CAT-C-humanresources.employee.loginid|AW中文目录列说明|humanresources.employee.loginid|
|d3:AW-CAT-C-humanresources.employee.jobtitle|AW-CAT-C-humanresources.employee.jobtitle|AW中文目录列说明|humanresources.employee.jobtitle|
|d3:AW-CAT-C-humanresources.employee.birthdate|AW-CAT-C-humanresources.employee.birthdate|AW中文目录列说明|humanresources.employee.birthdate|
|d3:AW-CAT-C-humanresources.employee.maritalstatus|AW-CAT-C-humanresources.employee.maritalstatus|AW中文目录列说明|humanresources.employee.maritalstatus|
|d3:AW-CAT-C-humanresources.employee.gender|AW-CAT-C-humanresources.employee.gender|AW中文目录列说明|humanresources.employee.gender|
|d3:AW-CAT-C-humanresources.employee.hiredate|AW-CAT-C-humanresources.employee.hiredate|AW中文目录列说明|humanresources.employee.hiredate|
|d3:AW-CAT-C-humanresources.employee.salariedflag|AW-CAT-C-humanresources.employee.salariedflag|AW中文目录列说明|humanresources.employee.salariedflag|
|d3:AW-CAT-C-humanresources.employee.vacationhours|AW-CAT-C-humanresources.employee.vacationhours|AW中文目录列说明|humanresources.employee.vacationhours|
|d3:AW-CAT-C-humanresources.employee.sickleavehours|AW-CAT-C-humanresources.employee.sickleavehours|AW中文目录列说明|humanresources.employee.sickleavehours|
|d3:AW-CAT-C-humanresources.employee.currentflag|AW-CAT-C-humanresources.employee.currentflag|AW中文目录列说明|humanresources.employee.currentflag|
|d3:AW-CAT-C-humanresources.employee.rowguid|AW-CAT-C-humanresources.employee.rowguid|AW中文目录列说明|humanresources.employee.rowguid|
|d3:AW-CAT-C-humanresources.employee.modifieddate|AW-CAT-C-humanresources.employee.modifieddate|AW中文目录列说明|humanresources.employee.modifieddate|
|d3:AW-CAT-C-humanresources.employee.organizationnode|AW-CAT-C-humanresources.employee.organizationnode|AW中文目录列说明|humanresources.employee.organizationnode|
|d3:AW-CAT-T-humanresources.employeedepartmenthistory|AW-CAT-T-humanresources.employeedepartmenthistory|AW中文目录表说明|humanresources.employeedepartmenthistory|
|d3:AW-CAT-C-humanresources.employeedepartmenthistory.businessentityid|AW-CAT-C-humanresources.employeedepartmenthistory.businessentityid|AW中文目录列说明|humanresources.employeedepartmenthistory.businessentityid|
|d3:AW-CAT-C-humanresources.employeedepartmenthistory.departmentid|AW-CAT-C-humanresources.employeedepartmenthistory.departmentid|AW中文目录列说明|humanresources.employeedepartmenthistory.departmentid|
|d3:AW-CAT-C-humanresources.employeedepartmenthistory.shiftid|AW-CAT-C-humanresources.employeedepartmenthistory.shiftid|AW中文目录列说明|humanresources.employeedepartmenthistory.shiftid|
|d3:AW-CAT-C-humanresources.employeedepartmenthistory.startdate|AW-CAT-C-humanresources.employeedepartmenthistory.startdate|AW中文目录列说明|humanresources.employeedepartmenthistory.startdate|
|d3:AW-CAT-C-humanresources.employeedepartmenthistory.enddate|AW-CAT-C-humanresources.employeedepartmenthistory.enddate|AW中文目录列说明|humanresources.employeedepartmenthistory.enddate|
|d3:AW-CAT-C-humanresources.employeedepartmenthistory.modifieddate|AW-CAT-C-humanresources.employeedepartmenthistory.modifieddate|AW中文目录列说明|humanresources.employeedepartmenthistory.modifieddate|
|d3:AW-CAT-T-humanresources.employeepayhistory|AW-CAT-T-humanresources.employeepayhistory|AW中文目录表说明|humanresources.employeepayhistory|
|d3:AW-CAT-C-humanresources.employeepayhistory.businessentityid|AW-CAT-C-humanresources.employeepayhistory.businessentityid|AW中文目录列说明|humanresources.employeepayhistory.businessentityid|
|d3:AW-CAT-C-humanresources.employeepayhistory.ratechangedate|AW-CAT-C-humanresources.employeepayhistory.ratechangedate|AW中文目录列说明|humanresources.employeepayhistory.ratechangedate|
|d3:AW-CAT-C-humanresources.employeepayhistory.rate|AW-CAT-C-humanresources.employeepayhistory.rate|AW中文目录列说明|humanresources.employeepayhistory.rate|
|d3:AW-CAT-C-humanresources.employeepayhistory.payfrequency|AW-CAT-C-humanresources.employeepayhistory.payfrequency|AW中文目录列说明|humanresources.employeepayhistory.payfrequency|
|d3:AW-CAT-C-humanresources.employeepayhistory.modifieddate|AW-CAT-C-humanresources.employeepayhistory.modifieddate|AW中文目录列说明|humanresources.employeepayhistory.modifieddate|
|d3:AW-CAT-T-humanresources.jobcandidate|AW-CAT-T-humanresources.jobcandidate|AW中文目录表说明|humanresources.jobcandidate|
|d3:AW-CAT-C-humanresources.jobcandidate.jobcandidateid|AW-CAT-C-humanresources.jobcandidate.jobcandidateid|AW中文目录列说明|humanresources.jobcandidate.jobcandidateid|
|d3:AW-CAT-C-humanresources.jobcandidate.businessentityid|AW-CAT-C-humanresources.jobcandidate.businessentityid|AW中文目录列说明|humanresources.jobcandidate.businessentityid|
|d3:AW-CAT-C-humanresources.jobcandidate.resume|AW-CAT-C-humanresources.jobcandidate.resume|AW中文目录列说明|humanresources.jobcandidate.resume|
|d3:AW-CAT-C-humanresources.jobcandidate.modifieddate|AW-CAT-C-humanresources.jobcandidate.modifieddate|AW中文目录列说明|humanresources.jobcandidate.modifieddate|
|d3:AW-CAT-T-humanresources.shift|AW-CAT-T-humanresources.shift|AW中文目录表说明|humanresources.shift|
|d3:AW-CAT-C-humanresources.shift.shiftid|AW-CAT-C-humanresources.shift.shiftid|AW中文目录列说明|humanresources.shift.shiftid|
|d3:AW-CAT-C-humanresources.shift.name|AW-CAT-C-humanresources.shift.name|AW中文目录列说明|humanresources.shift.name|
|d3:AW-CAT-C-humanresources.shift.starttime|AW-CAT-C-humanresources.shift.starttime|AW中文目录列说明|humanresources.shift.starttime|
|d3:AW-CAT-C-humanresources.shift.endtime|AW-CAT-C-humanresources.shift.endtime|AW中文目录列说明|humanresources.shift.endtime|
|d3:AW-CAT-C-humanresources.shift.modifieddate|AW-CAT-C-humanresources.shift.modifieddate|AW中文目录列说明|humanresources.shift.modifieddate|
|d3:AW-CAT-T-person.address|AW-CAT-T-person.address|AW中文目录表说明|person.address|
|d3:AW-CAT-C-person.address.addressid|AW-CAT-C-person.address.addressid|AW中文目录列说明|person.address.addressid|
|d3:AW-CAT-C-person.address.addressline1|AW-CAT-C-person.address.addressline1|AW中文目录列说明|person.address.addressline1|
|d3:AW-CAT-C-person.address.addressline2|AW-CAT-C-person.address.addressline2|AW中文目录列说明|person.address.addressline2|
|d3:AW-CAT-C-person.address.city|AW-CAT-C-person.address.city|AW中文目录列说明|person.address.city|
|d3:AW-CAT-C-person.address.stateprovinceid|AW-CAT-C-person.address.stateprovinceid|AW中文目录列说明|person.address.stateprovinceid|
|d3:AW-CAT-C-person.address.postalcode|AW-CAT-C-person.address.postalcode|AW中文目录列说明|person.address.postalcode|
|d3:AW-CAT-C-person.address.spatiallocation|AW-CAT-C-person.address.spatiallocation|AW中文目录列说明|person.address.spatiallocation|
|d3:AW-CAT-C-person.address.rowguid|AW-CAT-C-person.address.rowguid|AW中文目录列说明|person.address.rowguid|
|d3:AW-CAT-C-person.address.modifieddate|AW-CAT-C-person.address.modifieddate|AW中文目录列说明|person.address.modifieddate|
|d3:AW-CAT-T-person.addresstype|AW-CAT-T-person.addresstype|AW中文目录表说明|person.addresstype|
|d3:AW-CAT-C-person.addresstype.addresstypeid|AW-CAT-C-person.addresstype.addresstypeid|AW中文目录列说明|person.addresstype.addresstypeid|
|d3:AW-CAT-C-person.addresstype.name|AW-CAT-C-person.addresstype.name|AW中文目录列说明|person.addresstype.name|
|d3:AW-CAT-C-person.addresstype.rowguid|AW-CAT-C-person.addresstype.rowguid|AW中文目录列说明|person.addresstype.rowguid|
|d3:AW-CAT-C-person.addresstype.modifieddate|AW-CAT-C-person.addresstype.modifieddate|AW中文目录列说明|person.addresstype.modifieddate|
|d3:AW-CAT-T-person.businessentity|AW-CAT-T-person.businessentity|AW中文目录表说明|person.businessentity|
|d3:AW-CAT-C-person.businessentity.businessentityid|AW-CAT-C-person.businessentity.businessentityid|AW中文目录列说明|person.businessentity.businessentityid|
|d3:AW-CAT-C-person.businessentity.rowguid|AW-CAT-C-person.businessentity.rowguid|AW中文目录列说明|person.businessentity.rowguid|
|d3:AW-CAT-C-person.businessentity.modifieddate|AW-CAT-C-person.businessentity.modifieddate|AW中文目录列说明|person.businessentity.modifieddate|
|d3:AW-CAT-T-person.businessentityaddress|AW-CAT-T-person.businessentityaddress|AW中文目录表说明|person.businessentityaddress|
|d3:AW-CAT-C-person.businessentityaddress.businessentityid|AW-CAT-C-person.businessentityaddress.businessentityid|AW中文目录列说明|person.businessentityaddress.businessentityid|
|d3:AW-CAT-C-person.businessentityaddress.addressid|AW-CAT-C-person.businessentityaddress.addressid|AW中文目录列说明|person.businessentityaddress.addressid|
|d3:AW-CAT-C-person.businessentityaddress.addresstypeid|AW-CAT-C-person.businessentityaddress.addresstypeid|AW中文目录列说明|person.businessentityaddress.addresstypeid|
|d3:AW-CAT-C-person.businessentityaddress.rowguid|AW-CAT-C-person.businessentityaddress.rowguid|AW中文目录列说明|person.businessentityaddress.rowguid|
|d3:AW-CAT-C-person.businessentityaddress.modifieddate|AW-CAT-C-person.businessentityaddress.modifieddate|AW中文目录列说明|person.businessentityaddress.modifieddate|
|d3:AW-CAT-T-person.businessentitycontact|AW-CAT-T-person.businessentitycontact|AW中文目录表说明|person.businessentitycontact|
|d3:AW-CAT-C-person.businessentitycontact.businessentityid|AW-CAT-C-person.businessentitycontact.businessentityid|AW中文目录列说明|person.businessentitycontact.businessentityid|
|d3:AW-CAT-C-person.businessentitycontact.personid|AW-CAT-C-person.businessentitycontact.personid|AW中文目录列说明|person.businessentitycontact.personid|
|d3:AW-CAT-C-person.businessentitycontact.contacttypeid|AW-CAT-C-person.businessentitycontact.contacttypeid|AW中文目录列说明|person.businessentitycontact.contacttypeid|
|d3:AW-CAT-C-person.businessentitycontact.rowguid|AW-CAT-C-person.businessentitycontact.rowguid|AW中文目录列说明|person.businessentitycontact.rowguid|
|d3:AW-CAT-C-person.businessentitycontact.modifieddate|AW-CAT-C-person.businessentitycontact.modifieddate|AW中文目录列说明|person.businessentitycontact.modifieddate|
|d3:AW-CAT-T-person.contacttype|AW-CAT-T-person.contacttype|AW中文目录表说明|person.contacttype|
|d3:AW-CAT-C-person.contacttype.contacttypeid|AW-CAT-C-person.contacttype.contacttypeid|AW中文目录列说明|person.contacttype.contacttypeid|
|d3:AW-CAT-C-person.contacttype.name|AW-CAT-C-person.contacttype.name|AW中文目录列说明|person.contacttype.name|
|d3:AW-CAT-C-person.contacttype.modifieddate|AW-CAT-C-person.contacttype.modifieddate|AW中文目录列说明|person.contacttype.modifieddate|
|d3:AW-CAT-T-person.countryregion|AW-CAT-T-person.countryregion|AW中文目录表说明|person.countryregion|
|d3:AW-CAT-C-person.countryregion.countryregioncode|AW-CAT-C-person.countryregion.countryregioncode|AW中文目录列说明|person.countryregion.countryregioncode|
|d3:AW-CAT-C-person.countryregion.name|AW-CAT-C-person.countryregion.name|AW中文目录列说明|person.countryregion.name|
|d3:AW-CAT-C-person.countryregion.modifieddate|AW-CAT-C-person.countryregion.modifieddate|AW中文目录列说明|person.countryregion.modifieddate|
|d3:AW-CAT-T-person.emailaddress|AW-CAT-T-person.emailaddress|AW中文目录表说明|person.emailaddress|
|d3:AW-CAT-C-person.emailaddress.businessentityid|AW-CAT-C-person.emailaddress.businessentityid|AW中文目录列说明|person.emailaddress.businessentityid|
|d3:AW-CAT-C-person.emailaddress.emailaddressid|AW-CAT-C-person.emailaddress.emailaddressid|AW中文目录列说明|person.emailaddress.emailaddressid|
|d3:AW-CAT-C-person.emailaddress.emailaddress|AW-CAT-C-person.emailaddress.emailaddress|AW中文目录列说明|person.emailaddress.emailaddress|
|d3:AW-CAT-C-person.emailaddress.rowguid|AW-CAT-C-person.emailaddress.rowguid|AW中文目录列说明|person.emailaddress.rowguid|
|d3:AW-CAT-C-person.emailaddress.modifieddate|AW-CAT-C-person.emailaddress.modifieddate|AW中文目录列说明|person.emailaddress.modifieddate|
|d3:AW-CAT-T-person.password|AW-CAT-T-person.password|AW中文目录表说明|person.password|
|d3:AW-CAT-C-person.password.businessentityid|AW-CAT-C-person.password.businessentityid|AW中文目录列说明|person.password.businessentityid|
|d3:AW-CAT-C-person.password.passwordhash|AW-CAT-C-person.password.passwordhash|AW中文目录列说明|person.password.passwordhash|
|d3:AW-CAT-C-person.password.passwordsalt|AW-CAT-C-person.password.passwordsalt|AW中文目录列说明|person.password.passwordsalt|
|d3:AW-CAT-C-person.password.rowguid|AW-CAT-C-person.password.rowguid|AW中文目录列说明|person.password.rowguid|
|d3:AW-CAT-C-person.password.modifieddate|AW-CAT-C-person.password.modifieddate|AW中文目录列说明|person.password.modifieddate|
|d3:AW-CAT-C-person.person.businessentityid|AW-CAT-C-person.person.businessentityid|AW中文目录列说明|person.person.businessentityid|
|d3:AW-CAT-C-person.person.title|AW-CAT-C-person.person.title|AW中文目录列说明|person.person.title|
|d3:AW-CAT-C-person.person.firstname|AW-CAT-C-person.person.firstname|AW中文目录列说明|person.person.firstname|
|d3:AW-CAT-C-person.person.middlename|AW-CAT-C-person.person.middlename|AW中文目录列说明|person.person.middlename|
|d3:AW-CAT-C-person.person.lastname|AW-CAT-C-person.person.lastname|AW中文目录列说明|person.person.lastname|
|d3:AW-CAT-C-person.person.suffix|AW-CAT-C-person.person.suffix|AW中文目录列说明|person.person.suffix|
|d3:AW-CAT-C-person.person.additionalcontactinfo|AW-CAT-C-person.person.additionalcontactinfo|AW中文目录列说明|person.person.additionalcontactinfo|
|d3:AW-CAT-C-person.person.demographics|AW-CAT-C-person.person.demographics|AW中文目录列说明|person.person.demographics|
|d3:AW-CAT-C-person.person.rowguid|AW-CAT-C-person.person.rowguid|AW中文目录列说明|person.person.rowguid|
|d3:AW-CAT-C-person.person.modifieddate|AW-CAT-C-person.person.modifieddate|AW中文目录列说明|person.person.modifieddate|
|d3:AW-CAT-T-person.personphone|AW-CAT-T-person.personphone|AW中文目录表说明|person.personphone|
|d3:AW-CAT-C-person.personphone.businessentityid|AW-CAT-C-person.personphone.businessentityid|AW中文目录列说明|person.personphone.businessentityid|
|d3:AW-CAT-C-person.personphone.phonenumber|AW-CAT-C-person.personphone.phonenumber|AW中文目录列说明|person.personphone.phonenumber|
|d3:AW-CAT-C-person.personphone.phonenumbertypeid|AW-CAT-C-person.personphone.phonenumbertypeid|AW中文目录列说明|person.personphone.phonenumbertypeid|
|d3:AW-CAT-C-person.personphone.modifieddate|AW-CAT-C-person.personphone.modifieddate|AW中文目录列说明|person.personphone.modifieddate|
|d3:AW-CAT-T-person.phonenumbertype|AW-CAT-T-person.phonenumbertype|AW中文目录表说明|person.phonenumbertype|
|d3:AW-CAT-C-person.phonenumbertype.phonenumbertypeid|AW-CAT-C-person.phonenumbertype.phonenumbertypeid|AW中文目录列说明|person.phonenumbertype.phonenumbertypeid|
|d3:AW-CAT-C-person.phonenumbertype.name|AW-CAT-C-person.phonenumbertype.name|AW中文目录列说明|person.phonenumbertype.name|
|d3:AW-CAT-C-person.phonenumbertype.modifieddate|AW-CAT-C-person.phonenumbertype.modifieddate|AW中文目录列说明|person.phonenumbertype.modifieddate|
|d3:AW-CAT-T-person.stateprovince|AW-CAT-T-person.stateprovince|AW中文目录表说明|person.stateprovince|
|d3:AW-CAT-C-person.stateprovince.stateprovinceid|AW-CAT-C-person.stateprovince.stateprovinceid|AW中文目录列说明|person.stateprovince.stateprovinceid|
|d3:AW-CAT-C-person.stateprovince.stateprovincecode|AW-CAT-C-person.stateprovince.stateprovincecode|AW中文目录列说明|person.stateprovince.stateprovincecode|
|d3:AW-CAT-C-person.stateprovince.countryregioncode|AW-CAT-C-person.stateprovince.countryregioncode|AW中文目录列说明|person.stateprovince.countryregioncode|
|d3:AW-CAT-C-person.stateprovince.isonlystateprovinceflag|AW-CAT-C-person.stateprovince.isonlystateprovinceflag|AW中文目录列说明|person.stateprovince.isonlystateprovinceflag|
|d3:AW-CAT-C-person.stateprovince.name|AW-CAT-C-person.stateprovince.name|AW中文目录列说明|person.stateprovince.name|
|d3:AW-CAT-C-person.stateprovince.territoryid|AW-CAT-C-person.stateprovince.territoryid|AW中文目录列说明|person.stateprovince.territoryid|
|d3:AW-CAT-C-person.stateprovince.rowguid|AW-CAT-C-person.stateprovince.rowguid|AW中文目录列说明|person.stateprovince.rowguid|
|d3:AW-CAT-C-person.stateprovince.modifieddate|AW-CAT-C-person.stateprovince.modifieddate|AW中文目录列说明|person.stateprovince.modifieddate|
|d3:AW-CAT-T-production.billofmaterials|AW-CAT-T-production.billofmaterials|AW中文目录表说明|production.billofmaterials|
|d3:AW-CAT-C-production.billofmaterials.billofmaterialsid|AW-CAT-C-production.billofmaterials.billofmaterialsid|AW中文目录列说明|production.billofmaterials.billofmaterialsid|
|d3:AW-CAT-C-production.billofmaterials.productassemblyid|AW-CAT-C-production.billofmaterials.productassemblyid|AW中文目录列说明|production.billofmaterials.productassemblyid|
|d3:AW-CAT-C-production.billofmaterials.componentid|AW-CAT-C-production.billofmaterials.componentid|AW中文目录列说明|production.billofmaterials.componentid|
|d3:AW-CAT-C-production.billofmaterials.startdate|AW-CAT-C-production.billofmaterials.startdate|AW中文目录列说明|production.billofmaterials.startdate|
|d3:AW-CAT-C-production.billofmaterials.enddate|AW-CAT-C-production.billofmaterials.enddate|AW中文目录列说明|production.billofmaterials.enddate|
|d3:AW-CAT-C-production.billofmaterials.unitmeasurecode|AW-CAT-C-production.billofmaterials.unitmeasurecode|AW中文目录列说明|production.billofmaterials.unitmeasurecode|
|d3:AW-CAT-C-production.billofmaterials.bomlevel|AW-CAT-C-production.billofmaterials.bomlevel|AW中文目录列说明|production.billofmaterials.bomlevel|
|d3:AW-CAT-C-production.billofmaterials.perassemblyqty|AW-CAT-C-production.billofmaterials.perassemblyqty|AW中文目录列说明|production.billofmaterials.perassemblyqty|
|d3:AW-CAT-C-production.billofmaterials.modifieddate|AW-CAT-C-production.billofmaterials.modifieddate|AW中文目录列说明|production.billofmaterials.modifieddate|
|d3:AW-CAT-T-production.culture|AW-CAT-T-production.culture|AW中文目录表说明|production.culture|
|d3:AW-CAT-C-production.culture.cultureid|AW-CAT-C-production.culture.cultureid|AW中文目录列说明|production.culture.cultureid|
|d3:AW-CAT-C-production.culture.name|AW-CAT-C-production.culture.name|AW中文目录列说明|production.culture.name|
|d3:AW-CAT-C-production.culture.modifieddate|AW-CAT-C-production.culture.modifieddate|AW中文目录列说明|production.culture.modifieddate|
|d3:AW-CAT-C-production.document.title|AW-CAT-C-production.document.title|AW中文目录列说明|production.document.title|
|d3:AW-CAT-C-production.document.owner|AW-CAT-C-production.document.owner|AW中文目录列说明|production.document.owner|
|d3:AW-CAT-C-production.document.folderflag|AW-CAT-C-production.document.folderflag|AW中文目录列说明|production.document.folderflag|
|d3:AW-CAT-C-production.document.filename|AW-CAT-C-production.document.filename|AW中文目录列说明|production.document.filename|
|d3:AW-CAT-C-production.document.fileextension|AW-CAT-C-production.document.fileextension|AW中文目录列说明|production.document.fileextension|
|d3:AW-CAT-C-production.document.revision|AW-CAT-C-production.document.revision|AW中文目录列说明|production.document.revision|
|d3:AW-CAT-C-production.document.changenumber|AW-CAT-C-production.document.changenumber|AW中文目录列说明|production.document.changenumber|
|d3:AW-CAT-C-production.document.documentsummary|AW-CAT-C-production.document.documentsummary|AW中文目录列说明|production.document.documentsummary|
|d3:AW-CAT-C-production.document.document|AW-CAT-C-production.document.document|AW中文目录列说明|production.document.document|
|d3:AW-CAT-C-production.document.rowguid|AW-CAT-C-production.document.rowguid|AW中文目录列说明|production.document.rowguid|
|d3:AW-CAT-C-production.document.modifieddate|AW-CAT-C-production.document.modifieddate|AW中文目录列说明|production.document.modifieddate|
|d3:AW-CAT-T-production.illustration|AW-CAT-T-production.illustration|AW中文目录表说明|production.illustration|
|d3:AW-CAT-C-production.illustration.illustrationid|AW-CAT-C-production.illustration.illustrationid|AW中文目录列说明|production.illustration.illustrationid|
|d3:AW-CAT-C-production.illustration.diagram|AW-CAT-C-production.illustration.diagram|AW中文目录列说明|production.illustration.diagram|
|d3:AW-CAT-C-production.illustration.modifieddate|AW-CAT-C-production.illustration.modifieddate|AW中文目录列说明|production.illustration.modifieddate|
|d3:AW-CAT-T-production.location|AW-CAT-T-production.location|AW中文目录表说明|production.location|
|d3:AW-CAT-C-production.location.locationid|AW-CAT-C-production.location.locationid|AW中文目录列说明|production.location.locationid|
|d3:AW-CAT-C-production.location.name|AW-CAT-C-production.location.name|AW中文目录列说明|production.location.name|
|d3:AW-CAT-C-production.location.costrate|AW-CAT-C-production.location.costrate|AW中文目录列说明|production.location.costrate|
|d3:AW-CAT-C-production.location.availability|AW-CAT-C-production.location.availability|AW中文目录列说明|production.location.availability|
|d3:AW-CAT-C-production.location.modifieddate|AW-CAT-C-production.location.modifieddate|AW中文目录列说明|production.location.modifieddate|
|d3:AW-CAT-T-production.product|AW-CAT-T-production.product|AW中文目录表说明|production.product|
|d3:AW-CAT-C-production.product.productid|AW-CAT-C-production.product.productid|AW中文目录列说明|production.product.productid|
|d3:AW-CAT-C-production.product.name|AW-CAT-C-production.product.name|AW中文目录列说明|production.product.name|
|d3:AW-CAT-C-production.product.productnumber|AW-CAT-C-production.product.productnumber|AW中文目录列说明|production.product.productnumber|
|d3:AW-CAT-C-production.product.makeflag|AW-CAT-C-production.product.makeflag|AW中文目录列说明|production.product.makeflag|
|d3:AW-CAT-C-production.product.finishedgoodsflag|AW-CAT-C-production.product.finishedgoodsflag|AW中文目录列说明|production.product.finishedgoodsflag|
|d3:AW-CAT-C-production.product.color|AW-CAT-C-production.product.color|AW中文目录列说明|production.product.color|
|d3:AW-CAT-C-production.product.safetystocklevel|AW-CAT-C-production.product.safetystocklevel|AW中文目录列说明|production.product.safetystocklevel|
|d3:AW-CAT-C-production.product.reorderpoint|AW-CAT-C-production.product.reorderpoint|AW中文目录列说明|production.product.reorderpoint|
|d3:AW-CAT-C-production.product.standardcost|AW-CAT-C-production.product.standardcost|AW中文目录列说明|production.product.standardcost|
|d3:AW-CAT-C-production.product.listprice|AW-CAT-C-production.product.listprice|AW中文目录列说明|production.product.listprice|
|d3:AW-CAT-C-production.product.size|AW-CAT-C-production.product.size|AW中文目录列说明|production.product.size|
|d3:AW-CAT-C-production.product.sizeunitmeasurecode|AW-CAT-C-production.product.sizeunitmeasurecode|AW中文目录列说明|production.product.sizeunitmeasurecode|
|d3:AW-CAT-C-production.product.weightunitmeasurecode|AW-CAT-C-production.product.weightunitmeasurecode|AW中文目录列说明|production.product.weightunitmeasurecode|
|d3:AW-CAT-C-production.product.weight|AW-CAT-C-production.product.weight|AW中文目录列说明|production.product.weight|
|d3:AW-CAT-C-production.product.daystomanufacture|AW-CAT-C-production.product.daystomanufacture|AW中文目录列说明|production.product.daystomanufacture|
|d3:AW-CAT-C-production.product.productline|AW-CAT-C-production.product.productline|AW中文目录列说明|production.product.productline|
|d3:AW-CAT-C-production.product.class|AW-CAT-C-production.product.class|AW中文目录列说明|production.product.class|
|d3:AW-CAT-C-production.product.style|AW-CAT-C-production.product.style|AW中文目录列说明|production.product.style|
|d3:AW-CAT-C-production.product.productsubcategoryid|AW-CAT-C-production.product.productsubcategoryid|AW中文目录列说明|production.product.productsubcategoryid|
|d3:AW-CAT-C-production.product.productmodelid|AW-CAT-C-production.product.productmodelid|AW中文目录列说明|production.product.productmodelid|
|d3:AW-CAT-C-production.product.sellstartdate|AW-CAT-C-production.product.sellstartdate|AW中文目录列说明|production.product.sellstartdate|
|d3:AW-CAT-C-production.product.sellenddate|AW-CAT-C-production.product.sellenddate|AW中文目录列说明|production.product.sellenddate|
|d3:AW-CAT-C-production.product.discontinueddate|AW-CAT-C-production.product.discontinueddate|AW中文目录列说明|production.product.discontinueddate|
|d3:AW-CAT-C-production.product.rowguid|AW-CAT-C-production.product.rowguid|AW中文目录列说明|production.product.rowguid|
|d3:AW-CAT-C-production.product.modifieddate|AW-CAT-C-production.product.modifieddate|AW中文目录列说明|production.product.modifieddate|
|d3:AW-CAT-T-production.productcategory|AW-CAT-T-production.productcategory|AW中文目录表说明|production.productcategory|
|d3:AW-CAT-C-production.productcategory.productcategoryid|AW-CAT-C-production.productcategory.productcategoryid|AW中文目录列说明|production.productcategory.productcategoryid|
|d3:AW-CAT-C-production.productcategory.name|AW-CAT-C-production.productcategory.name|AW中文目录列说明|production.productcategory.name|
|d3:AW-CAT-C-production.productcategory.rowguid|AW-CAT-C-production.productcategory.rowguid|AW中文目录列说明|production.productcategory.rowguid|
|d3:AW-CAT-C-production.productcategory.modifieddate|AW-CAT-C-production.productcategory.modifieddate|AW中文目录列说明|production.productcategory.modifieddate|
|d3:AW-CAT-T-production.productcosthistory|AW-CAT-T-production.productcosthistory|AW中文目录表说明|production.productcosthistory|
|d3:AW-CAT-C-production.productcosthistory.productid|AW-CAT-C-production.productcosthistory.productid|AW中文目录列说明|production.productcosthistory.productid|
|d3:AW-CAT-C-production.productcosthistory.startdate|AW-CAT-C-production.productcosthistory.startdate|AW中文目录列说明|production.productcosthistory.startdate|
|d3:AW-CAT-C-production.productcosthistory.enddate|AW-CAT-C-production.productcosthistory.enddate|AW中文目录列说明|production.productcosthistory.enddate|
|d3:AW-CAT-C-production.productcosthistory.standardcost|AW-CAT-C-production.productcosthistory.standardcost|AW中文目录列说明|production.productcosthistory.standardcost|
|d3:AW-CAT-C-production.productcosthistory.modifieddate|AW-CAT-C-production.productcosthistory.modifieddate|AW中文目录列说明|production.productcosthistory.modifieddate|
|d3:AW-CAT-T-production.productdescription|AW-CAT-T-production.productdescription|AW中文目录表说明|production.productdescription|
|d3:AW-CAT-C-production.productdescription.productdescriptionid|AW-CAT-C-production.productdescription.productdescriptionid|AW中文目录列说明|production.productdescription.productdescriptionid|
|d3:AW-CAT-C-production.productdescription.description|AW-CAT-C-production.productdescription.description|AW中文目录列说明|production.productdescription.description|
|d3:AW-CAT-C-production.productdescription.rowguid|AW-CAT-C-production.productdescription.rowguid|AW中文目录列说明|production.productdescription.rowguid|
|d3:AW-CAT-C-production.productdescription.modifieddate|AW-CAT-C-production.productdescription.modifieddate|AW中文目录列说明|production.productdescription.modifieddate|
|d3:AW-CAT-T-production.productdocument|AW-CAT-T-production.productdocument|AW中文目录表说明|production.productdocument|
|d3:AW-CAT-C-production.productdocument.productid|AW-CAT-C-production.productdocument.productid|AW中文目录列说明|production.productdocument.productid|
|d3:AW-CAT-C-production.productdocument.modifieddate|AW-CAT-C-production.productdocument.modifieddate|AW中文目录列说明|production.productdocument.modifieddate|
|d3:AW-CAT-C-production.productdocument.documentnode|AW-CAT-C-production.productdocument.documentnode|AW中文目录列说明|production.productdocument.documentnode|
|d3:AW-CAT-T-production.productinventory|AW-CAT-T-production.productinventory|AW中文目录表说明|production.productinventory|
|d3:AW-CAT-C-production.productinventory.productid|AW-CAT-C-production.productinventory.productid|AW中文目录列说明|production.productinventory.productid|
|d3:AW-CAT-C-production.productinventory.locationid|AW-CAT-C-production.productinventory.locationid|AW中文目录列说明|production.productinventory.locationid|
|d3:AW-CAT-C-production.productinventory.shelf|AW-CAT-C-production.productinventory.shelf|AW中文目录列说明|production.productinventory.shelf|
|d3:AW-CAT-C-production.productinventory.bin|AW-CAT-C-production.productinventory.bin|AW中文目录列说明|production.productinventory.bin|
|d3:AW-CAT-C-production.productinventory.quantity|AW-CAT-C-production.productinventory.quantity|AW中文目录列说明|production.productinventory.quantity|
|d3:AW-CAT-C-production.productinventory.rowguid|AW-CAT-C-production.productinventory.rowguid|AW中文目录列说明|production.productinventory.rowguid|
|d3:AW-CAT-C-production.productinventory.modifieddate|AW-CAT-C-production.productinventory.modifieddate|AW中文目录列说明|production.productinventory.modifieddate|
|d3:AW-CAT-T-production.productlistpricehistory|AW-CAT-T-production.productlistpricehistory|AW中文目录表说明|production.productlistpricehistory|
|d3:AW-CAT-C-production.productlistpricehistory.productid|AW-CAT-C-production.productlistpricehistory.productid|AW中文目录列说明|production.productlistpricehistory.productid|
|d3:AW-CAT-C-production.productlistpricehistory.startdate|AW-CAT-C-production.productlistpricehistory.startdate|AW中文目录列说明|production.productlistpricehistory.startdate|
|d3:AW-CAT-C-production.productlistpricehistory.enddate|AW-CAT-C-production.productlistpricehistory.enddate|AW中文目录列说明|production.productlistpricehistory.enddate|
|d3:AW-CAT-C-production.productlistpricehistory.listprice|AW-CAT-C-production.productlistpricehistory.listprice|AW中文目录列说明|production.productlistpricehistory.listprice|
|d3:AW-CAT-C-production.productlistpricehistory.modifieddate|AW-CAT-C-production.productlistpricehistory.modifieddate|AW中文目录列说明|production.productlistpricehistory.modifieddate|
|d3:AW-CAT-T-production.productmodel|AW-CAT-T-production.productmodel|AW中文目录表说明|production.productmodel|
|d3:AW-CAT-C-production.productmodel.productmodelid|AW-CAT-C-production.productmodel.productmodelid|AW中文目录列说明|production.productmodel.productmodelid|
|d3:AW-CAT-C-production.productmodel.name|AW-CAT-C-production.productmodel.name|AW中文目录列说明|production.productmodel.name|
|d3:AW-CAT-C-production.productmodel.catalogdescription|AW-CAT-C-production.productmodel.catalogdescription|AW中文目录列说明|production.productmodel.catalogdescription|
|d3:AW-CAT-C-production.productmodel.instructions|AW-CAT-C-production.productmodel.instructions|AW中文目录列说明|production.productmodel.instructions|
|d3:AW-CAT-C-production.productmodel.rowguid|AW-CAT-C-production.productmodel.rowguid|AW中文目录列说明|production.productmodel.rowguid|
|d3:AW-CAT-C-production.productmodel.modifieddate|AW-CAT-C-production.productmodel.modifieddate|AW中文目录列说明|production.productmodel.modifieddate|
|d3:AW-CAT-T-production.productmodelillustration|AW-CAT-T-production.productmodelillustration|AW中文目录表说明|production.productmodelillustration|
|d3:AW-CAT-C-production.productmodelillustration.productmodelid|AW-CAT-C-production.productmodelillustration.productmodelid|AW中文目录列说明|production.productmodelillustration.productmodelid|
|d3:AW-CAT-C-production.productmodelillustration.illustrationid|AW-CAT-C-production.productmodelillustration.illustrationid|AW中文目录列说明|production.productmodelillustration.illustrationid|
|d3:AW-CAT-C-production.productmodelillustration.modifieddate|AW-CAT-C-production.productmodelillustration.modifieddate|AW中文目录列说明|production.productmodelillustration.modifieddate|
|d3:AW-CAT-T-production.productmodelproductdescriptionculture|AW-CAT-T-production.productmodelproductdescriptionculture|AW中文目录表说明|production.productmodelproductdescriptionculture|
|d3:AW-CAT-C-production.productmodelproductdescriptionculture.productmodelid|AW-CAT-C-production.productmodelproductdescriptionculture.productmodelid|AW中文目录列说明|production.productmodelproductdescriptionculture.productmodelid|
|d3:AW-CAT-C-production.productmodelproductdescriptionculture.productdescriptionid|AW-CAT-C-production.productmodelproductdescriptionculture.productdescriptionid|AW中文目录列说明|production.productmodelproductdescriptionculture.productdescriptionid|
|d3:AW-CAT-C-production.productmodelproductdescriptionculture.cultureid|AW-CAT-C-production.productmodelproductdescriptionculture.cultureid|AW中文目录列说明|production.productmodelproductdescriptionculture.cultureid|
|d3:AW-CAT-C-production.productmodelproductdescriptionculture.modifieddate|AW-CAT-C-production.productmodelproductdescriptionculture.modifieddate|AW中文目录列说明|production.productmodelproductdescriptionculture.modifieddate|
|d3:AW-CAT-T-production.productphoto|AW-CAT-T-production.productphoto|AW中文目录表说明|production.productphoto|
|d3:AW-CAT-C-production.productphoto.productphotoid|AW-CAT-C-production.productphoto.productphotoid|AW中文目录列说明|production.productphoto.productphotoid|
|d3:AW-CAT-C-production.productphoto.thumbnailphoto|AW-CAT-C-production.productphoto.thumbnailphoto|AW中文目录列说明|production.productphoto.thumbnailphoto|
|d3:AW-CAT-C-production.productphoto.thumbnailphotofilename|AW-CAT-C-production.productphoto.thumbnailphotofilename|AW中文目录列说明|production.productphoto.thumbnailphotofilename|
|d3:AW-CAT-C-production.productphoto.largephoto|AW-CAT-C-production.productphoto.largephoto|AW中文目录列说明|production.productphoto.largephoto|
|d3:AW-CAT-C-production.productphoto.largephotofilename|AW-CAT-C-production.productphoto.largephotofilename|AW中文目录列说明|production.productphoto.largephotofilename|
|d3:AW-CAT-C-production.productphoto.modifieddate|AW-CAT-C-production.productphoto.modifieddate|AW中文目录列说明|production.productphoto.modifieddate|
|d3:AW-CAT-T-production.productproductphoto|AW-CAT-T-production.productproductphoto|AW中文目录表说明|production.productproductphoto|
|d3:AW-CAT-C-production.productproductphoto.productid|AW-CAT-C-production.productproductphoto.productid|AW中文目录列说明|production.productproductphoto.productid|
|d3:AW-CAT-C-production.productproductphoto.productphotoid|AW-CAT-C-production.productproductphoto.productphotoid|AW中文目录列说明|production.productproductphoto.productphotoid|
|d3:AW-CAT-C-production.productproductphoto.primary|AW-CAT-C-production.productproductphoto.primary|AW中文目录列说明|production.productproductphoto.primary|
|d3:AW-CAT-C-production.productproductphoto.modifieddate|AW-CAT-C-production.productproductphoto.modifieddate|AW中文目录列说明|production.productproductphoto.modifieddate|
|d3:AW-CAT-T-production.productreview|AW-CAT-T-production.productreview|AW中文目录表说明|production.productreview|
|d3:AW-CAT-C-production.productreview.productreviewid|AW-CAT-C-production.productreview.productreviewid|AW中文目录列说明|production.productreview.productreviewid|
|d3:AW-CAT-C-production.productreview.productid|AW-CAT-C-production.productreview.productid|AW中文目录列说明|production.productreview.productid|
|d3:AW-CAT-C-production.productreview.reviewername|AW-CAT-C-production.productreview.reviewername|AW中文目录列说明|production.productreview.reviewername|
|d3:AW-CAT-C-production.productreview.reviewdate|AW-CAT-C-production.productreview.reviewdate|AW中文目录列说明|production.productreview.reviewdate|
|d3:AW-CAT-C-production.productreview.emailaddress|AW-CAT-C-production.productreview.emailaddress|AW中文目录列说明|production.productreview.emailaddress|
|d3:AW-CAT-C-production.productreview.rating|AW-CAT-C-production.productreview.rating|AW中文目录列说明|production.productreview.rating|
|d3:AW-CAT-C-production.productreview.comments|AW-CAT-C-production.productreview.comments|AW中文目录列说明|production.productreview.comments|
|d3:AW-CAT-C-production.productreview.modifieddate|AW-CAT-C-production.productreview.modifieddate|AW中文目录列说明|production.productreview.modifieddate|
|d3:AW-CAT-T-production.productsubcategory|AW-CAT-T-production.productsubcategory|AW中文目录表说明|production.productsubcategory|
|d3:AW-CAT-C-production.productsubcategory.productsubcategoryid|AW-CAT-C-production.productsubcategory.productsubcategoryid|AW中文目录列说明|production.productsubcategory.productsubcategoryid|
|d3:AW-CAT-C-production.productsubcategory.productcategoryid|AW-CAT-C-production.productsubcategory.productcategoryid|AW中文目录列说明|production.productsubcategory.productcategoryid|
|d3:AW-CAT-C-production.productsubcategory.name|AW-CAT-C-production.productsubcategory.name|AW中文目录列说明|production.productsubcategory.name|
|d3:AW-CAT-C-production.productsubcategory.rowguid|AW-CAT-C-production.productsubcategory.rowguid|AW中文目录列说明|production.productsubcategory.rowguid|
|d3:AW-CAT-C-production.productsubcategory.modifieddate|AW-CAT-C-production.productsubcategory.modifieddate|AW中文目录列说明|production.productsubcategory.modifieddate|
|d3:AW-CAT-T-production.scrapreason|AW-CAT-T-production.scrapreason|AW中文目录表说明|production.scrapreason|
|d3:AW-CAT-C-production.scrapreason.scrapreasonid|AW-CAT-C-production.scrapreason.scrapreasonid|AW中文目录列说明|production.scrapreason.scrapreasonid|
|d3:AW-CAT-C-production.scrapreason.name|AW-CAT-C-production.scrapreason.name|AW中文目录列说明|production.scrapreason.name|
|d3:AW-CAT-C-production.scrapreason.modifieddate|AW-CAT-C-production.scrapreason.modifieddate|AW中文目录列说明|production.scrapreason.modifieddate|
|d3:AW-CAT-T-production.transactionhistory|AW-CAT-T-production.transactionhistory|AW中文目录表说明|production.transactionhistory|
|d3:AW-CAT-C-production.transactionhistory.transactionid|AW-CAT-C-production.transactionhistory.transactionid|AW中文目录列说明|production.transactionhistory.transactionid|
|d3:AW-CAT-C-production.transactionhistory.productid|AW-CAT-C-production.transactionhistory.productid|AW中文目录列说明|production.transactionhistory.productid|
|d3:AW-CAT-C-production.transactionhistory.referenceorderid|AW-CAT-C-production.transactionhistory.referenceorderid|AW中文目录列说明|production.transactionhistory.referenceorderid|
|d3:AW-CAT-C-production.transactionhistory.referenceorderlineid|AW-CAT-C-production.transactionhistory.referenceorderlineid|AW中文目录列说明|production.transactionhistory.referenceorderlineid|
|d3:AW-CAT-C-production.transactionhistory.transactiondate|AW-CAT-C-production.transactionhistory.transactiondate|AW中文目录列说明|production.transactionhistory.transactiondate|
|d3:AW-CAT-C-production.transactionhistory.transactiontype|AW-CAT-C-production.transactionhistory.transactiontype|AW中文目录列说明|production.transactionhistory.transactiontype|
|d3:AW-CAT-C-production.transactionhistory.quantity|AW-CAT-C-production.transactionhistory.quantity|AW中文目录列说明|production.transactionhistory.quantity|
|d3:AW-CAT-C-production.transactionhistory.actualcost|AW-CAT-C-production.transactionhistory.actualcost|AW中文目录列说明|production.transactionhistory.actualcost|
|d3:AW-CAT-C-production.transactionhistory.modifieddate|AW-CAT-C-production.transactionhistory.modifieddate|AW中文目录列说明|production.transactionhistory.modifieddate|
|d3:AW-CAT-C-production.transactionhistoryarchive.transactionid|AW-CAT-C-production.transactionhistoryarchive.transactionid|AW中文目录列说明|production.transactionhistoryarchive.transactionid|
|d3:AW-CAT-C-production.transactionhistoryarchive.productid|AW-CAT-C-production.transactionhistoryarchive.productid|AW中文目录列说明|production.transactionhistoryarchive.productid|
|d3:AW-CAT-C-production.transactionhistoryarchive.referenceorderid|AW-CAT-C-production.transactionhistoryarchive.referenceorderid|AW中文目录列说明|production.transactionhistoryarchive.referenceorderid|
|d3:AW-CAT-C-production.transactionhistoryarchive.referenceorderlineid|AW-CAT-C-production.transactionhistoryarchive.referenceorderlineid|AW中文目录列说明|production.transactionhistoryarchive.referenceorderlineid|
|d3:AW-CAT-C-production.transactionhistoryarchive.transactiondate|AW-CAT-C-production.transactionhistoryarchive.transactiondate|AW中文目录列说明|production.transactionhistoryarchive.transactiondate|
|d3:AW-CAT-C-production.transactionhistoryarchive.quantity|AW-CAT-C-production.transactionhistoryarchive.quantity|AW中文目录列说明|production.transactionhistoryarchive.quantity|
|d3:AW-CAT-C-production.transactionhistoryarchive.modifieddate|AW-CAT-C-production.transactionhistoryarchive.modifieddate|AW中文目录列说明|production.transactionhistoryarchive.modifieddate|
|d3:AW-CAT-T-production.unitmeasure|AW-CAT-T-production.unitmeasure|AW中文目录表说明|production.unitmeasure|
|d3:AW-CAT-C-production.unitmeasure.unitmeasurecode|AW-CAT-C-production.unitmeasure.unitmeasurecode|AW中文目录列说明|production.unitmeasure.unitmeasurecode|
|d3:AW-CAT-C-production.unitmeasure.name|AW-CAT-C-production.unitmeasure.name|AW中文目录列说明|production.unitmeasure.name|
|d3:AW-CAT-C-production.unitmeasure.modifieddate|AW-CAT-C-production.unitmeasure.modifieddate|AW中文目录列说明|production.unitmeasure.modifieddate|
|d3:AW-CAT-T-production.workorder|AW-CAT-T-production.workorder|AW中文目录表说明|production.workorder|
|d3:AW-CAT-C-production.workorder.workorderid|AW-CAT-C-production.workorder.workorderid|AW中文目录列说明|production.workorder.workorderid|
|d3:AW-CAT-C-production.workorder.productid|AW-CAT-C-production.workorder.productid|AW中文目录列说明|production.workorder.productid|
|d3:AW-CAT-C-production.workorder.orderqty|AW-CAT-C-production.workorder.orderqty|AW中文目录列说明|production.workorder.orderqty|
|d3:AW-CAT-C-production.workorder.scrappedqty|AW-CAT-C-production.workorder.scrappedqty|AW中文目录列说明|production.workorder.scrappedqty|
|d3:AW-CAT-C-production.workorder.startdate|AW-CAT-C-production.workorder.startdate|AW中文目录列说明|production.workorder.startdate|
|d3:AW-CAT-C-production.workorder.enddate|AW-CAT-C-production.workorder.enddate|AW中文目录列说明|production.workorder.enddate|
|d3:AW-CAT-C-production.workorder.duedate|AW-CAT-C-production.workorder.duedate|AW中文目录列说明|production.workorder.duedate|
|d3:AW-CAT-C-production.workorder.scrapreasonid|AW-CAT-C-production.workorder.scrapreasonid|AW中文目录列说明|production.workorder.scrapreasonid|
|d3:AW-CAT-C-production.workorder.modifieddate|AW-CAT-C-production.workorder.modifieddate|AW中文目录列说明|production.workorder.modifieddate|
|d3:AW-CAT-T-production.workorderrouting|AW-CAT-T-production.workorderrouting|AW中文目录表说明|production.workorderrouting|
|d3:AW-CAT-C-production.workorderrouting.workorderid|AW-CAT-C-production.workorderrouting.workorderid|AW中文目录列说明|production.workorderrouting.workorderid|
|d3:AW-CAT-C-production.workorderrouting.productid|AW-CAT-C-production.workorderrouting.productid|AW中文目录列说明|production.workorderrouting.productid|
|d3:AW-CAT-C-production.workorderrouting.operationsequence|AW-CAT-C-production.workorderrouting.operationsequence|AW中文目录列说明|production.workorderrouting.operationsequence|
|d3:AW-CAT-C-production.workorderrouting.locationid|AW-CAT-C-production.workorderrouting.locationid|AW中文目录列说明|production.workorderrouting.locationid|
|d3:AW-CAT-C-production.workorderrouting.scheduledstartdate|AW-CAT-C-production.workorderrouting.scheduledstartdate|AW中文目录列说明|production.workorderrouting.scheduledstartdate|
|d3:AW-CAT-C-production.workorderrouting.scheduledenddate|AW-CAT-C-production.workorderrouting.scheduledenddate|AW中文目录列说明|production.workorderrouting.scheduledenddate|
|d3:AW-CAT-C-production.workorderrouting.actualstartdate|AW-CAT-C-production.workorderrouting.actualstartdate|AW中文目录列说明|production.workorderrouting.actualstartdate|
|d3:AW-CAT-C-production.workorderrouting.actualenddate|AW-CAT-C-production.workorderrouting.actualenddate|AW中文目录列说明|production.workorderrouting.actualenddate|
|d3:AW-CAT-C-production.workorderrouting.modifieddate|AW-CAT-C-production.workorderrouting.modifieddate|AW中文目录列说明|production.workorderrouting.modifieddate|
|d3:AW-CAT-T-purchasing.productvendor|AW-CAT-T-purchasing.productvendor|AW中文目录表说明|purchasing.productvendor|
|d3:AW-CAT-C-purchasing.productvendor.productid|AW-CAT-C-purchasing.productvendor.productid|AW中文目录列说明|purchasing.productvendor.productid|
|d3:AW-CAT-C-purchasing.productvendor.businessentityid|AW-CAT-C-purchasing.productvendor.businessentityid|AW中文目录列说明|purchasing.productvendor.businessentityid|
|d3:AW-CAT-C-purchasing.productvendor.lastreceiptdate|AW-CAT-C-purchasing.productvendor.lastreceiptdate|AW中文目录列说明|purchasing.productvendor.lastreceiptdate|
|d3:AW-CAT-C-purchasing.productvendor.minorderqty|AW-CAT-C-purchasing.productvendor.minorderqty|AW中文目录列说明|purchasing.productvendor.minorderqty|
|d3:AW-CAT-C-purchasing.productvendor.maxorderqty|AW-CAT-C-purchasing.productvendor.maxorderqty|AW中文目录列说明|purchasing.productvendor.maxorderqty|
|d3:AW-CAT-C-purchasing.productvendor.onorderqty|AW-CAT-C-purchasing.productvendor.onorderqty|AW中文目录列说明|purchasing.productvendor.onorderqty|
|d3:AW-CAT-C-purchasing.productvendor.unitmeasurecode|AW-CAT-C-purchasing.productvendor.unitmeasurecode|AW中文目录列说明|purchasing.productvendor.unitmeasurecode|
|d3:AW-CAT-C-purchasing.productvendor.modifieddate|AW-CAT-C-purchasing.productvendor.modifieddate|AW中文目录列说明|purchasing.productvendor.modifieddate|
|d3:AW-CAT-T-purchasing.purchaseorderdetail|AW-CAT-T-purchasing.purchaseorderdetail|AW中文目录表说明|purchasing.purchaseorderdetail|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.purchaseorderid|AW-CAT-C-purchasing.purchaseorderdetail.purchaseorderid|AW中文目录列说明|purchasing.purchaseorderdetail.purchaseorderid|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.purchaseorderdetailid|AW-CAT-C-purchasing.purchaseorderdetail.purchaseorderdetailid|AW中文目录列说明|purchasing.purchaseorderdetail.purchaseorderdetailid|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.duedate|AW-CAT-C-purchasing.purchaseorderdetail.duedate|AW中文目录列说明|purchasing.purchaseorderdetail.duedate|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.orderqty|AW-CAT-C-purchasing.purchaseorderdetail.orderqty|AW中文目录列说明|purchasing.purchaseorderdetail.orderqty|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.productid|AW-CAT-C-purchasing.purchaseorderdetail.productid|AW中文目录列说明|purchasing.purchaseorderdetail.productid|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.receivedqty|AW-CAT-C-purchasing.purchaseorderdetail.receivedqty|AW中文目录列说明|purchasing.purchaseorderdetail.receivedqty|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.rejectedqty|AW-CAT-C-purchasing.purchaseorderdetail.rejectedqty|AW中文目录列说明|purchasing.purchaseorderdetail.rejectedqty|
|d3:AW-CAT-C-purchasing.purchaseorderdetail.modifieddate|AW-CAT-C-purchasing.purchaseorderdetail.modifieddate|AW中文目录列说明|purchasing.purchaseorderdetail.modifieddate|
|d3:AW-CAT-C-purchasing.purchaseorderheader.purchaseorderid|AW-CAT-C-purchasing.purchaseorderheader.purchaseorderid|AW中文目录列说明|purchasing.purchaseorderheader.purchaseorderid|
|d3:AW-CAT-C-purchasing.purchaseorderheader.revisionnumber|AW-CAT-C-purchasing.purchaseorderheader.revisionnumber|AW中文目录列说明|purchasing.purchaseorderheader.revisionnumber|
|d3:AW-CAT-C-purchasing.purchaseorderheader.employeeid|AW-CAT-C-purchasing.purchaseorderheader.employeeid|AW中文目录列说明|purchasing.purchaseorderheader.employeeid|
|d3:AW-CAT-C-purchasing.purchaseorderheader.vendorid|AW-CAT-C-purchasing.purchaseorderheader.vendorid|AW中文目录列说明|purchasing.purchaseorderheader.vendorid|
|d3:AW-CAT-C-purchasing.purchaseorderheader.shipmethodid|AW-CAT-C-purchasing.purchaseorderheader.shipmethodid|AW中文目录列说明|purchasing.purchaseorderheader.shipmethodid|
|d3:AW-CAT-C-purchasing.purchaseorderheader.orderdate|AW-CAT-C-purchasing.purchaseorderheader.orderdate|AW中文目录列说明|purchasing.purchaseorderheader.orderdate|
|d3:AW-CAT-C-purchasing.purchaseorderheader.shipdate|AW-CAT-C-purchasing.purchaseorderheader.shipdate|AW中文目录列说明|purchasing.purchaseorderheader.shipdate|
|d3:AW-CAT-C-purchasing.purchaseorderheader.modifieddate|AW-CAT-C-purchasing.purchaseorderheader.modifieddate|AW中文目录列说明|purchasing.purchaseorderheader.modifieddate|
|d3:AW-CAT-C-purchasing.shipmethod.shipmethodid|AW-CAT-C-purchasing.shipmethod.shipmethodid|AW中文目录列说明|purchasing.shipmethod.shipmethodid|
|d3:AW-CAT-C-purchasing.shipmethod.name|AW-CAT-C-purchasing.shipmethod.name|AW中文目录列说明|purchasing.shipmethod.name|
|d3:AW-CAT-C-purchasing.shipmethod.rowguid|AW-CAT-C-purchasing.shipmethod.rowguid|AW中文目录列说明|purchasing.shipmethod.rowguid|
|d3:AW-CAT-C-purchasing.shipmethod.modifieddate|AW-CAT-C-purchasing.shipmethod.modifieddate|AW中文目录列说明|purchasing.shipmethod.modifieddate|
|d3:AW-CAT-T-purchasing.vendor|AW-CAT-T-purchasing.vendor|AW中文目录表说明|purchasing.vendor|
|d3:AW-CAT-C-purchasing.vendor.businessentityid|AW-CAT-C-purchasing.vendor.businessentityid|AW中文目录列说明|purchasing.vendor.businessentityid|
|d3:AW-CAT-C-purchasing.vendor.accountnumber|AW-CAT-C-purchasing.vendor.accountnumber|AW中文目录列说明|purchasing.vendor.accountnumber|
|d3:AW-CAT-C-purchasing.vendor.name|AW-CAT-C-purchasing.vendor.name|AW中文目录列说明|purchasing.vendor.name|
|d3:AW-CAT-C-purchasing.vendor.creditrating|AW-CAT-C-purchasing.vendor.creditrating|AW中文目录列说明|purchasing.vendor.creditrating|
|d3:AW-CAT-C-purchasing.vendor.preferredvendorstatus|AW-CAT-C-purchasing.vendor.preferredvendorstatus|AW中文目录列说明|purchasing.vendor.preferredvendorstatus|
|d3:AW-CAT-C-purchasing.vendor.activeflag|AW-CAT-C-purchasing.vendor.activeflag|AW中文目录列说明|purchasing.vendor.activeflag|
|d3:AW-CAT-C-purchasing.vendor.purchasingwebserviceurl|AW-CAT-C-purchasing.vendor.purchasingwebserviceurl|AW中文目录列说明|purchasing.vendor.purchasingwebserviceurl|
|d3:AW-CAT-C-purchasing.vendor.modifieddate|AW-CAT-C-purchasing.vendor.modifieddate|AW中文目录列说明|purchasing.vendor.modifieddate|
|d3:AW-CAT-T-sales.countryregioncurrency|AW-CAT-T-sales.countryregioncurrency|AW中文目录表说明|sales.countryregioncurrency|
|d3:AW-CAT-C-sales.countryregioncurrency.countryregioncode|AW-CAT-C-sales.countryregioncurrency.countryregioncode|AW中文目录列说明|sales.countryregioncurrency.countryregioncode|
|d3:AW-CAT-C-sales.countryregioncurrency.currencycode|AW-CAT-C-sales.countryregioncurrency.currencycode|AW中文目录列说明|sales.countryregioncurrency.currencycode|
|d3:AW-CAT-C-sales.countryregioncurrency.modifieddate|AW-CAT-C-sales.countryregioncurrency.modifieddate|AW中文目录列说明|sales.countryregioncurrency.modifieddate|
|d3:AW-CAT-T-sales.creditcard|AW-CAT-T-sales.creditcard|AW中文目录表说明|sales.creditcard|
|d3:AW-CAT-C-sales.creditcard.creditcardid|AW-CAT-C-sales.creditcard.creditcardid|AW中文目录列说明|sales.creditcard.creditcardid|
|d3:AW-CAT-C-sales.creditcard.cardtype|AW-CAT-C-sales.creditcard.cardtype|AW中文目录列说明|sales.creditcard.cardtype|
|d3:AW-CAT-C-sales.creditcard.cardnumber|AW-CAT-C-sales.creditcard.cardnumber|AW中文目录列说明|sales.creditcard.cardnumber|
|d3:AW-CAT-C-sales.creditcard.expmonth|AW-CAT-C-sales.creditcard.expmonth|AW中文目录列说明|sales.creditcard.expmonth|
|d3:AW-CAT-C-sales.creditcard.expyear|AW-CAT-C-sales.creditcard.expyear|AW中文目录列说明|sales.creditcard.expyear|
|d3:AW-CAT-C-sales.creditcard.modifieddate|AW-CAT-C-sales.creditcard.modifieddate|AW中文目录列说明|sales.creditcard.modifieddate|
|d3:AW-CAT-T-sales.currency|AW-CAT-T-sales.currency|AW中文目录表说明|sales.currency|
|d3:AW-CAT-C-sales.currency.currencycode|AW-CAT-C-sales.currency.currencycode|AW中文目录列说明|sales.currency.currencycode|
|d3:AW-CAT-C-sales.currency.name|AW-CAT-C-sales.currency.name|AW中文目录列说明|sales.currency.name|
|d3:AW-CAT-C-sales.currency.modifieddate|AW-CAT-C-sales.currency.modifieddate|AW中文目录列说明|sales.currency.modifieddate|
|d3:AW-CAT-T-sales.currencyrate|AW-CAT-T-sales.currencyrate|AW中文目录表说明|sales.currencyrate|
|d3:AW-CAT-C-sales.currencyrate.currencyrateid|AW-CAT-C-sales.currencyrate.currencyrateid|AW中文目录列说明|sales.currencyrate.currencyrateid|
|d3:AW-CAT-C-sales.currencyrate.currencyratedate|AW-CAT-C-sales.currencyrate.currencyratedate|AW中文目录列说明|sales.currencyrate.currencyratedate|
|d3:AW-CAT-C-sales.currencyrate.fromcurrencycode|AW-CAT-C-sales.currencyrate.fromcurrencycode|AW中文目录列说明|sales.currencyrate.fromcurrencycode|
|d3:AW-CAT-C-sales.currencyrate.tocurrencycode|AW-CAT-C-sales.currencyrate.tocurrencycode|AW中文目录列说明|sales.currencyrate.tocurrencycode|
|d3:AW-CAT-C-sales.currencyrate.averagerate|AW-CAT-C-sales.currencyrate.averagerate|AW中文目录列说明|sales.currencyrate.averagerate|
|d3:AW-CAT-C-sales.currencyrate.endofdayrate|AW-CAT-C-sales.currencyrate.endofdayrate|AW中文目录列说明|sales.currencyrate.endofdayrate|
|d3:AW-CAT-C-sales.currencyrate.modifieddate|AW-CAT-C-sales.currencyrate.modifieddate|AW中文目录列说明|sales.currencyrate.modifieddate|
|d3:AW-CAT-T-sales.customer|AW-CAT-T-sales.customer|AW中文目录表说明|sales.customer|
|d3:AW-CAT-C-sales.customer.customerid|AW-CAT-C-sales.customer.customerid|AW中文目录列说明|sales.customer.customerid|
|d3:AW-CAT-C-sales.customer.personid|AW-CAT-C-sales.customer.personid|AW中文目录列说明|sales.customer.personid|
|d3:AW-CAT-C-sales.customer.storeid|AW-CAT-C-sales.customer.storeid|AW中文目录列说明|sales.customer.storeid|
|d3:AW-CAT-C-sales.customer.territoryid|AW-CAT-C-sales.customer.territoryid|AW中文目录列说明|sales.customer.territoryid|
|d3:AW-CAT-C-sales.customer.rowguid|AW-CAT-C-sales.customer.rowguid|AW中文目录列说明|sales.customer.rowguid|
|d3:AW-CAT-C-sales.customer.modifieddate|AW-CAT-C-sales.customer.modifieddate|AW中文目录列说明|sales.customer.modifieddate|
|d3:AW-CAT-T-sales.personcreditcard|AW-CAT-T-sales.personcreditcard|AW中文目录表说明|sales.personcreditcard|
|d3:AW-CAT-C-sales.personcreditcard.businessentityid|AW-CAT-C-sales.personcreditcard.businessentityid|AW中文目录列说明|sales.personcreditcard.businessentityid|
|d3:AW-CAT-C-sales.personcreditcard.creditcardid|AW-CAT-C-sales.personcreditcard.creditcardid|AW中文目录列说明|sales.personcreditcard.creditcardid|
|d3:AW-CAT-C-sales.personcreditcard.modifieddate|AW-CAT-C-sales.personcreditcard.modifieddate|AW中文目录列说明|sales.personcreditcard.modifieddate|
|d3:AW-CAT-T-sales.salesorderdetail|AW-CAT-T-sales.salesorderdetail|AW中文目录表说明|sales.salesorderdetail|
|d3:AW-CAT-C-sales.salesorderdetail.salesorderid|AW-CAT-C-sales.salesorderdetail.salesorderid|AW中文目录列说明|sales.salesorderdetail.salesorderid|
|d3:AW-CAT-C-sales.salesorderdetail.salesorderdetailid|AW-CAT-C-sales.salesorderdetail.salesorderdetailid|AW中文目录列说明|sales.salesorderdetail.salesorderdetailid|
|d3:AW-CAT-C-sales.salesorderdetail.carriertrackingnumber|AW-CAT-C-sales.salesorderdetail.carriertrackingnumber|AW中文目录列说明|sales.salesorderdetail.carriertrackingnumber|
|d3:AW-CAT-C-sales.salesorderdetail.orderqty|AW-CAT-C-sales.salesorderdetail.orderqty|AW中文目录列说明|sales.salesorderdetail.orderqty|
|d3:AW-CAT-C-sales.salesorderdetail.productid|AW-CAT-C-sales.salesorderdetail.productid|AW中文目录列说明|sales.salesorderdetail.productid|
|d3:AW-CAT-C-sales.salesorderdetail.specialofferid|AW-CAT-C-sales.salesorderdetail.specialofferid|AW中文目录列说明|sales.salesorderdetail.specialofferid|
|d3:AW-CAT-C-sales.salesorderdetail.unitprice|AW-CAT-C-sales.salesorderdetail.unitprice|AW中文目录列说明|sales.salesorderdetail.unitprice|
|d3:AW-CAT-C-sales.salesorderdetail.unitpricediscount|AW-CAT-C-sales.salesorderdetail.unitpricediscount|AW中文目录列说明|sales.salesorderdetail.unitpricediscount|
|d3:AW-CAT-C-sales.salesorderdetail.rowguid|AW-CAT-C-sales.salesorderdetail.rowguid|AW中文目录列说明|sales.salesorderdetail.rowguid|
|d3:AW-CAT-C-sales.salesorderdetail.modifieddate|AW-CAT-C-sales.salesorderdetail.modifieddate|AW中文目录列说明|sales.salesorderdetail.modifieddate|
|d3:AW-CAT-T-sales.salesorderheader|AW-CAT-T-sales.salesorderheader|AW中文目录表说明|sales.salesorderheader|
|d3:AW-CAT-C-sales.salesorderheader.salesorderid|AW-CAT-C-sales.salesorderheader.salesorderid|AW中文目录列说明|sales.salesorderheader.salesorderid|
|d3:AW-CAT-C-sales.salesorderheader.revisionnumber|AW-CAT-C-sales.salesorderheader.revisionnumber|AW中文目录列说明|sales.salesorderheader.revisionnumber|
|d3:AW-CAT-C-sales.salesorderheader.orderdate|AW-CAT-C-sales.salesorderheader.orderdate|AW中文目录列说明|sales.salesorderheader.orderdate|
|d3:AW-CAT-C-sales.salesorderheader.duedate|AW-CAT-C-sales.salesorderheader.duedate|AW中文目录列说明|sales.salesorderheader.duedate|
|d3:AW-CAT-C-sales.salesorderheader.shipdate|AW-CAT-C-sales.salesorderheader.shipdate|AW中文目录列说明|sales.salesorderheader.shipdate|
|d3:AW-CAT-C-sales.salesorderheader.status|AW-CAT-C-sales.salesorderheader.status|AW中文目录列说明|sales.salesorderheader.status|
|d3:AW-CAT-C-sales.salesorderheader.onlineorderflag|AW-CAT-C-sales.salesorderheader.onlineorderflag|AW中文目录列说明|sales.salesorderheader.onlineorderflag|
|d3:AW-CAT-C-sales.salesorderheader.purchaseordernumber|AW-CAT-C-sales.salesorderheader.purchaseordernumber|AW中文目录列说明|sales.salesorderheader.purchaseordernumber|
|d3:AW-CAT-C-sales.salesorderheader.accountnumber|AW-CAT-C-sales.salesorderheader.accountnumber|AW中文目录列说明|sales.salesorderheader.accountnumber|
|d3:AW-CAT-C-sales.salesorderheader.customerid|AW-CAT-C-sales.salesorderheader.customerid|AW中文目录列说明|sales.salesorderheader.customerid|
|d3:AW-CAT-C-sales.salesorderheader.salespersonid|AW-CAT-C-sales.salesorderheader.salespersonid|AW中文目录列说明|sales.salesorderheader.salespersonid|
|d3:AW-CAT-C-sales.salesorderheader.territoryid|AW-CAT-C-sales.salesorderheader.territoryid|AW中文目录列说明|sales.salesorderheader.territoryid|
|d3:AW-CAT-C-sales.salesorderheader.billtoaddressid|AW-CAT-C-sales.salesorderheader.billtoaddressid|AW中文目录列说明|sales.salesorderheader.billtoaddressid|
|d3:AW-CAT-C-sales.salesorderheader.shiptoaddressid|AW-CAT-C-sales.salesorderheader.shiptoaddressid|AW中文目录列说明|sales.salesorderheader.shiptoaddressid|
|d3:AW-CAT-C-sales.salesorderheader.shipmethodid|AW-CAT-C-sales.salesorderheader.shipmethodid|AW中文目录列说明|sales.salesorderheader.shipmethodid|
|d3:AW-CAT-C-sales.salesorderheader.creditcardid|AW-CAT-C-sales.salesorderheader.creditcardid|AW中文目录列说明|sales.salesorderheader.creditcardid|
|d3:AW-CAT-C-sales.salesorderheader.creditcardapprovalcode|AW-CAT-C-sales.salesorderheader.creditcardapprovalcode|AW中文目录列说明|sales.salesorderheader.creditcardapprovalcode|
|d3:AW-CAT-C-sales.salesorderheader.currencyrateid|AW-CAT-C-sales.salesorderheader.currencyrateid|AW中文目录列说明|sales.salesorderheader.currencyrateid|
|d3:AW-CAT-C-sales.salesorderheader.subtotal|AW-CAT-C-sales.salesorderheader.subtotal|AW中文目录列说明|sales.salesorderheader.subtotal|
|d3:AW-CAT-C-sales.salesorderheader.taxamt|AW-CAT-C-sales.salesorderheader.taxamt|AW中文目录列说明|sales.salesorderheader.taxamt|
|d3:AW-CAT-C-sales.salesorderheader.freight|AW-CAT-C-sales.salesorderheader.freight|AW中文目录列说明|sales.salesorderheader.freight|
|d3:AW-CAT-C-sales.salesorderheader.totaldue|AW-CAT-C-sales.salesorderheader.totaldue|AW中文目录列说明|sales.salesorderheader.totaldue|
|d3:AW-CAT-C-sales.salesorderheader.comment|AW-CAT-C-sales.salesorderheader.comment|AW中文目录列说明|sales.salesorderheader.comment|
|d3:AW-CAT-C-sales.salesorderheader.rowguid|AW-CAT-C-sales.salesorderheader.rowguid|AW中文目录列说明|sales.salesorderheader.rowguid|
|d3:AW-CAT-C-sales.salesorderheader.modifieddate|AW-CAT-C-sales.salesorderheader.modifieddate|AW中文目录列说明|sales.salesorderheader.modifieddate|
|d3:AW-CAT-T-sales.salesorderheadersalesreason|AW-CAT-T-sales.salesorderheadersalesreason|AW中文目录表说明|sales.salesorderheadersalesreason|
|d3:AW-CAT-C-sales.salesorderheadersalesreason.salesorderid|AW-CAT-C-sales.salesorderheadersalesreason.salesorderid|AW中文目录列说明|sales.salesorderheadersalesreason.salesorderid|
|d3:AW-CAT-C-sales.salesorderheadersalesreason.salesreasonid|AW-CAT-C-sales.salesorderheadersalesreason.salesreasonid|AW中文目录列说明|sales.salesorderheadersalesreason.salesreasonid|
|d3:AW-CAT-C-sales.salesorderheadersalesreason.modifieddate|AW-CAT-C-sales.salesorderheadersalesreason.modifieddate|AW中文目录列说明|sales.salesorderheadersalesreason.modifieddate|
|d3:AW-CAT-T-sales.salesperson|AW-CAT-T-sales.salesperson|AW中文目录表说明|sales.salesperson|
|d3:AW-CAT-C-sales.salesperson.businessentityid|AW-CAT-C-sales.salesperson.businessentityid|AW中文目录列说明|sales.salesperson.businessentityid|
|d3:AW-CAT-C-sales.salesperson.territoryid|AW-CAT-C-sales.salesperson.territoryid|AW中文目录列说明|sales.salesperson.territoryid|
|d3:AW-CAT-C-sales.salesperson.salesquota|AW-CAT-C-sales.salesperson.salesquota|AW中文目录列说明|sales.salesperson.salesquota|
|d3:AW-CAT-C-sales.salesperson.bonus|AW-CAT-C-sales.salesperson.bonus|AW中文目录列说明|sales.salesperson.bonus|
|d3:AW-CAT-C-sales.salesperson.commissionpct|AW-CAT-C-sales.salesperson.commissionpct|AW中文目录列说明|sales.salesperson.commissionpct|
|d3:AW-CAT-C-sales.salesperson.salesytd|AW-CAT-C-sales.salesperson.salesytd|AW中文目录列说明|sales.salesperson.salesytd|
|d3:AW-CAT-C-sales.salesperson.saleslastyear|AW-CAT-C-sales.salesperson.saleslastyear|AW中文目录列说明|sales.salesperson.saleslastyear|
|d3:AW-CAT-C-sales.salesperson.rowguid|AW-CAT-C-sales.salesperson.rowguid|AW中文目录列说明|sales.salesperson.rowguid|
|d3:AW-CAT-C-sales.salesperson.modifieddate|AW-CAT-C-sales.salesperson.modifieddate|AW中文目录列说明|sales.salesperson.modifieddate|
|d3:AW-CAT-T-sales.salespersonquotahistory|AW-CAT-T-sales.salespersonquotahistory|AW中文目录表说明|sales.salespersonquotahistory|
|d3:AW-CAT-C-sales.salespersonquotahistory.businessentityid|AW-CAT-C-sales.salespersonquotahistory.businessentityid|AW中文目录列说明|sales.salespersonquotahistory.businessentityid|
|d3:AW-CAT-C-sales.salespersonquotahistory.quotadate|AW-CAT-C-sales.salespersonquotahistory.quotadate|AW中文目录列说明|sales.salespersonquotahistory.quotadate|
|d3:AW-CAT-C-sales.salespersonquotahistory.salesquota|AW-CAT-C-sales.salespersonquotahistory.salesquota|AW中文目录列说明|sales.salespersonquotahistory.salesquota|
|d3:AW-CAT-C-sales.salespersonquotahistory.rowguid|AW-CAT-C-sales.salespersonquotahistory.rowguid|AW中文目录列说明|sales.salespersonquotahistory.rowguid|
|d3:AW-CAT-C-sales.salespersonquotahistory.modifieddate|AW-CAT-C-sales.salespersonquotahistory.modifieddate|AW中文目录列说明|sales.salespersonquotahistory.modifieddate|
|d3:AW-CAT-T-sales.salesreason|AW-CAT-T-sales.salesreason|AW中文目录表说明|sales.salesreason|
|d3:AW-CAT-C-sales.salesreason.salesreasonid|AW-CAT-C-sales.salesreason.salesreasonid|AW中文目录列说明|sales.salesreason.salesreasonid|
|d3:AW-CAT-C-sales.salesreason.name|AW-CAT-C-sales.salesreason.name|AW中文目录列说明|sales.salesreason.name|
|d3:AW-CAT-C-sales.salesreason.reasontype|AW-CAT-C-sales.salesreason.reasontype|AW中文目录列说明|sales.salesreason.reasontype|
|d3:AW-CAT-C-sales.salesreason.modifieddate|AW-CAT-C-sales.salesreason.modifieddate|AW中文目录列说明|sales.salesreason.modifieddate|
|d3:AW-CAT-T-sales.salestaxrate|AW-CAT-T-sales.salestaxrate|AW中文目录表说明|sales.salestaxrate|
|d3:AW-CAT-C-sales.salestaxrate.salestaxrateid|AW-CAT-C-sales.salestaxrate.salestaxrateid|AW中文目录列说明|sales.salestaxrate.salestaxrateid|
|d3:AW-CAT-C-sales.salestaxrate.stateprovinceid|AW-CAT-C-sales.salestaxrate.stateprovinceid|AW中文目录列说明|sales.salestaxrate.stateprovinceid|
|d3:AW-CAT-C-sales.salestaxrate.taxtype|AW-CAT-C-sales.salestaxrate.taxtype|AW中文目录列说明|sales.salestaxrate.taxtype|
|d3:AW-CAT-C-sales.salestaxrate.taxrate|AW-CAT-C-sales.salestaxrate.taxrate|AW中文目录列说明|sales.salestaxrate.taxrate|
|d3:AW-CAT-C-sales.salestaxrate.name|AW-CAT-C-sales.salestaxrate.name|AW中文目录列说明|sales.salestaxrate.name|
|d3:AW-CAT-C-sales.salestaxrate.rowguid|AW-CAT-C-sales.salestaxrate.rowguid|AW中文目录列说明|sales.salestaxrate.rowguid|
|d3:AW-CAT-C-sales.salestaxrate.modifieddate|AW-CAT-C-sales.salestaxrate.modifieddate|AW中文目录列说明|sales.salestaxrate.modifieddate|
|d3:AW-CAT-T-sales.salesterritory|AW-CAT-T-sales.salesterritory|AW中文目录表说明|sales.salesterritory|
|d3:AW-CAT-C-sales.salesterritory.territoryid|AW-CAT-C-sales.salesterritory.territoryid|AW中文目录列说明|sales.salesterritory.territoryid|
|d3:AW-CAT-C-sales.salesterritory.name|AW-CAT-C-sales.salesterritory.name|AW中文目录列说明|sales.salesterritory.name|
|d3:AW-CAT-C-sales.salesterritory.countryregioncode|AW-CAT-C-sales.salesterritory.countryregioncode|AW中文目录列说明|sales.salesterritory.countryregioncode|
|d3:AW-CAT-C-sales.salesterritory.group|AW-CAT-C-sales.salesterritory.group|AW中文目录列说明|sales.salesterritory.group|
|d3:AW-CAT-C-sales.salesterritory.salesytd|AW-CAT-C-sales.salesterritory.salesytd|AW中文目录列说明|sales.salesterritory.salesytd|
|d3:AW-CAT-C-sales.salesterritory.saleslastyear|AW-CAT-C-sales.salesterritory.saleslastyear|AW中文目录列说明|sales.salesterritory.saleslastyear|
|d3:AW-CAT-C-sales.salesterritory.costytd|AW-CAT-C-sales.salesterritory.costytd|AW中文目录列说明|sales.salesterritory.costytd|
|d3:AW-CAT-C-sales.salesterritory.costlastyear|AW-CAT-C-sales.salesterritory.costlastyear|AW中文目录列说明|sales.salesterritory.costlastyear|
|d3:AW-CAT-C-sales.salesterritory.rowguid|AW-CAT-C-sales.salesterritory.rowguid|AW中文目录列说明|sales.salesterritory.rowguid|
|d3:AW-CAT-C-sales.salesterritory.modifieddate|AW-CAT-C-sales.salesterritory.modifieddate|AW中文目录列说明|sales.salesterritory.modifieddate|
|d3:AW-CAT-T-sales.salesterritoryhistory|AW-CAT-T-sales.salesterritoryhistory|AW中文目录表说明|sales.salesterritoryhistory|
|d3:AW-CAT-C-sales.salesterritoryhistory.businessentityid|AW-CAT-C-sales.salesterritoryhistory.businessentityid|AW中文目录列说明|sales.salesterritoryhistory.businessentityid|
|d3:AW-CAT-C-sales.salesterritoryhistory.territoryid|AW-CAT-C-sales.salesterritoryhistory.territoryid|AW中文目录列说明|sales.salesterritoryhistory.territoryid|
|d3:AW-CAT-C-sales.salesterritoryhistory.startdate|AW-CAT-C-sales.salesterritoryhistory.startdate|AW中文目录列说明|sales.salesterritoryhistory.startdate|
|d3:AW-CAT-C-sales.salesterritoryhistory.enddate|AW-CAT-C-sales.salesterritoryhistory.enddate|AW中文目录列说明|sales.salesterritoryhistory.enddate|
|d3:AW-CAT-C-sales.salesterritoryhistory.rowguid|AW-CAT-C-sales.salesterritoryhistory.rowguid|AW中文目录列说明|sales.salesterritoryhistory.rowguid|
|d3:AW-CAT-C-sales.salesterritoryhistory.modifieddate|AW-CAT-C-sales.salesterritoryhistory.modifieddate|AW中文目录列说明|sales.salesterritoryhistory.modifieddate|
|d3:AW-CAT-T-sales.shoppingcartitem|AW-CAT-T-sales.shoppingcartitem|AW中文目录表说明|sales.shoppingcartitem|
|d3:AW-CAT-C-sales.shoppingcartitem.shoppingcartitemid|AW-CAT-C-sales.shoppingcartitem.shoppingcartitemid|AW中文目录列说明|sales.shoppingcartitem.shoppingcartitemid|
|d3:AW-CAT-C-sales.shoppingcartitem.shoppingcartid|AW-CAT-C-sales.shoppingcartitem.shoppingcartid|AW中文目录列说明|sales.shoppingcartitem.shoppingcartid|
|d3:AW-CAT-C-sales.shoppingcartitem.quantity|AW-CAT-C-sales.shoppingcartitem.quantity|AW中文目录列说明|sales.shoppingcartitem.quantity|
|d3:AW-CAT-C-sales.shoppingcartitem.productid|AW-CAT-C-sales.shoppingcartitem.productid|AW中文目录列说明|sales.shoppingcartitem.productid|
|d3:AW-CAT-C-sales.shoppingcartitem.datecreated|AW-CAT-C-sales.shoppingcartitem.datecreated|AW中文目录列说明|sales.shoppingcartitem.datecreated|
|d3:AW-CAT-C-sales.shoppingcartitem.modifieddate|AW-CAT-C-sales.shoppingcartitem.modifieddate|AW中文目录列说明|sales.shoppingcartitem.modifieddate|
|d3:AW-CAT-T-sales.specialoffer|AW-CAT-T-sales.specialoffer|AW中文目录表说明|sales.specialoffer|
|d3:AW-CAT-C-sales.specialoffer.specialofferid|AW-CAT-C-sales.specialoffer.specialofferid|AW中文目录列说明|sales.specialoffer.specialofferid|
|d3:AW-CAT-C-sales.specialoffer.description|AW-CAT-C-sales.specialoffer.description|AW中文目录列说明|sales.specialoffer.description|
|d3:AW-CAT-C-sales.specialoffer.discountpct|AW-CAT-C-sales.specialoffer.discountpct|AW中文目录列说明|sales.specialoffer.discountpct|
|d3:AW-CAT-C-sales.specialoffer.type|AW-CAT-C-sales.specialoffer.type|AW中文目录列说明|sales.specialoffer.type|
|d3:AW-CAT-C-sales.specialoffer.category|AW-CAT-C-sales.specialoffer.category|AW中文目录列说明|sales.specialoffer.category|
|d3:AW-CAT-C-sales.specialoffer.startdate|AW-CAT-C-sales.specialoffer.startdate|AW中文目录列说明|sales.specialoffer.startdate|
|d3:AW-CAT-C-sales.specialoffer.enddate|AW-CAT-C-sales.specialoffer.enddate|AW中文目录列说明|sales.specialoffer.enddate|
|d3:AW-CAT-C-sales.specialoffer.minqty|AW-CAT-C-sales.specialoffer.minqty|AW中文目录列说明|sales.specialoffer.minqty|
|d3:AW-CAT-C-sales.specialoffer.maxqty|AW-CAT-C-sales.specialoffer.maxqty|AW中文目录列说明|sales.specialoffer.maxqty|
|d3:AW-CAT-C-sales.specialoffer.rowguid|AW-CAT-C-sales.specialoffer.rowguid|AW中文目录列说明|sales.specialoffer.rowguid|
|d3:AW-CAT-C-sales.specialoffer.modifieddate|AW-CAT-C-sales.specialoffer.modifieddate|AW中文目录列说明|sales.specialoffer.modifieddate|
|d3:AW-CAT-T-sales.specialofferproduct|AW-CAT-T-sales.specialofferproduct|AW中文目录表说明|sales.specialofferproduct|
|d3:AW-CAT-C-sales.specialofferproduct.specialofferid|AW-CAT-C-sales.specialofferproduct.specialofferid|AW中文目录列说明|sales.specialofferproduct.specialofferid|
|d3:AW-CAT-C-sales.specialofferproduct.productid|AW-CAT-C-sales.specialofferproduct.productid|AW中文目录列说明|sales.specialofferproduct.productid|
|d3:AW-CAT-C-sales.specialofferproduct.rowguid|AW-CAT-C-sales.specialofferproduct.rowguid|AW中文目录列说明|sales.specialofferproduct.rowguid|
|d3:AW-CAT-C-sales.specialofferproduct.modifieddate|AW-CAT-C-sales.specialofferproduct.modifieddate|AW中文目录列说明|sales.specialofferproduct.modifieddate|
|d3:AW-CAT-T-sales.store|AW-CAT-T-sales.store|AW中文目录表说明|sales.store|
|d3:AW-CAT-C-sales.store.businessentityid|AW-CAT-C-sales.store.businessentityid|AW中文目录列说明|sales.store.businessentityid|
|d3:AW-CAT-C-sales.store.name|AW-CAT-C-sales.store.name|AW中文目录列说明|sales.store.name|
|d3:AW-CAT-C-sales.store.salespersonid|AW-CAT-C-sales.store.salespersonid|AW中文目录列说明|sales.store.salespersonid|
|d3:AW-CAT-C-sales.store.demographics|AW-CAT-C-sales.store.demographics|AW中文目录列说明|sales.store.demographics|
|d3:AW-CAT-C-sales.store.rowguid|AW-CAT-C-sales.store.rowguid|AW中文目录列说明|sales.store.rowguid|
|d3:AW-CAT-C-sales.store.modifieddate|AW-CAT-C-sales.store.modifieddate|AW中文目录列说明|sales.store.modifieddate|
|d3:clarify-01|clarify-01|D3澄清开发集|巴西有多少客户？|
|d3:clarify-02|clarify-02|D3澄清开发集|genre.name 明确为 Rock 的曲目有多少首？|
|d3:clarify-04|clarify-04|D3澄清开发集|2024年全部发票的平均每张发票金额是多少？|
|d3:clarify-05|clarify-05|D3澄清开发集|数据库一共有多少个音乐流派？|
|d3:clarify-07|clarify-07|D3澄清开发集|2024年账单国家为Brazil的发票金额占同年所有发票金额的比例是多少？|
|d3:clarify-08|clarify-08|D3澄清开发集|2024年账单国家为USA的发票销售额同比增长率是多少？|
|d3:clarify-10|clarify-10|D3澄清开发集|2024年全部发票按总额从高到低列出前5张，相同金额按invoice_id升序。|
|d3:clarify-11|clarify-11|D3澄清开发集|2024年最受欢迎的5首曲目是哪些？|
|d3:clarify-13|clarify-13|D3澄清开发集|2022年卖得最好的2首歌有哪些？|
|d3:clarify-14|clarify-14|D3澄清开发集|2024年客户中谁买得最多？请列前3名。|
|d3:clarify-16|clarify-16|D3澄清开发集|账单国家为USA的发票销售额同比增长多少？|
|d3:clarify-17|clarify-17|D3澄清开发集|2024年同比增长多少？|
|d3:clarify-19|clarify-19|D3澄清开发集|2024年Brazil账单发票销售额占比是多少？|
|d3:clarify-20|clarify-20|D3澄清开发集|2024年哪些记录的金额占全部发票金额的比例？我还没确定分子范围。|
|d3:clarify-22|clarify-22|D3澄清开发集|2024年谁买得最多？|
|d3:clarify-23|clarify-23|D3澄清开发集|摇滚歌曲有多少首？|
|d3:clarify-25|clarify-25|D3澄清开发集|这批曲目的平均时长是多少？|
|d3:clarify-26|clarify-26|D3澄清开发集|有多少复购客户？|
|d3:clarify-27|clarify-27|D3澄清开发集|2024年全部发票销售额环比增长率是多少？|
|d3:clarify-28|clarify-28|D3澄清开发集|统计2024年的发票销售额，但日期必须从2023年1月1日到2023年12月31日。|
|d3:clarify-30|clarify-30|D3澄清开发集|摇滚乐曲目的平均时长是多少？|
|d3:d3-b-protocol|d3-b-protocol|公共接口与会话|新增可选 ChatRequest.clarification_id/intent_version/choice_id 和 AnswerEnvelope.intent；IntentContract 延续 extra=forbid，卡片恢复需ID与版本同时匹配，PDF物理页从1开始的既有约定不改。|
|d3:d3-b-defaults|d3-b-defaults|声明的对象限定假设|热门曲目缺指标采用已共同确认的购买数量口径；客户谁买得最多缺指标采用已共同确认金额；缺Top-N数量按方案默认10并声明；缺关键期间/对象不得猜。|
|d3:d3-b-growth-display|d3-b-growth-display|增长率显示单位|人工决定增长率结果表及文字采用fraction还是percent，以及统一舍入/单位说明方式；在决定前不修改原始输出。|
|d3:d3-b-measurement-scope|d3-b-measurement-scope|测试结论范围|21/21仅初始分级与执行门；7请求20/20为具体状态链；7UI请求10/10为控件连线。全部21题的澄清交互最终答案正确率尚未实测。|
|special:sp01-01|sp01-01|专项①消歧/改写|How many customers are from France?|
|special:sp01-02|sp01-02|专项①消歧/改写|Iron Maiden乐队一共有多少张专辑？|
|special:sp01-03|sp01-03|专项①消歧/改写|德国的发票一共开了多少钱？|
|special:sp01-04|sp01-04|专项①消歧/改写|Frnace 有多少客户？|
|special:sp01-05|sp01-05|专项①消歧/改写|Metallcia 有多少张专辑？|
|special:sp01-06|sp01-06|专项①消歧/改写|Deguo 有多少张专辑？|
|special:sp01-07|sp01-07|专项①消歧/改写|Chinook 里 Protected AAC audio file 这种 format 有多少首曲目？|
|special:sp01-08|sp01-08|专项①消歧/改写|意大利那边现在有多少客户？|
|special:sp01-09|sp01-09|专项①消歧/改写|Chinook 里有多少首摇滚歌曲？|
|special:sp01-10|sp01-10|专项①消歧/改写|查询 genre 为 Vaporwave 的曲目数量；如果数据库里根本没有这个流派，请直接报告没有记录。|
|special:sp01-11|sp01-11|专项①消歧/改写|How many customers are from Canada?|
|special:sp01-12|sp01-12|专项①消歧/改写|What was the total invoice revenue for France in 2022?|
|special:sp01-13|sp01-13|专项①消歧/改写|Iron Maiden乐队一共有多少张专辑？|
|special:sp01-14|sp01-14|专项①消歧/改写|法兰西共和国的发票一共开了多少张？|
|special:sp01-15|sp01-15|专项①消歧/改写|受保护AAC音频文件这种媒体格式有多少首曲目？|
|special:sp01-16|sp01-16|专项①消歧/改写|U2乐队一共有多少张专辑？|
|special:sp01-17|sp01-17|专项①消歧/改写|Fracne 有多少客户？|
|special:sp01-18|sp01-18|专项①消歧/改写|Led Zepelin 有多少张专辑？|
|special:sp01-19|sp01-19|专项①消歧/改写|Canda 的客户有多少？|
|special:sp01-20|sp01-20|专项①消歧/改写|MPEG adiou file 有多少首曲目？|
|special:sp01-21|sp01-21|专项①消歧/改写|Deguo 的客户有多少个？|
|special:sp01-22|sp01-22|专项①消歧/改写|Gudian 这个流派的曲目有多少首？|
|special:sp01-23|sp01-23|专项①消歧/改写|Canada 那边一共有多少 customers？|
|special:sp01-24|sp01-24|专项①消歧/改写|Iron Maiden 这个 artist 有多少 albums？|
|special:sp01-25|sp01-25|专项①消歧/改写|意大利那边的发票总共开了多少钱？|
|special:sp01-26|sp01-26|专项①消歧/改写|加拿大那边现在有多少客户？|
|special:sp01-27|sp01-27|专项①消歧/改写|Chinook 里摇滚曲目有多少首？|
|special:sp01-28|sp01-28|专项①消歧/改写|Chinook 里金属流派的曲目有多少首？|
|special:sp01-29|sp01-29|专项①消歧/改写|查一下 customer.country='Atlantis' 的客户数量；如果数据库没有这个国家，就按这个字面值查，直接报告没有记录。|
|special:sp01-30|sp01-30|专项①消歧/改写|统计 invoice_date 在 2030-01-01 到 2030-12-31（左闭右开）之间的发票张数；如果那段时间没有发票，就按这个时间范围查询并报告没有记录。|
|special:sp03-01|sp03-01|专项③分级澄清/续问|Chinook 里2020年全年的发票销售额是多少？如果那一年没有发票记录，请直接说没有可用记录，不要用0代替。|
|special:sp03-02|sp03-02|专项③分级澄清/续问|How many customers reside in France?|
|special:sp03-03|sp03-03|专项③分级澄清/续问|2024年巴西的销售额同比2023年增长了多少？|
|special:sp03-04|sp03-04|专项③分级澄清/续问|2023年按销售额排名最高的曲目。|
|special:sp03-05|sp03-05|专项③分级澄清/续问|2007年最受欢迎的10首爵士曲目是哪些？|
|special:sp03-06|sp03-06|专项③分级澄清/续问|销售额同比增长多少？|
|special:sp03-07|sp03-07|专项③分级澄清/续问|2024年账单国是美国的发票销售额占比是多少？|
|special:sp03-08|sp03-08|专项③分级澄清/续问|2023年谁买得最多？|
|special:sp03-09|sp03-09|专项③分级澄清/续问|2024年摇滚曲目卖了多少张？|
|special:sp03-10|sp03-10|专项③分级澄清/续问|2024年巴西的客户有多少？|
|special:sp03-11|sp03-11|专项③分级澄清/续问|How many customers reside in the USA?|
|special:sp03-12|sp03-12|专项③分级澄清/续问|意大利有多少客户？|
|special:sp03-13|sp03-13|专项③分级澄清/续问|What was the total invoice revenue for Canada in 2024?|
|special:sp03-14|sp03-14|专项③分级澄清/续问|2022年和2023年，Chinook 每年的发票销售额分别是多少？|
|special:sp03-15|sp03-15|专项③分级澄清/续问|2009 年和 2010 年之间，哪首曲目最受欢迎？|
|special:sp03-16|sp03-16|专项③分级澄清/续问|Chinook 里 Jazz 流派的曲目有多少首？|
|special:sp03-17|sp03-17|专项③分级澄清/续问|2020年全年复购（至少开2张发票）的客户有多少位？如果没有，请如实输出0。|
|special:sp03-18|sp03-18|专项③分级澄清/续问|2021到2022年最受欢迎的曲目有哪些？|
|special:sp03-19|sp03-19|专项③分级澄清/续问|2022年买得最多的客户是谁？|
|special:sp03-20|sp03-20|专项③分级澄清/续问|2023年按销售额排名最高的艺术家，取前10名。|
|special:sp03-21|sp03-21|专项③分级澄清/续问|德国的销售额同比增长多少？|
|special:sp03-22|sp03-22|专项③分级澄清/续问|2024年法国居住客户的销售额占比是多少？|
|special:sp03-23|sp03-23|专项③分级澄清/续问|2023年谁买得最多？|
|special:sp03-24|sp03-24|专项③分级澄清/续问|2022年澳大利亚的发票销售额是多少？|
|special:sp03-25|sp03-25|专项③分级澄清/续问|2024年摇滚曲目的销售额是多少？|
|special:sp03-26|sp03-26|专项③分级澄清/续问|同比增长多少？|
|special:sp03-27|sp03-27|专项③分级澄清/续问|2023年销售额占比是多少？|
|special:sp03-28|sp03-28|专项③分级澄清/续问|2022年金属乐队的销售额是多少？|
|special:sp03-29|sp03-29|专项③分级澄清/续问|最受欢迎的10首曲目是哪些？|
|special:sp03-30|sp03-30|专项③分级澄清/续问|谁买得最多？|
|oct12-join:oct12-join-01|oct12-join-01|10月12日JOIN新增回归|Metallica有多少张专辑？|
|oct12-join:oct12-join-02|oct12-join-02|10月12日JOIN新增回归|Metallcia有多少张专辑？|
|oct12-join:oct12-join-03|oct12-join-03|10月12日JOIN新增回归|AC/DC一共有几首曲目？|
|oct12-join:oct12-join-04|oct12-join-04|10月12日JOIN新增回归|Protected AAC audio file这种媒体类型有多少首曲目？|
|oct12-join:oct12-join-05|oct12-join-05|10月12日JOIN新增回归|Vaporwave流派有多少首曲目？|
|oct12-join:oct12-join-06|oct12-join-06|10月12日JOIN新增回归|Iron Maiden的专辑有哪些？按专辑编号从小到大列出编号和标题。|
|oct12-join:oct12-join-07|oct12-join-07|10月12日JOIN新增回归|专辑最多的5位艺术家是谁？列出艺术家编号、名字和专辑数，同数量时按艺术家编号从小到大。|
|oct12-join:oct12-join-08|oct12-join-08|10月12日JOIN新增回归|按购买数量排，最热门的3首曲目是什么？列出曲目编号、名称和购买数量，同数量按曲目编号升序。|
|oct12-join:oct12-join-09|oct12-join-09|10月12日JOIN新增回归|每位客户开过几张发票？没有发票的也要，列出客户编号、名字、姓氏和发票数，按客户编号升序。|
|oct12-join:oct12-join-10|oct12-join-10|10月12日JOIN新增回归|客户所在地在巴西的客户一共开过多少张发票？|
|oct12-join:oct12-join-11|oct12-join-11|10月12日JOIN新增回归|账单国家是France的发票一共买了多少首Rock流派的曲目？按购买数量计。|
|oct12-join:oct12-join-12|oct12-join-12|10月12日JOIN新增回归|Led Zeppelin所有曲目的销售额合计是多少？|
|oct12-join:oct12-join-13|oct12-join-13|10月12日JOIN新增回归|名字叫Jane、姓氏为Peacock的员工负责几位客户？|
|oct12-join:oct12-join-14|oct12-join-14|10月12日JOIN新增回归|每种媒体类型有几首曲目？没有曲目的也保留，列出类型编号、名称和曲目数，按类型编号升序。|
|oct12-join:oct12-join-15|oct12-join-15|10月12日JOIN新增回归|哪些专辑没有曲目？列出专辑编号和标题，按专辑编号升序。|
|robust:robust-01|robust-01|10月12日新系统回答|来自巴稀的客户有多少位？|
|robust:robust-02|robust-02|10月12日新系统回答|列出来自美囯的客户编号、城市和州，按客户编号升序。|
|robust:robust-03|robust-03|10月12日新系统回答|列出职位为 Sales Suport Agent 的员工编号、名字和姓氏，按员工编号升序。|
|robust:robust-06|robust-06|10月12日新系统回答|列出来自老美的客户编号、城市和州，按客户编号升序。|
|robust:robust-07|robust-07|10月12日新系统回答|来自意大利的客户有多少位？|
|robust:robust-08|robust-08|10月12日新系统回答|来自加拿大的客户有多少位？|
|robust:robust-11|robust-11|10月12日新系统回答|来自 ba xi 的客户有多少位？|
|robust:robust-12|robust-12|10月12日新系统回答|客户所在国家为 yi da li 的客户有多少位？|
|robust:robust-13|robust-13|10月12日新系统回答|客户所在国家为 jia na da 的客户有多少位？|
|robust:robust-16|robust-16|10月12日新系统回答|country 是 Brazil 的 customer 有多少位？|
|robust:robust-17|robust-17|10月12日新系统回答|列出 country 为 USA 的客户编号 customer_id、城市 city 和州 state，按 customer_id 升序。|
|robust:robust-18|robust-18|10月12日新系统回答|全部 invoice 的 total 加起来是多少？|
|robust:robust-19|robust-19|10月12日新系统回答|billing_country 为 Canada 的全部 invoice 的 total 总和是多少？|
|robust:robust-21|robust-21|10月12日新系统回答|咱们客户表一共有几个人？|
|robust:robust-22|robust-22|10月12日新系统回答|帮我数数，来自巴西的客户有几位呀？|
|robust:robust-24|robust-24|10月12日新系统回答|曲目里最短的一首有几毫秒呀？|
|robust:robust-26|robust-26|10月12日新系统回答|你好，请帮忙查一下来自巴西的客户有多少位，谢谢。|
|robust:robust-27|robust-27|10月12日新系统回答|麻烦帮我看看，有多少位客户没有填写公司名称，也就是 company 为 NULL 呢？谢谢。|
|robust:robust-28|robust-28|10月12日新系统回答|请帮我查一查，2023 年一共开了多少张发票，非常感谢。|
|robust:robust-29|robust-29|10月12日新系统回答|麻烦查一下客户所在国家为 Wakanda 的客户有多少位，保留原值，没匹配返回 0，谢谢。|
|sql:sql-31|sql-31|10月12日新系统回答|客户所在国家为 Italy 的客户有多少位？|
|sql:sql-32|sql-32|10月12日新系统回答|客户所在国家为 Canada 的客户有多少位？|
|sql:sql-33|sql-33|10月12日新系统回答|账单国家为 Canada 的全部发票总额是多少？|
|sql:sql-34|sql-34|10月12日新系统回答|曲目表中最短的时长是多少毫秒？|
|sql:sql-35|sql-35|10月12日新系统回答|曲目表中最高的单价是多少？|
|sql:sql-36|sql-36|10月12日新系统回答|按发票账单城市统计发票数，先按数量降序，并列按城市名称升序，返回前 10 个城市。|
|sql:sql-37|sql-37|10月12日新系统回答|按媒体类型编号统计曲目数，按媒体类型编号升序。|
|sql:sql-39|sql-39|10月12日新系统回答|2023 年一共开了多少张发票？|
|sql:sql-40|sql-40|10月12日新系统回答|2022 年 7 月 1 日（含）到 2022 年 10 月 1 日（不含）的发票总额是多少？|
|sql:sql-41|sql-41|10月12日新系统回答|列出名称以 The 开头的前 8 位艺术家，区分大小写，返回编号和名称，按艺术家编号升序。|
|sql:sql-42|sql-42|10月12日新系统回答|列出名称恰好为 U2 的艺术家编号和名称，按编号升序。|
|sql:sql-43|sql-43|10月12日新系统回答|没有填写州信息（state 为 NULL）的客户有多少位？|
|sql:sql-44|sql-44|10月12日新系统回答|客户所在国家为 Wakanda 的客户有多少位？保留原筛选值，没匹配时返回 0。|
|oct12-diagnostic:oct12-alias-us|oct12-alias-us|10月12日默认口径诊断|老美有多少客户？|
|oct12-diagnostic:oct12-default-ratio|oct12-default-ratio|10月12日默认口径诊断|2024年法国销售额占比是多少？|
|oct12-diagnostic:oct12-default-region|oct12-default-region|10月12日默认口径诊断|2024年巴西销售额是多少？|
|oct12-diagnostic:oct12-default-repeat|oct12-default-repeat|10月12日默认口径诊断|复购客户有多少？|
|oct12-diagnostic:oct12-default-track|oct12-default-track|10月12日默认口径诊断|最热门的3首曲目是什么？|
|oct12-diagnostic:oct12-default-who|oct12-default-who|10月12日默认口径诊断|谁买得最多？给我前三位。|
|oct12-diagnostic:oct12-explicit-region|oct12-explicit-region|10月12日默认口径诊断|2024年按客户所在地统计巴西销售额是多少？|
|oct12-diagnostic:oct12-context-numerator|oct12-context-numerator|10月12日默认口径诊断|2023年法国居住客户的销售额占比是多少？|
|oct12-diagnostic:oct12-context-year|oct12-context-year|10月12日默认口径诊断|2023年谁买得最多？给我前三位。|
|oct12-diagnostic:oct12-midnight-invoice-ratio|oct12-midnight-invoice-ratio|10月12日默认口径诊断|2024年账单国家为Brazil的发票金额占同年所有发票金额的比例是多少？|
|oct12-ui:invoice-ratio|oct12-ui:invoice-ratio|10月12日页面真实问答|2024年账单国家为Brazil的发票金额占同年所有发票金额的比例是多少？|

保留记录D2 33＋D3 18＝51；D1历史15条不另加。内容本轮不审核、不生成预测，独立边界见同目录JSON。

所有完整材料、AI意见、各版本真实回答、源码与原始证据路径在同名JSON和HTML中，脚本只创建新入口，不覆盖旧表。
