"""Bounded consistency between a current information request and answer shape.

This is neither an entity resolver nor a semantic/clarification gate.  It does
not select a document, query, default, or replacement subject.  A passthrough
only means that the specific SQL-for-document contradiction was not observed.
"""
from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import re

from pydantic import BaseModel

from qa_agent.fusion.obligations import clearly_database_question


_EXAMPLE_OR_NEGATIVE = re.compile(
    r"例如|比如|示例|例句|举例|假如|假设|如果|当我问|"
    r"不要|不用|无需|不必|不需要|(?<!分)别(?:再|给我|介绍|解释|讲|说明)|"
    r"不是(?:要|让|叫)|并非(?:要|让)|"
    r"\b(?:example|suppose|imagine|do\s+not|don't|not\s+asking)\b", re.I)
_TECHNICAL_QUERY = re.compile(
    r"\bSQL\b|数据库|数据库表|数据表|表结构|表名|列名|字段|主键|外键|"
    r"\b(?:schema|catalog|columns?|tables?|primary\s+key|foreign\s+key)\b", re.I)
_DATABASE_ACTION = re.compile(
    r"统计|汇总|求和|算出|求出|算一下|计算一下|查询|查一下|"
    r"排名|排行|最多|最少|最高|最低|前\s*(?:\d+|[一二三四五六七八九十百]+)\s*(?:名|位|个|条)|"
    r"(?:列出|列一下|返回|显示|展示|给我|给出|罗列|导出|查出|查找|找出).{0,60}(?:专辑|曲目|歌曲|发票|客户|员工|订单|\balbums?\b|\btracks?\b|\binvoices?\b|\bcustomers?\b)|"
    r"(?:查|查看|查询|计算|算|求)(?:一下|一算|出)?.{0,50}(?:销售额|销售金额|购买量|销量|购买数量|发票|客户|金额|数量|张数|首数|多少)|"
    r"(?:专辑|曲目|歌曲|发票|客户|员工|订单).{0,40}(?:有多少|多少张|多少首|多少个|多少名|多少位)|"
    r"\b(?:query|select|aggregate|rank|sum|count|calculate)\b|"
    r"\b(?:list|return|show|find|export)\b.{0,60}\b(?:albums?|tracks?|invoices?|customers?|employees?)\b",
    re.I)
_CATALOG_VALUE_QUESTION = re.compile(
    r"(?:客户|员工|发票|曲目|歌曲|专辑).{0,18}"
    r"(?:生日|姓名|名字|编号|\bID\b|电话|邮箱|地址|时长|毫秒|单价|价格|总额|余额|日期|文件大小)"
    r".{0,8}(?:是什么|是啥|多少|哪)|"
    r"(?:专辑|曲目|歌曲|发票|客户|员工).{0,20}(?:有哪些|有哪几)", re.I)
_INTRODUCTION = re.compile(
    r"^(?:(?:请|麻烦|帮我|给我|能否|能不能|可以|可否|我想|想要|想)\s*)*"
    r"(?:介绍|解释|讲讲|说说|概述|描述|说明|科普|了解)\s*(?:一下|下)?\s*\S|"
    r"^(?:please\s+)?(?:introduce|explain|describe|tell\s+me\s+about|give\s+me\s+an?\s+overview\s+of)\s+\S",
    re.I)
_DEFINITION = re.compile(
    r"(?:是什么|是啥|什么意思|指什么|怎么定义(?:的)?|如何定义(?:的)?|定义是什么|口径是什么|如何计算|怎么算)"
    r"\s*[？?。.!！]*$|"
    r"^(?:什么是|何谓)\s*\S|"
    r"^(?:what\s+(?:is|are)|who\s+(?:is|are)|how\s+is).+\??$", re.I)
_WHOLE_QUOTATION = re.compile(r'^(?:“[^”]*”|‘[^’]*’|「[^」]*」|"[^"\n]*"|`[^`\n]*`)\s*[。.!！?？]*$')
_CITATION_DIRECTION = r"(?:引用|附上?|注明|标明|给出)(?:原文)?(?:来源|出处|依据)"
_BRIEF_DIRECTION = (
    r"(?:只)?(?:用|以)[一二两三四五六七八九十\d]+句(?:话)?(?:回答|介绍|说明|解释)"
    r"(?:即可|就好)?(?:\s*[，,]?\s*(?:并|并且)\s*" + _CITATION_DIRECTION + r")?")
_OUTPUT_TAIL = re.compile(
    r"(?:[，,。！？!?；;]\s*|(?:并|并且)\s*)(?:请\s*)?(?:" +
    _BRIEF_DIRECTION + "|" + _CITATION_DIRECTION + r")\s*[。.!！?？]*$")

_NEGATED_DATABASE_PREFIX = re.compile(
    r"^(?:请\s*)?(?:不要|不用|无需|无须|不必|不需要|别再|别|do\s+not|don't)\s*", re.I)


