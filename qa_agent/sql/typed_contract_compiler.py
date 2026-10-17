"""Small, fail-closed compiler for two already confirmed invoice plans.

Pure construction only. All normal SQL validation and readonly execution must
still happen downstream. Unsupported substantive conditions return None.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from sqlglot import exp


@dataclass(frozen=True)
class CompiledQuery:
    sql: str
    method: str


class _Unsupported(ValueError):
    pass


def _get(value, key, default=None):
    return value.get(key, default) if isinstance(value, dict) else getattr(value, key, default)


def _empty(value):
    return value is None or value == [] or value == {} or value == ''


def _column(name):
    return exp.column(name, table='i', quoted=True)


def _numeric_type(value):
    return bool(re.fullmatch(r'(?:smallint|integer|bigint|int2|int4|int8|(?:numeric|decimal)(?:\s*\(\s*\d+\s*(?:,\s*\d+\s*)?\))?)',str(value).strip().casefold()))


def _exact_amount_type(value):
    return bool(re.fullmatch(r'(?:numeric|decimal)(?:\s*\(\s*\d+\s*(?:,\s*\d+\s*)?\))?',str(value).strip().casefold()))


def _date_type(value):
    return bool(re.fullmatch(r'(?:date|timestamp(?:\(\d+\))?(?: without time zone)?)',str(value).strip().casefold()))


def _literal(value, data_type):
    kind=str(data_type).casefold()
    if value is None or isinstance(value, (bool,float)):
        raise _Unsupported('NULL requires an explicit IS operator; binary floats are not exact literals.')
    if _numeric_type(kind):
        if not isinstance(value,(int,Decimal)):
            raise _Unsupported('Numeric fields require an exact typed number.')
        number=Decimal(value)
        if not number.is_finite():
            raise _Unsupported('Non-finite number.')
        if any(x in kind for x in ('integer','int2','int4','int8','smallint','bigint')) and number != number.to_integral_value():
            raise _Unsupported('Integral field requires an integral value.')
        return exp.Literal.number(str(number))
    if _date_type(kind):
        if not isinstance(value,str):
            raise _Unsupported('Date literal must be an explicit ISO string.')
        parsed=datetime.fromisoformat(value) if 'T' in value or ' ' in value else date.fromisoformat(value)
        if isinstance(parsed,datetime) and parsed.tzinfo is not None:
            raise _Unsupported('Timezone conversion is outside this compiler.')
        if kind == 'date' and isinstance(parsed,datetime):
            raise _Unsupported('Do not truncate a datetime to DATE implicitly.')
        return exp.Cast(this=exp.Literal.string(value),to=exp.DataType.build('date' if kind=='date' else 'timestamp'))
    if re.fullmatch(r'(?:text|(?:character varying|varchar|character|char)(?:\s*\(\s*\d+\s*\))?)',kind):
        if not isinstance(value,str):
            raise _Unsupported('Text fields require a string value.')
        return exp.Literal.string(value)
    raise _Unsupported('Unsupported physical field type.')


def _filter(item, columns):
    if not isinstance(item,dict):
        raise _Unsupported('A filter must be typed.')
    metadata={'column','field','operator','value','values','binding_scope','source','scope_evidence',
       'mention_id','method','evidence_ref','candidate_id','field_owner_proof','source_evidence',
       'lifetime','applies_to','evidence','value_text'}
    if any(key not in metadata for key in item):
        raise _Unsupported('Unknown filter modifier cannot be dropped.')
    if item.get('binding_scope') not in {None,'global'} or item.get('applies_to') not in {None,'global'}:
        raise _Unsupported('Operand-local and eligibility filters are unsupported.')
    field=item.get('column') or item.get('field')
    if item.get('column') and item.get('field') and item['column'] != item['field']:
        raise _Unsupported('Conflicting physical filter owners.')
    if not isinstance(field,str) or field.count('.')!=1:
        raise _Unsupported('Use a physical table.column filter.')
    owner,name=field.split('.')
    if owner!='invoice' or name not in columns:
        raise _Unsupported('Only actual invoice fields are supported.')
    operator=item.get('operator')
    if not isinstance(operator,str):
        raise _Unsupported('Missing operator.')
    if operator != operator.strip().upper():
        raise _Unsupported('Operator must already match the binding-validator form.')
    # Keep this initial bounded set compatible with the existing binding
    # validator; unsupported NULL tests/NOT IN fall back without losing them.
    if operator not in {'=','!=','IN','>','>=','<','<='}:
        raise _Unsupported('Operator is outside the existing binding-validator contract.')
    column=_column(name)
    if 'value' in item and 'values' in item and item['value'] != item['values']:
        raise _Unsupported('Conflicting filter values.')
    value=item.get('value',item.get('values'))
    if operator == 'IN':
        if not isinstance(value,list) or not value:
            raise _Unsupported('Membership requires a nonempty explicit list.')
        node=exp.In(this=column,expressions=[_literal(part,columns[name].data_type) for part in value])
        return node
    cls={'=':exp.EQ,'!=':exp.NEQ,'>':exp.GT,'>=':exp.GTE,'<':exp.LT,'<=':exp.LTE}.get(operator)
    if cls is None or isinstance(value,(list,dict,tuple)):
        raise _Unsupported('Unsupported comparison.')
    return cls(this=column,expression=_literal(value,columns[name].data_type))


def _period(time_scope, date_column):
    if not isinstance(time_scope,dict):
        raise _Unsupported('A complete confirmed period is required.')
    if any(key not in {'current','all_data','label'} for key in time_scope):
        raise _Unsupported('Additional period/base conditions are unsupported.')
    current=time_scope.get('current')
    if time_scope.get('all_data') is True:
        if not _empty(current):
            raise _Unsupported('All-data conflicts with a current period.')
        return []
    if 'all_data' in time_scope and time_scope['all_data'] is not False and time_scope['all_data'] is not None:
        raise _Unsupported('All-data must be an explicit boolean.')
    if not isinstance(current,dict):
        raise _Unsupported('Missing current period.')
    metadata={'start','end','label','grain','year_source','reference_datetime','timezone','start_inclusive','end_inclusive'}
    if any(key not in metadata for key in current):
        raise _Unsupported('Unknown current-period restriction.')
    if current.get('start_inclusive',True) is not True or current.get('end_inclusive',False) is not False:
        raise _Unsupported('Only confirmed half-open periods are supported.')
    start,end=current.get('start'),current.get('end')
    if not isinstance(start,str) or not isinstance(end,str):
        raise _Unsupported('Both period boundaries are required.')
    left=datetime.fromisoformat(start)
    right=datetime.fromisoformat(end)
    if left.tzinfo is not None or right.tzinfo is not None or not left<right:
        raise _Unsupported('Invalid/reversed/timezone-dependent period.')
    return [exp.GTE(this=_column('invoice_date'),expression=_literal(start,date_column.data_type)),
            exp.LT(this=_column('invoice_date'),expression=_literal(end,date_column.data_type))]


def compile_typed_contract(analysis: Any, catalog: Any) -> CompiledQuery | None:
    """Return a new SELECT AST's SQL for a supported complete contract, else None."""
    try:
        fields={'task_type','metric','time_scope','comparison','numerator','denominator','rank_object','top_n','order','region_scope','region_ambiguous','scope_missing','time_ambiguous','conflicts','grouping','filters','assumptions','default_assumptions','evidence_spans','query_scope','output_requirements','condition_sources','clarification_requests'}
        payload=analysis if isinstance(analysis,dict) else analysis.model_dump() if hasattr(analysis,'model_dump') else vars(analysis)
        if any(key not in fields and not _empty(value) for key,value in payload.items()):
            return None
        table=catalog.get_table('invoice','public')
        columns={column.name:column for column in table.columns}
        if not {'total','customer_id','invoice_date'}.issubset(columns):
            return None
        if not _exact_amount_type(columns['total'].data_type) or not _date_type(columns['invoice_date'].data_type):
            return None
        if _get(analysis,'task_type')!='aggregation':
            return None
        for key in ('comparison','numerator','denominator','rank_object','top_n','order','grouping','conflicts','clarification_requests'):
            if not _empty(_get(analysis,key)):
                return None
        if any(_get(analysis,key,False) is not False for key in ('region_ambiguous','scope_missing','time_ambiguous')):
            return None
        if _get(analysis,'region_scope') not in {None,'invoice.billing_country','customer.country'}:
            return None
        scope=_get(analysis,'query_scope',{})
        if not isinstance(scope,dict):
            return None
        metric=_get(analysis,'metric')
        is_mean=metric=='average_customer_amount'
        contract=scope.get('extrema_difference')
        is_gap=metric=='invoice_revenue' and isinstance(contract,dict)
        if not(is_mean or is_gap):
            return None
        empty_roles={'qualification_filters','pending_filters','partition_by','eligibility_object','ranking_scope','per_group_limit','numerator','denominator'}
        common={'aggregation_scope','output_shape','money_precision_source'}|empty_roles
        if 'money_precision_source'in scope:
            from qa_agent.sql.money_precision_source import valid_money_precision_metadata
            if not valid_money_precision_metadata(scope['money_precision_source']):return None
        allowed=common|({'average_grain','average_grain_missing'} if is_mean else {'extrema_difference'})
        if any(key not in allowed for key in scope):
            return None
        if any(not _empty(scope.get(key)) for key in empty_roles):
            return None
        aggregation=scope.get('aggregation_scope')
        accepted_aggregations={None,'','all','all_invoices','all_invoice_rows','all_matching_invoices','all_matching_invoice_rows'}
        if aggregation not in accepted_aggregations:
            return None
        if is_mean:
            if scope.get('average_grain')!='customer' or scope.get('average_grain_missing',False) is not False:
                return None
            if scope.get('output_shape') not in {None,'','scalar','scalar_value','single_value'}:
                return None
            requirements={'average_customer_amount','average_customer_amount_single_value','scalar_value','single_value','返回单一数值','金额保留两位小数','说明来自数据库','结论加一个数'}
            expression=exp.Div(this=exp.Sum(this=_column('total')),expression=exp.Nullif(this=exp.Count(this=exp.Distinct(expressions=[_column('customer_id')])),expression=exp.Literal.number(0)),typed=True)
            method='typed_contract_average_customer_amount'
        else:
            if set(contract) != {'grain','metric','operation','source','source_evidence'} or any(contract.get(key)!=value for key,value in {'grain':'month','metric':'invoice_revenue','operation':'max_minus_min','source':'program:explicit_extrema_difference'}.items()):
                return None
            if not isinstance(contract.get('source_evidence'),str) or not contract['source_evidence'].strip():
                return None
            if scope.get('output_shape') not in {None,'','scalar_absolute_difference'}:
                return None
            requirements={'max_month_minus_min_month','max_min_month_difference','scalar_absolute_difference','金额保留两位小数','说明来自数据库','结论加一个数'}
            method='typed_contract_monthly_extrema_difference'
        actual_requirements=_get(analysis,'output_requirements',[])
        if not isinstance(actual_requirements,list) or any(item not in requirements for item in actual_requirements):
            return None
        filters=_get(analysis,'filters',[])
        if not isinstance(filters,list):
            return None
        if _get(analysis,'region_scope')=='customer.country' and any(
            isinstance(item,dict) and (item.get('column') or item.get('field')) in {
                'customer.country','invoice.billing_country','invoice.billing_city',
                'invoice.billing_state','invoice.billing_postal_code'} for item in filters):
            return None
        # A country-owner role without an actual geographic predicate,
        # grouping or qualification is inert metadata; never invent a filter
        # from that role. All substantive query-scope roles were checked above.
        equality_values={}
        for item in filters:
            if isinstance(item,dict) and item.get('operator')=='=':
                field=item.get('column') or item.get('field')
                previous=equality_values.setdefault(field,item.get('value'))
                if previous != item.get('value'):
                    # Project value bindings can mean an alternative-candidate
                    # union here. Require an explicit IN before compilation.
                    return None
        predicates=_period(_get(analysis,'time_scope'),columns['invoice_date'])
        predicates.extend(_filter(item,columns) for item in filters)
        source=exp.Table(this=exp.to_identifier('invoice',quoted=True),db=exp.to_identifier('public',quoted=True),alias=exp.TableAlias(this=exp.to_identifier('i')))
        if is_mean:
            query=exp.select(exp.alias_(expression,'average_customer_amount',quoted=True)).from_(source)
        else:
            # Missing calendar months stay missing; SUM/MAX/MIN retain SQL NULL.
            if (_get(analysis,'time_scope') or {}).get('all_data') is True and columns['invoice_date'].nullable:
                return None
            month=exp.TimestampTrunc(this=_column('invoice_date'),unit=exp.Var(this='MONTH'))
            monthly=exp.select(exp.alias_(month.copy(),'month_start',quoted=True),exp.alias_(exp.Sum(this=_column('total')),'monthly_amount',quoted=True)).from_(source).group_by(month.copy())
            if predicates:
                monthly=monthly.where(exp.and_(*predicates))
            amount=exp.column('monthly_amount',table='m',quoted=True)
            gap=exp.Sub(this=exp.Max(this=amount.copy()),expression=exp.Min(this=amount.copy()))
            query=exp.select(exp.alias_(gap,'max_min_diff',quoted=True)).from_(monthly.subquery('m'))
        if is_mean and predicates:
            query=query.where(exp.and_(*predicates))
        return CompiledQuery(sql=query.sql(dialect='postgres'),method=method)
    except (ValueError,TypeError,AttributeError,KeyError,InvalidOperation):
        # Fail closed: the caller's bounded normal path may generate unsupported
        # shapes; this function never fabricates a reduced-condition query.
        return None
