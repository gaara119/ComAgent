"""Finite invoice-set share facts from complete actual user clauses.

A country owner identifies a physical column, not the operand scope. Only
verified current mentions inside a wholly consumed operand establish that role.
This module neither supplies a missing denominator nor weakens any SQL guard.
"""
from __future__ import annotations
from copy import deepcopy
import re

COUNTRIES={'customer.country','invoice.billing_country'}
MONEY=r'(?:发票|账单)(?:金额|总额)(?:合计|总和)?'

def invoice_share_candidate(question):
    """Detection only: incomplete/unsupported shares must reach semantics."""
    return bool(re.search(r'占(?:了)?[^。；;？?]{1,120}(?:百分之多少|百分比|比例|占比|多少)|\bpercent(?:age)?\s+share\b',question,re.I))

def plain_invoice_share_candidate(question):
    from qa_agent.nlu.ownership import explicit_country_dimensions
    return (invoice_share_candidate(question)and bool(explicit_country_dimensions(question))
        and bool(re.search(r'发票|账单|\binvoices?\b',question,re.I))
        and not re.search(r'曲目|歌曲|艺术家|乐队|专辑|流派|曲风|明细',re.split(r'占|\bpercent(?:age)?\s+share\b',question,maxsplit=1,flags=re.I)[0])
        and not re.search(r'排名|前\s*[\d一二两三四五六七八九十]+\s*(?:名|位|个客户|个月)|最高|最多|top\s*\d+',question,re.I))

def _unproved_share(question,analysis):
    analysis.numerator=None
    analysis.condition_sources.pop('numerator',None)
    if not any(x.get('source')=='program:invoice_set_share'for x in analysis.clarification_requests):
        analysis.clarification_requests.append({'field':'numerator','source':'program:invoice_set_share',
            'question':'当前发票金额占比含尚不能安全定位的操作数范围，请分别说明分子、分母及各自期间，或拆分查询。',
            'reason':'仅对完整可核验的同期国家条件发票金额集合比建立合同；未执行SQL。',
            'evidence':question})
    return analysis

def _operand_surface(text,bindings,*,denominator=False):
    """Consume all factual words, not an arbitrary successful substring."""
    surface=text.strip(' ，,。；;？?！!')
    for binding in sorted(bindings,key=lambda b:len(b['field_owner_proof']['evidence']),reverse=True):
        quote=binding['field_owner_proof']['evidence']
        if surface.count(quote)!=1:return False
        surface=surface.replace(quote,'<country>',1)
    prefix=r'(?:(?:请问|查询|计算|请计算|请查询)\s*)?(?:(?:\d{4}\s*年|今年|去年|前年)\s*)?'
    countries=r'(?:<country>(?:\s*(?:且|并且|和|与|、|，|,|and)\s*<country>)?\s*(?:的)?\s*)?'
    if denominator:
        timing=r'(?:(?:该年|同年|同期|当年|全年|\d{4}\s*年)(?:的)?\s*)?'
        total=r'(?:(?:全部|所有|全球|全库|整体)(?:的)?\s*)?'
        # “同期总金额” refers to the invoice measure just explicitly named.
        amount=r'(?:'+MONEY+r'|总金额|总销售额)'
        return bool(re.fullmatch(prefix+timing+total+countries+amount,surface,re.I))and(
            bool(bindings)or bool(re.search(r'全部|所有|全球|全库|整体|总金额|总销售额',surface)))
    return bool(bindings)and bool(re.fullmatch(prefix+countries+MONEY,surface,re.I))

def _format_tail_only(text):
    """Consume only a complete supported formatting clause, never a filter."""
    clauses=[x.strip()for x in re.split(r'[。；;？?！!]',text)if x.strip()]
    return all(re.fullmatch(r'(?:请)?百分比(?:保留|显示)[零〇一二两三四五六七八九\d]+位小数[，,]?\s*',x)for x in clauses)

