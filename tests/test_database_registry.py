"""Offline registry tests: no model calls and no source-database writes."""
from datetime import date
import json

import psycopg
from psycopg.conninfo import conninfo_to_dict
from pydantic import ValidationError
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from qa_agent.config import Settings
from qa_agent import database_registry as registry_module
from qa_agent.database_registry import (
    DatabaseRegistry, DatabaseRegistryError, RegistrationRequest,
    WindowsDPAPICodec, discover_catalog, is_registered_database_id,
)
from qa_agent.sql.catalog import load_catalog


class TestCodec:
    __test__ = False

    def encrypt(self, plaintext):
        # Test-only reversible obfuscation; production always defaults to DPAPI.
        return bytes(value ^ 0xAB for value in plaintext)

    def decrypt(self, ciphertext):
        return self.encrypt(ciphertext)


class Rows:
    def __init__(self, values):
        self.values = values

    def fetchall(self):
        return self.values

    def fetchone(self):
        return self.values[0] if self.values else None


class FakeConnection:
    def __init__(self):
        self.read_only = False
        self.in_transaction = 0
        self.calls = []
        self.tables = [
            {"oid": 1, "schema": "sales", "name": "orders", "description": "业务订单", "estimated_row_count": 42},
            {"oid": 2, "schema": "sales", "name": "customers", "description": None, "estimated_row_count": None},
        ]
        self.columns = [
            {"table_oid": 1, "attnum": 1, "name": "tenant_id", "type": "integer", "nullable": False, "description": None, "indexed_date": False},
            {"table_oid": 1, "attnum": 2, "name": "customer_id", "type": "integer", "nullable": False, "description": "客户", "indexed_date": False},
            {"table_oid": 1, "attnum": 3, "name": "ordered_at", "type": "date", "nullable": True, "description": None, "indexed_date": True},
            {"table_oid": 2, "attnum": 1, "name": "tenant_id", "type": "integer", "nullable": False, "description": None, "indexed_date": False},
            {"table_oid": 2, "attnum": 2, "name": "id", "type": "integer", "nullable": False, "description": None, "indexed_date": False},
        ]
        self.plan_node = "Index Only Scan"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def transaction(self):
        connection = self

        class Transaction:
            def __enter__(self):
                connection.in_transaction += 1

            def __exit__(self, *args):
                connection.in_transaction -= 1

        return Transaction()

    def execute(self, query, params=None):
        assert self.read_only and self.in_transaction > 0
        rendered = query if isinstance(query, str) else query.as_string()
        self.calls.append((rendered, params))
        if "current_database()" in rendered:
            return Rows([{"name": "existing_business_db", "read_only": "on"}])
        if "registry:tables" in rendered:
            return Rows(self.tables)
        if "registry:columns" in rendered:
            return Rows(self.columns)
        if "registry:primary_keys" in rendered:
            return Rows([{"table_oid": 2, "column_name": "tenant_id", "position": 1},
                         {"table_oid": 2, "column_name": "id", "position": 2}])
        if "registry:foreign_keys" in rendered:
            return Rows([
                {"constraint_oid": 99, "table_oid": 1, "target_oid": 2,
                 "target_schema": "sales", "target_table": "customers", "source_column": "tenant_id", "target_column": "tenant_id", "position": 1},
                {"constraint_oid": 99, "table_oid": 1, "target_oid": 2,
                 "target_schema": "sales", "target_table": "customers", "source_column": "customer_id", "target_column": "id", "position": 2},
            ])
        if rendered.startswith("EXPLAIN"):
            return Rows([{"QUERY PLAN": [{"Plan": {"Node Type": "Limit", "Plans": [{"Node Type": self.plan_node}]}}]}])
        if " AS value " in rendered:
            return Rows([{"value": date(2020, 1, 1) if " ASC " in rendered else date(2026, 10, 18)}])
        return Rows([])


class FakeConnector:
    def __init__(self, connection=None):
        self.connection = connection or FakeConnection()
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.connection


@pytest.fixture
def settings(tmp_path):
    return Settings(db_url="builtin-secret", aw_db_url="aw-secret",
                    catalog_path=tmp_path / "missing.yaml", aw_catalog_path=tmp_path / "aw-missing.yaml")


