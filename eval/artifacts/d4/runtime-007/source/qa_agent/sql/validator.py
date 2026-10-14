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


def _validate_invoice_ratio_binding(sql: str, catalog: Catalog, bindings: list[dict], context: dict) -> bool:
    """Prove a narrow same-period invoice share without weakening normal WHERE guards.

    The country is a numerator condition; the denominator is explicitly all
    invoices in the same period. Only a single invoice scan, CASE SUM numerator
    and unfiltered SUM(total) denominator are admitted. Every other form keeps
    the ordinary mandatory-filter validator.
    """
    if context.get('task_type')!='ratio' or len(bindings)!=1:
        return False
    binding=bindings[0]
    if binding.get('column')!='invoice.billing_country' or binding.get('operator')!='=':
        return False
    numerator=str(context.get('numerator') or '')
    denominator=str(context.get('denominator') or '')
    question=str(context.get('question') or '')
    value=str(binding.get('value') or '')
    surfaces=[value,*context.get('verified_original_surfaces',[])]
    if (not numerator or not denominator or not any(word in denominator for word in ('所有','全部','all')) or
        not any(word in question for word in ('所有','全部','all')) or
        not any(surface and surface.casefold() in numerator.casefold() for surface in surfaces) or
        any(surface and surface.casefold() in denominator.casefold() for surface in surfaces) or
        '发票' not in numerator or '发票' not in denominator):
        return False
    current=((context.get('time_scope') or {}).get('current') or {})
    start,end=current.get('start'),current.get('end')
    if not start or not end or context.get('region_scope')!='invoice.billing_country':
        return False
    denominator_start=re.search(r'占|分母|比例|比重',question)
    denominator_question=question[denominator_start.end():] if denominator_start else ''
    same_period=any(word in denominator_question for word in ('同年','同期','同一期间','相同期间','相同时期'))
    try:
        whole_year=(str(start).endswith('-01-01') and str(end)==f'{int(str(start)[:4])+1:04d}-01-01')
    except ValueError:whole_year=False
    explicit_same_year=whole_year and str(start)[:4]+'年' in denominator_question
    if not same_period and not explicit_same_year:
        # A numerator year cannot by itself establish the denominator period.
        return False
    expression=normalize_identifiers(sqlglot.parse_one(sql,read='postgres'),dialect='postgres')
    try:
        checked=qualify(expression,dialect='postgres',db='public',
                        schema=MappingSchema(catalog.sqlglot_schema(),dialect='postgres',normalize=False),
                        allow_partial_qualification=False,validate_qualify_columns=True)
    except (OptimizeError,ValueError,KeyError,UnsupportedError) as exc:
        raise SQLValidationError('比例分子绑定无法建立真实字段作用域。') from exc
    scopes=list(traverse_scope(checked))
    if (len(scopes)!=1 or not isinstance(checked,exp.Select) or len(checked.expressions)!=1 or
        checked.args.get('joins') or checked.args.get('group') or checked.args.get('having') or checked.args.get('distinct')):
        raise SQLValidationError('分子专属绑定仅支持已核验的单发票表同期间条件聚合比例。')
    scope=scopes[0]
    sources={alias:source for alias,(_,source) in scope.selected_sources.items()}
    if len(sources)!=1 or not all(isinstance(source,exp.Table) and source.name=='invoice' for source in sources.values()):
        raise SQLValidationError('分子专属绑定必须使用真实 invoice 单次扫描，禁止替换来源。')

    def real_column(node,name):
        return isinstance(node,exp.Column) and node.name==name and isinstance(sources.get(node.table),exp.Table) and sources[node.table].name=='invoice'

    def zero_or_null(node):
        return node is None or isinstance(node,exp.Null) or (isinstance(node,exp.Literal) and not node.is_string and str(node.this) in {'0','0.0'})

    def numeric_zero(node):
        return isinstance(node,exp.Literal) and not node.is_string and str(node.this) in {'0','0.0'}

    projected=checked.expressions[0]
    ratio=projected.this if isinstance(projected,exp.Alias) else projected
    if not isinstance(ratio,exp.Div) or not isinstance(ratio.left,exp.Sum) or not isinstance(ratio.right,exp.Nullif):
        raise SQLValidationError('分子专属绑定要求条件 SUM / NULLIF(同期间 SUM(total),0)，禁止任意 SELECT 表达式绕过。')
    case=ratio.left.this
    denominator_sum=ratio.right.this
    if (not isinstance(case,exp.Case) or len(case.args.get('ifs') or [])!=1 or not zero_or_null(case.args.get('default')) or
        not isinstance(denominator_sum,exp.Sum) or not real_column(denominator_sum.this,'total') or
        not numeric_zero(ratio.right.expression)):
        raise SQLValidationError('比例分子/分母金额字段或 ELSE 分支不符合已确认发票总额口径。')
    branch=case.args['ifs'][0]
    if not real_column(branch.args.get('true'),'total'):
        raise SQLValidationError('比例分子必须累计真实 invoice.total，不能用常量或不同粒度字段代替。')
    where=checked.args.get('where')
    guard=branch.this
    while isinstance(guard,exp.Paren):guard=guard.this
    exact_country_guard=(isinstance(guard,exp.EQ) and any(
        real_column(column,'billing_country') and isinstance(literal,exp.Literal) and literal.is_string and str(literal.this)==value
        for column,literal in ((guard.left,guard.right),(guard.right,guard.left))))
    if not exact_country_guard:
        raise SQLValidationError('比例分子仅允许已确认的账单国家等值，禁止附加未确认条件或 OR 绕过。')

    def literal_value(node):
        if isinstance(node,exp.Cast):node=node.this
        return str(node.this) if isinstance(node,exp.Literal) else None

    def period_constraints(node):
        if node is None:return set()
        if isinstance(node,(exp.Where,exp.Paren)):return period_constraints(node.this)
        if isinstance(node,exp.And):return period_constraints(node.left)|period_constraints(node.right)
        found=None
        if isinstance(node,(exp.GTE,exp.LT)) and real_column(node.left,'invoice_date'):
            found=('>=' if isinstance(node,exp.GTE) else '<',literal_value(node.right))
        elif isinstance(node,(exp.LTE,exp.GT)) and real_column(node.right,'invoice_date'):
            found=('>=' if isinstance(node,exp.LTE) else '<',literal_value(node.left))
        if found not in {('>=',str(start)),('<',str(end))}:
            raise SQLValidationError('全部发票分母仅允许已确认期间的两项等价边界，禁止额外期间、条件或 OR。')
        return {found}
    if not {('>=',str(start)),('<',str(end))}.issubset(period_constraints(where)):
        raise SQLValidationError('比例的分子与全部发票分母必须共享已确认的相同左闭右开期间。')
    if where is None or any(not real_column(column,'invoice_date') for column in where.find_all(exp.Column)):
        raise SQLValidationError('全部发票分母不得被国家或其它未经确认的筛选收窄。')
    # Reuse the existing mandatory-filter proof on the numerator branch. This
    # rejects a SELECT literal, wrong value/operator and any OR escape.
    numerator_check=checked.copy()
    numerator_check.set('expressions',[exp.Sum(this=branch.args['true'].copy())])
    numerator_check.set('where',exp.Where(this=exp.and_(where.this.copy(),branch.this.copy())))
    validate_value_bindings(numerator_check.sql(dialect='postgres'),catalog,bindings)
    return True


def validate_value_bindings(sql: str, catalog: Catalog, bindings: list[dict], *, ratio_context: dict | None = None) -> None:
    """Prove each verified value is a mandatory filter on its physical table.

    An equality in SELECT, a comment, an OR bypass or a different subquery is
    insufficient. Repeated table scans must each preserve the corresponding
    bindings. Conservative rejection of complex derived-table propagation is
    intentional in D2's single-table stage; no SQL text is rewritten here.
    """
    if not bindings:
        return
    if ratio_context is not None:
        from qa_agent.sql.ratio_guard import validate_invoice_share
        if validate_invoice_share(sql, catalog, bindings, ratio_context):
            return
    if ratio_context is not None and _validate_invoice_ratio_binding(sql,catalog,bindings,ratio_context):
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
