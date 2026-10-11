"""A country-source counterexample must differ even with the same summed total."""
from pathlib import Path
import sqlite3

import pytest

from qa_agent.clarify.sql_guard import validate_confirmed_country_output
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.validator import SQLValidationError

CATALOG=load_catalog(Path(__file__).resolve().parents[1]/'data/catalog/chinook.yaml')
TARGET='customer.country'


@pytest.mark.parametrize('sql',[
    'SELECT c.country, SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id GROUP BY c.country',
    'SELECT c.country AS billing_country, SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id GROUP BY c.country HAVING SUM(i.total)>0',
    'SELECT c.country,e.country, SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id JOIN employee e ON e.employee_id=c.support_rep_id WHERE e.country=\'USA\' GROUP BY c.country,e.country',
])
def test_real_customer_source_and_independent_employee_are_preserved(sql):
    validate_confirmed_country_output(sql,CATALOG,TARGET)


@pytest.mark.parametrize('sql',[
    'SELECT i.billing_country,SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id GROUP BY i.billing_country',
    'SELECT SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id GROUP BY i.billing_country',
    'SELECT c.country,SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id GROUP BY c.country HAVING MAX(i.billing_country)=\'Canada\'',
    'SELECT x.country,SUM(x.total) FROM (SELECT i.billing_country AS country,i.total FROM invoice i JOIN customer c ON c.customer_id=i.customer_id) x GROUP BY x.country',
])
def test_old_country_select_group_having_or_derived_source_is_rejected(sql):
    with pytest.raises(SQLValidationError):validate_confirmed_country_output(sql,CATALOG,TARGET)


def test_reverse_migration_rejects_customer_source_but_accepts_actual_billing_source():
    with pytest.raises(SQLValidationError):validate_confirmed_country_output(
        'SELECT c.country,SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id GROUP BY c.country',CATALOG,'invoice.billing_country')
    validate_confirmed_country_output('SELECT billing_country AS country,SUM(total) FROM invoice GROUP BY billing_country',CATALOG,'invoice.billing_country')


def test_different_customer_and_billing_country_exposes_the_business_error():
    # Isolated synthetic data: never modify the project database or gold labels.
    with sqlite3.connect(':memory:') as connection:
        connection.execute('CREATE TABLE customer (customer_id INTEGER,country TEXT)')
        connection.execute('CREATE TABLE invoice (customer_id INTEGER,billing_country TEXT,total INTEGER)')
        connection.execute('INSERT INTO customer VALUES (1,\'Canada\')')
        connection.executemany('INSERT INTO invoice VALUES (?,?,?)',[(1,'Canada',10),(1,'USA',20)])
        wrong="SELECT i.billing_country,SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id WHERE c.country='Canada' GROUP BY i.billing_country"
        correct="SELECT c.country,SUM(i.total) FROM invoice i JOIN customer c ON c.customer_id=i.customer_id WHERE c.country='Canada' GROUP BY c.country"
        wrong_rows=connection.execute(wrong).fetchall()
        correct_rows=connection.execute(correct).fetchall()
    assert sum(row[1] for row in wrong_rows)==sum(row[1] for row in correct_rows)==30
    assert wrong_rows==[('Canada',10),('USA',20)] and correct_rows==[('Canada',30)]
    with pytest.raises(SQLValidationError):validate_confirmed_country_output(wrong,CATALOG,TARGET)
    validate_confirmed_country_output(correct,CATALOG,TARGET)
