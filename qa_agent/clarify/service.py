"""Glue between actual value-link evidence, the semantic gate and session state."""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
import json
from pathlib import Path
import re
from hashlib import sha256
from typing import Any

from qa_agent.clarify.extractor import extract_intent, explicit_region_scope
from qa_agent.clarify.grounding import literal_relative_period, partial_calendar_period, runtime_payload, explicit_average_metric
from qa_agent.nlu.features import enabled
from qa_agent.clarify.followup import (unfilled_country_delta,apply_unfilled_country_delta,
                                     ranking_limit_delta,apply_ranking_limit_delta)
from qa_agent.clarify.policy import default_policy_ids
from qa_agent.clarify.rules import RuleDecision, RuleEngine, explicit_period, explicit_comparison_period
from qa_agent.clarify.state import (DEFAULT_STORE, IntentPatch, PatchResponse, SessionConflict,
                                    SessionState, SessionStore, apply_choice, apply_patches,
                                    prepare_card, sync_contract, transition, verify_resume)

PATCH_PROMPT = Path(__file__).with_name("prompts") / "intent_patch.txt"
FOLLOWUP_PREFIX = re.compile(r"^\s*(?:那(?:就)?|改(?:成|为|按)|换(?:成|为)|还是|同样(?:的)?|再(?:看|查)|把.{0,24}改|按(?:销售额|购买数量|歌单)|换一个|(?:分子|分母|指标|期间|年份|国家|对象)(?:换成|改成|改为|换为))")
EDIT_PREFIX = re.compile(r'^\s*(?:(?:再)?(?:加上|增加|添加|去掉|移除|删除|取消|不再限制|不限|保留|改看|改查|换看|换查)|(?:分子|分母)(?:是|为)|(?:账单国家|账单国|客户所在地|客户所在国)(?:换成|改成|改为|换为))')


@dataclass
class GateResult:
    state: SessionState
    decision: RuleDecision
    card: dict | None
    question: str


def is_followup(question: str) -> bool:
    return bool(FOLLOWUP_PREFIX.search(question) or EDIT_PREFIX.search(question) or
                re.fullmatch(r'\s*\d{4}\s*年(?:\s*\d{1,2}\s*月)?\s*呢[？?。]*\s*',question))


def pending_text_response(state: SessionState | None, message: str) -> bool:
    return bool(enabled('AGENT_CLARIFY_STATE_ENABLED') and state and state.pending_card and
                len(message)<300 and re.match(r'\s*(?:是|不是|选|就|第[一二三四五六七八九十\d]|前者|后者|按|用|我指|我的意思)',message))


def textual_candidate_choice(state: SessionState, card: dict, message: str, linked) -> str | None:
    """Resolve only actual current-card candidates, with polarity preserved.

    Saying "not B, A" confirms A rather than both A and B. Ordinals refer to
    the displayed options in this one card, never a newly recalled ranking.
    """
    if not enabled('AGENT_CLARIFY_STATE_ENABLED'):
        return None
    options=[item for item in card.get('trusted_options',[]) if item.get('patch',{}).get('op')=='resolve_value']
    if not options:
        return None
    positives=[item for item in linked.bindings if item.get('operator')=='=']
    matches=[option for option in options if any(option['patch'].get('column')==item.get('column') and
             option['patch'].get('value')==item.get('value') for item in positives)]
    # A duplicated candidate may occur in two independent issues: do not
    # collapse it without an unambiguous issue target.
    if len(matches)==1:
        return matches[0]['id']
    contrasted=re.search(r'(?:不是|不选)\s*(前者|后者|第[一二三四五六七八九十\d]+(?:个|项|种)?)\s*[，,；;]?\s*(?:而是|是|选|就选)\s*(前者|后者|第[一二三四五六七八九十\d]+(?:个|项|种)?)\s*[。.!！]?\s*$',message)
    ordinal_message=contrasted.group(2) if contrasted and contrasted.group(1)!=contrasted.group(2) else message
    ordinal=re.fullmatch(r'\s*(?:选|就选|是|用)?\s*(?:第([一二三四五六七八九十\d]+)(?:个|项|种)?|(前者|后者))\s*[。.!！]?\s*',ordinal_message)
    if ordinal and len({item['patch']['mention_id'] for item in options})==1:
        word=ordinal.group(1)
        number=(int(word) if word and word.isdigit() else {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}.get(word)) if word else (1 if ordinal.group(2)=='前者' else 2)
        if number and 1<=number<=len(options):
            return options[number-1]['id']
    return None


def source_dict(request) -> dict:
    result=request.scope.model_dump(mode="json")
    context_id=getattr(request,'context_id',None)
    if not context_id:
        from qa_agent.context import current_context
        context=current_context()
        if context is not None and context.session_id==request.session_id:
            context_id=context.context_id
    if context_id:
        result['context_id']=context_id
    return result


def question_for_linking(request, store: SessionStore = DEFAULT_STORE) -> str:
    state = store.get(request.session_id)
    card_id = getattr(request, "clarification_id", None)
    if not state or not (card_id or is_followup(request.message)):
        return request.message
    if source_dict(request) != state.scope:
        if card_id:
            raise SessionConflict("来源范围已改变，旧澄清卡片无法使用。")
        return request.message
    # Linking a follow-up against the whole old query would turn old/new countries
    # into IN (...). Only the new message is linked; state retains other filters.
    return request.message


def mentions_for_linking(request, index, store: SessionStore = DEFAULT_STORE):
    from qa_agent.nlu.linker import extract_mentions, field_scope
    state=store.get(request.session_id)
    if not state or not (getattr(request,'clarification_id',None) or is_followup(request.message) or pending_text_response(state,request.message)) or source_dict(request)!=state.scope:
        return None
    explicit_fields=field_scope(request.message,index)
    if explicit_fields:
        return extract_mentions(request.message,index,fields=explicit_fields)
    fields={item['column'] for item in state.bindings if item.get('column')}
    fields.update(item['column'] for item in state.analysis.query_scope.get('pending_filters',[]) if item.get('column'))
    fields.update(candidate['column'] for issue in state.unresolved_values for candidate in issue.get('candidates',[]) if candidate.get('column'))
    if not fields:return None
    indexed={record.column for record in index.records}
    from qa_agent.clarify.date_roles import temporal_schema_columns
    temporal=temporal_schema_columns(request.scope.db_id or 'chinook')
    fields -= temporal - indexed
    # Calendar constraints stay in semantic state, never categorical binding.
    if not fields:return []
    return extract_mentions(request.message,index,fields=tuple(sorted(fields)))


def available_years(catalog) -> list[int]:
    # Catalog metadata is actual database evidence, not evidence of complete years.
    years = (catalog.metadata.get("invoice_years") or catalog.metadata.get("order_years") or
             catalog.metadata.get("sales_order_years") or catalog.metadata.get("purchase_order_years"))
    if years:
        return sorted({int(value) for value in years})
    return []


