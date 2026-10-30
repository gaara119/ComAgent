"""Literal pinyin candidates derived from actual catalog descriptions.

These are schema vocabulary hints, not value aliases, bindings or a query
contract. Every candidate retains its real catalog location. A repeated word
in a table and its fields is one term with several evidence locations; two
different Chinese words with the same pinyin remain explicitly ambiguous.
No SQL validator is provided: a vocabulary match cannot prove query scope.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import json
import re

from qa_agent.sql.catalog import Catalog


_HAN_TERM = re.compile(r"[\u4e00-\u9fff]{2,8}\Z")
_NEGATIVE_OR_EXAMPLE = re.compile(
    r"不要|不用|不按|不以|不看|不是|并非|排除|忽略|别按|别看|勿|"
    r"例如|比如|示例|例句|引用|原话|假如|假设|如果")
_NAME_BEFORE = re.compile(
    r"(?:名为|名叫|叫做|称作|名字(?:是|为)|名称(?:是|为)|"
    r"(?:乐队|艺术家|歌手|专辑|曲目|歌曲|歌单|播放列表|客户|员工)"
    r"(?:名(?:称)?|名字)?(?:为|是|叫做|叫)?)\s*$")
_NAME_AFTER = re.compile(r"\s*(?:的)?\s*(?:乐队|艺术家|歌手|先生|女士|这个人|专辑|曲目|歌曲|歌单)")
_ROLE_BEFORE = re.compile(r"(?:按(?:照)?|依照|以|每(?:个|种|位|类)?|各(?:个|种|位|类)?|"
                          r"哪(?:个|些|种|类)|什么)\s*$")
_ROLE_AFTER = re.compile(r"\s*(?:(?:是|为)\s*哪(?:个|些|种|类)|"
                         r"(?:分组|分类|汇总|排名|排行|列表|名单)|"
                         r"(?:的)?(?:名称|编号|数量|总数|销售额|收入|平均|总时长|所在地))")
_QUOTE_PAIRS = (("'", "'"), ('"', '"'), ('“', '”'), ('‘', '’'), ('「', '」'), ('『', '』'), ('`', '`'))


def _in_quote(text: str, start: int, end: int) -> bool:
    for opening, closing in _QUOTE_PAIRS:
        # A conservative lexical exception: quoted names/examples do not
        # become schema roles. Apostrophes *inside* a pinyin span are fine.
        before = text.rfind(opening, 0, start)
        if before >= 0 and text.find(closing, before + len(opening)) >= end:
            return True
    return False


def _schema_role_context(text: str, start: int, end: int) -> bool:
    left = re.split(r"[。！？?；;，,\n]", text[:start])[-1]
    right = re.split(r"[。！？?；;，,\n]", text[end:], maxsplit=1)[0]
    if (_in_quote(text, start, end) or _NEGATIVE_OR_EXAMPLE.search(left)
            or _NAME_BEFORE.search(left) or _NAME_AFTER.match(right)):
        return False
    return bool(_ROLE_BEFORE.search(left) or _ROLE_AFTER.match(right))


def _descriptions(catalog: Catalog) -> tuple[tuple[str, str, str | None, str], ...]:
    return tuple((table.schema, table.name, column, description)
                 for table in catalog.tables
                 for column, description in [(None, table.description)] + [
                     (item.name, item.description) for item in table.columns]
                 if description)


@lru_cache(maxsize=8)
def _vocabulary(descriptions: tuple) -> tuple:
    # Both libraries are existing local dependencies; no model, dictionary
    # download or mutation of the value index / approved alias files occurs.
    import jieba
    from pypinyin import Style, lazy_pinyin

    tokenizer = jieba.Tokenizer()
    entries = []
    for schema, table, column, description in descriptions:
        # Text following an examples marker is not schema terminology. Do not
        # convert database values or illustrative proper names into roles.
        label = re.split(r"例如|比如|示例|举例|真实示例", description, maxsplit=1)[0]
        for term, start, end in tokenizer.tokenize(label, mode='default', HMM=False):
            if not _HAN_TERM.fullmatch(term):
                continue
            syllables = tuple(lazy_pinyin(term, style=Style.NORMAL))
            if any(not re.fullmatch(r'[a-z]+', syllable) for syllable in syllables):
                continue
            evidence = {'schema': schema, 'table': table, 'column': column,
                        'target': '.'.join(part for part in (schema, table, column) if part),
                        'description': description,
                        'description_sha256': sha256(description.encode()).hexdigest(),
                        'term': term, 'term_span': [start, end],
                        'source': 'catalog_description'}
            entries.append((term, syllables, evidence))
    return tuple(entries)


def schema_term_hints(question: str, catalog: Catalog) -> list[dict]:
    """Return exact, source-linked pinyin schema candidates in role contexts.

    ASCII case, spaces, hyphens and pinyin apostrophes may vary; no edit
    distance, initials, tone guessing or value matching is used. Unknown,
    quoted, negated and name-like spans simply receive no hint. Absence is
    never evidence that a query is valid or invalid.
    """
    if not isinstance(question, str) or not question:
        return []
    descriptions = _descriptions(catalog)
    schema_hash = sha256(json.dumps(descriptions, ensure_ascii=False,
        separators=(',', ':')).encode()).hexdigest()
    grouped = {}
    for term, syllables, evidence in _vocabulary(descriptions):
        # Whole ASCII token boundaries avoid turning an embedded substring
        # in a person/band name into a schema term.
        pattern = r'(?<![A-Za-z0-9_])' + r"[ \t'’-]*".join(map(re.escape, syllables)) + r'(?![A-Za-z0-9_])'
        for match in re.finditer(pattern, question, flags=re.I):
            if not _schema_role_context(question, *match.span()):
                continue
            key = match.span()
            item = grouped.setdefault(key, {'surface': match.group(), 'span': list(key),
                'question_sha256': sha256(question.encode()).hexdigest(),
                'catalog_description_sha256': schema_hash,
                'pinyin': ' '.join(syllables), 'terms': [], 'candidates': [],
                'status': 'candidate_only', 'semantic_verified': False,
                'schema_selection': 'not_selected',
                'authority': 'catalog_term_candidate_only'})
            if term not in item['terms']:
                item['terms'].append(term)
            if evidence not in item['candidates']:
                item['candidates'].append({**evidence, 'term_span': list(evidence['term_span'])})
    result = []
    for _, item in sorted(grouped.items()):
        item['terms'].sort()
        item['candidates'].sort(key=lambda candidate: (candidate['target'], candidate['term_span'][0]))
        item['status'] = 'ambiguous' if len(item['terms']) > 1 else 'candidate_only'
        item['schema_location_count'] = len(item['candidates'])
        # Repeated catalog locations are all retained; a single Chinese term
        # does not assert one table/field, a value identity or any WHERE scope.
        result.append(item)
    return result
