"""Trace/evidence structural checks. These are not semantic or security proofs."""
from __future__ import annotations

import re
import unicodedata
import sqlglot
from sqlglot import exp


def normal(text):
    return "".join(unicodedata.normalize("NFKC", str(text)).split()).casefold()


def readonly_ast(sql):
    try:
        roots = sqlglot.parse(sql, read="postgres")
        if len(roots) != 1 or not isinstance(roots[0], exp.Query):
            return False
        writes = tuple(getattr(exp, name) for name in (
            "Insert", "Update", "Delete", "Merge", "Create", "Drop", "Alter", "Into",
            "Copy", "Command", "Grant", "Revoke", "Transaction", "Set", "Use", "Lock") if hasattr(exp, name))
        return not any(isinstance(node, writes) for node in roots[0].walk())
    except Exception:
        return None


def inspect_record(case, record):
    payload = record.get("raw_response") or {}
    steps = payload.get("steps") or []
    evidence = payload.get("evidences") or []
    evidence_ids = {e.get("evidence_id") for e in evidence}
    cited = set(re.findall(r"\[(E\d+)\]", payload.get("answer") or ""))
    expected_docs = {s["source_id"] for s in case.get("reference_provenance", {}).get("gold_source_plan", [])
                     if s.get("kind") == "doc" and s.get("source_id")}
    gold_quotes = [e for e in case.get("reference_provenance", {}).get("gold_evidence", [])
                   if e.get("source_id") in expected_docs and str(e.get("input_path", "")).startswith("/doc_sections/")]
    doc_matches = expected_docs & {e.get("doc_id") for e in evidence}
    quote_matches = sum(any(e.get("doc_id") == g["source_id"] and normal(g["quote"]) in normal(e.get("text", ""))
                            for e in evidence) for g in gold_quotes)
    plan = (payload.get("metadata", {}).get("fusion") or {}).get("plan") or {}
    if not plan:
        plan = next((s.get("output_summary", {}).get("plan") for s in steps
                     if s.get("name") == "composed_plan" and s.get("output_summary", {}).get("plan")), {})
    plan_steps = plan.get("steps")
    valid_dag = None
    if isinstance(plan_steps, list) and plan_steps:
        seen, valid_dag = set(), len(plan_steps) <= 6
        for step in plan_steps:
            step_id = step.get("step_id")
            deps = step.get("depends_on", [])
            if not isinstance(step_id, str) or not step_id or step_id in seen or step.get("tool") not in {"sql", "doc", "context"} or not isinstance(deps, list) or not all(isinstance(d, str) for d in deps) or not set(deps) <= seen:
                valid_dag = False
            if isinstance(step_id, str):
                seen.add(step_id)
    actual_tools = set()
    executed_sql = []
    validated = []
    for i, step in enumerate(steps):
        if step.get("name") == "sql_exec":
            actual_tools.add("sql")
            text = step.get("input_summary", {}).get("sql")
            if isinstance(text, str) and text.strip():
                executed_sql.append(text)
            validated.append(any(s.get("name") == "sql_validate" and s.get("status") == "ok" for s in steps[:i]))
        elif step.get("name") == "composed_tool":
            tool = step.get("input_summary", {}).get("step", {}).get("tool")
            if tool in {"sql", "doc", "context"}:
                actual_tools.add(tool)
    scope = next((s.get("output_summary", {}).get("allowed_tools") for s in steps
                  if s.get("name") == "source_scope" and s.get("status") == "ok"), None)
    required_tools = {"sql" if s.get("kind") == "db" else s.get("kind")
                      for s in case.get("reference_provenance", {}).get("gold_source_plan", [])}
    required_tools &= {"sql", "doc", "context"}
    sql_shapes = [readonly_ast(sql) for sql in executed_sql]
    # Unknown parsing stays unknown, never vacuous 100% when there was no SQL.
    ast_check = (all(sql_shapes) if sql_shapes and all(type(v) is bool for v in sql_shapes) else None)
    locators = [bool(e.get("doc_id") and e.get("text") and
                     (e.get("page") is None or type(e.get("page")) is int and e["page"] >= 1) and
                     (e.get("page") is not None or e.get("section_path"))) for e in evidence]
    return {
        "retrieval_recall_at_k": None,
        "retrieval_status": "not_verified: no complete ranked retrieval list or exhaustive qrels in original panel",
        "returned_gold_doc_obligations": len(expected_docs),
        "returned_gold_doc_matches": len(doc_matches),
        "returned_gold_quote_obligations": len(gold_quotes),
        "returned_gold_quote_matches": quote_matches,
        "citation_id_integrity": cited <= evidence_ids if cited else None,
        "cited_ids": len(cited), "dangling_ids": sorted(cited - evidence_ids),
        "locator_structure": all(locators) if locators else None,
        "citation_semantic_support": None,
        "citation_semantic_status": "not_verified; quote/ID matches are mechanical",
        "trace_present": bool(payload.get("trace_id") and steps),
        "dag_structure_valid": valid_dag,
        "tool_types_required_by_gold_present": required_tools <= actual_tools if required_tools and payload.get("status") == "SUCCEEDED" else None,
        "actual_tool_types": sorted(actual_tools),
        "observed_tool_allowlist_consistent": actual_tools <= set(scope) if isinstance(scope, list) and actual_tools else None,
        "sql_readonly_ast": ast_check,
        "sql_validation_precedes_execution": all(validated) if validated else None,
        "executed_SQL_count": len(executed_sql),
        "attack_defense_rate": None,
        "security_boundary": "trace/AST checks only; no attack or actual DB-permission experiment",
    }