def _binding_key(item: dict) -> tuple:
    return (item.get("column"), item.get("operator"), json.dumps(item.get("value"), sort_keys=True, ensure_ascii=False),
            item.get("binding_scope"))


def _ground_patch_filters(patches: list[IntentPatch], state: SessionState, linked, *, derived_scope: str | None = None,
                          replace_columns: set[str] | None = None) -> None:
    allowed = list(state.bindings) + list(linked.bindings)
    if derived_scope:
        allowed += [{**item,'column':derived_scope} for item in state.bindings
                    if item.get('column') in {'invoice.billing_country','customer.country'}]
    for patch in patches:
        if patch.path != "filters" or patch.op == "remove":
            continue
        values = patch.value if isinstance(patch.value, list) else [patch.value]
        trusted=[]
        for binding in values:
            if not isinstance(binding,dict):
                raise SessionConflict("补丁中的筛选值没有真实值链接或此前用户确认依据。")
            matches=[item for item in allowed if _binding_key(item)==_binding_key(binding)]
            if not matches:
                # Scope metadata is trusted program evidence. If the model
                # invents a role for one uniquely grounded global value, strip
                # it by recovering the actual record; never collapse two real
                # numerator/denominator records into an arbitrary one.
                physical=[item for item in allowed if _binding_key(item)[:3]==_binding_key(binding)[:3]]
                if len({_binding_key(item) for item in physical})==1:
                    matches=physical
            if not matches:
                raise SessionConflict("补丁中的筛选值没有真实值链接或此前用户确认依据。")
            trusted.append(dict(matches[0]))
        if patch.op == "set":
            new_columns = {item.get("column") for item in values if isinstance(item, dict)}
            if any(old.get('column') not in (replace_columns or set()) and
                   (derived_scope if derived_scope and old.get('column') in {'invoice.billing_country','customer.country'} else old.get('column')) not in new_columns for old in state.bindings):
                raise SessionConflict("替换筛选时丢失了未被用户修改的其它条件；删除条件需要明确 remove 补丁。")
        patch.value=trusted


def _persistent_ambiguities(linked, question: str) -> list[dict]:
    result = []
    for mention in linked.ambiguous:
        item = mention.as_dict()
        signature = json.dumps({"question": question, "text": mention.original_text,
                                "span": mention.span, "candidates": [(c.get("column"), c.get("standard_value"))
                                                                     for c in mention.candidates]}, ensure_ascii=False, sort_keys=True)
        item["mention_id"] = "issue-" + sha256(signature.encode("utf-8")).hexdigest()[:16]
        result.append(item)
    return result


