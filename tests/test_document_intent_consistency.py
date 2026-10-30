"""Unit fixtures for routing/answer shape; no model or database results."""
from copy import deepcopy

import pytest

from qa_agent.intent_consistency import (
    check_answer_intent,
    database_operation_request,
    document_information_request,
)
from qa_agent.schemas import AnswerEnvelope, IntentContract


@pytest.fixture(autouse=True)
def forbid_external_calls(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline unit fixtures must not call a model or DB")
    import socket
    import psycopg
    from qa_agent.llm import JsonLLM
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(psycopg, "connect", forbidden)
    monkeypatch.setattr(JsonLLM, "complete_json", forbidden)


@pytest.mark.parametrize("question", [
    "金属乐队是什么？",
    "Metallica是什么？",
    "请介绍一下U2。",
    "介绍一下这支乐队的背景。",
    "请解释爵士乐是什么。",
    "专辑是什么？",
    "什么是录音室专辑？",
    "手册里的销售额是怎么定义的？",
    "解释一下手册中的销售额计算公式。",
    "按这份资料，平均每张发票金额怎么算？",
    "“销售额”的定义是什么？",
    "客单价是什么？",
    "金属乐队是什么？请用两句话介绍，并附出处。",
    "Atlas是什么？用一句话回答并引用来源。",
    "介绍 Atlas 的背景，请分别说明成员与风格，每段给出引用。",
    "Please introduce this band.",
    "What is a studio album?",
])
def test_positive_document_information_requests(question):
    assert document_information_request(question)


@pytest.mark.parametrize("question", [
    "请列出这支乐队的专辑。",
    "介绍一下这个乐队，再统计去年销售额。",
    "解释手册定义，并计算一下2024年销售额。",
    "介绍销售额最高的艺术家。",
    "这支乐队一共有多少张专辑？",
    "查询catalog里有哪些表和列名。",
    "SQL的字段名是什么意思？",
    "专辑数据表的主键是什么？",
    "不要介绍这个乐队。",
    "不用解释定义，列出专辑。",
    "例如：介绍一下这个乐队。",
    "如果我问这个乐队是什么，你怎么处理？",
    "“介绍一下这个乐队”",
    '"What is this band?"',
    "List the albums and explain the band background.",
    "这是一个介绍乐队的例句。",
    "2024年发票销售额是多少？",
    "查找这位艺术家的专辑名称，再解释它是什么。",
    "介绍这支乐队，再给我它的全部专辑。",
    "介绍这支乐队，然后查它2024年卖了多少。",
    "这位客户的邮箱是什么？",
    "这首曲目的时长是什么？",
    "这张发票的总额是什么？",
    "Atlas是什么？再列出其专辑。",
    "", None,
])
def test_database_mixed_negative_examples_and_unknown_not_authorized(question):
    assert not document_information_request(question)


@pytest.mark.parametrize("shape", [
    {"status": "SUCCEEDED", "sql": "SELECT title FROM public.album", "intent": {"route": "sql"}},
    {"status": "SUCCEEDED", "sql": "SELECT title FROM public.album", "intent": {"route": "doc"}},
    {"status": "SUCCEEDED", "sql": None, "intent": {"route": "sql"}},
])
def test_successful_SQL_or_actual_SQL_intent_cannot_replace_introduction(shape):
    before = deepcopy(shape)
    result = check_answer_intent("介绍一下这支乐队。", shape)
    assert result["status"] == "mismatch"
    assert result["intent_consistent"] is False
    assert result["semantic_verified"] is False
    assert result["business_correctness_asserted"] is False
    assert shape == before
    assert result["evidence"][0]["authority"] == "actual_original_user_question_only"


def test_actual_AnswerEnvelope_model_supported_and_unknown_source_not_overridden():
    env = AnswerEnvelope(trace_id="unit", status="SUCCEEDED", answer="unit fixture",
                         sql="SELECT title FROM public.album",
                         intent=IntentContract(route="sql"))
    assert check_answer_intent("这支乐队是什么？", env)["status"] == "mismatch"
    assert check_answer_intent("列出这支乐队的专辑。", env, "doc")["status"] == "not_verified"


@pytest.mark.parametrize("shape", [
    {"status": "SUCCEEDED", "sql": None, "intent": {"route": "doc"}, "answer": "unit fixture"},
    {"status": "SUCCEEDED", "sql": "  ", "intent": None, "answer": "unverified text"},
])
def test_document_passthrough_is_only_a_structural_check(shape):
    result = check_answer_intent("手册里的销售额是什么？", shape)
    assert result["status"] == "passthrough" and result["intent_consistent"] is True
    assert result["semantic_verified"] is False
    assert "semantics_not_verified" in result["reason"]


@pytest.mark.parametrize("status", ["NEEDS_CLARIFICATION", "FAILED", "EMPTY_RESULT", "UNSUPPORTED"])
def test_non_success_is_not_relabelled_as_success_or_mismatch(status):
    result = check_answer_intent("这支乐队是什么？", {"status": status, "intent": {"route": "sql"}})
    assert result["status"] == "not_verified" and result["intent_consistent"] is None


def test_question_string_and_explicit_route_cannot_be_replaced_by_normalized_task():
    shape = {"status": "SUCCEEDED", "sql": "SELECT title FROM public.album", "intent": {"route": "sql"}}
    assert check_answer_intent("请介绍这支乐队。", shape, expected_route="sql")["status"] == "mismatch"
    assert check_answer_intent("请列出这支乐队的专辑。", shape, expected_route="doc")["status"] == "not_verified"
    assert check_answer_intent("这支乐队是什么？", None)["status"] == "not_verified"


@pytest.mark.parametrize("question, expected", [
    ("列出 Lumen 的 albums，只查询专辑名单。", True),
    ("列出 Lumen 的 albums。", True),
    ("查询数据库中的专辑名称。", True),
    ("介绍这支乐队，再统计去年销售额。", True),
    ("查询SQL的表名和列名。", True),
    ("专辑是什么？", False),
    ("SQL是什么？", False),
    ("手册中发票销售额怎么算？", False),
    ("不要查询数据库。", False),
    ("例如：列出这支乐队的专辑。", False),
    ('“列出这支乐队的专辑”', False),
    ("介绍 Atlas 的背景，请分别说明成员与风格，每段给出引用。", False),
])
def test_database_operation_is_independent_of_entity_and_document_count(question, expected):
    assert database_operation_request(question) is expected


@pytest.mark.parametrize('question', [
    '请介绍 Metallica，不需要列出专辑。',
    '介绍 Lumen 的背景，不用查询数据库。',
    '不要列出专辑，请介绍 Atlas 的音乐风格。',
    '请介绍这个作者；不要返回客户名单。',
    "Please introduce this band; do not list albums.",
])
def test_prohibited_SQL_clause_does_not_cancel_positive_information_intent(question):
    assert document_information_request(question)
    assert not database_operation_request(question)
    result = check_answer_intent(question, {
        'status': 'SUCCEEDED', 'sql': 'SELECT title FROM public.album', 'intent': {'route': 'sql'}})
    assert result['status'] == 'mismatch'


@pytest.mark.parametrize('question', [
    '不要介绍这个乐队，不需要列出专辑。',
    '例如：请介绍这个乐队，不需要列出专辑。',
    '如果只介绍这个乐队，不需要列出专辑。',
    '请介绍这个乐队，不需要列出专辑吗？',
    '请介绍这个乐队，不要列出专辑并计算去年销售额。',
    '请介绍这个乐队，再列出专辑。',
    '请介绍甲，不要查询专辑而要列出曲目。',
    '请介绍甲，不要查询专辑但要返回客户名单。',
    '请介绍甲，不要查询专辑仅返回曲目。',
    '请介绍甲，不要查询专辑还要列出曲目。',
    '请介绍甲，不要查询专辑列出曲目。',
])
def test_negative_or_uncertain_clause_scope_does_not_grant_document_route(question):
    assert not document_information_request(question)
