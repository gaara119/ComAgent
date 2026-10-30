"""Finite S1 tool-output policy; never a customer business/metric proof."""
from __future__ import annotations

from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.optimizer.scope import Scope, build_scope

from qa_agent.sql.validator import SQLValidationError


def _native_name_representation_conflict(tree, root, marker, customer, question,
                                         source_text, user_history, *, transport=None):
    """Find a provable concatenation without an original name-format override.

    The existing PK/grain proof supplies the customer instance. A CTE which
    exposes only a full-name expression cannot acquire new native fields here.
    Unknown expressions are left to existing validation, not reinterpreted.
    """
    names = {'first_name', 'last_name'}
    if not isinstance(source_text, str) or not names <= customer.column_names:
        return None
    name_format = (r'姓名|全名|姓氏|客户名(?!单)|客户.{0,4}名字|名字[^。；;\n]{0,16}(?:写|显示|格式|拼|拆|分列|分开|合并|省略|简称)|'
                   r'模板|指定格式|列数|字段顺序|输出结构|表格结构|表头顺序|'
                   r'名\s*(?:加|和|与|及|、)\s*姓|'
                   r'姓\s*(?:加|和|与|及|、)\s*名|'
                   r'(?:姓名|名姓|名和姓|名与姓).{0,20}(?:拼|拆|分列|分开|合并)|'
                   r'(?<![A-Za-z0-9_])(?:first_name|last_name|full\s*name|surname|given\s*name)(?![A-Za-z0-9_])')
    users = [question, source_text] + [
        turn if isinstance(turn, str) else turn.get('user', '')
        for turn in user_history if isinstance(turn, str) or isinstance(turn, dict)
        and turn.get('role') in (None, 'user')]
    # A body containing only periods, measures and numeric display rules does
    # not revoke the existing native-name tool representation. Any recognized
    # actual name-layout request wins, including a previous real user request.
    # The caller has separately checked explicit output-column restrictions.
    if any(isinstance(text, str) and re.search(name_format, text, re.I) for text in users):
        return None
    if re.search(r'名字|列数|列名|字段|[0-9一二两三四五六七八九十]+\s*(?:个)?(?:列|栏)|'
                 r'例如|比如|示例|假设|如果|[“”"\'‘’「」]', question):
        return None

    def un(node):
        while isinstance(node, (exp.Alias, exp.Paren)):
            node = node.this
        return node

    def native(node, scope, depth=0):
        node = un(node)
        if depth > 3 or not isinstance(node, exp.Column):
            return None
        selected = scope.selected_sources.get(node.table)
        if selected is None:
            return None
        source = selected[1]
        if isinstance(source, exp.Table):
            if ((source.db or 'public') == 'public' and source.name == 'customer'
                    and (id(scope), node.table, customer.primary_key[0]) == marker
                    and node.name in names):
                return node.name
        elif isinstance(source, Scope):
            projections = [p for p in source.expression.selects if p.alias_or_name == node.name]
            if len(projections) == 1:
                return native(projections[0], source, depth + 1)
        return None

    def concatenated(node, scope, depth=0):
        node = un(node)
        if depth > 4:
            return None
        if isinstance(node, exp.Column):
            field = native(node, scope)
            if field:
                return [field]
            selected = scope.selected_sources.get(node.table)
            if selected and isinstance(selected[1], Scope):
                child = selected[1]
                projections = [p for p in child.expression.selects if p.alias_or_name == node.name]
                if len(projections) == 1:
                    return concatenated(projections[0], child, depth + 1)
            return None
        if (isinstance(node, exp.Literal) and node.is_string
                and re.fullmatch(r'[\s,，·.\-]{0,8}', node.this)):
            return []
        if isinstance(node, exp.DPipe):
            children = (node.this, node.expression)
        elif isinstance(node, (exp.Concat, exp.ConcatWs)):
            children = node.expressions
        else:
            return None
        parts = [concatenated(child, scope, depth + 1) for child in children]
        return None if any(part is None for part in parts) else [name for part in parts for name in part]

    try:
        available = {name: [] for name in names}
        for alias, (_, source) in root.selected_sources.items():
            if isinstance(source, exp.Table):
                for name in names:
                    if native(exp.column(name, table=alias), root) == name:
                        available[name].append(f'{alias}.{name}')
            elif isinstance(source, Scope):
                for projection in source.expression.selects:
                    name = native(projection, source)
                    if name and projection.alias_or_name:
                        available[name].append(f'{alias}.{projection.alias_or_name}')
        if any(len(available[name]) != 1 for name in names):
            if transport is None:
                return None
            available = {name: [transport['base_fields'][name]] for name in names}
        projected = {native(projection, root) for projection in tree.selects}
        if names <= projected:
            return None
        if not any((parts := concatenated(projection, root)) is not None
                   and len(parts) == 2 and set(parts) == names for projection in tree.selects):
            return None
        return {'policy': 'S1_source_scanned_native_customer_names',
                'available': {name: available[name][0] for name in sorted(names)},
                **({'transport': transport} if transport is not None else {}),
                'source_question_sha256': sha256(question.encode()).hexdigest(),
                'source_policy': 'native_names_unless_original_name_or_column_layout_overrides',
                'source_checks': [{'source_sha256':sha256(text.encode()).hexdigest()}
                                  for text in users if isinstance(text,str)],
                'business_semantics_verified': False, 'state_committed': False}
    except Exception:
        return None


