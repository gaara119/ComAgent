"""Prove a confirmed D3 invoice period survives SQL regeneration.

This bounded guard is used for patched/clarified Chinook queries with one
current period. Growth and ratio tasks have different period semantics and
are not routed here. No SQL is rewritten and no database is queried here.
"""
from __future__ import annotations

from datetime import datetime
import json

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope, walk_in_scope
from sqlglot.schema import MappingSchema

from qa_agent.sql.validator import SQLValidationError


def validate_current_patch_contract(sql: str, catalog, analysis, resolutions: list[dict]) -> None:
    """Reject retired filter atoms and stale ranking sizes before repair locks.

    Reads only the merged contract, trusted patch history and physical catalog.
    The previous filters are captured by apply_patches before mutation. Values
    still active in a different local ratio role are not treated as globally
    retired; the dedicated ratio guard proves those independent operand scopes.
    It never rewrites SQL or substitutes an entity/date/value.
    """
    if not resolutions:
        return

    def key(binding):
        return (binding.get('column'),binding.get('operator'),
                json.dumps(binding.get('value'),ensure_ascii=False,sort_keys=True),
                binding.get('binding_scope'))

    active=list(analysis.filters or [])
    active_keys={key(item) for item in active}
    historical=[]
    for resolution in resolutions:
        historical.extend(item for item in resolution.get('previous_filters',[]) if isinstance(item,dict))
        for patch in resolution.get('patches',[]):
            if patch.get('path')=='filters':
                values=patch.get('value') or []
                historical.extend(item for item in (values if isinstance(values,list) else [values]) if isinstance(item,dict))
    retired={key(item):item for item in historical if key(item) not in active_keys}

    checked=normalize_identifiers(sqlglot.parse_one(sql,read='postgres'),dialect='postgres')
    # TopN expresses the query size, not the response's max_rows display cap.
    if analysis.task_type=='ranking' and analysis.top_n is not None:
        limit=checked.args.get('limit')
        value=limit.expression if limit is not None else None
        if (not isinstance(value,exp.Literal) or value.is_string or
                not value.this.isdigit() or int(value.this)!=analysis.top_n):
            raise SQLValidationError(f'当前排名合同要求 LIMIT {analysis.top_n}；不能继续使用旧TopN，不能用展示行数上限替换用户请求。')
        offset=checked.args.get('offset')
        if offset is not None:
            offset_value=offset.expression
            if not isinstance(offset_value,exp.Literal) or offset_value.this!='0':
                raise SQLValidationError('当前排名合同要求前N名；不能用非零 OFFSET 跳过前面的名次。')

    try:
        checked=qualify(checked,dialect='postgres',db='public',
                        schema=MappingSchema(catalog.sqlglot_schema(),dialect='postgres',normalize=False),
                        allow_partial_qualification=False,validate_qualify_columns=True)
    except Exception as exc:
        raise SQLValidationError('当前补丁核验无法建立退役条件的真实字段作用域。') from exc
    scopes=list(traverse_scope(checked))
    # Some saved scalar-aggregation intents retain task_type=lookup. A direct
    # SELECT with aggregates is still an aggregation; do not key this guard on
    # a DEV question ID. Comparisons/ratios and multi-scope algebra remain under
    # their dedicated rules, not this intentionally bounded expression proof.
    simple_measure=(analysis.metric in {'purchased_quantity','detail_revenue','invoice_count','average_invoice_amount'} and
                    analysis.task_type in {'lookup','aggregation','ranking'} and
                    len(scopes)==1 and isinstance(checked,exp.Select))
    if simple_measure:
        sources={alias:source for alias,(_,source) in scopes[0].selected_sources.items()}

        def unwrap(node):
            while isinstance(node,(exp.Alias,exp.Paren,exp.Cast,exp.Round,exp.Coalesce)):
                node=node.this
            return node

        def field(node,table,name):
            node=unwrap(node)
            if not isinstance(node,exp.Column):
                return False
            source=sources.get(node.table)
            return isinstance(source,exp.Table) and source.db in {'public',''} and source.name==table and node.name==name

        def amount(node):
            node=unwrap(node)
            return (isinstance(node,exp.Mul) and
                    ((field(node.left,'invoice_line','unit_price') and field(node.right,'invoice_line','quantity')) or
                     (field(node.right,'invoice_line','unit_price') and field(node.left,'invoice_line','quantity'))))

        def matches(node):
            node=unwrap(node)
            if analysis.metric=='purchased_quantity':
                return isinstance(node,exp.Sum) and field(node.this,'invoice_line','quantity')
            if analysis.metric=='detail_revenue':
                return isinstance(node,exp.Sum) and amount(node.this)
            if analysis.metric=='average_invoice_amount':
                return isinstance(node,exp.Avg) and field(node.this,'invoice','total')
            if analysis.metric=='invoice_count' and isinstance(node,exp.Count):
                value=node.this
                if isinstance(value,exp.Distinct):
                    return len(value.expressions)==1 and field(value.expressions[0],'invoice','invoice_id')
                return field(value,'invoice','invoice_id')
            return False

        projections=[node for node in checked.expressions if any(isinstance(item,exp.AggFunc) for item in node.walk())]
        if not projections or any(not matches(node) for node in projections):
            required={'purchased_quantity':'SUM(invoice_line.quantity)',
                      'detail_revenue':'SUM(invoice_line.unit_price * invoice_line.quantity)',
                      'invoice_count':'COUNT(invoice.invoice_id)',
                      'average_invoice_amount':'AVG(invoice.total)'}[analysis.metric]
            raise SQLValidationError(f'当前补丁指标为 {analysis.metric}；该限定单作用域查询需要实际 {required}，不能沿用旧指标或额外投影其它聚合指标。')

    for scope in scopes:
        sources={alias:source for alias,(_,source) in scope.selected_sources.items()}

        def visit(node):
            if node is None:
                return
            if isinstance(node,(exp.Where,exp.Having,exp.Paren)):
                visit(node.this)
                return
            if isinstance(node,(exp.And,exp.Or)):
                visit(node.left);visit(node.right)
                return
            columns=[]
            for column in walk_in_scope(node):
                if isinstance(column,exp.Column):
                    source=sources.get(column.table)
                    if isinstance(source,exp.Table) and source.db in {'public',''}:
                        columns.append(f'{source.name}.{column.name}')
            literals={literal.this.casefold().strip('%_') for literal in walk_in_scope(node)
                      if isinstance(literal,exp.Literal) and literal.is_string}
            for binding in retired.values():
                # Local CASE predicates and operand switches are checked by the
                # existing independent ratio guard, not a global filter lock.
                if binding.get('binding_scope') in {'numerator','denominator'}:
                    continue
                values=binding.get('value')
                values=values if isinstance(values,list) else [values]
                current_values=set()
                for item in active:
                    if (item.get('column')==binding.get('column') and
                            item.get('binding_scope')==binding.get('binding_scope') and
                            item.get('operator') in {'=','IN'}):
                        present=item.get('value')
                        current_values.update(str(value).casefold() for value in
                                              (present if isinstance(present,list) else [present]))
                values=[value for value in values if str(value).casefold() not in current_values]
                if binding.get('column') in columns and any(str(value).casefold() in literals for value in values):
                    raise SQLValidationError(f"SQL 恢复了已被用户替换或删除的旧筛选 {binding.get('column')} {binding.get('operator')} {values!r}；只能依据当前合并合同重新生成。")

        visit(scope.expression.args.get('where'))
        visit(scope.expression.args.get('having'))
        for join in scope.expression.args.get('joins') or []:
            visit(join.args.get('on'))


