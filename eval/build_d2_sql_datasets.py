"""Extend the preserved D1 labels to 50 SQL + 30 same-split variants; SELECT only."""
from __future__ import annotations
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psycopg
from eval.build_gold import _json_value
from eval.dataset import load_dataset, review_hash
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import validate_sql


def new_specs() -> list[dict]:
    result = []
    def add(n, q, statement, category, ordered=False, money=()):
        result.append({"id": f"sql-{n:02d}", "question": q, "gold_sql": statement,
                       "category": category, "split": "dev" if n <= 44 else "holdout",
                       "ordered": ordered, "monetary_columns": list(money),
                       "family_id": f"chinook-question-{n:02d}", "db_id": "chinook", "route": "sql"})
    add(31, "客户所在国家为 Italy 的客户有多少位？", "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';", "count")
    add(32, "客户所在国家为 Canada 的客户有多少位？", "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';", "count")
    add(33, "账单国家为 Canada 的全部发票总额是多少？", "SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Canada';", "aggregate", money=("total_amount",))
    add(34, "曲目表中最短的时长是多少毫秒？", "SELECT MIN(milliseconds) AS minimum_milliseconds FROM track;", "aggregate")
    add(35, "曲目表中最高的单价是多少？", "SELECT MAX(unit_price) AS maximum_unit_price FROM track;", "aggregate", money=("maximum_unit_price",))
    add(36, "按发票账单城市统计发票数，先按数量降序，并列按城市名称升序，返回前 10 个城市。", "SELECT billing_city, COUNT(*) AS invoice_count FROM invoice GROUP BY billing_city ORDER BY invoice_count DESC, billing_city ASC LIMIT 10;", "group", True)
    add(37, "按媒体类型编号统计曲目数，按媒体类型编号升序。", "SELECT media_type_id, COUNT(*) AS track_count FROM track GROUP BY media_type_id ORDER BY media_type_id;", "group", True)
    add(38, "找出文件字节数最大的 3 首曲目，返回编号、名称和字节数；按字节数降序，并列按曲目编号升序。", "SELECT track_id, name, bytes FROM track ORDER BY bytes DESC, track_id ASC LIMIT 3;", "top", True)
    add(39, "2023 年一共开了多少张发票？", "SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01';", "date")
    add(40, "2022 年 7 月 1 日（含）到 2022 年 10 月 1 日（不含）的发票总额是多少？", "SELECT SUM(total) AS total_amount FROM invoice WHERE invoice_date >= '2022-07-01' AND invoice_date < '2022-10-01';", "date", money=("total_amount",))
    add(41, "列出名称以 The 开头的前 8 位艺术家，区分大小写，返回编号和名称，按艺术家编号升序。", "SELECT artist_id, name FROM artist WHERE name LIKE 'The%' ORDER BY artist_id LIMIT 8;", "like", True)
    add(42, "列出名称恰好为 U2 的艺术家编号和名称，按编号升序。", "SELECT artist_id, name FROM artist WHERE name = 'U2' ORDER BY artist_id;", "filter", True)
    add(43, "没有填写州信息（state 为 NULL）的客户有多少位？", "SELECT COUNT(*) AS customer_count FROM customer WHERE state IS NULL;", "null")
    add(44, "客户所在国家为 Wakanda 的客户有多少位？保留原筛选值，没匹配时返回 0。", "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Wakanda';", "no_match")
    add(45, "客户所在国家为 France 的客户有多少位？", "SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'France';", "count")
    add(46, "列出名称恰好为 Metallica 的艺术家编号和名称，按编号升序。", "SELECT artist_id, name FROM artist WHERE name = 'Metallica' ORDER BY artist_id;", "filter", True)
    add(47, "账单国家为 United Kingdom 的发票平均总额是多少？请保留两位小数。", "SELECT ROUND(AVG(total), 2) AS average_total FROM invoice WHERE billing_country = 'United Kingdom';", "aggregate", money=("average_total",))
    add(48, "按专辑编号统计曲目数，先按数量降序，并列按专辑编号升序，返回前 5 个专辑编号与曲目数。", "SELECT album_id, COUNT(*) AS track_count FROM track GROUP BY album_id ORDER BY track_count DESC, album_id ASC LIMIT 5;", "group", True)
    add(49, "2024 年 1 月 1 日（含）到 2024 年 7 月 1 日（不含）一共开了多少张发票？", "SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2024-01-01' AND invoice_date < '2024-07-01';", "date")
    add(50, "列出名称包含 Air 的前 6 张专辑，区分大小写，返回编号和标题，按专辑编号升序。", "SELECT album_id, title FROM album WHERE title LIKE '%Air%' ORDER BY album_id LIMIT 6;", "like", True)
    return result


