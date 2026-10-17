"""Bounded proof that a ranked entity key denotes an existing real entity.

Only current intent, actual explicit grouping source and authentic catalog/AST
are consumed. A nullable FK does not by itself denote a target row. This module proves row domain only, not
metric, period, fanout, grouping uniqueness or TopN correctness.
"""
from __future__ import annotations

import re
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope, walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes, _mandatory_atoms
from qa_agent.sql.validator import SQLValidationError


def ranked_entity_domain_requirement(catalog, intent, *, question=''):
    get=lambda key,default=None:intent.get(key,default)if isinstance(intent,dict)else getattr(intent,key,default)
    entity=get('rank_object')
    ranking=(get('task_type')=='ranking'or 'ranked_subset_total'in(get('output_requirements',[])or[])
             or get('task_type')=='ratio'and isinstance(get('top_n'),int)and not isinstance(get('top_n'),bool)and get('top_n')>0)
    domain_kind='ranked_entity'
    if not ranking or not entity:
        # Bounded current Chinook employee role: grouping a nullable support
        # representative FK is not the same as grouping actual employees.
        # Do not infer entity domains for arbitrary country/month/raw columns.
        actual_question=question.split('\n当前执行条件',1)[0]
        explicit_employee_group=bool(re.search(
            r'(?:各(?:个|位|名)?|每(?:个|位|名)?|按照?|分)\s*'
            r'(?:(?:销售|客户|支持|负责|客服|业务)\s*){0,4}(?:员工|人员|负责人)|'
            r'\b(?:each|per|by)\s+(?:(?:sales|support)\s+)*(?:employee|representative|rep)\b',
            actual_question,re.I))
        employees=[table for table in catalog.tables if table.schema=='public'and table.name=='employee'
                   and table.primary_key==('employee_id',)]
        if (catalog.database.lower()!='chinook'or get('task_type')!='aggregation'
                or not explicit_employee_group or len(employees)!=1):
            return None
        possible={'employee.employee_id','public.employee.employee_id'}
        for table in catalog.tables:
            for relation in table.foreign_keys:
                reference=relation['references']
                if (reference.get('schema',table.schema)=='public'and reference['table']=='employee'
                        and reference['columns']==['employee_id']and len(relation['columns'])==1):
                    possible.add(table.name+'.'+relation['columns'][0])
                    possible.add(table.schema+'.'+table.name+'.'+relation['columns'][0])
        if not any(field in possible for field in (get('grouping',[])or[])if isinstance(field,str)):
            return None
        entity='employee';domain_kind='explicit_employee_group'
    candidates=[table for table in catalog.tables if table.name==entity or table.schema+'.'+table.name==entity]
    if len(candidates)!=1:
        return None  # Month/country and unknown rank labels are not table rows.
    target=candidates[0]
    incoming=[]
    for table in catalog.tables:
        for relation in table.foreign_keys:
            reference=relation['references']
            if ((reference.get('schema',table.schema),reference['table'])==(target.schema,target.name)
                    and tuple(reference['columns'])==target.primary_key):
                incoming.append({'table':table.schema+'.'+table.name,'columns':list(relation['columns']),
                    'nullable':[next(c.nullable for c in table.columns if c.name==column)for column in relation['columns']]})
    # Explicit unassigned scope is not silently replaced by an INNER/NOT NULL.
    # Unsupported domain requests fail explicitly instead of creating defaults.
    qscope=get('query_scope',{})or{}
    words={'album':r'专辑|album','genre':r'流派|曲风|genre','artist':r'艺术家|艺人|artist',
           'employee':r'员工|销售支持人员|客户负责人|负责人|employee'}.get(target.name,re.escape(target.name))
    explicit_unassigned=bool(qscope.get('include_unassigned')is True or
        re.search(r'(?:未归属|未关联|未分配|未指派|无归属|没有归属)(?:到|给)?(?:任何)?(?:'+words+r')|'
                  r'(?:没有|无)(?:任何)?(?:'+words+r')(?:归属|关联|信息)?|'
                  r'(?:'+words+r')(?:归属|关联|编号|ID)?(?:未知|为空|缺失|未分配|未关联)|'+
                  re.escape(target.name)+r'_id\s+IS\s+NULL',question,re.I))
    return {'domain_kind':domain_kind,'target_table':target.schema+'.'+target.name,'primary_key':list(target.primary_key),
        'incoming_foreign_keys':incoming,'explicit_unassigned_requested':explicit_unassigned,
        'instruction':'按实体排名或明确按实际员工分组时，对象是实际实体。按指向该实体的可空外键分组前，必须通过真实FK到PK的必然INNER关系，'
          '或在该分组/排名之前用必要WHERE明确排除该外键NULL；不能把未归属NULL组当一张实体。'
          '若先CTE统计再取TopN，排名内部作用域保留真实实体键供证明，最终仅合计/名称时不要求额外投影该键。'
          '用户明确要求未归属/未知范围时不得擅自删掉它，当前证明器不支持则明确失败。'}


