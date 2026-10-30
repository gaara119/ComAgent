"""Finite existing invoice-share default consumption, never a semantic gate."""
from datetime import date
from hashlib import sha256
import re

from sqlglot import exp
from sqlglot.optimizer.scope import Scope,build_scope
from qa_agent.sql.business_knowledge import business_knowledge
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.validator import SQLValidationError


def _un(node):
    while isinstance(node,(exp.Alias,exp.Paren)):
        node=node.this
    return node


def _closed_source(question):
    if not isinstance(question,str) or re.search(
            r'例如|比如|示例|假设|如果|不要|不用|无需|无须|不必|不是|不需要|不算|别算|[“”"\'‘’]',question):
        return None
    if re.search(r'明细|曲目|歌曲|流派|艺术家|人数|数量|张数|首数|份数|客户数|计数|平均|人均|同比|环比|增长',question):
        return None
    if not re.search(r'客户',question) or not re.search(r'花钱最多|消费(?:金额)?最高|消费最多|开票(?:金额|额)最高',question):
        return None
    # Only a bare share question is supported. Any named denominator, equation,
    # further instruction or comparison remains with its actual source owner.
    matches=list(re.finditer(r'占',question))
    if len(matches)!=1:
        return None
    share=matches[0]
    if not re.fullmatch(r'占(?:了)?(?:多大(?:的)?比例|多少(?:的)?比例|百分之几|百分之多少|比(?:例)?(?:是)?多少)[?？。\s]*',question[share.start():]):
        return None
    return {'question_sha256':sha256(question.encode()).hexdigest(),
            'share_quote':question[share.start():],'share_start':share.start(),
            'denominator_explicit':False}


def _registered_policy():
    knowledge=business_knowledge()
    rows=[x for x in (knowledge or {}).get('references',[])
          if x.get('source_id')=='project:existing_authorized_defaults']
    if len(rows)!=1:
        return None
    row=rows[0];policy=(row.get('authorized_defaults') or {}).get('invoice_revenue_share')
    if (not isinstance(policy,dict) or policy.get('denominator')!='all_invoices_same_period'
            or not {'detail_revenue','customer_count'} <= set(policy.get('exclude_metrics') or [])
            or not row.get('authorization_source') or not re.fullmatch(r'[a-f0-9]{64}',str(row.get('sha256','')))):
        return None
    return {'source_id':row['source_id'],'path':row['path'],'sha256':row['sha256'],
            'authorization_source':row['authorization_source'],'policy':policy}


