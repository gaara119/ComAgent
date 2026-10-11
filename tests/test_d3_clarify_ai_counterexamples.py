"""Independent AI review counterexamples; these tests do not call DeepSeek."""
from types import SimpleNamespace
from qa_agent.clarify.extractor import extract_intent, needs_semantic_model
from qa_agent.clarify.rules import SemanticIntent, explicit_period, RuleEngine


class Catalog:
    database = "chinook"
    metadata = {"invoice_date_range": {"min_date": "2021-01-01", "max_date": "2025-12-22"}}

    def prompt_schema(self):
        return "invoice: invoice_date,total"


def model(**fields):
    return SimpleNamespace(complete_json=lambda *args, **kwargs: SemanticIntent(**fields))


def test_conflicting_years_must_enter_semantic_extraction():
    assert needs_semantic_model("统计2024年的发票销售额，但日期必须从2023年1月1日到2023年12月31日。")


def test_explicit_day_range_is_not_overwritten_with_whole_year():
    question = "2024年1月1日到2024年3月31日的发票销售额是多少？"
    period = explicit_period(question)
    assert period["current"]["start"] == "2024-01-01"
    assert period["current"]["end"] == "2024-04-01"
    result = extract_intent(question, Catalog(), model(metric="invoice_revenue"))
    assert result.time_scope["current"]["end"] == "2024-04-01"


def test_latest_year_phrase_is_not_automatically_a_calendar_year():
    question = "数据中最近一年的发票销售额是多少？"
    result = extract_intent(question, Catalog(), model(metric="invoice_revenue", task_type="aggregation"))
    assert result.time_scope is None
    assert result.time_ambiguous
    assert RuleEngine().evaluate(question, result).level == "L2"


def test_explicit_latest_record_year_declares_partial_year_limit():
    question = "数据中最近有记录的年份的发票销售额是多少？"
    result = extract_intent(question, Catalog(), model(metric="invoice_revenue", task_type="aggregation"))
    assert result.time_scope["current"]["start"] == "2025-01-01"
    assert any("不代表完整年度" in statement for statement in result.assumptions)
