"""Component 1 music-fact routing advice; no entity or tool authorization.

An artist's members, lyrical themes or first studio release are not COUNTs of
the music store catalog. A hint may enter the existing composed planner, which
still owns source scope, document identity, clarification and execution.
"""
from __future__ import annotations

from hashlib import sha256
import re

from qa_agent.nlu.linker import _contains_word_boundary, _normalized_source
from qa_agent.nlu.value_index import normalize
from qa_agent.source_scope import source_restriction


_MUSIC_ROLES = re.compile(r'乐队|艺术家|音乐人|歌手|专辑|\b(?:bands?|artists?|musicians?|singers?|albums?)\b', re.I)
_DATABASE_REQUEST = re.compile(
    r'数据库|数据表|表中|表里|字段|列名|SQL|Chinook|AdventureWorks|'
    r'\b(?:database|column|select|where|join|sum|count|avg|group\s+by|order\s+by)\b|'
    r'统计|汇总|发票|账单|订单|销售额|销售量|销量|消费|金额|购买|客户|单价|'
    r'时长|毫秒|字节|平均|合计|总数|排名|最多|最少|'
    r'(?:多少|几)\s*(?:首|张|条)?\s*(?:曲目|歌曲|专辑)|'
    r'\b(?:revenue|sales|invoice|purchases?|customers?|milliseconds|bytes|duration)\b|'
    r'\bhow\s+many\s+(?:tracks?|songs?|albums?)\b', re.I)
_ONLY_DATABASE_ACTION = re.compile(r'(?:只|仅|只能|仅能)\s*(?:允许|可以)?\s*(?:查询|查|访问|使用)\s*(?:数据库|数据表|SQL|Chinook)|'
    r'\bonly\s+(?:query|use|access)\s+(?:the\s+)?(?:database|SQL|Chinook)\b', re.I)

# Each family is bounded to actual music facts. The catalog's existing columns
# take precedence: this helper does not declare that a DB can never hold facts.
_FACTS = {
    'background': re.compile(r'公开背景|公开简介|乐队简介|艺术家简介|歌手简介|音乐人生平|'
        r'\b(?:artist|band|musician)\s+(?:biography|background|profile)\b', re.I),
    'members': re.compile(r'成员|主唱|吉他手|鼓手|贝斯手|键盘手|创始人|创办人|组建者|'
        r'\b(?:members?|lineup|vocalists?|guitarists?|drummers?|bassists?|founders?)\b', re.I),
    'style': re.compile(r'音乐风格|演奏风格|风格|曲风|\b(?:musical\s+style|music\s+style|genre|style)\b', re.I),
    'themes': re.compile(r'题材|歌词主题|歌词内容|作品主题|作品内容|歌曲主题|'
        r'\b(?:lyrical\s+themes?|lyrics?\s+themes?|themes?)\b', re.I),
    'formation': re.compile(r'(?:成立|组建|创立|成军).{0,12}(?:哪年|哪一年|何年|几年|年份|时候|时间)|'
        r'(?:哪年|哪一年|何年|什么时候).{0,12}(?:成立|组建|创立|成军)|'
        r'\b(?:when|what\s+year).{0,40}\b(?:formed|founded|established)\b', re.I),
    'release_year': re.compile(r'(?:发行|发布|推出|首发).{0,12}(?:哪年|哪一年|何年|年份|时候|时间)|'
        r'(?:哪年|哪一年|何年|什么时候).{0,12}(?:发行|发布|推出|首发)|'
        r'\b(?:when|what\s+year).{0,45}\b(?:released|release|published)\b', re.I),
    'debut_studio_album': re.compile(r'(?:首张|第一张|首部|出道).{0,8}录音室.{0,5}专辑|'
        r'\b(?:debut|first)\s+studio\s+album\b', re.I),
    'first_album': re.compile(r'(?:首张|第一张).{0,8}专辑|最早(?:发行|发布|推出)(?:的)?.{0,8}专辑|'
        r'\b(?:first|earliest\s+released)\s+album\b', re.I),
}
_ATTRIBUTES = {
    'background': {'biography','background','profile','bio','artist_background','artist_profile'},
    'members': {'member','members','member_name','member_names','lineup','personnel','vocalist','lead_singer','guitarist','drummer','bassist','founder','founders'},
    'style': {'genre','genre_id','style','styles','music_style','musical_style'},
    'themes': {'theme','themes','lyrical_theme','lyrical_themes','lyrics'},
    'formation': {'formation_year','formed_year','founding_year','founded','formed','formation_date','founded_date'},
    'release_year': {'release_year','released_year','release_date','released_at','publication_year','publication_date'},
}