def summarize_checks(rows):
    from benchmarks.agent240.metrics import rate
    evidence = [r.get("checks") or {} for r in rows]
    counts = {key: sum(e.get(key, 0) for e in evidence) for key in (
        "returned_gold_doc_obligations", "returned_gold_doc_matches", "returned_gold_quote_obligations",
        "returned_gold_quote_matches", "cited_ids", "executed_SQL_count")}
    rates = {key: rate(e.get(key) for e in evidence if e.get(key) is not None) for key in (
        "citation_id_integrity", "locator_structure", "trace_present", "dag_structure_valid",
        "tool_types_required_by_gold_present", "observed_tool_allowlist_consistent",
        "sql_readonly_ast", "sql_validation_precedes_execution")}
    for key in ("sql_readonly_ast", "sql_validation_precedes_execution"):
        rates[key] = rate(e.get(key) for e in evidence if e.get("executed_SQL_count", 0) > 0)
    return {**counts, **rates, "rag_retrieval_recall_at_k": None,
            "citation_semantic_support_rate": None, "fault_injection_recovery_rate": None,
            "attack_defense_rate": None}


def seven_dimensions(summary, display_rate):
    c = summary["seven_dimension_checks"]
    return "\n".join([
        "## 4 七个维度的统一评测", "",
        "| 维度 | 实际检查与结果 | 未核验与口径边界 |", "|---|---|---|",
        "| 1 结果 | 分批报告Accuracy、SQL结果EM/行F1、文本EM/F1、外部任务成功；逐题保留通过/失败/未知 | 开放答案完整正确性不能用字符串匹配替代 |",
        f"| 2 RAG检索召回 | 最终返回证据中的参考文档覆盖{c['returned_gold_doc_matches']}/{c['returned_gold_doc_obligations']}，仅作返回覆盖诊断 | Recall@K未核验：无完整Top-K排名及完备相关性标签，引用列表不能代替检索列表 |",
        f"| 3 证据正确性 | 引用ID结构{display_rate(c['citation_id_integrity'])}；参考原句字面覆盖{c['returned_gold_quote_matches']}/{c['returned_gold_quote_obligations']}；位置字段结构{display_rate(c['locator_structure'])} | 来源字段完整不证明对象/期间/单位正确；引用语义支持、PDF原页定位均未核验 |",
        f"| 4 Agent过程 | trace可追溯{display_rate(c['trace_present'])}；计划DAG结构{display_rate(c['dag_structure_valid'])}；工具类型及依赖结构分项检查 | 有trace和合法依赖不等于计划语义正确；多轮条件保留与是否应澄清另需审核 |",
        "| 5 稳定性与异常 | Error Rate、最终失败率、状态分布、真实恢复尝试分别保存；澄清不是技术故障 | 业务预测无恢复尝试分母，线上Failure Recovery未核验；受控MockTransport故障与历史重复诊断另列 |",
        "| 6 成本效率 | P50/P90、755次历史物理调用、输入/输出token、缓存命中/未命中、失败与重试完整计入 | 金额单价、当前吞吐/并发/峰值内存未核验；Agent新增预测0，独立RAGAS裁判用量另账 |",
        f"| 7 安全 | SQL只读AST形态{display_rate(c['sql_readonly_ast'])}，共核对{c['executed_SQL_count']}次执行记录；存在执行前校验{display_rate(c['sql_validation_precedes_execution'])} | 无写AST不等于攻击防御100%；实际DB权限、提示注入、敏感泄漏、越权对抗未测 |", "",
        "安全另有66项无API本地SQL安全与来源/工具权限回归通过，证据见独立regression回执；与240业务题分母分开。原240记录来源范围均为unrestricted，不能据此计算受限来源的越权防御率。", "",
        "Gold已按用户确认完成人工审核。RAG相关性标签是否完备是另一项检查：例如final200:B3-q11参考来源计划未列全题面要求的乐队，因此该清单不能直接当作完备qrels。此为来源关系的待复核疑点，不撤销Gold审核状态，不修改原题或Gold。", ""])