def _same_country_mirror(item,proved,role=None):
    """Only a complete identical country predicate is a harmless mirror."""
    allowed={'field','column','operator','value','values','binding_scope','scope_evidence'}
    if not isinstance(item,dict)or set(item)-allowed:return False
    field=item.get('column')or item.get('field')
    if item.get('column')and item.get('field')and item['column']!=item['field']:return False
    if 'values'in item and item['values']!=[item.get('value')]:return False
    matches=[x for x in proved if x.get('column')==field and x.get('operator')==item.get('operator')
        and x.get('value')==item.get('value')and (not role or x['binding_scope']==role)]
    scopes={x['binding_scope']for x in matches}
    return len(scopes)==1 and (item.get('binding_scope')is None or item.get('binding_scope')==next(iter(scopes)))and(
        not item.get('scope_evidence')or any(item['scope_evidence']==x.get('scope_evidence')for x in matches))

def explicit_invoice_operand_patch(message,analysis,bindings):
    """A closed, same-task replacement of one country invoice operand.

    This does not infer a denominator or authorize general local filtering.
    The actual field owner and value still come from the current ValueLinker.
    """
    if analysis.task_type!='ratio' or analysis.metric!='invoice_revenue':return None
    match=re.fullmatch(r'\s*(分子|分母)(?:改为|改成|换成)\s*(.+?)[，,]\s*(?:分母|分子)(?:及年份|和年份)?不变[。！!]?\s*',message)
    if not match:return None
    role='numerator'if match[1]=='分子'else'denominator'
    other='分母'if role=='numerator'else'分子'
    if not re.search(r'[，,]\s*'+other+r'(?:及年份|和年份)?不变',message):return None
    actual=[b for b in bindings if b.get('column')in COUNTRIES]
    if len(actual)!=1 or len(bindings)!=1 or actual[0].get('operator')!='=':return None
    proof=actual[0].get('field_owner_proof')or{}
    if (proof.get('source')!='program:literal_country_owner' or proof.get('column')!=actual[0]['column']
            or not proof.get('evidence')or proof['evidence']not in match[2]
            or not _operand_surface(match[2],actual)):
        return None
    return role,match[2].strip()

def invoice_ratio_delta(message,analysis):
    """Recognize closed edits of this task, including with a saved full brief."""
    if analysis.task_type!='ratio' or analysis.metric!='invoice_revenue':return False
    if re.match(r'\s*(?:请)?(?:分子|分母)(?:的)?(?:期间|年份|日期)?(?:改为|改成|换成)',message):return True
    text=message.strip(' 。！!')
    return bool(re.fullmatch(r'(?:年份(?:改为|改成|换成)\s*\d{4}\s*年|'
        r'(?:改为|改成)?百分比(?:保留|显示)[零〇一二两三四五六七八九\d]+位小数|'
        r'取消百分比小数位约定[，,]\s*按原值显示)[，,；;]\s*其他条件不变',text))

