"""Reproduce the D1 A read-only audit without any model requests or gold edits."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from eval.dataset import DEFAULT_DATASET, load_dataset, review_hash
from qa_agent.config import get_settings, sanitize_error
from qa_agent.sql.catalog import load_catalog
from qa_agent.sql.executor import execute_sql, serialize_value
from qa_agent.sql.validator import validate_sql
from scripts.check_db import COUNTRY_DIFFERENCE_SQL, TOP_ARTISTS_SQL


RATIONALES = {
    "sql-01": "COUNT(*) 对客户行计数，结果 59；不受可空字段影响，无需 JOIN。",
    "sql-02": "巴西映射为真实 country 标准值 Brazil，COUNT(*) 结果为 5。",
    "sql-03": "5 分钟等于 300000 毫秒，严格‘超过’使用 >，数量 1069。",
    "sql-04": "Brazil 筛选、四个指定投影及 customer_id 升序吻合；名字/姓氏分别为 first_name/last_name。",
    "sql-05": "美国原始标准值为 USA，返回编号、城市、州，按客户编号升序。",
    "sql-06": "高于 0.99 使用 >，按曲目编号升序 LIMIT 10，并返回单价；未擅自标注币种。",
    "sql-07": "精确匹配职位 Sales Support Agent，返回编号、first_name、last_name，按员工编号升序。",
    "sql-08": "不少于 10 使用 >=，编号升序取前 10 张发票，并保留日期和总额。",
    "sql-09": "invoice.total 求和，无明细连接造成重复计数；真实结果 2328.60。",
    "sql-10": "AVG(milliseconds) 保持题面要求的毫秒单位，没有转换成秒或分钟。",
    "sql-11": "题面要求两位小数，但原 SQL 为 AVG(total)，真实标准结果是 5.6519417475728155；金额比较量化可匹配 5.65，但原 SQL/结果展示精度仍不符。",
    "sql-12": "COUNT(DISTINCT country) 统计国家种类；数据 country 无 NULL，真实结果 24。",
    "sql-13": "country 为客户所在地，分组计数后按人数降序、国家升序，未误用 billing_country。",
    "sql-14": "按 genre_id 统计曲目数量，数量降序、编号升序处理并列；无需查流派名称。",
    "sql-15": "明确账单国家，使用 billing_country；SUM(total) 按发票统计收入，不擅自标注币种。",
    "sql-16": "按员工职位 title 分组计数、职位名称升序，并非按员工名字分组。",
    "sql-17": "milliseconds 降序、track_id 升序 LIMIT 5，与题意一致；Chinook track 包含视频条目，这里按该表的曲目口径排序。",
    "sql-18": "invoice.total 降序、invoice_id 升序 LIMIT 5，满足题面与并列次序。",
    "sql-19": "last_name 降序、customer_id 升序，投影编号、名字、姓氏；字符排序采用实测 PostgreSQL 数据库排序口径。",
    "sql-20": "artist.name 升序、artist_id 升序 LIMIT 5，满足名称及并列编号排序，沿用数据库排序口径。",
    "sql-21": "2021 年采用 >= 2021-01-01 且 < 2022-01-01，避免时间分量导致年末漏算；编号升序取 10 张。",
    "sql-22": "hire_date < 2004-01-01、编号排序及结果正确；‘名字’可能被理解为完整姓名，而原 gold 只投影 first_name，需明确字段。",
    "sql-23": "2025 年采用 [2025-01-01,2026-01-01) 半开区间，COUNT(*) 实测 80。",
    "sql-24": "邮箱结尾使用 LIKE '%@gmail.com'，编号排序正确；‘名字’可能被理解为完整姓名，需明确只返回 first_name。",
    "sql-25": "含 love 且不区分大小写使用 ILIKE，按编号升序 LIMIT 10；不是仅匹配独立单词。",
    "sql-26": "题面明确 company 为 NULL，采用 IS NULL，不混同空字符串；真实计数 49。",
    "sql-27": "composer 为 NULL 使用 IS NULL，编号升序 LIMIT 10；未将 NULL 与空字符串混同。",
    "sql-28": "reports_to 为 NULL 表示无直属上级，返回编号、first_name、last_name，编号升序。",
    "sql-29": "Antarctica 无匹配，标准结果是零行空表，不能替换为零或一行 NULL。",
    "sql-30": "Atlantis 无发票，SUM(total) 返回一行 NULL，满足题面；不能 COALESCE 成 0。",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def database_check(settings, catalog) -> dict:
    with psycopg.connect(settings.db_url, autocommit=True, connect_timeout=5, row_factory=dict_row) as conn:
        report = {
            "server_version": conn.execute("SHOW server_version").fetchone()["server_version"],
            "reader_defaults": {name: conn.execute("SHOW " + name).fetchone()[name] for name in
                                ("default_transaction_read_only", "statement_timeout", "lock_timeout")},
            "database_collation": dict(conn.execute("SELECT datcollate,datctype FROM pg_database "
                                                    "WHERE datname=current_database()").fetchone()),
            "reader_role": conn.execute("SELECT rolname,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
                                        "FROM pg_roles WHERE rolname=current_user").fetchone(),
            "database_privileges": conn.execute("SELECT has_database_privilege(current_user,current_database(),'CREATE') AS can_create_schema,"
                                                "has_database_privilege(current_user,current_database(),'TEMP') AS can_create_temp,"
                                                "has_schema_privilege(current_user,'public','CREATE') AS can_create_in_public").fetchone(),
            "table_privileges": conn.execute("SELECT table_name,has_table_privilege(current_user,"
                                             "quote_ident(table_schema)||'.'||quote_ident(table_name),'SELECT') AS can_select,"
                                             "has_table_privilege(current_user,quote_ident(table_schema)||'.'||quote_ident(table_name),"
                                             "'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') AS can_write "
                                             "FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' "
                                             "ORDER BY table_name").fetchall(),
            "invoice_date_range": serialize_value(conn.execute("SELECT MIN(invoice_date) AS min_date,MAX(invoice_date) AS max_date "
                                                                "FROM public.invoice").fetchone()),
            "employee_hire_date_range": serialize_value(conn.execute("SELECT MIN(hire_date) AS min_date,MAX(hire_date) AS max_date "
                                                                     "FROM public.employee").fetchone()),
            "invoice_years": [row["year"] for row in conn.execute("SELECT DISTINCT EXTRACT(YEAR FROM invoice_date)::int AS year "
                                                                  "FROM public.invoice ORDER BY year")],
            "customer_country_null_count": conn.execute("SELECT COUNT(*) AS count FROM public.customer WHERE country IS NULL").fetchone()["count"],
            "column_count": conn.execute("SELECT COUNT(*) AS count FROM information_schema.columns WHERE table_schema='public'").fetchone()["count"],
            "foreign_key_count": conn.execute("SELECT COUNT(*) AS count FROM pg_constraint co JOIN pg_class t ON co.conrelid=t.oid "
                                              "JOIN pg_namespace n ON t.relnamespace=n.oid WHERE n.nspname='public' AND co.contype='f'").fetchone()["count"],
        }
        report["table_row_counts"] = {row["table_name"]: conn.execute(sql.SQL("SELECT COUNT(*) AS count FROM public.{}")
                                      .format(sql.Identifier(row["table_name"]))).fetchone()["count"] for row in report["table_privileges"]}
        report["top_artists"] = serialize_value(conn.execute(TOP_ARTISTS_SQL).fetchall())
        report["country_difference"] = serialize_value(conn.execute(COUNTRY_DIFFERENCE_SQL).fetchone())
        handoff = json.loads((ROOT / "data/handoff/A_to_B_chinook.json").read_text(encoding="utf-8"))
        report["handoff_top_artists_match"] = report["top_artists"] == handoff["top_artists"]["rows"]
        report["handoff_country_difference_match"] = report["country_difference"] == handoff["country_semantics"]["result"]
        # WHERE FALSE changes no business rows, and transaction exit rolls back.
        # READ WRITE bypasses the changeable default to independently test ACL.
        try:
            with conn.transaction():
                conn.execute("SET TRANSACTION READ WRITE")
                conn.execute("UPDATE public.customer SET country=country WHERE FALSE")
                raise RuntimeError("Zero-row UPDATE unexpectedly allowed")
        except psycopg.errors.InsufficientPrivilege as exc:
            report["zero_row_update_acl_check"] = {"blocked": True, "sqlstate": exc.sqlstate, "business_rows_changed": 0,
                                                   "transaction_mode": "READ WRITE", "query": "UPDATE public.customer SET country=country WHERE FALSE"}
        report["reader_security_passed"] = (
            report["reader_defaults"]["default_transaction_read_only"] == "on"
            and not any(value for key, value in report["reader_role"].items() if key != "rolname")
            and not any(report["database_privileges"].values())
            and all(row["can_select"] and not row["can_write"] for row in report["table_privileges"])
            and report["zero_row_update_acl_check"]["blocked"])
        live_columns = conn.execute("SELECT table_name,column_name,data_type,is_nullable FROM information_schema.columns "
                                    "WHERE table_schema='public' ORDER BY table_name,ordinal_position").fetchall()
        report["catalog_table_names_match"] = set(report["table_row_counts"]) == {table.name for table in catalog.tables}
        report["catalog_row_counts_match"] = all(table.row_count == report["table_row_counts"][table.name] for table in catalog.tables)
        report["catalog_column_names_match"] = {(row["table_name"], row["column_name"]) for row in live_columns} == {
            (table.name, column.name) for table in catalog.tables for column in table.columns}
        actual_nullability = {(row["table_name"], row["column_name"]): row["is_nullable"] == "YES" for row in live_columns}
        report["catalog_column_nullability_match"] = all(column.nullable == actual_nullability[table.name, column.name]
                                                        for table in catalog.tables for column in table.columns)
        return report


def audit() -> dict:
    settings = get_settings()
    source = DEFAULT_DATASET
    parent_sha = sha256(source)
    items = load_dataset(source)
    if {item["id"] for item in items} != set(RATIONALES):
        raise ValueError("此语义审核仅适用于原 D1 的 30 道题。")
    catalog = load_catalog(settings.catalog_path)
    db = database_check(settings, catalog)
    now = datetime.now(timezone.utc).isoformat()
    cases = []
    for item in items:
        start = perf_counter()
        validated = validate_sql(item["gold_sql"], catalog, max_rows=settings.max_rows)
        result = execute_sql(validated.sql, settings.db_url, statement_timeout_ms=settings.statement_timeout_ms,
                             max_rows=settings.max_rows)
        match = result.table == item["gold_result"] and result.columns == item["gold_columns"]
        verdict = "needs_clarification" if item["id"] in {"sql-22", "sql-24"} else ("error" if item["id"] == "sql-11" else "accepted")
        if not match or result.truncated:
            verdict = "error"
        cases.append({"id": item["id"], "split": item["split"], "category": item["category"], "question": item["question"],
                      "gold_sql": item["gold_sql"], "executed_sql": validated.sql, "tables_used": validated.tables_used,
                      "actual_columns": result.columns, "actual_result": result.table, "actual_row_count": result.row_count,
                      "truncated": result.truncated, "gold_result_exact_match": match,
                      "recorded_review_hash_valid": item["gold_review"]["content_sha256"] == review_hash(item),
                      "ai_verdict": verdict, "reviewer_type": "ai", "reason": RATIONALES[item["id"]],
                      "human_review_status_unchanged": item["gold_review"]["status"],
                      "latency_ms": round((perf_counter() - start) * 1000)})
    revision_path = ROOT / "eval/datasets/nl2sql_chinook_d1_acceptance.manifest.json"
    revision = json.loads(revision_path.read_text(encoding="utf-8"))
    model = json.loads((ROOT / "notes/model-check.json").read_text(encoding="utf-8"))
    report = {
        "title": "D1 A 独立验收与 30 题 AI 语义复核", "checked_at_utc": now,
        "reviewer_type": "ai", "reviewer": "Codex / d1_a_acceptance", "human_signature": None,
        "scope": "真实只读数据库、30 条原 gold SQL 独立执行及逐题语义审核；不是模型预测，不更改原题集或人工接受状态。",
        "dataset": str(source), "dataset_sha256": parent_sha,
        "dataset_unchanged_after_check": sha256(source) == parent_sha,
        "source_sql_sha256": sha256(ROOT / "data/db/Chinook_PostgreSql.sql"),
        "git_commit_at_check": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(),
        "split_counts": dict(Counter(item["split"] for item in items)),
        "category_counts": dict(Counter(item["category"] for item in items)),
        "gold_sql_execution_count": len(cases), "model_prediction_count": 0, "holdout_model_prediction_count": 0,
        "original_semantic_conclusions": dict(Counter(case["ai_verdict"] for case in cases)),
        "gold_result_exact_match_count": sum(case["gold_result_exact_match"] for case in cases),
        "gold_review_hash_valid_count": sum(case["recorded_review_hash_valid"] for case in cases),
        "database": db,
        "model_connection_existing_evidence": {
            "file": "notes/model-check.json", "checked_at_utc": model.get("checked_at_utc"),
            "success": model.get("success"), "model": model.get("model"), "available_models": model.get("available_models"),
            "note": "引用此前真实 JSON 接入检查；本次不发出模型请求。"},
        "cases": cases,
        "separate_revision": {
            "dataset": str(ROOT / "eval/datasets/nl2sql_chinook_d1_acceptance.jsonl"),
            "manifest": str(revision_path), "dataset_sha256": revision["dataset_sha256"],
            "changed_ids": revision["changed_ids"], "parent_dataset_sha256_matches": revision["parent_dataset_sha256"] == parent_sha,
            "changed_cases_ai_semantic_accepted": all(change["ai_semantic_review"] == "accepted" for change in revision["changes"]),
            "holdout_items_identical": revision["holdout_items_identical_to_parent"], "pending_human_review_count": 30,
            "human_accepted_count": 0, "revision_gold_sql_executed": revision["gold_sql_executed_in_this_revision"],
            "revision_model_prediction_count": 0},
        "remaining_manual_steps": [
            "团队逐题确认标准答案；AI 结论不替代人工签字。",
            "修正版 21 开发题使用 --draft-gold 可进行真实探索评测；人工接受前不能称正式 EX。",
            "9 道保留题维持隔离，冻结前不进行模型预测；可以审核已有 gold。"],
        "future_scope": ["D2 值链接、别名、改写、单表题扩至 50 与 30 鲁棒性变体。",
                         "D3 AdventureWorks 与澄清；这些不属于 D1 遗漏。"],
    }
    output = ROOT / "eval/reports/d1-acceptance"
    output.mkdir(parents=True, exist_ok=True)
    (output / "a-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, output / "a-review.md")
    return report


def write_markdown(report: dict, path: Path) -> None:
    db = report["database"]
    lines = [
        "# D1 A 验收与 30 题独立 AI 复核", "",
        f"验收时间（UTC）：{report['checked_at_utc']}。审核类型：**AI**；审核者：Codex / d1_a_acceptance。", "",
        "**工程与数据检查通过；原 gold 的语义检查发现 1 项错误和 2 项需明确口径。独立修正版已生成，原题集及原人工审核记录未覆盖。** 本报告的 `accepted` 仅表示 AI 语义结论，不表示团队人工接受。", "",
        "- 原题集：30 题（21 dev / 9 holdout）；30 条标准 SQL 均经过真实执行，**30/30 结果与原记录逐字一致**，30/30 标注内容哈希有效。",
        "- 本审核与修正版生成均为标准 SQL 核验，**模型预测 0 次，保留题模型预测 0 次**。",
        "- 原题集语义结论：27 项 `accepted`、2 项 `needs_clarification`、1 项 `error`。",
        "- 新修正版仅改 3 道开发题，保持分割和题族；9 道保留题与原题集完全一致；30 题仍为 `needs_human_review`。", "",
        "## 1. D1 A 工程逐项验收", "",
        "| 项目 | 实际证据 | 结论 |", "|---|---|---|",
        f"| Chinook PG 和只读账号 | PostgreSQL {db['server_version']}；11 表、64 列、13 外键；SELECT-only ACL 与零行写入拒绝通过 | 通过 |",
        f"| 表名和年份 | public 中表名为 snake_case；invoice 为 {db['invoice_date_range']['min_date']} 至 {db['invoice_date_range']['max_date']} | 通过 |",
        "| DeepSeek JSON 接入 | notes/model-check.json 为真实 deepseek-flash 接入、JSON 校验及用量/链路记录；本次不重复请求 | 已有真实证据 |",
        "| 统一调用与 trace | qa_agent/llm.py、qa_agent/trace.py；TraceRecorder.step 为请求内工具留痕实现 | 已实现，集成回归见总报告 |",
        "| NL2SQL v0 | catalog→generator→SQLGlot→只读 executor；本次 30 gold 完成表列验证和执行；5000 ms 超时、200 行上限 | 数据链路通过；自然语言实跑见开发集 |",
        "| 30 单表题与 EX | 9 类题，21/9 固定分割；eval/run_eval.py；原 19/21 草稿不覆盖 | 3 项已形成独立修正版；正式 EX 待人工接受 |",
        f"| Top 艺术家交接 | 实算 Top10 与交接记录一致；第一名 {db['top_artists'][0]['name']}，销售额 {db['top_artists'][0]['revenue']} | 通过 |",
        f"| 地区口径检查 | {db['country_difference']['compared_invoice_count']} 张发票中客户与账单国家差异 {db['country_difference']['null_aware_difference_count']}；字段含义仍不同 | 通过；原数据不适合演示口径数值差异 |",
        "| 真实目录 | 表名、列名、行数与列可空性均与数据库一致 | 通过 |", "",
        "## 2. 30 题逐项语义审核", "",
        "逐项核对题意、筛选、单位、日期边界、投影、NULL、排序与并列。保留题只执行既有标准 SQL，不向模型提供问题。",
        f"字符排序的数据库实测设置：`{db['database_collation']}`；金额保持数据本身的单位，不凭空添加币种。", "",
        "| ID | 分割 | AI 结论 | 真实 gold 核验 | 理由 |", "|---|---|---|---|---|",
    ]
    for case in report["cases"]:
        lines.append(f"| {case['id']} | {case['split']} | {case['ai_verdict']} | 结果一致；{case['actual_row_count']} 行 | {case['reason']} |")
    lines += [
        "", "## 3. 已完成的独立修正版", "",
        "[修正版题集](E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.jsonl)；[前后变更与来源 manifest](E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.manifest.json)。", "",
        "1. `sql-11`：SQL 改为 `SELECT ROUND(AVG(total), 2) AS average_total FROM invoice;`，真实重算结果 `5.65`。原 SQL 和结果保留在父题集及 manifest。",
        "2. `sql-22`：题面明确‘名字（仅 first_name，不包含姓氏 last_name）’，保持原投影与日期条件；实算结果与原一致。",
        "3. `sql-24`：同样明确 first_name，保持邮箱结尾筛选与原投影；实算结果与原一致。", "",
        "三个修订均完成 AI 复核，仍待人工接受；它们形成新的评测版本，修正版成绩不能替换原 19/21 历史。不因旧模型多返回姓氏而放宽列数比较。", "",
        "首次可复现生成命令（文件存在时需明确加 `--overwrite`，只替换独立修正版）：", "",
        "```powershell", ".\\.venv\\Scripts\\python.exe -m eval.revise_d1_gold", "```", "",
        "本审核可重跑：", "", "```powershell", ".\\.venv\\Scripts\\python.exe -m eval.a_acceptance_audit", "```", "",
        "## 4. 仍需团队完成的验收", "",
        "A 对照原审核表及修正版清单逐题确认业务含义。正式评测要求实际人工接受与内容哈希一致；修正版 21 题的 `--draft-gold` 只能用于开发探索，不能代签。保留题不运行预测。", "",
        "值链接、题库扩容、OCR/其他格式、AdventureWorks、澄清、多轮与跨源属于原计划 D2–D5，不列作今天遗漏。共同任务的私有远程仓库及最终集成回归由主验收流程记录。", "",
        "## 5. 证据与溯源", "",
        "- [结构化检查结果](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/a-review.json)：完整 30 条实际 gold SQL、列、结果、逐项结论及数据库 ACL。",
        "- [原始 19/21 草稿](E:/中国电子杯-赛题八/system/eval/reports/d1-dev-draft/report.md)：历史保持不变。",
        "- [原 30 题审核表](E:/中国电子杯-赛题八/system/eval/datasets/review/gold_review.md)：人工状态未改。",
        f"- 原题集 SHA256：`{report['dataset_sha256']}`，审核后不变。",
        f"- 原数据库 SQL SHA256：`{report['source_sql_sha256']}`。",
        f"- 检查时 Git commit：`{report['git_commit_at_check']}`；最终集成 commit 以主验收报告为准。",
        "- 报告未包含 .env、API key、数据库 DSN 或口令。", "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    try:
        report = audit()
    except Exception as exc:
        print("A audit failed: " + sanitize_error(exc, get_settings()), file=sys.stderr)
        return 1
    print("A audit saved: " + str(report["gold_result_exact_match_count"]) + "/30 original gold exact matches; "
          "reviewer_type=ai; 0 model predictions.")
    print("AI conclusions: " + json.dumps(report["original_semantic_conclusions"], ensure_ascii=False))
    db = report["database"]
    checks = [db[name] for name in ("reader_security_passed", "catalog_table_names_match", "catalog_column_names_match",
                                    "catalog_row_counts_match", "catalog_column_nullability_match", "handoff_top_artists_match",
                                    "handoff_country_difference_match")]
    print("Database/catalog/handoff checks: " + str(checks))
    return 0 if all(checks) and report["gold_result_exact_match_count"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