@pytest.fixture
def request_payload():
    return RegistrationRequest(name="公司业务库", host="127.0.0.1", port=5432,
                               database="live-db", user="readonly",
                               password="p@ss:word ' /?\\=123", schemas=["sales"])


@pytest.fixture
def local_registry(tmp_path):
    return DatabaseRegistry(tmp_path / "registrations", codec=TestCodec(), connector=FakeConnector())


def test_register_encrypted_roundtrip_and_public_catalog(local_registry, request_payload, settings):
    public = local_registry.register(request_payload, settings)
    db_id = public["db_id"]
    assert is_registered_database_id(db_id)
    assert public["catalog_summary"]["table_count"] == 2
    assert public["catalog_summary"]["column_count"] == 5
    assert public["catalog_summary"]["tables"][0]["estimated_row_count"] == 42
    assert public["catalog_summary"]["date_ranges"][0]["min"] == "2020-01-01"
    assert public["catalog_summary"]["sample_values_included"] is False
    assert "password" not in public["connection"]
    assert request_payload.password.get_secret_value() not in json.dumps(public)
    connection = local_registry.get_connection(db_id, settings)
    parsed = conninfo_to_dict(connection.db_url)
    assert parsed["password"] == request_payload.password.get_secret_value()
    assert parsed["host"] == request_payload.host
    assert "default_transaction_read_only=on" in parsed["options"]
    assert request_payload.password.get_secret_value() not in repr(connection)
    assert request_payload.password.get_secret_value() not in repr(request_payload)
    for file in local_registry.root.iterdir():
        assert request_payload.password.get_secret_value() not in file.read_text(encoding="utf-8")
    catalog = load_catalog(connection.catalog_path)
    assert catalog.database == db_id
    assert catalog.metadata["database_name"] == "existing_business_db"
    assert catalog.tables[0].row_count is None
    assert catalog.tables[0].columns[0].sample_values == ()
    assert catalog.tables[1].primary_key == ("tenant_id", "id")
    assert catalog.tables[0].foreign_keys[0] == {"columns": ["tenant_id", "customer_id"], "references": {
        "schema": "sales", "table": "customers", "columns": ["tenant_id", "id"]}}


def test_metadata_permissions_limits_and_queries_are_readonly(local_registry, request_payload, settings):
    local_registry.register(request_payload, settings)
    connector = local_registry.connector
    kwargs = connector.calls[0]
    assert kwargs["connect_timeout"] == 5
    assert "default_transaction_read_only=on" in kwargs["options"]
    assert "statement_timeout=5000" in kwargs["options"]
    assert not kwargs.get("autocommit", False)
    calls = connector.connection.calls
    table_sql, table_params = next((query, parameters) for query, parameters in calls if "registry:tables" in query)
    assert "has_schema_privilege" in table_sql and "'USAGE'" in table_sql
    assert "has_table_privilege" in table_sql and "'SELECT'" in table_sql
    assert "c.relkind IN ('r', 'p')" in table_sql
    assert "information_schema" in table_sql and "pg\\_" in table_sql
    assert table_params == (["sales"], ["sales"], registry_module.MAX_TABLES + 1)
    sql_text = "\n".join(query for query, _ in calls)
    assert "COUNT(*)" not in sql_text and "SELECT DISTINCT" not in sql_text
    assert not any(query.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "GRANT", "COPY")) for query, _ in calls)
    assert "ref.position = k.position" in sql_text


def test_refresh_publishes_immutable_catalog_and_remove_never_connects(local_registry, request_payload, settings):
    public = local_registry.register(request_payload, settings)
    old = local_registry.get_connection(public["db_id"], settings).catalog_path
    calls_before = len(local_registry.connector.calls)
    refreshed = local_registry.refresh(public["db_id"], settings)
    new = local_registry.get_connection(public["db_id"], settings).catalog_path
    assert old != new and old.is_file() and new.is_file()
    assert refreshed["created_at"] == public["created_at"]
    assert len(local_registry.connector.calls) == calls_before + 1
    before_remove = len(local_registry.connector.calls)
    local_registry.remove(public["db_id"])
    assert len(local_registry.connector.calls) == before_remove
    assert local_registry.list_registered() == []
    with pytest.raises(DatabaseRegistryError, match="未找到"):
        local_registry.get_connection(public["db_id"], settings)
    assert old.is_file() and new.is_file()  # In-flight readers retain valid paths.


