"""D2 deterministic NLU/security checks; simulated approval/model/vector fixtures.

These tests are not real-model EX and do not approve the production alias CSV.
Real API/DB development-set runs are recorded separately by acceptance scripts.
"""
from dataclasses import replace
from hashlib import sha256
import csv
import json
from pathlib import Path
import subprocess
import sys
from time import sleep

import numpy as np
import pytest

from qa_agent.config import Settings, get_settings
from qa_agent.llm import LLMError
from qa_agent.nlu.linker import CandidateDecisions, Mention, ValueLinker, extract_mentions, field_scope
from qa_agent.nlu.rewrite import RewritePatch, apply_patches
from qa_agent.nlu.value_index import ValueIndex, ValueRecord, load_value_index, pinyin_key, record_id
from qa_agent.schemas import ChatRequest
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import (SQLValidationError, parameterize_strings, validate_sql, validate_value_bindings,
                                   validate_question_sources, validate_generation_claim)
from qa_agent.trace import TraceRecorder
from scripts.build_value_index import ALIAS_FIELDS, load_reviewed_aliases, write_index
from scripts.review_aliases import record_review


def value(column, standard, surface=None):
    return ValueRecord(record_id(column, standard), column, standard, surface or standard,
                       "synthetic-test-fixture", "alias" if surface else "standard",
                       "approved-in-test-fixture-only" if surface else None)


@pytest.fixture
def index():
    return ValueIndex([
        value("customer.country", "Brazil"), value("customer.country", "Brazil", "巴西"),
        value("customer.country", "USA"), value("customer.country", "USA", "美国"),
        value("customer.country", "USA", "老美"), value("customer.country", "Canada"),
        value("invoice.billing_country", "Brazil"), value("invoice.billing_country", "Brazil", "巴西"),
        value("genre.name", "Rock"), value("genre.name", "Rock", "摇滚"),
        value("genre.name", "Rock And Roll"), value("genre.name", "Rock And Roll", "摇滚"),
        value("artist.name", "Metallica"), value("customer.first_name", "Alice"),
        value("customer.city", "São Paulo"),
    ])


def linker(index, **kwargs):
    return ValueLinker(index, Settings(db_url="", nlu_fuzzy_threshold=0.82), **kwargs)


@pytest.mark.parametrize("question,canonical,method", [
    ("Brazil 的客户有多少位？", "Brazil", "exact"),
    ("老美的客户有多少位？", "USA", "exact"),
    ("巴稀的客户有多少位？", "Brazil", "pinyin"),
    ("ba xi 的客户有多少位？", "Brazil", "pinyin"),
    ("Brasil 的客户有多少位？", "Brazil", "fuzzy"),
    ("Metalica 乐队的名称是什么？", "Metallica", "fuzzy"),
])
def test_first_three_stages(index, question, canonical, method):
    result = linker(index).link(question)
    assert len(result.bindings) == 1
    assert result.bindings[0]["value"] == canonical
    assert result.bindings[0]["method"] == method
    assert canonical in result.rewritten_question


@pytest.mark.parametrize("question", [
    "列出来自巴西的客户编号、名字、姓氏和城市。",
    "来自巴西的客户有哪些名字和城市？",
])
def test_country_filter_wins_over_projection_words(index, question):
    assert field_scope(question, index) == ("customer.country",)
    result = linker(index).link(question)
    assert result.bindings[0]["column"] == "customer.country"
    assert result.bindings[0]["value"] == "Brazil"


def test_same_value_multiple_fields_is_scoped_not_arbitrary(index):
    customer = linker(index).link("巴西的客户有哪些？")
    invoice = linker(index).link("巴西的发票有多少张？")
    assert not customer.ambiguous and not invoice.ambiguous
    assert customer.bindings[0]["column"] == "customer.country"
    assert invoice.bindings[0]["column"] == "invoice.billing_country"


def test_explicit_negation_keeps_not_equal_filter(index):
    result = linker(index).link("国家不是 Brazil 的客户有多少？")
    assert result.bindings[0]["operator"] == "!="
    assert result.bindings[0]["value"] == "Brazil"


