"""Offline document intent regressions through the actual chat/tool/state chain.

The corpus and model replies below are unit fixtures, never fresh predictions.
Only model transport, physical database access and the deliberately exercised
SQL-channel boundary are scripted.  Routing, document task state, persisted
index validation, BM25 retrieval, answer citation checks and the final intent
consistency check remain real.
"""
from __future__ import annotations

from copy import deepcopy
import csv
from hashlib import sha256
import json
import socket
from types import SimpleNamespace

import pytest

from qa_agent.config import Settings
from qa_agent.pipeline import chat
from qa_agent.schemas import AnswerEnvelope, ChatRequest, IntentContract


CLOCK = "2026-10-15T09:00:00+08:00"
ZONE = "Asia/Shanghai"


class ScriptedDocumentModel:
    """Return only supplied local evidence; a planner/SQL model call is a bug."""

    def __init__(self):
        self.calls = []
        self.empty = False

    def complete_json(self, system, user, response_model, trace=None):
        from qa_agent.rag.answer import DocumentAnswer

        assert response_model is DocumentAnswer, "Unexpected planner or SQL generation"
        payload = json.loads(user)
        self.calls.append({"system": system, "payload": deepcopy(payload)})
        if self.empty:
            return DocumentAnswer(status="EMPTY_RESULT", answer="资料不足。", citation_ids=[])
        evidence = payload["evidence"]
        assert evidence, "The real retriever must supply actual fixture chunks"
        # Scripted copying exercises real citation validation, not model ability.
        return DocumentAnswer(
            status="SUCCEEDED",
            answer="\n".join(c["text"] + "[" + c["evidence_id"] + "]" for c in evidence),
            citation_ids=[c["evidence_id"] for c in evidence],
        )


@pytest.fixture
def chain(tmp_path, monkeypatch):
    import qa_agent.context as context
    import qa_agent.documents as documents
    import qa_agent.pipeline as pipeline
    import qa_agent.clarify.state as semantic_state
    import qa_agent.fusion.resume_state as fusion_state
    import qa_agent.rag.index as index
    import qa_agent.rag.service as service
    import qa_agent.rag.task as task
    from qa_agent.rag.retrieval_cache import clear_retrieval_cache

    def blocked(*args, **kwargs):
        pytest.fail("Offline document regression attempted network/DB/model access")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr("psycopg.connect", blocked)
    monkeypatch.setattr("qa_agent.llm.JsonLLM.complete_json", blocked)
    monkeypatch.setattr("qa_agent.sql.executor.execute_sql", blocked)
    monkeypatch.setattr(pipeline, "_sql", blocked)
    for key, value in {
        # Normal main configuration can issue document clarification cards.
        # Ablation-off cases below change only their individual test scope.
        "AGENT_SEMANTIC_GATE_ENABLED": "true",
        "AGENT_LINK_GROUNDING_ENABLED": "true",
        "AGENT_GROUNDING_ENABLED": "false",
        "AGENT_CLARIFY_STATE_ENABLED": "true",
        "AGENT_S1_REWRITE_ENABLED": "true",
    }.items():
        monkeypatch.setenv(key, value)

    source_dir = tmp_path / "data/docs"
    source_dir.mkdir(parents=True)
    records = [
        ("atlas-band", "Atlas（乐队）公开简介", "music:artist:801:Atlas",
         "Atlas 乐队背景来自山谷。成员：甲与乙。风格：民谣。"),
        ("atlas-person", "Atlas（人物）公开简介", "library:person:902:Atlas",
         "Atlas 人物背景来自海滨。职业：画家。风格：写实。"),
        ("lumen", "Lumen公开简介", "music:artist:803:Lumen",
         "Lumen 背景来自森林。成员：丙与丁。风格：器乐。"),
        ("lumen-notes", "Lumen资料", "music:artist:803:Lumen",
         "Lumen 背景资料说明成员丙与丁合作。风格是器乐。"),
        ("metallica", "Metallica 金属乐队公开简介", "chinook:artist:50:Metallica",
         "Metallica 金属乐队背景资料。成员：甲与丙。风格：金属。"),
        ("u2", "U2公开简介", "chinook:artist:150:U2",
         "U2 背景资料。成员：乙与丁。风格：摇滚。"),
    ]
    rows = []
    for doc_id, title, entity_ref, text in records:
        path = source_dir / (doc_id + ".md")
        path.write_text("# 背景资料\n\n" + text + "\n", encoding="utf-8")
        rows.append({
            "doc_id": doc_id, "title": title, "format": "md",
            "path": path.as_posix(), "content_hash": sha256(path.read_bytes()).hexdigest(),
            "language": "zh", "entity_ref": entity_ref,
        })
    manifest = source_dir / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    load_registered = documents.load_documents

    def registered(path=None):
        return load_registered(path or manifest, project_root=tmp_path)

    # Only the fixture's project-root binding changes, not scope/hash behavior.
    monkeypatch.setattr(documents, "load_documents", registered)
    monkeypatch.setattr(index, "load_documents", registered)
    monkeypatch.setattr(service, "load_documents", registered)
    settings = Settings(
        db_url="", llm_api_key="fixture-not-a-credential", nlu_enabled=True,
        rag_manifest_path=manifest, rag_index_path=tmp_path / "data/index",
        bge_model_path=tmp_path / "absent-model", rag_answer_mode="llm",
        rag_retrieval_strategy="hybrid", rag_top_k=8,
    )
    meta = index.build_index(settings=settings)
    assert meta["dense_embedding"]["enabled"] is False
    model = ScriptedDocumentModel()
    monkeypatch.setattr(service, "get_settings", lambda: settings)
    monkeypatch.setattr(service, "JsonLLM", lambda *args, **kwargs: model)
    contexts = context.ContextStore(tmp_path / "contexts")
    tasks = task.DocumentTaskStore(tmp_path / "document-tasks")
    monkeypatch.setattr(context, "DEFAULT_CONTEXT_STORE", contexts)
    monkeypatch.setattr(task, "DEFAULT_DOCUMENT_TASK_STORE", tasks)
    monkeypatch.setattr(semantic_state, "DEFAULT_STORE", semantic_state.SessionStore(tmp_path / "sessions"))
    monkeypatch.setattr(fusion_state, "DEFAULT_COMPOSED_STORE", fusion_state.ComposedStore(tmp_path / "composed"))
    clear_retrieval_cache()

    def ask(question, *, session="document-chain", doc_ids=(), route="auto", **kwargs):
        return chat(ChatRequest(
            session_id=session, message=question,
            scope={"route": route, "db_id": "chinook", "doc_ids": list(doc_ids)},
            reference_datetime=CLOCK, timezone=ZONE, **kwargs,
        ), llm=model, settings=settings)

    yield SimpleNamespace(ask=ask, settings=settings, model=model, contexts=contexts,
                          tasks=tasks, rows=rows, service=service, pipeline=pipeline,
                          root=tmp_path)
    clear_retrieval_cache()


