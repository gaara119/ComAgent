"""Normalize only proposed mirrors of a literal natural calendar period."""
from __future__ import annotations
from datetime import date,timedelta
import re


def normalize_global_calendar_mirrors(question,analysis,catalog,payload):
    from qa_agent.clarify.temporal_role import literal_hire_calendar_period
    from qa_agent.clarify.grounding import literal_relative_period
    literal=literal_hire_calendar_period(question)
    if literal is None and not re.search(r'\d{1,2}\s*月|\d{4}-\d{1,2}-\d{1,2}|between|介于|之间|截至|截止',question,re.I):
        current_relative=(literal_relative_period(question,payload) or {}).get('current') or {}
        if current_relative:literal={key:current_relative[key] for key in ('start','end')}
    current=(analysis.time_scope or {}).get('current') or {}
    if not literal or any(literal[key]!=current.get(key) for key in ('start','end')):return analysis
    role=analysis.query_scope.get('temporal_field_role') or {}
    column=role.get('column') if role.get('source')=='program:explicit_temporal_field_role' else None
    invoice_metrics={'invoice_revenue','detail_revenue','invoice_count','average_invoice_amount','average_customer_amount','repeat_customer_count','purchased_quantity'}
    if column is None and analysis.metric in invoice_metrics and re.search(r'发票|账单|销售额|消费金额|复购|活跃客户|客单价|购买数量|销量',question):
        column='invoice.invoice_date'
    if column is None:return analysis
    actual_dates={f'{table.name}.{field.name}' for table in catalog.tables for field in table.columns if re.search(r'date|timestamp',field.data_type,re.I)}
    if column not in actual_dates:return analysis
    last_day=(date.fromisoformat(literal['end'])-timedelta(days=1)).isoformat()
    containers=[(analysis.query_scope,'qualification_filters')]
    containers += [(analysis.query_scope[name],'filters') for name in ('numerator','denominator') if isinstance(analysis.query_scope.get(name),dict)]
    for container,key in containers:
        if key not in container:continue
        explicit=container.get('period')
        if isinstance(explicit,dict) and any(explicit.get(k)!=literal[k] for k in ('start','end')):continue
        filters=container[key]
        if (container is analysis.query_scope and column=='employee.hire_date' and
                role.get('source')=='program:explicit_temporal_field_role'):
            # The hire-role producer already owns this exact named calendar.
            # Reuse its strict predicate; a later generic pass must not erase
            # independent/local or internally contradictory qualification.
            from qa_agent.clarify.temporal_role import normalize_literal_temporal_mirror
            normalize_literal_temporal_mirror(question,analysis,column)
            continue
        mirrors=[item for item in filters if item.get('column',item.get('field'))==column and
            str(item.get('operator','')).upper()=='BETWEEN' and
            item.get('value',item.get('values')) in ([literal['start'],literal['end']],[literal['start'],last_day])]
        if not mirrors:continue
        # This lowering chooses the actual explicitly named calendar period,
        # not equivalence of SQL BETWEEN over date vs timestamp types.
        container[key]=[item for item in filters if item not in mirrors]
        if container is not analysis.query_scope:
            container['period']=dict(literal)
            container['period_source']={'source':'program:literal_calendar_role','evidence':question,
                'reason':'自然期间原文优先，模型日历镜像归并到单份半开期间。'}
    return analysis
