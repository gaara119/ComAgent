"""A current customer-owner role is proved by the actual customer FK."""
from __future__ import annotations
import re


def normalize_current_assignment_scope(question,analysis,catalog,payload):
    if analysis.task_type!='ranking' or analysis.rank_object!='employee':return analysis
    generic=re.search(r'(?:咱们|我们|本公司|当前|目前|现在)(?:的)?\s*(?:这几个|几个|这些)?\s*(?:客户负责人|客户支持人员|销售支持员工)',question)
    if generic is None:return analysis
    if re.search(r'名单|指定|选定|刚才|上述|上面|以下|其中|那几|只看|仅看|这批|编号|部门|小组|团队|\bteam\b',question,re.I):return analysis
    if any(str(item.get('column',item.get('field',''))).startswith('employee.') for item in analysis.filters+analysis.query_scope.get('qualification_filters',[])):return analysis
    history=payload.get('actual_conversation') or []
    if history and any(str(item.get('column',item.get('field',''))).startswith('employee.') for item in ((history[-1].get('intent') or {}).get('filters') or [])):return analysis
    customer=next((t for t in catalog.tables if t.schema=='public' and t.name=='customer'),None)
    employee=next((t for t in catalog.tables if t.schema=='public' and t.name=='employee'),None)
    if customer is None or employee is None or 'employee_id' not in employee.primary_key:return analysis
    proven=any(fk.get('columns')==['support_rep_id'] and fk.get('references',{}).get('table')=='employee' and
        (fk.get('references',{}).get('schema') or customer.schema)=='public' and
        fk.get('references',{}).get('columns')==['employee_id'] for fk in customer.foreign_keys)
    if not proven:return analysis
    analysis.query_scope['employee_domain']={'kind':'referenced_customer_support_reps','foreign_key':'customer.support_rep_id',
        'target':'employee.employee_id','source':'program:current_customer_ownership_domain','source_evidence':generic.group()}
    def unsupported_scope(item):
        original=item.get('source_field',item.get('field'))
        text=str(item.get('question') or '')+' '+str(item.get('reason') or '')
        return original in {'scope','scope_missing','employee_scope','owner_scope','employees'} and bool(
            re.search(r'客户负责人|销售支持员工|客户支持人员|负责人',text) and re.search(r'具体|哪些|集合|范围',text))
    analysis.clarification_requests=[item for item in analysis.clarification_requests if not unsupported_scope(item)]
    return analysis


def close_confirmed_assignment_measure(state):
    """A real metric patch resolves its old question, retaining the event log."""
    analysis = state.analysis
    if analysis.task_type != 'ranking' or analysis.rank_object != 'employee' or analysis.metric != 'customer_count':
        return
    evidence = None
    for resolution in reversed(state.resolutions):
        message = str(resolution.get('message') or '')
        patches = resolution.get('patches') or []
        if any(item.get('op') == 'set' and item.get('path') == 'metric' and item.get('value') == 'customer_count'
               and item.get('evidence') and item['evidence'] in message for item in patches):
            evidence = message
            break
    if evidence is None:
        return  # A model-filled metric/source tag is not a human confirmation.
    from qa_agent.clarify.normalization import canonical_slot
    resolved = [item for item in analysis.clarification_requests if canonical_slot(item.get('source_field', item.get('field', ''))) == 'metric']
    if resolved:
        analysis.clarification_requests = [item for item in analysis.clarification_requests if item not in resolved]
        state.history.append({'event': 'clarification_slot_resolved', 'field': 'metric',
            'resolved_requests': resolved, 'evidence': evidence, 'intent_version': state.intent.intent_version})
    domain = analysis.query_scope.get('employee_domain') or {}
    if domain.get('source') != 'program:current_customer_ownership_domain':
        return
    from qa_agent.clarify.applicability import normalize_assignment_period
    normalize_assignment_period(state.original_question, analysis)
    applicability = analysis.query_scope.get('period_applicability') or {}
    if applicability.get('status') != 'not_applicable':
        return  # Real dates, invoice activity and qualification remain active.
    stale = analysis.query_scope.get('aggregation_scope')
    if stale in {'all_invoices_for_qualified_employees', 'invoices_for_qualified_employees'}:
        analysis.query_scope['aggregation_scope'] = 'current_customers_for_qualified_support_reps'
        state.history.append({'event': 'assignment_snapshot_scope_normalized', 'previous_scope': stale,
            'aggregation_scope': analysis.query_scope['aggregation_scope'], 'evidence': evidence,
            'intent_version': state.intent.intent_version})
