from decimal import Decimal

import pytest

from eval.metrics import compare_plan_results, compare_results
from qa_agent.config import get_settings
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.repair_guard import (string_filter_contract, validate_repair_filters,
                                       validate_chinook_fk_joins)
from qa_agent.sql.validator import SQLValidationError
from qa_agent.sql.validator import validate_value_bindings
from qa_agent.sql.result_format import percentage_formats, display_percentage


@pytest.fixture
def catalog():
    return load_catalog(get_settings().catalog_path)


def test_lookup_join_allowed_without_value_linking(catalog):
    validate_chinook_fk_joins("SELECT COUNT(*) FROM album a JOIN artist r ON a.artist_id=r.artist_id WHERE r.name='Metallica'", catalog)
    validate_chinook_fk_joins("SELECT COUNT(*) FROM track t JOIN media_type m ON t.media_type_id=m.media_type_id WHERE m.name='Protected AAC audio file'", catalog)


@pytest.mark.parametrize("on", ["TRUE", "a.album_id=r.artist_id", "a.artist_id=r.artist_id OR TRUE"])
def test_lookups_require_mandatory_real_foreign_key(catalog, on):
    with pytest.raises(SQLValidationError):
        validate_chinook_fk_joins(f"SELECT COUNT(*) FROM album a JOIN artist r ON {on}", catalog)


def test_repair_cannot_change_artist_filter_into_album_title(catalog):
    original = "SELECT COUNT(*) FROM album a JOIN artist r ON a.artist_id=r.artist_id WHERE r.name='Metallcia'"
    contract = string_filter_contract(original, catalog)
    assert contract
    validate_repair_filters(contract, original.replace(" r ", " b ").replace("r.", "b."), catalog)
    with pytest.raises(SQLValidationError):
        validate_repair_filters(contract, "SELECT COUNT(*) FROM album WHERE title='Metallcia'", catalog)
    with pytest.raises(SQLValidationError):
        validate_repair_filters(contract, original.replace("r.name='Metallcia'", "r.name='Metallcia' OR TRUE"), catalog)


def test_plan_ex_allows_actual_name_column_with_one_global_mapping(catalog):
    gold = [{"id": 1, "amount": "12.345"}, {"id": 2, "amount": "9.125"}]
    actual = [{"customer_id": 1, "full_name": "Alice", "total": "12.346"},
              {"customer_id": 2, "full_name": "Bob", "total": "9.125"}]
    sql = "SELECT c.customer_id, c.first_name || ' ' || c.last_name AS full_name, SUM(i.total) AS total FROM customer c JOIN invoice i ON c.customer_id=i.customer_id GROUP BY c.customer_id"
    options = {"ordered": True, "numeric_columns": [0, 1], "round_numeric_columns": [1]}
    assert not compare_results(gold, actual, **options).matched
    result = compare_plan_results(gold, actual, actual_sql=sql, catalog=catalog, **options)
    assert result.matched and result.column_mapping == (0, 2)
    assert not compare_plan_results(gold, actual[::-1], actual_sql=sql, catalog=catalog, **options).matched


def test_plan_ex_does_not_discard_wrong_measure_or_fanout(catalog):
    sql = "SELECT customer_id, SUM(total) AS amount, COUNT(*) AS bogus FROM invoice GROUP BY customer_id"
    assert not compare_plan_results([[1, 20]], [[1, 20, 999]], actual_sql=sql, catalog=catalog).matched
    assert not compare_plan_results([[1, 20]], [[1, 20, "A"], [1, 20, "B"]],
                                    actual_sql="SELECT customer_id, total, billing_country FROM invoice", catalog=catalog).matched


def test_plan_ex_never_guesses_extra_columns_without_sql_proof(catalog):
    assert not compare_plan_results([[1]], [[1, "name"]], catalog=catalog).matched
    assert not compare_plan_results([], [], expected_columns=["id"], actual_columns=["id", "name"],
                                    actual_sql="SELECT customer_id, first_name FROM customer", catalog=catalog).matched
    assert not compare_plan_results([[None]], [[0]]).matched


@pytest.mark.parametrize("country_column,joined", [("invoice.billing_country", False), ("customer.country", True)])
@pytest.mark.parametrize("all_data", [False, True])
def test_country_share_local_numerator_keeps_all_invoice_denominator(catalog, country_column, joined, all_data):
    sql = f"SELECT SUM(CASE WHEN {country_column}='Brazil' THEN invoice.total ELSE 0 END)/NULLIF(SUM(invoice.total),0) AS ratio FROM invoice"
    if joined:
        sql += " JOIN customer ON invoice.customer_id=customer.customer_id"
    if not all_data:
        sql += " WHERE invoice.invoice_date >= '2023-01-01' AND invoice.invoice_date < '2024-01-01'"
    context = {"task_type": "ratio", "metric": "invoice_revenue", "region_scope": country_column,
               "denominator": "同期全部发票金额", "time_scope": {"all_data": True} if all_data else
               {"current": {"start": "2023-01-01", "end": "2024-01-01"}}}
    binding = [{"column": country_column, "operator": "=", "value": "Brazil"}]
    validate_value_bindings(sql, catalog, binding, ratio_context=context)
    with pytest.raises(SQLValidationError):
        validate_value_bindings(sql + (" WHERE " if all_data else " AND ") + f"{country_column}='Brazil'",
                                catalog, binding, ratio_context=context)
    with pytest.raises(SQLValidationError):
        validate_value_bindings(sql.replace("THEN invoice.total", "THEN 1"), catalog, binding, ratio_context=context)
    percent = sql.replace("SELECT SUM(", "SELECT 100.0 * SUM(")
    validate_value_bindings(percent, catalog, binding, ratio_context=context)
    assert percentage_formats(sql, ["ratio"], "ratio")["ratio"]["scale"] == 100
    assert percentage_formats(percent, ["ratio"], "ratio")["ratio"]["scale"] == 1
    assert display_percentage("0.07677004586099302662", {"scale": 100}) == "7.68%"


def test_percentage_metadata_preserves_accompanying_average_amount():
    sql = "SELECT SUM(total)/COUNT(*) AS average_amount, SUM(CASE WHEN billing_country='Brazil' THEN total ELSE 0 END)/NULLIF(SUM(total),0) AS share FROM invoice"
    formats = percentage_formats(sql, ["average_amount", "share"], "ratio")
    assert set(formats) == {"share"}


