from dataclasses import replace
import json

import pytest

from qa_agent.sql.catalog import Catalog, CatalogColumn, CatalogTable
from qa_agent.sql.pruner import PruningDecision, SchemaPruner, SchemaPruningError
from qa_agent.sql.schema_linker import SchemaBundle, build_fk_graph, complete_steiner
from qa_agent.trace import TraceRecorder


def table(name, target=None):
    columns = tuple(CatalogColumn(column, "integer") for column in ("id", "foreign_id", "amount", "unused"))
    fk = () if target is None else ({"columns": ["foreign_id"],
        "references": {"schema": "s", "table": target, "columns": ["id"]}},)
    return CatalogTable("s", name, columns, name, ("id",), fk)


def bundle(catalog, terminals):
    selected, joins, components = complete_steiner(build_fk_graph(catalog), terminals)
    return SchemaBundle(tuple(sorted(selected)), {}, tuple(joins), {}, (), (), (), tuple(terminals),
        tuple(sorted(selected - set(terminals))), tuple(tuple(c) for c in components),
        {name: .1 for name in terminals}, ("question",), (), catalog)


class LLM:
    def __init__(self, selected, excluded=None):
        self.decision = PruningDecision(selected=selected, excluded=excluded or {})
        self.payload = None

    def complete_json(self, **kwargs):
        self.payload = json.loads(kwargs["user_prompt"])
        if kwargs["trace"]:
            with kwargs["trace"].step("llm") as step:
                step.output_summary = {"usage": {"prompt_tokens": 100, "completion_tokens": 25}}
        return self.decision


def choice(name, columns=("amount",)):
    return {"table": name, "columns": list(columns), "reason": "用户要求的真实度量"}


def test_bridge_and_both_fk_columns_restored_without_invented_joins():
    catalog = Catalog("aw", (table("sales", "product"), table("product", "category"),
                              table("category"), table("purchase")))
    original = bundle(catalog, ["s.sales", "s.category", "s.purchase"])
    llm = LLM([choice("s.sales"), choice("s.category")], {"s.purchase": "采购不是销售"})
    trace = TraceRecorder()
    result = SchemaPruner(catalog).prune("按类别统计销售额", original, llm, trace)
    assert result.selected_tables == ("s.category", "s.product", "s.sales")
    assert result.bridge_tables == ("s.product",)
    assert result.pruning["connected"]
    assert "foreign_id" in result.columns["s.sales"]
    assert "id" in result.columns["s.category"]
    assert "unused" not in result.columns["s.sales"]
    assert result.excluded_tables["s.purchase"] == "采购不是销售"
    assert len(result.join_paths) == 2
    assert all(join in [fk for _, _, data in build_fk_graph(catalog).edges(data=True)
                       for fk in data["foreign_keys"]] for join in result.join_paths)
    assert [step.name for step in trace.steps] == ["schema_prune", "llm"]
    assert set(llm.payload) == {"question", "candidate_catalog", "required_columns"}
    assert "gold" not in llm.payload
    # Retaining references only when their source and target columns survive
    # ensures SQL validation sees the same genuine pruned catalog as generation.
    for selected_table in result.selected_catalog.tables:
        for fk in selected_table.foreign_keys:
            ref = fk["references"]
            target = result.selected_catalog.get_table(ref["table"], ref["schema"])
            assert set(ref["columns"]) <= target.column_names


@pytest.mark.parametrize("selected", [
    [choice("s.missing")], [choice("s.sales", ("invented",))],
    [choice("s.sales"), choice("s.sales")],
])
def test_hallucinated_or_duplicate_selection_rejected(selected):
    catalog = Catalog("aw", (table("sales"),))
    with pytest.raises(SchemaPruningError):
        SchemaPruner(catalog).prune("query", bundle(catalog, ["s.sales"]), LLM(selected))


@pytest.mark.parametrize("selected", [[choice("s.other")], [choice("s.sales", ("id",))]])
def test_verified_filter_cannot_disappear(selected):
    catalog = Catalog("aw", (table("sales"), table("other")))
    with pytest.raises(SchemaPruningError, match="verified filter"):
        SchemaPruner(catalog).prune("query", bundle(catalog, ["s.sales", "s.other"]),
            LLM(selected), required_columns=["sales.amount"])


def test_unknown_binding_rejected_before_model_call():
    catalog = Catalog("aw", (table("sales"),))
    llm = LLM([choice("s.sales")])
    with pytest.raises(SchemaPruningError, match="unknown"):
        SchemaPruner(catalog).prune("query", bundle(catalog, ["s.sales"]), llm,
            required_columns=["s.sales.fake"])
    assert llm.payload is None


def test_real_disconnected_components_exposed_without_fake_fk():
    catalog = Catalog("aw", (table("sales"), table("other")))
    result = SchemaPruner(catalog).prune("两个独立统计", bundle(catalog, ["s.sales", "s.other"]),
        LLM([choice("s.sales"), choice("s.other")]))
    assert not result.pruning["connected"]
    assert len(result.disconnected_components) == 2
    assert result.join_paths == ()


def test_at_most_twelve_authentic_candidates_without_label_selection():
    catalog = Catalog("aw", tuple(table(f"t{i:02}") for i in range(20)))
    original = bundle(catalog, [f"s.t{i:02}" for i in range(20)])
    llm = LLM([choice("s.t00")])
    result = SchemaPruner(catalog).prune("query", original, llm)
    assert result.pruning["candidate_count"] == 12
    assert len(result.excluded_tables) == 19
    assert all(name in {f"s.t{i:02}" for i in range(20)} for name in result.pruning["candidate_tables"])


@pytest.mark.parametrize("excluded", [{"s.fake": "错表"}, {"s.sales": "又选又排"}])
def test_exclusion_claim_validated(excluded):
    catalog = Catalog("aw", (table("sales"),))
    with pytest.raises(SchemaPruningError, match="Excluded"):
        SchemaPruner(catalog).prune("query", bundle(catalog, ["s.sales"]),
            LLM([choice("s.sales")], excluded))