def test_failed_refresh_keeps_previous_connection(local_registry, request_payload, settings):
    public = local_registry.register(request_payload, settings)
    before = local_registry.get_connection(public["db_id"], settings).catalog_path

    def broken(**kwargs):
        raise psycopg.OperationalError("leaked password=" + request_payload.password.get_secret_value())

    local_registry.connector = broken
    with pytest.raises(DatabaseRegistryError) as error:
        local_registry.refresh(public["db_id"], settings)
    assert request_payload.password.get_secret_value() not in str(error.value)
    assert error.value.code == "DATABASE_CONNECTION_FAILED"
    assert local_registry.get_connection(public["db_id"], settings).catalog_path == before
    assert local_registry.list_registered()[0] == public


def test_atomic_publish_failure_keeps_previous_catalog(local_registry, request_payload, settings, monkeypatch):
    public = local_registry.register(request_payload, settings)
    old = local_registry.get_connection(public["db_id"], settings).catalog_path
    before_files = set(local_registry.root.iterdir())

    def replace_denied(*args, **kwargs):
        raise PermissionError("sensitive driver detail should not be exposed")

    monkeypatch.setattr(registry_module.os, "replace", replace_denied)
    with pytest.raises(DatabaseRegistryError) as error:
        local_registry.refresh(public["db_id"], settings)
    assert error.value.code == "REGISTRY_WRITE_FAILED"
    assert "sensitive" not in str(error.value)
    assert set(local_registry.root.iterdir()) == before_files
    assert local_registry.get_connection(public["db_id"], settings).catalog_path == old
    assert local_registry.list_registered()[0] == public


def test_public_connection_fields_are_explicitly_allowlisted(local_registry, request_payload, settings):
    public = local_registry.register(request_payload, settings)
    path = local_registry.root / (public["db_id"] + ".json")
    record = json.loads(path.read_text(encoding="utf-8"))
    record["connection"]["password"] = "future-or-corrupt-secret"
    record["connection"]["db_url"] = "postgresql://secret@host/db"
    path.write_text(json.dumps(record), encoding="utf-8")
    assert local_registry.list_registered() == [public]


@pytest.mark.parametrize("field,value", [
    ("host", "postgresql://user:secret@localhost/db"), ("host", "localhost password=secret"),
    ("host", "/tmp/pg"), ("host", "localhost,remote"), ("port", "5432"),
    ("port", 0), ("schemas", ["pg_catalog"]), ("schemas", ["pg_toast"]),
    ("schemas", ["information_schema"]), ("database", "bad\nname"),
    ("password", "invalid\x00password"),
])
def test_input_validation_blocks_dsn_system_schema_and_invalid_port(request_payload, field, value):
    data = request_payload.model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        RegistrationRequest.model_validate(data)


@pytest.mark.parametrize("db_id", ["../../.env", "chinook", "pg-../../a", "pg-1234", "/etc/passwd", "pg-" + "z" * 32])
def test_unregistered_ids_cannot_be_paths(local_registry, settings, db_id):
    for action in (lambda: local_registry.get_connection(db_id, settings),
                   lambda: local_registry.refresh(db_id, settings), lambda: local_registry.remove(db_id)):
        with pytest.raises(DatabaseRegistryError) as error:
            action()
        assert error.value.code == "DATABASE_NOT_FOUND"


def test_empty_or_oversize_catalog_never_persists(local_registry, request_payload, settings, monkeypatch):
    fake = local_registry.connector.connection
    fake.tables = []
    with pytest.raises(DatabaseRegistryError) as error:
        local_registry.register(request_payload, settings)
    assert error.value.code == "NO_READABLE_TABLES"
    assert not local_registry.root.exists()
    fake.tables = [{"oid": 1, "schema": "sales", "name": "one", "description": "", "estimated_row_count": None}]
    monkeypatch.setattr(registry_module, "MAX_COLUMNS", 1)
    with pytest.raises(DatabaseRegistryError) as error:
        local_registry.register(request_payload, settings)
    assert error.value.code == "CATALOG_TOO_LARGE"
    monkeypatch.setattr(registry_module, "MAX_TABLES", 0)
    with pytest.raises(DatabaseRegistryError) as error:
        local_registry.register(request_payload, settings)
    assert error.value.code == "CATALOG_TOO_LARGE"
    assert not local_registry.root.exists()


