"""Check business scope independently of SQL executability and result equality.

The checks consume user wording/current structured intent and the authentic
catalog only. They never inspect evaluation IDs, expected SQL, or gold rows.
This is a deliberately narrow proof, not a claim to understand arbitrary SQL.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope, walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError

CUSTOMER_WINNER_PROVEN_METRICS=frozenset({'invoice_revenue','invoice_count'})


def _mandatory_atoms(node):
    """Atoms that hold in every boolean branch, without treating OR as AND."""
    if node is None:
        return {}
    if isinstance(node, (exp.Where, exp.Having, exp.Paren)):
        return _mandatory_atoms(node.this)
    if isinstance(node, exp.And):
        return {**_mandatory_atoms(node.left), **_mandatory_atoms(node.right)}
    if isinstance(node, exp.Or):
        left, right = _mandatory_atoms(node.left), _mandatory_atoms(node.right)
        return {key: left[key] for key in left.keys() & right.keys()}
    return {node.sql(dialect="postgres"): node}


def _midnight_date(node):
    target = None
    if isinstance(node, exp.Cast):
        target = node.args["to"].this
        if target not in {exp.DataType.Type.DATE, exp.DataType.Type.TIMESTAMP}:
            return None
        node = node.this
    if not isinstance(node, exp.Literal) or not node.is_string:
        return None
    try:
        text = str(node.this).strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return date.fromisoformat(text).isoformat()
        value = datetime.fromisoformat(text)
        # TIMESTAMP WITHOUT TIME ZONE boundaries are equivalent only at exact
        # midnight. Do not truncate nonzero seconds or assume a server timezone.
        if value.tzinfo is not None or value.time() != time(0):
            return None
        return value.date().isoformat()
    except (ValueError, TypeError):
        return None


def _active_scopes(scopes):
    active, pending = set(), [scope for scope in scopes if scope.parent is None]
    while pending:
        scope = pending.pop()
        if scope in active:
            continue
        active.add(scope)
        pending.extend(source for _,source in scope.selected_sources.values() if not isinstance(source,exp.Table))
        pending.extend(scope.subquery_scopes)
        pending.extend(scope.set_operation_scopes)
    return active


def _intent_value(intent, name, default=None):
    return intent.get(name, default) if isinstance(intent, dict) else getattr(intent, name, default)


def _resolve_projection(node, scope, depth=0):
    if depth > 12:
        raise SQLValidationError("派生字段谱系超过有界深度，无法证明当前业务指标。")
    while isinstance(node, (exp.Alias, exp.Paren, exp.Cast)):
        node = node.this
    if isinstance(node, exp.Column):
        source = scope.sources.get(node.table)
        if source is not None and not isinstance(source, exp.Table):
            projection = next((item for item in source.expression.selects if item.alias_or_name == node.name), None)
            if projection is None:
                raise SQLValidationError("派生字段没有可追溯的真实投影。")
            return _resolve_projection(projection, source, depth + 1)
    return node, scope


def _physical_field(node, scope):
    node, scope = _resolve_projection(node, scope)
    if not isinstance(node, exp.Column):
        return None
    source = scope.sources.get(node.table)
    if not isinstance(source, exp.Table):
        return None
    return (source.name + "." + node.name) if (source.db or "public") == "public" else source.db + "." + source.name + "." + node.name


def _measure_matches(node, scope, metric, catalog=None):
    node, scope = _resolve_projection(node, scope)
    if isinstance(node,exp.Round):
        # ROUND(SUM(numeric(...,2)),2) cannot change a ranking; rounding to
        # whole currency units can. Prove the declared scale, not a sample's
        # coincident value. Unknown/floating types remain unsupported.
        decimals=node.args.get("decimals")
        if catalog is None or not isinstance(decimals,exp.Literal) or decimals.is_string or not str(decimals.this).isdigit():
            return False
        inner,owner=_resolve_projection(node.this,scope)
        target=inner.this if isinstance(inner,exp.Sum) else None
        field=_physical_field(target,owner) if target is not None else None
        if not field or len(field.split("."))!=2:
            return False
        table,column=field.split(".")
        physical=next((item for item in catalog.get_table(table).columns if item.name==column),None)
        declared=re.fullmatch(r"(?:numeric|decimal)\(\s*\d+\s*,\s*(\d+)\s*\)",physical.data_type,re.I) if physical else None
        if declared is None or int(decimals.this)<int(declared[1]):
            return False
        node,scope=inner,owner
    if metric in {"invoice_revenue", "sales_revenue"}:
        return isinstance(node, exp.Sum) and _physical_field(node.this, scope) == "invoice.total"
    if metric in {"purchased_quantity", "purchase_quantity"}:
        return isinstance(node, exp.Sum) and _physical_field(node.this, scope) == "invoice_line.quantity"
    if metric == "detail_revenue":
        return isinstance(node, exp.Sum) and isinstance(node.this, exp.Mul) and {
            _physical_field(node.this.left,scope),_physical_field(node.this.right,scope)} == {"invoice_line.unit_price","invoice_line.quantity"}
    if metric == "customer_count":
        return isinstance(node, exp.Count) and _physical_field(node.this, scope) == "customer.customer_id"
    return False


def _invoice_grain_is_preserved(scope, catalog):
    """Every joined source is to-one from one authentic invoice alias."""
    sources={alias:source for alias,(_,source) in scope.selected_sources.items()}
    invoice_aliases={alias for alias,source in sources.items() if isinstance(source,exp.Table) and source.name=="invoice"}
    if len(invoice_aliases)!=1 or any(not isinstance(source,exp.Table) for source in sources.values()):
        return False
    equalities=[atom for join in scope.expression.args.get("joins") or []
                for atom in _mandatory_atoms(join.args.get("on")).values()
                if isinstance(atom,exp.EQ) and isinstance(atom.left,exp.Column) and isinstance(atom.right,exp.Column)]
    seen=set(invoice_aliases)
    while True:
        before=set(seen)
        for alias,source in sources.items():
            if alias in seen:
                continue
            primary=set(catalog.get_table(source.name,source.db or "public").primary_key)
            joined={column.name for atom in equalities for column,other in
                    ((atom.left,atom.right),(atom.right,atom.left)) if column.table==alias and other.table in seen}
            if primary and primary<=joined:
                seen.add(alias)
        if seen==before:
            return seen==set(sources)


def _denominator_metric(intent):
    """Only a current explicit operand contract creates this obligation."""
    scope=_intent_value(intent,"query_scope",{}) or {}
    denominator=scope.get("denominator") or {}
    if isinstance(denominator,dict):
        metric=denominator.get("metric")
        if metric:
            return metric
        if denominator.get("field") in {"invoice.total","invoice_line.unit_price*invoice_line.quantity"}:
            return "invoice_revenue" if denominator["field"]=="invoice.total" else "detail_revenue"
    wording=[str(_intent_value(intent,"denominator","") or "")]
    wording.extend(str(item) for item in _intent_value(intent,"output_requirements",[]) or []
                   if re.search(r"分母|denominator",str(item),re.I))
    if any(re.search(r"发票(?:金额|总额)|invoice\.total",text,re.I) for text in wording):
        return "invoice_revenue"
    return None


def _validate_ratio_denominator(tree, catalog, intent):
    """Trace the projected division's actual right operand, not any spare SUM."""
    required=_denominator_metric(intent)
    if required!="invoice_revenue":
        return {"verified":True,"mode":"no_explicit_invoice_denominator"}
    query=_intent_value(intent,'query_scope',{}) or {}
    if (_intent_value(intent,'task_type')=='ratio' and
            _intent_value(intent,'rank_object') is None and _intent_value(intent,'top_n') is None and
            _intent_value(intent,'metric') in {None,'invoice_revenue'} and
            all(isinstance(query.get(role),dict) and query[role].get('metric')=='invoice_revenue'
                for role in ('numerator','denominator'))):
        # Full physical operand proof also supports a real filtered/CASE
        # denominator. A spare SUM or a mode claim alone cannot authorize it.
        from qa_agent.sql.ratio_scope_guard import validate_typed_ratio_scope
        proof=validate_typed_ratio_scope(tree.sql(dialect='postgres'),catalog,intent)
        if proof.get('mode')!='typed_physical_ratio_operands' or not proof.get('proofs') or any(
                item.get('denominator',{}).get('metric')!='invoice_revenue' for item in proof['proofs']):
            raise SQLValidationError('完整发票比例合同未取得实际分母操作数的物理范围证明。')
        return {'verified':True,'mode':'actual_typed_invoice_operand_scopes','proofs':proof['proofs'],
            'output_rounding':proof['output_rounding']}
    if (_intent_value(intent,'rank_object')=='month' and
            'ranked_subset_total' in (_intent_value(intent,'output_requirements',[]) or [])):
        # An exhaustive exact-numeric monthly partition can be summed back
        # to the full invoice amount. Reuse its complete consumed-row proof,
        # rather than demanding an unrelated second invoice scan.
        from qa_agent.sql.ranked_subset_guard import validate_ranked_ratio_contract
        from types import SimpleNamespace
        analysis=SimpleNamespace(**intent) if isinstance(intent,dict) else intent
        proof=validate_ranked_ratio_contract(tree.sql(dialect='postgres'),catalog,analysis)
        if proof.get('denominator_mode')=='unfiltered_all_months_sum':
            return {'verified':True,'mode':'actual_full_invoice_month_partition_sum',
                'proofs':[{'metric':'invoice_revenue','lineage':'SUM(all unfiltered monthly SUM(invoice.total))',
                    'invoice_grain_preserved':True,'consumed_month_proof':proof}]}
    scopes=list(traverse_scope(tree))
    root=next(scope for scope in scopes if scope.parent is None)
    by_expression={id(scope.expression):scope for scope in scopes}
    divisions=[]
    def resolved(node,owner):
        node,owner=_resolve_projection(node,owner)
        if isinstance(node,exp.Subquery):
            inner=by_expression.get(id(node.this))
            if inner is None or len(node.this.selects)!=1:
                raise SQLValidationError("比例分母子查询没有唯一可追溯的投影。")
            return resolved(node.this.selects[0],inner)
        return node,owner
    for projection in root.expression.selects:
        value,owner=resolved(projection,root)
        for candidate in walk_in_scope(value):
            if isinstance(candidate,exp.Div):
                divisions.append((candidate,owner))
    if not divisions:
        raise SQLValidationError("当前要求比例及发票金额分母，实际输出缺少可证明的除法表达式。")
    proofs=[]
    for division,owner in divisions:
        value,amount_scope=resolved(division.right,owner)
        if isinstance(value,exp.Nullif):
            if not isinstance(value.expression,exp.Literal) or str(value.expression.this) not in {"0","0.0"}:
                raise SQLValidationError("分母除零保护只能NULLIF(真实金额,0)。")
            value,amount_scope=resolved(value.this,amount_scope)
        if not isinstance(value,exp.Sum) or _physical_field(value.this,amount_scope)!="invoice.total":
            raise SQLValidationError("已确认分母是发票金额，实际除法分母必须追溯到SUM(invoice.total)，不能以明细金额或同值结果替代。")
        if not _invoice_grain_is_preserved(amount_scope,catalog):
            raise SQLValidationError("发票金额分母的关联会重复发票或无法证明一张发票一行，不能连接明细后SUM(total)。")
        scope_contract=_intent_value(intent,"query_scope",{}) or {}
        denominator_contract=scope_contract.get("denominator") or {}
        denominator_contract=denominator_contract if isinstance(denominator_contract,dict) else {}
        time_contract=_intent_value(intent,"time_scope",{}) or {}
        default_period=time_contract.get("base" if _intent_value(intent,"task_type") in {"growth","yoy"} else "current") or {}
        current=denominator_contract.get("period") or default_period
        if current.get("start") and current.get("end"):
            boundaries=set()
            for atom in _mandatory_atoms(amount_scope.expression.args.get("where")).values():
                if isinstance(atom,(exp.GTE,exp.LT)) and _physical_field(atom.left,amount_scope)=="invoice.invoice_date":
                    boundaries.add((atom.key,_midnight_date(atom.right)))
            if not {("gte",current["start"]),("lt",current["end"])}<=boundaries:
                raise SQLValidationError("发票金额分母未保留当前合同的完整同期期间。")
        for binding in denominator_contract.get("filters",[]) or []:
            field=binding.get("column") or binding.get("field")
            wanted=binding.get("value")
            operator=str(binding.get("operator") or "=").upper()
            if not field or operator not in {"=","IN"}:
                raise SQLValidationError("当前分母筛选尚无受支持的结构证明，不能默许丢弃条件。")
            expected={str(value) for value in (wanted if isinstance(wanted,list) else [wanted])}
            matched=False
            for atom in _mandatory_atoms(amount_scope.expression.args.get("where")).values():
                if isinstance(atom,exp.EQ):
                    for column,literal in ((atom.left,atom.right),(atom.right,atom.left)):
                        if _physical_field(column,amount_scope)==field and isinstance(literal,exp.Literal) and {str(literal.this)}==expected:
                            matched=True
                elif isinstance(atom,exp.In) and _physical_field(atom.this,amount_scope)==field:
                    if all(isinstance(item,exp.Literal) for item in atom.expressions) and {str(item.this) for item in atom.expressions}==expected:
                        matched=True
            if not matched:
                raise SQLValidationError("实际发票金额分母没有保留当前合同已确认的分母筛选范围。")
        proofs.append({"metric":"invoice_revenue","lineage":"SUM(invoice.total)","invoice_grain_preserved":True})
    return {"verified":True,"mode":"actual_divisor_physical_invoice_sum","proofs":proofs}


