"""Bounded display lineage, derived from actual consumed SQL projections.

Labels are not SQL-validity proofs. Unsupported expressions keep their original
output identity. SQL text, row keys and values are never rewritten here.
"""
from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

ENTITY = {'invoice':'发票','customer':'客户','employee':'员工','track':'曲目','album':'专辑',
          'artist':'艺术家','playlist':'歌单','salesorderheader':'销售订单',
          'purchaseorderheader':'采购订单','product':'产品','vendor':'供应商',
          'department':'部门','shipmethod':'运输方式','salesperson':'销售员','genre':'流派',
          'salesterritory':'销售区域','productcategory':'产品大类','productsubcategory':'产品子类'}
PK_COUNT = {('invoice','invoice_id'):'发票张数',('customer','customer_id'):'客户数',
 ('employee','employee_id'):'员工人数',('track','track_id'):'曲目首数',
 ('playlist_track','track_id'):'曲目首数',('album','album_id'):'专辑数',
 ('salesorderheader','salesorderid'):'销售订单数',('purchaseorderheader','purchaseorderid'):'采购订单数',
 ('product','productid'):'产品数',('vendor','businessentityid'):'供应商数'}
TABLE_SCHEMAS={'invoice':'public','invoice_line':'public','customer':'public','employee':'public',
 'track':'public','playlist_track':'public','album':'public','artist':'public','genre':'public','playlist':'public',
 'salesorderheader':'sales','purchaseorderheader':'purchasing','product':'production','vendor':'purchasing',
 'department':'humanresources','shipmethod':'purchasing','salesperson':'sales','salesterritory':'sales',
 'productcategory':'production','productsubcategory':'production'}
MONEY = {('invoice','total'):'发票销售额',('invoice_line','unit_price'):'曲目销售单价',
 ('salesorderheader','subtotal'):'销售订单未税金额',('purchaseorderheader','subtotal'):'采购订单未税金额',
 ('salesorderheader','taxamt'):'销售订单税额',('purchaseorderheader','taxamt'):'采购订单税额',
 ('salesorderheader','freight'):'销售订单运费',('purchaseorderheader','freight'):'采购订单运费',
 ('product','listprice'):'产品标价',('product','standardcost'):'产品标准成本'}
FIELD_LABELS = {'customer_id':'客户编号','employee_id':'员工编号','support_rep_id':'客户负责员工编号',
 'first_name':'名字','last_name':'姓氏','invoice_id':'发票编号','album_id':'专辑编号',
 'artist_id':'艺术家编号','track_id':'曲目编号','billing_country':'账单国家','country':'国家',
 'productid':'产品编号','shipmethodid':'运输方式编号','territoryid':'区域编号',
 'personid':'人员关联编号(personid)','storeid':'门店关联编号(storeid)',
 'orderqty':'购买数量','quantity':'数量','month':'月份','year':'年份'}
PHYSICAL_FIELD_LABELS = {('public','track','milliseconds'):'曲目时长（毫秒）'}

def text(node):
    value=' '.join(node.sql(dialect='postgres').replace('|','／').split())
    return value if len(value)<=180 else value[:170]+'…'

def transparent(node):
    while isinstance(node,(exp.Alias,exp.Paren)):node=node.this
    return node

def _chinese(value):return bool(re.search('[\u3400-\u9fff]',value))