def validate_confirmed_invoice_period(sql: str, catalog, current: dict) -> None:
    def instant(value):
        try:
            result=datetime.fromisoformat(str(value))
        except (ValueError,TypeError):
            return None
        return result if result.tzinfo is None else None

    start,end=instant(current.get('start')),instant(current.get('end'))
    if start is None or end is None or start>=end:
        raise SQLValidationError('已确认期间不是有效的左闭右开日期范围。')
    checked=normalize_identifiers(sqlglot.parse_one(sql,read='postgres'),dialect='postgres')
    try:
        checked=qualify(checked,dialect='postgres',db='public',
                        schema=MappingSchema(catalog.sqlglot_schema(),dialect='postgres',normalize=False),
                        allow_partial_qualification=False,validate_qualify_columns=True)
        scopes=list(traverse_scope(checked))
    except Exception as exc:
        raise SQLValidationError('确认期间核验无法建立真实 invoice 字段作用域。') from exc
    if len(scopes)!=1 or not isinstance(checked,exp.Select):
        raise SQLValidationError('已确认发票期间的限定保护要求单个 SELECT 作用域；请把确认期间放入真实 invoice 的 WHERE，不能用多层来源替换或缩窄。')
    seen=False
    for scope in scopes:
        sources={alias:source for alias,(_,source) in scope.selected_sources.items()}
        invoice_aliases={alias for alias,source in sources.items() if isinstance(source,exp.Table) and
                         source.name=='invoice' and source.db in {'public',''}}
        if not invoice_aliases:
            continue
        seen=True

        def real_date(node,alias):
            return isinstance(node,exp.Column) and node.table==alias and node.name=='invoice_date'

        def literal(node):
            while isinstance(node,(exp.Paren,exp.Cast)):
                node=node.this
            return instant(node.this) if isinstance(node,exp.Literal) and node.is_string else None

        def constraints(node,alias):
            if node is None:
                return set()
            if isinstance(node,(exp.Where,exp.Paren)):
                return constraints(node.this,alias)
            if isinstance(node,exp.And):
                return constraints(node.left,alias)|constraints(node.right,alias)
            if isinstance(node,exp.Or):
                return constraints(node.left,alias)&constraints(node.right,alias)
            found=None
            if isinstance(node,(exp.GTE,exp.LT)) and real_date(node.left,alias):
                found=('>=' if isinstance(node,exp.GTE) else '<',literal(node.right))
            elif isinstance(node,(exp.LTE,exp.GT)) and real_date(node.right,alias):
                found=('>=' if isinstance(node,exp.LTE) else '<',literal(node.left))
            if found in {('>=',start),('<',end)}:
                return {found}
            if any(real_date(column,alias) for column in walk_in_scope(node) if isinstance(column,exp.Column)):
                raise SQLValidationError('SQL 日期筛选必须保留已确认期间的等价边界，禁止替换或额外缩窄期间。')
            return set()

        for alias in invoice_aliases:
            mandatory=constraints(scope.expression.args.get('where'),alias)
            if not {('>=',start),('<',end)}<=mandatory:
                raise SQLValidationError(f"SQL 未保留已确认 invoice 期间：invoice_date >= '{current['start']}' AND invoice_date < '{current['end']}'；必须是 WHERE 强制条件，不能用 SELECT 字面值或 OR 绕过。")
    if not seen:
        raise SQLValidationError('确认的发票期间必须作用于真实 invoice 扫描。')


