"""Serialization invariants plus real PostgreSQL integration when configured."""

import os
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
from dotenv import dotenv_values

from qa_agent.sql.executor import SQLExecutionError, SQLTimeoutError, execute_sql, serialize_value, unique_columns


@dataclass(frozen=True)
class _PrivateDatabase:
    # Pytest displays fixture repr on a failed assertion, so secrets must not
    # be represented there even though the local environment contains them.
    url: str = field(repr=False)


def test_serialization_preserves_money_null_integer_and_dates():
    assert serialize_value(Decimal("1234567890123456.10")) == "1234567890123456.10"
    assert serialize_value(None) is None
    assert serialize_value(0) == 0
    assert type(serialize_value(0)) is int
    assert serialize_value(date(2026, 10, 10)) == "2026-10-10"
    assert serialize_value(datetime(2026, 10, 10, 8, 9, 10)) == "2026-10-10T08:09:10"


def test_duplicate_result_labels_cannot_drop_columns():
    assert unique_columns(["value", "value", "value__2", "value", "value__3"]) == [
        "value", "value__4", "value__2", "value__5", "value__3",
    ]


@pytest.fixture(scope="module")
def db_url():
    env = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    url = os.environ.get("DB_URL") or env.get("DB_URL")
    if not url:
        pytest.skip("真实 PostgreSQL 尚未配置；纯校验与序列化测试仍执行。")
    try:
        with psycopg.connect(url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
    except psycopg.Error:
        pytest.skip("真实 PostgreSQL 暂不可连接；该集成测试没有伪造通过。")
    return _PrivateDatabase(url)


def test_real_result_money_date_null_and_duplicate_columns(db_url):
    result = execute_sql(
        "SELECT 7 AS value,12.340::numeric AS value,DATE '2026-10-10' AS day,NULL::text AS missing", db_url.url,
    )
    assert result.columns == ["value", "value__2", "day", "missing"]
    assert result.rows == [[7, "12.340", "2026-10-10", None]]
    assert result.table == [{"value": 7, "value__2": "12.340", "day": "2026-10-10", "missing": None}]
    assert result.row_count == 1 and not result.truncated


def test_real_empty_rows_count_zero_and_sum_null_are_distinct(db_url):
    empty = execute_sql("SELECT total FROM invoice WHERE false", db_url.url)
    aggregate = execute_sql("SELECT COUNT(*) AS n,SUM(total) AS amount FROM invoice WHERE false", db_url.url)
    assert empty.row_count == 0 and empty.rows == []
    assert aggregate.rows == [[0, None]] and aggregate.row_count == 1


def test_real_connection_transaction_is_read_only(db_url):
    result = execute_sql("SELECT current_setting('transaction_read_only') AS setting", db_url.url)
    assert result.rows == [["on"]]
    # This false predicate changes no data even if a regression disables read
    # only, while PostgreSQL still rejects the data-modifying CTE in read-only.
    with pytest.raises(SQLExecutionError) as failure:
        execute_sql("WITH no_changes AS (DELETE FROM customer WHERE false RETURNING *) SELECT * FROM no_changes", db_url.url)
    assert failure.value.sqlstate in {"25006", "42501", "0A000"}


def test_real_postgres_statement_timeout_is_active(db_url):
    with pytest.raises(SQLTimeoutError) as failure:
        execute_sql("SELECT pg_sleep(0.2)", db_url.url, statement_timeout_ms=10)
    assert failure.value.sqlstate == "57014"


def test_real_response_cap_is_explicit_and_preserves_order(db_url):
    result = execute_sql("SELECT customer_id FROM customer ORDER BY customer_id LIMIT 10", db_url.url, max_rows=3)
    assert result.rows == [[1], [2], [3]]
    assert result.row_count == 3 and result.truncated
