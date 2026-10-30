"""Keep a model-proposed denominator from impersonating user authority."""
from __future__ import annotations
import re
from copy import deepcopy
from hashlib import sha256

PENDING_DENOMINATOR='用户已选择自行指定本题分母，等待明确分母条件。'


def literal_customer_rank_pair(question):
    """An explicit first-minus-Nth customer amount question, without SQL."""
    if not re.search(r'客户|\bcustomer\b',question,re.I) or not re.search(r'花钱|消费|发票金额',question):return None
    if re.search(r'不要|不需要|不比较|不求|排除|除了|平均|张数|购买数量',question):return None
    first=re.search(r'第一(?:名|位)|(?:花钱|消费)(?:金额)?最多的那(?:一)?位',question)
    second=re.search(r'比第\s*([0-9一二三四五六七八九十]+)\s*名\s*(?:多花|多消费|多出|高出|多了|差)',question)
    if first is None or second is None:return None
    from qa_agent.clarify.literal_structures import number
    n=number(second[1])
    if not isinstance(n,int) or not 2<=n<=200:return None
    return {'source':'program:literal_customer_rank_pair','ranks':[1,n],
        'operation':'subtract','metric':'invoice_revenue','object':'customer',
        'source_evidence':question,'question_sha256':sha256(question.encode()).hexdigest()}


def literal_half_year_growth(question,analysis,payload):
    """Prove H2-H1 divided by H1 from one real calendar year and wording."""
    if analysis.metric!='invoice_revenue' or not re.search(r'发票(?:总额|金额)',question):return None
    if re.search(r'不要|不计算|不求|不按|季度|\d{1,2}\s*月|\d{4}-\d{2}-\d{2}',question):return None
    if not re.search(r'下半年比上半年(?:多(?:出)?(?:的)?(?:部分|金额)?|增长(?:的部分)?).{0,12}(?:相当于|占(?:了)?)上半年(?:发票总额|总额|金额)?(?:的)?(?:百分之几|百分比|比例)',question):return None
    years=set(re.findall(r'(?<!\d)(\d{4})\s*年',question))
    relatives=re.findall(r'前年|去年|今年|明年',question)
    if len(years)==1 and not relatives:year=int(next(iter(years)))
    elif not years and len(relatives)==1:
        from qa_agent.clarify.grounding import literal_relative_period
        annual=(literal_relative_period(question,payload)or{}).get('current')or{}
        if not annual:return None
        year=int(annual['start'][:4])
    else:return None
    if not 1<=year<9999:return None
    current=(analysis.time_scope or{}).get('current')or{}
    annual={'start':f'{year:04d}-01-01','end':f'{year+1:04d}-01-01'}
    if any(current.get(k)!=v for k,v in annual.items()):return None
    return {'source':'program:literal_half_year_growth','source_evidence':question,
        'question_sha256':sha256(question.encode()).hexdigest(),
        'h1':{'start':annual['start'],'end':f'{year:04d}-07-01'},
        'h2':{'start':f'{year:04d}-07-01','end':annual['end']},'operation':'(h2-h1)/h1'}


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
    analysis.query_scope.pop('rank_pair_comparison',None)
    pair=literal_customer_rank_pair(question)
    if pair and analysis.task_type=='ranking' and analysis.rank_object=='customer' and analysis.metric=='invoice_revenue':
        analysis.query_scope['rank_pair_comparison']=pair
        analysis.query_scope['output_shape']='scalar_rank_difference'
        # N is the consumed ranking coverage; output_shape remains one scalar.
        # Leaving None would let the existing generic ranking rule install 10.
        analysis.top_n=pair['ranks'][-1]
        analysis.output_requirements=[x for x in analysis.output_requirements if x not in {'ranked_subset_rows','ranked_subset_total'}]
    if analysis.task_type!='ratio':return analysis
    analysis.query_scope.pop('half_year_growth',None)
    half=literal_half_year_growth(question,analysis,payload)
    if half:
        analysis.query_scope['half_year_growth']=half
        analysis.denominator='上半年发票总额'
        analysis.condition_sources['denominator']={'source':'explicit_user','evidence':question,
            'lifetime':'task','applies_to':'denominator','verified':True}
        analysis.assumptions=[text for text in analysis.assumptions if '销售额占比默认以同期全部发票金额' not in text]
        analysis.default_assumptions=[text for text in analysis.default_assumptions if '销售额占比默认以同期全部发票金额' not in text]
        for role,period in (('numerator',half['h2']),('denominator',half['h1'])):
            operand=analysis.query_scope.setdefault(role,{})
            operand['metric']='invoice_revenue';operand['period']=dict(period)
            operand['scope']='explicit_h2_minus_h1' if role=='numerator' else 'explicit_h1_base'
            operand['source_evidence']=question
            # Retire only a plain exact model calendar mirror. Unknown extra
            # keys/predicates remain and must be proved or explicitly rejected.
            def mirror(item):
                if not isinstance(item,dict) or not set(item)<={'field','column','operator','value','scope_evidence'}:return False
                if item.get('field') and item.get('column') and item['field']!=item['column']:return False
                quote=item.get('scope_evidence')
                return ((item.get('column')or item.get('field'))=='invoice.invoice_date'
                    and str(item.get('operator','')).lower()=='between' and item.get('value')==period
                    and quote in ('下半年' if role=='numerator' else '上半年',question))
            operand['filters']=[item for item in operand.get('filters',[]) if not mirror(item)]
        return analysis
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
