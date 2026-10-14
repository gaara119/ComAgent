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

from pydantic import BaseModel, ConfigDict, Field

from qa_agent.clarify.rules import SemanticIntent, RuleDecision
from qa_agent.schemas import IntentContract

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SessionConflict(ValueError):
    """The supplied card or intent version no longer belongs to this task."""


class IntentPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["set", "add", "remove"]
    path: str
    value: Any = None
    evidence: str = ""


class PatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patches: list[IntentPatch] = Field(default_factory=list)


class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    scope: dict[str, Any]
    phase: Literal["IDLE", "CHECKING", "WAITING_CLARIFICATION", "EXECUTING", "ANSWERED"] = "IDLE"
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
    last_updated: str = ""


TRANSITIONS = {
    "IDLE": {"CHECKING"},
    "CHECKING": {"WAITING_CLARIFICATION", "EXECUTING"},
    "WAITING_CLARIFICATION": {"CHECKING"},
    "EXECUTING": {"ANSWERED"},
    "ANSWERED": {"CHECKING"},
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
            if state.session_id != session_id:
                raise SessionConflict("会话文件与请求编号不一致。")
            self.cache[session_id] = state
            return state.model_copy(deep=True)

    def save(self, state: SessionState) -> None:
        with self._lock:
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


def apply_patches(state: SessionState, patches: list[IntentPatch], *, user_message: str) -> None:
    payload = state.analysis.model_dump()
    previous_filters=[dict(item) for item in state.bindings]
    original_columns={item.get('column') for item in state.bindings}
    if (any(patch.path=='region_scope' for patch in patches) and
        len(original_columns & {'invoice.billing_country','customer.country'})>1):
        raise SessionConflict('当前有两个独立国家筛选，请明确需要改动的具体条件，不能同时合并或迁移。')
    invalidated = set()
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
        state.analysis = SemanticIntent.model_validate(payload)
        state.intent.intent_version += 1
        if any(patch.path == "filters" for patch in patches):
            state.bindings = list(state.analysis.filters)
        if any(patch.path == "region_scope" for patch in patches) and state.analysis.region_scope:
            state.bindings = [{**item, "column": state.analysis.region_scope}
                              if item.get("column") in {"customer.country", "invoice.billing_country"}
                              else item for item in state.bindings]
            state.analysis.filters = state.bindings
            state.analysis.region_ambiguous = False
        if {item.get('column') for item in state.bindings}!=original_columns:
            invalidated.update({'fields','schema','result'})
        state.invalidated = sorted(invalidated)
        state.history.append({"event": "patch", "patches": actual,
                              "intent_version": state.intent.intent_version, "invalidated": state.invalidated})
        state.resolutions.append({"message": user_message, "patches": actual,
                                  "previous_filters":previous_filters})
    state.pending_card = None
    state.switch_card = None
    transition(state, "CHECKING")
    sync_contract(state)


def apply_choice(state: SessionState, card: dict, choice_id: str) -> dict:
    match = next((item for item in card.get("trusted_options", []) if item["id"] == choice_id), None)
    if match is None:
        raise SessionConflict("所选选项不在当前澄清卡片中。")
    patch = match["patch"]
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
        apply_patches(state, patches, user_message=match["label"])
    return match


DEFAULT_STORE = SessionStore()
