"""Prepare 30 AW label queries read-only; never send held cases to QA.

New D3 families are distinct. Dataset manifests and development review files
separate the 21 development cases from the nine protected label-only cases.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psycopg
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql

# Each tuple: question, gold SQL, gold tables, distractor tables, semantic rationale.
DEV = [
    ("AdventureWorks 数据库共有多少张销售订单？请统计订单头记录数。", "SELECT COUNT(*) AS order_count FROM sales.salesorderheader", ["sales.salesorderheader"], ["purchasing.purchaseorderheader"], "销售而非采购；每张销售订单头是一条订单记录，不按明细计数。"),
    ("采购订单一共有多少张？按采购订单头计数。", "SELECT COUNT(*) AS order_count FROM purchasing.purchaseorderheader", ["purchasing.purchaseorderheader"], ["sales.salesorderheader"], "采购订单头计数，与销售订单头同名近似对象区分。"),
    ("员工档案中共有多少名员工？包括 currentflag 为 false 的档案。", "SELECT COUNT(*) AS employee_count FROM humanresources.employee", ["humanresources.employee"], ["sales.salesperson"], "统计完整员工档案；用户明确不做在职过滤。"),
    ("销售人员表中共有多少名销售人员？", "SELECT COUNT(*) AS salesperson_count FROM sales.salesperson", ["sales.salesperson"], ["humanresources.employee"], "销售人员只是员工的一部分；统计 salesperson。"),
    ("产品目录中共有多少个产品？不要用产品型号数替代。", "SELECT COUNT(*) AS product_count FROM production.product", ["production.product"], ["production.productmodel"], "产品记录计数，型号表是干扰项。"),
    ("产品颜色有多少种？未填写颜色的不计入。", "SELECT COUNT(DISTINCT color) AS color_count FROM production.product WHERE color IS NOT NULL", ["production.product"], ["production.productsubcategory"], "DISTINCT 颜色，NULL 排除，不将未填写视为一种颜色。"),
    ("列出目录售价最高的五个产品，给出产品编号、名称和售价；同价时按产品编号从小到大。", "SELECT productid,name,listprice FROM production.product ORDER BY listprice DESC NULLS LAST,productid ASC LIMIT 5", ["production.product"], ["production.productlistpricehistory", "production.productcosthistory"], "现行目录售价 listprice；不是历史价格或 standardcost。"),
    ("每个产品大类下面有多少个产品？只统计已分到子类别的产品，输出大类名称和数量，按数量降序、名称升序。", "SELECT c.name AS category_name,COUNT(*) AS product_count FROM production.product p JOIN production.productsubcategory s ON p.productsubcategoryid=s.productsubcategoryid JOIN production.productcategory c ON s.productcategoryid=c.productcategoryid GROUP BY c.productcategoryid,c.name ORDER BY product_count DESC,c.name ASC", ["production.product", "production.productsubcategory", "production.productcategory"], ["production.productmodel"], "必须经过子类别桥接；NULL 子类别产品按题意排除。"),
    ("供应商档案一共有多少条？不按客户或门店计数。", "SELECT COUNT(*) AS vendor_count FROM purchasing.vendor", ["purchasing.vendor"], ["sales.customer", "sales.store"], "供应商实体在 purchasing.vendor，与客户门店分开。"),
    ("各员工职位有多少人？列人数最多的十个职位，按人数降序、职位名称升序。", "SELECT jobtitle,COUNT(*) AS employee_count FROM humanresources.employee GROUP BY jobtitle ORDER BY employee_count DESC,jobtitle ASC LIMIT 10", ["humanresources.employee"], ["sales.salesperson", "humanresources.department"], "jobtitle 是职位；部门名称不能替代职位。"),
    ("2013 年销售订单头的 subtotal 合计是多少？仅算这个字段，不含 taxamt 和 freight。", "SELECT SUM(subtotal) AS subtotal_sum FROM sales.salesorderheader WHERE orderdate >= DATE '2013-01-01' AND orderdate < DATE '2014-01-01'", ["sales.salesorderheader"], ["purchasing.purchaseorderheader", "sales.salesorderdetail"], "完整2013自然年半开区间；明确 subtotal 而非 totaldue，币种不另行宣称。"),
    ("2013 年采购订单头的 subtotal 合计是多少？不含税与运费。", "SELECT SUM(subtotal) AS subtotal_sum FROM purchasing.purchaseorderheader WHERE orderdate >= DATE '2013-01-01' AND orderdate < DATE '2014-01-01'", ["purchasing.purchaseorderheader"], ["sales.salesorderheader", "purchasing.purchaseorderdetail"], "采购头金额，避免明细 JOIN 重复累计。"),
    ("地址档案里哪个城市的地址记录最多？列出前五名城市和记录数，按记录数降序、城市名升序。", "SELECT city,COUNT(*) AS address_count FROM person.address GROUP BY city ORDER BY address_count DESC,city ASC LIMIT 5", ["person.address"], ["sales.customer", "sales.salesterritory"], "按地址记录而不是人数/客户数；相同城市文字归为一组。"),
    ("2013 年每个月有多少张销售订单？输出月份数字和订单数，按月份从小到大。", "SELECT EXTRACT(MONTH FROM orderdate)::int AS month,COUNT(*) AS order_count FROM sales.salesorderheader WHERE orderdate >= DATE '2013-01-01' AND orderdate < DATE '2014-01-01' GROUP BY EXTRACT(MONTH FROM orderdate) ORDER BY month ASC", ["sales.salesorderheader"], ["purchasing.purchaseorderheader"], "按订单日期自然月，固定2013范围，订单头数量。"),
    ("销售原因字典里每个 reasontype 分别有多少条原因？按类型名称排序。", "SELECT reasontype,COUNT(*) AS reason_count FROM sales.salesreason GROUP BY reasontype ORDER BY reasontype ASC", ["sales.salesreason"], ["sales.salesorderheadersalesreason"], "统计字典定义项数量，不统计订单使用原因次数。"),
    ("客户档案中 personid 非空的有多少条，storeid 非空的有多少条？两个条件分别计数，不要求互斥。", "SELECT COUNT(personid) AS person_linked_count,COUNT(storeid) AS store_linked_count FROM sales.customer", ["sales.customer"], ["person.person", "sales.store"], "COUNT(列)排除NULL；不凭分类推断互斥或转换为人口数。"),
    ("汇总每个产品在所有库存地点的 quantity，列库存总量最高的五个产品编号、名称和数量；数量相同按编号升序。", "SELECT p.productid,p.name,SUM(i.quantity) AS total_quantity FROM production.productinventory i JOIN production.product p ON i.productid=p.productid GROUP BY p.productid,p.name ORDER BY total_quantity DESC,p.productid ASC LIMIT 5", ["production.productinventory", "production.product"], ["production.workorder", "sales.salesorderdetail"], "所有库位 quantity 加总，非订单销量；同编号聚合。"),
    ("2013 年各产品大类的销售购买数量分别是多少？按 salesorderdetail.orderqty 加总，只统计有子类别的产品，输出大类名和数量，按数量降序、名称升序。", "SELECT c.name AS category_name,SUM(d.orderqty) AS order_quantity FROM sales.salesorderdetail d JOIN sales.salesorderheader h ON d.salesorderid=h.salesorderid JOIN production.product p ON d.productid=p.productid JOIN production.productsubcategory s ON p.productsubcategoryid=s.productsubcategoryid JOIN production.productcategory c ON s.productcategoryid=c.productcategoryid WHERE h.orderdate >= DATE '2013-01-01' AND h.orderdate < DATE '2014-01-01' GROUP BY c.productcategoryid,c.name ORDER BY order_quantity DESC,c.name ASC", ["sales.salesorderdetail", "sales.salesorderheader", "production.product", "production.productsubcategory", "production.productcategory"], ["purchasing.purchaseorderdetail", "production.productinventory"], "销售明细数量、销售头日期、大类维度；产品→子类别→大类须真实外键桥接。"),
    ("每种运输方式被多少张采购订单使用？输出运输方式名称和采购订单数，按订单数降序、名称升序。", "SELECT s.name AS ship_method,COUNT(*) AS order_count FROM purchasing.purchaseorderheader h JOIN purchasing.shipmethod s ON h.shipmethodid=s.shipmethodid GROUP BY s.shipmethodid,s.name ORDER BY order_count DESC,s.name ASC", ["purchasing.purchaseorderheader", "purchasing.shipmethod"], ["sales.salesorderheader"], "题意采购订单；未使用方式不要求补0，运输方式FK链接。"),
    ("2013 年每个销售区域的销售订单 subtotal 合计是多少？不计 territoryid 为空的订单，输出区域名和合计，按金额降序、名称升序。", "SELECT t.name AS territory_name,SUM(h.subtotal) AS subtotal_sum FROM sales.salesorderheader h JOIN sales.salesterritory t ON h.territoryid=t.territoryid WHERE h.orderdate >= DATE '2013-01-01' AND h.orderdate < DATE '2014-01-01' GROUP BY t.territoryid,t.name ORDER BY subtotal_sum DESC NULLS LAST,t.name ASC", ["sales.salesorderheader", "sales.salesterritory"], ["person.stateprovince", "person.address"], "销售组织区域不是地址州省；明确排除未分配区域且只累加订单头。"),
    ("currentflag 为 true 的员工中，各部门目前分配了多少人？以部门历史记录 enddate 为空表示目前分配，输出部门名和人数，按人数降序、部门名升序。", "SELECT d.name AS department_name,COUNT(DISTINCT e.businessentityid) AS employee_count FROM humanresources.employee e JOIN humanresources.employeedepartmenthistory h ON e.businessentityid=h.businessentityid JOIN humanresources.department d ON h.departmentid=d.departmentid WHERE e.currentflag=true AND h.enddate IS NULL GROUP BY d.departmentid,d.name ORDER BY employee_count DESC,d.name ASC", ["humanresources.employee", "humanresources.employeedepartmenthistory", "humanresources.department"], ["sales.salesperson"], "在职标志和当前部门分配是两个显式条件；部门内按员工编号去重。"),
]

# Label-only blueprint. Its output is never passed to a model under test.
HOLD = [
    ("生产工单里的 orderqty 合计是多少？", "SELECT SUM(orderqty) AS quantity_sum FROM production.workorder", ["production.workorder"], ["sales.salesorderdetail"], "生产工单数量，不是销售购买数量。"),
    ("文化语言字典共有多少条记录？", "SELECT COUNT(*) AS culture_count FROM production.culture", ["production.culture"], ["person.countryregion"], "文化语言与国家地区字典区分。"),
    ("联系人类型字典共有多少条类型？", "SELECT COUNT(*) AS type_count FROM person.contacttype", ["person.contacttype"], ["person.addresstype"], "联系人类型而非地址类型。"),
    ("计量单位字典共有多少条？", "SELECT COUNT(*) AS unit_count FROM production.unitmeasure", ["production.unitmeasure"], ["production.location"], "单位定义项数量。"),
    ("员工薪资历史中最大的 rate 是多少？不换算日薪或年薪。", "SELECT MAX(rate) AS max_rate FROM humanresources.employeepayhistory", ["humanresources.employeepayhistory"], ["sales.salesperson"], "保留原始rate单位，不能用销售佣金替代。"),
    ("评分至少为4的产品评论共有多少条？", "SELECT COUNT(*) AS review_count FROM production.productreview WHERE rating>=4", ["production.productreview"], ["production.productdescription"], "评论筛选包含4，不统计描述。"),
    ("2013年货币汇率历史记录共有多少条？按 currencyratedate 过滤。", "SELECT COUNT(*) AS rate_count FROM sales.currencyrate WHERE currencyratedate >= DATE '2013-01-01' AND currencyratedate < DATE '2014-01-01'", ["sales.currencyrate"], ["sales.currency"], "汇率历史而非币种字典，日期完整自然年。"),
    ("每个国家地区关联了多少种币种？输出国家代码和种数，按国家代码升序。", "SELECT countryregioncode,COUNT(DISTINCT currencycode) AS currency_count FROM sales.countryregioncurrency GROUP BY countryregioncode ORDER BY countryregioncode ASC", ["sales.countryregioncurrency"], ["person.countryregion", "sales.currency"], "关联关系记录按币种去重，不能统计所有币种数。"),
    ("销售优惠字典中最大的 discountpct 是多少？保留原字段值，不转成百分数显示。", "SELECT MAX(discountpct) AS max_discount FROM sales.specialoffer", ["sales.specialoffer"], ["sales.salesorderdetail"], "优惠字典字段不是明细折扣；明确不乘100。"),
]


def main():
    settings = get_settings()
    catalog_path = ROOT / "data/catalog/adventureworks.yaml"
    if not catalog_path.exists():
        catalog_path = ROOT / "data/catalog/adventureworks-live.yaml"
    catalog = load_catalog(catalog_path)
    out = ROOT / "eval/datasets/d3"
    artifact = ROOT / "eval/artifacts/d3/a/gold"
    out.mkdir(parents=True, exist_ok=True)
    artifact.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256((ROOT / "data/db/aw_source_manifest.json").read_bytes()).hexdigest()
    records = []
    for index, (question, query, tables, distractors, rationale) in enumerate(DEV+HOLD, 1):
        id_ = f"aw-{index:02d}"
        split = "dev" if index <= len(DEV) else "holdout"
        checked = validate_sql(query, catalog, max_rows=200)
        if set(checked.tables_used) != set(tables):
            raise ValueError(f"{id_} declared gold tables disagree with SQL AST")
        result = execute_sql(checked.sql, settings.aw_db_url, settings.statement_timeout_ms, 200)
        if result.truncated:
            raise ValueError(f"{id_} gold unexpectedly truncated")
        with psycopg.connect(settings.aw_db_url, connect_timeout=5) as conn:
            conn.read_only = True
            conn.execute("SELECT set_config('statement_timeout', %s, true)", (str(settings.statement_timeout_ms),))
            with conn.cursor() as cur:
                cur.execute(checked.sql)
                types = ["number" if col.type_code in {20,21,23,700,701,1700} else "temporal" if col.type_code in {1082,1083,1114,1184,1186,1266} else "text" for col in cur.description]
        item = {"id": id_, "family_id": "d3-"+id_, "split": split, "db_id": "adventureworks",
                "question": question, "category": "distractor" if distractors else "schema_link",
                "gold_sql": checked.sql, "gold_tables": tables, "distractor_tables": distractors,
                "gold_result": result.rows, "gold_columns": result.columns, "column_types": types,
                "integer_columns": [i for i,c in enumerate(result.columns) if "count" in c or "quantity" in c or c.endswith("id") or c=="month"],
                "monetary_columns": [], "ordered": "ORDER BY" in query,
                "source_sha256": source_hash, "semantic_rationale": rationale,
                "gold_review": {"status": "pending_human_review", "reviewer": None, "review_date": None},
                "auto_review": {"actual_schema_checked": True, "sql_readonly_validated": True, "gold_sql_executed": True, "executed_at": datetime.now(timezone.utc).isoformat()},
                "ai_review": {"pass_1": "AI建议通过" if split=="dev" else "保护保留集：仅程序核验标签", "pass_1_reason": rationale if split=="dev" else None, "pass_2": "pending", "human_status": "pending_human_review"}}
        records.append(item)
        directory = artifact / split
        directory.mkdir(exist_ok=True)
        (directory / (id_+".json")).write_text(json.dumps({"id": id_, "sql": checked.sql, "tables": checked.tables_used, "columns": result.columns, "rows": result.rows, "truncated": result.truncated}, ensure_ascii=False, indent=2), encoding="utf-8")
    for split, name in ((None,"aw_schema_link.jsonl"),("dev","aw_schema_link.dev.jsonl"),("holdout","aw_schema_link.holdout.jsonl")):
        with (out / name).open("w", encoding="utf-8") as stream:
            for record in records:
                if split is None or record["split"] == split:
                    stream.write(json.dumps(record, ensure_ascii=False)+"\n")
    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "dataset": "eval/datasets/d3/aw_schema_link.jsonl",
                "count": len(records), "dev_count": len(DEV), "holdout_count": len(HOLD), "gold_sql_executed_count": len(records),
                "holdout_model_predictions": 0, "family_overlap": [], "gold_human_status": "pending_human_review",
                "dataset_sha256": hashlib.sha256((out / "aw_schema_link.jsonl").read_bytes()).hexdigest(),
                "source_sha256": source_hash, "protected_holdout_policy": "only automatic read-only labels; no model predictions before D5",
                "author_exposure_limit": "new synthetic D3 labels authored in this implementation; future heldout scores are not an independent external benchmark"}
    (out / "aw_schema_link_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# D3 AW 开发集 gold 第一遍 AI 预审（待人工复核）", "", "保留9题只核验程序标签；这里不展开保留题。", ""]
    for item in records[:len(DEV)]:
        lines += [f"## {item['id']}", "", item["question"], "", "AI建议通过；理由："+item["semantic_rationale"], "", "```sql", item["gold_sql"], "```", "", "标准表："+", ".join(item["gold_tables"]), "", "证据：[实际只读结果](../../artifacts/d3/a/gold/dev/"+item["id"]+".json)", "", "人工状态：pending_human_review。第二遍 AI 预审另存，不伪造签名。", ""]
    reviews = ROOT / "eval/reports/d3-ai-review"
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / "aw-dev-pass1.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
