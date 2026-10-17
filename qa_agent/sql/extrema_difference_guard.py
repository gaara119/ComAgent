"""Bounded proof of an explicitly requested monthly MAX-minus-MIN.

Consumes only the current typed intent and authentic catalog. No reference
answers, question identifiers, saved results, model calls or SQL rewriting.
"""
from __future__ import annotations

from hashlib import sha256
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes, _midnight_date
from qa_agent.sql.validator import SQLValidationError, validate_value_bindings


def validate_monthly_extrema_difference(sql, catalog, intent):
    get = lambda name, default=None: intent.get(name, default) if isinstance(intent, dict) else getattr(intent, name, default)
    contract = (get('query_scope', {}) or {}).get('extrema_difference')
    if contract is None:
        return {'verified': True, 'mode': 'no_typed_extrema_difference'}

    def deny(message):
        raise SQLValidationError('月度极值差：' + message)

    if not isinstance(contract, dict) or any(contract.get(k) != v for k, v in {
        'grain': 'month', 'metric': 'invoice_revenue', 'operation': 'max_minus_min',
    }.items()):
        deny('缺少受支持的月度发票金额最高减最低合同。')
    if contract.get('source') != 'program:explicit_extrema_difference' or not isinstance(contract.get('source_evidence'), str) or not contract['source_evidence'].strip():
        deny('月极值差合同必须由程序根据实际原句重建，并保存非空原文证据。')
    if get('metric') != 'invoice_revenue' or get('task_type') in {'growth', 'ratio', 'ranking'}:
        deny('任务必须是绝对金额差，不能仍为同比、占比或排名。')
    period = ((get('time_scope', {}) or {}).get('current') or {})
    if bool(period.get('start')) != bool(period.get('end')):
        deny('当前期间缺少完整半开边界。')
    if not period.get('start') and not (get('time_scope', {}) or {}).get('all_data'):
        deny('未证明明确期间或当前全数据授权。')
    required = get('filters', []) or []
    if any(b.get('binding_scope', 'global') not in {'global', None} for b in required):
        deny('极值差只支持同一全局范围，不能混入比例操作数或资格作用域。')
    tree = _qualified(sql, catalog)
    scopes = list(traverse_scope(tree))
    active = _active_scopes(scopes)
    by_expression = {id(s.expression): s for s in scopes}
    root = next(s for s in scopes if s.parent is None)

    def strip(node):
        while isinstance(node, (exp.Alias, exp.Paren)):
            node = node.this
        return node

    def resolve(node, owner, depth=0):
        if depth > 20:
            deny('投影谱系超过有界深度。')
        node = strip(node)
        if isinstance(node, exp.Column):
            source = owner.sources.get(node.table)
            if source is not None and not isinstance(source, exp.Table):
                projected = next((p for p in source.expression.selects if p.alias_or_name == node.name), None)
                if projected is None:
                    deny('派生字段没有实际投影。')
                return resolve(projected, source, depth + 1)
        if isinstance(node, exp.Subquery):
            source = by_expression.get(id(node.this))
            if source is None or len(source.expression.selects) != 1:
                deny('标量子查询必须唯一投影。')
            return resolve(source.expression.selects[0], source, depth + 1)
        return node, owner

    def field(node, owner):
        node = strip(node)
        if not isinstance(node, exp.Column):
            return None
        source = owner.sources.get(node.table)
        if not isinstance(source, exp.Table) or (source.db or 'public') != 'public':
            return None
        return source.name + '.' + node.name

    def exact_atoms(node):
        if node is None:
            return []
        node = strip(node)
        if isinstance(node, exp.Where):
            return exact_atoms(node.this)
        if isinstance(node, exp.And):
            return exact_atoms(node.left) + exact_atoms(node.right)
        return [node]

    # Deliberately bounded to one actual invoice source. Unsupported join-based
    # scopes fail explicitly rather than guessing invoice cardinality.
    def physical_monthly_sum(node, owner):
        node, owner = resolve(node, owner)
        if not isinstance(node, exp.Sum) or node.args.get('distinct') or field(node.this, owner) != 'invoice.total':
            deny('极值必须消费真实每月SUM(invoice.total)，不能消费常量、行极值或其它度量。')
        sources = [s for _, s in owner.selected_sources.values()]
        if len(sources) != 1 or not isinstance(sources[0], exp.Table) or sources[0].name != 'invoice':
            deny('当前有界证明只支持唯一真实发票行集，不能用联接或派生筛选改变金额粒度。')
        q = owner.expression
        if q.args.get('joins') or any(q.args.get(k) for k in ('having', 'qualify', 'distinct', 'offset', 'limit')):
            deny('月汇总不得提前TopN、HAVING、去重、偏移或连接改变集合。')
        group = q.args.get('group')
        if group is None or len(group.expressions) != 1:
            deny('必须只按真实完整月份分组。')
        month, mo = resolve(group.expressions[0], owner)
        if not isinstance(month, exp.TimestampTrunc) or str(month.args.get('unit')).upper() != 'MONTH' or month.args.get('zone') is not None or field(month.this, mo) != 'invoice.invoice_date':
            deny('月份键必须是实际发票日期的DATE_TRUNC(month)，不能截字符串、转整数或混合其它维度。')
        predicates = exact_atoms(q.args.get('where'))
        covered = set()
        matched = set()
        for atom in predicates:
            if not isinstance(atom, (exp.EQ, exp.NEQ, exp.In, exp.GT, exp.GTE, exp.LT, exp.LTE)):
                deny('筛选必须是完整AND连接的真实字段比较；OR/NOT不能被某个必然条件掩盖。')
            period_atom = False
            if period.get('start') and isinstance(atom, (exp.GTE, exp.LT)) and field(atom.left, owner) == 'invoice.invoice_date':
                key = 'start' if isinstance(atom, exp.GTE) else 'end'
                period_atom = _midnight_date(atom.right) == period[key]
                if period_atom:
                    covered.add(key)
            matches = []
            for index, binding in enumerate(required):
                probe = q.copy()
                probe.set('expressions', [exp.Literal.number(1)])
                for key in ('with_', 'group', 'having', 'order', 'limit', 'offset', 'qualify'):
                    probe.set(key, None)
                probe.set('where', exp.Where(this=atom.copy()))
                try:
                    validate_value_bindings(probe.sql(dialect='postgres'), catalog, [{**binding, 'binding_scope': 'global'}])
                    matches.append(index)
                except ValueError:
                    pass
            if not period_atom and not matches:
                deny('实际月集合含未授权额外条件或不受支持布尔筛选。')
            matched.update(matches)
        if period.get('start') and covered != {'start', 'end'}:
            deny('未保留当前完整半开期间。')
        if matched != set(range(len(required))):
            deny('实际月集合遗漏当前授权条件。')
        return owner, node.sql(dialect='postgres')

    consumed_monthly = set()
    extrema_owners = set()

    def extremum(node, owner, wanted=None):
        node, owner = resolve(node, owner)
        if not isinstance(node, (exp.Max, exp.Min)) or wanted is not None and not isinstance(node, wanted):
            deny('必须按真实最高月额减最低月额方向计算，不接受有损包装或常量。')
        if owner.expression.args.get('group'):
            deny('月极值层必须对完整月集合做全局聚合。')
        monthly, measure = physical_monthly_sum(node.this, owner)
        consumed_monthly.add(monthly)
        extrema_owners.add(owner)
        return monthly, measure

    differences = 0
    for projection in root.expression.selects:
        node, owner = resolve(projection, root)
        if isinstance(node, exp.Sub):
            left = extremum(node.left, owner, exp.Max)
            right = extremum(node.right, owner, exp.Min)
            if left != right:
                deny('最高与最低必须来自实际同一期间、同一条件、同一月汇总集合。')
            differences += 1
        else:
            extremum(node, owner)
    if differences != 1 or len(consumed_monthly) != 1:
        deny('最终输出必须包含唯一真实月汇总极值差，辅助项只能是同源最高/最低。')
    monthly = next(iter(consumed_monthly))
    for scope in active:
        if scope is monthly:
            continue
        q = scope.expression
        if not isinstance(q, exp.Select) or any(q.args.get(k) for k in ('where', 'group', 'having', 'qualify', 'distinct', 'offset')):
            deny('透传或极值层不得再次筛选、分组、去重或偏移月集合。')
        limit = q.args.get('limit')
        if limit is not None and (scope is not root or not isinstance(limit.expression, exp.Literal) or limit.expression.is_string or not str(limit.expression.this).isdigit() or int(limit.expression.this) < 1):
            deny('只允许最终单行结果的正数展示上限，不能提前限制月份。')
        sources = [s for _, s in scope.selected_sources.values()]
        if any(isinstance(s, exp.Table) for s in sources):
            deny('极值或透传层不能混入额外物理行集。')
        if scope in extrema_owners:
            if len(sources) != 1 or sources[0] is not monthly or q.args.get('joins'):
                deny('极值必须直接且唯一消费已证明的完整月份集合。')
        elif len(sources) > 1 or q.args.get('joins'):
            deny('当前有界证明不允许多行连接或独立极值集合，使用单个月汇总CTE后统一MAX/MIN。')
    return {'verified': True, 'mode': 'same_physical_monthly_invoice_max_minus_min',
            'sql_sha256': sha256(sql.encode('utf-8')).hexdigest(), 'monthly_scope': monthly.expression.sql(dialect='postgres'),
            'period': period, 'required_bindings': len(required), 'output_difference': 'max_minus_min',
            'reference_answers_consumed': False}