def ground_invoice_set_share(question,analysis,bindings,catalog):
    if catalog.database.casefold()!='chinook'or not invoice_share_candidate(question):return analysis
    # Classification is separate from operand proof. An unsupported share can
    # be incomplete and require clarification; it cannot execute as lookup.
    analysis.task_type='ratio'
    if not plain_invoice_share_candidate(question):return analysis
    match=re.search(r'(?P<n>[^。；;？?]+?)\s*占(?:了)?\s*(?P<d>[^。；;？?]+?)(?:的)?\s*(?:百分之多少|百分比|比例|占比|多少)(?=[？?。；;]|$)',question)
    if match is None:return _unproved_share(question,analysis)
    n=match['n'].strip(' ，,');d=re.sub(r'的$','',match['d'].strip(' ，,'))
    actual=[];roles={'numerator':[],'denominator':[]};ambiguous=False
    for binding in bindings:
        if binding.get('column')not in COUNTRIES:continue
        proof=binding.get('field_owner_proof')or{};span=proof.get('value_span')
        valid=(proof.get('source')=='program:literal_country_owner'and proof.get('column')==binding.get('column')
            and isinstance(span,list)and len(span)==2 and all(isinstance(x,int)and not isinstance(x,bool)for x in span)
            and 0<=span[0]<span[1]<=len(question)and proof.get('evidence')in question
            and binding.get('source')in{'verified_value_index','explicit_user_literal'})
        if not valid:ambiguous=True;continue
        role='numerator'if match.start('n')<=span[0]<span[1]<=match.end('n')else'denominator'if match.start('d')<=span[0]<span[1]<=match.end('d')else None
        if role is None or binding.get('operator')!='=':ambiguous=True;continue
        item=deepcopy(binding);item['binding_scope']=role
        item['scope_evidence']=n if role=='numerator'else d
        roles[role].append(item);actual.append(item)
    if not roles['numerator']:return _unproved_share(question,analysis)
    # A successful first substring is insufficient: additional source clauses
    # and model-proposed independent predicates remain unresolved, never erased.
    foreign=[x for x in analysis.filters if x.get('column',x.get('field'))not in COUNTRIES]
    supported=(not ambiguous and not foreign and len(actual)==len(bindings)
        and not question[:match.start()].strip(' ，,。；;？?！!')
        and _format_tail_only(question[match.end():])
        and _operand_surface(n,roles['numerator'])and _operand_surface(d,roles['denominator'],denominator=True)
        and not any(len({x['column']for x in items})!=len(items)for items in roles.values()))
    years=set(re.findall(r'(?<!\d)(\d{4})\s*年',question))
    if len(years)>1:supported=False
    current=(analysis.time_scope or{}).get('current')or{}
    if not current.get('start')or not current.get('end'):supported=False
    for item in analysis.query_scope.get('qualification_filters',[]):
        if not _same_country_mirror(item,actual):supported=False
    for role in('numerator','denominator'):
        operand=analysis.query_scope.get(role)
        if not isinstance(operand,dict):continue
        if set(operand)-{'metric','scope','source_evidence','filters','period'}:supported=False
        if any(not _same_country_mirror(item,actual,role)for item in operand.get('filters',[])):supported=False
        period=operand.get('period')
        if period and (not isinstance(period,dict)or any(period.get(k)!=current.get(k)for k in('start','end'))):supported=False
    analysis.task_type='ratio'
    if not supported:
        # Keep unknown constraints; a low-confidence proposal cannot silently
        # turn an unproved operand into global WHERE or an invented ranking.
        return _unproved_share(question,analysis)
    # Calendar lives in the typed period. Keep the operand description free of
    # an old year so a later global calendar edit cannot leave stale prose.
    n=re.sub(r'^(?:(?:请问|查询|计算|请计算|请查询)\s*)?(?:\d{4}\s*年|今年|去年|前年)\s*','',n)
    d=re.sub(r'^(?:该年|同年|同期|当年|全年|\d{4}\s*年)(?:的)?\s*','',d)
    analysis.metric='invoice_revenue';analysis.numerator=n;analysis.denominator=d
    analysis.comparison=None;analysis.grouping=[]
    analysis.rank_object=None;analysis.top_n=None;analysis.order=None;analysis.region_scope=None;analysis.region_ambiguous=False
    for key in ('ranked_subset','rank_metric','rank_metric_source','numerator_ranking_metric','outer_operator','ranking_scope'):
        analysis.query_scope.pop(key,None)
    from qa_agent.clarify.output_requirements import requirement_has_semantics
    analysis.output_requirements=[item for item in analysis.output_requirements if not requirement_has_semantics(item,'ranked_subset')]
    analysis.condition_sources.pop('region_scope',None)
    analysis.filters=actual
    from qa_agent.clarify.grounding import scope_local_qualification_mirrors
    scope_local_qualification_mirrors(analysis,actual)
    for role,text in [('numerator',n),('denominator',d)]:
        contract={'metric':'invoice_revenue','scope':text,'source_evidence':text,'filters':deepcopy(roles[role])}
        if current.get('start')and current.get('end'):contract['period']={key:current[key]for key in('start','end')}
        analysis.query_scope[role]=contract
        analysis.condition_sources[role]={'source':'explicit_user','evidence':text,'lifetime':'task','applies_to':role,'verified':True}
        analysis.evidence_spans[role]=text
    if 'percentage_share'not in analysis.output_requirements:analysis.output_requirements.append('percentage_share')
    return analysis
