"""Retain only the immediately referenced, program-confirmed task period."""
from __future__ import annotations
from copy import deepcopy
from datetime import date
import re


def retain_referenced_ratio_period(question,analysis,previous,payload):
    if analysis.task_type!='ratio' or analysis.time_scope or previous.phase not in {'ANSWERED','FAILED'}:
        return False
    if not re.search(r'刚才|上述|上面(?:的)?|前面(?:的)?',question):return False
    if re.search(r'\d{4}|去年|前年|今年|最近|对比期|主期间|本期|上期|改(?:成|为).{0,8}(?:期间|年|月)',question):return False
    history=payload.get('actual_conversation') or []
    if not history or not isinstance(history[-1],dict):return False
    latest=history[-1];intent=latest.get('intent') or {}
    prior=previous.analysis;period=prior.time_scope;current=(period or {}).get('current') or {}
    if prior.time_ambiguous or intent.get('intent_version')!=previous.intent.intent_version:return False
    if intent.get('time_scope')!=period:return False
    try:
        if date.fromisoformat(current['start'])>=date.fromisoformat(current['end']):return False
    except (KeyError,ValueError,TypeError):return False
    source=prior.condition_sources.get('time_scope') or {};quote=str(source.get('evidence') or '')
    corpus=str(payload.get('user_brief') or '')+'\n'+'\n'.join(str(turn.get('user') or '') for turn in history if isinstance(turn,dict))
    trusted=bool(source.get('verified') is True and quote and quote in corpus)
    if not trusted:
        trusted=any(record.get('field')=='time_scope' and record.get('status')=='active' and record.get('source')=='explicit_user'
            and record.get('value')==period and record.get('evidence') and record['evidence'] in str(latest.get('user') or '')
            for record in previous.constraint_ledger)
    if not trusted:return False
    prior_objects={field.split('.')[0] for field in prior.grouping if isinstance(field,str) and '.' in field}
    if prior.rank_object:prior_objects.add(prior.rank_object)
    same_object=bool(analysis.rank_object and analysis.rank_object in prior_objects and analysis.metric==prior.metric)
    explicit_period_reference=bool(re.search(r'(?:刚才|上述|上面).{0,8}(?:期间|月份|旺季)|那.{0,3}个月|同期',question))
    if not same_object and not explicit_period_reference:return False
    evidence=str(latest.get('user') or '')
    if not evidence:return False
    analysis.time_scope=deepcopy(period)
    analysis.time_ambiguous=False
    analysis.condition_sources['time_scope']={'source':'confirmed_history','evidence':evidence,
        'lifetime':'task','applies_to':'global','verified':True,'history_intent_version':previous.intent.intent_version,
        'verification':'immediate_structured_state_and_actual_history_match','prior_period_evidence':quote}
    analysis.evidence_spans['time_scope']=re.search(r'刚才|上述|上面(?:的)?|前面(?:的)?',question).group()
    denominator=analysis.query_scope.get('denominator')
    if isinstance(denominator,dict) and not denominator.get('period'):
        denominator['period']={key:current[key] for key in ('start','end')}
    return True
