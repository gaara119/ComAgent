"""Experimental physical operand proof. No gold, dataset IDs, execution or mutation.

Bounded support: SUM(invoice.total) or SUM(unit_price*quantity), physical
to-one FK joins, one-branch CASE, direct scalar subqueries/aggregate CTEs.
Unproved SQL is rejected for finite equivalent repair, not labelled false SQL.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _midnight_date, _active_scopes
from qa_agent.sql.validator import SQLValidationError, validate_value_bindings


def validate_typed_ratio_scope(sql, catalog, intent, bindings=None, *, binding_validator=None):
    get = lambda name, default=None: intent.get(name, default) if isinstance(intent, dict) else getattr(intent, name, default)
    if get('task_type') != 'ratio':
        return {'verified': True, 'mode': 'not_a_typed_ratio'}
    query = get('query_scope', {}) or {}
    contracts = {role: query.get(role) or {} for role in ('numerator', 'denominator')}
    if any(not isinstance(value, dict) for value in contracts.values()):
        raise SQLValidationError('比例作用域：操作数合同必须为结构对象。')
    expected = {'numerator': contracts['numerator'].get('metric') or get('metric'),
                'denominator': contracts['denominator'].get('metric')}
    # A typed numerator and denominator metric is necessary. No lexical guesses.
    if any(value not in {'detail_revenue', 'invoice_revenue'} for value in expected.values()):
        return {'verified': True, 'mode': 'no_complete_typed_ratio_contract'}
    if ('detail_revenue' not in expected.values() and
            (get('rank_object') is not None or get('top_n') is not None or
             get('metric') not in {None,'invoice_revenue'} or
             any(contracts[role].get('metric')!='invoice_revenue' for role in ('numerator','denominator')))):
        return {'verified': True, 'mode': 'invoice_only_ratio_delegated'}
    bindings = [{**item, 'binding_scope': item.get('binding_scope') or 'global'} for item in (bindings if bindings is not None else get('filters', []) or [])]
    for role, contract in contracts.items():
        bindings.extend({**item, 'binding_scope': role} for item in contract.get('filters', []) or [])
    if any(item.get('binding_scope') not in {'global', 'numerator', 'denominator'} for item in bindings):
        raise SQLValidationError('比例作用域：条件缺少合法操作数作用域。')
    tree = _qualified(sql, catalog)
    scopes = list(traverse_scope(tree))
    by_expression = {id(scope.expression): scope for scope in scopes}
    root = next(scope for scope in scopes if scope.parent is None)
    check_binding = binding_validator or validate_value_bindings

    def fail(message):
        raise SQLValidationError('比例作用域：' + message)

    root_limit = root.expression.args.get('limit')
    if root_limit is not None and (not isinstance(root_limit.expression, exp.Literal) or root_limit.expression.is_string or not str(root_limit.expression.this).isdigit() or int(root_limit.expression.this) < 1):
        fail('最终输出行数限制不是合法正数。')

    # A candidate is only a temporary permission to follow the consumed
    # lineage. It is NOT approved until measure/dimension/order are proved.
    # Unused good CTEs cannot create this candidate.
    wanted_n = get('top_n')
    ranking_scope = None
    if isinstance(wanted_n, int) and not isinstance(wanted_n, bool):
        limited = []
        for candidate in _active_scopes(scopes):
            limit = candidate.expression.args.get('limit')
            if limit is not None and isinstance(limit.expression, exp.Literal) and not limit.expression.is_string and str(limit.expression.this) == str(wanted_n):
                limited.append(candidate)
        if len(limited) == 1:
            ranking_scope = limited[0]

    def ranking_row_driver(scope, seen=None):
        seen = set() if seen is None else set(seen)
        if id(scope) in seen or not isinstance(scope.expression, exp.Select):
            return False
        seen.add(id(scope))
        if scope is ranking_scope:
            return True
        query = scope.expression
        if any(query.args.get(key) for key in ('where','having','group','distinct','offset','qualify','limit')) or query.args.get('joins'):
            return False
        sources = [source for _,source in scope.selected_sources.values()]
        return len(sources) == 1 and not isinstance(sources[0],exp.Table) and ranking_row_driver(sources[0],seen)

    def strip(node):
        while isinstance(node, (exp.Alias, exp.Paren)):
            node = node.this
        return node

    def scalar(scope, seen=None):
        seen = set() if seen is None else set(seen)
        if id(scope) in seen:
            return False
        seen.add(id(scope))
        select = scope.expression
        if not isinstance(select, exp.Select) or select.args.get('group') or select.args.get('having') or select.args.get('offset') or select.args.get('limit') or scope.external_columns:
            return False
        if all(isinstance(source, exp.Table) for _, source in scope.selected_sources.values()):
            return bool(scope.selected_sources) and all(any(isinstance(node, exp.AggFunc) and node.find_ancestor(exp.Select) is select for node in item.walk()) for item in select.selects)
        if select.args.get('where') or any(join.args.get('on') is not None or join.args.get('using') or join.args.get('side') for join in select.args.get('joins') or []):
            return False
        return bool(scope.selected_sources) and all(not isinstance(source, exp.Table) and scalar(source, seen) for _, source in scope.selected_sources.values())

    def resolve(node, scope, depth=0):
        if depth > 20:
            fail('派生操作数超过有界谱系深度。')
        node = strip(node)
        if isinstance(node, exp.Column):
            source = scope.sources.get(node.table)
            if source is not None and not isinstance(source, exp.Table):
                select = scope.expression
                if not isinstance(select, exp.Select) or select.args.get('group') or select.args.get('distinct') or select.args.get('offset') or select.args.get('qualify'):
                    fail('透传层存在未证明的集合操作、去重、分组或偏移。')
                limit = select.args.get('limit')
                if limit is not None:
                    number = limit.expression
                    allowed_rank_layer = scope is ranking_scope and str(number.this) == str(wanted_n)
                    if (scope is not root and not allowed_rank_layer) or not isinstance(number, exp.Literal) or number.is_string or not str(number.this).isdigit() or int(number.this) < 1:
                        fail('透传层行数限制可能删除真实结果，仅根层正数TopN交由排名守卫。')
                # Extra joins cannot change a consumed operand's multiplicity.
                for alias, (_, sibling) in scope.selected_sources.items():
                    if alias != node.table and (isinstance(sibling, exp.Table) or not scalar(sibling)):
                        grouped_driver = (scalar(source) and not isinstance(sibling, exp.Table) and isinstance(sibling.expression, exp.Select) and (sibling.expression.args.get('group') is not None or ranking_row_driver(sibling)) and len(scope.selected_sources) == 2)
                        if not grouped_driver:
                            fail('派生操作数与非单行来源关联，行数或金额可能改变。')
                if scope.expression.args.get('where') or scope.expression.args.get('having'):
                    fail('派生操作数外层存在未证明的额外行筛选。')
                if any(join.args.get('on') is not None or join.args.get('using') or join.args.get('side') for join in scope.expression.args.get('joins') or []):
                    fail('派生操作数仅支持无条件单行 CROSS JOIN。')
                projection = next((item for item in source.expression.selects if item.alias_or_name == node.name), None)
                if projection is None:
                    fail('派生列没有实际投影。')
                if not isinstance(source.expression, exp.Select):
                    fail('被消费来源含集合运算，无法证明唯一实际操作数。')
                return resolve(projection, source, depth + 1)
        if isinstance(node, exp.Subquery):
            owner = by_expression.get(id(node.this))
            if owner is None or len(node.this.selects) != 1 or not scalar(owner):
                fail('操作数子查询不是唯一单行的实际聚合。')
            return resolve(node.this.selects[0], owner, depth + 1)
        return node, scope

    def field(node, scope):
        node = strip(node)
        if not isinstance(node, exp.Column):
            return None
        source = scope.sources.get(node.table)
        if not isinstance(source, exp.Table) or (source.db or 'public') != 'public':
            return None
        return source.name + '.' + node.name

    def atoms(node):
        if node is None:
            return []
        node = strip(node)
        if isinstance(node, exp.Where):
            return atoms(node.this)
        if isinstance(node, exp.And):
            return atoms(node.left) + atoms(node.right)
        return [node]

    def physical_grain(scope, metric, role):
        sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
        if not sources or any(not isinstance(source, exp.Table) for source in sources.values()):
            fail('金额聚合必须落到实际物理行集，暂不证明派生明细行集。')
        base = 'invoice' if metric == 'invoice_revenue' else 'invoice_line'
        seen = {alias for alias, source in sources.items() if source.name == base}
        if len(seen) != 1:
            fail('金额行粒度缺少唯一真实主来源。')
        joins = scope.expression.args.get('joins') or []
        for join in joins:
            if (join.args.get('side') or join.args.get('using') or join.args.get('method') or
                    str(join.args.get('kind') or '').upper() not in {'','INNER'}):
                fail('金额聚合暂不证明外连接或 USING 的行粒度。')
            conditions = atoms(join.args.get('on'))
            if not conditions or any(not isinstance(atom, exp.EQ) or not isinstance(atom.left, exp.Column) or not isinstance(atom.right, exp.Column) for atom in conditions):
                fail('关联必须只由真实外键等值组成，不能混入 false、OR 或过滤条件。')
        equalities = [atom for join in joins for atom in atoms(join.args.get('on'))]
        while len(seen) < len(sources):
            before = set(seen)
            for alias, source in sources.items():
                if alias in seen:
                    continue
                target = catalog.get_table(source.name, source.db or 'public')
                for old in tuple(seen):
                    physical = catalog.get_table(sources[old].name, sources[old].db or 'public')
                    for fk in physical.foreign_keys:
                        ref = fk.get('references') or {}
                        columns, remote = fk.get('columns') or [], ref.get('columns') or []
                        if ref.get('table') != target.name or (ref.get('schema') or 'public') != target.schema or not columns or set(remote) != set(target.primary_key):
                            continue
                        nullable = any(next(column for column in physical.columns if column.name == name).nullable for name in columns)
                        # An explicitly requested dimension's inner join may
                        # exclude its unclassified NULL group. This exception
                        # never proves an ungrouped/global denominator.
                        grouping = get('grouping', []) or []
                        group_columns = list((scope.expression.args.get('group') or exp.Group()).find_all(exp.Column))
                        requested_dimension = any(str(item).startswith(target.name + '.') for item in grouping) or (get('rank_object') == target.name and isinstance(get('top_n'),int) and not isinstance(get('top_n'),bool) and get('top_n') > 0)
                        dimension = role == 'numerator' and requested_dimension and any(column.table == alias for column in group_columns)
                        if nullable and not dimension:
                            continue
                        required = {frozenset(((old, left), (alias, right))) for left, right in zip(columns, remote)}
                        actual = {frozenset(((atom.left.table, atom.left.name), (atom.right.table, atom.right.name))) for atom in equalities}
                        if required <= actual:
                            seen.add(alias)
            if seen == before:
                fail('关联缺少真实非空外键至主键的 to-one 证明，可能重复或丢弃金额。')
        # Every ON equality must be a used catalog FK; an extra EQ can still filter.
        for atom in equalities:
            legal = False
            for left, right in ((atom.left, atom.right), (atom.right, atom.left)):
                table = catalog.get_table(sources[left.table].name)
                legal |= any(fk.get('columns') == [left.name] and (fk.get('references') or {}).get('table') == sources[right.table].name and (fk.get('references') or {}).get('columns') == [right.name] for fk in table.foreign_keys)
            if not legal:
                fail('ON 含合同外额外等值条件。')

    def binding_matches(atom, scope, binding):
        # A single physical atom is checked in its real FROM/JOIN scope. This
        # does not expose another CTE's WHERE as evidence for this operand.
        probe = scope.expression.copy()
        probe.set('expressions', [exp.Literal.number(1)])
        for key in ('with_', 'group', 'having', 'order', 'limit', 'offset', 'qualify'):
            probe.set(key, None)
        probe.set('where', exp.Where(this=atom.copy()))
        try:
            check_binding(probe.sql(dialect='postgres'), catalog, [{**binding, 'binding_scope': 'global'}])
            return True
        except ValueError:
            return False

    proofs = []
    numerator_owners = []
    def operand(node, scope, role):
        node, owner = resolve(node, scope)
        rounded_digits = None
        if role == 'numerator' and isinstance(node, exp.Mul):
            candidates = [(literal, other) for literal, other in ((node.left, node.right), (node.right, node.left)) if isinstance(literal, exp.Literal) and not literal.is_string and Decimal(literal.this) in {1, 100}]
            if len(candidates) == 1:
                node, owner = resolve(candidates[0][1], owner)
        if role == 'denominator':
            if not isinstance(node,exp.Nullif) or not isinstance(node.expression, exp.Literal) or node.expression.is_string or Decimal(node.expression.this) != 0:
                fail('分母仅支持 NULLIF(真实分母,0)，禁止改变零/NULL分母。')
            node, owner = resolve(node.this, owner)
        # Current currency operands are numeric with two decimal places. An
        # unconstrained numeric cast / ROUND >=2 cannot truncate their cents;
        # casts inside a physical amount or a predicate remain prohibited.
        if isinstance(node, exp.Cast):
            target = node.args.get('to')
            if target is None or target.this != exp.DataType.Type.DECIMAL or target.expressions:
                fail('操作数转换没有原始金额精度证明。')
            node, owner = resolve(node.this, owner)
        if isinstance(node, exp.Round):
            digits = node.args.get('decimals')
            if not isinstance(digits, exp.Literal) or digits.is_string or not digits.this.isdigit() or int(digits.this) < 2:
                fail('操作数舍入损失金额精度。')
            rounded_digits = int(digits.this)
            node, owner = resolve(node.this, owner)
        filter_condition=None
        if isinstance(node,exp.Filter):
            filter_condition=node.expression
            if not isinstance(filter_condition,exp.Where):
                fail('聚合FILTER缺少可证明的真实WHERE条件。')
            filter_condition=filter_condition.this
            node=strip(node.this)
        if not isinstance(node, exp.Sum) or node.args.get('distinct'):
            fail('实际被消费的操作数不是所需 SUM。')
        group = owner.expression.args.get('group')
        declared_grouping = get('grouping', []) or []
        if group is not None and (role == 'denominator' or (not declared_grouping and get('top_n') is None)):
            fail('全局比例操作数不能被未声明GROUP BY拆成多个分组；分母必须保持全局同期范围。')
        if group is not None and declared_grouping:
            actual = {field(item, owner) for item in group.expressions}
            allowed = set(declared_grouping)
            for item in declared_grouping:
                if isinstance(item, str) and len(item.split('.')) == 2:
                    table = item.split('.')[0]
                    allowed.update(table + '.' + name for name in catalog.get_table(table).primary_key)
            if None in actual or not actual <= allowed:
                fail('比例实际GROUP BY含当前合同以外的维度。')
        value, condition = strip(node.this), None
        aggregate_null_policy='filtered_empty_set_null' if filter_condition is not None else 'empty_sum_null'
        if isinstance(value, exp.Case):
            branches = value.args.get('ifs') or []
            if value.this is not None or len(branches) != 1:
                fail('仅证明单分支 searched CASE，拒绝隐藏前置分支。')
            default = strip(value.args.get('default'))
            explicit_zero=isinstance(default,exp.Literal) and not default.is_string and Decimal(default.this)==0
            invoice_null=expected[role]=='invoice_revenue' and (default is None or isinstance(default,exp.Null))
            if not explicit_zero and not invoice_null:
                fail('条件金额仅支持明确 ELSE 0，NULL 语义需独立约定。')
            aggregate_null_policy='case_else_zero_existing_compatibility' if explicit_zero else 'case_else_null'
            condition, value = branches[0].this, strip(branches[0].args.get('true'))
        metric = expected[role]
        valid = field(value, owner) == 'invoice.total' if metric == 'invoice_revenue' else isinstance(value, exp.Mul) and {field(value.left, owner), field(value.right, owner)} == {'invoice_line.unit_price', 'invoice_line.quantity'}
        if not valid:
            fail(role + '实际金额字段与 typed metric 不同，不能以碰巧相同结果代替。')
        if rounded_digits is not None:
            table, column = ('invoice', 'total') if metric == 'invoice_revenue' else ('invoice_line', 'unit_price')
            amount = next(item for item in catalog.get_table(table).columns if item.name == column)
            scale = re.fullmatch(r'(?:numeric|decimal)\(\s*\d+\s*,\s*(\d+)\s*\)', amount.data_type, re.I)
            quantity = next(item for item in catalog.get_table('invoice_line').columns if item.name == 'quantity') if metric == 'detail_revenue' else None
            if scale is None or int(scale[1]) > rounded_digits or (quantity is not None and quantity.data_type.lower() not in {'integer', 'smallint', 'bigint'}):
                fail('目录类型不能证明该聚合舍入保持原始金额精度。')
        physical_grain(owner, metric, role)
        if owner.expression.args.get('having') or owner.expression.args.get('offset') or (owner.expression.args.get('limit') and not owner.expression.args.get('group')):
            fail('金额聚合输入有未证明的 HAVING/LIMIT/OFFSET。')
        predicates = atoms(owner.expression.args.get('where')) + atoms(condition) + atoms(filter_condition)
        required = [item for item in bindings if item.get('binding_scope', 'global') in {'global', role}]
        period = contracts[role].get('period') or ((get('time_scope', {}) or {}).get('current') or {})
        if bool(period.get('start')) != bool(period.get('end')):
            fail('期间合同缺少完整半开边界。')
        if not period.get('start') and (get('time_scope',{})or{}).get('all_data') is not True:
            fail('比例操作数没有完整期间或已明确批准的全部数据范围。')
        covered = set()
        for atom in predicates:
            period_atom = False
            if period.get('start') and isinstance(atom, (exp.GTE, exp.LT)) and field(atom.left, owner) == 'invoice.invoice_date':
                key = 'start' if isinstance(atom, exp.GTE) else 'end'
                period_atom = _midnight_date(atom.right) == period[key]
                if period_atom:
                    covered.add(key)
            matches = [index for index, binding in enumerate(required) if binding_matches(atom, owner, binding)]
            if not period_atom and not matches:
                fail(role + '含未授权筛选或其它操作数条件泄漏。')
        if period.get('start') and covered != {'start', 'end'}:
            fail(role + '未保留完整当前期间。')
        effective = owner.expression.copy()
        effective.set('expressions', [exp.Literal.number(1)])
        for key in ('with_', 'group', 'having', 'order', 'limit', 'offset', 'qualify'):
            effective.set(key, None)
        effective.set('where', exp.Where(this=exp.and_(*[item.copy() for item in predicates])) if predicates else None)
        # Binding validator sees ONLY this actual physical operand select.
        check_binding(effective.sql(dialect='postgres'), catalog, required)
        if role == 'numerator':
            numerator_owners.append((owner, node))
        return {'role': role, 'metric': metric, 'period': period, 'physical_owner': owner.expression.sql(dialect='postgres'), 'effective_filter_sql': effective.sql(dialect='postgres'), 'bindings_verified': len(required),
                'aggregate_null_policy':aggregate_null_policy,'zero_denominator_policy':'NULLIF_zero_to_null' if role=='denominator'else None}

    def projected_scale(node, scope, depth=0):
        if depth > 20:
            fail('比例输出包装超过有界深度。')
        node, scope = resolve(node, scope, depth)
        if isinstance(node, (exp.Round, exp.Cast)):
            return projected_scale(node.this, scope, depth + 1)
        if isinstance(node, exp.Mul):
            for literal, other in ((node.left, node.right), (node.right, node.left)):
                if isinstance(literal, exp.Literal) and not literal.is_string:
                    scale = projected_scale(other, scope, depth + 1)
                    return None if scale is None else Decimal(literal.this) * scale
        if isinstance(node, exp.Div):
            left, _ = resolve(node.left, scope, depth + 1)
            if isinstance(left, exp.Mul):
                for literal, other in ((left.left, left.right), (left.right, left.left)):
                    if isinstance(literal, exp.Literal) and not literal.is_string:
                        return Decimal(literal.this)
            return Decimal(1)
        return None

    output_rounding = []
    from qa_agent.sql.percentage_precision import requested_percent_digits as _percent_digits
    def requested_percent_digits():
        return _percent_digits(intent,fail)

    def find_ratio(node, scope, depth=0, outer_scale=Decimal(1)):
        node, scope = resolve(node, scope, depth)
        if isinstance(node, exp.Round):
            scale = projected_scale(node.this, scope)
            if scale is not None:
                digits, requested = node.args.get('decimals'), requested_percent_digits()
                if scale not in {Decimal(1), Decimal(100)} or not isinstance(digits, exp.Literal) or digits.is_string or not str(digits.this).isdigit() or requested is None:
                    fail('比例SQL舍入缺少明确当前百分比精度授权；请交程序最终格式化。')
                required = requested + (2 if scale == 1 else 0)
                if int(digits.this) != required:
                    fail('比例SQL舍入的原始/百分比尺度与明确展示精度不一致，可能提前损失或重复舍入。')
                output_rounding.append({'actual_scale': str(scale), 'sql_decimals': int(digits.this), 'requested_percent_decimals': requested, 'claim': 'explicit_display_rounding_not_lossless_ratio_equivalence'})
            return find_ratio(node.this, scope, depth + 1, outer_scale)
        if isinstance(node, exp.Cast):
            target = node.args.get('to')
            if target is None or target.this != exp.DataType.Type.DECIMAL or target.expressions:
                fail('比例输出类型转换没有保精度证明。')
            return find_ratio(node.this, scope, depth + 1, outer_scale)
        if isinstance(node, exp.Mul):
            for literal, other in ((node.left, node.right), (node.right, node.left)):
                if isinstance(literal, exp.Literal) and not literal.is_string and Decimal(literal.this) in {1, 100}:
                    return find_ratio(other, scope, depth + 1, outer_scale * Decimal(literal.this))
        if isinstance(node, exp.Div):
            scale = projected_scale(node, scope) * outer_scale
            if scale not in {Decimal(1), Decimal(100)}:
                fail('最终比例存在重复百分比放大或未授权缩放。')
            proofs.append({'numerator': operand(node.left, scope, 'numerator'), 'denominator': operand(node.right, scope, 'denominator'), 'output_scale': str(scale)})

    for projection in root.expression.selects:
        find_ratio(projection, root)
    if not proofs:
        fail('最终输出没有实际消费的可证明比例。')
    ranking = None
    top_n, rank_object = get('top_n'), get('rank_object')
    if top_n is not None:
        if isinstance(top_n, bool) or not isinstance(top_n, int) or not 1 <= top_n <= 200 or rank_object != 'genre' or expected['numerator'] != 'detail_revenue':
            fail('比例逐实体排名缺少受支持的对象/TopN合同。')
        if len(numerator_owners) != 1:
            fail('逐实体比例排名必须只有一个实际分子度量。')
        if ranking_scope is None:
            fail('比例列表缺少唯一实际消费的精确TopN限制。')
        actual_limit = root.expression.args.get('limit')
        if ranking_scope is not root and actual_limit is not None and int(actual_limit.expression.this) < top_n:
            fail('最终透传层LIMIT会丢弃已证明的TopN结果。')
        if root.expression.args.get('offset') or root.expression.args.get('distinct'):
            fail('最终排名不允许未授权偏移或去重。')
        order = ranking_scope.expression.args.get('order')
        if not order or not order.expressions or order.expressions[0].args.get('desc') is not True:
            fail('比例排名必须按当前分子实际金额降序。')
        if (get('order', {}) or {}).get('direction', 'desc') != 'desc':
            fail('当前比例排名合同并非受支持的降序TopN。')
        measure = strip(order.expressions[0].this)
        if isinstance(measure, exp.Column) and not measure.table:
            projected = next((item for item in ranking_scope.expression.selects if item.alias_or_name == measure.name), None)
            if projected is None:
                fail('排序别名没有真实最终投影。')
            measure = strip(projected)
        measure, order_owner = resolve(measure, ranking_scope)
        if isinstance(measure, exp.Cast):
            target = measure.args.get('to')
            if target is None or target.this != exp.DataType.Type.DECIMAL or target.expressions:
                fail('排序金额转换无法证明无损。')
            measure, order_owner = resolve(measure.this, order_owner)
        if isinstance(measure, exp.Round):
            digits = measure.args.get('decimals')
            price = next(item for item in catalog.get_table('invoice_line').columns if item.name == 'unit_price')
            quantity = next(item for item in catalog.get_table('invoice_line').columns if item.name == 'quantity')
            declared = re.fullmatch(r'(?:numeric|decimal)\(\s*\d+\s*,\s*(\d+)\s*\)', price.data_type, re.I)
            if not isinstance(digits, exp.Literal) or digits.is_string or not str(digits.this).isdigit() or declared is None or int(digits.this) < int(declared[1]) or quantity.data_type.lower() not in {'integer', 'smallint', 'bigint'}:
                fail('排序金额舍入无法证明保留真实精度。')
            measure, order_owner = resolve(measure.this, order_owner)
        # Match the exact already-proved consumed SUM, not a spare aggregate,
        # the ratio itself (denominator sign unknown), ID or monetary constant.
        numerator_owner, numerator_sum = numerator_owners[0]
        if order_owner is not numerator_owner or measure.sql(dialect='postgres') != numerator_sum.sql(dialect='postgres'):
            fail('主排序没有追溯至实际被消费的同一分子SUM明细金额。')
        if ranking_scope is not root:
            outer_order = root.expression.args.get('order')
            if not outer_order or not outer_order.expressions or outer_order.expressions[0].args.get('desc') is not True:
                fail('最终结果未保持已证明TopN的金额降序。')
            final_measure = strip(outer_order.expressions[0].this)
            if isinstance(final_measure,exp.Column) and not final_measure.table:
                projection = next((item for item in root.expression.selects if item.alias_or_name == final_measure.name),None)
                if projection is None:
                    fail('最终排序别名缺少真实投影。')
                final_measure=strip(projection)
            final_measure, final_owner=resolve(final_measure,root)
            if final_owner is not numerator_owner or final_measure.sql(dialect='postgres') != numerator_sum.sql(dialect='postgres'):
                fail('最终排序未追溯到同一已证明的分子金额。')
        group = numerator_owner.expression.args.get('group')
        if group is None:
            fail('逐曲风比例没有实际GROUP BY维度。')
        actual_fields = [field(item, numerator_owner) for item in group.expressions]
        if not actual_fields or any(not item or item.split('.')[0] != rank_object for item in actual_fields):
            fail('实际聚合混入其它维度，不能冒充每个曲风的金额。')
        requested = set(get('grouping', []) or [])
        primary = {rank_object + '.' + name for name in catalog.get_table(rank_object).primary_key}
        if not (primary <= set(actual_fields) or (requested and requested <= set(actual_fields))):
            fail('实际GROUP BY未覆盖当前请求的实体维度。')
        ranking = {'rank_object': rank_object, 'top_n': top_n, 'direction': 'desc', 'measure': 'same_consumed_detail_sum', 'group_fields': actual_fields, 'authority_scope':ranking_scope.expression.sql(dialect='postgres'), 'final_order_verified':True}
    return {'verified': True, 'mode': 'typed_physical_ratio_operands', 'proofs': proofs, 'ranking': ranking, 'output_rounding': output_rounding}

