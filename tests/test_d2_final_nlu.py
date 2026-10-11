"""Regression for accepted alias policies and source-preserving rewrite spans."""
import csv

from qa_agent.config import Settings
from qa_agent.nlu.linker import ValueLinker
from qa_agent.nlu.value_index import ValueIndex, ValueRecord, record_id
from scripts.build_value_index import ALIAS_FIELDS, load_reviewed_aliases


def test_candidate_only_alias_never_binds_even_when_only_candidate():
    row = ValueRecord(record_id("artist.name", "Iron Maiden"), "artist.name", "Iron Maiden",
                      "铁娘子", "reviewed-relation", "conditional_alias", "fixture")
    result = ValueLinker(ValueIndex([row]), Settings(db_url="")).link("铁娘子乐队的名称是什么？")
    assert result.ambiguous and not result.bindings and not result.patches
    assert result.ambiguous[0].guard_source == "reviewed_conditional_alias"


def test_politeness_and_origin_relation_are_outside_rewrite_patch():
    rows = [ValueRecord(record_id("customer.country", "Brazil"), "customer.country", "Brazil",
                        "巴西", "reviewed", "alias", "fixture")]
    question = "你好，请帮忙查一下来自巴西的客户有多少位，谢谢。"
    result = ValueLinker(ValueIndex(rows), Settings(db_url="")).link(question)
    assert result.rewritten_question == "你好，请帮忙查一下来自Brazil的客户有多少位，谢谢。"
    assert result.patches[0].original == "巴西"


def test_spaced_pinyin_uses_reviewed_country_surface():
    rows = [ValueRecord(record_id("customer.country", "Canada"), "customer.country", "Canada",
                        "加拿大", "reviewed", "alias", "fixture")]
    result = ValueLinker(ValueIndex(rows), Settings(db_url="")).link("客户所在国家为 jia na da 的客户有多少位？")
    assert result.bindings[0]["value"] == "Canada"
    assert result.bindings[0]["method"] == "pinyin"


def test_reviewed_candidate_is_indexed_separately_from_direct_mapping(tmp_path):
    path = tmp_path / "aliases.csv"
    row = dict(zip(ALIAS_FIELDS, ["Iron Maiden", "artist.name", "铁娘子", "source",
                                  "approved_candidate", "user-attested-audit", "fixture"]))
    with path.open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=ALIAS_FIELDS)
        writer.writeheader()
        writer.writerow(row)
    standard = ValueRecord(record_id("artist.name", "Iron Maiden"), "artist.name", "Iron Maiden",
                           "Iron Maiden", "catalog")
    aliases, audit = load_reviewed_aliases(path, [standard])
    assert aliases[0].kind == "conditional_alias"
    assert audit["candidate_only_count"] == 1 and audit["direct_count"] == 0
