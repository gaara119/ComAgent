"""Load the catalog exported from the real PostgreSQL database."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class CatalogError(ValueError):
    """The database catalog is missing, invalid, or inconsistent."""


@dataclass(frozen=True)
class CatalogColumn:
    name: str
    data_type: str
    description: str = ""
    nullable: bool = True
    sample_values: tuple[Any, ...] = ()


@dataclass(frozen=True)
class CatalogTable:
    schema: str
    name: str
    columns: tuple[CatalogColumn, ...]
    description: str = ""
    primary_key: tuple[str, ...] = ()
    foreign_keys: tuple[dict[str, Any], ...] = ()
    row_count: int | None = None

    @property
    def column_names(self) -> set[str]:
        return {column.name for column in self.columns}


@dataclass(frozen=True)
class Catalog:
    database: str
    tables: tuple[CatalogTable, ...]
    dialect: str = "postgres"
    version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_table(self, name: str, schema: str = "public") -> CatalogTable:
        for table in self.tables:
            if table.name == name and table.schema == schema:
                return table
        raise CatalogError(f"目录中不存在表 {schema}.{name}。")

    def sqlglot_schema(self) -> dict[str, dict[str, dict[str, str]]]:
        result: dict[str, dict[str, dict[str, str]]] = {}
        for table in self.tables:
            result.setdefault(table.schema, {})[table.name] = {
                column.name: column.data_type for column in table.columns
            }
        return result

    def prompt_schema(self) -> str:
        """The prompt contains actual names/types/values, never gold answers."""
        lines = [f"数据库：{self.database}；方言：PostgreSQL；数据版本：{self.version}"]
        if self.metadata.get("invoice_date_range"):
            lines.append(
                "真实发票日期范围=" + json.dumps(
                    self.metadata["invoice_date_range"], ensure_ascii=False, default=str
                ) + "；用户明确要求范围外日期时仍保留该条件。"
            )
        for table in self.tables:
            qualified = f'{_quote(table.schema)}.{_quote(table.name)}'
            lines.append(f"表 {qualified}：{table.description}")
            for column in table.columns:
                nullable = "可为 NULL" if column.nullable else "不可为 NULL"
                examples = ""
                if column.sample_values:
                    examples = "；真实示例=" + json.dumps(
                        column.sample_values, ensure_ascii=False, default=str
                    )
                lines.append(
                    f"  {_quote(column.name)} {column.data_type}（{nullable}）"
                    f"：{column.description}{examples}"
                )
            if table.primary_key:
                lines.append("  主键=" + ", ".join(map(_quote, table.primary_key)))
            for fk in table.foreign_keys:
                lines.append("  外键=" + json.dumps(fk, ensure_ascii=False, default=str))
        return "\n".join(lines)


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def load_catalog(path: str | Path) -> Catalog:
    path = Path(path)
    if not path.is_file():
        raise CatalogError("数据库目录尚未生成，请先运行 scripts/build_catalog.py。")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict) or not isinstance(data.get("tables"), list):
            raise CatalogError("目录必须包含 tables 列表。")
        tables = []
        seen = set()
        for entry in data["tables"]:
            name, schema = str(entry["name"]), str(entry.get("schema", "public"))
            if not name or not schema or (schema, name) in seen:
                raise CatalogError("目录包含空表名或重复表。")
            seen.add((schema, name))
            columns = tuple(
                CatalogColumn(
                    name=str(column["name"]),
                    data_type=str(column.get("type", column.get("data_type", "TEXT"))),
                    description=str(column.get("description", "")),
                    nullable=bool(column.get("nullable", True)),
                    sample_values=tuple(column.get("sample_values", column.get("examples", [])) or []),
                )
                for column in entry["columns"]
            )
            if not columns or any(not column.name for column in columns):
                raise CatalogError(f"表 {schema}.{name} 没有有效列。")
            if len({column.name for column in columns}) != len(columns):
                raise CatalogError(f"表 {schema}.{name} 包含重复列。")
            primary_key = tuple(entry.get("primary_key") or ())
            if not set(primary_key).issubset({column.name for column in columns}):
                raise CatalogError(f"表 {schema}.{name} 的主键不在列目录中。")
            tables.append(
                CatalogTable(
                    schema=schema, name=name, columns=columns,
                    description=str(entry.get("description", "")),
                    primary_key=primary_key,
                    foreign_keys=tuple(entry.get("foreign_keys") or ()),
                    row_count=entry.get("row_count"),
                )
            )
        if not tables:
            raise CatalogError("数据库目录没有业务表。")
        dialect = str(data.get("dialect", "postgres"))
        if dialect not in {"postgres", "postgresql"}:
            raise CatalogError("当前支持 PostgreSQL 数据目录。")
        return Catalog(
            database=str(data.get("database", data.get("db_id", "chinook"))),
            dialect="postgres", version=str(data.get("version", "")),
            tables=tuple(tables), metadata={k: v for k, v in data.items() if k != "tables"},
        )
    except CatalogError:
        raise
    except (OSError, yaml.YAMLError, KeyError, TypeError, ValueError) as exc:
        raise CatalogError(f"无法读取数据库目录：{type(exc).__name__}。") from exc
