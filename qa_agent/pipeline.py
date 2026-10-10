"""D1 dispatch and SQL pipeline. No evaluation labels are read by this service."""
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
    from qa_agent.sql.validator import SQLValidationError, validate_sql

    intent = IntentContract(route="sql", task_type="lookup")
    last_sql = None
    try:
        with trace.step("config_check") as step:
            step.output_summary = settings.public()
            if not settings.db_url:
                raise ValueError("请先在本地 .env 配置 DB_URL。")
            if not settings.llm_configured and isinstance(llm, JsonLLM):
                raise MissingCredentialError()
        with trace.step("catalog", {"db_id": "chinook"}) as step:
            catalog = load_catalog(settings.catalog_path)
            step.output_summary = {"table_count": len(catalog.tables)}
        repair_error = None
        for attempt in range(settings.sql_repair_attempts + 1):
            with trace.step("sql_gen", {"question": request.message, "repair_attempt": attempt}) as step:
                generation = generate_sql(request.message, catalog, llm, trace,
                                          previous_sql=last_sql, error=repair_error)
                last_sql = generation.sql
                step.output_summary = {"sql": generation.sql, "explanation": generation.explanation}
            with trace.step("sql_validate", {"sql": last_sql}) as step:
                validated = validate_sql(last_sql, catalog, max_rows=settings.max_rows)
                last_sql = validated.sql
                if not validated.tables_used:
                    raise SQLValidationError("问数 SQL 必须引用真实业务表，不能以常量代替数据库查询。")
                if len(validated.tables_used) > 1:
                    raise SQLValidationError("D1 SQL 通道目前只支持单表查询；跨表问题按后续计划实现。")
                step.output_summary = {"tables": validated.tables_used,
                                       "default_limit_added": validated.default_limit_added,
                                       "sql": last_sql}
            try:
                with trace.step("sql_exec", {"sql": last_sql, "db_id": "chinook"}) as step:
                    result = execute_sql(last_sql, settings.db_url,
                                         statement_timeout_ms=settings.statement_timeout_ms,
                                         max_rows=settings.max_rows)
                    step.output_summary = {"row_count": result.row_count, "columns": result.columns,
                                           "truncated": result.truncated}
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
            table=result.table, intent=intent, steps=trace.steps,
            metadata={"model": settings.llm_model, "db_id": "chinook", "result_columns": result.columns,
                      "truncated": result.truncated, "latency_ms": trace.latency_ms},
        )
    except MissingCredentialError as exc:
        return _error_envelope(trace, settings, str(exc), exc.code, intent=intent)
    except LLMError as exc:
        return _error_envelope(trace, settings, str(exc), exc.code, exc.retryable, last_sql, intent)
    except SQLValidationError as exc:
        return _error_envelope(trace, settings, f"SQL 未通过校验：{sanitize_error(exc, settings)}", "sql_rejected", sql=last_sql, intent=intent)
    except SQLTimeoutError as exc:
        return _error_envelope(trace, settings, "数据库查询超过允许时限。", "sql_timeout", sql=last_sql, intent=intent)
    except SQLExecutionError as exc:
        return _error_envelope(trace, settings, f"数据库查询失败：{sanitize_error(exc, settings)}", "sql_execution", sql=last_sql, intent=intent)
    except Exception as exc:
        return _error_envelope(trace, settings, sanitize_error(exc, settings), "pipeline_error", sql=last_sql, intent=intent)


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