def variant_specs() -> list[tuple[str, str, str]]:
    # Five variants per category; holdout remains tied to the base question.
    return [
        ("typo", "sql-02", "来自巴稀的客户有多少位？"),
        ("typo", "sql-05", "列出来自美囯的客户编号、城市和州，按客户编号升序。"),
        ("typo", "sql-07", "列出职位为 Sales Suport Agent 的员工编号、名字和姓氏，按员工编号升序。"),
        ("typo", "sql-45", "客户所在国家为 Frnace 的客户有多少位？"),
        ("typo", "sql-46", "列出名称恰好为 Metalica 的艺术家编号和名称，按编号升序。"),
        ("alias", "sql-05", "列出来自老美的客户编号、城市和州，按客户编号升序。"),
        ("alias", "sql-31", "来自意大利的客户有多少位？"),
        ("alias", "sql-32", "来自加拿大的客户有多少位？"),
        ("alias", "sql-45", "来自法国的客户有多少位？"),
        ("alias", "sql-47", "账单国家为英国的发票平均总额是多少？请保留两位小数。"),
        ("pinyin", "sql-02", "来自 ba xi 的客户有多少位？"),
        ("pinyin", "sql-31", "客户所在国家为 yi da li 的客户有多少位？"),
        ("pinyin", "sql-32", "客户所在国家为 jia na da 的客户有多少位？"),
        ("pinyin", "sql-45", "客户所在国家为 fa guo 的客户有多少位？"),
        ("pinyin", "sql-47", "账单国家为 ying guo 的发票平均总额是多少？请保留两位小数。"),
        ("mixed_language", "sql-02", "country 是 Brazil 的 customer 有多少位？"),
        ("mixed_language", "sql-05", "列出 country 为 USA 的客户编号 customer_id、城市 city 和州 state，按 customer_id 升序。"),
        ("mixed_language", "sql-09", "全部 invoice 的 total 加起来是多少？"),
        ("mixed_language", "sql-33", "billing_country 为 Canada 的全部 invoice 的 total 总和是多少？"),
        ("mixed_language", "sql-46", "artist 的 name 恰好为 Metallica，列出 artist_id 和 name，按 artist_id 升序。"),
        ("colloquial", "sql-01", "咱们客户表一共有几个人？"),
        ("colloquial", "sql-02", "帮我数数，来自巴西的客户有几位呀？"),
        ("colloquial", "sql-10", "这批曲目的平均长度是几毫秒？"),
        ("colloquial", "sql-34", "曲目里最短的一首有几毫秒呀？"),
        ("colloquial", "sql-49", "帮我数一下，2024 年上半年，也就是 1 月 1 日起到 7 月 1 日之前，开了几张发票？"),
        ("extra_words", "sql-02", "你好，请帮忙查一下来自巴西的客户有多少位，谢谢。"),
        ("extra_words", "sql-26", "麻烦帮我看看，有多少位客户没有填写公司名称，也就是 company 为 NULL 呢？谢谢。"),
        ("extra_words", "sql-39", "请帮我查一查，2023 年一共开了多少张发票，非常感谢。"),
        ("extra_words", "sql-44", "麻烦查一下客户所在国家为 Wakanda 的客户有多少位，保留原值，没匹配返回 0，谢谢。"),
        ("extra_words", "sql-50", "您好，请列出名称包含 Air 的前 6 张专辑，区分大小写，返回编号和标题，按专辑编号升序，谢谢。"),
    ]


