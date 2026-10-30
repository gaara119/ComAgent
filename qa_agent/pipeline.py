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


def _catalog_only_gate(request, linked):
    """Neutral containers for schemas without a registered semantic rule set.

    They carry the actual question through the shared SQL tool; they do not
    execute rules, confirm a metric/default, or persist a clarification state.
    """
    from qa_agent.ablation import BypassGate, BypassState
    from qa_agent.clarify.rules import SemanticIntent
    state = BypassState(original_question=request.message,
        effective_question=request.message, analysis=SemanticIntent(task_type='lookup'),
        intent=IntentContract(route='sql', task_type='lookup'), bindings=[],
        scope=request.scope.model_dump(mode='json'))
    return BypassGate(state=state, question=request.message)


def _doc(request: ChatRequest, trace: TraceRecorder, settings: Settings) -> AnswerEnvelope:
    from qa_agent.rag.task import (DEFAULT_DOCUMENT_TASK_STORE as tasks,
                                   document_entity_candidates, resolve_document_scope)
    intent = IntentContract(route="doc", task_type="doc_qa")
    module_name, separator, function_name = settings.rag_handler.partition(":")
    if not separator or not module_name.startswith("qa_agent.rag."):
        return _error_envelope(trace, settings, "RAG_HANDLER 配置必须指向项目的 qa_agent.rag 模块。", "rag_handler_config")
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name and (module_name == exc.name or module_name.startswith(exc.name + ".")):
            return _unsupported(trace, "文档问答入口未配置，请检查 RAG_HANDLER。")
        return _error_envelope(trace, settings, "文档模块缺少依赖，请按 requirements.txt 安装。", "rag_dependency")
    except ImportError:
        return _error_envelope(trace, settings, "文档模块导入失败，请检查模块及依赖。", "rag_dependency")
    try:
        documents = resolve_document_scope(request, settings)
        allowed_ids = [d['doc_id'] for d in documents]
        question = request.message
        task_metadata = {'original_question': question,
            'original_scope': request.scope.model_dump(mode='json'),
            'allowed_doc_ids': allowed_ids, 'entity_choice_changes_intent': False}
        from qa_agent.ablation import semantic_gate_enabled
        from qa_agent.nlu.features import enabled as feature_enabled
        clarify_enabled = semantic_gate_enabled() and feature_enabled('AGENT_CLARIFY_STATE_ENABLED')
        if request.clarification_id:
            if not clarify_enabled:
                raise ValueError('当前配置关闭澄清，不消费其它配置产生的文档澄清卡。')
            question, selected_ids, resumed = tasks.resume(request, documents)
            task_metadata.update(resumed)
        else:
            tasks.discard(request.session_id)
            candidates = document_entity_candidates(question, documents)
            if len(candidates) > 1:
                if not clarify_enabled:
                    return _unsupported(trace, '登记资料中存在不同的同名对象；当前配置关闭澄清，未自动绑定对象。')
                card = tasks.save(request, question, candidates)
                return AnswerEnvelope(trace_id=trace.trace_id, status='NEEDS_CLARIFICATION',
                    answer=card['question'], intent=intent, clarification=card, steps=trace.steps,
                    metadata={'document_task': task_metadata, 'clarify': {
                        'level': 'L2', 'execution_allowed': False, 'query_execution_allowed': False}})
            selected_ids = candidates[0]['doc_ids'] if len(candidates) == 1 else allowed_ids
            if len(candidates) == 1:
                task_metadata['document_candidate_selection'] = {
                    'kind': 'literal_registered_document_entity',
                    'entity_ref': candidates[0]['entity_ref'],
                    'matched_labels': candidates[0]['matched_labels'],
                    'allowed_source_scope_unchanged': True,
                    'SQL_binding_created': False, 'user_intent_confirmation_asserted': False}
        task_metadata['searched_doc_ids'] = selected_ids
    except (ValueError, OSError, KeyError) as exc:
        return _error_envelope(trace, settings, str(exc), 'document_task_conflict', intent=intent)
    handler = getattr(module, function_name, None)
    if len(selected_ids) != 1:
        # The configured single-document entry remains backwards compatible.
        # A module must explicitly expose this capability; never bypass scope.
        handler = getattr(module, 'run_documents_qa', None) if function_name == 'run_doc_qa' else None
    if not callable(handler):
        return _unsupported(trace, "当前 RAG 入口不支持所选文档范围，请检查文档问答配置。")
    try:
        with trace.step("rag_channel", {"doc_ids": selected_ids, 'original_question': question}) as step:
            scope_argument = ({'doc_id': selected_ids[0]} if len(selected_ids) == 1
                              else {'doc_ids': selected_ids})
            result = handler(question=question, **scope_argument, trace_id=trace.trace_id, intent=intent)
            if inspect.isawaitable(result):
                import asyncio
                result = asyncio.run(result)
            envelope = result if isinstance(result, AnswerEnvelope) else AnswerEnvelope.model_validate(result)
            if any(e.doc_id not in selected_ids for e in envelope.evidences):
                raise ValueError("RAG 返回了指定文档之外的证据")
            ids = [e.evidence_id for e in envelope.evidences]
            if len(ids) != len(set(ids)):
                raise ValueError("RAG 返回了重复证据编号")
            step.output_summary = {"status": envelope.status, "evidence_count": len(ids)}
        envelope.trace_id = trace.trace_id
        envelope.steps = trace.steps + envelope.steps
        envelope.metadata["latency_ms"] = trace.latency_ms
        envelope.metadata['document_task'] = task_metadata
        if envelope.status in {'SUCCEEDED', 'EMPTY_RESULT', 'UNSUPPORTED'}:
            tasks.discard(request.session_id)
        if envelope.metadata.get('clarify') is None:
            from qa_agent.clarify.answer_metadata import completed_source_only_level
            envelope.metadata['clarify']=completed_source_only_level({'document':{
                'source':'documents','status':envelope.status,'warnings':envelope.metadata.get('warnings')}})
        return envelope
    except Exception as exc:
        return _error_envelope(trace, settings, str(exc), "rag_failed", getattr(exc, "retryable", False))


