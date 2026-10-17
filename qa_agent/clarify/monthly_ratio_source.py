"""One closed, fresh literal monthly invoice share; no model rank aliases.

This parser accepts the whole actual source, not a substring. It supplies the
existing semantic contract only; SQL generation and SQL proofs remain separate.
"""
from __future__ import annotations

from datetime import date
import re

from qa_agent.clarify.rules import SemanticIntent


_NUMBER = r'(?:[0-9]{1,2}|一|二|两|三|四|五|六|七|八|九|十|十一|十二)'
_SOURCE = re.compile(
    r'\s*(?:请(?:问|计算|查询)?\s*)?'
    r'(?P<year>[0-9]{4})\s*年\s*'
    r'(?P<rank>(?:发票|账单)(?:总额|金额)\s*最高(?:的)?\s*'
    r'(?P<count>'+_NUMBER+r')\s*个?\s*月(?:份)?)\s*[，,]?\s*'
    r'(?P<numerator>(?:合计|总计|加总))\s*占\s*'
    r'(?P<denominator>全年(?:发票|账单)(?:总额|金额))\s*'
    r'(?:的)?\s*(?:百分之多少|百分比(?:是|为)?多少|比例(?:是|为)?多少)\s*[？?。.]?\s*'
)
_CHINESE = {word: value for value, word in enumerate(
    ('一','二','三','四','五','六','七','八','九','十','十一','十二'), 1)} | {'两': 2}


def literal_monthly_invoice_share(question, catalog, payload, bindings):
    """Return a contract only for an isolated, complete current-user source.

    Service separately authorizes this helper only when there is no previous
    semantic session. An absent runtime source never grants the fast path.
    """
    if (not isinstance(question, str) or payload.get('current_user_message') != question
            or payload.get('user_brief') or payload.get('actual_conversation') or bindings
            or catalog.database.casefold() != 'chinook'):
        return None
    match = _SOURCE.fullmatch(question)
    if not match:
        return None
    year = int(match['year'])
    count = int(match['count']) if match['count'].isascii() and match['count'].isdigit() else _CHINESE.get(match['count'])
    if not (1 <= year < 9999 and count is not None and 1 <= count <= 12):
        return None
    invoices = [table for table in catalog.tables if table.schema == 'public' and table.name == 'invoice']
    if len(invoices) != 1:
        return None
    fields = {column.name: column for column in invoices[0].columns}
    if not {'invoice_date', 'total'} <= fields.keys():
        return None
    if not re.fullmatch(r'date|timestamp(?:\(\d+\))?(?: (?:with|without) time zone)?', fields['invoice_date'].data_type, re.I):
        return None
    if not re.fullmatch(r'(?:numeric|decimal)(?:\(\s*\d+\s*(?:,\s*\d+\s*)?\))?|smallint|integer|bigint|real|double precision', fields['total'].data_type, re.I):
        return None
    period = {'start': date(year, 1, 1).isoformat(), 'end': date(year + 1, 1, 1).isoformat()}
    rank = match['rank']
    numerator = question[match.start('rank'):match.end('numerator')]
    denominator = match['denominator']
    year_quote = question[match.start('year'):question.index('年', match.end('year'))+1]
    sources = {field: {'source': 'explicit_user', 'evidence': quote,
                       'lifetime': 'task', 'applies_to': role}
               for field, quote, role in (
                   ('metric', rank, 'global'), ('time_scope', year_quote, 'global'),
                   ('rank_object', rank, 'numerator'), ('top_n', rank, 'numerator'),
                   ('order', rank, 'numerator'), ('numerator', numerator, 'numerator'),
                   ('denominator', denominator, 'denominator'))}
    return SemanticIntent(
        task_type='ratio', metric='invoice_revenue',
        time_scope={'current': {**period, 'grain': 'year', 'label': year_quote}},
        numerator=numerator, denominator=denominator, rank_object='month', top_n=count,
        order={'field': 'invoice_revenue', 'direction': 'desc'}, grouping=['month'],
        query_scope={
            'qualification_filters': [],
            'numerator': {'metric': 'invoice_revenue', 'filters': [],
                          'selection': {'kind': 'ranked_subset', 'definition_ref': 'query_scope.ranked_subset'}},
            'denominator': {'metric': 'invoice_revenue', 'filters': [], 'period': period,
                            'scope': denominator, 'source_evidence': denominator},
            'ranked_subset': {'group_by': 'invoice.invoice_date', 'grain': 'month',
                              'limit': count, 'metric': 'invoice_revenue',
                              'direction': 'desc', 'source_evidence': rank}},
        output_requirements=['percentage_share', 'ranked_subset_total'],
        evidence_spans={field: record['evidence'] for field, record in sources.items()},
        condition_sources=sources)
