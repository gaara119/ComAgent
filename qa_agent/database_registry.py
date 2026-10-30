"""Local PostgreSQL registrations and bounded, read-only schema discovery.

Only connection settings are encrypted; public summaries never contain a DSN,
password, local path, or example business rows. Windows DPAPI binds credentials
to the current Windows account. Other platforms must supply a secure codec;
there is deliberately no plaintext fallback.
"""
from __future__ import annotations

import base64
import ctypes
import ipaddress
import json
import os
import re
import threading
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Literal, Protocol
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
import yaml

from qa_agent.config import PROJECT_ROOT, Settings, get_settings
from qa_agent.sql.catalog import load_catalog

MAX_TABLES = 500
MAX_COLUMNS = 10000
MAX_DATE_RANGES = 16
_ID_RE = re.compile(r"pg-[0-9a-f]{32}\Z")
_VERSION_RE = re.compile(r"[0-9a-f]{32}\Z")
_LOCK = threading.RLock()


class DatabaseRegistryError(RuntimeError):
    """A deliberately safe error: never constructed from driver exception text."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def is_registered_database_id(db_id: object) -> bool:
    return isinstance(db_id, str) and _ID_RE.fullmatch(db_id) is not None


def _check_id(db_id: str) -> None:
    if not is_registered_database_id(db_id):
        raise DatabaseRegistryError("DATABASE_NOT_FOUND", "未找到此本地数据库连接。", 404)


class RegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    name: str = Field(min_length=1, max_length=80)
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(default=5432, ge=1, le=65535, strict=True)
    database: str = Field(min_length=1, max_length=63)
    user: str = Field(min_length=1, max_length=63)
    password: SecretStr = Field(default_factory=lambda: SecretStr(""), max_length=4096)
    sslmode: Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] = "prefer"
    schemas: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("name", "database", "user")
    @classmethod
    def valid_text(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("名称不能为空且不得包含控制字符")
        return value

    @field_validator("host")
    @classmethod
    def valid_host(cls, value: str) -> str:
        value = value.strip()
        # A single TCP host only: no DSN, URL, Unix socket, multi-host list, or
        # libpq option injection. make_conninfo still quotes every parameter.
        try:
            ipaddress.ip_address(value)
            return value
        except ValueError:
            if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", value):
                raise ValueError("主机必须是单个 IP 地址或主机名") from None
            if any(not part or len(part) > 63 for part in value.rstrip(".").split(".")):
                raise ValueError("主机名格式无效") from None
            return value

    @field_validator("schemas")
    @classmethod
    def valid_schemas(cls, value: list[str]) -> list[str]:
        result = []
        for name in value:
            if (not name or len(name.encode("utf-8")) > 63
                    or any(ord(c) < 32 or ord(c) == 127 for c in name)
                    or name.lower().startswith("pg_") or name.lower() == "information_schema"):
                raise ValueError("Schema 白名单只能包含有效的用户业务 Schema")
            if name not in result:
                result.append(name)
        return result

    @field_validator("password")
    @classmethod
    def valid_password(cls, value: SecretStr) -> SecretStr:
        if "\x00" in value.get_secret_value():
            raise ValueError("密码不得包含空字符")
        return value

    def connection_parameters(self) -> dict[str, Any]:
        return {"host": self.host, "port": self.port, "dbname": self.database,
                "user": self.user, "password": self.password.get_secret_value(),
                "sslmode": self.sslmode}


class CredentialCodec(Protocol):
    def encrypt(self, plaintext: bytes) -> bytes: ...
    def decrypt(self, ciphertext: bytes) -> bytes: ...


class WindowsDPAPICodec:
    """Current-user DPAPI, with UI disabled and no machine-wide decryption."""

    @staticmethod
    def _transform(data: bytes, *, decrypt: bool) -> bytes:
        if os.name != "nt":
            raise DatabaseRegistryError(
                "CREDENTIAL_PROTECTION_UNAVAILABLE",
                "此平台尚未配置安全凭据存储；未保存连接。Windows 使用当前账户的 DPAPI 保护。", 503)

        class DataBlob(ctypes.Structure):
            _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

        buffer = ctypes.create_string_buffer(data)
        source = DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
        output = DataBlob()
        crypt = ctypes.WinDLL("crypt32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree.restype = ctypes.c_void_p
        if decrypt:
            transform = crypt.CryptUnprotectData
            transform.argtypes = [ctypes.POINTER(DataBlob), ctypes.c_void_p,
                                  ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_ulong, ctypes.POINTER(DataBlob)]
        else:
            transform = crypt.CryptProtectData
            transform.argtypes = [ctypes.POINTER(DataBlob), ctypes.c_wchar_p,
                                  ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_ulong, ctypes.POINTER(DataBlob)]
        transform.restype = ctypes.c_int
        if not transform(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
            raise DatabaseRegistryError("CREDENTIAL_PROTECTION_FAILED", "无法使用当前账户保护或解密连接凭据。", 503)
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            kernel.LocalFree(ctypes.cast(output.pbData, ctypes.c_void_p))

    def encrypt(self, plaintext: bytes) -> bytes:
        return self._transform(plaintext, decrypt=False)

    def decrypt(self, ciphertext: bytes) -> bytes:
        return self._transform(ciphertext, decrypt=True)


@dataclass(frozen=True)
class DatabaseConnection:
    db_id: str
    label: str
    db_url: str = field(repr=False)
    catalog_path: Path = field(repr=False)
    builtin: bool = False

    @property
    def name(self) -> str:
        return self.label


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


_TABLES_SQL = """/* registry:tables */
SELECT c.oid, n.nspname AS schema, c.relname AS name,
       pg_catalog.obj_description(c.oid, 'pg_class') AS description,
       CASE WHEN c.reltuples < 0 THEN NULL ELSE c.reltuples::bigint END AS estimated_row_count
