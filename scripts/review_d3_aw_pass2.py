"""Record the second AI semantic review and independently recheck dev SQL.

The semantic notes below are an AI review of actual question/SQL/catalog,
not an automated proof, human signature, or prediction from the tested agent.
"""
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from hashlib import sha256

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql

NOTES = {
    "aw-01": "明确销售订单头记录数；COUNT全sales.salesorderheader，不误用采购头或明细行。",
    "aw-02": "明确采购订单头；COUNT purchasing.purchaseorderheader，不误用销售头。",
    "aw-03": "员工档案包含currentflag=false，COUNT employee全档案，没有偷偷只统计当前或salesperson。",
    "aw-04": "明确销售人员表记录数，COUNT sales.salesperson，不按employee职位或全员工替代。",
    "aw-05": "产品记录数，COUNT product，不按productmodel的型号数替代。",
    "aw-06": "不同颜色数且NULL排除；COUNT DISTINCT color和WHERE非NULL一致，不将空缺作为颜色。",
    "aw-07": "当前目录标价listprice，降序NULLS LAST并productid升序LIMIT5，不用成本或价格历史。",
    "aw-08": "按类别统计已归子类别的产品；product→subcategory→category真实外键内连接，COUNT产品行；按数量降序名称升序。",
    "aw-09": "供应商档案COUNT purchasing.vendor，避免客户/门店干扰。",
    "aw-10": "employee.jobtitle分组COUNT，降序人数升序职位LIMIT10；未增加currentflag筛选。",
    "aw-11": "2013销售头subtotal SUM，半开2013年筛选，无税运费；实际无匹配返回NULL，保留明确请求年份而不换年。",
    "aw-12": "2024采购头subtotal SUM，半开明确年，不含taxamt/freight；2024是首次预测前修订的题面，并非修改数据库或评分答案。",
    "aw-13": "地址档案按city分组COUNT地址记录，并非客户人数；降序记录数升序城市LIMIT5。",
    "aw-14": "2024 sales.orderdate限定后按MONTH分组COUNT订单头，月份数字INT与升序符合题意；没有任意补零月。",
    "aw-15": "原因字典salesreason按reasontype分组COUNT字典条目，不统计订单-原因桥表关联数。",
    "aw-16": "personid和storeid各自COUNT非NULL，独立计数可重叠；无错误互斥筛选。",
    "aw-17": "所有库存地点quantity聚合，inventory→product真实外键，按产品分组；数量降序productid升序LIMIT5，未用销量或工单数量。",
    "aw-18": "2024销售头期间，salesdetail.orderqty聚合；5表真实FK路径到产品大类；内连接按题面仅有子类别，避免采购数量/库存量替代。",
    "aw-19": "采购头关联shipmethod，COUNT订单头按运输方式分组；不统计销售头次数，真实FK无连接放大。",
    "aw-20": "2024销售订单头subtotal按territory分组，内连接排除空区域；金额降序NULLS LAST名称升序，无税费/收货地址区域混淆。",
    "aw-21": "currentflag=true且部门history.enddate为空是题面显式定义，按部门COUNT DISTINCT员工实体，排除历史任职重复行而非计salesperson。",
}


def main():
    dataset = ROOT / "eval/datasets/d3/aw_schema_link.dev.v2.jsonl"
    catalog_path = ROOT / "data/catalog/adventureworks.yaml"
    output = ROOT / "eval/reports/d3-ai-review/aw-dev-pass2.json"
    if output.exists():
        raise ValueError("第二遍记录已存在，不能覆盖。")
    catalog, settings = load_catalog(catalog_path), get_settings()
    rows = []
    for line in dataset.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        if item["split"] != "dev":
            raise ValueError("审核材料必须是仅开发集视图。")
        valid = validate_sql(item["gold_sql"], catalog)
        actual = execute_sql(valid.sql, settings.aw_db_url, settings.statement_timeout_ms, settings.max_rows)
        expected = item["gold_result"]
        if actual.rows != expected or actual.columns != item["gold_columns"] or actual.truncated:
            raise ValueError(f"{item['id']} 标准标签独立重跑不一致。")
        rows.append({"id": item["id"], "reference_status": "AI建议通过", "reason": NOTES[item["id"]],
                     "sql": valid.sql, "actual_rows": actual.rows, "actual_columns": actual.columns,
                     "evidence": [dataset.relative_to(ROOT).as_posix() + "#" + item["id"],
                                  catalog_path.relative_to(ROOT).as_posix(), "eval/artifacts/d3/a/gold"],
                     "db_reader": "qa_reader", "read_only": True, "timeout_ms": settings.statement_timeout_ms,
                     "system_actual_review": "本脚本未调用被测API；实际预测另存", "human_review": "pending_human_review"})
    report = {"review_pass": 2, "reviewer_type": "AI root semantic review plus independent read-only execution",
              "created_at_utc": datetime.now(timezone.utc).isoformat(), "dataset_sha256": sha256(dataset.read_bytes()).hexdigest(),
              "catalog_sha256": sha256(catalog_path.read_bytes()).hexdigest(), "count": len(rows), "rows": rows,
              "holdout_content_reviewed": False, "holdout_predictions": 0,
              "limitations": "AI预审不替代人工核对；空结果不足以证明SQL语义，故另核对每道题意与字段、FK、过滤、粒度、NULL、排序。"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# D3 AW 开发题第二遍 AI 预审", "", f"实际逐项核验 {len(rows)} 题；人工状态仍待审核。9道保留内容未展开或预测。", ""]
    lines.extend(f"- **{row['id']} — {row['reference_status']}**：{row['reason']}" for row in rows)
    lines += ["", "标准SQL独立只读重跑的完整结果、实际目录与题集摘要见同名JSON。首次预测之前已保留2013空边界，并将其他4道日期题另存2024开发修正版以验证非空关联。"]
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"reviewed": len(rows), "suggested_pass": len(rows), "human_status": "pending_human_review", "holdout_predictions": 0}))


if __name__ == "__main__":
    main()
