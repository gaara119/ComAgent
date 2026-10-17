"""Reject consumed aggregate NULL fallbacks without real user authorization.

No business default is created. COUNT, NULLIF and CASE are not zero-fill
synonyms. Only the fields actually consumed by final projections/control
clauses are followed; unconsumed CTEs and unused derived columns do not count.
"""
from hashlib import sha256
import re
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes
from qa_agent.sql.validator import SQLValidationError


def _explicit_zero_authorization(kind):
    from qa_agent.context import current_context
    ctx=current_context()
    if ctx is None:return None
    def events(text,authority):
        result=[]
        for match in re.finditer(r'[^。；;\n!?！？]+',text):
            sentence=match[0]
            zero=bool(re.search(r'(?:填|补|返回|记为|显示|当作|按)\s*(?:为)?\s*(?:0|零)',sentence))
            if not zero:continue
            if re.search(r'例如|比如|示例|假设|文档中|原文|引用|[“”"「」『』]',sentence):continue
            negative=bool(re.search(r'不要|不得|不能|不允许|禁止|不补|不填|不是|不再|不需要|不需|不用|无需|无须|不必|没有必要|避免|取消|作废|不生效|不适用|保留\s*NULL',sentence,re.I))
            absent=bool(re.search(r'无(?:任何)?记录|没有(?:任何)?(?:符合[^，,]{0,12})?记录|无数据|没有数据|空集|(?:结果|金额|合计)为空|NULL',sentence,re.I))
            if not negative and not absent:continue
            scope=('count_only'if re.search(r'计数|COUNT|人数|客户数|发票张数',sentence,re.I)
                   else'money'if re.search(r'金额|销售额|总额|消费',sentence)
                   else'quantity'if re.search(r'数量|件数|总时长|毫秒|字节',sentence)
                   else'ratio'if re.search(r'占比|比例|百分比|分母',sentence)
                   else'all_aggregates')
            result.append({'authorized':not negative,'scope':scope,'evidence':sentence,
                'start':match.start(),'end':match.end(),'authority':authority,
                'text_sha256':sha256(text.encode('utf-8')).hexdigest(),
                'context_id':ctx.context_id,'context_version':ctx.version,
                'source':'program:actual_user_explicit_empty_zero'})
        return result
    current=events(ctx.current_user_message or'','current_user_message')
    relevant=[e for e in current if e['scope']in{kind,'all_aggregates'}]
    if not relevant:
        relevant=[e for e in events(ctx.text or'','user_brief')if e['scope']in{kind,'all_aggregates'}]
    if not relevant or any(not e['authorized']for e in relevant):return None
    return relevant[-1]