FROM pg_catalog.pg_class c
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p')
  AND n.nspname NOT LIKE 'pg\\_%%' ESCAPE '\\'
  AND n.nspname <> 'information_schema'
  AND pg_catalog.has_schema_privilege(n.oid, 'USAGE')
  AND pg_catalog.has_table_privilege(c.oid, 'SELECT')
  AND (%s::text[] IS NULL OR n.nspname = ANY(%s::text[]))
ORDER BY n.nspname, c.relname LIMIT %s
"""
_COLUMNS_SQL = """/* registry:columns */
SELECT a.attrelid AS table_oid, a.attnum, a.attname AS name,
       pg_catalog.format_type(a.atttypid, a.atttypmod) AS type,
       NOT a.attnotnull AS nullable,
       pg_catalog.col_description(a.attrelid, a.attnum) AS description,
       (a.atttypid IN ('date'::regtype, 'timestamp'::regtype, 'timestamptz'::regtype)
        AND EXISTS (SELECT 1 FROM pg_catalog.pg_index i
          JOIN pg_catalog.pg_class ic ON ic.oid = i.indexrelid
          JOIN pg_catalog.pg_am am ON am.oid = ic.relam
          WHERE i.indrelid = a.attrelid AND i.indisvalid AND i.indisready
            AND i.indpred IS NULL AND i.indkey[0] = a.attnum AND am.amname = 'btree')) AS indexed_date
FROM pg_catalog.pg_attribute a
WHERE a.attrelid = ANY(%s::oid[]) AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attrelid, a.attnum LIMIT %s
"""
_PRIMARY_KEYS_SQL = """/* registry:primary_keys */
SELECT con.conrelid AS table_oid, a.attname AS column_name, k.position
FROM pg_catalog.pg_constraint con
CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS k(attnum, position)
JOIN pg_catalog.pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum
WHERE con.contype = 'p' AND con.conrelid = ANY(%s::oid[])
ORDER BY con.conrelid, k.position
"""
_FOREIGN_KEYS_SQL = """/* registry:foreign_keys */
SELECT con.oid AS constraint_oid, con.conrelid AS table_oid,
       con.confrelid AS target_oid, ns.nspname AS target_schema,
       obj.relname AS target_table, source.attname AS source_column,
       target.attname AS target_column, k.position
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class obj ON obj.oid = con.confrelid
JOIN pg_catalog.pg_namespace ns ON ns.oid = obj.relnamespace
CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS k(attnum, position)
JOIN LATERAL unnest(con.confkey) WITH ORDINALITY AS ref(attnum, position)
  ON ref.position = k.position
