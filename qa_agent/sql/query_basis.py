"""Bounded, display-only explanations of actual consumed monetary SQL ratios.

No question, intent, result value, model, or reference answer participates. This
is not a business-correctness certificate and never rewrites SQL or table data.
Unsupported lineage/conditions/scales yield None rather than invented wording.
"""
from __future__ import annotations

from decimal import Decimal
from hashlib import sha256

from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import traverse_scope

from qa_agent.sql.projection_semantics import projection_semantics, transparent
from qa_agent.sql.repair_guard import _qualified


class _Unproved(ValueError):
    pass


_FIELDS = {
    ('public', 'invoice', 'billing_country'): '账单国家',
    ('public', 'invoice', 'invoice_date'): '发票日期',
    ('public', 'customer', 'country'): '客户所在地国家',
    ('public', 'genre', 'name'): '流派',
    ('public', 'genre', 'genre_id'): '流派编号',
    ('public', 'artist', 'name'): '艺术家',
    ('public', 'album', 'title'): '专辑',
    ('public', 'track', 'name'): '曲目',
    ('public', 'track', 'milliseconds'): '曲目时长（毫秒）',
    ('public', 'media_type', 'name'): '媒体格式',
}
_METRICS = {
    'invoice_revenue': '发票金额字段合计',
    'detail_revenue': '销售明细金额合计（每条明细的成交单价×购买数量后加总）',
}


def describe_query_basis(sql, columns=None, *, catalog=None):
    """Return {source, text, columns, sql_sha256}, or None when unproved.

    Requires the real catalog and an already validated SQL string. Supports
    consumed aggregate CTEs/scalars, SUM(invoice.total), same-row invoice-line
    price*quantity, one conditional branch/FILTER, and output ROUND. A ratio
    multiplier of 1 or 100 is explained explicitly; arbitrary scaling, opaque
    casts, set operations, and unknown predicates are deliberately unsupported.
    """
    if catalog is None or not isinstance(sql, str) or not sql.strip():
        return None
    try:
        return _describe(sql, columns, catalog)
    except (ValueError, TypeError, KeyError, AttributeError, StopIteration, ArithmeticError, SqlglotError):
        return None