def assert_document_answer(result, searched, *, allowed_upper=None):
    allowed_upper = searched if allowed_upper is None else allowed_upper
    assert result.status == "SUCCEEDED", result.model_dump()
    assert result.sql is None and result.table is None
    assert result.intent.route == "doc"
    assert result.evidences
    assert {e.doc_id for e in result.evidences} <= set(searched)
    # Retriever scope is its actual candidate set, not the user's upper bound.
    assert set(result.metadata["allowed_doc_ids"]) == set(searched)
    task = result.metadata["document_task"]
    assert set(task["allowed_doc_ids"]) == set(allowed_upper)
    assert set(task["searched_doc_ids"]) == set(searched)
    retrieval = next(step for step in result.steps if step.name == "retrieve")
    assert set(retrieval.output_summary["allowed_doc_ids"]) == set(searched)
    assert any(step.name == "retrieve" for step in result.steps)
    assert any(step.name == "rag_validate" for step in result.steps)
    assert not any(step.name in {"sql_gen", "sql_exec"} for step in result.steps)
    assert result.metadata["answer_intent_check"]["status"] == "passthrough"


@pytest.mark.parametrize("route", ["auto", "doc"])
def test_selected_document_stays_doc_through_real_service_retrieval_and_validation(chain, route):
    original = "介绍 Atlas 的背景，分段说明成员和风格，每段标出引用。"
    result = chain.ask(original, doc_ids=["atlas-band"], route=route)
    assert_document_answer(result, ["atlas-band"])
    assert "画家" not in result.answer and "Lumen" not in result.answer
    assert chain.model.calls[-1]["payload"]["question"] == original
    assert result.metadata["reference_clock"]["datetime"] == CLOCK