def validate_groupwise_ranking(sql: str, catalog, analysis) -> dict:
    """Prove the current per-group Top-N with physical partition/measure lineage.

    Unsupported MAX/NOT EXISTS forms are explicitly rejected for equivalent
    ROW_NUMBER repair; they are never assumed correct from an empty result.
    """
    query_scope = _intent_value(analysis, "query_scope", {}) or {}
    if query_scope.get("ranking_scope") != "per_group":
        return {"verified": True, "mode": "not_groupwise"}
    wanted = list(query_scope.get("partition_by") or [])
    limit = query_scope.get("per_group_limit")
    if not wanted or not isinstance(limit, int) or not 1 <= limit <= 200:
        raise SQLValidationError("每组排名缺少合法分组字段或每组数量，不能猜测。")
    metric = _intent_value(analysis, "metric")
    direction = (_intent_value(analysis,"order",{}) or {}).get("direction", "desc")
    tree = _qualified(sql, catalog)
    def transparent_node(node,owner,depth=0):
        if depth>12:return None,owner
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        if isinstance(node,exp.Column):
            source=owner.sources.get(node.table)
            if source is not None and not isinstance(source,exp.Table)and isinstance(source.expression,exp.Select):
                projection=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
                if projection is None:return None,owner
                return transparent_node(projection,source,depth+1)
        return node,owner
    def exact_sort_field(node, owner, depth=0):
        # A display proof cannot strip CAST/ROUND or turn a transformed key into
        # a claim that the original physical key was used for tie-breaking.
        if depth>12:return None
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        if not isinstance(node,exp.Column):return None
        source=owner.sources.get(node.table)
        if isinstance(source,exp.Table):
            return (source.name+'.'+node.name)if(source.db or'public')=='public'else source.db+'.'+source.name+'.'+node.name
        if source is None or not isinstance(source.expression,exp.Select):return None
        projection=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
        return exact_sort_field(projection,source,depth+1)if projection is not None else None
    def exact_measure_type(node,owner,depth=0):
        if depth>16:return None
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        if isinstance(node,exp.Column):
            source=owner.sources.get(node.table)
            if not isinstance(source,exp.Table):
                projection=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)if source is not None and isinstance(source.expression,exp.Select)else None
                return exact_measure_type(projection,source,depth+1)if projection is not None else None
            physical=next((c for t in catalog.tables if t.schema==(source.db or'public')and t.name==source.name for c in t.columns if c.name==node.name),None)
            kind=str(physical.data_type).casefold().strip()if physical else ''
            numeric=re.fullmatch(r'(?:numeric|decimal)\(\s*(\d+)\s*,\s*(\d+)\s*\)',kind)
            if numeric:return {'scale':int(numeric[2]),'integer_digits':int(numeric[1])-int(numeric[2]),'int64_safe':False,'native':'numeric'}
            if kind in {'smallint','integer','bigint'}:
                return {'scale':0,'integer_digits':{'smallint':5,'integer':10,'bigint':19}[kind],'int64_safe':True,'native':kind}
            return None
        if isinstance(node,exp.Count):return {'scale':0,'integer_digits':19,'int64_safe':True,'native':'bigint'}
        if isinstance(node,exp.Sum):
            inner=exact_measure_type(node.this,owner,depth+1)
            if inner is None:return None
            if inner['native']in{'smallint','integer'}:return {'scale':0,'integer_digits':19,'int64_safe':True,'native':'bigint'}
            return {'scale':inner['scale'],'integer_digits':None,'int64_safe':False,'native':'numeric'}
        if isinstance(node,exp.Mul):
            left=exact_measure_type(node.left,owner,depth+1);right=exact_measure_type(node.right,owner,depth+1)
            if not left or not right:return None
            digits=(left['integer_digits']+right['integer_digits']if left['integer_digits']is not None and right['integer_digits']is not None else None)
            return {'scale':left['scale']+right['scale'],'integer_digits':digits,'int64_safe':False,'native':'numeric'}
        if isinstance(node,exp.Round):
            inner=exact_measure_type(node.this,owner,depth+1);digits=node.args.get('decimals')
            if not inner or not isinstance(digits,exp.Literal)or digits.is_string or not str(digits.this).isdigit()or int(digits.this)<inner['scale']:return None
            return {**inner,'native':'numeric'}
        if isinstance(node,exp.Cast):
            inner=exact_measure_type(node.this,owner,depth+1);target=node.args.get('to')
            if not inner or not isinstance(target,exp.DataType):return None
            if target.this==exp.DataType.Type.BIGINT:
                return {**inner,'native':'bigint'}if inner['scale']==0 and inner['int64_safe']else None
            if target.this!=exp.DataType.Type.DECIMAL:return None
            parts=[item.sql(dialect='postgres')for item in target.expressions]
            if not parts:return {**inner,'native':'numeric'}
            if len(parts)not in{1,2}or any(not p.isdigit()for p in parts):return None
            precision=int(parts[0]);scale=int(parts[1])if len(parts)==2 else 0
            if inner['integer_digits']is None or scale<inner['scale']or precision-scale<inner['integer_digits']:return None
            return {**inner,'native':'numeric'}
        return None
    proofs = []
    for scope in _active_scopes(list(traverse_scope(tree))):
        for atom in _mandatory_atoms(scope.expression.args.get("where")).values():
            if not isinstance(atom, (exp.EQ, exp.LTE, exp.LT, exp.GTE, exp.GT)):
                continue
            column, bound, op = atom.left, atom.right, atom.key
            if isinstance(bound, exp.Column):
                column, bound = bound, column
                op={"eq":"eq","lte":"gte","lt":"gt","gte":"lte","gt":"lt"}[op]
            if not isinstance(column,exp.Column) or not isinstance(bound,exp.Literal) or bound.is_string:
                continue
            if (op,str(bound.this)) not in ({("eq","1"),("lte","1"),("lt","2")} if limit==1 else {("lte",str(limit)),("lt",str(limit+1))}):
                continue
            window, owner = transparent_node(column, scope)
            if not isinstance(window,exp.Window) or not isinstance(window.this,exp.RowNumber):
                continue
            actual = [exact_sort_field(part,owner) for part in window.args.get("partition_by") or []]
            if actual != wanted:
                raise SQLValidationError("每组排名的真实PARTITION BY字段与用户分组不一致，客户所在地不能换成账单国家。")
            order = window.args.get("order")
            if not order or not order.expressions or bool(order.expressions[0].args.get("desc")) != (direction=="desc"):
                raise SQLValidationError("每组排名的主排序方向不符合当前合同。")
            if exact_measure_type(order.expressions[0].this,owner)is None or not _measure_matches(order.expressions[0].this,owner,metric,catalog):
                raise SQLValidationError("每组排名未按当前真实业务度量排序，不能用ID或其它金额代替。")
            tie_breakers=[];complete=True
            for item in order.expressions[1:]:
                field=exact_sort_field(item.this,owner)
                if not field:complete=False;break
                tie_breakers.append({'field':field,'direction':'desc'if item.args.get('desc')else'asc',
                                     'nulls_first':bool(item.args.get('nulls_first'))})
            proofs.append({"partition_by":actual,"per_group_limit":limit,"metric":metric,"rank_function":"ROW_NUMBER",
                           "tie_breakers":tie_breakers if complete else [],"tie_breakers_verified":complete,
                           "order_source":"actual_consumed_ROW_NUMBER_window"})
    if not proofs:
        raise SQLValidationError("当前要求每组TopN，SQL缺少可证明的ROW_NUMBER分组与外层每组排名限制。全局Top不能替代；未证明的MAX/NOT EXISTS请修为等价ROW_NUMBER。")
    from hashlib import sha256
    return {"verified":True,"mode":"physical_partition_measure_and_rank_filter","proofs":proofs,
            "source":"program:proved_groupwise_window","sql_sha256":sha256(sql.encode('utf-8')).hexdigest()}


