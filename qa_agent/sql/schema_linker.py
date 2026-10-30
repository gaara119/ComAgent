"""Table/column dense recall and genuine FK completion, shared by D3/D4.

The optional D4 SchemaPruner consumes this bundle. Recall itself remains
deterministic and never sees evaluation labels or invents a JOIN.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Callable, Iterable

import networkx as nx
from networkx.algorithms.approximation import steiner_tree
import numpy as np

from qa_agent.sql.catalog import Catalog, CatalogTable


def qualified(table: CatalogTable) -> str:
    return f"{table.schema}.{table.name}"


@dataclass(frozen=True)
class SchemaBundle:
    selected_tables: tuple[str, ...]
    columns: dict[str, tuple[str, ...]]
    join_paths: tuple[dict, ...]
    reasons: dict[str, tuple[str, ...]]
    table_recall: tuple[str, ...]
    column_recall: tuple[str, ...]
    value_recall: tuple[str, ...]
    terminal_tables: tuple[str, ...]
    bridge_tables: tuple[str, ...]
    disconnected_components: tuple[tuple[str, ...], ...]
    scores: dict[str, float]
    query_facets: tuple[str, ...]
    per_query_recall: tuple[dict, ...]
    selected_catalog: Catalog
    excluded_tables: dict[str, str] = field(default_factory=dict)
    pruning: dict = field(default_factory=dict)
    lexical_recall: tuple[str, ...] = ()
    protected_columns: tuple[str, ...] = ()
    protected_tables: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {key: value for key, value in self.__dict__.items() if key != "selected_catalog"}


def build_fk_graph(catalog: Catalog) -> nx.Graph:
    graph = nx.Graph()
    known = {qualified(table) for table in catalog.tables}
    graph.add_nodes_from(sorted(known))
    for table in catalog.tables:
        source = qualified(table)
        for fk in table.foreign_keys:
            ref = fk.get("references", {})
            target = f"{ref.get('schema', table.schema)}.{ref.get('table', '')}"
            if target not in known:
                continue
            pair = {"source_table": source, "source_columns": list(fk.get("columns", [])),
                    "target_table": target, "target_columns": list(ref.get("columns", []))}
            if len(pair["source_columns"]) != len(pair["target_columns"]) or not pair["source_columns"]:
                raise ValueError(f"Invalid foreign key from {source} to {target}")
            if graph.has_edge(source, target):
                graph[source][target]["foreign_keys"].append(pair)
            else:
                graph.add_edge(source, target, weight=1.0, foreign_keys=[pair])
    return graph


def reciprocal_rank_fusion(rankings: Iterable[Iterable[str]], k: int = 60) -> dict[str, float]:
    if k < 1:
        raise ValueError("RRF k must be positive")
    scores: dict[str, float] = {}
    for ranking in rankings:
        # One table contributes at most once per channel, even with many columns.
        for rank, name in enumerate(dict.fromkeys(ranking), 1):
            scores[name] = scores.get(name, 0.0) + 1.0 / (k + rank)
    return dict(sorted(scores.items(), key=lambda item: (-item[1], item[0])))


def complete_steiner(graph: nx.Graph, terminals: Iterable[str]) -> tuple[set[str], list[dict], list[list[str]]]:
    terminal_set = set(terminals)
    unknown = terminal_set - set(graph)
    if unknown:
        raise ValueError(f"Unknown terminal tables: {sorted(unknown)}")
    selected = set(terminal_set)
    paths: list[dict] = []
    components: list[list[str]] = []
    # Steiner's approximation requires connected input. Treat real disconnected
    # components independently, and expose the gap instead of joining by name.
    for nodes in nx.connected_components(graph):
        wanted = terminal_set & nodes
        if not wanted:
            continue
        components.append(sorted(wanted))
        if len(wanted) == 1:
            continue
        subgraph = steiner_tree(graph.subgraph(nodes), sorted(wanted), weight="weight", method="mehlhorn")
        selected.update(subgraph.nodes)
        for source, target in sorted(subgraph.edges):
            # Multiple FKs between the same tables are retained as alternatives;
            # generator must choose an actual matching column pair.
            paths.extend(graph[source][target]["foreign_keys"])
    return selected, paths, components


def _text_records(catalog: Catalog):
    table_names, table_texts, column_names, column_texts = [], [], [], []
    for table in catalog.tables:
        name = qualified(table)
        table_names.append(name)
        table_texts.append(f"表 {name}：{table.description}。列：" + "；".join(
            f"{column.name} {column.description}" for column in table.columns))
        for column in table.columns:
            column_names.append(name + "." + column.name)
            column_texts.append(f"表 {name}：{table.description}；列 {column.name}：{column.description}；类型 {column.data_type}")
    return table_names, table_texts, column_names, column_texts


def query_facets(question: str, mentions: Iterable[str] = ()) -> list[str]:
    """Verbatim dimension phrases prevent a long measure clause dominating.

    No table/answer mapping is used. Every returned facet occurs in the user
    question or was supplied by the caller as an extracted mention. These
    hints affect recall only and never become SQL bindings.
    """
    supplied = [str(mention).strip() for mention in mentions if str(mention).strip()]
    groups = [match.group(1).strip() for match in re.finditer(
        r"(?:每个|每种|各)([^，。？；,;.?]{2,24}?)(?:的|下面|分别|被|有|目前|关联)", question)]
    explicit = re.findall(r"(?<![A-Za-z0-9_])(?:[A-Za-z_][A-Za-z0-9_]*\.){1,2}[A-Za-z_][A-Za-z0-9_]*", question)
    return list(dict.fromkeys([question] + supplied + groups + explicit))[:8]


def _lexical_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text.casefold()))
    # Chinese character bigrams preserve catalog terminology without a new NER
    # model or a manually curated question-to-table lookup.
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        tokens.update(run[index:index + 2] for index in range(len(run) - 1))
    return tokens - {"的数", "数量", "多少", "记录", "字段", "保存", "对应", "例如", "table", "public"}


def lexical_schema_recall(question: str, catalog: Catalog, limit: int = 8) -> tuple[list[str], list[str], list[str]]:
    """Complement dense recall with IDF lexical items and exact identifiers.

    Exact names are protected; description overlap remains a candidate signal,
    never proof of a unique business entity or approval of a default policy.
    """
    query = _lexical_tokens(question)
    records = [(qualified(table), _lexical_tokens(table.name + " " + table.description.split("核验限制")[0] + " " +
                " ".join(column.name + " " + column.description.split("例如")[0] for column in table.columns))) for table in catalog.tables]
    df = {term: sum(term in terms for _, terms in records) for term in query}
    scores = {name: sum(math.log(1 + len(records) / (1 + df[term])) for term in query & terms) /
                   math.sqrt(max(1, len(terms))) for name, terms in records}
    exact_tables, exact_columns = [], []
    exact_columns, exact_tables = explicit_schema_references(question, catalog)
    exact_tables = list(dict.fromkeys(exact_tables))
    ranked = [name for name in sorted(scores, key=lambda name: (-scores[name], name)) if scores[name] > 0]
    return list(dict.fromkeys(exact_tables + ranked))[:limit], list(dict.fromkeys(exact_columns)), exact_tables


def explicit_schema_references(question: str, catalog: Catalog) -> tuple[list[str], list[str]]:
    """Resolve only identifier tokens, independently of optional lexical recall."""
    identifiers = set(re.findall(r"(?<![A-Za-z0-9_])(?:[A-Za-z_][A-Za-z0-9_]*\.){0,2}[A-Za-z_][A-Za-z0-9_]*(?![A-Za-z0-9_])", question.casefold()))
    exact_tables, exact_columns = [], []
    for table in catalog.tables:
        name = qualified(table)
        if name.casefold() in identifiers or table.name.casefold() in identifiers:
            exact_tables.append(name)
        for column in table.columns:
            forms = (name + "." + column.name, table.name + "." + column.name)
            if any(form.casefold() in identifiers for form in forms):
                exact_columns.append(name + "." + column.name)
                exact_tables.append(name)
    return list(dict.fromkeys(exact_columns)), list(dict.fromkeys(exact_tables))


def augment_bundle_from_sql(bundle: SchemaBundle, catalog: Catalog, sql: str) -> SchemaBundle:
    """Recover valid draft-referenced items omitted by forward pruning.

    Inspired by the bidirectional recall idea in RSL-SQL; this is not its full
    multi-candidate algorithm. A draft must pass the complete authentic catalog
    validator first. Unsafe SQL, invented items and cross-database objects never
    expand the available catalog. No expected answer/table list is accepted.
    """
    from dataclasses import replace
    from sqlglot import exp
    from sqlglot.optimizer.scope import traverse_scope
    from qa_agent.sql.repair_guard import _qualified
    from qa_agent.sql.validator import validate_sql

    validate_sql(sql, catalog)
    tree = _qualified(sql, catalog)
    needed: dict[str, set[str]] = {name: set(columns) for name, columns in bundle.columns.items()}
    draft_items = []
    for scope in traverse_scope(tree):
        sources = {alias: source for alias, (_, source) in scope.selected_sources.items()}
        for column in scope.columns:
            source = sources.get(column.table)
            if isinstance(source, exp.Table):
                name = f"{source.db or 'public'}.{source.name}"
                needed.setdefault(name, set()).add(column.name)
                draft_items.append(name + "." + column.name)
        for source in sources.values():
            if isinstance(source, exp.Table):
                needed.setdefault(f"{source.db or 'public'}.{source.name}", set())
    selected, joins, components = complete_steiner(build_fk_graph(catalog), needed)
    originals = {qualified(table): table for table in catalog.tables}
    for name in selected:
        if name not in needed:
            needed[name] = set(originals[name].column_names)
        needed[name].update(originals[name].primary_key)
    for join in joins:
        needed[join["source_table"]].update(join["source_columns"])
        needed[join["target_table"]].update(join["target_columns"])
    tables = tuple(replace(originals[name], columns=tuple(column for column in originals[name].columns if column.name in needed[name]),
        foreign_keys=tuple(fk for fk in originals[name].foreign_keys
            if f"{fk['references'].get('schema', originals[name].schema)}.{fk['references']['table']}" in selected
            and set(fk['columns']) <= needed[name]
            and set(fk['references']['columns']) <= needed[f"{fk['references'].get('schema', originals[name].schema)}.{fk['references']['table']}"]))
        for name in sorted(selected))
    original_items = {name + "." + column for name, columns in bundle.columns.items() for column in columns}
    additions = sorted(set(draft_items) - original_items)
    diagnostics = {**bundle.pruning, "backward_recall": {"status": "completed", "draft_verified_against_full_catalog": True,
                   "added_items": additions, "gold_input": False, "extra_llm_calls": 0}}
    return replace(bundle, selected_tables=tuple(sorted(selected)), columns={name: tuple(column.name for column in originals[name].columns if column.name in needed[name]) for name in sorted(selected)},
        selected_catalog=replace(catalog, tables=tables), join_paths=tuple(joins), pruning=diagnostics,
        disconnected_components=tuple(tuple(c) for c in components))


def build_schema_index(catalog: Catalog, catalog_path: Path, output: Path, embedder) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    table_names, table_texts, column_names, column_texts = _text_records(catalog)
    table_vectors = embedder.encode(table_texts)
    column_vectors = embedder.encode(column_texts)
    np.save(output / "tables.npy", table_vectors, allow_pickle=False)
    np.save(output / "columns.npy", column_vectors, allow_pickle=False)
    # Real examples are lookup hints only. They do not authorize a SQL filter.
    values = []
    for table in catalog.tables:
        for column in table.columns:
            for value in column.sample_values:
                if isinstance(value, str) and len(value.strip()) >= 3 and len(value) <= 100:
                    values.append({"column": qualified(table) + "." + column.name, "value": value})
    metadata = {"format": "d3_schema_dense_v1", "database": catalog.database,
                "catalog_path": str(catalog_path), "catalog_sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
                "table_names": table_names, "column_names": column_names,
                "table_count": len(table_names), "column_count": len(column_names),
                "table_vector_shape": list(table_vectors.shape), "column_vector_shape": list(column_vectors.shape),
                "embedder": embedder.metadata(), "value_hints": values}
    for name in ("tables.npy", "columns.npy"):
        metadata[name + "_sha256"] = hashlib.sha256((output / name).read_bytes()).hexdigest()
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return metadata


class SchemaLinker:
    def __init__(self, catalog: Catalog, index_path: Path, encoder: Callable[[list[str]], np.ndarray], *,
                 catalog_path: Path | None = None, table_top_k: int = 8, column_top_k: int = 20,
                 terminal_top_k: int = 8, rrf_k: int = 60, enhanced_recall: bool | None = None):
        self.catalog = catalog
        self.encoder = encoder
        self.table_top_k, self.column_top_k = table_top_k, column_top_k
        self.terminal_top_k, self.rrf_k = terminal_top_k, rrf_k
        self.enhanced_recall = (os.getenv("SCHEMA_RECALL_ENHANCED", "false").casefold() not in {"false", "0", "off"}
                                if enhanced_recall is None else enhanced_recall)
        self.graph = build_fk_graph(catalog)
        self.metadata = json.loads((index_path / "metadata.json").read_text(encoding="utf-8"))
        if catalog_path and self.metadata["catalog_sha256"] != hashlib.sha256(catalog_path.read_bytes()).hexdigest():
            raise ValueError("AW catalog changed; rebuild schema index before querying")
        for name in ("tables.npy", "columns.npy"):
            if self.metadata[name + "_sha256"] != hashlib.sha256((index_path / name).read_bytes()).hexdigest():
                raise ValueError(f"Corrupt schema vectors: {name}")
        self.tables = np.load(index_path / "tables.npy", allow_pickle=False)
        self.columns = np.load(index_path / "columns.npy", allow_pickle=False)
        expected = {qualified(table) for table in catalog.tables}
        if set(self.metadata["table_names"]) != expected:
            raise ValueError("Schema index contains missing or unknown tables")
        if self.tables.shape[0] != len(self.metadata["table_names"]) or self.columns.shape[0] != len(self.metadata["column_names"]):
            raise ValueError("Schema index shape mismatch")
        expected_columns = {qualified(table) + "." + column.name for table in catalog.tables for column in table.columns}
        if (set(self.metadata["column_names"]) != expected_columns or len(self.metadata["column_names"]) != len(expected_columns)
                or self.tables.ndim != 2 or self.columns.ndim != 2 or self.tables.shape[1] != self.columns.shape[1]
                or not np.isfinite(self.tables).all() or not np.isfinite(self.columns).all()):
            raise ValueError("Schema index contains invalid column domains or vector values")

    def link(self, question: str, mentions: Iterable[str] = (), value_columns: Iterable[str] = ()) -> SchemaBundle:
        queries = query_facets(question, mentions)
        vectors = np.asarray(self.encoder(queries), dtype=np.float32)
        if vectors.shape != (len(queries), self.tables.shape[1]) or not np.isfinite(vectors).all():
            raise ValueError("Schema query encoder returned invalid shape or non-finite values")
        vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
        # Max pooled similarities preserve a dimension's own recall signal even
        # when the complete question contains many measure/order/date tokens.
        table_scores = vectors @ self.tables.T
        column_scores = vectors @ self.columns.T
        table_max, column_max = table_scores.max(axis=0), column_scores.max(axis=0)
        table_order = np.argsort(-table_max, kind="stable")[:self.table_top_k]
        column_order = np.argsort(-column_max, kind="stable")[:self.column_top_k]
        per_query = []
        for index, query in enumerate(queries):
            per_query.append({"query":query,
                "table_top": [self.metadata["table_names"][int(i)] for i in np.argsort(-table_scores[index], kind="stable")[:self.table_top_k]],
                "column_top": [self.metadata["column_names"][int(i)] for i in np.argsort(-column_scores[index], kind="stable")[:self.column_top_k]]})
        table_hits = [self.metadata["table_names"][int(i)] for i in table_order]
        column_hits = [self.metadata["column_names"][int(i)] for i in column_order]
        # Vote columns to their owning table. Dense similarity breaks vote ties.
        votes: dict[str, tuple[int, float]] = {}
        for i, column in zip(column_order, column_hits):
            name = column.rsplit(".", 1)[0]
            count, score = votes.get(name, (0, 0.0))
            votes[name] = (count + 1, score + float(column_max[int(i)]))
        column_tables = sorted(votes, key=lambda name: (-votes[name][0], -votes[name][1], name))
        known_columns = set(self.metadata["column_names"])
        external_columns = list(dict.fromkeys(value_columns))
        if set(external_columns) - known_columns:
            raise ValueError("Value hit references a column outside the AW catalog")
        lower_question = question.casefold()
        hints = [entry["column"] for entry in self.metadata.get("value_hints", [])
                 if entry["value"].casefold() in lower_question]
        value_hits = list(dict.fromkeys(external_columns + hints))
        value_tables = list(dict.fromkeys(column.rsplit(".", 1)[0] for column in value_hits))
        facet_coverage = list(dict.fromkeys(item["table_top"][0] for item in per_query[1:] if item["table_top"]))
        table_hits = list(dict.fromkeys(facet_coverage + table_hits))[:self.table_top_k]
        protected_columns, protected_tables = explicit_schema_references(question, self.catalog)
        lexical_hits = (lexical_schema_recall(question, self.catalog, self.table_top_k)[0] if self.enhanced_recall else [])
        channels = [table_hits, column_tables, value_tables] + ([lexical_hits] if self.enhanced_recall else [])
        scores = reciprocal_rank_fusion(channels, self.rrf_k)
        # Similarities from differently sized queries are not calibrated. A
        # strong explicit dimension may otherwise disappear behind twenty
        # measure columns. Reserve one recall candidate per verbatim facet,
        # then fill the same terminal budget by three-channel RRF. This is
        # candidate coverage, never approval of a unique SQL binding.
        protected = list(dict.fromkeys(protected_tables + [column.rsplit(".", 1)[0] for column in external_columns]))
        terminals = list(dict.fromkeys(protected + facet_coverage + list(scores)))[:max(self.terminal_top_k, len(protected))]
        selected, joins, components = complete_steiner(self.graph, terminals)
        bridges = selected - set(terminals)
        reasons: dict[str, tuple[str, ...]] = {}
        for table in sorted(selected):
            entries = []
            if table in table_hits:
                entries.append(f"表描述向量召回第 {table_hits.index(table)+1} 位")
            if table in column_tables:
                entries.append(f"列描述 Top-{self.column_top_k} 投票：{votes[table][0]} 列")
            if table in value_tables:
                entries.append("真实目录示例值或已核验值命中对应列；仅提供定位候选")
            if table in lexical_hits:
                entries.append(f"真实表列说明的词项 IDF 召回第 {lexical_hits.index(table)+1} 位；与向量通道融合")
            if table in protected_tables:
                entries.append("用户显式提到的真实表/字段，禁止剪枝时静默丢失")
            if table in bridges:
                entries.append("真实外键图 Steiner 补全的桥接表")
            for query in per_query[1:]:
                if query["table_top"] and table == query["table_top"][0]:
                    entries.append(f"用户原文要素‘{query['query']}’的独立向量召回最高候选；仅提供定位")
            reasons[table] = tuple(entries)
        selected_catalog = Catalog(database=self.catalog.database,
            tables=tuple(table for table in self.catalog.tables if qualified(table) in selected),
            dialect=self.catalog.dialect, version=self.catalog.version,
            metadata={**self.catalog.metadata, "schema_linker": "RRF + Steiner; no LLM pruning"})
        return SchemaBundle(tuple(sorted(selected)),
            {qualified(table): tuple(column.name for column in table.columns) for table in selected_catalog.tables},
            tuple(joins), reasons, tuple(table_hits), tuple(column_hits), tuple(value_hits),
            tuple(terminals), tuple(sorted(bridges)), tuple(tuple(c) for c in components), scores,
            tuple(queries), tuple(per_query), selected_catalog,
            lexical_recall=tuple(lexical_hits), protected_columns=tuple(protected_columns), protected_tables=tuple(protected_tables))
