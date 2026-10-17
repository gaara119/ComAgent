"""Ground semantic proposals in real user text, schema and request context.

The program owns precedence and provenance. These checks are not confidence
estimates, and no test identifier, expected answer or result is consulted.
"""
from __future__ import annotations

from datetime import date, datetime
import re
from zoneinfo import ZoneInfo

from qa_agent.nlu.features import enabled
from qa_agent.clarify.normalization import normalize_internal_contract, normalize_ranked_output,normalize_scope_collections
from qa_agent.clarify.policy import CUSTOMER_AMOUNT
from qa_agent.clarify.scope_contract import explicit_ranked_ratio_subject,partition_named_comparison


def scope_local_qualification_mirrors(analysis, proved_local: list[dict]) -> None:
    """Keep model qualification mirrors in their program-proved operand scope.

    Called only after literal operand reconstruction. Independent predicates,
    explicit other scopes and unrelated source quotes remain untouched.
    """
    def identity(item):
        return (item.get('column', item.get('field')), str(item.get('operator', '')).upper(), item.get('value'))
    for mirror in analysis.query_scope.get('qualification_filters', []):
        if mirror.get('binding_scope') is not None:
            continue
        matches = [item for item in proved_local if item.get('binding_scope') in {'numerator', 'denominator'}
                   and identity(item) == identity(mirror)
                   and (not mirror.get('scope_evidence') or mirror.get('scope_evidence') == item.get('scope_evidence'))]
        if len({item['binding_scope'] for item in matches}) == 1:
            mirror['binding_scope'] = matches[0]['binding_scope']


def runtime_payload() -> dict:
    # Import lazily to retain compatibility with offline/module users.
    try:
        from qa_agent.context import current_context
    except ImportError:
        return {}
    context = current_context()
    return context.prompt_payload() if context is not None else {}


def literal_relative_period(question: str, payload: dict | None = None) -> dict | None:
    """Resolve a named relative calendar year against one injected clock.

    An explicit conflicting definition in a user brief is left to the full
    grounded parser. "最近" is intentionally not a calendar-year synonym.
    """
    payload = payload or runtime_payload()
    match = re.search(r"前年|去年|今年|明年", question)
    if not match or not payload.get("reference_datetime"):
        return None
    brief = str(payload.get("user_brief") or "")
    if re.search(r"[‘“\"']?" + re.escape(match.group()) + r"[’”\"']?.{0,12}(?:指|不指|理解|为)", brief):
        return None
    try:
        moment = datetime.fromisoformat(str(payload["reference_datetime"]).replace("Z", "+00:00"))
        if moment.tzinfo is None:
            return None
        zone = payload.get("timezone")
        if zone:
            moment = moment.astimezone(ZoneInfo(zone))
        year = moment.year + {"前年": -2, "去年": -1, "今年": 0, "明年": 1}[match.group()]
        if not 1 <= year < 9999:
            return None
    except (ValueError, TypeError, KeyError):
        return None
    return {"current": {"start": f"{year:04d}-01-01", "end": f"{year+1:04d}-01-01",
                        "grain": "year", "label": match.group(),
                        "reference_datetime": payload["reference_datetime"],
                        "timezone": payload.get("timezone")}}


def literal_sales_context(question: str) -> bool:
    return bool(re.search(r"(?:卖出|卖了|售出|售卖|销售|售出过).{0,14}(?:曲目|歌曲|首)|(?:曲目|歌曲).{0,14}(?:卖出|售出|销售)", question))


def explicit_average_metric(question: str) -> tuple[str,str] | None:
    found=[]
    patterns={'average_customer_amount':r'平均每(?:位|个|名)客户(?:的)?(?:消费|金额)?|按客户(?:算|平均)|每(?:位|个|名)客户(?:的)?平均',
              'average_invoice_amount':r'平均每张(?:发票|账单)(?:的)?(?:金额)?|按(?:发票|账单|张)(?:算|平均)|每张(?:发票|账单)(?:的)?平均|客单价'}
    for metric,pattern in patterns.items():
        for match in re.finditer(pattern,question):
            if not re.search(r'不是|并非|不(?:要|按)?\s*$',question[max(0,match.start()-6):match.start()]):
                found.append((metric,match.group()))
    return found[0] if len({metric for metric,_ in found})==1 else None


def confirmed_average_from_history(payload: dict):
    pending=False;confirmed=None
    for turn in payload.get('actual_conversation',[]):
        if not isinstance(turn,dict):
            continue
        user=str(turn.get('user') or '')
        if re.search(r'(?:取消|撤销|重新定义).{0,8}(?:人均|平均口径|平均粒度)',user):
            confirmed=None
        average=explicit_average_metric(user)
        persistent=bool(re.search(r'人均|以后|后面|默认|整个会话',user))
        if average and (pending or persistent):
            confirmed=(average[0],user)
            pending=False
        card=turn.get('clarification') or {}
        if card and (re.search(r'人均|平均.*(?:客户|发票)|粒度',str(card.get('question') or '')) or
                     any(str(item.get('field')) in {'average_grain','metric'} for item in card.get('issues',[])) and re.search('人均|平均消费',user)):
            pending=True
    return confirmed