def _validate_average_customer(sql, catalog, intent=None):
    from qa_agent.sql.average_customer_scope_guard import validate_average_customer_scope
    return validate_average_customer_scope(sql, catalog, intent)


def query_semantic_constraints(question: str, catalog, *, intent=None) -> dict:
    """Describe only supported semantic obligations before SQL generation."""
    result = {}
    query_scope = _intent_value(intent, "query_scope", {}) or {}
    eligible_customer = (
        query_scope.get("aggregation_scope") == "all_invoices_for_qualified_customers"
        or (re.search(r"(?:买过|购买过|购过).{1,60}?客户(?:里|中|之中)", question)
            and re.search(r"(?:花钱|消费|总消费|总支出|全部消费)", question))
    )
    if (_intent_value(intent,'task_type')=='ratio' and _intent_value(intent,'rank_object')=='customer' and
            _intent_value(intent,'top_n')==1 and _intent_value(intent,'metric')=='invoice_revenue'):
        result['customer_inner_winner']={'rank_metric':query_scope.get('rank_metric') or 'invoice_revenue','amount_metric':'invoice_revenue',
            'instruction':'按当前已确认的每客户金额/发票张数选Top1；张数切换的并列规则须由本次用户明确选择。分子和全年分母仍SUM(invoice.total)。实际输出同一winner的customer_id、该客户发票金额、比例，不能只给比例。'}
    names = {table.name for table in catalog.tables}
    if eligible_customer and {"customer", "invoice"} <= names:
        result["customer_eligibility"] = {
            "qualification_grain": "customer.customer_id",
            "aggregation_scope": "all_invoices_for_qualified_customers",
            "instruction": "购买条件只决定客户资格集合；按题目期间汇总合格客户的全部发票，不能只汇总含该商品/流派的发票。资格子查询应关联客户键，不关联外层当前发票键。",
        }
    if re.search(r"客户负责人|负责客户的员工|客户支持负责人|销售支持员工", question) and {"customer", "employee"} <= names:
        result["customer_representative_role"] = {
            "role_source": "customer.support_rep_id -> employee.employee_id",
            "instruction": "用户对象是客户负责人，不是全部员工。按实际客户负责关系确定人员集合；若外连接保留零客户员工，需要题面明确要求或真实角色筛选依据。",
        }
    outputs = _intent_value(intent, "output_requirements", []) or []
    if outputs:
        result["output_requirements"] = outputs
    if query_scope.get("ranking_scope") == "per_group":
        result["groupwise_ranking"] = query_scope
    customer_country_scope=(_intent_value(intent,"region_scope")=="customer.country" or "customer.country" in query_scope.get("partition_by",[]))
    all_customer_invoices=query_scope.get("aggregation_scope")=="all_invoices_for_qualified_customers"
    customer_country_winners=(query_scope.get("ranking_scope")=="per_group" and
        query_scope.get("partition_by")==["customer.country"] and _intent_value(intent,"region_scope")=="customer.country" and
        _intent_value(intent,"metric") in {"invoice_revenue","sales_revenue"})
    if customer_country_scope and (all_customer_invoices or customer_country_winners):
        result["customer_country_eligibility_all_invoice_amount"] = True
    if _intent_value(intent,"metric") == "average_customer_amount":
        result["explicit_average_grain"] = {"grain":"customer", "expression":"SUM(invoice.total)/COUNT(DISTINCT invoice.customer_id)",
                                           "instruction":"这是用户显式指定按购买客户平均，不是每张发票AVG，不安装新默认。"}
    if query_scope.get('extrema_difference') is not None:
        result['monthly_extrema_difference'] = query_scope['extrema_difference']
    if _intent_value(intent,'metric') == 'repeat_customer_count' and not _intent_value(intent,'grouping'):
        result['global_repeat_customer_count'] = {'output_shape':'single_scalar_customer_count'}
    if _intent_value(intent,"task_type") in {"ratio","growth","yoy"} and _denominator_metric(intent)=="invoice_revenue":
        result["ratio_denominator"]={"metric":"invoice_revenue","expression":"SUM(invoice.total)",
            "instruction":"这是当前合同明确的分母度量；流派/曲目分子仍按明细金额。实际除法右项必须来自发票总额，不能用明细同值结果替代，保留分母期间与范围。"}
    # This phrase proves a location role, without assuming a specific unseen
    # value exists or silently replacing it with a familiar country/name.
    location = re.search(r"(?P<value>[A-Za-z][A-Za-z .'-]{1,50}?)\s*(?:那边|当地|地区|所在(?:的)?国家|国家).{0,8}?员工", question)
    if location and "employee" in names:
        result["explicit_employee_location"] = {
            "user_value": location.group("value").strip(),
            "role": "location",
            "instruction": "这是员工所在地条件，不是员工姓名；使用合同已确认的位置字段并保留原值。值不存在可返回无匹配，禁止换成姓名字段。",
        }
    return result


