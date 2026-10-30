"""Grounded decisions, with only explicitly authorized business defaults."""
from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field,field_validator,PrivateAttr
import yaml
from qa_agent.clarify.normalization import normalize_internal_contract,validate_scope_structure
from qa_agent.clarify.conflict_contract import ConflictProposal

RULES_PATH = Path(__file__).with_name("clarify_rules.yaml")


class SemanticIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Transient program audit, never model output or an execution-contract field.
    _retired_conflict_proposals: list[dict[str, Any]] = PrivateAttr(default_factory=list)
    _program_conflict_records: list[dict[str, Any]] = PrivateAttr(default_factory=list)
    _conflict_input_audit: list[dict[str, Any]] = PrivateAttr(default_factory=list)
    _conflicts_projected: bool = PrivateAttr(default=False)
    task_type: Literal["lookup", "aggregation", "growth", "ratio", "ranking"] = "lookup"
    metric: str | None = None
    time_scope: dict[str, Any] | None = None
    comparison: dict[str, Any] | None = None
    numerator: str | None = None
    denominator: str | None = None
    rank_object: str | None = None
    top_n: int | None = Field(default=None, ge=1, le=5000)
    order: dict[str, Any] | None = None
    region_scope: Literal["invoice.billing_country", "customer.country"] | None = None
    region_ambiguous: bool = False
    scope_missing: bool = False
    time_ambiguous: bool = False
    conflicts: list[str] = Field(default_factory=list)
    conflict_proposals: list[ConflictProposal] = Field(default_factory=list,exclude=True)
    grouping: list[str] = Field(default_factory=list)
    filters: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    default_assumptions: list[str] = Field(default_factory=list)
    evidence_spans: dict[str, str] = Field(default_factory=dict)
    # Internal semantic contract; shared request/response models stay stable.
    query_scope: dict[str, Any] = Field(default_factory=dict,json_schema_extra={'properties':{
        'partition_by':{'type':'array','items':{'type':'string'}},
        'qualification_filters':{'type':'array','items':{'type':'object'}},
        'pending_filters':{'type':'array','items':{'type':'object'}},
        'numerator':{'anyOf':[{'type':'object','properties':{'filters':{'type':'array','items':{'type':'object'}}}},{'type':'null'}]},
        'denominator':{'anyOf':[{'type':'object','properties':{'filters':{'type':'array','items':{'type':'object'}}}},{'type':'null'}]}}})
    output_requirements: list[str] = Field(default_factory=list)
    condition_sources: dict[str, dict[str, Any]] = Field(default_factory=dict)
    clarification_requests: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator('query_scope',mode='before')
    @classmethod
    def validate_query_scope(cls,value):
        return validate_scope_structure(value)


class IntentExtractionResponse(SemanticIntent):
    """Fresh model wire: free prose is not a program conflict projection."""
    conflicts:list[str]=Field(default_factory=list,max_length=0)


@dataclass
class ClarificationIssue:
    id: str
    question: str
    reason: str
    field: str
    options: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self, *, public: bool = False) -> dict:
        result = dict(self.__dict__)
        if public:
            result['options']=[{key:value for key,value in option.items() if key!='patch'} for option in self.options]
        return result


@dataclass
class RuleDecision:
    level: Literal["L0", "L1", "L2"]
    analysis: SemanticIntent
    issues: list[ClarificationIssue] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    switches: list[dict[str, Any]] = field(default_factory=list)
    derived: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"level": self.level, "analysis": self.analysis.model_dump(),
                "issues": [item.as_dict() for item in self.issues],
                "assumptions": self.assumptions, "switches": self.switches,
                "derived": self.derived}