def build(output_dir: Path) -> dict:
    baseline = ROOT / "eval/datasets/nl2sql_chinook_d1_acceptance.jsonl"
    items = deepcopy(load_dataset(baseline)) + new_specs()
    source_hash = hashlib.sha256((ROOT / "data/db/Chinook_PostgreSql.sql").read_bytes()).hexdigest()
    settings = get_settings()
    catalog = load_catalog(settings.catalog_path)
    old_responses = ROOT / "eval/reports/d1-acceptance/sql-dev/responses.jsonl"
    exposure_files = [old_responses, ROOT / "eval/reports/d1-dev-draft/responses.jsonl"]
    exposed = set()
    for path in exposure_files:
        if path.exists():
            exposed.update(json.loads(line)["id"] for line in path.read_text(encoding="utf8").splitlines() if line)
    gold_checks = []
    with psycopg.connect(settings.db_url, options="-c default_transaction_read_only=on -c statement_timeout=5000") as conn:
        for item in items:
            validate_sql(item["gold_sql"], catalog)
            with conn.cursor() as cursor:
                cursor.execute(item["gold_sql"])
                item["gold_columns"] = [d.name for d in cursor.description]
                item["column_types"] = ["number" if d.type_code in {20,21,23,700,701,1700}
                                        else "temporal" if d.type_code in {1082,1114,1184,1083,1266}
                                        else "text" for d in cursor.description]
                item["integer_columns"] = [i for i,d in enumerate(cursor.description) if d.type_code in {20,21,23}]
                actual = [dict(zip(item["gold_columns"], map(_json_value,row))) for row in cursor.fetchall()]
            original = item.get("gold_result")
            gold_checks.append({"id": item["id"], "sql": item["gold_sql"], "status": "EXECUTED",
                                "rows": len(actual), "matches_d1_gold": None if original is None else original == actual})
            if original is not None and original != actual:
                raise ValueError("D1 gold changed against current database: " + item["id"])
            item.update(gold_result=actual, source_sha256=source_hash,
                        gold_generated_at_utc=datetime.now(timezone.utc).isoformat(),
                        expected_status="EMPTY_RESULT" if not actual else "SUCCEEDED",
                        exposure_history={"d1_model_exposed": item["id"] in exposed,
                                          "d1_prediction_records": [str(p.relative_to(ROOT)).replace("\\", "/")
                                                                    for p in exposure_files if p.exists()],
                                          "d2_model_exposed": False})
            item["gold_review"] = {"status": "needs_human_review", "reviewer": None,
                                   "content_sha256": review_hash(item)}
            if item["split"] == "holdout" and item["id"] in exposed:
                raise ValueError("An exposed D1 question was assigned to holdout")
    lookup = {item["id"]: item for item in items}
    variants = []
    for n,(kind, base_id, question) in enumerate(variant_specs(), 1):
        item = deepcopy(lookup[base_id])
        item.update(id=f"robust-{n:02d}", base_id=base_id, question=question, variant_type=kind,
                    exposure_history={"d1_model_exposed": False, "d2_model_exposed": False,
                                      "base_split": lookup[base_id]["split"]})
        item["gold_review"] = {"status": "needs_human_review", "reviewer": None,
                               "content_sha256": review_hash(item)}
        variants.append(item)
    assert len(items) == 50 and Counter(i["split"] for i in items) == {"dev":35,"holdout":15}
    assert len(variants) == 30 and Counter(i["split"] for i in variants) == {"dev":21,"holdout":9}
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, dataset in [("nl2sql_chinook_d2.jsonl", items), ("robust.jsonl", variants)]:
        target = output_dir / filename
        target.write_text("".join(json.dumps(item, ensure_ascii=False)+"\n" for item in dataset), encoding="utf8")
        load_dataset(target)
    manifest = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "parent": baseline.relative_to(ROOT).as_posix(),
                "parent_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
                "sql_counts": dict(Counter(i["split"] for i in items)),
                "robust_counts": dict(Counter(i["split"] for i in variants)),
                "sql_category_counts": dict(Counter(i["category"] for i in items)),
                "robust_type_counts": dict(Counter(i["variant_type"] for i in variants)),
                "gold_sql_executed": 50, "model_predictions_in_build": 0,
                "human_accepted_count": 0, "holdout_model_predictions": 0,
                "gold_checks": gold_checks}
    (output_dir / "d2_sql.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf8")
    review_dir = output_dir / "review_d2"
    review_dir.mkdir(exist_ok=True)
    lines = ["# D2 SQL 与鲁棒题 gold 人工审核表", "", "50 条 gold 已只读实跑；30 变体复用同源 gold。业务含义仍待人工审核。保留题不调用模型，D5 冻结后再测。", ""]
    for item in items + variants:
        lines += [f"## {item['id']} · {item['split']} · {item.get('variant_type',item['category'])}", "",
                  f"同源：{item['family_id']}；审核：needs_human_review。", "", item["question"], "",
                  "```sql", item["gold_sql"], "```", "", "```json", json.dumps(item["gold_result"],ensure_ascii=False,indent=2), "```", "",
                  "- [ ] 已核对题意、字段、条件、单位和排序。", "- [ ] 已核对实际 SQL 结果并记录审核人。", ""]
    (review_dir / "sql_gold_review.md").write_text("\n".join(lines), encoding="utf8")
    return {k:v for k,v in manifest.items() if k != "gold_checks"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,default=ROOT / "eval/datasets")
    print(json.dumps(build(p.parse_args().output_dir),ensure_ascii=False,indent=2))
