"""Prove two compared count operands from actual SQL columns and result rows.

This is an execution-result shape contract. It does not replace SQL scope or
business correctness checks and never calls a model or reads reference answers.
"""
from __future__ import annotations

from decimal import Decimal,InvalidOperation
import re

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from qa_agent.sql.projection_labels import projection_labels_from_sql
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _physical_field,_resolve_projection,_intent_value
from qa_agent.sql.validator import SQLValidationError


def comparison_requirement(question,intent):
    if not (re.search(r"哪个|哪一个|谁",question) and re.search(r"更多|多些|最多|多一点",question)
            and re.search(r"多(?:多少|几|了多少).{0,4}(?:首|张|个|条|件|人)|差(?:多少|几)",question)):
        return None
    groups={}
    for binding in _intent_value(intent,"filters",[]) or []:
        field=binding.get("column") or binding.get("field")
        if not field or not field.endswith((".name",".title")) or binding.get("operator","=").upper() not in {"=","IN"}:
            continue
        values=binding.get("value")
        values=values if isinstance(values,list) else [values]
        groups.setdefault(field,[]).extend(str(value) for value in values if value is not None)
    pairs=[(field,list(dict.fromkeys(values))) for field,values in groups.items()
           if len(set(values))==2]
    if len(pairs)!=1:
        return None
    field,values=pairs[0]
    return {"field":field,"entities":values,"output":"both_actual_counts_and_program_derived_difference"}


def validate_comparison_result(question,sql,catalog,rows,*,intent=None):
    requirement=comparison_requirement(question,intent)
    if requirement is None:
        return {"verified":True,"mode":"not_explicit_paired_count_comparison"}
    expected=requirement["entities"]
    tree=_qualified(sql,catalog)
    root=next(scope for scope in traverse_scope(tree) if scope.parent is None)
    values={}
    units={}
    def number(value):
        try:
            actual=Decimal(str(value))
            if actual.is_finite() and actual>=0 and actual==actual.to_integral_value():
                return actual
        except (ValueError,TypeError,InvalidOperation):
            pass
        raise SQLValidationError("比较题所需的实际首数/数量不是有限非负整数，不能补造差额。")
    # Row-oriented output: identity column must trace to the confirmed field,
    # and the measure must be an actual COUNT, rather than an alias/literal.
    identities=[]
    measures=[]
    for projection in root.expression.selects:
        key=projection.alias_or_name
        value,owner=_resolve_projection(projection,root)
        if _physical_field(value,owner)==requirement["field"]:
            identities.append(key)
        if isinstance(value,exp.Count):
            target=value.this
            if isinstance(target,exp.Distinct) and len(target.expressions)==1:
                target=target.expressions[0]
            physical=_physical_field(target,owner)
            unit=("曲目首数" if physical in {"track.track_id","playlist_track.track_id"} else
                  "专辑数" if physical=="album.album_id" else "发票张数" if physical=="invoice.invoice_id" else None)
            if unit:
                measures.append((key,unit))
    if len(identities)==1 and len(measures)==1:
        key,unit=measures[0]
        for row in rows:
            entity=row.get(identities[0])
            if entity in expected:
                if entity in values:
                    raise SQLValidationError("同一个比较对象返回多条计数，无法确定本次实际比较值。")
                values[entity]=number(row.get(key));units[entity]=unit
    # Pivot/scalar output: entity and count lineage were independently proved
    # by the AST label extractor. A generated alias alone gives no evidence.
    if len(rows)==1:
        labels=projection_labels_from_sql(sql)
        for key,label in labels.items():
            for entity in expected:
                prefix=entity+" · "
                if label.startswith(prefix) and label[len(prefix):] in {"曲目首数","专辑数","发票张数"}:
                    values[entity]=number(rows[0].get(key));units[entity]=label[len(prefix):]
    if set(values)!=set(expected) or len(set(units.values()))!=1:
        raise SQLValidationError("用户同时要求哪个更多及多几项，实际结果必须提供两个确认对象的可比较真实数量；只返回赢家会遗漏差额依据。请返回两项计数或两项计数加差额。")
    left,right=expected
    difference=values[left]-values[right]
    winner=left if difference>0 else right if difference<0 else None
    return {"verified":True,"mode":"actual_two_operand_counts","field":requirement["field"],
            "left":{"entity":left,"value":str(values[left])},"right":{"entity":right,"value":str(values[right])},
            "winner":winner,"difference":str(abs(difference)),"unit":units[left],
            "derived_by_program":True,"requires_display":True}
