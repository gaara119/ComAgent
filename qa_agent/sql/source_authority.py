"""Explicit-source constraints originate in real user input, not tool prose."""
from __future__ import annotations

import re

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers

from qa_agent.sql.catalog import CatalogError
from qa_agent.sql.validator import SQLValidationError


def requested_source_text(message: str, generation_context: dict | None = None) -> tuple[str, str]:
    if generation_context and generation_context.get("kind") == "composed":
        original = generation_context.get("original_question")
        if not isinstance(original, str) or not original.strip():
            raise SQLValidationError("内部跨源计划缺少真实用户原始问题，不能把工具子问题提升为用户显式来源约束。")
        return original, "original_user_question"
    return message, "direct_user_message"


def validate_explicit_sources(question: str, catalog) -> list[str]:
    # PostgreSQL lowercases unquoted identifiers; SQL double quotes preserve
    # case. Markdown backticks are display markup, not PostgreSQL case quotes.
    # https://www.postgresql.org/docs/16/sql-syntax-lexical.html
    component = r'(?:"(?:[^"\x00]|"")+"|[A-Za-z_][A-Za-z0-9_$]*)'
    identifier = rf"(?:{component}\.)?{component}"
    patterns = [rf"(?<![A-Za-z0-9_])(?P<name>{identifier})\s*`?\s*表",
                rf"(?:表名(?:为|是|叫|：|:)|table\s+(?:named|called))\s*`?(?P<name>{identifier})",
                rf"(?:名为|叫做)\s*`?(?P<name>{identifier})\s*`?\s*的表"]
    names = [match.group("name") for pattern in patterns for match in re.finditer(pattern, question, re.I)]
    result=[]
    for name in dict.fromkeys(names):
        try:
            tree=normalize_identifiers(sqlglot.parse_one("SELECT 1 FROM "+name,read="postgres"),dialect="postgres")
            source=tree.find(exp.Table)
            if source is None or source.catalog:
                raise CatalogError("invalid source")
            table=catalog.get_table(source.name,source.db or "public")
        except Exception as exc:
            raise SQLValidationError(f"请求显式指定的表 {name} 不在真实目录中，不能替换成其他业务表。") from exc
        canonical=table.name if table.schema=="public" else table.schema+"."+table.name
        if canonical not in result:
            result.append(canonical)
    return result


def requested_source_contract(message: str, catalog, generation_context: dict | None = None) -> dict:
    text,authority=requested_source_text(message,generation_context)
    return {"explicit_tables":validate_explicit_sources(text,catalog),"authority":authority,
            "unknown_sources":False,"planned_subquestion_is_user_authority":False}


def validate_composed_source_coverage(original_question: str, catalog, outputs: dict) -> dict:
    """Compare real user sources with consumed physical SQL sources over a DAG.

    Unknown user sources fail before processing any outputs. Missing coverage
    returns ``verified=False`` with a complete proof so the caller can record it
    and block whole-request success. This is source coverage, not a proof that
    every SQL computation implements its question's entire business meaning.

    A step can query one of several requested tables. Only the completed plan's
    union must cover all requested sources; model-suggested tables and unused
    CTEs never contribute. EMPTY_RESULT is an executed query, not a missing one.
    """
    required=validate_explicit_sources(original_question,catalog)
    if not isinstance(outputs,dict):
        raise SQLValidationError("跨源执行结果必须是实际步骤映射，不能用规划表名单代替。")
    from sqlglot.optimizer.scope import traverse_scope
    from qa_agent.sql.repair_guard import _qualified
    from qa_agent.sql.semantic_guard import _active_scopes

    each_step={}
    consumed=set()
    for step_id,output in outputs.items():
        if not isinstance(output,dict):
            raise SQLValidationError("跨源步骤缺少实际执行记录。")
        source=output.get("source")
        status=output.get("status")
        if source!="database" or status not in {"SUCCEEDED","EMPTY_RESULT"}:
            each_step[str(step_id)]={"source":source,"status":status,"consumed_tables":[],"counted":False}
            continue
        sql=output.get("sql")
        if not isinstance(sql,str) or not sql.strip() or not isinstance(output.get("table"),list):
            raise SQLValidationError("数据库步骤没有实际SQL与结果表，不能宣称覆盖用户指定来源。")
        try:
            tree=_qualified(sql,catalog)
            scopes=list(traverse_scope(tree))
            active=_active_scopes(scopes)
            physical=set()
            for scope in active:
                for _,table in scope.selected_sources.values():
                    if not isinstance(table,exp.Table):
                        continue
                    authentic=catalog.get_table(table.name,table.db or "public")
                    physical.add(authentic.name if authentic.schema=="public" else authentic.schema+"."+authentic.name)
        except Exception as exc:
            raise SQLValidationError("无法建立实际SQL消费的真实来源，不能用规划文字补齐来源覆盖。") from exc
        consumed.update(physical)
        each_step[str(step_id)]={"source":source,"status":status,"consumed_tables":sorted(physical),"counted":True}
    missing=sorted(set(required)-consumed)
    return {"verified":not missing,"mode":"whole_plan_consumed_physical_sources",
            "authority":"original_user_question","original_required":required,
            "each_step":each_step,"union":sorted(consumed),"missing":missing,
            "unused_ctes_counted":False,"model_suggested_tables_counted":False}
