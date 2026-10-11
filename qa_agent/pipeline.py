"""Shared dispatch and incremental SQL pipeline; no evaluation labels are read."""
from __future__ import annotations

import importlib
import inspect

from qa_agent.config import Settings, get_settings, sanitize_error
from qa_agent.llm import JsonLLM, LLMError, MissingCredentialError
from qa_agent.schemas import AnswerEnvelope, ChatRequest, ErrorDetail, IntentContract
from qa_agent.trace import TraceRecorder


def _error_envelope(trace: TraceRecorder, settings: Settings, message: str,
                    code: str, retryable: bool = False, sql: str | None = None,
                    intent: IntentContract | None = None) -> AnswerEnvelope:
    safe = sanitize_error(message, settings)
    return AnswerEnvelope(
        trace_id=trace.trace_id, status="FAILED", answer=safe, sql=sql, intent=intent,
        steps=trace.steps, error=ErrorDetail(code=code, message=safe, retryable=retryable),
        metadata={"model": settings.llm_model, "db_id": "chinook", "latency_ms": trace.latency_ms},
    )


def _unsupported(trace: TraceRecorder, answer: str) -> AnswerEnvelope:
    return AnswerEnvelope(trace_id=trace.trace_id, status="UNSUPPORTED", answer=answer,
                          steps=trace.steps, metadata={"latency_ms": trace.latency_ms})


def _doc(request: ChatRequest, trace: TraceRecorder, settings: Settings) -> AnswerEnvelope:
    if len(request.scope.doc_ids) != 1:
        return _unsupported(trace, "D1 单文档问答需要选择且仅选择一份文档。")
    module_name, separator, function_name = settings.rag_handler.partition(":")
    if not separator or not module_name.startswith("qa_agent.rag."):
        return _error_envelope(trace, settings, "RAG_HANDLER 配置必须指向项目的 qa_agent.rag 模块。", "rag_handler_config")
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name and (module_name == exc.name or module_name.startswith(exc.name + ".")):
            return _unsupported(trace, "B 的 RAG 入口尚未接入。请按 notes/B接口交接.md 实现并配置 RAG_HANDLER。")
        return _error_envelope(trace, settings, "RAG 模块缺少依赖，请检查 B 的安装步骤。", "rag_dependency")
    except ImportError:
        return _error_envelope(trace, settings, "RAG 模块导入失败，请检查 B 的模块及依赖。", "rag_dependency")
    handler = getattr(module, function_name, None)
    if not callable(handler):
        return _unsupported(trace, "B 的 RAG 入口尚未接入。请按 notes/B接口交接.md 实现并配置 RAG_HANDLER。")
    try:
        intent = IntentContract(route="doc", task_type="doc_qa")
        with trace.step("rag_channel", {"doc_id": request.scope.doc_ids[0]}) as step:
            result = handler(question=request.message, doc_id=request.scope.doc_ids[0],
                             trace_id=trace.trace_id, intent=intent)
            if inspect.isawaitable(result):
                import asyncio
                result = asyncio.run(result)
            envelope = result if isinstance(result, AnswerEnvelope) else AnswerEnvelope.model_validate(result)
            if any(e.doc_id != request.scope.doc_ids[0] for e in envelope.evidences):
                raise ValueError("RAG 返回了指定文档之外的证据")
            ids = [e.evidence_id for e in envelope.evidences]
            if len(ids) != len(set(ids)):
                raise ValueError("RAG 返回了重复证据编号")
            step.output_summary = {"status": envelope.status, "evidence_count": len(ids)}
        envelope.trace_id = trace.trace_id
        envelope.steps = trace.steps + envelope.steps
        envelope.metadata["latency_ms"] = trace.latency_ms
        return envelope
    except Exception as exc:
        return _error_envelope(trace, settings, str(exc), "rag_failed", getattr(exc, "retryable", False))


