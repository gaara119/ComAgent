"""Re-execute existing DEV-only SQL for audit evidence, never produce predictions.

Only this new audit directory is written. Database work is SELECT-only under
the already-configured qa_reader role, read-only transactions and a 5s timeout.
No question answering API, LLM, gold mutation, or holdout-content audit occurs.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import psycopg
import sqlglot
from sqlglot import exp
from qa_agent.config import get_settings, sanitize_error


def clean(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    return value


def normalized(value):
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value)).normalize().to_eng_string()
    if isinstance(value, str):
        try:
            return Decimal(value).normalize().to_eng_string()
        except Exception:
            return value
    return str(value)


def same_values(rows, original, ordered):
    a = [tuple(normalized(v) for v in row) for row in rows]
    b = [tuple(normalized(v) for v in row.values()) for row in original]
    return a == b if ordered else Counter(a) == Counter(b)


def read_only(statement):
    nodes = sqlglot.parse(statement, read="postgres")
    if len(nodes) != 1 or not isinstance(nodes[0], exp.Select):
        raise ValueError("Audit only accepts one SELECT")
    bad = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Alter, exp.Into)
    if any(isinstance(node, bad) for node in nodes[0].walk()):
        raise ValueError("Mutating SQL is prohibited")
    for node in nodes[0].find_all(exp.Anonymous):
        if node.name.lower() not in {"has_table_privilege"}:
            raise ValueError("Unexpected custom function")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = datetime.now(timezone.utc).isoformat()
    table_path = ROOT / "eval/reports/d2-acceptance/unified-review.json"
    data = json.loads(table_path.read_text(encoding="utf-8"))
    rows = [row for row in data["rows"]
            if row.get("group") in {"nl2sql", "robust"} and row.get("split") == "dev"]
    assert Counter(row["group"] for row in rows) == {"nl2sql": 35, "robust": 21}
    # Do not project, display, or query any holdout question, SQL, or answer.
    skipped = {group: sum(row.get("group") == group and row.get("split") == "holdout"
                         for row in data["rows"]) for group in ("nl2sql", "robust")}
    sources = {}
    for group in ("nl2sql", "robust"):
        path = ROOT / f"eval/artifacts/d2/{group}/final/responses.jsonl"
        entries = {}
        for line, value in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            item = json.loads(value)
            if item.get("split") == "dev":
                entries[item["id"]] = {"line": line, "row": item}
        sources[group] = {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(path), "entries": entries}
    tasks = []
    comparisons = []
    for row in rows:
        original = sources[row["group"]]["entries"][row["id"]]
        response = original["row"]["response"]
        matches = {key: response.get(key) == row["actual"].get(key)
                   for key in ("status", "sql", "table", "answer", "rewritten_question", "error")}
        comparisons.append({"review_id": row["review_id"], "source": sources[row["group"]]["path"],
                            "source_line": original["line"], "embedded_matches_original": matches,
                            "http_status": original["row"].get("http_status"),
                            "original_step_statuses": [{"name": step["name"], "status": step["status"]}
                                                       for step in response.get("steps", [])],
                            "truncated": response.get("metadata", {}).get("truncated"),
                            "intent": response.get("intent"), "clarification": response.get("clarification")})
        assert all(matches.values()), row["review_id"]
        assert original["row"]["request"]["message"] == row["title"], row["review_id"]
        ref = row["expected"]
        tasks.append({"review_id": row["review_id"], "object": "reference", "group": row["group"], "split": "dev",
                      "source_path": "eval/reports/d2-acceptance/unified-review.json", "section": row["review_id"] + ".expected",
                      "sql": ref["gold_sql"], "params": None, "stored_rows": ref["gold_result"],
                      "ordered": ref["ordered"]})
        tasks.append({"review_id": row["review_id"], "object": "actual", "group": row["group"], "split": "dev",
                      "source_path": sources[row["group"]]["path"], "source_line": original["line"],
                      "sql": response["sql"], "params": None, "stored_rows": response["table"],
                      "ordered": ref["ordered"]})
    metrics = json.loads((ROOT / "data/rules/metric_definitions.json").read_text(encoding="utf-8"))
    for name, statement in metrics["sql_examples"].items():
        tasks.append({"review_id": "metric-example:" + name, "object": "metric_sql_example", "sql": statement,
                      "params": None, "source_path": "data/rules/metric_definitions.json", "section": "sql_examples." + name})
    supplemental = {
        "postgres-desc-null-order": "SELECT v FROM (VALUES (1), (NULL::integer)) AS t(v) ORDER BY v DESC;",
        "nullable-columns": "SELECT COUNT(*) FILTER (WHERE bytes IS NULL) AS bytes_nulls, COUNT(*) FILTER (WHERE genre_id IS NULL) AS genre_id_nulls, COUNT(*) FILTER (WHERE album_id IS NULL) AS album_id_nulls, COUNT(*) FILTER (WHERE composer IS NULL) AS composer_nulls FROM public.track;",
        "customer-null-values": "SELECT COUNT(*) FILTER (WHERE country IS NULL) AS country_nulls, COUNT(*) FILTER (WHERE city IS NULL) AS city_nulls, COUNT(*) FILTER (WHERE state IS NULL) AS state_nulls, COUNT(*) FILTER (WHERE company IS NULL) AS company_nulls, COUNT(*) FILTER (WHERE company = '') AS company_empty_strings FROM public.customer;",
        "invoice-null-regions": "SELECT COUNT(*) FILTER (WHERE billing_country IS NULL) AS country_nulls, COUNT(*) FILTER (WHERE billing_city IS NULL) AS city_nulls FROM public.invoice;",
        "region-semantics": "SELECT COUNT(*) AS mismatching_region_invoices FROM public.invoice i JOIN public.customer c ON c.customer_id = i.customer_id WHERE i.billing_country IS DISTINCT FROM c.country;",
        "empty-amount-semantics": "SELECT SUM(total) AS revenue, AVG(total) AS average, COUNT(*) AS invoice_count FROM public.invoice WHERE invoice_date >= DATE '2099-01-01' AND invoice_date < DATE '2100-01-01';",
        "invoice-years": "SELECT EXTRACT(YEAR FROM invoice_date)::integer AS year, COUNT(*) AS invoice_count, SUM(total) AS amount FROM public.invoice GROUP BY year ORDER BY year;",
        "repeat-customer-check": "SELECT customer_id, COUNT(*) AS invoice_count FROM public.invoice WHERE invoice_date >= DATE '2024-01-01' AND invoice_date < DATE '2025-01-01' GROUP BY customer_id HAVING COUNT(*) >= 2 ORDER BY customer_id;",
        "popular-quantity-ties": "SELECT il.track_id, t.name, SUM(il.quantity) AS purchased_quantity FROM public.invoice_line il JOIN public.invoice i ON i.invoice_id = il.invoice_id JOIN public.track t ON t.track_id = il.track_id WHERE i.invoice_date >= DATE '2024-01-01' AND i.invoice_date < DATE '2025-01-01' GROUP BY il.track_id, t.name ORDER BY purchased_quantity DESC, il.track_id ASC LIMIT 10;",
        "employee-hire-nulls": "SELECT COUNT(*) FILTER (WHERE hire_date IS NULL) AS hire_date_nulls FROM public.employee;",
        "artist-name-nulls": "SELECT COUNT(*) FILTER (WHERE name IS NULL) AS name_nulls FROM public.artist;"
    }
    for name, statement in supplemental.items():
        tasks.append({"review_id": "supplemental:" + name, "object": "audit_select", "sql": statement, "params": None,
                      "source_path": "eval/artifacts/d2-ai-preaudit/verify_sql.py", "section": "supplemental." + name})
    for task in tasks:
        read_only(task["sql"])
    settings = get_settings()
    records = []
    errors = []
    try:
        with psycopg.connect(settings.db_url, connect_timeout=8) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '5000ms'")
            begin = time.perf_counter()
            identity_sql = "SELECT current_database(), current_user, current_setting('transaction_read_only'), current_setting('statement_timeout');"
            cursor = conn.execute(identity_sql)
            identity = cursor.fetchone()
            records.append({"review_id": "audit:identity", "object": "audit_select", "sql": identity_sql,
                            "params": None, "columns": [column.name for column in cursor.description], "rows": [list(identity)],
                            "elapsed_ms": round((time.perf_counter() - begin) * 1000, 3), "status": "executed"})
            if identity[1] != "qa_reader" or identity[2:] != ("on", "5s"):
                raise ValueError("qa_reader, read-only transaction and 5s timeout must all be verified")
            for task in tasks:
                begin = time.perf_counter()
                record = {key: value for key, value in task.items() if key != "stored_rows"}
                cursor = conn.execute(task["sql"], task["params"])
                values = cursor.fetchall()
                record.update({"columns": [column.name for column in cursor.description], "rows": clean(values),
                               "row_count": len(values), "elapsed_ms": round((time.perf_counter() - begin) * 1000, 3),
                               "status": "executed", "truncated": False})
                if "stored_rows" in task:
                    record["matches_stored_values"] = same_values(clean(values), task["stored_rows"], task["ordered"])
                    record["column_names_match_stored"] = (not task["stored_rows"] or record["columns"] == list(task["stored_rows"][0]))
                records.append(record)
            conn.rollback()
    except Exception as exc:
        errors.append(sanitize_error(exc, settings))
    (OUT / "sql-verification.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records) + "\n", encoding="utf-8")
    summary = {"started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
               "operation": "Existing DEV gold and original predictions re-executed as SELECT only; no new system predictions or models",
               "identity": {"role": records[0]["rows"][0][1], "transaction_read_only": records[0]["rows"][0][2], "statement_timeout": records[0]["rows"][0][3]} if records else None,
               "dev_rows": dict(Counter(row["group"] for row in rows)), "skipped_holdout_counts": skipped,
               "source_response_rechecks": comparisons,
               "query_count": len(records), "expected_query_count": len(tasks) + 1,
               "failed_value_comparisons": [item["review_id"] + ":" + item["object"] for item in records if item.get("matches_stored_values") is False],
               "errors": errors,
               "script_sha256": digest(Path(__file__)),
               "source_hashes": {"unified-review": digest(table_path), **{group: item["sha256"] for group, item in sources.items()}}}
    (OUT / "sql-verification-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("query_count", "expected_query_count", "dev_rows", "skipped_holdout_counts", "failed_value_comparisons", "errors")}, ensure_ascii=False))
    return 1 if errors or summary["failed_value_comparisons"] else 0


if __name__ == "__main__":
    sys.exit(main())
