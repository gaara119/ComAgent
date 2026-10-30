"""Virtual display ranks from an actual complete SQL window prefix.

Never edits SQL/rows, selects a business population, or reads evaluation data.
Unknown lineage, hidden ordering precision and incomplete output stay unverified.
"""
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import Scope, build_scope, walk_in_scope
from qa_agent.sql.repair_guard import _qualified


def _un(node):
    while isinstance(node, (exp.Alias, exp.Paren)):
        node = node.this
    return node


def _resolve(node, scope, depth=0):
    if depth > 6:
        raise ValueError('lineage_depth')
    node = _un(node)
    if not isinstance(node, exp.Column):
        return node, scope
    if not node.table:
        aliases = [p for p in scope.expression.selects
                   if isinstance(p, exp.Alias) and p.alias == node.name]
        if len(aliases) == 1:
            return _resolve(aliases[0].this, scope, depth + 1)
    selected = scope.selected_sources.get(node.table)
    if selected and isinstance(selected[1], Scope):
        child = selected[1]
        projections = [p for p in child.expression.selects if p.alias_or_name == node.name]
        if len(projections) != 1:
            raise ValueError('ambiguous_projection')
        return _resolve(projections[0], child, depth + 1)
    return node, scope


def _key(node, scope):
    node, owner = _resolve(node, scope)
    return node.sql(dialect='postgres'), id(owner)


def _numeric(node, scope, catalog):
    node, owner = _resolve(node, scope)
    if isinstance(node, exp.Count):
        target = _un(node.this)
        return isinstance(target, (exp.Column, exp.Star, exp.Distinct))
    if isinstance(node, (exp.Sum, exp.Avg)):
        return isinstance(_un(node.this), exp.Column) and _numeric(node.this, owner, catalog)
    if not isinstance(node, exp.Column):
        return False
    selected = owner.selected_sources.get(node.table)
    if not selected or not isinstance(selected[1], exp.Table):
        return False
    physical = selected[1]
    column = next(c for c in catalog.get_table(physical.name, physical.db or 'public').columns
                  if c.name == node.name)
    return bool(re.match(r'^(?:smallint|integer|bigint|numeric|decimal|real|double precision)\b',
                         column.data_type, re.I))


def _source(question, brief, history):
    if not isinstance(question, str) or not isinstance(brief, str):
        return None
    if re.search(r'例如|比如|示例|假设|引用|不要.{0,10}(?:名次|排名|序号)|'
                 r'(?:不用|不需要|无需|无须|不列|别列).{0,8}(?:名次|排名|序号)|'
                 r'(?:名次|排名|序号).{0,6}(?:不要|不用|不需要|无需|无须|不列)', question):
        return None
    restricted = re.search(r'(?:只|仅)(?:要|给|显示|输出|返回|保留|列)'
                           r'[^。；;\n]{0,50}(?:姓名|名字|金额|数值)', question)
    if restricted and not re.search(r'名次|序号', restricted.group()):
        return None
    sources = [('current', question), ('brief', brief)]
    # Old one-off requests do not become persistent display policy.
    for i, turn in enumerate(history if isinstance(history, (list, tuple)) else ()):
        if isinstance(turn, dict) and turn.get('role') in (None, 'user'):
            user = turn.get('user') or turn.get('content')
            if isinstance(user, str) and re.search(r'以后|接下来所有|从现在起', user):
                sources.append((f'user_history_{i + 1}', user))
    if any(re.search(r'(?:SQL|查询结果|数据库结果).{0,20}(?:必须|包含|输出|返回|列).{0,10}'
                     r'(?:名次|rank|排名)|(?:名次|rank|排名).{0,15}必须.{0,10}(?:SQL|查询列)', t, re.I)
           for _, t in sources):
        return None
    if not re.search(r'排名|排行|前\s*[0-9一二两三四五六七八九十]+\s*(?:名|位)', question):
        return None
    for source_id, text in sources:
        for m in re.finditer(r'[^。\n]*(?:名次|序号)[^。\n]*', text):
            quote = m.group()
            if re.search(r'不要|不用|无需|不需要|例如|示例|假设|引用', quote):
                continue
            if re.search(r'列|写|显示|展示|给', quote):
                return {'source_id': source_id, 'quote': quote, 'span': list(m.span()),
                        'source_sha256': sha256(text.encode()).hexdigest()}
    return None


