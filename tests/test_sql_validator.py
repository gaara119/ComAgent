"""Safety boundaries and SQL result semantics, independent of live credentials."""

import pytest
import sqlglot
from sqlglot import exp

from qa_agent.sql.catalog import Catalog, CatalogColumn, CatalogError, CatalogTable, load_catalog
from qa_agent.sql.validator import SQLValidationError, validate_sql


@pytest.fixture
def catalog():
    return Catalog(
        "chinook", (
            CatalogTable("public", "customer", (
                CatalogColumn("customer_id", "integer"),
                CatalogColumn("country", "text"),
                CatalogColumn("first_name", "text"),
            )),
            CatalogTable("public", "invoice", (
                CatalogColumn("invoice_id", "integer"),
                CatalogColumn("customer_id", "integer"),
                CatalogColumn("total", "numeric"),
                CatalogColumn("invoice_date", "timestamp without time zone"),
            )),
        ),
    )


@pytest.mark.parametrize("sql", [
    "DELETE FROM customer WHERE false",
    "SELECT country FROM customer; SELECT 1",
    "SELECT country INTO copied_customers FROM customer",
    "WITH changed AS (DELETE FROM customer WHERE false RETURNING *) SELECT * FROM changed",
    "WITH changed AS (UPDATE customer SET country='X' WHERE false RETURNING *) SELECT * FROM changed",
    "WITH changed AS (INSERT INTO customer(customer_id) VALUES(9999) RETURNING *) SELECT * FROM changed",
    "SELECT country FROM customer FOR UPDATE",
    "SELECT pg_sleep(10)",
    "SELECT pg_catalog.count(*) FROM customer",
    "WITH unused AS (SELECT pg_read_file('/etc/passwd')) SELECT count(*) FROM customer",
    "SELECT * FROM information_schema.tables",
    "SELECT * FROM other_database.public.customer",
    "SELECT * FROM generate_series(1,1000000)",
    "SELECT country::regclass FROM customer",
    "SELECT unknown_column FROM customer",
    "SELECT c.unknown_column FROM customer AS c",
    "SELECT 'Brazil' FROM nonexistent",
    "WITH s AS (SELECT country FROM customer) SELECT s.unknown_column FROM s",
    "SELECT customer_id FROM customer c JOIN invoice i ON c.customer_id=i.customer_id",
    "SELECT c.country FROM customer c WHERE EXISTS(SELECT 1 FROM invoice i WHERE i.bogus=c.customer_id)",
    "SELECT c.country FROM customer c JOIN invoice c ON true",
    "WITH RECURSIVE s AS (SELECT 1 UNION ALL SELECT 1 FROM s) SELECT * FROM s",
    "SELECT FROM",
    "-- comment only",
])
def test_rejects_unsafe_and_unresolved_queries(catalog, sql):
    with pytest.raises(SQLValidationError):
        validate_sql(sql, catalog)


def test_scopes_allow_real_aliases_cte_and_correlated_columns(catalog):
    result = validate_sql(
        "WITH countries AS (SELECT c.country FROM customer AS c WHERE EXISTS "
        "(SELECT 1 FROM invoice i WHERE i.customer_id=c.customer_id)) "
        "SELECT x.country FROM countries AS x ORDER BY x.country LIMIT 7", catalog,
    )
    assert result.tables_used == ["customer", "invoice"]
    assert not result.default_limit_added
    assert sqlglot.parse_one(result.sql, read="postgres").args["limit"].expression.this == "7"


def test_top_n_and_stable_order_are_preserved(catalog):
    result = validate_sql("SELECT invoice_id,total FROM invoice ORDER BY total DESC,invoice_id LIMIT 12", catalog)
    tree = sqlglot.parse_one(result.sql, read="postgres")
    assert tree.args["limit"].expression.this == "12"
    assert "total DESC, invoice_id" in result.sql
    assert not result.default_limit_added