def _safe_chinese_alias(alias, label, kind, population=True):
    if not _chinese(alias):return False
    if kind=='count':
        if not population and not re.search(r'非空|计数|出现次数',alias):return False
        if re.search(r'金额|销售额|价格|单价|百分|比例|占比|增长率|姓名|名称',alias):return False
        if re.search(r'去重|不同',alias) and '去重'not in label:return False
        objects=['采购订单','销售订单','发票','客户','员工','曲目','专辑','供应商','产品','人员','门店']
        actual=[o for o in objects if o in label]
        claimed=[o for o in objects if o in alias]
        if actual and claimed and not set(actual)&set(claimed):return False
    if kind=='money' and re.search(r'数量|人数|张数|首数|订单数|客户数|百分|占比|比例',alias):return False
    if alias==label:return True
    if kind=='money':
        # A monetary unit does not prove profit, budget, tax or any invented
        # business measure. Only bounded synonyms of the actual unit survive.
        allowed={'金额','金额合计'}
        if '销售额'in label:allowed|={'销售额','销售额合计','发票金额','发票总额','发票销售额','发票金额合计'}
        if '明细'in label:allowed|={'明细销售额','销售明细金额','明细销售金额'}
        return alias in allowed
    if kind=='count':
        if not population:return alias in{'数量','计数','记录数'}and label=='数量'
        for group in [{'客户数','客户人数','客户数量'},{'发票张数','发票数','发票数量'},
                      {'采购订单数','采购订单数量'},{'销售订单数','销售订单数量'},
                      {'员工人数','员工数'},{'曲目首数','曲目数'},{'专辑数','专辑数量'}]:
            if any(v in label for v in group):return alias in group
        return False
    if kind=='field':return alias==label
    return False