def _stable_order_ordinal(sql, table, catalog, question, brief, history, boundary, original_sql, visible_source):
    """One source-authorized customer prefix, not competition/dense ranking."""
    def no(reason):
        return {'status': 'not_verified', 'reason': reason,
                'business_semantics_verified': False, 'SQL_and_rows_mutated': False}
    if '客户' not in question or re.search(r'并列|竞争|稠密|RANK|DENSE_RANK', question, re.I):
        return no('not_one_customer_stable_ordinal_request')
    users = [turn if isinstance(turn, str) else turn.get('user', turn.get('content', ''))
             for turn in history if isinstance(turn, str) or isinstance(turn, dict)
             and turn.get('role') in (None, 'user')] if isinstance(history, (tuple, list)) else []
    # A generic stable policy in the brief cannot choose the PK rule over an
    # actual user prohibition or another explicit ordering instruction. Its
    # lifecycle/meaning is not inferred here: unresolved precedence stays NV.
    ordering_override = re.compile(
        r'(?:不允许|禁止|不能|不要|不需要|不用|无需|无须|不必|别|取消|不采用|不使用)'
        r'[^。；;\n]{0,28}(?:稳定|截取|截断|取前|按编号)|'
        r'(?:同分|同值|指标相同|金额相同|数值相同|分数相同)'
        r'[^。；;\n]{0,40}(?:按|排序|排列|次序|顺序|先|后)|'
        r'(?:按|按照|依照)[^。；;\n]{0,28}(?:排序|排列|升序|降序|次序|顺序|从少到多|从小到大|从高到低|从大到小|列出)|'
        r'(?:改为|改用|另用)[^。；;\n]{0,16}(?:排序|次序|规则)|'
        r'\bORDER\s+BY\b|\btie[- ]?break', re.I)
    if any(ordering_override.search(text) for text in [question] +
           [t for t in users if isinstance(t, str)]):
        return no('explicit_actual_user_ordering_or_selection_policy_not_inferred')
    if any(re.search(r'全部并列|所有并列|保留并列|并列名次|竞争排名|稠密排名|DENSE_RANK|\bRANK\b',
                     text, re.I) for text in [brief] + [t for t in users if isinstance(t, str)]):
        return no('explicit_competing_tie_policy_not_overridden')
    policy = None
    for source_id, text in [('current', question), ('brief', brief)]:
        for match in re.finditer(r'(?:允许|可以)你?按(?:一条)?稳定的?规则(?:处理|排序|截取)'
                r'[^。\n]{0,30}(?:说明|说出来|披露)[^。\n]{0,15}(?:规则|方式)', text):
            left = max(text.rfind('。', 0, match.start()), text.rfind('\n', 0, match.start())) + 1
            if re.search(r'不允许|不可以|禁止|不能|不要|不用|不是|不采用|未确认|示例|例如|举例|假设|引用',
                         text[left:match.end()]):
                continue
            policy = {'source_id': source_id, 'quote': match.group(),
                'span': list(match.span()), 'source_sha256': sha256(text.encode()).hexdigest()}
    numbers = {'一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
               '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    sizes = [int(x) if x.isdigit() else numbers.get(x)
             for x in re.findall(r'前\s*(\d+|[一二两三四五六七八九十])\s*(?:名|位)', question)]
    if not policy or not sizes or None in sizes or len(set(sizes)) != 1:
        return no('no_single_source_authorized_stable_TopN')
    n = sizes[0]
    if (not isinstance(table, list) or not table or not all(isinstance(r, dict) for r in table)
            or not isinstance(boundary, dict) or type(boundary.get('row_count')) is not int
            or boundary['row_count'] != len(table) or type(boundary.get('response_cap')) is not int
            or not 0 < len(table) <= n < boundary['response_cap']
            or boundary.get('program_added_limit') is not False
            or boundary.get('cursor_truncated') is not False
            or boundary.get('possibly_incomplete_enumeration') is not False
            or not isinstance(original_sql, str)
            or sha256(original_sql.encode()).hexdigest() != boundary.get('original_sql_sha256')):
        return no('stable_prefix_original_or_actual_output_not_proved')
    try:
        actual = sqlglot.parse_one(sql, read='postgres')
        original = sqlglot.parse_one(original_sql, read='postgres')
        if actual.sql(dialect='postgres') != original.sql(dialect='postgres'):
            return no('stable_prefix_original_SQL_differs')
        tree = _qualified(sql, catalog)
        scope = build_scope(tree)
        limit = tree.args.get('limit')
        if (not isinstance(tree, exp.Select) or scope is None or limit is None
                or not isinstance(limit.expression, exp.Literal) or limit.expression.is_string
                or str(limit.expression.this) != str(n) or limit.args.get('limit_options')
                or boundary.get('original_limit') != limit.sql(dialect='postgres')
                or any(tree.args.get(k) for k in ('offset', 'distinct', 'having', 'qualify'))
                or any(isinstance(node, (exp.Window, exp.Subquery, exp.With)) for node in tree.walk())):
            return no('not_one_direct_unmodified_ordinal_prefix')
        sources = {alias: src for alias, (_, src) in scope.selected_sources.items()}
        if (catalog.database != 'chinook' or len(sources) != 2
                or any(not isinstance(t, exp.Table) or (t.db or 'public') != 'public' for t in sources.values())
                or sorted(t.name for t in sources.values()) != ['customer', 'invoice']):
            return no('not_direct_customer_invoice_scope')
        customer = next(alias for alias, t in sources.items() if t.name == 'customer')
        invoice = next(alias for alias, t in sources.items() if t.name == 'invoice')
        ctable = catalog.get_table('customer'); itable = catalog.get_table('invoice')
        if len(ctable.primary_key) != 1:
            return no('unsupported_customer_catalog_PK')
        pk = ctable.primary_key[0]
        foreign = [f for f in itable.foreign_keys if f.get('references', {}).get('table') == 'customer'
            and f.get('references', {}).get('schema', 'public') == 'public'
            and tuple(f['references'].get('columns', ())) == ctable.primary_key]
        joins = tree.args.get('joins') or []
        if len(foreign) != 1 or len(foreign[0].get('columns', ())) != 1 or len(joins) != 1:
            return no('no_unique_real_invoice_customer_FK')
        join = joins[0]; on = _un(join.args.get('on'))
        required = {(invoice, foreign[0]['columns'][0]), (customer, pk)}
        if (join.side or join.kind not in ('', 'INNER') or not isinstance(on, exp.EQ)
                or not all(isinstance(c, exp.Column) for c in (on.left, on.right))
                or {(on.left.table, on.left.name), (on.right.table, on.right.name)} != required):
            return no('wrong_or_non_unique_customer_invoice_rowset')
        group = list((tree.args.get('group') or exp.Group()).expressions)
        if (not group or any(not isinstance(c, exp.Column) or c.table != customer
                or c.name not in ctable.column_names for c in group)
                or pk not in {c.name for c in group}):
            return no('not_one_native_customer_PK_group')
        order = list((tree.args.get('order') or exp.Order()).expressions)
        if len(order) != 2 or order[0].args.get('desc') is not True or order[1].args.get('desc'):
            return no('not_metric_desc_customer_PK_asc')
        measure, owner = _resolve(order[0].this, scope)
        tie, _ = _resolve(order[1].this, scope)
        target = _un(measure.this) if isinstance(measure, (exp.Sum, exp.Count)) else None
        if not ((isinstance(measure, exp.Sum) and isinstance(target, exp.Column)
                 and target.table == invoice and target.name == 'total')
                or (isinstance(measure, exp.Count) and (isinstance(target, exp.Star)
                    or isinstance(target, exp.Column) and target.table == invoice
                    and target.name in itable.primary_key))):
            return no('not_supported_native_invoice_numeric_measure')
        if not isinstance(tie, exp.Column) or (tie.table, tie.name) != (customer, pk):
            return no('not_complete_real_customer_PK_tie_breaker')
        outputs = {}
        for p in tree.selects:
            if re.search(r'^rank$|^rnk$|^rn$|名次', p.alias_or_name, re.I):
                return no('actual_rank_already_projected')
            value = _un(p)
            if isinstance(value, exp.Column):
                allowed = value.table == customer and value.name in ctable.column_names
            elif _key(value, scope) == _key(measure, owner):
                allowed = True
            elif isinstance(value, exp.DPipe):
                leaves = []
                def parts(node):
                    node = _un(node)
                    if isinstance(node, exp.DPipe):
                        parts(node.left); parts(node.right)
                    else:
                        leaves.append(node)
                parts(value)
                fields = [(x.table, x.name) for x in leaves if isinstance(x, exp.Column)]
                allowed = (len(fields) == 2 and set(fields) ==
                    {(customer, 'first_name'), (customer, 'last_name')}
                    and all(isinstance(x, exp.Column) or isinstance(x, exp.Literal)
                        and x.is_string and 0 < len(x.this) <= 8
                        and all(c.isspace() or c in ',.-·' for c in x.this) for x in leaves))
            else:
                allowed = False
            if not allowed:
                return no('unknown_or_transformed_customer_projection')
            outputs.setdefault(_key(p, scope), []).append(p.alias_or_name)
        identities = [_key(measure, owner), _key(tie, scope)]
        if any(len(outputs.get(k, [])) != 1 for k in identities):
            return no('raw_metric_or_customer_PK_not_uniquely_projected')
        names = [outputs[k][0] for k in identities]
        previous = None; seen = set()
        for row in table:
            if any(name not in row or row[name] is None or isinstance(row[name], bool)
                   or not isinstance(row[name], (str, int, Decimal)) for name in names):
                return no('missing_or_unknown_numeric_keys')
            values = tuple(Decimal(row[name]) for name in names)
            if any(not v.is_finite() for v in values) or values[1] in seen:
                return no('nonfinite_metric_or_nonunique_customer_PK')
            if previous is not None and not (previous[0] > values[0]
                    or previous[0] == values[0] and previous[1] < values[1]):
                return no('actual_rows_not_in_proved_stable_order')
            previous = values; seen.add(values[1])
        return {'status': 'verified_SQL_ranking_display_only', 'rank_kind': 'SQLOrderOrdinal',
            'mode': 'source_authorized_stable_customer_prefix', 'prefix_bound': n,
            'virtual_ranks': [{'row_index': i, 'rank': i + 1, 'partition_values': []} for i in range(len(table))],
            'source': visible_source, 'stable_order_source': policy,
            'catalog_PK': {'table': 'public.customer', 'columns': list(ctable.primary_key)},
            'actual_order': [x.sql(dialect='postgres') for x in order],
            'order_output_columns': names, 'partition_output_columns': [],
            'tie_breaker_text': f'按实际指标从高到低排列；指标相同时按客户编号升序选取前{n}位。名次为该稳定次序的位置。',
            'actual_SQL_sha256': sha256(sql.encode()).hexdigest(),
            'actual_table_sha256': sha256(json.dumps(table, ensure_ascii=False, sort_keys=True,
                default=str, separators=(',', ':')).encode()).hexdigest(),
            'business_semantics_verified': False, 'complete_business_population_proved': False,
            'SQL_and_rows_mutated': False}
    except (ValueError, TypeError, KeyError, StopIteration, InvalidOperation, SqlglotError, AttributeError):
        return no('unresolved_stable_ordinal_structure')