def validate_ranked_entity_domain(sql,catalog,intent,*,question=''):
    requirement=ranked_entity_domain_requirement(catalog,intent,question=question)
    if requirement is None:
        return {'verified':True,'mode':'no_ranked_table_entity_domain'}
    def deny(message):raise SQLValidationError('排名实体域：'+message)
    if requirement['explicit_unassigned_requested']:
        deny('题面明确包含未归属/未知对象，不能自动改为真实已归属实体；当前有界实体域证明不支持该特殊分组。')
    target_schema,target_name=requirement['target_table'].split('.')
    target=catalog.get_table(target_name,target_schema)
    if len(target.primary_key)!=1:
        deny('当前实体域证明只支持真实单列主键，不能静默忽略复合身份。')
    target_column=target.primary_key[0]
    key_fields={(target_schema,target_name,target_column)}
    for relation in requirement['incoming_foreign_keys']:
        if len(relation['columns'])==1:
            schema,table=relation['table'].split('.')
            key_fields.add((schema,table,relation['columns'][0]))
    tree=_qualified(sql,catalog)
    scopes=list(traverse_scope(tree));active=set(_active_scopes(scopes))
    indices={scope:index for index,scope in enumerate(scopes)}
    if any(isinstance(scope.expression,(exp.SetOperation,exp.Values))for scope in active):
        deny('实际排名消费链路包含集合运算或VALUES；当前证明器不能证明所有分支的实体身份，需改为已支持的真实表实体计划。')

    def strip(node):
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        return node

    def source(scope,alias):
        entry=scope.selected_sources.get(alias)
        return entry[1]if entry else None

    def projection(scope,name):
        if not isinstance(scope.expression,exp.Select):return None
        return next((node for node in scope.expression.selects if node.alias_or_name==name),None)

    def identity(node,owner,depth=0):
        if depth>20:deny('实体键的透明投影谱系超过有界深度。')
        node=strip(node)
        if not isinstance(node,exp.Column):return None
        selected=source(owner,node.table)
        if isinstance(selected,exp.Table):
            physical=(selected.db or'public',selected.name,node.name)
            return (owner,node.table,*physical)if physical in key_fields else None
        if isinstance(selected,Scope):
            value=projection(selected,node.name)
            return identity(value,selected,depth+1)if value is not None else None
        return None

    def related(node,owner,depth=0):
        if depth>20:deny('实体键候选谱系超过有界深度。')
        node=strip(node)
        if isinstance(node,exp.Column):
            selected=source(owner,node.table)
            if isinstance(selected,exp.Table):
                physical=(selected.db or'public',selected.name,node.name)
                return [physical]if physical in key_fields else[]
            if isinstance(selected,Scope):
                value=projection(selected,node.name)
                return related(value,selected,depth+1)if value is not None else[]
            return[]
        if isinstance(node,(exp.Subquery,exp.Select)):return[]
        return [value for child in node.iter_expressions()for value in related(child,owner,depth+1)]

    def measure_lineage(node,owner,depth=0):
        if depth>20:deny('度量与实体身份区分超过有界深度。')
        node=strip(node)
        if isinstance(node,(exp.AggFunc,exp.Window,exp.Subquery,exp.Select)):return True
        if isinstance(node,exp.Column):
            selected=source(owner,node.table)
            if isinstance(selected,Scope):
                value=projection(selected,node.name)
                return measure_lineage(value,selected,depth+1)if value is not None else False
            return False
        return any(measure_lineage(child,owner,depth+1)for child in node.iter_expressions())

    def constant_projection(node,owner,depth=0):
        if depth>20:deny('常量投影谱系超过有界深度。')
        node=strip(node)
        if isinstance(node,exp.Column):
            selected=source(owner,node.table)
            if isinstance(selected,Scope):
                value=projection(selected,node.name)
                return constant_projection(value,selected,depth+1)if value is not None else False
            return False
        return not any(isinstance(value,(exp.Column,exp.AggFunc,exp.Window,exp.Subquery,exp.Select))for value in node.walk())

    def outer_nullable(owner,alias):
        q=owner.expression
        first=q.args.get('from_')
        seen={first.this.alias_or_name}if first is not None and first.this is not None else set()
        nullable=set()
        for join in q.args.get('joins')or[]:
            right=join.this.alias_or_name;side=(join.args.get('side')or'').upper()
            if side=='LEFT':nullable.add(right)
            elif side=='RIGHT':nullable.update(seen)
            elif side=='FULL':nullable.update(seen|{right})
            seen.add(right)
        return alias in nullable

    def is_not_null(atom,column):
        atom=strip(atom)
        if isinstance(atom,exp.Not):
            inside=strip(atom.this)
            return (isinstance(inside,exp.Is)and not inside.args.get('negate')and
                isinstance(inside.expression,exp.Null)and strip(inside.this)==column)
        return (isinstance(atom,exp.Is)and atom.args.get('negate')and
            isinstance(atom.expression,exp.Null)and strip(atom.this)==column)

    def has_synthetic_groups(owner):
        group=owner.expression.args.get('group')
        return group is not None and any(isinstance(node,(exp.Rollup,exp.Cube,exp.GroupingSets))for node in group.walk())

    def nonnull(node,owner,depth=0,allow_join=True):
        if depth>20:deny('实体非空证明超过有界深度。')
        node=strip(node)
        if not isinstance(node,exp.Column)or identity(node,owner)is None:return None
        where=list(_mandatory_atoms(owner.expression.args.get('where')).values())
        having=list(_mandatory_atoms(owner.expression.args.get('having')).values())
        if any(is_not_null(atom,node)for atom in where+having):return 'mandatory_same_scope_IS_NOT_NULL'
        # Only actual mandatory equalities qualify. A LEFT ON condition, OR
        # branch, SELECT expression or unused CTE cannot prove membership.
        atoms=list(where)
        if allow_join:
            for join in owner.expression.args.get('joins')or[]:
                if not join.args.get('side')and (join.args.get('kind')or'').upper()in{'','INNER'}:
                    atoms.extend(_mandatory_atoms(join.args.get('on')).values())
            for atom in atoms:
                if not isinstance(atom,exp.EQ):continue
                other=atom.right if strip(atom.left)==node else atom.left if strip(atom.right)==node else None
                if other is None:continue
                actual=identity(other,owner)
                if actual is None or actual[2:]!=(target_schema,target_name,target_column):continue
                if nonnull(other,owner,depth+1,allow_join=False):
                    return 'mandatory_real_FK_to_target_PK'
        if outer_nullable(owner,node.table)or has_synthetic_groups(owner):return None
        selected=source(owner,node.table)
        if isinstance(selected,exp.Table):
            table=catalog.get_table(selected.name,selected.db or'public')
            column=next(c for c in table.columns if c.name==node.name)
            if node.name in table.primary_key or not column.nullable:
                return 'authentic_PK_or_NOT_NULL_FK'
            return None
        if isinstance(selected,Scope):
            value=projection(selected,node.name)
            return nonnull(value,selected,depth+1,allow_join=allow_join)if value is not None else None
        return None

    checks=[]
    for owner in scopes:
        if owner not in active or not isinstance(owner.expression,exp.Select):continue
        q=owner.expression;group=q.args.get('group')
        ranking_window=any(isinstance(node,exp.Window)and isinstance(node.this,(exp.RowNumber,exp.Rank,exp.DenseRank))
                           for node in walk_in_scope(q))
        rank_boundary=q.args.get('limit')is not None or ranking_window
        # A raw CTE may transport nullable keys to a later mandatory filter.
        # Require membership at aggregation/ranking boundaries, not at every
        # intermediate projection before the real domain has been selected.
        if group is None and not rank_boundary:
            continue
        candidates=[(node,True)for node in group.expressions]if group is not None else[]
        # Direct ranked rows or projected CTE identity keys are also checked;
        # outer scalar totals are covered by their actually consumed children.
        candidates+=[(node,False)for node in q.selects]
        # PostgreSQL may consume a real derived key in this boundary's ORDER
        # without projecting that key into the user-visible result. Only this
        # scope's actual sorting expressions count; keys in another scope or
        # inside scalar subqueries cannot provide this boundary's identity.
        boundary_order=q.args.get('order')if rank_boundary else None
        if boundary_order is not None:
            candidates+=[(ordered.this,False)for ordered in boundary_order.expressions]
        relevant=[(node,is_group)for node,is_group in candidates if related(node,owner)]
        if relevant and has_synthetic_groups(owner):deny('ROLLUP/CUBE/GROUPING SETS会产生非真实实体NULL汇总组，当前排名域不支持。')
        if rank_boundary and any(constant_projection(node,owner)for node in q.selects):
            deny('实际排名作用域含常量投影，不能把常量身份或金额包装为真实实体排名；当前证明器不支持该输出。')
        local_start=len(checks)
        for node,is_group in relevant:
            if not is_group and measure_lineage(node,owner):continue
            key=identity(node,owner)
            if key is None:
                # Measures may mention a key in COUNT(DISTINCT key), without
                # using it as an entity identity. They are not domain proof.
                bare=strip(node)
                if isinstance(bare,(exp.AggFunc,exp.Window)):continue
                deny('实体键经过CAST/COALESCE/算术等非透明变换，不能证明真实实体身份。')
            method=nonnull(node,owner)
            if method is None:deny('实际消费的实体键可能为NULL；必须在该分组/排名前用必要IS NOT NULL或真实INNER FK→PK限制，不能把NULL桶当实体。')
            checks.append({'scope_index':indices[owner],'key_sql':strip(node).sql(dialect='postgres'),
                'physical_column':'.'.join(key[2:]),'proof':method})
        if len(checks)==local_start:
            # Naming/grouping a genuine target row does not require an extra
            # ID in the final user-visible projection. Its actual PK source
            # must still be present and non-null in this same boundary.
            for alias,(_,selected)in owner.selected_sources.items():
                if not isinstance(selected,exp.Table)or(selected.db or'public',selected.name)!=(target_schema,target_name):continue
                key=exp.column(target_column,table=alias)
                method=nonnull(key,owner)
                if method:
                    if has_synthetic_groups(owner):deny('实体排名不能消费ROLLUP/CUBE/GROUPING SETS产生的非实体总计组。')
                    checks.append({'scope_index':indices[owner],'key_sql':key.sql(dialect='postgres'),
                        'physical_column':requirement['target_table']+'.'+target_column,
                        'proof':'same_scope_real_target_PK_row_domain/'+method})
            if rank_boundary and len(checks)==local_start:
                deny('实际TopN/排名作用域自身没有可追溯实体身份；其它已消费或未消费的正确子查询不能替代该身份。')
    if not checks:deny('最终实际消费链路没有可证明的真实实体键；未使用的正确CTE不能提供证明。')
    return {'verified':True,'mode':'grouped_real_entity_domain'if requirement['domain_kind']=='explicit_employee_group'else'ranked_real_entity_domain','target_table':requirement['target_table'],
        'primary_key':requirement['primary_key'],'checks':checks,'proof_scope':'Entity membership only; existing metric/period/TopN/fanout checks still required.',
        'reference_answers_consumed':False}
