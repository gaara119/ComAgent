"""Prove a consumed employee ranking stays inside current customer ownership.

Bounded AST proof only: no database, files, values, sample rows or gold answers.
It proves the employee row domain, not the count metric, TopN or all filters;
those existing SQL guards must still run unchanged.
"""
from __future__ import annotations

from decimal import Decimal,InvalidOperation

from sqlglot import exp, parse
from sqlglot.optimizer.scope import Scope, traverse_scope, walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes, _mandatory_atoms
from qa_agent.sql.validator import SQLValidationError


def validate_employee_domain(sql, catalog, intent, *, question=''):
    get=lambda key,default=None:intent.get(key,default) if isinstance(intent,dict) else getattr(intent,key,default)
    domain=(get('query_scope',{}) or {}).get('employee_domain')
    if domain is None:
        return {'verified':True,'mode':'no_program_grounded_employee_domain'}

    def deny(message):raise SQLValidationError('客户负责人域：'+message)
    expected={'kind':'referenced_customer_support_reps','foreign_key':'customer.support_rep_id',
              'target':'employee.employee_id','source':'program:current_customer_ownership_domain'}
    if not isinstance(domain,dict) or any(domain.get(key)!=value for key,value in expected.items()):
        deny('缺少当前客户负责人域的程序权威关系，不能由模型自由声明替代。')
    if set(domain)-set(expected)-{'source_evidence'}:
        deny('负责人域包含当前证明器未支持的额外条件，不能静默丢弃。')
    evidence=domain.get('source_evidence')
    if not isinstance(evidence,str) or not evidence.strip():deny('负责人域缺少实际名词原文证据。')
    compact=lambda value:''.join(value.split())
    if question and compact(evidence) not in compact(question):deny('域证据不是当前真实问题中的连续原文。')
    if get('task_type')!='ranking' or get('rank_object')!='employee' or get('metric')!='customer_count':
        deny('当前有界证明仅支持按负责客户数对员工排名；其它指标不能冒充已验证。')
    try:
        employee=catalog.get_table('employee','public');customer=catalog.get_table('customer','public')
    except Exception as exc:deny('真实目录缺少员工或客户关系：'+type(exc).__name__)
    if employee.primary_key!=('employee_id',) or not {'employee_id'}<=employee.column_names or not {'support_rep_id','customer_id'}<=customer.column_names:
        deny('真实员工主键或客户外键列不符合当前域。')
    valid_fk=False
    for fk in customer.foreign_keys:
        if not isinstance(fk,dict):continue
        ref=fk.get('references') or {}
        if not isinstance(ref,dict):continue
        if (tuple(fk.get('columns') or ())==('support_rep_id',) and ref.get('table')=='employee'
                and (ref.get('schema') or 'public')=='public' and tuple(ref.get('columns') or ())==('employee_id',)):
            valid_fk=True
    if not valid_fk:deny('目录没有customer.support_rep_id到employee.employee_id的真实完整外键。')
    try:
        statements=parse(sql,read='postgres')
        if len(statements)!=1 or not isinstance(statements[0],exp.Select):deny('仅支持单条SELECT的有界负责人域证明。')
        if statements[0].args.get('with_') and statements[0].args['with_'].args.get('recursive'):
            deny('递归作用域不在当前证明范围内。')
        tree=_qualified(sql,catalog)
        all_scopes=list(traverse_scope(tree));active=_active_scopes(all_scopes)
    except SQLValidationError:raise
    except Exception as exc:deny('SQL无法建立真实目录作用域：'+type(exc).__name__)
    scopes=[scope for scope in all_scopes if scope in active]
    if not scopes:deny('没有实际消费的SELECT作用域。')
    for scope in scopes:
        if not isinstance(scope.expression,exp.Select):deny('集合运算可能引入未证明员工行，当前不支持。')
        group=scope.expression.args.get('group')
        if group is not None and (any(isinstance(item,(exp.Rollup,exp.Cube,exp.GroupingSets)) for item in group.walk()) or
                                  any(value not in (None,False,[]) for key,value in group.args.items() if key!='expressions')):
            deny('ROLLUP/CUBE/GROUPING SETS可能输出不对应真实员工的总计NULL行，当前不支持。')
        limit=scope.expression.args.get('limit')
        if limit is not None and isinstance(limit.expression,exp.Literal) and str(limit.expression.this)=='0':
            deny('LIMIT0空查询不能作为实际消费当前负责人域的证据。')
        if any((join.args.get('side') or '').upper() in {'RIGHT','FULL'} for join in scope.expression.args.get('joins') or []):
            deny('RIGHT/FULL连接可能补入空员工域，当前有界证明不支持。')

    def sources(scope):return {alias:source for alias,(_,source) in scope.selected_sources.items()}
    def strip(node):
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        return node
    def field(node,scope,depth=0):
        if depth>16:return None
        node=strip(node)
        if not isinstance(node,exp.Column):return None
        current=scope
        while current is not None:
            source=sources(current).get(node.table)
            if source is not None:break
            current=current.parent
        if current is None:return None
        if isinstance(source,exp.Table):
            return current,node.table,source.db or 'public',source.name,node.name
        if isinstance(source,Scope) and isinstance(source.expression,exp.Select):
            projection=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
            if projection is not None:return field(projection,source,depth+1)
        return None
    def atoms(node):return list(_mandatory_atoms(node).values())
    def inner_atoms(scope):
        result=atoms(scope.expression.args.get('where'))
        for join in scope.expression.args.get('joins') or []:
            if not join.args.get('side'):result.extend(atoms(join.args.get('on')))
        return result
    def null_rejects(node,alias):
        node=strip(node)
        if isinstance(node,exp.Is) and node.args.get('negate') and isinstance(node.expression,exp.Null):
            return isinstance(node.this,exp.Column) and node.this.table==alias
        if isinstance(node,exp.Not):
            inside=strip(node.this)
            if isinstance(inside,exp.Is) and not inside.args.get('negate') and isinstance(inside.expression,exp.Null):
                return isinstance(inside.this,exp.Column) and inside.this.table==alias
        if isinstance(node,(exp.EQ,exp.NEQ,exp.GT,exp.GTE,exp.LT,exp.LTE)):
            return any(isinstance(side,exp.Column) and side.table==alias for side in (node.left,node.right))
        return False
    def positive_count(node,alias):
        node=strip(node)
        if not isinstance(node,(exp.GT,exp.GTE,exp.LT,exp.LTE)):return False
        left,right,op=node.left,node.right,node.key
        if isinstance(right,exp.Count):left,right,op=right,left,{'lt':'gt','lte':'gte'}.get(op,op)
        if not isinstance(left,exp.Count) or not isinstance(right,exp.Literal) or right.is_string:return False
        allowed=(op=='gt' and str(right.this)=='0') or (op=='gte' and str(right.this)=='1')
        counted=left.this
        if isinstance(counted,exp.Distinct) and len(counted.expressions)==1:counted=counted.expressions[0]
        return allowed and isinstance(counted,exp.Column) and counted.table==alias
    def grouped_employee(scope):
        group=scope.expression.args.get('group')
        return group is not None and any((value:=field(item,scope)) is not None and value[2:]==('public','employee','employee_id') for item in group.expressions)
    def explicit_presence(scope,alias):
        return any(null_rejects(node,alias) for node in inner_atoms(scope)) or (grouped_employee(scope) and any(positive_count(node,alias) for node in atoms(scope.expression.args.get('having'))))
    def mandatory(scope):
        result=inner_atoms(scope)
        for join in scope.expression.args.get('joins') or []:
            if (join.args.get('side') or '').upper()=='LEFT' and explicit_presence(scope,join.this.alias_or_name):
                result.extend(atoms(join.args.get('on')))
        return result
    def constant_false(node):
        node=strip(node)
        if isinstance(node,exp.Null):return True
        if isinstance(node,exp.Boolean):return str(node.this).casefold()=='false'
        if isinstance(node,exp.EQ) and isinstance(node.left,exp.Literal) and isinstance(node.right,exp.Literal):
            if not node.left.is_string and not node.right.is_string:
                try:return Decimal(str(node.left.this))!=Decimal(str(node.right.this))
                except InvalidOperation:return False
        return False
    def pair(node,scope,target):
        if not isinstance(node,exp.EQ):return False
        left,right=field(node.left,scope),field(node.right,scope)
        if left is None or right is None:return False
        def owner(value):return value[:2]==target and value[2:]==('public','employee','employee_id')
        def customers(value):return value[2:]==('public','customer','support_rep_id')
        return (owner(left) and customers(right)) or (owner(right) and customers(left))
    by_expression={id(scope.expression):scope for scope in scopes}
    def ordinary_subquery(node):
        node=strip(node)
        if isinstance(node,exp.Subquery):node=node.this
        child=by_expression.get(id(node))
        if child is None or not isinstance(node,exp.Select):return None
        if node.args.get('group') or node.args.get('having') or node.args.get('qualify'):return None
        if any(isinstance(item,exp.AggFunc) for item in walk_in_scope(node)):return None
        # LIMIT0 is an artificial empty marker, not current-domain evidence.
        limit=node.args.get('limit')
        if limit is not None and isinstance(limit.expression,exp.Literal) and str(limit.expression.this)=='0':return None
        return child
    def exists_proof(node,scope,target):
        if isinstance(node,exp.Exists):
            child=ordinary_subquery(node.this)
            return child is not None and any(pair(atom,child,target) for atom in mandatory(child))
        if isinstance(node,exp.In):
            left=field(node.this,scope)
            if left is None or left[:2]!=target or left[2:]!=('public','employee','employee_id'):return False
            child=ordinary_subquery(node.args.get('query'))
            if child is None or len(child.expression.selects)!=1:return False
            selected=field(child.expression.selects[0],child)
            return selected is not None and selected[2:]==('public','customer','support_rep_id')
        return False

    owned={};physical=[]
    for index,scope in enumerate(scopes):
        if any(constant_false(node) for node in mandatory(scope)+atoms(scope.expression.args.get('having'))):
            deny('恒假条件不能把名义外键片段包装成实际负责人域查询。')
        for alias,source in sources(scope).items():
            if isinstance(source,exp.Table) and (source.db or 'public')=='public' and source.name=='employee':
                target=(scope,alias);physical.append(target)
                proofs=mandatory(scope)
                method='mandatory_actual_customer_FK' if any(pair(node,scope,target) for node in proofs) else 'mandatory_correlated_customer_exists_or_in' if any(exists_proof(node,scope,target) for node in proofs) else None
                if method is None:deny('实际员工来源未被真实客户外键INNER关系、必然WHERE或相关EXISTS/IN约束；不能把LEFT全体员工、SELECT中的等式或未使用CTE当证据。')
                owned[target]={'scope_index':index,'employee_alias':alias,'proof':method}
    if not physical:deny('真实结果没有消费任何员工物理来源，未用CTE或常量不能证明负责人。')

    def visible_owner(node,scope,depth=0):
        if depth>16:return False
        node=strip(node)
        if isinstance(node,exp.Column):
            source=sources(scope).get(node.table)
            if source is None:return False
            nullable=any((join.args.get('side') or '').upper()=='LEFT' and join.this.alias_or_name==node.table for join in scope.expression.args.get('joins') or [])
            if isinstance(source,exp.Table):return (scope,node.table) in owned and source.name=='employee' and node.name in {'employee_id','first_name','last_name'}
            if nullable and not explicit_presence(scope,node.table):return False
            if isinstance(source,Scope) and isinstance(source.expression,exp.Select):
                projection=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
                return projection is not None and visible_owner(projection,source,depth+1)
        # Name concatenation is an actual identity display; arbitrary CASE,
        # arithmetic, scalar subquery or COALESCE placeholder is not one.
        if isinstance(node,(exp.DPipe,exp.Concat)):
            children=list(node.expressions) if isinstance(node,exp.Concat) else [node.left,node.right]
            nonliteral=[child for child in children if not isinstance(child,exp.Literal)]
            return bool(nonliteral) and all(visible_owner(child,scope,depth+1) for child in nonliteral)
        return False
    root=next((scope for scope in scopes if scope.parent is None),None)
    if root is None or not any(visible_owner(item,root) for item in root.expression.selects):
        deny('最终输出没有沿实际非空行来源消费已证明的员工标识/姓名；正确CTE不能只藏在标量子查询或被LEFT补空。')
    return {'verified':True,'mode':'program_grounded_current_customer_support_employee_domain',
            'domain':dict(domain),'employee_sources':list(owned.values()),'output_consumes_owned_employee':True,
            'boundary':'Proves current ownership row domain only; existing metric/FK/filter/TopN/readonly guards remain required.'}
