"""Prove actual average-customer operands use exactly current scope.

No reference answers/results, dataset IDs, calls, rewrites or implicit defaults.
Bounded to actual invoice rows and transparent single-source CTEs/subqueries.
"""
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes, _midnight_date
from qa_agent.sql.validator import SQLValidationError, validate_value_bindings


def validate_average_customer_scope(sql, catalog, intent):
    get=lambda key,default=None:intent.get(key,default)if isinstance(intent,dict)else getattr(intent,key,default)
    if get('metric')!='average_customer_amount':
        return {'verified':True,'mode':'not_average_customer_amount'}

    def deny(message):raise SQLValidationError('客户平均金额作用域：'+message)
    if get('grouping') or get('top_n') is not None:
        deny('当前有界证明只支持本轮全局平均，分组平均需独立证明。')
    time_scope=get('time_scope',{})or{}
    period=time_scope.get('current')or{}
    if bool(period.get('start'))!=bool(period.get('end')):
        deny('当前期间缺少完整半开边界。')
    if not period.get('start') and not time_scope.get('all_data'):
        deny('未证明明确当前期间或全数据授权。')
    required=get('filters',[])or[]
    if any(b.get('binding_scope','global')not in{'global',None}for b in required):
        deny('平均金额不能混用比例操作数或未证明资格条件。')
    if(get('query_scope',{})or{}).get('qualification_filters'):
        deny('存在独立资格合同，当前有界单发票集合证明不能静默忽略。')
    tree=_qualified(sql,catalog);scopes=list(traverse_scope(tree));active=_active_scopes(scopes)
    root=next(s for s in scopes if s.parent is None);by_expr={id(s.expression):s for s in scopes}

    def strip(node):
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        return node

    def resolve(node,owner,depth=0):
        if depth>20:deny('投影谱系超过有界深度。')
        node=strip(node)
        if isinstance(node,exp.Column):
            source=owner.sources.get(node.table)
            if source is not None and not isinstance(source,exp.Table):
                projection=next((p for p in source.expression.selects if p.alias_or_name==node.name),None)
                if projection is None:deny('派生字段没有实际投影。')
                return resolve(projection,source,depth+1)
        if isinstance(node,exp.Subquery):
            source=by_expr.get(id(node.this))
            if source is None or len(source.expression.selects)!=1:deny('标量子查询不是唯一实际投影。')
            return resolve(source.expression.selects[0],source,depth+1)
        return node,owner

    def exact_atoms(node):
        if node is None:return[]
        node=strip(node)
        if isinstance(node,exp.Where):return exact_atoms(node.this)
        if isinstance(node,exp.And):return exact_atoms(node.left)+exact_atoms(node.right)
        return[node]

    physical_scopes=set()
    aggregate_scopes=set()
    def field(node,owner):
        node,owner=resolve(node,owner)
        if not isinstance(node,exp.Column):deny('金额/客户键不能被CAST、ROUND、COALESCE或算术改写。')
        source=owner.sources.get(node.table)
        if not isinstance(source,exp.Table)or(source.db or'public')!='public'or source.name!='invoice':
            deny('操作数必须来自实际invoice行集。')
        physical_scopes.add(owner)
        return 'invoice.'+node.name

    def aggregate(node,owner,role):
        node,owner=resolve(node,owner)
        aggregate_scopes.add(owner)
        if role=='amount':
            if not isinstance(node,exp.Sum)or node.args.get('distinct')or field(node.this,owner)!='invoice.total':
                deny('分子必须是当前同一invoice集合的真实SUM(total)。')
        else:
            distinct=node.this if isinstance(node,exp.Count)else None
            if not isinstance(distinct,exp.Distinct)or len(distinct.expressions)!=1 or field(distinct.expressions[0],owner)!='invoice.customer_id':
                deny('分母必须是当前同一invoice集合的COUNT(DISTINCT customer_id)。')
        return {'role':role,'owner_sql':owner.expression.sql(dialect='postgres')}

    ratios=[];display_authorization=None
    for projection in root.expression.selects:
        node,owner=resolve(projection,root)
        if isinstance(node,exp.Round):
            # Only the final complete result may be formatted. Every operand
            # below is still proved independently without stripping ROUND.
            if owner is not root:
                deny('只允许最终输出的完整平均值按真实用户授权格式化，不能提前舍入派生值。')
            from qa_agent.sql.money_precision_source import actual_money_precision
            authorized=actual_money_precision(intent)
            places=node.args.get('decimals')
            if (not authorized or not authorized.get('authorized')or authorized.get('digits')!=2
                    or not isinstance(places,exp.Literal)or places.is_string or places.this!='2'):
                deny('最终金额ROUND仅允许真实用户明确授权的两位小数；不能使用模型说明或默认猜测。')
            display_authorization=authorized
            node,owner=resolve(node.this,owner)
        if isinstance(node,exp.Cast):
            target=node.args.get('to')
            if target is None or target.this!=exp.DataType.Type.DECIMAL or target.expressions:
                deny('最终平均值转换没有无损精度证明。')
            node,owner=resolve(node.this,owner)
        if not isinstance(node,exp.Div):deny('最终输出必须实际消费SUM金额除以唯一客户数，不能仅附无关正确聚合。')
        denom,den_owner=resolve(node.right,owner)
        if not isinstance(denom,exp.Nullif)or not isinstance(denom.expression,exp.Literal)or denom.expression.is_string or denom.expression.this!='0':
            deny('零客户分母必须明确NULLIF(真实客户数,0)，不能补1/补0。')
        ratios.append({'amount':aggregate(node.left,owner,'amount'),'customers':aggregate(denom.this,den_owner,'customers')})
    if len(ratios)!=1:deny('当前全局平均必须有唯一实际平均结果。')

    def binding_matches(atom,owner,binding):
        q=owner.expression.copy();q.set('expressions',[exp.Literal.number(1)])
        for key in('with_','group','having','order','limit','offset','qualify'):q.set(key,None)
        q.set('where',exp.Where(this=atom.copy()))
        try:validate_value_bindings(q.sql(dialect='postgres'),catalog,[{**binding,'binding_scope':'global'}]);return True
        except ValueError:return False

    checked=[]
    for owner in physical_scopes:
        sources=[s for _,s in owner.selected_sources.values()]
        if len(sources)!=1 or not isinstance(sources[0],exp.Table)or sources[0].name!='invoice':
            deny('物理输入只支持唯一invoice来源；不能通过明细扇出或未证明JOIN改变人数/金额。')
        predicates=exact_atoms(owner.expression.args.get('where'));covered=set();matched=set()
        for atom in predicates:
            if not isinstance(atom,(exp.EQ,exp.NEQ,exp.In,exp.GT,exp.GTE,exp.LT,exp.LTE)):
                deny('不支持OR/NOT/子查询等隐藏筛选；不得只证明其某个必要片段。')
            period_atom=False
            if period.get('start')and isinstance(atom,(exp.GTE,exp.LT)):
                key='start'if isinstance(atom,exp.GTE)else'end'
                if isinstance(atom.left,exp.Column)and field(atom.left,owner)=='invoice.invoice_date'and _midnight_date(atom.right)==period[key]:
                    period_atom=True;covered.add(key)
            matches=[index for index,b in enumerate(required)if binding_matches(atom,owner,b)]
            if not period_atom and not matches:deny('实际操作数包含当前未授权额外过滤，可能继承已退休名单或阈值。')
            matched.update(matches)
        if period.get('start')and covered!={'start','end'}:deny('实际操作数遗漏或改变当前期间边界。')
        if matched!=set(range(len(required))):deny('实际操作数遗漏当前已授权全局条件。')
        checked.append(owner.expression.sql(dialect='postgres'))
    for owner in active:
        q=owner.expression
        if not isinstance(q,exp.Select)or any(q.args.get(k)for k in('group','having','qualify','distinct','offset')):
            deny('当前集合不能被分组、去重、HAVING或偏移改变。')
        if owner not in physical_scopes and q.args.get('where'):
            deny('派生/聚合透传层含额外筛选，当前有界证明不静默跨层忽略。')
        if q.args.get('joins'):deny('不支持连接产生新行或筛去发票；单源同集合形式可等价重试。')
        sources=[s for _,s in owner.selected_sources.values()]
        if len(sources)>1 or any(isinstance(s,exp.Table)for s in sources)and owner not in physical_scopes:
            deny('存在额外未证明物理来源或多行集合。')
        limit=q.args.get('limit')
        if limit is not None and(owner is not root or not isinstance(limit.expression,exp.Literal)or limit.expression.is_string or not str(limit.expression.this).isdigit()or int(limit.expression.this)<1):
            deny('不能在聚合前限制行集，仅允许最终单行结果正数展示上限。')
        if owner in aggregate_scopes:
            # All aggregate functions in its actual output must be the consumed
            # global SUM/COUNT; no extra projection may turn this into row SQL.
            for p in q.selects:
                value=strip(p)
                if value.find(exp.Window)is not None:deny('不能用窗口重复值冒充唯一全局聚合。')

    def is_scalar(owner,seen=None):
        seen=set()if seen is None else set(seen)
        if id(owner)in seen:return False
        seen.add(id(owner))
        if owner in aggregate_scopes:return True
        sources=[s for _,s in owner.selected_sources.values()]
        if not sources:return True
        return len(sources)==1 and not isinstance(sources[0],exp.Table)and is_scalar(sources[0],seen)
    if not is_scalar(root):
        deny('最终投影仍逐发票/派生明细重复标量平均值，不能冒充唯一聚合结果。')
    return{'verified':True,'mode':'same_invoice_population_average_customer_amount',
           'period':period,'required_bindings':len(required),'physical_populations':checked,
           'operands':ratios,'bounded_support':'single invoice source; transparent CTE/scalar aggregate; no joins',
           'display_precision_authorization':display_authorization,
           'reference_answers_consumed':False}
