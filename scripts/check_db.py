"""Record real data, verify the reader's privileges, and prepare B's SQL handoff."""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from qa_agent.config import get_settings, sanitize_error
from scripts.bootstrap_db import timestamp, write_json

TOP_ARTISTS_SQL = """SELECT ar.artist_id, ar.name,
       SUM(il.unit_price * il.quantity) AS revenue
FROM public.invoice_line il
JOIN public.track t ON il.track_id = t.track_id
JOIN public.album al ON t.album_id = al.album_id
JOIN public.artist ar ON al.artist_id = ar.artist_id
GROUP BY ar.artist_id, ar.name
ORDER BY revenue DESC, ar.artist_id ASC
LIMIT 10;"""

COUNTRY_DIFFERENCE_SQL = """SELECT
  COUNT(*) FILTER (WHERE i.billing_country <> c.country) AS non_null_difference_count,
  COUNT(*) FILTER (WHERE i.billing_country IS DISTINCT FROM c.country) AS null_aware_difference_count,
  COUNT(*) FILTER (WHERE i.billing_country IS NULL OR c.country IS NULL) AS rows_with_null_country,
  COUNT(*) AS compared_invoice_count
FROM public.invoice i
JOIN public.customer c USING (customer_id);"""


def normalized(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [normalized(item) for item in value]
    return value


def main() -> None:
    settings = get_settings()
    report = {"checked_at": timestamp(), "database": "chinook", "status": "checking"}
    with psycopg.connect(settings.db_url, autocommit=True, connect_timeout=5, row_factory=dict_row) as conn:
        report["server_version"] = conn.execute("SHOW server_version").fetchone()["server_version"]
        report["connection"] = conn.execute("SELECT current_database() AS database, current_user AS reader_user, "
                                             "current_schema() AS schema").fetchone()
        table_rows = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
        counts = {}
        for row in table_rows:
            table = row["tablename"]
            counts[table] = conn.execute(sql.SQL("SELECT COUNT(*) AS count FROM public.{}")
                                        .format(sql.Identifier(table))).fetchone()["count"]
        report["table_row_counts"] = counts
        report["invoice_date_range"] = normalized(conn.execute("SELECT MIN(invoice_date) AS min_date, "
                                                                "MAX(invoice_date) AS max_date FROM public.invoice").fetchone())
        report["invoice_years"] = [row["year"] for row in conn.execute("SELECT DISTINCT EXTRACT(YEAR FROM invoice_date)::int AS year "
                                                                       "FROM public.invoice ORDER BY year")]
        report["customer_countries"] = [row["country"] for row in conn.execute("SELECT DISTINCT country FROM public.customer ORDER BY country")]
        role = conn.execute("SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolinherit "
                            "FROM pg_roles WHERE rolname=current_user").fetchone()
        report["reader_role"] = role
        privileges = conn.execute("SELECT table_name, "
                                  "has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'SELECT') AS can_select, "
                                  "has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS can_write "
                                  "FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name").fetchall()
        report["table_privileges"] = privileges
        report["database_privileges"] = conn.execute("SELECT has_database_privilege(current_user, current_database(), 'CREATE') AS can_create_schema, "
                                                     "has_database_privilege(current_user, current_database(), 'TEMP') AS can_create_temp, "
                                                     "has_schema_privilege(current_user, 'public', 'CREATE') AS can_create_in_public").fetchone()
        report["reader_defaults"] = {name: conn.execute(sql.SQL("SHOW {}").format(sql.Identifier(name))).fetchone()[name]
                                     for name in ["default_transaction_read_only", "statement_timeout", "lock_timeout"]}
        if report["reader_defaults"]["default_transaction_read_only"] != "on":
            raise RuntimeError("Reader default transaction must be read only")
        if any(role[key] for key in ["rolsuper", "rolcreatedb", "rolcreaterole", "rolreplication", "rolbypassrls"]):
            raise RuntimeError("Reader has elevated role attributes")
        if any(not row["can_select"] or row["can_write"] for row in privileges):
            raise RuntimeError("Reader must have SELECT and no write privilege on each business table")
        if any(report["database_privileges"].values()):
            raise RuntimeError("Reader must not have database/schema creation or temporary-table privileges")
        # Zero matching rows and rollback guarantee that this check never changes business data.
        # READ WRITE deliberately bypasses the changeable read-only default to prove ACL enforcement.
        try:
            with conn.transaction():
                conn.execute("SET TRANSACTION READ WRITE")
                conn.execute("UPDATE public.customer SET country = country WHERE FALSE")
                raise RuntimeError("Reader unexpectedly passed the zero-row UPDATE permission check")
        except psycopg.errors.InsufficientPrivilege as exc:
            report["zero_row_update_check"] = {"sqlstate": exc.sqlstate, "blocked": True,
                                               "transaction_mode": "READ WRITE", "business_rows_changed": 0}
        top_artists = normalized(conn.execute(TOP_ARTISTS_SQL).fetchall())
        country_difference = conn.execute(COUNTRY_DIFFERENCE_SQL).fetchone()
        report["country_difference"] = country_difference
    report["status"] = "passed"
    write_json(ROOT / "data/db/db_check.json", normalized(report))
    handoff = {"generated_at": timestamp(), "dataset_version": "Chinook 1.4.5",
               "scope": "A-to-B source preparation; direct reviewed SQL, not an NL2SQL evaluation",
               "revenue_definition": "Sum invoice_line.unit_price * invoice_line.quantity over all invoices; database amount unit, no inferred currency",
               "top_artists": {"sql": TOP_ARTISTS_SQL, "rows": top_artists},
               "country_semantics": {"customer.country": "客户所在地国家", "invoice.billing_country": "发票账单地址国家",
                                     "sql": COUNTRY_DIFFERENCE_SQL, "result": country_difference},
               "invoice_date_range": report["invoice_date_range"], "invoice_years": report["invoice_years"],
               "source_manifest": "data/db/source_manifest.json"}
    write_json(ROOT / "data/handoff/A_to_B_chinook.json", handoff)
    lines = ["# A → B：Chinook 实际查询交接", "", f"取数时间（UTC）：{handoff['generated_at']}", "",
             "数据源：官方 Chinook 1.4.5；本文件由只读账号执行实际 SQL 产生，供后续文档选材。", "",
             "销售额口径：汇总发票明细的单价 × 数量，覆盖全部已导入年份；原数据未声明币种，金额不擅自标注币种。", "",
             "| 排名 | artist_id | 艺术家英文名 | 销售额 |", "|---|---|---|---|"]
    for index, row in enumerate(top_artists, 1):
        lines.append(f"| {index} | {row['artist_id']} | {row['name']} | {row['revenue']} |")
    lines += ["", "```sql", TOP_ARTISTS_SQL, "```", "", "客户国家与账单国家分别是不同业务字段，不能互换。", "",
              f"非空国家不同的发票数：{country_difference['non_null_difference_count']}；包括 NULL 的不同数：{country_difference['null_aware_difference_count']}；含 NULL 国家数：{country_difference['rows_with_null_country']}。", "",
              "```sql", COUNTRY_DIFFERENCE_SQL, "```", "",
              f"发票实际日期范围：{report['invoice_date_range']['min_date']} 至 {report['invoice_date_range']['max_date']}。", "",
              "本次原始数据如果差异为 0，不能据此声称演示已展示两种地区口径的数值差异；后续可解释字段含义或使用单独标明的补充数据。", "",
              "来源、原始文件 SHA256 与 MIT 许可证见 data/db/source_manifest.json 和 data/db/LICENSE.md。", ""]
    (ROOT / "data/handoff/A_to_B_chinook.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Database checks passed: {len(counts)} tables; customer={counts['customer']}, track={counts['track']}, invoice={counts['invoice']}.")
    print(f"Invoice years: {report['invoice_years']}; reader SELECT-only ACL verified with zero business rows changed.")
    print(f"Top artist: {top_artists[0]['name']}, revenue={top_artists[0]['revenue']}; country differences={country_difference['null_aware_difference_count']}.")
    print("Saved data/db/db_check.json and data/handoff/A_to_B_chinook.{json,md}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Database verification failed: {sanitize_error(exc, get_settings())}", file=sys.stderr)
        sys.exit(1)