def validate_question_semantics(question: str, sql: str, catalog, *, intent=None) -> dict:
    """Reject proved field-role/scope errors before every read-only execution."""
    obligations = query_semantic_constraints(question, catalog, intent=intent)
    if not obligations:
        return {"verified": True, "checks": [], "mode": "no_narrow_obligation"}
    tree = _qualified(sql, catalog)
    scopes = list(traverse_scope(tree))
    checks = []
    if 'customer_inner_winner' in obligations:
        from qa_agent.sql.customer_winner_guard import validate_customer_winner_ratio
        checks.append(validate_customer_winner_ratio(sql,catalog,intent))
    if "ratio_denominator" in obligations:
        checks.append(_validate_ratio_denominator(tree,catalog,intent))
    if obligations.get("customer_country_eligibility_all_invoice_amount"):
        approved_invoice_filters = [item for item in _intent_value(intent,"filters",[]) or []
                                    if item.get("column")=="invoice.billing_country"]
        if not approved_invoice_filters:
            for scope in scopes:
                for wrapper in (scope.expression.args.get("where"),scope.expression.args.get("having")):
                    if wrapper is None:
                        continue
                    for column in walk_in_scope(wrapper):
                        if isinstance(column,exp.Column) and _physical_field(column,scope)=="invoice.billing_country":
                            raise SQLValidationError("当前国家用于客户资格/分组，消费范围是这些客户的全部发票；SQL额外按invoice.billing_country筛金额会缩窄统计范围，即使当前结果碰巧相同也不允许。")
        checks.append("customer_country_does_not_filter_invoice_billing_country")
    if "groupwise_ranking" in obligations:
        checks.append(validate_groupwise_ranking(sql,catalog,intent))
    if "explicit_average_grain" in obligations:
        checks.append(_validate_average_customer(sql,catalog,intent))
    if 'monthly_extrema_difference' in obligations:
        from qa_agent.sql.extrema_difference_guard import validate_monthly_extrema_difference
        checks.append(validate_monthly_extrema_difference(sql,catalog,intent))
    if 'global_repeat_customer_count' in obligations:
        from qa_agent.sql.repeat_count_guard import validate_repeat_customer_count_output
        checks.append(validate_repeat_customer_count_output(sql,catalog,intent,question=question))
    location = obligations.get("explicit_employee_location")
    if location:
        value = location["user_value"]
        for scope in scopes:
            sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
            where = scope.expression.args.get("where")
            if where is None:
                continue
            for predicate in walk_in_scope(where):
                if not isinstance(predicate, (exp.EQ, exp.NEQ, exp.In, exp.Like, exp.ILike)):
                    continue
                if not any(str(item.this).casefold() == value.casefold() for item in predicate.find_all(exp.Literal) if item.is_string):
                    continue
                for column in predicate.find_all(exp.Column):
                    source = sources.get(column.table)
                    if isinstance(source, exp.Table) and source.name == "employee" and column.name in {"first_name", "last_name", "name"}:
                        raise SQLValidationError("用户指定的是员工所在地，SQL 却把原值绑定到姓名字段；须保留已确认位置字段与原值，不能因空结果换过滤列。")
        checks.append("explicit_location_not_person_name")
    if "customer_eligibility" in obligations:
        for scope in scopes:
            sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
            invoice_aliases = {alias for alias, source in sources.items() if isinstance(source, exp.Table) and source.name == "invoice"}
            # Inspect only the amount aggregation's own SELECT scope; a
            # legitimate qualification subquery must remain independently free
            # to filter genre/track/invoice_line.
            amount_aggregates = [node for node in walk_in_scope(scope.expression)
                if isinstance(node, exp.Sum) and any(column.table in invoice_aliases and column.name == "total" for column in node.find_all(exp.Column))]
            if not amount_aggregates:
                continue
            restrictors = {"genre", "track", "invoice_line", "album", "artist", "playlist", "playlist_track"}
            direct_restrictors = {source.name for source in sources.values() if isinstance(source, exp.Table)} & restrictors
            if direct_restrictors:
                raise SQLValidationError("客户资格条件与金额统计范围混淆：购买对象只筛选客户集合，全部消费不能在相同金额聚合层连接并过滤购买明细。请改为客户键 EXISTS/IN 集合，再汇总这些客户的全部发票。")
            for inner in scopes:
                if inner is scope or not inner.is_subquery or inner.parent is not scope:
                    continue
                for external in inner.external_columns:
                    if external.table in invoice_aliases and external.name == "invoice_id":
                        raise SQLValidationError("客户资格被错误关联到当前发票 invoice_id，导致只累计包含指定商品/流派的发票。资格条件必须关联 customer_id，金额仍统计合格客户的全部发票并保留题目期间。")
        checks.append("customer_qualification_separated_from_amount_scope")
    if "customer_representative_role" in obligations:
        for scope in scopes:
            sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
            employee_aliases = {alias for alias, source in sources.items() if isinstance(source, exp.Table) and source.name == "employee"}
            customer_aliases = {alias for alias, source in sources.items() if isinstance(source, exp.Table) and source.name == "customer"}
            if not employee_aliases or not customer_aliases:
                continue
            optional_customer = any(join.this.alias_or_name in customer_aliases and str(join.args.get("side") or "").upper() == "LEFT"
                                    for join in scope.expression.args.get("joins") or [])
            if not optional_customer:
                continue
            explicit_zero = bool(re.search(r"包括.{0,8}(?:零|0|没有|未分配)|即使.{0,8}(?:零|0|没有)|所有员工|全部员工", question))
            def role_filter(node):
                if node is None:
                    return False
                if isinstance(node, (exp.Where, exp.Having, exp.Paren)):
                    return role_filter(node.this)
                if isinstance(node, exp.And):
                    return role_filter(node.left) or role_filter(node.right)
                if isinstance(node, exp.Or):
                    return role_filter(node.left) and role_filter(node.right)
                if isinstance(node, exp.Not) and isinstance(node.this, exp.Is) and isinstance(node.this.expression, exp.Null):
                    column = node.this.this
                    return isinstance(column, exp.Column) and column.table in customer_aliases and column.name == "customer_id"
                if isinstance(node, exp.Is) and node.args.get("negate") and isinstance(node.expression, exp.Null):
                    return isinstance(node.this, exp.Column) and node.this.table in customer_aliases and node.this.name == "customer_id"
                if isinstance(node, (exp.GT, exp.GTE)) and isinstance(node.left, exp.Count) and isinstance(node.right, exp.Literal):
                    counted = node.left.this
                    if isinstance(counted, exp.Distinct) and len(counted.expressions) == 1:
                        counted = counted.expressions[0]
                    return (isinstance(counted, exp.Column) and counted.table in customer_aliases and counted.name == "customer_id"
                            and (node.key, str(node.right.this)) in {("gt", "0"), ("gte", "1")})
                if isinstance(node, exp.EQ):
                    return any(isinstance(column, exp.Column) and column.table in employee_aliases and column.name == "title"
                               and isinstance(value, exp.Literal) and value.is_string for column, value in ((node.left,node.right),(node.right,node.left)))
                return False
            if not explicit_zero and not (role_filter(scope.expression.args.get("where")) or role_filter(scope.expression.args.get("having"))):
                raise SQLValidationError("用户查询客户负责人，当前 LEFT JOIN 却把没有任何负责客户的普通员工也纳入；应按真实 customer.support_rep_id 确定负责人集合，不能扩大成全部员工。")
        checks.append("customer_representative_role_not_all_employees")
    return {"verified": True, "checks": checks, "obligations": obligations,
            "mode": "qualified_ast_semantic_scope"}


