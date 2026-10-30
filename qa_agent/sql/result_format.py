"""Describe percentage presentation without changing database evidence."""
from decimal import Decimal, InvalidOperation

import sqlglot
from sqlglot import exp


def percentage_formats(sql, columns, task_type, *, catalog=None, question=None):
    if task_type not in {"ratio", "growth", "yoy"}:
        # BASE/S1 deliberately have no component-3 task state. Their external
        # percentage display can still use the actual user's explicit request
        # plus the same physical SQL-expression proof, without enabling a gate.
        import re
        if not (task_type is None and isinstance(question,str)
                and re.search(r'占比|比例|百分|增长率|同比|环比|\bpercent(?:age)?\b',question,re.I)
                and not re.search(r'多少倍|几倍|倍数|\btimes\b',question,re.I)):
            return {}
    try:
        from qa_agent.sql.projection_semantics import projection_semantics
        meanings=projection_semantics(sql,columns,catalog=catalog)
        result = {}
        for name,meaning in meanings.items():
            if meaning['kind']!='ratio':continue
            multiplier=Decimal(meaning.get('ratio_scale','1'))
            if multiplier not in(1,100):continue
            result[name] = {"kind": "percentage", "scale": 1 if multiplier==100 else 100,
                            "raw_values_preserved": True, "source": "sql_projection"}
        return result
    except Exception:
        return {}


def display_percentage(value, rule):
    if value is None:
        return "NULL"
    try:
        number = Decimal(str(value)) * Decimal(str(rule["scale"]))
        return f"{number:.2f}%" if number.is_finite() else str(value)
    except (InvalidOperation, KeyError, ValueError):
        return str(value)


def presentation_formats(sql, columns, base_formats, *, query_scope=None, brief='', catalog=None, question=None):
    """Publish the same verified display roles/precision used by the answer.

    Explicit digits=None is an intentional raw display, different from a
    legacy response with no digits key. No raw result value is changed.
    """
    from qa_agent.sql.projection_semantics import projection_semantics
    from qa_agent.sql.percentage_precision import requested_percent_digits
    from qa_agent.sql.money_precision_source import valid_money_precision_metadata
    scope=query_scope or{}
    def error(message):raise ValueError(message)
    digits=requested_percent_digits({'query_scope':scope},error)
    source=scope.get('percent_precision_source')or{}
    if source.get('source')=='program:explicit_percent_precision_pending':
        raise ValueError('百分比展示精度仍待确认。')
    raw=source.get('source')=='program:explicit_percent_precision_removed'
    # Optional actual S1 current source; no model precision or new authority.
    # Existing program semantic precision/removal remains higher priority.
    if digits is None and not source and isinstance(question, str):
        digits=requested_percent_digits({'output_requirements':[question]},error)
    if digits is None and not source:
        digits=requested_percent_digits({'output_requirements':[brief]},error)
    percent_digits=None if raw else digits if digits is not None else 2
    money_source=scope.get('money_precision_source');money_digits=2
    if money_source is not None:
        if not valid_money_precision_metadata(money_source):
            raise ValueError('金额展示精度缺少合法程序来源或尚待确认。')
        money_digits=None if money_source['status']=='removed'else money_source['digits']
    meanings=projection_semantics(sql,columns,catalog=catalog)
    output={}
    for column in columns:
        kind=meanings.get(column,{}).get('kind');rule=base_formats.get(column)or{}
        common={'source':'actual_sql_projection','raw_values_preserved':True,'rounding':'half_even'}
        if kind in{'count','rank'}:
            output[column]={**common,'kind':'count'}
        elif kind=='money':
            output[column]={**common,'kind':'money','digits':money_digits}
        elif rule and rule.get('kind','percentage')=='percentage'and kind not in{'field','count','money','rank'}:
            if rule.get('scale')in(1,100)and not isinstance(rule.get('scale'),bool):
                output[column]={**common,'kind':'percentage','scale':rule['scale'],'digits':percent_digits}
    return output


def display_numeric(value, rule):
    """Format a copy using trusted metadata; malformed rules retain raw data.

    Existing Python Decimal half-even display is retained. A local precision
    sized to the actual value prevents the default 28-digit context from
    rounding long evidence before the requested presentation rounding.
    """
    from decimal import localcontext, ROUND_HALF_EVEN
    if value is None or isinstance(value,bool)or not isinstance(rule,dict):return value
    kind=rule.get('kind');has_digits='digits'in rule
    if has_digits and rule.get('source')!='actual_sql_projection':return value
    if not has_digits and rule.get('source')not in{None,'sql_projection','actual_sql_projection'}:return value
    if rule.get('rounding','half_even')!='half_even':return value
    try:
        number=Decimal(str(value))
        if not number.is_finite():return value
        if kind=='count':
            return str(int(number))if rule.get('source')=='actual_sql_projection'and number==number.to_integral_value()else value
        if kind not in{'percentage','money'}:return value
        digits=rule.get('digits',2)
        if digits is not None and(type(digits)is not int or not 0<=digits<=9):return value
        scale=rule.get('scale',1)
        if type(scale)is not int or scale not in((1,100)if kind=='percentage'else(1,)):return value
        if kind=='money'and not has_digits:return value
        with localcontext()as ctx:
            ctx.prec=max(50,len(number.as_tuple().digits)+abs(number.adjusted())+20)
            ctx.rounding=ROUND_HALF_EVEN
            scaled=number*Decimal(scale)
            result=format(scaled,'f')if digits is None else f'{scaled:.{digits}f}'
            return result+('%'if kind=='percentage'else'')
    except(InvalidOperation,ValueError,TypeError):return value
