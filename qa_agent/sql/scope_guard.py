"""Enforce an explicitly program-derived unrestricted geography contract."""
from __future__ import annotations

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _active_scopes, _physical_field
from qa_agent.sql.validator import SQLValidationError


def validate_unrestricted_geography(sql, catalog, intent, *, question=None):
    scope_contract = getattr(intent, "query_scope", {}) or {}
    if scope_contract.get("geography_unrestricted") is not True:
        return {"verified": True, "mode": "no_programmatic_unrestricted_geography_contract"}
    proof = scope_contract.get("geography_provenance") or {}
    if proof.get("source") != "program:inactive_named_region" or not question or proof.get("current_evidence") != question:
        raise SQLValidationError("地区不受限标记没有对应本轮原文的程序来源，不能消费模型伪造的约束标记。")
    tree = _qualified(sql, catalog)
    restricted = set()
    for scope in _active_scopes(list(traverse_scope(tree))):
        for column in scope.columns:
            field = _physical_field(column, scope)
            if field not in {"invoice.billing_country", "customer.country", "employee.country"}:
                continue
            parent = column.parent
            while parent is not None and parent is not scope.expression:
                if isinstance(parent, (exp.Where, exp.Having, exp.Case, exp.If)):
                    restricted.add(field)
                    break
                parent = parent.parent
    if restricted:
        raise SQLValidationError("当前问题没有激活地区集合，程序确认本次地区不受限；SQL不能从历史问题恢复国家筛选或把国家条件藏进条件聚合。请保留本次期间、指标和已确认的其它条件，删除未授权的地区限制。")
    return {"verified": True, "mode": "programmatic_unrestricted_geography", "active_geographic_filters": []}