def _sql(request: ChatRequest, trace: TraceRecorder, settings: Settings,
         llm: JsonLLM) -> AnswerEnvelope:
    from qa_agent.sql.catalog import load_catalog
    from qa_agent.sql.executor import SQLExecutionError, SQLTimeoutError, execute_sql
    from qa_agent.sql.generator import generate_sql
    from qa_agent.sql.validator import (SQLValidationError, validate_sql, validate_value_bindings,
                                       parameterize_strings, validate_question_sources, validate_generation_claim)
    from qa_agent.nlu.linker import LinkResult, ValueLinker
    from qa_agent.nlu.value_index import load_value_index

    intent = IntentContract(route="sql", task_type="lookup")
    last_sql = None
    linked = LinkResult(request.message, request.message, [], [], [], "not_loaded")

    def failed(*args, **kwargs):
        result = _error_envelope(*args, **kwargs)
        result.metadata["nlu"] = linked.as_dict()
        result.rewritten_question = linked.rewritten_question if linked.patches else None
        return result

    try:
        with trace.step("config_check") as step:
            step.output_summary = settings.public()
            if not settings.db_url:
                raise ValueError("请先在本地 .env 配置 CHINOOK_DB_URL（兼容 DB_URL）。")
            if not settings.llm_configured and isinstance(llm, JsonLLM):
                raise MissingCredentialError()
        with trace.step("catalog", {"db_id": "chinook"}) as step:
            catalog = load_catalog(settings.catalog_path)
            step.output_summary = {"table_count": len(catalog.tables)}
        with trace.step("requested_source_check") as step:
            requested_tables = validate_question_sources(request.message, catalog)
            step.output_summary = {"explicit_tables": requested_tables, "unknown_sources": False}
        with trace.step("value_link", {"enabled": settings.nlu_enabled}) as step:
            index = load_value_index(settings.value_index_path) if settings.nlu_enabled else None
            if index is None:
                linked.index_status = "disabled" if not settings.nlu_enabled else "missing"
                step.status = "skipped"
                step.output_summary = {"reason": linked.index_status, "bindings": []}
            else:
                def encode_values(texts):
                    from qa_agent.rag.embeddings import get_embedder
                    embedder = get_embedder(settings)
                    if embedder is None:
                        raise ValueError("值链接需要 D1 BGE-M3 模型，但模型尚未找到。")
                    model = index.metadata.get("embedding") or {}
                    current = embedder.metadata()
                    for key in ("model_sha256", "model_revision", "max_length"):
                        if model.get(key) != current.get(key):
                            raise ValueError("值索引与当前 embedding 配置不一致，请重建该值索引。")
                    return embedder.encode(texts)
                linker = ValueLinker(index, settings, llm=llm, encode=encode_values)
                try:
                    linked = linker.link(request.message, trace)
                except Exception:
                    if linker.last_result is not None:
                        linked = linker.last_result
                    raise
                intent.filters = linked.bindings
                intent.unresolved = [item.as_dict() for item in linked.ambiguous]
                step.output_summary = {"mention_count": len(linked.mentions), "bindings": linked.bindings,
                                       "ambiguous_count": len(linked.ambiguous), "index_status": linked.index_status}
        with trace.step("rewrite", {"original_question": request.message}) as step:
            step.output_summary = {"rewritten_question": linked.rewritten_question,
                                   "patches": [patch.as_dict() for patch in linked.patches]}
            if not linked.patches:
                step.status = "skipped"
        if linked.ambiguous:
            choices = [{"mention_id": item.mention_id, "original_text": item.original_text,
                        "candidates": item.candidates} for item in linked.ambiguous]
            answer = "这个说法有多个可用解释，请用候选中的明确名称重新提问。"
            with trace.step("clarification_gate") as step:
                step.status = "warn"
                step.output_summary = {"ambiguity_count": len(choices), "mode": "d2_reask_with_explicit_value"}
            return AnswerEnvelope(trace_id=trace.trace_id, status="NEEDS_CLARIFICATION", answer=answer,
                                  rewritten_question=linked.rewritten_question if linked.patches else None,
                                  clarification={"question": answer, "options": choices, "resume_supported": False},
                                  intent=intent, steps=trace.steps,
                                  metadata={"model": settings.llm_model, "db_id": "chinook", "latency_ms": trace.latency_ms,
                                            "nlu": linked.as_dict()})
        repair_error = None
        for attempt in range(settings.sql_repair_attempts + 1):
            with trace.step("sql_gen", {"question": linked.rewritten_question, "repair_attempt": attempt}) as step:
                generation = generate_sql(linked.rewritten_question, catalog, llm, trace,
                                          previous_sql=last_sql, error=repair_error,
                                          intent=intent, bindings=linked.bindings)
                last_sql = generation.sql
                step.output_summary = {"sql": generation.sql, "explanation": generation.explanation}
            try:
                with trace.step("sql_validate", {"sql": last_sql}) as step:
                    validated = validate_sql(last_sql, catalog, max_rows=settings.max_rows)
                    last_sql = validated.sql
                    validate_generation_claim(request.message, last_sql, generation.explanation)
                    if not validated.tables_used:
                        raise SQLValidationError("问数 SQL 必须引用真实业务表，不能以常量代替数据库查询。")
                    if len(validated.tables_used) > 1:
                        raise SQLValidationError("当前 SQL 通道只支持单表查询；跨表问题按后续计划实现。")
                    if requested_tables and set(validated.tables_used) != set(requested_tables):
                        raise SQLValidationError("生成 SQL 改变了原问题显式指定的业务表，禁止替换查询来源。")
                    step.output_summary = {"tables": validated.tables_used,
                                           "default_limit_added": validated.default_limit_added,
                                           "sql": last_sql}
                with trace.step("sql_binding_validate", {"binding_count": len(linked.bindings)}) as step:
                    validate_value_bindings(last_sql, catalog, linked.bindings)
                    step.output_summary = {"verified": True, "bindings": linked.bindings,
                                           "mode": "qualified_ast_mandatory_filters"}
            except SQLValidationError as exc:
                if attempt >= settings.sql_repair_attempts:
                    raise
                repair_error = sanitize_error(exc, settings)
                with trace.step("sql_repair", {"attempt": attempt + 1}) as step:
                    step.status, step.output_summary = "warn", {"reason": repair_error, "preserve_bindings": True}
                continue
            try:
                executable_sql, parameters = parameterize_strings(last_sql) if linked.bindings else (last_sql, {})
                result = execute_sql(executable_sql, settings.db_url,
                                     statement_timeout_ms=settings.statement_timeout_ms,
                                     max_rows=settings.max_rows, trace=trace, parameters=parameters)
                break
            except SQLTimeoutError:
                raise
            except SQLExecutionError as exc:
                repairable_states = {"42601", "42703", "42P01", "42883", "42804", "42803", "42702"}
                if attempt >= settings.sql_repair_attempts or exc.sqlstate not in repairable_states:
                    raise
                repair_error = sanitize_error(exc, settings)
        with trace.step("answer") as step:
            if not result.rows:
                status = "EMPTY_RESULT"
                answer = "按原问题条件未查到记录。"
            elif len(result.rows) == 1 and len(result.columns) == 1:
                status = "SUCCEEDED"
                value = result.rows[0][0]
                answer = "查询结果为 NULL，没有可汇总的值。" if value is None else f"查询结果：{value}。"
            else:
                status = "SUCCEEDED"
                answer = f"查询返回 {result.row_count} 行，详细数据见结果表。"
            if result.truncated:
                answer += f"本次最多展示 {settings.max_rows} 行。"
            step.output_summary = {"status": status, "summary_source": "database_result_template"}
        return AnswerEnvelope(
            trace_id=trace.trace_id, status=status, answer=answer, sql=last_sql,
            rewritten_question=linked.rewritten_question if linked.patches else None,
            table=result.table, intent=intent, steps=trace.steps,
            metadata={"model": settings.llm_model, "db_id": "chinook", "result_columns": result.columns,
                      "truncated": result.truncated, "latency_ms": trace.latency_ms, "nlu": linked.as_dict()},
        )
    except MissingCredentialError as exc:
        return failed(trace, settings, str(exc), exc.code, intent=intent)
    except LLMError as exc:
        return failed(trace, settings, str(exc), exc.code, exc.retryable, last_sql, intent)
    except SQLValidationError as exc:
        return failed(trace, settings, f"SQL 未通过校验：{sanitize_error(exc, settings)}", "sql_rejected", sql=last_sql, intent=intent)
    except SQLTimeoutError as exc:
        return failed(trace, settings, "数据库查询超过允许时限。", "sql_timeout", sql=last_sql, intent=intent)
    except SQLExecutionError as exc:
        return failed(trace, settings, f"数据库查询失败：{sanitize_error(exc, settings)}", "sql_execution", sql=last_sql, intent=intent)
    except Exception as exc:
        return failed(trace, settings, sanitize_error(exc, settings), "pipeline_error", sql=last_sql, intent=intent)


def chat(request: ChatRequest, llm: JsonLLM | None = None,
         settings: Settings | None = None) -> AnswerEnvelope:
    settings = settings or get_settings()
    trace = TraceRecorder(settings=settings)
    with trace.step("route", {"selected": request.scope.route}) as step:
        step.output_summary = {"route": request.scope.route, "mode": "explicit_source_scope"}
    if request.scope.route == "doc":
        return _doc(request, trace, settings)
    if request.scope.route != "sql":
        return _unsupported(trace, "D1 先使用显式来源范围，请选择 sql 或指定单文档 doc。")
    if request.scope.db_id != "chinook":
        return _unsupported(trace, "D1 SQL 通道仅支持 Chinook 数据库。")
    if request.scope.doc_ids:
        return _unsupported(trace, "SQL 请求请清空 doc_ids；混合来源查询按后续计划实现。")
    return _sql(request, trace, settings, llm or JsonLLM(settings))
