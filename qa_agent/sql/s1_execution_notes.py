"""Display facts about executed S1 SQL; never grant or commit conditions.

The real question, user material and existing policy are provenance, not Gold.
Unknown lineage or policy applicability is left unverified.  The caller must
enable this only for component 1 with the component-3 gate disabled.
"""
from __future__ import annotations

from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import Scope, traverse_scope

from qa_agent.sql.business_knowledge import business_knowledge
from qa_agent.sql.projection_semantics import transparent
from qa_agent.sql.query_basis import describe_query_basis
from qa_agent.sql.repair_guard import _qualified


_PERIOD = re.compile(r'20\d{2}|去年|今年|明年|上年|本年|前年|上月|本月|这月|季度|期间|时期|旺季|淡季|半年|月份|最近|截至|截止|日期|时间范围|时间限制|时间筛选|全部数据|所有数据|所有年份|全部年份|不限时间|不限期间')
_UNCERTAIN = re.compile(r'例如|比如|示例|假设|如果|不要|不用|无需|无须|不必|不是|不需要|别(?:按|用|算|查|将|把|改|默认|统计|使用)|[“”"\'‘’]')
_CUSTOMER = re.compile(r'客户|顾客|消费者')
_RANKING = re.compile(r'最多|最高|排名|排行|前\s*\d+|最能|最高的|分别是谁')
_COUNTER_METRIC = re.compile(r'人数|客户数|数量|件数|首数|张数|发票数|购买次数|订单数|平均|人均|单价|时长|销售明细|明细金额|曲目金额')
_BUY_MOST = re.compile(r'买得最多|购买最多|消费最多|花钱最多|消费(?:金额)?最高|开票(?:金额|额)最高')
_CONTRARY_RANK = re.compile(
    r'(?:买得最多|消费排名|客户排名|顾客排名).{0,18}(?:按|依据|使用).{0,12}'
    r'(?:数量|次数|张数|单价|平均|人均|人数|客户数|明细|曲目)'
    r'|(?:不要|不用|禁止|取消|不是)(?:采用|使用|按|沿用)?'
    r'(?:金额(?:口径|排名|统计)?|发票金额|全部现有数据|全部数据)'
    r'|(?:不要|不用|禁止|取消)(?:采用|使用|沿用)?(?:任何|全部|所有)?'
    r'默认(?:口径|规则)?(?=[。；;\n]|$)')


def _user_text(history):
    texts = []
    for item in history or ():
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict) and (item.get('role') == 'user' or isinstance(item.get('user'), str)):
            # ContextStore.record stores {user, assistant, sql}, whereas API
            # message histories may use {role, content}. Only real user text
            # is authority; SQL and assistant prose must never supply defaults.
            value = item.get('user') if isinstance(item.get('user'), str) else item.get('content', item.get('message', ''))
            if isinstance(value, str):
                texts.append(value)
    return '\n'.join(texts)


def _policies():
    rows = [row for row in (business_knowledge() or {}).get('references', ())
            if row.get('source_id') == 'project:existing_authorized_defaults']
    if len(rows) != 1:
        return None
    row = rows[0]
    if not row.get('authorization_source') or not re.fullmatch(r'[0-9a-f]{64}', str(row.get('sha256', ''))):
        return None
    return row


def _physical(node, scope):
    node = transparent(node)
    if not isinstance(node, exp.Column):
        return None
    source = scope.sources.get(node.table)
    if isinstance(source, exp.Table):
        return source.db or 'public', source.name, node.name
    return None


def _resolve(node, scope, depth=0):
    node = transparent(node)
    if depth > 12:
        return None, scope
    if isinstance(node, exp.Round):
        return _resolve(node.this, scope, depth + 1)
    if isinstance(node, exp.Column):
        source = scope.sources.get(node.table)
        if isinstance(source, Scope) and isinstance(source.expression, exp.Select):
            matches = [p for p in source.expression.selects if p.alias_or_name == node.name]
            if len(matches) == 1:
                return _resolve(matches[0], source, depth + 1)
        if not node.table:
            matches = [p for p in scope.expression.selects if p.alias and p.alias == node.name]
            if len(matches) == 1:
                return _resolve(matches[0], scope, depth + 1)
    return node, scope


def _customer_amount(node, scope):
    node, owner = _resolve(node, scope)
    if not isinstance(node, exp.Sum) or _physical(node.this, owner) != ('public', 'invoice', 'total'):
        return False
    group = owner.expression.args.get('group')
    return bool(group and any(_physical(value, owner) in {
        ('public', 'invoice', 'customer_id'), ('public', 'customer', 'customer_id')
    } for value in group.expressions))