JOIN pg_catalog.pg_attribute source ON source.attrelid = con.conrelid AND source.attnum = k.attnum
JOIN pg_catalog.pg_attribute target ON target.attrelid = con.confrelid AND target.attnum = ref.attnum
WHERE con.contype = 'f' AND con.conrelid = ANY(%s::oid[])
  AND con.confrelid = ANY(%s::oid[])
ORDER BY con.conrelid, con.oid, k.position
"""


def _index_only_plan(node: dict[str, Any]) -> bool:
    """Allow only a single index endpoint, never a sequential/bitmap scan."""
    if not isinstance(node, dict) or node.get("Node Type") not in {"Limit", "Index Scan", "Index Only Scan"}:
        return False
    children = node.get("Plans", [])
    if node.get("Node Type") == "Limit":
        return len(children) == 1 and _index_only_plan(children[0])
    return not children


def _indexed_date_range(connection: Any, schema: str, table: str, column: str) -> dict | None:
    endpoints = []
    # Savepoints make an optional stale/missing statistics index harmless to
    # the enclosing discovery transaction. EXPLAIN is never ANALYZE.
    try:
        with connection.transaction():
            for direction in (sql.SQL("ASC"), sql.SQL("DESC")):
                query = sql.SQL("SELECT {} AS value FROM {}.{} WHERE {} IS NOT NULL ORDER BY {} {} LIMIT 1").format(
                    sql.Identifier(column), sql.Identifier(schema), sql.Identifier(table),
                    sql.Identifier(column), sql.Identifier(column), direction)
                plan = connection.execute(sql.SQL("EXPLAIN (FORMAT JSON) ") + query).fetchone()
                plan_data = plan["QUERY PLAN"]
                if not isinstance(plan_data, list) or not plan_data or not _index_only_plan(plan_data[0].get("Plan", {})):
                    return None
                row = connection.execute(query).fetchone()
                value = row["value"] if row else None
                # Exclude +/-infinity or malformed date values from the model.
                if value is not None and not isinstance(value, (date, datetime)):
                    return None
                endpoints.append(value.isoformat() if value is not None else None)
    except psycopg.Error:
        return None
    return {"schema": schema, "table": table, "column": column,
            "min": endpoints[0], "max": endpoints[1]}


def discover_catalog(request: RegistrationRequest, db_id: str, settings: Settings,
                     connector: Callable[..., Any] = psycopg.connect) -> dict[str, Any]:
    """Discover granted business tables without COUNT(*), samples, or model calls."""
    _check_id(db_id)
    timeout = min(max(settings.statement_timeout_ms, 1), 10000)
    try:
        with connector(**request.connection_parameters(), connect_timeout=5, row_factory=dict_row,
                       options=f"-c default_transaction_read_only=on -c statement_timeout={timeout} -c lock_timeout=1000") as connection:
            connection.read_only = True
            with connection.transaction():
                connection.execute("SET LOCAL search_path TO pg_catalog")
                identity = connection.execute("SELECT current_database() AS name, current_setting('transaction_read_only') AS read_only").fetchone()
                if identity["read_only"] != "on":
                    raise DatabaseRegistryError("READ_ONLY_REQUIRED", "无法建立只读事务；未保存连接。")
                selected = request.schemas or None
                rows = connection.execute(_TABLES_SQL, (selected, selected, MAX_TABLES + 1)).fetchall()
                if not rows:
                    raise DatabaseRegistryError("NO_READABLE_TABLES", "未发现可 SELECT 的业务表；请检查 Schema 白名单、USAGE 和 SELECT 权限。")
                if len(rows) > MAX_TABLES:
                    raise DatabaseRegistryError("CATALOG_TOO_LARGE", f"可读业务表超过 {MAX_TABLES} 张，请缩小 Schema 白名单。")
                tables = {row["oid"]: {"schema": row["schema"], "name": row["name"],
                          "description": row["description"] or "", "row_count": None,
                          "estimated_row_count": row["estimated_row_count"],
                          "columns": [], "primary_key": [], "foreign_keys": []} for row in rows}
                oids = list(tables)
                columns = connection.execute(_COLUMNS_SQL, (oids, MAX_COLUMNS + 1)).fetchall()
                if len(columns) > MAX_COLUMNS:
                    raise DatabaseRegistryError("CATALOG_TOO_LARGE", f"可读业务列超过 {MAX_COLUMNS} 列，请缩小 Schema 白名单。")
                for column in columns:
                    tables[column["table_oid"]]["columns"].append({
                        "name": column["name"], "type": column["type"],
                        "nullable": column["nullable"], "description": column["description"] or ""})
                for table in tables.values():
                    if not table["columns"]:
                        raise DatabaseRegistryError("NO_READABLE_COLUMNS", "业务表没有可分析的列；未保存连接。")
                    connection.execute(sql.SQL("SELECT 1 FROM {}.{} LIMIT 0").format(
                        sql.Identifier(table["schema"]), sql.Identifier(table["name"])))
                for key in connection.execute(_PRIMARY_KEYS_SQL, (oids,)).fetchall():
                    tables[key["table_oid"]]["primary_key"].append(key["column_name"])
                foreign_keys: dict[tuple, dict] = {}
                for key in connection.execute(_FOREIGN_KEYS_SQL, (oids, oids)).fetchall():
                    group = (key["table_oid"], key["constraint_oid"])
                    if group not in foreign_keys:
                        foreign_keys[group] = {"columns": [], "references": {
                            "schema": key["target_schema"], "table": key["target_table"], "columns": []}}
                        tables[key["table_oid"]]["foreign_keys"].append(foreign_keys[group])
                    foreign_keys[group]["columns"].append(key["source_column"])
                    foreign_keys[group]["references"]["columns"].append(key["target_column"])
                indexed_dates = [column for column in columns if column["indexed_date"]]
                ranges = []
                for column in indexed_dates[:MAX_DATE_RANGES]:
                    table = tables[column["table_oid"]]
                    value = _indexed_date_range(connection, table["schema"], table["name"], column["name"])
                    if value is not None:
                        ranges.append(value)
                return {"database": db_id, "database_name": identity["name"], "dialect": "postgres",
                        "version": "registered-readonly-v1", "generated_at": _timestamp(),
                        "sample_values_included": False, "row_count_policy": "postgres_statistics_estimate_only",
                        "date_range_policy": "exact_index_endpoints_only", "date_ranges": ranges,
                        "date_ranges_limited": len(indexed_dates) > MAX_DATE_RANGES,
                        "tables": list(tables.values())}
    except DatabaseRegistryError:
        raise
    except psycopg.errors.QueryCanceled:
        raise DatabaseRegistryError("DATABASE_TIMEOUT", "连接验证或目录发现超时；请缩小 Schema 范围后重试。", 408) from None
    except psycopg.Error:
        raise DatabaseRegistryError("DATABASE_CONNECTION_FAILED", "无法验证只读 PostgreSQL 连接；请检查地址、账户、SSL 和访问权限。", 400) from None


def _summary(catalog: dict) -> dict:
    tables = catalog["tables"]
    return {"table_count": len(tables), "column_count": sum(len(t["columns"]) for t in tables),
            "foreign_key_count": sum(len(t.get("foreign_keys", [])) for t in tables),
            "schemas": sorted({t["schema"] for t in tables}),
            "tables": [{"schema": t["schema"], "name": t["name"], "column_count": len(t["columns"]),
                        "estimated_row_count": t.get("estimated_row_count")} for t in tables],
            "date_ranges": catalog.get("date_ranges", []), "sample_values_included": False}


class DatabaseRegistry:
    """One local registry; injectable codec/connector keep unit tests offline."""

    def __init__(self, root: Path | None = None, *, codec: CredentialCodec | None = None,
                 connector: Callable[..., Any] | None = None):
        self.root = root if root is not None else PROJECT_ROOT / ".runtime" / "registered_databases"
        self.codec = codec if codec is not None else WindowsDPAPICodec()
        self.connector = connector if connector is not None else psycopg.connect

    def _record_path(self, db_id: str) -> Path:
        _check_id(db_id)
        path = self.root / f"{db_id}.json"
        if path.is_symlink():
            raise DatabaseRegistryError("REGISTRY_INVALID", "本地数据库连接记录无效。", 409)
        return path

    def _catalog_path(self, record: dict) -> Path:
        _check_id(record.get("db_id"))
        version = record.get("catalog_version", "")
        if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
            raise DatabaseRegistryError("REGISTRY_INVALID", "本地数据库目录版本无效。", 409)
        path = self.root / f"{record['db_id']}-{version}.yaml"
        if path.is_symlink():
            raise DatabaseRegistryError("REGISTRY_INVALID", "本地数据库目录无效。", 409)
        return path

    def _load(self, db_id: str) -> dict:
        path = self._record_path(db_id)
        if not path.is_file():
            raise DatabaseRegistryError("DATABASE_NOT_FOUND", "未找到此本地数据库连接。", 404)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("db_id") != db_id or record.get("version") != 1:
                raise ValueError("invalid local record")
            self._catalog_path(record)
            return record
        except DatabaseRegistryError:
            raise
        except (OSError, ValueError, TypeError, AttributeError):
            raise DatabaseRegistryError("REGISTRY_INVALID", "本地数据库连接记录无法读取。", 409) from None

    def _decode(self, record: dict) -> RegistrationRequest:
        try:
            raw = self.codec.decrypt(base64.b64decode(record["protected_connection"], validate=True))
            return RegistrationRequest.model_validate_json(raw)
        except DatabaseRegistryError:
            raise
        except Exception:
            raise DatabaseRegistryError("CREDENTIAL_PROTECTION_FAILED", "无法使用当前账户解密连接凭据。", 503) from None

    def _public(self, record: dict) -> dict:
        # Explicit allowlist: encrypted blobs and local filesystem paths never
        # become part of a response, including failure responses.
        return {"db_id": record["db_id"], "name": record["name"], "label": record["name"],
                "builtin": False, "configured": True, "catalog_exists": self._catalog_path(record).is_file(),
                "catalog_summary": record["catalog_summary"],
                "connection": {key: record["connection"][key] for key in
                               ("host", "port", "database", "user", "sslmode", "schemas")},
                "created_at": record["created_at"], "updated_at": record["updated_at"]}

    def _save(self, record: dict, catalog: dict) -> None:
        # Each refresh publishes a new immutable catalog then atomically swaps
        # the record. Readers that already resolved an older path stay valid.
        catalog_path = self._catalog_path(record)
        record_path = self._record_path(record["db_id"])
        temporary = self.root / f".{record['db_id']}-{uuid4().hex}.tmp"
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            catalog_path.write_text(yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False), encoding="utf-8")
            temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temporary, record_path)
        except OSError:
            for path in (temporary, catalog_path):
                with suppress(OSError):
                    path.unlink(missing_ok=True)
            raise DatabaseRegistryError("REGISTRY_WRITE_FAILED", "无法保存本地连接和目录；源数据库未被修改。", 503) from None

    def register(self, request: RegistrationRequest, settings: Settings | None = None) -> dict:
        settings = settings or get_settings()
        # Protect before opening a connection, so unsupported credential storage
        # cannot result in a successful registration with plaintext fallback.
        plain = request.model_dump(mode="json")
        plain["password"] = request.password.get_secret_value()
        try:
            encrypted = self.codec.encrypt(json.dumps(plain, ensure_ascii=False).encode("utf-8"))
        except DatabaseRegistryError:
            raise
        except Exception:
            raise DatabaseRegistryError("CREDENTIAL_PROTECTION_FAILED", "无法安全保存连接凭据；未保存连接。", 503) from None
        db_id = "pg-" + uuid4().hex
        catalog = discover_catalog(request, db_id, settings, self.connector)
        now = _timestamp()
        record = {"version": 1, "db_id": db_id, "name": request.name,
                  "protected_connection": base64.b64encode(encrypted).decode("ascii"),
                  "connection": {key: plain[key] for key in ("host", "port", "database", "user", "sslmode", "schemas")},
                  "catalog_version": uuid4().hex, "catalog_summary": _summary(catalog),
                  "created_at": now, "updated_at": now}
        with _LOCK:
            self._save(record, catalog)
            return self._public(record)

    def list_registered(self) -> list[dict]:
        with _LOCK:
            if not self.root.is_dir():
                return []
            result = []
            for path in sorted(self.root.glob("pg-*.json")):
                if is_registered_database_id(path.stem):
                    result.append(self._public(self._load(path.stem)))
            return result

    def get_connection(self, db_id: str, settings: Settings | None = None) -> DatabaseConnection:
        with _LOCK:
            record = self._load(db_id)
            request = self._decode(record)
            # libpq quoting, rather than string interpolation, handles spaces,
            # quotes, backslashes, and all password punctuation safely.
            conninfo = make_conninfo(**request.connection_parameters(), connect_timeout=5,
                                     options="-c default_transaction_read_only=on")
            return DatabaseConnection(db_id, record["name"], conninfo, self._catalog_path(record))

    def refresh(self, db_id: str, settings: Settings | None = None) -> dict:
        with _LOCK:
            previous = self._load(db_id)
            request = self._decode(previous)
            catalog = discover_catalog(request, db_id, settings or get_settings(), self.connector)
            record = {**previous, "catalog_version": uuid4().hex,
                      "catalog_summary": _summary(catalog), "updated_at": _timestamp()}
            self._save(record, catalog)
            return self._public(record)

    def remove(self, db_id: str) -> None:
        with _LOCK:
            record = self._load(db_id)
            try:
                self._record_path(record["db_id"]).unlink()
                # Preserve immutable catalogs for already-running queries. They
                # contain schema metadata only; credentials are in the removed
                # record. No connection to the source database is made.
            except OSError:
                raise DatabaseRegistryError("REGISTRY_WRITE_FAILED", "无法移除此本地数据库连接。", 503) from None


@lru_cache(maxsize=1)
def get_registry() -> DatabaseRegistry:
    return DatabaseRegistry()


def _builtin_summary(path: Path) -> dict | None:
    try:
        catalog = load_catalog(path)
        return _summary({"tables": [{"schema": table.schema, "name": table.name,
                         "columns": table.columns, "foreign_keys": table.foreign_keys}
                         for table in catalog.tables]})
    except (ValueError, OSError):
        return None


def list_databases(settings: Settings | None = None) -> list[dict]:
    settings = settings or get_settings()
    builtins = []
    for db_id, label, configured, path in (
        ("chinook", "Chinook", bool(settings.db_url), settings.catalog_path),
        ("adventureworks", "AdventureWorks", bool(settings.aw_db_url), settings.aw_catalog_path),
    ):
        builtins.append({"db_id": db_id, "name": label, "label": label, "builtin": True,
                         "configured": configured, "catalog_exists": path.is_file(),
                         "catalog_summary": _builtin_summary(path)})
    return builtins + get_registry().list_registered()


def get_connection(db_id: str, settings: Settings | None = None) -> DatabaseConnection:
    settings = settings or get_settings()
    if db_id == "chinook":
        return DatabaseConnection(db_id, "Chinook", settings.db_url, settings.catalog_path, True)
    if db_id in {"aw", "adventureworks"}:
        return DatabaseConnection(db_id, "AdventureWorks", settings.aw_db_url, settings.aw_catalog_path, True)
    return get_registry().get_connection(db_id, settings)


def register_database(request: RegistrationRequest, settings: Settings | None = None) -> dict:
    return get_registry().register(request, settings)


def refresh_database(db_id: str, settings: Settings | None = None) -> dict:
    return get_registry().refresh(db_id, settings)


def remove_database(db_id: str, settings: Settings | None = None) -> None:
    get_registry().remove(db_id)
