"""Source-explicit Top-N cohort sum, distinct from each member's share.

Only the consumed SQL structure is checked. No metric, default, entity value,
reference query, state or execution authorization is inferred here.
"""
from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.optimizer.scope import Scope, build_scope, traverse_scope, walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


def validate_s1_cohort_sum(sql, catalog, source_question, *, enabled=False):
    def no(reason):
        return {'status':'not_verified','reason':reason,
                'business_semantics_verified':False,'state_committed':False}
    if enabled is not True or not isinstance(source_question,str):
        return no('disabled_or_missing_actual_source')
    if re.search(r'例如|比如|示例|举例|例句|假设|如果|不需要|不要|不用|无需|无须|不必|不算|不求|不是|[“”"\'‘’]',source_question):
        return no('source_contains_negation_example_or_quote')
    choices=list(re.finditer(r'前\s*(\d+)\s*(?:位|名|个|项|张|支)',source_question))
    combined=re.search(r'(?:他们|它们|这些|这几(?:位|名|个|项|张|支))的?合计[^。；;!?！？]{0,90}占',source_question)
    if len(choices)!=1 or combined is None or choices[0].end()>combined.start():
        return no('not_one_source_explicit_TopN_collective_share')
    count=int(choices[0][1])
    if not 1<=count<=1000:
        return no('unsupported_TopN')
    try:
        tree=_qualified(sql,catalog);root=build_scope(tree)
        if root is None or not isinstance(tree,exp.Select):
            return no('unsupported_root')
        scopes={id(s.expression):s for s in traverse_scope(tree)}
        def un(node):
            while isinstance(node,(exp.Alias,exp.Paren)):
                node=node.this
            return node
        def projection(source,name):
            if not isinstance(source.expression,exp.Select):return None
            matches=[p for p in source.expression.selects if p.alias_or_name==name]
            return matches[0]if len(matches)==1 else None
        def resolve(node,scope,depth=0):
            if depth>20:return None,scope
            node=un(node)
            if isinstance(node,exp.Column):
                source=scope.sources.get(node.table)
                if isinstance(source,Scope):
                    value=projection(source,node.name)
                    return resolve(value,source,depth+1)if value is not None else(None,scope)
            return node,scope
        def ranked(scope):
            q=scope.expression
            limit=q.args.get('limit')
            return (isinstance(q,exp.Select) and q.args.get('order') is not None
                and q.args.get('offset') is None and limit is not None
                and isinstance(limit.expression,exp.Literal) and not limit.expression.is_string
                and str(limit.expression.this)==str(count))
        def ratio(node,scope,depth=0):
            node,scope=resolve(node,scope,depth)
            if isinstance(node,exp.Round):return ratio(node.this,scope,depth+1)
            if isinstance(node,exp.Div):return node,scope
            if isinstance(node,exp.Mul):
                for constant,other in ((node.left,node.right),(node.right,node.left)):
                    literal=un(constant)
                    if isinstance(literal,exp.Literal) and not literal.is_string and literal.this in {'100','100.0'}:
                        return ratio(other,scope,depth+1)
            return None,scope
        def one_row(source):
            if not isinstance(source,Scope) or not isinstance(source.expression,exp.Select):return False
            q=source.expression
            if any(q.args.get(k) for k in ('group','having','qualify','limit','offset','distinct')):return False
            nodes=[n for p in q.selects for n in walk_in_scope(p)]
            if any(isinstance(n,exp.Window) for n in nodes):return False
            if any(isinstance(n,exp.AggFunc) for n in nodes):return True
            return not source.selected_sources and q.args.get('where') is None
        def sum_population(owner,cohort):
            # A scalar aggregate or a global SUM window must consume exactly
            # one selected cohort instance, not a GROUP BY member or fanout.
            q=owner.expression
            if any(q.args.get(k) for k in ('group','where','having','qualify','distinct','limit','offset')):return False
            sources=[value for _,value in owner.selected_sources.values()]
            if sum(source is cohort for source in sources)!=1:return False
            if any(source is not cohort and not one_row(source) for source in sources):return False
            return all(join.kind=='CROSS' and join.side=='' and join.args.get('on') is None
                       for join in q.args.get('joins') or [])
        proofs=[]
        for output in tree.selects:
            quotient,owner=ratio(output,root)
            if quotient is None:continue
            paths=[];unknown=[]
            def walk(node,scope,aggregated=False,crossed=False,depth=0,seen=frozenset(),sum_scope=None):
                if depth>24:unknown.append('depth');return
                node=un(node)
                if node is None:unknown.append('missing');return
                if isinstance(node,exp.Subquery):
                    child=scopes.get(id(node.this))
                    if child is None or len(node.this.selects)!=1:unknown.append('subquery');return
                    return walk(node.this.selects[0],child,aggregated,crossed,depth+1,seen,sum_scope)
                if isinstance(node,exp.Window):
                    if (not isinstance(node.this,exp.Sum) or any(node.args.get(k)
                            for k in ('partition_by','order','spec'))):
                        unknown.append('window');return
                    return walk(node.this,scope,aggregated,crossed,depth+1,seen,sum_scope)
                if isinstance(node,exp.Sum):
                    if isinstance(node.this,exp.Distinct):unknown.append('distinct_sum');return
                    if not crossed and aggregated:unknown.append('nested_sum');return
                    return walk(node.this,scope,aggregated or not crossed,crossed,depth+1,seen,
                                scope if not crossed else sum_scope)
                if isinstance(node,exp.Column):
                    child=scope.sources.get(node.table)
                    if isinstance(child,Scope):
                        marker=(id(child),node.name)
                        if marker in seen:unknown.append('cycle');return
                        value=projection(child,node.name)
                        if value is None:unknown.append('column');return
                        if ranked(child) and not crossed:
                            if aggregated and (sum_scope is not scope or not sum_population(scope,child)):
                                unknown.append('unproved_complete_cohort_sum_population');return
                            paths.append({'scope_SQL_sha256':sha256(child.expression.sql(dialect='postgres').encode()).hexdigest(),
                                'summed_after_TopN':aggregated,'TopN':count})
                            crossed=True
                        return walk(value,child,aggregated,crossed,depth+1,seen|{marker},sum_scope)
                    return  # A physical field is not an additional cohort proof.
                if isinstance(node,exp.Mul) and not aggregated and not crossed:
                    for constant,other in ((node.left,node.right),(node.right,node.left)):
                        literal=un(constant)
                        if isinstance(literal,exp.Literal) and not literal.is_string and literal.this in {'100','100.0'}:
                            return walk(other,scope,aggregated,crossed,depth+1,seen,sum_scope)
                if isinstance(node,(exp.Mul,exp.Add,exp.Sub,exp.Div)):
                    unknown.append('unproved_numerator_arithmetic');return
                if not isinstance(node,(exp.Literal,exp.Null)):
                    unknown.append(type(node).__name__)
            walk(quotient.left,owner)
            if not paths or unknown:continue
            if len({p['scope_SQL_sha256']for p in paths})!=1:continue
            if all(p['summed_after_TopN']for p in paths):
                proofs.extend(paths)
            elif not any(p['summed_after_TopN']for p in paths):
                error=SQLValidationError('①原问明确要求前N项合计的份额，当前最终分子却直接使用每个入选对象各自的指标。'
                    '请先保留实际排名指标和稳定TopN集合，再对入选集合做外层SUM或全集合SUM(...) OVER()形成一个合计分子；'
                    '分母仍按原问自己的全体范围，不能用逐人/逐项比例冒充合计。原问要求的名单和每项指标仍须保留，'
                    '不能改指标、对象、期间、筛选、单位或NULL，也不在最终LIMIT之后才尝试合计。')
                error.source_cohort_evidence={'source_sha256':sha256(source_question.encode()).hexdigest(),
                    'TopN_quote':choices[0].group(),'collective_quote':combined.group(),
                    'actual_numerator_paths':paths,'business_semantics_verified':False}
                raise error
        return ({'status':'checked_cohort_sum_structure_only','TopN':count,'paths':proofs,
            'business_semantics_verified':False,'state_committed':False}if proofs else no('no_supported_consumed_TopN_cohort_sum_proof'))
    except SQLValidationError:
        raise
    except (ValueError,TypeError,KeyError,AttributeError):
        return no('unsupported_SQL_lineage')
