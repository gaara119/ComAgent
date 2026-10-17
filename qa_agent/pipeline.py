"""Shared dispatch and incremental SQL pipeline; no evaluation labels are read."""
from __future__ import annotations

import importlib
import inspect
import re

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
        if envelope.metadata.get('clarify') is None:
            from qa_agent.clarify.answer_metadata import completed_source_only_level
            envelope.metadata['clarify']=completed_source_only_level({'document':{
                'source':'documents','status':envelope.status,'warnings':envelope.metadata.get('warnings')}})
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
    from qa_agent.ablation import semantic_gate_enabled, bypass_gate, bypass_metadata
    from qa_agent.sql.ranked_subset_guard import (preflight_ranked_ratio_contract,
                                                  RankedRatioContractUnsupported)

    use_semantic_gate = semantic_gate_enabled()

    db_id = request.scope.db_id or "chinook"
    db_url = settings.aw_db_url if db_id == "adventureworks" else settings.db_url
    catalog_path = settings.aw_catalog_path if db_id == "adventureworks" else settings.catalog_path
    intent = IntentContract(route="sql", task_type="lookup")
    last_sql = None
    linked = LinkResult(request.message, request.message, [], [], [], "not_loaded")
    source_entity_hints = []
    gate = None
    schema_bundle = None
    groupwise_presentation_proof = None

    def metadata():
        result = {"model": settings.llm_model, "db_id": db_id, "latency_ms": trace.latency_ms,
                  "typed_sql_compiler_enabled": settings.typed_sql_compiler_enabled,
                  "nlu": linked.as_dict()}
        if source_entity_hints:
            result['nlu']['source_entity_hints'] = source_entity_hints
        if db_id == "adventureworks":
            result["aw_schema_mode"] = settings.aw_schema_mode
            result["aw_schema_pruning_enabled"] = settings.aw_schema_pruning_enabled
        if gate:
            result["clarify"] = public_metadata(gate) if use_semantic_gate else bypass_metadata(gate)
        if schema_bundle:
            result["schema_linker"] = schema_bundle.as_dict()
        return result

    def failed(*args, **kwargs):
        if gate and use_semantic_gate:
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
            if not use_semantic_gate:
                raise SessionConflict("当前累计消融组关闭语义澄清，不消费其它实验组的澄清卡片。")
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
            from qa_agent.sql.source_authority import requested_source_contract
            source_contract = requested_source_contract(request.message, catalog, generation_context)
            composed_step = bool(generation_context and generation_context.get("kind") == "composed")
            requested_tables = [] if composed_step else source_contract["explicit_tables"]
            step.output_summary = {**source_contract, "coverage_scope": "whole_plan" if composed_step else "this_query"}
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
                    linked = linker.link(question_for_linking(request) if use_semantic_gate else request.message,
                        trace, mentions=mentions_for_linking(request,index) if use_semantic_gate else None)
                except Exception:
                    if linker.last_result is not None:
                        linked = linker.last_result
                    raise
                step.output_summary = {"mention_count": len(linked.mentions), "bindings": linked.bindings,
                                       "ambiguous_count": len(linked.ambiguous), "index_status": linked.index_status}
                from qa_agent.nlu.features import enabled
                if settings.nlu_enabled and not use_semantic_gate and enabled('AGENT_LINK_GROUNDING_ENABLED'):
                    from qa_agent.nlu.source_elements import collect_source_elements
                    source_entity_hints = collect_source_elements(catalog, index, linked.bindings,
                        session_id=request.session_id, mentions=linked.mentions,
                        linking_question=linked.original_question)
                    if source_entity_hints:
                        step.output_summary['source_entity_hints'] = source_entity_hints
        with trace.step("rewrite", {"original_question": request.message}) as step:
            step.output_summary = {"rewritten_question": linked.rewritten_question,
                                   "patches": [patch.as_dict() for patch in linked.patches]}
            if not linked.patches:
                step.status = "skipped"
        with trace.step("clarification_gate") as step:
            gate = (run_gate(request, catalog, llm, linked, trace) if use_semantic_gate
                    else bypass_gate(request, linked))
            intent = gate.state.intent
            bindings = gate.state.bindings
            question = gate.question
            step.status = ("warn" if gate.card else "ok") if use_semantic_gate else "skipped"
            step.output_summary = {"level": gate.decision.level, "intent_version": intent.intent_version,
                                   "semantic_gate_executed": use_semantic_gate,
                                   "issues": [item.as_dict(public=True) for item in gate.decision.issues],
                                   "assumptions": gate.decision.assumptions, "derived": gate.decision.derived,
                                   "invalidated": gate.state.invalidated, "resume_supported": use_semantic_gate}
        if gate.card:
            return AnswerEnvelope(trace_id=trace.trace_id, status="NEEDS_CLARIFICATION",
                                  answer=gate.card["question"], clarification=gate.card,
                                  rewritten_question=linked.rewritten_question if linked.patches else None,
                                  intent=intent, steps=trace.steps, metadata=metadata())
        if use_semantic_gate:
            # Unsupported intent structure cannot be repaired by resampling SQL.
            # The later SQL proof reuses this state check, without treating a
            # supported state as proof of the generated SQL or actual result.
            with trace.step("semantic_contract_preflight") as step:
                step.output_summary = preflight_ranked_ratio_contract(gate.state.analysis, catalog=catalog)
        if gate.state.original_question != request.message:
            restored_source = requested_source_contract(gate.state.original_question, catalog, generation_context)
            requested_tables = [] if generation_context and generation_context.get("kind") == "composed" else restored_source["explicit_tables"]
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
            from qa_agent.sql.pruner import apply_optional_pruning
            schema_bundle = apply_optional_pruning(
                question, schema_bundle, catalog, llm, trace,
                enabled=settings.aw_schema_pruning_enabled,
                required_columns=[item["column"] for item in bindings])
            selected_catalog = schema_bundle.selected_catalog
        # Lookup names need FK joins even when no alias/candidate was bound.
        # The catalog, FK proof and mandatory-filter checks still govern access.
        allow_joins = db_id in {"chinook", "adventureworks"}
        repair_error = None
        repair_filters = None
        disabled_semantics = {"verified": False, "mode": "disabled_cumulative_semantic_gate"}
        semantic_sql_proof = dict(disabled_semantics)
        partition_proof = dict(disabled_semantics)
        typed_ratio_proof = dict(disabled_semantics)
        comparison_proof = dict(disabled_semantics)
        ratio_context = None
        for attempt in range(settings.sql_repair_attempts + 1):
            with trace.step("sql_gen", {"question": question, "repair_attempt": attempt,
                                       "db_id": db_id, "allow_joins": allow_joins}) as step:
                compiled = None
                if use_semantic_gate and attempt == 0 and db_id == "chinook" and settings.typed_sql_compiler_enabled:
                    from qa_agent.sql.typed_contract_compiler import compile_typed_contract
                    compiled = compile_typed_contract(gate.state.analysis, selected_catalog)
                if compiled is not None:
                    from qa_agent.schemas import SQLGeneration
                    generation = SQLGeneration(sql=compiled.sql, tables_used=["invoice"],
                        explanation="按本轮已确认的结构化统计条件构建查询，仍须通过相同SQL校验和只读执行。")
                else:
                    generation = generate_sql(question, selected_catalog, llm, trace,
                                          previous_sql=last_sql, error=repair_error,
                                          intent=intent, bindings=bindings, allow_joins=allow_joins,
                                          context=generation_context,
                                          semantic_intent=gate.state.analysis if use_semantic_gate else None,
                                          use_semantic_contract=use_semantic_gate,
                                          task_input={"effective_question": getattr(gate.state, "effective_question", gate.state.original_question),
                                              "original_question": gate.state.original_question,
                                              "has_applied_patches": bool(gate.state.resolutions),
                                              "intent_version": gate.state.intent.intent_version}
                                               if use_semantic_gate else None,
                                          **({'source_entity_hints': source_entity_hints} if source_entity_hints else {}))
                last_sql = generation.sql
                step.output_summary = {"sql": generation.sql, "explanation": generation.explanation,
                    "generation_method": compiled.method if compiled is not None else "llm",
                    "compiler_attempted": use_semantic_gate and attempt == 0 and db_id == "chinook" and settings.typed_sql_compiler_enabled}
            try:
                if schema_bundle:
                    # Backward grounding uses only the model's real draft and
                    # the authentic catalog, never expected table labels.
                    try:
                        validate_sql(last_sql, selected_catalog, max_rows=settings.max_rows)
                    except SQLValidationError:
                        from qa_agent.sql.schema_linker import augment_bundle_from_sql
                        with trace.step("schema_backward_recall") as backward:
                            augmented = augment_bundle_from_sql(schema_bundle, catalog, last_sql)
                            if len(augmented.disconnected_components) > 1:
                                raise SQLValidationError("草稿补回的表在真实外键图中不连通。")
                            schema_bundle = augmented
                            selected_catalog = augmented.selected_catalog
                            backward.output_summary = augmented.as_dict()
                # Reject malformed/non-SELECT drafts before semantic lineage
                # routines assume a SELECT root. Keep display LIMIT insertion
                # deferred until after the original contract has been checked.
                with trace.step("sql_safety_preflight") as safety_step:
                    prevalidated = validate_sql(last_sql, selected_catalog, max_rows=settings.max_rows)
                    safety_step.output_summary = {"verified": True, "before_semantic_proofs": True}
                from qa_agent.sql.aggregate_null_guard import validate_aggregate_null_fallback
                with trace.step("sql_aggregate_null_validate") as null_step:
                    null_step.output_summary = validate_aggregate_null_fallback(
                        last_sql, selected_catalog, gate.state.analysis)
                if use_semantic_gate:
                    from qa_agent.sql.ranked_entity_domain import validate_ranked_entity_domain
                    with trace.step('sql_ranked_entity_domain_validate') as entity_step:
                        entity_step.output_summary = validate_ranked_entity_domain(
                            last_sql, catalog, gate.state.analysis,
                            question=gate.state.original_question + '\n' + request.message)
                    if db_id == "chinook":
                        from qa_agent.sql.repeat_qualification_guard import validate_repeat_qualification
                        with trace.step("sql_registered_repeat_qualification") as repeat_step:
                            repeat_step.output_summary = validate_repeat_qualification(
                                last_sql, selected_catalog, gate.state.analysis)
                        from qa_agent.sql.employee_domain_guard import validate_employee_domain
                        with trace.step("sql_employee_domain_validate") as employee_step:
                            employee_step.output_summary = validate_employee_domain(
                                last_sql, selected_catalog, gate.state.analysis,
                                question=gate.state.original_question)
                    # Initial requests also have typed obligations (e.g. DISTINCT
                    # track identity). The guard itself selects applicable proofs;
                    # routing only clarified/ranking requests would bypass them.
                    if db_id == "chinook":
                        from qa_agent.clarify.sql_guard import validate_current_patch_contract
                        with trace.step("sql_current_contract_validate", {"intent_version": gate.state.intent.intent_version}) as step:
                            validate_current_patch_contract(last_sql, selected_catalog,
                                                            gate.state.analysis, gate.state.resolutions)
                            step.output_summary = {"verified": True, "before_repair_filter_capture": True}
                        from qa_agent.sql.temporal_field_role_guard import validate_temporal_field_role
                        with trace.step("sql_temporal_field_role_validate") as temporal_step:
                            temporal_step.output_summary = validate_temporal_field_role(
                                last_sql, selected_catalog, gate.state.analysis,
                                question=gate.state.original_question)
                    from qa_agent.sql.semantic_guard import validate_question_semantics
                    with trace.step("sql_semantic_contract", {"intent_version": intent.intent_version}) as step:
                        semantic_sql_proof = validate_question_semantics(
                            question, last_sql, selected_catalog, intent=gate.state.analysis)
                        step.output_summary = semantic_sql_proof
                    from qa_agent.sql.scope_guard import validate_unrestricted_geography
                    with trace.step("sql_active_scope_validate") as scope_step:
                        scope_step.output_summary = validate_unrestricted_geography(last_sql, selected_catalog, gate.state.analysis, question=gate.state.original_question)
                    from qa_agent.sql.partition_guard import validate_partition_comparison
                    with trace.step("sql_partition_contract") as partition_step:
                        partition_proof = validate_partition_comparison(last_sql, selected_catalog, gate.state.analysis)
                        partition_step.output_summary = partition_proof
                    from qa_agent.sql.ratio_scope_guard import validate_typed_ratio_scope
                    with trace.step('sql_ratio_operand_scope') as ratio_step:
                        typed_ratio_proof = validate_typed_ratio_scope(last_sql, selected_catalog,
                                                                      gate.state.analysis, bindings)
                        ratio_step.output_summary = typed_ratio_proof
                    with trace.step("sql_binding_validate", {"binding_count": len(bindings)}) as step:
                        ratio_context = ({"task_type": "ratio", "numerator": gate.state.analysis.numerator,
                                          "metric": gate.state.analysis.metric,
                                          "denominator": gate.state.analysis.denominator,
                                          "time_scope": gate.state.analysis.time_scope,
                                          "region_scope": gate.state.analysis.region_scope,
                                          "query_scope": gate.state.analysis.query_scope,
                                          "output_requirements": gate.state.analysis.output_requirements,
                                          "question": gate.state.original_question,
                                          "verified_original_surfaces": [item.original_text for item in linked.mentions
                                                                         if item.status == "resolved"]}
                                         if gate.state.analysis.task_type == "ratio" else None)
                        if ratio_context is not None:
                            from qa_agent.context import current_context
                            active_context = current_context()
                            ratio_context['user_brief'] = active_context.text if active_context else ''
                            ratio_context['named_scope_evidence'] = str((
                                (gate.state.analysis.condition_sources or {}).get('region_scope') or
                                (gate.state.analysis.condition_sources or {}).get('filters') or {}).get('evidence') or '')
                        if typed_ratio_proof.get('mode') != 'typed_physical_ratio_operands':
                            validate_value_bindings(last_sql, selected_catalog, bindings, ratio_context=ratio_context)
                        step.output_summary = {"verified": True, "bindings": bindings,
                            "before_repair_filter_capture": True,
                            "mode": typed_ratio_proof['mode'] if typed_ratio_proof.get('mode') == 'typed_physical_ratio_operands'
                                    else "qualified_ast_scoped_ratio_or_mandatory_filters" if ratio_context
                                    else "qualified_ast_mandatory_filters"}
                else:
                    with trace.step("semantic_checks_disabled") as disabled:
                        disabled.status = "skipped"
                        disabled.output_summary = dict(disabled_semantics)
                if generation_context:
                    from qa_agent.fusion.planner import validate_fusion_sql
                    with trace.step("fusion_plan_validate", {"kind": generation_context.get("kind"),
                            "original_sql": last_sql, "before_program_row_limit": True}) as step:
                        fusion_proof = validate_fusion_sql(last_sql, selected_catalog, generation_context)
                        step.output_summary = {"verified": True, "before_program_row_limit": True,
                            "before_readonly_execution": True, "definition_proof": fusion_proof}
                # A rejected draft can contain retired conditions. Do not make
                # them mandatory for subsequent technical repair attempts.
                if repair_filters is None:
                    repair_filters = string_filter_contract(last_sql, selected_catalog)
                with trace.step("sql_validate", {"sql": last_sql}) as step:
                    validated = prevalidated
                    last_sql = validated.sql
                    validate_generation_claim(gate.state.original_question, last_sql, generation.explanation,
                                              generation_context=generation_context)
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
                if (getattr(gate.state.analysis,'query_scope',{})or{}).get('ranking_scope')=='per_group':
                    from qa_agent.sql.semantic_guard import validate_groupwise_ranking
                    with trace.step('sql_groupwise_output_order')as order_step:
                        groupwise_presentation_proof=validate_groupwise_ranking(last_sql,selected_catalog,gate.state.analysis)
                        order_step.output_summary=groupwise_presentation_proof
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
            except SQLValidationError as exc:
                if isinstance(exc, RankedRatioContractUnsupported) or attempt >= settings.sql_repair_attempts:
                    raise
                repair_error = sanitize_error(exc, settings)
                with trace.step("sql_repair", {"attempt": attempt + 1}) as step:
                    step.status, step.output_summary = "warn", {"reason": repair_error, "preserve_bindings": True}
                continue
            try:
                executable_sql, parameters = parameterize_strings(last_sql) if bindings else (last_sql, {})
                result = execute_sql(executable_sql, db_url, statement_timeout_ms=settings.statement_timeout_ms,
                                     max_rows=settings.max_rows, trace=trace, parameters=parameters, db_id=db_id)
                if use_semantic_gate:
                    from qa_agent.sql.comparison_result import validate_comparison_result
                    with trace.step("sql_result_contract") as result_step:
                        comparison_proof = validate_comparison_result(gate.question, last_sql, selected_catalog,
                            result.table, intent=gate.state.analysis)
                        result_step.output_summary = comparison_proof
                    from qa_agent.sql.partition_result import bind_partition_result
                    from qa_agent.sql.ranking_result import validate_ranking_result
                    with trace.step('sql_actual_projection_validate') as projection_step:
                        partition_proof = bind_partition_result(partition_proof, result.columns, result.table)
                        ranking_proof = validate_ranking_result(last_sql, selected_catalog, gate.state.analysis,
                                                               result.columns, result.table)
                        projection_step.output_summary = {'partition':partition_proof,'ranking':ranking_proof}
                else:
                    with trace.step("semantic_result_checks_disabled") as disabled:
                        disabled.status = "skipped"
                        disabled.output_summary = dict(disabled_semantics)
                break
            except SQLValidationError as exc:
                if isinstance(exc, RankedRatioContractUnsupported) or attempt >= settings.sql_repair_attempts:
                    raise
                repair_error = sanitize_error(exc, settings)
                with trace.step("sql_repair", {"attempt": attempt + 1}) as repair_step:
                    repair_step.status = "warn"
                    repair_step.output_summary = {"reason": repair_error, "stage": "actual_result_contract", "preserve_bindings": True}
                continue
            except SQLTimeoutError:
                raise
            except SQLExecutionError as exc:
                repairable_states = {"42601", "42703", "42P01", "42883", "42804", "42803", "42702"}
                if attempt >= settings.sql_repair_attempts or exc.sqlstate not in repairable_states:
                    raise
                repair_error = sanitize_error(exc, settings)
        from qa_agent.sql.result_format import percentage_formats, display_percentage, presentation_formats
        result_formats = percentage_formats(last_sql, result.columns, intent.task_type, catalog=selected_catalog)
        from qa_agent.sql.ratio_presentation import (describe_typed_ratio,
            describe_verified_invoice_share, describe_customer_winner_ratio)
        ratio_basis = ((describe_typed_ratio(typed_ratio_proof) or
                       describe_customer_winner_ratio(semantic_sql_proof, gate.state.analysis) or
                       describe_verified_invoice_share(last_sql, selected_catalog, bindings, ratio_context))
                       if use_semantic_gate else None)
        presentation_labels = {}
        with trace.step("answer") as step:
            status = "SUCCEEDED" if result.rows else "EMPTY_RESULT"
            from qa_agent.context import current_context
            from qa_agent.sql.presentation import present
            user_context = current_context()
            result_formats = presentation_formats(last_sql, result.columns, result_formats,
                query_scope=getattr(gate.state.analysis, "query_scope", {}),
                brief=user_context.text if user_context else "", catalog=selected_catalog)
            answer, presentation_labels = present(gate.state.original_question, result.table,
                result.columns, result_formats, metric=intent.metric,
                brief=user_context.text if user_context else "", task_type=intent.task_type,
                sql=last_sql, query_scope=getattr(gate.state.analysis, "query_scope", {}),
                partition_proof=partition_proof, ratio_basis=ratio_basis,
                groupwise_proof=groupwise_presentation_proof,
                comparison_proof=comparison_proof, catalog=selected_catalog,
                semantic_intent=gate.state.analysis)
            if result.truncated:
                answer += f"本次最多展示 {settings.max_rows} 行。"
            if comparison_proof.get("requires_display") and comparison_proof.get("winner"):
                winner = comparison_proof["winner"]
                other = comparison_proof["right"]["entity"] if winner == comparison_proof["left"]["entity"] else comparison_proof["left"]["entity"]
                comparison_sentence = f"{winner}比{other}多{comparison_proof['difference']}（{comparison_proof['unit']}）。"
                if comparison_sentence not in answer:
                    answer += "\n" + comparison_sentence
            if gate.decision.assumptions:
                answer += "\n口径说明：" + " ".join(gate.decision.assumptions)
            from qa_agent.clarify.answer_metadata import default_action_hint
            switch_hint=default_action_hint(gate.decision.level,getattr(gate.state,'switch_card',None))
            if switch_hint:answer+='\n'+switch_hint
            step.output_summary = {"status": status, "summary_source": "database_result_template",
                                   "ratio_business_basis": ratio_basis}
        if use_semantic_gate:
            finish_gate(gate, succeeded=True)
        return AnswerEnvelope(trace_id=trace.trace_id, status=status, answer=answer, sql=last_sql,
                              rewritten_question=linked.rewritten_question if linked.patches else None,
                              table=result.table, intent=intent, steps=trace.steps,
                              metadata={**metadata(), "result_columns": result.columns, "truncated": result.truncated,
                                        "result_format": result_formats, "column_labels": presentation_labels,
                                        "ratio_business_basis": ratio_basis,
                                        "groupwise_order_proof": groupwise_presentation_proof,
                                        "data_status": "NO_DATA" if not result.table or all(
                                            value is None for row in result.table for value in row.values()) else "AVAILABLE"})
    except SessionConflict as exc:
        return failed(trace, settings, str(exc), "clarification_conflict", intent=intent)
    except MissingCredentialError as exc:
        return failed(trace, settings, str(exc), exc.code, intent=intent)
    except LLMError as exc:
        return failed(trace, settings, str(exc), exc.code, exc.retryable, last_sql, intent)
    except RankedRatioContractUnsupported as exc:
        return failed(trace, settings, str(exc), exc.code, sql=last_sql, intent=intent)
    except SQLValidationError as exc:
        return failed(trace, settings, f"SQL 未通过校验：{sanitize_error(exc, settings)}", "sql_rejected", sql=last_sql, intent=intent)
    except SQLTimeoutError:
        return failed(trace, settings, "数据库查询超过允许时限。", "sql_timeout", sql=last_sql, intent=intent)
    except SQLExecutionError as exc:
        return failed(trace, settings, f"数据库查询失败：{sanitize_error(exc, settings)}", "sql_execution", sql=last_sql, intent=intent)
    except Exception as exc:
        return failed(trace, settings, sanitize_error(exc, settings), "pipeline_error", sql=last_sql, intent=intent)



