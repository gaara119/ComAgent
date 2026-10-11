"""Introspect real PostgreSQL names, keys and values, adding reviewed Chinese descriptions."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg
import yaml
from psycopg import sql
from psycopg.rows import dict_row

from qa_agent.config import get_settings, sanitize_error
from scripts.bootstrap_db import timestamp
from scripts.check_db import normalized

TABLE_DESCRIPTIONS = {
    "album": "专辑，每张专辑关联一位艺术家", "artist": "艺术家、乐队及组合的英文名称",
    "customer": "客户及其所在地、联系方式、销售支持员工", "employee": "员工及其职位、入职日期、上下级关系",
    "genre": "曲目音乐流派", "invoice": "销售发票，含客户、开票时间、账单地址及发票总额",
    "invoice_line": "发票销售明细，含实际成交单价及销售数量", "media_type": "曲目媒体格式",
    "playlist": "播放列表", "playlist_track": "播放列表与曲目的多对多关系", "track": "曲目、专辑、流派、媒体格式、时长和目录单价",
}

COMMON_DESCRIPTIONS = {
    "album_id": "专辑编号", "artist_id": "艺术家编号", "customer_id": "客户编号", "employee_id": "员工编号",
    "genre_id": "流派编号", "invoice_id": "发票编号", "invoice_line_id": "发票明细编号", "media_type_id": "媒体格式编号",
    "playlist_id": "播放列表编号", "track_id": "曲目编号", "first_name": "名字", "last_name": "姓氏",
    "address": "所在地街道地址", "city": "所在地城市", "state": "所在地州或省，可为空",
    "country": "所在地国家，使用原始英文标准值，例如 USA、Brazil", "postal_code": "所在地邮政编码，可为空",
    "phone": "联系电话，可为空", "fax": "传真号码，可为空", "email": "电子邮箱", "company": "客户公司名称，可为空",
    "support_rep_id": "负责该客户的销售支持员工编号，关联 employee.employee_id",
    "reports_to": "直接上级员工编号，关联 employee.employee_id；最高层员工为空",
    "birth_date": "员工出生日期", "hire_date": "员工入职日期", "invoice_date": "开票时间，不是客户创建时间",
    "billing_address": "发票账单街道地址", "billing_city": "发票账单城市", "billing_state": "发票账单州或省，可为空",
    "billing_country": "发票账单地址国家，与 customer.country 是不同字段，不可直接互换",
    "billing_postal_code": "发票账单邮政编码，可为空", "total": "发票总额；按发票统计收入使用该列，避免明细 JOIN 导致重复求和",
    "composer": "曲目作曲者，可为空", "milliseconds": "曲目时长，单位毫秒；秒 = 毫秒 / 1000.0",
    "bytes": "媒体文件大小，单位字节，可为空", "quantity": "本发票明细购买的曲目数量",
}

SPECIFIC_DESCRIPTIONS = {
    ("album", "title"): "专辑标题", ("employee", "title"): "员工职位，原始英文值",
    ("artist", "name"): "艺术家或乐队名称", ("genre", "name"): "流派英文名称",
    ("media_type", "name"): "媒体格式名称", ("playlist", "name"): "播放列表名称", ("track", "name"): "曲目名称",
    ("track", "unit_price"): "曲目目录单价，不是整张发票总额；币种未在本数据源声明",
    ("invoice_line", "unit_price"): "本发票明细实际成交单价；销售额 = 单价 × quantity",
}


def foreign_keys(conn, schema: str, table: str) -> list:
    rows = conn.execute("""SELECT con.conname, src.attname AS source_column,
        refns.nspname AS target_schema, ref.relname AS target_table,
        dst.attname AS target_column, cols.position
      FROM pg_constraint con
      JOIN pg_class obj ON obj.oid=con.conrelid
      JOIN pg_namespace ns ON ns.oid=obj.relnamespace
      JOIN pg_class ref ON ref.oid=con.confrelid
      JOIN pg_namespace refns ON refns.oid=ref.relnamespace
      CROSS JOIN LATERAL unnest(con.conkey, con.confkey) WITH ORDINALITY AS cols(source_num,target_num,position)
      JOIN pg_attribute src ON src.attrelid=obj.oid AND src.attnum=cols.source_num
      JOIN pg_attribute dst ON dst.attrelid=ref.oid AND dst.attnum=cols.target_num
      WHERE con.contype='f' AND ns.nspname=%s AND obj.relname=%s
      ORDER BY con.conname, cols.position""", (schema, table)).fetchall()
    groups = {}
    for row in rows:
        key = groups.setdefault(row["conname"], {"columns": [], "references": {"schema": row["target_schema"],
                                                                             "table": row["target_table"], "columns": []}})
        key["columns"].append(row["source_column"])
        key["references"]["columns"].append(row["target_column"])
    return list(groups.values())


def main() -> None:
    settings = get_settings()
    with psycopg.connect(settings.db_url, connect_timeout=5, row_factory=dict_row) as conn:
        catalog = {"database": conn.execute("SELECT current_database() AS name").fetchone()["name"],
                   "dialect": "postgres", "version": "Chinook 1.4.5", "generated_at": timestamp(),
                   "source_manifest": "data/db/source_manifest.json", "tables": []}
        tables = conn.execute("SELECT table_schema, table_name FROM information_schema.tables "
                              "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name").fetchall()
        for row in tables:
            schema, table = row["table_schema"], row["table_name"]
            info = {"schema": schema, "name": table, "description": TABLE_DESCRIPTIONS.get(table, table),
                    "row_count": conn.execute(sql.SQL("SELECT COUNT(*) AS count FROM {}.{}")
                                              .format(sql.Identifier(schema), sql.Identifier(table))).fetchone()["count"],
                    "columns": [], "primary_key": [], "foreign_keys": foreign_keys(conn, schema, table)}
            columns = conn.execute("SELECT column_name, data_type, udt_name, is_nullable, character_maximum_length, numeric_precision, numeric_scale "
                                   "FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position", (schema, table)).fetchall()
            for column in columns:
                name = column["column_name"]
                data_type = column["data_type"]
                if column["character_maximum_length"]:
                    data_type += f"({column['character_maximum_length']})"
                if data_type == "numeric":
                    data_type += f"({column['numeric_precision']},{column['numeric_scale']})"
                limit = 30 if name in {"country", "billing_country"} else 3
                values = conn.execute(sql.SQL("SELECT DISTINCT {} AS value FROM {}.{} WHERE {} IS NOT NULL ORDER BY {} LIMIT %s")
                                      .format(sql.Identifier(name), sql.Identifier(schema), sql.Identifier(table),
                                              sql.Identifier(name), sql.Identifier(name)), (limit,)).fetchall()
                description = SPECIFIC_DESCRIPTIONS.get((table, name), COMMON_DESCRIPTIONS.get(name, name))
                info["columns"].append({"name": name, "type": data_type, "nullable": column["is_nullable"] == "YES",
                                        "description": description, "sample_values": normalized([value["value"] for value in values])})
            # information_schema.table_constraints excludes a SELECT-only role's
            # tables. pg_constraint exposes real keys without granting write access.
            info["primary_key"] = [item["column_name"] for item in conn.execute("""SELECT attr.attname AS column_name
                FROM pg_constraint con
                JOIN pg_class obj ON obj.oid=con.conrelid
                JOIN pg_namespace ns ON ns.oid=obj.relnamespace
                CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS cols(attnum,position)
                JOIN pg_attribute attr ON attr.attrelid=obj.oid AND attr.attnum=cols.attnum
                WHERE con.contype='p' AND ns.nspname=%s AND obj.relname=%s
                ORDER BY cols.position""", (schema, table))]
            catalog["tables"].append(info)
        catalog["table_count"] = len(tables)
        catalog["invoice_date_range"] = normalized(conn.execute("SELECT MIN(invoice_date) AS min_date, MAX(invoice_date) AS max_date FROM public.invoice").fetchone())
        catalog["invoice_years"] = [item["year"] for item in conn.execute("SELECT DISTINCT EXTRACT(YEAR FROM invoice_date)::int AS year FROM public.invoice ORDER BY year")]
    settings.catalog_path.parent.mkdir(parents=True, exist_ok=True)
    settings.catalog_path.write_text(yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    print(f"Catalog exported: {settings.catalog_path.name}, {len(tables)} tables, {sum(len(t['columns']) for t in catalog['tables'])} columns; names and keys from the live database.")


if __name__ == "__main__":
    try:
        if "--db-id" in sys.argv:
            position = sys.argv.index("--db-id")
            db_id = sys.argv[position + 1] if len(sys.argv) > position + 1 else ""
            if db_id not in {"aw", "adventureworks"}:
                raise ValueError("--db-id currently accepts aw / adventureworks")
            from scripts.build_aw_catalog import main as build_aw
            build_aw(sys.argv[1:position] + sys.argv[position+2:])
        else:
            main()
    except Exception as exc:
        print(f"Catalog generation failed: {sanitize_error(exc, get_settings())}", file=sys.stderr)
        sys.exit(1)