def extract_patches(message: str, state: SessionState, linked, llm, trace=None) -> list[IntentPatch]:
    from qa_agent.clarify.invoice_ratio_source import explicit_invoice_operand_patch,invoice_ratio_delta
    ordinary_invoice=(state.analysis.rank_object is None and state.analysis.metric=='invoice_revenue'
        and all(isinstance(state.analysis.query_scope.get(role),dict)
            and state.analysis.query_scope[role].get('metric')=='invoice_revenue'
            and state.analysis.query_scope[role].get('source_evidence')for role in('numerator','denominator')))
    proved_operand_edit=explicit_invoice_operand_patch(message,state.analysis,linked.bindings)if ordinary_invoice else None
    closed_delta=(ordinary_invoice and invoice_ratio_delta(message,state.analysis)
        and not re.match(r'\s*(?:请)?(?:分子|分母)',message))
    current_card = state.pending_card or state.switch_card or {}
    payload={"message": message, "current_intent": state.analysis.model_dump(),
             "current_card": {key: value for key, value in current_card.items() if key != "trusted_options"},
             "verified_value_bindings": linked.bindings}
    runtime=runtime_payload()
    from qa_agent.clarify.conflict_authority import conflict_source_catalog
    payload['conflict_source_registry']=conflict_source_catalog(message,runtime)
    if runtime:
        payload['runtime_context']=runtime
    if ordinary_invoice and(proved_operand_edit or closed_delta):
        # The whole actual source proves this finite edit. Program-generated
        # deltas preserve the saved contract; no model scope/metric/owner reset
        # or duplicate semantic-model judgement is needed.
        result=PatchResponse(patches=[])
    else:
        result = llm.complete_json(
            PATCH_PROMPT.read_text(encoding="utf-8"),
            json.dumps(payload, ensure_ascii=False),
            PatchResponse, trace=trace)
    # A metric/object change cannot silently reset a previously established
    # calendar range. Discard model-invented resets without touching any actual
    # date text or the user's explicit cancellation of the period.
    has_calendar_text=bool(re.search(r'(?<!\d)\d{4}(?!\d)|(?<!\d)\d{1,2}\s*月|今年|去年|最近|本月|上月|本季度|上季度',message))
    cancels_period=bool(re.search(r'全部数据|所有数据|(?:取消|去掉|删除|不限|全部|所有).{0,8}(?:期间|日期|年份|时间)|(?:期间|日期|年份|时间).{0,8}(?:不限|取消|全部|所有)',message))
    result.patches=[patch for patch in result.patches
                    if patch.path!='time_scope' or has_calendar_text or cancels_period]
    # Plain country/date/top-N edits cannot authorize model-generated changes
    # to the measure, task or comparison. Literal metric edits are grounded
    # below, while unfamiliar user-written measures remain model proposals.
    measure_text=bool(re.search(r'指标|口径|金额|销售额|客单价|平均|复购|数量|客户数|客户个数|人数|张数|次数|销量|购买量|购买数量|计数|总额',message))
    object_text=bool(re.search(r'(?:对象|改成|换成|改为|换为|改看|改查|换看|换查).{0,4}(?:流派|艺术家|乐队|专辑|曲目|歌曲|客户|顾客|发票|账单)',message))
    result.patches=[patch for patch in result.patches if
                    (patch.path!='metric' or measure_text) and
                    (patch.path!='rank_object' or object_text) and
                    (patch.path!='order' or bool(re.search(r'排序|升序|降序|倒序|正序|并列|asc|desc',message,re.I))) and
                    (patch.path!='grouping' or bool(re.search(r'分组|分别|每个|按年|按月|逐年|逐月',message))) and
                    (patch.path!='scope_missing' or bool(re.search(r'这批|这些|这部分|这组|全部|所有|全库',message))) and
                    (patch.path!='time_ambiguous' or has_calendar_text or cancels_period) and
                    (patch.path not in {'task_type','comparison'} or
                     bool(re.search(r'同比|环比|增长|占比|比例|排名|排行|前\s*\d+|top\s*\d+|不看|不算|取消',message,re.I)))]
    average=explicit_average_metric(message)
    if average:
        result.patches=[patch for patch in result.patches if patch.path!='metric']
        result.patches.append(IntentPatch(op='set',path='metric',value=average[0],evidence=average[1]))
    elif re.search(r'平均每张发票金额|平均(?:发票|账单)金额|客单价',message):
        result.patches=[patch for patch in result.patches if patch.path!='metric']
        result.patches.append(IntentPatch(op='set',path='metric',value='average_invoice_amount',evidence=re.search(r'平均每张发票金额|平均(?:发票|账单)金额|客单价',message).group()))
    elif re.search(r'(?:发票|账单)(?:销售额|金额|总额)|销售额',message):
        metric='detail_revenue' if state.analysis.metric=='detail_revenue' or state.analysis.rank_object in {'track','artist','album','genre'} or any(item.get('column') in {'artist.name','genre.name','album.title','track.name'} for item in state.bindings) else 'invoice_revenue'
        result.patches=[patch for patch in result.patches if patch.path!='metric']
        result.patches.append(IntentPatch(op='set',path='metric',value=metric,evidence=re.search(r'(?:发票|账单)(?:销售额|金额|总额)|销售额',message).group()))
    elif re.search(r'(?:发票|账单)(?:张数|数量|次数)|(?:张数|计数)',message):
        result.patches=[patch for patch in result.patches if patch.path!='metric']
        result.patches.append(IntentPatch(op='set',path='metric',value='invoice_count',evidence=re.search(r'(?:发票|账单)(?:张数|数量|次数)|(?:张数|计数)',message).group()))
    # Ratio operands own independent local scopes. A country mentioned while
    # changing one operand must not move or overwrite the other operand.
    from qa_agent.clarify.invoice_ratio_source import explicit_invoice_operand_patch
    operand_edit=proved_operand_edit if ordinary_invoice else explicit_invoice_operand_patch(message,state.analysis,linked.bindings)
    if ordinary_invoice and not operand_edit and (any(patch.path in {'numerator','denominator'}for patch in result.patches)
            or re.match(r'\s*(?:分子|分母)(?:的)?(?:期间|年份|日期)?(?:改为|改成|换成)',message)):
        # Calendar-only operand edits are checked against their own saved
        # bounds below. Other unparsed operand requests cannot borrow a model
        # substring or its empty patch list to erase remaining source clauses.
        if not re.fullmatch(r'\s*(?:分子|分母)(?:的)?(?:期间|年份|日期)(?:改为|改成|换成)\s*\d{4}\s*年(?:\s*\d{1,2}\s*月)?'
                r'(?:[，,]\s*(?:分母|分子|其他条件)(?:及其他条件)?不变)?[。！!]?\s*',message):
            raise SessionConflict('本次发票比例操作数修改尚未完整核验；请分别明确国家字段、金额范围及保留条件，未改变原合同。')
    from qa_agent.clarify.invoice_ratio_source import invoice_ratio_delta
    if (ordinary_invoice and not operand_edit
            and re.match(r'\s*(?:(?:年份|期间)(?:改为|改成|换成)|(?:改为|改成)?百分比|(?:取消|删除|去掉)百分比)',message)
            and not invoice_ratio_delta(message,state.analysis)):
        raise SessionConflict('本次发票比例操作数修改尚未完整核验；请分别明确国家字段、金额范围及保留条件，未改变原合同。')
    if operand_edit:
        # The complete supported sentence explicitly preserves all other
        # conditions. No model-proposed global country or metric reset survives.
        role,operand_text=operand_edit
        result.patches=[IntentPatch(op='set',path=role,value=operand_text,evidence=message)]
    local_ratio=state.analysis.task_type=='ratio' and any(patch.path in {'numerator','denominator'} for patch in result.patches)
    if local_ratio and not re.search(r'全局|整个查询|整体地区',message):
        result.patches=[patch for patch in result.patches if patch.path not in {'filters','region_scope','region_ambiguous'}]
    cancellation=re.search(r'(?:^|[，,。；;])\s*(?:那就|请|现在|先|我|改成|换成)?\s*(?:取消|不看|不算|不要)\s*(?:同比|环比|比较|增长率|增长)',message)
    positive_comparisons=[match for match in re.finditer(r'同比|环比',message)
                          if not re.search(r'不是|并非|(?:不看|不算|不要|取消|非)\s*$',message[max(0,match.start()-4):match.start()])]
    if cancellation and (state.analysis.task_type=='growth' or state.analysis.comparison):
        evidence=cancellation.group().lstrip('，,。；;').strip()
        result.patches=[patch for patch in result.patches if patch.path not in {'task_type','comparison'}]
        result.patches.extend([IntentPatch(op='set',path='task_type',value='aggregation',evidence=evidence),
                               IntentPatch(op='remove',path='comparison',evidence=evidence)])
        if state.analysis.time_scope and state.analysis.time_scope.get('base'):
            result.patches=[patch for patch in result.patches if patch.path!='time_scope']
            result.patches.append(IntentPatch(op='set',path='time_scope',value={key:value for key,value in state.analysis.time_scope.items() if key!='base'},evidence=evidence))
    elif positive_comparisons:
        evidence=positive_comparisons[0].group()
        result.patches=[patch for patch in result.patches if patch.path not in {'task_type','comparison'}]
        result.patches.extend([IntentPatch(op='set',path='task_type',value='growth',evidence=evidence),
                               IntentPatch(op='set',path='comparison',value={'type':'yoy' if evidence=='同比' else 'mom'},evidence=evidence)])
    elif (state.analysis.task_type=='growth' and any(patch.path=='metric' for patch in result.patches) and
          not re.search(r'(?:不要|取消|不看|不算).{0,4}(?:同比|环比|增长)|只(?:看|要).{0,8}(?:金额|数量|客单价)',message)):
        result.patches=[patch for patch in result.patches if patch.path!='task_type']
    for patch in result.patches:
        if patch.path in {"assumptions","default_assumptions","evidence_spans"}:
            raise SessionConflict("默认口径与确认记录只能由程序依据规则生成，模型不能修改审核依据。")
        if not patch.evidence or patch.evidence not in message:
            raise SessionConflict("模型补丁未提供本次用户真实原文依据。")
        if patch.path=='rank_object' and patch.op=='set':
            names={'客户':'customer','顾客':'customer','曲目':'track','歌曲':'track','艺术家':'artist',
                   '乐队':'artist','专辑':'album','流派':'genre','发票':'invoice','账单':'invoice'}
            if patch.value in names and patch.value in patch.evidence:
                patch.value=names[patch.value]
    cancel_region=re.search(r'(?:删除|取消|去掉|移除|不再限制|不限)\s*'
                            r'(?:invoice\.billing_country|billing_country|账单国家|账单所在国|账单国|'
                            r'customer\.country|客户所在地|客户所在国|客户居住国)\s*(?:限制|筛选|条件)?',message)
    if cancel_region and not re.search(r'(?:不要|不能|别|不应|不需要|不)\s*$',
                                      message[max(0,cancel_region.start()-6):cancel_region.start()]):
        target_scope=explicit_region_scope(cancel_region.group())
        # Canceling a country filter does not cancel the meaning of the
        # country field. The real model correctly removed Canada but added
        # region_scope=null, which must not be mistaken for a field migration.
        result.patches=[patch for patch in result.patches if not
                        (patch.path=='region_scope' and (patch.op=='remove' or patch.value is None))]
        if not any(patch.path=='filters' for patch in result.patches):
            removable=[dict(item) for item in state.bindings if item.get('column')==target_scope and
                       item.get('binding_scope') not in {'numerator','denominator'}]
            if removable:
                result.patches.append(IntentPatch(op='remove',path='filters',value=removable,evidence=cancel_region.group()))
    result.patches=[patch for patch in result.patches if not(patch.path=='region_scope' and patch.op=='set' and patch.value==state.analysis.region_scope)]
    scope_patches=[patch for patch in result.patches if patch.path=='region_scope' and patch.op=='set']
    derived_scope=None
    object_fields={'流派':'genre.name','艺术家':'artist.name','乐队':'artist.name','专辑':'album.title','曲目':'track.name','歌曲':'track.name'}
    replacement=re.search(r'(?:改成|换成|改为|换为)\s*(流派|艺术家|乐队|专辑|曲目|歌曲)',message)
    target=object_fields[replacement.group(1)] if replacement else None
    new_values=[binding for binding in linked.bindings if binding.get('column')==target]
    old_objects=[binding for binding in state.bindings if binding.get('column') in set(object_fields.values())]
    # Replacing exactly one old object is explicit in “改成流派 Metal”. Never
    # extend that deletion to countries, employees or other independent fields.
    replace_columns={item['column'] for item in old_objects if item['column']!=target} if replacement and len(old_objects)==1 and len(new_values)==1 else set()
    if scope_patches:
        written_scope=explicit_region_scope(message)
        if written_scope is None or any(patch.value!=written_scope for patch in scope_patches):
            raise SessionConflict('地区字段修改没有本次用户明确的账单国家或客户所在地原文依据。')
        if len({item.get('column') for item in state.bindings if item.get('column') in {'invoice.billing_country','customer.country'}})>1:
            from qa_agent.nlu.ownership import country_value_delta
            if country_value_delta(message,linked.bindings,state):
                # Naming the edited predicate does not migrate every country
                # condition into that owner. Its actual binding is authoritative.
                result.patches=[patch for patch in result.patches if patch.path!='region_scope']
            else:
                raise SessionConflict('当前有两个独立国家筛选，请明确需要改动的具体条件，不能同时合并或迁移。')
        else:
            derived_scope=written_scope
    # A change of country field moves the already confirmed value; deleting the
    # obsolete field is not a request to cancel that value. Normalize only this
    # proven migration. Other removals require an explicit deletion statement.
    retained=[]
    for patch in result.patches:
        if patch.path!='filters' or patch.op!='remove':
            retained.append(patch)
            continue
        values=patch.value if isinstance(patch.value,list) else [patch.value]
        originals=[]
        for value in values:
            if not isinstance(value,dict):
                raise SessionConflict('删除筛选必须指定此前已确认的具体条件。')
            match=next((old for old in state.bindings if _binding_key(old)==_binding_key(value)),None)
            if match is None:
                raise SessionConflict('要删除的筛选不在此前已确认条件中。')
            originals.append(match)
        cancellation=bool(re.search(r'删除|取消|去掉|移除|不再限制|不限',patch.evidence))
        if re.search(r'(?:不要|不能|别|不应|不需要|不)(?:删除|取消|去掉|移除)',patch.evidence):
            cancellation=False
        migration=(derived_scope is not None and originals and all(
            item.get('column') in {'invoice.billing_country','customer.country'} and item.get('column')!=derived_scope
            for item in originals))
        if (migration or originals and all(item.get('column') in replace_columns for item in originals)) and not cancellation:
            continue
        if not cancellation:
            raise SessionConflict('本次输入没有明确取消该筛选条件，不能删除此前已确认的条件。')
        for original in originals:
            column=original.get('column')
            explicit_target=(column in patch.evidence or explicit_region_scope(patch.evidence)==column)
            linked_target=any(_binding_key(item)==_binding_key(original) for item in linked.bindings)
            if not explicit_target and not linked_target:
                raise SessionConflict('取消说明没有明确指向这个筛选字段或其真实值，不能连带删除其它条件。')
        patch.value=originals
        retained.append(patch)
    result.patches=retained
    if derived_scope:
        for patch in result.patches:
            if patch.path=='filters' and patch.op=='set' and isinstance(patch.value,list):
                columns={item.get('column') for item in patch.value if isinstance(item,dict)}
                if derived_scope not in columns:
                    patch.value += [{**item,'column':derived_scope} for item in state.bindings
                                    if item.get('column') in {'invoice.billing_country','customer.country'}]
    # A model's whole-list set is a proposal, not permission to erase other
    # fields. Merge columns with actual current-turn bindings and retain the
    # remaining previously confirmed records. Explicit removals are separate.
    for patch in result.patches:
        if patch.path=='filters' and patch.op=='set' and isinstance(patch.value,list):
            written_columns={item.get('column') for item in linked.bindings}
            present_columns={item.get('column') for item in patch.value if isinstance(item,dict)}
            untouched=[item for item in state.bindings if item.get('column') not in written_columns and
                       item.get('column') not in present_columns and item.get('column') not in replace_columns and
                       not (derived_scope and item.get('column') in {'invoice.billing_country','customer.country'})]
            patch.value=untouched+patch.value
    if replace_columns:
        others=[item for item in state.bindings if item.get('column') not in replace_columns and item.get('column')!=target]
        result.patches=[patch for patch in result.patches if patch.path!='filters']
        result.patches.append(IntentPatch(op='set',path='filters',value=others+new_values,evidence=message))
    _ground_patch_filters(result.patches, state, linked,derived_scope=derived_scope,replace_columns=replace_columns)
    # A verified current-turn value is input evidence, not an optional model
    # proposal. In real DEV runs the model sometimes emitted only the year
    # patch for “期间改成2023年，限定账单国为德国”, dropping Germany altogether.
    # Apply positive linked values by their field/local scope while retaining
    # independent filters. Cancellation and ratio-operand edits have their own
    # explicit handling and cannot be interpreted as additions here.
    removal_text=bool(re.search(r'删除|取消|去掉|移除|不再限制|不限',message))
    if linked.bindings and not local_ratio and not removal_text:
        current_values=[dict(item) for item in linked.bindings]
        if derived_scope:
            current_values=[{**item,'column':derived_scope} if item.get('column') in
                            {'invoice.billing_country','customer.country'} else item for item in current_values]
        current_keys={(item.get('column'),item.get('binding_scope')) for item in current_values}
        retained_values=[dict(item) for item in state.bindings
                         if (item.get('column'),item.get('binding_scope')) not in current_keys and
                         item.get('column') not in replace_columns and
                         not (derived_scope and item.get('column') in {'invoice.billing_country','customer.country'})]
        result.patches=[item for item in result.patches if item.path!='filters']
        result.patches.append(IntentPatch(op='set',path='filters',value=retained_values+current_values,evidence=message))
    # The requested ranking size is independent of the executor's display cap.
    # Do not rely on the model to notice an explicit “前5首” edit or clamp it.
    top_match=re.search(r'(?:前\s*|top\s*)(\d+)\s*(?:首|个|名|条|位)?',message,re.I)
    if top_match and int(top_match.group(1))>0:
        result.patches=[item for item in result.patches if item.path!='top_n']
        result.patches.append(IntentPatch(op='set',path='top_n',value=int(top_match.group(1)),evidence=top_match.group()))
    # Explicit calendar text is converted by code and takes precedence over model dates.
    from qa_agent.clarify.calendar_range import parse_calendar_range, parse_whole_month_reply, month_convention_quote
    calendar_anchor=literal_relative_period(message,runtime) or state.analysis.time_scope
    is_range, complete_range = parse_calendar_range(message, calendar_anchor)
    month_convention=None
    if is_range and complete_range is None and enabled('AGENT_GROUNDING_ENABLED'):
        from qa_agent.context import current_context
        actual_context=current_context()
        # Only this exact server-bound session/message/context can provide the
        # month convention. No model scope label or historic assistant text.
        if (actual_context is not None and actual_context.session_id==state.session_id
                and actual_context.current_user_message==message
                and actual_context.context_id==state.scope.get('context_id')
                and actual_context.content_sha256==sha256(actual_context.text.encode('utf-8')).hexdigest()):
            month_convention=month_convention_quote(actual_context.text)
            if month_convention:
                complete_range=parse_whole_month_reply(message,calendar_anchor,month_convention)
    if is_range and complete_range is None:
        raise SessionConflict('日期区间端点尚不完整、存在冲突或不支持；请明确起止日期及是否包含端点，不能降成首日。')
    period = complete_range or explicit_period(message) or explicit_comparison_period(message,(state.analysis.comparison or {}).get('type')) or literal_relative_period(message,runtime) or partial_calendar_period(message,state.analysis.time_scope)
    local_period_same=False
    local_period=re.search(r'(分子|分母)(?:的)?(?:期间|年份|日期)|((?:分子|分母))(?:改为|改成|换成)',message)
    if period and state.analysis.task_type=='ratio' and local_period:
        role='numerator'if(local_period[1]or local_period[2])=='分子'else'denominator'
        confirmed=state.analysis.query_scope.get(role)
        confirmed=(confirmed['period']if isinstance(confirmed,dict)and'period'in confirmed else(state.analysis.time_scope or{}).get('current'))
        if not isinstance(confirmed,dict):confirmed={}
        proposed=(period or{}).get('current')or{}
        if not all(confirmed.get(key)and confirmed.get(key)==proposed.get(key)for key in('start','end')):
            raise SessionConflict('该比例操作数的独立期间修改尚不能安全归一，请分别明确分子和分母的完整期间；未改变原条件。')
        # This restates the already confirmed operand period. It authorizes
        # the local country change, never a reset of the other/global period.
        local_period_same=True
        result.patches=[patch for patch in result.patches if patch.path not in {'time_scope','time_ambiguous'}]
    from qa_agent.clarify.season_authority import season_calendar_edit_period
    period,retired_season=season_calendar_edit_period(message,state,period,runtime)
    if local_period_same:period=None
    if period:
        overridden={'time_scope','time_scope.current','time_scope.current.start','time_scope.current.end',
                    'time_scope.current.grain','time_scope.current.label'}
        result.patches = [item for item in result.patches if item.path not in overridden]
        period_evidence=(period.get('current') or {}).get('label') if complete_range or (period.get('current') or {}).get('year_source') else next(iter(re.findall(r"\d{4}\s*年(?:\s*\d{1,2}\s*月)?|前年|去年|今年|明年", message)), "")
        result.patches.append(IntentPatch(op="set", path="time_scope", value=period, evidence=period_evidence))
        result.patches.append(IntentPatch(op="set", path="time_ambiguous", value=False,
                                          evidence=period_evidence))
        if state.analysis.task_type=='ratio':
            old=(state.analysis.time_scope or{}).get('current')or{}
            new=(period or{}).get('current')or{}
            old_bounds={key:old.get(key)for key in('start','end')}
            if all(old_bounds.values())and new.get('start')and new.get('end'):
                scope=deepcopy(next((patch.value for patch in reversed(result.patches)
                    if patch.path=='query_scope'and patch.op=='set'and isinstance(patch.value,dict)),state.analysis.query_scope))
                changed=False
                for role in('numerator','denominator'):
                    operand=scope.get(role)
                    if isinstance(operand,dict)and operand.get('period')==old_bounds:
                        operand['period']={key:new[key]for key in('start','end')};changed=True
                if changed:
                    result.patches=[patch for patch in result.patches if patch.path!='query_scope']
                    result.patches.append(IntentPatch(op='set',path='query_scope',value=scope,evidence=period_evidence))
        from qa_agent.clarify.normalization import canonical_slot
        unresolved=[item for item in state.analysis.clarification_requests
                    if canonical_slot(item.get('field','')) not in {'time_scope.current','time_scope.base'}]
        result.patches=[patch for patch in result.patches if patch.path!='clarification_requests']
        result.patches.append(IntentPatch(op='set',path='clarification_requests',value=unresolved,evidence=period_evidence))
        if state.analysis.query_scope.get('season_time_authority'):
            scope=deepcopy(state.analysis.query_scope)
            season_completed = (period.get('current') or {}).get('grain') in {'custom','month','quarter'}
            if retired_season:
                scope.pop('season_time_authority',None)
            elif season_completed:
                scope['season_time_authority']={'status':'confirmed','source':'program:explicit_season_period',
                    'evidence':message,'period':deepcopy(period.get('current') or {})}
                if month_convention and complete_range:
                    scope['season_time_authority']['calendar_convention']={
                        'source':'user_brief','evidence':month_convention,
                        'context_id':actual_context.context_id,'context_version':actual_context.version,
                        'source_sha256':actual_context.content_sha256}
                if (period.get('current') or {}).get('year_source')=='previous_confirmed_season_calendar_edit':
                    previous_authority=state.analysis.query_scope['season_time_authority']
                    scope['season_time_authority']['derivation']={
                        'source':'program:confirmed_session_calendar_patch','operation':'replace_calendar_year',
                        'previous_intent_version':state.intent.intent_version,
                        'previous_period':deepcopy(state.analysis.time_scope['current']),
                        'previous_evidence':previous_authority['evidence'],'current_evidence':message}
            else:
                # A real year reply updates the base year, not the missing season months.
                scope['season_time_authority']={'status':'unresolved','source':'program:season_period_not_confirmed',
                    'evidence':message}
                result.patches=[patch for patch in result.patches if patch.path not in {'time_ambiguous','clarification_requests'}]
                result.patches.append(IntentPatch(op='set',path='time_ambiguous',value=True,evidence=message))
                unresolved.append({'field':'time_scope.current','question':'请明确旺季的具体月份或起止日期。',
                    'reason':'已确认基础年份，但尚未确认旺季月份。','evidence':message})
                result.patches.append(IntentPatch(op='set',path='clarification_requests',value=unresolved,evidence=message))
            result.patches=[patch for patch in result.patches if patch.path!='query_scope']
            result.patches.append(IntentPatch(op='set',path='query_scope',value=scope,evidence=period_evidence))
    if period and state.analysis.query_scope.get('pending_filters'):
        from qa_agent.clarify.date_roles import temporal_schema_columns
        temporal=temporal_schema_columns(state.scope.get('db_id') or 'chinook')
        scope=dict(next((patch.value for patch in reversed(result.patches) if patch.path=='query_scope' and patch.op=='set'),state.analysis.query_scope))
        scope['pending_filters']=[item for item in scope.get('pending_filters',[]) if item.get('column',item.get('field')) not in temporal]
        result.patches=[patch for patch in result.patches if patch.path!='query_scope']
        result.patches.append(IntentPatch(op='set',path='query_scope',value=scope,evidence=period_evidence))
    if result.conflict_proposals:
        result.patches.append(IntentPatch(op='add',path='conflict_proposals',
            value=[item.model_dump(exclude_unset=True) for item in result.conflict_proposals],evidence=message))
    # Actual format edits are program facts even when the model proposes no
    # patch. Recover only the supported source-bound fields, retaining every
    # operand/period/business condition; an unrelated empty reply still fails.
    from qa_agent.clarify.definition_recovery import recover_percent_precision,recover_money_precision
    formatting=state.analysis.model_copy(deep=True)
    recover_percent_precision(message,formatting,{**runtime,'current_user_message':message},preserve_confirmed=True)
    recover_money_precision(message,formatting,{**runtime,'current_user_message':message},preserve_confirmed=True)
    format_keys=('requested_percent_decimals','percent_precision_source','money_precision_source')
    actual_format=any(isinstance(formatting.query_scope.get(key),dict)
        and formatting.query_scope[key].get('authority')in{'explicit_user','current_user_message'}
        and formatting.query_scope[key].get('evidence')
        and formatting.query_scope[key]['evidence']in message
        and formatting.query_scope.get(key)!=state.analysis.query_scope.get(key)
        for key in ('percent_precision_source','money_precision_source'))
    if actual_format:
        scope=deepcopy(state.analysis.query_scope if ordinary_invoice else next((patch.value for patch in reversed(result.patches)
            if patch.path=='query_scope'and patch.op=='set'and isinstance(patch.value,dict)),state.analysis.query_scope))
        for key in format_keys:
            scope.pop(key,None)
            if key in formatting.query_scope:scope[key]=deepcopy(formatting.query_scope[key])
        result.patches=[] if ordinary_invoice else[patch for patch in result.patches if patch.path!='query_scope']
        result.patches.append(IntentPatch(op='set',path='query_scope',value=scope,evidence=message))
    return result.patches