def _consumed_scopes(root):
    reached, pending = [], [root]
    while pending:
        scope = pending.pop()
        if any(scope is previous for previous in reached):
            continue
        reached.append(scope)
        pending.extend(source for _, source in scope.selected_sources.values() if isinstance(source, Scope))
        # Scalar subqueries actually used in projections/filters are consumers;
        # unused CTE definitions are deliberately not evidence.
        pending.extend(scope.subquery_scopes)
    return reached


def describe_s1_execution_notes(question, sql, columns, table, *, catalog,
                                brief='', user_history=(), enabled=False,
                                output_scope=None, existing_query_basis=None):
    """Return structured, display-only notes, or None; never mutate inputs.

    SQL must already have been validated and executed. ``table`` is accepted
    for the public presentation boundary, but values never choose a rule or
    prove that a cutoff has no tied following row. Policy applicability and
    actual SQL behavior are separate fields.  No model/database calls occur.
    """
    if enabled is not True or getattr(catalog, 'database', None) != 'chinook':
        return None
    if not all(isinstance(value, str) for value in (question, sql, brief)) or not sql.strip():
        return None
    try:
        tree = _qualified(sql, catalog)
        scopes = list(traverse_scope(tree))
        root = next(scope for scope in scopes if scope.parent is None)
        if not isinstance(root.expression, exp.Select):
            return None
        consumed = _consumed_scopes(root)
        if any(not isinstance(scope.expression, exp.Select) for scope in consumed):
            return None
        notes = []
        policy_source = _policies()
        defaults = (policy_source or {}).get('authorized_defaults') or {}
        provenance = {'source_id': (policy_source or {}).get('source_id'),
                      'path': (policy_source or {}).get('path'),
                      'sha256': (policy_source or {}).get('sha256')}
        source_text = '\n'.join((question, brief, _user_text(user_history)))
        ranking = bool(_CUSTOMER.search(question) and _RANKING.search(question))
        customer_amount = False
        ranking_orders = []
        for scope in consumed:
            query = scope.expression
            order = query.args.get('order')
            if order and order.expressions:
                first = order.expressions[0]
                if first.args.get('desc') is True and _customer_amount(first.this, scope):
                    customer_amount = True
                    ranking_orders.append((scope, order, None))
            for window in (value for value in query.find_all(exp.Window)
                           if value.find_ancestor(exp.Select) is query):
                order = window.args.get('order')
                if (isinstance(window.this, (exp.RowNumber, exp.Rank, exp.DenseRank))
                        and order and order.expressions and order.expressions[0].args.get('desc') is True
                        and _customer_amount(order.expressions[0].this, scope)):
                    customer_amount = True
                    ranking_orders.append((scope, order, window))
        safe_question = not _UNCERTAIN.search(question)
        metric_counter = bool(_COUNTER_METRIC.search(question))
        money_policy = defaults.get('who_buys_most')
        if (ranking and customer_amount and safe_question and not metric_counter
                and not _CONTRARY_RANK.search(source_text)
                and _BUY_MOST.search(question) and isinstance(money_policy, dict)
                and money_policy.get('object') == 'customer' and money_policy.get('metric') == 'invoice_revenue'):
            notes.append({'kind': 'customer_amount_basis', 'policy_id': 'oct12.customer.amount',
                          'policy_source': provenance, 'applicability': 'actual_customer_invoice_sum_ranking',
                          'text': '口径说明：本次“买得最多/消费最高”按每位客户的发票金额合计比较，采用既有客户金额口径；可指定购买数量等其他口径后重新查询。'})
        if ranking and customer_amount:
            # Any temporal predicate in a consumed scope prevents claiming an
            # unfiltered period, including dates hidden behind CTE columns.
            date_columns = {column.name.lower() for entry in catalog.tables for column in entry.columns
                            if 'date' in column.data_type.lower() or 'timestamp' in column.data_type.lower()}
            predicates = [scope.expression.args.get(key) for scope in consumed for key in ('where', 'having', 'qualify')]
            predicates += [join.args.get('on') for scope in consumed for join in scope.expression.args.get('joins') or []]
            date_filter = any(column.name.lower() in date_columns
                              for scope in consumed for column in scope.columns)
            # A literal date or runtime date function may be a hidden temporal
            # dependency. Be conservative rather than assert full coverage.
            date_filter = date_filter or any(
                re.search(r'\b20\d{2}-\d{2}-\d{2}\b', part.sql(dialect='postgres'))
                or part.find(exp.CurrentDate) or part.find(exp.CurrentTimestamp)
                for part in predicates if part is not None)
            if not date_filter:
                period = defaults.get('missing_period')
                applicable = (safe_question and not _PERIOD.search(source_text)
                              and not _CONTRARY_RANK.search(source_text)
                              and not metric_counter and isinstance(period, dict)
                              and 'customer_ranking' in period.get('objects', ())
                              and period.get('scope') == 'all_existing_data'
                              and period.get('preserve_confirmed_period') is True)
                notes.append({'kind': 'executed_period_scope',
                    'policy_id': 'oct12.period.all_data' if applicable else None,
                    'policy_source': provenance if applicable else None,
                    'applicability': 'existing_missing_period_customer_ranking_policy' if applicable else 'not_verified',
                    'text': ('期间说明：本次客户排名未加期间筛选，依既有缺期间客户排名政策使用全部现有数据；如需特定期间，可指定后重新查询。'
                             if applicable else '实际查询说明：本次客户排名未加期间筛选；这不代表已有期间约定已被取消。如需按原期间或其他期间查询，请明确指定。')})
        # Describe only the order/window that is actually consumed. An unused
        # ROW_NUMBER or top-N CTE must not manufacture a tie policy statement.
        for scope, order, window in ranking_orders:
            identifier_tie = False
            for value in order.expressions[1:]:
                node, owner = _resolve(value.this, scope)
                if _physical(node, owner) in {('public', 'customer', 'customer_id'), ('public', 'invoice', 'customer_id')}:
                    identifier_tie = not bool(value.args.get('desc'))
            if window is not None:
                name = type(window.this).__name__
                sql_name = {'RowNumber': 'ROW_NUMBER', 'Rank': 'RANK', 'DenseRank': 'DENSE_RANK'}[name]
                text = ('排序说明：实际SQL在金额相同时按客户编号升序排列。' if identifier_tie else '')
                text += ('本次使用逐行编号（ROW_NUMBER），并列金额也分配不同序号。'
                         if isinstance(window.this, exp.RowNumber) else
                         (f'本次使用{sql_name}，仅按金额排序，相同金额保留同一名次；筛选名次可能返回多于指定名次数的客户。'
                          if len(order.expressions) == 1 else
                          f'本次使用{sql_name}，仅完整ORDER BY排序键一致时保留同一名次；金额相同但其他排序键不同的客户可能分配不同名次。'))
                notes.append({'kind': 'executed_ranking_behavior', 'window': name,
                              'order_key_count': len(order.expressions),
                              'text': text, 'following_row_checked': False})
            elif scope.expression.args.get('limit') is not None:
                limit = scope.expression.args['limit'].expression
                if isinstance(limit, exp.Literal) and not limit.is_string and str(limit.this).isdigit():
                    notes.append({'kind': 'executed_ranking_behavior', 'limit': int(limit.this),
                        'following_row_checked': False,
                        'text': ('排序说明：实际SQL在金额相同时按客户编号升序排列；' if identifier_tie else '排序说明：')
                                + f'本次查询最多取前{limit.this}行，未额外查询边界之后是否仍有同金额客户。'})
        basis = None if existing_query_basis else describe_query_basis(sql, columns, catalog=catalog)
        if basis:
            notes.append({'kind': 'executed_ratio_basis', 'text': basis['text'],
                          'source': basis['source'], 'columns': basis['columns']})
        if isinstance(output_scope, dict) and (output_scope.get('cursor_truncated') is True
                or output_scope.get('possibly_incomplete_enumeration') is True):
            notes.append({'kind': 'executed_response_scope',
                          'text': '结果范围：本次响应受到行数限制，返回行数不等于全部符合条件的记录数。'})
        unique = {note['text']: note for note in notes}
        if not unique:
            return None
        return {'source': 'program:actual_s1_sql_display_notes',
                'sql_sha256': sha256(sql.encode()).hexdigest(),
                'question_sha256': sha256(question.encode()).hexdigest(),
                'brief_sha256': sha256(brief.encode()).hexdigest(),
                'user_history_sha256': sha256(_user_text(user_history).encode()).hexdigest(),
                'notes': list(unique.values()), 'text': '\n'.join(unique),
                'display_only': True, 'state_committed': False,
                'business_correctness_asserted': False}
    except (ValueError, TypeError, KeyError, AttributeError, StopIteration, SqlglotError):
        return None
