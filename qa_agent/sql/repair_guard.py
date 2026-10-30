"""Preserve qualified business filters through technical SQL repair.

This guard reads SQL and the existing catalog only; it cannot choose or replace
an entity. Unknown columns/syntax remain repairable, while valid physical string
filters cannot be moved to a different column to evade another validation.
"""
from __future__ import annotations

from collections import Counter

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope, walk_in_scope
from sqlglot.schema import MappingSchema

from qa_agent.sql.validator import SQLValidationError


def _qualified(sql, catalog):
    tree = normalize_identifiers(sqlglot.parse_one(sql, read="postgres"), dialect="postgres")
    return qualify(tree, dialect="postgres", db="public",
                   schema=MappingSchema(catalog.sqlglot_schema(), dialect="postgres", normalize=False),
                   allow_partial_qualification=False, validate_qualify_columns=True)


def string_filter_contract(sql: str, catalog) -> Counter:
    """Capture physical string-filter atoms with boolean context, ignoring aliases.

    If the first SQL has unresolved syntax/columns, existing bindings and the
    catalog validator govern repair. A parseable, qualified filter is locked.
    """
    try:
        tree = _qualified(sql, catalog)
    except Exception:
        return Counter()
    contracts = Counter()
    for scope in traverse_scope(tree):
        sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}

        def visit(node, path=()):
            if node is None:
                return
            if isinstance(node, (exp.Where, exp.Having, exp.Paren)):
                visit(node.this, path)
                return
            if isinstance(node, (exp.And, exp.Or)):
                # AND additions must not invalidate existing predicates, but an
                # OR wrapper could weaken them, so retain OR ancestry.
                next_path = path + ("or",) if isinstance(node, exp.Or) else path
                visit(node.left, next_path)
                visit(node.right, next_path)
                return
            if not any(isinstance(n, exp.Literal) and n.is_string for n in walk_in_scope(node)):
                return
            copy = node.copy()
            physical = False
            for column in copy.find_all(exp.Column):
                source = sources.get(column.table)
                if not isinstance(source, exp.Table):
                    return  # no unproved derived-column lineage
                column.set("table", exp.to_identifier(source.name))
                column.set("db", exp.to_identifier(source.db or "public"))
                physical = True
            if physical:
                contracts[(path, copy.sql(dialect="postgres", normalize=True))] += 1

        visit(scope.expression.args.get("where"))
        visit(scope.expression.args.get("having"))
        for join in scope.expression.args.get("joins") or []:
            visit(join.args.get("on"))
    return contracts


def validate_repair_filters(contract: Counter, sql: str, catalog) -> None:
    if not contract:
        return
    actual = string_filter_contract(sql, catalog)
    missing = contract - actual
    if missing:
        raise SQLValidationError("技术修复改变了原 SQL 的真实筛选字段、值、运算符或布尔范围；禁止换过滤列绕过校验。")


def validate_catalog_fk_joins(sql: str, catalog, *, source_label: str = '数据库') -> None:
    """Allow lookup joins independently of NLU success; prove catalog FK edges.

    CTE/subquery joins retain the general validator's scope checks. For direct
    physical joins each newly joined table needs a mandatory catalog FK edge to
    an already selected table. CROSS/ON TRUE and wrong-key lookups are rejected.
    """
    tree = _qualified(sql, catalog)
    edges = set()
    for table in catalog.tables:
        for fk in table.foreign_keys:
            ref = fk["references"]
            pairs = frozenset(frozenset(((table.schema, table.name, a),
                                        (ref.get('schema', 'public'), ref["table"], b)))
                              for a, b in zip(fk["columns"], ref["columns"]))
            edges.add(pairs)
    for scope in traverse_scope(tree):
        sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
        joins = scope.expression.args.get("joins") or []
        from_node = scope.expression.args.get("from_")
        selected = {from_node.this.alias_or_name} if from_node is not None else set()

        def equalities(node):
            if isinstance(node, exp.Paren):
                return equalities(node.this)
            if isinstance(node, exp.And):
                return equalities(node.left) | equalities(node.right)
            if isinstance(node, exp.Or):
                return equalities(node.left) & equalities(node.right)
            if isinstance(node, exp.EQ) and isinstance(node.left, exp.Column) and isinstance(node.right, exp.Column):
                left, right = node.left, node.right
                a, b = sources.get(left.table), sources.get(right.table)
                if isinstance(a, exp.Table) and isinstance(b, exp.Table):
                    return {(frozenset(((a.db or 'public', a.name, left.name),
                                        (b.db or 'public', b.name, right.name))),
                             frozenset((left.table, right.table)))}
            return set()

        for join in joins:
            alias = join.this.alias_or_name
            target = sources.get(alias)
            if isinstance(target, exp.Table) and all(isinstance(sources.get(a), exp.Table) for a in selected):
                keys = {pair for pair, aliases in equalities(join.args.get("on"))
                        if alias in aliases and bool((aliases - {alias}) & selected)}
                if not any(edge <= keys for edge in edges):
                    raise SQLValidationError(f"{source_label}关联必须使用真实目录中的完整外键，禁止笛卡尔积、ON TRUE 或换连接键。")
            selected.add(alias)


def validate_chinook_fk_joins(sql: str, catalog) -> None:
    validate_catalog_fk_joins(sql, catalog, source_label='Chinook ')