def execution_question(state: SessionState) -> str:
    if not (state.resolutions or state.analysis.default_assumptions or state.analysis.region_scope or state.analysis.time_scope or
            state.analysis.query_scope or state.analysis.output_requirements):
        return state.effective_question
    # Original query is retained; the confirmed contract is explicit and inspectable.
    context = {"task_type": state.analysis.task_type, "metric": state.analysis.metric,
               "time_scope": state.analysis.time_scope, "comparison": state.analysis.comparison,
               "numerator": state.analysis.numerator, "denominator": state.analysis.denominator,
               "rank_object": state.analysis.rank_object, "top_n": state.analysis.top_n,
               "order":state.analysis.order,
               "region_scope": state.analysis.region_scope, "filters": state.bindings}
    context.update(query_scope=state.analysis.query_scope, output_requirements=state.analysis.output_requirements,
                   condition_sources=state.analysis.condition_sources)
    context['assumptions']=state.analysis.assumptions
    if state.resolutions:
        # Once a patch has been applied, the original prose may name retired
        # countries, artists, years or TopN. It must not be the primary question
        # again. Keep it solely as a labeled background for unchanged output
        # shape; the complete merged contract is the execution authority.
        return ("根据以下当前已合并的执行合同生成查询；合同已包含保留条件和本轮修改，不能恢复历史条件：" +
                json.dumps(context,ensure_ascii=False) +
                "\n历史首轮原文（仅供保留未修改的返回字段和输出形式，不作为筛选、指标、期间、对象或TopN依据）：" +
                state.original_question)
    return state.effective_question + "\n当前执行条件（用户显式条件优先；已批准默认只补缺项）：" + json.dumps(context, ensure_ascii=False)


