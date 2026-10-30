"""Candidate S1-only total/preview output check, not a business certificate.

The caller may enable this only for the final, unique non-identity business SQL
which owns both obligations. This function cannot infer a multi-SQL plan from
one SQL string. It never chooses a measure, entity, period, unit or default.
"""
from collections import Counter
from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import Scope, build_scope, walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


class TotalPreviewIncomplete(SQLValidationError):
    """A proven full-total obligation was answered by a bounded preview only."""


class _Unknown(ValueError):
    pass


def _un(node):
    while isinstance(node, (exp.Alias, exp.Paren)):
        node = node.this
    return node


def _source(question):
    if not isinstance(question, str) or not question.strip():
        return None
    # A quoted/example/conditional or waived obligation is not an instruction.
    # This deliberately does not reject unrelated final "别混在一块儿" wording.
    if re.search(r'[“”「」『』"\']|例如|比如|示例|举例|假如|假设|如果|只解释|仅解释', question):
        return None
    if re.search(r'(?:不要|不用|无需|无须|不必|不需要|不算|不能|不应|不是|别|不(?:用|要)再).{0,12}(?:总额|总量|合计|总数|结论|明细|详情)|(?:总额|总量|合计|结论).{0,6}(?:不必|不要|不用|不算)', question):
        return None
    if re.search(r'占比|比例|百分|分母|除以|同比|环比|增长|平均|每(?:张|笔|人|组|月|年)|各自|分别|各(?:组|国|类|个)', question):
        return None
    # The contract below is one global total, never each entity's subtotal.
    # Keep a finite conservative source boundary, not a group-by interpreter.
    group_object = (r'(?:客户|用户|艺术家|艺人|乐队|员工|部门|公司|国家|地区|城市|'
                    r'流派|专辑|曲目|歌单|月份|季度|年份|门店|类别|分组|月|季|年)')
    if re.search(r'(?:各|每)(?:个|位|名|一)?\s*' + group_object
                 + r'|按(?:照)?\s*' + group_object + r'|\b(?:each|per)\b', question, re.I):
        return None
    preview = re.search(r'(?:明细|详情)(?:只(?:展示|返回|给)?前?|最多|不超过|至多)\s*(\d{1,4}|[一二两三四五六七八九十])\s*行', question)
    if not preview:
        return None
    number = preview[1]
    cap = int(number) if number.isdigit() else {'一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}.get(number)
    if not cap or cap > 1000:
        return None
    explicit = re.search(r'(?:完整|全部|总体|全范围|所有)(?:的)?(?:销售)?(?:总额|总量|合计|总数)|(?:销售总额|金额合计|销售额合计|总销售额|总数量)', question)
    whole = re.search(r'全部(?:数据)?(?:都)?(?:算上|计入|统计)|全部数据|全范围|所有(?:数据|记录)', question)
    money = re.search(r'销售总额|总销售额|销售额|销售金额|金额|收入|营收|\bsales\b|\brevenue\b', question, re.I)
    conclusion = re.search(r'先.{0,12}(?:结论|合计|总额).{0,12}再.{0,8}(?:明细|详情)', question)
    total = explicit or (whole if whole and money and conclusion else None)
    if not total:
        return None
    return {'preview_limit': cap, 'source_id': 'current', 'monetary_word_present': bool(money),
            'source_sha256': sha256(question.encode('utf-8')).hexdigest(),
            'evidence': [{'quote': m[0], 'start': m.start(), 'end': m.end()}
                         for m in (total, preview)]}


def validate_s1_total_preview(sql, catalog, source_question, *, brief='', user_history=(), enabled=False):
    """Prove only a complete total is visibly consumed, or reject a known preview.

    brief/history are intentionally not reinterpreted. Source/default/state and
    plan permissions remain with their existing owners. Unknown SQL yields NV.
    """
    result = {'status': 'not_verified', 'verified': False,
              'business_semantics_verified': False, 'source': 'actual_sql_total_preview_shape'}
    source = _source(source_question) if enabled is True else None
    if source is None:
        return {**result, 'reason': 'disabled_or_no_closed_current_total_and_preview_request'}
    result['source_evidence'] = source
    try:
        root = build_scope(_qualified(sql, catalog))
        if root is None or not isinstance(root.expression, exp.Select):
            raise _Unknown('non_select_root')
        proof = _complete(root, catalog, allow_count=not source['monetary_word_present'])
        if proof is not None:
            return {**result, 'status': 'verified', 'verified': True,
                    'sql_sha256': sha256(sql.encode('utf-8')).hexdigest(), 'proof': proof}
        # Unknown transformations are never treated as a missing known total.
        # Reject only the bounded plain row/aggregate family, including totals
        # whose underlying input was already limited.
        if _plain(root, set()) and _has_limit(root, set()):
            error = TotalPreviewIncomplete(
                '原问同时要求完整范围的合计结论和限行明细；当前 SQL 只证明限行预览/局部小计。'
                '请在最终可见输出中消费同一实际范围、截断前的独立完整聚合或无分区全范围窗口合计；'
                '未消费的 CTE、常量、分区小计及先 LIMIT 后 SUM 不能代替完整合计。'
                '本检查不选择金额公式、对象、期间、单位或默认。')
            error.total_preview_evidence = result
            raise error
        return {**result, 'reason': 'unsupported_or_not_proven_total_shape'}
    except TotalPreviewIncomplete:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError, SqlglotError):
        return {**result, 'reason': 'unsupported_or_not_proven_total_shape'}


