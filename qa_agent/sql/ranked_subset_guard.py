"""Bounded proof of a projected ratio whose numerator sums a real Top-N.

Only current intent and authentic schema are consumed. No evaluation IDs,
reference SQL, saved labels, API calls or executable rewrites are used.
"""
from __future__ import annotations

from decimal import Decimal,InvalidOperation
from datetime import date
import re

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope,walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import (_physical_field,_measure_matches,_mandatory_atoms,_midnight_date,
                                         _invoice_grain_is_preserved,_active_scopes)
from qa_agent.sql.validator import SQLValidationError


class RankedRatioContractUnsupported(SQLValidationError):
    """A current operand state outside this proof cannot be repaired by SQL."""

    code = 'semantic_contract_unsupported'
    retryable = False
    sql_repairable = False

    def __init__(self, reason, message):
        self.reason = reason
        super().__init__('月份排名比例合同暂不支持：'+message)


def _invoice_date_identity(field,catalog):
    if not isinstance(field,str):return None
    if catalog is None:
        return 'invoice.invoice_date' if field=='invoice.invoice_date' else None
    matches=[(table,column) for table in catalog.tables for column in table.columns
             if column.name=='invoice_date' and
             (field=='invoice_date' or field==table.name+'.'+column.name or
              field==table.schema+'.'+table.name+'.'+column.name)]
    if len(matches)!=1:return None
    table,column=matches[0]
    if (table.name!='invoice' or table.schema!='public' or
            not str(column.data_type).lower().startswith(('date','timestamp'))):return None
    return 'invoice.invoice_date'


def _validate_month_operand_state(analysis,catalog=None):
    """Share the existing state-only limits with preflight and SQL proof.

    Nothing here recognizes/removes a mirror, changes a scope or proves SQL.
    Only the producer can canonicalize an actual-source-verified mirror.
    """
    query=getattr(analysis,'query_scope',{})
    if not isinstance(query,dict):
        raise RankedRatioContractUnsupported('numerator_shape','操作数合同必须为已规范的结构对象。')
    numerator=query.get('numerator',{})
    if not isinstance(numerator,dict):
        raise RankedRatioContractUnsupported('numerator_shape','月份排名分子合同必须为已规范的结构对象。')
    if 'filters'in numerator and (not isinstance(numerator['filters'],list)or numerator['filters']):
        raise RankedRatioContractUnsupported('unproved_numerator_filters','月份排名分子仍有独立或未规范筛选，当前证明不能默许丢弃。')
    if numerator.get('metric')is not None and numerator['metric']!=analysis.metric:
        raise RankedRatioContractUnsupported('numerator_metric','月份排名分子度量与实际排名合计口径不一致。')
    if 'period'in numerator:
        current=(analysis.time_scope or{}).get('current')or{}
        local=numerator['period']
        if (not isinstance(local,dict)or not current.get('start')or not current.get('end')or
                any(local.get(key)!=current[key]for key in('start','end'))):
            raise RankedRatioContractUnsupported('local_numerator_period','月份排名分子的局部期间不完整或与当前排名期间不同，不能静默回退。')
    denominator=query.get('denominator',{})
    filters=denominator.get('filters',[]) if isinstance(denominator,dict) else []
    for binding in filters if isinstance(filters,list) else []:
        if not isinstance(binding,dict)or str(binding.get('operator','')).upper()!='IN':continue
        fields=[binding[key] for key in ('column','field') if binding.get(key)not in(None,'')]
        identities=[_invoice_date_identity(field,catalog)for field in fields]
        if 'invoice.invoice_date'not in identities:continue
        if any(identity!='invoice.invoice_date'for identity in identities):
            raise RankedRatioContractUnsupported('denominator_date_field','分母日期条件的field与column身份矛盾，不能择一丢弃。')
        values=[binding[key]for key in ('value','values')if key in binding]
        if not values:
            raise RankedRatioContractUnsupported('denominator_date_members','分母物理日期IN缺少实际日期成员，不能把排名散文当日期值。')
        sets=[]
        for value in values:
            members=value if isinstance(value,list)else[value]
            valid=bool(members)
            for member in members:
                if not isinstance(member,str)or re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',member)is None:
                    valid=False;break
                try:date.fromisoformat(member)
                except ValueError:valid=False;break
            if not valid:
                raise RankedRatioContractUnsupported('denominator_date_members','分母物理日期IN只能保留有效ISO日期成员，非日期或排名散文须先解决当前合同，不能用SQL修复。')
            sets.append(set(members))
        if len(sets)>1 and any(items!=sets[0]for items in sets[1:]):
            raise RankedRatioContractUnsupported('denominator_date_members','分母日期IN的value与values实际成员矛盾，不能忽略其中一份。')


