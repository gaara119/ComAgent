"""Small persistent state machine with trusted patches and stale-card rejection."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field,model_validator,field_validator

from qa_agent.clarify.rules import SemanticIntent, RuleDecision
from qa_agent.schemas import IntentContract
from qa_agent.clarify.normalization import normalize_internal_contract,validate_scope_structure
from qa_agent.clarify.conflict_contract import ConflictProposal

MODEL_PATCH_PATHS=[field for field in SemanticIntent.model_fields if field not in {'conflicts','conflict_proposals'}]

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SessionConflict(ValueError):
    """The supplied card or intent version no longer belongs to this task."""


class IntentPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["set", "add", "remove"]
    path: str
    value: Any = None
    evidence: str = ""

    @model_validator(mode='after')
    def validate_scope_patch(self):
        if self.path=='query_scope' and self.op=='set':
            if not isinstance(self.value,dict):raise ValueError('query_scope补丁必须是完整对象，不能静默删除现有范围。')
            self.value=validate_scope_structure(self.value)
        return self


class PatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Model-facing schema is narrower than the direct internal constructor.
    # Legacy program IntentPatch invalid-path checks still run in apply_patches.
    patches: list[IntentPatch] = Field(default_factory=list)
    conflict_proposals: list[ConflictProposal] = Field(default_factory=list,exclude=True)

    @field_validator('patches',mode='before')
    @classmethod
    def validate_model_patch_paths(cls,value):
        if isinstance(value,list):
            for item in value:
                # Python IntentPatch instances are internal legacy program
                # constructions, not model JSON. Keep apply's atomic checks.
                if isinstance(item,dict) and item.get('path') not in MODEL_PATCH_PATHS:
                    raise ValueError('模型补丁path必须是合法顶层字段：'+', '.join(MODEL_PATCH_PATHS)+
                        '；平均粒度应通过metric或完整query_scope表达，不能静默丢弃非法补丁。')
        return value

    @classmethod
    def model_json_schema(cls,*args,**kwargs):
        schema=super().model_json_schema(*args,**kwargs)
        schema['$defs']['IntentPatch']['properties']['path']['enum']=list(MODEL_PATCH_PATHS)
        return schema


class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    scope: dict[str, Any]
    phase: Literal["IDLE", "CHECKING", "WAITING_CLARIFICATION", "EXECUTING", "ANSWERED", "FAILED"] = "IDLE"
    intent: IntentContract
    analysis: SemanticIntent
    original_question: str
    effective_question: str
    bindings: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_values: list[dict[str, Any]] = Field(default_factory=list)
    pending_card: dict[str, Any] | None = None
    switch_card: dict[str, Any] | None = None
    resolutions: list[dict[str, Any]] = Field(default_factory=list)
    invalidated: list[str] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)
    constraint_ledger: list[dict[str, Any]] = Field(default_factory=list)
    conflict_ledger: list[dict[str, Any]] = Field(default_factory=list)
    last_updated: str = ""


TRANSITIONS = {
    "IDLE": {"CHECKING"},
    "CHECKING": {"WAITING_CLARIFICATION", "EXECUTING"},
    "WAITING_CLARIFICATION": {"CHECKING"},
    "EXECUTING": {"ANSWERED", "FAILED"},
    "ANSWERED": {"CHECKING"},
    "FAILED": {"CHECKING"},
}
ALLOWED_PATHS = set(SemanticIntent.model_fields)
INVALIDATION = {
    "region_scope": ["result"], "filters": ["result"],
    "time_scope": ["derived_period", "result"],
    "comparison": ["derived_period", "result"],
    "metric": ["grain", "aggregation", "fields", "schema", "result"],
    "rank_object": ["grain", "fields", "schema", "result"],
    "grouping": ["grain", "fields", "schema", "result"],
    "top_n": ["result"],
    "order": ["result"],
}


def sync_contract(state: SessionState) -> None:
    semantic = state.analysis
    state.intent.task_type = semantic.task_type
    state.intent.metric = semantic.metric
    state.intent.time_scope = semantic.time_scope
    # Semantic filters are strictly restricted to verified value-link records.
    # Numeric/date predicates remain in the original query and structured time.
    state.intent.filters = list(state.bindings)
    state.intent.grouping = semantic.grouping
    state.intent.order = ({**(semantic.order or {}), "rank_object": semantic.rank_object, "top_n": semantic.top_n}
                          if semantic.task_type == "ranking" else semantic.order)
    state.intent.assumptions = semantic.assumptions
    state.intent.unresolved = state.pending_card.get("issues", []) if state.pending_card else []


class SessionStore:
    def __init__(self, root: Path | None = None):
        self.root = root or PROJECT_ROOT / ".runtime" / "sessions"
        self.cache: dict[str, SessionState] = {}
        self._lock = RLock()
        self._session_locks: dict[str, RLock] = {}

    def path(self, session_id: str) -> Path:
        return self.root / (sha256(session_id.encode("utf-8")).hexdigest() + ".json")

    @contextmanager
    def locked(self, session_id: str):
        with self._lock:
            lock = self._session_locks.setdefault(session_id, RLock())
        with lock:
            yield

    def get(self, session_id: str) -> SessionState | None:
        with self._lock:
            if session_id in self.cache:
                return self.cache[session_id].model_copy(deep=True)
            path = self.path(session_id)
            if not path.is_file():
                return None
            state = SessionState.model_validate_json(path.read_text(encoding="utf-8"))
            from qa_agent.clarify.conflict_authority import restore_conflict_ledger
            if state.conflict_ledger:
                restore_conflict_ledger(state)
            if state.session_id != session_id:
                raise SessionConflict("会话文件与请求编号不一致。")
            self.cache[session_id] = state
            return state.model_copy(deep=True)

    def save(self, state: SessionState) -> None:
        with self._lock:
            from qa_agent.clarify.conflict_authority import commit_conflict_ledger
            commit_conflict_ledger(state)
            if state.analysis._retired_conflict_proposals:
                state.history.append({'event':'retired_model_conflict_proposals',
                    'intent_version':state.intent.intent_version,
                    'proposals':state.analysis._retired_conflict_proposals})
                state.analysis._retired_conflict_proposals=[]
            state.last_updated = datetime.now(timezone.utc).isoformat()
            self.root.mkdir(parents=True, exist_ok=True)
            target = self.path(state.session_id)
            temporary = target.with_suffix(".tmp")
            temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
            temporary.replace(target)
            self.cache[state.session_id] = state.model_copy(deep=True)

    def start(self, session_id: str, scope: dict, question: str, analysis: SemanticIntent,
              bindings: list[dict] | None = None) -> SessionState:
        previous = self.get(session_id)
        # A new question is a new intent: no previous filters are silently inherited.
        version = previous.intent.intent_version + 1 if previous else 1
        state = SessionState(session_id=session_id, scope=scope,
                             intent=IntentContract(route="sql", intent_version=version),
                             analysis=analysis, original_question=question, effective_question=question,
                             bindings=bindings or [])
        if previous:
            state.constraint_ledger=[dict(record) for record in previous.constraint_ledger]
            for record in state.constraint_ledger:
                if record.get('status')=='active' and record.get('lifetime')!='persistent':
                    record['status']='retired'
                    record['retired_at_version']=version
                    record['retirement_reason']='new_task_boundary'
        for field,source in analysis.condition_sources.items():
            state.constraint_ledger.append({'field':field,'value':analysis.model_dump().get(field),
                                            **source,'intent_version':version,'status':'active'})
        transition(state, "CHECKING")
        sync_contract(state)
        self.save(state)
        return state


def transition(state: SessionState, destination: str) -> None:
    if destination not in TRANSITIONS[state.phase]:
        raise SessionConflict(f"非法会话状态迁移：{state.phase} → {destination}")
    state.history.append({"event": "transition", "from": state.phase, "to": destination,
                          "intent_version": state.intent.intent_version})
    state.phase = destination


def prepare_card(state: SessionState, decision: RuleDecision) -> dict | None:
    state.analysis = decision.analysis
    options = [option for issue in decision.issues for option in issue.options]
    public_options = [{key: value for key, value in option.items() if key != "patch"} for option in options]
    if decision.level == "L2":
        card = {"clarification_id": str(uuid4()), "intent_version": state.intent.intent_version,
                "level": "L2", "question": " ".join(issue.question for issue in decision.issues),
                "reason": " ".join(issue.reason for issue in decision.issues),
                "issues": [item.as_dict(public=True) for item in decision.issues],
                "options": public_options, "resume_supported": True}
        # Patches are held only by the server; clients submit stable option ids.
        state.pending_card = {**card, "trusted_options": options}
        state.switch_card = None
        transition(state, "WAITING_CLARIFICATION")
    else:
        card = None
        state.pending_card = None
        if decision.switches:
            state.switch_card = {"clarification_id": str(uuid4()), "intent_version": state.intent.intent_version,
                                 "level": decision.level, "trusted_options": decision.switches,
                                 "options": [{key: value for key, value in item.items() if key != "patch"}
                                             for item in decision.switches]}
        else:
            state.switch_card = None
        transition(state, "EXECUTING")
    sync_contract(state)
    return card


def verify_resume(state: SessionState, clarification_id: str | None,
                  intent_version: int | None, scope: dict) -> dict:
    card = state.pending_card or state.switch_card
    if scope != state.scope:
        raise SessionConflict("来源范围已经改变，请重新提交该来源的问题。")
    if card is None or clarification_id != card["clarification_id"] or intent_version != state.intent.intent_version:
        raise SessionConflict("这张澄清卡片已经失效，请使用当前问题的最新卡片。")
    return card


def apply_patches(state: SessionState, patches: list[IntentPatch], *, user_message: str, trusted_region_choice: bool = False) -> None:
    # Authority audit and ledger migration are part of the same transaction as
    # ordinary conditions. No partial migration escapes a rejected patch.
    candidate=state.model_copy(deep=True)
    _apply_patches_in_place(candidate,patches,user_message=user_message,trusted_region_choice=trusted_region_choice)
    for field in SessionState.model_fields:setattr(state,field,getattr(candidate,field))


def _apply_patches_in_place(state: SessionState, patches: list[IntentPatch], *, user_message: str, trusted_region_choice: bool = False) -> None:
    from qa_agent.clarify.conflict_authority import (commit_conflict_ledger, restore_conflict_ledger,
        adjudicate_conflict_proposals, reconcile_conflicts_after_patch)
    from qa_agent.clarify.grounding import runtime_payload
    # Commit input-only proposals before rebuilding the intent model. A model
    # cannot clear the authority ledger by patching its public projection.
    adjudicate_conflict_proposals(state.original_question,state.analysis,runtime_payload())
    commit_conflict_ledger(state)
    previous_analysis=state.analysis.model_copy(deep=True)
    authority_patches=[patch for patch in patches if patch.path in {'conflicts','conflict_proposals'}]
    patches=[patch for patch in patches if patch.path not in {'conflicts','conflict_proposals'}]
    authority_changed=False
    if authority_patches:
        proposed=SemanticIntent()
        for patch in authority_patches:
            if patch.path=='conflict_proposals' and patch.op in {'set','add'}:
                values=patch.value if isinstance(patch.value,list) else [patch.value]
                proposed.conflict_proposals.extend(ConflictProposal.model_validate(value) for value in values)
            elif patch.path=='conflicts' and patch.op in {'set','add'}:
                values=patch.value if isinstance(patch.value,list) else [patch.value]
                proposed.conflicts.extend(str(value) for value in values if value)
        adjudicate_conflict_proposals(user_message,proposed,runtime_payload(),prior_records=state.conflict_ledger)
        by_id={record['record_id']:record for record in state.conflict_ledger}
        for record in proposed._program_conflict_records:
            existing=by_id.get(record['record_id'])
            if existing is None:
                by_id[record['record_id']]=record;authority_changed=True
            else:
                # Repeated model input cannot override a real user rejection
                # or a program resolution of the same source-bound point.
                existing['proposal_ids']=list(dict.fromkeys(existing['proposal_ids']+record['proposal_ids']))
        state.conflict_ledger=list(by_id.values())
        state.history.append({'event':'conflict_proposal_patch_audit','not_authoritative':True,
            'status':'unverified','proposals':[patch.model_dump() for patch in authority_patches]})
        restore_conflict_ledger(state)
    payload = state.analysis.model_dump()
    from copy import deepcopy
    previous_query_scope=deepcopy(state.analysis.query_scope)
    previous_region=state.analysis.region_scope
    previous_filters=deepcopy(state.bindings)
    original_columns={item.get('column') for item in state.bindings}
    if (any(patch.path=='region_scope' for patch in patches) and
        len(original_columns & {'invoice.billing_country','customer.country'})>1):
        raise SessionConflict('当前有两个独立国家筛选，请明确需要改动的具体条件，不能同时合并或迁移。')
    invalidated = set()
    retired_owner_proofs = []
    actual = []
    for patch in patches:
        if patch.path not in ALLOWED_PATHS:
            raise SessionConflict(f"不允许修改该意图字段：{patch.path}")
        if patch.evidence and patch.evidence not in user_message:
            raise SessionConflict("意图补丁的原文依据不在本次用户输入中。")
        old = payload.get(patch.path)
        if patch.op == "set":
            payload[patch.path] = patch.value
        elif patch.op == "add":
            if not isinstance(old, list):
                raise SessionConflict("add 仅能用于列表型条件。")
            values = patch.value if isinstance(patch.value, list) else [patch.value]
            for value in values:
                if value not in old:
                    old.append(value)
        elif patch.op == "remove":
            if isinstance(old, list):
                values = patch.value if isinstance(patch.value, list) else [patch.value]
                payload[patch.path] = [item for item in old if item not in values]
            else:
                payload[patch.path] = None
        invalidated.update(INVALIDATION.get(patch.path, ["result"]))
        actual.append(patch.model_dump())
    if actual:
        if any(patch.path=="metric" for patch in patches):
            # In a ranking, the ordinary primary sort is derived from the
            # chosen measure. The observed DEV contract changed metric to
            # detail_revenue but retained order.field=purchased_quantity.
            # Update only an old metric-ID reference, preserving direction and
            # tie-breakers. An explicit independent order edit remains intact.
            if (payload.get('task_type')=='ranking' and payload.get('order') and
                    not any(patch.path=='order' for patch in patches) and
                    payload.get('metric')!=state.analysis.metric):
                order=dict(payload['order'])
                changed=False
                for key in ('field','by','metric'):
                    if order.get(key)==state.analysis.metric:
                        order[key]=payload['metric'];changed=True
                if changed:
                    payload['order']=order
                    invalidated.update({'order','result'})
            # Confirmed old choices belong in history, not in the current
            # assumptions after a free-text metric change. A trusted card
            # supplies the new current confirmation in its assumptions patch.
            has_current_confirmation=any(patch.path=="assumptions" for patch in patches)
            stale=lambda text:("热门曲目按" in text or "“客户谁买得最多”按" in text or
                               (not has_current_confirmation and "用户已选择热门曲目口径：" in text))
            payload['assumptions']=[text for text in payload.get('assumptions',[]) if not stale(text)]
            payload['default_assumptions']=[text for text in payload.get('default_assumptions',[]) if not stale(text)]
            if (payload.get('metric')!='invoice_revenue' and
                    any('销售额占比默认以同期全部发票金额' in text for text in state.analysis.default_assumptions) and
                    not any(patch.path=='denominator' for patch in patches)):
                # An amount-specific default is stale after changing the metric
                # to customer counts or another quantity. Ask for that scope.
                payload['denominator']=None
                payload['assumptions']=[text for text in payload.get('assumptions',[]) if '销售额占比默认以同期全部发票金额' not in text]
                payload['default_assumptions']=[text for text in payload.get('default_assumptions',[]) if '销售额占比默认以同期全部发票金额' not in text]
        if any(patch.path=="top_n" for patch in patches):
            payload['assumptions']=[text for text in payload.get('assumptions',[]) if "未指定排名条数" not in text]
            payload['default_assumptions']=[text for text in payload.get('default_assumptions',[]) if "未指定排名条数" not in text]
        if any(patch.path=='time_scope' for patch in patches):
            payload['assumptions']=[text for text in payload.get('assumptions',[]) if '未指定期间，按全部现有数据' not in text]
            payload['default_assumptions']=[text for text in payload.get('default_assumptions',[]) if '未指定期间，按全部现有数据' not in text]
        if any(patch.path=='denominator' for patch in patches):
            payload['assumptions']=[text for text in payload.get('assumptions',[]) if '销售额占比默认以同期全部发票金额' not in text]
            payload['default_assumptions']=[text for text in payload.get('default_assumptions',[]) if '销售额占比默认以同期全部发票金额' not in text]
        # Derived comparison periods become stale when the current period changes.
        if "derived_period" in invalidated and payload.get("time_scope"):
            base=payload['time_scope'].get('base') or {}
            if base.get('derived_from'):
                payload["time_scope"] = {key: value for key, value in payload["time_scope"].items() if key != "base"}
        # A model can mirror a full query_scope but cannot manufacture a
        # program precision grant. Retain a previous real grant only when its
        # original evidence remains in actual user text; new real formatting
        # choices are recovered below from the actual current message.
        scope=payload.get('query_scope')or{}
        for key in ('requested_percent_decimals','percent_precision_source','money_precision_source'):scope.pop(key,None)
        previous_source=previous_query_scope.get('percent_precision_source')or{}
        quote=str(previous_source.get('evidence')or'')
        actual_texts=[state.original_question,str(runtime_payload().get('user_brief')or'')]+[
            str(resolution.get('message')or'')for resolution in state.resolutions]
        confirmed_precision=bool(previous_source.get('source')in{'program:explicit_percent_precision',
            'program:explicit_percent_precision_removed','program:explicit_percent_precision_pending'}and quote and
            any(quote in text for text in actual_texts))
        if confirmed_precision:
            if previous_query_scope.get('requested_percent_decimals')is not None:
                scope['requested_percent_decimals']=deepcopy(previous_query_scope['requested_percent_decimals'])
            scope['percent_precision_source']=deepcopy(previous_source)
        previous_money=previous_query_scope.get('money_precision_source')or{}
        money_quote=str(previous_money.get('evidence')or'')
        confirmed_money=bool(previous_money.get('source')=='program:actual_user_money_precision'and money_quote and
            any(money_quote in text for text in actual_texts))
        if confirmed_money:scope['money_precision_source']=deepcopy(previous_money)
        payload['query_scope']=scope
        state.analysis = SemanticIntent.model_validate(payload)
        restore_conflict_ledger(state)
        normalize_internal_contract(state.analysis,user_message)
        from qa_agent.clarify.definition_recovery import recover_percent_precision,recover_money_precision
        patch_runtime={**runtime_payload(),'current_user_message':user_message}
        recover_percent_precision(user_message,state.analysis,patch_runtime,preserve_confirmed=confirmed_precision)
        recover_money_precision(user_message,state.analysis,patch_runtime,preserve_confirmed=confirmed_money)
        state.intent.intent_version += 1
        for patch in patches:
            for record in state.constraint_ledger:
                if record.get('field')==patch.path and record.get('status')=='active':
                    record['status']='retired'
                    record['retired_at_version']=state.intent.intent_version
            lifetime=('persistent' if any(word in user_message for word in ('以后','后面都','接下来都','一直','默认都','整个会话')) else 'task')
            record={'field':patch.path,'value':state.analysis.model_dump().get(patch.path),
                    'source':'explicit_user','evidence':patch.evidence or user_message,
                    'lifetime':lifetime,'applies_to':patch.path if patch.path in {'numerator','denominator'} else 'global','intent_version':state.intent.intent_version,
                    'status':'retired' if patch.op=='remove' or patch.value is None else 'active'}
            state.constraint_ledger.append(record)
            state.analysis.condition_sources[patch.path]={key:value for key,value in record.items() if key not in {'value','status','intent_version'}}
        if any(patch.path == "filters" for patch in patches):
            state.bindings = list(state.analysis.filters)
        if any(patch.path == "region_scope" for patch in patches) and state.analysis.region_scope:
            from qa_agent.clarify.binding_provenance import migrate_region_bindings
            state.bindings, retired_owner_proofs = migrate_region_bindings(
                state.bindings, state.analysis.region_scope, user_message, state.intent.intent_version,previous_filters)
            from qa_agent.clarify.binding_provenance import migrate_operand_bindings
            if trusted_region_choice or not any(p.path=='query_scope' for p in patches):
                state.analysis.query_scope,retired_operand_proofs=migrate_operand_bindings(
                    state.analysis.query_scope,previous_query_scope,previous_region,state.analysis.region_scope,
                    user_message,state.intent.intent_version)
                retired_owner_proofs.extend(retired_operand_proofs)
            state.analysis.filters = state.bindings
            state.analysis.region_ambiguous = False
        if {item.get('column') for item in state.bindings}!=original_columns:
            invalidated.update({'fields','schema','result'})
        state.invalidated = sorted(invalidated)
        state.history.append({"event": "patch", "patches": actual,
                              "intent_version": state.intent.intent_version, "invalidated": state.invalidated,
                              **({"retired_field_owner_proofs": retired_owner_proofs} if retired_owner_proofs else {})})
        state.resolutions.append({"message": user_message, "patches": actual,
                                  "previous_filters":previous_filters})
        reconcile_conflicts_after_patch(state,[patch.path for patch in patches],user_message,previous_analysis)
        commit_conflict_ledger(state)
    elif authority_changed:
        state.intent.intent_version+=1
        state.invalidated=sorted(set(state.invalidated)|{'result'})
        state.history.append({'event':'conflict_authority_changed','intent_version':state.intent.intent_version,
            'invalidated':['result'],'source':'program:verified_proposal_commit'})
    commit_conflict_ledger(state)
    state.pending_card = None
    state.switch_card = None
    transition(state, "CHECKING")
    sync_contract(state)


def apply_choice(state: SessionState, card: dict, choice_id: str) -> dict:
    match = next((item for item in card.get("trusted_options", []) if item["id"] == choice_id), None)
    if match is None:
        raise SessionConflict("所选选项不在当前澄清卡片中。")
    patch = match["patch"]
    if patch.get('op')=='reject_conflict':
        current=state.pending_card
        if (not current or card.get('clarification_id')!=current.get('clarification_id') or
                card.get('intent_version')!=state.intent.intent_version):
            raise SessionConflict('候选歧义卡片已失效，不能退休当前冲突。')
        record=next((item for item in state.conflict_ledger if item['record_id']==patch.get('record_id') and item['status']=='unknown'),None)
        if record is None:raise SessionConflict('该未核验候选歧义已不存在。')
        state.intent.intent_version+=1
        record.update(status='retired',reason_code='explicit_trusted_user_rejection',
            evaluated_intent_version=state.intent.intent_version)
        from qa_agent.clarify.conflict_authority import restore_conflict_ledger
        restore_conflict_ledger(state)
        state.invalidated=['result']
        state.history.append({'event':'conflict_point_rejected','record_id':record['record_id'],
            'choice_id':choice_id,'clarification_id':card['clarification_id'],
            'intent_version':state.intent.intent_version,'evidence':match['label']})
        state.resolutions.append({'message':match['label'],'record_id':record['record_id'],'patches':[]})
        state.pending_card=None;state.switch_card=None
        transition(state,'CHECKING');sync_contract(state)
        return match
    if patch.get('op')=='bundle':
        raw=patch.get('patches')
        if not isinstance(raw,list) or not 1<=len(raw)<=12:
            raise SessionConflict('可信切换选项没有合法的原子补丁集合。')
        patches=[IntentPatch.model_validate(item) for item in raw]
        candidate=state.model_copy(deep=True)
        apply_patches(candidate,patches,user_message=match['label'],trusted_region_choice=True)
        from qa_agent.clarify.binding_provenance import attach_region_choice
        attach_region_choice(candidate,card,match,patches)
        candidate.history.append({'event':'trusted_default_switch','choice_id':choice_id,
                                  'clarification_id':card['clarification_id'],'intent_version':candidate.intent.intent_version})
        for field in SessionState.model_fields:setattr(state,field,getattr(candidate,field))
        return match
    valid_current_choice=False
    if patch.get('path')=='time_scope' and patch.get('op')=='set' and isinstance(patch.get('value'),dict):
        try:
            current=patch['value']['current']
            valid_current_choice=date.fromisoformat(current['start'])<date.fromisoformat(current['end'])
        except (KeyError,TypeError,ValueError):
            pass
        if not valid_current_choice:
            raise SessionConflict('可信日期选项没有有效的当前期间，请重新提交明确日期。')
    if patch["op"] == "resolve_value":
        binding = {"mention_id": patch["mention_id"], "column": patch["column"],
                   "operator": "=", "value": patch["value"],
                   "candidate_id": patch["candidate_id"], "method": "explicit_user_choice",
                   "evidence_ref": f"clarification:{card['clarification_id']}:{choice_id}"}
        bindings = [item for item in state.bindings if item.get("mention_id") != patch["mention_id"]]
        bindings.append(binding)
        apply_patches(state, [IntentPatch(op="set", path="filters", value=bindings)], user_message=match["label"])
        state.unresolved_values = [item for item in state.unresolved_values if item["mention_id"] != patch["mention_id"]]
        state.history[-1]["resolved_value_issue"] = patch["mention_id"]
    else:
        patches = [IntentPatch.model_validate(patch)]
        if patch["path"] == "region_scope":
            patches.append(IntentPatch(op="set", path="region_ambiguous", value=False))
            # Changing the country scope preserves the selected country value.
            countries = [item for item in state.bindings if item.get("column") in {"customer.country", "invoice.billing_country"}]
            if countries:
                others = [item for item in state.bindings if item not in countries]
                selected = {**countries[0], "column": patch["value"]}
                patches.append(IntentPatch(op="set", path="filters", value=others + [selected]))
        elif patch['path']=='time_scope' and valid_current_choice:
            # The trusted calendar choice is actual user confirmation, just
            # like an explicit free-text period. It clears only period ambiguity.
            patches.append(IntentPatch(op='set',path='time_ambiguous',value=False))
        elif patch["path"] == "metric":
            assumptions = [text for text in state.analysis.assumptions if
                           "热门曲目按" not in text and "用户已选择热门曲目口径：" not in text]
            assumptions.append(f"用户已选择热门曲目口径：{match['label']}。")
            patches.append(IntentPatch(op="set", path="assumptions", value=assumptions))
        elif match["id"] == "playlist_snapshot":
            patches.append(IntentPatch(op="add", path="assumptions",
                                        value="用户明确取消期间约束，歌单次数按当前收录快照统计。"))
        apply_patches(state, patches, user_message=match["label"],trusted_region_choice=True)
        from qa_agent.clarify.binding_provenance import attach_region_choice
        attach_region_choice(state,card,match,patches)
    return match


DEFAULT_STORE = SessionStore()
