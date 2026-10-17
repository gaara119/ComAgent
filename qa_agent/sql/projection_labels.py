"""Derive business column labels from actual validated SQL, never alias guesses.

Supported proofs: singleton entity filters in scalar aggregate subqueries and
conditional pivots over a real aggregate/CTE. Unknown shapes return no label.
Only display metadata is produced; SQL, values and raw column names stay intact.
"""
from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope


@dataclass(frozen=True)
class Meaning:
    entity: str
    unit: str


def projection_labels_from_sql(sql: str, columns=None, *, include_simple=False) -> dict[str,str]:
    try:
        tree=sqlglot.parse_one(sql,read="postgres")
        scopes=list(traverse_scope(tree))
        root=next(scope for scope in scopes if scope.parent is None)
    except Exception:
        return {}
    by_expr={id(scope.expression):scope for scope in scopes}

    def unwrap(node):
        while isinstance(node,(exp.Alias,exp.Paren,exp.Cast)):
            node=node.this
        return node

    def resolve(node,scope,depth=0):
        if depth>12:
            return None,scope
        node=unwrap(node)
        if isinstance(node,exp.Column):
            source=scope.sources.get(node.table)
            if source is None and not node.table and len(scope.selected_sources)==1:
                source=next(iter(scope.selected_sources.values()))[1]
            if source is not None and not isinstance(source,exp.Table):
                candidate=next((item for item in source.expression.selects if item.alias_or_name==node.name),None)
                return resolve(candidate,source,depth+1) if candidate is not None else (None,scope)
        return node,scope

    def unit_for(node,scope):
        node,scope=resolve(node,scope)
        if (include_simple and isinstance(node,exp.Window) and isinstance(node.this,exp.Sum)
                and not any(node.args.get(key) for key in ('partition_by','order','spec','alias'))):
            unit=unit_for(node.this.this,scope)
            if unit in {'销售额','销售明细金额','购买数量'}:
                return unit+'合计'
        if include_simple and isinstance(node,exp.Window) and isinstance(node.this,(exp.RowNumber,exp.Rank,exp.DenseRank)):
            return '名次'
        if isinstance(node,exp.Count):
            target=unwrap(node.this)
            if isinstance(target,exp.Distinct) and len(target.expressions)==1:
                target=target.expressions[0]
            if isinstance(target,exp.Column):
                source=scope.sources.get(target.table)
                table=source.name.casefold() if isinstance(source,exp.Table) else ""
                if table in {"track","playlist_track"} and target.name.casefold()=="track_id":
                    return "曲目首数"
                if table=="album" and target.name.casefold()=="album_id":
                    return "专辑数"
                if table=="customer" and target.name.casefold()=="customer_id":
                    return "客户数"
                if table=="invoice" and target.name.casefold()=="invoice_id":
                    return "发票张数"
            return "数量"
        if isinstance(node,exp.Sum):
            target=unwrap(node.this)
            if isinstance(target,exp.Column):
                source=scope.sources.get(target.table)
                if isinstance(source,exp.Table) and source.name.casefold()=="invoice" and target.name.casefold()=="total":
                    return "销售额"
        if include_simple and isinstance(node,exp.Sum):
            target=unwrap(node.this)
            if isinstance(target,exp.Mul):
                fields=[]
                for term in (target.left,target.right):
                    value,owner=resolve(term,scope)
                    source=owner.sources.get(value.table)if isinstance(value,exp.Column)else None
                    fields.append((source.name,value.name)if isinstance(source,exp.Table)else None)
                if set(fields)=={('invoice_line','unit_price'),('invoice_line','quantity')}:
                    return '销售明细金额'
            if isinstance(target,exp.Column):
                source=scope.sources.get(target.table)
                if isinstance(source,exp.Table)and(source.name,target.name)==('invoice_line','quantity'):
                    return '购买数量'
        if include_simple and isinstance(node,(exp.Max,exp.Min)):
            child=unit_for(node.this,scope)
            if child in {'销售额','销售明细金额','购买数量'}:
                return ('最大'if isinstance(node,exp.Max)else'最小')+child
        return None

    def identity(predicate,scope):
        predicate=unwrap(predicate)
        if not isinstance(predicate,exp.EQ):
            return None
        for column,literal in ((predicate.left,predicate.right),(predicate.right,predicate.left)):
            actual,owner=resolve(column,scope)
            if not isinstance(actual,exp.Column) or not isinstance(literal,exp.Literal) or not literal.is_string:
                continue
            source=owner.sources.get(actual.table)
            if isinstance(source,exp.Table) and actual.name.casefold() in {"name","title","country","billing_country"}:
                text=" ".join(str(literal.this).replace("|","／").split())
                if 0<len(text)<=100:
                    return text
        return None

    def meaning(node,scope,depth=0):
        if depth>12:
            return None
        node,scope=resolve(node,scope)
        if isinstance(node,exp.Subquery):
            inner=by_expr.get(id(node.this))
            if inner is None or len(node.this.selects)!=1:
                return None
            unit=unit_for(node.this.selects[0],inner)
            where=node.this.args.get("where")
            # Single exact identity predicate only: no OR/scope invention.
            entity=identity(where.this,inner) if where is not None else None
            return Meaning(entity,unit) if entity and unit else None
        if isinstance(node,(exp.Max,exp.Min)) and isinstance(node.this,exp.Case):
            case=node.this
            branches=case.args.get("ifs") or []
            if len(branches)!=1 or case.args.get("default") is not None and not isinstance(case.args["default"],exp.Null):
                return None
            entity=identity(branches[0].this,scope)
            unit=unit_for(branches[0].args.get("true"),scope)
            return Meaning(entity,unit) if entity and unit else None
        return None

    labels={}
    for index,projection in enumerate(tree.selects):
        key=columns[index] if columns is not None and index<len(columns) else projection.alias_or_name
        if not key:
            continue
        node=unwrap(projection)
        proved=meaning(node,root)
        if proved:
            labels[key]=proved.entity+" · "+proved.unit
        elif isinstance(node,exp.Sub):
            left,right=meaning(node.left,root),meaning(node.right,root)
            if left and right and left.unit==right.unit and left.entity!=right.entity:
                labels[key]=left.entity+" − "+right.entity+" · "+left.unit+"差"
        if include_simple and key not in labels:
            unit=unit_for(node,root)
            if unit:
                labels[key]='发票销售额'if unit=='销售额'else unit
            elif isinstance(node,exp.Sub):
                left_unit,right_unit=unit_for(node.left,root),unit_for(node.right,root)
                if (left_unit and right_unit and left_unit.startswith('最大')and right_unit.startswith('最小')
                        and left_unit[2:]==right_unit[2:]):
                    labels[key]=left_unit[2:]+'差额'
    return labels
