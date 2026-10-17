"""Resolved program facts outrank unsupported model uncertainty, narrowly."""
from __future__ import annotations
from copy import deepcopy
import re


def resolved_named_collective(question,analysis,payload):
    if analysis.task_type!='ratio' or analysis.metric!='invoice_revenue' or re.search(r'各(?:个|国|自)|每个|分别|逐国',question):
        return analysis
    from qa_agent.clarify.definition_recovery import complete_definitions,closed_country_members,label_is_referenced
    corpus=str(payload.get('user_brief') or '')
    for label,clauses in complete_definitions(payload).items():
        if len(clauses)!=1 or not label_is_referenced(label,question):continue
        members=closed_country_members(label,clauses[0])
        if not members:continue
        collective=re.search(re.escape(label)+r'的销售额[”"’]?[，,]?[^。；;\n]{0,24}(?:加在一起|合计|加总|总计)',corpus)
        if not collective:continue
        actual=next((item for item in analysis.filters if item.get('source')=='user_session_context' and
            item.get('column')=='invoice.billing_country' and item.get('operator')=='IN' and
            isinstance(item.get('value'),list) and set(item['value'])==set(members) and
            item.get('scope_evidence')==clauses[0]),None)
        if actual is None:continue
        marker=re.search('占',question)
        if marker is None or label not in question[:marker.start()]:continue
        numerator=question[:marker.start()].strip(' ，,')
        analysis.numerator=numerator
        actual['binding_scope']='numerator'
        analysis.query_scope['numerator']={'metric':'invoice_revenue','scope':numerator,'filters':[deepcopy(actual)],
           'source':'program:confirmed_named_collective','source_evidence':numerator,'definition_evidence':collective.group()}
        current=(analysis.time_scope or {}).get('current') or {}
        if current:analysis.query_scope['numerator']['period']={key:current[key] for key in ('start','end')}
        analysis.condition_sources['numerator']={'source':'explicit_user','evidence':numerator,'lifetime':'task','applies_to':'numerator'}
        def same_uncertainty(text):
            return bool(re.search(r'分子',text) and re.search(r'缺失|未指明|不明确|还是',text) and
                re.search(re.escape(label)+r'|合计|各国|具体国家',text) and
                not re.search(r'分母|期间|年份|\d{4}|币种|单位|互斥|相反|不一致',text))
        analysis.conflicts=[text for text in analysis.conflicts if not same_uncertainty(text)]
        analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field')!='numerator']
    return analysis


def resolve_approved_period_uncertainty(question,analysis,payload):
    if not ((analysis.task_type=='ranking' and analysis.rank_object=='customer') or analysis.metric=='repeat_customer_count'):
        return analysis
    if re.search(r'\d{4}|去年|今年|前年|最近|旺季|主期间|对比期|本期|上期|期间|年份|季度|半年|月份|刚才|接着|只要|只看|全部数据|所有数据|不限(?:时间|期间|年份)',question):
        return analysis
    if re.match(r'\s*(?:那|改成|改为|换成)',question):return analysis
    source=analysis.condition_sources.get('time_scope') or {}
    actual_history='\n'.join(str(turn.get('user') or '') for turn in payload.get('actual_conversation',[]) if isinstance(turn,dict))
    if (source.get('lifetime')=='persistent' and source.get('source') in {'confirmed_history','explicit_user'} and
            source.get('evidence') and source['evidence'] in actual_history and
            any(re.search(r'以后|后面都|接下来都|整个会话|本会话都',str(turn.get('user') or '')) and
                source['evidence'] in str(turn.get('user') or '') for turn in payload.get('actual_conversation',[]) if isinstance(turn,dict))):
        return analysis
    analysis.time_scope=None;analysis.time_ambiguous=False
    analysis.condition_sources.pop('time_scope',None)
    def redundant(item):
        text=str(item.get('question') or '')+' '+str(item.get('reason') or '')
        return item.get('field') in {'time_scope','time_scope.current'} and bool(re.search(r'未指定|没有指定|没有给出|未说|默认',text)) and not re.search(r'旺季|最近|去年|今年|\d{4}',text)
    analysis.clarification_requests=[item for item in analysis.clarification_requests if not redundant(item)]
    return analysis
