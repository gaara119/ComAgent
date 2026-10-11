"""Build a reviewable D2 metric proposal from read-only SQL checks.

This prepares evidence only. It never changes business defaults or records
human approval. The SQL examples intentionally include several tables when
needed for source preparation; online D2 NL2SQL remains single-table.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qa_agent.config import get_settings
from qa_agent.sql.executor import execute_sql


SQL_EXAMPLES = {
    "revenue_invoice": "SELECT SUM(total) AS revenue FROM public.invoice WHERE invoice_date >= DATE '2024-01-01' AND invoice_date < DATE '2025-01-01';",
    "average_invoice": "SELECT ROUND(AVG(total), 2) AS average_invoice_amount FROM public.invoice WHERE invoice_date >= DATE '2024-01-01' AND invoice_date < DATE '2025-01-01';",
    "repeat_customers": "SELECT COUNT(*) AS repeat_customer_count FROM (SELECT customer_id FROM public.invoice WHERE invoice_date >= DATE '2024-01-01' AND invoice_date < DATE '2025-01-01' GROUP BY customer_id HAVING COUNT(*) >= 2) AS repeat_customers;",
    "popular_tracks": "SELECT track_id, SUM(quantity) AS purchased_quantity FROM public.invoice_line WHERE invoice_id IN (SELECT invoice_id FROM public.invoice WHERE invoice_date >= DATE '2024-01-01' AND invoice_date < DATE '2025-01-01') GROUP BY track_id ORDER BY purchased_quantity DESC, track_id ASC LIMIT 5;",
    "revenue_reconciliation": "SELECT (SELECT SUM(total) FROM public.invoice) AS invoice_revenue, (SELECT SUM(unit_price * quantity) FROM public.invoice_line) AS detail_revenue, (SELECT SUM(total) FROM public.invoice) - (SELECT SUM(unit_price * quantity) FROM public.invoice_line) AS difference;",
    "available_dates": "SELECT MIN(invoice_date) AS first_date, MAX(invoice_date) AS last_date FROM public.invoice;",
}


def definitions() -> dict:
    return {
        "version": "d2-proposal-1",
        "review_status": "pending_human_review",
        "runtime_defaults_enabled": False,
        "reviewer_a": None,
        "reviewer_b": None,
        "reviewed_at_utc": None,
        "source": "Project-authored proposal based on D2 plan; not external company policy",
        "general": {
            "date_field": "invoice.invoice_date",
            "period": "Half-open [start_date, end_date); no missing period is silently filled",
            "region": "customer.country is customer residence; invoice.billing_country is invoice billing address; equality in current snapshot does not merge meanings",
            "unit": "Database amount unit; no inferred USD/CNY or payment status",
            "zero_denominator": "Return null and explain unavailable denominator",
        },
        "metrics": [
            {"id": "sales_revenue", "name": "发票销售额", "grain": "invoice", "expression": "SUM(invoice.total)", "empty_behavior": "Aggregate SUM yields NULL; presentation may say no available sales records but must not silently replace with zero", "alternative": "For track/artist analysis use SUM(invoice_line.unit_price * invoice_line.quantity), with invoice date filtering and no repeated SUM(invoice.total) after joining lines"},
            {"id": "average_invoice_amount", "name": "平均每张发票金额", "short_label_proposal": "客单价", "grain": "invoice", "expression": "AVG(invoice.total)", "empty_behavior": "NULL when no invoices", "alternative": "平均每位购买客户金额 = SUM(invoice.total) / COUNT(DISTINCT invoice.customer_id), kept as a separately named metric"},
            {"id": "repeat_customer_count", "name": "期间内复购客户数", "grain": "customer within explicitly given period", "expression": "COUNT of customers with COUNT(invoice_id) >= 2 in period", "empty_behavior": "0 when no qualifying customers", "limitation": "Invoice records are not evidence of successful payment; crossing period bounds is not inferred"},
            {"id": "popular_tracks", "name": "热门曲目", "grain": "track within explicitly given period", "expression": "SUM(invoice_line.quantity)", "default_from_total_plan": True, "alternatives": ["SUM(invoice_line.unit_price * invoice_line.quantity)", "COUNT of playlist_track memberships"], "tie_breaker": "track_id ascending", "distinct_object_rule_proposal": "曲目最受欢迎 follows purchased quantity; 客户谁买得最多 follows appendix amount definition. Generic subject-free 谁买得最多 remains unresolved; no global default is installed in D2"},
        ],
        "sql_examples": SQL_EXAMPLES,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="eval/artifacts/d2/source/metric-sql-checks.json")
    args = parser.parse_args()
    settings = get_settings()
    records = []
    for name, sql in SQL_EXAMPLES.items():
        result = execute_sql(sql, settings.db_url, settings.statement_timeout_ms)
        records.append({"id": name, "sql": sql, "status": "executed", "columns": result.columns,
                        "rows": result.rows, "truncated": result.truncated})
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    audit = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
             "command": ".venv/Scripts/python.exe scripts/prepare_d2_metric_proposal.py",
             "connection_role": "existing configured qa_reader; read-only transactions",
             "human_review": "pending", "records": records}
    output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    rule_file = ROOT / "data/rules/metric_definitions.json"
    rule_file.parent.mkdir(parents=True, exist_ok=True)
    current = json.loads(rule_file.read_text(encoding="utf8")) if rule_file.exists() else None
    approved_existing = bool(current and current.get("review_status") == "approved")
    if approved_existing:
        if current["metrics"] != definitions()["metrics"] or current["general"] != definitions()["general"]:
            raise ValueError("Approved business definitions differ from regenerated proposal; explicit new review is required")
    else:
        rule_file.write_text(json.dumps(definitions(), ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    lines = ["# D2 业务指标口径提案 待 A 和 B 人工确认", "", "本提案用于制作项目自编的 2–3 页指标手册。当前 `review_status=pending_human_review`，没有作为在线业务默认启用。SQL 已在现有只读 Chinook 快照实际执行；数据库未导入、重建或写入。", "", "请确认以下四项及短语区分，或给出修改：", "", "1. **销售额**：发票粒度用 `SUM(invoice.total)`；曲目或艺术家粒度用明细 `SUM(unit_price * quantity)`。JOIN 发票与明细后不能重复累加发票总额。", "2. **客单价**：拟明确命名为“平均每张发票金额”，采用 `AVG(invoice.total)`；“平均每位购买客户金额”另起名称，不当作同一指标。", "3. **复购客户**：指定期间内发票数量至少 2 张的客户。日期字段 `invoice_date`，期间采用左闭右开；没有期间时不悄悄补全。发票记录不等于已付款证据。", "4. **热门曲目**：沿用总计划的购买数量默认；销售额与歌单收录数是可选口径。拟保留附录“客户谁买得最多”的金额定义；缺查询对象的“谁买得最多”不自动套同一个全局默认。", "", "通用约定：客户所在地 `customer.country` 与账单地址 `invoice.billing_country` 保留各自含义；金额仅称数据库金额单位；空 SUM/AVG 保留 NULL，零分母保留 NULL 并说明；并列排序使用稳定 ID。", "", "## 已实际执行的 SQL 检查", ""]
    for record in records:
        lines += [f"### {record['id']}", "", "```sql", record["sql"], "```", "", "实际结果：`" + json.dumps(record["rows"], ensure_ascii=False) + "`", ""]
    lines += ["## 审核记录", "", "A：待确认。B：待确认。确认时间：暂无。", "", "机器定义：[metric_definitions.json](../../data/rules/metric_definitions.json)。实跑证据：[metric-sql-checks.json](../../eval/artifacts/d2/source/metric-sql-checks.json)。", ""]
    proposal = ROOT / "notes/d2/业务指标口径提案.md"
    proposal.parent.mkdir(parents=True, exist_ok=True)
    if not approved_existing:
        proposal.write_text("\n".join(lines), encoding="utf8")
    print(json.dumps({"sql_checks": len(records), "proposal": proposal.relative_to(ROOT).as_posix(),
                      "rules": rule_file.relative_to(ROOT).as_posix(), "status": "approved_preserved" if approved_existing else "pending_human_review"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
