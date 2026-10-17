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


def validate_generation_claim(question: str, sql: str, explanation: str, *, generation_context: dict | None = None) -> None:
    """A model's explicit refusal or empty placeholder is not a DB answer."""
    from qa_agent.sql.generation_scope import document_scope_disclaimer,reject_unrequested_null_projection
    if (re.search(r"(?:无法|不能|不支持)(?:执行|查询|生成(?:SQL|查询|针对)|访问)|目标表.*不在.*目录", explanation, re.IGNORECASE)
            and not document_scope_disclaimer(explanation,question,generation_context)):
        raise SQLValidationError("模型明确说明无法执行该请求，禁止把占位 SQL 当作数据库空结果。")
    expression = sqlglot.parse_one(sql, read="postgres")
    reject_unrequested_null_projection(expression,generation_context)
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
    # Genuine PostgreSQL read-only analytic functions. Keeping a finite list
    # does not authorize arbitrary anonymous functions or table functions.
    "LAG", "LEAD", "ROW_NUMBER", "RANK", "DENSE_RANK", "PERCENT_RANK",
    "CUME_DIST", "NTILE", "FIRST_VALUE", "LAST_VALUE", "NTH_VALUE",
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
    # Separate entity mentions on one scalar column denote the requested set,
    # not the impossible conjunction column=A AND column=B. Preserve the exact
    # set: neither dropping a member nor adding a third member is authorized.
    grouped = {}
    other = []
    for binding in bindings:
        if binding.get("operator") == "=" and not isinstance(binding.get("value"), list):
            key = (binding.get("column"), binding.get("binding_scope", "global"))
            grouped.setdefault(key, []).append(binding)
        else:
            other.append(binding)
    bindings = list(other)
    for group in grouped.values():
        values = list(dict.fromkeys(str(item["value"]) for item in group))
        bindings.append({**group[0], "operator": "IN", "value": values} if len(values) > 1 else group[0])
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
        if len(parts) not in {2, 3} or binding.get("operator") not in {"=", "!=", "IN", ">", ">=", "<", "<="}:
            raise SQLValidationError("值绑定包含不受支持的字段或操作符。")
        table = catalog.get_table(parts[-2], parts[-3] if len(parts) == 3 else "public")
        if parts[-1] not in table.column_names:
            raise SQLValidationError("值绑定引用了目录之外的字段。")
        by_table.setdefault(parts[-2], []).append(binding)
    seen_tables = set()
    set_coverage: dict[tuple[str, tuple[str, ...]], set[str]] = {}

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
            left, right = constraints(node.left, sources), constraints(node.right, sources)
            # (same_column=A OR same_column=B) is an exact set restriction.
            # Any other atom/boolean escape keeps the intersection proof.
            if len(left) == len(right) == 1:
                a, b = next(iter(left)), next(iter(right))
                if a[0] == b[0] and a[3] == b[3] and a[1] in {"=", "IN"} and b[1] in {"=", "IN"}:
                    return {(a[0], "IN", a[2] | b[2], a[3])}
            return left & right
        operator = "=" if isinstance(node, exp.EQ) else "!=" if isinstance(node, exp.NEQ) else None
        numeric_operator = {exp.EQ:'=',exp.NEQ:'!=',exp.GT:'>',exp.GTE:'>=',exp.LT:'<',exp.LTE:'<='}.get(type(node))
        if numeric_operator:
            from decimal import Decimal, InvalidOperation
            for lhs,rhs,reverse in ((node.left,node.right,False),(node.right,node.left,True)):
                column=column_and_transform(lhs,sources)
                if not column or column[1] is not None or not isinstance(rhs,exp.Literal) or rhs.is_string:
                    continue
                try:
                    value=Decimal(rhs.this)
                    if not value.is_finite():continue
                except InvalidOperation:
                    continue
                operation=({'<':'>','<=':'>=','>':'<','>=':'<='}.get(numeric_operator,numeric_operator) if reverse else numeric_operator)
                return {(column[0],operation,frozenset([str(value.normalize())]),'numeric')}
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
                if binding["operator"] == "IN" and len(wanted) > 1:
                    key = (column, tuple(sorted(str(value) for value in wanted)))
                    coverage = set_coverage.setdefault(key, set())
                    restrictions = []
                    for name, op, values, transform in mandatory:
                        if name != column or op not in {"=", "IN"}:
                            continue
                        convert = (str.lower if transform == "lower" else str.upper if transform == "upper" else lambda value: value)
                        expected_map = {convert(str(value)): str(value) for value in wanted}
                        if not values or not values <= set(expected_map):
                            continue
                        restrictions.append({expected_map[value] for value in values})
                    allowed = set.intersection(*restrictions) if restrictions else set()
                    if allowed and allowed!=set(str(value)for value in wanted)and _customer_identity_lookup_shape(scope,binding):
                        raise SQLValidationError("主键实名回查层额外缩小了完整国家集合，不能借此前CTE的完整IN掩盖。")
                    if not allowed:
                        if _prove_identity_lookup_set(scope,catalog,binding):
                            coverage.update(str(value) for value in wanted)
                            continue
                        raise SQLValidationError(f"SQL 未保留已核验多值集合 {column} IN；不能遗漏全部值、添加集合外值或用互斥 AND 制造空结果。")
                    coverage.update(allowed)
                    continue
                accepted = False
                for name, op, values, transform in mandatory:
                    if transform == 'numeric':
                        from decimal import Decimal, InvalidOperation
                        try:
                            if any(isinstance(value,bool) for value in wanted):continue
                            parsed=[Decimal(str(value)) for value in wanted]
                            if any(not value.is_finite() for value in parsed):continue
                            expected=frozenset(str(value.normalize()) for value in parsed)
                        except InvalidOperation:
                            continue
                    else:
                        expected = frozenset(str(value).lower() if transform == "lower" else str(value).upper() if transform == "upper" else str(value) for value in wanted)
                    same_op = op == binding["operator"] or (binding["operator"] == "=" and op == "IN" and len(expected) == 1)
                    if name == column and same_op and values == expected:
                        accepted = True
                        break
                if not accepted:
                    raise SQLValidationError(f"SQL 未保留已核验绑定 {column} {binding['operator']}；禁止执行或删除用户条件。")
    if set(by_table) - seen_tables:
        raise SQLValidationError("SQL 没有查询已核验绑定对应的真实业务表。")
    for (_, wanted), found in set_coverage.items():
        if set(wanted) != found:
            raise SQLValidationError("SQL 未覆盖已核验多值集合的全部成员；分支或子查询可以拆分，但不能漏掉用户指定对象。")


