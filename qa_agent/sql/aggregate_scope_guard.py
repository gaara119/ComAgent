"""Reject one provable lost-period aggregate shape before SQL execution.

This is a shared SQL safety check, not an intent/default/semantic-state builder.
Only one direct SUM over a physical child and a real FK -> parent PK lookup is
covered. A LEFT parent's ON-only year filter cannot restrict that child SUM.
All other shapes return not_verified; they are never certified by this check.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from qa_agent.sql.catalog import CatalogError
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


def _single_year(question):
    if not isinstance(question, str):
        return None
    # No clock, history, model tags or business defaults are used. Partial,
    # relative, alternative, quoted and example periods stay outside this gate.
    if re.search(r'[“”"「」『』]|例如|比如|示例|假设|如果|可能|或|还是|'
                 r'月|季度|半年|上半年|下半年|今年|去年|最近|至今|跨年|同比|环比', question):
        return None
    matches = list(re.finditer(r'(?<!\d)(?P<year>[12]\d{3})\s*年(?!代)', question))
    if len(matches) != 1 or len(re.findall(r'(?<!\d)[12]\d{3}(?!\d)', question)) != 1:
        return None
    match = matches[0]
    if (re.search(r'不要|不查|不统计|不按|不是|排除|除去|截至|截止|不止|不只是|不限于', question[max(0, match.start()-12):match.start()])
            or re.match(r'\s*(?:之前|以前|之后|以后|以来|前|后|起|底|初|末)', question[match.end():])):
        return None
    year = int(match['year'])
    if year >= 9999:
        return None
    return year, {'source': 'actual_current_question', 'quote': match[0],
                  'start': match.start(), 'end': match.end(),
                  'source_sha256': sha256(question.encode('utf-8')).hexdigest()}


def _un(node):
    while isinstance(node, (exp.Alias, exp.Paren)):
        node = node.this
    return node


def _atoms(node):
    node = _un(node)
    if isinstance(node, exp.And):
        return _atoms(node.left) + _atoms(node.right)
    return [node] if node is not None else []


def _pair(node):
    node = _un(node)
    if isinstance(node, exp.EQ) and all(isinstance(_un(x), exp.Column) for x in (node.left, node.right)):
        return frozenset((_un(x).table, _un(x).name) for x in (node.left, node.right))
    return None


def _fk_pairs(catalog, sources, child, parent):
    local, remote = sources[child], sources[parent]
    child_table = catalog.get_table(local.name, local.db or 'public')
    parent_table = catalog.get_table(remote.name, remote.db or 'public')
    result = []
    for fk in child_table.foreign_keys:
        target = fk.get('references') or {}
        if ((target.get('schema', child_table.schema), target.get('table')) !=
                (parent_table.schema, parent_table.name)
                or not parent_table.primary_key
                or tuple(target.get('columns') or ()) != parent_table.primary_key):
            continue
        columns = fk.get('columns') or []
        if (len(columns) != len(parent_table.primary_key)
                or not set(columns) <= child_table.column_names):
            continue
        result.append({frozenset(((child, lc), (parent, rc)))
                       for lc, rc in zip(columns, parent_table.primary_key)})
    return result


def _midnight(node):
    node = _un(node)
    if isinstance(node, exp.Cast):
        if str(node.args.get('to')).upper() not in {'DATE', 'TIMESTAMP', 'TIMESTAMPNTZ'}:
            return None
        node = _un(node.this)
    if not isinstance(node, exp.Literal) or not node.is_string:
        return None
    try:
        value = datetime.fromisoformat(node.this)
    except ValueError:
        return None
    if value.tzinfo is not None or (value.hour, value.minute, value.second, value.microsecond) != (0, 0, 0, 0):
        return None
    return value.date().isoformat()


def _year_bound(node, parent, date_fields, year):
    node = _un(node)
    if not isinstance(node, (exp.GTE, exp.LT, exp.LTE, exp.GT)):
        return None
    left, right = _un(node.left), _un(node.right)
    if isinstance(left, exp.Column) and left.table == parent and left.name in date_fields:
        op, column, value = type(node), left, _midnight(right)
    elif isinstance(right, exp.Column) and right.table == parent and right.name in date_fields:
        op = {exp.GTE: exp.LTE, exp.LT: exp.GT, exp.LTE: exp.GTE, exp.GT: exp.LT}[type(node)]
        column, value = right, _midnight(left)
    else:
        return None
    if op is exp.GTE and value == f'{year:04d}-01-01':
        return column.name, 'start'
    if op is exp.LT and value == f'{year+1:04d}-01-01':
        return column.name, 'end'
    return None


def validate_aggregate_scope(sql, catalog, question=None):
    """Raise SQLValidationError only for the bounded ON-only lost-year shape."""
    def unknown(reason):
        return {'verified': False, 'status': 'not_verified', 'reason': reason,
                'checked_aggregates': 0}

    actual = _single_year(question)
    if actual is None:
        return unknown('no_single_explicit_current_year')
    year, source_ref = actual
    try:
        tree = _qualified(sql, catalog)
    except Exception:
        return unknown('unresolved_sql_or_catalog')
    scopes = list(traverse_scope(tree))
    if (not isinstance(tree, exp.Select) or len(scopes) != 1
            or tree.args.get('with_') or tree.args.get('distinct')
            or any(tree.find(kind) for kind in (exp.Subquery, exp.Window, exp.Union, exp.Intersect, exp.Except))):
        return unknown('not_one_direct_select')
    scope = scopes[0]
    sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
    if not sources or any(not isinstance(source, exp.Table) for source in sources.values()):
        return unknown('nonphysical_sources')
    try:
        for source in sources.values():
            catalog.get_table(source.name, source.db or 'public')
    except CatalogError:
        return unknown('unproven_physical_catalog')
    identities = [(source.db or 'public', source.name) for source in sources.values()]
    if len(identities) != len(set(identities)):
        return unknown('multiple_instances_of_physical_table')
    aggregates = list(tree.find_all(exp.AggFunc))
    if len(aggregates) != 1 or not isinstance(aggregates[0], exp.Sum):
        return unknown('not_single_sum')
    aggregate = aggregates[0]
    value = _un(aggregate.this)
    fields = list(value.find_all(exp.Column))
    if isinstance(value, exp.Column):
        fields = [value]
    elif not (isinstance(value, exp.Mul)
              and isinstance(_un(value.left), exp.Column) and isinstance(_un(value.right), exp.Column)):
        return unknown('not_direct_child_measure')
    owners = {column.table for column in fields}
    if len(owners) != 1 or next(iter(owners)) not in sources:
        return unknown('not_single_child_owner')
    child = next(iter(owners))
    # A ratio, an outer CASE or a FILTER needs its own consumed-scope proof.
    # ROUND/CAST here only wrap the numeric output; they do not establish scope.
    consumed_projections = 0
    for projection in tree.selects:
        projected = _un(projection)
        if aggregate in list(projected.walk()):
            consumed_projections += 1
            while isinstance(projected, (exp.Round, exp.Cast)):
                projected = _un(projected.this)
            if projected is not aggregate:
                return unknown('transformed_or_filtered_aggregate')
        elif not isinstance(projected, exp.Column):
            return unknown('nonidentity_other_projection')
    if consumed_projections != 1:
        return unknown('not_one_consumed_output_measure')
    joins = tree.args.get('joins') or []
    for join in joins:
        if (str(join.args.get('side') or '').upper() not in {'', 'LEFT'}
                or str(join.args.get('kind') or '').upper() not in {'', 'INNER', 'OUTER'}):
            return unknown('unsupported_join_direction')
    for join in joins:
        parent = join.this.alias_or_name
        if (str(join.args.get('side') or '').upper() != 'LEFT' or parent == child
                or parent not in sources):
            continue
        fk_options = _fk_pairs(catalog, sources, child, parent)
        atoms = _atoms(join.args.get('on'))
        pairs = {_pair(atom) for atom in atoms}
        fk = next((option for option in fk_options if option <= pairs), None)
        if fk is None:
            continue
        parent_table = catalog.get_table(sources[parent].name, sources[parent].db or 'public')
        dates = {column.name for column in parent_table.columns
                 if column.data_type.lower().startswith(('date', 'timestamp'))}
        bounds = [_year_bound(atom, parent, dates, year) for atom in atoms if _pair(atom) not in fk]
        if len(bounds) != 2 or None in bounds or len({field for field, _ in bounds}) != 1 or {edge for _, edge in bounds} != {'start', 'end'}:
            continue
        on_nodes = {id(node) for node in join.args['on'].walk()}
        # WHERE/HAVING/SUM CASE/FILTER, or any other actual parent use, prevents
        # this specific proof of non-consumption. Such SQL is not certified here.
        if any(column.table == parent and id(column) not in on_nodes for column in tree.find_all(exp.Column)):
            continue
        # Do not infer through prefilters, other temporal paths, or non-FK joins.
        where = tree.args.get('where')
        if where is not None and any(column.table == child for column in where.find_all(exp.Column)):
            continue
        other_dates = False
        for column in tree.find_all(exp.Column):
            if id(column) in on_nodes:
                continue
            physical = catalog.get_table(sources[column.table].name, sources[column.table].db or 'public') if column.table in sources else None
            if physical and any(c.name == column.name and c.data_type.lower().startswith(('date', 'timestamp')) for c in physical.columns):
                other_dates = True
        if other_dates:
            continue
        other_joins_proven = True
        for other in joins:
            if other is join:
                continue
            other_atoms = _atoms(other.args.get('on'))
            other_pairs = {_pair(atom) for atom in other_atoms}
            if None in other_pairs:
                other_joins_proven = False
                break
            all_fk_pairs = set().union(*(option for local in sources for remote in sources if local != remote
                                        for option in _fk_pairs(catalog, sources, local, remote)))
            if not other_pairs or not other_pairs <= all_fk_pairs:
                other_joins_proven = False
                break
        if not other_joins_proven:
            continue
        error = SQLValidationError(
            f'聚合期间丢失：当前原问明确{year}年，但LEFT JOIN {sources[parent].name}的日期仅在ON中；'
            f'SUM的{sources[child].name}明细并未消费该父表匹配，未匹配期间的子明细仍会被累计。'
            '请在WHERE中实际限制父表日期，或使用明确依赖父表匹配的SUM CASE/FILTER；'
            '需要保留无销售对象时，先按同一期间预聚合明细再LEFT JOIN。不得仅把日期继续放在nullable父表ON中。')
        error.aggregate_scope_evidence = {
            'source_ref': source_ref, 'year': year,
            'child_table': f'{sources[child].db or "public"}.{sources[child].name}',
            'parent_table': f'{sources[parent].db or "public"}.{sources[parent].name}',
            'aggregate_sql': aggregate.sql(dialect='postgres'),
            'on_sql': join.args['on'].sql(dialect='postgres'),
            'mode': 'left_fk_parent_period_not_consumed_by_child_sum'}
        raise error
    return unknown('no_proven_on_only_lost_period')
