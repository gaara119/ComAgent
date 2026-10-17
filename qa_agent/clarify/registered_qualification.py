"""Lower one approved repeat metric; never treat its name as a DB column."""
from __future__ import annotations
import json,re


def normalize_repeat_metric_qualification(question,analysis,catalog):
    if analysis.metric!='repeat_customer_count' or not re.search(r'复购|活跃客户',question):return analysis
    # A true explicit post-aggregation customer threshold is an independent
    # requirement, not the metric-definition mirror addressed here.
    if re.search(r'(?:复购|活跃)客户(?:数|人数).{0,8}(?:至少|不低于|超过|>=|>)[\s\d一二两三四五六七八九十]+|至少.{0,4}(?:位|名|个)(?:复购|活跃)客户',question):return analysis
    from qa_agent.config import PROJECT_ROOT
    path=PROJECT_ROOT/'data/rules/metric_definitions.json'
    definition=json.loads(path.read_text(encoding='utf-8'))
    registered=next((item for item in definition.get('metrics',[]) if item.get('id')=='repeat_customer_count'),None)
    if definition.get('review_status')!='approved' or not registered or not re.search(r'>=\s*2',registered.get('expression','')):return analysis
    invoice=next((table for table in catalog.tables if table.schema=='public' and table.name=='invoice'),None)
    if invoice is None or 'invoice_id' not in invoice.primary_key or 'customer_id' not in invoice.column_names:return analysis
    filters=analysis.query_scope.get('qualification_filters') or []
    mirror=lambda item:item.get('column',item.get('field'))=='repeat_customer_count' and item.get('operator')=='>=' and type(item.get('value')) is int and item['value']==2
    if not any(mirror(item) for item in filters):return analysis
    analysis.query_scope['qualification_filters']=[item for item in filters if not mirror(item)]
    period_ref=('time_scope.current' if (analysis.time_scope or {}).get('current') else
                'time_scope.all_data' if (analysis.time_scope or {}).get('all_data') is True else 'time_scope')
    analysis.query_scope['repeat_qualification']={'group_by':'invoice.customer_id','aggregate':'COUNT','column':'invoice.invoice_id',
        'operator':'>=','value':2,'period_ref':period_ref,'source':'program:approved_registered_repeat_metric',
        'definition_ref':'data/rules/metric_definitions.json#metric_id=repeat_customer_count','source_evidence':question}
    return analysis