def _selection(scope, name):
    if not isinstance(scope.expression, exp.Select):
        raise _Unknown()
    matches = [p for p in scope.expression.selects if p.alias_or_name == name]
    if len(matches) != 1:
        raise _Unknown()
    return matches[0]


def _resolve(node, scope, path=(), depth=0):
    if depth > 16:
        raise _Unknown()
    node = _un(node)
    if isinstance(node, exp.Round):
        return _resolve(node.this, scope, path, depth + 1)
    if isinstance(node, exp.Column):
        source = scope.selected_sources.get(node.table, (None, None))[1]
        if isinstance(source, Scope):
            return _resolve(_selection(source, node.name), source, path + (scope,), depth + 1)
    if isinstance(node, exp.Subquery):
        owners = [s for s in scope.subquery_scopes if s.expression is node.this]
        if len(owners) != 1 or len(node.this.selects) != 1:
            raise _Unknown()
        return _resolve(node.this.selects[0], owners[0], path + (scope,), depth + 1)
    return node, scope, path


def _field(node, scope, catalog, depth=0):
    if depth > 16:
        raise _Unknown()
    node = _un(node)
    if not isinstance(node, exp.Column):
        raise _Unknown()
    source = scope.selected_sources.get(node.table, (None, None))[1]
    if isinstance(source, exp.Table):
        table = catalog.get_table(source.name, source.db or 'public')
        if node.name not in table.column_names:
            raise _Unknown()
        return exp.column(node.name, table=table.name, db=table.schema)
    if isinstance(source, Scope):
        return _field(_selection(source, node.name), source, catalog, depth + 1)
    raise _Unknown()


def _measure(node, scope, catalog, depth=0, *, allow_count=False):
    """Additive actual fields, never aliases or constant-filled fake totals."""
    if depth > 16:
        return False
    node = _un(node)
    if isinstance(node, exp.Column):
        source = scope.selected_sources.get(node.table, (None, None))[1]
        if isinstance(source, Scope):
            if source.expression.args.get('having') or source.expression.args.get('distinct'):
                return False
            return _measure(_selection(source, node.name), source, catalog, depth + 1, allow_count=allow_count)
        _field(node, scope, catalog)
        return True
    if isinstance(node, (exp.Sum, exp.Count)):
        if isinstance(node, exp.Count) and not allow_count:
            return False
        if isinstance(node.this, exp.Distinct):
            return False
        if isinstance(node.this, exp.Star):
            return isinstance(node, exp.Count) and bool(_population(scope, catalog)[0])
        return _measure(node.this, scope, catalog, depth + 1, allow_count=allow_count)
    if isinstance(node, (exp.Mul, exp.Add, exp.Sub)):
        return (_measure(node.left, scope, catalog, depth + 1, allow_count=allow_count)
                and _measure(node.right, scope, catalog, depth + 1, allow_count=allow_count))
    return False


