"""Bounded proof for explicit TopN rows plus their same-subset total.

The supported shape is one final transparent read of a genuine ranked source,
with SUM(that source's measure) OVER (). No API, database or SQL rewriting for
execution is performed; a scalar witness reuses the existing TopN sum proof.
"""
from __future__ import annotations

from hashlib import sha256
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


def validate_ranked_rows_total(sql,catalog,analysis):
    def deny(message):
        raise SQLValidationError('排名名单与合计未通过：'+message)
    requirements=set(analysis.output_requirements or [])
    if not {'ranked_subset_rows','ranked_subset_total'}<=requirements or analysis.task_type!='ranking':
        return {'applicable':False}
    if analysis.query_scope.get('ranking_scope')=='per_group':
        deny('分组TopN名单加合计尚无此有界证明，不能冒充全局子集合计。')
    if isinstance(analysis.top_n,bool) or not isinstance(analysis.top_n,int) or analysis.top_n<1:
        deny('缺少真实整数TopN。')
    tree=_qualified(sql,catalog)
    scopes=list(traverse_scope(tree))
    root=next((s for s in scopes if s.parent is None),None)
    if root is None or not isinstance(tree,exp.Select):deny('最终结果必须为SELECT。')
    if len(root.selected_sources)!=1:deny('最终只能消费一个真实TopN来源，不能增加JOIN或旁路。')
    alias,(_,ranked)=next(iter(root.selected_sources.items()))
    if isinstance(ranked,exp.Table) or not isinstance(ranked.expression,exp.Select):deny('名单必须直接消费实际TopN子查询或CTE。')
    if any(tree.args.get(key) for key in ('joins','where','group','having','qualify','distinct','offset')):
        deny('最终名单不能添加筛选、分组、去重、偏移或连接。')
    limit=tree.args.get('limit')
    if limit is not None:
        node=limit.expression
        if not isinstance(node,exp.Literal) or node.is_string or not str(node.this).isdigit() or int(node.this)<analysis.top_n:
            deny('最终行数限制不能截断实际TopN名单。')

    def un(node):
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        return node

    def projected(column,owner):
        if not isinstance(column,exp.Column):deny('字段必须为无变换的真实列。')
        source=owner.sources.get(column.table)
        if source is None:deny('列没有实际来源。')
        if isinstance(source,exp.Table):return column,owner
        if not isinstance(source.expression,exp.Select):deny('不支持消费集合操作或VALUES作为真实身份。')
        target=next((p for p in source.expression.selects if p.alias_or_name==column.name),None)
        if target is None:deny('派生字段没有实际投影。')
        return target,source

    def trace(node,owner,depth=0):
        if depth>16:deny('派生字段谱系超过有界深度。')
        node=un(node)
        if isinstance(node,exp.Column):
            if not node.table:
                target=next((p for p in owner.expression.selects if p.alias_or_name==node.name),None)
                if target is None or target is node or un(target) is node:deny('排序别名缺少可追溯实际投影。')
                return trace(target,owner,depth+1)
            target,child=projected(node,owner)
            if child is not owner:return trace(target,child,depth+1)
        return node,owner

    windows=[];columns=[]
    for projection in tree.selects:
        node=un(projection)
        if isinstance(node,exp.Window):
            if (not isinstance(node.this,exp.Sum) or node.args.get('partition_by') or
                    node.args.get('order') or node.args.get('spec') or node.args.get('alias')):
                deny('合计必须是同一TopN全部行的无分区、无排序窗口SUM。')
            value=un(node.this.this)
            if not isinstance(value,exp.Column) or value.table!=alias:deny('合计必须消费实际排名指标列。')
            windows.append((projection,value))
        elif isinstance(node,exp.Column) and node.table==alias:
            columns.append((projection,node))
        else:deny('名单只能透明展示真实对象字段和指标，不能混入常量、算术或其它聚合。')
    if len(windows)!=1:deny('需要且只允许一个实际TopN窗口合计。')
    names=[p.alias_or_name for p in tree.selects]
    if not all(names) or len(names)!=len(set(names)):deny('输出列名必须唯一，不能让合计覆盖实体或每项金额。')
    total_projection,measure=windows[0]
    if not any(column.name==measure.name for _,column in columns):deny('必须同时展示各项实际指标，不能仅展示身份与总额。')

    # The transparent measure chain must end in the exact registered measure,
    # without numeric wrappers that silently change pre-ranking values.
    value,owner=trace(measure,root)
    def field(node,scope):
        node,scope=trace(node,scope)
        if not isinstance(node,exp.Column):return None
        source=scope.sources.get(node.table)
        if not isinstance(source,exp.Table):return None
        return (source.db or 'public',source.name,node.name)
    metric=analysis.metric
    valid=(isinstance(value,exp.Sum) and (
        metric=='invoice_revenue' and field(value.this,owner)==('public','invoice','total') or
        metric=='purchased_quantity' and field(value.this,owner)==('public','invoice_line','quantity') or
        metric=='detail_revenue' and isinstance(un(value.this),exp.Mul) and
        {field(un(value.this).left,owner),field(un(value.this).right,owner)}==
        {('public','invoice_line','unit_price'),('public','invoice_line','quantity')}))
    if not valid:deny('每项指标没有无损追溯到当前真实聚合口径。')

    try:target=catalog.get_table(analysis.rank_object)
    except Exception:deny('排名对象没有唯一真实表。')
    def entity_key(node,scope=root):
        actual=field(node,scope)
        if actual is None:return None
        schema,table_name,name=actual
        if (schema,table_name)==(target.schema,target.name) and name in target.primary_key:return name
        physical=catalog.get_table(table_name,schema)
        for fk in physical.foreign_keys:
            ref=fk['references']
            if (ref.get('schema',schema),ref['table'])!=(target.schema,target.name):continue
            for local,remote in zip(fk['columns'],ref['columns']):
                if local==name and remote in target.primary_key:return remote
        return None
    visible={entity_key(column) for _,column in columns}
    if not target.primary_key or not set(target.primary_key)<=visible:deny('名单必须真实展示当前排名对象的主键，不能只给总额或伪造身份。')

    # A grouped date/invoice ID would rank customer-days rather than customers.
    # Only target PKs and transparently catalog-dependent attributes are safe.
    group=owner.expression.args.get('group')
    if group is None or any(not isinstance(un(p),exp.Column) for p in group.expressions):
        deny('排名指标必须按真实对象键分组，不能用分组集或表达式拆分实体。')
    if len(target.primary_key)!=1:deny('复合实体键的名单合计暂不支持此有界证明。')
    grouped_keys=[p for p in group.expressions if entity_key(p,owner)==target.primary_key[0]]
    if not grouped_keys:deny('指标分组没有保留实际排名对象主键。')
    from qa_agent.sql.semantic_guard import _mandatory_atoms,_active_scopes
    equalities=[atom for join in owner.expression.args.get('joins') or []
        for atom in _mandatory_atoms(join.args.get('on')).values()
        if isinstance(atom,exp.EQ) and isinstance(un(atom.left),exp.Column) and isinstance(un(atom.right),exp.Column)]
    # A valid metric expression alone does not prove one fact per input row.
    # Every joined dimension must be a real complete FK -> unique PK lookup.
    sources={alias:source for alias,(_,source) in owner.selected_sources.items()}
    fact_name='invoice' if metric=='invoice_revenue' else 'invoice_line'
    facts=[alias for alias,source in sources.items() if isinstance(source,exp.Table) and source.name==fact_name]
    if len(facts)!=1 or any(not isinstance(source,exp.Table) for source in sources.values()):
        deny('每项聚合的真实事实粒度暂须由单一物理事实表及到一目录关联证明。')
    actual={frozenset(((un(eq.left).table,un(eq.left).name),(un(eq.right).table,un(eq.right).name))) for eq in equalities}
    edges=[]
    for prior,local_node in sources.items():
        local=catalog.get_table(local_node.name,local_node.db or 'public')
        for alias,table_node in sources.items():
            if prior==alias:continue
            remote=catalog.get_table(table_node.name,table_node.db or 'public')
            for fk in local.foreign_keys:
                ref=fk['references']
                if (ref.get('schema',local.schema),ref['table'])!=(remote.schema,remote.name) or tuple(ref['columns'])!=remote.primary_key:
                    continue
                pairs={frozenset(((prior,lc),(alias,rc))) for lc,rc in zip(fk['columns'],ref['columns'])}
                if pairs and pairs<=actual:
                    nonnull=all(not next(c for c in local.columns if c.name==name).nullable for name in fk['columns'])
                    edges.append((prior,alias,nonnull,pairs))
    seen=set(facts);nonnull_aliases=set(facts)
    while True:
        before=(set(seen),set(nonnull_aliases))
        for prior,alias,nonnull,_ in edges:
            if prior in seen:seen.add(alias)
            if prior in nonnull_aliases and nonnull:nonnull_aliases.add(alias)
        if (seen,nonnull_aliases)==before:break
    if seen!=set(sources):deny('排名金额输入包含不能证明到一的连接，可能重复或改变事实粒度。')
    identity_aliases={trace(p,owner)[0].table for p in grouped_keys}
    needed=set(identity_aliases)
    for expression in grouped_keys:
        identity,_=trace(expression,owner)
        for prior,alias,_,pairs in edges:
            dimension=sources[alias]
            if (prior==identity.table and (dimension.db or 'public',dimension.name)==(target.schema,target.name)
                    and frozenset(((prior,identity.name),(alias,target.primary_key[0]))) in pairs):
                # The actual target lookup establishes membership when the
                # grouped target FK is nullable (real employee/album domain).
                needed.add(alias)
    for _ in range(len(sources)):
        for prior,alias,_,_ in edges:
            if alias in needed:needed.add(prior)
    joins=owner.expression.args.get('joins') or []
    origin=owner.expression.args.get('from_')
    base_alias=origin.this.alias_or_name if origin is not None else None
    fk_pairs=set().union(*(pairs for _,_,_,pairs in edges)) if edges else set()
    def conjunctions(node):
        node=un(node)
        return conjunctions(node.left)+conjunctions(node.right) if isinstance(node,exp.And) else [node]
    for join in joins:
        side=str(join.args.get('side') or '').upper();kind=str(join.args.get('kind') or '').upper()
        alias=join.this.alias_or_name
        if side not in {'','LEFT'} or (side and kind not in {'','OUTER'}) or (not side and kind not in {'','INNER'}):
            deny('此有界事实粒度证明不支持RIGHT/FULL/SEMI/ANTI或其它连接方向。')
        if side=='LEFT' and base_alias not in facts:
            deny('外连接必须从真实事实表锚定，不能补入无事实的维表实体。')
        if any(not isinstance(atom,exp.EQ) or not isinstance(un(atom.left),exp.Column) or
                not isinstance(un(atom.right),exp.Column) or
                frozenset(((un(atom.left).table,un(atom.left).name),(un(atom.right).table,un(atom.right).name))) not in fk_pairs
                for atom in conjunctions(join.args.get('on'))):
            deny('关联ON暂只支持真实FK到主键的必要等值；额外ON筛选须改用明确且可核验的范围。')
    # In all-INNER reverse table order, the source on the syntactic right may
    # be the fact itself; classify every non-fact relation independently.
    inner_aliases={alias for alias in sources if alias not in facts and
        not any(j.this.alias_or_name==alias and str(j.args.get('side') or '').upper()=='LEFT' for j in joins)}
    for alias in inner_aliases:
        if alias not in nonnull_aliases and alias not in needed:
            deny('非必要的可空外键INNER维表会删除未分配事实，不能视为透明查名。')
    token=lambda p:(un(p).table,un(p).name)
    connected={token(grouped_keys[0])}
    for _ in range(len(equalities)+1):
        old=set(connected)
        for eq in equalities:
            left,right=token(eq.left),token(eq.right)
            if left in connected:connected.add(right)
            if right in connected:connected.add(left)
        if old==connected:break
    if any(token(p) not in connected for p in grouped_keys):
        deny('多个实体键没有同一身份等值证明，不能按不同客户的组合拆排名。')
    for expression in group.expressions:
        if expression in grouped_keys:continue
        item,at=trace(expression,owner)
        source=at.sources.get(item.table) if isinstance(item,exp.Column) else None
        if (at is not owner or not isinstance(source,exp.Table) or
                (source.db or 'public',source.name)!=(target.schema,target.name) or
                (item.table,target.primary_key[0]) not in connected):
            deny('额外GROUP列不是同实体主键函数依赖属性，不能把实体拆成多项。')
    for scope in _active_scopes(scopes):
        query=scope.expression
        if not isinstance(query,exp.Select):deny('不支持实际消费集合操作作为排名或金额输入。')
        if scope not in {root,ranked} and (query.args.get('limit') or query.args.get('offset')):
            deny('实际排名前不能先截取金额输入或其它关联来源。')

    # Both selection and display must use the same complete order. A later
    # country/ID order cannot reinterpret the selected ranks.
    rank_order=ranked.expression.args.get('order')
    outer_order=tree.args.get('order')
    if rank_order is None or outer_order is None or len(rank_order.expressions)!=len(outer_order.expressions):
        deny('展示顺序必须完整保留实际TopN的排序。')
    for actual,selected in zip(outer_order.expressions,rank_order.expressions):
        actual_value,actual_owner=trace(actual.this,root)
        selected_value,selected_owner=trace(selected.this,ranked)
        if (actual_value.sql(dialect='postgres')!=selected_value.sql(dialect='postgres') or actual_owner is not selected_owner or
                bool(actual.args.get('desc'))!=bool(selected.args.get('desc')) or
                bool(actual.args.get('nulls_first'))!=bool(selected.args.get('nulls_first'))):
            deny('展示排序与实际被合计的完整TopN排序不一致。')

    # This witness cannot broaden the accepted scalar contract: it invokes the
    # unchanged existing proof on the same ranked source and same measure.
    witness=tree.copy()
    witness.set('expressions',[exp.alias_(exp.Sum(this=measure.copy()),'ranked_subset_total')])
    for key in ('order','limit','offset'):witness.set(key,None)
    scalar=analysis.model_copy(deep=True)
    scalar.output_requirements=[r for r in scalar.output_requirements if r!='ranked_subset_rows']
    from qa_agent.clarify.sql_guard import validate_current_patch_contract
    validate_current_patch_contract(witness.sql(dialect='postgres'),catalog,scalar,[])
    from qa_agent.sql.ranked_entity_domain import validate_ranked_entity_domain
    validate_ranked_entity_domain(sql,catalog,analysis)
    return {'applicable':True,'verified':True,'source':'program:proved_ranked_rows_and_total',
        'sql_sha256':sha256(sql.encode('utf-8')).hexdigest(),'top_n':analysis.top_n,
        'measure_column':measure.name,'total_column':total_projection.alias_or_name,
        'row_columns':[p.alias_or_name for p,_ in columns],
        'proof':'same ranked source; exact measure; visible physical entity key; identical full order; existing scalar TopN witness'}
