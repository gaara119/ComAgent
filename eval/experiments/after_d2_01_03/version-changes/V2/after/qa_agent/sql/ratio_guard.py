"""Prove local customer-country invoice numerator without shrinking denominator.

This supports a deliberately small SQL grammar and refuses other customer
invoice ratios instead of inviting repair to put the numerator in global WHERE.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import re

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope
from sqlglot.schema import MappingSchema

from qa_agent.sql.validator import SQLValidationError
from qa_agent.sql.catalog import CatalogError


def verified_country_binding_surfaces(index, bindings):
    """Re-use actual loaded index provenance, never enable pending candidates.

    Alias surfaces are taken only from the same real value/column and the
    binding's exact alias evidence reference. Candidate-only/pending relations
    never become proof of an automatic synonym. Canonical values remain valid.
    """
    result=[]
    for binding in bindings:
        if binding.get('column')!='customer.country':continue
        value=binding.get('value');ref=binding.get('evidence_ref')
        surfaces=[str(value)] if value is not None else []
        for record in getattr(index,'records',[]) if index is not None else []:
            if record.column!=binding['column'] or record.standard_value!=value:continue
            if (record.kind=='standard' and record.surface==record.standard_value or
                record.kind=='alias' and record.alias_id and record.alias_id==ref):
                surfaces.append(record.surface)
        result.append({'column':binding['column'],'value':value,'surfaces':list(dict.fromkeys(surfaces))})
    return result


def _deny(reason):
    raise SQLValidationError("客户国家比例作用域未获证明：" + reason +
                             "；修复仅可调整技术等价SQL，不能把分子国家加到全局WHERE或改变分母范围。")


def _unparen(node):
    while isinstance(node, (exp.Paren, exp.Alias)):
        node = node.this
    return node


def _number(node, value):
    node=_unparen(node)
    if not isinstance(node,exp.Literal) or node.is_string:
        return False
    try:return Decimal(str(node.this)) == Decimal(value)
    except InvalidOperation:return False


def _same_period_all_invoice_text(text, start, end):
    """Recognize explicit whole-year/same-period global denominator, no extras.

    This intentionally rejects unrecognized qualifiers, countries, payment state
    or a differently scoped period rather than inventing a business definition.
    """
    text=str(text or '').strip()
    if not text:return False
    whole_year=start.endswith('-01-01') and end==f'{int(start[:4])+1:04d}-01-01'
    same_tokens=('同期','同年','同一期间','相同期间','相同时期','same period','same year')
    same=any(word in text.casefold() for word in same_tokens)
    years=re.findall(r'(?<!\d)(\d{4})\s*年',text)
    if years:
        if not whole_year or set(years)!={start[:4]}:return False
        same=True
    if not same:return False
    cleaned=text.casefold()
    for token in same_tokens:cleaned=cleaned.replace(token,'')
    cleaned=re.sub(r'(?<!\d)\d{4}\s*年','',cleaned)
    cleaned=re.sub(r'[\s。，？！?!.：:]','',cleaned)
    cleaned=re.sub(r'^(?:分母(?:就)?(?:用|是|为)|用|占|以)','',cleaned)
    # No open-ended .+ means "all France invoices" is not admitted as global.
    return bool(re.fullmatch(r'(?:所有|全部|全库|全球)(?:的)?(?:发票)(?:的)?(?:总)?(?:销售额|金额|收入|总额)',cleaned)) or bool(
        re.fullmatch(r'(?:all|global)invoices?(?:revenue|amount|total)',cleaned))


def _trusted_denominator(context,start,end):
    denominator=str(context.get('denominator') or '')
    if not _same_period_all_invoice_text(denominator,start,end):
        _deny('当前分母并非明确全部发票同期间金额')
    resolutions=context.get('confirmed_resolutions') or []
    setters=[]
    for resolution in resolutions:
        for patch in resolution.get('patches',[]):
            if patch.get('path')=='denominator' and patch.get('op')=='set':
                setters.append((resolution,patch))
    if setters:
        resolution,patch=setters[-1]
        message=str(resolution.get('message') or '')
        evidence=str(patch.get('evidence') or '')
        if (patch.get('value')!=context.get('denominator') or not evidence or evidence not in message or
            not _same_period_all_invoice_text(evidence,start,end)):
            _deny('最近分母补丁原文、当前值或期间不一致，历史全部口径不能代替当前确认')
        return
    question=str(context.get('question') or '')
    marker=re.search(r'占|分母|比例|比重|share of',question,re.I)
    tail=question[marker.end():] if marker else ''
    # A numerator date alone does not establish denominator scope/period.
    tail=re.sub(r'(?:是多少|多少|的比例|比例|比重)$','',tail.strip('？?。 .'))
    if not _same_period_all_invoice_text(tail,start,end):
        _deny('原题没有证明同期间全部发票分母，不能相信模型孤立描述')


def validate_customer_invoice_ratio_binding(sql,catalog,bindings,context):
    """Return false only outside the candidate class; inside it prove or raise."""
    if context.get('task_type')!='ratio' or not any(b.get('column')=='customer.country' for b in bindings):
        return False
    if len(bindings)!=1 or bindings[0].get('operator')!='=':
        _deny('仅支持唯一customer.country等值分子，禁止忽略其它条件')
    country=str(bindings[0].get('value') or '')
    current=(context.get('time_scope') or {}).get('current') or {}
    start,end=str(current.get('start') or ''),str(current.get('end') or '')
    try:
        if date.fromisoformat(start)>=date.fromisoformat(end):raise ValueError()
    except ValueError:_deny('当前期间无效或缺失')
    _trusted_denominator(context,start,end)
    numerator=str(context.get('numerator') or '')
    source_texts=[str(context.get('question') or '')]
    numerator_setters=[(r,p) for r in context.get('confirmed_resolutions') or [] for p in r.get('patches',[])
                       if p.get('path')=='numerator' and p.get('op')=='set']
    if numerator_setters:
        resolution,patch=numerator_setters[-1]
        message=str(resolution.get('message') or '')
        evidence=str(patch.get('evidence') or '')
        if patch.get('value')!=numerator or not evidence or evidence not in message:
            _deny('最新分子补丁与当前值/真实原文不一致')
        source_texts=[message]
    surfaces=[country]
    for item in context.get('verified_binding_surfaces') or []:
        if item.get('column')=='customer.country' and item.get('value')==country:
            surfaces.extend(str(s) for s in item.get('surfaces',[]) if s)
    source_scope=any(word in numerator for word in ('居住客户','客户所在地','客户所在国','customer.country','resident'))
    if (not numerator or not source_scope or not any(numerator in text for text in source_texts) or
        not any(surface.casefold() in numerator.casefold() for surface in surfaces if surface)):
        _deny('分子客户归属没有实际用户原文证据')
    if context.get('region_scope') not in {None,'customer.country'}:
        _deny('已确认地区归属与客户分子冲突')
    try:
        invoice=catalog.get_table('invoice','public');customer=catalog.get_table('customer','public')
    except CatalogError:_deny('目录缺少真实invoice/customer来源')
    fk_ok=any(fk.get('columns')==['customer_id'] and fk.get('references',{}).get('schema')=='public' and
              fk.get('references',{}).get('table')=='customer' and fk.get('references',{}).get('columns')==['customer_id']
              for fk in invoice.foreign_keys)
    fk_column=next((c for c in invoice.columns if c.name=='customer_id'),None)
    if customer.primary_key!=('customer_id',) or not fk_ok or fk_column is None or fk_column.nullable:
        _deny('目录未证明唯一customer主键、真实invoice外键及非NULL关联')
    expression=normalize_identifiers(sqlglot.parse_one(sql,read='postgres'),dialect='postgres')
    try:
        checked=qualify(expression,dialect='postgres',db='public',
                        schema=MappingSchema(catalog.sqlglot_schema(),dialect='postgres',normalize=False),
                        allow_partial_qualification=False,validate_qualify_columns=True)
    except Exception as exc:
        raise SQLValidationError('客户国家比例无法建立真实字段作用域；不允许改变分母修复。') from exc
    scopes=list(traverse_scope(checked))
    if (len(scopes)!=1 or not isinstance(checked,exp.Select) or len(checked.expressions)!=1 or
        any(checked.args.get(key) for key in ('with_','group','having','distinct','qualify','offset','order')) or
        any(isinstance(n,(exp.Window,exp.Subquery)) for n in checked.walk())):
        _deny('仅支持单SELECT、单比例列、无分组/子查询/窗口')
    sources={alias:source for alias,(_,source) in scopes[0].selected_sources.items()}
    if (len(sources)!=2 or sorted(s.name for s in sources.values() if isinstance(s,exp.Table))!=['customer','invoice'] or
        any(not isinstance(s,exp.Table) or s.db!='public' for s in sources.values())):
        _deny('invoice/customer各只能真实扫描一次')

    def column(node,table,name):
        node=_unparen(node)
        source=sources.get(node.table) if isinstance(node,exp.Column) else None
        return isinstance(source,exp.Table) and source.name==table and node.name==name

    def total_sum(node):
        node=_unparen(node)
        return isinstance(node,exp.Sum) and column(node.this,'invoice','total')

    joins=checked.args.get('joins') or []
    from_table=(checked.args.get('from_') or checked.args.get('from')).this
    if (len(joins)!=1 or not isinstance(from_table,exp.Table) or from_table.name!='invoice' or
        not isinstance(joins[0].this,exp.Table) or joins[0].this.name!='customer' or
        joins[0].args.get('side') or joins[0].args.get('kind') not in {None,'','INNER'} or joins[0].args.get('using')):
        _deny('仅支持invoice INNER JOIN customer的真实外键关联')
    on=_unparen(joins[0].args.get('on'))
    if not isinstance(on,exp.EQ) or not any(column(a,'invoice','customer_id') and column(b,'customer','customer_id') for a,b in ((on.left,on.right),(on.right,on.left))):
        _deny('关联必须为invoice.customer_id=customer.customer_id，无其它JOIN条件')

    def date_literal(node):
        if isinstance(node,exp.Cast):
            if node.to.this not in {exp.DataType.Type.DATE,exp.DataType.Type.TIMESTAMP}:return None
            node=node.this
        if not isinstance(node,exp.Literal) or not node.is_string:return None
        text=str(node.this)
        return text[:10] if re.fullmatch(r'\d{4}-\d{2}-\d{2}(?: 00:00:00)?',text) else None

    def dates(node):
        node=_unparen(node.this if isinstance(node,exp.Where) else node)
        if isinstance(node,exp.And):return dates(node.left)|dates(node.right)
        found=None
        if isinstance(node,(exp.GTE,exp.LT)) and column(node.left,'invoice','invoice_date'):
            found=('>=' if isinstance(node,exp.GTE) else '<',date_literal(node.right))
        elif isinstance(node,(exp.LTE,exp.GT)) and column(node.right,'invoice','invoice_date'):
            found=('>=' if isinstance(node,exp.LTE) else '<',date_literal(node.left))
        if found not in {('>=',start),('<',end)}:_deny('全库分母WHERE只能是已确认期间两边界，不能添加国家或额外限制')
        return {found}
    if dates(checked.args.get('where'))!={('>=',start),('<',end)}:_deny('必须保留两个同期间边界')

    projected=_unparen(checked.expressions[0])
    protected=False
    if isinstance(projected,exp.Case):
        if len(projected.args.get('ifs') or [])!=1:_deny('比例零分母CASE只允许一个保护分支')
        branch=projected.args['ifs'][0]
        if not isinstance(_unparen(branch.args.get('true')),exp.Null):_deny('零分母必须返回NULL')
        def zero_guard(node):
            node=_unparen(node)
            if isinstance(node,exp.Or):return zero_guard(node.left) and zero_guard(node.right)
            if isinstance(node,exp.EQ):return any(total_sum(a) and _number(b,'0') for a,b in ((node.left,node.right),(node.right,node.left)))
            if isinstance(node,exp.Is):return total_sum(node.this) and isinstance(node.expression,exp.Null)
            return False
        guard=branch.this
        if not zero_guard(guard) or not any(isinstance(n,exp.EQ) and any(total_sum(a) and _number(b,'0') for a,b in ((n.left,n.right),(n.right,n.left))) for n in guard.walk()):
            _deny('外层CASE必须证明同一SUM(total)等于0时保护，不能只防NULL')
        protected=True;projected=_unparen(projected.args.get('default'))
    if isinstance(projected,exp.Round):
        decimals=projected.args.get('decimals')
        if decimals is not None and not any(_number(decimals,str(i)) for i in range(13)):_deny('ROUND只允许明确0至12位展示精度')
        projected=_unparen(projected.this)
    if not isinstance(projected,exp.Div):_deny('必须为条件SUM与SUM(total)的比例')
    num,den=_unparen(projected.left),_unparen(projected.right)
    if isinstance(num,exp.Mul):
        if _number(num.left,'100'):num=_unparen(num.right)
        elif _number(num.right,'100'):num=_unparen(num.left)
        else:_deny('只允许未缩放比例或明确百分比100倍展示')
    if isinstance(den,exp.Nullif):
        if not total_sum(den.this) or not _number(den.expression,'0'):_deny('NULLIF必须保护SUM(invoice.total)的0分母')
    elif not total_sum(den) or not protected:_deny('分母必须无条件SUM(total)并有防零保护')
    if not isinstance(num,exp.Sum) or not isinstance(_unparen(num.this),exp.Case):_deny('分子必须条件SUM发票金额')
    case=_unparen(num.this)
    if len(case.args.get('ifs') or [])!=1:_deny('分子只允许一个已确认国家分支')
    default=case.args.get('default')
    if default is not None and not isinstance(_unparen(default),exp.Null) and not _number(default,'0'):_deny('分子ELSE只能0或NULL')
    branch=case.args['ifs'][0];condition=_unparen(branch.this)
    if not column(branch.args.get('true'),'invoice','total'):_deny('分子只累计invoice.total')
    if not isinstance(condition,exp.EQ) or not any(column(a,'customer','country') and isinstance(b,exp.Literal) and b.is_string and str(b.this)==country for a,b in ((condition.left,condition.right),(condition.right,condition.left))):
        _deny('分子CASE只能已核验customer.country等值，不得加条件/OR或换值')
    if checked.args.get('limit') and not any(_number(checked.args['limit'].expression,str(n)) for n in range(1,201)):
        _deny('比例结果不能被LIMIT0或不明表达式隐藏')
    return True
