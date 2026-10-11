"""Validate the complete PostgreSQL AST before database execution.

SQLGlot qualification runs on a copy: checking CTEs, aliases, and correlated
subqueries must not silently change the SQL that the user sees or that is run.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, OptimizeError, ParseError, UnsupportedError
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope, walk_in_scope
from sqlglot.schema import MappingSchema

from qa_agent.sql.catalog import Catalog, CatalogError


def validate_question_sources(question: str, catalog: Catalog) -> list[str]:
    """Reject confidently explicit unknown table names before model fallback.

    This is deliberately limited to named source syntax, not general entity
    extraction: a country, a column or ordinary question prose is not a table.
    It prevents an unknown requested table being replaced by customer plus an
    artificial empty result. It does not create the D3 multi-table locator.
    """
    identifier = r"(?:[A-Za-z_][A-Za-z0-9_]*\.)?[A-Za-z_][A-Za-z0-9_]*"
    names = []
    patterns = [rf"(?<![A-Za-z0-9_])(?P<name>{identifier})\s*[`\"']?\s*表",
                rf"(?:表名(?:为|是|叫|：|:)|table\s+(?:named|called))\s*[`\"']?(?P<name>{identifier})",
                rf"(?:名为|叫做)\s*[`\"']?(?P<name>{identifier})\s*[`\"']?\s*的表"]
    for pattern in patterns:
        names.extend(match.group("name") for match in re.finditer(pattern, question, re.IGNORECASE))
    result = []
    for name in dict.fromkeys(names):
        parts = name.split(".")
        try:
            table = catalog.get_table(parts[-1], parts[-2] if len(parts) == 2 else "public")
        except CatalogError as exc:
            raise SQLValidationError(f"请求显式指定的表 {name} 不在真实目录中，不能替换成其他业务表。") from exc
        canonical = table.name if table.schema == "public" else f"{table.schema}.{table.name}"
        if canonical not in result:
            result.append(canonical)
    return result


def validate_generation_claim(question: str, sql: str, explanation: str) -> None:
    """A model's explicit refusal or empty placeholder is not a DB answer."""
    if re.search(r"(?:无法|不能|不支持)(?:执行|查询|生成(?:SQL|查询|针对)|访问)|目标表.*不在.*目录", explanation, re.IGNORECASE):
        raise SQLValidationError("模型明确说明无法执行该请求，禁止把占位 SQL 当作数据库空结果。")
    expression = sqlglot.parse_one(sql, read="postgres")
    limit = expression.args.get("limit")
    zero_limit = limit and isinstance(limit.expression, exp.Literal) and str(limit.expression.this) == "0"
    constant_projection = isinstance(expression, exp.Select) and all(isinstance(item, exp.Literal) for item in expression.expressions)
    explicit_zero = re.search(r"\blimit\s+0\b|前\s*0\s*(?:行|个)|\b0\s+rows\b", question, re.IGNORECASE)
    if zero_limit and constant_projection and not explicit_zero:
        raise SQLValidationError("模型生成了未请求的零行常量占位查询，不能冒充原条件的空结果。")


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


