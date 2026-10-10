"""Build 30 SQL labels from the real Chinook database, not model predictions.

All generated labels remain needs_human_review. Running ALL gold SQL here is
label verification; the holdout questions are never sent to /api/chat.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from eval.dataset import DEFAULT_DATASET, ROOT, load_dataset, reviewed, review_hash
from qa_agent.config import get_settings, sanitize_error


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _specs(first_year: int, last_year: int, hire_cutoff: int) -> list[dict[str, Any]]:
    specifications: list[dict[str, Any]] = []

    def add(number: int, question: str, sql: str, category: str, split: str,
            *, ordered: bool = False, money: tuple[str, ...] = (), family: str | None = None) -> None:
        specifications.append({"id": f"sql-{number:02d}", "question": question,
                               "gold_sql": sql, "category": category, "split": split,
                               "ordered": ordered, "monetary_columns": list(money),
                               "family_id": family or f"chinook-question-{number:02d}",
                               "db_id": "chinook", "route": "sql"})

    add(1, "客户表共有多少位客户？", "SELECT COUNT(*) AS customer_count FROM customer;", "count", "dev")
    add(2, "来自巴西的客户有多少位？", "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';", "count", "dev", family="brazil_customer")
    add(3, "曲目表中时长超过 5 分钟的曲目有多少首？", "SELECT COUNT(*) AS track_count FROM track WHERE milliseconds > 300000;", "count", "holdout")
    add(4, "列出来自巴西的客户编号、名字、姓氏和城市，按客户编号升序。", "SELECT customer_id, first_name, last_name, city FROM customer WHERE country = 'Brazil' ORDER BY customer_id;", "filter", "dev", ordered=True, family="brazil_customer")
    add(5, "列出来自美国的客户编号、城市和州，按客户编号升序。", "SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;", "filter", "dev", ordered=True)
    add(6, "列出单价高于 0.99 的前 10 首曲目的编号、名称和单价，按曲目编号升序。", "SELECT track_id, name, unit_price FROM track WHERE unit_price > 0.99 ORDER BY track_id LIMIT 10;", "filter", "dev", ordered=True, money=("unit_price",))
    add(7, "列出职位为 Sales Support Agent 的员工编号、名字和姓氏，按员工编号升序。", "SELECT employee_id, first_name, last_name FROM employee WHERE title = 'Sales Support Agent' ORDER BY employee_id;", "filter", "dev", ordered=True)
    add(8, "列出总额不少于 10 的前 10 张发票的编号、日期和总额，按发票编号升序。", "SELECT invoice_id, invoice_date, total FROM invoice WHERE total >= 10 ORDER BY invoice_id LIMIT 10;", "filter", "holdout", ordered=True, money=("total",))
    add(9, "全部发票的总金额是多少？", "SELECT SUM(total) AS total_amount FROM invoice;", "aggregate", "dev", money=("total_amount",), family="invoice_global_totals")
    add(10, "全部曲目的平均时长是多少毫秒？", "SELECT AVG(milliseconds) AS average_milliseconds FROM track;", "aggregate", "dev")
    add(11, "全部发票的平均总额是多少？请保留两位小数。", "SELECT AVG(total) AS average_total FROM invoice;", "aggregate", "dev", money=("average_total",), family="invoice_global_totals")
    add(12, "客户所在国家共有多少种？", "SELECT COUNT(DISTINCT country) AS country_count FROM customer;", "aggregate", "holdout")
    add(13, "按客户所在国家统计客户数，先按客户数降序，并列时按国家名称升序。", "SELECT country, COUNT(*) AS customer_count FROM customer GROUP BY country ORDER BY customer_count DESC, country ASC;", "group", "dev", ordered=True)
    add(14, "按流派编号统计曲目数，先按曲目数降序，并列时按流派编号升序。", "SELECT genre_id, COUNT(*) AS track_count FROM track GROUP BY genre_id ORDER BY track_count DESC, genre_id ASC;", "group", "dev", ordered=True)
    add(15, "按发票的账单国家统计销售总额，先按销售总额降序，并列时按国家名称升序。", "SELECT billing_country, SUM(total) AS sales_total FROM invoice GROUP BY billing_country ORDER BY sales_total DESC, billing_country ASC;", "group", "dev", ordered=True, money=("sales_total",))
    add(16, "按员工职位统计人数，按职位名称升序。", "SELECT title, COUNT(*) AS employee_count FROM employee GROUP BY title ORDER BY title ASC;", "group", "holdout", ordered=True)
    add(17, "找出时长最长的 5 首曲目，返回编号、名称和毫秒时长；按时长降序，并列按编号升序。", "SELECT track_id, name, milliseconds FROM track ORDER BY milliseconds DESC, track_id ASC LIMIT 5;", "top", "dev", ordered=True)
    add(18, "找出总额最高的 5 张发票，返回编号和总额；按总额降序，并列按编号升序。", "SELECT invoice_id, total FROM invoice ORDER BY total DESC, invoice_id ASC LIMIT 5;", "top", "dev", ordered=True, money=("total",))
    add(19, "按姓氏降序取前 5 位客户，返回编号、名字和姓氏；姓氏相同时按客户编号升序。", "SELECT customer_id, first_name, last_name FROM customer ORDER BY last_name DESC, customer_id ASC LIMIT 5;", "top", "dev", ordered=True)
    add(20, "按名称升序取前 5 位艺术家，返回编号和名称；名称相同按艺术家编号升序。", "SELECT artist_id, name FROM artist ORDER BY name ASC, artist_id ASC LIMIT 5;", "top", "holdout", ordered=True)
    add(21, f"列出 {first_year} 年的前 10 张发票，返回编号、日期和总额，按发票编号升序。", f"SELECT invoice_id, invoice_date, total FROM invoice WHERE invoice_date >= '{first_year}-01-01' AND invoice_date < '{first_year + 1}-01-01' ORDER BY invoice_id LIMIT 10;", "date", "dev", ordered=True, money=("total",))
    add(22, f"列出 {hire_cutoff} 年 1 月 1 日之前入职的员工编号、名字和入职日期，按员工编号升序。", f"SELECT employee_id, first_name, hire_date FROM employee WHERE hire_date < '{hire_cutoff}-01-01' ORDER BY employee_id;", "date", "dev", ordered=True)
    add(23, f"{last_year} 年一共开了多少张发票？", f"SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '{last_year}-01-01' AND invoice_date < '{last_year + 1}-01-01';", "date", "holdout")
    add(24, "列出邮箱以 @gmail.com 结尾的客户编号、名字和邮箱，按客户编号升序。", "SELECT customer_id, first_name, email FROM customer WHERE email LIKE '%@gmail.com' ORDER BY customer_id;", "like", "dev", ordered=True)
    add(25, "查找名称含 love 的前 10 首曲目，不区分英文大小写，返回编号和名称，按曲目编号升序。", "SELECT track_id, name FROM track WHERE name ILIKE '%love%' ORDER BY track_id LIMIT 10;", "like", "holdout", ordered=True)
    add(26, "有多少位客户没有填写公司名称（company 为 NULL）？", "SELECT COUNT(*) AS customer_count FROM customer WHERE company IS NULL;", "null", "dev")
    add(27, "列出没有作曲者信息（composer 为 NULL）的前 10 首曲目编号和名称，按曲目编号升序。", "SELECT track_id, name FROM track WHERE composer IS NULL ORDER BY track_id LIMIT 10;", "null", "dev", ordered=True)
    add(28, "列出没有直属上级（reports_to 为 NULL）的员工编号、名字和姓氏，按员工编号升序。", "SELECT employee_id, first_name, last_name FROM employee WHERE reports_to IS NULL ORDER BY employee_id;", "null", "holdout", ordered=True)
    add(29, "列出国家字段为 Antarctica 的客户编号、名字和姓氏，按客户编号升序。", "SELECT customer_id, first_name, last_name FROM customer WHERE country = 'Antarctica' ORDER BY customer_id;", "no_match", "dev", ordered=True)
    add(30, "账单国家字段为 Atlantis 的发票总金额是多少？若没有匹配记录，按 SQL SUM 的语义保留 NULL。", "SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Atlantis';", "no_match", "holdout", money=("total_amount",))
    return specifications


def build(output: Path = DEFAULT_DATASET) -> dict[str, Any]:
    settings = get_settings()
    source = ROOT / "data/db/Chinook_PostgreSql.sql"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    previous = {item["id"]: item for item in load_dataset(output)} if output.exists() else {}
    with psycopg.connect(settings.db_url, options="-c default_transaction_read_only=on -c statement_timeout=5000") as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT MIN(invoice_date), MAX(invoice_date) FROM public.invoice")
            earliest, latest = cursor.fetchone()
            cursor.execute("SELECT EXTRACT(YEAR FROM MAX(hire_date))::integer FROM public.employee")
            hire_cutoff = cursor.fetchone()[0]
            specifications = _specs(earliest.year, latest.year, hire_cutoff)
            for item in specifications:
                cursor.execute(item["gold_sql"])
                columns = [description.name for description in cursor.description]
                item["gold_columns"] = columns
                item["column_types"] = [
                    "number" if d.type_code in {20, 21, 23, 700, 701, 1700}
                    else "temporal" if d.type_code in {1082, 1114, 1184, 1083, 1266}
                    else "text" for d in cursor.description]
                item["gold_result"] = [dict(zip(columns, (_json_value(value) for value in row))) for row in cursor.fetchall()]
                item["source_sha256"] = source_hash
                item["gold_generated_at_utc"] = datetime.now(timezone.utc).isoformat()
                item["gold_review"] = {"status": "needs_human_review", "reviewer": None,
                                       "content_sha256": review_hash(item)}
                if item["id"] in previous and reviewed(previous[item["id"]]) and review_hash(previous[item["id"]]) == review_hash(item):
                    item["gold_review"] = previous[item["id"]]["gold_review"]
    assert len(specifications) == 30
    split_counts = Counter(item["split"] for item in specifications)
    assert split_counts == {"dev": 21, "holdout": 9}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in specifications), encoding="utf-8")
    # Validate family grouping and unique IDs after materialization.
    load_dataset(output)
    manifest = {
        "source_sql": str(source.relative_to(ROOT)), "source_sha256": source_hash,
        "dataset_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "actual_invoice_date_range": [earliest.isoformat(), latest.isoformat()],
        "split_counts": dict(split_counts), "category_counts": dict(Counter(item["category"] for item in specifications)),
        "gold_sql_executed": 30, "gold_build_model_prediction_count": 0, "gold_build_holdout_prediction_count": 0,
        "gold_pending_human_review": sum(not reviewed(item) for item in specifications),
        "notes": "上述执行与预测计数仅描述本次题库构建：运行 30 条 gold SQL 是标注核验，构建过程没有模型预测。实际系统预测次数和成绩以 eval/reports 下各次运行记录为准。日期取自真实导入数据库。",
    }
    (output.parent / "nl2sql_chinook_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_DATASET)
    args = parser.parse_args()
    try:
        manifest = build(args.output)
    except (OSError, psycopg.Error, ValueError) as exc:
        print(sanitize_error(exc, get_settings()), file=sys.stderr)
        return 2
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