def test_no_date_endpoints_when_plan_would_scan_table(local_registry, request_payload, settings):
    local_registry.connector.connection.plan_node = "Seq Scan"
    public = local_registry.register(request_payload, settings)
    assert public["catalog_summary"]["date_ranges"] == []
    assert not any(" AS value " in query and not query.startswith("EXPLAIN")
                   for query, _ in local_registry.connector.connection.calls)


def test_builtin_list_and_connection_hide_dsns(local_registry, settings, monkeypatch):
    monkeypatch.setattr(registry_module, "get_registry", lambda: local_registry)
    databases = registry_module.list_databases(settings)
    assert [item["db_id"] for item in databases] == ["chinook", "adventureworks"]
    assert all(item["builtin"] for item in databases)
    assert "builtin-secret" not in json.dumps(databases) and "aw-secret" not in json.dumps(databases)
    assert registry_module.get_connection("aw", settings).db_url == "aw-secret"


def test_codec_failure_does_not_connect_or_save(tmp_path, request_payload, settings):
    class BrokenCodec(TestCodec):
        def encrypt(self, plaintext):
            raise RuntimeError("plaintext should never appear: " + plaintext.decode())

    connector = FakeConnector()
    local = DatabaseRegistry(tmp_path / "empty", codec=BrokenCodec(), connector=connector)
    with pytest.raises(DatabaseRegistryError) as error:
        local.register(request_payload, settings)
    assert error.value.code == "CREDENTIAL_PROTECTION_FAILED"
    assert request_payload.password.get_secret_value() not in str(error.value)
    assert connector.calls == [] and not local.root.exists()


@pytest.mark.skipif(registry_module.os.name != "nt", reason="DPAPI is Windows current-user credential protection")
def test_actual_windows_dpapi_roundtrip():
    codec = WindowsDPAPICodec()
    secret = b"unit-test credential with quotes ' and punctuation !@#"
    encrypted = codec.encrypt(secret)
    assert secret not in encrypted
    assert encrypted != secret
    assert codec.decrypt(encrypted) == secret


@pytest.fixture
def api_client(monkeypatch, local_registry, settings):
    from api import databases
    monkeypatch.setattr(registry_module, "get_registry", lambda: local_registry)
    monkeypatch.setattr(registry_module, "get_settings", lambda: settings)
    app = FastAPI()
    app.include_router(databases.router)
    with TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        yield client


def _json_request(request_payload):
    data = request_payload.model_dump(mode="json")
    data["password"] = request_payload.password.get_secret_value()
    return data


def test_api_add_list_refresh_delete(api_client, request_payload):
    created = api_client.post("/api/databases", json=_json_request(request_payload))
    assert created.status_code == 201, created.text
    db_id = created.json()["db_id"]
    assert request_payload.password.get_secret_value() not in created.text
    assert len(api_client.get("/api/databases").json()["databases"]) == 3
    assert api_client.post(f"/api/databases/{db_id}/refresh").status_code == 200
    assert api_client.delete(f"/api/databases/{db_id}").json() == {"db_id": db_id, "removed": True}
    assert api_client.delete("/api/databases/chinook").status_code == 404


def test_api_validation_never_echoes_password_or_invalid_input(api_client, request_payload):
    body = _json_request(request_payload)
    body["password"] = "unmistakable-sensitive-input-" * 200
    body["host"] = "postgresql://username:another-secret@host/db"
    response = api_client.post("/api/databases", json=body)
    assert response.status_code == 422
    assert "unmistakable" not in response.text and "another-secret" not in response.text
    assert "input" not in response.text and "ctx" not in response.text
    assert api_client.post("/api/databases", content="bad json", headers={"content-type": "application/json"}).status_code == 422


@pytest.mark.parametrize("headers", [
    {"Origin": "https://evil.example"}, {"Origin": "null"},
    {"Sec-Fetch-Site": "cross-site"}, {"Host": "evil.example"},
])
def test_api_rejects_nonlocal_and_cross_origin_requests(api_client, request_payload, headers):
    response = api_client.post("/api/databases", json=_json_request(request_payload), headers=headers)
    assert response.status_code == 403


def test_api_accepts_local_same_origin(api_client):
    assert api_client.get("/api/databases", headers={"Origin": "http://127.0.0.1"}).status_code == 200
