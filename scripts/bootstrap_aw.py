"""Install lorint's full OLTP in an isolated D3 service; never touch Chinook.

Run with .venv\\Scripts\\python.exe -B scripts/bootstrap_aw.py.  Downloads the
official Microsoft data and a pinned upstream converter/DDL; raw data and
credentials remain in ignored directories. Existing populated AW is verified,
not re-imported. No drop/down/reset operation is provided.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import quote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import requests
from dotenv import dotenv_values, set_key

RAW = ROOT / "data/raw/adventureworks"
ART = ROOT / "eval/artifacts/d3/a"
ENV = ROOT / ".runtime/aw.env"
COMPOSE = ["docker", "compose", "--env-file", str(ENV), "-f", "docker-compose.aw.yml"]
CONTAINER = "comagent-d3-aw-aw-pg-1"
SCHEMAS = ("humanresources", "person", "production", "purchasing", "sales")


def now():
    return datetime.now(timezone.utc).isoformat()


def run(command, *, input_text=None, name="command"):
    started = time.monotonic()
    process = subprocess.run(command, cwd=ROOT, input=input_text, text=True,
                             encoding="utf-8", errors="replace", capture_output=True)
    # Commands never contain passwords. Sensitive SQL stdin is deliberately excluded.
    text = process.stdout + process.stderr
    if ENV.is_file():
        private = dotenv_values(ENV)
        for key in ("AW_POSTGRES_PASSWORD", "AW_READER_PASSWORD"):
            if private.get(key):
                text = text.replace(str(private[key]), "[redacted]")
    path = ART / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    with (ART / "commands.jsonl").open("a", encoding="utf-8") as out:
        out.write(json.dumps({"time": now(), "argv": command,
                              "stdin": "private role SQL omitted" if input_text else None,
                              "exit_code": process.returncode,
                              "elapsed_seconds": round(time.monotonic()-started, 3),
                              "output": str(path.relative_to(ROOT))}, ensure_ascii=False)+"\n")
    if process.returncode:
        raise RuntimeError(f"{name} failed (see {path.relative_to(ROOT)}): {text[-1200:]}")
    return process.stdout


def download(url, target):
    if target.is_file() and target.stat().st_size:
        return
    with requests.get(url, stream=True, timeout=(30, 180)) as response:
        response.raise_for_status()
        tmp = target.with_suffix(target.suffix + ".partial")
        with tmp.open("wb") as out:
            for part in response.iter_content(1024*1024):
                out.write(part)
        tmp.replace(target)


def fetch_sources():
    manifest_path = ROOT / "data/db/aw_source_manifest.json"
    if manifest_path.is_file():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        revision = old["upstream_revision"]
    else:
        response = requests.get("https://api.github.com/repos/lorint/AdventureWorks-for-Postgres/commits/master", timeout=30)
        response.raise_for_status()
        revision = response.json()["sha"]
    sources = []
    for name in ("install.sql", "update_csvs.rb", "README.md", "LICENSE"):
        url = f"https://raw.githubusercontent.com/lorint/AdventureWorks-for-Postgres/{revision}/{name}"
        target = RAW / name
        download(url, target)
        sources.append({"name": name, "url": url, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    archive_url = "https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks-oltp-install-script.zip"
    archive = RAW / "adventure_works_2014_OLTP_script.zip"
    download(archive_url + "?d3=" + str(int(time.time())), archive)
    sources.append({"name": archive.name, "url": archive_url,
                    "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "size_bytes": archive.stat().st_size})
    if not (RAW / ".converted.json").exists():
        with zipfile.ZipFile(archive) as zipped:
            csvs = [entry for entry in zipped.infolist() if entry.filename.lower().endswith(".csv")]
            for entry in csvs:
                target = RAW / Path(entry.filename).name
                target.write_bytes(zipped.read(entry))
        if len(csvs) < 68:
            raise RuntimeError(f"Full OLTP archive has only {len(csvs)} CSV files")
        run(["docker", "run", "--rm", "-v", f"{RAW}:/awdata", "-w", "/awdata",
             "ruby:3.4-alpine", "ruby", "update_csvs.rb"], name="ruby-convert")
        converted = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in RAW.glob("*.csv")}
        (RAW / ".converted.json").write_text(json.dumps(converted, indent=2), encoding="utf-8")
    manifest = {"database": "AdventureWorks full OLTP", "fetched_at": now(),
                "upstream_repository": "https://github.com/lorint/AdventureWorks-for-Postgres",
                "upstream_revision": revision, "sources": sources,
                "converter": "upstream update_csvs.rb run by ruby:3.4-alpine",
                "expected_base_table_count": 68, "business_schemas": list(SCHEMAS)}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def psql(query, name):
    return run(["docker", "exec", CONTAINER, "psql", "-U", "postgres", "-d", "adventureworks", "-At", "-v", "ON_ERROR_STOP=1", "-c", query], name=name)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    ENV.parent.mkdir(parents=True, exist_ok=True)
    if not ENV.exists():
        ENV.write_text("AW_POSTGRES_PASSWORD="+secrets.token_urlsafe(30)+"\nAW_READER_PASSWORD="+secrets.token_urlsafe(30)+"\nAW_PORT=55433\n", encoding="utf-8")
    private = dotenv_values(ENV)
    manifest = fetch_sources()
    run(COMPOSE + ["up", "-d", "--wait", "aw-pg"], name="compose-up")
    count = int(psql("SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('humanresources','person','production','purchasing','sales') AND table_type='BASE TABLE'", "existing-table-count").strip())
    if count == 0:
        run(["docker", "exec", "-w", "/awdata", CONTAINER, "psql", "-U", "postgres", "-d", "adventureworks", "-v", "ON_ERROR_STOP=1", "-f", "/awdata/install.sql"], name="import-full-oltp")
        import_status = "imported_once"
    elif count == 68:
        import_status = "existing_full_database_verified_without_reimport"
    else:
        raise RuntimeError(f"AW has {count} base tables; refusing to overwrite a partial/existing database")
    password = private["AW_READER_PASSWORD"]
    schema_list = ",".join(SCHEMAS)
    role_sql = f"""DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='qa_reader') THEN CREATE ROLE qa_reader LOGIN; END IF; END $$;
