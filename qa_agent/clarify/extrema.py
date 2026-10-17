"""Current-wording authority for one absolute monthly-invoice extrema gap."""
from __future__ import annotations
import re
from qa_agent.clarify.output_requirements import requirement_has_semantics


def explicit_extrema_difference(question,analysis,catalog):
    if catalog.database.casefold()!='chinook':return analysis
    # Relative changes, percentages and additional grouping are distinct tasks.
    if re.search(r'同比|环比|增长率|增长幅度|百分|比例|占比|增长多少|(?:各个|每个|分别|按客户|按国家|按艺术家)',question):
        return analysis
    measure=re.search(r'(?:发票|账单)(?:金额|总额|销售额)',question)
    monthly=re.search(r'按月|每月|逐月|月份',question)
    gap=re.search(r'(?:最高|最大|最多)(?:的)?\s*(?:月份|月)?\s*(?:比|与|和)\s*(?:最低|最小|最少)(?:的)?\s*(?:月份|月)?\s*(?:多多少|差多少|相差多少|的?差额|的?金额差)',question)
    if not measure or not monthly or not gap or re.search(r'每(?:一)?张(?:发票|账单)|单张(?:发票|账单)|同时|顺便|并且列',question):
        return analysis
    analysis.task_type='aggregation';analysis.metric='invoice_revenue'
    analysis.comparison=None;analysis.numerator=None;analysis.denominator=None
    analysis.rank_object=None;analysis.top_n=None;analysis.order=None;analysis.grouping=[]
    for field in ('numerator','denominator','comparison','rank_object','top_n','order','grouping'):
        analysis.condition_sources.pop(field,None)
    for key in ('numerator','denominator','ranked_subset','ranking_scope','rank_metric','rank_metric_source','outer_operator','per_group_limit','partition_by'):
        analysis.query_scope.pop(key,None)
    analysis.query_scope['extrema_difference']={'grain':'month','metric':'invoice_revenue',
        'operation':'max_minus_min','source':'program:explicit_extrema_difference','source_evidence':question}
    analysis.query_scope['output_shape']='scalar_absolute_difference'
    analysis.condition_sources['metric']={'source':'explicit_user','evidence':measure.group(),
        'lifetime':'task','applies_to':'global'}
    analysis.condition_sources['task_type']={'source':'explicit_user','evidence':gap.group(),
        'lifetime':'task','applies_to':'global'}
    analysis.clarification_requests=[item for item in analysis.clarification_requests
        if item.get('field') not in {'comparison','comparison.type','numerator','denominator'}]
    analysis.output_requirements=[item for item in analysis.output_requirements
        if not requirement_has_semantics(item,'ratio','growth','monthly_rows')]
    if 'max_month_minus_min_month' not in analysis.output_requirements:
        analysis.output_requirements.append('max_month_minus_min_month')
    return analysis