def _customer_identity_lookup_shape(scope,binding):
    if binding.get("column")not in{"customer.country","public.customer.country"}:return False
    sources={alias:source for alias,(_,source)in scope.selected_sources.items()}
    lookups=[alias for alias,source in sources.items()if isinstance(source,exp.Table)and source.name=="customer"and(source.db or"public")=="public"]
    derived={alias for alias,source in sources.items()if not isinstance(source,exp.Table)}
    if len(sources)not in{2,3}or len(lookups)!=1 or len(derived)!=1:return False
    extra=[source for alias,source in sources.items()if alias not in lookups and alias not in derived]
    if extra and(any(not isinstance(table,exp.Table)or table.name!="invoice"or(table.db or"public")!="public"for table in extra)or not scope.expression.args.get("group")):return False
    for join in scope.expression.args.get("joins")or[]:
        on=join.args.get("on")
        if isinstance(on,exp.EQ)and isinstance(on.left,exp.Column)and isinstance(on.right,exp.Column):
            if any(left.table==lookups[0]and left.name=="customer_id"and right.table in derived for left,right in((on.left,on.right),(on.right,on.left))):return True
    return False


def _prove_identity_lookup_set(scope,catalog,binding):
    """Only a consumed, unique customer-key driver licenses its PK lookup.

    This exception proves identity/filter propagation, not rankings or results.
    It never searches unrelated CTEs and never rewrites or executes SQL.
    A grouped invoice measurement may perform the same primary-key identity
    lookup before ranking: both joins must preserve the qualified customer key,
    and grouping must retain that key without invoice-level fanout.
    """
    if _prove_grouped_invoice_key_customer_lookup(scope,catalog,binding):return True
    if binding.get("column")not in{"customer.country","public.customer.country"}or binding.get("operator")!="IN":return False
    wanted=binding.get("value")
    if not isinstance(wanted,list)or len(wanted)<2 or any(not isinstance(v,str)for v in wanted):return False
    physical={alias:source for alias,(_,source)in scope.selected_sources.items()if isinstance(source,exp.Table)}
    derived={alias:source for alias,(_,source)in scope.selected_sources.items()if not isinstance(source,exp.Table)}
    if len(physical)not in{1,2}or len(derived)!=1:return False
    lookups=[(alias,table)for alias,table in physical.items()if table.name=="customer"and(table.db or"public")=="public"]
    if len(lookups)!=1:return False
    lookup_alias,lookup=lookups[0];driver_alias,driver=next(iter(derived.items()))
    extras={alias:table for alias,table in physical.items()if alias!=lookup_alias}
    if any(table.name!="invoice"or(table.db or"public")!="public"for table in extras.values()):return False
    if lookup.name!="customer"or(lookup.db or"public")!="public":return False
    if tuple(catalog.get_table("customer").primary_key)!=("customer_id",):return False
    invoice=catalog.get_table("invoice")
    if (next(c for c in invoice.columns if c.name=="customer_id").nullable or
            not any(fk.get("columns")==["customer_id"]and(fk.get("references")or{}).get("table")=="customer"and(fk.get("references")or{}).get("columns")==["customer_id"]for fk in invoice.foreign_keys)):
        return False
    def bare(node):
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        return node
    def follow(node,owner):
        path=[];seen=set()
        for _ in range(20):
            node=bare(node)
            if not isinstance(node,exp.Column):return node,owner,path
            source=owner.sources.get(node.table)
            if isinstance(source,exp.Table):return node,owner,path
            marker=(id(source),node.name)
            if source is None or marker in seen or not isinstance(source.expression,exp.Select):return None,None,[]
            seen.add(marker);path.append(source)
            node=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
            if node is None:return None,None,[]
            owner=source
        return None,None,[]
    def origin(node,owner):
        node,owner,path=follow(node,owner)
        if not isinstance(node,exp.Column):return None
        source=owner.sources.get(node.table)
        if not isinstance(source,exp.Table):return None
        return(source.name,node.name,owner,node.table,path)
    joins=scope.expression.args.get("joins")or[]
    if len(joins)!=len(physical)or any(join.args.get("side")or join.args.get("using")for join in joins):return False
    key=None
    invoice_keys=[]
    for join in joins:
        on=bare(join.args.get("on"))
        if not isinstance(on,exp.EQ)or not isinstance(on.left,exp.Column)or not isinstance(on.right,exp.Column):return False
        role=None
        for left,right in((on.left,on.right),(on.right,on.left)):
            if left.table==lookup_alias and left.name=="customer_id"and right.table==driver_alias:
                key=right;role="identity"
            if left.table in extras and left.name=="customer_id"and right.table in{driver_alias,lookup_alias}and right.name=="customer_id":
                invoice_keys.append(right);role="invoice"
        if role is None:return False
    if len(invoice_keys)!=len(extras):return False
    if key is None:return False
    actual=origin(key,scope)
    if not actual or actual[:2]!=("customer","customer_id"):return False
    _,_,base,base_alias,path=actual
    if base is scope:return False
    def same_customer_field(node,owner,field=None):
        item=origin(node,owner)
        return bool(item and item[0]=="customer"and((item[2]is base and item[3]==base_alias)or(item[2]is scope and item[3]==lookup_alias))and(field is None or item[1]==field))
    if any(not same_customer_field(key,scope,"customer_id")for key in invoice_keys):return False
    def rank_filter(owner):
        where=owner.expression.args.get("where")
        if where is None:return True
        atom=bare(where.this)
        if not isinstance(atom,exp.EQ):return False
        column=atom.left;number=atom.right
        if not isinstance(number,exp.Literal)or number.is_string or number.this!="1":return False
        window,window_owner,_=follow(column,owner)
        if not isinstance(window,exp.Window)or not isinstance(window.this,exp.RowNumber):return False
        partition=window.args.get("partition_by")or[]
        return len(partition)==1 and same_customer_field(partition[0],window_owner,"country")
    for owner in [scope]+path:
        query=owner.expression
        if not isinstance(query,exp.Select)or any(query.args.get(k)for k in("having","qualify","distinct","offset")):return False
        limit=query.args.get("limit")
        if limit and(owner is not scope or not isinstance(limit.expression,exp.Literal)or limit.expression.is_string or not limit.expression.this.isdigit()or int(limit.expression.this)<1):return False
        if owner is base:
            if len(owner.selected_sources)!=1 or query.args.get("group")or query.args.get("joins"):return False
            where=query.args.get("where");atom=bare(where.this)if where is not None else None
            if (not isinstance(atom,exp.In)or atom.args.get("query")or not same_customer_field(atom.this,owner,"country")
                    or not atom.expressions or any(not isinstance(v,exp.Literal)or not v.is_string for v in atom.expressions)
                    or {v.this for v in atom.expressions}!=set(wanted)):return False
            continue
        if not rank_filter(owner):return False
        if owner is scope:
            group=query.args.get("group")
            if extras:
                if not group or not any(same_customer_field(item,owner,"customer_id")for item in group.expressions)or not all(same_customer_field(item,owner)for item in group.expressions):return False
            elif group:return False
            continue
        child=[source for _,source in owner.selected_sources.values()if not isinstance(source,exp.Table)]
        tables={alias:source for alias,(_,source)in owner.selected_sources.items()if isinstance(source,exp.Table)}
        if len(child)!=1:return False
        group=query.args.get("group")
        if group:
            if not any(same_customer_field(item,owner,"customer_id")for item in group.expressions)or not all(same_customer_field(item,owner)for item in group.expressions):return False
        elif tables:return False  # Ungrouped invoice-to-customer joins fan out.
        for join in query.args.get("joins")or[]:
            atom=bare(join.args.get("on"))
            if join.args.get("side")or join.args.get("using")or not isinstance(atom,exp.EQ):return False
            left=origin(atom.left,owner);right=origin(atom.right,owner)
            if not left or not right:return False
            fields=frozenset((left[:2],right[:2]))
            if fields!=frozenset({("invoice","customer_id"),("customer","customer_id")}):return False
        if tables and(any(table.name!="invoice"or(table.db or"public")!="public"for table in tables.values())or len(tables)!=1 or len(query.args.get("joins")or[])!=1):return False
    return True