def projection_semantics(sql, columns=None, *, catalog=None):
    """Map final result keys to actual label/style/expression evidence.

    With a real catalog, unqualified fields in multi-table SQL are resolved by
    SQLGlot qualification. Without one, only unique single-source resolution is
    used. CAST/ROUND are described explicitly, never treated as transparent.
    """
    try:
        tree=sqlglot.parse_one(sql,read='postgres')
        if catalog is not None:
            from sqlglot.optimizer.qualify import qualify
            tree=qualify(tree,dialect='postgres',schema=catalog.sqlglot_schema(),
                validate_qualify_columns=False,allow_partial_qualification=True)
        scopes=list(traverse_scope(tree));root=next(s for s in scopes if s.parent is None)
        if not isinstance(root.expression,exp.Select):return {}
    except Exception:return {}
    by_expr={id(s.expression):s for s in scopes}

    def resolve(node,scope,depth=0):
        if node is None or depth>16:return None,scope
        node=transparent(node)
        if isinstance(node,exp.Column):
            source=scope.sources.get(node.table)
            if source is None and not node.table and len(scope.selected_sources)==1:
                source=next(iter(scope.selected_sources.values()))[1]
            if source is not None and not isinstance(source,exp.Table):
                if not isinstance(source.expression,exp.Select):return None,scope
                matches=[p for p in source.expression.selects if p.alias_or_name==node.name]
                return resolve(matches[0],source,depth+1)if len(matches)==1 else(None,scope)
        return node,scope

    def field(node,scope,depth=0):
        if node is None or depth>16:return None
        node=transparent(node)
        if not isinstance(node,exp.Column):return None
        source_alias=node.table
        source=scope.sources.get(source_alias)
        if source is None and not node.table and len(scope.selected_sources)==1:
            source_alias,(_,source)=next(iter(scope.selected_sources.items()))
        if source is not None and not isinstance(source,exp.Table):
            if not isinstance(source.expression,exp.Select):return None
            matches=[p for p in source.expression.selects if p.alias_or_name==node.name]
            if len(matches)!=1:return None
            actual=field(matches[0],source,depth+1)
            if actual is None:return None
            # Reusing one CTE through a/b creates distinct row instances even
            # when both eventually reach the same physical scope and alias.
            return {**actual,'_consumer_path':((id(scope),source_alias),)+actual['_consumer_path']}
        if not isinstance(source,exp.Table):return None
        schema=source.db or 'public';table=source.name;name=node.name
        if catalog is not None:
            try:
                entry=catalog.get_table(table,schema)
                if name not in entry.column_names:return None
            except Exception:return None
        semantic_table=table if TABLE_SCHEMAS.get(table)==schema else None
        return {'table':table,'semantic_table':semantic_table,'column':name,'qualified':f'{schema}.{table}.{name}','alias':source_alias,
                '_scope_identity':id(scope),'_consumer_path':(),
                'label':((PHYSICAL_FIELD_LABELS.get((schema,table,name))or FIELD_LABELS.get(name)or MONEY.get((table,name))or
                    (ENTITY[table]+'名称'if name in{'name','title'}and table in ENTITY else f'{table}.{name}'))
                    if semantic_table else (FIELD_LABELS[name]+' ['+f'{schema}.{table}.{name}'+']'if name in FIELD_LABELS else f'{schema}.{table}.{name}'))}

    def population_unique(f,scope):
        """COUNT(PK) counts unique entities only if no consumed join fans out.

        Bounded physical N:1 join graph; derived/unknown joins fall back to
        physical non-null occurrences instead of inventing entity counts.
        """
        if catalog is None:return False
        aliases={a:t for a,(_,t)in scope.selected_sources.items()if isinstance(t,exp.Table)}
        if len(aliases)!=len(scope.selected_sources):return False
        entries={}
        try:
            entries={a:catalog.get_table(t.name,t.db or'public')for a,t in aliases.items()}
            owner=entries[f['alias']]
            keys=set(owner.primary_key)
            if f['column']not in keys:return False
            remaining=keys-{f['column']}
            fixed=set()
            group=scope.expression.args.get('group')
            if group:
                for item in group.expressions:
                    key=transparent(item)
                    if isinstance(key,exp.Column)and key.table==f['alias']:fixed.add(key.name)
            where=scope.expression.args.get('where')
            def atoms(n):
                n=transparent(n)
                return atoms(n.left)+atoms(n.right)if isinstance(n,exp.And)else[n]
            if where:
                for atom in atoms(where.this):
                    if isinstance(atom,exp.EQ):
                        for key,value in((atom.left,atom.right),(atom.right,atom.left)):
                            if isinstance(key,exp.Column)and key.table==f['alias']and isinstance(value,exp.Literal):fixed.add(key.name)
            if not remaining<=fixed:return False
        except Exception:return False
        if not scope.expression.args.get('joins'):return True
        edges=[]
        for join in scope.expression.args.get('joins')or[]:
            on=join.args.get('on')
            if on is None or on.find(exp.Or):return False
            equalities=[]
            def conjunction(n):
                n=transparent(n)
                return conjunction(n.left)+conjunction(n.right)if isinstance(n,exp.And)else[n]
            for clause in conjunction(on):
                if isinstance(clause,exp.EQ)and isinstance(clause.left,exp.Column)and isinstance(clause.right,exp.Column):
                    equalities.append((clause.left,clause.right))
            for alias,entry in entries.items():
                for fk in entry.foreign_keys:
                    refs=fk['references']
                    for other,target in entries.items():
                        if alias==other or target.name!=refs['table']or target.schema!=refs.get('schema',entry.schema):continue
                        pairs=set(zip(fk['columns'],refs['columns']))
                        actual=set()
                        for l,r in equalities:
                            for left,right in((l,r),(r,l)):
                                if left.table==alias and right.table==other:actual.add((left.name,right.name))
                        if pairs and pairs<=actual and tuple(refs['columns'])==tuple(target.primary_key):edges.append((alias,other))
        reached={f['alias']}
        for _ in aliases:
            reached|={b for a,b in edges if a in reached}
        return set(aliases)<=reached

    def detail_amount_product(node,scope):
        """One actual invoice-line row's price times its own quantity.

        The same table name in two aliases/CTEs is not the same row owner.
        Only transparent physical lineage is accepted; casts, arbitrary
        multiplication and missing catalog evidence cannot install a unit.
        """
        node,scope=resolve(node,scope)
        if catalog is None or not isinstance(node,exp.Mul):return False
        fields=[field(node.left,scope),field(node.right,scope)]
        return (all(fields)and
            {(f['semantic_table'],f['column'])for f in fields}=={('invoice_line','unit_price'),('invoice_line','quantity')}and
            fields[0]['alias']==fields[1]['alias']and fields[0]['_scope_identity']==fields[1]['_scope_identity']and
            fields[0]['_consumer_path']==fields[1]['_consumer_path'])

    def describe(node,scope,depth=0):
        if depth>20:return None
        node,scope=resolve(node,scope)
        if node is None:return None
        def sub(x):return describe(x,scope,depth+1)
        def info(kind,label,**extra):return {'kind':kind,'label':label,'expression':node.sql(dialect='postgres'),**extra}
        def info_from(child,kind,label,**extra):
            evidence={key:value for key,value in child.items()if key not in{'kind','label','expression'}}
            evidence.update(extra)
            if kind!='ratio':evidence.pop('ratio_scale',None)
            return info(kind,label,**evidence)
        def business_value(value,level=0):
            """A bounded label rendering, never a SQL equivalence proof."""
            if level>10:return None
            value=transparent(value)
            actual=field(value,scope)
            if actual:return actual['label']
            if detail_amount_product(value,scope):return '销售明细金额'
            if isinstance(value,exp.Null):return '空值'
            if isinstance(value,exp.Literal):return str(value.this).replace('|','／')
            if isinstance(value,exp.Neg)and isinstance(value.this,exp.Literal):return '-'+str(value.this.this)
            if isinstance(value,exp.Case):
                parts=[]
                for branch in value.args.get('ifs')or[]:
                    condition=condition_label(branch.this,level+1)
                    result=business_value(branch.args.get('true'),level+1)
                    if not condition or result is None:return None
                    parts.append('当'+condition+'时取'+result)
                default=value.args.get('default')
                if default is None or isinstance(default,exp.Null):other='否则为空'
                else:
                    result=business_value(default,level+1)
                    if result is None:return None
                    other='否则为'+result
                return '；'.join(parts+[other])if parts else None
            return None
        def condition_label(predicate,level=0):
            if predicate is None or level>10:return None
            predicate=transparent(predicate)
            if isinstance(predicate,exp.Where):return condition_label(predicate.this,level+1)
            if isinstance(predicate,(exp.And,exp.Or)):
                left=condition_label(predicate.left,level+1);right=condition_label(predicate.right,level+1)
                return '('+left+('且'if isinstance(predicate,exp.And)else'或')+right+')'if left and right else None
            if isinstance(predicate,exp.Not):
                child=condition_label(predicate.this,level+1)
                return '不满足('+child+')'if child else None
            for cls,symbol in((exp.EQ,'='),(exp.NEQ,'≠'),(exp.LT,'<'),(exp.LTE,'≤'),(exp.GT,'>'),(exp.GTE,'≥')):
                if isinstance(predicate,cls):
                    left=business_value(predicate.left,level+1);right=business_value(predicate.right,level+1)
                    return left+symbol+right if left is not None and right is not None else None
            if isinstance(predicate,exp.Is)and isinstance(predicate.expression,exp.Null):
                actual=business_value(predicate.this,level+1)
                # SQLGlot represents IS NOT NULL as Is(negate=True), while
                # an explicit NOT (...) remains a separate Not node above.
                return actual+('不为空'if predicate.args.get('negate')else'为空')if actual else None
            if isinstance(predicate,exp.In)and not predicate.args.get('query'):
                actual=business_value(predicate.this,level+1)
                values=[business_value(x,level+1)for x in predicate.expressions]
                return actual+'属于['+'、'.join(values)+']'if actual and values and all(x is not None for x in values)else None
            return None
        def cast_target(target):
            if not isinstance(target,exp.DataType):return None
            name=getattr(target.this,'value',str(target.this))
            params=[]
            for param in target.expressions:
                value=param.this if isinstance(param,exp.DataTypeParam)else param
                if not isinstance(value,exp.Literal)or value.is_string or not str(value.this).isdigit():return None
                params.append(int(value.this))
            numeric={'INT':'整数','BIGINT':'64位整数','SMALLINT':'16位整数',
                     'DOUBLE':'双精度浮点数','FLOAT':'单精度浮点数','REAL':'单精度浮点数'}
            if name in numeric and not params:return numeric[name],True
            if name in{'DECIMAL','NUMERIC'}:
                if not params:return '任意精度数',True
                if len(params)in{1,2}:
                    return '定点数（总精度'+str(params[0])+'位，小数'+str(params[1]if len(params)==2 else 0)+'位）',True
            if name in{'TEXT','VARCHAR','CHAR'}:
                if not params:return '文本',False
                if len(params)==1:return '文本（最多'+str(params[0])+'字符）',False
            return None
        def literal(n):
            n=transparent(n)
            if isinstance(n,exp.Literal)and not n.is_string:
                try:return Decimal(n.this)
                except InvalidOperation:pass
            return None
        if isinstance(node,(exp.Concat,exp.DPipe)):
            def pieces(n):
                n=transparent(n)
                if isinstance(n,exp.DPipe):return pieces(n.left)+pieces(n.right)
                if isinstance(n,exp.Concat):return [part for v in n.expressions for part in pieces(v)]
                if isinstance(n,exp.Literal)and n.is_string and not n.this.strip():return []
                f=field(n,scope)
                return [f]if f else[None]
            fields=pieces(node)
            if (len(fields)==2 and all(fields)and fields[0]['alias']==fields[1]['alias']
                    and fields[0]['table']==fields[1]['table']and fields[0]['semantic_table']is not None
                    and{f['column']for f in fields}in({'first_name','last_name'},{'firstname','lastname'})):
                return info('field',{'customer':'客户姓名','employee':'员工姓名','person':'姓名'}.get(fields[0]['table'],'姓名'))
            return None
        def scaled(n,owner=None,level=0):
            owner=scope if owner is None else owner
            if level>16:return Decimal(1),n,owner
            n,owner=resolve(n,owner)
            if n is None:return Decimal(1),n,owner
            if isinstance(n,exp.Nullif)and literal(n.expression)==0:return scaled(n.this,owner,level+1)
            if isinstance(n,exp.Subquery):
                actual_owner=by_expr.get(id(n.this))
                if actual_owner and isinstance(n.this,exp.Select)and len(n.this.selects)==1:
                    # Follow only the consumed scalar projection. ROUND/CAST
                    # remain opaque to this scale walk and keep their own
                    # actual transform semantics in describe().
                    return scaled(n.this.selects[0],actual_owner,level+1)
            if isinstance(n,exp.Mul):
                for constant,value in((n.left,n.right),(n.right,n.left)):
                    factor=literal(constant)
                    if factor is not None:
                        inner,core,actual_owner=scaled(value,owner,level+1);return factor*inner,core,actual_owner
            if isinstance(n,exp.Div)and literal(n.right)not in{None,0}:
                inner,core,actual_owner=scaled(n.left,owner,level+1);return inner/literal(n.right),core,actual_owner
            return Decimal(1),n,owner
        if isinstance(node,exp.Subquery):
            owner=by_expr.get(id(node.this))
            if owner and isinstance(node.this,exp.Select)and len(node.this.selects)==1:
                return describe(node.this.selects[0],owner,depth+1)
            return None
        if isinstance(node,exp.Column):
            f=field(node,scope)
            if f:return info('money'if(f['semantic_table'],f['column'])in MONEY else'field',f['label'],physical_field=f['qualified'])
            return None
        if isinstance(node,exp.Count):
            target=node.this;distinct=isinstance(target,exp.Distinct)
            if distinct:
                if len(target.expressions)!=1:return info('count','去重计数：'+text(target),distinct=True)
                target=target.expressions[0]
            f=field(target,scope)
            if isinstance(target,exp.Star):
                label='数量'
            elif f:
                unique=distinct or population_unique(f,scope)
                label=(PK_COUNT.get((f['semantic_table'],f['column']))if unique else None)or f['label']+'非空计数'
                if distinct:label+='（去重）'
            else:
                label=('去重计数：'if distinct else'非空计数：')+(business_value(target)or'表达式结果')
            return info('count',label,distinct=distinct,physical_field=f['qualified']if f else None,
                        population_count_proven=bool(f and(f['semantic_table'],f['column'])in PK_COUNT and (distinct or population_unique(f,scope))))
        if isinstance(node,exp.Filter):
            child=sub(node.this)
            if child:
                condition=node.args.get('expression')
                label=condition_label(condition)
                return info_from(child,child['kind'],child['label']+'（仅计入'+(label+'的记录'if label else'指定条件成立的记录')+'）',
                            filtered=True,label_protected=True,condition_expression=condition.sql(dialect='postgres'))
            return None
        if isinstance(node,exp.Sum):
            f=field(node.this,scope)
            if f:
                if(f['semantic_table'],f['column'])in MONEY:
                    label='发票销售额'if(f['table'],f['column'])==('invoice','total')else f['label']+'合计'
                    return info('money',label)
                return info('numeric',f['label']+'合计')
            if detail_amount_product(node.this,scope):return info('money','销售明细金额')
            child=sub(node.this)
            if child and child['kind']=='money':return info_from(child,'money',child['label'].replace('发票销售额','销售额')+'合计')
            return None
        if isinstance(node,exp.Avg):
            child=sub(node.this)
            return info_from(child,child['kind'],
                '逐条'+child['label']+'的平均值'if child.get('transformed')else'平均'+child['label'],
                label_protected=True)if child else None
        if isinstance(node,exp.Case):
            branches=node.args.get('ifs')or[]
            values=[sub(b.args.get('true'))for b in branches]
            default=node.args.get('default')
            if values and all(v and v['kind']=='money'for v in values)and(default is None or isinstance(default,exp.Null)or literal(default)==0):
                return info('money','条件金额（'+(business_value(node)or'按实际条件取值')+'）',label_protected=True,
                    **({'scope_label':condition_label(branches[0].this)}if len(branches)==1 and condition_label(branches[0].this)else{}))
            return None
        if isinstance(node,exp.Window):
            if isinstance(node.this,(exp.RowNumber,exp.Rank,exp.DenseRank)):return info('rank','名次')
            child=sub(node.this)
            if child and not any(node.args.get(k)for k in('partition_by','order','spec','alias')):
                return info_from(child,child['kind'],child['label'])
            return None
        if isinstance(node,(exp.Max,exp.Min)):
            child=sub(node.this)
            if child:return info_from(child,child['kind'],('最大'if isinstance(node,exp.Max)else'最小')+child['label'].replace('发票销售额','销售额'),label_protected=True)
            return None
        if isinstance(node,exp.Nullif):return sub(node.this)
        if isinstance(node,exp.Div):
            lf,lc,lo=scaled(node.left);rf,rc,ro=scaled(node.right)
            l,r=describe(lc,lo,depth+1),describe(rc,ro,depth+1)
            if l and r:
                notes=('（分子：'+l['label']+'；分母：'+r['label']+'）')if l.get('transformed')or r.get('transformed')else''
                if l['kind']=='money'and r['kind']=='count':return info('money','平均金额'+notes,label_protected=bool(notes))
                if l['kind']==r['kind']and l['kind']in{'money','count','numeric'}and rf:
                    return info('ratio',((l['scope_label']+'占比')if l.get('scope_label')else'占比')+notes,
                                ratio_scale=str(lf/rf),label_protected=bool(notes))
            factor,core,owner=scaled(node)
            if core is not node:
                child=describe(core,owner,depth+1)
                if child and child['kind']=='ratio':return info('ratio',child['label'],ratio_scale=str(factor*Decimal(child.get('ratio_scale','1'))))
            return None
        if isinstance(node,exp.Sub):
            l,r=sub(node.left),sub(node.right)
            if l and r and l['kind']==r['kind']:
                qualifiers={key:True for key in('label_protected','transformed','filtered')if l.get(key)or r.get(key)}
                if l['label'].startswith('最大')and r['label'].startswith('最小')and l['label'][2:]==r['label'][2:]:
                    return info(l['kind'],l['label'][2:]+'差额',**qualifiers)
                return info(l['kind'],l['label']+' − '+r['label'],**qualifiers)
            return None
        if isinstance(node,(exp.Cast,exp.Round)):
            child=sub(node.this)
            if child:
                kind=child['kind']
                if isinstance(node,exp.Round):
                    raw_digits=node.args.get('decimals')
                    digits=Decimal(0)if raw_digits is None else literal(raw_digits)
                    if isinstance(raw_digits,exp.Neg)and literal(raw_digits.this)is not None:digits=-literal(raw_digits.this)
                    if digits is None or digits!=digits.to_integral_value():return None
                    digits=int(digits)
                    label=child['label']+('（保留'+str(digits)+'位小数）'if digits>=0 else'（四舍五入至小数点前'+str(-digits)+'位）')
                    operation={'operation':'round','digits':digits}
                else:
                    actual=cast_target(node.args.get('to'))
                    if actual is None:return None
                    label=child['label']+'（转换为'+actual[0]+'）'
                    if not actual[1]:kind='field'
                    operation={'operation':'cast','target_type':node.args['to'].sql(dialect='postgres')}
                # Only label/style metadata changes. This is not an assertion
                # that numeric casts or rounding are lossless transformations.
                return info_from(child,kind,label,transformed=True,label_protected=True,
                                 child_kind=child['kind'],display_transform=operation)
            return None
        if isinstance(node,exp.Mul):
            if detail_amount_product(node,scope):return info('money','销售明细金额')
            factor,core,owner=scaled(node)
            if core is not node:
                child=describe(core,owner,depth+1)
                if child and child['kind']=='ratio':return info('ratio',child['label'],ratio_scale=str(factor*Decimal(child.get('ratio_scale','1'))))
            return None
        return None

    result={}
    for i,projection in enumerate(root.expression.selects):
        key=columns[i]if columns is not None and i<len(columns)else projection.alias_or_name
        if not key:continue
        item=describe(projection,root)
        if item is None:continue
        original=projection.alias
        if original and not item.get('label_protected')and _safe_chinese_alias(original,item['label'],item['kind'],item.get('population_count_proven',True)):item['label']=original
        result[key]={**item,'source':'actual_consumed_sql_projection','projection_index':i}
    return result


