"""Call-local proof that one final SQL owns total and preview obligations.

Only backend-constructed generation context is accepted. Plan prose never
proves another SQL is an identity lookup: actual SQL/result/cap are checked.
This helper grants no source, object, metric, period, state or execution right.
"""
from copy import deepcopy
from hashlib import sha256
import json
import re

from sqlglot import exp
from sqlglot.errors import SqlglotError

from qa_agent.sql.helper_identity import _identity_ast


def _hash(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode()).hexdigest()


def total_preview_caller_evidence(context, catalog, *, enabled=False):
    """Return enabled=true only for direct or one final business SQL.

    The outer caller supplies its actual S1 flag. A true result says only that
    earlier SQLs are pure native identity results; it does not say this SQL has
    consumed the requested total. validate_s1_total_preview performs that check.
    """
    no = {'enabled': False, 'verified': False, 'business_semantics_verified': False,
          'source': 'program_call_local_total_preview_role'}
    if enabled is not True:
        return {**no, 'reason': 's1_mode_not_enabled'}
    if context is None:
        return {**no, 'enabled': True, 'verified': True, 'mode': 'direct_single_sql'}
    if not isinstance(context, dict) or context.get('kind') != 'composed':
        return {**no, 'reason': 'unknown_context_kind'}
    try:
        return _composed(context, catalog, no)
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError, SqlglotError):
        return {**no, 'reason': 'unproved_plan_or_actual_identity_dependency'}


def _composed(context, catalog, no):
    plan = context.get('_program_composed_plan')
    if not isinstance(plan, dict) or not isinstance(plan.get('steps'), list) or not plan['steps']:
        raise ValueError('Missing backend validated plan')
    seen = {}
    for step in plan['steps']:
        if (not isinstance(step, dict) or not re.fullmatch(r's[1-6]', str(step.get('step_id', '')))
                or step['step_id'] in seen or step.get('tool') not in {'sql', 'doc', 'context'}
                or not isinstance(step.get('question'), str) or not step['question'].strip()
                or not isinstance(step.get('depends_on'), list)
                or len(set(step['depends_on'])) != len(step['depends_on'])
                or any(dep not in seen for dep in step['depends_on'])):
            raise ValueError('Invalid program plan DAG')
        seen[step['step_id']] = step
    sql_steps = [step for step in seen.values() if step['tool'] == 'sql']
    current = context.get('sql_step')
    if (not sql_steps or not isinstance(current, dict)
            or current != {k: sql_steps[-1][k] for k in ('step_id', 'question')}
            or type(context.get('sql_step_count')) is not int
            or context['sql_step_count'] != len(sql_steps)):
        raise ValueError('Not the actual final SQL node')
    dependencies = context.get('dependencies')
    if (not isinstance(dependencies, dict)
            or set(dependencies) != set(sql_steps[-1]['depends_on'])):
        raise ValueError('Incomplete actual dependency map')
    proofs = {}
    for step in sql_steps[:-1]:
        key = step['step_id']
        if key not in dependencies:
            raise ValueError('Earlier SQL not actually available')
        proofs[key] = _native_identity(dependencies[key], catalog)
    return {**no, 'enabled': True, 'verified': True,
            'mode': 'last_sql_after_actual_native_identity_only',
            'step_id': current['step_id'], 'plan_sha256': _hash(plan),
            'identity_sql_proofs': proofs,
            'boundary': 'Only SQL division of work proved; no business/source/default/total-consumption approval'}


def _native_identity(dependency, catalog):
    if (not isinstance(dependency, dict) or dependency.get('status') != 'SUCCEEDED'
            or dependency.get('source') != 'database' or dependency.get('warnings')):
        raise ValueError('No successful actual SQL result')
    sql, rows = dependency.get('sql'), dependency.get('table')
    meta = dependency.get('metadata')
    if not isinstance(sql, str) or not isinstance(meta, dict) or meta.get('truncated') is not False:
        raise ValueError('No actual SQL/cursor evidence')
    out = meta.get('query_output_scope')
    if (not isinstance(out, dict) or not isinstance(rows, list) or len(rows) != 1
            or type(out.get('row_count')) is not int or out['row_count'] != len(rows)
            or type(out.get('response_cap')) is not int or out['response_cap'] <= len(rows)
            or type(out.get('program_added_limit')) is not bool
            or out.get('original_limit') is not None or out.get('cursor_truncated') is not False
            or out.get('possibly_incomplete_enumeration') is not False
            or not re.fullmatch(r'[0-9a-f]{64}', str(out.get('original_sql_sha256', '')))):
        raise ValueError('Identity cursor may be incomplete')
    tree, tables, projections, predicates = _identity_ast(sql, catalog, out)
    original_sql = sql
    if out['program_added_limit']:
        tail = re.search(r'\s+LIMIT\s+' + str(out['response_cap']) + r'\s*;?\s*$', sql, re.I)
        if tail is None:
            raise ValueError('Cannot bind actual program limit to original SQL')
        original_sql = sql[:tail.start()]
    if sha256(original_sql.encode()).hexdigest() != out['original_sql_sha256']:
        raise ValueError('Actual SQL does not match program output-scope SQL hash')
    if (len(tables) != 1 or len(projections) != 2 or not predicates
            or any(isinstance(n, exp.Func) and not isinstance(n, exp.And) for n in tree.walk())):
        raise ValueError('Not a pure single physical identity projection')
    alias, table = next(iter(tables.items()))
    if (table.schema != 'public' or table.name not in {'artist', 'album', 'playlist'}
            or len(table.primary_key) != 1):
        raise ValueError('Unknown identity domain')
    key = table.primary_key[0]
    name = 'title' if table.name == 'album' else 'name'
    output = {field: label for label, (owner, field) in projections.items() if owner == alias}
    row = rows[0]
    if (set(output) != {key, name} or not isinstance(row, dict) or set(row) != set(projections)
            or type(row.get(output[key])) is not int
            or not isinstance(row.get(output[name]), str) or not row[output[name]].strip()):
        raise ValueError('No unique actual native PK/name row')
    for predicate in predicates:
        choices = [(a, b) for a, b in ((predicate.left, predicate.right), (predicate.right, predicate.left))
                   if isinstance(a, exp.Column) and isinstance(b, exp.Literal)]
        if len(choices) != 1:
            raise ValueError('Unknown identity equality')
        column, literal = choices[0]
        if column.table != alias or column.name not in output:
            raise ValueError('Non-identity condition')
        if column.name == name:
            if not literal.is_string or literal.this != row[output[name]]:
                raise ValueError('Actual name does not satisfy SQL identity')
        elif literal.is_string or str(literal.this) != str(row[output[key]]):
            raise ValueError('Actual PK does not satisfy SQL identity')
    return {'verified': True, 'kind': 'actual_native_identity_only',
            'table': f'{table.schema}.{table.name}',
            'sql_sha256': sha256(sql.encode()).hexdigest(), 'table_sha256': _hash(rows),
            'query_output_scope': deepcopy(out), 'metric_or_population_verified': False}
