"""Recover a named date role only from explicit language and real schema."""
from __future__ import annotations
import re
from datetime import date


def literal_hire_calendar_period(question):
    """A literal half-year/year role, excluding explicit endpoint predicates."""
    if re.search(r'between|介于|之间|截至|截止|\d{1,2}\s*月|\d{4}-\d{1,2}-\d{1,2}',question,re.I):return None
    if len(set(re.findall(r'(?<!\d)(\d{4})\s*年',question)))>1:return None
    half=re.search(r'(?<!\d)(\d{4})\s*年\s*([上下])半年',question)
    if half:
        year=int(half[1])
        if not 1<=year<9999:return None
        return {'start':f'{year:04d}-'+('01-01' if half[2]=='上' else '07-01'),
                'end':f'{year:04d}-07-01' if half[2]=='上' else f'{year+1:04d}-01-01'}
    from qa_agent.clarify.rules import explicit_period
    period=(explicit_period(question) or {}).get('current') or {}
    return {key:period[key] for key in ('start','end')} if period else None


def _literal_temporal_predicate(item,question,analysis,column):
    """Return real period/value only for a plain same-role model predicate."""
    literal=literal_hire_calendar_period(question)
    current=(analysis.time_scope or {}).get('current') or {}
    if not literal or any(literal[key]!=current.get(key) for key in ('start','end')):return None
    calendars=list(re.finditer(r'(?<!\d)\d{4}\s*年\s*(?:[上下]半年)?',question))
    if len(calendars)!=1 or len(re.findall(r'[上下]半年',question))>1 or re.search(r'季度|\bQ[1-4]\b',question,re.I):return None
    role=analysis.query_scope.get('temporal_field_role') or {}
    if (role.get('column')!=column or role.get('role')!='hire_date' or
        role.get('source')!='program:explicit_temporal_field_role' or
        not isinstance(role.get('source_evidence'),str) or not role['source_evidence'] or
        role['source_evidence'] not in question):return None
    if not isinstance(item,dict) or not set(item)<={'field','column','operator','value','values','scope_evidence','binding_scope'}:return None
    if item.get('column') and item.get('field') and item['column']!=item['field']:return None
    if (item.get('column') or item.get('field'))!=column:return None
    if 'binding_scope' in item and item['binding_scope']!='global':return None
    if 'scope_evidence' in item:
        quote=item['scope_evidence']
        if not isinstance(quote,str) or not quote or quote not in question or calendars[0].group().strip() not in quote:return None
    values=[item[key] for key in ('value','values') if key in item]
    if not values or any(type(value) is not type(values[0]) or value!=values[0] for value in values):return None
    return literal,values[0]


def literal_temporal_mirror(item,question,analysis,column):
    """Retire only a proved calendar proposal, not SQL BETWEEN semantics.

    Raw model packets remain in the existing immutable provider capture.
    """
    plain=_literal_temporal_predicate(item,question,analysis,column)
    if plain is None or str(item.get('operator','')).upper()!='BETWEEN':return False
    literal,value=plain
    return (type(value) is list and value==[literal['start'],literal['end']] or
            type(value) is dict and set(value)=={'start','end'} and value==literal)


def normalize_literal_temporal_mirror(question,analysis,column):
    filters=analysis.query_scope.get('qualification_filters')
    if filters is None:return
    if not isinstance(filters,list) or any(not isinstance(item,dict) for item in filters):
        raise ValueError('入职日期资格筛选必须为对象数组；未知形状不能丢弃或作为已确认条件。')
    dates=[item for item in filters if column in (item.get('column'),item.get('field'))]
    pair=False
    if len(dates)==2:
        proved=[_literal_temporal_predicate(item,question,analysis,column) for item in dates]
        if all(value is not None for value in proved):
            pair=({(str(item.get('operator','')).upper(),value[1]) for item,value in zip(dates,proved)
                   if isinstance(value[1],str)}=={('>=',proved[0][0]['start']),('<',proved[0][0]['end'])})
    analysis.query_scope['qualification_filters']=[item for item in filters
        if not (pair and item in dates) and not literal_temporal_mirror(item,question,analysis,column)]


def explicit_temporal_field_role(question,analysis,catalog):
    if not re.search(r'员工|雇员|employees?',question,re.I) or not re.search(r'入职|雇用|雇佣|hired?',question,re.I):
        return analysis
    if re.search(r'出生|生日|birth|发票日期|invoice_date',question,re.I):return analysis
    period=r'(?:\d{4}\s*年?|今年|去年|前年|本年|上半年|下半年)'
    evidence=(re.search(period+r'[^，,。；;？?]{0,20}?(?:入职|雇用|雇佣|hired?)',question,re.I) or
              re.search(r'(?:入职|雇用|雇佣|hire)(?:日期|时间)?\s*(?:在|为|是)?\s*'+period,question,re.I))
    if not evidence:return analysis
    candidates=[f'{table.name}.{column.name}' for table in catalog.tables for column in table.columns
        if table.name.casefold()=='employee' and re.search(r'date|timestamp',column.data_type,re.I) and
        (re.search(r'hire|hired',column.name,re.I) or re.search(r'入职|雇用|雇佣',column.description))]
    if len(candidates)!=1:
        analysis.clarification_requests.append({'field':'temporal_field_role','question':'请确认员工入职时间对应的真实日期字段。',
           'reason':'真实目录中入职日期字段缺失或不唯一，不能按发票日期等其它字段代替。','evidence':evidence.group()})
        return analysis
    analysis.query_scope['temporal_field_role']={'column':candidates[0],'source':'program:explicit_temporal_field_role',
        'source_evidence':evidence.group(),'role':'hire_date'}
    literal=literal_hire_calendar_period(question)
    current=(analysis.time_scope or {}).get('current') or {}
    if literal:
        if any(current.get(key)!=literal[key] for key in ('start','end')):
            analysis.time_scope={'current':{**literal,'grain':'custom','label':evidence.group()}}
        analysis.time_ambiguous=False
        analysis.condition_sources['time_scope']={'source':'explicit_user','evidence':evidence.group(),
            'lifetime':'task','applies_to':'global'}
    normalize_literal_temporal_mirror(question,analysis,candidates[0])
    return analysis
