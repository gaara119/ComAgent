"""Collect read-only D2 pre-audit inputs; never call the evaluated QA system."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            result.update(part)
    return result.hexdigest()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def snapshot():
    files = {}
    for parent, dirs, names in os.walk(ROOT):
        base = Path(parent)
        dirs[:] = [name for name in dirs if name not in {".git", ".venv", ".runtime", "__pycache__"}
                   and (base / name).relative_to(ROOT).as_posix() not in {
                       "data/models", "eval/artifacts/d2-ai-preaudit", "eval/reports/d2-ai-preaudit"}]
        for name in names:
            path = base / name
            if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
                files[path.relative_to(ROOT).as_posix()] = digest(path)
    write("protected-inputs-before.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(),
          "scope": "Existing project files except runtime, virtual environment, model weights, Git metadata, Python caches and new AI audit directories",
          "file_sha256": files})
    print(json.dumps({"protected_files": len(files)}, ensure_ascii=False))


def materials():
    raw_path = ROOT / "eval/reports/d2-acceptance/unified-review.json"
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    accessed = {}
    paths = set()
    for row in data["rows"]:
        if row["split"] == "holdout":
            continue
        for entry in row["evidence_files"]:
            paths.add(entry["path"])
    paths.update({"data/catalog/chinook.yaml", "data/docs/manifest.csv", "data/aliases/aliases.csv",
                  "data/rules/metric_definitions.json", "eval/artifacts/d2/source/metric-human-review.json",
                  "data/indexes/docs-final/chunks.jsonl", "data/indexes/values/values.jsonl",
                  "data/indexes/values/records.jsonl", "data/indexes/values/index_meta.json",
                  "data/raw/ohr/qas_v2.json"})
    with (ROOT / "data/docs/manifest.csv").open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            paths.add(row["path"])
    for name in sorted(paths):
        path = ROOT / name
        entry = {"path": name, "readable": path.is_file()}
        if entry["readable"]:
            entry.update({"bytes": path.stat().st_size, "sha256": digest(path),
                          "access_level": "bytes read; semantic content review recorded separately"})
        accessed[name] = entry
    write("material-access.json", {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "actual_row_counts": {group: sum(row["group"] == group for row in data["rows"])
                              for group in ["alias", "nl2sql", "robust", "rag", "metric"]},
        "actual_dev_rows_with_output": sum(row["split"] == "dev" and row["actual"] is not None for row in data["rows"]),
        "holdout_rows": sum(row["split"] == "holdout" for row in data["rows"]),
        "holdout_policy": "Content audit skipped: current conversation is a development environment without independent holdout isolation",
        "files": list(accessed.values())})
    print(json.dumps({"accessible_files": sum(item["readable"] for item in accessed.values()),
                      "missing": [name for name, entry in accessed.items() if not entry["readable"]]}, ensure_ascii=False))


def database():
    import psycopg
    from psycopg import sql
    from qa_agent.config import get_settings, sanitize_error

    settings = get_settings()
    report = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "status": "EVIDENCE_INSUFFICIENT",
              "operation": "Existing qa_reader; SELECT only; no model calls, system predictions or holdout label queries",
              "queries": [], "schema": [], "text_values": {}, "errors": []}
    try:
        with psycopg.connect(settings.db_url, connect_timeout=8) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '5000ms'")

            def query(statement, params=None):
                start = time.perf_counter()
                cursor = conn.execute(statement, params)
                result = cursor.fetchall()
                report["queries"].append({"sql": statement.as_string(conn) if hasattr(statement, "as_string") else statement,
                    "params": params, "columns": [column.name for column in cursor.description],
                    "rows": result, "elapsed_ms": round((time.perf_counter() - start) * 1000, 3)})
                return result

            identity = query("SELECT current_database(), current_user, current_setting('transaction_read_only'), current_setting('statement_timeout');")[0]
            report["identity"] = {"database": identity[0], "role": identity[1], "transaction_read_only": identity[2], "statement_timeout": identity[3]}
            if identity[1] != "qa_reader" or identity[2] != "on":
                raise ValueError("Read-only qa_reader identity not verified")
            columns = query("SELECT table_schema, table_name, column_name, data_type, is_nullable, ordinal_position FROM information_schema.columns WHERE table_schema = 'public' ORDER BY table_name, ordinal_position;")
            report["schema"] = [{"schema": row[0], "table": row[1], "column": row[2], "type": row[3],
                                  "nullable": row[4] == "YES", "ordinal": row[5]} for row in columns]
            tables = sorted({row[1] for row in columns})
            report["row_counts"] = {}
            for table in tables:
                statement = sql.SQL("SELECT COUNT(*) FROM public.{}").format(sql.Identifier(table))
                report["row_counts"][table] = query(statement)[0][0]
            for schema, table, column, kind, nullable, ordinal in columns:
                if kind not in {"text", "character varying", "character"}:
                    continue
                statement = sql.SQL("SELECT DISTINCT {column} FROM {schema}.{table} WHERE {column} IS NOT NULL ORDER BY {column} LIMIT 5001").format(
                    column=sql.Identifier(column), schema=sql.Identifier(schema), table=sql.Identifier(table))
                values = [row[0] for row in query(statement)]
                report["text_values"][f"{table}.{column}"] = {"values": values, "truncated": len(values) > 5000}
            report["invoice_dates"] = query("SELECT MIN(invoice_date), MAX(invoice_date) FROM public.invoice;")[0]
            report["privileges"] = query("SELECT table_name, has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'SELECT'), has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'INSERT,UPDATE,DELETE,TRUNCATE') FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;")
            report["status"] = "READ_ONLY_MATERIALS_VERIFIED"
    except Exception as exc:
        report["errors"].append(sanitize_error(exc, settings))
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    write("database-materials.json", report)
    print(json.dumps({"status": report["status"], "identity": report.get("identity"),
                      "schema_columns": len(report["schema"]), "text_fields": len(report["text_values"]),
                      "query_count": len(report["queries"]), "errors": report["errors"]}, ensure_ascii=False))
    return 0 if report["status"] == "READ_ONLY_MATERIALS_VERIFIED" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["snapshot", "materials", "database"])
    mode = parser.parse_args().mode
    if mode == "snapshot":
        snapshot()
    elif mode == "materials":
        materials()
    else:
        sys.exit(database())
