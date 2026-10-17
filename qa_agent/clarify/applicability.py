"""Period applicability for explicitly chosen assignment-snapshot measures."""
from __future__ import annotations
import re


def normalize_assignment_period(question, analysis):
    """Never ask invoice dates for a current customer-owner snapshot.

    A possible invoice metric cannot establish its own period dependency before
    the user has chosen it.  Explicit temporal/activity restrictions survive.
    This does not introduce an all-data default or reinterpret activity counts.
    """
    analysis.query_scope.pop('period_applicability', None)
    if analysis.task_type != 'ranking' or analysis.rank_object != 'employee':
        return analysis
    if not re.search(r'客户负责人|客户.{0,4}(?:支持|负责)人员|销售支持人员|(?:员工|负责人).{0,8}(?:名下|负责)|业绩|绩效', question):
        return analysis
    temporal = bool(re.search(
        r'(?<!\d)\d{4}(?!\d)|\d{1,2}\s*月|期间|去年|今年|前年|最近|旺季|历史|曾经|当时|当年|以前|截至|截止|入职|登记|新增|新客户|复购|活跃|买过|购买过|开过|发票|账单|收入|销售额|消费金额', question))
    current = (analysis.time_scope or {}).get('current')
    scopes = [analysis.filters, analysis.query_scope.get('qualification_filters', [])]
    constrained = any(re.search(r'(?:invoice|invoice_line)\.|(?:date|time)$', str(item.get('column') or item.get('field') or ''), re.I)
                      for scope in scopes for item in scope)
    if temporal or current or constrained or (analysis.time_scope or {}).get('all_data'):
        return analysis
    if analysis.metric not in {None, 'customer_count'}:
        return analysis
    phase = 'deferred_until_metric' if analysis.metric is None else 'not_applicable'
    analysis.time_ambiguous = False
    analysis.clarification_requests = [item for item in analysis.clarification_requests
        if item.get('field') not in {'time_scope', 'time_scope.current'}]
    analysis.query_scope['period_applicability'] = {
        'status': phase, 'source': 'program:assignment_snapshot_measure',
        'question_evidence': question,
        'reason': ('先确认业绩指标；尚未确定指标时不能预设需要发票期间。' if analysis.metric is None else
                   '当前负责人名下客户记录计数为当前关系快照；本轮没有期间或客户发票活动条件。')}
    return analysis
