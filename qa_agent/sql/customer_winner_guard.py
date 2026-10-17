"""Prove invoice-count selection with invoice-amount ratio operands.

The inner selection metric never changes either monetary operand. Supported
forms are a per-customer amount/count CTE and an invoice SUM qualified by a
Top-1 customer key, using a scalar subquery/IN or an authenticated key join.
"""
from __future__ import annotations

from decimal import Decimal,InvalidOperation
from types import SimpleNamespace
import re

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope,walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _physical_field,_midnight_date,_invoice_grain_is_preserved,_active_scopes
from qa_agent.sql.validator import SQLValidationError


def validate_customer_winner_ratio(sql,catalog,analysis):
    if isinstance(analysis,dict):
        values={"task_type":None,"rank_object":None,"metric":None,"top_n":None,"time_scope":None,"filters":[],"query_scope":{}}
        values.update(analysis);analysis=SimpleNamespace(**values)
    if analysis.task_type!="ratio" or analysis.rank_object!="customer" or analysis.top_n!=1:
        return {"verified":True,"mode":"not_single_customer_winner_ratio"}
    def deny(text):raise SQLValidationError("客户内层排名比例未通过："+text)
    rank_metric=analysis.query_scope.get("rank_metric") or analysis.metric
    if rank_metric not in {"invoice_revenue","invoice_count"}:deny("当前内层排名指标尚未证明，不能暗换成金额或开放未验证选项。")
    if analysis.metric!="invoice_revenue" or analysis.top_n!=1:
        deny("该已证明切换只选择发票张数最多的1位客户，最终指标必须仍是发票金额。")
    for operand in ("numerator","denominator"):
        value=analysis.query_scope.get(operand) or {}
        if isinstance(value,dict) and value.get("metric") not in {None,"invoice_revenue"}:
            deny("内层选人规则不能覆盖分子或分母的金额合同。")
    tie=analysis.query_scope.get("rank_tie_breaker") or {}
    if rank_metric=="invoice_count" and tie!={"field":"customer.customer_id","direction":"asc","source":"explicit_user_choice"}:
        deny("发票张数可能并列，切换必须同时有用户明确选择的客户编号升序规则，不能暗装默认。")
    tree=_qualified(sql,catalog);scopes=list(traverse_scope(tree))
    root=next(scope for scope in scopes if scope.parent is None)
    by_expression={id(scope.expression):scope for scope in scopes}
    def un(node):
        while isinstance(node,(exp.Alias,exp.Paren,exp.Cast,exp.Round)):node=node.this
        return node
    def number(node,value):
        try:return isinstance(un(node),exp.Literal) and not un(node).is_string and Decimal(un(node).this)==Decimal(value)
        except (InvalidOperation,TypeError):return False
    def trace(node,owner):
        path=[];seen=set()
        for _ in range(20):
            node=un(node)
            if isinstance(node,exp.Subquery):
                owner=by_expression.get(id(node.this))
                if owner is None or len(owner.expression.selects)!=1:deny("标量投影来源不唯一。")
                path.append(owner);node=owner.expression.selects[0];continue
            if not isinstance(node,exp.Column):return node,owner,path
            if not node.table:
                marker=("output_alias",id(owner),node.name)
                projected=next((item for item in owner.expression.selects if item.alias_or_name==node.name),None)
                if projected is None or projected is node or marker in seen:deny("未限定字段不是可证明的真实输出别名。")
                seen.add(marker);node=projected;continue
            source=owner.sources.get(node.table)
            if isinstance(source,exp.Table):return node,owner,path
            marker=(id(source),node.name)
            if source is None or marker in seen:deny("投影谱系未知或循环。")
            seen.add(marker)
            projection=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
            if projection is None:deny("投影字段无法追溯。")
            path.append(source);owner=source;node=projection
        deny("投影深度超过限制。")
    def customer_key(node,owner):
        return _physical_field(node,owner) in {"invoice.customer_id","customer.customer_id"}
    def atoms(node):
        if node is None:return []
        if isinstance(node,(exp.Where,exp.Paren)):return atoms(node.this)
        if isinstance(node,exp.And):return atoms(node.left)+atoms(node.right)
        if isinstance(node,exp.Or):deny("期间和地域不能由未证明的OR旁路改写。")
        return [node]
    def grouped_customer(owner,scalar_group=None):
        group=owner.expression.args.get("group")
        if not group or not any(customer_key(item,owner) for item in group.expressions):return False
        for item in group.expressions:
            if scalar_group is not None and trace(item,owner)[1] is scalar_group:
                continue
            field=_physical_field(item,owner)
            if not field or not (field=="invoice.customer_id" or field.startswith("customer.")):return False
        return not owner.expression.args.get("having")
    def row_shape(owner,*,group=False,where=False):
        query=owner.expression
        if (not isinstance(query,exp.Select) or query.args.get("having") or query.args.get("qualify") or query.args.get("distinct") or
                query.args.get("group") and not group or query.args.get("where") and not where):
            deny("排名或透传结果附加了改变行集的筛选/聚合。")
        offset=query.args.get("offset")
        if offset and not number(offset.expression,0):deny("不能跳过第一名。")
        limit=query.args.get("limit")
        if limit and (not isinstance(limit.expression,exp.Literal) or not str(limit.expression.this).isdigit() or int(limit.expression.this)<1):deny("标量结果不能被隐藏。")
    def safe_period_filters(owner,operand,extras=()):
        contract=analysis.query_scope.get(operand) or {}
        contract=contract if isinstance(contract,dict) else {}
        current=contract.get("period") or (analysis.time_scope or {}).get("current") or {}
        filters=contract.get("filters")
        if filters is None:
            filters=[item for item in analysis.filters or [] if
                     (item.get("binding_scope")=="denominator" if operand=="denominator" else item.get("binding_scope")!="denominator")]
        expected=[]
        for item in filters:
            column=item.get("column") or item.get("field")
            values=item.get("value");values=values if isinstance(values,list) else [values]
            if str(item.get("operator") or "=").upper() not in {"=","IN"}:deny("当前地域/对象筛选尚无受支持的证明。")
            expected.append((column,frozenset(str(value) for value in values)))
        seen=set();dates=set()
        for atom in atoms(owner.expression.args.get("where")):
            if id(atom) in extras:continue
            if isinstance(atom,(exp.GTE,exp.LT)) and _physical_field(atom.left,owner)=="invoice.invoice_date":
                dates.add((atom.key,_midnight_date(atom.right)));continue
            actual=None
            if isinstance(atom,exp.EQ):
                for column,value in ((atom.left,atom.right),(atom.right,atom.left)):
                    if isinstance(value,exp.Literal):actual=(_physical_field(column,owner),frozenset({str(value.this)}))
            elif isinstance(atom,exp.In) and atom.expressions and all(isinstance(item,exp.Literal) for item in atom.expressions):
                actual=(_physical_field(atom.this,owner),frozenset(str(item.this) for item in atom.expressions))
            if actual not in expected:deny("SQL额外增加了未经当前合同确认的地域/对象条件。")
            seen.add(actual)
        wanted={("gte",current["start"]),("lt",current["end"])} if current.get("start") and current.get("end") else set()
        if dates!=wanted:deny("排名、客户金额或全年分母的期间被丢弃或改变。")
        if set(expected)!=seen:deny("当前确认的地域/对象筛选没有在正确操作数保留。")
    def invoice_grain(owner):
        physical={alias:pair for alias,pair in owner.selected_sources.items() if isinstance(pair[1],exp.Table)}
        return _invoice_grain_is_preserved(SimpleNamespace(selected_sources=physical,expression=owner.expression),catalog)
    def count_metric(node,owner):
        node=un(node)
        if not isinstance(node,exp.Count):return False
        target=node.this
        if isinstance(target,exp.Distinct):
            return invoice_grain(owner) and len(target.expressions)==1 and _physical_field(target.expressions[0],owner)=="invoice.invoice_id"
        return invoice_grain(owner) and (isinstance(target,exp.Star) or _physical_field(target,owner)=="invoice.invoice_id")
    def parse_division(value):
        value=un(value)
        if isinstance(value,exp.Mul):
            if number(value.left,100):value=un(value.right)
            elif number(value.right,100):value=un(value.left)
        return value if isinstance(value,exp.Div) else None
    candidates=[]
    for projection in root.expression.selects:
        value,owner,path=trace(projection,root)
        division=parse_division(value)
        if division is not None:candidates.append((division,owner,path))
    if len(candidates)!=1:deny("必须有唯一可追溯的真实金额比例，不能只返回计数或混入其它比例。")
    division,division_owner,ratio_path=candidates[0]
    # CAST/ROUND are not transparent around a quotient. Follow only the actual
    # projected ratio through genuine aliases; an unused well-formed ratio or
    # a lossless monetary wrapper cannot authorize rounding the final value.
    def exact_projection(node,owner,depth=0,seen=None):
        if depth>20:deny('比例投影超过有界深度。')
        seen=set() if seen is None else set(seen)
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        if isinstance(node,exp.Subquery):
            inner=by_expression.get(id(node.this))
            if inner is None or len(inner.expression.selects)!=1:deny('比例标量来源没有唯一投影。')
            return exact_projection(inner.expression.selects[0],inner,depth+1,seen)
        if isinstance(node,exp.Column):
            source=owner.sources.get(node.table) if node.table else None
            if isinstance(source,exp.Table):return node,owner
            target=source if source is not None else owner
            marker=(id(target),node.name)
            projected=next((item for item in target.expression.selects if item.alias_or_name==node.name),None)
            if marker in seen or projected is None or projected is node:deny('比例别名谱系未知或循环。')
            seen.add(marker)
            return exact_projection(projected,target,depth+1,seen)
        return node,owner
    def literal_scale(node):
        while isinstance(node,(exp.Paren,exp.Alias)):node=node.this
        if not isinstance(node,exp.Literal) or node.is_string:return None
        try:
            value=Decimal(node.this)
            return value if value in {Decimal(1),Decimal(100)} else None
        except (InvalidOperation,TypeError):return None
    def monetary_shape(node,owner,depth=0,*,zero_guard=False):
        node,owner=exact_projection(node,owner,depth)
        if isinstance(node,exp.Column):
            source=owner.sources.get(node.table)
            if (not isinstance(source,exp.Table) or source.name!='invoice' or
                    (source.db or 'public')!='public' or node.name!='total'):
                deny('金额操作数必须追溯到实际invoice.total。')
            column=next(c for c in catalog.get_table('invoice','public').columns if c.name=='total')
            declared=re.fullmatch(r'(?:numeric|decimal)\(\s*\d+\s*,\s*(\d+)\s*\)',column.data_type,re.I)
            if declared is None:deny('金额字段的精确小数scale未知，不能证明转换无损。')
            return {'scale':Decimal(1),'fractional_digits':int(declared[1])}
        if isinstance(node,exp.Sum):
            return monetary_shape(node.this,owner,depth+1,zero_guard=False)
        if isinstance(node,exp.Nullif) and zero_guard:
            zero=node.expression
            while isinstance(zero,(exp.Alias,exp.Paren)):zero=zero.this
            try:zero_ok=isinstance(zero,exp.Literal) and not zero.is_string and Decimal(zero.this)==0
            except (InvalidOperation,TypeError):zero_ok=False
            if not zero_ok:deny('分母NULLIF只允许真实字面0保护。')
            return monetary_shape(node.this,owner,depth+1,zero_guard=False)
        if isinstance(node,exp.Mul):
            for value,other in ((node.left,node.right),(node.right,node.left)):
                factor=literal_scale(value)
                if factor is not None:
                    proof=monetary_shape(other,owner,depth+1,zero_guard=False)
                    return {'scale':factor*proof['scale'],
                            'fractional_digits':max(0,proof['fractional_digits']-(2 if factor==100 else 0))}
            deny('分子乘数必须是真实数值字面量1或100，不能将ROUND/CAST等改变的常数当透明比例尺度。')
        if isinstance(node,(exp.Cast,exp.Round)):
            proof=monetary_shape(node.this,owner,depth+1,zero_guard=zero_guard)
            if isinstance(node,exp.Round):
                places=node.args.get('decimals')
                if (not isinstance(places,exp.Literal) or places.is_string or not str(places.this).isdigit() or
                        int(places.this)<proof['fractional_digits']):
                    deny('分子/分母缩放后的金额不能先ROUND损失真实最小货币单位，再参与比例。')
            else:
                target=node.args.get('to')
                if target is None or target.this!=exp.DataType.Type.DECIMAL:
                    deny('金额操作数不支持整数/浮点等可能改变数值的CAST。')
                parts=[part.sql(dialect='postgres')for part in target.expressions]
                if parts and (len(parts)not in{1,2}or any(not part.isdigit()for part in parts)or
                              (int(parts[1])if len(parts)==2 else 0)<proof['fractional_digits']):
                    deny('金额CAST的scale不能低于当前缩放后的实际小数位数。')
            return proof
        deny('金额操作数含未证明的数学包装，不能作为透明比例操作数。')
    def projected_ratio(node,owner,depth=0):
        node,owner=exact_projection(node,owner,depth)
        if isinstance(node,exp.Div):
            numerator_shape=monetary_shape(node.left,owner,depth+1)
            denominator_shape=monetary_shape(node.right,owner,depth+1,zero_guard=True)
            if denominator_shape['scale']!=1:deny('分母金额不能另加缩放改变全年金额口径。')
            return {'scale':numerator_shape['scale'],'rounding':[]}
        if isinstance(node,exp.Mul):
            for value,other in ((node.left,node.right),(node.right,node.left)):
                factor=literal_scale(value)
                if factor is not None:
                    proof=projected_ratio(other,owner,depth+1)
                    if proof is not None:return {**proof,'scale':factor*proof['scale']}
            return None
        if isinstance(node,(exp.Cast,exp.Round)):
            proof=projected_ratio(node.this,owner,depth+1)
            if proof is None:return None
            if isinstance(node,exp.Cast):
                target=node.args.get('to')
                if target is None or target.this!=exp.DataType.Type.DECIMAL or target.expressions:
                    deny('最终比例只允许无精度收缩的NUMERIC转换；定点scale/整数/浮点CAST不能冒充透明投影。')
                return proof
            from qa_agent.sql.percentage_precision import requested_percent_digits
            requested=requested_percent_digits(analysis,deny)
            places=node.args.get('decimals')
            if (requested is None or proof['scale'] not in {Decimal(1),Decimal(100)} or proof['rounding'] or
                    not isinstance(places,exp.Literal) or places.is_string or not str(places.this).isdigit() or
                    int(places.this)!=requested+(2 if proof['scale']==1 else 0)):
                deny('比例SQL舍入必须只执行一次，并与明确授权的最终百分比精度及真实原始/百分比尺度完全一致；否则交程序格式化。')
            return {**proof,'rounding':[{'actual_scale':str(proof['scale']),'sql_decimals':int(places.this),
                'requested_percent_decimals':requested,'claim':'explicit_display_rounding_not_lossless_ratio_equivalence'}]}
        return None
    ratio_outputs=[proof for projected in root.expression.selects
                   if (proof:=projected_ratio(projected,root)) is not None]
    if len(ratio_outputs)!=1 or ratio_outputs[0]['scale'] not in {Decimal(1),Decimal(100)}:
        deny('最终比例只能是原始比例或恰好一次百分比放大，不能在分子与输出层重复乘100。')
    ratio_output_proof=ratio_outputs[0]
    numerator=un(division.left)
    if isinstance(numerator,exp.Mul):
        if number(numerator.left,100):numerator=un(numerator.right)
        elif number(numerator.right,100):numerator=un(numerator.left)
        else:deny("金额分子不能另加缩放。")
    amount,amount_owner,amount_path=trace(numerator,division_owner)
    outer_sum=None
    if isinstance(amount,exp.Sum) and isinstance(un(amount.this),exp.Column) and _physical_field(amount.this,amount_owner)!="invoice.total":
        outer_sum=amount_owner
        amount,amount_owner,child_path=trace(amount.this,amount_owner);amount_path+=child_path
    if not isinstance(amount,exp.Sum) or _physical_field(amount.this,amount_owner)!="invoice.total" or not invoice_grain(amount_owner):
        deny("分子必须仍是客户发票SUM(invoice.total)，不能用COUNT、明细金额或重复发票替代。")
    denominator=un(division.right)
    if isinstance(denominator,exp.Nullif):
        if not number(denominator.expression,0):deny("分母NULLIF保护常量必须为0。")
        denominator=denominator.this
    total,total_owner,total_path=trace(denominator,division_owner)
    if (not isinstance(total,exp.Sum) or _physical_field(total.this,total_owner)!="invoice.total" or
            total_owner.expression.args.get("group") or not invoice_grain(total_owner)):
        deny("分母必须仍是独立全期发票金额SUM(invoice.total)，不能改成张数、选中客户金额或明细金额。")
    row_shape(total_owner,where=True);safe_period_filters(total_owner,"denominator")
    # Presentation wrappers must not silently turn exact invoice cents into
    # integers before division. The catalog's invoice.total scale is two.
    for scope in _active_scopes(scopes):
        for projected in [scope.expression]:
            for transform in walk_in_scope(projected):
                if not isinstance(transform,(exp.Round,exp.Cast)):continue
                actual,owner,_=trace(transform.this,scope)
                money=(_physical_field(actual,owner)=="invoice.total" or
                       isinstance(actual,exp.Sum) and _physical_field(actual.this,owner)=="invoice.total")
                integer_identity=count_metric(actual,owner) or customer_key(actual,owner)
                window_identity=isinstance(actual,exp.Window) and isinstance(actual.this,exp.RowNumber)
                if window_identity:
                    if isinstance(transform,exp.Round):
                        places=transform.args.get('decimals')
                        if not isinstance(places,exp.Literal) or places.is_string or not str(places.this).isdigit():
                            deny('真实ROW_NUMBER不能负精度舍入后冒充唯一第一。')
                    else:
                        target=transform.args['to'].sql(dialect='postgres')
                        if not re.fullmatch(r'(?:BIGINT|NUMERIC|DECIMAL)',target,re.I):
                            deny('真实ROW_NUMBER仅允许完整整数类型，不能截断字符串或压缩成多重第一。')
                if isinstance(transform,exp.Round) and integer_identity:
                    places=transform.args.get("decimals")
                    if not isinstance(places,exp.Literal) or places.is_string or not str(places.this).isdigit():
                        deny("发票张数或客户键不能通过负精度ROUND改变真实排序。")
                elif isinstance(transform,exp.Cast) and integer_identity:
                    target=transform.args["to"].sql(dialect="postgres")
                    if not re.fullmatch(r"(?:SMALLINT|INT|INTEGER|BIGINT|(?:NUMERIC|DECIMAL)(?:\(\s*\d+\s*,\s*\d+\s*\))?)",target,re.I):
                        deny("发票张数或客户键不能转成字符串/浮点数改变实际排序。")
                if isinstance(transform,exp.Round) and money:
                    places=transform.args.get("decimals")
                    if not isinstance(places,exp.Literal) or places.is_string or not str(places.this).isdigit() or int(places.this)<2:
                        deny("分子/分母金额不能先损失发票的小数精度再计算比例。")
                elif isinstance(transform,exp.Cast) and (money or isinstance(actual,exp.Div)):
                    target=transform.args["to"].sql(dialect="postgres")
                    numeric=re.fullmatch(r"(?:NUMERIC|DECIMAL)(?:\(\s*\d+\s*,\s*(\d+)\s*\))?",target,re.I)
                    if not numeric or numeric[1] is not None and int(numeric[1])<(2 if money else 1):
                        deny("金额或比例不能通过整数/低精度CAST改变已确认的数值。")
    # Find the Top-1 node actually consumed by the numerator's value or by its
    # mandatory customer-key qualification. An unrelated winner CTE is ignored.
    winner=None;key_filter=None;join_winner_alias=None
    window_rank=None;window_owner=None;prewinner_scopes=set()
    for scope in amount_path:
        if scope.expression.args.get("limit") and number(scope.expression.args["limit"].expression,1):winner=scope;break
    if winner is None and rank_metric=='invoice_revenue':
        for candidate in amount_path:
            conditions=atoms(candidate.expression.args.get('where'))
            if len(conditions)!=1 or not isinstance(conditions[0],(exp.EQ,exp.LTE)) or not number(conditions[0].right,1):
                continue
            actual,owner,path=trace(conditions[0].left,candidate)
            if not isinstance(actual,exp.Window) or not isinstance(actual.this,exp.RowNumber) or actual.args.get('partition_by'):
                continue
            if candidate.expression.args.get('limit') or candidate.expression.args.get('offset'):
                deny('窗口Top1结果不能再次限制或偏移。')
            row_shape(owner)
            if len(owner.selected_sources)!=1 or any(isinstance(source,exp.Table) for _,source in owner.selected_sources.values()):
                deny('客户窗口只能由同一真实客户聚合透传，不能额外多行关联。')
            winner=candidate;window_rank=actual;window_owner=owner
            # Every stage before the actual winner is a verified unchanged
            # row stream, not a new scalar source available for arbitrary JOIN.
            position=amount_path.index(candidate)
            prewinner_scopes=set(amount_path[position+1:])-{amount_owner}
            for stage in prewinner_scopes:
                row_shape(stage)
                if len(stage.selected_sources)!=1 or any(isinstance(source,exp.Table) for _,source in stage.selected_sources.values()):
                    deny('窗口之前存在未证明的多行来源或行集变更。')
            break
    if winner is None:
        for atom in atoms(amount_owner.expression.args.get("where")):
            pairs=[]
            if isinstance(atom,exp.EQ):pairs=[(atom.left,atom.right),(atom.right,atom.left)]
            if isinstance(atom,exp.In) and atom.args.get("query"):pairs=[(atom.this,atom.args["query"])]
            for column,subquery in pairs:
                if not customer_key(column,amount_owner) or not isinstance(un(subquery),exp.Subquery):continue
                key,key_owner,path=trace(subquery,amount_owner)
                for scope in path:
                    if scope.expression.args.get("limit") and number(scope.expression.args["limit"].expression,1) and customer_key(key,key_owner):
                        winner=scope;key_filter=atom;break
                if winner:break
            if winner:break
    if winner is None:
        for alias,(_,source) in amount_owner.selected_sources.items():
            if isinstance(source,exp.Table) or not source.expression.args.get("limit") or not number(source.expression.args["limit"].expression,1):continue
            for join in amount_owner.expression.args.get("joins") or []:
                on=join.args.get("on")
                if not isinstance(on,exp.EQ) or join.args.get("side"):continue
                for left,right in ((on.left,on.right),(on.right,on.left)):
                    if isinstance(right,exp.Column) and right.table==alias and customer_key(left,amount_owner) and customer_key(right,amount_owner):
                        winner=source;join_winner_alias=alias;break
                if winner:break
            if winner:break
    if winner is None:deny("客户金额没有实际依赖当前排名Top1的客户键，不能用未消费winner CTE冒充。")
    row_shape(winner,group=bool(winner.expression.args.get("group")),where=bool(winner.expression.args.get("where")))
    limit=winner.expression.args.get("limit")
    if window_rank is None and (not limit or not number(limit.expression,1)):deny("真实客户排名必须选择Top1。")
    ordering=window_rank.args.get('order') if window_rank is not None else winner.expression.args.get("order")
    if not ordering or not ordering.expressions or not ordering.expressions[0].args.get("desc"):deny("内层客户排名必须按当前已确认的排名指标降序。")
    order=un(ordering.expressions[0].this)
    if isinstance(order,exp.Column) and not order.table:
        order=next((item for item in winner.expression.selects if item.alias_or_name==order.name),order)
    counted,count_owner,count_path=trace(order,window_owner if window_rank is not None else winner)
    correct_rank=(count_metric(counted,count_owner) if rank_metric=="invoice_count" else
                  isinstance(un(counted),exp.Sum) and _physical_field(un(counted).this,count_owner)=="invoice.total" and invoice_grain(count_owner))
    if not correct_rank or not grouped_customer(count_owner):deny("内层必须使用当前已确认的每客户金额/发票张数，不能按ID或明细行数选人。")
    if rank_metric=="invoice_count" and len(ordering.expressions)<2:
        deny("发票张数并列时必须实际按客户编号升序取第一。")
    if rank_metric=="invoice_count":
        second=ordering.expressions[1]
        second_value=un(second.this)
        if isinstance(second_value,exp.Column) and not second_value.table:
            second_value=next((item for item in winner.expression.selects if item.alias_or_name==second_value.name),second_value)
        if second.args.get("desc") or not customer_key(second_value,winner):
            deny("真实第二排序必须是同一客户键升序，不能按金额或其它人物键代替明确并列规则。")
    identity_passthrough_scopes=set()
    def transparent_winner_identity_lookup(owner):
        """Only a real same-customer PK lookup may accompany the ranked stream.

        Invoice.customer_id is a non-null FK in the actual catalog.  Looking
        up that existing customer's unique PK cannot remove or duplicate a
        grouped customer.  No other physical/derived stream, ON predicate or
        pre-ranking filter is accepted as a transparent identity lookup.
        """
        if len(owner.selected_sources)!=2:return None
        physical=[(alias,source) for alias,(_,source) in owner.selected_sources.items() if isinstance(source,exp.Table)]
        derived=[(alias,source) for alias,(_,source) in owner.selected_sources.items() if not isinstance(source,exp.Table)]
        if len(physical)!=1 or len(derived)!=1:return None
        identity_alias,identity=physical[0];stream_alias,stream=derived[0]
        if identity.name!='customer' or (identity.db or 'public')!='public':return None
        target=catalog.get_table(identity.name,identity.db or 'public')
        if target.primary_key!=('customer_id',) or not any(c.name=='customer_id' and not c.nullable for c in target.columns):return None
        def unchanged(source,seen=None):
            seen=set() if seen is None else set(seen)
            if id(source) in seen or not isinstance(source.expression,exp.Select):return False
            if source is count_owner:
                return not any(source.expression.args.get(key) for key in ('limit','offset','having','qualify','distinct'))
            seen.add(id(source))
            if any(source.expression.args.get(key) for key in ('where','group','having','qualify','distinct','limit','offset','joins')):return False
            safe=(len(source.selected_sources)==1 and all(not isinstance(child,exp.Table) and unchanged(child,seen)
                for _,child in source.selected_sources.values()))
            if safe:identity_passthrough_scopes.add(source)
            return safe
        if not unchanged(stream):return None
        def exact_origin(node,scope,seen=None):
            seen=set() if seen is None else set(seen)
            while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
            if not isinstance(node,exp.Column) or not node.table:return None
            source=scope.sources.get(node.table)
            if isinstance(source,exp.Table):return source,node.name,scope
            marker=(id(source),node.name)
            if source is None or marker in seen or not isinstance(source.expression,exp.Select):return None
            seen.add(marker)
            projected=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
            return exact_origin(projected,source,seen) if projected is not None else None
        joins=owner.expression.args.get('joins') or []
        if len(joins)!=1:return None
        join=joins[0];on=join.args.get('on')
        while isinstance(on,exp.Paren):on=on.this
        side=str(join.args.get('side') or '').upper();kind=str(join.args.get('kind') or '').upper()
        if (not isinstance(on,exp.EQ) or join.args.get('using') or join.args.get('method') or
                side not in {'','LEFT'} or kind not in {'','INNER'} or
                side=='LEFT' and join.this.alias_or_name!=identity_alias):return None
        for real,key in ((on.left,on.right),(on.right,on.left)):
            while isinstance(real,exp.Paren):real=real.this
            while isinstance(key,exp.Paren):key=key.this
            if (not isinstance(real,exp.Column) or real.table!=identity_alias or real.name!='customer_id' or
                    not isinstance(key,exp.Column) or key.table!=stream_alias):continue
            origin=exact_origin(key,owner)
            if origin is None:continue
            source,column,scope=origin
            if scope is not count_owner or (source.db or 'public')!='public':continue
            if source.name not in {'invoice','customer'} or column!='customer_id':continue
            # Even a physical customer PK can be NULL-extended by an earlier
            # LEFT JOIN. Require the real invoice FK/non-null guarantee for
            # this bounded lookup proof rather than the PK name alone.
            invoice=catalog.get_table('invoice','public')
            if not any(c.name=='customer_id' and not c.nullable for c in invoice.columns):continue
            if any(fk.get('columns')==['customer_id'] and (fk.get('references') or {}).get('schema','public')=='public' and
                    fk['references'].get('table')==target.name and fk['references'].get('columns')==list(target.primary_key)
                    for fk in invoice.foreign_keys):return identity_alias
        return None
    winner_lookup_alias=None
    if winner is not count_owner:
        row_shape(winner,where=window_rank is not None)
        if len(winner.selected_sources)!=1:
            winner_lookup_alias=transparent_winner_identity_lookup(winner)
            if winner_lookup_alias is None:deny("Top1透传层只能通过实际非空FK关联同一客户唯一PK，不能连接其它客户、额外筛选或多行列表。")
            prewinner_scopes.update(identity_passthrough_scopes)
    safe_period_filters(count_owner,"numerator")
    if amount_owner.expression.args.get("group") and count_owner is amount_owner:
        if not grouped_customer(amount_owner):deny("分组金额与排名指标不属于同一个客户粒度，可能错绑其他客户。")
    elif key_filter is not None:
        if amount_owner.expression.args.get("group") and not grouped_customer(amount_owner,total_owner):deny("选中客户金额不能额外按其它对象拆分。")
        safe_period_filters(amount_owner,"numerator",extras={id(key_filter)})
    elif join_winner_alias is not None:
        if amount_owner.expression.args.get("group") and not grouped_customer(amount_owner,total_owner):deny("选中客户金额不能额外按其它对象拆分。")
        safe_period_filters(amount_owner,"numerator")
    else:deny("客户金额没有正确限定为实际选中的客户。")
    if total_owner is amount_owner or total_owner is count_owner:deny("全期分母不能复用选中客户的聚合。")
    def identity_join(owner,alias):
        if owner is winner and alias==winner_lookup_alias:return True
        physical=owner.sources.get(alias)
        if not isinstance(physical,exp.Table) or physical.name!='customer' or (physical.db or 'public')!='public' or catalog.get_table('customer').primary_key!=('customer_id',):
            return False
        for join in owner.expression.args.get('joins') or []:
            on=join.args.get('on')
            if join.this.alias_or_name!=alias or not isinstance(on,exp.EQ) or str(join.args.get('side') or '').upper() not in {'','LEFT'} or join.args.get('using'):
                continue
            for real,key in ((on.left,on.right),(on.right,on.left)):
                if isinstance(real,exp.Column) and real.table==alias and real.name=='customer_id' and isinstance(key,exp.Column) and owner.sources.get(key.table) is winner and customer_key(key,owner):
                    return True
        return False
    # No other derived source may be multi-row. The winner can have at most one
    # row; the denominator is an unconditional scalar aggregate (exactly one).
    allowed_scalar={total_owner,winner}
    if not amount_owner.expression.args.get("group"):
        allowed_scalar.add(amount_owner)
    def scalar_source(scope,seen=None):
        seen=set() if seen is None else set(seen)
        if scope in allowed_scalar:return True
        if id(scope) in seen:return False
        seen.add(id(scope));row_shape(scope)
        return all(identity_join(scope,alias) if isinstance(source,exp.Table) else scalar_source(source,seen) for alias,(_,source) in scope.selected_sources.items())
    for owner in set(ratio_path+total_path+amount_path+[root,division_owner]+([outer_sum] if outer_sum else [])):
        if owner in {amount_owner,count_owner,total_owner,winner} or owner in prewinner_scopes:continue
        row_shape(owner)
        if not scalar_source(owner):deny("最终比例连接了未经证明的多行来源。")
    for owner in {root,division_owner,amount_owner}:
        for alias,(_,source) in owner.selected_sources.items():
            if isinstance(source,exp.Table):
                if owner is not amount_owner and not identity_join(owner,alias):deny("最终结果额外扫描了无关多行物理表。")
            elif source is not winner and not scalar_source(source):deny("金额侧连接了额外多行派生列表。")
    for owner in {root,division_owner,amount_owner,count_owner,total_owner}:
        for join in owner.expression.args.get("joins") or []:
            alias=join.this.alias_or_name;source=owner.sources.get(alias);on=join.args.get("on")
            if isinstance(source,exp.Table):
                if (not isinstance(on,exp.EQ) or not isinstance(on.left,exp.Column) or not isinstance(on.right,exp.Column)
                        or str(join.args.get("side") or "").upper() not in {"","LEFT"}):
                    deny("物理表关联不能另加地域/对象条件或改变发票粒度。")
                left,right=on.left,on.right
                left_source,right_source=owner.sources.get(left.table),owner.sources.get(right.table)
                if isinstance(left_source,exp.Table) and isinstance(right_source,exp.Table):
                    keys=frozenset(((left_source.name,left.name),(right_source.name,right.name)))
                    valid=False
                    for physical in catalog.tables:
                        for foreign in physical.foreign_keys:
                            reference=foreign["references"]
                            if len(foreign["columns"])==1 and keys==frozenset(((physical.name,foreign["columns"][0]),(reference["table"],reference["columns"][0]))):valid=True
                    if not valid:deny("客户/发票物理关联没有使用真实目录外键，不能用同类型的错误键碰巧匹配。")
                elif not identity_join(owner,alias) and not (owner is amount_owner and join_winner_alias is not None and
                          (left_source is winner or right_source is winner) and customer_key(left,owner) and customer_key(right,owner)):
                    deny("物理金额侧只能通过已验证winner的真实客户键关联。")
            elif owner is amount_owner and alias==join_winner_alias:
                if not isinstance(on,exp.EQ):deny("选中客户的键关联不能另加条件。")
            elif (join.args.get("side") or str(join.args.get("kind") or "").upper() not in {"","INNER","CROSS"}
                  or on is not None and not (isinstance(on,exp.Boolean) and on.this is True)):
                deny("一行辅助结果只能无过滤地连接。")
    actual_identity=False;actual_numerator=False
    for projected in root.expression.selects:
        value,owner,path=trace(projected,root)
        for step in path:
            if step not in {amount_owner,count_owner,total_owner,winner}:row_shape(step)
        if parse_division(value) is not None:continue
        if isinstance(value,exp.Column) and (_physical_field(value,owner) or '').startswith('customer.') and identity_join(owner,value.table):
            if value.name=='customer_id':actual_identity=True
            continue
        anchored=(winner in path or owner is amount_owner and (key_filter is not None or join_winner_alias is not None))
        if customer_key(value,owner) and anchored:
            actual_identity=True;continue
        if owner is amount_owner and value.sql(dialect="postgres")==amount.sql(dialect="postgres") and anchored:
            actual_numerator=True;continue
        if owner is total_owner and value.sql(dialect="postgres")==total.sql(dialect="postgres"):continue
        if anchored and ((owner is count_owner and (count_metric(value,owner) or (_physical_field(value,owner) or "").startswith("customer.")))
                         or owner is amount_owner and (_physical_field(value,owner) or "").startswith("customer.")):
            continue
        deny("额外显示列没有来自已验证客户/计数/金额的真实投影。")
    if not actual_identity or not actual_numerator:
        deny("单一客户赢家比例必须实际输出同一winner的可靠客户编号及其发票金额，不能只给比例或展示另一客户的资料。")
    return {"verified":True,"mode":"customer_invoice_count_winner_invoice_amount_ratio" if rank_metric=="invoice_count" else "customer_amount_winner_invoice_amount_ratio",
            "rank_metric":rank_metric,"amount_metric":"invoice_revenue","top_n":1,
            "customer_key_dependency":True,"invoice_grain_preserved":True,"denominator_unchanged":True,
            "tie_breaker":tie,"actual_customer_identity_and_amount_projected":True,
            "actual_window_top1":window_rank is not None,
            "pre_top_identity_lookup_proven":winner_lookup_alias is not None,
            "ratio_output_scale":str(ratio_output_proof['scale']),
            "output_rounding":ratio_output_proof['rounding'],
            "physical_identity_join_proven":winner_lookup_alias is not None or any(identity_join(root,alias) for alias in root.sources)}
