"""Use the existing JSON model only for semantic tasks that need the D3 gate."""
from __future__ import annotations

import json
from pathlib import Path
import re
from datetime import date

from qa_agent.clarify.rules import SemanticIntent, explicit_period, explicit_comparison_period

PROMPT_PATH = Path(__file__).with_name("prompts") / "intent_extract.txt"
COMPLEX_WORDS = ("同比", "环比", "增长", "增幅", "占比", "比例", "最受欢迎", "最热门", "最火", "卖得最好",
                 "热门", "谁买得最多", "买得最多", "复购", "客单价", "改成", "换成", "还是", "改为", "相比")


def _bare_amount_share(question: str) -> bool:
    """A period plus amount share names no numerator subset.

    Explicit "全部发票金额占同期全部发票金额" remains a legitimate
    full-library numerator and denominator. This is a literal input-shape
    guard, not an entity/gold/case-ID default.
    """
    return bool(re.fullmatch(
        r'\s*(?:请(?:问|帮我)?\s*)?(?:(?:查(?:询)?|计算)\s*)?'
        r'(?:\d{4}\s*年(?:\s*(?:全年|\d{1,2}\s*月))?\s*)?'
        r'(?:销售额|发票金额|账单金额)\s*(?:的)?\s*(?:占比|比例)\s*'
        r'(?:(?:是|有)?多少(?:百分比)?|是什么|怎么算)?\s*[？?。.!！]*\s*',question))


def explicit_region_scope(question: str) -> str | None:
    if any(word in question for word in ('billing_country','账单国家','账单所在国','账单国')):
        return 'invoice.billing_country'
    if any(word in question for word in ('customer.country','客户所在地','客户所在国','客户居住国','居住客户','居住的客户')):
        return 'customer.country'
    return None


def region_needs_semantic_gate(question: str, bindings: list[dict], catalog) -> bool:
    return (catalog.database.casefold()=='chinook' and
            any(word in question for word in ('发票','账单','invoice','销售额')) and
            any(word in question for word in ('销售额','金额','总额','total','revenue')) and
            any(item.get('column') in {'customer.country','invoice.billing_country'} for item in bindings))


def needs_semantic_model(question: str, *, is_followup: bool = False) -> bool:
    return (is_followup or any(word in question for word in COMPLEX_WORDS) or
            any(word in question for word in ("这批", "这些", "最近", "今年", "去年", "这期间", "这个期间", "这个时间段")) or
            len(set(re.findall(r"(?<!\d)(\d{4})(?:年|-)",question)))>1 or
            bool(re.search(r"\d{4}(?:年|-)\d{1,2}(?:月|-)\d{1,2}",question)) or
            bool(re.search(r"\d{4}\s*年.*?(?:月|日|季度|半年|周)",question)) or
            bool(re.search(r"排名|前\s*\d+|top\s*\d+", question, re.I)))


def explicit_customer_attribute_top(question: str, catalog, *, expected_n: int | None = None,
                                    expected_order: dict | None = None) -> bool:
    """Prove a whole pure attribute lookup, including every remaining clause.

    A name/ID sort followed by any unrecognized business request is not covered.
    No business metric is installed and no missing business condition is hidden.
    """
    if catalog.database.casefold() != 'chinook':
        return False
    table=next((table for table in catalog.tables if table.name=='customer' and table.schema=='public'),None)
    if table is None:
        return False
    fields={'客户编号':'customer_id','编号':'customer_id','客户名字':'first_name','名字':'first_name',
            '客户姓氏':'last_name','姓氏':'last_name','customer_id':'customer_id',
            'first_name':'first_name','last_name':'last_name',
            'customer.customer_id':'customer_id','customer.first_name':'first_name','customer.last_name':'last_name'}
    attr='(?:'+'|'.join(re.escape(name) for name in sorted(fields,key=len,reverse=True))+')'
    direction=r'(?:升序|降序|ASC|DESC)'
    clauses=[clause.strip() for clause in re.split(r'[，,；;。？！?!]',question.strip()) if clause.strip()]
    if not clauses:
        return False
    primary=re.fullmatch(r'(?:按|依|根据)\s*(?P<field>'+attr+r')\s*(?P<direction>'+direction+r')'+
                         r'\s*(?:排序)?\s*(?:取|列出|获取|展示|返回|查看)?\s*前\s*(?P<n>\d+)\s*(?:位|个|名)?\s*客户',clauses[0],re.I)
    if primary is None or not 1<=int(primary.group('n'))<=5000:
        return False
    if expected_n is not None and expected_n != int(primary.group('n')):
        return False
    if expected_order is not None:
        model_field=fields.get(str(expected_order.get('field','')).strip().casefold())
        written_field=fields[primary.group('field').casefold()]
        directions={'升序':'asc','降序':'desc','asc':'asc','desc':'desc'}
        model_direction=directions.get(str(expected_order.get('direction','')).strip().casefold())
        written_direction=directions[primary.group('direction').casefold()]
        if model_field != written_field or model_direction != written_direction:
            return False
    requested=[fields[primary.group('field').lower()]]
    for clause in clauses[1:]:
        projection=re.fullmatch(r'(?:返回|输出|展示|列出)\s*(?P<fields>'+attr+r'(?:\s*(?:、|和|与|及)\s*'+attr+r')*)',clause,re.I)
        tie=re.fullmatch(r'(?P<same>'+attr+r')\s*相同(?:时)?\s*(?:按|依|根据)\s*(?P<field>'+attr+r')\s*'+direction+r'\s*(?:排序)?',clause,re.I)
        if projection:
            requested.extend(fields[match.group().lower()] for match in re.finditer(attr,projection.group('fields'),re.I))
        elif tie:
            requested.extend([fields[tie.group('same').lower()],fields[tie.group('field').lower()]])
        else:
            return False
    return set(requested)<={column.name for column in table.columns}


