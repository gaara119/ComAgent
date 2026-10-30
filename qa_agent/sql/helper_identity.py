"""Backend-only preliminary identity roles and actual playlist-key handoff.

The validated plan proves only that a later SQL step is planned to consume this
lookup. Only a separately checked actual result can authorize a container key;
the later metric still requires its document and physical SQL proof.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import re

from sqlglot import exp
from sqlglot.optimizer.scope import build_scope

from qa_agent.sql.validator import SQLValidationError


def _hash(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), default=str).encode()).hexdigest()


def _deny(message):
    raise SQLValidationError('前置身份查询：' + message)


def identity_lookup_role(context):
    if not isinstance(context, dict) or context.get('kind') != 'composed':
        return None
    from qa_agent.sql.document_metric_lineage import document_metric_target
    if (context.get('debut_identity_lookup') is True
            or document_metric_target(context.get('original_question', '')) != '热门曲目'):
        return None
    plan = context.get('_program_composed_plan')
    current = (context.get('sql_step') or {}).get('step_id')
    if not isinstance(plan, dict) or not isinstance(plan.get('steps'), list):
        return None
    steps, seen = plan['steps'], {}
    for step in steps:
        if (not isinstance(step, dict) or not isinstance(step.get('step_id'), str)
                or step['step_id'] in seen or step.get('tool') not in {'sql', 'doc', 'context'}
                or not isinstance(step.get('depends_on'), list)
                or any(key not in seen for key in step['depends_on'])):
            return None
        seen[step['step_id']] = step
    item = seen.get(current)
    if (not item or item['tool'] != 'sql' or sum(s['tool'] == 'sql' for s in steps) < 2
            or any(seen[key]['tool'] != 'sql' for key in item['depends_on'])):
        return None
    consumers = [s['step_id'] for s in steps if s['tool'] == 'sql' and current in s['depends_on']]
    if not consumers:
        return None
    return {'kind': 'preliminary_identity_lookup', 'step_id': current,
            'consumer_step_ids': consumers, 'plan_sha256': _hash(plan),
            'downstream_consumption_verified': False,
            'tool_purpose': '本步只核查后续计算所需集合容器的真实主键和原生名称；'
            '不要枚举全部曲目ID，不聚合或计算指标。后续仍须按真实外键现场查询完整成员并消费真实文档定义。'}


def _identity_ast(sql, catalog, query_output_scope=None):
    from qa_agent.sql.repair_guard import _qualified
    tree = _qualified(sql, catalog)
    if (not isinstance(tree, exp.Select) or len(list(tree.find_all(exp.Select))) != 1
            or any(tree.args.get(k) for k in ('with_', 'distinct', 'group', 'having', 'qualify', 'offset', 'laterals'))):
        _deny('只支持未截断的一层真实身份SELECT，不能聚合、去重或藏入派生查询。')
    if tree.args.get('limit'):
        limit = tree.args['limit'].expression
        if not (isinstance(query_output_scope, dict)
                and query_output_scope.get('program_added_limit') is True
                and query_output_scope.get('original_limit') is None
                and isinstance(limit, exp.Literal) and not limit.is_string
                and str(limit.this) == str(query_output_scope.get('response_cap'))):
            _deny('显式LIMIT可能隐藏其它身份，不能据此选择唯一对象。')
        tree = tree.copy()
        tree.set('limit', None)
    scope = build_scope(tree)
    sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
    if not sources or any(not isinstance(source, exp.Table) for source in sources.values()):
        _deny('身份来源必须是当前真实目录物理表。')
    tables = {alias: catalog.get_table(source.name, source.db or 'public') for alias, source in sources.items()}
    fields = {}
    for alias, table in tables.items():
        fields[alias] = set(table.primary_key) | {'name', 'title', 'first_name', 'last_name'}
        for fk in table.foreign_keys:
            fields[alias].update(fk.get('columns') or [])

    def column(node):
        return isinstance(node, exp.Column) and node.table in fields and node.name in fields[node.table]

    projections = {}
    for p in tree.selects:
        value = p.this if isinstance(p, exp.Alias) else p
        if not column(value) or not p.alias_or_name or p.alias_or_name in projections:
            _deny('只能投影真实PK/FK及原生名称/标题；不能用常量、函数、CASE、CAST、窗口或聚合冒充身份。')
        projections[p.alias_or_name] = (value.table, value.name)

    def atoms(node):
        node = node.this if isinstance(node, (exp.Where, exp.Paren)) else node
        return atoms(node.left) + atoms(node.right) if isinstance(node, exp.And) else [node]

    def true_fk(left, right):
        if not column(left) or not column(right) or left.table == right.table:
            return False
        for child, parent in ((left, right), (right, left)):
            source, target = tables[child.table], tables[parent.table]
            if target.primary_key == (parent.name,) and any(
                    f.get('columns') == [child.name]
                    and f.get('references', {}).get('columns') == [parent.name]
                    and f.get('references', {}).get('table') == target.name
                    and f.get('references', {}).get('schema', 'public') == target.schema
                    for f in source.foreign_keys):
                return True
        return False

    for join in tree.args.get('joins') or []:
        if join.side or join.kind not in ('', 'INNER') or not join.args.get('on'):
            _deny('身份关联只支持真实INNER FK→PK连接。')
        if any(not isinstance(a, exp.EQ) or not true_fk(a.left, a.right) for a in atoms(join.args['on'])):
            _deny('身份关联没有证明完整的真实FK→PK关系。')
    predicates = atoms(tree.args['where']) if tree.args.get('where') else []
    for predicate in predicates:
        if not isinstance(predicate, exp.EQ) or not any(
                column(left) and isinstance(right, exp.Literal)
                for left, right in ((predicate.left, predicate.right), (predicate.right, predicate.left))):
            _deny('身份筛选只支持真实身份字段的明确等值，不接受OR或额外业务指标条件。')
    return tree, tables, projections, predicates


def validate_identity_lookup_sql(sql, catalog, context):
    role = identity_lookup_role(context)
    if role is None:
        return None
    if catalog.database != 'chinook':
        _deny('当前文档与容器证明仅适用于实际Chinook目录，不能外推到另一数据库。')
    tree, tables, projections, predicates = _identity_ast(sql, catalog)
    # A container lookup must not transmit a capped enumeration of children.
    if any(t.name == 'playlist' and t.schema == 'public' for t in tables.values()) and (
            len(tables) != 1 or any(t.name != 'playlist' for t in tables.values())):
        _deny('歌单前置查询请仅返回真实playlist主键和名称；不要枚举全部track IDs。'
              '后续应以实际歌单主键沿真实FK查询完整成员，不能把受500行上限影响的部分ID当全集。')
    if (len(tables) != 1 or next(iter(tables.values())).name != 'playlist'
            or next(iter(tables.values())).schema != 'public'):
        _deny('该前置角色只能核查实际歌单容器，不替代别的实体或业务计算。')
    physical = next(iter(tables.values()))
    if (len(physical.primary_key) != 1 or len(projections) != 2
            or {f for _, f in projections.values()} != {physical.primary_key[0], 'name'}
            or len(predicates) != 1):
        _deny('歌单前置查询只返回实际单主键和name，并以明确身份等值筛选；不能先枚举其它集合。')
    return {'verified': True, **role, 'mode': 'physical_native_identity_projection_only',
            'projection_count': len(projections), 'business_metric_verified': False}


def prove_identity_lookup_result(sql, table, catalog, context, query_output_scope):
    role = identity_lookup_role(context)
    if role is None:
        return None
    if catalog.database != 'chinook':
        _deny('身份结果与本次真实Chinook文档/目录不对应。')
    tree, tables, projections, predicates = _identity_ast(sql, catalog, query_output_scope)
    if not isinstance(query_output_scope, dict):
        _deny('缺少程序实际行上限/截断证明，不能把结果当完整身份集合。')
    scope = query_output_scope
    if (not isinstance(table, list) or type(scope.get('program_added_limit')) is not bool
            or scope.get('original_limit') is not None
            or type(scope.get('row_count')) is not int or type(scope.get('response_cap')) is not int
            or scope['response_cap'] < 1 or type(scope.get('cursor_truncated')) is not bool
            or type(scope.get('possibly_incomplete_enumeration')) is not bool
            or not re.fullmatch(r'[0-9a-f]{64}', str(scope.get('original_sql_sha256') or ''))
            or scope['row_count'] != len(table) or scope['cursor_truncated']
            or scope['possibly_incomplete_enumeration']
            or (scope['program_added_limit'] and scope['row_count'] >= scope['response_cap'])):
        _deny('身份结果存在显式/程序行上限或截断不确定性，不能据部分列表确定总体。')
    if not table:
        return {'verified': False, **role, 'status': 'EMPTY_RESULT'}
    if len(tables) != 1 or len(table) != 1:
        _deny('身份交接需唯一实际容器行，不能任取多行或合并部分成员。')
    alias, physical = next(iter(tables.items()))
    if physical.schema != 'public' or physical.name != 'playlist' or len(physical.primary_key) != 1:
        _deny('本次容器交接仅支持真实playlist单主键与原生名称，未知对象不得猜测。')
    key = physical.primary_key[0]
    keys = {field: output for output, (owner, field) in projections.items() if owner == alias}
    if set(keys) != {key, 'name'} or len(projections) != 2 or len(predicates) != 1:
        _deny('歌单身份必须实际投影同一行的完整PK与name，并有唯一明确身份等值条件。')
    from qa_agent.sql.document_metric_lineage import _request
    requested = _request(context.get('original_question', ''), '热门曲目')
    row = table[0]
    if (not isinstance(row, dict) or type(row.get(keys[key])) is not int
            or row.get(keys['name']) != requested['value']):
        _deny('实际返回的歌单主键/名称未对应原问真实canonical对象。')
    predicate = predicates[0]
    choices = [(a, b) for a, b in ((predicate.left, predicate.right), (predicate.right, predicate.left))
               if isinstance(a, exp.Column) and isinstance(b, exp.Literal)]
    if not any(a.table == alias and (
            (a.name == 'name' and b.is_string and b.this == requested['value']) or
            (a.name == key and not b.is_string and str(b.this) == str(row[keys[key]]))) for a, b in choices):
        _deny('实际身份WHERE与原名称或返回的真实PK不一致。')
    return {'verified': True, **role, 'mode': 'actual_complete_unique_playlist_identity',
            'playlist_id': row[keys[key]], 'playlist_name': row[keys['name']],
            'pk_column': key, 'source_sql_sha256': sha256(sql.encode()).hexdigest(),
            'source_table_sha256': _hash(table), 'query_output_scope': deepcopy(scope),
            'original_question_sha256': sha256(context.get('original_question', '').encode()).hexdigest(),
            'business_metric_verified': False}


def resolved_playlist_identity(dependencies, catalog, context):
    if not isinstance(context, dict) or not context.get('_program_composed_plan'):
        return None
    found = []
    current = (context.get('sql_step') or {}).get('step_id')
    for step_id, dependency in dependencies.items():
        metadata = dependency.get('metadata') or {}
        saved = metadata.get('identity_lookup_proof')
        if not isinstance(saved, dict) or saved.get('verified') is not True:
            continue
        if dependency.get('source') != 'database' or dependency.get('status') != 'SUCCEEDED':
            _deny('容器身份没有实际成功数据库结果。')
        original = {**context, 'sql_step': {'step_id': step_id}}
        actual = prove_identity_lookup_result(dependency.get('sql', ''), dependency.get('table', []),
            catalog, original, metadata.get('query_output_scope'))
        if (actual != saved or current not in actual.get('consumer_step_ids', [])
                or step_id not in next((s.get('depends_on', []) for s in context['_program_composed_plan']['steps']
                                       if s['step_id'] == current), [])):
            _deny('身份实际SQL/table/行限/计划/消费者不匹配，不能信任单个metadata声明。')
        found.append(actual)
    if len(found) > 1:
        _deny('多个实际容器身份尚无唯一对应，不能任选一个。')
    return found[0] if found else None