ALTER ROLE qa_reader NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '{password}';
ALTER ROLE qa_reader SET default_transaction_read_only = on;
ALTER ROLE qa_reader SET statement_timeout = '5000ms';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE adventureworks TO qa_reader;
GRANT USAGE ON SCHEMA {schema_list} TO qa_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA {schema_list} TO qa_reader;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA {schema_list} FROM qa_reader;
"""
    run(["docker", "exec", "-i", CONTAINER, "psql", "-U", "postgres", "-d", "adventureworks", "-v", "ON_ERROR_STOP=1"], input_text=role_sql, name="readonly-role-setup")
    url = f"postgresql://qa_reader:{quote(password, safe='')}@127.0.0.1:{private['AW_PORT']}/adventureworks"
    set_key(str(ROOT / ".env"), "AW_DB_URL", url)
    result = {"time": now(), "import_status": import_status, "upstream_revision": manifest["upstream_revision"],
              "base_table_count": int(psql("SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('humanresources','person','production','purchasing','sales') AND table_type='BASE TABLE'", "base-table-count").strip()),
              "foreign_key_count": int(psql("SELECT count(*) FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace WHERE c.contype='f' AND n.nspname IN ('humanresources','person','production','purchasing','sales')", "foreign-key-count").strip()),
              "salesorderdetail_rows": int(psql("SELECT count(*) FROM sales.salesorderdetail", "salesorderdetail-count").strip()),
              "schema_counts": psql("SELECT table_schema,count(*) FROM information_schema.tables WHERE table_schema IN ('humanresources','person','production','purchasing','sales') AND table_type='BASE TABLE' GROUP BY table_schema ORDER BY table_schema", "schema-counts").strip().splitlines(),
              "reader": "qa_reader", "reader_default_read_only": True, "statement_timeout_ms": 5000,
              "old_chinook_service_touched": False}
    (ART / "bootstrap-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