def test_explicit_alternative_countries_preserve_instead_of_impossible_and(index):
    result = linker(index).link("国家为 Brazil 或 USA 的客户有多少？")
    assert len(result.bindings) == 1
    assert result.bindings[0]["operator"] == "IN"
    assert result.bindings[0]["value"] == ["Brazil", "USA"]


def test_explicit_english_canonical_does_not_expand_to_similar_genre(index):
    result = linker(index).link("流派名称为 Rock 是什么？")
    assert not result.ambiguous
    assert result.bindings[0]["value"] == "Rock"


def test_reviewed_ambiguous_alias_never_picks_first(index):
    result = linker(index).link("名称为摇滚的流派有哪些？")
    assert len(result.ambiguous) == 1
    assert {item["standard_value"] for item in result.ambiguous[0].candidates} == {"Rock", "Rock And Roll"}
    assert result.bindings == [] and result.patches == []


def test_same_pinyin_preserves_multiple_ids():
    sample = ValueIndex([value("person.name", "张三"), value("person.name", "章三")])
    assert len(sample.pinyin[pinyin_key("张三")]) == 2
    mention = Mention("zhang san", 0, 9, ("person.name",))
    result = linker(sample).link("zhang san", mentions=[mention])
    assert len(result.ambiguous) == 1 and not result.bindings


def test_vector_stage_is_real_computation_in_deterministic_fixture():
    sample = ValueIndex([value("customer.country", "Brazil"), value("customer.country", "USA")],
                        np.asarray([[1.0, 0], [0, 1.0]], dtype=np.float32))
    trace = TraceRecorder()
    def encode(texts):
        sleep(0.015)
        return np.asarray([[1, 0]], dtype=np.float32)
    result = linker(sample, encode=encode).link("未登记说法", trace, [Mention("未登记说法", 0, 5, ("customer.country",))])
    assert result.bindings[0]["method"] == "vector"
    assert result.bindings[0]["value"] == "Brazil"
    assert next(step for step in trace.steps if step.name == "value_link_vector").latency_ms >= 10


class ScriptedDecisions:
    def __init__(self, status="resolved", illegal=False, omit=False, duplicate=False):
        self.calls = 0
        self.status, self.illegal, self.omit, self.duplicate = status, illegal, omit, duplicate
    def complete_json(self, system_prompt, user_prompt, response_model, trace=None):
        self.calls += 1
        data = json.loads(user_prompt)
        decisions = [{"mention_id": item["mention_id"], "status": self.status,
                      "candidate_id": ("forged-id" if self.illegal else item["candidates"][0]["candidate_id"]) if self.status == "resolved" else None}
                     for item in data["mentions"]]
        if self.omit:
            decisions = []
        if self.duplicate:
            decisions.append(decisions[0])
        return response_model(decisions=decisions)


def fifth_stage_fixture(model):
    sample = ValueIndex([value("customer.country", "Brazil"), value("customer.country", "USA")],
                        np.eye(2, dtype=np.float32))
    return linker(sample, llm=model, encode=lambda texts: np.asarray([[0.70710677, 0.70710677]], dtype=np.float32))


@pytest.mark.parametrize("status", ["resolved", "ambiguous", "unmatched"])
def test_fifth_stage_accepts_only_legal_ids_or_explicit_uncertainty(status):
    model = ScriptedDecisions(status)
    result = fifth_stage_fixture(model).link("模糊说法", mentions=[Mention("模糊说法", 0, 4, ("customer.country",))])
    assert model.calls == 1 and result.mentions[0].status == status
    if status != "resolved":
        assert not result.bindings
    else:
        assert result.bindings[0]["method"] == "llm"


@pytest.mark.parametrize("kwargs", [{"illegal": True}, {"omit": True}, {"duplicate": True}])
def test_fifth_stage_invalid_model_decision_is_technical_failure(kwargs):
    with pytest.raises(LLMError):
        fifth_stage_fixture(ScriptedDecisions(**kwargs)).link("模糊说法", mentions=[Mention("模糊说法", 0, 4, ("customer.country",))])


def test_fifth_stage_batches_mentions_once():
    model = ScriptedDecisions("unmatched")
    result = fifth_stage_fixture(model).link("模糊说法以及另一名称", mentions=[
        Mention("模糊说法", 0, 4, ("customer.country",)), Mention("另一名称", 6, 10, ("customer.country",))])
    assert model.calls == 1 and len(result.mentions) == 2


