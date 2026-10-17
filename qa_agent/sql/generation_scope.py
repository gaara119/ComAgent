"""Keep SQL subtask claims separate from explicitly delegated document facts."""
from __future__ import annotations
import re
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope

_REFUSAL=re.compile(r'(?:无法|不能|不支持)(?:执行|查询|生成(?:SQL|查询|针对)|访问)|目标表.*不在.*目录',re.I)
_DOCUMENT_TOPICS=('成立','组建','音乐风格','名人堂')
_SQL_SUBJECTS=('专辑','曲目','客户','发票','销售额','消费金额','购买数量','总时长','存储空间')

def document_scope_disclaimer(explanation,question,context):
    """A narrow exception for an actual separate document-step topic only.

    It never authorizes unknown tables, unsafe SQL, missing measures or a
    refusal to perform the current SQL task. The full SQL guards still run.
    """
    if not isinstance(context,dict)or context.get('kind')!='composed':return False
    step=context.get('sql_step')or{}
    if step.get('question')!=question or not step.get('step_id'):return False
    original=context.get('original_question')or''
    delegated=context.get('delegated_document_steps')or[]
    topics={topic for topic in _DOCUMENT_TOPICS if topic in original and topic not in question
        and any(isinstance(item,dict)and item.get('step_id')!=step['step_id']
                and topic in str(item.get('question')or'')for item in delegated)}
    if not topics:return False
    clauses=[part for part in re.split(r'[。；;\n]+',explanation)if _REFUSAL.search(part)]
    if not clauses:return False
    for clause in clauses:
        if not any(topic in clause for topic in topics):return False
        if any(subject in question and subject in clause for subject in _SQL_SUBJECTS):return False
        # A scoped fact disclaimer cannot hide a second unscoped SQL refusal.
        if len(_REFUSAL.findall(clause))!=1:return False
    return True

def reject_unrequested_null_projection(expression,context):
    """Missing document facts cannot be fabricated as database NULL columns."""
    if not isinstance(context,dict)or context.get('kind')!='composed':return
    original=str(context.get('original_question')or'')
    explicit=bool(re.search(r'(?:返回|输出|显示|添加|增加).{0,10}(?:NULL(?:列)?|空列|空值列)',original,re.I))
    if explicit and not re.search(r'不要|禁止|不得|不允许',original):return
    scopes=list(traverse_scope(expression))
    by_expression={id(scope.expression):scope for scope in scopes}

    def projections(scope):
        names=scope.outer_columns or []
        return [(names[index] if index<len(names) else item.alias_or_name,item)
                for index,item in enumerate(scope.expression.selects)]

    def is_placeholder(node,scope,seen):
        while isinstance(node,(exp.Alias,exp.Paren,exp.Cast)):node=node.this
        if isinstance(node,exp.Null):return True
        if len(seen)>32 or (id(node),id(scope)) in seen:return False
        seen=seen|{(id(node),id(scope))}
        if isinstance(node,exp.Subquery):
            child=by_expression.get(id(node.this))
            return bool(child and len(child.expression.selects)==1
                        and is_placeholder(child.expression.selects[0],child,seen))
        if isinstance(node,exp.Column):
            sources={alias:source for alias,(_,source) in scope.selected_sources.items()}
            candidates=[]
            for alias,source in sources.items():
                if node.table and node.table!=alias:continue
                if not isinstance(source,Scope):continue
                candidates.extend((source,item)for name,item in projections(source)if name==node.name)
            # A physical nullable field is not a fabricated constant. Ambiguous
            # unqualified references remain the catalog validator's concern.
            if len(candidates)==1:
                child,item=candidates[0]
                return is_placeholder(item,child,seen)
            if not candidates and not node.is_star:
                # A downstream named column can flow through SELECT * in an
                # intermediate CTE; follow only selected derived sources.
                return any(is_placeholder(exp.column(node.name,table=(getattr(star,'table','') or None)),source,seen)
                           for alias,source in sources.items()
                           if (not node.table or alias==node.table) and isinstance(source,Scope)
                           for _,star in projections(source)
                           if isinstance(star,exp.Star) or isinstance(star,exp.Column) and star.is_star)
            if node.is_star:
                return any(is_placeholder(item,source,seen)
                           for alias,source in sources.items()
                           if (not node.table or alias==node.table) and isinstance(source,Scope)
                           for _,item in projections(source))
        if isinstance(node,exp.Star):
            return any(is_placeholder(item,source,seen)
                       for _,source in scope.selected_sources.values()if isinstance(source,Scope)
                       for _,item in projections(source))
        return False

    root=by_expression.get(id(expression))
    if root is None:return
    for projection in expression.selects:
        if is_placeholder(projection,root,set()):
            from qa_agent.sql.validator import SQLValidationError
            raise SQLValidationError('SQL子任务不得用常量NULL列冒充数据库缺失事实；已分配给文档的事实须由对应文档步骤回答。')
