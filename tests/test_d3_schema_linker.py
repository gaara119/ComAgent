from pathlib import Path
import json

import networkx as nx
import numpy as np
import pytest

from qa_agent.sql.catalog import Catalog, CatalogColumn, CatalogTable
from qa_agent.sql.schema_linker import (SchemaLinker, build_fk_graph, build_schema_index,
                                        complete_steiner, reciprocal_rank_fusion, query_facets)


def col(name="id"):
    return CatalogColumn(name, "integer", name, False)


def tbl(name, reference=None):
    fks = () if reference is None else ({"columns": ["id"], "references": {"schema": "s", "table": reference, "columns": ["id"]}},)
    return CatalogTable("s", name, (col(),), name, ("id",), fks)


def test_steiner_adds_real_bridge_and_exposes_disconnection():
    catalog = Catalog("aw", (tbl("detail", "product"), tbl("product", "subcategory"),
                              tbl("subcategory", "category"), tbl("category"), tbl("isolated")))
    selected, paths, components = complete_steiner(build_fk_graph(catalog), ["s.detail", "s.category", "s.isolated"])
    assert selected == {"s.detail", "s.product", "s.subcategory", "s.category", "s.isolated"}
    assert len(paths) == 3
    assert len(components) == 2
    assert all(pair["source_columns"] == pair["target_columns"] == ["id"] for pair in paths)


def test_rrf_has_no_duplicate_vote_in_single_channel():
    values = reciprocal_rank_fusion([["a", "a", "b"], ["b"]])
    assert list(values) == ["b", "a"]
    assert values["a"] == pytest.approx(1/61)


def test_dimension_facets_are_verbatim_and_not_table_bindings():
    question = "各运输地区的数量分别是多少？按 actual.items.count 统计。"
    facets = query_facets(question)
    assert facets == [question, "运输地区", "actual.items.count"]
    assert all(facet in question for facet in facets)
    assert query_facets("某个未说明对象有多少条？") == ["某个未说明对象有多少条？"]


def test_unknown_terminal_rejected():
    with pytest.raises(ValueError, match="Unknown"):
        complete_steiner(nx.Graph(), ["invented.table"])


class Encoder:
    def encode(self, texts):
        result = np.zeros((len(texts), 4), dtype=np.float32)
        result[:, 0] = 1.0
        return result

    def metadata(self):
        return {"test_encoder": True}


def test_schema_index_integrity_and_external_value_scope(tmp_path):
    catalog = Catalog("aw", (tbl("a"), tbl("b")))
    path = tmp_path / "catalog.yaml"
    path.write_text("catalog snapshot", encoding="utf-8")
    encoder = Encoder()
    build_schema_index(catalog, path, tmp_path / "index", encoder)
    linker = SchemaLinker(catalog, tmp_path / "index", encoder.encode, catalog_path=path)
    bundle = linker.link("query", value_columns=["s.b.id"])
    assert "s.b" in bundle.selected_tables
    assert "s.b.id" in bundle.value_recall
    assert set(bundle.selected_catalog.sqlglot_schema()["s"]) == {"a", "b"}
    with pytest.raises(ValueError, match="outside"):
        linker.link("query", value_columns=["private.invented.id"])
    path.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="catalog changed"):
        SchemaLinker(catalog, tmp_path / "index", encoder.encode, catalog_path=path)


def test_corrupt_vectors_fail_before_query(tmp_path):
    catalog = Catalog("aw", (tbl("a"),))
    path = tmp_path / "catalog.yaml"
    path.write_text("snapshot", encoding="utf-8")
    build_schema_index(catalog, path, tmp_path / "index", Encoder())
    (tmp_path / "index/tables.npy").write_bytes(b"wrong data")
    with pytest.raises(ValueError, match="Corrupt"):
        SchemaLinker(catalog, tmp_path / "index", Encoder().encode)


def test_dimension_is_not_lost_behind_uncalibrated_measure_scores(tmp_path):
    catalog = Catalog("aw", (tbl("measure_a"), tbl("measure_b"), tbl("dimension")))
    path = tmp_path / "catalog.yaml"
    path.write_text("snapshot", encoding="utf-8")
    directory = tmp_path / "index"
    build_schema_index(catalog, path, directory, Encoder())
    # A short dimension query has its own reliable ordering but smaller cosine
    # magnitude than a long explicit measure clause. Coverage must survive.
    np.save(directory / "tables.npy", np.asarray([[1,0,0,0],[.99,.01,0,0],[0,.6,.8,0]], dtype=np.float32))
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    from hashlib import sha256
    metadata["tables.npy_sha256"] = sha256((directory / "tables.npy").read_bytes()).hexdigest()
    (directory / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    def encode(texts):
        return np.asarray([[0,1,0,0] if text == "区域" else [1,0,0,0] for text in texts], dtype=np.float32)

    linker = SchemaLinker(catalog, directory, encode, table_top_k=2, terminal_top_k=2)
    bundle = linker.link("各区域的订单数量分别是多少？")
    assert "s.dimension" in bundle.terminal_tables
    assert "s.measure_a" in bundle.terminal_tables
    assert "s.dimension" in bundle.scores
    assert all("binding" not in key for key in bundle.as_dict())