def build_ranking_display(sql, table, *, catalog, source_question, brief='',
                          user_history=(), output_scope=None, original_sql=None):
    """Return virtual ranks/provenance or not_verified; never modifies inputs.

    Initial finite support: one consumed window SELECT with at most two
    transparent outer SELECTs; one <=N/<N/=1 window-prefix predicate; identical
    final partition+window ordering; numeric raw ordering/partition keys.
    """
    def no(reason):
        return {'status': 'not_verified', 'reason': reason,
                'business_semantics_verified': False, 'SQL_and_rows_mutated': False}
    source = _source(source_question, brief, user_history)
    if source is None:
        return no('no_applicable_visible_rank_source_or_SQL_column_required')
    if isinstance(output_scope, dict) and output_scope.get('original_limit') is not None:
        return _stable_order_ordinal(sql, table, catalog, source_question, brief,
            user_history, output_scope, original_sql, source)
    if (not isinstance(table, list) or not table or not all(isinstance(r, dict) for r in table)
            or not isinstance(output_scope, dict)
            or type(output_scope.get('row_count')) is not int
            or output_scope.get('row_count') != len(table)
            or type(output_scope.get('response_cap')) is not int
            or output_scope['response_cap'] < len(table)
            or output_scope.get('cursor_truncated') is not False
            or output_scope.get('possibly_incomplete_enumeration') is not False
            or type(output_scope.get('program_added_limit')) is not bool
            or output_scope.get('original_limit') is not None):
        return no('output_completeness_not_proved')
    try:
        proof_sql = sql
        cap_evidence = None
        if output_scope['program_added_limit']:
            # A program cap is transparent only with the actual original SQL,
            # its backend scope hash and a fully exhausted below-cap result.
            if (len(table) >= output_scope['response_cap']
                    or not isinstance(original_sql, str)
                    or sha256(original_sql.encode()).hexdigest() != output_scope.get('original_sql_sha256')):
                return no('program_cap_original_or_exhaustion_not_proved')
            original = sqlglot.parse_one(original_sql, read='postgres')
            executed = sqlglot.parse_one(sql, read='postgres')
            limit = executed.args.get('limit')
            if (not isinstance(original, exp.Select) or not isinstance(executed, exp.Select)
                    or original.args.get('limit') is not None
                    or original.args.get('offset') is not None
                    or executed.args.get('offset') is not None
                    or limit is None or limit.args.get('limit_options') is not None
                    or not isinstance(limit.expression, exp.Literal) or limit.expression.is_string
                    or str(limit.expression.this) != str(output_scope['response_cap'])):
                return no('not_the_exact_backend_root_cap')
            uncapped = executed.copy()
            uncapped.set('limit', None)
            if uncapped.sql(dialect='postgres') != original.sql(dialect='postgres'):
                return no('program_cap_is_not_the_only_original_SQL_change')
            proof_sql = uncapped.sql(dialect='postgres')
            cap_evidence = {'source': 'backend_original_SQL_and_exhausted_result',
                'original_SQL_sha256': output_scope['original_sql_sha256'],
                'program_root_limit': output_scope['response_cap'],
                'actual_row_count': len(table), 'cursor_truncated': False,
                'possibly_incomplete_enumeration': False}
        tree = _qualified(proof_sql, catalog)
        root = build_scope(tree)
        if root is None or not isinstance(tree, exp.Select):
            return no('not_a_SELECT')
        scope = root
        outer = []
        while True:
            windows = [n for p in scope.expression.selects for n in walk_in_scope(p)
                       if isinstance(n, exp.Window)]
            if windows:
                break
            if len(outer) >= 2 or len(scope.selected_sources) != 1:
                return no('no_unique_consumed_window_scope')
            if any(scope.expression.args.get(k) for k in ('group', 'having', 'qualify',
                    'distinct', 'limit', 'offset', 'joins')):
                return no('nontransparent_outer_scope')
            outer.append(scope)
            child = next(iter(scope.selected_sources.values()))[1]
            if not isinstance(child, Scope):
                return no('no_real_window_lineage')
            scope = child
        if (len(windows) != 1 or not outer or any(scope.expression.args.get(k)
                for k in ('limit', 'offset', 'qualify', 'distinct'))):
            return no('not_one_unlimited_consumed_window')
        window = windows[0]
        if not isinstance(window.this, (exp.RowNumber, exp.Rank, exp.DenseRank)):
            return no('unsupported_window_kind')
        orders = list((window.args.get('order') or exp.Order()).expressions)
        partitions = list(window.args.get('partition_by') or [])
        if not orders or any(not isinstance(_un(p), exp.Column) for p in partitions):
            return no('unknown_window_keys')
        window_key = _key(window, scope)
        if any(_key(p, root) == window_key for p in tree.selects):
            return no('actual_rank_already_projected')
        prefix = None
        for owner in outer:
            where = owner.expression.args.get('where')
            if where is None:
                continue
            condition = _un(where.this)
            if prefix is not None or not isinstance(condition, (exp.LTE, exp.LT, exp.EQ)):
                return no('not_one_complete_rank_prefix')
            if _key(condition.left, owner) != window_key:
                return no('post_window_filter_is_not_rank_prefix')
            bound = _un(condition.right)
            if not isinstance(bound, exp.Literal) or bound.is_string or not str(bound.this).isdigit():
                return no('nonliteral_rank_prefix')
            n = int(bound.this)
            if isinstance(condition, exp.LT):
                n -= 1
            if n < 1 or isinstance(condition, exp.EQ) and n != 1:
                return no('rank_prefix_has_holes')
            prefix = n
        if prefix is None:
            return no('window_prefix_filter_missing')
        partition_keys = [_key(n, scope) for n in partitions]
        order_keys = [_key(n.this, scope) for n in orders]
        final = list((tree.args.get('order') or exp.Order()).expressions)
        if (len(final) != len(partitions) + len(orders)
                or [_key(n.this, root) for n in final] != partition_keys + order_keys
                or any(bool(a.args.get('desc')) != bool(b.args.get('desc'))
                       or bool(a.args.get('nulls_first')) != bool(b.args.get('nulls_first'))
                       for a, b in zip(final[len(partitions):], orders))):
            return no('final_order_not_same_partition_window_order')
        outputs = {}
        for p in tree.selects:
            outputs.setdefault(_key(p, root), []).append(p.alias_or_name)
        keys = partitions + [n.this for n in orders]
        names = []
        for key in keys:
            identity = _key(key, scope)
            if len(outputs.get(identity, [])) != 1 or not _numeric(key, scope, catalog):
                return no('raw_sort_or_partition_key_hidden_transformed_or_not_numeric')
            names.append(outputs[identity][0])
        if any(any(name not in row for name in names) for row in table):
            return no('actual_table_missing_proved_key')
        def values(row, fields):
            result = []
            for name in fields:
                value = row[name]
                if value is None:
                    result.append(None)
                elif isinstance(value, (str, int, Decimal)) and not isinstance(value, bool):
                    number = Decimal(value)
                    if not number.is_finite():
                        raise ValueError('nonfinite_key')
                    result.append(number)
                else:
                    raise ValueError('unknown_or_lossy_key_type')
            return tuple(result)
        def follows(left, right):
            for a, b, order in zip(left, right, final):
                if a == b:
                    continue
                if a is None or b is None:
                    return bool(order.args.get('nulls_first')) if a is None else not bool(order.args.get('nulls_first'))
                return a > b if order.args.get('desc') else a < b
            return True
        positions, previous, dense, seen_order = {}, {}, {}, {}
        previous_sort = None
        ranks = []
        for i, row in enumerate(table):
            partition = values(row, names[:len(partitions)])
            order = values(row, names[len(partitions):])
            if previous_sort is not None and not follows(previous_sort, partition + order):
                return no('actual_row_order_conflicts_with_proved_SQL_order')
            previous_sort = partition + order
            position = positions.get(partition, 0) + 1
            tied = partition in previous and previous[partition][0] == order
            if isinstance(window.this, exp.RowNumber):
                if order in seen_order.setdefault(partition, set()):
                    return no('ROW_NUMBER_peer_position_not_reconstructible')
                seen_order[partition].add(order)
                rank = position
            elif isinstance(window.this, exp.Rank):
                rank = previous[partition][1] if tied else position
            else:
                rank = dense.get(partition, 0) if tied else dense.get(partition, 0) + 1
                dense[partition] = rank
            if rank > prefix:
                return no('actual_rows_conflict_with_window_prefix')
            positions[partition] = position
            previous[partition] = order, rank
            ranks.append({'row_index': i, 'rank': rank,
                          'partition_values': [row[n] for n in names[:len(partitions)]]})
        return {'status': 'verified_SQL_ranking_display_only', 'virtual_ranks': ranks,
                'rank_kind': type(window.this).__name__, 'prefix_bound': prefix,
                'program_cap_evidence': cap_evidence,
                'partition_output_columns': names[:len(partitions)],
                'order_output_columns': names[len(partitions):], 'source': source,
                'actual_SQL_sha256': sha256(sql.encode()).hexdigest(),
                'actual_table_sha256': sha256(json.dumps(table, ensure_ascii=False,
                    sort_keys=True, default=str, separators=(',', ':')).encode()).hexdigest(),
                'business_semantics_verified': False, 'complete_business_population_proved': False,
                'SQL_and_rows_mutated': False}
    except (ValueError, TypeError, KeyError, StopIteration, InvalidOperation, SqlglotError, AttributeError):
        return no('unresolved_SQL_lineage_or_raw_keys')
