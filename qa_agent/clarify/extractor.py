"""Use the existing JSON model only for semantic tasks that need the D3 gate."""
from __future__ import annotations

import json
from pathlib import Path
import re
from datetime import date

from qa_agent.clarify.rules import SemanticIntent, explicit_period

PROMPT_PATH = Path(__file__).with_name("prompts") / "intent_extract.txt"
COMPLEX_WORDS = ("同比", "环比", "增长", "增幅", "占比", "比例", "最受欢迎", "最热门", "最火", "卖得最好",
                 "热门", "谁买得最多", "买得最多", "复购", "客单价", "改成", "换成", "还是", "改为", "相比")


def explicit_region_scope(question: str) -> str | None:
    if any(word in question for word in ('billing_country','账单国家','账单所在国')):
        return 'invoice.billing_country'
    if any(word in question for word in ('customer.country','客户所在地','客户所在国','客户居住国')):
        return 'customer.country'
    return None


def region_needs_semantic_gate(question: str, bindings: list[dict], catalog) -> bool:
    return (catalog.database.casefold()=='chinook' and
            any(word in question for word in ('发票','账单','invoice')) and
            any(word in question for word in ('销售额','金额','总额','total','revenue')) and
            any(item.get('column') in {'customer.country','invoice.billing_country'} for item in bindings))


def needs_semantic_model(question: str, *, is_followup: bool = False) -> bool:
    return (is_followup or any(word in question for word in COMPLEX_WORDS) or
            any(word in question for word in ("这批", "这些", "最近", "今年", "去年", "这期间", "这个期间", "这个时间段")) or
            len(set(re.findall(r"(?<!\d)(\d{4})(?:年|-)",question)))>1 or
            bool(re.search(r"\d{4}(?:年|-)\d{1,2}(?:月|-)\d{1,2}",question)) or
            bool(re.search(r"\d{4}\s*年.*?(?:月|日|季度|半年|周)",question)) or
            bool(re.search(r"排名|前\s*\d+|top\s*\d+", question, re.I)))


def extract_intent(question: str, catalog, llm, trace=None, *, bindings: list[dict] | None = None) -> SemanticIntent:
    region_gate=region_needs_semantic_gate(question,bindings or [],catalog)
    explicit_scope=explicit_region_scope(question) if region_gate else None
    if not needs_semantic_model(question) and (not region_gate or explicit_scope is not None):
        # Existing D1/D2 clear lookup questions retain their original fast path.
        return SemanticIntent(time_scope=explicit_period(question), filters=bindings or [],region_scope=explicit_scope)
    prompt = {"question": question, "catalog": catalog.prompt_schema(),
              "verified_value_bindings": bindings or []}
    result = llm.complete_json(PROMPT_PATH.read_text(encoding="utf-8"),
                               json.dumps(prompt, ensure_ascii=False), SemanticIntent, trace=trace)
    result.assumptions=[]
    result.default_assumptions=[]
    if catalog.database.casefold()=="chinook" and result.rank_object:
        # The semantic model may spell the explicit object in Chinese. Convert
        # only a named real Chinook object, never infer a missing ranking object.
        object_names={"曲目":"track","歌曲":"track","客户":"customer","顾客":"customer",
                      "艺术家":"artist","乐队":"artist","发票":"invoice","账单":"invoice",
                      "专辑":"album","流派":"genre","歌单":"playlist","播放列表":"playlist"}
        written=result.rank_object.strip()
        if written in object_names and written in question and object_names[written] in {table.name for table in catalog.tables}:
            result.rank_object=object_names[written]
    if region_gate:
        result.region_scope=explicit_scope
        result.region_ambiguous=explicit_scope is None
    if catalog.database.casefold()=="chinook":
        popularity=any(word in question for word in ("最受欢迎","最热门","最火","热门曲目","热门歌曲","卖得最好"))
        explicit_measure=any(word in question for word in ("购买数量","销量","销售额","金额","歌单","收录","quantity","revenue"))
        if popularity and result.rank_object=="track" and not explicit_measure:
            result.metric=None
        if any(word in question for word in ("谁买得最多","买得最多的客户")) and not explicit_measure:
            result.metric=None
        if result.rank_object=="customer" and not any(word in question for word in ("客户","顾客","customer")):
            result.rank_object=None
    # The calendar conversion is programmatic whenever the user wrote one period.
    period = explicit_period(question)
    if period:
        result.time_scope = period
    else:
        # Do not let words like “期间/最近” bypass grounding of model-filled dates.
        explicit_years = {int(value) for value in re.findall(r"(?<!\d)(\d{4})(?!\d)", question)}
        try:
            current = (result.time_scope or {}).get("current") or {}
            start, end = date.fromisoformat(current["start"]), date.fromisoformat(current["end"])
            valid = start < end and start.year in explicit_years and end.year in explicit_years | {year+1 for year in explicit_years}
        except (KeyError, TypeError, ValueError):
            valid = False
        if not valid:
            result.time_scope = None
            if any(word in question for word in ("这期间", "这个期间", "这个时间段")):
                result.time_ambiguous = True
        if any(word in question for word in ("最近", "今年", "去年")):
            actual_range = catalog.metadata.get("invoice_date_range") or {}
            if ("数据" in question and "最近" in question and "有记录" in question and
                "年份" in question and "完整" not in question and actual_range.get("max_date")):
                try:
                    year = date.fromisoformat(str(actual_range["max_date"])[:10]).year
                    result.time_scope = explicit_period(f"{year}年")
                    result.assumptions.append(f"用户要求数据中最近有记录的年份，按{year}年筛选；不代表完整年度。")
                except ValueError:
                    result.time_ambiguous = True
            else:
                result.time_scope = None
                result.time_ambiguous = True
    if "同比" in question:
        result.comparison = {"type": "yoy"}
    elif "环比" in question:
        result.comparison = {"type": "mom"}
    result.filters = bindings or []
    return result
