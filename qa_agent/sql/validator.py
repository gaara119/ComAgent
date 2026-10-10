"""Validate the complete PostgreSQL AST before database execution.

SQLGlot qualification runs on a copy: checking CTEs, aliases, and correlated
subqueries must not silently change the SQL that the user sees or that is run.
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, OptimizeError, ParseError, UnsupportedError
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope, walk_in_scope
from sqlglot.schema import MappingSchema

from qa_agent.sql.catalog import Catalog, CatalogError


class SQLValidationError(ValueError):
    """SQL is unsafe or references objects outside the catalog."""


@dataclass(frozen=True)
class ValidatedSQL:
    sql: str
    tables_used: list[str]
    default_limit_added: bool = False


# Names are SQLGlot's canonical names, which may differ from PostgreSQL syntax
# (for example date_trunc is TIMESTAMP_TRUNC and char_length is LENGTH).
ALLOWED_FUNCTIONS = frozenset({
    "COUNT", "SUM", "AVG", "MIN", "MAX", "ROUND", "ABS", "CEIL", "FLOOR",
    "COALESCE", "NULLIF", "LOWER", "UPPER", "LENGTH", "TRIM", "SUBSTRING",
    "EXTRACT", "TIMESTAMP_TRUNC", "DATE_TRUNC", "CAST", "CASE", "IF",
    "EXISTS", "CONCAT", "CONCAT_WS", "GREATEST", "LEAST", "DATE",
    "CURRENT_DATE", "CURRENT_TIMESTAMP", "CURRENT_TIME", "TIME_TO_STR",
    # SQLGlot represents these boolean operators as Func subclasses.
    "AND", "OR",
})
ALLOWED_CAST_TYPES = frozenset({
    "SMALLINT", "INT", "BIGINT", "DECIMAL", "FLOAT", "DOUBLE", "REAL",
    "BOOLEAN", "CHAR", "VARCHAR", "TEXT", "DATE", "TIME", "TIMETZ",
    "TIMESTAMP", "TIMESTAMPTZ", "INTERVAL",
})


def _function_name(function: exp.Func) -> str:
    if isinstance(function, exp.Anonymous):
        return function.name.upper()
    return function.sql_name().upper()


def _root_is_scalar_aggregate(expression: exp.Expression) -> bool:
    if not isinstance(expression, exp.Select) or expression.args.get("group"):
        return False
    # Windows produce a value per input row, and must receive a list limit.
    nodes = list(walk_in_scope(expression))
    return any(isinstance(node, exp.AggFunc) for node in nodes) and not any(
        isinstance(node, exp.Window) for node in nodes
    )


def validate_sql(sql: str, catalog: Catalog, max_rows: int = 200) -> ValidatedSQL:
    if not isinstance(sql, str) or not sql.strip():
        raise SQLValidationError("模型没有生成有效 SQL。")
    if max_rows < 1:
        raise SQLValidationError("查询行数上限必须大于 0。")
    try:
        statements = sqlglot.parse(sql, read="postgres", error_level=ErrorLevel.RAISE)
    except (ParseError, ValueError) as exc:
        raise SQLValidationError(f"PostgreSQL SQL 无法解析：{exc}") from exc
    # Empty/comment-only statements do not authorize a second statement.
    if len(statements) != 1 or statements[0] is None:
        raise SQLValidationError("只允许一条 SELECT 查询，禁止多语句。")
    expression = statements[0]
    if not isinstance(expression, (exp.Select, exp.SetOperation)):
        raise SQLValidationError("只允许 SELECT 查询。")
    if len(list(expression.walk())) > 5000:
        raise SQLValidationError("SQL 结构过于复杂。")
    for node in expression.walk():
        if isinstance(node, (exp.DDL, exp.DML, exp.Into, exp.Lock, exp.Command)):
            raise SQLValidationError("禁止写操作、SELECT INTO、锁定或命令，包括 CTE 内部操作。")
        if isinstance(node, exp.With) and node.args.get("recursive"):
            raise SQLValidationError("D1 不支持递归 CTE。")
        if isinstance(node, exp.Table):
            if not isinstance(node.this, exp.Identifier) or node.args.get("catalog"):
                raise SQLValidationError("禁止表函数和跨数据库对象。")
        if isinstance(node, exp.Dot) and isinstance(node.expression, exp.Func):
            raise SQLValidationError("禁止带命名空间的函数。")
        if isinstance(node, exp.Func) and _function_name(node) not in ALLOWED_FUNCTIONS:
            raise SQLValidationError(f"函数 {_function_name(node)} 不在 D1 白名单中。")
        if isinstance(node, exp.DataType):
            data_type = node.this.value if hasattr(node.this, "value") else str(node.this)
            if data_type.upper() not in ALLOWED_CAST_TYPES:
                raise SQLValidationError(f"不允许数据类型 {data_type} 或自定义类型转换。")

    checked = normalize_identifiers(expression.copy(), dialect="postgres")
    physical_tables = set()
    try:
        scopes = traverse_scope(checked)
        if not scopes:
            raise SQLValidationError("无法建立 SQL 查询作用域。")
        for scope in scopes:
            for _, source in scope.selected_sources.values():
                if isinstance(source, exp.Table):
                    table = catalog.get_table(source.name, source.db or "public")
                    physical_tables.add(
                        table.name if table.schema == "public" else f"{table.schema}.{table.name}"
                    )
        schema = MappingSchema(catalog.sqlglot_schema(), dialect="postgres", normalize=False)
        qualify(
            checked, dialect="postgres", db="public", schema=schema,
            allow_partial_qualification=False, validate_qualify_columns=True,
        )
    except SQLValidationError:
        raise
    except (CatalogError, OptimizeError, ValueError, KeyError, UnsupportedError) as exc:
        raise SQLValidationError(f"表列或作用域校验失败：{exc}") from exc

    added = False
    if expression.args.get("limit") is None and not _root_is_scalar_aggregate(expression):
        expression = expression.limit(max_rows, copy=False)
        added = True
    # Render strictly; unsupported PostgreSQL output must not get executed.
    try:
        rendered = expression.sql(dialect="postgres", unsupported_level=ErrorLevel.RAISE)
    except UnsupportedError as exc:
        raise SQLValidationError(f"D1 不支持该 PostgreSQL 语法：{exc}") from exc
    return ValidatedSQL(sql=rendered, tables_used=sorted(physical_tables), default_limit_added=added)