def confirmed_history_period(payload: dict, evidence: str, period: dict | None) -> bool:
    current=(period or {}).get('current') or {}
    if not evidence or not current:
        return False
    history=payload.get('actual_conversation',[])
    for index,turn in enumerate(history):
        if not isinstance(turn,dict) or evidence not in str(turn.get('user') or ''):
            continue
        previous=((turn.get('intent') or {}).get('time_scope') or {}).get('current') or {}
        if not previous or any(previous.get(key)!=current.get(key) for key in ('start','end')):
            continue
        later='\n'.join(str(item.get('user') or '') for item in history[index+1:] if isinstance(item,dict))
        if re.search(r'(?:去掉|取消|删除|不限).{0,8}(?:时间|期间|年份)|(?:时间|期间|年份).{0,8}(?:去掉|取消|不限)',later):
            return False
        return True
    return False


def partial_calendar_period(message: str, established: dict | None) -> dict | None:
    """A literal month/day range can reuse one already confirmed calendar year."""
    from qa_agent.clarify.calendar_range import parse_calendar_range
    is_range, period = parse_calendar_range(message, established)
    if is_range:
        return period
    current=(established or {}).get('current') or {}
    try:
        year=date.fromisoformat(current['start']).year
    except (KeyError,ValueError,TypeError):
        return None
    match=re.search(r'(?<!\d)(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(?:到|至|—|~|～)\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*(之前|不含(?:当天)?|含(?:当天)?)?',message)
    if not match or re.search(r'\d{4}\s*年',message):
        return None
    try:
        start=date(year,int(match.group(1)),int(match.group(2)))
        end=date(year,int(match.group(3)),int(match.group(4)))
        if match.group(5) and match.group(5).startswith('含'):
            from datetime import timedelta
            end+=timedelta(days=1)
        elif not match.group(5):
            return None  # Never guess whether an unqualified end is inclusive.
        if start>=end:
            return None
    except (ValueError,OverflowError):
        return None
    return {'current':{'start':start.isoformat(),'end':end.isoformat(),'grain':'custom','label':match.group(),
                       'year_source':'previous_confirmed_period'}}


def schema_columns(catalog) -> set[str]:
    return {f"{table.name}.{column.name}" for table in catalog.tables for column in table.columns}


def context_filter_is_active(binding: dict, question: str, payload: dict) -> bool:
    evidence=str(binding.get('scope_evidence') or binding.get('evidence') or '')
    named=re.search(r'[“\"‘]([^”\"’]{2,24})[”\"’]\s*[:：]',evidence)
    if named:
        from qa_agent.clarify.definition_recovery import label_is_retired
        if label_is_retired(named.group(1),question):return False
    if re.search(r'(?:本会话|整个会话|全程|以后|接下来所有).{0,12}(?:只查|限定|仅限|都按|都查|只看)',evidence):
        return True
    label=re.search(r'[“\"‘]([^”\"’]{2,24})[”\"’]\s*[:：]',evidence)
    if label:
        term=label.group(1)
        from qa_agent.nlu.value_index import pinyin_key
        if term in question or pinyin_key(term) in re.sub(r'[^a-z]','',question.casefold()):
            return True
        if '市场' in term and re.search(r'市场|market|shi\s*chang',question,re.I):
            return True
    if binding.get('column') in {'invoice.billing_country','customer.country','employee.country'}:
        if re.search(r'重点市场|非重点市场|market|shi\s*chang|(?:这|那|各|每).{0,4}(?:国|国家|市场)',question,re.I):
            return True
        if re.search(r'(?:这些|这批|刚才的).{0,4}客户',question):
            history=payload.get('actual_conversation',[])
            if history:
                last=(history[-1].get('intent') or {}) if isinstance(history[-1],dict) else {}
                if any(item.get('column')==binding.get('column') and item.get('value')==binding.get('value') for item in last.get('filters',[])):
                    return True
        return False
    # A persistent definition of an entity/threshold does not activate its
    # restriction globally. Current wording must reference that definition.
    return bool(label and label.group(1) in question)