def test_auto_empty_doc_ids_keeps_scope_upper_bound_but_searches_unique_identity_documents(chain):
    result = chain.ask("介绍 Lumen 的背景与成员，引用资料。")
    assert_document_answer(result, ["lumen", "lumen-notes"],
                           allowed_upper=[row["doc_id"] for row in chain.rows])
    assert result.metadata["document_task"]["allowed_doc_ids"] == [row["doc_id"] for row in chain.rows]
    assert {e.doc_id for e in result.evidences} == {"lumen", "lumen-notes"}
    assert result.clarification is None


@pytest.mark.parametrize("question,doc_id,excluded_name", [
    ("金属乐队是什么？", "metallica", "U2"),
    ("介绍 U2 的成员和风格，给出引用。", "u2", "Metallica"),
])
def test_all_documents_named_subject_cites_only_its_registered_identity(
        chain, question, doc_id, excluded_name):
    result = chain.ask(question)
    assert_document_answer(result, [doc_id], allowed_upper=[row["doc_id"] for row in chain.rows])
    assert {e.doc_id for e in result.evidences} == {doc_id}
    assert excluded_name not in result.answer and "Atlas" not in result.answer
    assert {e["doc_id"] for e in chain.model.calls[-1]["payload"]["evidence"]} == {doc_id}
    assert chain.model.calls[-1]["payload"]["question"] == question


def test_generic_information_request_without_registered_subject_really_searches_all_documents(chain):
    result = chain.ask("概述可用文档的背景与风格，并给出引用。")
    all_ids = [row["doc_id"] for row in chain.rows]
    assert_document_answer(result, all_ids)
    assert {e.doc_id for e in result.evidences} == set(all_ids)
    assert result.metadata["document_task"].get("document_candidate_selection") is None


def test_same_title_without_registered_entity_relation_is_not_proved_entity_ambiguity(chain):
    from pathlib import Path
    from qa_agent.rag.index import build_index
    from qa_agent.rag.retrieval_cache import clear_retrieval_cache

    # Rebuild the real fixture snapshot after changing its registration. File
    # identity alone is not evidence that these represent two different people.
    for row in chain.rows[:2]:
        row["title"] = "Echo公开简介"
        row["entity_ref"] = ""
        path = Path(row["path"])
        path.write_text("# 背景资料\n\nEcho 背景资料，风格与成员见原文说明。\n", encoding="utf-8")
        row["content_hash"] = sha256(path.read_bytes()).hexdigest()
    with chain.settings.rag_manifest_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(chain.rows[0]))
        writer.writeheader()
        writer.writerows(chain.rows)
    build_index(settings=chain.settings)
    clear_retrieval_cache()
    result = chain.ask("介绍 Echo 的背景与风格，给出引用。")
    assert_document_answer(result, [row["doc_id"] for row in chain.rows])
    assert result.clarification is None
    assert result.metadata["document_task"].get("document_candidate_selection") is None
    assert not chain.tasks.path("document-chain").exists()


def test_generic_entity_role_in_registered_title_does_not_select_that_entity(chain):
    from qa_agent.rag.index import build_index
    from qa_agent.rag.retrieval_cache import clear_retrieval_cache

    row = next(row for row in chain.rows if row["doc_id"] == "lumen")
    row["title"] = "Lumen 乐队公开简介"
    with chain.settings.rag_manifest_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(chain.rows[0]))
        writer.writeheader()
        writer.writerows(chain.rows)
    build_index(settings=chain.settings)
    clear_retrieval_cache()
    result = chain.ask("乐队是什么？")
    assert_document_answer(result, [row["doc_id"] for row in chain.rows])
    assert result.clarification is None
    assert result.metadata["document_task"].get("document_candidate_selection") is None


def test_explicit_multiple_document_scope_is_an_actual_retrieval_filter(chain):
    result = chain.ask("介绍 Lumen 的背景与成员，引用资料。", doc_ids=["lumen", "lumen-notes"])
    assert_document_answer(result, ["lumen", "lumen-notes"])
    assert "Atlas" not in result.answer
    assert {item["doc_id"] for item in chain.model.calls[-1]["payload"]["evidence"]} <= {"lumen", "lumen-notes"}


def test_only_same_literal_different_registered_entity_identity_needs_doc_choice(chain):
    result = chain.ask("介绍 Atlas 的背景和风格，给出引用。")
    assert result.status == "NEEDS_CLARIFICATION", result.model_dump()
    assert result.intent.route == "doc"
    assert len(result.clarification["options"]) == 2
    assert result.clarification["resume_supported"] is True
    assert not chain.model.calls and result.sql is None and not result.evidences
    assert chain.tasks.path("document-chain").is_file()


