"""Prove a confirmed D3 invoice period survives SQL regeneration.

This bounded guard is used for patched/clarified Chinook queries with one
current period. Growth and ratio tasks have different period semantics and
are not routed here. No SQL is rewritten and no database is queried here.
"""
from __future__ import annotations

from datetime import datetime

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope, walk_in_scope
from sqlglot.schema import MappingSchema

from qa_agent.sql.validator import SQLValidationError


def validate_confirmed_invoice_period(sql: str, catalog, current: dict) -> None:
    def instant(value):
        try:
            result=datetime.fromisoformat(str(value))
        except (ValueError,TypeError):
            return None
        return result if result.tzinfo is None else None

    start,end=instant(current.get('start')),instant(current.get('end'))
    if start is None or end is None or start>=end:
        raise SQLValidationError('已确认期间不是有效的左闭右开日期范围。')
    checked=normalize_identifiers(sqlglot.parse_one(sql,read='postgres'),dialect='postgres')
    try:
        checked=qualify(checked,dialect='postgres',db='public',
                        schema=MappingSchema(catalog.sqlglot_schema(),dialect='postgres',normalize=False),
                        allow_partial_qualification=False,validate_qualify_columns=True)
        scopes=list(traverse_scope(checked))
    except Exception as exc:
        raise SQLValidationError('确认期间核验无法建立真实 invoice 字段作用域。') from exc
    if len(scopes)!=1 or not isinstance(checked,exp.Select):
        raise SQLValidationError('已确认发票期间的限定保护要求单个 SELECT 作用域；请把确认期间放入真实 invoice 的 WHERE，不能用多层来源替换或缩窄。')
    seen=False
    for scope in scopes:
        sources={alias:source for alias,(_,source) in scope.selected_sources.items()}
        invoice_aliases={alias for alias,source in sources.items() if isinstance(source,exp.Table) and
                         source.name=='invoice' and source.db in {'public',''}}
        if not invoice_aliases:
            continue
        seen=True

        def real_date(node,alias):
            return isinstance(node,exp.Column) and node.table==alias and node.name=='invoice_date'

        def literal(node):
            while isinstance(node,(exp.Paren,exp.Cast)):
                node=node.this
            return instant(node.this) if isinstance(node,exp.Literal) and node.is_string else None

        def constraints(node,alias):
            if node is None:
                return set()
            if isinstance(node,(exp.Where,exp.Paren)):
                return constraints(node.this,alias)
            if isinstance(node,exp.And):
                return constraints(node.left,alias)|constraints(node.right,alias)
            if isinstance(node,exp.Or):
                return constraints(node.left,alias)&constraints(node.right,alias)
            found=None
            if isinstance(node,(exp.GTE,exp.LT)) and real_date(node.left,alias):
                found=('>=' if isinstance(node,exp.GTE) else '<',literal(node.right))
            elif isinstance(node,(exp.LTE,exp.GT)) and real_date(node.right,alias):
                found=('>=' if isinstance(node,exp.LTE) else '<',literal(node.left))
            if found in {('>=',start),('<',end)}:
                return {found}
            if any(real_date(column,alias) for column in walk_in_scope(node) if isinstance(column,exp.Column)):
                raise SQLValidationError('SQL 日期筛选必须保留已确认期间的等价边界，禁止替换或额外缩窄期间。')
            return set()

        for alias in invoice_aliases:
            mandatory=constraints(scope.expression.args.get('where'),alias)
            if not {('>=',start),('<',end)}<=mandatory:
                raise SQLValidationError(f"SQL 未保留已确认 invoice 期间：invoice_date >= '{current['start']}' AND invoice_date < '{current['end']}'；必须是 WHERE 强制条件，不能用 SELECT 字面值或 OR 绕过。")
    if not seen:
        raise SQLValidationError('确认的发票期间必须作用于真实 invoice 扫描。')


def validate_confirmed_country_output(sql: str,catalog,target: str) -> None:
    """A confirmed country-scope switch must also govern country result columns.

    WHERE bindings are checked separately. Here only SELECT/GROUP BY/HAVING
    country sources are constrained; independent employee columns stay intact.
    Result aliases are labels, so c.country AS billing_country is still c.country.
    """
    if target not in {'invoice.billing_country','customer.country'}:
        raise SQLValidationError('确认地区的输出核验只支持账单国家或客户所在地的明确字段。')
    checked=normalize_identifiers(sqlglot.parse_one(sql,read='postgres'),dialect='postgres')
    try:
        checked=qualify(checked,dialect='postgres',db='public',
                        schema=MappingSchema(catalog.sqlglot_schema(),dialect='postgres',normalize=False),
                        allow_partial_qualification=False,validate_qualify_columns=True)
        scopes=list(traverse_scope(checked))
    except Exception as exc:
        raise SQLValidationError('确认地区输出核验无法建立真实国家字段作用域。') from exc
    if len(scopes)!=1 or not isinstance(checked,exp.Select):
        raise SQLValidationError('确认地区输出的限定核验要求单个 SELECT 作用域，不能用派生列别名替换真实地区来源。')
    sources={alias:source for alias,(_,source) in scopes[0].selected_sources.items()}
    forbidden='customer.country' if target=='invoice.billing_country' else 'invoice.billing_country'
    nodes=[*checked.expressions,checked.args.get('group'),checked.args.get('having')]
    for node in nodes:
        if node is None:
            continue
        for column in node.find_all(exp.Column):
            source=sources.get(column.table)
            if isinstance(source,exp.Table) and source.db in {'public',''}:
                actual=f'{source.name}.{column.name}'
                if actual==forbidden:
                    raise SQLValidationError(f'已确认地区归属为 {target}；SELECT/GROUP BY/HAVING 不能继续使用旧的 {forbidden}，相同数据结果不能代替真实字段口径。')
