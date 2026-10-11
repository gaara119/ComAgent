"""Read-only D2 preflight; snapshot D1 evidence without rerunning D1 writers."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
import psycopg
from psycopg import sql
from qa_agent.config import get_settings, sanitize_error


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def check_database() -> dict:
    settings = get_settings()
    with psycopg.connect(settings.db_url, connect_timeout=8) as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        identity = conn.execute("SELECT current_database(), current_user").fetchone()
        tables = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
        counts = {}
        fingerprints = {}
        for (table,) in tables:
            rows = conn.execute(sql.SQL("SELECT * FROM public.{} ORDER BY 1").format(sql.Identifier(table))).fetchall()
            counts[table] = len(rows)
            fingerprints[table] = hashlib.sha256(json.dumps(rows, default=str, ensure_ascii=False,
                                                             separators=(",", ":")).encode()).hexdigest()
        defaults = {name: conn.execute(sql.SQL("SHOW {}").format(sql.Identifier(name))).fetchone()[0]
                    for name in ("default_transaction_read_only", "statement_timeout")}
        privileges = conn.execute("SELECT table_name, has_table_privilege(current_user, "
                                  "quote_ident(table_schema)||'.'||quote_ident(table_name), 'SELECT'), "
                                  "has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), "
                                  "'INSERT,UPDATE,DELETE,TRUNCATE') FROM information_schema.tables "
                                  "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name").fetchall()
        dates = conn.execute("SELECT MIN(invoice_date), MAX(invoice_date), COUNT(*) FROM invoice").fetchone()
        if identity[1] != "qa_reader" or defaults["default_transaction_read_only"] != "on":
            raise ValueError("Expected qa_reader with read-only default")
        if not all(select and not write for _, select, write in privileges):
            raise ValueError("Reader privileges differ from SELECT-only")
        return {"database": identity[0], "reader": identity[1], "defaults": defaults,
                "table_row_counts": counts, "table_content_sha256": fingerprints,
                "invoice_date_range": [str(v) for v in dates[:2]],
                "privileges": [{"table": t, "select": r, "write": w} for t, r, w in privileges],
                "operation": "SELECT only; no bootstrap/import/recreate"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "eval/artifacts/d2/preflight.json")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--verify-d1", type=Path)
    args = parser.parse_args()
    settings = get_settings()
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version.split()[0],
              "executable": str(Path(sys.executable).relative_to(ROOT)), "configuration": settings.public(),
              "checks": {}, "errors": [], "d1_evidence_hashes": {}}
    try:
        report["database"] = check_database()
        report["checks"]["database_read_only"] = True
    except Exception as exc:
        report["errors"].append(sanitize_error(exc, settings))
        report["checks"]["database_read_only"] = False
    try:
        report["api_health"] = httpx.get(args.api_base_url + "/health", timeout=8, trust_env=False).json()
        report["checks"]["api_available"] = report["api_health"].get("status") == "ok"
    except Exception as exc:
        report["errors"].append(sanitize_error(exc, settings))
        report["checks"]["api_available"] = False
    tracked = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, encoding="utf8", check=True).stdout.splitlines()
    # Git -c core.quotepath=false returns readable paths for filenames in Chinese.
    tracked = subprocess.run(["git", "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", "HEAD"],
                              cwd=ROOT, capture_output=True, text=True, encoding="utf8", check=True).stdout.splitlines()
    for name in tracked:
        if (name.startswith("eval/reports/d1") or name.startswith("eval/reports/rag-d1")
            or name.startswith("notes/screenshots/D1") or name.startswith("eval/datasets/")
            or name == "qa_agent/schemas.py"):
            path = ROOT / name
            if path.exists():
                report["d1_evidence_hashes"][name] = digest(path)
    if args.verify_d1:
        baseline = json.loads(args.verify_d1.read_text(encoding="utf8"))
        changed = [name for name, sha in baseline["d1_evidence_hashes"].items()
                   if not (ROOT / name).exists() or digest(ROOT / name) != sha]
        report["d1_changed_paths"] = changed
        report["checks"]["d1_evidence_unchanged"] = not changed
        report["checks"]["database_snapshot_unchanged"] = (
            baseline.get("database", {}).get("table_content_sha256") ==
            report.get("database", {}).get("table_content_sha256"))
    report["status"] = "PASS" if all(report["checks"].values()) else "PARTIAL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps({"status": report["status"], "checks": report["checks"], "errors": report["errors"],
                      "d1_evidence_file_count": len(report["d1_evidence_hashes"])}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