def _retire_direct_task_plans(request, trace):
    """A newly selected direct/fresh hybrid task replaces both old caches.

    Real card-bound replies remain under their existing version checks. This
    function is called after source authorization and after resume selection,
    never by a tool running inside the current hybrid/composed plan.
    """
    if request.clarification_id:
        return
    from qa_agent.fusion.resume_state import DEFAULT_COMPOSED_STORE
    from qa_agent.fusion.planner import retire_plan
    composed = DEFAULT_COMPOSED_STORE.path(request.session_id).is_file()
    DEFAULT_COMPOSED_STORE.discard(request.session_id)
    legacy = retire_plan(request.session_id)
    if composed or legacy:
        with trace.step("fusion_task_retired", {"authority": "selected_new_direct_task"}) as step:
            step.output_summary = {"composed_retired": composed, "legacy_hybrid_retired": legacy,
                                   "session_only": True}


def _dispatch(request: ChatRequest, llm: JsonLLM | None = None,
         settings: Settings | None = None) -> AnswerEnvelope:
    settings = settings or get_settings()
    if request.scope.db_id == "aw":
        request = request.model_copy(update={"scope": request.scope.model_copy(update={"db_id": "adventureworks"})})
    trace = TraceRecorder(settings=settings)
    # Actual source restrictions precede cached-plan resume and auto fallback.
    from qa_agent.context import current_context
    from qa_agent.source_scope import source_restriction, restriction_conflict
    active_context = current_context()
    restriction = source_restriction(request.message)
    with trace.step("source_scope", {"authority": "actual_current_user_message",
            "original_scope": request.scope.model_dump(mode="json")}) as source_step:
        source_step.output_summary = restriction.public()
    source_error = restriction_conflict(restriction, request.scope.route,
        bool(active_context and active_context.text), request.scope.doc_ids)
    if source_error:
        return _unsupported(trace, source_error)
    from qa_agent.fusion.obligations import explicit_new_task
    from qa_agent.fusion.planner import _explicit_hybrid_kind
    if not request.clarification_id and (explicit_new_task(request.message) or _explicit_hybrid_kind(request.message)):
        _retire_direct_task_plans(request, trace)
    if restriction.mode == "context_only":
        from qa_agent.fusion.composed import run_context_only
        _retire_direct_task_plans(request, trace)
        return run_context_only(request, trace, settings, llm or JsonLLM(settings), restriction)
    if restriction.mode == "documents_only":
        _retire_direct_task_plans(request, trace)
        return _doc(request.model_copy(update={"scope": request.scope.model_copy(
            update={"route": "doc", "db_id": None})}), trace, settings)
    if restriction.mode == "database_only":
        request = request.model_copy(update={"scope": request.scope.model_copy(
            update={"route": "sql", "doc_ids": []})})
    if restriction.mode in {"allowed_set", "local_mixed"}:
        # A source set is an upper bound, not a requirement to call every tool.
        if request.scope.route == "sql":
            request = request.model_copy(update={"scope": request.scope.model_copy(update={"doc_ids": []})})
        elif request.scope.route == "doc":
            _retire_direct_task_plans(request, trace)
            return _doc(request.model_copy(update={"scope": request.scope.model_copy(update={"db_id": None})}), trace, settings)
        else:
            from qa_agent.fusion.composed import run_composed
            from qa_agent.clarify.state import DEFAULT_STORE
            with DEFAULT_STORE.locked(request.session_id):
                return run_composed(request, trace, settings, llm or JsonLLM(settings), _sql,
                                    source_contract=restriction)
    if request.scope.route in {"auto", "hybrid"}:
        from qa_agent.fusion.resume_state import has_pending_composed
        if has_pending_composed(request):
            from qa_agent.fusion.composed import run_composed
            from qa_agent.clarify.state import DEFAULT_STORE
            with DEFAULT_STORE.locked(request.session_id):
                return run_composed(request, trace, settings, llm or JsonLLM(settings), _sql)
    with trace.step("route", {"selected": request.scope.route}) as step:
        step.output_summary = {"route": request.scope.route, "mode": "explicit_source_scope"}
    if request.scope.route == "doc":
        _retire_direct_task_plans(request, trace)
        return _doc(request, trace, settings)
    if request.scope.route in {"auto", "hybrid"}:
        from qa_agent.fusion.planner import classify_route, run_hybrid
        from qa_agent.clarify.state import DEFAULT_STORE
        route = classify_route(request)
        from qa_agent.fusion.composed import needs_composed_plan, run_composed
        if route not in {"sql_to_doc", "doc_to_sql"} and needs_composed_plan(request):
            with DEFAULT_STORE.locked(request.session_id):
                return run_composed(request, trace, settings, llm or JsonLLM(settings), _sql)
        if route in {"sql_to_doc", "doc_to_sql"}:
            from qa_agent.fusion.planner import legacy_resume
            if not legacy_resume(request):
                _retire_direct_task_plans(request, trace)
            with DEFAULT_STORE.locked(request.session_id):
                return run_hybrid(request, trace, settings, llm or JsonLLM(settings), _sql)
        if request.scope.route == "auto" and route == "doc":
            _retire_direct_task_plans(request, trace)
            return _doc(request.model_copy(update={"scope": request.scope.model_copy(update={"route": "doc", "db_id": None})}), trace, settings)
        if request.scope.route == "auto" and route == "sql":
            request = request.model_copy(update={"scope": request.scope.model_copy(update={"route": "sql", "doc_ids": []})})
        else:
            return _unsupported(trace, "请选择已支持的跨源流程：艺术家销售排名与介绍，或手册客单价定义与计算。")
    if request.scope.route != "sql":
        return _unsupported(trace, "D1 先使用显式来源范围，请选择 sql 或指定单文档 doc。")
    if request.scope.db_id not in {"chinook", "adventureworks"}:
        return _unsupported(trace, "SQL 来源请选择 Chinook 或 AdventureWorks 数据库。")
    if request.scope.doc_ids:
        return _unsupported(trace, "SQL 请求请清空 doc_ids；混合来源查询按后续计划实现。")
    from qa_agent.clarify.state import DEFAULT_STORE
    _retire_direct_task_plans(request, trace)
    with DEFAULT_STORE.locked(request.session_id):
        return _sql(request, trace, settings, llm or JsonLLM(settings))


