"""Actual response limits, without claiming a complete business population."""
from hashlib import sha256
import sqlglot


def query_output_scope(original_sql, *, program_added_limit, row_count, cap, truncated):
    try:
        limit=sqlglot.parse_one(original_sql,read='postgres').args.get('limit')
        limit=limit.sql(dialect='postgres') if limit is not None else None
    except (ValueError,TypeError,sqlglot.errors.ParseError):
        limit='not_verified'
    return {
        'original_limit':limit,'original_sql_sha256':sha256(original_sql.encode()).hexdigest(),
        'program_added_limit':bool(program_added_limit),
        'row_count':row_count,'response_cap':cap,'cursor_truncated':bool(truncated),
        'possibly_incomplete_enumeration':bool(truncated or program_added_limit and row_count>=cap),
        'complete_business_population_proved':False,
        'boundary':'Returned row_count is not total population; an explicit LIMIT describes only the executed subset.'}