def test_vector_top5_does_not_erase_a_legal_fuzzy_candidate():
    standards = ["Brazil", "USA", "Germany", "Italy", "France", "Canada", "India"]
    vectors = np.asarray([[0, 1]] + [[score, np.sqrt(1 - score * score)] for score in [0.90, 0.88, 0.86, 0.84, 0.82, 0.80]], dtype=np.float32)
    sample = ValueIndex([value("customer.country", text) for text in standards], vectors)
    class SelectBrazil:
        def complete_json(self, system_prompt, user_prompt, response_model, trace=None):
            data = json.loads(user_prompt)
            candidates = data["mentions"][0]["candidates"]
            selected = next(item for item in candidates if item["standard_value"] == "Brazil")
            assert "fuzzy" in selected["stage_scores"] and "vector" not in selected["stage_scores"]
            return response_model(decisions=[{"mention_id": "mention-1", "status": "resolved", "candidate_id": selected["candidate_id"]}])
    result = linker(sample, llm=SelectBrazil(), encode=lambda texts: np.asarray([[1, 0]], dtype=np.float32)).link(
        "ba xi", mentions=[Mention("ba xi", 0, 5, ("customer.country",))])
    assert result.bindings[0]["value"] == "Brazil" and result.bindings[0]["method"] == "llm"


def test_role_typo_extracts_filter_before_employee_projection_fields():
    sample = ValueIndex([value("employee.title", "Sales Support Agent"), value("employee.title", "General Manager"),
                         value("employee.first_name", "Jane")])
    question = "列出职位为 Sales Suport Agent 的员工编号、名字和姓氏。"
    result = linker(sample).link(question)
    assert result.bindings[0]["column"] == "employee.title"
    assert result.bindings[0]["value"] == "Sales Support Agent"
    assert result.bindings[0]["method"] == "fuzzy"


def test_plan_ambiguity_guard_is_not_pending_alias_activation():
    sample = ValueIndex([value("genre.name", "Rock"), value("genre.name", "Rock And Roll")])
    assert all(item.kind == "standard" for item in sample.records)
    result = linker(sample).link("摇滚歌曲有多少？")
    assert result.ambiguous and not result.bindings and not result.patches
    assert result.ambiguous[0].guard_source == "user_total_plan:3.6.4_multi_candidate_value"
    assert result.ambiguous[0].match_method is None


def test_candidate_failure_retains_partial_provenance():
    handler = fifth_stage_fixture(ScriptedDecisions(illegal=True))
    with pytest.raises(LLMError):
        handler.link("模糊说法", mentions=[Mention("模糊说法", 0, 4, ("customer.country",))])
    assert handler.last_result.index_status == "ready"
    assert handler.last_result.mentions[0].candidates
    assert any(stage["method"] == "vector" for stage in handler.last_result.mentions[0].stages)


@pytest.mark.parametrize("text", ["Antarctica", "Wakanda", "南极洲", "Atlantis"])
def test_legal_absent_values_are_preserved_without_nearest_country(index, text):
    question = f"国家为{text}的客户有多少位？"
    result = linker(index, llm=ScriptedDecisions(illegal=True)).link(question)
    assert result.rewritten_question == question
    assert not result.bindings
    assert result.mentions[0].status == "unmatched"


@pytest.mark.parametrize("text", ["Narnia", "XYZ-land"])
def test_explicit_preserve_unknown_directive_is_generic(index, text):
    question = f"客户国家恰好为{text}，保留原值，不做近似。"
    result = linker(index, llm=ScriptedDecisions(illegal=True)).link(question)
    assert not result.bindings and result.rewritten_question == question
    assert result.mentions[0].original_text == text


def test_partial_name_query_keeps_like_meaning(index):
    question = "列出名字以 Alice 开头的客户。"
    assert extract_mentions(question, index) == []


def test_exact_scanning_does_not_match_inside_english_word(index):
    assert not linker(index).link("Brazilian 客户有多少？").bindings


@pytest.mark.parametrize("question", ["客户表共有多少位客户？", "媒体格式有哪些？", "艺术家名称是什么？", "工程检查客户数量", "帮我查客户有多少"])
def test_question_prose_does_not_become_a_value_mention(index, question):
    assert extract_mentions(question, index) == []


