"""Explicit cumulative experiment controls; maintained semantic gate stays on.

No model, session-store, rule engine, extraction or database operation occurs
here. Bypassed containers carry identity hints only, never confirmed semantics.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import os
from typing import Any

STAGES=('S0','S1','S2','S3')
CUMULATIVE_MODES=tuple('cumulative_'+stage for stage in STAGES)


def semantic_gate_enabled() -> bool:
    value=os.getenv('AGENT_SEMANTIC_GATE_ENABLED','true').strip().casefold()
    if value in {'true','1','yes','on'}:return True
    if value in {'false','0','no','off'}:return False
    raise ValueError('AGENT_SEMANTIC_GATE_ENABLED must be an explicit boolean')


def expected_cumulative_flags(stage: str) -> dict:
    if stage.startswith('cumulative_'):stage=stage.removeprefix('cumulative_')
    if stage not in STAGES:raise ValueError('Unknown cumulative stage')
    elements=stage!='S0';semantics=stage in {'S2','S3'};schema=stage=='S3'
    return {'nlu_enabled':elements,'link_grounding_enabled':elements,
        'semantic_gate_enabled':semantics,'clarify_grounding_enabled':semantics,
        'clarify_state_enabled':semantics,'aw_schema_mode':'subgraph'if schema else'full',
        'aw_schema_pruning_enabled':schema,'typed_sql_compiler_enabled':True,
        'schema_recall_enhanced':False}


def actual_feature_vector(settings=None) -> dict:
    if settings is None:
        from qa_agent.config import get_settings
        settings=get_settings()
    from qa_agent.nlu.features import enabled
    return {'nlu_enabled':settings.nlu_enabled,
        'link_grounding_enabled':enabled('AGENT_LINK_GROUNDING_ENABLED'),
        'semantic_gate_enabled':semantic_gate_enabled(),
        'clarify_grounding_enabled':enabled('AGENT_GROUNDING_ENABLED'),
        'clarify_state_enabled':enabled('AGENT_CLARIFY_STATE_ENABLED'),
        'aw_schema_mode':settings.aw_schema_mode,
        'aw_schema_pruning_enabled':settings.aw_schema_pruning_enabled,
        'typed_sql_compiler_enabled':settings.typed_sql_compiler_enabled,
        'schema_recall_enhanced':os.getenv('SCHEMA_RECALL_ENHANCED','false').casefold()not in{'false','0','off'}}


def validate_cumulative_health(health: dict, stage: str) -> dict:
    """Validate actual typed values, not a stage label or truthy strings."""
    expected=expected_cumulative_flags(stage)
    stage=stage.removeprefix('cumulative_')
    if health.get('component_mode')!='cumulative_'+stage or health.get('cumulative_stage')!=stage:
        raise ValueError('Cumulative stage identity is not confirmed by actual health')
    mismatches={key:{'expected':wanted,'actual':health.get(key),'missing':key not in health}
        for key,wanted in expected.items() if key not in health or type(health[key])is not type(wanted)or health[key]!=wanted}
    if mismatches:raise ValueError('Cumulative feature vector mismatch: '+repr(mismatches))
    return expected


def cumulative_health(settings=None) -> dict:
    """Only publish a stage when the full real feature vector establishes it."""
    vector=actual_feature_vector(settings)
    mode=os.getenv('AGENT_COMPONENT_MODE','none')
    stage=mode.removeprefix('cumulative_')if mode in CUMULATIVE_MODES else None
    if stage is not None:
        expected=expected_cumulative_flags(stage)
        if any(type(vector[key])is not type(value)or vector[key]!=value for key,value in expected.items()):stage=None
    return {'semantic_gate_enabled':vector['semantic_gate_enabled'],'cumulative_stage':stage}


@dataclass
class BypassDecision:
    level: None=None
    issues: list=field(default_factory=list)
    assumptions: list=field(default_factory=list)
    derived: dict=field(default_factory=dict)


@dataclass
class BypassState:
    original_question: str
    effective_question: str
    analysis: Any
    intent: Any
    bindings: list[dict]
    resolutions: list=field(default_factory=list)
    invalidated: list=field(default_factory=list)
    scope: dict=field(default_factory=dict)
    history: list=field(default_factory=list)
    phase: str='BYPASSED'
    switch_card: None=None
    pending_card: None=None


@dataclass
class BypassGate:
    state: BypassState
    question: str
    decision: BypassDecision=field(default_factory=BypassDecision)
    card: None=None
    bypassed: bool=True


def bypass_gate(request, linked) -> BypassGate:
    if semantic_gate_enabled():
        raise ValueError('Cannot construct a bypass while semantic gate is enabled')
    # Import the internal data model only; no extractor/RuleEngine/store call.
    from qa_agent.clarify.rules import SemanticIntent
    from qa_agent.schemas import IntentContract
    raw=request.message
    rewritten=getattr(linked,'rewritten_question',None)
    rewritten=rewritten if isinstance(rewritten,str)and rewritten.strip()else raw
    identities=deepcopy(getattr(linked,'bindings',[])or[])
    state=BypassState(original_question=raw,effective_question=rewritten,
        analysis=SemanticIntent(task_type='lookup'),
        intent=IntentContract(route='sql',task_type='lookup',filters=[]),
        bindings=identities,scope=request.scope.model_dump(mode='json'))
    return BypassGate(state=state,question=rewritten)


def bypass_metadata(gate=None) -> dict:
    if gate is not None and getattr(gate,'bypassed',False)is not True:
        raise ValueError('Bypass metadata cannot describe an executed semantic gate')
    return {'enabled':False,'level':None,'semantic_gate_executed':False,
        'semantic_state_persisted':False,'semantic_contract':None,
        'state':None,'intent_version':None,'assumptions':[],
        'identity_hints_scope':'unconfirmed','switch_card':None}
