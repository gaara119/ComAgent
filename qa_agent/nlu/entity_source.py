"""Resolve a single named entity from actual user source, not planner prose."""
from __future__ import annotations
import re

OWNERS={'artist.name':r'艺术家|乐队|artist|band','album.title':r'专辑|album',
        'genre.name':r'流派|曲风|genre','playlist.name':r'歌单|播放列表|playlist'}

def canonical_spans(text,index,column,value):
    from qa_agent.nlu.linker import _contains_word_boundary
    spans=[]
    longer=[record.surface for record in index.records if record.column==column and record.kind=='standard' and
            len(record.surface)>len(value) and record.surface.casefold().startswith(value.casefold())]
    for match in re.finditer(re.escape(value),text,re.I):
        if not _contains_word_boundary(text,match.start(),match.end(),value):continue
        if any(text[match.start():match.start()+len(name)].casefold()==name.casefold() and
               _contains_word_boundary(text,match.start(),match.start()+len(name),name) for name in longer):continue
        spans.append((match.start(),match.end()))
    return spans

def canonical_mentions(text,index,column):
    found={}
    for record in index.records:
        if record.column!=column or record.kind!='standard' or record.surface!=record.standard_value:continue
        if canonical_spans(text,index,column,record.surface):found[record.standard_value]=record
    return found

def explicit_named_fields(question,index):
    fields=[]
    for column,words in OWNERS.items():
        for value in canonical_mentions(question,index,column):
            for match in re.finditer(re.escape(value),question,re.I):
                before=question[max(0,match.start()-24):match.start()];after=question[match.end():match.end()+18]
                if (re.search(r'(?:'+words+r')(?:\s*(?:里|中|的))?[，,]?\s*$',before,re.I) or
                    re.match(r'\s*(?:的|这位|该|这支)?\s*(?:'+words+r')',after,re.I)):
                    fields.append(column)
    return tuple(sorted(set(fields)))

def literal_polarity(text,value,spans=None):
    """A canonical name does not erase a literal exclusion around that name."""
    from qa_agent.nlu.linker import _contains_word_boundary
    states=[]
    roles='(?:艺术家|乐队|专辑|曲风|流派|歌单|artist|band|album|genre|playlist)'
    for match in re.finditer(re.escape(value),text,re.I):
        if not _contains_word_boundary(text,match.start(),match.end(),value):continue
        if spans is not None and (match.start(),match.end()) not in spans:continue
        before=text[max(0,match.start()-25):match.start()]
        after=text[match.end():match.end()+12]
        excluded=re.search(r'(?:除了?|排除|不包括|不含|不是|并非|不要|不看|不统计|不选(?:择)?|非|\bnot\b|\bexcept(?:\s+for)?\b|\bexclud(?:e|ing)\b|\bwithout\b)\s*(?:'+roles+r'\s*)?$',before,re.I)
        double_negative=excluded and re.search(r'不要|别|不能|并非|不是|不\s*$|\bnot\b',before[:excluded.start()],re.I)
        if double_negative:raise ValueError('真实用户实体含嵌套否定，不能猜测正向或排除关系。')
        states.append('!=' if excluded or re.match(r'\s*(?:以外|之外|除外)',after) else '=')
    if len(set(states))!=1:raise ValueError('真实用户对同一实体的肯定与否定关系未唯一确定。')
    return states[0]

def affirmative_single_definition(clause,value,words):
    """Accept a complete single-name definition, not an example or negation."""
    body=re.split('[:：]',clause,maxsplit=1)[-1].strip()
    return bool(re.fullmatch(r'(?:只指|仅指|指(?:的是)?|就是|是|为)\s*(?:(?:'+words+r')\s*)?[“"‘\']?'+
        re.escape(value)+r'[”"’\']?\s*',body,re.I))

