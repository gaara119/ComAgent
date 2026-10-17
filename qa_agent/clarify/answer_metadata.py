"""Explain actual interaction decisions without inventing a SQL gate."""
from __future__ import annotations


def default_action_hint(level,switch_card):
    if level!='L1':return ''
    options=(switch_card or {}).get('options')or[]
    labels=list(dict.fromkeys(item['label']for item in options
        if isinstance(item,dict)and isinstance(item.get('label'),str)and item['label'].strip()))
    if labels:
        return '可在本条回答的口径选项中切换：'+'；'.join(labels)+'。'
    return '如需调整本题的默认口径，请直接补充新的条件；系统会重新校验后查询。'


def completed_source_only_level(outputs):
    """Classify an actual completed source-only task, not a fabricated SQL state.

    This metadata is not consumed as execution permission. A SQL-containing,
    blocked, failed, empty or unverified plan cannot receive this declaration.
    """
    if not isinstance(outputs,dict)or not outputs:return None
    for output in outputs.values():
        if (not isinstance(output,dict)or output.get('source')not in {'documents','user_session_context'}
            or output.get('status','SUCCEEDED')!='SUCCEEDED'or output.get('warnings')):return None
    return {'level':'L0','state':'ANSWERED','assumptions':[],
        'classification_source':'program:completed_source_only_plan',
        'semantic_gate_executed':False,
        'reason':'已完成的文档或用户正文任务没有未解决的来源问题；此声明不代表执行了SQL语义门控。'}
