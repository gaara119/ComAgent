"""A shared, narrow SQL/source contradiction check, independent of component3.

Only an explicit current exclusion plus replacement request and a necessary
positive equality on the same physical artist-name field is proven here.
No entity linking, alias/default approval, replacement choice or state exists.
Unknown boolean/derived/comparison shapes remain not_verified.
"""
from __future__ import annotations

from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.optimizer.scope import build_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


class ExplicitSourceConflict(SQLValidationError):
    code = 'explicit_source_conflict'
    fatal = True
    retryable = False
    sql_repairable = False

    def __init__(self, message, details):
        super().__init__(message)
        self.details = details


_NAME = r'[^，,；;。！？!?“”"\'‘’（）()—\n]{1,100}?'
_OTHER_ARTIST = r'(?:换|改)(?:成|为)?\s*另(?:一个|一支|一位|一)\s*(?:乐队|艺术家|(?<![a-z0-9_])(?:artist|band)(?![a-z0-9_]))'
_EXCLUSIONS = (
    re.compile(r'(?:^|[，,；;。！？!?\n])\s*[“"\'‘]?(?P<name>'+_NAME+r')[”"\'’]?\s*'
               r'(?:先)?不看\s*[，,；;。\s]*'+_OTHER_ARTIST, re.I),
    re.compile(r'(?:^|[，,；;。！？!?\n])\s*(?:先不看|不看|排除|不要看)\s*[“"\'‘]?'
               r'(?P<name>'+_NAME+r')[”"\'’]?\s*[，,；;。\s]*'+_OTHER_ARTIST, re.I),
)


def _excluded_artist_literals(question):
    found = []
    for pattern in _EXCLUSIONS:
        for match in pattern.finditer(question):
            prefix = re.split(r'[。！？!?\n]', question[:match.start()])[-1]
            if re.search(r'例如|比如|举例|示例|例句|假设|如果|并非|不是|引用|翻译|解释这句', prefix):
                continue
            if question[match.end():match.end()+1] in {'”', '"', '’', "'"}:
                continue  # an entire quoted instruction is not a current exclusion
            raw = match['name']; value = raw.strip()
            if not value:
                continue
            start = match.start('name') + len(raw) - len(raw.lstrip())
            entry = {'literal': value, 'char_start': start, 'char_end': start+len(value)}
            if entry not in found:
                found.append(entry)
    return found


def _necessary_equalities(node):
    # Do not descend into NOT, OR, EXISTS, CASE, FILTER, HAVING or subqueries.
    if isinstance(node, (exp.Where, exp.Paren)):
        yield from _necessary_equalities(node.this)
    elif isinstance(node, exp.And):
        yield from _necessary_equalities(node.left)
        yield from _necessary_equalities(node.right)
    elif isinstance(node, exp.EQ) and node.args.get('negate') is not True:
        yield node


def validate_source_literal_consistency(sql, catalog, *, question):
    """Raise only for a proved direct contradiction; otherwise do not certify SQL.

    Caller must supply the actual current user question, never a model plan or
    prior assistant answer. Returned not_verified is not execution permission.
    Existing SQL safety, source restrictions and any enabled gate still apply.
    """
    result = {'applicable': False, 'status': 'not_verified', 'verified': False,
              'business_correctness_asserted': False,
              'method': 'explicit_current_artist_exclusion_vs_direct_physical_equality'}
    if not isinstance(question, str) or not isinstance(sql, str):
        return result
    exclusions = _excluded_artist_literals(question)
    if not exclusions:
        return result
    result['applicable'] = True
    try:
        artist = catalog.get_table('artist', 'public')
        if 'name' not in artist.column_names:
            return result
        tree = _qualified(sql, catalog)
        scope = build_scope(tree)
        if not isinstance(tree, exp.Select) or scope is None:
            return result
        artists = {alias: source for alias, (_, source) in scope.selected_sources.items()
                   if isinstance(source, exp.Table) and source.name == 'artist'
                   and (source.db or 'public') == 'public'}
        if len(artists) != 1:
            return result  # no inferred lineage or multi-instance comparison role
    except Exception:
        return result
    alias = next(iter(artists))
    predicates = list(_necessary_equalities(tree.args.get('where')))
    for join in tree.args.get('joins') or ():
        if not join.args.get('side') and join.args.get('kind') in (None, '', 'INNER'):
            predicates.extend(_necessary_equalities(join.args.get('on')))
    for predicate in predicates:
        left, right = predicate.left, predicate.right
        if isinstance(right, exp.Column):
            left, right = right, left
        if (not isinstance(left, exp.Column) or left.table != alias or left.name != 'name'
                or not isinstance(right, exp.Literal) or not right.is_string):
            continue
        for source in exclusions:
            if right.this != source['literal']:
                continue  # no fuzzy/case/alias equivalence is granted
            details = {'source': {'kind': 'actual_current_user_question',
                        'sha256': sha256(question.encode('utf-8')).hexdigest(), **source},
                       'physical_column': 'public.artist.name', 'sql_operator': '=',
                       'sql_literal': right.this, 'replacement_selected': False}
            raise ExplicitSourceConflict(
                '本轮原文明示先不看该乐队并改为另一个对象，但查询仍把被排除对象作为正向条件。'
                '已停止执行，未猜测替代对象；此问题不能通过自动SQL修复选择替代值。', details)
    return result