def _indexed_entities(question, index, catalog):
    """Preserve all actual same-span candidates, including conditional aliases."""
    tables={table.name:table for table in catalog.tables if table.schema=='public'}
    fields={field for field in ('artist.name','album.title')
        if field.split('.')[0] in tables and field.split('.')[1] in tables[field.split('.')[0]].column_names}
    rows=[record for record in index.records if record.column in fields and len(record.surface.strip())>=2]
    if not rows:return [],set()
    view,offsets=_normalized_source(question)
    occurrences={}
    for record in rows:
        pattern=r'\s+'.join(re.escape(part) for part in normalize(record.surface).split())
        if not pattern:continue
        for match in re.finditer(pattern,view,re.I):
            start,end=offsets[match.start()],offsets[match.end()-1]+1
            if not _contains_word_boundary(question,start,end,record.surface):continue
            key=(start,end)
            candidate={'column':record.column,'value':record.standard_value,'candidate_id':record.candidate_id,
                'evidence_ref':record.alias_id or record.candidate_id,
                'binding_policy':'candidate_only' if record.kind=='conditional_alias' else 'direct'}
            if candidate not in occurrences.setdefault(key,[]):occurrences[key].append(candidate)
    entities=[]
    for (start,end),candidates in sorted(occurrences.items(),key=lambda row:(-(row[0][1]-row[0][0]),row[0][0])):
        if any(start<other['span'][1] and other['span'][0]<end for other in entities):continue
        identities={(row['column'],row['candidate_id']) for row in candidates}
        ambiguous=len(identities)!=1 or any(row['binding_policy']=='candidate_only' for row in candidates)
        entities.append({'surface':question[start:end],'span':[start,end],
            'identity_status':'ambiguous_index_identity' if ambiguous else 'unique_index_identity',
            'candidates':candidates,'selected_candidate_id':None})
    return sorted(entities,key=lambda row:row['span'][0]),fields


def _catalog_track_genre_request(question, tables):
    """A literal track-category request is answered by the actual genre FK.

    This only avoids inventing an absent artist-profile attribute. It neither
    binds the artist nor proves the generated SQL, and it never suppresses an
    explicit document/style-description subtask.
    """
    track, genre = tables.get('track'), tables.get('genre')
    if (track is None or genre is None or 'genre_id' not in track.column_names
            or not {'genre_id', 'name'} <= genre.column_names):
        return False
    if not any(fk.get('columns') == ['genre_id']
               and fk.get('references', {}).get('schema', 'public') == 'public'
               and fk.get('references', {}).get('table') == 'genre'
               and fk.get('references', {}).get('columns') == ['genre_id']
               for fk in track.foreign_keys):
        return False
    clauses = re.split(r'[，,；;。！？!?\n]', question)
    style = r'曲风|流派|音乐风格|(?<![a-z0-9_])(?:genres?|styles?)(?![a-z0-9_])'
    for clause in clauses:
        if _FACTS['style'].search(clause) and re.search(
                r'简介|资料|文档|介绍|描述|讲讲|(?<![a-z0-9_])(?:profile|biography|describe)(?![a-z0-9_])', clause, re.I):
            return False
    return any(re.search(
        r'(?:曲目|歌曲|(?<![a-z0-9_])(?:tracks?|songs?)(?![a-z0-9_]))[^，,；;。！？!?\n]{0,24}'
        r'(?:几(?:个|种|类)|哪些|哪几(?:个|种|类)|多少(?:种|类))\s*(?:' + style + r')',
        clause, re.I) for clause in clauses)