def test_patch_repeated_mentions_and_mixed_punctuation(index):
    question = "巴稀的客户，巴稀的客户（只核对国家）；"
    result = linker(index).link(question)
    assert len(result.patches) == 2
    assert result.rewritten_question == "Brazil的客户，Brazil的客户（只核对国家）；"
    assert len(result.bindings) == 1


@pytest.mark.parametrize("patches", [
    [RewritePatch(-1, 2, "巴西", "Brazil", "exact", "v-fixture")],
    [RewritePatch(0, 2, "巴稀", "Brazil", "pinyin", "v-fixture")],
    [RewritePatch(0, 2, "巴西", "Brazil", "exact", "v-fixture"), RewritePatch(1, 3, "西的", "X", "exact", "v-fixture")],
    [RewritePatch(0, 2, "巴西", "Brazil", "exact", "")],
])
def test_invalid_patch_never_modifies_question(patches):
    with pytest.raises(ValueError):
        apply_patches("巴西的客户", patches)


def alias_csv(tmp_path, rows):
    path = tmp_path / "aliases.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=ALIAS_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_pending_rejected_and_unidentified_review_rows_never_enter_index(tmp_path):
    rows = [{"standard_value": "Brazil", "column": "customer.country", "alias": alias,
             "source": "synthetic-test-fixture", "review_status": status, "reviewer": reviewer,
             "alias_id": alias} for alias, status, reviewer in [
                 ("巴西", "approved", "synthetic-test-reviewer"), ("巴稀", "pending", ""),
                 ("巴西共和国", "rejected", "synthetic-test-reviewer"), ("XX", "approved", "")]]
    aliases, audit = load_reviewed_aliases(alias_csv(tmp_path, rows), [value("customer.country", "Brazil")])
    assert [item.surface for item in aliases] == ["巴西"]
    assert audit["accepted_count"] == 1 and audit["excluded_count"] == 3


def test_alias_requires_real_canonical_field_value_and_deduplicates(tmp_path):
    rows = [{"standard_value": standard, "column": "customer.country", "alias": alias,
             "source": "synthetic-test-fixture", "review_status": "approved", "reviewer": "test-reviewer", "alias_id": str(i)}
            for i, (standard, alias) in enumerate([("Brazil", "巴西"), ("Brazil", "巴西"), ("FakeCountry", "假国家")])]
    aliases, audit = load_reviewed_aliases(alias_csv(tmp_path, rows), [value("customer.country", "Brazil")])
    assert len(aliases) == 1 and len(audit["invalid"]) == 1


def test_vector_record_shape_must_match_and_be_normalized():
    with pytest.raises(ValueError):
        ValueIndex([value("customer.country", "Brazil")], np.eye(2))
    with pytest.raises(ValueError):
        ValueIndex([value("customer.country", "Brazil")], np.asarray([[2, 0]]))


def test_rebuild_replaces_records_and_hash_guards_corruption(tmp_path):
    values = [value("customer.country", "Brazil")]
    for _ in range(2):
        write_index(values, [], tmp_path, [], {"accepted_count": 0}, build_embeddings=False, settings=Settings(db_url=""))
    assert len(load_value_index(tmp_path).records) == 1
    (tmp_path / "records.jsonl").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="摘要"):
        ValueIndex.load(tmp_path)


def test_review_decision_requires_hash_and_explicit_human_ids(tmp_path):
    rows = [{"standard_value": "Brazil", "column": "customer.country", "alias": "巴西", "source": "synthetic",
             "review_status": "pending", "reviewer": "", "alias_id": "fixture-id"}]
    path = alias_csv(tmp_path, rows)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        record_review(path, "bad-hash", "synthetic-reviewer", ["fixture-id"], [], tmp_path / "audit.json")
    assert path.read_bytes() == before
    audit = record_review(path, sha256(before).hexdigest(), "synthetic-reviewer", ["fixture-id"], [], tmp_path / "audit.json")
    assert audit["pending_count"] == 0 and audit["approved"][0]["reviewer"] == "synthetic-reviewer"
    assert load_reviewed_aliases(path, [value("customer.country", "Brazil")])[1]["accepted_count"] == 1


