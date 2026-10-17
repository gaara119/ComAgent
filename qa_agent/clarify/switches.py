"""Trusted, optional switches for defaults that were actually applied."""
from __future__ import annotations
from copy import deepcopy
from qa_agent.clarify.policy import CUSTOMER_AMOUNT,POLICY_PATTERNS,default_policy_ids


def _without_policy(notes,identities):
    return [note for note in notes if not any(identity in identities and pattern in note for pattern,identity in POLICY_PATTERNS)]


def _patch(path,value):return {'op':'set','path':path,'value':value}


def _option(identity,label,patches):return {'id':identity,'label':label,'patch':{'op':'bundle','patches':patches}}


def approved_default_switches(analysis):
    policies=set(default_policy_ids(analysis));result=[]
    if 'oct12.ratio.invoice_denominator' in policies:
        from qa_agent.clarify.denominator_authority import PENDING_DENOMINATOR
        scope=deepcopy(analysis.query_scope);scope.pop('denominator',None)
        notes=_without_policy(analysis.assumptions,{'oct12.ratio.invoice_denominator'})
        requests=[item for item in analysis.clarification_requests if item.get('field')!='denominator']
        requests.append({'field':'denominator','question':'请明确本题分母的对象、范围和期间。',
            'reason':'用户选择自行指定分母；确认前不执行最终业务查询。'})
        result.append(_option('denominator_specify','自行指定本题分母（先暂停计算并询问）',[
            _patch('denominator',None),_patch('query_scope',scope),_patch('clarification_requests',requests),
            _patch('assumptions',notes+[PENDING_DENOMINATOR]),
            _patch('default_assumptions',_without_policy(analysis.default_assumptions,{'oct12.ratio.invoice_denominator'}))]))
    region_policies={'oct12.region.invoice_billing','oct12.region.customer_residence'}
    if policies & region_policies and analysis.region_scope and len({item.get('column') for item in analysis.filters} & {'invoice.billing_country','customer.country'})<=1:
        for identity,label,column in [('billing_country','按发票账单国家','invoice.billing_country'),('customer_country','按客户所在地国家','customer.country')]:
            scope=deepcopy(analysis.query_scope)
            for name in ('numerator','denominator'):
                operand=scope.get(name)
                if isinstance(operand,dict) and 'filters' in operand:
                    operand['filters']=[{**item,'column':column} if item.get('column')==analysis.region_scope else item for item in operand['filters']]
            if scope.get('region_scope')==analysis.region_scope:scope['region_scope']=column
            patches=[_patch('region_scope',column),_patch('region_ambiguous',False),_patch('query_scope',scope),
                _patch('assumptions',_without_policy(analysis.assumptions,region_policies)+[f'用户已选择地区口径：{label}。']),
                _patch('default_assumptions',_without_policy(analysis.default_assumptions,region_policies))]
            result.append(_option(identity,label,patches))
    if CUSTOMER_AMOUNT in policies and analysis.task_type=='ratio' and analysis.rank_object=='customer' and analysis.top_n==1:
        from qa_agent.sql import semantic_guard
        proven=set(getattr(semantic_guard,'CUSTOMER_WINNER_PROVEN_METRICS',{'invoice_revenue'}))
        # The first verified count-winner path has no global or local filter
        # binding bridge. Keep unsupported cards absent rather than offering
        # a button that the legacy binding guard would reject afterwards.
        local_filters=any(isinstance(analysis.query_scope.get(name),dict) and analysis.query_scope[name].get('filters')
                          for name in ('numerator','denominator'))
        if analysis.filters or analysis.query_scope.get('qualification_filters') or local_filters:
            proven.discard('invoice_count')
        if len(proven & {'invoice_revenue','invoice_count','purchased_quantity'})<2:
            return result
        for identity,label,metric in [('customer_inner_by_amount','按发票消费金额选择客户，分子仍为该客户的发票金额','invoice_revenue'),
             ('customer_inner_by_quantity','按购买件数选择客户，分子仍为该客户的发票金额','purchased_quantity'),
             ('customer_inner_by_invoice_count','按发票张数；并列按客户编号升序取第一，分子仍为该客户的发票金额','invoice_count')]:
            if metric not in proven:continue
            scope=deepcopy(analysis.query_scope)
            scope.update(rank_metric=metric,rank_metric_source='explicit_user_choice',numerator_ranking_metric=metric)
            if metric=='invoice_count':
                scope['rank_tie_breaker']={'field':'customer.customer_id','direction':'asc','source':'explicit_user_choice'}
            scope['numerator']={**scope.get('numerator',{}),'metric':'invoice_revenue','scope':label}
            patches=[_patch('query_scope',scope),_patch('metric','invoice_revenue'),_patch('numerator',label),
                _patch('assumptions',_without_policy(analysis.assumptions,{CUSTOMER_AMOUNT})+[f'用户已选择客户排名口径：{label}。']),
                _patch('default_assumptions',_without_policy(analysis.default_assumptions,{CUSTOMER_AMOUNT}))]
            result.append(_option(identity,label,patches))
    return result