def contextual_filters(proposed: list[dict], payload: dict, catalog, *, question: str | None = None) -> list[dict]:
    """Admit context-only filter literals only with verifiable source text.

    They remain user-session instructions, never promoted to an approved
    business policy. Canonical countries/entities supplied as literal values
    must occur verbatim in the full user brief or actual user turns.
    """
    corpus = str(payload.get("user_brief") or "") + "\n" + "\n".join(
        str(turn.get("user") or "") for turn in payload.get("actual_conversation", []) if isinstance(turn, dict))
    columns = schema_columns(catalog)
    grounded = []
    for item in proposed:
        if not isinstance(item, dict) or item.get("column") not in columns:
            continue
        if item.get("operator") not in {"=", "!=", "IN", "NOT IN", ">", ">=", "<", "<=", "IS NOT NULL", "IS NULL"}:
            continue
        values = item.get("value") if isinstance(item.get("value"), list) else [item.get("value")]
        if not values or not all(value is not None and str(value) in corpus for value in values):
            continue
        basis = str(item.get("scope_evidence") or item.get("evidence") or "")
        if not basis or basis not in corpus:
            continue
        definition=re.search(r'[“"‘]([^”"’]{2,24})[”"’]\s*[:：]',basis)
        label=definition.group(1) if definition else None
        actual_definitions={}
        for line in corpus.splitlines():
            for named in re.finditer(r'[“"‘]([^”"’]{2,24})[”"’]\s*[:：]',line):
                clause=re.split(r'[。；;\n]',line[named.start():],maxsplit=1)[0]
                key=re.sub(r'\s+','',clause).translate(str.maketrans({'“':'"','”':'"','‘':'"','’':'"'}))
                actual_definitions.setdefault(named.group(1),{})[key]=clause
        if not label and question:
            applicable=[]
            for name,clauses in actual_definitions.items():
                if name in question and any(all(str(value) in clause for value in values) for clause in clauses.values()):
                    applicable.append(name)
            if len(applicable)>1:continue
            label=applicable[0] if applicable else None
        if label:
            clauses=actual_definitions.get(label,{})
            # A source prefix is evidence of neither set completeness nor
            # authority. Resolve the actual full definition, never its cut.
            if len(clauses)!=1:continue
            basis=next(iter(clauses.values()))
            definition=re.search(r'[“"‘]([^”"’]{2,24})[”"’]\s*[:：]',basis)
        if not all(str(value) in basis for value in values):continue
        if definition:
            # Examples and explicit exclusions after the definition sentence
            # are not members of its named set.
            clause=re.split(r'[。；;\n]',basis,maxsplit=1)[0]
            if not all(str(value) in clause for value in values):
                continue
            basis=clause
            if (item.get('column') in {'invoice.billing_country','customer.country','employee.country'} and
                    item.get('operator') in {'IN','NOT IN'} and re.search(r'只指|仅指',clause)):
                body=re.split(r'只指|仅指',clause[definition.end():],maxsplit=1)[-1]
                declared=re.search(r'(?:这|共|合计)([\d一二两三四五六七八九十]+)(?:个)?(?:国家|市场|地区|国)',body)
                body=re.split(r'(?:这|共|合计)[\d一二两三四五六七八九十]+(?:个)?(?:国家|市场|地区|国)',body,maxsplit=1)[0]
                if re.search(r'…|\.\.\.|等(?:等|国家|市场|地区)?\s*$',body):continue
                members=[part.strip() for part in re.split(r'[、，,]|\s*[和与及]\s*',body) if part.strip()]
                if declared:
                    from qa_agent.clarify.literal_structures import number
                    if number(declared.group(1))!=len(members):continue
                matched=[]
                for value in values:
                    matches=[]
                    for index,member in enumerate(members):
                        names=[re.split(r'[（(]',member,maxsplit=1)[0].strip()]
                        names+=re.findall(r'[（(]([^）)]+)[）)]',member)
                        if str(value) in names:matches.append(index)
                    if len(matches)!=1:break
                    matched.append(matches[0])
                if len(matched)!=len(values) or len(set(matched))!=len(members) or len(matched)!=len(members):
                    continue
        if question is not None and not context_filter_is_active(item,question,payload):
            continue
        grounded.append({**item, "source": "user_session_context", "scope_evidence": basis})
    return grounded