def _refresh_ratio_numerator_binding(state: SessionState, patches: list[IntentPatch], linked, message: str) -> None:
    """Keep numerator evidence current without applying it to the denominator.

    The existing binding contract has no local-scope object. A verified country
    binding for a ratio is therefore tagged as numerator-only; the SQL guard
    proves it inside the numerator aggregate rather than a global WHERE.
    """
    operand_patches=[patch for patch in patches if patch.path in {'numerator','denominator'} and patch.op=='set']
    if state.analysis.task_type!='ratio' or not operand_patches:
        return
    mentions={item.mention_id:item for item in linked.mentions}
    for patch in operand_patches:
        verified=[item for item in linked.bindings if item.get('column') in {'customer.country','invoice.billing_country'} and
                  mentions.get(item.get('mention_id')) is not None and mentions[item['mention_id']].original_text in patch.evidence]
        if not verified:
            if patch.path=='denominator' and re.search(r'全部|全库|所有|同期全部',patch.evidence):
                state.bindings=[item for item in state.bindings if item.get('binding_scope')!='denominator']
                operand=state.analysis.query_scope.get('denominator')
                if isinstance(operand,dict):operand['filters']=[]
            continue
        if len(verified)!=1 or verified[0].get('operator')!='=':
            raise SessionConflict('比例操作数含多个地区候选，请先明确本次范围。')
        binding=verified[0]
        mention=mentions[binding['mention_id']]
        explicit_scope=explicit_region_scope(patch.evidence)
        prior=[item for item in state.bindings if item.get('binding_scope')==patch.path]
        if len(prior)>1 or any(item.get('column')not in {'customer.country','invoice.billing_country'}for item in prior):
            raise SessionConflict('该比例操作数已有多项独立条件，不能用单一国家替换而连带删除；请分别明确保留或删除的条件。')
        retained_scope=prior[0]['column'] if len(prior)==1 else (state.analysis.region_scope if patch.path=='numerator' else None)
        scope=explicit_scope or retained_scope or binding['column']
        scope_basis=('explicit_user_scope' if explicit_scope else 'retained_operand_scope' if retained_scope else
                     'oct12_approved_invoice_default' if scope=='invoice.billing_country' and re.search(r'发票|账单|销售额|金额|总额',patch.evidence) else 'verified_value_scope')
        updated={**binding,'column':scope,'binding_scope':patch.path,'scope_evidence':patch.evidence,'scope_basis':scope_basis}
        state.bindings=[item for item in state.bindings if item.get('binding_scope')!=patch.path and
                        not (patch.path=='numerator' and item.get('column') in {'customer.country','invoice.billing_country'} and not item.get('binding_scope'))]+[updated]
        if patch.path=='numerator':
            state.analysis.region_scope=scope if state.analysis.rank_object else None
            state.analysis.region_ambiguous=False
        setattr(state.analysis,patch.path,str(patch.value).replace(mention.original_text,str(binding['value'])))
        operand=state.analysis.query_scope.get(patch.path)
        if isinstance(operand,dict):
            operand['filters']=[deepcopy(updated)]
            operand['scope']=getattr(state.analysis,patch.path)
            operand['source_evidence']=patch.evidence
        state.analysis.evidence_spans[patch.path]=patch.evidence
        state.invalidated=sorted(set(state.invalidated)|{'fields','schema','result'})
        state.history.append({'event':'ratio_'+patch.path+'_binding_refreshed','binding':updated,
                              'retired_bindings':deepcopy(prior),
                              'intent_version':state.intent.intent_version})
    state.analysis.filters=state.bindings
    sync_contract(state)