def _prove_grouped_invoice_key_customer_lookup(scope,catalog,binding):
    """Prove customer-set propagation through a grouped invoice FK identity.

    Alias names are scoped, never globally matched. A real invoice.customer_id
    non-NULL FK and the actual INNER customer PK join establish the same key;
    the final customer lookup cannot introduce a customer outside that set.
    Ranking/measure/period proofs remain independent mandatory guards.
    """
    if binding.get('column')not in{'customer.country','public.customer.country'}or binding.get('operator')!='IN':return False
    values=binding.get('value')
    if not isinstance(values,list)or len(values)<2 or any(not isinstance(v,str)for v in values):return False
    def bare(node):
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        return node
    def sources(owner):return {a:s for a,(_,s)in owner.selected_sources.items()}
    def is_table(value,name):return isinstance(value,exp.Table)and(value.db or'public')=='public'and value.name==name
    outer=sources(scope);physical={a:s for a,s in outer.items()if isinstance(s,exp.Table)}
    derived={a:s for a,s in outer.items()if not isinstance(s,exp.Table)}
    if len(physical)!=1 or len(derived)!=1 or not all(is_table(s,'customer')for s in physical.values()):return False
    lookup_alias=next(iter(physical));driver_alias,driver=next(iter(derived.items()))
    query=scope.expression
    if not isinstance(query,exp.Select)or any(query.args.get(k)for k in('group','having','qualify','distinct','offset')):return False
    limit=query.args.get('limit')
    if limit is not None and(not isinstance(limit.expression,exp.Literal)or limit.expression.is_string or not limit.expression.this.isdigit()or int(limit.expression.this)<1):return False
    joins=query.args.get('joins')or[]
    if len(joins)!=1 or joins[0].args.get('side')or joins[0].args.get('using')or str(joins[0].args.get('kind')or'').upper()not in{'','INNER'}:return False
    on=bare(joins[0].args.get('on'))
    if not isinstance(on,exp.EQ):return False
    key=None
    for left,right in((on.left,on.right),(on.right,on.left)):
        if isinstance(left,exp.Column)and left.table==lookup_alias and left.name=='customer_id'and isinstance(right,exp.Column)and right.table==driver_alias:
            key=right
    if key is None:return False
    selected=next((v for v in driver.expression.selects if v.alias_or_name==key.name),None)
    selected=bare(selected)
    inputs=sources(driver);invoices=[a for a,s in inputs.items()if is_table(s,'invoice')];customers=[a for a,s in inputs.items()if is_table(s,'customer')]
    if len(inputs)!=2 or len(invoices)!=1 or len(customers)!=1:return False
    invoice_alias,customer_alias=invoices[0],customers[0]
    if not isinstance(selected,exp.Column)or selected.table not in{invoice_alias,customer_alias}or selected.name!='customer_id':return False
    try:
        inv=catalog.get_table('invoice');customer=catalog.get_table('customer')
        if customer.primary_key!=('customer_id',)or next(c for c in inv.columns if c.name=='customer_id').nullable:return False
        if not any(f.get('columns')==['customer_id']and(f.get('references')or{}).get('table')=='customer'and(f.get('references')or{}).get('columns')==['customer_id']for f in inv.foreign_keys):return False
    except Exception:return False
    inner=driver.expression
    if not isinstance(inner,exp.Select)or any(inner.args.get(k)for k in('having','qualify','distinct','offset','limit')):return False
    inner_joins=inner.args.get('joins')or[]
    if len(inner_joins)!=1 or inner_joins[0].args.get('side')or inner_joins[0].args.get('using')or str(inner_joins[0].args.get('kind')or'').upper()not in{'','INNER'}:return False
    relation=bare(inner_joins[0].args.get('on'))
    if not isinstance(relation,exp.EQ)or any(not isinstance(x,exp.Column)for x in(relation.left,relation.right)):return False
    if {(relation.left.table,relation.left.name),(relation.right.table,relation.right.name)}!={(invoice_alias,'customer_id'),(customer_alias,'customer_id')}:return False
    group=inner.args.get('group')
    if group is None or any(v not in(None,False,[])for k,v in group.args.items()if k!='expressions'):return False
    fields=[]
    for node in group.expressions:
        node=bare(node)
        if not isinstance(node,exp.Column):return False
        fields.append((node.table,node.name))
    if not any(v in{(invoice_alias,'customer_id'),(customer_alias,'customer_id')}for v in fields):return False
    if any(alias!=customer_alias and(alias,name)!=(invoice_alias,'customer_id')for alias,name in fields):return False
    where=inner.args.get('where');predicate=bare(where.this)if where is not None else None
    if not isinstance(predicate,exp.In)or predicate.args.get('query'):return False
    country=bare(predicate.this)
    if not isinstance(country,exp.Column)or(country.table,country.name)!=(customer_alias,'country'):return False
    if not predicate.expressions or any(not isinstance(v,exp.Literal)or not v.is_string for v in predicate.expressions):return False
    if {v.this for v in predicate.expressions}!=set(values):return False
    # This narrow arm consumes its actual one-per-country rank column at the
    # final lookup. An unrelated ROW_NUMBER in an unused CTE is never visited.
    final_where=query.args.get('where');rank_filter=bare(final_where.this)if final_where is not None else None
    if not isinstance(rank_filter,(exp.EQ,exp.LTE))or not isinstance(rank_filter.right,exp.Literal)or rank_filter.right.is_string or rank_filter.right.this!='1':return False
    rank=bare(rank_filter.left)
    if not isinstance(rank,exp.Column)or rank.table!=driver_alias:return False
    window=bare(next((v for v in inner.selects if v.alias_or_name==rank.name),None))
    if not isinstance(window,exp.Window)or not isinstance(window.this,exp.RowNumber):return False
    partition=window.args.get('partition_by')or[]
    if len(partition)!=1:return False
    country=bare(partition[0])
    return isinstance(country,exp.Column)and(country.table,country.name)==(customer_alias,'country')


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