def _population(scope, catalog, ignored=frozenset(), active=frozenset()):
    """Exact bounded SQL rowset identity, not a user-population certificate."""
    if id(scope) in active or not isinstance(scope.expression, exp.Select):
        raise _Unknown()
    active = active | {id(scope)}
    query = scope.expression
    if any(query.args.get(k) for k in ('having', 'qualify', 'distinct', 'offset')):
        raise _Unknown()
    tables, predicates, limited = Counter(), Counter(), bool(query.args.get('limit'))
    for alias, (_, source) in scope.selected_sources.items():
        if alias in ignored:
            continue
        if isinstance(source, exp.Table):
            table = catalog.get_table(source.name, source.db or 'public')
            tables[(table.schema, table.name)] += 1
        elif isinstance(source, Scope):
            t, p, lim = _population(source, catalog, active=active)
            tables.update(t); predicates.update(p); limited |= lim
        else:
            raise _Unknown()
    if not tables or any(count != 1 for count in tables.values()):
        raise _Unknown()  # self joins require a richer instance proof
    conditions = [query.args.get('where')]
    for join in query.args.get('joins') or []:
        if join.alias_or_name in ignored:
            if join.args.get('on') or join.args.get('using') or join.side:
                raise _Unknown()
            continue
        if join.side or join.kind not in ('', 'INNER', 'CROSS') or join.args.get('using'):
            raise _Unknown()
        conditions.append(join.args.get('on'))
    def add(node):
        node = _un(node)
        if isinstance(node, exp.Where):
            node = _un(node.this)
        if node is None:
            return
        if isinstance(node, exp.And):
            add(node.left); add(node.right); return
        if any(isinstance(n, (exp.Query, exp.AggFunc, exp.Window)) for n in walk_in_scope(node)):
            raise _Unknown()
        copy = node.copy()
        for col in list(copy.find_all(exp.Column)):
            col.replace(_field(col, scope, catalog))
        predicates[copy.sql(dialect='postgres', normalize=True)] += 1
    for condition in conditions:
        add(condition)
    return tables, predicates, limited


def _complete(root, catalog, *, allow_count):
    for index, projection in enumerate(root.expression.selects):
        try:
            node, owner, path = _resolve(projection, root)
            if isinstance(node, exp.Window):
                # Post-window predicates change the surviving detail population;
                # a copied pre-filter window is not a newly proved full total.
                if any(p.expression.args.get('where') or p.expression.args.get('group')
                       or p.expression.args.get('having') for p in path):
                    continue
                if (node.args.get('partition_by') or node.args.get('order') or node.args.get('spec')
                        or not isinstance(node.this, (exp.Sum, exp.Count))):
                    continue
                total = node.this
                tables, predicates, _ = _population(owner, catalog)
                if (tables, predicates) != _population(root, catalog)[:2]:
                    continue  # a later join cannot borrow a sibling rowset total
                # This scope's own LIMIT runs after its window. Lower LIMITs do not.
                if any(isinstance(s, Scope) and _population(s, catalog)[2]
                       for _, s in owner.selected_sources.values()):
                    continue
                if _measure(total, owner, catalog, allow_count=allow_count):
                    return {'kind': 'consumed_unpartitioned_window_before_preview_limit',
                            'output_index': index, 'population_is_sql_local_only': True}
            elif isinstance(node, (exp.Sum, exp.Count)):
                if owner.expression.args.get('group') or owner.expression.args.get('limit'):
                    continue
                total_population = _population(owner, catalog)
                if total_population[2] or not _measure(node, owner, catalog, allow_count=allow_count):
                    continue
                ignored = frozenset(alias for alias, (_, s) in root.selected_sources.items() if s is owner)
                preview_population = _population(root, catalog, ignored=ignored)
                if total_population[:2] == preview_population[:2]:
                    return {'kind': 'consumed_independent_unlimited_scalar_aggregate',
                            'output_index': index, 'population_is_sql_local_only': True}
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            continue
    return None


def _has_limit(scope, active):
    if id(scope) in active:
        return False
    active = active | {id(scope)}
    return bool(scope.expression.args.get('limit')) or any(
        _has_limit(source, active) for _, source in scope.selected_sources.values()
        if isinstance(source, Scope))


def _plain(scope, active):
    """Finite known preview shape; opaque SQL remains not_verified."""
    if id(scope) in active or not isinstance(scope.expression, exp.Select):
        return False
    active = active | {id(scope)}
    if any(scope.expression.args.get(k) for k in ('having', 'qualify', 'distinct', 'offset')):
        return False
    if scope.expression.args.get('where') and any(
            isinstance(source, Scope) and any(isinstance(n, exp.Window)
                for n in walk_in_scope(source.expression))
            for _, source in scope.selected_sources.values()):
        return False  # post-window filtering needs a separate population proof
    if any(isinstance(n, exp.Func) and not isinstance(n, (
            exp.Sum, exp.Count, exp.Round, exp.And, exp.Or, exp.Window))
           or isinstance(n, (exp.Case, exp.Filter, exp.Union, exp.Intersect, exp.Except))
           or isinstance(n, exp.Subquery) and not isinstance(n.parent, (exp.From, exp.Join))
           for n in walk_in_scope(scope.expression)):
        return False
    return bool(scope.selected_sources) and all(
        isinstance(source, exp.Table) or isinstance(source, Scope) and _plain(source, active)
        for _, source in scope.selected_sources.values())