def validate_value_bindings(sql: str, catalog: Catalog, bindings: list[dict]) -> None:
    """Prove each verified value is a mandatory filter on its physical table.

    An equality in SELECT, a comment, an OR bypass or a different subquery is
    insufficient. Repeated table scans must each preserve the corresponding
    bindings. Conservative rejection of complex derived-table propagation is
    intentional in D2's single-table stage; no SQL text is rewritten here.
    """
    if not bindings:
        return
    expression = normalize_identifiers(sqlglot.parse_one(sql, read="postgres"), dialect="postgres")
    try:
        checked = qualify(expression, dialect="postgres", db="public",
                          schema=MappingSchema(catalog.sqlglot_schema(), dialect="postgres", normalize=False),
                          allow_partial_qualification=False, validate_qualify_columns=True)
    except (OptimizeError, ValueError, KeyError, UnsupportedError) as exc:
        raise SQLValidationError("值绑定核验无法建立真实字段作用域。") from exc
    scopes = traverse_scope(checked)
    by_table: dict[str, list[dict]] = {}
    for binding in bindings:
        parts = str(binding.get("column", "")).split(".")
        if len(parts) not in {2, 3} or binding.get("operator") not in {"=", "!=", "IN"}:
            raise SQLValidationError("值绑定包含不受支持的字段或操作符。")
        table = catalog.get_table(parts[-2], parts[-3] if len(parts) == 3 else "public")
        if parts[-1] not in table.column_names:
            raise SQLValidationError("值绑定引用了目录之外的字段。")
        by_table.setdefault(parts[-2], []).append(binding)
    seen_tables = set()

    def column_and_transform(node, sources):
        transform = None
        if isinstance(node, (exp.Lower, exp.Upper)):
            transform = str.lower if isinstance(node, exp.Lower) else str.upper
            node = node.this
        if not isinstance(node, exp.Column):
            return None
        source = sources.get(node.table)
        if not isinstance(source, exp.Table):
            return None
        return f"{source.name}.{node.name}", transform

    def literal(node):
        return node.this if isinstance(node, exp.Literal) and node.is_string else None

    def constraints(node, sources):
        if node is None:
            return set()
        if isinstance(node, (exp.Where, exp.Having, exp.Paren)):
            return constraints(node.this, sources)
        if isinstance(node, exp.And):
            return constraints(node.left, sources) | constraints(node.right, sources)
        if isinstance(node, exp.Or):
            # A bound value must hold in every OR branch.
            return constraints(node.left, sources) & constraints(node.right, sources)
        operator = "=" if isinstance(node, exp.EQ) else "!=" if isinstance(node, exp.NEQ) else None
        if operator:
            for lhs, rhs in ((node.left, node.right), (node.right, node.left)):
                column = column_and_transform(lhs, sources)
                value = literal(rhs)
                if column and value is not None:
                    name, transform = column
                    return {(name, operator, frozenset([value]), "lower" if transform is str.lower else "upper" if transform is str.upper else None)}
        if isinstance(node, exp.In) and not node.args.get("query"):
            column = column_and_transform(node.this, sources)
            values = [literal(item) for item in node.expressions]
            if column and values and all(value is not None for value in values):
                name, transform = column
                return {(name, "IN", frozenset(values), "lower" if transform is str.lower else "upper" if transform is str.upper else None)}
        if isinstance(node, exp.Not) and isinstance(node.this, exp.In):
            inner = constraints(node.this, sources)
            if len(node.this.expressions) == 1:
                return {(name, "!=", values, transform) for name, _, values, transform in inner}
        return set()

    for scope in scopes:
        sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
        target_tables = {source.name for source in sources.values() if isinstance(source, exp.Table) and source.name in by_table}
        if not target_tables:
            continue
        seen_tables |= target_tables
        mandatory = constraints(scope.expression.args.get("where"), sources) | constraints(scope.expression.args.get("having"), sources)
        for table in target_tables:
            for binding in by_table[table]:
                column = ".".join(str(binding["column"]).split(".")[-2:])
                wanted = binding["value"] if isinstance(binding["value"], list) else [binding["value"]]
                accepted = False
                for name, op, values, transform in mandatory:
                    expected = frozenset(str(value).lower() if transform == "lower" else str(value).upper() if transform == "upper" else str(value) for value in wanted)
                    same_op = op == binding["operator"] or (binding["operator"] == "=" and op == "IN" and len(expected) == 1)
                    if name == column and same_op and values == expected:
                        accepted = True
                        break
                if not accepted:
                    raise SQLValidationError(f"SQL 未保留已核验绑定 {column} {binding['operator']}；禁止执行或删除用户条件。")
    if set(by_table) - seen_tables:
        raise SQLValidationError("SQL 没有查询已核验绑定对应的真实业务表。")


def parameterize_strings(sql: str) -> tuple[str, dict[str, str]]:
    """Use AST nodes to bind text values; never substitute a canonical value.

    The visible/validated SQL is preserved by the caller. Escaping percent
    tokens here is solely the psycopg placeholder protocol, including modulo
    operators; every string literal itself travels as a separate parameter.
    """
    expression = sqlglot.parse_one(sql, read="postgres")
    parameters = {}
    for literal in list(expression.find_all(exp.Literal)):
        if literal.is_string:
            name = f"qa_value_{len(parameters)}"
            parameters[name] = literal.this
            literal.replace(exp.Placeholder(this=name))
    rendered = expression.sql(dialect="postgres")
    if parameters:
        rendered = rendered.replace("%", "%%")
        for name in parameters:
            rendered = rendered.replace("%%(" + name + ")s", "%(" + name + ")s")
    return rendered, parameters
