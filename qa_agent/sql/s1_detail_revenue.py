"""Bounded S1 revenue-grain check; no defaults, state, SQL edits or execution.

Only a final direct physical SUM is checked. In particular, a valid independent
invoice denominator and an unconsumed CTE are not artist-detail aggregates.
"""
from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.optimizer.scope import build_scope, walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


def _un(node):
    while isinstance(node, (exp.Alias, exp.Paren)):
        node = node.this
    return node


def _atoms(node):
    if isinstance(node, exp.Where):
        node = node.this
    node = _un(node)
    return _atoms(node.left) + _atoms(node.right) if isinstance(node, exp.And) else [node] if node is not None else []


def _positive_directive(match, source):
    if match is None:
        return False
    start = max((source.rfind(mark, 0, match.start()) for mark in '，,。；;\n！？!?'), default=-1) + 1
    prefix = source[start:match.start()]
    # The exact affirmative substring is not authority when its owning source
    # clause negates, quotes or merely proposes it. Cross-comma current edits
    # must be checked even when that clause contains no revenue noun itself.
    if re.search(r'不要|不能|不可|不应|不必|不用|无需|不需要|并非|不是|不按|不采用|别|例如|比如|示例|举例|假设|引用|[“”"「」『』]', prefix):
        return False
    tail = source[match.end():match.end()+60].split('\n', 1)[0]
    return not re.search(r'尚未(?:确认|确定)|还没定|未确认|未确定|仅供举例|仅为示例', tail)


def _source_measure(question, text):
    """Record actual approved knowledge and actual user priority, not model tags."""
    from qa_agent.sql.business_knowledge import business_knowledge
    if not isinstance(question, str) or not isinstance(text, str):
        return None
    if (not re.search(r'销售额|销售金额|销售收入|营收|收入|卖了?多少(?:钱|金额)|\bsales\b|\brevenue\b', question, re.I)
            or re.search(r'客户|customer|占比|比例|百分|分母|除以|平均|每张|同比|环比|增长|定义|口径是什么', question, re.I)):
        return None
    clauses = re.split(r'[，,。；;！？!?\n]', question)
    money = [c for c in clauses if re.search(r'销售额|销售金额|销售收入|营收|收入|卖了?多少(?:钱|金额)|\bsales\b|\brevenue\b', c, re.I)]
    if not money or any(re.search(r'不要|不按|不用|不需要|不是|只解释|仅解释|例如|比如|示例|假设|引用', c) for c in money):
        return None
    subject = bool(re.search(r'艺术家|艺人|乐队|专辑|曲目|歌曲|流派|\b(?:artist|band|album|track|genre)s?\b', question, re.I))
    if not subject:
        # Exact direct index identity only establishes this broad music domain;
        # it never selects/approves a binding or an ambiguous candidate.
        from qa_agent.config import get_settings
        from qa_agent.nlu.value_index import load_value_index
        index = load_value_index(get_settings().value_index_path)
        subject = bool(index and any(record.kind in {'standard', 'alias'}
            and record.column in {'artist.name', 'album.title', 'track.name', 'genre.name'}
            and re.search(r'(?<![\w])' + re.escape(record.surface) + r'(?![\w])', question, re.I)
            for record in index.records if record.surface))
    if not subject:
        return None
    known = business_knowledge() or {}
    references = [r for r in known.get('references', [])
                  if r.get('source_id') == 'project:confirmed_metric_definitions'
                  and r.get('review_status') == 'approved']
    if len(references) != 1:
        return None
    ref = references[0]
    metrics = [m for m in ref.get('metrics', []) if m.get('id') == 'sales_revenue']
    if (len(metrics) != 1 or re.sub(r'\s', '', metrics[0].get('expression', '')).casefold() != 'sum(invoice.total)'
            or 'sum(invoice_line.unit_price*invoice_line.quantity)' not in
            re.sub(r'\s', '', metrics[0].get('alternative', '')).casefold()):
        return None
    explicit_detail = re.search(r'(?:按明细算|按明细口径|按实际成交算|按曲目层面算|逐条明细|每条明细)', question)
    explicit_invoice = re.search(r'(?:按发票(?:层面|口径)|逐张发票|每张发票只|发票逐张)', question)
    # Only closed source wording is recognized. Unknown user metric overrides
    # are not replaced by the registered alternative or model interpretation.
    if (explicit_detail and not _positive_directive(explicit_detail, question)
            or explicit_invoice and not _positive_directive(explicit_invoice, question)
            or explicit_detail and explicit_invoice):
        return None
    invoice_rule = re.search(r'(?:一律|统一).{0,8}(?:指|按|使用).{0,8}发票层面.{0,20}发票总额', text)
    detail_rule = re.search(r'如果我问.{0,120}(?:艺术家|曲目|流派).{0,120}(?:明细行|每一行明细)', text, re.S)
    if (invoice_rule and not _positive_directive(invoice_rule, text)
            or detail_rule and not _positive_directive(detail_rule, text)):
        return None
    if explicit_detail:
        mode, quote, location = 'detail', explicit_detail[0], 'current'
    elif explicit_invoice:
        mode, quote, location = 'invoice_once', explicit_invoice[0], 'current'
    elif invoice_rule:
        mode, quote, location = 'invoice_once', invoice_rule[0], 'brief'
    elif detail_rule:
        mode, quote, location = 'detail', detail_rule[0], 'brief'
    elif re.search(r'金额|销售额|收入', text) and re.search(r'口径|定义|发票|明细', text):
        return None  # Unrecognized actual user policy takes priority; no guess.
    else:
        mode, quote, location = 'detail', metrics[0]['alternative'], 'approved_metric'
    return {'mode': mode, 'source': location, 'quote': quote,
            'source_sha256': sha256((question if location == 'current' else text if location == 'brief'
                                      else metrics[0]['alternative']).encode()).hexdigest(),
            'approved_metric_source': {k: ref.get(k) for k in ('source_id', 'path', 'sha256', 'review_status')},
            'model_or_semantic_contract_used': False}


