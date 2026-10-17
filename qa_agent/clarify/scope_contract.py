"""Program-owned local scope roles grounded in actual user definitions."""
from __future__ import annotations
import re
from qa_agent.clarify.output_requirements import requirement_has_semantics


def recover_named_filters(proposals,question,payload,catalog):
    from qa_agent.clarify.grounding import contextual_filters,schema_columns
    recovered=[]
    for proposal in proposals:
        if not isinstance(proposal,dict):continue
        item=dict(proposal)
        column=item.get('column') or item.get('field')
        if column not in schema_columns(catalog):continue
        item['column']=column;item.pop('field',None)
        item['operator']=str(item.get('operator') or '').upper()
        if 'value' not in item and 'values' in item:item['value']=item.pop('values')
        values=item.get('value') if isinstance(item.get('value'),list) else [item.get('value')]
        for line in str(payload.get('user_brief') or '').splitlines():
            if not re.search(r'[“"‘][^”"’]{2,24}[”"’]\s*[:：]',line):continue
            clause=re.split(r'[。；;\n]',line,maxsplit=1)[0]
            if not all(value is not None and str(value) in clause for value in values):continue
            grounded=contextual_filters([{**item,'scope_evidence':clause}],payload,catalog,question=question)
            if grounded:
                if not any(old.get('column')==column and old.get('operator')==item['operator'] and old.get('value')==item.get('value') for old in recovered):
                    recovered.extend(grounded)
                break
    return recovered


def explicit_ranked_ratio_subject(question,analysis):
    """A literal ranked subject is a numerator, even if the model omits it."""
    if analysis.task_type!='ratio' or analysis.numerator:return
    match=re.search(r'(?P<subject>(?:销售额|消费金额|购买数量)(?:最高(?:的)?|前[\d一二两三四五六七八九十]+大(?:的)?|最多(?:的)?)[^，,。；;]{0,10}(?:曲风|流派|艺术家|专辑|曲目|客户))\s*[，,]?\s*各占',question)
    if not match:return
    analysis.numerator=match.group('subject')
    analysis.evidence_spans['numerator']=match.group('subject')
    analysis.condition_sources['numerator']={'source':'explicit_user','evidence':match.group('subject'),'lifetime':'task','applies_to':'numerator'}
    if 'ranked_subset_ratios' not in analysis.output_requirements:analysis.output_requirements.append('ranked_subset_ratios')


def partition_named_comparison(question,analysis,payload,catalog):
    """A named set versus its complement is a partition, not a WHERE."""
    if analysis.metric!='invoice_revenue' or not re.search(r'其余|其他|非重点|剩余',question):return
    if not re.search(r'差',question) or not re.search(r'(?:invoice|发票).{0,6}金额|销售额|消费金额',question,re.I):return
    if re.search(r'比例|占比|百分|每个|各个|每位|各位|分别按|按.{0,8}(?:分组|汇总)',question):return
    if len(set(re.findall(r'(?<!\d)\d{4}(?!\d)',question)))>1:return
    if not re.search(r'(?:跟|和|与|相比|对比|比较|比).*(?:各|两边|分别|差)',question):return
    candidates=[]
    for binding in analysis.filters:
        if not (binding.get('column') in {'invoice.billing_country','customer.country'} and
                binding.get('operator') in {'IN','NOT IN'} and isinstance(binding.get('value'),list) and binding.get('source')=='user_session_context'):
            continue
        if not any(item['column']==binding['column'] and set(map(str,item['value']))==set(map(str,binding['value'])) for item in candidates):
            candidates.append(binding)
    if len(candidates)!=1:return
    item=candidates[0];quote=str(item.get('scope_evidence') or '')
    if not re.search(r'[“"‘][^”"’]{2,24}[”"’]\s*[:：]',quote):return
    from qa_agent.clarify.grounding import contextual_filters
    if quote not in str(payload.get('user_brief') or '') or not contextual_filters([item],payload,catalog,question=question):return
    analysis.query_scope['comparison_partition']={'column':item['column'],'values':list(item['value']),
        'metric':'invoice_revenue','source_evidence':quote,'other_operator':'NOT IN',
        'difference':{'left':'focus','right':'other'},'source':'program:confirmed_comparison_partition','question_evidence':question}
    def partition_binding(old):
        return (old.get('column',old.get('field'))==item['column'] and old.get('operator') in {'IN','NOT IN'} and
                isinstance(old.get('value',old.get('values')),list) and
                set(map(str,old.get('value',old.get('values'))))==set(map(str,item['value'])) and old.get('source')=='user_session_context')
    analysis.filters=[old for old in analysis.filters if not partition_binding(old)]
    analysis.query_scope['qualification_filters']=[old for old in analysis.query_scope.get('qualification_filters',[])
        if not (old.get('column',old.get('field'))==item['column'] and old.get('value',old.get('values'))==item['value'])]
    if not analysis.filters:analysis.condition_sources.pop('filters',None)
    # The actual request asks two amounts and their difference, not a ratio.
    # Remove incompatible model-carried outer operators together atomically.
    analysis.task_type='aggregation'
    analysis.comparison={'type':'partition_difference','left':'focus','right':'other'}
    analysis.numerator=None;analysis.denominator=None
    analysis.rank_object=None;analysis.top_n=None;analysis.order=None;analysis.grouping=[]
    analysis.query_scope.pop('numerator',None);analysis.query_scope.pop('denominator',None)
    analysis.query_scope.pop('outer_operator',None)
    analysis.query_scope['output_shape']='partition_amounts_and_difference'
    for name in ('numerator','denominator','comparison','rank_object','top_n','order','grouping'):
        analysis.condition_sources.pop(name,None)
    analysis.output_requirements=[item for item in analysis.output_requirements if not requirement_has_semantics(item,'ratio','ranked_subset')]
    analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field') not in {'numerator','denominator','comparison.type','rank_object','top_n','order','grouping'}]
    analysis.assumptions=[note for note in analysis.assumptions if '销售额占比默认以同期全部发票金额' not in note]
    analysis.default_assumptions=[note for note in analysis.default_assumptions if '销售额占比默认以同期全部发票金额' not in note]
    analysis.condition_sources['query_scope']={'source':'user_brief','evidence':quote,'lifetime':'task',
        'applies_to':'global','semantic_role':'partition_definition'}
    if 'partition_comparison' not in analysis.output_requirements:analysis.output_requirements.append('partition_comparison')
