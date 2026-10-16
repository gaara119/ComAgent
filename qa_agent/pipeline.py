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
         llm: JsonLLM, *, generation_context: dict | None = None) -> AnswerEnvelope:
    from qa_agent.sql.catalog import load_catalog
    from qa_agent.sql.executor import SQLExecutionError, SQLTimeoutError, execute_sql
    from qa_agent.sql.generator import generate_sql
    from qa_agent.sql.repair_guard import (string_filter_contract, validate_repair_filters,
                                           validate_chinook_fk_joins)
    from qa_agent.sql.validator import (SQLValidationError, validate_sql, validate_value_bindings,
                                       parameterize_strings, validate_question_sources, validate_generation_claim)
    from qa_agent.nlu.linker import LinkResult, ValueLinker
    from qa_agent.nlu.value_index import load_value_index
    from qa_agent.clarify.service import (run_gate, finish_gate, public_metadata,
                                         question_for_linking, mentions_for_linking, source_dict)
    from qa_agent.clarify.state import DEFAULT_STORE, SessionConflict, verify_resume

    db_id = request.scope.db_id or "chinook"
    db_url = settings.aw_db_url if db_id == "adventureworks" else settings.db_url
    catalog_path = settings.aw_catalog_path if db_id == "adventureworks" else settings.catalog_path
    intent = IntentContract(route="sql", task_type="lookup")
    last_sql = None
    linked = LinkResult(request.message, request.message, [], [], [], "not_loaded")
    gate = None
    schema_bundle = None

    def metadata():
        result = {"model": settings.llm_model, "db_id": db_id, "latency_ms": trace.latency_ms,
                  "nlu": linked.as_dict()}
        if db_id == "adventureworks":
            result["aw_schema_mode"] = settings.aw_schema_mode
        if gate:
            result["clarify"] = public_metadata(gate)
        if schema_bundle:
            result["schema_linker"] = schema_bundle.as_dict()
        return result

    def failed(*args, **kwargs):
        if gate:
            finish_gate(gate, succeeded=False)
        result = _error_envelope(*args, **kwargs)
        result.metadata.update(metadata())
        result.rewritten_question = linked.rewritten_question if linked.patches else None
        return result

    try:
        with trace.step("config_check") as step:
            step.output_summary = {**settings.public(), "selected_db_id": db_id}
            if not db_url:
                raise ValueError("请先在本地 .env 配置 AW_DB_URL。" if db_id == "adventureworks"
                                 else "请先在本地 .env 配置 CHINOOK_DB_URL（兼容 DB_URL）。")
            if not settings.llm_configured and isinstance(llm, JsonLLM):
                raise MissingCredentialError()
        # A stale card fails before value linking, model calls or SQL generation.
        if request.clarification_id:
            with trace.step("clarification_version_check") as step:
                previous = DEFAULT_STORE.get(request.session_id)
                if previous is None:
                    raise SessionConflict("会话已不存在，请重新提交完整问题。")
                verify_resume(previous, request.clarification_id, request.intent_version, source_dict(request))
                step.output_summary = {"verified": True, "intent_version": request.intent_version}
        with trace.step("catalog", {"db_id": db_id}) as step:
            catalog = load_catalog(catalog_path)
            step.output_summary = {"table_count": len(catalog.tables), "db_id": db_id}
        with trace.step("requested_source_check") as step:
            requested_tables = validate_question_sources(request.message, catalog)
            step.output_summary = {"explicit_tables": requested_tables, "unknown_sources": False}
        with trace.step("value_link", {"enabled": settings.nlu_enabled, "db_id": db_id}) as step:
            # Chinook's value index is never used to bind AdventureWorks fields.
            index = load_value_index(settings.value_index_path) if settings.nlu_enabled and db_id == "chinook" else None
            if index is None or request.choice_id:
                linked.index_status = ("explicit_card_choice" if request.choice_id else
                                       "not_registered_for_db" if db_id == "adventureworks" else
                                       "disabled" if not settings.nlu_enabled else "missing")
                step.status = "skipped"
                step.output_summary = {"reason": linked.index_status, "bindings": []}
            else:
                def encode_values(texts):
                    from qa_agent.rag.embeddings import get_embedder
                    embedder = get_embedder(settings)
                    if embedder is None:
                        raise ValueError("值链接需要 BGE-M3 模型，但模型尚未找到。")
                    model = index.metadata.get("embedding") or {}
                    current = embedder.metadata()
                    for key in ("model_sha256", "model_revision", "max_length"):
                        if model.get(key) != current.get(key):
                            raise ValueError("值索引与当前 embedding 配置不一致，请重建该值索引。")
                    return embedder.encode(texts)
                linker = ValueLinker(index, settings, llm=llm, encode=encode_values)
                try:
                    linked = linker.link(question_for_linking(request), trace,mentions=mentions_for_linking(request,index))
                except Exception:
                    if linker.last_result is not None:
                        linked = linker.last_result
                    raise
                step.output_summary = {"mention_count": len(linked.mentions), "bindings": linked.bindings,
                                       "ambiguous_count": len(linked.ambiguous), "index_status": linked.index_status}
        with trace.step("rewrite", {"original_question": request.message}) as step:
            step.output_summary = {"rewritten_question": linked.rewritten_question,
                                   "patches": [patch.as_dict() for patch in linked.patches]}
            if not linked.patches:
                step.status = "skipped"
        with trace.step("clarification_gate") as step:
            gate = run_gate(request, catalog, llm, linked, trace)
            intent = gate.state.intent
            bindings = gate.state.bindings
            question = gate.question
            step.status = "warn" if gate.card else "ok"
            step.output_summary = {"level": gate.decision.level, "intent_version": intent.intent_version,
                                   "issues": [item.as_dict(public=True) for item in gate.decision.issues],
                                   "assumptions": gate.decision.assumptions, "derived": gate.decision.derived,
                                   "invalidated": gate.state.invalidated, "resume_supported": True}
        if gate.card:
            return AnswerEnvelope(trace_id=trace.trace_id, status="NEEDS_CLARIFICATION",
                                  answer=gate.card["question"], clarification=gate.card,
                                  rewritten_question=linked.rewritten_question if linked.patches else None,
                                  intent=intent, steps=trace.steps, metadata=metadata())
        if gate.state.original_question != request.message:
            requested_tables = validate_question_sources(gate.state.original_question, catalog)
        selected_catalog = catalog
        # Only remap an unqualified value-index binding when a stress catalog
        # contains one uniquely identified table. Canonical values and scopes
        # are preserved, and normal public/AW catalogs retain their bindings.
        bindings = [dict(item) for item in bindings]
        for binding in bindings:
            parts = str(binding.get("column", "")).split(".")
            if len(parts) == 2:
                table_name, column_name = parts
                matches = [table for table in catalog.tables
                           if table.name == table_name and column_name in table.column_names]
                if len(matches) == 1 and matches[0].schema != "public":
                    binding["column"] = f"{matches[0].schema}.{table_name}.{column_name}"
        if db_id == "adventureworks" and settings.aw_schema_mode not in {"full", "subgraph"}:
            raise ValueError("AW_SCHEMA_MODE 必须为 full 或 subgraph。")
        if db_id == "adventureworks" and settings.aw_schema_mode == "subgraph":
            with trace.step("schema_link", {"db_id": db_id, "question": question}) as step:
                from qa_agent.sql.schema_linker import SchemaLinker
                from qa_agent.rag.embeddings import get_embedder
                embedder = get_embedder(settings)
                if embedder is None:
                    raise ValueError("AdventureWorks Schema Linking 需要已安装的 BGE-M3 模型。")
                schema_linker = SchemaLinker(catalog, settings.aw_schema_index_path, embedder.encode,
                                             catalog_path=catalog_path)
                schema_bundle = schema_linker.link(question, mentions=[item.original_text for item in linked.mentions],
                                                   value_columns=[item["column"] for item in bindings])
                selected_catalog = schema_bundle.selected_catalog
                step.output_summary = schema_bundle.as_dict()
            from qa_agent.sql.pruner import SchemaPruner
            schema_bundle = SchemaPruner(catalog).prune(
                question, schema_bundle, llm, trace,
                required_columns=[item["column"] for item in bindings])
            selected_catalog = schema_bundle.selected_catalog
        # Lookup names need FK joins even when no alias/candidate was bound.
        # The catalog, FK proof and mandatory-filter checks still govern access.
        allow_joins = db_id in {"chinook", "adventureworks"}
        repair_error = None
        repair_filters = None
        for attempt in range(settings.sql_repair_attempts + 1):
            with trace.step("sql_gen", {"question": question, "repair_attempt": attempt,
                                       "db_id": db_id, "allow_joins": allow_joins}) as step:
                generation = generate_sql(question, selected_catalog, llm, trace,
                                          previous_sql=last_sql, error=repair_error,
                                          intent=intent, bindings=bindings, allow_joins=allow_joins,
                                          context=generation_context)
                last_sql = generation.sql
                step.output_summary = {"sql": generation.sql, "explanation": generation.explanation}
            try:
                current_order = gate.state.analysis.order or {}
                explicit_ranking_order = (gate.state.analysis.task_type == "ranking"
                                          and current_order.get("field")
                                          and current_order.get("direction") in {"asc", "desc"})
                if db_id == "chinook" and (gate.state.resolutions or explicit_ranking_order):
                    from qa_agent.clarify.sql_guard import validate_current_patch_contract
                    with trace.step("sql_current_contract_validate", {"intent_version": gate.state.intent.intent_version}) as step:
                        validate_current_patch_contract(last_sql, selected_catalog,
                                                        gate.state.analysis, gate.state.resolutions)
                        step.output_summary = {"verified": True, "before_repair_filter_capture": True}
                # A rejected draft can contain retired conditions. Do not make
                # them mandatory for subsequent technical repair attempts.
                if repair_filters is None:
                    repair_filters = string_filter_contract(last_sql, selected_catalog)
                with trace.step("sql_validate", {"sql": last_sql}) as step:
                    validated = validate_sql(last_sql, selected_catalog, max_rows=settings.max_rows)
                    last_sql = validated.sql
                    validate_generation_claim(gate.state.original_question, last_sql, generation.explanation)
                    if not validated.tables_used:
                        raise SQLValidationError("问数 SQL 必须引用真实业务表，不能以常量代替数据库查询。")
                    validate_repair_filters(repair_filters, last_sql, selected_catalog)
                    if db_id == "chinook":
                        validate_chinook_fk_joins(last_sql, selected_catalog)
                    if len(validated.tables_used) > 1 and not allow_joins:
                        raise SQLValidationError("该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。")
                    if requested_tables and ((not allow_joins and set(validated.tables_used) != set(requested_tables))
                                             or (allow_joins and not set(requested_tables).issubset(validated.tables_used))):
                        raise SQLValidationError("生成 SQL 改变了原问题显式指定的业务表，禁止替换查询来源。")
                    step.output_summary = {"tables": validated.tables_used,
                                           "default_limit_added": validated.default_limit_added, "sql": last_sql}
                current=(gate.state.analysis.time_scope or {}).get('current')
                if (db_id=='chinook' and gate.state.resolutions and current and
                    gate.state.analysis.task_type not in {'growth','ratio'} and 'invoice' in validated.tables_used):
                    from qa_agent.clarify.sql_guard import validate_confirmed_invoice_period
                    with trace.step('sql_period_validate',{'current':current,'db_id':db_id}) as step:
                        validate_confirmed_invoice_period(last_sql,selected_catalog,current)
                        step.output_summary={'verified':True,'mode':'qualified_invoice_where_period','current':current}
                region=gate.state.analysis.region_scope
                country_fields={item.get('column') for item in bindings if item.get('column') in
                                {'invoice.billing_country','customer.country'}}
                confirmed_region=any(patch.get('path')=='region_scope' and patch.get('op')=='set' and
                                     patch.get('value')==region for resolution in gate.state.resolutions
                                     for patch in resolution.get('patches',[]))
                if (db_id=='chinook' and confirmed_region and region in {'invoice.billing_country','customer.country'}
                    and not (country_fields-{region})):
                    from qa_agent.clarify.sql_guard import validate_confirmed_country_output
                    with trace.step('sql_region_validate',{'region_scope':region,'db_id':db_id}) as step:
                        validate_confirmed_country_output(last_sql,selected_catalog,region)
                        step.output_summary={'verified':True,'mode':'qualified_country_result_sources','region_scope':region}
                with trace.step("sql_binding_validate", {"binding_count": len(bindings)}) as step:
                    ratio_context = ({"task_type": "ratio", "numerator": gate.state.analysis.numerator,
                                      "metric": gate.state.analysis.metric,
                                      "denominator": gate.state.analysis.denominator,
                                      "time_scope": gate.state.analysis.time_scope,
                                      "region_scope": gate.state.analysis.region_scope,
                                      "question": gate.state.original_question,
                                      "verified_original_surfaces": [item.original_text for item in linked.mentions
                                                                     if item.status == "resolved"]}
                                     if gate.state.analysis.task_type == "ratio" else None)
                    validate_value_bindings(last_sql, selected_catalog, bindings, ratio_context=ratio_context)
                    step.output_summary = {"verified": True, "bindings": bindings,
                                           "mode": "qualified_ast_scoped_ratio_or_mandatory_filters" if ratio_context
                                           else "qualified_ast_mandatory_filters"}
                if generation_context:
                    from qa_agent.fusion.planner import validate_fusion_sql
                    with trace.step("fusion_plan_validate", {"kind": generation_context.get("kind")}) as step:
                        validate_fusion_sql(last_sql, selected_catalog, generation_context)
                        step.output_summary = {"verified": True, "before_readonly_execution": True}
            except SQLValidationError as exc:
                if attempt >= settings.sql_repair_attempts:
                    raise
                repair_error = sanitize_error(exc, settings)
                with trace.step("sql_repair", {"attempt": attempt + 1}) as step:
                    step.status, step.output_summary = "warn", {"reason": repair_error, "preserve_bindings": True}
                continue
            try:
                executable_sql, parameters = parameterize_strings(last_sql) if bindings else (last_sql, {})
                result = execute_sql(executable_sql, db_url, statement_timeout_ms=settings.statement_timeout_ms,
                                     max_rows=settings.max_rows, trace=trace, parameters=parameters, db_id=db_id)
                break
            except SQLTimeoutError:
                raise
            except SQLExecutionError as exc:
                repairable_states = {"42601", "42703", "42P01", "42883", "42804", "42803", "42702"}
                if attempt >= settings.sql_repair_attempts or exc.sqlstate not in repairable_states:
                    raise
                repair_error = sanitize_error(exc, settings)
        from qa_agent.sql.result_format import percentage_formats, display_percentage
        result_formats = percentage_formats(last_sql, result.columns, intent.task_type)
        with trace.step("answer") as step:
            if not result.rows:
                status = "EMPTY_RESULT"
                answer = "按原问题条件未查到记录。"
            elif len(result.rows) == 1 and len(result.columns) == 1:
                status = "SUCCEEDED"
                value = result.rows[0][0]
                displayed = display_percentage(value, result_formats[result.columns[0]]) if result.columns[0] in result_formats else value
                answer = "查询结果为 NULL，没有可汇总的值。" if value is None else f"查询结果：{displayed}。"
            else:
                status = "SUCCEEDED"
                answer = f"查询返回 {result.row_count} 行，详细数据见结果表。"
            if result.truncated:
                answer += f"本次最多展示 {settings.max_rows} 行。"
            if gate.decision.assumptions:
                answer += "\n口径说明：" + " ".join(gate.decision.assumptions)
            step.output_summary = {"status": status, "summary_source": "database_result_template"}
        finish_gate(gate, succeeded=True)
        return AnswerEnvelope(trace_id=trace.trace_id, status=status, answer=answer, sql=last_sql,
                              rewritten_question=linked.rewritten_question if linked.patches else None,
                              table=result.table, intent=intent, steps=trace.steps,
                              metadata={**metadata(), "result_columns": result.columns, "truncated": result.truncated,
                                        "result_format": result_formats})
    except SessionConflict as exc:
        return failed(trace, settings, str(exc), "clarification_conflict", intent=intent)
    except MissingCredentialError as exc:
        return failed(trace, settings, str(exc), exc.code, intent=intent)
    except LLMError as exc:
        return failed(trace, settings, str(exc), exc.code, exc.retryable, last_sql, intent)
    except SQLValidationError as exc:
        return failed(trace, settings, f"SQL 未通过校验：{sanitize_error(exc, settings)}", "sql_rejected", sql=last_sql, intent=intent)
    except SQLTimeoutError:
        return failed(trace, settings, "数据库查询超过允许时限。", "sql_timeout", sql=last_sql, intent=intent)
    except SQLExecutionError as exc:
        return failed(trace, settings, f"数据库查询失败：{sanitize_error(exc, settings)}", "sql_execution", sql=last_sql, intent=intent)
    except Exception as exc:
        return failed(trace, settings, sanitize_error(exc, settings), "pipeline_error", sql=last_sql, intent=intent)



