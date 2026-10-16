"""Safety and semantic boundaries for the formally applied joint DEV review."""
from hashlib import sha256
import json
from pathlib import Path

from eval.dataset import reviewed
from eval.rag_dataset import reviewed as rag_reviewed

ROOT = Path(__file__).resolve().parents[1]
VERSION = ROOT / "eval/datasets/manual-applied-20261013-v3"


def read_suite(name, suffix="dev"):
    return [json.loads(line) for line in (VERSION / f"{name}-{suffix}.jsonl").read_text(encoding="utf-8").splitlines()]


def test_new_review_versions_are_dev_only_and_original_sources_unchanged():
    manifest = json.loads((VERSION / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["total_count"] == 194
    assert manifest["active_count"] == 190
    assert manifest["new_holdout_predictions"] == 0
    assert manifest["new_llm_requests"] == 0
    assert manifest["holdout_content_read"] is False
    for source, expected in manifest["input_source_hashes"].items():
        assert sha256((ROOT / source).read_bytes()).hexdigest() == expected
    for suite in manifest["suites"]:
        cases = read_suite(suite)
        assert all(case["split"] == "dev" and case["enabled"] for case in cases)
        assert len(cases) == len({case["id"] for case in cases})
        check = rag_reviewed if suite == "rag" else reviewed
        assert all(check(case) for case in cases)
        assert all(case["gold_review"].get("human_confirmation_date") is None for case in cases)


def test_new_sql_38_excludes_unknown_sizes_even_when_fewer_than_three_known():
    from sqlglot import exp, parse_one
    case = next(case for case in read_suite("nl2sql") if case["id"] == "sql-38")
    query = parse_one(case["gold_sql"], read="postgres")
    assert query.args["where"].this.sql(dialect="postgres") == "bytes IS NOT NULL"
    assert query.args["limit"].expression.this == "3"
    assert [item.this.name for item in query.args["order"].expressions] == ["bytes", "track_id"]
    assert query.args["order"].expressions[0].args["desc"] is True
    assert query.args["order"].expressions[1].args["desc"] is False
    assert not list(query.find_all(exp.Coalesce))
    assert "NULLS LAST" not in case["gold_sql"]  # Sorting unknowns last would still admit them if fewer than three known.


def test_robust_23_average_has_no_unstated_subset_or_unit_conversion():
    from sqlglot import exp, parse_one
    case = next(case for case in read_suite("robust") if case["id"] == "robust-23")
    query = parse_one(case["gold_sql"], read="postgres")
    assert query.args.get("where") is None
    assert len(list(query.find_all(exp.Table))) == 1
    assert next(query.find_all(exp.Table)).name == "track"
    assert next(query.find_all(exp.Avg)).this.name == "milliseconds"
    assert not list(query.find_all(exp.Div))
    assert case["gold_columns"] == ["average_milliseconds"]


def test_half_open_boundary_and_explicit_top_one_do_not_use_coincidental_equal_results():
    from sqlglot import exp, parse_one
    cases = {case["id"]: case for case in read_suite("special")}
    query = parse_one(cases["sp01-30"]["gold_sql"], read="postgres")
    upper = next(query.find_all(exp.LT)).expression.sql()
    assert "2030-12-31" in upper
    assert cases["sp01-30"]["reference_intent"]["time_scope"]["end_exclusive"] == "2030-12-31"
    for identifier in ["sp03-08", "sp03-19", "sp03-23", "sp03-30"]:
        query = parse_one(cases[identifier]["gold_sql"], read="postgres")
        assert query.args["limit"].expression.this == "1"
        assert cases[identifier]["reference_intent"]["top_n"] == 1
    assert cases["sp03-23"]["controller"]["post_completion_turns"]


def test_defaulted_initial_conditions_do_not_require_hidden_old_supplements():
    cases = {case["id"]: case for case in read_suite("special")}
    for identifier in ["sp03-07", "sp03-08", "sp03-22", "sp03-23", "sp03-24", "sp03-29", "sp03-30"]:
        case = cases[identifier]
        assert case["category"] == "L1"
        assert case["missing_conditions"] == []
        assert case["controller"]["allowed_user_supplements"] == {}
        assert case["controller"]["max_clarification_followups"] == 0
    for identifier in ["sp03-29", "sp03-30"]:
        assert cases[identifier]["reference_intent"]["time_scope"]["kind"] == "all_existing_data"
        assert "2023" not in cases[identifier]["gold_sql"]
    assert cases["sp03-27"]["missing_conditions"] == ["numerator"]
    assert "denominator" not in cases["sp03-27"]["controller"]["allowed_user_supplements"]
    assert len(cases["sp03-27"]["controller"]["post_completion_turns"]) == 2


def test_rejected_ambiguous_references_and_explicit_band_choice_remain_distinct():
    all_cases = {case["id"]: case for case in read_suite("special", "all")}
    active = {case["id"] for case in read_suite("special")}
    assert "sp01-13" not in active and all_cases["sp01-13"]["canonical_id"] == "sp01-02"
    assert not {"sp01-06", "sp01-28", "sp03-10"} & active
    assert all_cases["sp03-10"]["conditional_reference_branches"][0]["gold_verification_evidence"]
    assert all_cases["sp03-10"]["gold_sql"] is None
    assert all_cases["sp03-10"]["controller"] is None
    assert all_cases["sp03-10"]["reference_intent"]["time_semantics"] is None
    assert "sp03-28" in active
    band = all_cases["sp03-28"]
    assert band["category"] == "L2" and band["missing_conditions"] == ["object"]
    assert not {"region_scope", "region_column"} & set(band["controller"]["allowed_user_supplements"])
    assert band["controller"]["allowed_user_supplements"]["object"]["value"] == {"column": "artist.name", "value": "Metallica"}
    assert band["controller"]["post_completion_turns"][-1]["expected_intent"]["region_scope"]["value"] == "Germany"
    for identifier in ["sp01-09", "sp01-27"]:
        case = all_cases[identifier]
        assert case["gold_sql"] is None
        assert case["reference_intent"]["automatic_union"] is False
        assert case["reference_intent"]["genre"]["value"] is None
        assert case["expected_final_intent"]["genre"]["value"] is None
        assert case["expected_bindings"] == [] and case["raw_expected_bindings"] == []
        assert case["expected_unresolved_constraints"]
        assert case["expected_candidates"] == [{"column": "genre.name", "value": "Rock"}, {"column": "genre.name", "value": "Rock And Roll"}]
    assert all(case["canonical_input"] == case["input"] for case in all_cases.values())