def test_default_limit_is_only_on_outer_query(catalog):
    result = validate_sql(
        "SELECT country FROM (SELECT country FROM customer WHERE country IS NOT NULL) c", catalog,
    )
    tree = sqlglot.parse_one(result.sql, read="postgres")
    assert tree.args["limit"].expression.this == "200"
    inner_select = tree.find(exp.Subquery).this
    assert inner_select.args.get("limit") is None
    assert "country IS NULL" in result.sql or "country IS NOT NULL" in result.sql


@pytest.mark.parametrize("sql", [
    "SELECT COUNT(*) AS customer_count FROM customer WHERE country='Antarctica'",
    "SELECT SUM(total),AVG(total),MIN(total),MAX(total) FROM invoice",
    "SELECT ROUND(AVG(total),2) FROM invoice",
])
def test_scalar_aggregate_input_is_never_capped(catalog, sql):
    result = validate_sql(sql, catalog)
    assert not result.default_limit_added
    assert not list(sqlglot.parse_one(result.sql, read="postgres").find_all(exp.Limit))


@pytest.mark.parametrize("sql", [
    "SELECT country,COUNT(*) AS n FROM customer GROUP BY country ORDER BY n DESC",
    "SELECT SUM(total) OVER() FROM invoice",
    "SELECT (SELECT COUNT(*) FROM invoice) FROM customer",
])
def test_group_and_window_and_subquery_result_lists_receive_outer_limit(catalog, sql):
    result = validate_sql(sql, catalog)
    assert result.default_limit_added
    assert sqlglot.parse_one(result.sql, read="postgres").args["limit"].expression.this == "200"


def test_postgres_quoted_case_is_not_guessed(catalog):
    with pytest.raises(SQLValidationError):
        validate_sql('SELECT "Country" FROM customer', catalog)
    actual = Catalog("case_sensitive", (
        CatalogTable("public", "Customer", (CatalogColumn("Country", "text"),)),
    ))
    assert validate_sql('SELECT "Country" FROM "Customer"', actual).tables_used == ["Customer"]
    with pytest.raises(SQLValidationError):
        validate_sql("SELECT Country FROM Customer", actual)


def test_date_null_and_like_functions_are_allowed(catalog):
    for sql in (
        "SELECT EXTRACT(YEAR FROM invoice_date),SUM(total) FROM invoice GROUP BY 1",
        "SELECT DATE_TRUNC('year',invoice_date) FROM invoice",
        "SELECT COALESCE(country,'Unknown') FROM customer WHERE country ILIKE 'b%'",
        "SELECT CASE WHEN total IS NULL THEN 0 ELSE total END FROM invoice",
        "SELECT SUM(total) FROM invoice WHERE invoice_date >= DATE '2021-01-01' AND invoice_date < DATE '2022-01-01'",
        "SELECT country FROM customer WHERE country='Brazil' OR country='USA'",
    ):
        validate_sql(sql, catalog)


def test_catalog_loads_actual_export_fields(tmp_path):
    path = tmp_path / "catalog.yaml"
    path.write_text(
        "database: chinook\ndialect: postgres\nversion: v1.4.5\ntables:\n"
        "- schema: public\n  name: invoice\n  primary_key: [invoice_id]\n  columns:\n"
        "  - {name: invoice_id, type: integer, nullable: false}\n"
        "  - {name: total, type: numeric, description: 发票总额, sample_values: ['0.99']}\n",
        encoding="utf-8",
    )
    loaded = load_catalog(path)
    assert loaded.get_table("invoice").column_names == {"invoice_id", "total"}
    assert "发票总额" in loaded.prompt_schema()
    assert '"total" numeric' in loaded.prompt_schema()


def test_missing_catalog_is_actionable(tmp_path):
    with pytest.raises(CatalogError, match="build_catalog"):
        load_catalog(tmp_path / "not-created.yaml")