@pytest.fixture
def catalog():
    return load_catalog(get_settings().catalog_path)


@pytest.mark.parametrize("sql", [
    "SELECT COUNT(*) FROM customer WHERE country='Brazil'",
    "SELECT COUNT(*) FROM customer c WHERE c.country='Brazil' AND c.customer_id>0",
    "SELECT COUNT(*) FROM customer WHERE LOWER(country)='brazil'",
    "SELECT COUNT(*) FROM customer WHERE country IN ('Brazil')",
    "SELECT COUNT(*) FROM customer WHERE (country='Brazil' AND customer_id>0) OR (country='Brazil' AND customer_id<100)",
])
def test_ast_binding_accepts_mandatory_real_column_value(catalog, sql):
    checked = validate_sql(sql, catalog)
    validate_value_bindings(checked.sql, catalog, [{"column": "customer.country", "operator": "=", "value": "Brazil"}])


@pytest.mark.parametrize("sql", [
    "SELECT COUNT(*) FROM customer WHERE country='USA'",
    "SELECT COUNT(*) FROM customer WHERE country='Brazil' OR 1=1",
    "SELECT country='Brazil' FROM customer",
    "SELECT COUNT(*) FROM customer /* country='Brazil' */",
    "SELECT COUNT(*) FROM customer WHERE country IN ('Brazil','USA')",
    "SELECT COUNT(*) FROM customer WHERE NOT(country='Brazil')",
    "SELECT COUNT(*) FROM customer WHERE country LIKE 'Brazil%'",
    "SELECT COUNT(*) FROM customer WHERE EXISTS(SELECT 1 FROM customer c WHERE c.country='Brazil')",
    "SELECT COUNT(*) FROM customer WHERE country='Brazil' UNION ALL SELECT COUNT(*) FROM customer WHERE country='USA'",
    "SELECT COUNT(*) FROM invoice WHERE billing_country='Brazil'",
])
def test_ast_binding_rejects_wrong_dropped_or_bypassed_filter(catalog, sql):
    checked = validate_sql(sql, catalog)
    with pytest.raises(SQLValidationError):
        validate_value_bindings(checked.sql, catalog, [{"column": "customer.country", "operator": "=", "value": "Brazil"}])


def test_parameterization_uses_ast_and_preserves_apostrophe_like_and_modulo():
    sql = "SELECT customer_id FROM customer WHERE country='Brazil' AND first_name LIKE '%O''Brien%' AND customer_id % 2 = 0"
    parameterized, parameters = parameterize_strings(sql)
    assert set(parameters.values()) == {"Brazil", "%O'Brien%"}
    assert "%% 2" in parameterized
    assert "Brazil" not in parameterized and "O'Brien" not in parameterized
    assert "%(qa_value_0)s" in parameterized


@pytest.mark.parametrize("question", ["仅查询 d2_nonexistent_table_20261010 表，不得换成customer。",
                                    "表名为 no_such_table，列出5行。", "Query table named no_such_table"])
def test_explicit_unknown_source_is_rejected_before_model(catalog, question):
    with pytest.raises(SQLValidationError, match="真实目录"):
        validate_question_sources(question, catalog)


@pytest.mark.parametrize("question,expected", [("查询 customer 表前5行", ["customer"]),
                                                ("查询 public.invoice 表", ["invoice"]),
                                                ("来自 USA 的客户有多少？", []),
                                                ("名字为 Alice 的客户有多少？", [])])
def test_source_guard_does_not_treat_country_column_or_prose_as_table(catalog, question, expected):
    assert validate_question_sources(question, catalog) == expected


def test_model_refusal_is_not_empty_database_result():
    with pytest.raises(SQLValidationError, match="明确说明无法执行"):
        validate_generation_claim("查询目录之外的表", "SELECT 1 FROM customer LIMIT 0", "无法执行：目标表不在数据库目录中。")


def test_unrequested_constant_zero_limit_is_rejected_but_valid_empty_semantics_remain(catalog):
    with pytest.raises(SQLValidationError, match="占位查询"):
        validate_generation_claim("列出前5行", "SELECT 1 FROM customer LIMIT 0", "占位")
    validate_generation_claim("列出前0行", "SELECT 1 FROM customer LIMIT 0", "显式零行检查")
    validate_generation_claim("无匹配客户", "SELECT customer_id FROM customer WHERE country='Narnia'", "合法空结果")
    validate_generation_claim("无匹配数量", "SELECT COUNT(*) FROM customer WHERE country='Narnia'", "合法计数0")
    assert validate_sql("SELECT 1 FROM customer LIMIT 0", catalog).tables_used == ["customer"]