def _recognition_text(text: str) -> str:
    """Exclude only standalone, explicitly prohibited database clauses.

    This affects recognition, never the stored/user/model request. A ban on
    listing records is not a ban on the adjacent positive introduction.
    Quoted, hypothetical, interrogative and mixed clauses remain conservative.
    """
    kept = []
    parts = re.split(r'([，,。；;\n])', text)
    for index in range(0, len(parts), 2):
        raw = parts[index]
        clause = raw.strip()
        prefix = _NEGATED_DATABASE_PREFIX.match(clause)
        if prefix:
            body = clause[prefix.end():].strip()
            if (not re.search(r'[？?"“”\'‘’`]|例如|比如|假设|如果|然后|再|并|但|而|仅|只要|还要|也要|同时|\b(?:and|but|then|only|also)\b', body, re.I)
                    and len(list(_DATABASE_ACTION.finditer(body))) <= 1
                    and (_DATABASE_ACTION.search(body) or
                         re.match(r'(?:使用|调用|use)\s*', body, re.I) and _TECHNICAL_QUERY.search(body))):
                continue
        kept.append(raw + (parts[index + 1] if index + 1 < len(parts) else ''))
    return ''.join(kept).strip('，,。；;\n ')


def database_operation_request(question: str) -> bool:
    """Recognize a positive database operation, independently of doc scope.

    Selecting one or several documents and mentioning a registered entity do
    not decide this classification.  Concept explanations and instruction
    examples are not database operations; an explicit mixed request may be.
    """
    if not isinstance(question, str) or not question.strip():
        return False
    text = question.strip()
    if not _WHOLE_QUOTATION.fullmatch(text):
        text = _recognition_text(text)
    if _WHOLE_QUOTATION.fullmatch(text) or _EXAMPLE_OR_NEGATIVE.search(text):
        return False
    if re.fullmatch(
            r"(?:请解释\s*)?(?:SQL|数据库|数据表|查询|统计|计算|汇总)"
            r"(?:方法|公式|含义)?(?:是什么|是什么意思|什么意思)\s*[？?。.!！]*", text, re.I):
        return False
    if _DATABASE_ACTION.search(text) or _TECHNICAL_QUERY.search(text):
        return True
    try:
        return clearly_database_question(text)
    except (ValueError, TypeError):
        return False


def document_information_request(question: str) -> bool:
    """Recognize only positive, non-mixed introductions/explanations/definitions.

    Entity or catalog-object names alone never select SQL: for example,
    ``专辑是什么`` remains an information request.  Unsupported wording,
    examples, negation, database operations and mixed tasks return False.
    """
    if not isinstance(question, str) or not question.strip():
        return False
    text = question.strip()
    if not _WHOLE_QUOTATION.fullmatch(text):
        text = _recognition_text(text)
    if (_WHOLE_QUOTATION.fullmatch(text)
            or _EXAMPLE_OR_NEGATIVE.search(text)
            or _TECHNICAL_QUERY.search(text)
            or _DATABASE_ACTION.search(text)
            or _CATALOG_VALUE_QUESTION.search(text)):
        return False
    # A following length/citation instruction is part of the original request,
    # not a new database task.  Remove only this finite suffix for recognition;
    # the original question is retained and hashed by the checker unchanged.
    information_text = text
    for _ in range(3):
        shortened = _OUTPUT_TAIL.sub("", information_text).strip()
        if shortened == information_text:
            break
        information_text = shortened
    if not (_INTRODUCTION.search(information_text) or _DEFINITION.search(information_text)):
        return False
    try:
        if clearly_database_question(text):
            return False
    except (ValueError, TypeError):
        # An unresolved source/entity shape cannot authorize a document route.
        return False
    return True


def _mapping(value) -> Mapping | None:
    if isinstance(value, BaseModel):
        return value.model_dump()
    return value if isinstance(value, Mapping) else None


def check_answer_intent(original_question, envelope, expected_route=None) -> dict:
    """Report a successful SQL answer substituted for a pure information task.

    ``expected_route`` is diagnostic only; it never overrides the actual user
    wording or grants tools.  No state or envelope is mutated.  The evidence
    exposes hashes and structural observations, not a semantic correctness
    assertion about either the answer or the selected entity.
    """
    result = {
        "check": "pure_document_answer_shape",
        "status": "not_verified",
        "intent_consistent": None,
        "semantic_verified": False,
        "business_correctness_asserted": False,
        "expected_route": expected_route,
        "evidence": [],
    }
    if not document_information_request(original_question):
        return result | {"reason": "original_question_not_a_proved_pure_information_request"}
    result["evidence"].append({
        "kind": "original_current_information_request",
        "question_sha256": sha256(original_question.encode("utf-8")).hexdigest(),
        "authority": "actual_original_user_question_only",
    })
    actual = _mapping(envelope)
    if actual is None or actual.get("status") != "SUCCEEDED":
        return result | {"reason": "no_successful_answer_shape_to_check"}
    sql = actual.get("sql")
    sql_present = isinstance(sql, str) and bool(sql.strip())
    intent = _mapping(actual.get("intent"))
    actual_route = intent.get("route") if intent is not None else None
    if sql_present:
        result["evidence"].append({
            "kind": "actual_SQL_present",
            "sql_sha256": sha256(sql.encode("utf-8")).hexdigest(),
        })
    if actual_route is not None:
        result["evidence"].append({"kind": "actual_intent_route", "route": actual_route})
    if sql_present or actual_route == "sql":
        return result | {
            "status": "mismatch", "intent_consistent": False,
            "reason": "successful_SQL_answer_substitutes_for_original_information_request",
        }
    return result | {
        "status": "passthrough", "intent_consistent": True,
        "reason": "no_SQL_for_document_shape_conflict_observed; answer_semantics_not_verified",
    }