def explicit_period(question: str) -> dict | None:
    """Parse an explicitly written year/month, not a complete-year assumption."""
    from qa_agent.clarify.calendar_range import parse_calendar_range
    is_range, period = parse_calendar_range(question)
    if is_range:
        return period
    dates=list(re.finditer(r"(?<!\d)(\d{4})\s*(?:年|-)\s*(\d+)\s*(?:月|-)\s*(\d+)(?!\d)\s*(?:日)?",question))
    if dates:
        try:
            values=[date(*map(int,match.groups())) for match in dates]
            if len(dates)==1:
                prefix=question[:dates[0].start()]
                suffix=question[dates[0].end():]
                before_prefix=re.search(r"(?<![不未])(?:早于|小于)\s*$",prefix)
                before_suffix=re.match(r"\s*之前",suffix)
                # Only a literal strict-before date is proven. Inclusive,
                # negated, later-than and shifted-day expressions are left
                # unparsed rather than downgraded to a day/month window.
                operator_prefix=re.split(r"[，,；;。？！?!]",prefix)[-1]
                operator_suffix=re.split(r"[，,；;。？！?!]",suffix)[0]
                # Only negation attached to the date relation affects its
                # direction; “未支付且早于...” still names a strict date bound.
                negated=bool(re.search(r"(?:不|未|非|不是|并非|不要(?:查询|列出|查)?|禁止(?:查询|列出|查)?|别(?:查询|列出|查)?)(?:严格)?(?:早于|小于)\s*$",prefix) or
                             before_suffix and re.search(r"(?:不|未|非|不是|并非|不要(?:查询|列出|查)?|禁止(?:查询|列出|查)?|别(?:查询|列出|查)?)(?:在)?\s*$",prefix))
                clock_or_zone=bool(re.match(r"\s*(?:日\s*)?(?:T\s*)?(?:\d{1,2}(?::\d{2}|\s*[点时])|上午|下午|中午|凌晨|午夜|晚上)",suffix,re.I) or
                                   re.search(r"UTC|GMT|北京时间|时区",operator_prefix+operator_suffix,re.I))
                temporal_qualifier=bool(clock_or_zone or re.match(r"\s*(?:的)?(?:次日|翌日|第二天|前一天)|\s*[（(]\s*(?:含|包含|包括)",suffix))
                relation_prefix=bool(re.search(r"(?:早于|小于|晚于|大于|(?:早于|小于)(?:或)?等于|<=|≤)\s*$",prefix))
                relation_suffix=bool(re.match(r"\s*(?:(?:并非|不是|不|未)\s*)?(?:之前|之后|以前|以后|及之前|当天及之前|当日及之前)",suffix))
                date_relation=bool(relation_prefix or relation_suffix or
                                   temporal_qualifier and re.search(r"之前|早于|小于|之后|晚于|大于",operator_suffix))
                # Ordinary day lookups may have unrelated amount comparisons
                # or unpaid predicates; those do not modify the calendar day.
                if date_relation:
                    unsupported=bool(negated or clock_or_zone or re.search(r"次日|翌日|第二天|前一天|含(?:当天|当日|该日|边界)|包含(?:当天|当日|该日|边界)|包括(?:当天|当日|该日|边界)|或等于|或当天|或当日|<=|≤",operator_prefix+operator_suffix))
                    if unsupported or not (before_prefix or before_suffix):
                        return None
                    label_start=before_prefix.start() if before_prefix else dates[0].start()
                    label_end=dates[0].end()+before_suffix.end() if before_suffix else dates[0].end()
                    return {"current":{"end":values[0].isoformat(),"grain":"before",
                                       "label":question[label_start:label_end].strip()}}
                start,end=values[0],values[0]+timedelta(days=1)
            elif len(dates)==2 and re.search(r"到|至|—|~|～",question[dates[0].end():dates[1].start()]):
                start=values[0]
                exclusive=bool(re.search(r"不含|之前|小于",question[max(0,dates[1].start()-8):dates[1].end()+8]))
                end=values[1] if exclusive else values[1]+timedelta(days=1)
            else:
                return None
            if start>=end:return None
            return {"current":{"start":start.isoformat(),"end":end.isoformat(),"grain":"custom",
                               "label":question[dates[0].start():dates[-1].end()]}}
        except (ValueError,OverflowError):
            return None
    months = re.findall(r"(?<!\d)(\d{4})\s*年\s*(\d{1,2})\s*月", question)
    if len(months) == 1:
        year, month = map(int, months[0])
        if not 1 <= month <= 12 or not 1 <= year < 9999:
            return None
        start = date(year, month, 1)
        end = date(year + (month == 12), month % 12 + 1, 1)
        return {"current": {"start": start.isoformat(), "end": end.isoformat(),
                            "label": f"{year}年{month}月", "grain": "month"}}
    if len(months)>1:
        return None
    quarter=re.search(r"(?<!\d)(\d{4})\s*年\s*第?([一二三四1-4])\s*季度",question)
    if quarter:
        year=int(quarter.group(1));number={'一':1,'二':2,'三':3,'四':4}.get(quarter.group(2),int(quarter.group(2)) if quarter.group(2).isdigit() else 0)
        if not 1<=year<9999:return None
        month=(number-1)*3+1
        return {'current':{'start':date(year,month,1).isoformat(),
                           'end':date(year+(number==4),month+3 if number<4 else 1,1).isoformat(),
                           'grain':'quarter','label':quarter.group(0)}}
    # Partial sub-year expressions must be left for grounded structured parsing.
    if re.search(r"\d{4}\s*年.*?(?:月|日|季度|半年|周)",question):
        return None
    years = re.findall(r"(?<!\d)(\d{4})\s*年", question)
    distinct_years=sorted({int(value) for value in years})
    if (len(distinct_years)==2 and distinct_years[1]-distinct_years[0]==1 and
            any(word in question for word in ('每年','分别','按年','逐年')) and
            not any(word in question for word in ('同比','环比','相比','比较','增长','增幅','相对','对比'))):
        first,last=distinct_years
        if 1<=first<last<9999:
            return {'current':{'start':f'{first:04d}-01-01','end':f'{last+1:04d}-01-01',
                               'grain':'multi_year','label':f'{first}年和{last}年'},'years':distinct_years}
    if len(set(years)) == 1:
        year = int(years[0])
        if year < 1 or year >= 9999:
            return None
        return {"current": {"start": f"{year:04d}-01-01", "end": f"{year+1:04d}-01-01",
                            "label": f"{year}年", "grain": "year"}}
    return None