def test_pipeline_explicit_unknown_source_never_calls_model_or_executor(monkeypatch):
    from qa_agent.pipeline import chat
    class NeverModel:
        def complete_json(self, **kwargs):
            pytest.fail("未知显式来源不能交给模型换表")
    def forbidden(*args, **kwargs):
        pytest.fail("未知显式来源不能执行customer占位")
    monkeypatch.setattr("qa_agent.sql.executor.execute_sql", forbidden)
    response = chat(ChatRequest(message="请仅查询 d2_nonexistent_table_20261010 表，列出前5行，不得换成customer。"), llm=NeverModel())
    assert response.status == "FAILED" and response.error.code == "sql_rejected"
    assert response.sql is None and response.table is None
    assert "sql_exec" not in [step.name for step in response.steps]


def test_builder_help_does_not_touch_database_or_model():
    result = subprocess.run([sys.executable, "scripts/build_value_index.py", "--help"], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0
    assert "--catalog" in result.stdout and "--output-dir" in result.stdout and "--audit-output" in result.stdout


def test_pipeline_wrong_model_value_never_executes(monkeypatch, index):
    from qa_agent.pipeline import chat
    class WrongSQL:
        def complete_json(self, system_prompt, user_prompt, response_model, trace=None):
            return response_model(sql="SELECT COUNT(*) FROM customer WHERE country='USA'", explanation="simulated wrong value")
    monkeypatch.setattr("qa_agent.nlu.value_index.load_value_index", lambda path: index)
    def forbidden(*args, **kwargs):
        pytest.fail("错误标准值不得执行")
    monkeypatch.setattr("qa_agent.sql.executor.execute_sql", forbidden)
    result = chat(ChatRequest(message="巴西的客户有多少？"), llm=WrongSQL(), settings=replace(get_settings(), sql_repair_attempts=0))
    assert result.status == "FAILED" and result.error.code == "sql_rejected"
    assert "sql_exec" not in [step.name for step in result.steps]
    assert result.metadata["nlu"]["bindings"][0]["value"] == "Brazil"


def test_pipeline_true_ambiguity_uses_existing_protocol_without_sql(monkeypatch, index):
    from qa_agent.pipeline import chat
    monkeypatch.setattr("qa_agent.nlu.value_index.load_value_index", lambda path: index)
    class NeverModel:
        def complete_json(self, **kwargs):
            pytest.fail("已知真实歧义不应生成SQL")
    result = chat(ChatRequest(message="名称为摇滚的流派有哪些？"), llm=NeverModel())
    assert result.status == "NEEDS_CLARIFICATION"
    assert result.sql is None and not result.table
    # D3 keeps the D2 no-SQL ambiguity guard and adds a versioned resume card.
    assert result.intent.unresolved and result.clarification["resume_supported"] is True
    assert result.clarification["clarification_id"]
    assert result.clarification["intent_version"] == result.intent.intent_version


@pytest.mark.integration
def test_real_database_parameterized_binding_wiring(monkeypatch, index):
    from qa_agent.pipeline import chat
    monkeypatch.setattr("qa_agent.nlu.value_index.load_value_index", lambda path: index)
    class FixedSQL:
        def complete_json(self, system_prompt, user_prompt, response_model, trace=None):
            payload = json.loads(user_prompt)
            assert payload["verified_value_bindings"][0]["value"] == "Brazil"
            return response_model(sql="SELECT COUNT(*) AS n FROM customer WHERE country='Brazil'", explanation="simulated model, real read-only DB")
    result = chat(ChatRequest(message="巴西的客户有多少？"), llm=FixedSQL())
    assert result.status == "SUCCEEDED" and result.table == [{"n": 5}]
    executed = next(step for step in result.steps if step.name == "sql_exec")
    assert "%(qa_value_0)s" in executed.input_summary["sql"]
    assert "'Brazil'" in result.sql