def _describe(sql, columns, catalog):
    meanings = projection_semantics(sql, columns, catalog=catalog)
    tree = _qualified(sql, catalog)
    scopes = list(traverse_scope(tree))
    root = next(s for s in scopes if s.parent is None)
    by_expression = {id(s.expression): s for s in scopes}
    if not isinstance(root.expression, exp.Select):
        return None
    # An outer filter/join predicate can alter both derived operands. Do not
    # silently assign it to one role or describe a filtered row as a total.
    if any(root.expression.args.get(k) for k in ('having', 'qualify', 'distinct', 'offset')):
        return None

    def literal(node):
        node = transparent(node)
        if isinstance(node, exp.Literal) and not node.is_string:
            return Decimal(node.this)
        return None

    def resolve(node, scope, path=(), depth=0):
        if node is None or depth > 18:
            raise _Unproved()
        node = transparent(node)
        if isinstance(node, exp.Column):
            source = scope.sources.get(node.table)
            if source is not None and not isinstance(source, exp.Table):
                if not isinstance(source.expression, exp.Select):
                    raise _Unproved()
                items = [p for p in source.expression.selects if p.alias_or_name == node.name]
                if len(items) != 1:
                    raise _Unproved()
                return resolve(items[0], source, path + (scope,), depth + 1)
        if isinstance(node, exp.Subquery):
            owner = by_expression.get(id(node.this))
            if owner is None or not isinstance(node.this, exp.Select) or len(node.this.selects) != 1:
                raise _Unproved()
            return resolve(node.this.selects[0], owner, path + (scope,), depth + 1)
        return node, scope, path

    def field(node, scope, path=(), depth=0):
        if depth > 18:
            raise _Unproved()
        node = transparent(node)
        if not isinstance(node, exp.Column):
            raise _Unproved()
        source = scope.sources.get(node.table)
        if isinstance(source, exp.Table):
            schema = source.db or 'public'
            table = catalog.get_table(source.name, schema)
            if node.name not in table.column_names:
                raise _Unproved()
            return (schema, source.name, node.name), path + ((id(scope), node.table),)
        if source is None or not isinstance(source.expression, exp.Select):
            raise _Unproved()
        items = [p for p in source.expression.selects if p.alias_or_name == node.name]
        if len(items) != 1:
            raise _Unproved()
        return field(items[0], source, path + ((id(scope), node.table),), depth + 1)

    def label(node, scope):
        identity, _ = field(node, scope)
        if identity not in _FIELDS:
            # A grouping key may travel through a fact-table FK rather than
            # the dimension itself. Use only a recorded one-column FK whose
            # referenced field already has a known display label.
            physical = catalog.get_table(identity[1], identity[0])
            candidates = set()
            for fk in physical.foreign_keys:
                reference = fk.get('references') or {}
                if fk.get('columns') == [identity[2]] and len(reference.get('columns') or []) == 1:
                    target = (reference.get('schema', 'public'), reference.get('table'), reference['columns'][0])
                    if target in _FIELDS:
                        candidates.add(_FIELDS[target])
            if len(candidates) != 1:
                raise _Unproved()
            return next(iter(candidates))
        return _FIELDS[identity]

    def dimension_join(join):
        """Prove a root label join is many-to-one using the actual catalog.

        This only preserves a returned row's operand identity. It does not
        certify the query's business population or assert that no row was
        removed by an inner join. Arbitrary joins/filters stay unsupported.
        """
        if join.args.get('using') or join.args.get('side') or join.args.get('method'):
            raise _Unproved()
        if str(join.args.get('kind') or '').upper() not in {'', 'INNER'}:
            raise _Unproved()
        target = join.this
        if not isinstance(target, exp.Table):
            raise _Unproved()
        table = catalog.get_table(target.name, target.db or 'public')
        if not table.primary_key:
            raise _Unproved()
        predicates = []
        def split(node):
            node = transparent(node)
            if isinstance(node, exp.And):
                split(node.left)
                split(node.right)
            else:
                predicates.append(node)
        split(join.args.get('on'))
        pairs, origins = {}, set()
        for predicate in predicates:
            if not isinstance(predicate, exp.EQ):
                raise _Unproved()
            a, b = predicate.left, predicate.right
            if not isinstance(a, exp.Column) or not isinstance(b, exp.Column):
                raise _Unproved()
            if b.table == target.alias_or_name:
                a, b = b, a
            if a.table != target.alias_or_name or b.table == target.alias_or_name:
                raise _Unproved()
            identity, _ = field(b, root)
            if a.name in pairs:
                raise _Unproved()
            pairs[a.name] = identity[2]
            origins.add(identity[:2])
        if set(pairs) != set(table.primary_key) or len(origins) != 1:
            raise _Unproved()
        schema, source = next(iter(origins))
        source_table = catalog.get_table(source, schema)
        for fk in source_table.foreign_keys:
            reference = fk.get('references') or {}
            mapping = dict(zip(reference.get('columns') or [], fk.get('columns') or []))
            if (reference.get('schema', 'public') == table.schema
                    and reference.get('table') == table.name
                    and len(reference.get('columns') or []) == len(fk.get('columns') or [])
                    and mapping == pairs):
                return {'kind': 'catalog_fk_to_unique_dimension',
                        'source': f'{schema}.{source}', 'target': f'{table.schema}.{table.name}',
                        'target_key': list(table.primary_key),
                        'row_set_completeness_asserted': False}
        raise _Unproved()

    def value(node):
        node = transparent(node)
        if isinstance(node, exp.Cast) and isinstance(node.this, exp.Literal):
            if node.args['to'].this.value not in {'DATE', 'TIMESTAMP', 'TIMESTAMPTZ'}:
                raise _Unproved()
            node = node.this
        if not isinstance(node, exp.Literal):
            raise _Unproved()
        return str(node.this)

    def condition(node, scope):
        node = transparent(node)
        if isinstance(node, exp.Where):
            return condition(node.this, scope)
        if isinstance(node, (exp.And, exp.Or)):
            return '(' + condition(node.left, scope) + ('且' if isinstance(node, exp.And) else '或') + condition(node.right, scope) + ')'
        if isinstance(node, exp.Not):
            return '不满足（' + condition(node.this, scope) + '）'
        if isinstance(node, exp.Is) and isinstance(node.expression, exp.Null):
            return label(node.this, scope) + ('不为空' if node.args.get('negate') else '为空')
        if isinstance(node, exp.In) and node.expressions and not node.args.get('query'):
            return label(node.this, scope) + '为' + '、'.join(value(x) for x in node.expressions)
        for cls, word in ((exp.EQ, '等于'), (exp.NEQ, '不等于'), (exp.GTE, '不早于/不小于'),
                          (exp.GT, '晚于/大于'), (exp.LT, '早于/小于'), (exp.LTE, '不晚于/不大于')):
            if isinstance(node, cls):
                name = label(node.left, scope)
                # Date bounds retain their actual inclusivity, not an inferred year.
                if name == '发票日期':
                    word = {exp.EQ: '等于', exp.NEQ: '不等于', exp.GTE: '不早于（含）',
                            exp.GT: '晚于（不含）', exp.LT: '早于（不含）', exp.LTE: '不晚于（含）'}[cls]
                return name + word + value(node.right)
        raise _Unproved()

    def scale(node, scope, depth=0):
        if depth > 18:
            raise _Unproved()
        node, scope, path = resolve(node, scope)
        if isinstance(node, exp.Nullif) and literal(node.expression) == 0:
            factor, core, owner, more = scale(node.this, scope, depth + 1)
            return factor, core, owner, path + more
        if isinstance(node, exp.Mul):
            for constant, rest in ((node.left, node.right), (node.right, node.left)):
                number = literal(constant)
                if number is not None:
                    factor, core, owner, more = scale(rest, scope, depth + 1)
                    return number * factor, core, owner, path + more
        if isinstance(node, exp.Div) and literal(node.right) not in (None, 0):
            factor, core, owner, more = scale(node.left, scope, depth + 1)
            return factor / literal(node.right), core, owner, path + more
        return Decimal(1), node, scope, path

    def metric(node, scope):
        # Follow only the exact consumed expression, e.g. SUM(x.line_amount)
        # where that projection is this row's price*quantity. Do not flatten
        # casts, aggregates, or combine fields from different consumer paths.
        node, scope, _ = resolve(node, scope)
        if isinstance(node, exp.Column) and field(node, scope)[0] == ('public', 'invoice', 'total'):
            return 'invoice_revenue'
        if isinstance(node, exp.Mul):
            left, lp = field(node.left, scope)
            right, rp = field(node.right, scope)
            if {left, right} == {('public', 'invoice_line', 'unit_price'), ('public', 'invoice_line', 'quantity')} and lp == rp:
                return 'detail_revenue'
        raise _Unproved()

    def local_scopes(scope, seen=None):
        seen = set() if seen is None else seen
        if id(scope) in seen:
            return []
        seen.add(id(scope))
        if not isinstance(scope.expression, exp.Select):
            raise _Unproved()
        query = scope.expression
        if any(query.args.get(k) for k in ('having', 'qualify', 'distinct', 'offset')) or scope.external_columns:
            raise _Unproved()
        # Only plain column-to-column join predicates are outside the displayed
        # filters. Literal/OR/outer joins require a richer explanation.
        def join_keys(n):
            n = transparent(n)
            return (join_keys(n.left) and join_keys(n.right)) if isinstance(n, exp.And) else (
                isinstance(n, exp.EQ) and isinstance(n.left, exp.Column) and isinstance(n.right, exp.Column))
        for join in query.args.get('joins') or []:
            if join.args.get('side') or join.args.get('using') or join.args.get('method'):
                raise _Unproved()
            if join.args.get('on') is not None and not join_keys(join.args['on']):
                raise _Unproved()
        result = [scope]
        for _, source in scope.selected_sources.values():
            if not isinstance(source, exp.Table):
                result.extend(local_scopes(source, seen))
        return result

    def operand(node, scope, path):
        node, scope, more = resolve(node, scope)
        extra = []
        if isinstance(node, exp.Filter):
            extra.append(condition(node.expression, scope))
            node = transparent(node.this)
        if not isinstance(node, exp.Sum) or isinstance(node.this, exp.Distinct):
            raise _Unproved()
        body = transparent(node.this)
        if isinstance(body, exp.Case):
            branches = body.args.get('ifs') or []
            default = body.args.get('default')
            if len(branches) != 1 or not (default is None or isinstance(default, exp.Null) or literal(default) == 0):
                raise _Unproved()
            extra.append(condition(branches[0].this, scope))
            body = transparent(branches[0].args['true'])
        measure = metric(body, scope)
        reached = list(dict.fromkeys([s for s in path + more if s is not root] + local_scopes(scope)))
        filters, groups, selections = list(extra), [], []
        for current in reached:
            query = current.expression
            if query.args.get('where'):
                filters.append(condition(query.args['where'], current))
            if query.args.get('group'):
                for item in query.args['group'].expressions:
                    groups.append(label(item, current))
            limit, order = query.args.get('limit'), query.args.get('order')
            if limit is not None and current is not root:
                number = literal(limit.expression)
                if not order or number is None or number != int(number) or number < 1:
                    raise _Unproved()
                # Only a proved monetary sort can be described as a sales rank.
                first = order.expressions[0]
                selected = first.this
                if isinstance(selected, exp.Column) and not selected.table:
                    aliases = [p for p in query.selects if p.alias_or_name == selected.name]
                    if len(aliases) != 1:
                        raise _Unproved()
                    selected = aliases[0]
                selected, owner, _ = resolve(selected, current)
                if not isinstance(selected, exp.Sum) or metric(selected.this, owner) != measure:
                    raise _Unproved()
                selections.append('按该金额' + ('降序' if first.args.get('desc') else '升序') + '取前' + str(int(number)) + '行')
        filters, groups, selections = [list(dict.fromkeys(items)) for items in (filters, groups, selections)]
        wording = ('在' + '，'.join(filters) + '的记录范围内，' if filters else '')
        wording += ('按' + '、'.join(groups) + '分组的' if groups else '') + _METRICS[measure]
        if selections:
            wording += '；' + '，'.join(selections)
        return {'metric': measure, 'text': wording, 'conditions': filters, 'grouping': groups,
                'selection': selections, 'aggregate_sql': node.sql(dialect='postgres')}

    results = []
    for index, projection in enumerate(root.expression.selects):
        key = columns[index] if columns is not None and index < len(columns) else projection.alias_or_name
        meaning = meanings.get(key) or {}
        if meaning.get('kind') != 'ratio':
            continue
        node, scope, outer_path = resolve(projection, root)
        rounding = None
        if isinstance(node, exp.Round):
            digits = literal(node.args.get('decimals')) if node.args.get('decimals') is not None else Decimal(0)
            if digits is None or digits != int(digits) or not 0 <= digits <= 9:
                continue
            rounding = int(digits)
            node = node.this
        try:
            factor, division, scope, path = scale(node, scope)
            if not isinstance(division, exp.Div):
                raise _Unproved()
            lf, left, lo, lp = scale(division.left, scope)
            rf, right, ro, rp = scale(division.right, scope)
            multiplier = factor * lf / rf
            if multiplier not in (1, 100) or multiplier != Decimal(meaning.get('ratio_scale', '0')):
                raise _Unproved()
            # Derived operands cannot inherit an undisplayed outer row filter
            # or join predicate. Direct aggregate operands render their own
            # physical row-set conditions through local_scopes below.
            if lo is not root or ro is not root:
                if root.expression.args.get('where') or root.expression.args.get('group'):
                    raise _Unproved()
                for join in root.expression.args.get('joins') or []:
                    if join.args.get('on') is not None:
                        dimension_join(join)
                    elif join.args.get('using') or join.args.get('side'):
                        raise _Unproved()
            numerator = operand(left, lo, outer_path + path + lp)
            denominator = operand(right, ro, outer_path + path + rp)
        except _Unproved:
            continue
        formula = ('本列数值为分子÷分母×100，作为百分数展示。' if multiplier == 100 else
                   '本列原值为分子÷分母；展示百分比时再乘100并加百分号。')
        if rounding is not None:
            formula += '该列数值最后保留' + str(rounding) + '位小数。'
        results.append({'column': key, 'projection_index': index, 'numerator': numerator,
                        'denominator': denominator, 'sql_multiplier': str(multiplier), 'round_digits': rounding,
                        'text': '计算口径（第' + str(index + 1) + '列占比）：分子为' + numerator['text'] + '；分母为' + denominator['text'] + '。' + formula})
    if not results:
        return None
    return {'source': 'program:actual_sql_projection_basis', 'sql_sha256': sha256(sql.encode('utf-8')).hexdigest(),
            'text': '\n'.join(item['text'] for item in results), 'columns': results,
            'business_correctness_asserted': False}