def revenue_source_hint(source_question, source_text=''):
    """Expose the same checked source interpretation to generation, as a hint.

    This selects no entity/filter/period and grants no contract or execution
    permission. All wording, priority and polarity checks stay in one function.
    """
    return _source_measure(source_question, source_text)


def _line_rowset(scope, catalog):
    """At most one output per surviving line, not full-population preservation.

    A nullable FK inner lookup can remove a line but cannot multiply it. The
    manual's stronger nonnull/full-population helper must not be reused here.
    """
    sources = {alias: value for alias, (_, value) in scope.selected_sources.items()}
    if any(not isinstance(t, exp.Table) or (t.db or 'public') != 'public' for t in sources.values()):
        return None
    physical = {a: catalog.get_table(t.name, t.db or 'public') for a, t in sources.items()}
    if len({(t.schema, t.name) for t in physical.values()}) != len(physical):
        return None
    seen = {a for a, t in physical.items() if t.name == 'invoice_line'}
    if len(seen) != 1:
        return None
    actual = set()
    for join in scope.expression.args.get('joins') or []:
        atoms = _atoms(join.args.get('on'))
        if (join.side or join.kind not in ('', 'INNER') or not atoms
                or any(not isinstance(a, exp.EQ) or not isinstance(a.left, exp.Column)
                       or not isinstance(a.right, exp.Column) for a in atoms)):
            return None
        actual.update(frozenset(((a.left.table, a.left.name), (a.right.table, a.right.name))) for a in atoms)
    used = set()
    while len(seen) < len(sources):
        before = set(seen)
        for parent, table in physical.items():
            if parent in seen:
                continue
            for child in tuple(seen):
                for fk in physical[child].foreign_keys:
                    ref = fk.get('references') or {}
                    local, remote = fk.get('columns') or [], ref.get('columns') or []
                    if ((ref.get('schema', 'public'), ref.get('table')) != (table.schema, table.name)
                            or tuple(remote) != table.primary_key or not local or len(local) != len(remote)):
                        continue
                    needed = {frozenset(((child, l), (parent, r))) for l, r in zip(local, remote)}
                    if needed <= actual:
                        seen.add(parent)
                        used.update(needed)
        if seen == before:
            return None
    return sources if actual <= used else None


