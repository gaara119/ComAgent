"""Build D2 read-only value indexes, or draft aliases for explicit human review.

No dataset/gold inputs are accepted. SQL identifiers come only from the catalog.
The two phases allow inspection before the expensive, shared BGE batch build.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import psycopg
from psycopg import sql
from pydantic import BaseModel, ConfigDict, Field

from qa_agent.config import get_settings, sanitize_error
from qa_agent.llm import JsonLLM
from qa_agent.nlu.value_index import ValueIndex, ValueRecord, normalize, pinyin_key, record_id
from qa_agent.rag.embeddings import get_embedder
from qa_agent.sql.catalog import Catalog, load_catalog
from qa_agent.trace import TraceRecorder

ALIAS_FIELDS = ["standard_value", "column", "alias", "source", "review_status", "reviewer", "alias_id"]


def read_values(catalog: Catalog, db_url: str) -> tuple[list[ValueRecord], list[dict]]:
    values, audit = [], []
    with psycopg.connect(db_url, connect_timeout=5) as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        connection.execute("SET LOCAL statement_timeout = '5000ms'")
        for table in catalog.tables:
            for column in table.columns:
                if not any(kind in column.data_type.lower() for kind in ("char", "text", "citext")):
                    continue
                name = f"{table.name}.{column.name}" if table.schema == "public" else f"{table.schema}.{table.name}.{column.name}"
                query = sql.SQL("SELECT DISTINCT {col} FROM {schema}.{table} WHERE {col} IS NOT NULL ORDER BY {col} LIMIT 5000").format(
                    col=sql.Identifier(column.name), schema=sql.Identifier(table.schema), table=sql.Identifier(table.name))
                started = perf_counter()
                try:
                    with connection.transaction():
                        rows = connection.execute(query).fetchall()
                    if len(rows) == 5000:
                        audit.append({"column": name, "status": "skipped", "reason": "distinct_non_null_at_least_5000", "fetched_count": 5000})
                        continue
                    for row in rows:
                        value = str(row[0])
                        values.append(ValueRecord(record_id(name, value), name, value, value, "catalog:" + name))
                    audit.append({"column": name, "status": "indexed", "distinct_non_null_count": len(rows),
                                  "latency_ms": round((perf_counter() - started) * 1000)})
                except Exception as exc:
                    audit.append({"column": name, "status": "failed", "error_type": type(exc).__name__})
    return values, audit


def load_reviewed_aliases(path: Path, values: list[ValueRecord]) -> tuple[list[ValueRecord], dict]:
    standard = {(item.column, item.standard_value): item for item in values}
    accepted, excluded, invalid = [], 0, []
    if not path.is_file():
        return [], {"path": str(path), "accepted_count": 0, "excluded_count": 0, "invalid": []}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    seen = set()
    for number, item in enumerate(rows, 2):
        if item.get("review_status") not in {"approved", "approved_candidate"} or not item.get("reviewer", "").strip():
            excluded += 1
            continue
        key = (item.get("column", ""), item.get("standard_value", ""))
        if key not in standard or not item.get("alias", "").strip():
            invalid.append({"row": number, "reason": "unknown_canonical_or_empty_alias"})
            continue
        identity = (*key, normalize(item["alias"]))
        if identity in seen:
            continue
        seen.add(identity)
        value = standard[key]
        accepted.append(ValueRecord(value.candidate_id, value.column, value.standard_value, item["alias"],
                                    item.get("source", "") or f"alias-row:{number}",
                                    "conditional_alias" if item["review_status"] == "approved_candidate" else "alias",
                                    item.get("alias_id") or f"alias-row:{number}"))
    return accepted, {"accepted_count": len(accepted),
                      "direct_count": sum(item.kind == "alias" for item in accepted),
                      "candidate_only_count": sum(item.kind == "conditional_alias" for item in accepted),
                      "excluded_count": excluded, "invalid": invalid,
                      "input_sha256": sha256(path.read_bytes()).hexdigest()}


class AliasDraftRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    standard_value: str
    column: str
    aliases: list[str] = Field(max_length=8)


class AliasDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rows: list[AliasDraftRow]


def draft_aliases(values: list[ValueRecord], output: Path, audit_path: Path,
                  only_standards: list[str] | None = None) -> dict:
    if output.is_file():
        raise ValueError("别名表已存在，拒绝覆盖审核记录；用不同的 --aliases 路径起草新版。")
    selected = [value for value in values if
                (value.column in {"customer.country", "invoice.billing_country"} and value.standard_value in
                 {"Brazil", "USA", "Canada", "Germany", "France", "United Kingdom", "China", "India", "Japan", "Australia"}) or
                (value.column == "genre.name" and value.standard_value in {"Rock", "Rock And Roll", "Jazz", "Metal", "Pop", "Classical"}) or
                value.column == "media_type.name" or
                (value.column == "artist.name" and value.standard_value in {"Iron Maiden", "U2", "Metallica", "Led Zeppelin"})]
    if only_standards:
        selected = [value for value in values if value.standard_value in only_standards and
                    value.column in {"customer.country", "invoice.billing_country", "genre.name", "media_type.name", "artist.name"}]
    settings, started = get_settings(), perf_counter()
    trace = TraceRecorder(settings=settings)
    draft = JsonLLM(settings).complete_json(
        system_prompt="你是数据库别名草案助手。只为给定标准值列出常见中文名称、简称或拼音写法。不得引入未提供标准值，不得把Rock与Rock And Roll合并。USA可给美国、老美；Brazil可给巴西，不把错别字巴稀作为正式别名。每个标准值1到4个别名。结果是待人工审核草案，不能声称已审核。",
        user_prompt=json.dumps({"standards": [{"standard_value": item.standard_value, "column": item.column} for item in selected]}, ensure_ascii=False),
        response_model=AliasDraft, trace=trace)
    allowed = {(value.column, value.standard_value) for value in selected}
    rows, seen = [], set()
    for entry in draft.rows:
        if (entry.column, entry.standard_value) not in allowed:
            raise ValueError("模型别名草案引用了候选之外的标准值，停止写入。")
        for alias in entry.aliases:
            if not alias.strip() or normalize(alias) == normalize(entry.standard_value):
                continue
            key = (entry.column, entry.standard_value, normalize(alias))
            if key in seen:
                continue
            seen.add(key)
            rows.append({"standard_value": entry.standard_value, "column": entry.column, "alias": alias.strip(),
                         "source": "llm_draft:" + settings.llm_model, "review_status": "pending", "reviewer": "",
                         "alias_id": "a-" + sha256("\0".join(key).encode()).hexdigest()[:16]})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=ALIAS_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    audit = {"task": "d2_alias_draft", "human_review_status": "pending", "model": settings.llm_model,
             "source": "live_catalog_distinct_values_only", "candidate_standard_count": len(selected),
             "alias_count": len(rows), "latency_ms": round((perf_counter() - started) * 1000),
             "artifact_sha256": sha256(output.read_bytes()).hexdigest(),
             "steps": [step.model_dump(mode="json") for step in trace.steps]}
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return audit


def write_index(values: list[ValueRecord], alias_records: list[ValueRecord], output: Path, audit: list[dict],
                alias_audit: dict, *, build_embeddings: bool = True, settings=None) -> dict:
    settings = settings or get_settings()
    records = sorted(values + alias_records, key=lambda item: (item.column, item.standard_value, item.kind, item.surface))
    output.mkdir(parents=True, exist_ok=True)
    def json_lines(items):
        return "".join(json.dumps(item.as_dict(), ensure_ascii=False) + "\n" for item in items)
    (output / "values.jsonl").write_text(json_lines(sorted(values, key=lambda value: (value.column, value.standard_value))), encoding="utf-8")
    (output / "records.jsonl").write_text(json_lines(records), encoding="utf-8")
    pinyin = {}
    for value in records:
        key = pinyin_key(value.surface)
        if value.candidate_id not in pinyin.setdefault(key, []):
            pinyin[key].append(value.candidate_id)
    (output / "pinyin_index.json").write_text(json.dumps(pinyin, ensure_ascii=False), encoding="utf-8")
    vectors, model = None, None
    if build_embeddings:
        embedder = get_embedder(settings)
        if embedder is None:
            raise ValueError("D1 BGE-M3 模型未找到，不能将未生成向量标成已完成。")
        # Encode repeated surfaces once, but preserve an explicit vector per field/record.
        surfaces = list(dict.fromkeys(item.surface for item in records))
        unique_vectors = embedder.encode(surfaces)
        positions = {text: index for index, text in enumerate(surfaces)}
        vectors = np.asarray([unique_vectors[positions[item.surface]] for item in records], dtype=np.float32)
        np.save(output / "embeddings.npy", vectors, allow_pickle=False)
        model = embedder.metadata()
    elif (output / "embeddings.npy").is_file():
        raise ValueError("--no-embeddings 不覆盖包含旧向量的目录，请选新目录。")
    ValueIndex(records, vectors)
    artifacts = ["values.jsonl", "records.jsonl", "pinyin_index.json"] + (["embeddings.npy"] if vectors is not None else [])
    metadata = {"format_version": 1, "complete": True,
                "built_at": datetime.now(timezone.utc).isoformat(), "source": "read_only_live_database",
                "standard_count": len(values), "record_count": len(records), "alias_audit": alias_audit,
                "column_audit": audit, "vector_count": 0 if vectors is None else len(vectors),
                "vector_shape": None if vectors is None else list(vectors.shape), "embedding": model,
                "artifact_sha256": {name: sha256((output / name).read_bytes()).hexdigest() for name in artifacts},
                "human_review_status": "approved_aliases_only", "vectors_enabled": build_embeddings}
    if settings.catalog_path.is_file():
        metadata["catalog_sha256"] = sha256(settings.catalog_path.read_bytes()).hexdigest()
    metadata["build_config"] = {"distinct_non_null_limit": 5000, "read_only": True,
                                "statement_timeout_ms": 5000, "normalization": "NFKC_casefold_whitespace",
                                "alias_review_required": True}
    (output / "index_meta.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "--output-dir", dest="output", type=Path, default=ROOT / "data/indexes/values")
    parser.add_argument("--catalog", type=Path, help="Read an existing trusted catalog; never builds or imports a database")
    parser.add_argument("--aliases", type=Path, default=ROOT / "data/aliases/aliases.csv")
    parser.add_argument("--audit", "--audit-output", dest="audit", type=Path, default=ROOT / "eval/reports/d2-acceptance/value-index-build.json")
    parser.add_argument("--draft-aliases", action="store_true")
    parser.add_argument("--draft-standard", action="append", help="Only draft this actual standard value; repeatable")
    parser.add_argument("--no-embeddings", action="store_true", help="Preparation/audit only; does not satisfy D2 vector acceptance")
    args, started = parser.parse_args(), perf_counter()
    settings = get_settings()
    if args.catalog:
        settings = replace(settings, catalog_path=args.catalog.resolve())
    values, columns = read_values(load_catalog(settings.catalog_path), settings.db_url)
    if args.draft_aliases:
        audit = draft_aliases(values, args.aliases, args.audit, args.draft_standard)
        print(json.dumps({key: audit[key] for key in ("alias_count", "human_review_status", "model", "latency_ms")}, ensure_ascii=False))
        return
    aliases, alias_audit = load_reviewed_aliases(args.aliases, values)
    metadata = write_index(values, aliases, args.output, columns, alias_audit, build_embeddings=not args.no_embeddings, settings=settings)
    metadata["latency_ms"] = round((perf_counter() - started) * 1000)
    metadata["catalog_sha256"] = sha256(settings.catalog_path.read_bytes()).hexdigest()
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: metadata[key] for key in ("standard_count", "record_count", "vector_shape", "latency_ms")}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(sanitize_error(exc, get_settings()), file=sys.stderr)
        sys.exit(1)