def validate_s1_customer_identity(sql, catalog, source_question, *, enabled=False,
                                  source_text='', user_history=()):
    """Require an already available real customer PK in a customer-row result.

    Only the caller's actual S1-on/gate-off switch enables this output policy.
    Unknown scopes do not certify anything. No SQL or result is rewritten.
    """
    def no(reason, status='not_verified'):
        return {'verified': False, 'status': status, 'reason': reason,
                'mode': 's1_customer_identity_output_policy',
                'business_semantics_verified': False}

    if enabled is not True:
        return no('S1 output policy disabled', 'not_applicable')
    if not isinstance(source_question, str) or not re.search(r'客户|\bcustomers?\b', source_question, re.I):
        return no('Current original question has no explicit customer subject', 'not_applicable')
    if not re.search(r'名单|排名|前\s*(?:\d+|[一二三四五六七八九十百]+)\s*(?:位|名)|谁|哪(?:些|位|个)|\b(?:list|rank|top|who|which)\b', source_question, re.I):
        return no('Current original question is not an explicit customer-row request', 'not_applicable')
    texts = [source_question, source_text] + [
        turn if isinstance(turn, str) else turn.get('user', '')
        for turn in user_history if isinstance(turn, (str, dict))]
    fields = r'(?:列|字段|编号|主键|ID|姓名|名字|姓氏|名称|比例|占比|金额|数量)'
    nearby = r'[^，,。；;!?！？\n]{0,24}'
    restriction = (r'(?:只|仅)(?:要|需|给|列|留|显示|输出|返回)' + nearby + fields
                   + r'|(?:不要|不用|无需|无须|不必|不需要)(?:再)?'
                   r'(?:显示|输出|返回|列出|列|带|留|保留|给|附带)' + nearby + fields
                   + r'|(?:不带|不留|不显示|不返回)' + nearby + fields
                   + r'|(?:不要|不用|无需|不必|去掉|省略)\s*(?:客户)?(?:编号|主键|ID)'
                   r'|列(?:数)?不要太多|问什么给什么|不要(?:顺手)?多(?:带|给|加)(?:几)?列'
                   r'|\b(?:only\s+(?:return|show|output)|(?:omit|exclude|without)\s+(?:id|key))\b')
    def restricts_columns(text):
        if not isinstance(text, str):
            return False
        # This explicit list names technical exposition, not result contents.
        # Only the matching clause span is exempt; adjacent actual output-column
        # restrictions retain their ordinary authority in full.
        technical = [m.span() for m in re.finditer(
            r'不要输出\s*表名\s*[、,，]\s*字段名\s*[、,，]\s*连接方式\s*这类技术细节', text)]
        return any(not any(start <= m.start() and m.end() <= end for start, end in technical)
                   for m in re.finditer(restriction, text, re.I))
    if any(restricts_columns(text) for text in texts):
        return no('Explicit original-source output restriction takes priority')
    try:
        customer = catalog.get_table('customer', 'public')
        if len(customer.primary_key) != 1:
            return no('Actual customer catalog has no supported single-column PK')
        pk = customer.primary_key[0]
        from qa_agent.sql.repair_guard import _qualified
        tree = _qualified(sql, catalog)
        root = build_scope(tree)
        if not isinstance(tree, exp.Select) or root is None:
            return no('Final query is not a supported SELECT')

        def un(node):
            while isinstance(node, (exp.Alias, exp.Paren)):
                node = node.this
            return node

        def key_of(node, scope, depth=0):
            node = un(node)
            if depth > 3 or not isinstance(node, exp.Column):
                return None
            selected = scope.selected_sources.get(node.table)
            if selected is None:
                return None
            source = selected[1]
            if isinstance(source, exp.Table):
                if (source.db or 'public') == 'public' and source.name == 'customer' and node.name == pk:
                    return (id(scope), node.table, pk)
            elif isinstance(source, Scope) and isinstance(source.expression, exp.Select):
                projections = [p for p in source.expression.selects if p.alias_or_name == node.name]
                if len(projections) == 1:
                    return key_of(projections[0], source, depth + 1)
            return None

        def customer_field(node, scope, depth=0):
            """Native field provenance for one carrier, never field-name guessing."""
            node = un(node)
            if depth > 3 or not isinstance(node, exp.Column):
                return None
            selected = scope.selected_sources.get(node.table)
            if selected is None:
                return None
            source = selected[1]
            if isinstance(source, exp.Table):
                if ((source.db or 'public') == 'public' and source.name == 'customer'
                        and node.name in customer.column_names):
                    return (id(scope), node.table, pk), node.name
            elif isinstance(source, Scope) and isinstance(source.expression, exp.Select):
                matches = [p for p in source.expression.selects if p.alias_or_name == node.name]
                if len(matches) == 1:
                    return customer_field(matches[0], source, depth + 1)
            return None

        def customer_key_set(node, scope, depth=0):
            """A transparent customer PK/FK value can identify a joined set.

            This does not prove the set's ranking, uniqueness, filters or metric.
            The outer GROUP BY real customer PK is what supplies row grain.
            """
            node = un(node)
            if depth > 3 or not isinstance(node, exp.Column):
                return False
            selected = scope.selected_sources.get(node.table)
            if selected is None:
                return False
            source = selected[1]
            if isinstance(source, Scope) and isinstance(source.expression, exp.Select):
                matches = [p for p in source.expression.selects if p.alias_or_name == node.name]
                return len(matches) == 1 and customer_key_set(matches[0], source, depth + 1)
            if not isinstance(source, exp.Table) or (source.db or 'public') != 'public':
                return False
            table = catalog.get_table(source.name, 'public')
            if source.name == 'customer':
                return node.name == pk
            return any(f.get('columns') == [node.name]
                and (f.get('references') or {}).get('schema', table.schema) == 'public'
                and (f.get('references') or {}).get('table') == 'customer'
                and (f.get('references') or {}).get('columns') == [pk]
                for f in table.foreign_keys)

        def joined_key_set(join, scope, customer_alias):
            on = un(join.args.get('on'))
            other = join.this.alias_or_name
            if not isinstance(on, exp.EQ):
                return False
            for left, right in ((un(on.left), un(on.right)), (un(on.right), un(on.left))):
                if (isinstance(left, exp.Column) and (left.table, left.name) == (customer_alias, pk)
                        and isinstance(right, exp.Column) and right.table == other
                        and customer_key_set(right, scope)):
                    return True
            return False

        def single_global_aggregate(child):
            q = child.expression
            if (not isinstance(q, exp.Select) or len(q.selects) != 1
                    or any(q.args.get(k) for k in ('where', 'group', 'having', 'qualify', 'distinct',
                                                   'limit', 'offset', 'laterals', 'joins'))
                    or q.find(exp.Subquery) or q.find(exp.Window)):
                return False
            aggregate = un(q.selects[0])
            if (not isinstance(aggregate, (exp.Sum, exp.Count, exp.Avg, exp.Min, exp.Max))
                    or not isinstance(un(aggregate.this), (exp.Column, exp.Star))):
                return False
            sources = child.selected_sources
            if len(sources) != 1:
                return False
            if any(column.table not in sources for column in q.find_all(exp.Column)):
                return False
            source = next(iter(sources.values()))[1]
            return (isinstance(source, exp.Table) and (source.db or 'public') == 'public'
                    and catalog.get_table(source.name, 'public') is not None)

        def to_one_employee(join, scope, marker):
            source = scope.selected_sources[join.this.alias_or_name][1]
            if (not isinstance(source, exp.Table) or (source.db or 'public') != 'public'
                    or source.name != 'employee' or join.side not in ('', 'LEFT')
                    or join.kind not in ('', 'INNER')):
                return False
            employee = catalog.get_table('employee', 'public')
            if len(employee.primary_key) != 1:
                return False
            on = un(join.args.get('on'))
            if not isinstance(on, exp.EQ):
                return False
            for left, right in ((un(on.left), un(on.right)), (un(on.right), un(on.left))):
                if not (isinstance(left, exp.Column) and left.table == join.this.alias_or_name
                        and left.name == employee.primary_key[0]):
                    continue
                field = customer_field(right, scope)
                if field is not None and field[0] == marker and any(
                        f.get('columns') == [field[1]]
                        and (f.get('references') or {}).get('schema', customer.schema) == 'public'
                        and (f.get('references') or {}).get('table') == 'employee'
                        and tuple((f.get('references') or {}).get('columns') or ()) == employee.primary_key
                        for f in customer.foreign_keys):
                    return True
            return False

        def grain(scope, depth=0):
            q = scope.expression
            if depth > 2 or not isinstance(q, exp.Select):
                return None
            if any(q.args.get(k) for k in ('distinct', 'qualify', 'laterals')):
                return None
            source_subqueries = {id(node) for node in
                [q.args.get('from_').this if q.args.get('from_') else None,
                 *(j.this for j in q.args.get('joins') or [])] if isinstance(node, exp.Subquery)}
            if (any(id(node) not in source_subqueries for node in q.find_all(exp.Subquery))
                    or any(isinstance(p, exp.Star) or p.find(exp.Star) for p in q.selects)):
                return None
            if any(not isinstance(w.this, (exp.RowNumber, exp.Rank, exp.DenseRank)) for w in q.find_all(exp.Window)):
                return None
            names = [p.alias_or_name for p in q.selects]
            if any(not name for name in names) or len(names) != len(set(names)):
                return None
            sources = scope.selected_sources
            customers = [alias for alias, (_, s) in sources.items()
                         if isinstance(s, exp.Table) and (s.db or 'public') == 'public' and s.name == 'customer']
            if not customers:
                if q.args.get('group') or q.args.get('having') or any(
                            isinstance(n, exp.AggFunc) and not (
                                isinstance(n, (exp.Rank, exp.DenseRank)) and isinstance(n.parent, exp.Window))
                            for p in q.selects for n in p.walk()):
                    return None
                carriers = [(a, s, previous) for a, (_, s) in sources.items()
                            if isinstance(s, Scope) and (previous := grain(s, depth + 1)) is not None]
                if len(carriers) != 1:
                    return None
                alias, child, (marker, _) = carriers[0]
                anchor = q.args.get('from_')
                if anchor is None or anchor.this.alias_or_name != alias:
                    return None
                available = [p.alias_or_name for p in child.expression.selects if key_of(p, child) == marker]
                if len(available) != 1:
                    return None
                employee_count = 0
                for join in q.args.get('joins') or []:
                    other = sources[join.this.alias_or_name][1]
                    if isinstance(other, Scope):
                        if (join.kind != 'CROSS' or join.args.get('on') or join.side
                                or not single_global_aggregate(other)):
                            return None
                    elif isinstance(other, exp.Table) and to_one_employee(join, scope, marker):
                        employee_count += 1
                        if employee_count > 1:
                            return None
                    else:
                        return None
                return marker, f'{alias}.{available[0]}'
            if len(customers) != 1:
                return None
            alias = customers[0]
            marker = (id(scope), alias, pk)
            group = q.args.get('group')
            if not group or any(group.args.get(k) for k in ('rollup', 'cube', 'grouping_sets')):
                return None
            fields = group.expressions
            if not fields or any(not isinstance(v, exp.Column) or v.table != alias for v in fields):
                return None
            if not any(v.name == pk for v in fields):
                return None
            anchor = q.args.get('from_')
            anchored = anchor is not None and isinstance(anchor.this, exp.Table) and anchor.this.alias_or_name == alias
            derived = [s for _, s in sources.values() if isinstance(s, Scope)]
            if derived and (not anchored or len(derived) > 1):
                return None
            for join in q.args.get('joins') or []:
                if join.kind not in ('', 'INNER') or join.side not in ('', 'LEFT'):
                    return None
                if join.side and not anchored:
                    return None
                other = sources[join.this.alias_or_name][1]
                if isinstance(other, Scope) and not joined_key_set(join, scope, alias):
                    return None
                if not isinstance(other, (Scope, exp.Table)):
                    return None
            return marker, f'{alias}.{pk}'

        def transport_chain(scope, depth=0):
            """A missing projection may be carried through one proven row chain.

            This checks the existing row shape only. It neither invents a JOIN
            nor treats an unavailable field as already projected. The repair
            must explicitly expose the catalog fields at every existing stage.
            """
            q = scope.expression
            if depth > 3 or not isinstance(q, exp.Select):
                return None
            if any(q.args.get(k) for k in ('distinct', 'qualify', 'laterals', 'offset')):
                return None
            source_subqueries = {id(n) for n in
                [q.args.get('from_').this if q.args.get('from_') else None]
                if isinstance(n, exp.Subquery)}
            if any(id(n) not in source_subqueries for n in q.find_all(exp.Subquery)):
                return None
            if any(not isinstance(w.this, (exp.RowNumber, exp.Rank, exp.DenseRank))
                   for w in q.find_all(exp.Window)):
                return None
            sources = scope.selected_sources
            physical = [(alias, s) for alias, (_, s) in sources.items()
                        if isinstance(s, exp.Table) and (s.db or 'public') == 'public'
                        and s.name == 'customer']
            if physical:
                if (len(physical) != 1 or any(isinstance(s, Scope) for _, s in sources.values())
                        or (proof := grain(scope)) is None):
                    return None
                alias, _ = physical[0]
                marker, _ = proof
                return {'marker': marker, 'base_scope': scope,
                        'base_fields': {name: f'{alias}.{name}' for name in
                            (pk, 'first_name', 'last_name') if name in customer.column_names},
                        'steps': [{'kind': 'physical_customer_PK_group',
                            'source_alias': alias, 'group_PK': f'{alias}.{pk}'}]}
            if (len(sources) != 1 or q.args.get('joins') or q.args.get('group')
                    or q.args.get('having')):
                return None
            alias, (_, child) = next(iter(sources.items()))
            if not isinstance(child, Scope):
                return None
            if any(isinstance(n, exp.AggFunc) and not (
                        isinstance(n, (exp.Rank, exp.DenseRank)) and isinstance(n.parent, exp.Window))
                   for p in q.selects for n in p.walk()):
                return None
            previous = transport_chain(child, depth + 1)
            if previous is None:
                return None
            return {**previous, 'steps': [*previous['steps'],
                {'kind': 'transparent_customer_row_projection', 'source_alias': alias,
                 'projection_names': [p.alias_or_name for p in q.selects]}]}

        transport = transport_chain(root)
        actual = grain(root)
        needs_transport = actual is None and transport is not None
        if needs_transport:
            actual = transport['marker'], transport['base_fields'][pk]
        if actual is None:
            return no('Final single-customer grain or available PK is outside the bounded proof')
        marker, available = actual
        projected = [p.alias_or_name for p in tree.selects if key_of(p, root) == marker]
    except Exception as exc:
        return no('AST/catalog identity shape unsupported: ' + type(exc).__name__)
    if not projected:
        if needs_transport:
            evidence = {k: transport[k] for k in ('base_fields', 'steps')}
            evidence['source_question_sha256'] = sha256(source_question.encode()).hexdigest()
            evidence['business_semantics_verified'] = False
            error = SQLValidationError(
                'S1客户行输出结构：底层已按同一真实客户主键分组，但现有透明CTE/排名透传链没有把'
                f'该主键 {available} 传到最终投影。请只沿现有链逐层显式投影并传递该真实主键；'
                '不增加JOIN、不改变WHERE、聚合指标、ORDER、LIMIT、并列或行数。'
                '若同层GROUP BY需要显式列字段，只补同一客户真实PK决定的字段。'
                '不要用常量、姓名、发票编号代替主键。此检查只规定工具身份表示，不认证业务语义。')
            error.output_shape_evidence = evidence
            raise error
        raise SQLValidationError(
            'S1客户行输出结构：当前原问明确请求客户名单/排名，且没有显式输出列限制；'
            f'最终SELECT遗漏同一客户行已可投影的真实主键 {available}。'
            '请仅把该同源真实主键加入最终投影；保留原有条件、分组、指标、排名、并列与行数，'
            '不要增加JOIN，不用常量、发票编号或其他对象编号冒充客户主键。此检查仅是工具输出政策，不证明业务语义。')
    native_conflict = _native_name_representation_conflict(
        tree, root, marker, customer, source_question, source_text, user_history,
        transport=({k: transport[k] for k in ('base_fields', 'steps')}
                   if transport is not None and {'first_name', 'last_name'} <= transport['base_fields'].keys()
                   else None))
    if native_conflict is not None:
        fields = native_conflict['available']
        error = SQLValidationError(
            'S1客户行原生姓名输出结构：实际原问、正文和真实用户历史中未识别到优先的姓名或列格式指令；'
            '同一客户行已有可直接投影的原生姓名字段 '
            f"{fields['first_name']} 与 {fields['last_name']}。"
            '用这两个原生姓名字段替代仅拼接姓名的表达式；已投影的原生字段不要重复。'
            '保留真实客户主键、指标、筛选、期间、分组、排名、行数与NULL语义，不要增加JOIN，'
            + ('若现有CTE遗漏该同源字段，只沿已证明的客户行透传链逐层显式投影，底层需要时把同一客户'
             'PK决定的原生字段补入GROUP BY；不新增JOIN或改变指标与行数。'
             if native_conflict.get('transport') is not None else '不要从不可得CTE追补字段；')
            + '这只是S1工具默认表示，不认证客户、金额或业务条件。')
        error.output_shape_evidence = native_conflict
        raise error
    return {'verified': True, 'status': 'complete', 'mode': 's1_customer_identity_output_policy',
            'customer_pk': f'public.customer.{pk}', 'projected_as': projected,
            'business_semantics_verified': False}