def explicit_comparison_period(question: str, comparison_type: str | None) -> dict | None:
    """Current year is the first written year in an explicit comparison.

    “2024年，和2023年比” names two roles rather than a two-year total. It is
    converted only when the comparison wording and both calendar years exist.
    """
    if not re.search(r'同比|环比|相比|比较|对比|比[。？?，,\s]*$',question):
        return None
    if re.search(r'\d{4}\s*年\s*(?:\d{1,2}\s*月|第?.{1,2}季度|[上下]半年)',question):
        return None
    years=re.findall(r'(?<!\d)(\d{4})\s*年',question)
    if len(years)!=2 or years[0]==years[1] or not all(1<=int(value)<9999 for value in years):
        return None
    first_year=re.search(r'(?<!\d)\d{4}\s*年',question)
    if first_year and re.search(r'相比|相对|对比|基期|基准',question[:first_year.start()]):
        return None
    current=explicit_period(years[0]+'年')
    base=explicit_period(years[1]+'年')
    if current and base:
        return {**current,'base':base['current']}
    return None


def _literal_quarter_comparison(question: str) -> tuple[dict, dict] | None:
    """Two written quarters in current-then-base order, never a model alias."""
    matches = list(re.finditer(r'(?<!\d)\d{4}\s*年\s*第?[一二三四1-4]\s*季度', question))
    if len(matches) != 2 or not re.search(r'增长|增幅|变动|变化|百分|同比|环比', question):
        return None
    first, second = matches
    between = question[first.end():second.start()]
    if not re.search(r'(?:比|相比(?:于)?|相对(?:于)?|较)\s*$', between):
        return None
    remaining = question[:first.start()] + between + question[second.end():]
    if re.search(r'\d{4}\s*年|\d{1,2}\s*月|季度|[上下]半年|前年|去年|今年|明年|或者|或是|还是', remaining):
        return None
    if '同比' in question and '环比' in question:
        return None
    for match in matches:
        sentence_prefix = re.split(r'[。；;\n？！!?]', question[:match.start()])[-1]
        prefix = re.split(r'[，,]', sentence_prefix)[-1]
        if (re.search(r'例如|比如|示例|假设|不确定|可能', sentence_prefix)
                or re.search(r'不要|不按|不是|并非', prefix)):
            return None
    current = explicit_period(first.group())
    base = explicit_period(second.group())
    if current and base:
        return current['current'], base['current']
    return None


