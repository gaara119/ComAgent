import pytest
import yaml
from pathlib import Path

from scripts.d4_bench_utils import compare_case, p50_p90, summarize, trace_cost
from scripts.d4_sql_scale import load_cases, remap_sql
from scripts.scale_data import build_sql


def test_stress_copy_never_writes_or_redefines_original_public_tables():
    original = yaml.safe_load((Path(__file__).parents[1] / "data/catalog/chinook.yaml").read_text(encoding="utf-8"))
    sql = build_sql(original,"d4_stress_10000",10000)
    writes = [line for line in sql.splitlines() if line.startswith(("INSERT", "UPDATE", "ALTER TABLE", "CREATE TABLE"))]
    assert writes
    assert all('"d4_stress_10000".' in line.split(" SELECT ")[0] for line in writes)
    assert "DROP " not in sql
    assert "TRUNCATE " not in sql
    assert "SET LOCAL statement_timeout = '5000ms'" in sql
    assert "INTERVAL '5 years'" in sql
    assert sql.count(" FOREIGN KEY ") == sum(len(table["foreign_keys"]) for table in original["tables"])
    assert "GRANT SELECT ON ALL TABLES" in sql
    assert "GRANT ALL" not in sql


@pytest.mark.parametrize("schema,target", [("public",10000),("d4_stress_10",10000),("d4_stress_10000;DROP public",10000),
                                           ("d4_stress_10000",20000)])
def test_stress_write_scope_restrictions(schema,target):
    with pytest.raises(ValueError):
        build_sql({"tables":[]},schema,target)


def test_gold_recomputed_on_copy_by_identical_ast_except_schema():
    sql = "SELECT SUM(l.quantity) FROM public.invoice_line l JOIN invoice i ON i.invoice_id=l.invoice_id WHERE i.billing_country='USA'"
    remapped = remap_sql(sql,"d4_stress_100000")
    assert remapped.count("d4_stress_100000.") == 2
    assert "'USA'" in remapped
    assert "SUM(l.quantity)" in remapped
    with pytest.raises(ValueError):
        remap_sql("SELECT * FROM private.invoice","d4_stress_100000")
    with pytest.raises(ValueError):
        remap_sql("WITH t AS (SELECT * FROM invoice) SELECT * FROM t","d4_stress_100000")


def test_exactly_twenty_existing_dev_questions_no_held_content():
    cases,_ = load_cases()
    assert len(cases) == len({case["id"] for case in cases}) == 20
    assert all(case["split"] == "dev" for case in cases)
    assert not any(case["id"] in {"sql-38","robust-23"} for case in cases)


def test_cost_includes_selector_calls_and_preserves_nested_durations():
    envelope = {"steps":[
        {"name":"schema_link","latency_ms":2300},
        {"name":"schema_prune","latency_ms":2200},
        {"name":"llm","latency_ms":2100,"output_summary":{"usage":{"prompt_tokens":100,"total_tokens":130}}},
        {"name":"sql_gen","latency_ms":1100},
        {"name":"llm","latency_ms":1000,"output_summary":{"usage":{"prompt_tokens":200,"total_tokens":230}}}]}
    cost = trace_cost(envelope)
    assert cost["usage"]["prompt_tokens"] == 300
    assert cost["usage"]["schema_selection_prompt_tokens"] == 100
    assert cost["usage"]["sql_generation_prompt_tokens"] == 200
    assert cost["stages_ms"]["schema_selection"] == 4500
    assert cost["model_attempts"]["all"] == 2
    assert cost["stages_ms"]["model_calls"] == 3100
    assert p50_p90([1,2,3])["p90_ms"] == 2.8


def test_real_trace_append_order_assigns_selector_and_sql_calls_separately():
    from qa_agent.trace import TraceRecorder
    recorder=TraceRecorder()
    with recorder.step("schema_link"):
        pass
    with recorder.step("schema_prune"):
        with recorder.step("llm") as step:
            step.output_summary={"usage":{"prompt_tokens":100}}
    with recorder.step("sql_gen"):
        with recorder.step("llm") as step:
            step.output_summary={"usage":{"prompt_tokens":200}}
    assert [step.name for step in recorder.steps]==["schema_link","schema_prune","llm","sql_gen","llm"]
    for step,duration in zip(recorder.steps,[10,20,15,30,22]):
        step.latency_ms=duration
    cost=trace_cost({"steps":[step.model_dump() for step in recorder.steps]})
    assert cost["stages_ms"]["schema_selection"]==30
    assert cost["stages_ms"]["sql_generation"]==30
    assert cost["usage"]["schema_selection_prompt_tokens"]==100
    assert cost["usage"]["sql_generation_prompt_tokens"]==200
    assert cost["usage"]["prompt_tokens"]==300


def test_missing_trace_is_not_invented_as_zero_stage_latency():
    summary = summarize([
        {"matched": False, "elapsed_ms": 50, "failure_category": "runner_exception"},
        {"matched": True, "elapsed_ms": 100, "response": {"status": "SUCCEEDED"},
         "cost": {"stages_ms": {"sql_execution": 20}, "model_attempts": {"all": 2}}}])
    assert summary["requests"] == 2
    assert summary["ex"] == .5
    assert summary["stages"]["sql_execution"] == {"p50_ms": 20, "p90_ms": 20, "n": 1}
    assert summary["trace_available_requests"] == 1
    assert summary["response_statuses"]["NO_RESPONSE"] == 1


def test_plan_two_decimal_numeric_ex_keeps_legacy_exact_result_separate():
    from types import SimpleNamespace
    case = {"column_types": ["number"], "integer_columns": [], "monetary_columns": []}
    gold = SimpleNamespace(rows=[{"average": "123.456"}], columns=["average"])
    response = {"status": "SUCCEEDED", "table": [{"mean": "123.46"}],
                "metadata": {"result_columns": ["mean"]}}
    result = compare_case(case, response, None, gold)
    assert result["matched"] is True
    assert result["legacy_matched"] is False


def test_rag_efficiency_twenty_questions_share_ten_real_pdf_dev_evidence_pages():
    from scripts.d4_rag_scale import efficiency_cases
    path=Path(__file__).parents[1]/"eval/artifacts/d2-final/review/rag-dev-view.jsonl"
    cases,pages=efficiency_cases(path)
    assert len(cases)==20
    assert len(pages)==10
    assert len({doc for doc,_ in pages})==5
    assert len({case["efficiency_id"] for case in cases})==20
    assert all(case["split"]=="dev" and case["answerable"] for case in cases)
    for original,variant in zip(cases[::2],cases[1::2]):
        assert original["question"]!=variant["question"]
        for field in ("answer","reference_text","doc_id","physical_pages","family_id"):
            assert original[field]==variant[field]
        assert variant["gold_review"]["status"]=="pending_human_review"
        assert variant["gold_review"]["reviewer"] is None