def remove_inactive_scope_text(question: str, analysis, payload: dict):
    """Recover explicit ratio operands when model text imports an inactive set.

    Only a verbatim split of this actual user turn is used. No new filter,
    name, date or value is inferred. Unprovable free-text mirrors are removed.
    """
    # This flag is program-owned. A model proposal cannot authorize removing
    # or adding a geographic restriction by setting it itself.
    analysis.query_scope.pop('geography_unrestricted',None)
    analysis.query_scope.pop('geography_provenance',None)
    definitions=[]
    for line in str(payload.get('user_brief') or '').splitlines():
        label=re.search(r'[“\"‘]([^”\"’]{2,24})[”\"’]\s*[:：]',line)
        if label:
            definitions.append((label.group(1),line))
    inactive=[label for label,line in definitions if not context_filter_is_active({'scope_evidence':line},question,payload)]
    contaminated=any(label in str(analysis.numerator or '')+'\n'+str(analysis.denominator or '') for label in inactive)
    if contaminated and analysis.task_type=='ratio':
        split=re.search(r'(?P<numerator>[^，,。；;]+?)[，,]?\s*占(?:了)?(?P<denominator>[^，,。；;]+?)(?:的)?(?:比例|占比|百分之多少|百分比)',question)
        if split:
            numerator=split.group('numerator').strip(' ，,')
            denominator=re.sub(r'的$','',split.group('denominator').strip(' ，,'))
            if '卖出' in numerator and '金额' in numerator:
                explicit=re.search(r'[^，,。；;]*(?:长曲目|短曲目|曲目|流派|曲风|客户)[^，,。；;]*金额',numerator)
                if explicit:numerator=explicit.group()
            analysis.numerator=numerator
            analysis.denominator=denominator
            analysis.evidence_spans['numerator']=numerator
            analysis.evidence_spans['denominator']=denominator
        else:
            # Do not silently choose a different meaning when the actual turn
            # has no provable operand split. Leave that operand unresolved.
            if any(label in str(analysis.numerator or '') for label in inactive):analysis.numerator=None
            if any(label in str(analysis.denominator or '') for label in inactive):analysis.denominator=None
    for key,value in list(analysis.query_scope.items()):
        if isinstance(value,str) and (any(label in value for label in inactive) or
                contaminated and any('市场' in label for label in inactive) and 'market' in value.casefold()):
            analysis.query_scope.pop(key,None)
    for name in ('numerator','denominator'):
        operand=analysis.query_scope.get(name)
        if isinstance(operand,dict):
            operand['scope']=getattr(analysis,name)
            if 'filters' in operand:
                operand['filters']=[binding for binding in operand['filters'] if context_filter_is_active(binding,question,payload)]
    # A literal recovered share with no active geographic scope must not
    # acquire an old country WHERE/CASE later in SQL generation. Keep the
    # proof narrowly scoped to a demonstrably inactive named-region set.
    region_lines=[line for label,line in definitions if label in inactive and re.search(r'国家|市场|地区',label)]
    country_fields={'invoice.billing_country','customer.country','employee.country'}
    country_filters=[binding for binding in analysis.filters if binding.get('column') in country_fields]
    for name in ('numerator','denominator'):
        operand=analysis.query_scope.get(name)
        if isinstance(operand,dict):
            country_filters.extend(binding for binding in operand.get('filters',[])
                                   if isinstance(binding,dict) and binding.get('column',binding.get('field')) in country_fields)
    geographic_reference=bool(re.search(r'国家|各国|地区|市场|地域|哪国|那边|那里|这边|这些|这批|market|countr|shi\s*chang',question,re.I))
    # Definition literals include both English names and parenthetical
    # Chinese labels. A current literal country reference defeats this proof.
    for line in region_lines:
        for match in re.finditer(r'[A-Z][A-Za-z ]*[A-Za-z]|[（(][^）)]+[）)]',line):
            literal=match.group().strip('（）() ')
            if literal and literal in question:
                geographic_reference=True
    literal_operands=all(value and value in question for value in (analysis.numerator,analysis.denominator))
    if contaminated and region_lines and literal_operands and not country_filters and not geographic_reference:
        analysis.query_scope['geography_unrestricted']=True
        analysis.query_scope['geography_provenance']={'source':'program:inactive_named_region',
            'current_evidence':question,'inactive_definition_evidence':region_lines}
    return analysis


def validate_provenance(analysis, question: str, payload: dict) -> None:
    """Keep only source records with real quoted evidence and valid scope."""
    current = str(payload.get("current_user_message") or question)
    brief = str(payload.get("user_brief") or "")
    historical = "\n".join(str(turn.get("user") or "") for turn in payload.get("actual_conversation", []) if isinstance(turn, dict))
    valid = {}
    for field, item in analysis.condition_sources.items():
        if field not in type(analysis).model_fields or not isinstance(item, dict):
            continue
        evidence = str(item.get("evidence") or "")
        source = item.get("source")
        corpus = current if source == "explicit_user" else brief if source == "user_brief" else historical if source == "confirmed_history" else ""
        if (evidence and evidence in corpus and item.get("lifetime", "task") in {"task", "persistent", "retired"}
                and item.get("applies_to", "global") in {"global", "numerator", "denominator", "eligibility"}):
            if field == 'time_scope':
                from qa_agent.clarify.season_authority import temporal_source_matches
                if not temporal_source_matches(analysis, item, current, payload):
                    continue
            valid[field] = {**item, "verified": True}
    analysis.condition_sources = valid


