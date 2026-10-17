"""Known ranking mirrors are operators, never literal database identifiers."""
from __future__ import annotations
import re


def normalize_customer_winner_symbol(question,analysis,catalog):
    """Lower only an exact duplicate of an already grounded money winner.

    Unknown predicates remain in the contract for the existing strict SQL
    guard. This does not interpret a symbolic value as a database identifier.
    """
    if (analysis.task_type!='ratio' or analysis.metric!='invoice_revenue' or analysis.rank_object!='customer' or
            type(analysis.top_n) is not int or analysis.top_n!=1 or
            analysis.query_scope.get('rank_metric')!='invoice_revenue'):return analysis
    subject=re.split('占',question,maxsplit=1)[0]
    # Negation must target the ranking, not an independent qualification or
    # a rejected alternative measure ("不是按张数，按发票金额最高...").
    rank_word=r'(?:买得最多|(?:消费金额|发票金额|消费总额)(?:最高|最多))'
    compact=re.sub(r'\s+','',subject)
    if (re.search(r'rank_1_by_invoice_revenue|customer\.rank',question,re.I) or
            re.search(r'(?:不要|不准|禁止|不是|并非|别|不选择|不选|排除)(?:把|将)?(?:选择|选取|选|查询|查|看|统计)?'
                      r'(?:(?:那|这)(?:一)?(?:位|个)|该(?:位|名)?)?(?:按)?'+rank_word,compact) or
            re.search(rank_word+r'[^，,。；;]{0,8}客户(?:以外|之外|除外)',compact) or
            any(value not in {'1','一'} for value in re.findall(
                r'前\s*([\d一二两三四五六七八九十百千万]+)\s*(?:(?:位|名|个)\s*)?(?:的)?(?:客户|顾客)',subject))):return analysis
    bare=bool(re.search(r'买得最多.{0,8}客户',subject) and not re.search(r'数量|张数|份数|销量|购买量',subject)
              and analysis.query_scope.get('rank_metric_source')=='oct12.customer.amount')
    explicit_amount=bool(re.search(r'(?:消费金额|发票金额|消费总额)(?:最高|最多).{0,8}客户',subject))
    if not bare and not explicit_amount:return analysis
    tables=[table for table in getattr(catalog,'tables',()) if table.name=='customer']
    if len(tables)!=1:return analysis
    table=tables[0]
    keys=[column for column in table.columns if column.name=='customer_id']
    if (table.primary_key!=('customer_id',) or len(keys)!=1 or keys[0].nullable or
            not re.fullmatch(r'(?:smallint|integer|bigint|int[248]?|smallserial|serial|bigserial)',keys[0].data_type.strip(),re.I) or
            any(column.name=='rank' for column in table.columns)):return analysis
    numerator=analysis.query_scope.get('numerator')
    if not isinstance(numerator,dict):return analysis
    selection={'kind':'ranking_winner','object_ref':'rank_object','metric_ref':'query_scope.rank_metric',
        'limit_ref':'top_n','source':'program:verified_ranked_subject','source_evidence':subject}
    if numerator.get('selection') not in (None,selection):return analysis
    filters=numerator.get('filters') or [];kept=[];resolved=False
    for item in filters:
        # Extra scope/period/N/metric keys are substantive until proved, not
        # disposable model noise. Dual field/value spellings must agree.
        allowed={'field','column','operator','value','values','metric'}
        plain=(isinstance(item,dict) and set(item)<=allowed and
            not (item.get('field') and item.get('column') and item['field']!=item['column']) and
            ('value' not in item or 'values' not in item or
                type(item['value']) is type(item['values']) and item['value']==item['values']))
        field=(item.get('column') or item.get('field')) if plain else None
        value=item.get('value',item.get('values')) if plain else None
        legacy=(field=='customer.customer_id' and item.get('operator')=='=' and
                value=='rank_1_by_invoice_revenue' and item.get('metric','invoice_revenue')=='invoice_revenue')
        rank=(field=='customer.rank' and item.get('operator')=='top' and type(value) is int and value==1 and
              item.get('metric')=='invoice_revenue')
        if legacy or rank:
            resolved=True
        else:kept.append(item)
    if resolved:
        numerator['filters']=kept
        numerator['selection']=selection
    return analysis