def proved_repeat_count_labels(sql, columns, *, catalog=None, semantic_intent=None):
    """Refine a count only after existing registered grain/period/output proofs.

    A question or alias saying 'repeat' is never evidence. Missing program
    contract/catalog/current source context falls back to the actual COUNT.
    """
    if catalog is None or semantic_intent is None:return {}
    get=lambda k,d=None:semantic_intent.get(k,d)if isinstance(semantic_intent,dict)else getattr(semantic_intent,k,d)
    if get('metric')!='repeat_customer_count':return {}
    try:
        from qa_agent.sql.repeat_qualification_guard import validate_repeat_qualification
        proof=validate_repeat_qualification(sql,catalog,semantic_intent)
        if proof.get('mode')!='registered_repeat_qualification_consumed':return {}
        if get('grouping'):
            from qa_agent.sql.repair_guard import _qualified
            from qa_agent.sql.document_repeat_lineage import prove_grouped_repeat_output,prove_derived_customer_qualification
            scopes=list(traverse_scope(_qualified(sql,catalog)))
            qualifications={s:prove_derived_customer_qualification(s,catalog,question=(get('query_scope',{}).get('repeat_qualification')or{}).get('source_evidence',''))
                            for s in scopes if s.expression.sql(dialect='postgres')in proof['qualified_scopes']}
            output=prove_grouped_repeat_output(scopes,qualifications,catalog)
        else:output=proof.get('global_output_proof')or{}
        if output.get('verified')is not True:return {}
        meanings=projection_semantics(sql,columns,catalog=catalog)
        prefix='期间内'if proof.get('period')else''
        return {column:prefix+'复购客户数'for column,item in meanings.items()if item['kind']=='count'}
    except(ValueError,KeyError,TypeError,StopIteration):return {}
