"""Create 15 new, DEV-only natural FK-join regression labels using read-only SQL.

These are draft references until human review. Original datasets are untouched.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql
from qa_agent.sql.validator import validate_sql
from qa_agent.sql.repair_guard import validate_chinook_fk_joins

CASES = [
    ("Metallica有多少张专辑？", "SELECT COUNT(*) AS album_count FROM album a JOIN artist r ON a.artist_id=r.artist_id WHERE r.name='Metallica'", False, [0]),
    ("Metallcia有多少张专辑？", "SELECT COUNT(*) AS album_count FROM album a JOIN artist r ON a.artist_id=r.artist_id WHERE r.name='Metallica'", False, [0]),
    ("AC/DC一共有几首曲目？", "SELECT COUNT(*) AS track_count FROM track t JOIN album a ON t.album_id=a.album_id JOIN artist r ON a.artist_id=r.artist_id WHERE r.name='AC/DC'", False, [0]),
    ("Protected AAC audio file这种媒体类型有多少首曲目？", "SELECT COUNT(*) AS track_count FROM track t JOIN media_type m ON t.media_type_id=m.media_type_id WHERE m.name='Protected AAC audio file'", False, [0]),
    ("Vaporwave流派有多少首曲目？", "SELECT COUNT(*) AS track_count FROM track t JOIN genre g ON t.genre_id=g.genre_id WHERE g.name='Vaporwave'", False, [0]),
    ("Iron Maiden的专辑有哪些？按专辑编号从小到大列出编号和标题。", "SELECT a.album_id,a.title FROM album a JOIN artist r ON a.artist_id=r.artist_id WHERE r.name='Iron Maiden' ORDER BY a.album_id ASC", True, [0]),
    ("专辑最多的5位艺术家是谁？列出艺术家编号、名字和专辑数，同数量时按艺术家编号从小到大。", "SELECT r.artist_id,r.name,COUNT(a.album_id) AS album_count FROM artist r JOIN album a ON a.artist_id=r.artist_id GROUP BY r.artist_id,r.name ORDER BY album_count DESC,r.artist_id ASC LIMIT 5", True, [0,2]),
    ("按购买数量排，最热门的3首曲目是什么？列出曲目编号、名称和购买数量，同数量按曲目编号升序。", "SELECT t.track_id,t.name,SUM(l.quantity) AS purchased_quantity FROM track t JOIN invoice_line l ON l.track_id=t.track_id GROUP BY t.track_id,t.name ORDER BY purchased_quantity DESC,t.track_id ASC LIMIT 3", True, [0,2]),
    ("每位客户开过几张发票？没有发票的也要，列出客户编号、名字、姓氏和发票数，按客户编号升序。", "SELECT c.customer_id,c.first_name,c.last_name,COUNT(i.invoice_id) AS invoice_count FROM customer c LEFT JOIN invoice i ON i.customer_id=c.customer_id GROUP BY c.customer_id,c.first_name,c.last_name ORDER BY c.customer_id ASC", True, [0,3]),
    ("客户所在地在巴西的客户一共开过多少张发票？", "SELECT COUNT(*) AS invoice_count FROM invoice i JOIN customer c ON i.customer_id=c.customer_id WHERE c.country='Brazil'", False, [0]),
    ("账单国家是France的发票一共买了多少首Rock流派的曲目？按购买数量计。", "SELECT SUM(l.quantity) AS purchased_quantity FROM invoice i JOIN invoice_line l ON l.invoice_id=i.invoice_id JOIN track t ON l.track_id=t.track_id JOIN genre g ON t.genre_id=g.genre_id WHERE i.billing_country='France' AND g.name='Rock'", False, [0]),
    ("Led Zeppelin所有曲目的销售额合计是多少？", "SELECT SUM(l.unit_price*l.quantity) AS revenue FROM invoice_line l JOIN track t ON l.track_id=t.track_id JOIN album a ON t.album_id=a.album_id JOIN artist r ON a.artist_id=r.artist_id WHERE r.name='Led Zeppelin'", False, []),
    ("名字叫Jane、姓氏为Peacock的员工负责几位客户？", "SELECT COUNT(*) AS customer_count FROM customer c JOIN employee e ON c.support_rep_id=e.employee_id WHERE e.first_name='Jane' AND e.last_name='Peacock'", False, [0]),
    ("每种媒体类型有几首曲目？没有曲目的也保留，列出类型编号、名称和曲目数，按类型编号升序。", "SELECT m.media_type_id,m.name,COUNT(t.track_id) AS track_count FROM media_type m LEFT JOIN track t ON t.media_type_id=m.media_type_id GROUP BY m.media_type_id,m.name ORDER BY m.media_type_id ASC", True, [0,2]),
    ("哪些专辑没有曲目？列出专辑编号和标题，按专辑编号升序。", "SELECT a.album_id,a.title FROM album a LEFT JOIN track t ON t.album_id=a.album_id GROUP BY a.album_id,a.title HAVING COUNT(t.track_id)=0 ORDER BY a.album_id ASC", True, [0]),
]


def main():
    output = ROOT / "eval/datasets/oct12/chinook_join_dev_v1.jsonl"
    evidence = ROOT / "eval/artifacts/oct12/join-gold"
    if output.exists() or evidence.exists():
        raise SystemExit("Use a new version; existing labels/evidence must not be overwritten")
    evidence.mkdir(parents=True)
    settings = get_settings()
    catalog = load_catalog(settings.catalog_path)
    source = sha256(settings.catalog_path.read_bytes()).hexdigest()
    items, records = [], []
    for number, (question, sql, ordered, integer_cols) in enumerate(CASES, 1):
        case_id = f"oct12-join-{number:02d}"
        valid = validate_sql(sql, catalog)
        validate_chinook_fk_joins(valid.sql, catalog)
        result = execute_sql(valid.sql, settings.db_url, settings.statement_timeout_ms, max_rows=200)
        observed_types = ["number" if (index in integer_cols or name == "revenue") else "text" for index, name in enumerate(result.columns)]
        record = {"id": case_id, "command": [sys.executable, "-B", "scripts/build_oct12_join_dev.py"],
                  "sql": valid.sql, "status": "EXECUTED", "columns": result.columns, "rows": result.rows,
                  "read_only": True, "statement_timeout_ms": settings.statement_timeout_ms,
                  "generated_at_utc": datetime.now(timezone.utc).isoformat(), "truncated": result.truncated}
        records.append(record)
        (evidence / (case_id + ".json")).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        item = {"id": case_id, "question": question, "gold_sql": valid.sql, "category": "fk_join",
                "split": "dev", "family_id": f"oct12-join-family-{number if number != 2 else 1:02d}",
                "source_sha256": source, "source": "Oct12 project-authored natural Chinook FK regression",
                "gold_columns": result.columns, "gold_result": result.table, "column_types": observed_types,
                "integer_columns": integer_cols, "monetary_columns": [0] if number == 12 else [],
                "ordered": ordered, "gold_review": {"status": "pending_human_review"},
                "expected_status": "SUCCEEDED" if result.rows else "EMPTY_RESULT", "gold_evidence": record["id"] + ".json"}
        items.append(item)
        print(case_id, "gold executed", result.row_count, flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf-8")
    (evidence / "manifest.json").write_text(json.dumps({"count": len(items), "database": "existing Chinook",
        "dataset": output.relative_to(ROOT).as_posix(), "sha256": sha256(output.read_bytes()).hexdigest(),
        "holdout_prediction_count": 0, "human_review_status": "pending_human_review", "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