def chat(request: ChatRequest, llm: JsonLLM | None = None,
         settings: Settings | None = None) -> AnswerEnvelope:
    from qa_agent.context import (ContextError, DEFAULT_CONTEXT_STORE,
                                  bind_context)
    settings = settings or get_settings()
    try:
        # Serialize context reads, query execution and actual-history commits.
        from qa_agent.clarify.state import DEFAULT_STORE
        with DEFAULT_STORE.locked(request.session_id):
            context = DEFAULT_CONTEXT_STORE.resolve(request)
            if context.context_id and request.context_id is None:
                # The actual context identity is authoritative even when a
                # client relies on session auto-binding instead of spelling it.
                request = request.model_copy(update={"context_id": context.context_id})
            with bind_context(context):
                response = _dispatch(request, llm=llm, settings=settings)
                DEFAULT_CONTEXT_STORE.record(context, request, response)
                response.metadata["reference_clock"] = {"datetime": context.reference_datetime,
                                                          "timezone": context.timezone}
                if context.context_id:
                    response.metadata["session_context"] = {
                        "context_id": context.context_id, "version": context.version,
                        "content_sha256": context.content_sha256, "characters": len(context.text),
                        "prior_actual_turns": len(context.history), "truncated": False}
                return response
    except ContextError as exc:
        return _error_envelope(TraceRecorder(settings=settings), settings, str(exc), "context_conflict")