def extract_intent(question: str, catalog, llm, trace=None, *, bindings: list[dict] | None = None) -> SemanticIntent:
    region_gate=region_needs_semantic_gate(question,bindings or [],catalog)
    explicit_scope=explicit_region_scope(question) if catalog.database.casefold()=='chinook' else None
    default_scope = ('invoice.billing_country' if region_gate else None)
    if not needs_semantic_model(question):
        # Existing D1/D2 clear lookup questions retain their original fast path.
        measure=None
        if catalog.database.casefold()=='chinook':
            if '客单价' in question or '平均每张发票金额' in question:
                measure='average_invoice_amount'
            elif any(word in question for word in ('销售额','发票金额','账单金额')):
                detail=any(word in question for word in ('曲目','歌曲','艺术家','乐队','专辑','流派','明细')) or any(item.get('column') in {'artist.name','genre.name','album.title','track.name'} for item in bindings or [])
                measure='detail_revenue' if detail else 'invoice_revenue'
            elif re.search(r'(?:发票|账单)(?:张数|数量|次数)',question):
                measure='invoice_count'
        return SemanticIntent(metric=measure,time_scope=explicit_period(question), filters=bindings or [],region_scope=explicit_scope or default_scope)
    prompt = {"question": question, "catalog": catalog.prompt_schema(),
              "verified_value_bindings": bindings or []}
    result = llm.complete_json(PROMPT_PATH.read_text(encoding="utf-8"),
                               json.dumps(prompt, ensure_ascii=False), SemanticIntent, trace=trace)
    result.assumptions=[]
    result.default_assumptions=[]
    # A missing measure is not an undefined record-set reference. A model may
    # request a set only when the user actually used a deictic set expression.
    if not re.search(r'这批|这些|这部分|这组|该批|上述|前面(?:的)?(?:记录|曲目|客户)', question):
        result.scope_missing=False
    if (result.task_type=='ranking' and result.metric is None and
            result.rank_object in {None,'customer','客户','顾客'} and
            result.top_n is not None and result.order is not None and
            explicit_customer_attribute_top(question,catalog,expected_n=result.top_n,expected_order=result.order)):
        # The complete question proves a direct lookup, not a business ranking.
        # Preserve order and N; canonicalize only the named customer object.
        result.task_type='lookup'
        if result.rank_object in {'客户','顾客'}:
            result.rank_object='customer'
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
        result.region_scope=explicit_scope or default_scope
        result.region_ambiguous=False
        if not explicit_scope:
            result.assumptions.append('销售额的地区按发票账单国家统计（10月12日已确认默认口径）。')
    if catalog.database.casefold()=="chinook":
        if explicit_scope:
            result.region_scope=explicit_scope
            result.region_ambiguous=False
        elif result.region_ambiguous:
            result.region_scope = ('invoice.billing_country' if any(word in question for word in ('销售额','发票','账单')) else
                                   'customer.country' if any(word in question for word in ('客户','顾客')) else None)
            result.region_ambiguous = result.region_scope is None
        # Ground familiar, reviewed metric IDs from literal wording. The model
        # cannot turn explicit sales revenue into another missing condition.
        if '客单价' in question:
            result.metric='average_invoice_amount'
        elif '复购' in question:
            result.metric='repeat_customer_count'
        elif any(word in question for word in ('销售额','发票金额','账单金额')):
            result.metric=('detail_revenue' if any(word in question for word in ('曲目','艺术家','歌曲','乐队','明细')) else 'invoice_revenue')
        elif '客户数量' in question or '客户数占比' in question:
            result.metric='customer_count'
        if any(word in question for word in ('占比','比例')):
            result.task_type='ratio'
            if _bare_amount_share(question):
                # In fresh DEV execution the model invented "2023年销售额"
                # as numerator of an unspecified share, then returned 100%.
                # The approved same-period denominator does not authorize
                # guessing a numerator; ask the missing scope instead.
                result.numerator=None
                result.evidence_spans.pop('numerator',None)
            # A country before “销售额占比” is an explicitly written numerator,
            # not evidence to filter both numerator and denominator globally.
            marker = re.search(r'(?:销售额|发票金额|账单金额)(?:的)?(?:占比|比例)',question)
            if marker and any(item.get('column') in {'invoice.billing_country','customer.country'} for item in bindings or []):
                prefix=question[:marker.end()].strip(' ，,。？?')
                if not any(word in question[:marker.start()] for word in ('分母','除以')):
                    result.numerator=prefix
        popularity=any(word in question for word in ("最受欢迎","最热门","最火","热门曲目","热门歌曲","卖得最好"))
        explicit_measure=any(word in question for word in ("购买数量","销量","销售额","金额","歌单","收录","quantity","revenue"))
        if popularity and result.rank_object=="track" and not explicit_measure:
            result.metric=None
        if any(word in question for word in ("谁买得最多","买得最多的客户")) and not explicit_measure:
            result.metric=None
        if (result.rank_object=="customer" and not any(word in question for word in ("客户","顾客","customer")) and
                '谁买得最多' not in question):
            result.rank_object=None
    # The calendar conversion is programmatic whenever the user wrote one period.
    period = explicit_period(question) or explicit_comparison_period(question,(result.comparison or {}).get('type'))
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