def _sql(request: ChatRequest, trace: TraceRecorder, settings: Settings,
         llm: JsonLLM, *, generation_context: dict | None = None) -> AnswerEnvelope:
    sql_trace_start = len(trace.steps)
    from qa_agent.sql.catalog import load_catalog
    from qa_agent.sql.executor import SQLExecutionError, SQLTimeoutError, execute_sql
    from qa_agent.sql.generator import generate_sql
    from qa_agent.sql.repair_guard import (string_filter_contract, validate_repair_filters,
                                           validate_chinook_fk_joins, validate_catalog_fk_joins)
    from qa_agent.database_registry import DatabaseRegistryError, get_connection
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
    from qa_agent.sql.source_literal_guard import (validate_source_literal_consistency,
                                                   ExplicitSourceConflict)
    from qa_agent.sql.aggregate_scope_guard import validate_aggregate_scope

    db_id = request.scope.db_id or "chinook"
    builtin_database = db_id in {'chinook', 'adventureworks'}
    semantic_gate_requested = semantic_gate_enabled()
    use_semantic_gate = semantic_gate_requested and builtin_database
    db_url = (settings.aw_db_url if db_id == "adventureworks" else settings.db_url) if builtin_database else None
    catalog_path = (settings.aw_catalog_path if db_id == "adventureworks" else settings.catalog_path) if builtin_database else None
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
        if not builtin_database:
            result['database_capabilities'] = {
                'schema_grounded_sql': True, 'catalog_fk_validation': True,
                'value_alias_index': False, 'semantic_clarification': False,
                'semantic_gate_requested': semantic_gate_requested,
                'semantic_gate_executed': False, 'schema_subgraph_index': False,
                'typed_sql_compiler': False, 'cross_source_fusion': False}
            result.setdefault('clarify', bypass_metadata())['unsupported_reason'] = (
                '所选数据库未登记专用语义规则；按真实目录生成SQL，未确认业务口径或启用语义澄清。')
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
            if not builtin_database:
                from dataclasses import replace
                connection = get_connection(db_id, settings)
                db_url, catalog_path = connection.db_url, connection.catalog_path
                # Dynamic credentials must be redacted by the same trace and
                # error sanitizers as the built-in connection strings.
                settings = replace(settings, db_url=db_url, catalog_path=catalog_path,
                                   nlu_enabled=False, typed_sql_compiler_enabled=False)
                trace.settings = settings
            step.output_summary = {**settings.public(), "selected_db_id": db_id}
            if not db_url:
                raise ValueError("请先在本地 .env 配置 AW_DB_URL。" if db_id == "adventureworks"
                                 else "请先在本地 .env 配置 CHINOOK_DB_URL（兼容 DB_URL）。")
            if not settings.llm_configured and isinstance(llm, JsonLLM):
                raise MissingCredentialError()
        # A stale card fails before value linking, model calls or SQL generation.
        if request.clarification_id:
            if not use_semantic_gate:
                raise SessionConflict("所选数据库暂不支持语义澄清卡；请提交完整问题。" if not builtin_database
                    else "当前累计消融组关闭语义澄清，不消费其它实验组的澄清卡片。")
            with trace.step("clarification_version_check") as step:
                previous = DEFAULT_STORE.get(request.session_id)
                if previous is None:
                    raise SessionConflict("会话已不存在，请重新提交完整问题。")
                verify_resume(previous, request.clarification_id, request.intent_version, source_dict(request))
                step.output_summary = {"verified": True, "intent_version": request.intent_version}
                from qa_agent.intent_consistency import document_information_request
                if document_information_request(previous.original_question):
                    raise SessionConflict('原问题要求文档介绍，旧 SQL 澄清卡不能改成数据库查询；请重新提交原问题，介绍意图未被改写。')
        with trace.step("catalog", {"db_id": db_id}) as step:
            catalog = load_catalog(catalog_path)
            if not builtin_database and catalog.database != db_id:
                raise ValueError('登记数据库与结构目录不匹配，请刷新该数据库连接。')
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
                                       "not_registered_for_db" if db_id != "chinook" else
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
            gate = (_catalog_only_gate(request, linked) if not builtin_database else
                    run_gate(request, catalog, llm, linked, trace) if use_semantic_gate
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
            if not builtin_database:
                step.output_summary['unsupported_for_selected_database'] = True
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
        question_elements = None
        from qa_agent.nlu.grounded_rewrite import enabled as s1_rewrite_enabled
        from qa_agent.nlu.features import enabled as feature_enabled
        s1_source_mode = builtin_database and s1_rewrite_enabled(nlu_enabled=settings.nlu_enabled,
                              semantic_gate=use_semantic_gate,
                              link_grounding=feature_enabled('AGENT_LINK_GROUNDING_ENABLED'))
        if s1_source_mode:
            from qa_agent.nlu.grounded_rewrite import collect_question_elements
            with trace.step('s1_question_elements', {'semantic_gate_executed': False}) as step:
                try:
                    from qa_agent.context import current_context
                    rewrite_runtime = current_context()
                    rewrite_original = request.message
                    rewrite_task = None
                    if (generation_context and generation_context.get('kind') == 'composed'
                            and rewrite_runtime is not None):
                        rewrite_original = rewrite_runtime.current_user_message
                        rewrite_task = request.message
                        from qa_agent.sql.s1_tool_context import tool_purpose
                        rewrite_task = tool_purpose(generation_context, rewrite_task)
                    question_elements = collect_question_elements(rewrite_original, catalog, llm, trace,
                        source_entity_hints=source_entity_hints, linked=linked, tool_task=rewrite_task)
                    step.output_summary = question_elements or {'status': 'no_advisory'}
                except (LLMError, ValueError, TypeError, AttributeError) as exc:
                    # An advisory must not block a previously valid BASE path.
                    # Its actual attempts remain in the common trace/capture.
                    step.status = 'warn'
                    step.output_summary = {'status': 'fallback_original',
                        'reason': sanitize_error(exc, settings), 'semantic_verified': False}
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
        allow_joins = True  # Registered schemas can require real FK lookup joins.
        repair_error = None
        repair_filters = None
        disabled_semantics = {"verified": False, "mode": ("disabled_cumulative_semantic_gate"
            if builtin_database else "unregistered_semantic_rules_for_database")}
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
                                          **({'source_entity_hints': source_entity_hints} if source_entity_hints else {}),
                                          **({'question_elements': question_elements} if question_elements else {}),
                                          **({'s1_source_mode': True} if s1_source_mode else {}))
                last_sql = generation.sql
                ranking_display_proof = None
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
                                                            gate.state.analysis, gate.state.resolutions,
                                                            question=gate.state.original_question)
                            step.output_summary = {"verified": True, "before_repair_filter_capture": True}
                        from qa_agent.sql.temporal_field_role_guard import validate_temporal_field_role
                        with trace.step("sql_temporal_field_role_validate") as temporal_step:
                            temporal_step.output_summary = validate_temporal_field_role(
                                last_sql, selected_catalog, gate.state.analysis,
                                question=gate.state.original_question)
                    from qa_agent.sql.semantic_guard import validate_question_semantics
                    with trace.step("sql_semantic_contract", {"intent_version": intent.intent_version}) as step:
                        semantic_sql_proof = validate_question_semantics(
                            question, last_sql, selected_catalog, intent=gate.state.analysis,
                            source_question=gate.state.original_question)
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
                        half_growth_proof = next((proof for proof in semantic_sql_proof.get('checks', [])
                            if isinstance(proof, dict) and proof.get('verified') is True
                            and proof.get('mode') == 'actual_invoice_half_year_growth'), None)
                        # The preceding narrow proof validates the actually
                        # consumed (H2-H1)/H1 operands. The generic SUM/SUM
                        # checker cannot express a difference numerator.
                        typed_ratio_proof = (half_growth_proof if half_growth_proof is not None else
                            validate_typed_ratio_scope(last_sql, selected_catalog, gate.state.analysis, bindings))
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
                                         if gate.state.analysis.task_type == "ratio" and half_growth_proof is None else None)
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
                # Shared SQL tool check: a directly contradicted literal is
                # never a placeholder for an unknown replacement. This check
                # does not select a value or consume component-3 state.
                from qa_agent.context import current_context as literal_context
                actual_context = literal_context()
                actual_question = (actual_context.current_user_message if actual_context else
                    str((generation_context or {}).get('original_question') or request.message))
                with trace.step('sql_original_literal_consistency', {'shared_BASE_S1': True,
                        'source': 'actual_current_user_message', 'state_committed': False}) as literal_step:
                    try:
                        if builtin_database:
                            literal_step.output_summary = validate_source_literal_consistency(
                                last_sql, selected_catalog, question=actual_question)
                        else:
                            literal_step.status = 'skipped'
                            literal_step.output_summary = {'verified': False,
                                'reason': 'built_in_entity_rule_not_registered_for_database'}
                    except ExplicitSourceConflict as conflict:
                        literal_step.output_summary = {'status':'blocked', 'fatal':True,
                            'retryable':False, 'business_correctness_asserted':False,
                            'conflict':conflict.details}
                        raise
                with trace.step('sql_aggregate_period_scope', {'shared_BASE_S1': True,
                        'source': 'actual_current_user_message', 'state_committed': False}) as period_step:
                    try:
                        period_step.output_summary = validate_aggregate_scope(
                            last_sql, selected_catalog, question=actual_question)
                    except SQLValidationError as conflict:
                        period_step.output_summary = {'status': 'blocked', 'retryable': True,
                            'business_correctness_asserted': False,
                            'conflict': getattr(conflict, 'aggregate_scope_evidence', None)}
                        raise
                if s1_source_mode:
                    from qa_agent.sql.s1_cohort_sum import validate_s1_cohort_sum
                    with trace.step('s1_SQL_collective_numerator_structure', {
                            'semantic_gate_executed':False,
                            'business_correctness_asserted':False}) as cohort_step:
                        cohort_step.output_summary = validate_s1_cohort_sum(
                            last_sql, selected_catalog, actual_question, enabled=True)
                    from qa_agent.sql.s1_invoice_share_default import validate_s1_invoice_share_default
                    with trace.step('s1_SQL_existing_invoice_share_default', {
                            'semantic_gate_executed':False,
                            'business_correctness_asserted':False}) as default_step:
                        default_step.output_summary = validate_s1_invoice_share_default(
                            last_sql, selected_catalog, actual_question, enabled=True,
                            brief=actual_context.text if actual_context else '',
                            user_history=actual_context.history if actual_context else ())
                    from qa_agent.sql.s1_total_preview import validate_s1_total_preview
                    from qa_agent.sql.s1_total_preview_caller import total_preview_caller_evidence
                    with trace.step('s1_SQL_complete_total_and_preview', {
                            'semantic_gate_executed':False,
                            'business_correctness_asserted':False}) as total_step:
                        total_owner = total_preview_caller_evidence(
                            generation_context, selected_catalog, enabled=True)
                        total_step.output_summary = {'caller': total_owner,
                            'shape': validate_s1_total_preview(
                                last_sql, selected_catalog, actual_question,
                                brief=actual_context.text if actual_context else '',
                                user_history=actual_context.history if actual_context else (),
                                enabled=total_owner['enabled'])}
                    from qa_agent.sql.s1_detail_revenue import validate_s1_detail_revenue
                    with trace.step('s1_SQL_revenue_grain_source', {
                            'semantic_gate_executed':False,
                            'business_correctness_asserted':False}) as grain_step:
                        grain_step.output_summary = validate_s1_detail_revenue(
                            last_sql, selected_catalog, actual_question, enabled=True,
                            source_text=actual_context.text if actual_context else '',
                            generation_context=generation_context)
                    from qa_agent.sql.s1_source_scope import validate_s1_source_scope
                    with trace.step('s1_SQL_source_period_roles', {
                            'semantic_gate_executed':False,
                            'business_correctness_asserted':False}) as scope_step:
                        scope_step.output_summary = validate_s1_source_scope(
                            last_sql, selected_catalog, actual_question,
                            source_text=actual_context.text if actual_context else '',
                            user_history=actual_context.history if actual_context else (), enabled=True)
                    from qa_agent.sql.s1_customer_identity import validate_s1_customer_identity
                    with trace.step('s1_SQL_customer_identity_structure', {
                            'semantic_gate_executed':False,
                            'business_correctness_asserted':False}) as identity_step:
                        identity_step.output_summary = validate_s1_customer_identity(
                            last_sql, selected_catalog, actual_question, enabled=True,
                            source_text=actual_context.text if actual_context else '',
                            user_history=actual_context.history if actual_context else ())
                from qa_agent.sql.s1_output_shape import requested_shape, validate_projection, validate_source_fraction
                if s1_source_mode:
                    with trace.step('s1_SQL_ratio_display_structure', {
                            'business_correctness_asserted':False}) as ratio_step:
                        ratio_step.output_summary = validate_source_fraction(
                            last_sql,actual_question,
                            brief=actual_context.text if actual_context else '',
                            has_history=bool(actual_context and actual_context.history),
                            composed=(generation_context or {}).get('kind')=='composed')
                    from qa_agent.sql.s1_percent_display import validate_s1_percent_display
                    evidence_text = '\n'.join(
                        evidence['text']
                        for dependency in ((generation_context or {}).get('dependencies') or {}).values()
                        if isinstance(dependency, dict)
                        for evidence in (dependency.get('evidences') or [])
                        if isinstance(evidence, dict) and isinstance(evidence.get('text'), str))
                    with trace.step('s1_SQL_percent_display_structure', {
                            'business_correctness_asserted':False}) as percent_step:
                        percent_step.output_summary = validate_s1_percent_display(
                            last_sql, actual_question,
                            brief=actual_context.text if actual_context else '',
                            has_history=bool(actual_context and actual_context.history),
                            composed=(generation_context or {}).get('kind') == 'composed',
                            evidence_text=evidence_text)
                s1_shape = (requested_shape(actual_question,
                    brief=actual_context.text if actual_context else '',
                    has_history=bool(actual_context and actual_context.history),
                    composed=(generation_context or {}).get('kind') == 'composed')
                    if s1_source_mode else None)
                if s1_source_mode and s1_shape is None:
                    from qa_agent.sql.s1_sql_clause_shape import source_sql_scalar_shape
                    s1_shape = source_sql_scalar_shape(actual_question,
                        context=generation_context,
                        brief=actual_context.text if actual_context else '',
                        has_history=bool(actual_context and actual_context.history))
                if s1_shape is not None:
                    with trace.step('s1_SQL_output_shape', {'semantic_gate_executed':False,
                            'business_correctness_asserted':False}) as shape_step:
                        shape_step.output_summary = validate_projection(last_sql, s1_shape)
                    from qa_agent.sql.s1_ordinal_gap import validate_ordinal_gap_sql
                    with trace.step('s1_SQL_ordinal_gap_structure', {
                            'business_correctness_asserted':False}) as ordinal_step:
                        ordinal_step.output_summary = validate_ordinal_gap_sql(
                            last_sql, selected_catalog, actual_question, s1_shape)
                with trace.step('sql_debut_album_identity') as debut_step:
                    if builtin_database:
                        from qa_agent.fusion.obligations import validate_debut_album_sql
                        debut_step.output_summary = validate_debut_album_sql(
                            last_sql, selected_catalog, generation_context)
                    else:
                        debut_step.status = 'skipped'
                        debut_step.output_summary = {'reason': 'No registered music-domain contract for this database'}
                if generation_context:
                    from qa_agent.fusion.planner import validate_fusion_sql
                    with trace.step("fusion_plan_validate", {"kind": generation_context.get("kind"),
                            "original_sql": last_sql, "before_program_row_limit": True}) as step:
                        fusion_options = {}
                        if s1_source_mode:
                            # Backend-only display context; never promote a model
                            # plan field into user precision or semantic authority.
                            fusion_options['s1_percent_display_context'] = {
                                'enabled': True,
                                'brief': actual_context.text if actual_context else '',
                                'has_history': bool(actual_context and actual_context.history),
                                'composed': generation_context.get('kind') == 'composed'}
                        fusion_proof = validate_fusion_sql(
                            last_sql, selected_catalog, generation_context, **fusion_options)
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
                    elif not builtin_database:
                        validate_catalog_fk_joins(last_sql, selected_catalog)
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
                if (isinstance(exc, (RankedRatioContractUnsupported, ExplicitSourceConflict))
                        or getattr(exc, 'sql_repairable', True) is False
                        or attempt >= settings.sql_repair_attempts):
                    raise
                repair_error = sanitize_error(exc, settings)
                with trace.step("sql_repair", {"attempt": attempt + 1}) as step:
                    step.status, step.output_summary = "warn", {"reason": repair_error, "preserve_bindings": True}
                continue
            try:
                executable_sql, parameters = parameterize_strings(last_sql) if bindings else (last_sql, {})
                result = execute_sql(executable_sql, db_url, statement_timeout_ms=settings.statement_timeout_ms,
                                     max_rows=settings.max_rows, trace=trace, parameters=parameters, db_id=db_id)
                if s1_source_mode:
                    from qa_agent.sql.ranking_display import build_ranking_display, _source as visible_rank_source
                    from qa_agent.sql.result_scope import query_output_scope
                    rank_scope = query_output_scope(generation.sql,
                        program_added_limit=validated.default_limit_added,row_count=result.row_count,
                        cap=settings.max_rows,truncated=result.truncated)
                    with trace.step('s1_SQL_ranking_display') as rank_step:
                        ranking_display_proof = build_ranking_display(
                            last_sql, result.table, catalog=selected_catalog,
                            source_question=actual_question,
                            brief=actual_context.text if actual_context else '',
                            user_history=actual_context.history if actual_context else (),
                            output_scope=rank_scope, original_sql=generation.sql)
                        rank_step.output_summary = ranking_display_proof
                        rank_step.status = ('ok' if ranking_display_proof.get('status') ==
                            'verified_SQL_ranking_display_only' else 'skipped')
                    if (result.table and visible_rank_source(actual_question,
                            actual_context.text if actual_context else '',
                            actual_context.history if actual_context else ()) is not None
                            and ranking_display_proof.get('status') != 'verified_SQL_ranking_display_only'):
                        from qa_agent.sql.projection_semantics import projection_semantics
                        meanings = projection_semantics(last_sql,result.columns,catalog=selected_catalog)
                        if not any(v.get('kind') == 'rank' for v in meanings.values()):
                            raise SQLValidationError('原始用户来源明确要求显示名次，但当前SQL未返回真实名次，'
                                '现有窗口、排序键或结果完整性也不足以由展示层核验名次。'
                                '请保留原条件、分组、指标、并列与行数，在最终投影返回实际消费的真实排名窗口列；'
                                '不能用常量或任意行序冒充名次。此处仅补交付，不能改变排名定义。')
                if s1_shape is not None:
                    from qa_agent.sql.s1_output_shape import validate_result
                    with trace.step('s1_SQL_actual_output_shape', {'business_correctness_asserted':False}) as shape_step:
                        validate_result(result.columns, result.table, s1_shape)
                        shape_step.output_summary = {'status':'verified_output_structure_only',
                            'actual_columns':len(result.columns),'actual_rows':len(result.table),
                            'business_correctness_asserted':False}
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
        if not builtin_database:
            # Preserve actual output identities and values. Built-in business
            # labels/units/defaults cannot describe an unfamiliar schema.
            with trace.step('answer') as step:
                status = 'SUCCEEDED' if result.rows else 'EMPTY_RESULT'
                answer = (f'查询返回 {result.row_count} 行，结果见数据表。' if result.rows
                          else '查询未返回符合条件的记录。')
                if result.row_count == 1 and len(result.columns) == 1:
                    value = result.rows[0][0]
                    answer = f'{result.columns[0]}：{value if value is not None else "NULL（无可汇总值）"}'
                if result.truncated:
                    answer += f'本次最多展示 {settings.max_rows} 行。'
                step.output_summary = {'status': status, 'summary_source': 'database_result_template',
                                       'business_semantics_verified': False}
            from qa_agent.sql.result_scope import query_output_scope
            output_scope = query_output_scope(generation.sql,
                program_added_limit=validated.default_limit_added, row_count=result.row_count,
                cap=settings.max_rows, truncated=result.truncated)
            return AnswerEnvelope(trace_id=trace.trace_id, status=status, answer=answer, sql=last_sql,
                table=result.table, intent=intent, steps=trace.steps,
                metadata={**metadata(), 'result_columns': result.columns, 'truncated': result.truncated,
                    'query_output_scope': output_scope, 'result_format': {},
                    'column_labels': {name: name for name in result.columns},
                    'data_status': 'NO_DATA' if not result.table or all(
                        value is None for row in result.table for value in row.values()) else 'AVAILABLE'})
        from qa_agent.sql.result_format import percentage_formats, display_percentage, presentation_formats
        result_formats = percentage_formats(last_sql, result.columns, intent.task_type if use_semantic_gate else None,
            catalog=selected_catalog, question=gate.state.original_question)
        from qa_agent.sql.ratio_presentation import (describe_typed_ratio,
            describe_verified_invoice_share, describe_customer_winner_ratio)
        ratio_basis = ((describe_typed_ratio(typed_ratio_proof) or
                       describe_customer_winner_ratio(semantic_sql_proof, gate.state.analysis) or
                       describe_verified_invoice_share(last_sql, selected_catalog, bindings, ratio_context))
                       if use_semantic_gate else None)
        query_basis = None
        if ratio_basis is None and any(rule.get('kind') == 'percentage' for rule in result_formats.values()):
            # Explain the SQL actually executed, independently of component 3.
            # An optional display annotation is never an execution certificate.
            with trace.step('sql_query_basis') as basis_step:
                try:
                    from qa_agent.sql.query_basis import describe_query_basis
                    query_basis = describe_query_basis(last_sql, result.columns, catalog=selected_catalog)
                    basis_step.status = 'ok' if query_basis else 'skipped'
                    basis_step.output_summary = query_basis or {'status': 'unsupported_sql_shape',
                        'business_correctness_asserted': False}
                except Exception as exc:
                    basis_step.status = 'warn'
                    basis_step.output_summary = {'reason': sanitize_error(exc, settings),
                        'business_correctness_asserted': False}
        from qa_agent.sql.result_scope import query_output_scope
        output_scope = query_output_scope(generation.sql,
            program_added_limit=validated.default_limit_added, row_count=result.row_count,
            cap=settings.max_rows, truncated=result.truncated)
        presentation_labels = {}
        s1_execution_notes = None
        with trace.step("answer") as step:
            status = "SUCCEEDED" if result.rows else "EMPTY_RESULT"
            from qa_agent.context import current_context
            from qa_agent.sql.presentation import present, data_coverage_note
            user_context = current_context()
            result_formats = presentation_formats(last_sql, result.columns, result_formats,
                query_scope=getattr(gate.state.analysis, "query_scope", {}),
                brief=user_context.text if user_context else "", catalog=selected_catalog,
                **({'question':actual_question} if s1_source_mode else {}))
            answer, presentation_labels = present(gate.state.original_question, result.table,
                result.columns, result_formats, metric=intent.metric,
                brief=user_context.text if user_context else "", task_type=intent.task_type,
                sql=last_sql, query_scope=getattr(gate.state.analysis, "query_scope", {}),
                partition_proof=partition_proof, ratio_basis=ratio_basis,
                groupwise_proof=groupwise_presentation_proof,
                comparison_proof=comparison_proof, catalog=selected_catalog,
                semantic_intent=gate.state.analysis,
                ranking_display_proof=ranking_display_proof,
                **({'display_question':actual_question} if s1_source_mode else {}))
            if query_basis:
                answer += '\n' + query_basis['text']
            if s1_source_mode:
                with trace.step('s1_SQL_execution_notes') as notes_step:
                    try:
                        from qa_agent.sql.s1_execution_notes import describe_s1_execution_notes
                        s1_execution_notes = describe_s1_execution_notes(
                            actual_question, last_sql, result.columns, result.table,
                            catalog=selected_catalog, enabled=True,
                            brief=user_context.text if user_context else '',
                            user_history=user_context.history if user_context else (),
                            output_scope=output_scope, existing_query_basis=query_basis)
                        notes_step.output_summary = s1_execution_notes or {
                            'status': 'not_verified', 'display_only': True,
                            'business_correctness_asserted': False}
                    except Exception as exc:
                        notes_step.status = 'warn'
                        notes_step.output_summary = {'reason': sanitize_error(exc, settings),
                            'display_only': True, 'business_correctness_asserted': False}
                if s1_execution_notes:
                    answer += '\n' + s1_execution_notes['text']
            coverage_note=data_coverage_note(last_sql,selected_catalog,result.table)
            if coverage_note:
                answer += '\n'+coverage_note
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
                                   "ratio_business_basis": ratio_basis,
                                   **({'query_basis': query_basis} if query_basis else {})}
        if use_semantic_gate:
            finish_gate(gate, succeeded=True)
        last_rewrite = next((entry.output_summary for entry in reversed(trace.steps[sql_trace_start:])
            if entry.name == 's1_rewrite_task_consume'), None)
        used_rewrite = (last_rewrite if isinstance(last_rewrite,dict)
            and last_rewrite.get('status') == 'quote_checked_advisory_task' else None)
        return AnswerEnvelope(trace_id=trace.trace_id, status=status, answer=answer, sql=last_sql,
                              rewritten_question=(used_rewrite['normalized_sql_question'] if used_rewrite
                                  and used_rewrite.get('normalized_text_role')!='advisory_only'
                                  else linked.rewritten_question if linked.patches else None),
                              table=result.table, intent=intent, steps=trace.steps,
                              metadata={**metadata(), "result_columns": result.columns, "truncated": result.truncated,
                                        "query_output_scope":output_scope,
                                        **({'ranking_display_proof':ranking_display_proof}
                                            if ranking_display_proof and ranking_display_proof.get('status') ==
                                            'verified_SQL_ranking_display_only' else {}),
                                        **({'s1_rewrite':{'authority':'advisory_only','semantic_verified':False,
                                            'original_question_sha256':used_rewrite['original_question_sha256'],
                                            'task_used_for_SQL_generation':True,
                                            'consumption_policy':used_rewrite.get('consumption_policy','legacy_primary_rewrite'),
                                            'primary_question_source':used_rewrite.get('primary_question_source'),
                                            'normalized_text_role':used_rewrite.get('normalized_text_role')}} if used_rewrite else {}),
                                        "result_format": result_formats, "column_labels": presentation_labels,
                                        "ratio_business_basis": ratio_basis,
                                        **({'query_basis': query_basis} if query_basis else {}),
                                        **({'s1_execution_notes': s1_execution_notes}
                                            if s1_execution_notes else {}),
                                        "groupwise_order_proof": groupwise_presentation_proof,
                                        "data_status": "NO_DATA" if not result.table or all(
                                            value is None for row in result.table for value in row.values()) else "AVAILABLE"})
    except DatabaseRegistryError as exc:
        return failed(trace, settings, str(exc), exc.code, intent=intent)
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
    from qa_agent.rag.task import DEFAULT_DOCUMENT_TASK_STORE
    if (request.clarification_id and (request.clarification_id.startswith('doc-')
            or DEFAULT_DOCUMENT_TASK_STORE.pending(request))):
        # Resume before classifying the short choice label as a fresh question.
        if 'doc' not in restriction.allowed_tools:
            return _unsupported(trace, '本轮来源约束禁止使用文档，未继续旧澄清或改成另一数据库任务；请重新提交完整问题。')
        return _doc(request, trace, settings)
    if (request.scope.db_id not in {None, 'chinook', 'adventureworks'}
            and request.scope.route in {'auto', 'hybrid'}):
        # Built-in planners contain registered metric and entity assumptions.
        # A custom database may use the shared SQL or document tools directly,
        # but cannot acquire those assumptions through an auto fallback.
        from qa_agent.intent_consistency import document_information_request
        from qa_agent.source_scope import has_context_reference
        if (restriction.mode == 'documents_only' or
                request.scope.route == 'auto' and restriction.mode == 'unrestricted'
                and not request.clarification_id and not has_context_reference(request.message)
                and document_information_request(request.message)):
            _retire_direct_task_plans(request, trace)
            return _doc(request, trace, settings)
        if (request.scope.route == 'hybrid' or restriction.mode in {'context_only', 'local_mixed'}
                or has_context_reference(request.message)
                or re.search(r'文档|手册|PDF|资料|百科|介绍|简介|背景', request.message, re.I)):
            return _unsupported(trace, '所选数据库支持按真实结构目录问数及独立文档问答，'
                '暂不支持跨源综合、正文驱动的业务口径绑定或语义澄清；请提交完整的数据库问题，'
                '或选择文档问答。')
        request = request.model_copy(update={'scope': request.scope.model_copy(
            update={'route': 'sql', 'doc_ids': []})})
    from qa_agent.fusion.obligations import explicit_new_task
    from qa_agent.fusion.planner import _explicit_hybrid_kind
    if (request.scope.db_id in {None, 'chinook', 'adventureworks'} and not request.clarification_id
            and (explicit_new_task(request.message) or _explicit_hybrid_kind(request.message))):
        _retire_direct_task_plans(request, trace)
    if restriction.mode == "context_only":
        from qa_agent.fusion.composed import run_context_only
        _retire_direct_task_plans(request, trace)
        return run_context_only(request, trace, settings, llm or JsonLLM(settings), restriction)
    if restriction.mode == "documents_only":
        _retire_direct_task_plans(request, trace)
        return _doc(request, trace, settings)
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
    from qa_agent.intent_consistency import document_information_request
    from qa_agent.source_scope import has_context_reference
    if (request.scope.route == 'auto' and restriction.mode == 'unrestricted'
            and not request.clarification_id and not has_context_reference(request.message)
            and document_information_request(request.message)):
        _retire_direct_task_plans(request, trace)
        with trace.step('document_intent_route', {'authority': 'actual_user_request'}) as step:
            step.output_summary = {'route': 'doc', 'scope_size_does_not_change_intent': True,
                                   'SQL_entity_candidates_are_not_tasks': True}
        return _doc(request, trace, settings)
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
        from qa_agent.nlu.grounded_rewrite import enabled as s1_rewrite_enabled
        from qa_agent.nlu.features import enabled as feature_enabled
        from qa_agent.ablation import semantic_gate_enabled
        if s1_rewrite_enabled(nlu_enabled=settings.nlu_enabled,
                semantic_gate=semantic_gate_enabled(),
                link_grounding=feature_enabled('AGENT_LINK_GROUNDING_ENABLED')):
            from qa_agent.nlu.route_hints import music_fact_route_hint
            from qa_agent.nlu.value_index import load_value_index
            from qa_agent.sql.catalog import load_catalog
            with trace.step('s1_source_route_hint') as hint_step:
                try:
                    route_hint = None
                    if request.scope.route == 'auto' and restriction.mode == 'unrestricted':
                        from qa_agent.nlu.session_fact_route import session_fact_route_hint
                        route_hint = session_fact_route_hint(request.message, nlu_enabled=True,
                            semantic_gate=False, runtime=active_context)
                    if not route_hint:
                        route_hint = music_fact_route_hint(request.message,
                            index=load_value_index(settings.value_index_path),
                            catalog=load_catalog(settings.catalog_path),
                            nlu_enabled=True, semantic_gate_enabled=False,
                            route=request.scope.route, restriction=restriction)
                    hint_step.output_summary = route_hint or {'status': 'keep_existing_route'}
                except (ValueError, OSError) as exc:
                    route_hint = None
                    hint_step.status = 'warn'
                    hint_step.output_summary = {'status': 'keep_existing_route',
                        'reason': sanitize_error(exc, settings)}
            if route_hint:
                if route_hint.get('kind') in {'session_definition_recall', 'session_definition_relation_recall'}:
                    # A bounded, source-backed recall has no current database
                    # task. Do not ask a second planner to reinterpret a stated
                    # future list intention as a query to execute right now.
                    from qa_agent.fusion.composed import run_context_only
                    _retire_direct_task_plans(request, trace)
                    return run_context_only(request, trace, settings, llm or JsonLLM(settings), restriction)
                with DEFAULT_STORE.locked(request.session_id):
                    return run_composed(request, trace, settings, llm or JsonLLM(settings), _sql)
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
        return _unsupported(trace, "请指定数据库或文档来源后重试。")
    if request.scope.db_id is None:
        return _unsupported(trace, "SQL 来源请选择已登记的数据库。")
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
                from qa_agent.intent_consistency import check_answer_intent
                original = response.metadata.get('document_task', {}).get('original_question', request.message)
                consistency = check_answer_intent(original, response,
                    expected_route='doc' if response.metadata.get('document_task') else None)
                response.metadata['answer_intent_check'] = consistency
                if consistency['status'] == 'mismatch':
                    response = AnswerEnvelope(trace_id=response.trace_id, status='FAILED',
                        answer='执行结果与原始问题的资料介绍意图不一致，已阻止将其作为答案。',
                        intent=response.intent, steps=response.steps,
                        metadata={**response.metadata, 'rejected_result_not_returned': True},
                        error=ErrorDetail(code='answer_intent_mismatch',
                            message='执行结果与原始问题不一致。', retryable=False))
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