def test_multiple_sources_for_one_identity_are_not_entity_ambiguity(chain):
    result = chain.ask("介绍 Lumen 的背景和风格，给出引用。", doc_ids=["lumen", "lumen-notes"])
    assert_document_answer(result, ["lumen", "lumen-notes"])
    assert result.clarification is None
    assert not chain.tasks.path("document-chain").exists()


def card_and_choice(chain, *, session="document-chain", doc_ids=()):
    original = "介绍 Atlas 的背景，请分别说明成员与风格，每段给出引用。"
    first = chain.ask(original, session=session, doc_ids=doc_ids)
    assert first.status == "NEEDS_CLARIFICATION", first.model_dump()
    card = first.clarification
    choice = next(item["id"] for item in card["options"] if "乐队" in item["label"])
    return original, card, choice


def test_card_choice_changes_only_document_entity_and_preserves_full_original_output_request(chain):
    original, card, choice = card_and_choice(chain, doc_ids=["atlas-band", "atlas-person"])
    result = chain.ask("就按这个对象继续。", doc_ids=["atlas-band", "atlas-person"],
                       clarification_id=card["clarification_id"], intent_version=card["intent_version"],
                       choice_id=choice)
    assert_document_answer(result, ["atlas-band"], allowed_upper=["atlas-band", "atlas-person"])
    payload = chain.model.calls[-1]["payload"]
    assert payload["question"] == original
    assert "成员" in payload["question"] and "风格" in payload["question"] and "每段" in payload["question"]
    task = result.metadata["document_task"]
    assert task["original_question"] == original
    assert set(task["original_scope"]["doc_ids"]) == {"atlas-band", "atlas-person"}
    assert task["SQL_binding_or_new_task_created"] is False
    assert not chain.tasks.path("document-chain").exists()


def test_evidence_insufficient_after_choice_retires_card_and_rejects_replay(chain):
    original, card, choice = card_and_choice(chain)
    chain.model.empty = True
    arguments = dict(clarification_id=card["clarification_id"],
                     intent_version=card["intent_version"], choice_id=choice)
    result = chain.ask("按所选对象继续。", **arguments)
    assert result.status == "EMPTY_RESULT", result.model_dump()
    assert chain.model.calls[-1]["payload"]["question"] == original
    assert result.sql is None and result.table is None and not result.evidences
    assert not chain.tasks.path("document-chain").exists()
    calls = len(chain.model.calls)
    repeated = chain.ask("按所选对象继续。", **arguments)
    assert repeated.status == "FAILED", repeated.model_dump()
    assert repeated.sql is None and repeated.table is None
    assert len(chain.model.calls) == calls


def test_card_choice_cannot_override_current_explicit_database_only_permission(chain):
    _, card, choice = card_and_choice(chain)
    result = chain.ask("只查询数据库，不要查文档。",
                       clarification_id=card["clarification_id"],
                       intent_version=card["intent_version"], choice_id=choice)
    assert result.status in {"UNSUPPORTED", "FAILED"}, result.model_dump()
    assert result.sql is None and result.table is None and not result.evidences
    assert not chain.model.calls
    assert not any(step.name in {"retrieve", "rag_generate", "sql_gen", "sql_exec"}
                   for step in result.steps)


def test_card_choice_does_not_swallow_an_explicit_new_database_task(chain):
    _, card, choice = card_and_choice(chain)
    result = chain.ask("查询2025年客户发票销售额，并列出客户名单。",
                       clarification_id=card["clarification_id"],
                       intent_version=card["intent_version"], choice_id=choice)
    assert result.status == "FAILED", result.model_dump()
    assert result.error.code == "document_task_conflict"
    assert result.sql is None and result.table is None and not result.evidences
    assert not chain.model.calls
    assert not any(step.name in {"retrieve", "rag_generate", "sql_gen", "sql_exec"}
                   for step in result.steps)


