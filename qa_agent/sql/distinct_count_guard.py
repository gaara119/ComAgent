"""Prove complete, consumed counts over the program-confirmed track set."""
from __future__ import annotations
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _physical_field,_midnight_date
from qa_agent.sql.validator import SQLValidationError

def validate_distinct_count(sql,catalog,analysis):
    contract=(analysis.query_scope or {}).get('distinct_count')
    if not contract:return {'verified':True,'mode':'no_explicit_distinct_count'}
    def deny(message):raise SQLValidationError('不同曲目计数未通过：'+message)
    target=contract.get('column') if isinstance(contract,dict) else None
    if (catalog.database.casefold()!='chinook' or target not in {'track.track_id','invoice_line.track_id'}
        or contract.get('source')!='program:explicit_distinct_tracks'
        or not contract.get('source_evidence') or analysis.metric!='record_count'):
        deny('合同缺少真实目录、程序来源或一致指标。')
    scopes=list(traverse_scope(_qualified(sql,catalog)))
    root=next((scope for scope in scopes if scope.parent is None),None)
    if root is None or not isinstance(root.expression,exp.Select):deny('最终输出必须是SELECT。')
    consumed=set()
    def unwrap(node):
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        return node
    def passthrough(scope):
        query=scope.expression
        if (not isinstance(query,exp.Select) or len(scope.selected_sources)!=1 or query.args.get('joins')
            or any(query.args.get(key) for key in ('where','group','having','qualify','distinct','offset','limit'))):
            deny('派生透传必须单来源且不能筛选、分组、截断或隐藏实际行。')
    def resolve(node,owner,seen=None):
        seen=set() if seen is None else set(seen);consumed.add(owner);node=unwrap(node)
        if isinstance(node,exp.Column):
            child=owner.sources.get(node.table)
            if child is not None and not isinstance(child,exp.Table):
                marker=(id(child),node.name)
                if marker in seen:deny('派生投影循环。')
                passthrough(owner)
                projection=next((v for v in child.expression.selects if v.alias_or_name==node.name),None)
                if projection is None:deny('派生字段没有实际投影。')
                return resolve(projection,child,seen|{marker})
        return node,owner
    def column(node,owner):
        node,owner=resolve(node,owner)
        field=_physical_field(node,owner) if isinstance(node,exp.Column) else None
        if not field:deny('身份/分组键必须是无CAST/ROUND/运算的真实物理字段。')
        return node,owner,field
    def conjunction(node):
        if node is None:return []
        if isinstance(node,(exp.Where,exp.Paren)):return conjunction(node.this)
        if isinstance(node,exp.And):return conjunction(node.left)+conjunction(node.right)
        if isinstance(node,exp.Or):deny('不能用OR伪造必需筛选或关联。')
        return [node]
    def rowset(owner,identity):
        query=owner.expression
        if any(query.args.get(key) for key in ('having','qualify','distinct','offset')):deny('计数层不能额外删行。')
        limit=query.args.get('limit')
        if limit is not None:
            value=limit.expression
            if (not isinstance(value,exp.Literal) or value.is_string or not str(value.this).isdigit()
                or int(value.this)<1 or query.args.get('group')):deny('计数结果不能被LIMIT隐藏或截断分组。')
        from_=query.args.get('from_');anchor=from_.this if from_ is not None else None
        if not isinstance(anchor,exp.Table):deny('计数行集需要真实物理表锚点。')
        facts=[alias for alias,(_,source) in owner.selected_sources.items()
               if isinstance(source,exp.Table) and source.name==target.split('.')[0]]
        if len(facts)!=1:deny('实际行集必须包含唯一所问明细/目录锚点。')
        fact_alias=facts[0]
        preserved={anchor.alias_or_name};pairs=[];edges=[]
        for join in query.args.get('joins') or []:
            alias=join.this.alias_or_name;other=owner.sources.get(alias)
            side=str(join.args.get('side') or '').upper();kind=str(join.args.get('kind') or '').upper()
            atoms=conjunction(join.args.get('on'))
            if side not in {'','LEFT'} or kind not in {'','INNER'} or not isinstance(other,exp.Table) or len(atoms)!=1:
                deny('只支持保留成员行的外键到一关联。')
            atom=atoms[0]
            if not isinstance(atom,exp.EQ) or not isinstance(atom.left,exp.Column) or not isinstance(atom.right,exp.Column):
                deny('ON必须是当前真实别名上的键相等。')
            valid=False
            for foreign,primary in ((atom.left,atom.right),(atom.right,atom.left)):
                connected=((foreign.table==alias and primary.table in preserved) or
                           (primary.table==alias and foreign.table in preserved))
                if not connected:continue
                if side=='LEFT' and (anchor.alias_or_name!=fact_alias or foreign.table not in preserved or primary.table!=alias):continue
                source=owner.sources.get(foreign.table)
                referenced=owner.sources.get(primary.table)
                if not isinstance(source,exp.Table) or not isinstance(referenced,exp.Table):continue
                table=catalog.get_table(source.name,source.db or 'public')
                for fk in table.foreign_keys:
                    ref=fk['references']
                    if fk['columns']==[foreign.name] and ref['table']==referenced.name and ref['columns']==[primary.name]:
                        nullable=next(c.nullable for c in table.columns if c.name==foreign.name)
                        valid=not nullable or side=='LEFT'
                        if valid:break
                if valid:
                    pairs.append(frozenset(((foreign.table,foreign.name),(primary.table,primary.name))))
                    edges.append((foreign.table,primary.table));break
            if not valid:deny('未证明当前别名的真实FK到一并保留成员行。')
            preserved.add(alias)
        # SQL FROM order may start at invoice then INNER JOIN its details.
        # Prove the same set from the requested fact via outgoing FK-to-one
        # edges; a reverse child join cannot establish catalogue membership.
        reachable={fact_alias}
        for _ in range(len(edges)+1):
            reachable.update(primary for foreign,primary in edges if foreign in reachable)
        if set(owner.selected_sources)!=reachable:deny('存在无法从所问锚点证明保留成员的反向/额外行集。')
        field=_physical_field(identity,owner)
        if field==target:
            if identity.table!=fact_alias:deny('无关同表别名不能替代真实锚点。')
        elif {field,target}=={'track.track_id','invoice_line.track_id'}:
            if frozenset(((identity.table,identity.name),(fact_alias,'track_id'))) not in pairs:
                deny('计数别名与明细锚点缺少同一真实FK证明。')
        else:deny('COUNT DISTINCT没有消费合同真实曲目键。')
    wanted=set(analysis.grouping or []);proofs=[];projected_groups=[];count_owner=physical_owner=None
    for projection in root.expression.selects:
        value,owner=resolve(projection,root)
        if isinstance(value,exp.Count):
            distinct=value.this
            if not isinstance(distinct,exp.Distinct) or len(distinct.expressions)!=1:
                deny('必须完整COUNT(DISTINCT真实曲目键)，不能SUM数量/普通COUNT。')
            identity,key_owner,field=column(distinct.expressions[0],owner)
            if count_owner is not None:deny('当前合同只证明一个完整计数输出。')
            if owner is not key_owner:passthrough(owner)
            rowset(key_owner,identity);count_owner=owner;physical_owner=key_owner
            proofs.append({'column':field,'requested_column':target,'distinct':True})
        elif isinstance(value,exp.Column):
            _,group_owner,field=column(value,owner)
            if field not in wanted:deny('额外字段必须是当前明确请求的分组字段。')
            projected_groups.append((field,group_owner))
        else:deny('最终输出不能以算术、ROUND、CAST、FILTER或常量修改完整计数。')
    if len(proofs)!=1:deny('最终输出未消费唯一真实计数；未引用CTE不构成证明。')
    actual_groups=[]
    group=physical_owner.expression.args.get('group')
    for item in group.expressions if group is not None else []:
        _,owner,field=column(item,physical_owner)
        if owner is not physical_owner:deny('分组必须属于同一计数行集。')
        actual_groups.append(field)
    if (set(actual_groups)!=wanted or {field for field,_ in projected_groups}!=wanted
        or any(owner is not physical_owner for _,owner in projected_groups)):
        deny('实际及可见分组必须与请求一致，不能将整体计数拆组。')
    for scope in consumed:
        if scope is not physical_owner:passthrough(scope)
    approved=[]
    for item in analysis.filters or []:
        if item.get('binding_scope') not in {None,'global','eligibility'}:continue
        values=item.get('value',item.get('values'));values=values if isinstance(values,list) else [values]
        approved.append((item.get('column',item.get('field')),str(item.get('operator') or '=').upper(),frozenset(str(v) for v in values)))
    current=(analysis.time_scope or {}).get('current') or {};seen=set();dates=set()
    for atom in conjunction(physical_owner.expression.args.get('where')):
        if (current.get('start') and current.get('end') and isinstance(atom,(exp.GTE,exp.LT)) and column(atom.left,physical_owner)[2]=='invoice.invoice_date'
            and _midnight_date(atom.right)==current.get('start' if isinstance(atom,exp.GTE) else 'end')):
            dates.add('start' if isinstance(atom,exp.GTE) else 'end');continue
        candidate=None
        if isinstance(atom,exp.In) and atom.expressions and all(isinstance(v,exp.Literal) for v in atom.expressions):
            candidate=(column(atom.this,physical_owner)[2],'IN',frozenset(str(v.this) for v in atom.expressions))
        elif isinstance(atom,(exp.EQ,exp.NEQ,exp.GT,exp.GTE,exp.LT,exp.LTE)) and isinstance(atom.right,exp.Literal):
            candidate=(column(atom.left,physical_owner)[2],{'eq':'=','neq':'!=','gt':'>','gte':'>=','lt':'<','lte':'<='}[atom.key],frozenset({str(atom.right.this)}))
        if candidate not in approved:deny('实际计数含当前合同未授权的额外筛选。')
        seen.add(candidate)
    if set(approved)-seen:deny('实际行集丢失已确认筛选。')
    if current and dates!={'start','end'}:deny('实际行集未保留当前完整半开期间。')
    return {'verified':True,'mode':'physical_distinct_track_identity','proofs':proofs,'grouping':sorted(wanted)}

