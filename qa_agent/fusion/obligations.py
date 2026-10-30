"""Bounded, original-question obligations, independent of model plan coverage.

This is deliberately not a general semantic judge. It protects the already
supported database numeric requests and artist formation/style facts from being
silently dropped by a syntactically valid tool plan. It never reads labels,
entity answers, files or model history, and never authorizes an extra tool.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import re

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import build_scope,Scope


@dataclass(frozen=True)
class RequestObligation:
    kind: str
    evidence: str
    object: str | None = None
    entity: str | None = None
    fact_detail: str | None = None

    def public(self):
        return asdict(self)


_COUNTS = {
    "album": r"专辑|albums?", "track": r"曲目|歌曲|tracks?|songs?",
    "customer": r"客户|customers?", "invoice": r"发票|invoices?",
    "employee": r"员工|employees?", "playlist": r"歌单|playlists?",
    "artist": r"艺术家|乐队|artists?|bands?",
}
_COUNT = r"多少|几(?:张|个|位|名|首|条|支)|数量|总数|首数|张数|人数|\bcount\b|\bhow many\b|\bnumber\s+of\b"
_AMOUNT = r"销售(?:明细)?(?:额|金额)|发票(?:总额|金额|销售额)|消费金额|明细金额|成交金额|多少钱|(?<![a-z0-9_])revenue(?![a-z0-9_])|(?<![a-z0-9_])sales\s+amount(?![a-z0-9_])"
_SALES_MEASURE = r"(?<![a-z0-9_])sales(?:\s+volume)?(?![a-z0-9_])|销量"
_NUMERIC_REQUEST = r"多少|计算|统计|查询|汇总|加总|求|合计|总额|最高|最低|排名|返回|列出|\b(?:what|show|return|calculate|total|sum|how much)\b"
# A requested total of purchased/sold units is distinct from the number of
# catalog objects. These are natural-language task identities, not a choice of
# SUM/COUNT, a document definition or proof that any SQL implements the metric.
_SALES_UNITS = (r"(?:销售|售出|卖出|卖了|购买|买了)\s*(?:的\s*)?(?:总\s*)?(?:份数|件数|数量)"
                r"|(?:销售|售出|卖出|卖|购买|买)(?:了)?\s*(?:多少|几)\s*(?:份|件)")
# Keep original-question classification and proposed-step matching on the same
# bounded date vocabulary. A date fact is still distinct from people/background.
_FORMATION_DATE = r"何时|什么时候|哪(?:一)?年|何年|几年|时间|年份|\bwhen\b|\bdate\b|\byear\b"
_DEBUT_CN = r"(?:首张|第一张)\s*(?:(?:录音室|[（(]\s*录音室\s*[）)])\s*)?专辑"
_DEBUT_ALBUM = _DEBUT_CN + r"|\b(?:debut|first)\s+(?:studio\s+)?album\b"
_RELEASE_DATE = (r"(?:哪(?:一)?年|何年|何时|什么时候)\s*(?:发行|发布|推出|首发|发的)"
                 r"|(?:发行|发布|推出|首发)(?:于)?(?:哪(?:一)?年|何年|何时|什么时候)"
                 r"|(?:发行|发布)(?:年份|日期|时间)"
                 r"|\b(?:when|(?:what|which)\s+year)\b[^，,；;。！？!?\n]{0,64}\breleased\b")
_FACTS = {
    "artist_debut": _DEBUT_ALBUM,
    "artist_background": r"公开背景|(?:公开简介|乐队简介|艺术家简介|歌手简介)(?!里|中|内|的)|音乐人生平|\b(?:artist|band|musician)\s+(?:biography|background|profile)\b",
    "artist_members": r"(?:核心)?成员(?:名单|名录)|(?:核心)?成员.{0,10}(?:谁|哪些|包括|都有)|(?:谁|哪些人).{0,10}(?:核心)?成员|(?<![a-z0-9_])(?:members?|lineup)(?![a-z0-9_])",
    "artist_themes": r"(?:作品|歌词|歌曲).{0,8}(?:题材|主题)|题材.{0,10}(?:什么|哪些)|\blyrical\s+themes?\b",
    "formation": r"(?:何时|什么时候|哪(?:一)?年|何年|几年|谁|哪些人|when|who).{0,12}(?:成立|组建|formed|founded)|(?:成立|组建)(?:时间|年份|背景|经过|于哪|在哪年|于何年)|(?:组建者|创始人).{0,8}(?:是谁|有哪些|包括谁)|\b(?:formation|founding)\s+(?:date|year)\b|\b(?:when|(?:what|which)\s+year)\b[^，,；;。！？!?\n]{0,48}\b(?:formed|founded)\b",
    "music_style": r"(?:介绍|说明|描述|什么|哪些|哪种|怎样|如何).{0,14}(?:音乐风格|音乐类型|曲风|风格|(?<![a-z0-9_])style(?![a-z0-9_]))|(?:音乐风格|曲风|风格).{0,10}(?:是什么|有哪些|怎样)|\b(?:music(?:al)?\s+style)\b|\bwhat\b.{0,45}\b(?:style|genre)\b|(?<![a-z0-9_])genre(?![a-z0-9_])(?:\s*(?:是什么|有哪些|怎样))?\s*$",
    "release_year": _RELEASE_DATE,
}


def _clauses(question):
    return [part.strip() for part in re.split(r"[。！？!?；;，,\n]", question) if part.strip()]


def document_music_release_clauses(question):
    """Only explicit music-document release-date questions, not every profile.

    The shared planner may protect an explicitly requested document fact even
    when component 1 is off. This function selects no document, value or year.
    Colloquial ``哪年发的`` needs an actual source-container assertion, so a
    profile's own update/publication date is not treated as an album release.
    """
    if not re.search(r'专辑|唱片|录音室|曲目|歌曲|单曲|乐队|艺术家|(?<![a-z0-9_])(?:albums?|tracks?|songs?|bands?|artists?)(?![a-z0-9_])', question, re.I):
        return ()
    found = []
    for clause in _clauses(question):
        source = re.search(r'(?<![a-z0-9_])profile(?![a-z0-9_])|简介|资料|文档', clause, re.I)
        date = re.search(_RELEASE_DATE, clause, re.I)
        if not source or not date or _negated(clause, source) or _negated(clause, date):
            continue
        if re.search(r'例如|比如|示例|例句|假设|如果|(?:翻译|解释).{0,8}(?:这句话|问法)', clause):
            continue
        if re.search(r'(?:先不答|不要回答|不用回答|无需回答)', clause[date.end():]):
            continue
        if '发的' in date.group() and not re.search(
                r'(?:里|中|上|内)\s*(?:说|写|记载|提到|介绍|记录)', clause[source.end():date.start()]):
            continue
        found.append(clause)
    return tuple(found)


def _entity_names(documents):
    names = set()
    for document in documents:
        ref = document.get('entity_ref', '') or ''
        if ref.startswith('chinook:artist:') and len(ref.split(':',3)) == 4:
            names.add(ref.split(':',3)[3])
    return sorted(names, key=len, reverse=True)


def _named_entities(question, names):
    return tuple(name for name in names if re.search(r'(?<![A-Za-z0-9])'+re.escape(name)+r'(?![A-Za-z0-9])',question,re.I))


def _document_entities(question, documents):
    """Literal registered title names identify documents, never SQL bindings.

    Only the bounded Chinese name segment in an artist's actual registration
    title is eligible. Colliding names are unverified. This does not read the
    conditional value-alias index or choose a catalog identity for SQL.
    """
    names = _entity_names(documents)
    found = set(_named_entities(question, names))
    aliases = {}
    for document in documents:
        ref = document.get('entity_ref') or ''
        if not ref.startswith('chinook:artist:') or len(ref.split(':', 3)) != 4:
            continue
        name = ref.split(':', 3)[3]
        title = document.get('title') or ''
        match = re.fullmatch(re.escape(name) + r'\s+([\u4e00-\u9fff]{2,24}(?:乐队|乐团|组合))\s*公开简介', title)
        if match:
            aliases.setdefault(match[1], set()).add((name, ref))
    for alias, targets in aliases.items():
        if len(targets) == 1 and alias in question:
            found.add(next(iter(targets))[0])
    return tuple(name for name in names if name in found)


def _distributive_artist_reference(question, clause):
    # A plural document reference plus an explicit distributive in the same
    # sentence can refer back to the already named set. A singular ambiguous
    # pronoun cannot silently stand for all previously mentioned artists.
    for sentence in re.split(r'[。！？!?；;\n]', question):
        if (clause in sentence
                and re.search(r'(?:那|这|上述|前述)(?:几|些|\d+|[一二三四五六七八九十])?(?:份|支|位|个)?(?:乐队简介|艺术家简介|公开简介|简介|乐队|艺术家|bands?|artists?)', sentence, re.I)
                and re.search(r'分别|各自|逐一|逐个|逐支', sentence)):
            return True
    return False


def _check_explicit_entity_list(prefix,names):
    """An explicitly coordinated unknown target must not disappear.

    This is only a finite name-list check, not open-domain entity recognition.
    With a partially registered list, unexplained subject text is unverified.
    """
    # A new clause beginning "和资料里那份 U2 简介" coordinates tasks, not
    # an unknown artist with U2. Unknown names within a real list still fail.
    prefix = re.sub(r'^\s*(?:和|与|及|以及|\band\b|&)\s*', '', prefix, flags=re.I)
    if not _named_entities(prefix,names)or not re.search(r'和|与|及|、|\band\b|&',prefix,re.I):
        return
    head=re.split(r'各有|分别有|各自有|有多少|的专辑|的曲目|并(?:且)?|以及|同时',prefix,maxsplit=1)[0]
    for name in names:
        head=re.sub(re.escape(name),'',head,flags=re.I)
    head=re.sub(r'根据|依据|文档|资料|介绍|请问|乐队|艺术家|歌手|分别|各自|各|它们|这两支|这两个|的|和|与|及|、|\band\b|&|\s','',head,flags=re.I)
    if head.strip('，,：:()（）“”"「」'):
        raise ValueError('显式多实体名单中存在未能对应实际登记来源的对象，不能只回答其中已知对象。')


def _negated(clause, match):
    # Only a local negative request suppresses this obligation. A name alone,
    # unrelated preceding clause or a document quotation does not add a tool.
    prefix = clause[max(0, match.start() - 32):match.start()]
    return bool(re.search(r"(?:不要|无需|不用|不必|(?<!分)别)(?:再|去|额外)?[^，,；;。并但而只]{0,22}$", prefix))


def _set_selector(clause, count):
    """These demonstratives select an existing set; they do not ask its size."""
    return (count.group().startswith('几') and bool(re.search(
        r'(?:那|这|哪|某|上述|前述|关注的|提到的)\s*$',clause[:count.start()])))


def _numeric_entities(clause, clause_entities, whole_entities):
    # Only an explicit singular artist anaphor with one registered antecedent.
    # A bare generic numeric question does not inherit arbitrary artist names.
    if clause_entities:
        return clause_entities
    if len(whole_entities)==1 and re.search(
            r'(?:这位|该|这个|此)(?:\s*)(?:artist|艺术家|乐队|歌手)|\bthis\s+artist\b',clause,re.I):
        return whole_entities
    return (None,)


def _affirmative_numeric_request(clause):
    for match in re.finditer(_NUMERIC_REQUEST, clause, re.I):
        prefix = clause[:match.start()]
        if (_negated(clause, match) or re.search(r'例如|举例|示例|假设|如果', prefix)
                or any(prefix.count(left) > prefix.count(right)
                       for left, right in (('“', '”'), ('「', '」'), ('‘', '’')))
                or prefix.count('"') % 2):
            continue
        return True
    return False


def _numeric_plan_question(question):
    # A parenthetical date/scope annotation is part of its enclosing task.
    # Preserve every word; only avoid treating its internal comma as a new
    # instruction. Unbalanced text retains the original conservative splitter.
    depth = 0
    result = []
    for char in question:
        if char in '([（【':
            depth += 1
        elif char in ')]）】':
            depth -= 1
            if depth < 0:
                return question
        result.append(' ' if depth and char in ',，' else char)
    return ''.join(result) if depth == 0 else question


def _sales_unit_object_gap(gap):
    if re.fullmatch(r'\s*(?:的|内|中|里的|内的|中的)?\s*', gap):
        return True
    # A calendar-qualified object remains that object. Recognizing this finite
    # grammatical attachment proves neither the period nor a SQL expression.
    # Keep parentheses containing commas together only in this numeric matcher;
    # do not join unrelated clauses or erase arbitrary intervening predicates.
    date = r'\d{4}-(?:\d{2})-(?:\d{2})'
    date_field = r'(?:[A-Za-z_][A-Za-z_0-9.]*|(?:发票|开票)(?:日期|时间))'
    annotation = (r'[（(]\s*按\s*' + date_field + r'\s*[，,]\s*'
                  r'(?:半开|左闭右开)区间\s*\[\s*' + date + r'\s*,\s*' + date
                  + r'\s*[)\]]\s*[）)]')
    gap = re.sub(annotation, '', gap, count=1)
    calendar = r'(?:' + date + r'|\d{4}\s*年)'
    return bool(re.fullmatch(r'\s*在\s*' + calendar + r'(?:\s*(?:至|到)\s*' + calendar
                             + r')?\s*(?:期间)?\s*(?:内|中)?\s*(?:的)?\s*', gap))


def _sales_governing_action_positive(clause, noun):
    # The governing verb can be far from the quantity after a calendar/scope
    # attachment. Do not let a trailing "合计/返回" revive "不要统计...曲目...".
    # This affects sale-unit task matching only, not global negation or metric
    # authorization. Unknown attachments are still rejected by the gap grammar.
    actions = list(re.finditer(r'计算|统计|查询|汇总|加总|求和|返回|列出', clause[:noun.start()]))
    if not actions:
        return True
    action = actions[-1]
    prefix = clause[max(0, action.start() - 32):action.start()]
    return not (_negated(clause, action) or re.search(
        r'(?:不需要|无须)(?:再|去)?[^，,；;。并但而只]{0,22}$', prefix))


def _sales_units(clause):
    """Finite, affirmative unit requests with a nearby explicit object noun."""
    if not _affirmative_numeric_request(clause):
        return []
    found = []
    for match in re.finditer(_SALES_UNITS, clause):
        prefix = clause[:match.start()]
        if (_negated(clause, match)
                or re.search(r'例如|举例|示例|假设|如果', prefix)
                or any(prefix.count(left) > prefix.count(right)
                       for left, right in (('“', '”'), ('「', '」'), ('‘', '’')))
                or prefix.count('"') % 2):
            continue
        objects = [(match.start() - noun.end(), obj)
                   for obj, pattern in _COUNTS.items()
                   for noun in re.finditer(pattern, clause, re.I)
                   if 0 <= match.start() - noun.end() <= 220
                   and not _negated(clause, noun)
                   and _sales_governing_action_positive(clause, noun)
                   and _sales_unit_object_gap(clause[noun.end():match.start()])]
        if objects:
            found.append((match, min(objects)[1]))
    return found


def debut_requires_document(question, catalog=None):
    """A music-history first release is not the smallest catalog primary key."""
    if not re.search(_DEBUT_ALBUM,question,re.I):
        return False
    from qa_agent.context import current_context
    runtime=current_context()
    user_sources=[question]+([runtime.text] if runtime and runtime.text else [])
    for text in user_sources:
        for clause in _clauses(text):
            if (re.search(_DEBUT_ALBUM,clause,re.I) and re.search(r'按|指|定义|以|就是|为',clause)
                    and re.search(r'(?:专辑)?编号|专辑\s*ID|\balbum[_ ]?id\b',clause,re.I)
                    and re.search(r'最小|最低|升序.{0,5}第一|从小到大.{0,5}第一|按编号(?:升序)?(?:的)?第一条',clause)
                    and not re.search(r'不要|不按|不是|并非|不能|不代表|是否|是不是|难道',clause)):
                return False
    if catalog is not None:
        try:
            columns=set(catalog.get_table('album').column_names)
        except (ValueError,KeyError):
            columns=set()
        chronology=columns&{'release_date','release_year','released_at','released_year','release_order','release_sequence'}
        studio=not re.search(r'录音室|\bstudio\b',question,re.I) or bool(columns&{'album_type','release_type','is_studio','studio_album'})
        if chronology and studio:
            return False
    return True


def request_obligations(question: str, *, documents=(), catalog=None) -> list[RequestObligation]:
    obligations = []
    documents = tuple(documents)
    names = _entity_names(documents)
    whole_entities = _named_entities(question, names)
    document_entities = _document_entities(question, documents)
    release_clauses = set(document_music_release_clauses(question))
    clauses = _clauses(question)
    for clause_index, clause in enumerate(clauses):
        if asks_definition_only(clause):
            continue
        clause_entities=_named_entities(clause,names)
        def add_count(obj, detail=None):
            for entity in clause_entities or (None,):
                obligations.append(RequestObligation('database_quantity',clause,obj,entity,detail))
        clause_quantity=False
        sales_units = _sales_units(clause)
        for _, obj in sales_units:
            add_count(obj, 'purchased_units')
            clause_quantity=True
        for count in re.finditer(_COUNT, clause, re.I):
            if (_negated(clause,count) or _set_selector(clause,count)
                    or (count.group() == '多少' and clause[count.end():].startswith('钱'))
                    or any(match.start() <= count.start() and count.end() <= match.end()
                           for match, _ in sales_units)):
                continue
            following=[]
            preceding=[]
            for obj, pattern in _COUNTS.items():
                # Count attaches to a nearby noun, not every noun occurring in
                # a multi-part clause ("band formed ... how many albums").
                for noun in re.finditer(pattern,clause,re.I):
                    if count.end()<=noun.start()<=count.end()+5:
                        following.append((noun.start()-count.end(),obj))
                    elif (not re.fullmatch(r'number\s+of',count.group(),re.I)
                          and noun.end()<=count.start()<=noun.end()+6
                          and not re.search(_AMOUNT,clause[noun.end():count.start()],re.I)
                          and not re.search(r'总额|金额',clause[noun.end():count.start()])):
                        preceding.append((count.start()-noun.end(),obj))
            closest=following or preceding
            if closest:
                add_count(min(closest)[1])
                clause_quantity=True
            elif (count.group() == '几张' and re.search(r'标题', clause)
                    and clause_index > 0 and re.search(_COUNTS['album'], clauses[clause_index-1], re.I)):
                # A comma does not drop an explicit album-count request:
                # "...albums，标题包含X的有几张". This only adds an output
                # obligation; it does not infer a value, predicate or SQL.
                add_count('album')
                clause_quantity=True
        for obj,pattern in _COUNTS.items():
            noun_count=re.search(r'(?:'+pattern+r')(?:的)?(?:数量|总数|首数|张数|人数|数)',clause,re.I)
            if noun_count and not _negated(clause,noun_count):
                add_count(obj)
                clause_quantity=True
        for kind, pattern in _FACTS.items():
            if kind == 'release_year' and clause not in release_clauses:
                continue
            if kind=='artist_debut' and not debut_requires_document(question,catalog):
                continue
            if kind == 'artist_background' and not whole_entities and not re.search(
                    r'乐队|艺术家|歌手|\b(?:artist|band|musician)\b', question, re.I):
                continue
            match = re.search(pattern, clause, re.I)
            if match and not _negated(clause, match):
                if (kind == 'artist_background' and len(document_entities) == 1
                        and re.fullmatch(r'(?:资料|文档)(?:里|中|内)(?:的)?那(?:篇|份)'
                            r'(?:它|该乐队|这支乐队)的(?:乐队|艺术家)?公开简介', clause)
                        and clause_index + 1 < len(clauses)
                        and any(not _negated(clauses[clause_index + 1], detail)
                            for detail_kind in ('formation', 'artist_members', 'artist_themes', 'music_style')
                            for detail in re.finditer(_FACTS[detail_kind], clauses[clause_index + 1], re.I))):
                    # Singular registered-document container followed by its
                    # explicit requested fact; not an extra full biography.
                    continue
                if (kind == 'artist_background' and len(document_entities) > 1
                        and re.fullmatch(r'(?:(?:资料|文档)(?:里|中|内)(?:的)?)?(?:那|这|上述|前述)'
                            r'(?:几|[二三四五六七八九十0-9]+)份(?:乐队|艺术家|歌手)?(?:公开)?简介', clause)
                        and clause_index + 1 < len(clauses)
                        and _distributive_artist_reference(question, clause)
                        and any(not _negated(clauses[clause_index + 1], detail)
                            for detail_kind in ('formation', 'artist_members', 'artist_themes', 'music_style')
                            for detail in re.finditer(_FACTS[detail_kind], clauses[clause_index + 1], re.I))):
                    # "Those profiles, respectively what year/city formed?"
                    # names the source of the adjacent specific facts. It does
                    # not additionally request each artist's entire biography.
                    continue
                if (kind == 'artist_background'
                        and re.fullmatch(r'销售(?:数字|数据|金额)和公开背景分开(?:给我|展示|说明|列出)', clause)
                        and set(document_entities) <= {o.entity for o in obligations if o.kind in _FACTS}):
                    # This repeats the already bound document task as a
                    # presentation instruction, not a new singular subject.
                    continue
                _check_explicit_entity_list(clause[:match.start()],names)
                entities = _document_entities(clause, documents)
                if not entities and len(document_entities)==1:
                    entities = document_entities
                if not entities and len(document_entities)>1:
                    if re.search(r'分别|各(?:自)?|逐一|逐个|逐支',clause) or _distributive_artist_reference(question,clause):
                        # Check the actual coordinated named set as well; a
                        # plural reference must not erase an unknown member.
                        for source_clause in _clauses(question):
                            named = _named_entities(source_clause, names)
                            if len(named) > 1:
                                first = min(re.search(re.escape(name), source_clause, re.I).start() for name in named)
                                head = source_clause[:first]
                                if not re.search(r'和|与|及|、|\band\b|&',head,re.I):
                                    source_clause = source_clause[first:]
                                _check_explicit_entity_list(source_clause, names)
                        entities=document_entities
                    else:
                    # An unbound pronoun after several entities is not proof
                    # that any one named document covers all of them.
                        raise ValueError('多个实际登记实体的文档子问题未明确对应对象，完整性尚未核实。')
                for entity in entities or (None,):
                    detail = None
                    if kind == 'artist_debut':
                        detail = 'studio' if re.search(r'录音室|\bstudio\b', clause, re.I) else 'album'
                    elif kind == 'formation':
                        detail = ('people' if re.search(r'谁|哪些人|组建者|创始人|\bwho\b', clause, re.I)
                                  else 'date' if re.search(_FORMATION_DATE, clause, re.I) else 'background')
                    obligations.append(RequestObligation(kind, clause, entity=entity,fact_detail=detail))
        amount=re.search(_AMOUNT,clause,re.I)
        if (amount and not _negated(clause,amount)
                and _affirmative_numeric_request(clause)
                and not re.search(r"(?:定义|口径).{0,8}(?:是什么|如何解释|说明)$", clause)):
            for entity in _numeric_entities(clause,clause_entities,whole_entities):
                obligations.append(RequestObligation("database_amount",clause,entity=entity))
        measure=re.search(_SALES_MEASURE,clause,re.I)
        if (measure and not amount and not clause_quantity and not _negated(clause,measure)
                and _affirmative_numeric_request(clause)):
            for entity in _numeric_entities(clause,clause_entities,whole_entities):
                obligations.append(RequestObligation("database_measure",clause,entity=entity))
    return list(dict.fromkeys(obligations))


def clearly_database_question(question: str) -> bool:
    """Only positive database requests; selecting documents is not a request."""
    obligations = request_obligations(question)
    if any(o.kind in _FACTS for o in obligations):
        return False
    if any(o.kind.startswith("database_") for o in obligations):
        return True
    return bool(re.search(r"发票|销售额|销售金额|消费金额|购买数量|账单", question)
                and re.search(r"多少|统计|计算|求|汇总|排名|最高|最低|合计|总额", question)
                and not re.search(r"定义|口径|手册|资料|文档|正文|解释", question))


def asks_definition_only(question: str) -> bool:
    """Explain a formula is not authorization to calculate a database value."""
    if not re.search(r'手册|口径|定义|公式',question):
        return False
    if not re.search(r'怎么算|如何计算|计算方法|计算公式|公式是什么|定义是什么|什么定义|怎么定义|如何定义|解释|说明',question):
        return False
    for delivery in re.finditer(r'(?:把|将)[^，,；;。！？!?\n]{0,80}(?:' + _AMOUNT + r')', question, re.I):
        prefix = question[:delivery.start()]
        if (_negated(question, delivery)
                or re.search(r'(?:不需要|无须)(?:再|去)?\s*$', prefix)
                or re.search(r'例如|举例|示例|假设|如果', prefix)
                or any(prefix.count(left) > prefix.count(right)
                       for left, right in (('“', '”'), ('「', '」'), ('‘', '’')))
                or prefix.count('"') % 2
                or re.match(r'\s*[”」’"]?\s*(?:的)?(?:定义|口径|公式|计算方法)', question[delivery.end():])):
            continue
        sentence = re.split(r'[。！？!?；;\n]', question[delivery.start():], maxsplit=1)[0]
        if re.search(r'(?:不计算|不查询|不统计|不汇总|(?:不用|不要|无需|不必|不需要)(?:再)?(?:计算|查询|统计|汇总))', sentence):
            continue
        if re.search(r'放在一起|并列(?:展示|给我|呈现|说明)', sentence):
            # Delivering an actual amount alongside a document fact remains a
            # numeric task when the final writing instruction says "explain
            # the basis". It does not choose that amount's metric or period.
            return False
    # A separate request for a real value/dimension is still a computation;
    # its missing period belongs to the existing clarification gate.
    calculation=re.sub(r'怎么算|如何计算|计算方法|计算公式','',question)
    return not bool(re.search(r'算一下|计算一下|求出|算出|(?:再|另(?:外)?|并(?:且)?)(?:统计|查询|计算|列出)|再查(?:询)?(?:一下)?(?:数据库|库里)|计算.{0,18}(?:客户|美国|加拿大|销售额|发票|\d{4}\s*年)|\d{4}\s*年.{0,18}(?:客单价|金额|客户数|发票数|客户数量)|(?:客单价|客户数|发票数|销售额|金额)(?:数值|是多少)|有多少(?:个|名|位)?客户|有多少张发票',calculation))


def explicit_new_task(question: str) -> bool:
    """A complete new query must not be captured by a bare ^按/^用 prefix.

    Short slot replies such as 按发票张数/按2024年 remain genuine resumes.
    A client-supplied card ID is checked separately and always takes priority.
    """
    return bool(re.search(r'统计|查询|列出|计算',question)
                and re.search(r'\d{4}\s*年',question)
                and clearly_database_question(question))


def _matches(obligation, question):
    if obligation.kind=='artist_debut':
        return bool(re.search(_DEBUT_ALBUM,question,re.I) and
                    (obligation.fact_detail!='studio' or re.search(r'录音室|\bstudio\b',question,re.I)))
    if obligation.kind == "formation":
        if not re.search(r"成立|组建|创始人|\bformed\b|\bfounded\b|\bformation\b", question, re.I):
            return False
        detail={'people':r'谁|哪些人|组建者|创始人|\bwho\b|\bfounders?\b',
                'date':_FORMATION_DATE,
                'background':r'背景|经过|过程|\bbackground\b'}.get(obligation.fact_detail)
        return detail is None or bool(re.search(detail,question,re.I))
    if obligation.kind == "music_style":
        return bool(re.search(r"音乐风格|音乐类型|曲风|风格|(?<![a-z0-9_])(?:style|genre)(?![a-z0-9_])", question, re.I))
    if obligation.kind == 'release_year':
        return any(not _negated(question, match) for match in re.finditer(_RELEASE_DATE, question, re.I))
    if obligation.kind == 'artist_themes':
        if any(not _negated(question, match)
               for match in re.finditer(_FACTS['artist_themes'], question, re.I)):
            return True
        # Tool subtasks are often imperatives, not repeated user questions.
        # This adds no original-question obligation or entity/source authority.
        return any(not _negated(question, match) and not re.search(
            r'不要|无需|不用|不必|不需要|不涉及|不包含|不是|并非', match.group())
            for match in re.finditer(r'(?:提取|概括|归纳|介绍|说明|列出)'
                r'[^，,；;。！？!?\n]{0,24}题材(?:所)?(?:涉及(?:的)?方面|内容|方面)', question))
    if obligation.kind in {'artist_background','artist_members','artist_themes'}:
        return any(not _negated(question, match)
                   for match in re.finditer(_FACTS[obligation.kind], question, re.I))
    proposed = request_obligations(_numeric_plan_question(question))
    if obligation.kind == 'database_quantity' and obligation.fact_detail == 'purchased_units':
        # The ordinary clause splitter intentionally separates commas. A plan's
        # parenthesized calendar annotation may contain commas, so use the same
        # bounded attachment matcher once on the intact step as well. This does
        # not authorize inventory counts, a different object or a SQL formula.
        if any(obj == obligation.object for _, obj in _sales_units(question)):
            return True
    if obligation.kind=='database_measure':
        # An unspecified sales measure asks for a numeric database result, not
        # an invented monetary default. A sale quantity is eligible, a catalog
        # album count is not. The SQL semantic gate still determines the metric.
        return any(p.kind in {'database_measure','database_amount'} or
                   (p.kind=='database_quantity' and re.search(
                       r'购买|卖出|售出|销售|销量|\b(?:sold|purchased|sales)\b',question,re.I))
                   for p in proposed)
    return any(p.kind == obligation.kind and p.object == obligation.object
               and (obligation.kind != 'database_quantity' or p.fact_detail == obligation.fact_detail)
               for p in proposed)


def _derived_artist_request(question):
    return bool(re.search(r'(?:最高|第一|冠军|最多).{0,10}(?:艺术家|乐队|歌手|(?<![a-z0-9_])(?:artists?|bands?)(?![a-z0-9_]))|(?:艺术家|乐队|歌手|(?<![a-z0-9_])(?:artists?|bands?)(?![a-z0-9_])).{0,12}(?:最高|第一|冠军|最多)',question,re.I))


def _actual_artist_refs(dependencies,outputs,documents,catalog=None):
    """Bounded lineage: physical artist PK/name projections and real rows.

    Direct, CTE and derived-table transparent columns are supported. Arithmetic,
    casts, constants, set operations and unrelated unused CTEs cannot establish
    identity. A step name or free-form model prose is not an entity binding.
    """
    registry={d['entity_ref'] for d in documents if (d.get('entity_ref')or'').startswith('chinook:artist:')}
    found=set()
    for dependency in dependencies:
        output=outputs.get(dependency)or{}
        if output.get('source')!='database'or output.get('status')!='SUCCEEDED':
            continue
        try:
            if catalog is not None:
                from qa_agent.sql.repair_guard import _qualified
                tree=_qualified(output.get('sql')or'',catalog)
            else:
                tree=sqlglot.parse_one(output.get('sql')or'',read='postgres')
            scope=build_scope(tree)
        except (sqlglot.errors.SqlglotError,ValueError):
            continue
        if not isinstance(tree,exp.Select)or not scope:
            continue
        if len({p.alias_or_name for p in tree.expressions})!=len(tree.expressions):
            continue
        def identity(node,owner,depth=0):
            if depth>12 or node is None:return None
            while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
            if not isinstance(node,exp.Column):return None
            selected=owner.selected_sources.get(node.table)
            if selected is None and not node.table and len(owner.selected_sources)==1:
                selected=next(iter(owner.selected_sources.values()))
            source=selected[1]if selected else None
            if isinstance(source,exp.Table):
                return node.name if(source.db or'public')=='public'and source.name=='artist'and node.name in{'name','artist_id'}else None
            if isinstance(source,Scope)and isinstance(source.expression,exp.Select):
                projections=[p for p in source.expression.expressions if p.alias_or_name==node.name]
                return identity(projections[0],source,depth+1)if len(projections)==1 else None
            return None
        keys={}
        for projection in tree.expressions:
            field=identity(projection,scope)
            if field:keys[field]=projection.alias_or_name
        # Chinook artist.name is not UNIQUE. Name coincidence cannot choose a
        # registered document for a different real artist with the same name.
        if 'artist_id'not in keys:
            continue
        for row in output.get('table')or[]:
            if not isinstance(row,dict):
                continue
            for ref in registry:
                parts=ref.split(':',3)
                matches=[]
                if len(parts)==4 and keys.get('artist_id')in row:
                    matches.append(str(row[keys['artist_id']])==parts[2])
                if len(parts)==4 and keys.get('name')in row:
                    matches.append(str(row[keys['name']]).casefold()==parts[3].casefold())
                if matches and all(matches):
                    found.add(ref)
    return found


def prove_obligation_coverage(question, plan, *, allowed_tools, outputs=None, documents=(),catalog=None):
    """Verify supported explicit obligations against actual plan/tool outputs.

    A fact needs a document/context step which actually asks that fact. A
    database numeric request needs a matching SQL step when SQL is authorized. Source
    restrictions remain upper bounds: this function cannot grant SQL or RAG.
    RAG correctness and literal citations are still checked by their own tool.
    """
    records = []
    documents = tuple(documents)
    doc_entities = {d.get('doc_id'):_entity_names([d]) for d in documents}
    obligations=request_obligations(question,documents=documents,catalog=catalog)
    by_id={step.step_id:step for step in plan.steps}
    def ancestors(step):
        found=set(step.depends_on)
        for key in tuple(found):
            found.update(ancestors(by_id[key]))
        return found
    for obligation in obligations:
        database_obligation = obligation.kind.startswith("database_")
        tools = ({"sql"} if database_obligation else {"doc", "context"}) & set(allowed_tools)
        if obligation.kind=='artist_debut':
            tools={'doc'} & set(allowed_tools)
        # A body-only question can count facts in the body; it is not an
        # implicit request to query the similarly named database table.
        if database_obligation and "sql" not in allowed_tools:
            tools = {"context", "doc"} & set(allowed_tools)
        def entity_matches(step):
            if obligation.entity is None:
                if obligation.kind not in _FACTS:
                    return True
                if step.tool=='context':
                    return obligation.evidence in step.question or question in step.question
                # An unregistered named entity cannot be substituted by any
                # convenient registered artist document. Only a genuinely
                # requested SQL-selected artist can acquire its identity later.
                return (_derived_artist_request(question) and bool(step.depends_on)
                        and any(prior.step_id in step.depends_on and prior.tool=='sql'for prior in plan.steps))
            named = _named_entities(step.question,[obligation.entity])
            selected = {name for doc_id in step.doc_ids for name in doc_entities.get(doc_id,())}
            if obligation.kind == 'artist_debut' and step.doc_ids:
                return selected == {obligation.entity}
            return bool(named or obligation.entity in selected)
        matches = [step for step in plan.steps if step.tool in tools and _matches(obligation, step.question) and entity_matches(step)]
        if not matches:
            raise ValueError("执行计划未覆盖原问题明确要求的" + obligation.kind + "，未将不完整计划交付为成功答案。")
        if obligation.kind=='artist_debut':
            fact_ids={step.step_id for step in matches}
            for numeric in obligations:
                if not numeric.kind.startswith('database_') or numeric.entity!=obligation.entity:
                    continue
                consumers=[step for step in plan.steps if step.tool=='sql' and _matches(numeric,step.question)]
                if any(not ancestors(step)&fact_ids for step in consumers):
                    raise ValueError('首张专辑的数据库计算必须依赖对应艺术家文档中实际核验的首专身份，不能按编号或首行猜测。')
        actual = []
        if outputs is not None:
            for step in matches:
                value = outputs.get(step.step_id)
                if not isinstance(value, dict):
                    continue
                expected = {"sql": "database", "doc": "documents", "context": "user_session_context"}[step.tool]
                if value.get("source") != expected:
                    continue
                if step.tool == "sql" and not value.get("sql"):
                    continue
                if step.tool == "doc" and value.get("status") == "SUCCEEDED" and not value.get("evidences"):
                    continue
                if step.tool == 'doc' and obligation.entity:
                    returned = {name for evidence in value.get('evidences',()) for name in doc_entities.get(evidence.get('doc_id'),())}
                    if obligation.entity not in returned and value.get('status')=='SUCCEEDED':
                        continue
                if step.tool=='doc'and obligation.kind in _FACTS and obligation.entity is None:
                    expected_refs=_actual_artist_refs(step.depends_on,outputs,documents,catalog)
                    returned_refs={d.get('entity_ref')for d in documents if any(e.get('doc_id')==d.get('doc_id')for e in value.get('evidences',()))}
                    if not expected_refs or not expected_refs<=returned_refs:
                        continue
                if step.tool == "context" and not value.get("quotes"):
                    continue
                actual.append(step.step_id)
            if not actual:
                raise ValueError("原问题要求的" + obligation.kind + "没有对应的真实工具证据，不能交付完整成功答案。")
        records.append({**obligation.public(), "planned_step_ids": [s.step_id for s in matches],
                        "actual_step_ids": actual if outputs is not None else None})
    return {"verified": True, "bounded_supported_obligations": records,
            "boundary": "Only explicit supported quantities, monetary/generic sales numeric requests and formation/music-style facts; generic measure does not select a metric. Not a general semantic proof."}


def debut_album_identities(question, dependencies, documents):
    """Read a bounded debut assertion from actual document excerpts, never answer text.

    ``documents`` is the already hash-verified registration selected by the tool.
    Model plans/answers cannot supply a title or artist primary key for this proof.
    """
    from hashlib import sha256
    documents = tuple(documents)
    names = _named_entities(question, _entity_names(documents))
    if len(names) != 1:
        raise ValueError('首张专辑对象不能唯一对应实际登记的艺术家资料，尚未核实。')
    artist = names[0]
    found = []
    studio = bool(re.search(r'录音室|\bstudio\b', question, re.I))
    for step_id, output in dependencies.items():
        if (output.get('source') != 'documents' or output.get('status') != 'SUCCEEDED'
                or output.get('warnings')):
            continue
        for evidence in output.get('evidences', ()):
            text = evidence.get('text')
            if not isinstance(text, str):
                continue
            registered = [d for d in documents if d.get('doc_id') == evidence.get('doc_id')
                          and artist in _entity_names([d])]
            if len(registered) != 1:
                continue
            document = registered[0]
            ref = document.get('entity_ref', '')
            if ref not in output.get('entity_refs', ()):
                continue
            # A finite source grammar, not open-world discography inference.
            # Require the same explicit artist in the source sentence.
            for sentence in re.finditer(r'[^。！？!?\n]+', text):
                source = sentence.group()
                subject = re.search(r'(?<![A-Za-z0-9])' + re.escape(artist) + r'(?![A-Za-z0-9])', source, re.I)
                if not subject:
                    continue
                tail = source[subject.end():]
                marker = re.search(r'(?:发行|推出|发表)\s*(?:了|其)?\s*' + _DEBUT_CN + r'\s*', tail)
                source_studio = bool(marker and '录音室' in marker.group())
                if not marker or (studio and not source_studio):
                    continue
                prefix = tail[:marker.start()]
                if len(prefix) > 45 or re.search(r'并非|不是|没有|未曾|不代表|误称|据传|可能', source[:subject.end()+marker.end()]):
                    continue
                rest = tail[marker.end():]
                title = re.match(r'[《“\"]([^》”\"\n]{1,160})[》”\"]|([A-Za-z0-9][A-Za-z0-9 .:&\x27()!+\-/]{0,159})(?=[，,。；;]|$)', rest)
                if not title:
                    continue
                value = (title[1] or title[2]).strip()
                if not value:
                    continue
                start = sentence.start() + subject.end() + marker.start()
                end = sentence.start() + subject.end() + marker.end() + title.end()
                found.append({'artist': artist, 'artist_id': ref.split(':', 3)[2],
                              'entity_ref': ref, 'album_title': value, 'studio': source_studio,
                              'step_id': step_id, 'doc_id': evidence.get('doc_id'),
                              'evidence_id': evidence.get('evidence_id'),
                              'text_sha256': sha256(text.encode('utf-8')).hexdigest(),
                              'quote': text[start:end], 'char_start': start, 'char_end': end,
                              'document_content_hash': document.get('content_hash')})
    identities = {(p['entity_ref'], p['album_title']) for p in found}
    if len(identities) != 1:
        raise ValueError('实际艺术家文档未提供唯一、可逐字核验的首张专辑标题，不能按编号或首行猜测。')
    return found[0]


def debut_artist_lookup_context(question, documents):
    """Only a registry-bound artist identity may precede debut document lookup."""
    documents = tuple(documents)
    names = _named_entities(question, _entity_names(documents))
    if len(names) != 1:
        raise ValueError('首专文档前的艺术家查询没有唯一登记对象，不能猜身份。')
    selected = [d for d in documents if names[0] in _entity_names([d])]
    refs = {d.get('entity_ref') for d in selected}
    if len(refs) != 1:
        raise ValueError('同名艺术家的登记主键不唯一，不能自动选择。')
    ref = next(iter(refs))
    parts = ref.split(':', 3)
    if not parts[2].isdigit():
        raise ValueError('艺术家登记主键无法核验。')
    return {'debut_identity_lookup': True,
            'debut_artist_identity': {'entity_ref': ref, 'artist_id': parts[2], 'artist': parts[3]},
            'debut_documents': [{key: d.get(key) for key in ('doc_id','title','entity_ref','content_hash')}
                                for d in selected]}


def debut_required_sql_predicates(identity, catalog):
    """Project only actual document/registration facts onto proven catalog fields.

    Called with ``debut_album_identities`` output, never a model plan's fields.
    This is a compact generation handoff; the independent SQL consumer still
    reconstructs the source proof and checks real WHERE/ON consumption.
    """
    try:
        album = catalog.get_table('album', 'public')
        artist = catalog.get_table('artist', 'public')
        owner_fk = any(fk.get('columns') == ['artist_id'] and fk.get('references') == {
            'schema':'public', 'table':'artist', 'columns':['artist_id']}
            for fk in album.foreign_keys)
        if (not {'artist_id','title'} <= album.column_names
                or artist.primary_key != ('artist_id',) or not owner_fk):
            raise ValueError('首专身份没有实际专辑到艺术家的目录外键。')
    except (ValueError, KeyError, AttributeError) as exc:
        raise ValueError('无法把首专实际来源绑定到真实目录字段。') from exc
    if (not str(identity.get('artist_id','')).isdigit() or not identity.get('album_title')
            or not identity.get('entity_ref') or not identity.get('quote')
            or not identity.get('text_sha256') or not identity.get('document_content_hash')):
        raise ValueError('首专实际文档身份记录不完整，不能生成字段条件。')
    registry_source = {key:identity[key] for key in
        ('doc_id','entity_ref','step_id','document_content_hash')}
    quote_source = {**registry_source, **{key:identity[key] for key in
        ('evidence_id','text_sha256','quote','char_start','char_end')}}
    return [
        {'column':'public.album.artist_id', 'operator':'=', 'value':int(identity['artist_id']),
         'source':{'kind':'registered_artist_entity_ref', **registry_source}},
        {'column':'public.album.title', 'operator':'=', 'value':identity['album_title'],
         'source':{'kind':'actual_document_debut_quote', **quote_source}},
    ]


def _validate_debut_artist_lookup(sql, catalog, question, context):
    """No album, track, aggregate, CTE, join or date/order inference is allowed."""
    from qa_agent.sql.validator import SQLValidationError
    from qa_agent.sql.repair_guard import _qualified
    def deny():
        raise SQLValidationError('首专前置查询只能读取当前唯一艺术家的真实主键和名称，不能查询专辑、聚合或推断首专。')
    expected = debut_artist_lookup_context(question, context.get('debut_documents', ()))
    if context.get('debut_artist_identity') != expected['debut_artist_identity']:
        deny()
    target = expected['debut_artist_identity']
    try:
        tree = _qualified(sql, catalog)
        scope = build_scope(tree)
        sources = list(scope.selected_sources.items()) if scope else []
        if catalog.get_table('artist').primary_key != ('artist_id',):
            deny()
    except Exception as exc:
        raise SQLValidationError('首专前置艺术家查询无法通过真实目录核验。') from exc
    if (not isinstance(tree, exp.Select) or tree.find(exp.CTE) or tree.args.get('joins')
            or tree.args.get('group') or tree.args.get('having') or tree.args.get('qualify') or len(sources) != 1
            or len(list(tree.find_all(exp.Select))) != 1):
        deny()
    alias, (_, source) = sources[0]
    if not isinstance(source, exp.Table) or source.name != 'artist' or (source.db or 'public') != 'public':
        deny()
    fields = []
    aliases = []
    for projection in tree.expressions:
        node = projection.this if isinstance(projection, exp.Alias) else projection
        if not isinstance(node, exp.Column) or node.table != alias or node.name not in {'artist_id','name'}:
            deny()
        fields.append(node.name)
        aliases.append(projection.alias_or_name)
    if set(fields) != {'artist_id','name'} or len(fields) != 2 or len(set(aliases)) != 2:
        deny()
    def atoms(node):
        if isinstance(node, (exp.Where, exp.Paren)): return atoms(node.this)
        if isinstance(node, exp.And): return atoms(node.left) + atoms(node.right)
        return [node]
    proved_pk = False
    proved_name = False
    for atom in atoms(tree.args.get('where')):
        if not isinstance(atom, exp.EQ): deny()
        left, right = atom.left, atom.right
        if isinstance(right, exp.Column): left, right = right, left
        if not isinstance(left, exp.Column) or left.table != alias or not isinstance(right, exp.Literal): deny()
        wanted = {'artist_id':target['artist_id'], 'name':target['artist']}.get(left.name)
        if wanted is None or str(right.this) != wanted: deny()
        proved_pk = proved_pk or left.name == 'artist_id'
        proved_name = proved_name or left.name == 'name'
    if not proved_pk and not proved_name: deny()
    if not proved_pk:
        # Name is not UNIQUE. Fetching at least two matching rows lets the
        # actual-result check reject duplicates; LIMIT1/OFFSET/DISTINCT ON may
        # hide a second identity and therefore cannot establish uniqueness.
        limit = tree.args.get('limit')
        value = limit.expression if limit else None
        distinct = tree.args.get('distinct')
        if (tree.args.get('offset') or distinct and distinct.args.get('on')
                or limit is not None and not isinstance(limit, exp.Limit)
                or value is not None and (not isinstance(value, exp.Literal) or value.is_string
                    or not str(value.this).isdigit() or int(value.this) < 2)):
            deny()
    return {'applicable': True, 'verified': True, 'method':'registry_artist_identity_lookup_only',
            'artist_identity': target, 'actual_result_identity_required': True,
            'debut_album_identity_proved': False}


def validate_debut_artist_lookup_result(sql, table, catalog, generation_context):
    """Bind only one actual returned PK/name before consuming the document.

    A syntactically exact-name lookup is permitted, but a name alone never
    selects among several database identities. No additional query is issued.
    """
    from qa_agent.sql.validator import SQLValidationError
    from qa_agent.sql.repair_guard import _qualified
    context = generation_context
    question = context.get('original_question', '')
    proof = _validate_debut_artist_lookup(sql, catalog, question, context)
    tree = _qualified(sql, catalog)
    keys = {}
    for projection in tree.expressions:
        node = projection.this if isinstance(projection, exp.Alias) else projection
        keys[node.name] = projection.alias_or_name
    target = proof['artist_identity']
    if (not isinstance(table, list) or len(table) != 1 or not isinstance(table[0], dict)
            or set(table[0]) != set(keys.values())
            or str(table[0].get(keys['artist_id'])) != target['artist_id']
            or table[0].get(keys['name']) != target['artist']):
        raise SQLValidationError('实际艺术家查询未返回唯一且与登记对象一致的主键/名称；不选择首行，不继续首专文档和曲目计算。')
    return {**proof, 'actual_result_identity_verified': True, 'actual_row_count': 1}


def validate_debut_album_sql(sql, catalog, generation_context=None):
    """Prove that a debut-dependent SQL consumes the actual document identity.

    Supported shapes: physical album/artist joins, and track.album_id IN/= a
    single-column physical album selection. Unknown CTE/OR/identity transforms
    fail conservatively; existing general SQL guards remain mandatory.
    """
    from qa_agent.context import current_context
    from qa_agent.sql.validator import SQLValidationError
    from qa_agent.sql.repair_guard import _qualified
    from sqlglot.optimizer.scope import traverse_scope
    runtime = current_context()
    context = generation_context or {}
    question = context.get('original_question') or (runtime.current_user_message if runtime else '')
    if not debut_requires_document(question, catalog):
        return {'applicable': False, 'verified': True}
    if context.get('debut_identity_lookup') is True:
        return _validate_debut_artist_lookup(sql, catalog, question, context)
    def deny(message):
        raise SQLValidationError('首张专辑身份尚未核实：' + message)
    try:
        identity = debut_album_identities(question, context.get('debut_dependencies', context.get('dependencies', {})),
                                         context.get('debut_documents', ()))
    except ValueError as exc:
        deny(str(exc))
    if context.get('debut_album_identity') != identity:
        deny('缺少来自实际文档依赖的程序身份记录。')
    try:
        tree = _qualified(sql, catalog)
        scopes = list(traverse_scope(tree))
    except Exception:
        deny('SQL物理投影无法核验。')
    root_scope = next((s for s in scopes if s.expression is tree), None)
    if (not isinstance(tree, exp.Select) or root_scope is None or tree.find(exp.CTE)
            or any(isinstance(source, Scope) for s in scopes for _, source in s.selected_sources.values())):
        deny('WITH或派生来源尚未建立到最终曲目结果的消费证明。')
    if not any(isinstance(source, exp.Table) and (source.db or 'public') == 'public'
               and source.name == 'track' for _, source in root_scope.selected_sources.values()):
        deny('最终结果没有消费真实曲目来源，不能借未使用子查询证明首专。')
    if any(isinstance(s.expression, (exp.Union, exp.Intersect, exp.Except)) for s in scopes):
        deny('集合语法未在首专身份证明范围内。')
    verified = {}
    all_tracks = []
    def conjuncts(node):
        if node is None:
            return []
        if isinstance(node, (exp.Where, exp.Paren)):
            return conjuncts(node.this)
        if isinstance(node, exp.And):
            return conjuncts(node.left) + conjuncts(node.right)
        return [node]
    def literal(node, value):
        return isinstance(node, exp.Literal) and str(node.this) == str(value)
    for scope in scopes:
        select = scope.expression
        if not isinstance(select, exp.Select):
            continue
        physical = {alias: source for alias, (_, source) in scope.selected_sources.items()
                    if isinstance(source, exp.Table) and (source.db or 'public') == 'public'}
        # Derived sources must be explicitly consumed by a supported IN/scalar
        # selection below, never treated as physical identity by alias spelling.
        atoms = conjuncts(select.args.get('where'))
        for join in select.args.get('joins', ()):
            if join.args.get('side') or join.args.get('kind') in {'CROSS', 'OUTER'}:
                continue
            atoms += conjuncts(join.args.get('on'))
        def field(node, table, column, alias=None, physical=physical):
            return (isinstance(node, exp.Column) and node.name == column and node.table in physical
                    and physical[node.table].name == table and (alias is None or node.table == alias))
        def equal(left, right, atoms=atoms):
            return any(isinstance(a, exp.EQ) and ((left(a.left) and right(a.right))
                         or (left(a.right) and right(a.left))) for a in atoms)
        protected = set()
        for alias, table in physical.items():
            if table.name != 'album':
                continue
            title_ok = equal(lambda n: field(n, 'album', 'title', alias),
                             lambda n: literal(n, identity['album_title']))
            owner_ok = equal(lambda n: field(n, 'album', 'artist_id', alias),
                             lambda n: literal(n, identity['artist_id']))
            for artist_alias, artist_table in physical.items():
                if artist_table.name != 'artist':
                    continue
                joined = equal(lambda n: field(n, 'album', 'artist_id', alias),
                               lambda n: field(n, 'artist', 'artist_id', artist_alias))
                bound = (equal(lambda n: field(n, 'artist', 'artist_id', artist_alias),
                               lambda n: literal(n, identity['artist_id'])))
                # Registry PK is required. Names alone are not unique.
                owner_ok = owner_ok or joined and bound
            if title_ok and owner_ok:
                protected.add(alias)
        verified[id(select)] = (scope, protected)
        for alias, table in physical.items():
            if table.name == 'track':
                all_tracks.append((scope, alias, atoms, equal, field, protected))
    for scope, alias, atoms, equal, field, protected in all_tracks:
        direct = any(equal(lambda n: field(n, 'track', 'album_id', alias),
                           lambda n, a=a: field(n, 'album', 'album_id', a)) for a in protected)
        if direct:
            continue
        consumed = False
        for atom in atoms:
            nested = None
            if isinstance(atom, exp.In) and field(atom.this, 'track', 'album_id', alias):
                nested = atom.args.get('query')
            elif isinstance(atom, exp.EQ):
                if field(atom.left, 'track', 'album_id', alias): nested = atom.right
                elif field(atom.right, 'track', 'album_id', alias): nested = atom.left
            if isinstance(nested, exp.Subquery): nested = nested.this
            if not isinstance(nested, exp.Select) or id(nested) not in verified:
                continue
            owner, albums = verified[id(nested)]
            projections = nested.expressions
            if len(projections) != 1 or not albums:
                continue
            projection = projections[0].this if isinstance(projections[0], exp.Alias) else projections[0]
            if isinstance(projection, exp.Column) and projection.name == 'album_id' and projection.table in albums:
                consumed = True
        if not consumed:
            deny('曲目计算没有消费文档标题及对应艺术家主键限定的真实专辑。需要实际 '
                 + 'public.album.artist_id=' + identity['artist_id'] + ' 与 public.album.title='
                 + repr(identity['album_title']) + ' 在WHERE/ON中消费；名称不能替主键。')
    if not all_tracks or not any(p for _, p in verified.values()):
        deny('未发现已消费的专辑标题/艺术家主键来源。')
    return {'applicable': True, 'verified': True, 'method': 'document_debut_title_and_artist_primary_key',
            'identity': identity, 'boundary': 'physical joins or album-id IN/scalar selection; no catalog-id chronology inference'}