def literal_owner_roles(text,value,spans):
    """A role elsewhere in a sentence does not own this particular name."""
    positive=set();negative=set()
    roles={**OWNERS,'track.name':r'曲目|歌曲|tracks?|songs?'}
    for start,end in spans:
        before=text[max(0,start-24):start];after=text[end:end+28]
        for column,words in roles.items():
            if (re.search(r'(?:'+words+r')(?:\s*(?:里|中|的))?[，,]?\s*$',before,re.I) or
                re.match(r'\s*(?:的|这位|这支|这张|这个|该)?\s*(?:'+words+r')',after,re.I)):
                positive.add(column)
            if re.match(r'\s*(?:这个名字|这(?:个|位|支|张))?\s*(?:不是|并非|is\s+not)\s*(?:'+words+r')',after,re.I):negative.add(column)
    return positive,negative

def actual_source_bindings(question,index):
    from qa_agent.context import current_context
    ctx=current_context()
    if ctx is None:return []
    source=str(getattr(ctx,'current_user_message','') or '')
    if not source:return []
    recovered=[]
    for column,words in OWNERS.items():
        actual=canonical_mentions(source,index,column)
        proposed=canonical_mentions(question,index,column)
        for value in set(actual)&set(proposed):
            actual_roles,excluded_roles=literal_owner_roles(source,value,canonical_spans(source,index,column,value))
            proposed_roles,_=literal_owner_roles(question,value,canonical_spans(question,index,column,value))
            if column in proposed_roles and (column in excluded_roles or actual_roles and column not in actual_roles):
                raise ValueError('子步骤改变了真实用户明确的实体字段归属，不能以同名其它类型替代。')
            if literal_polarity(source,value,canonical_spans(source,index,column,value))!=literal_polarity(question,value,canonical_spans(question,index,column,value)):
                raise ValueError('编排子步骤改变了真实用户明确的实体肯定/排除关系，不能执行。')
        if len(actual)!=1 or not re.search(words,source,re.I) or not re.search(words,question,re.I):continue
        value,record=next(iter(actual.items()))
        actual_roles,excluded_roles=literal_owner_roles(source,value,canonical_spans(source,index,column,value))
        if column not in actual_roles or column in excluded_roles:continue
        if proposed and set(proposed)!={value}:
            raise ValueError('编排子步骤的实体与真实本轮用户原句中的唯一明确实体不一致，不能执行。')
        if not proposed and not re.search(r'这位|这支|该艺术家|该乐队|这(?:个|张|种)|该(?:专辑|流派|歌单)',question):continue
        recovered.append({'column':column,'operator':literal_polarity(source,value,canonical_spans(source,index,column,value)),'value':value,'source':'verified_value_index',
            'method':'actual_user_canonical','evidence_ref':record.candidate_id,'scope_evidence':source,
            'source_quote':source,'lifetime':'task','session_id':ctx.session_id})
    # A user-defined name may have a single real canonical referent. A four-
    # artist list such as "关注艺术家" never chooses one member by itself.
    from qa_agent.clarify.definition_recovery import complete_definitions,label_is_referenced
    for label,clauses in complete_definitions(ctx.prompt_payload()).items():
        if len(clauses)!=1 or not label_is_referenced(label,source):continue
        clause=clauses[0]
        for column,words in OWNERS.items():
            actual=canonical_mentions(clause,index,column)
            if len(actual)!=1 or not re.search(words,label+clause,re.I) or not re.search(words,question,re.I):continue
            value,record=next(iter(actual.items()));proposed=canonical_mentions(question,index,column)
            if not affirmative_single_definition(clause,value,words):continue
            if proposed and set(proposed)!={value}:raise ValueError('子步骤实体违反实际完整单实体定义。')
            if any(item['column']==column for item in recovered):continue
            recovered.append({'column':column,'operator':'=','value':value,'source':'verified_value_index',
                'definition_source':'user_session_context','method':'actual_single_entity_definition','evidence_ref':record.candidate_id,
                'scope_evidence':clause,'source_quote':clause,'lifetime':'task','session_id':ctx.session_id})
    return recovered