def apply_literal_contract(question: str, analysis, catalog, bindings: list[dict], payload: dict | None = None):
    """Small, composable repairs backed by wording, never an expected answer."""
    normalize_scope_collections(analysis)
    analysis.query_scope.pop('geography_unrestricted',None)
    analysis.query_scope.pop('geography_provenance',None)
    payload = payload or runtime_payload()
    source_question=str(payload.get("current_user_message") or question)
    analysis.query_scope.pop('comparison_partition',None)
    analysis.query_scope.pop('distinct_count',None)
    analysis.query_scope.pop('extrema_difference',None)
    analysis.query_scope.pop('temporal_field_role',None)
    analysis.query_scope.pop('paired_count_comparison',None)
    analysis.query_scope.pop('season_time_authority',None)
    analysis.query_scope.pop('employee_domain',None)
    analysis.query_scope.pop('repeat_qualification',None)
    for key in ('period_applicability','requested_percent_decimals','percent_precision_source','money_precision_source'):
        analysis.query_scope.pop(key,None)
    # Precision is an actual-source authorization boundary for SQL rounding,
    # including modes which disable optional literal-grounding enhancements.
    from qa_agent.clarify.definition_recovery import recover_percent_precision,recover_money_precision,strip_model_percent_precision
    strip_model_percent_precision(analysis)
    relative = literal_relative_period(question, payload)
    if relative:
        analysis.time_scope=relative
        analysis.time_ambiguous=False
    if not enabled("AGENT_GROUNDING_ENABLED"):
        recover_money_precision(source_question,analysis,payload)
        recover_percent_precision(source_question,analysis,payload)
        from qa_agent.clarify.conflict_authority import adjudicate_conflict_proposals
        adjudicate_conflict_proposals(source_question,analysis,payload)
        return analysis
    from qa_agent.nlu.ownership import ground_explicit_owner,remove_inapplicable_average_region_question
    ground_explicit_owner(question,analysis,bindings)
    remove_inapplicable_average_region_question(question,analysis)
    from qa_agent.clarify.literal_structures import explicit_literal_structures
    explicit_literal_structures(question,analysis,catalog)
    from qa_agent.clarify.extrema import explicit_extrema_difference
    explicit_extrema_difference(source_question,analysis,catalog)
    from qa_agent.clarify.temporal_role import explicit_temporal_field_role
    explicit_temporal_field_role(source_question,analysis,catalog)
    from qa_agent.clarify.comparison_grounding import explicit_paired_count
    explicit_paired_count(source_question,analysis)
    from qa_agent.clarify.date_roles import recover_explicit_named_period
    recover_explicit_named_period(question,analysis,payload)
    explicit_ranked_ratio_subject(question,analysis)
    if catalog.database.casefold() == "chinook":
        average=explicit_average_metric(question)
        if not average and re.search(r'人均(?:消费|金额|支出)|平均消费',question):
            historical_average=confirmed_average_from_history(payload)
            if historical_average:
                average=(historical_average[0],historical_average[1])
                analysis.condition_sources['metric']={'source':'confirmed_history','evidence':historical_average[1],
                                                      'lifetime':'persistent','applies_to':'global'}
            else:
                analysis.metric=None
                analysis.query_scope['average_grain']=None
                analysis.query_scope['average_grain_missing']=True
                from qa_agent.clarify.average_grain import with_unique_average_grain_request
                analysis.clarification_requests=with_unique_average_grain_request(analysis.clarification_requests,
                     {'field':'average_grain','question':'人均消费按每位客户平均，还是按每张发票平均？',
                     'reason':'实际用户尚未确认平均粒度，模型填入的指标不能代替用户授权。','evidence':re.search(r'人均(?:消费|金额|支出)|平均消费',question).group()})
        if average:
            analysis.metric=average[0]
            analysis.query_scope['average_grain']='customer' if average[0]=='average_customer_amount' else 'invoice'
            if explicit_average_metric(question):
                analysis.condition_sources['metric']={'source':'explicit_user','evidence':average[1],
                                                      'lifetime':'task','applies_to':'global'}
        if re.search(r"业绩|表现(?:最好|最高)|绩效", question) and not re.search(r"按.{0,12}(?:客户数|客户个数|人数|金额|销售额)|负责(?:的)?客户(?:数|个数)", question):
            analysis.task_type = "ranking"
            analysis.rank_object = "employee"
            analysis.metric = None
            analysis.clarification_requests = [item for item in analysis.clarification_requests if item.get("field") != "metric"]
            analysis.clarification_requests.append({"field": "metric", "question": "业绩按负责客户数，还是按名下客户的发票金额排名？", "reason": "当前没有获批的员工绩效默认指标。"})
        explicit_top=bool(re.search(r'(?:前\s*|top\s*)\d+|(?:最高|最多|最好)(?:的)?\s*\d+\s*(?:位|名|个|张|首)',question,re.I))
        singular_extreme=bool(re.search(r'谁[^？?。；;]{0,30}(?:最好|最高|最多|第一)|(?:第一名|那(?:一)?位|最高的一位)',question))
        approved_customer_phrase=bool(re.search(r'谁买得最多',question))
        if (analysis.task_type=='ranking' and analysis.rank_object in {'employee','customer','artist','album','track','genre'}
                and singular_extreme and not explicit_top and not approved_customer_phrase):
            analysis.top_n=1
            analysis.evidence_spans['top_n']=re.search(r'谁[^？?。；;]{0,30}(?:最好|最高|最多|第一)|(?:第一名|那(?:一)?位|最高的一位)',question).group()
        groupwise=(analysis.task_type=='ranking' and analysis.rank_object=='customer' and
                   bool(re.search(r'各个|每个|各(?:国|位|名)|分别|每组|各组',question)) and
                   bool(re.search(r'最高|最多|第一|前\s*[\d一二三四五六七八九十]+',question)))
        if groupwise:
            partition=('customer.support_rep_id' if re.search(r'负责人|支持员工|销售员工|员工手下|员工名下',question) else
                       'invoice.billing_country' if re.search(r'账单国家|开票国家|账单国',question) else
                       'customer.country' if re.search(r'国家|各国|市场|market|shi\s*chang',question,re.I) else None)
            if partition and partition in schema_columns(catalog):
                explicit=re.search(r'前\s*([\d一二三四五六七八九十]+)\s*(?:名|位|个)?',question)
                word=explicit.group(1) if explicit else None
                number=int(word) if word and word.isdigit() else {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}.get(word,1)
                analysis.query_scope.update(ranking_scope='per_group',partition_by=[partition],per_group_limit=number)
                analysis.top_n=number
                if 'groupwise_ranking' not in analysis.output_requirements:
                    analysis.output_requirements.append('groupwise_ranking')
                if partition=='customer.country':
                    analysis.region_scope=partition
                    analysis.region_ambiguous=False
                    analysis.filters=[{**item,'column':partition} if item.get('column')=='invoice.billing_country' else item for item in analysis.filters]
                    analysis.default_assumptions=[note for note in analysis.default_assumptions if '地区按发票账单国家' not in note]
                    analysis.assumptions=[note for note in analysis.assumptions if '地区按发票账单国家' not in note]
        # The amount named after "占" defines the denominator, not the inner
        # customer's ranking criterion. Apply only the existing approved
        # customer-purchase default, and retain explicit amount rankings as L0.
        numerator_clause=re.split(r'[，,]|占(?:了)?',question,maxsplit=1)[0]
        if (analysis.task_type=='ratio' and re.search(r'买得最多.{0,12}(?:客户|顾客)',numerator_clause) and
                not re.search(r'销售额|消费金额|发票金额|购买数量|发票张数|曲目数量|件数',numerator_clause)):
            note='客户“买得最多”的分子排名按发票金额统计（已确认客户专属默认口径）。'
            analysis.query_scope['rank_metric']='invoice_revenue'
            analysis.query_scope['rank_metric_source']=CUSTOMER_AMOUNT
            analysis.query_scope['numerator_ranking_metric']='invoice_revenue'
            analysis.metric='invoice_revenue'
            if not analysis.numerator:
                analysis.numerator=numerator_clause.strip()+'的同期发票金额（按客户发票金额合计排名）'
                analysis.evidence_spans['numerator']=numerator_clause.strip()
            if re.search(r'那位|第一|最高的?(?:一位|客户)',numerator_clause):
                analysis.top_n=1
            if note not in analysis.assumptions:analysis.assumptions.append(note)
            if note not in analysis.default_assumptions:analysis.default_assumptions.append(note)
        if re.search(r"(?:买过|购买过|消费过).{0,50}(?:客户|顾客).{0,8}(?:里|中)", question) and re.search(r"花钱|消费|消费金额", question):
            qualified = [{**item, "binding_scope": "eligibility"} for item in bindings if item.get("column", "").split(".")[0] in {"genre", "artist", "album", "track", "media_type"}]
            if qualified:
                analysis.query_scope = {**analysis.query_scope, "eligibility_object": "customer",
                                        "qualification_filters": qualified,
                                        "aggregation_scope": "all_invoices_for_qualified_customers"}
                analysis.filters = [item for item in bindings if item.get("column", "").split(".")[0] not in {"genre", "artist", "album", "track", "media_type"}] + qualified
                analysis.metric = "invoice_revenue"
                analysis.rank_object = "customer"
                analysis.task_type = "ranking"
        if re.search(r"(?:专辑|艺术家|曲目|歌曲|流派|曲风)", question) and re.search(r"销售额|卖了多少钱|卖出.{0,6}金额", question):
            analysis.metric = "detail_revenue"
        if analysis.task_type=='ratio' and analysis.rank_object is None:
            # The subject before the share operator names the numerator's
            # real object. A denominator's "全部曲目" cannot change it.
            subject=re.split(r'占(?:了)?',question,maxsplit=1)[0]
            objects={target for term,target in {'曲风':'genre','流派':'genre','艺术家':'artist','专辑':'album','曲目':'track','歌曲':'track'}.items() if term in subject}
            if len(objects)==1 and next(iter(objects)) in {table.name for table in catalog.tables}:
                analysis.rank_object=next(iter(objects))
        # Mixed-grain share: music-entity revenue is a detail numerator;
        # the explicitly named whole-market sales denominator uses the
        # already approved invoice amount definition. Keep each operand's
        # own scope rather than installing one global aggregation metric.
        if (analysis.task_type=='ratio' and analysis.rank_object in {'genre','artist','album','track'} and
                re.search(r'各占|占.{0,40}(?:整体|全部|总)(?:销售额|发票金额)',question) and
                analysis.numerator and analysis.denominator and re.search(r'整体销售额|全部发票|发票总额',str(analysis.denominator))):
            analysis.metric='detail_revenue'
            analysis.query_scope['numerator']={'metric':'detail_revenue','scope':analysis.numerator,
                'source_evidence':re.search(r'曲风|流派|艺术家|专辑|曲目',question).group() if re.search(r'曲风|流派|艺术家|专辑|曲目',question) else analysis.rank_object}
            analysis.query_scope['denominator']={'metric':'invoice_revenue','scope':analysis.denominator,
                'source_evidence':re.search(r'(?:整体|全部|总)(?:销售额|发票金额)',question).group() if re.search(r'(?:整体|全部|总)(?:销售额|发票金额)',question) else analysis.denominator}
            current=(analysis.time_scope or {}).get('current')
            if current:
                analysis.query_scope['denominator']['period']={key:current[key] for key in ('start','end') if key in current}
        if analysis.task_type == "ranking" and re.search(r"合计|总计|一共.{0,6}(?:多少钱|金额)|金额.{0,6}合计", question):
            if "ranked_subset_total" not in analysis.output_requirements:
                analysis.output_requirements.append("ranked_subset_total")
        # An album/artist ranking has no authorized all-data period default.
        if (analysis.task_type == "ranking" and analysis.rank_object in {"album", "artist", "genre"}
                and analysis.metric in {"detail_revenue", "purchased_quantity"}
                and not analysis.time_scope and re.search(r"一共|合计|总计", question)):
            analysis.clarification_requests.append({"field": "time_scope.current", "question": "请明确统计期间。", "reason": "该对象未登记缺少期间时使用全库的授权默认。"})
    relative = literal_relative_period(question, payload)
    if relative:
        analysis.time_scope = relative
        analysis.time_ambiguous = False
        analysis.condition_sources["time_scope"] = {"source": "explicit_user", "evidence": relative["current"]["label"], "lifetime": "task", "applies_to": "global", "verified": True, "reference_datetime": payload["reference_datetime"]}
    all_data=re.search(r'全部数据|所有数据|所有年份|全部年份|不限(?:时间|期间|年份)|(?:去掉|取消|删除).{0,8}(?:时间|期间|年份)(?:限制|筛选|条件)?',question)
    if all_data:
        analysis.time_scope={'all_data':True,'label':all_data.group()}
        analysis.time_ambiguous=False
        analysis.condition_sources['time_scope']={'source':'explicit_user','evidence':all_data.group(),
                                                 'lifetime':'task','applies_to':'global'}
    if (payload.get('user_brief') and analysis.task_type=='ranking' and analysis.rank_object=='customer'
            and not re.search(r'(?<!\d)\d{4}(?!\d)|主期间|对比期|本期|上期|去年|前年|今年|月份|季度|刚才|接着|同样|只要|只看前',question)
            and analysis.time_scope and not analysis.time_scope.get('all_data')):
        # The approved missing-period rule is explicit in the brief's handoff;
        # an unrelated preceding question's year is not a new user constraint.
        analysis.time_scope=None
        analysis.condition_sources.pop('time_scope',None)
    if payload.get('user_brief') and analysis.metric=='repeat_customer_count' and not re.search(r'(?<!\d)\d{4}(?!\d)|主期间|对比期|本期|上期|去年|前年|今年|刚才|接着|同样',question):
        analysis.time_scope=None
        analysis.condition_sources.pop('time_scope',None)
    from qa_agent.clarify.definition_recovery import recover_activated_definitions
    recover_activated_definitions(question,analysis,payload,catalog)
    # A model may point at a named context set using a short question fragment.
    # Ground its complete literal set against one actual quoted definition,
    # rather than retaining an unverified parallel qualification mirror.
    if payload.get('user_brief') and analysis.query_scope.get('qualification_filters'):
        for proposed in analysis.query_scope['qualification_filters']:
            if not isinstance(proposed,dict):
                continue
            if not proposed.get('column') and proposed.get('field') in schema_columns(catalog):
                proposed['column']=proposed.pop('field')
            values=proposed.get('value') if isinstance(proposed.get('value'),list) else [proposed.get('value')]
            for source in analysis.condition_sources.values():
                quote=str(source.get('evidence') or '')
                if quote and all(value is not None and str(value) in quote for value in values):
                    grounded=contextual_filters([{**proposed,'scope_evidence':quote}],payload,catalog,question=question)
                    for binding in grounded:
                        if not any(item.get('column')==binding.get('column') and item.get('value')==binding.get('value') for item in analysis.filters):
                            analysis.filters.append(binding)
                    if grounded:
                        break
            else:
                # Models sometimes paraphrase a source quote. Resolve only
                # the same literal set against one actual named definition
                # line; every proposed member must occur in that line.
                for line in str(payload.get('user_brief') or '').splitlines():
                    if not re.search(r'[“"‘][^”"’]{2,24}[”"’]\s*[:：]',line):
                        continue
                    if not all(value is not None and str(value) in line for value in values):
                        continue
                    definition_clause=re.split(r'[。；;\n]',line,maxsplit=1)[0]
                    grounded=contextual_filters([{**proposed,'scope_evidence':definition_clause}],payload,catalog,question=question)
                    for binding in grounded:
                        if not any(item.get('column')==binding.get('column') and item.get('value')==binding.get('value') for item in analysis.filters):
                            analysis.filters.append(binding)
                    if grounded:
                        break
    from qa_agent.clarify.invoice_ratio_source import plain_invoice_share_candidate
    plain_invoice_share=plain_invoice_share_candidate(source_question)
    if payload.get('user_brief'):
        analysis.filters=[item for item in analysis.filters if item.get('source')!='user_session_context' or context_filter_is_active(item,question,payload)]
        actual={(item.get('column'),str(item.get('value'))) for item in analysis.filters}
        if not plain_invoice_share:
            analysis.query_scope['qualification_filters']=[item for item in analysis.query_scope.get('qualification_filters',[])
                 if (item.get('column'),str(item.get('value'))) in actual]
        if not plain_invoice_share:
            remove_inactive_scope_text(question,analysis,payload)
    normalize_ranked_output(question,analysis)
    normalize_internal_contract(analysis,question)
    partition_named_comparison(question,analysis,payload,catalog)
    if analysis.task_type=='ratio' and analysis.metric=='detail_revenue':
        share=re.search(r'(?P<numerator>[^，,。；;]*(?:曲目|歌曲)[^，,。；;]*(?:卖出(?:的)?金额|销售额|成交金额))\s*[，,]?\s*占(?:了)?(?P<denominator>同期全部(?:曲目|歌曲)(?:销售额|成交金额|卖出金额))',question)
        if share:
            # Both operands are actual track-sales amounts. A named duration
            # condition scopes only the numerator, not the entire invoice.
            numerator_text=share.group('numerator').strip(' ，,')
            denominator_text=share.group('denominator')
            local=[];global_filters=[]
            for item in analysis.filters:
                quote=str(item.get('scope_evidence') or '')
                named=re.search(r'[“"‘]([^”"’]{2,24})[”"’]\s*[:：]',quote)
                numerator_only=item.get('binding_scope')=='numerator' or bool(named and named.group(1) in numerator_text and named.group(1) not in denominator_text)
                if numerator_only:
                    item['binding_scope']='numerator';local.append(dict(item))
                elif item.get('binding_scope') not in {'denominator','eligibility'}:global_filters.append(dict(item))
            scope_local_qualification_mirrors(analysis,local)
            analysis.numerator=numerator_text;analysis.denominator=denominator_text
            current=(analysis.time_scope or {}).get('current') or {}
            period={key:current[key] for key in ('start','end') if key in current}
            analysis.query_scope['numerator']={'metric':'detail_revenue','scope':numerator_text,'source_evidence':numerator_text,'filters':global_filters+local}
            analysis.query_scope['denominator']={'metric':'detail_revenue','scope':denominator_text,'source_evidence':denominator_text,'filters':global_filters}
            if period:
                analysis.query_scope['numerator']['period']=dict(period)
                analysis.query_scope['denominator']['period']=dict(period)
            for name,text in [('numerator',numerator_text),('denominator',denominator_text)]:
                analysis.condition_sources[name]={'source':'explicit_user','evidence':text,'lifetime':'task','applies_to':name}
    if not plain_invoice_share and analysis.query_scope.get('denominator',{}).get('metric')=='invoice_revenue':
        regional=[dict(item) for item in analysis.filters if item.get('column') in {'invoice.billing_country','customer.country'} and
                  item.get('binding_scope') not in {'numerator','eligibility'}]
        if regional:
            analysis.query_scope['denominator']['filters']=regional
    from qa_agent.clarify.date_roles import normalize_operand_calendar_roles
    from qa_agent.clarify.applicability import normalize_assignment_period
    from qa_agent.clarify.invoice_ratio_source import ground_invoice_set_share
    normalize_operand_calendar_roles(question,analysis,catalog=catalog)
    ground_invoice_set_share(source_question,analysis,bindings,catalog)
    recover_money_precision(source_question,analysis,payload)
    recover_percent_precision(source_question,analysis,payload)
    normalize_operand_calendar_roles(question,analysis,catalog=catalog)
    from qa_agent.clarify.calendar_contract import normalize_global_calendar_mirrors
    normalize_global_calendar_mirrors(source_question,analysis,catalog,payload)
    from qa_agent.clarify.assignment_scope import normalize_current_assignment_scope
    normalize_current_assignment_scope(source_question,analysis,catalog,payload)
    from qa_agent.clarify.registered_qualification import normalize_repeat_metric_qualification
    normalize_repeat_metric_qualification(source_question,analysis,catalog)
    from qa_agent.clarify.ranking_symbols import normalize_customer_winner_symbol
    normalize_customer_winner_symbol(source_question,analysis,catalog)
    normalize_assignment_period(question,analysis)
    from qa_agent.clarify.authority_priority import resolved_named_collective,resolve_approved_period_uncertainty
    resolved_named_collective(source_question,analysis,payload)
    resolve_approved_period_uncertainty(source_question,analysis,payload)
    from qa_agent.clarify.denominator_authority import ground_denominator_authority
    ground_denominator_authority(source_question,analysis,payload)
    from qa_agent.clarify.season_authority import season_period_authority
    season_period_authority(source_question,analysis,payload)
    from qa_agent.clarify.calendar_range import parse_calendar_range
    from qa_agent.clarify.season_authority import actual_calendar_anchor
    is_range, literal_range = parse_calendar_range(source_question, actual_calendar_anchor(source_question,payload))
    if is_range:
        if literal_range:
            analysis.time_scope=literal_range
            analysis.time_ambiguous=False
            analysis.condition_sources['time_scope']={'source':'explicit_user', 'evidence':source_question,
                'lifetime':'task', 'applies_to':'global'}
            analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field') not in {'time_scope','time_scope.current'}]
        else:
            analysis.time_ambiguous=True
            analysis.clarification_requests.append({'field':'time_scope.current', 'question':'请明确完整起止日期及端点是否包含。',
                'reason':'实际日期区间尚不能完整解析，不能退化为第一个日期或月份。', 'evidence':source_question})
    validate_provenance(analysis, question, payload)
    from qa_agent.clarify.conflict_authority import adjudicate_conflict_proposals
    adjudicate_conflict_proposals(source_question,analysis,payload)
    return analysis