def derive_base(current: dict, comparison: str) -> dict | None:
    try:
        start, end = date.fromisoformat(current["start"]), date.fromisoformat(current["end"])
    except (KeyError, TypeError, ValueError):
        return None
    if start.year <= 1 or end.year <= 1:
        return None
    if comparison == "yoy":
        def shifted(value):
            return date(value.year - 1, value.month, min(value.day, monthrange(value.year-1, value.month)[1]))
        return {"start": shifted(start).isoformat(), "end": shifted(end).isoformat(),
                "derived_from": "explicit current period and yoy"}
    if comparison == "mom" and current.get("grain") == "month":
        def shifted(value):
            month = value.month - 1 or 12
            year = value.year - (value.month == 1)
            return date(year, month, min(value.day, monthrange(year, month)[1]))
        return {"start": shifted(start).isoformat(), "end": shifted(end).isoformat(),
                "derived_from": "explicit current month and mom"}
    return None


class RuleEngine:
    def __init__(self, path: Path = RULES_PATH):
        self.rules = yaml.safe_load(path.read_text(encoding="utf-8"))

    def evaluate(self, question: str, analysis: SemanticIntent, *,
                 ambiguous: list[dict] | None = None,
                 available_years: list[int] | None = None,
                 db_id: str = "chinook") -> RuleDecision:
        analysis = analysis.model_copy(deep=True)
        from qa_agent.clarify.conflict_authority import adjudicate_conflict_proposals
        from qa_agent.clarify.grounding import runtime_payload
        adjudicate_conflict_proposals(question,analysis,runtime_payload())
        from qa_agent.clarify.denominator_authority import PENDING_DENOMINATOR
        if analysis.denominator:
            analysis.assumptions=[text for text in analysis.assumptions if text!=PENDING_DENOMINATOR]
        normalize_internal_contract(analysis,question)
        from qa_agent.nlu.features import enabled
        if enabled('AGENT_GROUNDING_ENABLED'):
            from qa_agent.clarify.applicability import normalize_assignment_period
            normalize_assignment_period(question,analysis)
        issues: list[ClarificationIssue] = []
        assumptions = list(analysis.assumptions)
        defaults = list(analysis.default_assumptions)
        switches: list[dict] = []
        derived: dict = {}
        written_quarters = (_literal_quarter_comparison(question)
            if db_id == 'chinook' and analysis.task_type == 'growth' and enabled('AGENT_GROUNDING_ENABLED') else None)
        if written_quarters:
            written_current, written_base = written_quarters
            analysis.time_scope = {'current': written_current, 'base': written_base}
            analysis.time_ambiguous = False
            analysis.comparison = dict(analysis.comparison or {})
            analysis.comparison.pop('base_period', None)
            analysis.comparison['type'] = ('yoy' if '同比' in question else 'mom' if '环比' in question else 'custom')
            for path, period in (('time_scope', written_current), ('time_scope.base', written_base)):
                analysis.condition_sources[path] = {'source': 'explicit_user', 'evidence': period['label'],
                    'lifetime': 'task', 'applies_to': 'global', 'verified': True}
            analysis.evidence_spans['time_scope.current'] = written_current['label']
            analysis.evidence_spans['time_scope.base'] = written_base['label']
            analysis.clarification_requests = [item for item in analysis.clarification_requests
                if item.get('field') not in {'time_scope.current', 'time_scope.base', 'comparison.type'}]
        current = (analysis.time_scope or {}).get("current")

        if db_id == 'chinook':
            # The Oct 12 task explicitly replaces the older missing-object rule
            # for this phrase. It does not replace an already named object.
            if ('谁买得最多' in question and analysis.task_type not in {'growth','ratio'} and
                    analysis.rank_object is None and not any(word in question for word in ('曲目','歌曲','艺术家','乐队','专辑','流派'))):
                analysis.task_type='ranking'
                analysis.rank_object='customer'
                note='“谁买得最多”默认查询客户消费金额排名（10月12日已确认）。'
                assumptions.append(note)
                defaults.append(note)
                derived['rank_object']={'source':'oct12_approved_default','value':'customer'}
            if analysis.region_ambiguous and analysis.region_scope is None:
                if analysis.metric in {'invoice_revenue','average_invoice_amount'} or any(word in question for word in ('销售额','发票','账单')):
                    analysis.region_scope='invoice.billing_country'
                elif analysis.metric in {'customer_count','repeat_customer_count'} or analysis.rank_object=='customer':
                    analysis.region_scope='customer.country'
                if analysis.region_scope:
                    analysis.region_ambiguous=False
                    derived['region_scope']={'source':'oct12_approved_default','value':analysis.region_scope}
            if (analysis.task_type=='ratio' and analysis.metric=='invoice_revenue' and not analysis.denominator
                    and PENDING_DENOMINATOR not in analysis.assumptions):
                analysis.denominator='同期全部发票金额（SUM(invoice.total)，分母不加分子地区筛选）'
                note='销售额占比默认以同期全部发票金额作分母（10月12日已确认）。'
                assumptions.append(note)
                defaults.append(note)
                derived['denominator']={'source':'oct12_approved_default','scope':'all_invoices_same_period',
                                        'metric':'invoice_revenue'}
                analysis.query_scope['denominator']={'metric':'invoice_revenue','scope':'all_invoices_same_period',
                    'filters':[dict(item) for item in analysis.filters if item.get('binding_scope') in {None,'global'}]}
                if current:
                    analysis.query_scope['denominator']['period']={key:current[key] for key in ('start','end') if key in current}

        for mention in ambiguous or []:
            candidates = mention.get("candidates", [])
            options = []
            for candidate in candidates:
                cid = str(candidate.get("candidate_id", candidate.get("id", "")))
                value = candidate.get("standard_value", candidate.get("canonical_value", candidate.get("value")))
                column = candidate.get("column")
                if cid and value is not None and column:
                    options.append({"id": "value:" + str(mention["mention_id"]) + ":" + cid,
                                    "label": f"{value}（{column}）",
                                    "patch": {"op": "resolve_value", "mention_id": mention["mention_id"],
                                              "candidate_id": cid, "column": column, "value": value}})
            issues.append(ClarificationIssue(
                "value:" + str(mention["mention_id"]),
                f"“{mention.get('original_text', '')}”具体指哪个对象？",
                "这个说法可能对应不同对象，请选择本次要查询的对象。", "filters", options))

        if analysis.conflicts:
            from qa_agent.clarify.conflict_authority import conflict_review_label
            options=[{'id':'reject_conflict:'+record['record_id'],
                'label':conflict_review_label(record,index),
                'review_hint':record.get('review_hint')or{'status':'not_verified'},
                'not_authoritative':True,
                'patch':{'op':'reject_conflict','record_id':record['record_id']}}
                for index,record in enumerate([record for record in analysis._program_conflict_records if record['status']=='unknown'])]
            issues.append(ClarificationIssue("conflicting_conditions", "请说明具体冲突条件，或拒绝不适用的候选歧义。",
                                             "；".join(analysis.conflicts), "conflicts",options))
        if analysis.scope_missing:
            issues.append(ClarificationIssue("missing:reference_scope", "“这批/这些”具体指哪些记录？",
                                             "当前会话没有这批记录的范围依据，不能擅自按全库统计。", "scope_missing"))
        if analysis.time_ambiguous:
            options=[{"id":"year:"+str(year),"label":f"{year}年（该年有数据，不代表完整年度）",
                      "patch":{"op":"set","path":"time_scope","value":explicit_period(f"{year}年")}}
                     for year in sorted(set(available_years or []))]
            issues.append(ClarificationIssue("ambiguous:time_scope", "请明确具体统计期间。",
                                             "目录中的最大日期或年份不能证明完整年度；不猜未说明的日期。", "time_scope.current",options))
        if analysis.region_ambiguous and analysis.region_scope is None:
            scope_rule = next(item for item in self.rules["ambiguities"] if item["id"] == "invoice_country_scope")
            options = [{"id": item["id"], "label": item["label"],
                        "patch": {"op": "set", "path": "region_scope", "value": item["column"]}}
                       for item in scope_rule["options"]]
            issues.append(ClarificationIssue("region_scope", "国家按客户所在地还是发票账单国家？",
                                             "这两个字段业务含义不同，不能因当前结果相同而合并。", "region_scope", options))

        popularity = next(item for item in self.rules["ambiguities"] if item["id"] == "popularity")
        is_popular = (db_id == "chinook" and analysis.rank_object == "track" and
                      any(word in question for word in popularity["trigger"]))
        if is_popular and analysis.metric is None and analysis.task_type not in {"growth", "ratio"}:
            default = next(item for item in popularity["options"] if item["id"] == popularity["default"])
            analysis.metric = default["metric"]
            default_note="热门曲目按购买数量统计（已确认默认口径）。"
            assumptions.append(default_note)
            defaults.append(default_note)
        if is_popular and analysis.task_type not in {"growth","ratio"} and analysis.metric in {item['metric'] for item in popularity['options']}:
            switches = [{"id": item["id"], "label": item["label"],
                         "patch": {"op": "set", "path": "metric", "value": item["metric"]}}
                        for item in popularity["options"]]
        customer_default = next(item for item in self.rules["ambiguities"] if item["id"] == "customer_purchase_ranking")
        if (db_id == "chinook" and analysis.rank_object == "customer" and analysis.metric is None and
            analysis.task_type == "ranking" and any(word in question for word in customer_default["trigger"])):
            analysis.metric = "invoice_revenue"
            default_note="“客户谁买得最多”按发票金额统计（已确认对象专属口径）。"
            assumptions.append(default_note)
            defaults.append(default_note)

        all_data_allowed=(db_id=='chinook' and analysis.task_type not in {'growth','ratio'} and
                          ((is_popular and analysis.metric!='playlist_memberships') or
                           analysis.metric=='repeat_customer_count' or
                           analysis.task_type=='ranking' and analysis.rank_object=='customer'))
        if all_data_allowed and not current and not (analysis.time_scope or {}).get('all_data') and not analysis.time_ambiguous:
            # No synthetic calendar boundaries: use all rows in the existing DB.
            # An explicitly established period stays in current and is untouched.
            analysis.time_scope={'all_data':True,'label':'全部现有数据'}
            note='未指定期间，按全部现有数据统计（10月12日已确认）；已确认的会话期间继续保留。'
            assumptions.append(note)
            defaults.append(note)
            derived['time_scope']={'source':'oct12_approved_default','scope':'all_existing_data',
                                   'available_years':sorted(set(available_years or []))}

        # Resolve known policy defaults before deciding whether a precise
        # backend slot still needs human input. Free model field names never
        # become independent, permanently unfulfillable conditions.
        from qa_agent.nlu.features import enabled
        if enabled('AGENT_GROUNDING_ENABLED'):
            normalize_internal_contract(analysis,question)
            for requested in analysis.clarification_requests:
                path=requested['field']
                present={'metric':analysis.metric,'time_scope.current':current if not analysis.time_ambiguous else None,
                         'average_grain':analysis.query_scope.get('average_grain'),
                         'query_scope.rank_metric':analysis.query_scope.get('rank_metric'),
                         'filters':bool(analysis.filters) and not analysis.query_scope.get('pending_filters'),
                         'numerator':analysis.numerator,'denominator':analysis.denominator,
                         'rank_object':analysis.rank_object,'region_scope':analysis.region_scope,
                         'comparison.type':(analysis.comparison or {}).get('type')}.get(path)
                if present:
                    continue
                issues=[issue for issue in issues if issue.field!=path]
                issues.append(ClarificationIssue('grounded:'+path,str(requested.get('question') or '请明确该条件。'),
                                                str(requested.get('reason') or '没有足够依据选择。'),path))

        required = self.rules["task_types"].get(analysis.task_type, {}).get("required", [])
        paths = {"metric": analysis.metric, "time_scope.current": current,
                 "comparison.type": (analysis.comparison or {}).get("type"),
                 "numerator": analysis.numerator, "denominator": analysis.denominator,
                 "rank_object": analysis.rank_object}
        labels = {"metric": "要计算的指标", "time_scope.current": "当前比较期间", "comparison.type": "同比还是环比",
                  "numerator": "分子范围", "denominator": "分母范围", "rank_object": "排名对象"}
        for path in required:
            if not paths[path]:
                # A relative/missing current period is one issue, not two cards
                # asking for the same year through separate grammar rules.
                if any(item.field==path for item in issues):
                    continue
                options = []
                if path == "time_scope.current":
                    options = [{"id": "year:" + str(year), "label": f"{year}年（该年有数据，不代表完整年度）",
                                "patch": {"op": "set", "path": "time_scope",
                                          "value": explicit_period(f"{year}年")}}
                               for year in sorted(set(available_years or []))]
                elif path == "comparison.type":
                    options = [{"id": "yoy", "label": "同比（与上年同期间）",
                                "patch": {"op": "set", "path": "comparison", "value": {"type": "yoy"}}},
                               {"id": "mom", "label": "环比（与上月，仅适用于明确月份）",
                                "patch": {"op": "set", "path": "comparison", "value": {"type": "mom"}}}]
                issues.append(ClarificationIssue("missing:" + path, f"请明确{labels[path]}。",
                                                 "该任务缺少必需条件，未登记可直接代填的默认值。", path, options))
        if analysis.metric == "playlist_memberships" and current:
            issues.append(ClarificationIssue(
                "unsupported:playlist_period", "歌单收录快照没有收录日期，是否明确取消期间约束？",
                "不能把发票日期冒充歌单收录日期；也可切回购买数量或销售额。", "time_scope.current",
                [{"id": "playlist_snapshot", "label": "取消期间，只统计当前歌单收录快照",
                  "patch": {"op": "set", "path": "time_scope", "value": None}},
                 {"id": "by_quantity", "label": "保留期间，按购买数量",
                  "patch": {"op": "set", "path": "metric", "value": "purchased_quantity"}},
                 {"id": "by_revenue", "label": "保留期间，按销售额",
                  "patch": {"op": "set", "path": "metric", "value": "detail_revenue"}}]))
        if analysis.task_type == "ranking" and analysis.top_n is None:
            analysis.top_n = int(self.rules["task_types"]["ranking"]["defaults"]["top_n"])
            default_note="未指定排名条数，按总计划规则展示前 10 名。"
            assumptions.append(default_note)
            defaults.append(default_note)
        if analysis.task_type == "growth" and current and (analysis.comparison or {}).get("type"):
            comp_type = analysis.comparison["type"]
            explicit_base=(analysis.time_scope or {}).get("base")
            derived_base=derive_base(current,comp_type)
            base = explicit_base or derived_base
            if explicit_base and derived_base and any(explicit_base.get(key)!=derived_base.get(key) for key in ('start','end')):
                issues.append(ClarificationIssue('conflicting:comparison_period','当前基期与同比/环比规则冲突，请确认比较方式。',
                                                 '不能把跨两年的比较标成同比，也不能擅自替换用户明确的基期。','comparison'))
            if base:
                analysis.time_scope = {**(analysis.time_scope or {}), "base": base}
                derived["time_scope.base"] = base
            elif not any(item.field == "time_scope.current" for item in issues):
                issues.append(ClarificationIssue("missing:base_period", "请明确基期，或提供适用比较规则的当前月份。",
                                                 "当前范围无法唯一推导比较基期。", "time_scope.base"))
        analysis.assumptions = list(dict.fromkeys(assumptions))
        analysis.default_assumptions = list(dict.fromkeys(defaults))
        from qa_agent.clarify.switches import approved_default_switches
        switches += approved_default_switches(analysis)
        level = "L2" if issues else "L1" if defaults else "L0"
        return RuleDecision(level, analysis, issues, analysis.assumptions, switches, derived)
