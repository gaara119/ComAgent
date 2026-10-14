"""Create explicitly marked Chinook stress schemas without touching public.

New invoice IDs and shifted dates accompany replicated invoice_line rows.
All eleven business tables and actual FK constraints are copied; invoice
totals are recomputed from the stress lines. No source gold is copied as fact.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml
from qa_agent.config import get_settings, sanitize_error
from scripts.d4_bench_utils import write_json


def quote(value):
    return '"' + value.replace('"', '""') + '"'


def checksum_sql(catalog):
    entries = []
    for table in catalog["tables"]:
        name = table["name"]
        order = ",".join(quote(column) for column in table["primary_key"])
        entries.append(f"'{name}', (SELECT json_build_object('count',COUNT(*),'content_md5',"
            f"md5(COALESCE(string_agg(row_to_json(t)::text, ',' ORDER BY {order}),''))) FROM public.{quote(name)} AS t)")
    return "SELECT json_build_object(" + ",".join(entries) + ");\n"


def build_sql(catalog, schema, target):
    if not re.fullmatch(r"d4_stress_(?:10000|100000)(?:_[a-z0-9]+)?", schema):
        raise ValueError("Stress writes are restricted to explicitly marked d4_stress schemas")
    if target not in {10000, 100000}:
        raise ValueError("Only the planned 10,000 and 100,000 line scales are accepted")
    statements = ["BEGIN;", "SET LOCAL statement_timeout = '5000ms';", "SET LOCAL lock_timeout = '2000ms';",
                  f"CREATE SCHEMA {quote(schema)};", f"COMMENT ON SCHEMA {quote(schema)} IS 'D4 压测副本；合成扩容，非原业务数据';"]
    for table in catalog["tables"]:
        name = table["name"]
        statements.append(f"CREATE TABLE {quote(schema)}.{quote(name)} (LIKE public.{quote(name)} INCLUDING ALL);")
        statements.append(f"COMMENT ON TABLE {quote(schema)}.{quote(name)} IS 'D4 压测副本；仅用于数据规模效率实验';")
        if name not in {"invoice", "invoice_line"}:
            statements.append(f"INSERT INTO {quote(schema)}.{quote(name)} SELECT * FROM public.{quote(name)};")
    invoice = next(table for table in catalog["tables"] if table["name"] == "invoice")
    names = [column["name"] for column in invoice["columns"]]
    expressions = []
    for name in names:
        if name == "invoice_id":
            expressions.append("i.invoice_id + b.batch * (SELECT MAX(invoice_id) FROM public.invoice)")
        elif name == "invoice_date":
            expressions.append("i.invoice_date + b.batch * INTERVAL '5 years'")
        else:
            expressions.append("i." + quote(name))
    statements.append(f"INSERT INTO {quote(schema)}.invoice ({','.join(map(quote,names))}) "
        f"SELECT {','.join(expressions)} FROM public.invoice AS i CROSS JOIN generate_series(0,"
        f"(({target}-1)/(SELECT COUNT(*) FROM public.invoice_line))::integer) AS b(batch);")
    line = next(table for table in catalog["tables"] if table["name"] == "invoice_line")
    names = [column["name"] for column in line["columns"]]
    expressions = []
    for name in names:
        if name == "invoice_line_id":
            expressions.append("s.ordinal + b.batch * (SELECT COUNT(*) FROM public.invoice_line)")
        elif name == "invoice_id":
            expressions.append("s.invoice_id + b.batch * (SELECT MAX(invoice_id) FROM public.invoice)")
        else:
            expressions.append("s." + quote(name))
    statements.append(f"INSERT INTO {quote(schema)}.invoice_line ({','.join(map(quote,names))}) "
        f"SELECT {','.join(expressions)} FROM (SELECT l.*,ROW_NUMBER() OVER(ORDER BY invoice_line_id) AS ordinal "
        f"FROM public.invoice_line AS l) AS s CROSS JOIN generate_series(0,"
        f"(({target}-1)/(SELECT COUNT(*) FROM public.invoice_line))::integer) AS b(batch) "
        f"WHERE s.ordinal + b.batch * (SELECT COUNT(*) FROM public.invoice_line) <= {target};")
    statements.append(f"UPDATE {quote(schema)}.invoice AS i SET total = COALESCE((SELECT SUM(l.unit_price*l.quantity) "
                      f"FROM {quote(schema)}.invoice_line AS l WHERE l.invoice_id=i.invoice_id),0);")
    for table in catalog["tables"]:
        for number, fk in enumerate(table["foreign_keys"]):
            reference = fk["references"]
            statements.append(f"ALTER TABLE {quote(schema)}.{quote(table['name'])} ADD CONSTRAINT "
                f"{quote('d4_fk_'+table['name']+'_'+str(number))} FOREIGN KEY ({','.join(map(quote,fk['columns']))}) "
                f"REFERENCES {quote(schema)}.{quote(reference['table'])} ({','.join(map(quote,reference['columns']))});")
    statements.extend([f"GRANT USAGE ON SCHEMA {quote(schema)} TO qa_reader;",
                       f"GRANT SELECT ON ALL TABLES IN SCHEMA {quote(schema)} TO qa_reader;", "COMMIT;"])
    for table in catalog["tables"]:
        statements.append(f"ANALYZE {quote(schema)}.{quote(table['name'])};")
    return "\n".join(statements) + "\n"


def run_psql(container, user, database, sql, output):
    command = ["docker", "exec", "--interactive", container, "psql", "--username", user,
               "--dbname", database, "--no-psqlrc", "--set", "ON_ERROR_STOP=1", "--tuples-only", "--no-align"]
    process = subprocess.run(command, input=sql, capture_output=True, text=True, encoding="utf-8")
    output.with_suffix(".stdout.txt").write_text(process.stdout, encoding="utf-8")
    output.with_suffix(".stderr.txt").write_text(process.stderr, encoding="utf-8")
    write_json(output.with_suffix(".command.json"), {"command": command, "exit_code": process.returncode,
                                                   "sql": output.name + ".sql"})
    output.with_suffix(".sql").write_text(sql, encoding="utf-8")
    if process.returncode:
        raise RuntimeError("Stress setup/read-only verification failed; see saved psql output")
    return [json.loads(line) for line in process.stdout.splitlines() if line.strip().startswith("{")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", required=True)
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--database", default="chinook")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--schema-suffix", default="")
    args = parser.parse_args()
    args.output = args.output.resolve()
    if args.output.exists():
        raise ValueError("Choose a new output directory; existing schemas and evidence are never overwritten")
    if args.schema_suffix and not re.fullmatch("[a-z0-9]+", args.schema_suffix):
        raise ValueError("Suffix must be lowercase alphanumeric")
    args.output.mkdir(parents=True)
    original = yaml.safe_load((ROOT / "data/catalog/chinook.yaml").read_text(encoding="utf-8"))
    before = run_psql(args.container, args.user, args.database, checksum_sql(original), args.output / "public-before")[0]
    write_json(args.output / "public-before.json", before)
    scales = []
    for target in (10000, 100000):
        schema = f"d4_stress_{target}" + ("_"+args.schema_suffix if args.schema_suffix else "")
        run_psql(args.container, args.user, args.database, build_sql(original, schema, target), args.output / f"create-{target}")
        stats = f"SELECT json_build_object('schema','{schema}','line_count',(SELECT COUNT(*) FROM {quote(schema)}.invoice_line)," \
            f"'invoice_count',(SELECT COUNT(*) FROM {quote(schema)}.invoice),'orphan_lines',(SELECT COUNT(*) FROM {quote(schema)}.invoice_line l " \
            f"LEFT JOIN {quote(schema)}.invoice i USING(invoice_id) WHERE i.invoice_id IS NULL),'min_date',(SELECT MIN(invoice_date) FROM {quote(schema)}.invoice)," \
            f"'max_date',(SELECT MAX(invoice_date) FROM {quote(schema)}.invoice),'years',(SELECT json_agg(y ORDER BY y) FROM " \
            f"(SELECT DISTINCT EXTRACT(YEAR FROM invoice_date)::integer y FROM {quote(schema)}.invoice)t),'invoice_total',(SELECT SUM(total) FROM {quote(schema)}.invoice)," \
            f"'line_total',(SELECT SUM(unit_price*quantity) FROM {quote(schema)}.invoice_line),'readonly_role'," \
            f"(SELECT rolconfig FROM pg_roles WHERE rolname='qa_reader'),'table_counts',json_build_object(" + ",".join(
                f"'{table['name']}',(SELECT COUNT(*) FROM {quote(schema)}.{quote(table['name'])})" for table in original["tables"]) + "));"
        actual = run_psql(args.container, args.user, args.database, stats, args.output / f"verify-{target}")[0]
        if actual["line_count"] != target or actual["orphan_lines"] or actual["invoice_total"] != actual["line_total"]:
            raise RuntimeError("Stress copy failed count/FK/money consistency checks")
        derived = copy.deepcopy(original)
        derived.update({"database": "chinook", "version": f"D4 STRESS COPY {target} lines; derived from Chinook 1.4.5",
            "stress_copy": True, "stress_schema": schema, "invoice_date_range": {"min_date":actual["min_date"],"max_date":actual["max_date"]},
            "invoice_years":actual["years"], "derivation": "deterministic line duplication, new invoice/line IDs, +5 years per batch, totals recomputed"})
        for table in derived["tables"]:
            table["schema"] = schema
            table["description"] = "【压测副本】" + table["description"]
            table["row_count"] = actual["table_counts"][table["name"]]
            for fk in table["foreign_keys"]:
                fk["references"]["schema"] = schema
        catalog_path = args.output / f"chinook-stress-{target}.yaml"
        catalog_path.write_text(yaml.safe_dump(derived, allow_unicode=True, sort_keys=False), encoding="utf-8")
        actual["catalog"] = catalog_path.relative_to(ROOT).as_posix()
        scales.append(actual)
    after = run_psql(args.container, args.user, args.database, checksum_sql(original), args.output / "public-after")[0]
    write_json(args.output / "public-after.json", after)
    if before != after:
        raise RuntimeError("Original public checksum changed; stop benchmarking and investigate")
    write_json(args.output / "manifest.json", {"status":"ACTUALLY_CREATED_AND_VERIFIED", "stress_copy":True,
        "original_public_unchanged":True,"original_public_fingerprints":before,"scales":scales,
        "all_original_foreign_keys_recreated":True,"gold_policy":"Every question's standard SQL is executed separately on each copy"})
    print(json.dumps({"original_public_unchanged":True,"scales":scales}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(sanitize_error(exc, get_settings()), file=sys.stderr)
        raise SystemExit(1)