def validate_s1_invoice_share_default(sql,catalog,source_question,*,enabled=False,brief='',user_history=()):
    """Reject only a known same-customer subset used as the default invoice D.

    No date/value/metric is selected from prose. The verified dates below come
    solely from the actual numerator SQL; this does not certify their meaning.
    Unknown SQL and any source denominator/body/history remain not_verified.
    """
    def no(reason):
        return {'status':'not_verified','verified':False,'reason':reason,
                'business_semantics_verified':False,'state_committed':False}
    if enabled is not True or not isinstance(brief,str) or brief.strip() or user_history:
        return no('disabled_or_actual_brief_history_present')
    source=_closed_source(source_question)
    if source is None or getattr(catalog,'database',None)!='chinook':
        return no('source_is_not_a_closed_bare_customer_invoice_winner_share')
    policy=_registered_policy()
    if policy is None:
        return no('existing_authorized_invoice_share_default_unavailable')
    try:
        tree=_qualified(sql,catalog);root=build_scope(tree)
        if not isinstance(tree,exp.Select) or root is None or len(root.selected_sources)!=1:
            return no('unsupported_final_scope')
        scopes={id(s.expression):s for s in root.traverse()}

        def resolve(node,scope,depth=0,path=()):
            node=_un(node)
            if depth>8:
                return None,scope,path
            path=(*path,scope)
            if isinstance(node,exp.Column):
                selected=scope.selected_sources.get(node.table)
                if selected and isinstance(selected[1],Scope):
                    child=selected[1]
                    if not isinstance(child.expression,exp.Select):return None,scope,path
                    matches=[p for p in child.expression.selects if p.alias_or_name==node.name]
                    if len(matches)==1:return resolve(matches[0],child,depth+1,path)
                    return None,scope,path
                if not node.table:
                    matches=[p for p in scope.expression.selects if p.alias_or_name==node.name]
                    if len(matches)==1 and _un(matches[0]).sql()!=node.sql():
                        return resolve(matches[0],scope,depth+1,path)
            return node,scope,path

        def direct_invoice_sum(node,scope):
            node=_un(node)
            if not isinstance(node,exp.Sum) or not isinstance(node.this,exp.Column):return None
            col=node.this;selected=scope.selected_sources.get(col.table)
            if not selected or not isinstance(selected[1],exp.Table):return None
            physical=selected[1]
            if (physical.db or 'public')!='public' or physical.name!='invoice' or col.name!='total':return None
            invoice=catalog.get_table('invoice','public')
            return col.table if 'total' in invoice.column_names else None

        def iso_literal(node):
            node=_un(node)
            if isinstance(node,exp.Cast) and node.to.sql().upper() in {'DATE','TIMESTAMP','TIMESTAMPTZ'}:
                node=_un(node.this)
            if not isinstance(node,exp.Literal) or not node.is_string:return None
            try:
                return node.this if date.fromisoformat(node.this).isoformat()==node.this else None
            except ValueError:return None

        def conditions(scope,invoice_alias,customer_alias=None):
            where=scope.expression.args.get('where')
            if where is None:return None
            parts=[]
            def split(node):
                node=_un(node)
                if isinstance(node,exp.And):split(node.left);split(node.right)
                else:parts.append(node)
            split(where.this)
            bounds={};restricted=[]
            for part in parts:
                if isinstance(part,(exp.GTE,exp.LT)) and isinstance(part.left,exp.Column):
                    col=part.left;value=iso_literal(part.right);key='gte' if isinstance(part,exp.GTE) else 'lt'
                    if (col.table,col.name)!=(invoice_alias,'invoice_date') or value is None or key in bounds:return None
                    bounds[key]=value
                elif customer_alias and isinstance(part,exp.EQ):
                    choices=[(a,b) for a,b in [(part.left,part.right),(part.right,part.left)]
                        if isinstance(a,exp.Column) and isinstance(b,exp.Literal)]
                    if len(choices)!=1:return None
                    col,value=choices[0]
                    if col.table!=customer_alias or col.name not in {'country','customer_id'}:return None
                    if (col.name=='country') is not value.is_string:return None
                    restricted.append({'column':f'public.customer.{col.name}','operator':'=','value':value.this})
                else:return None
            if set(bounds)!={'gte','lt'} or bounds['gte']>=bounds['lt']:return None
            return bounds,restricted

        def numerator_base(sum_node,scope):
            invoice_alias=direct_invoice_sum(sum_node,scope)
            q=scope.expression
            if invoice_alias is None or any(q.args.get(k) for k in ('distinct','having','qualify','limit','offset')):
                return None
            tables={a:s for a,(_,s) in scope.selected_sources.items()}
            if len(tables)!=2 or any(not isinstance(t,exp.Table) or (t.db or 'public')!='public' for t in tables.values()):return None
            customers=[a for a,t in tables.items() if t.name=='customer']
            if len(customers)!=1 or tables[invoice_alias].name!='invoice':return None
            c=customers[0];customer=catalog.get_table('customer','public');invoice=catalog.get_table('invoice','public')
            if customer.primary_key!=('customer_id',):return None
            if not any(f.get('columns')==['customer_id'] and (f.get('references') or {}).get('table')=='customer'
                and (f.get('references') or {}).get('schema','public')=='public'
                and (f.get('references') or {}).get('columns')==['customer_id'] for f in invoice.foreign_keys):return None
            joins=q.args.get('joins') or []
            if len(joins)!=1 or joins[0].side or joins[0].kind not in ('','INNER'):return None
            on=_un(joins[0].args.get('on'))
            if not isinstance(on,exp.EQ) or not all(isinstance(x,exp.Column) for x in (on.left,on.right)):return None
            if {(on.left.table,on.left.name),(on.right.table,on.right.name)}!={(invoice_alias,'customer_id'),(c,'customer_id')}:return None
            group=q.args.get('group')
            if group is None or any(group.args.get(k) for k in ('rollup','cube','grouping_sets')):return None
            if not group.expressions or any(not isinstance(x,exp.Column) or x.table!=c for x in group.expressions):return None
            if not any(x.name=='customer_id' for x in group.expressions):return None
            parsed=conditions(scope,invoice_alias,c)
            return (invoice_alias,*parsed) if parsed else None

        def ranked_one(scope,base,sum_node):
            q=scope.expression;limit=q.args.get('limit');order=q.args.get('order')
            if (limit is None or not isinstance(limit.expression,exp.Literal) or limit.expression.is_string
                    or limit.expression.this!='1' or q.args.get('offset') or order is None or not order.expressions):return False
            first=order.expressions[0]
            if first.args.get('desc') is not True:return False
            actual,owner,_=resolve(first.this,scope)
            return owner is base and actual is not None and actual==sum_node

        def quotient(node,scope):
            node,scope,_=resolve(node,scope)
            if isinstance(node,exp.Round):return quotient(node.this,scope)
            if isinstance(node,exp.Mul):
                for const,other in [(node.left,node.right),(node.right,node.left)]:
                    const=_un(const)
                    if isinstance(const,exp.Literal) and not const.is_string and const.this in {'100','100.0'}:
                        return quotient(other,scope)
            return (node,scope) if isinstance(node,exp.Div) else (None,scope)

        found=[(ratio,scope) for p in tree.selects for ratio,scope in [quotient(p,root)] if ratio is not None]
        if len(found)!=1:return no('not_one_consumed_ratio_projection')
        ratio,owner=found[0];n=_un(ratio.left)
        if isinstance(n,exp.Mul):
            choices=[other for const,other in [(n.left,n.right),(n.right,n.left)]
                if isinstance(_un(const),exp.Literal) and not _un(const).is_string and _un(const).this in {'100','100.0'}]
            if len(choices)!=1:return no('unknown_numerator_scaling')
            n=choices[0]
        n,base,n_path=resolve(n,owner)
        parsed=numerator_base(n,base)
        if parsed is None or not any(ranked_one(s,base,n) for s in n_path):
            return no('numerator_invoice_customer_PK_period_or_actual_Top1_unproved')
        invoice_alias,period,restricted=parsed
        d=_un(ratio.right)
        if isinstance(d,exp.Nullif):
            if not isinstance(d.expression,exp.Literal) or d.expression.this!='0':return no('unknown_denominator_null_policy')
            d=_un(d.this)
        d_scope=owner
        if isinstance(d,exp.Subquery):
            d_scope=scopes.get(id(d.this))
            if d_scope is None or len(d.this.selects)!=1:return no('unknown_scalar_denominator')
            d=d.this.selects[0]
        d,d_scope,_=resolve(d,d_scope)
        if isinstance(d,exp.Window):
            if any(d.args.get(k) for k in ('partition_by','order','spec')):return no('unknown_denominator_window')
            d=d.this
        if not isinstance(d,exp.Sum):return no('denominator_not_supported_SUM')
        q=d_scope.expression
        if (not isinstance(q,exp.Select) or any(q.args.get(k) for k in ('where','group','having','qualify','distinct','offset','limit'))
                or len(d_scope.selected_sources)!=1):
            # A direct physical full-invoice denominator has exactly two date
            # predicates; it is considered separately below, never repaired.
            alias=direct_invoice_sum(d,d_scope)
            full=conditions(d_scope,alias) if alias and len(d_scope.selected_sources)==1 else None
            if (full and full[0]==period and not full[1]
                    and not any(q.args.get(k) for k in ('group','having','qualify','distinct','offset','limit','joins'))):
                return {'status':'checked_existing_invoice_share_default_structure_only','verified':True,
                    'authorized_default':policy,'source':source,'actual_numerator_period':period,
                    'business_semantics_verified':False,'state_committed':False}
            return no('unknown_denominator_population_or_period')
        inner,den_base,den_path=resolve(d.this,d_scope)
        if den_base is not base or inner!=n:return no('denominator_is_not_the_same_customer_invoice_aggregate')
        limited=any(ranked_one(s,base,n) for s in den_path)
        if not restricted and not limited:return no('same_aggregate_not_proven_restricted')
        evidence={'authorized_default':policy,'source':source,'actual_numerator_period':period,
            'actual_customer_restrictions':restricted,'denominator_reuses_restricted_customer_amount':True,
            'denominator_reuses_Top1':limited,'business_semantics_verified':False,'state_committed':False}
        error=SQLValidationError(
            '现有invoice_revenue_share默认仅本题适用的发票金额份额：分母是同期间全体发票，'
            '不能复用已受国家、客户或TopN筛选的客户金额集合。请独立按实际分子已使用的半开期间 '
            f"[{period['gte']}, {period['lt']}) 聚合真实 public.invoice.total，"
            '分母不要带客户/国家/TopN限制；保留原winner、分子、用户期间和输出要求。'
            '此检查只消费已登记默认，不证明客户选择、年份或完整业务正确性，不新增默认或状态。')
        error.invoice_share_default_evidence=evidence
        raise error
    except SQLValidationError:
        raise
    except Exception as exc:
        return no('unsupported_catalog_or_SQL_shape:'+type(exc).__name__)
