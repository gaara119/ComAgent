"""Download the pinned source and initialize only this project's PostgreSQL service.

Re-running preserves the named volume and existing business data. Credentials are
read from the local .env and never appear in command arguments or public reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg
from psycopg import sql

from qa_agent.config import get_settings, sanitize_error

PROJECT = "comagent-d1"
SERVICE = "chinook-pg"
IMAGE = "postgres:16.15-alpine3.23"
IMAGE_REF = IMAGE + "@sha256:621a761097839bdb50207afd6b87a72f38e2d718dd46c3d744828d8917c4f1e0"
SOURCE_URL = "https://github.com/lerocha/chinook-database/releases/download/v1.4.5/Chinook_PostgreSql.sql"
LICENSE_URL = "https://raw.githubusercontent.com/lerocha/chinook-database/v1.4.5/LICENSE.md"
SOURCE_SHA256 = "e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e"
LICENSE_SHA256 = "5064d720db431474b0a0b0cef9d2b5e362b6c6f80602b35c6443b07cbc979f77"


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def docker(*args: str, timeout: int = 180) -> str:
    completed = subprocess.run(["docker", *args], cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if completed.returncode:
        raise RuntimeError(sanitize_error(completed.stderr or completed.stdout, get_settings()))
    return completed.stdout.strip()


def compose(*args: str, timeout: int = 180) -> str:
    return docker("compose", "--project-name", PROJECT, "--env-file", str(ROOT / ".env"),
                  "--file", str(ROOT / "docker-compose.yml"), *args, timeout=timeout)


def admin_connection(**kwargs):
    get_settings()  # Load the same local .env as the application.
    return psycopg.connect(host="127.0.0.1", port=int(os.getenv("CHINOOK_PORT", "55432")),
                           dbname=os.getenv("DB_NAME", "chinook"),
                           user=os.getenv("POSTGRES_USER", "postgres"),
                           password=os.environ["POSTGRES_PASSWORD"], connect_timeout=5, **kwargs)


def prepare_source() -> dict:
    target = ROOT / "data/db"
    target.mkdir(parents=True, exist_ok=True)
    for filename, url, expected in [("Chinook_PostgreSql.sql", SOURCE_URL, SOURCE_SHA256),
                                     ("LICENSE.md", LICENSE_URL, LICENSE_SHA256)]:
        path = target / filename
        if not path.is_file():
            with urlopen(url, timeout=60) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != expected:
                raise RuntimeError(f"Source hash mismatch for {filename}; refusing to initialize")
            path.write_bytes(content)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Local source hash mismatch for {filename}; keep original release bytes")
    original = (target / "Chinook_PostgreSql.sql").read_text(encoding="utf-8-sig")
    marker = "CREATE TABLE album"
    if marker not in original:
        raise RuntimeError("Pinned source lacks expected first table; refusing to transform")
    safe_source = original[original.index(marker):]
    if "DROP DATABASE" in safe_source.upper() or "\\c " in safe_source:
        raise RuntimeError("Database management command remains in prepared import")
    header = "-- Derived from official Chinook v1.4.5; database DROP/CREATE/\\c preamble removed.\n"
    transformed = (header + safe_source).encode("utf-8")
    (target / "Chinook_PostgreSql.import.sql").write_bytes(transformed)
    manifest = {
        "dataset": "Chinook", "version": "1.4.5", "prepared_at": timestamp(),
        "upstream_repository": "https://github.com/lerocha/chinook-database",
        "source": {"file": "Chinook_PostgreSql.sql", "url": SOURCE_URL,
                   "sha256": SOURCE_SHA256, "size_bytes": (target / "Chinook_PostgreSql.sql").stat().st_size},
        "license": {"file": "LICENSE.md", "url": LICENSE_URL, "sha256": LICENSE_SHA256,
                    "name": "MIT", "copyright": "2008-2024 Luis Rocha"},
        "import": {"file": "Chinook_PostgreSql.import.sql",
                   "sha256": hashlib.sha256(transformed).hexdigest(),
                   "transformation": "Remove DROP DATABASE, CREATE DATABASE and psql \\c preamble; retain all table/data statements"},
        "docker": {"project": PROJECT, "service": SERVICE, "image_tag": IMAGE, "pinned_image": IMAGE_REF,
                   "volume": f"{PROJECT}_chinook-data"},
        "primary_references": [SOURCE_URL, "https://hub.docker.com/_/postgres",
                               "https://www.postgresql.org/docs/16/sql-grant.html",
                               "https://www.postgresql.org/docs/16/runtime-config-client.html"],
    }
    write_json(target / "source_manifest.json", manifest)
    return manifest


def check_scope() -> None:
    docker("info", "--format", "{{.ServerVersion}}", timeout=20)
    volume_name = f"{PROJECT}_chinook-data"
    existing = docker("volume", "ls", "--filter", f"name=^{volume_name}$", "--format", "{{.Name}}")
    if existing:
        labels = json.loads(docker("volume", "inspect", volume_name, "--format", "{{json .Labels}}"))
        if (labels or {}).get("com.docker.compose.project") != PROJECT:
            raise RuntimeError("Named volume exists outside this Compose project; refusing to attach it")
    container = compose("ps", "--all", "--quiet", SERVICE)
    if not container:
        with socket.socket() as probe:
            if probe.connect_ex(("127.0.0.1", int(os.getenv("CHINOOK_PORT", "55432")))) == 0:
                raise RuntimeError("Configured Chinook port is occupied by another service")


def configure_reader() -> None:
    reader = os.getenv("DB_READER_USER", "qa_reader")
    owner = os.getenv("POSTGRES_USER", "postgres")
    db_name = os.getenv("DB_NAME", "chinook")
    if not os.getenv("DB_READER_PASSWORD") or reader == owner:
        raise RuntimeError("Provide a distinct reader login and DB_READER_PASSWORD in .env")
    with admin_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
            expected = {"album", "artist", "customer", "employee", "genre", "invoice",
                        "invoice_line", "media_type", "playlist", "playlist_track", "track"}
            existing = {row[0] for row in cur.fetchall()}
            if existing != expected:
                raise RuntimeError("Business tables differ from the pinned Chinook source; no re-import or deletion performed")
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (reader,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("ALTER ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD {}")
                        .format(sql.Identifier(reader), sql.Literal(os.environ["DB_READER_PASSWORD"])))
            cur.execute("SELECT parent.rolname FROM pg_auth_members m JOIN pg_roles child ON child.oid=m.member "
                        "JOIN pg_roles parent ON parent.oid=m.roleid WHERE child.rolname=%s", (reader,))
            for (parent,) in cur.fetchall():
                cur.execute(sql.SQL("REVOKE {} FROM {}").format(sql.Identifier(parent), sql.Identifier(reader)))
            cur.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(db_name)))
            cur.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM {}").format(sql.Identifier(db_name), sql.Identifier(reader)))
            cur.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(db_name), sql.Identifier(reader)))
            cur.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
            cur.execute(sql.SQL("REVOKE ALL ON SCHEMA public FROM {}").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {}").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {}").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public GRANT SELECT ON TABLES TO {}")
                        .format(sql.Identifier(owner), sql.Identifier(reader)))
            cur.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("ALTER ROLE {} SET statement_timeout = {}")
                        .format(sql.Identifier(reader), sql.Literal(f"{get_settings().statement_timeout_ms}ms")))
            cur.execute(sql.SQL("ALTER ROLE {} SET lock_timeout = '2s'").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("ALTER ROLE {} SET idle_in_transaction_session_timeout = '10s'").format(sql.Identifier(reader)))
            cur.execute(sql.SQL("ALTER ROLE {} SET search_path = public").format(sql.Identifier(reader)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true", help="Download/verify source without starting Docker")
    args = parser.parse_args()
    settings = get_settings()
    manifest = prepare_source()
    if args.prepare_only:
        print("Pinned source verified; safe import SQL and source manifest prepared.")
        return
    check_scope()
    print(f"Starting {PROJECT}/{SERVICE}; existing volume and business data are preserved.", flush=True)
    compose("up", "--detach", "--wait", "--wait-timeout", "120", SERVICE, timeout=180)
    deadline = time.monotonic() + 60
    while True:
        try:
            with admin_connection() as conn:
                conn.execute("SELECT 1")
            break
        except psycopg.OperationalError:
            if time.monotonic() >= deadline:
                raise RuntimeError("PostgreSQL did not become reachable; inspect this project's container logs")
            time.sleep(1)
    configure_reader()
    container = compose("ps", "--quiet", SERVICE)
    dump = docker("exec", container, "pg_dump", "--schema-only", "--no-owner", "--no-privileges",
                  "--username", os.getenv("POSTGRES_USER", "postgres"), "--dbname", os.getenv("DB_NAME", "chinook"))
    (ROOT / "data/db/chinook_schema.sql").write_text(dump + "\n", encoding="utf-8")
    manifest["docker"]["resolved_digest"] = json.loads(docker("image", "inspect", IMAGE_REF, "--format", "{{json .RepoDigests}}"))[0]
    manifest["initialized_at"] = timestamp()
    write_json(ROOT / "data/db/source_manifest.json", manifest)
    print("PostgreSQL is healthy. Reader permissions configured; schema and source manifest exported.")
    print("Next: python scripts/check_db.py and python scripts/build_catalog.py")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Database bootstrap failed: {sanitize_error(exc, get_settings())}", file=sys.stderr)
        sys.exit(1)
