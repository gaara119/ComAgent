"""Create explicitly authorized recovery copies; never mutate old source/evidence.

This is not the old bootstrap: it cannot replace sources, download datasets,
write .env, drop databases, or address the old comagent-d1/d3 volume names.
Run only after authorization for the two independent D4 recovery volumes.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import dotenv_values
from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.catalog import load_catalog

PROJECT = "comagent-d4-recovery"
SCHEMAS = ["humanresources", "person", "production", "purchasing", "sales"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="eval/artifacts/d4/database-recovery-001")
    parser.add_argument("--allow-recovery", action="store_true")
    args = parser.parse_args()
    out = ROOT / args.output
    if out.exists():
        raise RuntimeError("Use a fresh evidence directory; existing evidence is preserved")
    settings = get_settings()
    original_manifest = json.loads((ROOT / "data/db/source_manifest.json").read_text("utf-8"))
    aw_manifest = json.loads((ROOT / "data/db/aw_source_manifest.json").read_text("utf-8"))
    protected = [ROOT / ".env", ROOT / ".runtime/aw.env", ROOT / "data/db/source_manifest.json",
                 ROOT / "data/db/aw_source_manifest.json", ROOT / "data/db/aw_live_data_manifest.json"]
    for item in (original_manifest["source"], original_manifest["import"]):
        path = ROOT / "data/db" / item["file"]
        if sha(path) != item["sha256"]:
            raise RuntimeError("Chinook source/import checksum mismatch")
        protected.append(path)
    for item in aw_manifest["sources"]:
        path = ROOT / "data/raw/adventureworks" / item["name"]
        if sha(path) != item["sha256"]:
            raise RuntimeError("AW immutable source checksum mismatch: " + item["name"])
        protected.append(path)
    converted = ROOT / "data/raw/adventureworks/.converted.json"
    for name, expected in json.loads(converted.read_text("utf-8")).items():
        path = converted.parent / name
        if sha(path) != expected:
            raise RuntimeError("Converted AW data checksum mismatch: " + name)
        protected.append(path)
    before = {str(p.relative_to(ROOT)): sha(p) for p in protected}
    out.mkdir(parents=True)
    private = {**dotenv_values(ROOT / ".env"), **dotenv_values(ROOT / ".runtime/aw.env")}

    def run(command, name, input_text=None):
        started = datetime.now(timezone.utc)
        result = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                                input=input_text, capture_output=True)
        output = sanitize_error(result.stdout + result.stderr, settings)
        for secret in private.values():
            if secret and len(str(secret)) >= 12:
                output = output.replace(str(secret), "[redacted]")
        (out / (name + ".txt")).write_text(output, "utf-8")
        with (out / "commands.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"at": started.isoformat(), "argv": command,
                "stdin": "private role SQL omitted" if input_text else None,
                "exit_code": result.returncode, "evidence": name + ".txt"}, ensure_ascii=False) + "\n")
        if result.returncode:
            raise RuntimeError(name + " failed; inspect the sanitized evidence")
        return result.stdout.strip()

    snapshot = {"source_verification": "passed", "protected_file_count": len(before),
                "copy_project": PROJECT, "purpose": "D4 recovery copies, not original volumes",
                "old_source_and_configuration_hashes": before}
    (out / "preparation.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), "utf-8")
    if not args.allow_recovery:
        print(json.dumps({"prepared": True, "executed": False, "verified_files": len(before)}))
        return
    existing = run(["docker", "ps", "-a", "--format", "{{.Names}}"], "containers-before").splitlines()
    for port, service in [(55432, "chinook-pg"), (55433, "aw-pg")]:
        connection = socket.socket()
        available = connection.connect_ex(("127.0.0.1", port)) != 0
        connection.close()
        if not available and f"{PROJECT}-{service}-1" not in existing:
            raise RuntimeError(f"Port {port} belongs to another service; refusing to replace it")
    run(["docker", "volume", "ls", "--format", "{{.Name}}"], "volumes-before")
    compose = ["docker", "compose", "--env-file", str(ROOT / ".env"), "--env-file",
               str(ROOT / ".runtime/aw.env"), "-f", "docker-compose.d4-recovery.yml"]
    run(compose + ["up", "-d", "--wait"], "recovery-compose-up")

    def psql(service, database, query, name, private_stdin=False):
        command = ["docker", "exec", "-i", f"{PROJECT}-{service}-1", "psql", "-U", "postgres", "-d", database,
                   "-At", "-v", "ON_ERROR_STOP=1"]
        return run(command if private_stdin else command + ["-c", query], name,
                   input_text=query if private_stdin else None)

    count_sql = "SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('humanresources','person','production','purchasing','sales') AND table_type='BASE TABLE'"
    count = int(psql("aw-pg", "adventureworks", count_sql, "aw-before-table-count"))
    if count == 0:
        run(["docker", "exec", "-w", "/awdata", f"{PROJECT}-aw-pg-1", "psql", "-U", "postgres", "-d",
             "adventureworks", "-v", "ON_ERROR_STOP=1", "-f", "/awdata/install.sql"], "aw-recovery-import")
    elif count != 68:
        raise RuntimeError("Existing D4 recovery database is partial; refusing to replace it")
    details = {}
    for service, database, url, catalog_path, schemas in [
        ("chinook-pg", "chinook", settings.db_url, settings.catalog_path, ["public"]),
        ("aw-pg", "adventureworks", settings.aw_db_url, settings.aw_catalog_path, SCHEMAS)]:
        parsed = urlsplit(url)
        if parsed.hostname != "127.0.0.1" or unquote(parsed.username or "") != "qa_reader":
            raise RuntimeError("Existing reader URL differs from the expected local read-only service")
        password = unquote(parsed.password or "").replace("'", "''")
        schema_list = ",".join(schemas)
        role_sql = f"""DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='qa_reader') THEN CREATE ROLE qa_reader LOGIN; END IF; END $$;
ALTER ROLE qa_reader NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD '{password}';
ALTER ROLE qa_reader SET default_transaction_read_only = on;
ALTER ROLE qa_reader SET statement_timeout = '5000ms';
ALTER ROLE qa_reader SET lock_timeout = '2000ms';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE {database} TO qa_reader;
GRANT USAGE ON SCHEMA {schema_list} TO qa_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA {schema_list} TO qa_reader;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA {schema_list} FROM qa_reader;
"""
        psql(service, database, role_sql, database + "-readonly-role", private_stdin=True)
        import psycopg
        with psycopg.connect(url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                counts = {}
                for table in load_catalog(catalog_path).tables:
                    cur.execute(f'SELECT COUNT(*) FROM "{table.schema}"."{table.name}"')
                    rows = cur.fetchone()[0]
                    if table.row_count is not None and rows != table.row_count:
                        raise RuntimeError(f"Recovered {table.schema}.{table.name} differs from existing catalog row count")
                    counts[table.schema + "." + table.name] = rows
                cur.execute("SHOW default_transaction_read_only")
                readonly = cur.fetchone()[0]
                cur.execute("SHOW statement_timeout")
                timeout = cur.fetchone()[0]
                details[database] = {"table_count": len(counts), "row_counts": counts,
                    "reader": "qa_reader", "default_transaction_read_only": readonly, "statement_timeout": timeout}
    after = {str(p.relative_to(ROOT)): sha(p) for p in protected}
    if before != after:
        raise RuntimeError("A protected original file changed during recovery")
    snapshot.update(executed=True, databases=details, old_sources_and_configuration_unchanged=True)
    (out / "recovery-result.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps({"ready": True, "databases": details, "original_files_unchanged": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