def validate_s1_detail_revenue(sql, catalog, source_question, *, enabled=False,
                             source_text='', generation_context=None):
    """Raise a normal SQLValidationError for one source-backed wrong SUM grain."""
    def unknown(reason):
        return {'verified': False, 'status': 'not_verified', 'reason': reason,
                'business_semantics_verified': False}
    if enabled is not True or catalog.database != 'chinook':
        return unknown('disabled_or_other_database')
    measure = _source_measure(source_question, source_text)
    if measure is None:
        return unknown('no_unambiguous_source_supported_music_revenue_task')
    try:
        tree = _qualified(sql, catalog)
        scope = build_scope(tree)
    except Exception:
        return unknown('unresolved_SQL_or_catalog')
    if (not isinstance(tree, exp.Select) or scope is None or tree.args.get('distinct')
            or any(tree.args.get(k) for k in ('having', 'qualify'))
            or any(not isinstance(value, exp.Table) for _, value in scope.selected_sources.values())):
        return unknown('not_direct_physical_consumed_scope')
    nodes = list(walk_in_scope(tree))
    aggregates = [n for n in nodes if isinstance(n, exp.AggFunc)]
    if (len(aggregates) != 1 or not isinstance(aggregates[0], exp.Sum)
            or any(isinstance(n, (exp.Window, exp.Subquery, exp.Exists)) for n in nodes)):
        return unknown('not_one_direct_SUM_or_independent_operand_present')
    aggregate = aggregates[0]
    consumed = 0
    for projection in tree.selects:
        value = _un(projection)
        if aggregate in list(value.walk()):
            while isinstance(value, (exp.Round, exp.Cast)):
                value = _un(value.this)
            if value is not aggregate:
                return unknown('SUM_is_transformed_or_ratio_not_just_displayed')
            consumed += 1
        elif not isinstance(value, exp.Column):
            return unknown('other_output_not_native_identity')
    if consumed != 1:
        return unknown('aggregate_not_the_actual_output')
    # Prove only the surviving invoice_line row grain, not its full population.
    try:
        sources = _line_rowset(scope, catalog)
    except (ValueError, KeyError, StopIteration):
        sources = None
    if sources is None:
        return unknown('no_single_real_line_grain_FK_rowset')
    invoices = [a for a, s in sources.items() if s.name == 'invoice']
    lines = [a for a, s in sources.items() if s.name == 'invoice_line']
    if len(invoices) != 1 or len(lines) != 1:
        return unknown('not_one_invoice_and_one_detail_instance')
    owner, child = invoices[0], lines[0]
    value = _un(aggregate.this)
    if isinstance(value, exp.Distinct):
        if len(value.expressions) != 1:
            return unknown('not_single_DISTINCT_sum_argument')
        value = _un(value.expressions[0])
    # The reverse mismatch is independent of repeated parent-row fanout:
    # even one line's price*quantity is not the source-defined whole invoice.
    # Only the actually consumed, untransformed same-instance physical product
    # is recognized; CTE wrappers, unknown expressions and other owners stay NV.
    product = (isinstance(value, exp.Mul)
        and isinstance(_un(value.left), exp.Column)
        and isinstance(_un(value.right), exp.Column)
        and {_un(value.left).table, _un(value.right).table} == {child}
        and {_un(value.left).name, _un(value.right).name} == {'unit_price', 'quantity'})
    if measure['mode'] == 'invoice_once' and product:
        error = SQLValidationError('S1销售金额粒度：实际用户肯定来源要求按发票逐票累加、每票只计一次；'
            '当前最终输出却是明细成交单价×数量的SUM，不能代替该来源的整张发票金额。'
            '请保留原对象、期间、分组、筛选和NULL，用真实分组身份与invoice主键确定唯一发票集合后逐票汇总发票总额；'
            '不能直接在明细JOIN上SUM发票总额，也不能用SUM(DISTINCT 金额)冒充按票去重。'
            '只有本轮真实用户明确切换为明细口径时才使用明细成交金额；不要从模型解释或条件句替用户切换。')
        error.source_measure_proof = measure
        error.sql_grain_proof = {'mode': 'single_consumed_detail_SUM_conflicts_with_invoice_once_source',
            'invoice_alias': owner, 'detail_alias': child, 'SQL_sha256': sha256(sql.encode()).hexdigest(),
            'expected_source_measure': 'invoice_once', 'actual_consumed_measure': 'detail_amount',
            'business_semantics_verified': False}
        raise error
    if not (isinstance(value, exp.Column) and value.table == owner and value.name == 'total'):
        return unknown('not_a_direct_invoice_total_SUM')
    line_table = catalog.get_table('invoice_line', 'public')
    if len(line_table.primary_key) != 1:
        return unknown('no_single_physical_detail_PK')
    pk = line_table.primary_key[0]
    # A literal equality on the real child PK proves at most one input row;
    # grouping by that PK likewise cannot repeat a parent within one SUM.
    restricted = any(isinstance(a, exp.EQ) and any(
        isinstance(l, exp.Column) and l.table == child and l.name == pk
        and isinstance(r, exp.Literal) and not r.is_string
        for l, r in ((a.left, a.right), (a.right, a.left))) for a in _atoms(tree.args.get('where')))
    group = tree.args.get('group')
    per_line = bool(group and any(isinstance(_un(g), exp.Column)
        and _un(g).table == child and _un(g).name == pk for g in group.expressions))
    if measure['mode'] == 'invoice_once' and (restricted or per_line):
        return unknown('child_PK_prevents_repeated_parent_within_this_SUM')
    if measure['mode'] == 'detail':
        message = ('原问及已确认来源要求艺术家/专辑/曲目明细销售金额；当前实际输出却累加整张发票金额。'
            '请使用真实明细成交单价×购买数量的SUM，保留原对象、期间、筛选和NULL，不把其它明细的金额归入该对象。')
    else:
        message = ('实际用户正文要求发票逐张累加、每票只计一次；当前SUM(invoice.total)仍处于invoice_line明细行粒度，'
            '会把同一张发票重复计入。请先用真实invoice主键确定符合条件的唯一发票集合，再逐票汇总实际发票总额；'
            '不能用SUM(DISTINCT total)去重金额，也不要擅自切成明细销售额。保留原对象、期间、筛选和NULL。')
    error = SQLValidationError('S1销售金额粒度：' + message)
    error.source_measure_proof = measure
    error.sql_grain_proof = {'mode': 'single_consumed_physical_invoice_SUM_at_detail_grain',
        'invoice_alias': owner, 'detail_alias': child, 'SQL_sha256': sha256(sql.encode()).hexdigest(),
        'business_semantics_verified': False}
    raise error