def preflight_ranked_ratio_contract(analysis,*,catalog=None):
    """Fail before SQL generation for the bounded monthly ratio state only.

    The caller must also keep this behind the actual semantic-gate flag. The
    return value is not a SQL proof or execution authorization. Ordinary month
    aggregation, customer winners and other ratio families are not routed here.
    """
    if (getattr(analysis,'task_type',None)not in {'ratio','growth','yoy'}or
            getattr(analysis,'rank_object',None)!='month'or
            'ranked_subset_total'not in (getattr(analysis,'output_requirements',[])or[])):
        return {'applicable':False,'state_checked':False,'sql_proof_verified':False}
    _validate_month_operand_state(analysis,catalog)
    return {'applicable':True,'state_checked':True,
            'mode':'month_ranked_operand_state','sql_proof_verified':False}


def validate_ranked_ratio_contract(sql,catalog,analysis):
    tree=_qualified(sql,catalog)
    scopes=list(traverse_scope(tree))
    root=next((scope for scope in scopes if scope.parent is None),None)
    by_expression={id(scope.expression):scope for scope in scopes}
    if root is None or not isinstance(root.expression,exp.Select):
        raise SQLValidationError("排名子集比例缺少可证明的SELECT结果。")

    def deny(message):
        raise SQLValidationError("排名子集比例未通过："+message)

    if getattr(analysis,'rank_object',None)=='month':
        # This bounded path proves ranking over the current monthly stream.
        # A second scalar denominator does not prove independent numerator
        # predicates. Producers may remove a proved mirror, never this guard.
        _validate_month_operand_state(analysis,catalog)

    def unwrap(node):
        while isinstance(node,(exp.Alias,exp.Paren,exp.Cast,exp.Round)):
            node=node.this
        return node

    def literal(node,value):
        node=unwrap(node)
        try:
            return isinstance(node,exp.Literal) and not node.is_string and Decimal(node.this)==Decimal(value)
        except (InvalidOperation,TypeError):
            return False

    def trace(node,owner):
        seen=set();path=[]
        for _ in range(20):
            node=unwrap(node)
            if isinstance(node,exp.Subquery):
                target=by_expression.get(id(node.this))
                if target is None or len(target.expression.selects)!=1:
                    deny("标量子查询必须有唯一实际投影。")
                path.append(target);owner=target;node=target.expression.selects[0];continue
            if not isinstance(node,exp.Column):
                return node,owner,path
            if not node.table:
                marker=("output_alias",id(owner),node.name)
                projected=next((item for item in owner.expression.selects if item.alias_or_name==node.name),None)
                if projected is None or projected is node or marker in seen:
                    deny("未限定字段不是可追溯的真实输出别名。")
                seen.add(marker);node=projected;continue
            source=owner.sources.get(node.table)
            if isinstance(source,exp.Table):
                return node,owner,path
            if source is None:
                deny("派生投影没有可追溯来源。")
            marker=(id(source),node.name)
            if marker in seen:
                deny("派生投影出现循环。")
            seen.add(marker)
            projected=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
            if projected is None:
                deny("派生字段没有实际投影。")
            path.append(source);owner=source;node=projected
        deny("投影谱系超过有界深度。")

    def declared_value_kind(node,owner,depth=0):
        """Prove wrapper identity from actual column types, not current values."""
        if depth>20:deny("数值类型谱系超过有界深度。")
        node,owner,_=trace(node,owner)
        if isinstance(node,exp.TimestampTrunc):
            return ("date",None)
        if isinstance(node,(exp.Sum,exp.Min,exp.Max)):
            return declared_value_kind(node.this,owner,depth+1)
        if isinstance(node,exp.Case):
            branches=node.args.get("ifs") or []
            if node.this is None and len(branches)==1:
                return declared_value_kind(branches[0].args.get("true"),owner,depth+1)
        if isinstance(node,exp.Count):return ("numeric",0)
        if isinstance(node,exp.Mul):
            left=declared_value_kind(node.left,owner,depth+1)
            right=declared_value_kind(node.right,owner,depth+1)
            if left and right and left[0]==right[0]=="numeric":
                return ("numeric",left[1]+right[1])
        field=_physical_field(node,owner)
        if not field:return None
        parts=field.split(".")
        if len(parts)!=2:return None
        table,column=parts
        physical=next((item for item in catalog.get_table(table).columns if item.name==column),None)
        declared=str(physical.data_type).strip().lower() if physical else ""
        numeric=re.fullmatch(r"(?:numeric|decimal)\(\s*\d+\s*,\s*(\d+)\s*\)",declared)
        if numeric:return ("numeric",int(numeric[1]))
        if declared in {"smallint","integer","bigint"}:return ("numeric",0)
        if declared=="date" or declared.startswith("timestamp"):return ("date",None)
        return None

    def ratio_scale(node,owner,depth=0):
        if depth>20:return None
        node,owner,_=trace(node,owner)
        if isinstance(node,exp.Mul):
            for factor,other in ((node.left,node.right),(node.right,node.left)):
                if isinstance(factor,exp.Literal) and not factor.is_string:
                    scale=ratio_scale(other,owner,depth+1)
                    return None if scale is None else Decimal(factor.this)*scale
        if isinstance(node,exp.Div):
            left,_,_=trace(node.left,owner)
            if isinstance(left,exp.Mul):
                for factor,other in ((left.left,left.right),(left.right,left.left)):
                    if isinstance(factor,exp.Literal) and not factor.is_string:return Decimal(factor.this)
            return Decimal(1)
        return None

    # unwrap() is used only after every consumed CAST/ROUND has separately
    # proved it cannot change a ranked amount, its operand, or the month key.
    # In particular, rounding invoice cents before division is not formatting.
    for scope in _active_scopes(scopes):
        for transform in walk_in_scope(scope.expression):
            if not isinstance(transform,(exp.Round,exp.Cast)):continue
            kind=declared_value_kind(transform.this,scope)
            if kind is None:
                value,_,_=trace(transform.this,scope)
                if isinstance(transform,exp.Round) and value.find(exp.Div) is not None:
                    places=transform.args.get("decimals")
                    from qa_agent.sql.percentage_precision import requested_percent_digits
                    requested=requested_percent_digits(analysis,deny)
                    scale=ratio_scale(transform.this,scope)
                    if (not isinstance(places,exp.Literal) or places.is_string or not str(places.this).isdigit()
                            or requested is None or scale not in {Decimal(1),Decimal(100)}
                            or int(places.this)!=requested+(2 if scale==1 else 0)):
                        deny("最终比例ROUND必须与当前明确的百分比精度和真实尺度一致；无授权时交程序最终格式化。")
                if isinstance(transform,exp.Cast) and value.find(exp.Div) is not None:
                    target=transform.args["to"].sql(dialect="postgres")
                    numeric=re.fullmatch(r"(?:NUMERIC|DECIMAL)(?:\(\s*\d+\s*,\s*(\d+)\s*\))?",target,re.I)
                    if not numeric or "(" in target:
                        deny("最终比例只允许无精度限制的NUMERIC转换，不能用整数、浮点或固定精度CAST改变比例。")
                continue
            if isinstance(transform,exp.Round):
                places=transform.args.get("decimals")
                if (kind[0]!="numeric" or not isinstance(places,exp.Literal) or places.is_string
                        or not str(places.this).isdigit() or int(places.this)<kind[1]):
                    deny("排名金额/计数或月份键不能通过有损ROUND改变真实值。")
                continue
            target=transform.args["to"].sql(dialect="postgres")
            if kind[0]=="date":
                if target.upper() not in {"DATE","TIMESTAMP","TIMESTAMP WITHOUT TIME ZONE"}:
                    deny("真实发票日期/月度键不能转成整数、字符串或带时区值改变分组。")
                continue
            numeric=re.fullmatch(r"(?:NUMERIC|DECIMAL)(?:\(\s*\d+(?:\s*,\s*(\d+))?\s*\))?",target,re.I)
            target_scale=(int(numeric[1]) if numeric[1] is not None else (0 if "(" in target else None)) if numeric else None
            integer=target.upper() in {"SMALLINT","INT","INTEGER","BIGINT"}
            if not (numeric and (target_scale is None or target_scale>=kind[1]) or integer and kind[1]==0):
                deny("排名金额/计数不能通过整数、浮点或低精度CAST丢失真实精度。")

    proven_rank_where=set()
    def no_row_filters(scope,*,allow_group=False):
        query=scope.expression
        if (query.args.get("where") and scope not in proven_rank_where or
                any(query.args.get(key) for key in ("having","qualify","distinct")) or
                query.args.get("group") and not allow_group):
            deny("分子或结果的透传层附加了WHERE/GROUP/HAVING等筛选。")
        offset=query.args.get("offset")
        if offset and not literal(offset.expression,0):
            deny("标量结果不能跳过实际行。")
        limit=query.args.get("limit")
        if limit and (not isinstance(limit.expression,exp.Literal) or not str(limit.expression.this).isdigit() or int(limit.expression.this)<1):
            deny("标量结果不能被LIMIT0或未知限制隐藏。")

    def safe_join_shape(scope):
        for join in scope.expression.args.get("joins") or []:
            on=join.args.get("on")
            if join.args.get("side") or str(join.args.get("kind") or "").upper() not in {"","INNER","CROSS"}:
                deny("辅助标量只能无过滤地连接，不能产生额外行或丢行。")
            if on is not None and not (isinstance(on,exp.Boolean) and on.this is True):
                deny("最终标量连接不能引入额外ON条件。")

    def scalar_scope(scope,seen=None):
        seen=set() if seen is None else set(seen)
        if id(scope) in seen or not isinstance(scope.expression,exp.Select):
            return False
        seen.add(id(scope));query=scope.expression
        if any(query.args.get(key) for key in ("group","having","qualify","distinct","offset")):
            return False
        limit=query.args.get("limit")
        if limit and (not isinstance(limit.expression,exp.Literal) or not str(limit.expression.this).isdigit() or int(limit.expression.this)<1):
            return False
        if any(isinstance(node,exp.Window) for projection in query.selects for node in walk_in_scope(projection)):
            return False
        has_aggregate=any(isinstance(node,exp.AggFunc) for projection in query.selects for node in walk_in_scope(projection))
        if has_aggregate:
            def all_grouped(node):
                if isinstance(node,(exp.AggFunc,exp.Subquery)):
                    return True
                if isinstance(node,exp.Column):
                    return False
                return all(all_grouped(child) for child in node.iter_expressions())
            return all(all_grouped(projection) for projection in query.selects)
        if query.args.get("where"):
            return False
        for _,source in scope.selected_sources.values():
            if isinstance(source,exp.Table) or not scalar_scope(source,seen):
                return False
        try:
            safe_join_shape(scope)
        except SQLValidationError:
            return False
        return True

    safe_join_shape(root)
    divisions=[]
    for projected in root.expression.selects:
        actual,owner,path=trace(projected,root)
        if isinstance(actual,exp.Mul):
            if literal(actual.left,100):actual=unwrap(actual.right)
            elif literal(actual.right,100):actual=unwrap(actual.left)
        if isinstance(actual,exp.Div):
            divisions.append((actual,owner,path))
    if not divisions:
        deny("当前任务是比例，最终必须保留真实分子除以分母，不能只返回合计。")
    division,division_owner,ratio_path=divisions[0]
    numerator=unwrap(division.left)
    if isinstance(numerator,exp.Mul):
        if literal(numerator.left,100):numerator=unwrap(numerator.right)
        elif literal(numerator.right,100):numerator=unwrap(numerator.left)
        else:deny("分子不能增加非百分比缩放。")
    summed,sum_owner,sum_path=trace(numerator,division_owner)
    summed_value=unwrap(summed.this) if isinstance(summed,exp.Sum) else None
    rank_case_condition=None
    if isinstance(summed_value,exp.Case):
        branches=summed_value.args.get("ifs") or []
        otherwise=summed_value.args.get("default")
        # Missing/NULL ELSE is the exact selected-row SUM semantics: unselected
        # rows contribute NULL and are ignored. It is not rewritten to zero.
        if (summed_value.this is not None or len(branches)!=1 or
                not (otherwise is None or isinstance(unwrap(otherwise),exp.Null) or literal(otherwise,0))):
            deny("窗口TopN分子只支持单分支searched CASE，未选行须为NULL或0，不能增加金额。")
        rank_case_condition=branches[0].this
        summed_value=unwrap(branches[0].args.get("true"))
    if not isinstance(summed,exp.Sum) or not isinstance(summed_value,exp.Column):
        deny("分子必须实际SUM已排名的同一指标列，不能使用常量或仅列排名。")
    column=summed_value
    ranked=sum_owner.sources.get(column.table)
    if ranked is None or isinstance(ranked,exp.Table):
        deny("分子没有消费真实TopN子查询。")
    # Every other source is an independent exactly-one-row scalar, rather than
    # a second list which would duplicate the ranked values before the SUM.
    for alias,(_,source) in sum_owner.selected_sources.items():
        if alias==column.table:
            continue
        if isinstance(source,exp.Table) or not scalar_scope(source):
            deny("分子SUM连接了额外多行来源，可能重复TopN金额。")
    safe_join_shape(sum_owner)
    for scope in [root,division_owner]+ratio_path+sum_path:
        if scope is sum_owner:
            continue
        if not scalar_scope(scope):
            deny("最终比例的CTE/辅助连接未证明恰好一行，不能放大或隐藏结果。")
    ranking=ranked.expression
    if not isinstance(ranking,exp.Select):deny("TopN必须是受支持SELECT。")
    limit=ranking.args.get("limit");offset=ranking.args.get("offset")
    wanted=analysis.top_n
    if not isinstance(wanted,int) or isinstance(wanted,bool) or wanted<1:
        deny("实际TopN缺少已确认正整数。")
    window_proof=None
    if limit is not None:
        if rank_case_condition is not None:deny("不能用未证明的CASE进一步缩小已有LIMIT排名子集。")
        if (not isinstance(limit.expression,exp.Literal) or not literal(limit.expression,wanted)
                or offset and not literal(offset.expression,0)):
            deny(f"实际被合计的排名子查询必须取前{wanted}项，不能用无关LIMIT或非零OFFSET。")
        ordered=ranking.args.get("order")
    else:
        # Only this very SUM's mandatory rank predicate can establish TopN.
        # A spare window, an outer LIMIT or a rank with other qualifications
        # never licenses arbitrary WHERE conditions on the numerator.
        if analysis.rank_object!="month":deny("窗口TopN当前只证明真实月份排名。")
        predicate=rank_case_condition
        if predicate is not None and sum_owner.expression.args.get("where") is not None:
            deny("CASE窗口TopN不能同时附加未证明的WHERE筛选。")
        if predicate is None:
            predicate=sum_owner.expression.args.get("where")
            predicate=predicate.this if predicate is not None else None
        while isinstance(predicate,exp.Paren):predicate=predicate.this
        if (not isinstance(predicate,exp.LTE) or not isinstance(predicate.left,exp.Column)
                or predicate.left.table!=column.table or not isinstance(predicate.right,exp.Literal)
                or not literal(predicate.right,wanted)):
            deny("窗口TopN必须由实际SUM行集上唯一的排名列<=N筛选建立，不能附带额外条件。")
        projected=next((item for item in ranking.selects if item.alias_or_name==predicate.left.name),None)
        while isinstance(projected,(exp.Alias,exp.Paren)):projected=projected.this
        if (not isinstance(projected,exp.Window) or not isinstance(projected.this,exp.RowNumber)
                or projected.args.get("partition_by") or offset is not None):
            deny("实际排名列必须是无分区、未变换的ROW_NUMBER，不能换RANK、分区或其它值。")
        if any(isinstance(node,exp.Window) for node in walk_in_scope(projected.this)):
            deny("排名函数不能嵌套其它窗口。")
        ordered=projected.args.get("order")
        if rank_case_condition is None:proven_rank_where.add(sum_owner)
        window_proof={"rank_column":predicate.left.name,"predicate":"<=","top_n":wanted,"partitioned":False}
    for scope in [root,sum_owner]+ratio_path+sum_path:
        no_row_filters(scope)
    if not ordered or not ordered.expressions or not ordered.expressions[0].args.get("desc"):
        deny("实际TopN必须按合计指标降序。")
    selected=next((item for item in ranking.selects if item.alias_or_name==column.name),None)
    if selected is None:deny("被合计的列不在TopN真实投影里。")
    order_value=unwrap(ordered.expressions[0].this)
    if isinstance(order_value,exp.Literal) and not order_value.is_string and str(order_value.this).isdigit():
        position=int(order_value.this)-1
        if not 0<=position<len(ranking.selects):deny("排名排序位置不存在。")
        order_value=ranking.selects[position]
    elif isinstance(order_value,exp.Column) and not order_value.table:
        order_value=next((item for item in ranking.selects if item.alias_or_name==order_value.name),order_value)
    actual_metric,metric_owner,metric_path=trace(selected,ranked)
    actual_order,order_owner,_=trace(order_value,ranked)
    if actual_metric.sql(dialect="postgres")!=actual_order.sql(dialect="postgres") or metric_owner is not order_owner:
        deny("TopN主排序必须是最终被合计的同一指标谱系。")
    if not _measure_matches(actual_metric,metric_owner,analysis.metric,catalog):
        deny("排名指标没有追溯到当前确认的真实金额/数量字段。")
    if window_proof is not None:
        def conjunction(node):
            if node is None:return []
            if isinstance(node,(exp.Where,exp.Paren)):return conjunction(node.this)
            if isinstance(node,exp.And):return conjunction(node.left)+conjunction(node.right)
            if isinstance(node,exp.Or):deny("窗口排名不能由额外OR条件改变实际统计集合。")
            return [node]
        source_query=metric_owner.expression
        if any(source_query.args.get(key) for key in ("having","qualify","distinct","limit","offset")):
            deny("真实月份汇总不能先经HAVING/LIMIT等额外删减。")
        current=(analysis.time_scope or {}).get("current") or {}
        approved=[]
        for item in analysis.filters or []:
            if item.get("binding_scope") not in {None,"global","numerator"}:continue
            field=item.get("column") or item.get("field")
            operator=str(item.get("operator") or "=").upper()
            values=item.get("value");values=values if isinstance(values,list) else [values]
            approved.append((field,operator,frozenset(str(value) for value in values)))
        for atom in conjunction(source_query.args.get("where")):
            if (isinstance(atom,(exp.GTE,exp.LT)) and _physical_field(atom.left,metric_owner)=="invoice.invoice_date"
                    and _midnight_date(atom.right)==current.get("start" if isinstance(atom,exp.GTE) else "end")):
                continue
            candidate=None
            if isinstance(atom,exp.In) and atom.expressions and all(isinstance(item,exp.Literal) for item in atom.expressions):
                candidate=(_physical_field(atom.this,metric_owner),"IN",frozenset(str(item.this) for item in atom.expressions))
            elif isinstance(atom,(exp.EQ,exp.GT,exp.GTE,exp.LT,exp.LTE)) and isinstance(atom.right,exp.Literal):
                candidate=(_physical_field(atom.left,metric_owner),{"eq":"=","gt":">","gte":">=","lt":"<","lte":"<="}[atom.key],frozenset({str(atom.right.this)}))
            if candidate not in approved:
                deny("窗口原始月份金额含未经当前合同确认的额外WHERE筛选。")
        # To-one primary-key matching is necessary but does not establish the
        # correct FK or prevent a nullable INNER JOIN from dropping invoices.
        for join in source_query.args.get("joins") or []:
            for atom in conjunction(join.args.get("on")):
                if not isinstance(atom,exp.EQ) or not isinstance(atom.left,exp.Column) or not isinstance(atom.right,exp.Column):
                    deny("窗口月份金额的JOIN只能使用真实外键，不能混入附加过滤。")
                left,right=metric_owner.sources.get(atom.left.table),metric_owner.sources.get(atom.right.table)
                if not isinstance(left,exp.Table) or not isinstance(right,exp.Table):
                    deny("窗口原始金额暂不证明派生物理关联。")
                pair=frozenset(((left.name,atom.left.name),(right.name,atom.right.name)))
                matches=[]
                for physical in catalog.tables:
                    for foreign in physical.foreign_keys:
                        reference=foreign["references"]
                        if len(foreign["columns"])==1 and pair==frozenset(((physical.name,foreign["columns"][0]),(reference["table"],reference["columns"][0]))):
                            matches.append(not next(c for c in physical.columns if c.name==foreign["columns"][0]).nullable)
                if not matches or not any(matches) and str(join.args.get("side") or "").upper()!="LEFT":
                    deny("窗口金额关联缺少非空真实外键的无损证明。")
        group=metric_owner.expression.args.get("group")
        keys={node.sql(dialect="postgres") for node in group.expressions} if group else set()
        for secondary in ordered.expressions[1:]:
            actual,owner,_=trace(secondary.this,ranked)
            if owner is not metric_owner or actual.sql(dialect="postgres") not in keys:
                deny("窗口并列排序键必须来自同一真实月份分组，不能借无关列改变排名。")
    if analysis.metric=="invoice_revenue" and not _invoice_grain_is_preserved(metric_owner,catalog):
        deny("月度发票总额的来源不能重复每张发票，明细扇出会改变排名与合计。")
    for scope in metric_path:
        if scope is not metric_owner:
            no_row_filters(scope)
            if scope.expression.args.get("limit") or len(scope.selected_sources)!=1:
                deny("排名前的指标透传层不能额外截断或连接多行列表。")
    if ranked is not metric_owner:
        no_row_filters(ranked)
        if len(ranked.selected_sources)!=1:
            deny("TopN层不能连接额外多行来源后重复同一个排名对象。")
    if ranking.args.get("where") and ranked is not metric_owner:
        deny("月度排名层附加了未证明的子集筛选。")
    if analysis.rank_object=="month":
        group=metric_owner.expression.args.get("group")
        group_nodes=list(group.expressions) if group else []
        def month_grain(node):
            node=unwrap(node)
            return isinstance(node,exp.TimestampTrunc) and str(node.unit.name).upper()=="MONTH" and _physical_field(node.this,metric_owner)=="invoice.invoice_date"
        if len(group_nodes)!=1 or not month_grain(group_nodes[0]):
            deny("要求按月排名，真实指标聚合必须是发票日期的月份粒度，不能按发票或其它对象替代。")
    current=(analysis.time_scope or {}).get("current") or {}
    if current.get("start") and current.get("end"):
        dates={(atom.key,_midnight_date(atom.right)) for atom in _mandatory_atoms(metric_owner.expression.args.get("where")).values()
               if isinstance(atom,(exp.GTE,exp.LT)) and _physical_field(atom.left,metric_owner)=="invoice.invoice_date"}
        if not {("gte",current["start"]),("lt",current["end"])}<=dates:
            deny("TopN原始金额未保留当前确认期间。")
    denominator=unwrap(division.right)
    if isinstance(denominator,exp.Nullif):
        if not literal(denominator.expression,0):deny("分母除零保护常量必须为0。")
        denominator=denominator.this
    actual_denominator,denominator_owner,denominator_path=trace(denominator,division_owner)
    if not isinstance(actual_denominator,exp.AggFunc) or not scalar_scope(denominator_owner):
        deny("分母必须来自独立的一行真实聚合，不能是常量或多行名单。")
    denominator_mode='independent_scalar_aggregate'
    if denominator_owner is sum_owner:
        # A CASE predicate masks ONLY the numerator. The physical row stream
        # still contains every month; an unconditional SUM of the exact same
        # proved monthly amount is the full-period denominator. Do not confuse
        # this with WHERE rn<=N, which really removes denominator rows.
        denominator_value=unwrap(actual_denominator.this)
        if (rank_case_condition is None or window_proof is None or
                not isinstance(actual_denominator,exp.Sum) or
                not isinstance(denominator_value,exp.Column) or
                denominator_value.table!=column.table or denominator_value.name!=column.name or
                sum_owner.expression.args.get('where') is not None or ranking.args.get('limit') is not None):
            deny('同层分母必须无条件SUM同一完整月份金额流；不能复用WHERE或CASE筛选后的TopN子集。')
        invoice_total=next((item for item in catalog.get_table('invoice').columns if item.name=='total'),None)
        exact_amount=(invoice_total is not None and not invoice_total.nullable and
                      re.fullmatch(r'(?:numeric|decimal)\(\s*\d+\s*,\s*\d+\s*\)',str(invoice_total.data_type),re.I))
        contracts=analysis.query_scope or {}
        operands=[contracts.get(role) or {} for role in ('numerator','denominator')]
        if (analysis.metric!='invoice_revenue' or not exact_amount or
                any(not isinstance(item,dict) or item.get('metric') not in {None,'invoice_revenue'} or
                    item.get('filters') or (item.get('period') and any(item['period'].get(key)!=current.get(key) for key in ('start','end'))) for item in operands) or
                any(item.get('binding_scope') not in {None,'global'} for item in analysis.filters or [])):
            deny('同一完整月份流只证明无损、非空精确发票金额和同期间全局范围；有独立操作数条件时须使用各自实际单行聚合。')
        denominator_mode='unfiltered_all_months_sum'
    elif denominator_owner is ranked:
        deny("整体分母不能复用分子TopN子集。")
    for scope in denominator_path:
        if scope is not denominator_owner:
            no_row_filters(scope)
    for alternative,owner,_ in divisions[1:]:
        left=unwrap(alternative.left)
        if isinstance(left,exp.Mul):
            if literal(left.left,100):left=unwrap(left.right)
            elif literal(left.right,100):left=unwrap(left.left)
            else:deny("辅助比例不能引入其它缩放。")
        right=unwrap(alternative.right)
        if isinstance(right,exp.Nullif):
            if not literal(right.expression,0):deny("辅助比例分母保护必须为0。")
            right=right.this
        left,left_owner,_=trace(left,owner)
        right,right_owner,_=trace(right,owner)
        if (left_owner is not sum_owner or right_owner is not denominator_owner or
                left.sql(dialect="postgres")!=summed.sql(dialect="postgres") or
                right.sql(dialect="postgres")!=actual_denominator.sql(dialect="postgres")):
            deny("额外比例列不能换用另一分子或分母。")
    # Extra visible columns may repeat the actual numerator/denominator values,
    # not introduce another detail rowset or an invented helper constant.
    allowed={(id(sum_owner),summed.sql(dialect="postgres")),
             (id(denominator_owner),actual_denominator.sql(dialect="postgres"))}
    ratio_keys={(id(owner),node.sql(dialect="postgres")) for node,owner,_ in divisions}
    for projected in root.expression.selects:
        value,owner,_=trace(projected,root)
        if (id(owner),value.sql(dialect="postgres")) in allowed:
            continue
        candidate=value
        if isinstance(candidate,exp.Mul):
            if literal(candidate.left,100):candidate=unwrap(candidate.right)
            elif literal(candidate.right,100):candidate=unwrap(candidate.left)
        if (id(owner),candidate.sql(dialect="postgres")) not in ratio_keys:
            deny("辅助显示列必须来自实际分子/分母，不能增加其它度量或常量。")
    return {"verified":True,"mode":"consumed_ratio_numerator_ranked_sum",
            "top_n":wanted,"rank_object":analysis.rank_object,"metric":analysis.metric,
            "independent_denominator_single_row":denominator_mode=='independent_scalar_aggregate',
            "denominator_mode":denominator_mode,"extra_helper_columns_same_origin":True,
            "window_topn":window_proof}