def chat(request: ChatRequest, llm: JsonLLM | None = None,
         settings: Settings | None = None) -> AnswerEnvelope:
    settings = settings or get_settings()
    if request.scope.db_id == "aw":
        request = request.model_copy(update={"scope": request.scope.model_copy(update={"db_id": "adventureworks"})})
    trace = TraceRecorder(settings=settings)
    with trace.step("route", {"selected": request.scope.route}) as step:
        step.output_summary = {"route": request.scope.route, "mode": "explicit_source_scope"}
    if request.scope.route == "doc":
        return _doc(request, trace, settings)
    if request.scope.route in {"auto", "hybrid"}:
        from qa_agent.fusion.planner import classify_route, run_hybrid
        from qa_agent.clarify.state import DEFAULT_STORE
        route = classify_route(request)
        if route in {"sql_to_doc", "doc_to_sql"}:
            with DEFAULT_STORE.locked(request.session_id):
                return run_hybrid(request, trace, settings, llm or JsonLLM(settings), _sql)
        if request.scope.route == "auto" and route == "doc":
            return _doc(request.model_copy(update={"scope": request.scope.model_copy(update={"route": "doc", "db_id": None})}), trace, settings)
        if request.scope.route == "auto" and route == "sql":
            request = request.model_copy(update={"scope": request.scope.model_copy(update={"route": "sql"})})
        else:
            return _unsupported(trace, "请选择已支持的跨源流程：艺术家销售排名与介绍，或手册客单价定义与计算。")
    if request.scope.route != "sql":
        return _unsupported(trace, "D1 先使用显式来源范围，请选择 sql 或指定单文档 doc。")
    if request.scope.db_id not in {"chinook", "adventureworks"}:
        return _unsupported(trace, "SQL 来源请选择 Chinook 或 AdventureWorks 数据库。")
    if request.scope.doc_ids:
        return _unsupported(trace, "SQL 请求请清空 doc_ids；混合来源查询按后续计划实现。")
    from qa_agent.clarify.state import DEFAULT_STORE
    with DEFAULT_STORE.locked(request.session_id):
        return _sql(request, trace, settings, llm or JsonLLM(settings))