def music_fact_route_hint(question, *, index, catalog, nlu_enabled, semantic_gate_enabled,
                          route='auto', restriction=None):
    """Return a bounded ``composed`` suggestion or None, with no side effects.

    ``restriction`` may be the caller's actual SourceRestriction. Both its
    authority and the current source instruction must remain unrestricted.
    Candidate-only/unknown music identities may need document clarification;
    a route hint never promotes them to a binding or selects a document.
    """
    if nlu_enabled is not True or semantic_gate_enabled is not False or route!='auto':return None
    if not isinstance(question,str) or not question.strip() or index is None or catalog is None:return None
    local=source_restriction(question)
    for scope in (local,restriction or local):
        if getattr(scope,'mode',None)!='unrestricted' or 'doc' not in getattr(scope,'allowed_tools',()):return None
    if _ONLY_DATABASE_ACTION.search(question):return None
    entities,fields=_indexed_entities(question,index,catalog)
    if not fields:return None
    music_role=_MUSIC_ROLES.search(question)
    if not entities and music_role is None:return None
    # Names are evidence of objects, not evidence of a fact request themselves.
    surface=list(question)
    for item in entities:
        a,b=item['span'];surface[a:b]=' '*(b-a)
    surface=''.join(surface)
    def positive_fact(pattern):
        for match in pattern.finditer(surface):
            prefix=re.split(r'[，,；;。！？!?\n]',surface[:match.start()])[-1]
            if not re.search(r'(?:不要|无需|不用|不必|不需要|do\s+not|don.t)\s*[^，,；;。！？!?\n]{0,18}$',prefix,re.I):
                return True
        return False
    facts=[kind for kind,pattern in _FACTS.items() if positive_fact(pattern)]
    from qa_agent.fusion.obligations import document_music_release_clauses
    document_release = bool(document_music_release_clauses(question))
    if document_release and 'release_year' not in facts:
        facts.append('release_year')
    if not facts:return None
    tables={table.name:table for table in catalog.tables if table.schema=='public'}
    columns={name:table.column_names for name,table in tables.items()}
    missing=[]
    for kind in facts:
        if kind == 'style' and _catalog_track_genre_request(question, tables):
            available = True
        elif kind=='debut_studio_album':
            # A min album ID is not a release-order proof. Existing release
            # date AND studio-type fields are needed to keep this in DB scope.
            available=bool(columns.get('album',set()) & _ATTRIBUTES['release_year']) and bool(
                columns.get('album',set()) & {'album_type','release_type','is_studio','studio_album'})
        elif kind=='first_album':
            available=bool(columns.get('album',set()) & _ATTRIBUTES['release_year'])
        else:
            table='album' if kind=='release_year' else 'artist'
            available=bool(columns.get(table,set()) & _ATTRIBUTES[kind])
        if not available or kind == 'release_year' and document_release:missing.append(kind)
    if not missing:return None
    if _DATABASE_REQUEST.search(question) and not set(missing)&{'first_album','debut_studio_album'}:
        # A sales filter by style is still SQL. A separate explicit request to
        # introduce/describe a missing fact needs the existing composed tools.
        explicit_fact_request=(bool(set(missing)&{'background','members','themes','formation','release_year'})
            and bool(re.search(r'另外|此外|同时|一并|一起|也|再|还|并|\balso\b|\band\b',question,re.I)))
        explicit_fact_request = explicit_fact_request or document_release
        if 'style' in missing and re.search(r'(?:介绍|描述|说明|讲讲).{0,25}(?:音乐风格|曲风|风格)|'
                r'(?:音乐风格|曲风|风格).{0,10}(?:是什么|有哪些|怎样)',question):
            explicit_fact_request=True
        if not explicit_fact_request:return None
    if not entities:
        entities=[{'surface':music_role.group(),'span':[music_role.start(),music_role.end()],
            'identity_status':'unresolved_music_role','candidates':[],'selected_candidate_id':None}]
    return {'route':'composed','reason':'indexed_music_fact_not_in_catalog',
        'fact_kinds':facts,'missing_catalog_attributes':missing,'entities':entities,
        'question_sha256':sha256(question.encode()).hexdigest(),
        'authority':'advisory_only','semantic_verified':False,
        'source_scope_unchanged':True,'executes_tools':False}
