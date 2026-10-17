"""Only a complete sort-only edit may retain one proved hiring query."""
from __future__ import annotations
from copy import deepcopy
import re


def temporal_sort_delta(message,previous,catalog):
    if previous is None or previous.phase not in {'ANSWERED','FAILED'}:return None
    role=previous.analysis.query_scope.get('temporal_field_role') or {}
    if role.get('source')!='program:explicit_temporal_field_role' or role.get('role')!='hire_date':return None
    if not role.get('source_evidence') or role['source_evidence'] not in previous.original_question:return None
    from qa_agent.clarify.temporal_role import explicit_temporal_field_role,literal_hire_calendar_period
    from qa_agent.clarify.rules import SemanticIntent
    proof=SemanticIntent()
    explicit_temporal_field_role(previous.original_question,proof,catalog)
    if (proof.query_scope.get('temporal_field_role') or {}).get('column')!=role.get('column'):return None
    literal=literal_hire_calendar_period(previous.original_question)
    current=(previous.analysis.time_scope or {}).get('current') or {}
    if not literal or previous.analysis.time_ambiguous or any(current.get(key)!=literal[key] for key in ('start','end')):return None
    columns={'姓氏':'employee.last_name','名字':'employee.first_name','员工编号':'employee.employee_id',
             'employee.last_name':'employee.last_name','employee.first_name':'employee.first_name','employee.employee_id':'employee.employee_id'}
    field='|'.join(re.escape(name) for name in columns)
    match=re.fullmatch(r'\s*(?:那)?(?:再)?按\s*(?P<field>'+field+r')\s*(?P<direction>升序|降序|ASC|DESC)?\s*(?:排(?:一下)?序|排序)\s*[。？！?!]?\s*',message,re.I)
    if match is None:return None
    column=columns[match['field'].casefold()]
    if previous.analysis.grouping and column not in previous.analysis.grouping:return None
    if not any(table.name=='employee' and any(c.name==column.split('.')[1] for c in table.columns) for table in catalog.tables):return None
    word=(match['direction'] or '').casefold()
    direction='asc' if word in {'asc','升序'} else 'desc' if word in {'desc','降序'} else None
    return {'field':column,'direction':direction}


def apply_temporal_sort_delta(state,message,order):
    from qa_agent.clarify.state import IntentPatch,apply_patches
    requests=[deepcopy(item) for item in state.analysis.clarification_requests if item.get('field')!='order']
    if order['direction'] is None:
        requests.append({'field':'order','question':'姓氏、名字或员工编号需要升序还是降序排列？',
            'reason':'本轮只指定排序字段，没有授权默认方向；入职条件和期间继续保留。','evidence':message})
    apply_patches(state,[IntentPatch(op='set',path='order',value=order,evidence=message),
                         IntentPatch(op='set',path='clarification_requests',value=requests,evidence=message)],user_message=message)
    state.history.append({'event':'confirmed_temporal_sort_delta','source_evidence':message,
        'retained_fields':['temporal_field_role','time_scope','filters','metric','grouping'],
        'intent_version':state.intent.intent_version})