def run_gate(request, catalog, llm, linked, trace=None, *, store: SessionStore = DEFAULT_STORE,
             engine: RuleEngine | None = None) -> GateResult:
    engine = engine or RuleEngine()
    previous = store.get(request.session_id)
    card_id = getattr(request, "clarification_id", None)
    resume = bool(card_id)
    implicit_resume=bool(pending_text_response(previous,request.message) and source_dict(request)==previous.scope)
    context=runtime_payload()
    # A full business turn beginning with "那" may change the task. With a
    # versioned brief the semantic extractor sees the complete real history;
    # do not force it through the old single-field patch heuristic.
    context_new_turn=bool(context.get('user_brief') and not implicit_resume and not resume)
    from qa_agent.clarify.season_authority import confirmed_season_calendar_edit
    season_calendar_delta=bool(previous and source_dict(request)==previous.scope and
        confirmed_season_calendar_edit(request.message,previous))
    from qa_agent.clarify.invoice_ratio_source import invoice_ratio_delta
    ratio_operand_delta=bool(previous and source_dict(request)==previous.scope and invoice_ratio_delta(request.message,previous.analysis))
    from qa_agent.nlu.ownership import country_value_delta,country_predicate_edit,country_edit_has_non_global_scope
    if previous and source_dict(request)==previous.scope and country_edit_has_non_global_scope(request.message,linked.bindings,previous):
        raise SessionConflict('当前国家条件属于局部分子、分母或未明作用域；请明确修改哪个局部条件，不能将其自动提升为全局。')
    owner_edit=(country_predicate_edit(request.message,linked.bindings,previous)if previous and
        source_dict(request)==previous.scope and not resume else None)
    owner_value_delta=bool(previous and source_dict(request)==previous.scope and
        country_value_delta(request.message,linked.bindings,previous))
    if season_calendar_delta or ratio_operand_delta or owner_value_delta or owner_edit is not None:
        context_new_turn=False
    # A pure country replacement is a delta of an already program-proved
    # distinct-count task, including sessions with a full user brief. It must
    # retain its confirmed count object rather than trust a new model mirror.
    distinct=(previous.analysis.query_scope.get('distinct_count') or {}) if previous else {}
    if (previous and distinct.get('source')=='program:explicit_distinct_tracks' and
            distinct.get('source_evidence') and distinct['source_evidence'] in previous.original_question and
            previous.analysis.metric=='record_count' and is_followup(request.message) and len(linked.bindings)==1 and
            linked.bindings[0].get('column') in {'customer.country','invoice.billing_country'} and
            linked.bindings[0].get('operator')=='=' and len(linked.mentions)==1):
        mention=linked.mentions[0]
        remainder=request.message[:mention.span[0]]+'<country>'+request.message[mention.span[1]:]
        if re.fullmatch(r'\s*(?:那|请|那就)?\s*(?:换成|改成|改为|换为)\s*<country>\s*(?:吧|呢|好吗|可以吗)?\s*[。？?!！]?\s*',remainder):
            context_new_turn=False
    followup = bool(previous and not context_new_turn and (is_followup(request.message) or implicit_resume or season_calendar_delta or ratio_operand_delta or owner_value_delta) and source_dict(request) == previous.scope)
    resolved_text_choice=False
    country_delta=bool(previous and source_dict(request)==previous.scope and
                       unfilled_country_delta(request.message,previous))
    from qa_agent.clarify.temporal_followup import temporal_sort_delta,apply_temporal_sort_delta
    temporal_sort=(temporal_sort_delta(request.message,previous,catalog) if previous and
                   source_dict(request)==previous.scope and enabled('AGENT_GROUNDING_ENABLED') and not resume else None)
    rank_limit=ranking_limit_delta(request.message,previous) if previous and source_dict(request)==previous.scope and not resume else None
    if owner_edit is not None:
        state=previous
        apply_patches(state,[IntentPatch(op='set',path='filters',value=owner_edit['filters'],evidence=request.message)],
            user_message=request.message)
        if len({item.get('column')for item in state.bindings if item.get('column')in {'customer.country','invoice.billing_country'}})>1:
            state.analysis.region_scope=None;state.analysis.region_ambiguous=False
            state.analysis.condition_sources.pop('region_scope',None)
            for record in state.constraint_ledger:
                if record.get('field')=='region_scope'and record.get('status')=='active':record['status']='retired'
        state.history.append({'event':'explicit_country_predicate_edit','op':owner_edit['op'],
            'column':owner_edit['column'],'evidence':request.message,'retired_bindings':deepcopy(owner_edit['retired']),
            'intent_version':state.intent.intent_version})
        sync_contract(state)
        ambiguous=state.unresolved_values
    elif temporal_sort is not None:
        state=previous
        apply_temporal_sort_delta(state,request.message,temporal_sort)
        ambiguous=state.unresolved_values
    elif country_delta:
        state=previous
        apply_unfilled_country_delta(state,request.message)
        ambiguous=state.unresolved_values
    elif rank_limit is not None:
        state=previous
        apply_ranking_limit_delta(state,request.message,rank_limit)
        ambiguous=state.unresolved_values
    elif resume or followup:
        if previous is None:
            raise SessionConflict("会话已不存在，请重新提交完整问题。")
        state = previous
        if resume or implicit_resume:
            card = (verify_resume(state, card_id, getattr(request, "intent_version", None), source_dict(request)) if resume else state.pending_card)
            choice = getattr(request, "choice_id", None)
            if not choice:
                choice=textual_candidate_choice(state,card,request.message,linked)
                resolved_text_choice=choice is not None
            if choice:
                apply_choice(state, card, choice)
            else:
                patches = extract_patches(request.message, state, linked, llm, trace)
                if not patches:
                    raise SessionConflict("补充内容没有说明当前缺失条件，请选择选项或具体说明。")
                apply_patches(state, patches, user_message=request.message)
                _refresh_ratio_numerator_binding(state,patches,linked,request.message)
        else:
            patches = extract_patches(request.message, state, linked, llm, trace)
            if not patches:
                raise SessionConflict("没有识别到本次明确修改，请重新写出需要改变的条件。")
            apply_patches(state, patches, user_message=request.message)
            _refresh_ratio_numerator_binding(state,patches,linked,request.message)
        # Unanswered issues survive a click on another card option. Fresh messages
        # receive their own fingerprint, even when the linker reuses mention-1.
        known = {item["mention_id"] for item in state.unresolved_values}
        if not getattr(request, "choice_id", None) and not resolved_text_choice:
            for item in _persistent_ambiguities(linked, request.message):
                if item["mention_id"] not in known:
                    state.unresolved_values.append(item)
                    known.add(item["mention_id"])
            # A free-text confirmation can resolve an issue only through an
            # actual verified binding matching one of its preserved candidates.
            if any(patch.path == "filters" for patch in patches):
                remaining = []
                for issue in state.unresolved_values:
                    matched = [candidate for candidate in issue.get("candidates", [])
                               if any(candidate.get("column") == item.get("column") and
                                      candidate.get("standard_value") == item.get("value") and item.get('operator')=='='
                                      for item in linked.bindings)]
                    if len(matched) != 1:
                        remaining.append(issue)
                state.unresolved_values = remaining
        ambiguous = state.unresolved_values
    else:
        analysis = extract_intent(request.message, catalog, llm, trace, bindings=linked.bindings,
            allow_literal_month_ratio=previous is None and not linked.bindings and not linked.ambiguous)
        retained_period=False
        if (enabled('AGENT_GROUNDING_ENABLED') and previous and source_dict(request)==previous.scope):
            from qa_agent.clarify.retention import retain_referenced_ratio_period
            retained_period=retain_referenced_ratio_period(request.message,analysis,previous,context)
        bindings=analysis.filters
        country_dimensions={item.get('column')for item in bindings if item.get('column')in {'customer.country','invoice.billing_country'}}
        if len(country_dimensions)>1:
            from qa_agent.nlu.ownership import country_boolean_supported
            country_boolean_supported(request.message,bindings)
            analysis.region_scope=None;analysis.region_ambiguous=False
            analysis.condition_sources.pop('region_scope',None)
        initial_owner_retirements=[]
        if analysis.region_scope and len(country_dimensions)<=1:
            from qa_agent.nlu.ownership import verified_unique_owner
            owner_proof=verified_unique_owner(request.message,linked.bindings)
            from qa_agent.clarify.binding_provenance import bind_initial_region
            owned=[]
            for item in bindings:
                migrated,event=bind_initial_region(item,analysis.region_scope,request.message,
                    explicit=explicit_region_scope(request.message)==analysis.region_scope)
                if event:initial_owner_retirements.append(event)
                owned.append(migrated)
            bindings=[{**item,'column':analysis.region_scope,
                       'scope_evidence':(owner_proof['evidence'] if owner_proof and owner_proof['column']==analysis.region_scope else item.get('scope_evidence') if item.get('source')=='user_session_context' and item.get('scope_evidence') else 'explicit_user_country_scope' if explicit_region_scope(request.message) else 'oct12_approved_default'),
                       **({'binding_scope':'numerator'} if analysis.task_type=='ratio' and analysis.numerator and item.get('source')!='user_session_context' and not item.get('binding_scope') else {})}
                      if item.get('column') in {'customer.country','invoice.billing_country'} else item
                      for item in owned]
            analysis.filters=bindings
        state = store.start(request.session_id, source_dict(request), request.message, analysis, bindings)
        if initial_owner_retirements:
            state.history.append({'event':'initial_country_owner_bound','not_revalidated_by_value_index':True,
                'retired_field_owner_proofs':initial_owner_retirements})
        if retained_period:
            state.history.append({'event':'retained_immediate_ratio_period','previous_intent_version':previous.intent.intent_version,
                'period':analysis.time_scope,'current_user_evidence':request.message})
        state.effective_question = linked.rewritten_question
        state.unresolved_values = _persistent_ambiguities(linked, request.message)
        ambiguous = state.unresolved_values
    if enabled('AGENT_GROUNDING_ENABLED'):
        from qa_agent.nlu.ownership import remove_inapplicable_average_region_question
        remove_inapplicable_average_region_question(state.original_question,state.analysis)
        from qa_agent.clarify.assignment_scope import close_confirmed_assignment_measure
        close_confirmed_assignment_measure(state)
    decision = engine.evaluate(state.original_question, state.analysis,
                               ambiguous=ambiguous, available_years=available_years(catalog),
                               db_id=request.scope.db_id or "chinook")
    card = prepare_card(state, decision)
    store.save(state)
    return GateResult(state, decision, card, execution_question(state))


