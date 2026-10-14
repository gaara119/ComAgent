"""Read-only validation after Windows/Docker restart; never create or modify data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
import psycopg
from qa_agent.config import get_settings

settings = get_settings()
base = ROOT / "eval/artifacts/d4/sql-scale-data-001"
manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
record = {"at_utc": datetime.now(timezone.utc).isoformat(), "model_calls": 0,
          "data_mutations": 0, "new_schemas": 0, "holdout_predictions": 0,
          "connection": "existing Chinook qa_reader; transaction READ ONLY; 5000ms statement timeout",
          "queries": [], "scales": []}
fk_sql = """SELECT c.conname, c.convalidated, n2.nspname AS target_schema,
                   pg_get_constraintdef(c.oid) AS definition
            FROM pg_constraint c
            JOIN pg_class t ON t.oid=c.conrelid
            JOIN pg_namespace n ON n.oid=t.relnamespace
            JOIN pg_class t2 ON t2.oid=c.confrelid
            JOIN pg_namespace n2 ON n2.oid=t2.relnamespace
            WHERE n.nspname=%s AND c.contype='f'
            ORDER BY t.relname,c.conname"""
with psycopg.connect(settings.db_url, connect_timeout=5) as conn:
    conn.read_only = True
    with conn.transaction():
        conn.execute("SELECT set_config('statement_timeout',%s,true)", (str(settings.statement_timeout_ms),))
        record["current_user"] = conn.execute("SELECT current_user").fetchone()[0]
        record["transaction_read_only"] = conn.execute("SHOW transaction_read_only").fetchone()[0]
        record["actual_statement_timeout"] = conn.execute("SHOW statement_timeout").fetchone()[0]
        assert record["current_user"] == "qa_reader"
        assert record["transaction_read_only"] == "on"
        for source, name in [(base / "public-before.sql", "public_fingerprints")]:
            sql = source.read_text(encoding="utf-8")
            record[name] = conn.execute(sql).fetchone()[0]
            record["queries"].append({"sql_file": source.relative_to(ROOT).as_posix(),
                                      "sql_sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        record["original_public_unchanged"] = record["public_fingerprints"] == manifest["original_public_fingerprints"]
        assert record["original_public_unchanged"]
        for original in manifest["scales"]:
            schema, count = original["schema"], original["line_count"]
            source = base / f"verify-{count}.sql"
            row = conn.execute(source.read_text(encoding="utf-8")).fetchone()[0]
            constraints = conn.execute(fk_sql, (schema,)).fetchall()
            actual_fks = [{"name": value[0], "validated": value[1], "target_schema": value[2],
                           "definition": value[3]} for value in constraints]
            row["actual_foreign_keys"] = actual_fks
            row["actual_fk_count"] = len(actual_fks)
            row["all_fks_validated_and_in_same_copy"] = all(value["validated"] and value["target_schema"] == schema
                                                             for value in actual_fks)
            row["table_counts_match_manifest"] = row["table_counts"] == original["table_counts"]
            assert row["line_count"] == count and row["orphan_lines"] == 0
            assert row["invoice_total"] == row["line_total"]
            assert row["table_counts_match_manifest"]
            assert row["actual_fk_count"] == 11 and row["all_fks_validated_and_in_same_copy"]
            record["scales"].append(row)
            record["queries"].append({"sql_file": source.relative_to(ROOT).as_posix(),
                                      "sql_sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        record["fk_query"] = fk_sql
record["status"] = "ACTUALLY_READONLY_VERIFIED_AFTER_RESTART"
target = ROOT / "eval/artifacts/d4/a-readiness-001/restarted-scale-check.json"
target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({key: value for key, value in record.items() if key not in {"public_fingerprints", "queries", "fk_query", "scales"}},
                 ensure_ascii=False, indent=2))
print(json.dumps([{key: value for key, value in scale.items() if key in {"schema", "line_count", "invoice_count", "orphan_lines",
                  "actual_fk_count", "all_fks_validated_and_in_same_copy", "table_counts_match_manifest"}}
                 for scale in record["scales"]], ensure_ascii=False, indent=2))