def validate_confirmed_country_output(sql: str,catalog,target: str) -> None:
    """A confirmed country-scope switch must also govern country result columns.

    WHERE bindings are checked separately. Here only SELECT/GROUP BY/HAVING
    country sources are constrained; independent employee columns stay intact.
    Result aliases are labels, so c.country AS billing_country is still c.country.
    """
    if target not in {'invoice.billing_country','customer.country'}:
        raise SQLValidationError('确认地区的输出核验只支持账单国家或客户所在地的明确字段。')
    checked=normalize_identifiers(sqlglot.parse_one(sql,read='postgres'),dialect='postgres')
    try:
        checked=qualify(checked,dialect='postgres',db='public',
                        schema=MappingSchema(catalog.sqlglot_schema(),dialect='postgres',normalize=False),
                        allow_partial_qualification=False,validate_qualify_columns=True)
        scopes=list(traverse_scope(checked))
    except Exception as exc:
        raise SQLValidationError('确认地区输出核验无法建立真实国家字段作用域。') from exc
    if len(scopes)!=1 or not isinstance(checked,exp.Select):
        raise SQLValidationError('确认地区输出的限定核验要求单个 SELECT 作用域，不能用派生列别名替换真实地区来源。')
    sources={alias:source for alias,(_,source) in scopes[0].selected_sources.items()}
    forbidden='customer.country' if target=='invoice.billing_country' else 'invoice.billing_country'
    nodes=[*checked.expressions,checked.args.get('group'),checked.args.get('having')]
    for node in nodes:
        if node is None:
            continue
        for column in node.find_all(exp.Column):
            source=sources.get(column.table)
            if isinstance(source,exp.Table) and source.db in {'public',''}:
                actual=f'{source.name}.{column.name}'
                if actual==forbidden:
                    raise SQLValidationError(f'已确认地区归属为 {target}；SELECT/GROUP BY/HAVING 不能继续使用旧的 {forbidden}，相同数据结果不能代替真实字段口径。')