def finish_gate(gate: GateResult, *, succeeded: bool, store: SessionStore = DEFAULT_STORE) -> None:
    if gate.state.phase == "EXECUTING":
        transition(gate.state, "ANSWERED" if succeeded else "FAILED")
        gate.state.history.append({"event": "query_finished", "succeeded": succeeded,
                                   "intent_version": gate.state.intent.intent_version})
        sync_contract(gate.state)
        store.save(gate.state)


def public_metadata(gate: GateResult) -> dict[str, Any]:
    switches = gate.state.switch_card
    policy_ids=default_policy_ids(gate.state.analysis)
    return {"level": gate.decision.level, "intent_version": gate.state.intent.intent_version,
            "state": gate.state.phase, "assumptions": gate.decision.assumptions,
            "region_scope": gate.state.analysis.region_scope,
            "derived": gate.decision.derived, "invalidated": gate.state.invalidated,
            "default_policy_ids":policy_ids,
            "semantic_contract": gate.state.analysis.model_dump(),
            "patch_history": [item for item in gate.state.history if item.get('event')=='patch'],
            "invalidated_execution": (["sql_plan","sql","result"] if gate.state.invalidated else []),
            "switch": ({key: value for key, value in switches.items() if key != "trusted_options"}
                       if switches else None)}

