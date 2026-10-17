"""Business wording from proved physical operands; never a second model rewrite."""
from decimal import Decimal
from sqlglot import exp, parse_one


METRICS={'invoice_revenue':'发票金额合计（每张发票只计算一次）',
         'detail_revenue':'销售明细金额合计（每笔成交单价乘以购买数量后加总）'}


def _conditions(proof):
    sql=proof.get('effective_filter_sql')
    if not sql:return []
    tree=parse_one(sql,read='postgres')
    sources={table.alias_or_name:table.name for table in tree.find_all(exp.Table)}
    result=[]
    def field(node):
        return sources.get(node.table,'')+'.'+node.name if isinstance(node,exp.Column) else None
    def visit(node):
        if node is None:return
        if isinstance(node,(exp.Where,exp.Paren)):visit(node.this);return
        if isinstance(node,exp.And):visit(node.left);visit(node.right);return
        target=field(node.this) if isinstance(node,exp.In) else field(node.left) if isinstance(node,exp.Binary) else None
        names={'invoice.billing_country':'账单国家','customer.country':'客户所在地国家',
            'genre.name':'曲风','artist.name':'艺术家','album.title':'专辑','track.name':'曲目'}
        if isinstance(node,exp.In) and target in names and node.expressions and all(isinstance(item,exp.Literal) and item.is_string for item in node.expressions):
            result.append(names[target]+'为'+ '、'.join(str(item.this) for item in node.expressions));return
        if target=='track.milliseconds' and isinstance(node,(exp.GT,exp.GTE,exp.LT,exp.LTE,exp.EQ)) and isinstance(node.right,exp.Literal):
            value=Decimal(node.right.this);minutes=value/Decimal(60000)
            wording={exp.GT:'超过',exp.GTE:'不少于',exp.LT:'少于',exp.LTE:'不超过',exp.EQ:'等于'}[type(node)]
            result.append('曲目时长'+wording+(f'{minutes:f}分钟' if minutes==minutes.to_integral_value() else f'{value:f}毫秒'));return
        if isinstance(node,exp.EQ) and target in names and isinstance(node.right,exp.Literal):
            result.append(names[target]+'为'+str(node.right.this));return
        if target=='invoice.invoice_date':return  # The separately proved period is rendered below.
        result.append('其它已确认的筛选条件')
    visit(tree.args.get('where'))
    return list(dict.fromkeys(result))


def describe_typed_ratio(proof):
    if proof.get('mode')!='typed_physical_ratio_operands' or not proof.get('proofs'):
        return None
    first=proof['proofs'][0]
    parts={}
    for role in ('numerator','denominator'):
        operand=first[role]
        if operand.get('metric') not in METRICS:return None
        filters=_conditions(operand)
        metric=METRICS[operand['metric']]
        if proof.get('ranking') and role=='numerator':metric='各曲风的'+metric
        parts[role]=('、'.join(filters)+'范围内的' if filters else '该期间全部相关记录的')+metric
    def period_text(period):
        return f"{period['start']}（含）至{period['end']}（不含）" if period.get('start') and period.get('end') else '当前已确认期间'
    left=first['numerator'].get('period') or {};right=first['denominator'].get('period') or {}
    times=(f'统计期间为{period_text(left)}' if left.get('start')==right.get('start') and left.get('end')==right.get('end')
           else f'分子期间为{period_text(left)}，分母期间为{period_text(right)}')
    return {'source':'program:proved_ratio_operands','text':f"计算口径：{times}。分子为{parts['numerator']}；分母为{parts['denominator']}。占比按分子除以分母计算。",
            'ranking':proof.get('ranking')}


def describe_verified_invoice_share(sql,catalog,bindings,context):
    from qa_agent.sql.ratio_guard import validate_invoice_share
    if context is None or not validate_invoice_share(sql,catalog,bindings,context):return None
    tree=parse_one(sql,read='postgres')
    division=next(tree.find_all(exp.Div))
    def un(node):
        while isinstance(node,(exp.Alias,exp.Paren,exp.Cast,exp.Round)):node=node.this
        return node
    def operand(node):
        node=un(node)
        if isinstance(node,exp.Mul):
            left,right=un(node.left),un(node.right)
            if isinstance(left,exp.Literal) and not left.is_string and Decimal(left.this) in (Decimal(1),Decimal(100)):
                node=right
            elif isinstance(right,exp.Literal) and not right.is_string and Decimal(right.this) in (Decimal(1),Decimal(100)):
                node=left
            else:
                return None
        if isinstance(node,exp.Nullif):node=un(node.this)
        condition=None
        if isinstance(node,exp.Sum) and isinstance(un(node.this),exp.Case):
            condition=un(node.this).args['ifs'][0].this
        effective=tree.copy();effective.set('expressions',[exp.Literal.number(1)])
        current=effective.args.get('where')
        if condition is not None:effective.set('where',exp.Where(this=exp.and_(current.this.copy(),condition.copy()) if current else condition.copy()))
        return {'metric':'invoice_revenue','period':(context.get('time_scope') or {}).get('current') or {},
                'effective_filter_sql':effective.sql(dialect='postgres')}
    numerator,denominator=operand(division.left),operand(division.right)
    if numerator is None or denominator is None:return None
    result=describe_typed_ratio({'mode':'typed_physical_ratio_operands','proofs':[{
        'numerator':numerator,'denominator':denominator}]})
    result['source']='program:proved_invoice_share'
    return result


def describe_customer_winner_ratio(semantic_proof,analysis):
    """Render only an actual winning-customer physical proof already passed."""
    accepted={'customer_amount_winner_invoice_amount_ratio',
              'customer_invoice_count_winner_invoice_amount_ratio'}
    checked=next((item for item in (semantic_proof or {}).get('checks',[])
        if isinstance(item,dict) and item.get('mode') in accepted and item.get('verified')
        and item.get('customer_key_dependency') and item.get('invoice_grain_preserved')
        and item.get('denominator_unchanged') and item.get('actual_customer_identity_and_amount_projected')),None)
    if checked is None:return None
    get=lambda key:analysis.get(key) if isinstance(analysis,dict) else getattr(analysis,key,None)
    period=(get('time_scope') or {}).get('current') or {}
    times=(f"{period['start']}（含）至{period['end']}（不含）" if period.get('start') and period.get('end')
           else '已确认的统计期间')
    criterion='发票张数' if checked['rank_metric']=='invoice_count' else '发票消费金额'
    return {'source':'program:proved_customer_winner_ratio','ranking':None,
        'text':f'计算口径：在{times}，先按每位客户的{criterion}选出第一名；分子为该客户在该期间的发票金额合计，分母为该期间全部发票金额合计，每张发票只计算一次。占比按分子除以分母计算。'}
