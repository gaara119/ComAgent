"""Execute SQL with a fresh read-only PostgreSQL transaction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

import psycopg


class SQLExecutionError(RuntimeError):
    def __init__(self, message: str, sqlstate: str | None = None):
        super().__init__(message)
        self.sqlstate = sqlstate


class SQLTimeoutError(SQLExecutionError):
    """The PostgreSQL statement timeout canceled the query."""


@dataclass(frozen=True)
class SQLResult:
    columns: list[str]
    rows: list[list[Any]]
    table: list[dict[str, Any]]
    row_count: int
    truncated: bool = False


def serialize_value(value: Any) -> Any:
    """Preserve NULL, integers, and exact money; normalize dates for JSON."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {str(key): serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    return value


def unique_columns(names: list[str]) -> list[str]:
    """Make dictionary keys distinct without dropping any result column.

    Original names are reserved first, so [x, x, x__2] becomes
    [x, x__3, x__2], and no later real alias overwrites a generated one.
    """
    reserved, used, result = set(names), set(), []
    for name in names:
        candidate = name
        if candidate in used:
            suffix = 2
            while f"{name}__{suffix}" in reserved or f"{name}__{suffix}" in used:
                suffix += 1
            candidate = f"{name}__{suffix}"
        used.add(candidate)
        result.append(candidate)
    return result


def execute_sql(
    sql: str,
    db_url: str,
    statement_timeout_ms: int = 5000,
    max_rows: int = 200,
) -> SQLResult:
    """Run a previously validated query; caller must call validate_sql first.

    The server cursor fetches at most max_rows + 1 rows. If an explicit SQL
    LIMIT exceeds the response cap, SQL is preserved and truncated is reported.
    row_count is the number of returned rows, never an invented total count.
    """
    if not db_url:
        raise SQLExecutionError("未配置 DB_URL；请先初始化 Chinook 并配置只读连接。")
    if statement_timeout_ms < 1 or max_rows < 1:
        raise SQLExecutionError("数据库超时和结果行数上限必须大于 0。")
    try:
        with psycopg.connect(db_url, connect_timeout=5) as connection:
            connection.read_only = True
            with connection.transaction():
                with connection.cursor() as control:
                    control.execute(
                        "SELECT set_config('statement_timeout', %s, true)",
                        (str(statement_timeout_ms),),
                    )
                    control.execute("SET LOCAL search_path TO pg_catalog, public")
                with connection.cursor(name="qa_d1_result") as cursor:
                    cursor.execute(sql)
                    columns = unique_columns([column.name for column in cursor.description or []])
                    fetched = cursor.fetchmany(max_rows + 1)
                    truncated = len(fetched) > max_rows
                    rows = [
                        [serialize_value(value) for value in row]
                        for row in fetched[:max_rows]
                    ]
                    table = [dict(zip(columns, row, strict=True)) for row in rows]
        return SQLResult(columns=columns, rows=rows, table=table, row_count=len(rows), truncated=truncated)
    except psycopg.errors.QueryCanceled as exc:
        raise SQLTimeoutError(
            f"数据库查询超过 {statement_timeout_ms} 毫秒，已被 PostgreSQL 取消。", exc.sqlstate
        ) from exc
    except psycopg.Error as exc:
        primary = exc.diag.message_primary if exc.diag else None
        if exc.sqlstate and primary:
            message = f"数据库查询失败（SQLSTATE {exc.sqlstate}）：{primary}"
        else:
            # libpq connection messages are not copied into user-visible logs:
            # a driver/server failure must never expose the configured DSN.
            message = "无法连接数据库，请检查 Docker 服务、端口及本地 DB_URL 配置。"
        raise SQLExecutionError(message, exc.sqlstate) from exc
