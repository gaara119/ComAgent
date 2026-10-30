"""Source-backed field/value identities, never executable query conditions.

This component does not call semantic extraction, rules or session state.  A
closed user-defined list identifies its members; it does not choose a country
owner, a predicate, a period, an aggregate or a numerator/denominator role.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import re
from types import SimpleNamespace

from qa_agent.clarify.conflict_authority import build_conflict_sources, _exact_span
from qa_agent.clarify.definition_recovery import (
    closed_country_members, complete_definitions, label_is_referenced,
)
from qa_agent.nlu.ownership import COUNTRY_ROLE_PATTERNS, literal_country_owner


def _source_ref(source, quote, *, start=None):
    ref = SimpleNamespace(quote=quote, source_version=source['source_version'],
        content_sha256=source['content_sha256'], char_start=start, char_end=None)
    span = _exact_span(ref, source)
    if span is None:
        return None
    return {key: source[key] for key in ('source_id', 'source_version', 'content_sha256')} | {
        'quote': quote, 'char_start': span[0], 'char_end': span[1]}


def _statement(text, start, end):
    left = max((match.end() for match in re.finditer(r'[。！？!?；;\n]', text[:start])), default=0)
    right = re.search(r'[。！？!?；;\n]', text[end:])
    finish = end + right.start() if right else len(text)
    return left, finish, text[left:finish]


def _asserted(text, start, end):
    """Examples and explicitly denied role assertions are not positive facts."""
    left, _, clause = _statement(text, start, end)
    if re.search(r'例如|比如|示例|举例|假设|如果|可能|也许|不确定|尚未确定', clause):
        return False
    before, after = text[left:start], text[end:]
    if re.search(r'(?:不要|不应|不能|不按|别按|不是|并不是|并非|不指|不代表|不表示|\bnot)\s*[(（]?[“\"‘\x27]?\s*$', before, re.I):
        return False
    if re.match(r'\s*[”\"’\x27]?\s*(?:不是|并非|不指|不代表|不表示)', after):
        return False
    return True


def _denied_label_at(text, start, end):
    """A literal label mention can be cancelled without defining a new fact."""
    before = text[max(0, start - 30):start]
    after = text[end:end + 24]
    denied = (r'(?:取消|删除|移除|去掉|排除|不看|不查|不统计|不考虑|不要|不应|不能|别)'
              r'(?:按|查(?:询)?|看|统计|使用|采用)?\s*[“\"‘\x27]?\s*$')
    retired = r'\s*[”\"’\x27]?\s*(?:这个称呼|的(?:限制|条件))?\s*(?:先|暂时|暂且)?\s*(?:不看|不考虑|不用|取消|删除|移除)'
    return bool(re.search(denied, before) or re.match(retired, after))


def _label_references(source, label):
    """Keep actual occurrence offsets; mixed denied/positive uses stay unknown."""
    from qa_agent.nlu.linker import _contains_word_boundary
    text, refs = source['text'], []
    for match in re.finditer(re.escape(label), text):
        if not _contains_word_boundary(text, *match.span(), label):
            continue
        if not _asserted(text, *match.span()) or _denied_label_at(text, *match.span()):
            return []
        ref = _source_ref(source, label, start=match.start())
        if ref is not None:
            refs.append(ref)
    return refs


def _historical_label_denial(label, sources):
    # This is source uncertainty, not a persistent scope or a precedence rule.
    # A cancelled/redefined historical name needs fresh clarification elsewhere.
    return any(_denied_label_at(source['text'], *match.span())
        for source in sources.values() if source['kind'] == 'confirmed_history'
        for match in re.finditer(re.escape(label), source['text']))


def _columns(catalog):
    return {f'{table.name}.{column.name}' for table in catalog.tables
            if table.schema == 'public' for column in table.columns}


def _standard_records(index, column, value):
    return [record for record in index.records if record.column == column and
            record.kind == 'standard' and record.standard_value == value and record.surface == value]


def _closed_declaration_tail(clause, members):
    """A declared count cannot hide another alternative or qualification."""
    declared = re.search(r'(?:这|共|合计)([\d一二两三四五六七八九十]+)(?:个)?(?:国家|市场|地区|国)', clause)
    if declared is None:
        return True
    tail = clause[declared.end():].strip().lstrip('，,').strip()
    if not tail:
        return True
    closure = re.fullmatch(r'不多不少(?:就是|是|为)这([\d一二两三四五六七八九十]+)个(?:国家|市场|地区)?', tail)
    if closure is None:
        return False
    from qa_agent.clarify.literal_structures import number
    return number(closure.group(1)) == len(members or [])


def _literal_bindings(bindings, sources, columns, index):
    current = next((source for source in sources.values() if source['kind'] == 'current_user'), None)
    if current is None:
        return []
    text, result = current['text'], []
    for binding in bindings:
        if not isinstance(binding, dict) or binding.get('column') not in columns:
            continue
        column, value = binding['column'], binding.get('value')
        proof = binding.get('field_owner_proof')
        if (binding.get('source') != 'verified_value_index' or not isinstance(value, str)
                or not isinstance(proof, dict) or proof.get('column') != column):
            continue
        span = proof.get('value_span')
        if (not isinstance(span, (list, tuple)) or len(span) != 2 or
                any(type(item) is not int for item in span) or not 0 <= span[0] < span[1] <= len(text)):
            continue
        records = [record for record in index.records if record.column == column and
                   record.standard_value == value and binding.get('evidence_ref') in {record.candidate_id, record.alias_id}
                   and record.kind in {'standard', 'alias'} and record.surface == text[span[0]:span[1]]]
        if not records:
            continue
        actual = literal_country_owner(text, *span, column)
        if actual is None or actual != proof:
            continue
        owner_start, owner_end = actual['owner_span']
        if not _asserted(text, owner_start, owner_end):
            continue
        quote = actual['evidence']
        quote_start = min(span[0], owner_start)
        ref = _source_ref(current, quote, start=quote_start)
        if ref is not None:
            result.append({'kind': 'linked_identity', 'column': column, 'value': value,
                'evidence_ref': binding['evidence_ref'], 'source_ref': ref,
                'field_owner_proof': deepcopy(actual)})
    return result


def _bound_noncountry_identities(bindings, mentions, linking_question, sources, columns, index):
    """Attach sources to identities already chosen by the existing linker.

    A candidate ID proves an indexed identity, not an executable predicate.
    Fuzzy spelling remains the literal user spelling in its source reference.
    A planner's rewritten sentence cannot supply a missing user occurrence.
    """
    from qa_agent.nlu.entity_source import canonical_spans, literal_owner_roles
    from qa_agent.nlu.value_index import normalize
    current = next((s for s in sources.values() if s['kind'] == 'current_user'), None)
    if current is None:
        return []
    text, result = current['text'], []
    linking_question = text if linking_question is None else linking_question
    if not isinstance(linking_question, str):
        return []
    by_mention = {getattr(m, 'mention_id', None): m for m in mentions or ()}
    supported = {'artist.name', 'album.title', 'genre.name', 'playlist.name',
                 'track.name', 'media_type.name'}
    for binding in bindings:
        if (not isinstance(binding, dict) or binding.get('source') != 'verified_value_index'
                or binding.get('column') not in columns & supported
                or not isinstance(binding.get('value'), str)):
            continue
        column, value = binding['column'], binding['value']
        records = [r for r in index.records if r.column == column and r.standard_value == value
                   and r.kind in {'standard', 'alias'}
                   # Aliases share the canonical candidate ID with their
                   # standard value, but their evidence is the alias ID.
                   # An exact standard binding must not pick an earlier alias.
                   and binding.get('evidence_ref') ==
                       (r.alias_id if r.kind == 'alias' else r.candidate_id)]
        if len(records) != 1:
            continue
        mention = by_mention.get(binding.get('mention_id'))
        if mention is not None:
            span, quote = mention.span, mention.original_text
            if (mention.status != 'resolved' or mention.column != column
                    or mention.canonical_value != value or mention.evidence_ref != binding.get('evidence_ref')
                    or mention.match_method != binding.get('method')
                    or not isinstance(span, (tuple, list)) or len(span) != 2
                    or any(type(n) is not int for n in span)
                    or not 0 <= span[0] < span[1] <= len(linking_question)
                    or linking_question[span[0]:span[1]] != quote):
                continue
            records = [r for r in records if r.candidate_id == mention.selected_candidate_id]
            if not records:
                continue
            # The mention offset belongs to the linker's input. A generated
            # subquestion may have different offsets; relocate only a unique
            # exact occurrence in the actual current user message.
            ref = _source_ref(current, quote, start=span[0] if linking_question == text else None)
        elif not mentions and binding.get('method') in {'exact', 'actual_user_canonical'}:
            # Existing captures can lack the LinkedMention array. Reattach
            # only a unique literal existing-index spelling, never fuzzy or
            # a canonical value absent from the actual current user text.
            refs = [(r, _source_ref(current, text[start:end], start=start))
                    for r in records for start, end in canonical_spans(text, index, column, r.surface)]
            refs = {(ref['char_start'], ref['char_end']): (r, ref) for r, ref in refs if ref is not None}
            if len(refs) != 1:
                continue
            record, ref = next(iter(refs.values()))
            records = [record]
        else:
            continue
        if ref is None or not _asserted(text, ref['char_start'], ref['char_end']):
            continue
        actual_roles, denied_roles = literal_owner_roles(text, ref['quote'],
            [(ref['char_start'], ref['char_end'])])
        if column in denied_roles or actual_roles and actual_roles != {column}:
            continue
        record = records[0]
        if binding.get('method') in {'exact', 'actual_user_canonical'} and normalize(ref['quote']) != normalize(record.surface):
            continue
        left, _, clause = _statement(text, ref['char_start'], ref['char_end'])
        identity = {'kind': 'linked_identity', 'column': column, 'value': value,
                    'candidate_id': record.candidate_id, 'evidence_ref': binding['evidence_ref'],
                    'match_method': binding.get('method'), 'source_ref': ref,
                    'context_ref': _source_ref(current, clause, start=left)}
        if actual_roles == {column}:
            identity['field_owner_proof'] = {'source': 'program:literal_entity_owner',
                'column': column, 'value_span': [ref['char_start'], ref['char_end']],
                'evidence': clause}
        result.append(identity)
    return result


def _referenced_field_definitions(current, sources, columns):
    """A literal field-name definition is an identity, not a scope default."""
    actual = next(s for s in sources.values() if s['kind'] == 'current_user')
    candidates = {}
    for source in sources.values():
        for label, clauses in complete_definitions({'user_brief': source['text']}).items():
            mention_refs = _label_references(actual, label)
            if not mention_refs or _historical_label_denial(label, sources):
                continue
            for clause in clauses:
                ref = _source_ref(source, clause)
                body = re.split(r'[:：]', clause, maxsplit=1)[-1].strip()
                found = {column for column, pattern in COUNTRY_ROLE_PATTERNS.items()
                    if column in columns and re.fullmatch(r'(?:只指|仅指|指(?:的是)?|就是|是|对应)\s*' + pattern, body, re.I)}
                valid = ref is not None and _asserted(source['text'], ref['char_start'], ref['char_end'])
                candidates.setdefault(label, []).append((found if valid else set(), ref, mention_refs))
    result = []
    for label, definitions in candidates.items():
        owners = definitions[0][0]
        if len(owners) != 1 or any(item[0] != owners for item in definitions):
            continue
        for _, ref, mention_refs in definitions:
            result.append({'kind': 'field_identity', 'surface': label, 'column': next(iter(owners)),
                           'source_ref': ref, 'mention_ref': mention_refs[0],
                           'mention_refs': mention_refs})
    return result


def _named_entity_identities(sources, columns, index):
    """Associate a referenced user name with one literal indexed entity.

    The complete definition must identify an actual entity field, not a
    predicate, default or a choice among list members. The resulting relation
    remains an identity hint; it creates no binding or execution obligation.
    """
    from qa_agent.nlu.entity_source import OWNERS
    actual = next(source for source in sources.values() if source['kind'] == 'current_user')
    roles = {column: r'(?<![A-Za-z0-9_])(?:' + words + r')(?![A-Za-z0-9_])'
             for column, words in {**OWNERS, 'track.name': r'曲目|歌曲|tracks?|songs?',
                                  'media_type.name': r'媒体类型|media\s+type'}.items()}
    candidates = {}
    for source in sources.values():
        definitions = complete_definitions({'user_brief': source['text']})
        for label, clauses in definitions.items():
            mentions = _label_references(actual, label)
            if not mentions or _historical_label_denial(label, sources):
                continue
            for clause in clauses:
                ref = _source_ref(source, clause)
                found = []
                if ref is not None and _asserted(source['text'], ref['char_start'], ref['char_end']):
                    body = re.split(r'[:：]', clause, maxsplit=1)[-1].strip()
                    label_roles = {column for column, words in roles.items()
                                   if re.search(words, label, re.I)}
                    for record in index.records:
                        if (record.column not in columns or record.column not in roles
                                or record.kind not in {'standard', 'alias'}
                                or (record.kind == 'standard' and record.surface != record.standard_value)
                                or (record.kind == 'alias' and not record.alias_id)):
                            continue
                        words = roles[record.column]
                        match = re.fullmatch(r'(?:只指|仅指|指(?:的是)?|就是|是|为)\s*'
                            r'(?P<role>(?:' + words + r'))?\s*[“\"‘\x27]?'
                            r'(?P<value>' + re.escape(record.surface) + r')[”\"’\x27]?\s*', body, re.I)
                        if match is None or (label_roles and label_roles != {record.column}):
                            continue
                        if match['role'] is None and label_roles != {record.column}:
                            continue
                        value_start = ref['char_start'] + clause.index(body) + match.start('value')
                        value_ref = _source_ref(source, match['value'], start=value_start)
                        if value_ref is not None:
                            found.append((record, ref, value_ref, mentions))
                # Duplicate evidence is not resolved by index order, and an
                # invalid competing definition must not be silently skipped.
                candidates.setdefault(label, []).append(found[0] if len(found) == 1 else None)
    result = []
    for label, definitions in candidates.items():
        if any(item is None for item in definitions):
            continue
        identities = {(item[0].column, item[0].standard_value) for item in definitions}
        if len(identities) != 1:
            continue
        for record, ref, value_ref, mentions in definitions:
            result.append({'kind': 'named_entity_identity', 'surface': label,
                'column': record.column, 'value': record.standard_value,
                'candidate_id': record.candidate_id,
                'evidence_ref': record.alias_id if record.kind == 'alias' else record.candidate_id,
                'source_ref': ref, 'value_ref': value_ref, 'mention_refs': mentions})
    return result


def _field_identities(current, sources, columns):
    result = []
    current_owners = {column for column, pattern in COUNTRY_ROLE_PATTERNS.items()
        for match in re.finditer(pattern, current, re.I) if _asserted(current, *match.span())}
    for source in sources.values():
        if source['kind'] == 'confirmed_history':
            # An old question is not a continuing field restriction.  History
            # supplies only explicit named definitions handled separately.
            continue
        text = source['text']
        for column, pattern in COUNTRY_ROLE_PATTERNS.items():
            if column not in columns or column not in current_owners:
                continue
            for match in re.finditer(pattern, text, re.I):
                if not _asserted(text, *match.span()):
                    continue
                left, _, clause = _statement(text, *match.span())
                if clause.lstrip().startswith('【'):
                    continue
                roles = {owner for owner, role in COUNTRY_ROLE_PATTERNS.items()
                         if re.search(role, clause, re.I)}
                # A contrast or cross-owner definition is not one unambiguous
                # field assertion. Never pick a default from such a sentence.
                if roles != {column}:
                    continue
                ref = _source_ref(source, clause, start=left)
                if ref is not None:
                    result.append({'kind': 'field_identity', 'surface': match.group(),
                                   'column': column, 'source_ref': ref})
    return result + _referenced_field_definitions(current, sources, columns)


def _named_sets(current, sources, columns, index):
    candidates = {}
    for source in sources.values():
        for label, clauses in complete_definitions({'user_brief': source['text']}).items():
            if not label_is_referenced(label, current):
                continue
            for clause in clauses:
                ref = _source_ref(source, clause)
                members = closed_country_members(label, clause)
                affirmative = re.match(r'^[“\"‘]' + re.escape(label) + r'[”\"’]\s*[:：]\s*(?:只指|仅指)', clause)
                valid = (affirmative and ref is not None and _closed_declaration_tail(clause, members)
                         and _asserted(source['text'], ref['char_start'], ref['char_end']))
                candidates.setdefault(label, []).append((members if valid else None, ref))
    result = []
    for label, definitions in candidates.items():
        # Different/unsupported real definitions remain unresolved identities;
        # this layer does not adjudicate source precedence or user intent.
        members = definitions[0][0]
        if not members or any(item[0] is None or set(item[0]) != set(members) for item in definitions):
            continue
        owners, evidence = [], []
        for column in sorted(columns):
            if column not in {'customer.country', 'invoice.billing_country', 'employee.country'}:
                continue
            records = [_standard_records(index, column, member) for member in members]
            if all(len(group) == 1 for group in records):
                owners.append(column)
                evidence.append({'column': column, 'candidate_ids': [group[0].candidate_id for group in records]})
        if owners:
            result.append({'kind': 'named_value_set', 'label': label, 'values': list(members),
                'candidate_columns': owners, 'value_evidence': evidence,
                'source_refs': [item[1] for item in definitions]})
    return result


def collect_source_elements(catalog, index, bindings=(), *, runtime=None, session_id=None,
                            mentions=(), linking_question=None):
    """Read actual source identities.  No bindings or query state are mutated."""
    if runtime is None:
        from qa_agent.context import current_context
        runtime = current_context()
    if (runtime is None or index is None or catalog.database.casefold() != 'chinook'
            or (session_id is not None and runtime.session_id != session_id)):
        return []
    current = runtime.current_user_message
    if not isinstance(current, str) or not current.strip():
        return []
    if runtime.content_sha256 is not None and runtime.content_sha256 != sha256(runtime.text.encode()).hexdigest():
        return []
    # The existing registry uses current user text, original brief and user-only
    # history.  Assistant answers, planner prose and generated SQL never enter.
    sources = build_conflict_sources(current, runtime.prompt_payload())
    columns = _columns(catalog)
    result = _literal_bindings(bindings, sources, columns, index)
    result += _bound_noncountry_identities(bindings, mentions, linking_question, sources, columns, index)
    result += _field_identities(current, sources, columns)
    result += _named_sets(current, sources, columns, index)
    result += _named_entity_identities(sources, columns, index)
    unique = {}
    for item in result:
        unique.setdefault(json.dumps(item, ensure_ascii=False, sort_keys=True), item)
    return list(unique.values())
