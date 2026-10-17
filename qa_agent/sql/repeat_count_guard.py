"""Prove a requested global repeat-customer count is a consumed scalar count.

Thresholds use the existing registered repeat metric; document callers retain
their independent evidence/grain/period proof and pass its actual candidates.
No answer values, row-count guesses or reference SQL are consumed.
"""
import re
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes, _invoice_grain_is_preserved
from qa_agent.sql.validator import SQLValidationError


def validate_repeat_customer_count_output(sql,catalog,intent=None,*,question='',qualified_scope_sqls=None):
    get=lambda k,d=None:intent.get(k,d)if isinstance(intent,dict)else getattr(intent,k,d)
    explicit_count=bool(re.search(r'(?:复购|活跃)客户.{0,12}(?:多少|几位|人数|数量|客户数|数是多少)|(?:复购|活跃)客户数',question))
    if intent is not None:
        active=get('metric')=='repeat_customer_count'and not get('grouping')
    else:
        active=explicit_count and not re.search(r'各|每(?:个|位)|按.{0,18}(?:员工|国家|地区|分组)',question)
    if not active:return{'verified':True,'mode':'not_global_repeat_customer_count'}
    def deny(message):raise SQLValidationError('复购客户人数输出：'+message)
    tree=_qualified(sql,catalog);scopes=list(traverse_scope(tree));actual=_active_scopes(scopes)
    root=next(s for s in scopes if s.parent is None)

    def strip(n):
        while isinstance(n,(exp.Alias,exp.Paren)):n=n.this
        return n
    def resolve(n,owner,depth=0):
        if depth>20:deny('投影谱系超过有界深度。')
        n=strip(n)
        if isinstance(n,exp.Column):
            source=owner.sources.get(n.table)
            if source is not None and not isinstance(source,exp.Table):
                p=next((p for p in source.expression.selects if p.alias_or_name==n.name),None)
                if p is None:deny('派生字段没有实际投影。')
                return resolve(p,source,depth+1)
        return n,owner
    def field(n,owner):
        n,owner=resolve(n,owner)
        if not isinstance(n,exp.Column):return None
        source=owner.sources.get(n.table)
        return source.name+'.'+n.name if isinstance(source,exp.Table)and(source.db or'public')=='public'else None

    candidates=set()
    for s in actual:
        if qualified_scope_sqls is not None:
            if s.expression.sql(dialect='postgres')in qualified_scope_sqls:candidates.add(s)
            continue
        q=s.expression;group=q.args.get('group');having=q.args.get('having')
        if not group or not having:continue
        keys=[field(n,s)for n in group.expressions]
        if not any(k in{'invoice.customer_id','customer.customer_id'}for k in keys)or any(k not in{'invoice.customer_id','customer.customer_id','customer.support_rep_id'}for k in keys):continue
        h=strip(having.this)
        if not isinstance(h,(exp.GTE,exp.GT)):continue
        count=strip(h.left);threshold=strip(h.right)
        if not isinstance(count,exp.Count)or not isinstance(threshold,exp.Literal)or threshold.is_string:continue
        if(h.key,str(threshold.this))not in{('gte','2'),('gt','1')}:continue
        target=count.this;distinct=isinstance(target,exp.Distinct)
        if distinct:
            if len(target.expressions)!=1:continue
            target=target.expressions[0]
        if not(isinstance(target,exp.Star)or field(target,s)=='invoice.invoice_id'):continue
        if not distinct and not _invoice_grain_is_preserved(s,catalog):continue
        candidates.add(s)
    if not candidates:deny('缺少实际消费的客户粒度发票数至少2资格集合，不能用普通客户数。')

    def clean(q,owner,*,allow_root_limit=False):
        if any(q.args.get(k)for k in('where','group','having','qualify','distinct','offset'))or q.args.get('joins'):
            deny('最终人数层/资格透传层不能按客户再次分组、附加筛选、去重或连接产生多行。')
        limit=q.args.get('limit')
        if limit is not None and(not allow_root_limit or not isinstance(limit.expression,exp.Literal)or limit.expression.is_string or not str(limit.expression.this).isdigit()or int(limit.expression.this)<1):
            deny('只能保留最终标量人数正数展示上限，不能截取资格客户。')

    consumed=set()
    def qualified_rows(owner,seen=None):
        seen=set()if seen is None else set(seen)
        if id(owner)in seen:deny('资格行集出现循环。')
        seen.add(id(owner))
        if owner in candidates:
            consumed.add(owner);return
        clean(owner.expression,owner)
        sources=[s for _,s in owner.selected_sources.values()]
        if len(sources)!=1 or isinstance(sources[0],exp.Table):deny('COUNT没有唯一消费真实复购资格集合；无关CTE不能作证。')
        if any(not isinstance(strip(p),(exp.Column,exp.Literal))for p in owner.expression.selects):
            deny('资格透传投影含函数/集合扩展，不能推定一客户仍一行。')
        qualified_rows(sources[0],seen)

    if len(root.expression.selects)!=1:deny('问全局客户人数时须唯一标量计数，不能交付每客户一行或不相关列。')
    node,owner=resolve(root.expression.selects[0],root)
    if not isinstance(node,exp.Count):deny('最终结果不是实际资格客户COUNT，不能用每组1、常量、SUM发票数或窗口计数代替。')
    clean(owner.expression,owner,allow_root_limit=owner is root)
    sources=[s for _,s in owner.selected_sources.values()]
    if len(sources)!=1 or isinstance(sources[0],exp.Table):deny('最终COUNT必须消费真实客户资格行集，不能直接每客户GROUP返回1。')
    qualified_rows(sources[0])
    value=node.this
    if isinstance(value,exp.Distinct):
        if len(value.expressions)!=1:deny('人数DISTINCT必须唯一真实客户键。')
        value=value.expressions[0]
    if not isinstance(value,exp.Star)and field(value,owner)not in{'invoice.customer_id','customer.customer_id'}:
        deny('COUNT必须计资格行或真实非空客户键，不能数常量NULL/其它实体。')
    # Root aliases may transparently expose a true single-row aggregate. They
    # cannot filter or replicate it over a second source.
    cursor=root;seen=set()
    while cursor is not owner:
        if id(cursor)in seen:deny('标量透传出现循环。')
        seen.add(id(cursor));clean(cursor.expression,cursor,allow_root_limit=cursor is root)
        sources=[s for _,s in cursor.selected_sources.values()]
        if len(sources)!=1 or isinstance(sources[0],exp.Table):deny('最终人数不是单行聚合透传。')
        cursor=sources[0]
    return{'verified':True,'mode':'global_count_of_consumed_qualified_customer_rows',
           'qualified_scopes':[s.expression.sql(dialect='postgres')for s in consumed],
           'output_shape':'single_scalar_customer_count','threshold_source':'registered_repeat_customer_count_or_verified_document_dependency'}