def validate_aggregate_null_fallback(sql,catalog,intent=None):
    tree=_qualified(sql,catalog)
    scopes=list(traverse_scope(tree));active=set(_active_scopes(scopes))
    by_expr={id(s.expression):s for s in scopes}
    root=next((s for s in scopes if s.parent is None),None)
    if root is None:return {'verified':True,'mode':'no_select_scope','checked_fallbacks':0}
    visited=set();control_seen=set();checks=[]
    def deny(message):raise SQLValidationError('聚合空值语义：'+message)
    def strip(node):
        while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
        return node
    def projected(column,owner):
        source=owner.sources.get(column.table)
        if source is None and not column.table:
            return next((p for p in owner.expression.selects if p.alias_or_name==column.name),None),owner
        if source is not None and not isinstance(source,exp.Table):
            return next((p for p in source.expression.selects if p.alias_or_name==column.name),None),source
        return None,None
    def aggregate_kinds(node,owner,seen=None,depth=0):
        if depth>24:deny('聚合值谱系超过有界深度，不能猜测NULL不可能。')
        seen=set()if seen is None else set(seen);node=strip(node)
        marker=(id(node),id(owner))
        if marker in seen:return set()
        seen.add(marker)
        if isinstance(node,(exp.Sum,exp.Avg)):
            # Money versus quantity is inferred from actual physical lineage,
            # never the display alias. Unknown sums require a generic explicit
            # authorization rather than borrowing a money-only rule.
            def physical_fields(value,target,trail=None):
                trail=set()if trail is None else set(trail)
                marker=(id(value),id(target))
                if marker in trail:return []
                trail.add(marker)
                if len(trail)>24:deny('真实度量字段谱系超过有界深度。')
                if isinstance(value,exp.Column):
                    parent,scope=projected(value,target)
                    if parent is not None:return physical_fields(parent,scope,trail)
                    physical=target.sources.get(value.table)
                    return[(physical.name,value.name)]if isinstance(physical,exp.Table)else[]
                return[pair for child in value.iter_expressions()for pair in physical_fields(child,target,trail)]
            physical=physical_fields(node,owner)
            money=any(pair in{('invoice','total'),('invoice_line','unit_price')}for pair in physical)
            quantity=physical and all(name in{'quantity','milliseconds','bytes'}for _,name in physical)
            return {'money'if money else'quantity'if quantity else'unknown_aggregate'}
        if isinstance(node,exp.Column):
            value,target=projected(node,owner)
            return aggregate_kinds(value,target,seen,depth+1)if value is not None else set()
        if isinstance(node,exp.Subquery):
            target=by_expr.get(id(node.this))
            return set().union(*(aggregate_kinds(p,target,seen,depth+1)for p in target.expression.selects))if target else set()
        return set().union(*(aggregate_kinds(c,owner,seen,depth+1)for c in node.iter_expressions()))
    def controls(owner):
        if owner in control_seen or owner not in active:return
        control_seen.add(owner)
        q=owner.expression
        for key in('where','having','qualify','order','group'):
            if q.args.get(key) is not None:visit(q.args[key],owner)
        for join in q.args.get('joins')or[]:
            if join.args.get('on')is not None:visit(join.args['on'],owner)
        # Every selected source affects the row stream, but only its control
        # clauses (not all of its unused projection expressions) are consumed.
        for _,source in owner.selected_sources.values():
            if not isinstance(source,exp.Table):controls(source)
    def visit(node,owner):
        if node is None:return
        node=strip(node);marker=(id(node),id(owner))
        if marker in visited:return
        visited.add(marker)
        if isinstance(node,exp.Column):
            value,target=projected(node,owner)
            if value is not None:controls(target);visit(value,target)
            return
        if isinstance(node,exp.Subquery):
            target=by_expr.get(id(node.this))
            if target:
                controls(target)
                for p in target.expression.selects:visit(p,target)
            return
        if isinstance(node,exp.Select):
            target=by_expr.get(id(node),owner);controls(target)
            for p in node.selects:visit(p,target)
            return
        if isinstance(node,exp.Coalesce):
            kinds=aggregate_kinds(node.this,owner)
            fallbacks=[strip(v)for v in node.expressions]
            if kinds and any(not isinstance(v,exp.Null)for v in fallbacks):
                if len(fallbacks)!=1 or not isinstance(fallbacks[0],exp.Literal)or fallbacks[0].is_string or fallbacks[0].this!='0':
                    deny('实际消费的SUM/AVG非NULL兜底未获支持，不能把NULL任意改成业务值。')
                authorizations=[_explicit_zero_authorization(kind)for kind in kinds]
                if not all(authorizations):deny('实际消费的SUM/AVG未经真实用户明确授权补0；空集应保留NULL。')
                checks.append({'fallback_sql':node.sql(dialect='postgres'),'authorizations':authorizations})
        # CTE declarations are intentionally skipped; actual columns above
        # resolve only the projections that participate in the result.
        for key,value in node.args.items():
            if key in{'with_','from_'}:continue
            if isinstance(value,exp.Expression):visit(value,owner)
            elif isinstance(value,list):
                for child in value:
                    if isinstance(child,exp.Expression):visit(child,owner)
    controls(root)
    if isinstance(root.expression,exp.Select):
        for projection in root.expression.selects:visit(projection,root)
    else:visit(root.expression,root)
    return {'verified':True,'mode':'consumed_aggregate_null_fallback','checked_fallbacks':len(checks),
        'authorized_fallbacks':checks,'reference_answers_consumed':False}