@pytest.mark.parametrize("disabled_switch", [
    "AGENT_SEMANTIC_GATE_ENABLED", "AGENT_CLARIFY_STATE_ENABLED",
])
@pytest.mark.parametrize("has_existing_card", [False, True])
def test_document_clarification_respects_each_disabled_experiment_switch(
        chain, monkeypatch, disabled_switch, has_existing_card):
    arguments = {}
    if has_existing_card:
        _, card, choice = card_and_choice(chain)
        arguments = dict(clarification_id=card["clarification_id"],
                         intent_version=card["intent_version"], choice_id=choice)
    monkeypatch.setenv(disabled_switch, "false")
    question = ("按所选对象继续。" if has_existing_card
                else "介绍 Atlas 的背景和风格，给出引用。")
    result = chain.ask(question, **arguments)
    assert result.status == ("FAILED" if has_existing_card else "UNSUPPORTED"), result.model_dump()
    if has_existing_card:
        assert result.error.code == "document_task_conflict"
    else:
        assert not chain.tasks.path("document-chain").exists()
    assert result.clarification is None
    assert (result.metadata.get("clarify") or {}).get("level") != "L2"
    assert result.sql is None and result.table is None and not result.evidences
    assert not chain.model.calls
    assert not any(step.name in {"retrieve", "rag_generate", "sql_gen", "sql_exec"}
                   for step in result.steps)


@pytest.mark.parametrize("changed", ["scope", "session", "version", "choice", "context"])
def test_stale_or_cross_session_document_cards_fail_before_tools(chain, changed):
    if changed == "context":
        chain.contexts.create("document-chain", "原先的完整输出要求。", CLOCK, ZONE)
    _, card, choice = card_and_choice(chain)
    arguments = dict(clarification_id=card["clarification_id"], intent_version=card["intent_version"], choice_id=choice)
    if changed == "scope":
        arguments["doc_ids"] = ["atlas-band"]
    elif changed == "session":
        arguments["session"] = "different-session"
    elif changed == "version":
        arguments["intent_version"] += 1
    elif changed == "choice":
        arguments["choice_id"] = "document-999"
    else:
        chain.contexts.create("document-chain", "替换后的正文版本。", CLOCK, ZONE)
    result = chain.ask("继续这个对象。", **arguments)
    assert result.status == "FAILED", result.model_dump()
    assert result.sql is None and result.table is None and not result.evidences
    assert not chain.model.calls


def test_unregistered_subject_has_no_special_music_or_sql_fallback(chain):
    chain.model.empty = True
    result = chain.ask("介绍 Quasar 的背景。", doc_ids=["lumen"])
    assert result.status == "EMPTY_RESULT", result.model_dump()
    assert result.intent.route == "doc"
    assert result.sql is None and result.table is None
    assert chain.model.calls[-1]["payload"]["question"] == "介绍 Quasar 的背景。"


@pytest.mark.parametrize("doc_ids", [[], ["lumen"], ["lumen", "atlas-band"]])
def test_explicit_album_listing_keeps_real_router_sql_and_clears_doc_scope(chain, monkeypatch, doc_ids):
    received = []

    def sql_boundary(request, trace, settings, llm, **kwargs):
        received.append(request)
        return AnswerEnvelope(trace_id=trace.trace_id, status="SUCCEEDED", answer="实际SQL边界的脚本输出。",
                              sql="SELECT album_id,title FROM public.album", table=[],
                              intent=IntentContract(route="sql"))

    monkeypatch.setattr(chain.pipeline, "_sql", sql_boundary)
    original = "列出 Lumen 的 albums，只查询专辑名单。"
    result = chain.ask(original, doc_ids=doc_ids)
    assert result.status == "SUCCEEDED", result.model_dump()
    assert len(received) == 1
    assert received[0].message == original
    assert received[0].scope.route == "sql" and received[0].scope.db_id == "chinook"
    assert received[0].scope.doc_ids == []
    assert result.intent.route == "sql" and result.sql is not None
    assert result.clarification is None and not chain.model.calls


def test_successful_sql_envelope_cannot_replace_doc_answer_at_final_chat_boundary(chain, monkeypatch):
    # Deliberately wrong downstream plugin output; the final guard stays real.
    def wrong_handler(**kwargs):
        return AnswerEnvelope(trace_id=kwargs["trace_id"], status="SUCCEEDED", answer="不相关的专辑数量。",
                              sql="SELECT COUNT(*) FROM public.album", table=[{"n": 5}],
                              intent=IntentContract(route="sql"))

    monkeypatch.setattr(chain.service, "run_doc_qa", wrong_handler)
    result = chain.ask("介绍 Atlas 的背景。", doc_ids=["atlas-band"])
    assert result.status == "FAILED", result.model_dump()
    assert result.error.code == "answer_intent_mismatch"
    assert result.sql is None and result.table is None
    assert result.metadata["rejected_result_not_returned"] is True
    assert result.metadata["answer_intent_check"]["status"] == "mismatch"
