"""Keep a model-proposed denominator from impersonating user authority."""
from __future__ import annotations
import re
from copy import deepcopy

PENDING_DENOMINATOR='用户已选择自行指定本题分母，等待明确分母条件。'


def literal_denominator(question):
    assigned=re.search(r'分母\s*(?:改为|换成|采用|使用|用|取|为|是)\s*([^，,。；;？?]+)',question)
    if assigned and re.search(r'发票|账单|销售额|金额|收入|曲目|客户',assigned.group(1)):
        return assigned.group(1).strip()
    ratio=re.search(r'占(?:了)?\s*(?P<scope>[^，,。；;？?]{2,80}?)(?:的)?(?:比例|占比|百分)',question)
    if ratio and re.search(r'发票|账单|销售额|金额|收入|全部|整体|全年|同期|曲目',ratio['scope']):
        return re.sub('的$','',ratio['scope'].strip())
    ratio=re.search(r'(?:与|和)\s*(?P<scope>[^，,。；;？?]{2,60}?)(?:的)?之比',question)
    if ratio and re.search(r'发票|账单|销售额|金额|收入|全部|整体|曲目',ratio['scope']):return ratio['scope'].strip()
    compared=re.search(r'(?:与|和|跟)\s*(?P<scope>[^，,。；;？?]{2,40}?)(?:相比|比)[^。；;？?]*(?:占比|比例)',question)
    if compared and re.search(r'国家|市场|地区|客户|发票|账单|金额|销售额',compared['scope']):
        return compared['scope'].strip()
    return None


def ground_denominator_authority(question,analysis,payload):
    if analysis.task_type!='ratio':return analysis
    literal=literal_denominator(question)
    if literal:
        effective=literal
        from qa_agent.clarify.definition_recovery import complete_definitions
        for label,clauses in complete_definitions(payload).items():
            if (len(clauses)==1 and label in str(analysis.denominator or '') and label not in literal and
                    re.search(r'(?:本会话|整个会话|全程|以后|接下来所有).{0,12}(?:只查|限定|仅限|都按|都查|只看)',clauses[0])):
                effective=analysis.denominator
        analysis.denominator=effective
        analysis.condition_sources['denominator']={'source':'explicit_user','evidence':literal,
            'lifetime':'task','applies_to':'denominator'}
        operand=analysis.query_scope.setdefault('denominator',{})
        operand['scope']=effective;operand['source_evidence']=literal
        # The already approved whole-sales amount is invoice-grained; an
        # explicit music-entity numerator still uses detail amount separately.
        if re.search(r'整体销售额|全部发票|发票总额|全年发票|同期全部.*发票',literal):
            operand['metric']='invoice_revenue'
            if analysis.rank_object in {'genre','artist','album','track'}:
                analysis.query_scope.setdefault('numerator',{})['metric']='detail_revenue'
        from qa_agent.clarify.definition_recovery import label_is_referenced
        for binding in analysis.filters:
            quote=str(binding.get('scope_evidence') or '')
            named=re.search(r'[“"‘]([^”"’]{2,24})[”"’]\s*[:：]',quote)
            if (binding.get('source')=='user_session_context' and named and label_is_referenced(named[1],literal) and
                    binding.get('column') in {'invoice.billing_country','customer.country'} and
                    binding.get('binding_scope') not in {'numerator','eligibility'}):
                current=operand.setdefault('filters',[])
                same=lambda item:item.get('column',item.get('field'))==binding['column'] and item.get('operator')==binding['operator'] and item.get('value',item.get('values'))==binding['value']
                operand['filters']=[item for item in current if not same(item)]+[deepcopy(binding)]
        current=(analysis.time_scope or {}).get('current') or {}
        if current and 'period' not in operand:operand['period']={key:current[key] for key in ('start','end')}
        analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field')!='denominator']
        return analysis
    if analysis.metric!='invoice_revenue':return analysis
    # A concrete brief definition is authority; delegating to a policy (S7)
    # is not itself a newly explicit denominator. Reject model quote prefixes.
    source=analysis.condition_sources.get('denominator') or {};quote=str(source.get('evidence') or '')
    brief=str(payload.get('user_brief') or '')
    if source.get('source')=='user_brief' and quote and quote in brief:
        definitions=[]
        for clause in re.split(r'[。；;\n]',brief):
            definition=literal_denominator(clause)
            if not definition or '分母' not in clause:continue
            named=re.search(r'[“"‘]([^”"’]{2,24})[”"’]\s*[:：]',clause)
            if named and named[1] not in question:continue
            definitions.append((definition,clause))
        if len({definition for definition,_ in definitions})>1:
            analysis.conflicts.append('实际会话正文存在冲突的明确分母定义，不能任选一条或使用默认覆盖。')
        elif definitions and any(quote in clause for _,clause in definitions):
            definition,clause=definitions[0]
            analysis.denominator=definition
            analysis.condition_sources['denominator']={**source,'evidence':clause}
            return analysis
    # Only an immediate, explicitly referenced actual task can inherit its
    # previous structural denominator. Unrelated older ratio answers cannot.
    history=payload.get('actual_conversation') or []
    latest=history[-1] if history and isinstance(history[-1],dict) else {}
    intent=latest.get('intent') or {};prior_question=str(latest.get('user') or '')
    prior_literal=literal_denominator(prior_question)
    followup=bool(re.search(r'^\s*(?:那|改成|换成|改为|只要|再按|同样|接着|刚才)',question))
    if (followup and prior_literal and intent.get('task_type')=='ratio' and intent.get('denominator')
            and latest.get('status') in {'SUCCEEDED','ANSWERED'}):
        analysis.denominator=prior_literal
        prior_scope=(intent.get('query_scope') or {}).get('denominator')
        if isinstance(prior_scope,dict):analysis.query_scope['denominator']=deepcopy(prior_scope)
        analysis.condition_sources['denominator']={'source':'confirmed_history','evidence':prior_question,
            'lifetime':'task','applies_to':'denominator','verification':'immediate_actual_user_explicit_denominator'}
        return analysis
    # The existing RuleEngine now gets to apply the already approved policy,
    # register its ID and disclose its meaning. No alternative is invented.
    analysis.denominator=None
    analysis.query_scope.pop('denominator',None)
    analysis.condition_sources.pop('denominator',None)
    return analysis
