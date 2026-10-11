"""Glue between actual value-link evidence, the semantic gate and session state."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from hashlib import sha256
from typing import Any

from qa_agent.clarify.extractor import extract_intent, explicit_region_scope
from qa_agent.clarify.rules import RuleDecision, RuleEngine, explicit_period
from qa_agent.clarify.state import (DEFAULT_STORE, IntentPatch, PatchResponse, SessionConflict,
                                    SessionState, SessionStore, apply_choice, apply_patches,
                                    prepare_card, sync_contract, transition, verify_resume)

PATCH_PROMPT = Path(__file__).with_name("prompts") / "intent_patch.txt"
FOLLOWUP_PREFIX = re.compile(r"^\s*(?:那(?:就)?|改(?:成|为|按)|换(?:成|为)|还是|同样(?:的)?|再(?:看|查)|把.{0,24}改|按(?:销售额|购买数量|歌单)|换一个)")


@dataclass
class GateResult:
    state: SessionState
    decision: RuleDecision
    card: dict | None
    question: str


def is_followup(question: str) -> bool:
    return bool(FOLLOWUP_PREFIX.search(question))


def source_dict(request) -> dict:
    return request.scope.model_dump(mode="json")


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
    if not state or not (getattr(request,'clarification_id',None) or is_followup(request.message)) or source_dict(request)!=state.scope:
        return None
    explicit_fields=field_scope(request.message,index)
    if explicit_fields:
        return extract_mentions(request.message,index,fields=explicit_fields)
    fields={item['column'] for item in state.bindings if item.get('column')}
    fields.update(candidate['column'] for issue in state.unresolved_values for candidate in issue.get('candidates',[]) if candidate.get('column'))
    if not fields:return None
    return extract_mentions(request.message,index,fields=tuple(sorted(fields)))


def available_years(catalog) -> list[int]:
    # Catalog metadata is actual database evidence, not evidence of complete years.
    years = (catalog.metadata.get("invoice_years") or catalog.metadata.get("order_years") or
             catalog.metadata.get("sales_order_years") or catalog.metadata.get("purchase_order_years"))
    if years:
        return sorted({int(value) for value in years})
    return []


def _binding_key(item: dict) -> tuple:
    return (item.get("column"), item.get("operator"), json.dumps(item.get("value"), sort_keys=True, ensure_ascii=False))


def _ground_patch_filters(patches: list[IntentPatch], state: SessionState, linked, *, derived_scope: str | None = None) -> None:
    allowed = list(state.bindings) + list(linked.bindings)
    if derived_scope:
        allowed += [{**item,'column':derived_scope} for item in state.bindings
                    if item.get('column') in {'invoice.billing_country','customer.country'}]
    for patch in patches:
        if patch.path != "filters" or patch.op == "remove":
            continue
        values = patch.value if isinstance(patch.value, list) else [patch.value]
        for binding in values:
            if not isinstance(binding, dict) or not any(
                _binding_key(item) == _binding_key(binding)
                for item in allowed
            ):
                raise SessionConflict("补丁中的筛选值没有真实值链接或此前用户确认依据。")
        if patch.op == "set":
            new_columns = {item.get("column") for item in values if isinstance(item, dict)}
            if any((derived_scope if derived_scope and old.get('column') in {'invoice.billing_country','customer.country'} else old.get('column')) not in new_columns for old in state.bindings):
                raise SessionConflict("替换筛选时丢失了未被用户修改的其它条件；删除条件需要明确 remove 补丁。")


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
    current_card = state.pending_card or state.switch_card or {}
    result = llm.complete_json(
        PATCH_PROMPT.read_text(encoding="utf-8"),
        json.dumps({"message": message, "current_intent": state.analysis.model_dump(),
                    "current_card": {key: value for key, value in current_card.items() if key != "trusted_options"},
                    "verified_value_bindings": linked.bindings}, ensure_ascii=False),
        PatchResponse, trace=trace)
    for patch in result.patches:
        if patch.path in {"assumptions","default_assumptions","evidence_spans"}:
            raise SessionConflict("默认口径与确认记录只能由程序依据规则生成，模型不能修改审核依据。")
        if not patch.evidence or patch.evidence not in message:
            raise SessionConflict("模型补丁未提供本次用户真实原文依据。")
    scope_patches=[patch for patch in result.patches if patch.path=='region_scope' and patch.op=='set']
    derived_scope=None
    if scope_patches:
        written_scope=explicit_region_scope(message)
        if written_scope is None or any(patch.value!=written_scope for patch in scope_patches):
            raise SessionConflict('地区字段修改没有本次用户明确的账单国家或客户所在地原文依据。')
        if len({item.get('column') for item in state.bindings if item.get('column') in {'invoice.billing_country','customer.country'}})>1:
            raise SessionConflict('当前有两个独立国家筛选，请明确需要改动的具体条件，不能同时合并或迁移。')
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
        if migration and not cancellation:
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
    _ground_patch_filters(result.patches, state, linked,derived_scope=derived_scope)
    # Explicit calendar text is converted by code and takes precedence over model dates.
    period = explicit_period(message)
    if period:
        overridden={'time_scope','time_scope.current','time_scope.current.start','time_scope.current.end',
                    'time_scope.current.grain','time_scope.current.label'}
        result.patches = [item for item in result.patches if item.path not in overridden]
        result.patches.append(IntentPatch(op="set", path="time_scope", value=period,
                                          evidence=next(iter(re.findall(r"\d{4}\s*年(?:\s*\d{1,2}\s*月)?", message)), "")))
        result.patches.append(IntentPatch(op="set", path="time_ambiguous", value=False,
                                          evidence=next(iter(re.findall(r"\d{4}\s*年(?:\s*\d{1,2}\s*月)?", message)), "")))
    return result.patches


def execution_question(state: SessionState) -> str:
    if not state.resolutions:
        return state.effective_question
    # Original query is retained; the confirmed contract is explicit and inspectable.
    context = {"task_type": state.analysis.task_type, "metric": state.analysis.metric,
               "time_scope": state.analysis.time_scope, "comparison": state.analysis.comparison,
               "numerator": state.analysis.numerator, "denominator": state.analysis.denominator,
               "rank_object": state.analysis.rank_object, "top_n": state.analysis.top_n,
               "order":state.analysis.order,
               "region_scope": state.analysis.region_scope, "filters": state.bindings}
    return state.original_question + "\n用户已确认的当前条件（替代被改动的旧条件，其余条件保留）：" + json.dumps(context, ensure_ascii=False)


def run_gate(request, catalog, llm, linked, trace=None, *, store: SessionStore = DEFAULT_STORE,
             engine: RuleEngine | None = None) -> GateResult:
    engine = engine or RuleEngine()
    previous = store.get(request.session_id)
    card_id = getattr(request, "clarification_id", None)
    resume = bool(card_id)
    followup = bool(previous and is_followup(request.message) and source_dict(request) == previous.scope)
    if resume or followup:
        if previous is None:
            raise SessionConflict("会话已不存在，请重新提交完整问题。")
        state = previous
        if resume:
            card = verify_resume(state, card_id, getattr(request, "intent_version", None), source_dict(request))
            choice = getattr(request, "choice_id", None)
            if choice:
                apply_choice(state, card, choice)
            else:
                patches = extract_patches(request.message, state, linked, llm, trace)
                if not patches:
                    raise SessionConflict("补充内容没有说明当前缺失条件，请选择选项或具体说明。")
                apply_patches(state, patches, user_message=request.message)
        else:
            patches = extract_patches(request.message, state, linked, llm, trace)
            if not patches:
                raise SessionConflict("没有识别到本次明确修改，请重新写出需要改变的条件。")
            apply_patches(state, patches, user_message=request.message)
        # Unanswered issues survive a click on another card option. Fresh messages
        # receive their own fingerprint, even when the linker reuses mention-1.
        known = {item["mention_id"] for item in state.unresolved_values}
        if not getattr(request, "choice_id", None):
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
                                      candidate.get("standard_value") == item.get("value")
                                      for item in linked.bindings)]
                    if len(matched) != 1:
                        remaining.append(issue)
                state.unresolved_values = remaining
        ambiguous = state.unresolved_values
    else:
        analysis = extract_intent(request.message, catalog, llm, trace, bindings=linked.bindings)
        bindings=linked.bindings
        if analysis.region_scope:
            bindings=[{**item,'column':analysis.region_scope,'scope_evidence':'explicit_user_country_scope'}
                      if item.get('column') in {'customer.country','invoice.billing_country'} else item
                      for item in bindings]
            analysis.filters=bindings
        state = store.start(request.session_id, source_dict(request), request.message, analysis, bindings)
        state.effective_question = linked.rewritten_question
        state.unresolved_values = _persistent_ambiguities(linked, request.message)
        ambiguous = state.unresolved_values
    decision = engine.evaluate(state.original_question, state.analysis,
                               ambiguous=ambiguous, available_years=available_years(catalog),
                               db_id=request.scope.db_id or "chinook")
    card = prepare_card(state, decision)
    store.save(state)
    return GateResult(state, decision, card, execution_question(state))


def finish_gate(gate: GateResult, *, succeeded: bool, store: SessionStore = DEFAULT_STORE) -> None:
    if gate.state.phase == "EXECUTING":
        transition(gate.state, "ANSWERED")
        gate.state.history.append({"event": "query_finished", "succeeded": succeeded,
                                   "intent_version": gate.state.intent.intent_version})
        sync_contract(gate.state)
        store.save(gate.state)


def public_metadata(gate: GateResult) -> dict[str, Any]:
    switches = gate.state.switch_card
    return {"level": gate.decision.level, "intent_version": gate.state.intent.intent_version,
            "state": gate.state.phase, "assumptions": gate.decision.assumptions,
            "region_scope": gate.state.analysis.region_scope,
            "derived": gate.decision.derived, "invalidated": gate.state.invalidated,
            "switch": ({key: value for key, value in switches.items() if key != "trusted_options"}
                       if switches else None)}