def validate_document_dependencies(sql: str, catalog, dependencies: dict, *, question: str = "") -> dict:
    """Prove a supported retrieved definition actually governs the SQL AST.

    A descriptive artist passage imposes no aggregate. A metric rule needs both
    the actual dependency answer and its quoted source. Unrecognized rules are
    recorded as unverified, not silently certified as document-driven math.
    """
    tree = _qualified(sql, catalog)
    scopes = list(traverse_scope(tree))
    # Follow sources actually referenced by the root result, excluding a CTE
    # that merely exists in WITH but contributes nothing to the answer.
    active_scopes = _active_scopes(scopes)
    proofs, unverified = [], []
    for step_id, dependency in dependencies.items():
        if dependency.get("source") != "documents":
            continue
        answer = str(dependency.get("answer") or "")
        evidence = "\n".join(str(item.get("text") or "") for item in dependency.get("evidences", []))
        role = dependency.get("dependency_role")
        if role in {"schema_mapping", "facts", "session_context"}:
            continue
        if role is None:
            # Legacy dependency records have no role. Infer a computation only
            # from a real definition/formula/threshold, not the occurrence of
            # 'repeat customer' in a field-mapping or ordinary background fact.
            is_definition = bool(re.search(r"定义.{0,80}(?:除以|乘以|至少|COUNT|AVG|SUM|/|>=|≥)|(?:至少\s*[\d二两]+.{0,8}发票)|AVG\s*\(\s*invoice\.total", answer+"\n"+evidence,re.I))
            if not is_definition:
                continue
        if "复购" in answer:
            if not evidence or not re.search(r"(?:至少\s*[2二两]|[≥>]\s*=?\s*2|>=\s*2|2\s*张|两张)", evidence):
                raise SQLValidationError("复购定义依赖缺少支持至少两张发票的实际文档证据，不能仅凭模型回答绑定计算。")
            candidates = []
            derived_proofs = []
            derived_scopes = {}
            unused_definition = False
            unsafe_grain = False
            for scope in scopes:
                sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
                invoice_aliases = {alias for alias, source in sources.items() if isinstance(source, exp.Table) and source.name == "invoice"}
                if not invoice_aliases:
                    continue
                if (any(not isinstance(source, exp.Table) for source in sources.values())
                        or re.search(r"(?:各|每|按).{0,24}(?:销售|支持|负责|员工)",question)):
                    # The derived relation must actually participate in the
                    # qualifying GROUP/HAVING; a nearby/unconsumed CTE is not
                    # evidence. The finite proof preserves real PK/FK identity
                    # and rejects filters, fanout, transforms and set branches.
                    if scope not in active_scopes:
                        unused_definition = True
                        continue
                    if scope.expression.args.get("group") is None or scope.expression.args.get("having") is None:
                        continue
                    from qa_agent.sql.document_repeat_lineage import prove_derived_customer_qualification
                    derived_proof=prove_derived_customer_qualification(scope,catalog,question=question)
                    derived_proofs.append(derived_proof)
                    derived_scopes[scope]=derived_proof
                    candidates.append((scope, sources, invoice_aliases))
                    continue
                group = scope.expression.args.get("group")
                has_customer_group = group is not None and any(column.name == "customer_id" and
                    isinstance(sources.get(column.table), exp.Table) and sources[column.table].name in {"invoice", "customer"}
                    for column in group.find_all(exp.Column))
                if not has_customer_group:
                    continue
                if scope in active_scopes:
                    from qa_agent.sql.document_repeat_lineage import (prove_direct_customer_group_grain,
                                                                     prove_direct_global_customer_membership)
                    prove_direct_customer_group_grain(scope,catalog)
                    prove_direct_global_customer_membership(scope,catalog)
                having = scope.expression.args.get("having")
                if having is None:
                    continue
                for node in _mandatory_atoms(having).values():
                    if not isinstance(node, (exp.GTE, exp.GT, exp.LTE, exp.LT)):
                        continue
                    count, number, op = node.left, node.right, node.key
                    if isinstance(number, exp.Count):
                        count, number = number, count
                        op = {"lte": "gte", "lt": "gt", "gte": "lte", "gt": "lt"}[op]
                    if not isinstance(count, exp.Count) or not isinstance(number, exp.Literal) or number.is_string:
                        continue
                    if (op, str(number.this)) not in {("gte", "2"), ("gt", "1")}:
                        continue
                    counted = count.this
                    is_distinct = isinstance(counted, exp.Distinct)
                    if isinstance(counted, exp.Distinct) and len(counted.expressions) == 1:
                        counted = counted.expressions[0]
                    is_invoice_count = (isinstance(counted, exp.Star) or
                        isinstance(counted, exp.Column) and counted.table in invoice_aliases and counted.name == "invoice_id")
                    if is_invoice_count:
                        if scope not in active_scopes:
                            unused_definition = True
                            continue
                        # Detail-side joins can repeat each invoice. A normal
                        # COUNT(invoice_id) is not the number of invoices there.
                        # Allow only catalog-proven to-one joins, or DISTINCT
                        # invoice keys. Never infer cardinality from equal data.
                        to_one = len(invoice_aliases) == 1 and all(isinstance(source,exp.Table) for source in sources.values())
                        equalities=[]
                        for join in scope.expression.args.get("joins") or []:
                            on = join.args.get("on")
                            equalities.extend(atom for atom in _mandatory_atoms(on).values() if isinstance(atom,exp.EQ)
                                              and isinstance(atom.left,exp.Column) and isinstance(atom.right,exp.Column))
                        # Prove to-one reachability from the counted invoice,
                        # independent of the syntactic FROM/JOIN order.
                        seen=set(invoice_aliases)
                        while to_one:
                            before=set(seen)
                            for alias,source in sources.items():
                                if alias in seen:
                                    continue
                                primary=set(catalog.get_table(source.name,source.db or "public").primary_key)
                                keys={column.name for atom in equalities for column,other in
                                      ((atom.left,atom.right),(atom.right,atom.left))
                                      if column.table==alias and other.table in seen}
                                if primary and primary<=keys:
                                    seen.add(alias)
                            if seen==before:
                                break
                        to_one=to_one and seen==set(sources)
                        if not is_distinct and not to_one:
                            unsafe_grain = True
                            continue
                        candidates.append((scope, sources, invoice_aliases))
            if not candidates:
                if unsafe_grain:
                    raise SQLValidationError("复购须保持发票粒度；一对多明细关联会重复发票，应按 DISTINCT invoice_id 计数或先恢复每张发票一次，不能将明细行数当发票次数。")
                if unused_definition:
                    raise SQLValidationError("复购定义只出现在未被实际结果引用的 CTE 中，没有参与当前输出，不能把无关定义冒充文档驱动查询。")
                raise SQLValidationError("检索定义要求按客户在期间内至少两张发票，但 SQL 缺少客户粒度 GROUP BY 与 COUNT(invoice_id)>=2（或等价 >1）的资格计算；不能把普通客户数附上文档引用冒充复购。")
            year = re.search(r"(?<!\d)(20\d{2}|19\d{2})\s*年", question)
            if year:
                expected_start, expected_end = f"{year[1]}-01-01", f"{int(year[1])+1}-01-01"
                for scope, sources, invoice_aliases in candidates:
                    where = scope.expression.args.get("where")
                    atoms = _mandatory_atoms(where).values()
                    found = set()
                    for atom in atoms:
                        if not isinstance(atom, (exp.GTE, exp.LT, exp.LTE, exp.GT)):
                            continue
                        column, value, op = atom.left, atom.right, atom.key
                        if isinstance(atom.right, exp.Column):
                            column, value = atom.right, atom.left
                            op = {"gte":"lte","lt":"gt","lte":"gte","gt":"lt"}[op]
                        if not isinstance(column, exp.Column) or column.table not in invoice_aliases or column.name != "invoice_date":
                            continue
                        normalized = _midnight_date(value)
                        if normalized is not None:
                            found.add((op, normalized))
                    if not {("gte", expected_start), ("lt", expected_end)} <= found:
                        raise SQLValidationError("复购资格的发票计数未在用户指定年份内完成，不能用跨期间购买次数确定期间内复购。")
            from qa_agent.sql.repeat_count_guard import validate_repeat_customer_count_output
            output_proof=validate_repeat_customer_count_output(sql,catalog,question=question,
                qualified_scope_sqls={scope.expression.sql(dialect='postgres') for scope,_,_ in candidates})
            if derived_scopes and re.search(r"(?:各|每|按).{0,24}(?:销售|支持|负责|员工)",question):
                from qa_agent.sql.document_repeat_lineage import prove_grouped_repeat_output
                output_proof=prove_grouped_repeat_output(scopes,derived_scopes,catalog)
            proofs.append({"dependency": step_id, "metric": "repeat_customer_count",
                           "proof": "customer-grain invoice count >=2", "period_checked": bool(year),
                           "derived_customer_proofs": derived_proofs,
                           "output_proof":output_proof})
        elif "客单价" in answer or "平均每张发票" in answer:
            if not re.search(r"AVG\s*\(\s*invoice\.total\s*\)", evidence, re.I):
                raise SQLValidationError("客单价定义没有实际文档中的 AVG(invoice.total) 支持，不能猜测按客户或按发票平均。")
            if not any(isinstance(node, exp.Avg) and isinstance(node.this, exp.Column) and node.this.name == "total"
                       for node in tree.walk()):
                raise SQLValidationError("文档要求平均每张发票金额 AVG(invoice.total)，SQL 未采用该定义。")
            proofs.append({"dependency": step_id, "metric": "average_invoice_amount", "proof": "retrieved AVG expression"})
        elif re.search(r"定义|计算口径|计算公式", answer):
            unverified.append({"dependency": step_id, "reason": "当前没有覆盖此定义的程序化语义证明"})
    return {"verified": not unverified, "proofs": proofs, "not_verified": unverified}
