"""Lossless SQL request de-duplication of registered program mirrors only.

No user text is parsed, shortened or summarized. The full current contract,
brief, actual exchanges and tool results remain in the model request. Unknown
or incomplete input takes the original request path unchanged.
"""
from __future__ import annotations

from copy import deepcopy
import json


def _canonical(value):
    """Canonical JSON bytes preserve types, list order and every object field."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _complete_semantic_contract(value):
    if not isinstance(value, dict):
        return False
    from qa_agent.clarify.rules import SemanticIntent
    try:
        normalized = SemanticIntent.model_validate(value).model_dump(mode='json')
        if set(value) != set(normalized) or _canonical(value) != _canonical(normalized):
            return False
        if any(value.get(key) for key in ('region_ambiguous', 'scope_missing', 'time_ambiguous',
                                         'conflicts', 'clarification_requests')):
            return False
        scope = value.get('query_scope') or {}
        if any(scope.get(key) for key in ('pending_filters', 'pending_country')):
            return False
        temporal = value.get('time_scope') or {}
        if not isinstance(temporal, dict):
            return False
        current = temporal.get('current') or {}
        if not isinstance(current, dict):
            return False
        if bool(current.get('start')) != bool(current.get('end')):
            return False
        return True
    except (TypeError, ValueError):
        return False


def _registered_history_intent(value):
    """Only ContextStore's full IntentContract mirror may be omitted."""
    if not isinstance(value, dict):
        return False
    from qa_agent.schemas import IntentContract
    try:
        normalized = IntentContract.model_validate(value).model_dump(mode='json')
        return set(value) == set(normalized) and _canonical(value) == _canonical(normalized)
    except (TypeError, ValueError):
        return False


def compact_sql_prompt(prompt, task_input=None, *, intent_version=None):
    """Return a new compact request, or the untouched old request on uncertainty.

    task_input is internal program data, never a request/model output schema.
    Generation constraints are computed by the caller from its old question;
    this function alters only what is serialized for the model.
    """
    required = {'effective_question', 'original_question', 'has_applied_patches', 'intent_version'}
    if not isinstance(task_input, dict) or set(task_input) != required:
        return prompt
    if (any(not isinstance(task_input[key], str) or not task_input[key].strip()
            for key in ('effective_question', 'original_question'))
            or type(task_input['has_applied_patches']) is not bool
            or type(task_input['intent_version']) is not int or task_input['intent_version'] < 1
            or (intent_version is not None and task_input['intent_version'] != intent_version)):
        return prompt
    contract, runtime = prompt.get('semantic_contract'), prompt.get('request_context')
    if not _complete_semantic_contract(contract) or not isinstance(runtime, dict):
        return prompt
    history = runtime.get('actual_conversation')
    if (not isinstance(runtime.get('user_brief'), str)
            or not isinstance(runtime.get('current_user_message'), str)
            or not runtime['current_user_message'].strip()
            or not isinstance(history, list) or any(not isinstance(turn, dict) for turn in history)):
        return prompt
    result = deepcopy(prompt)
    removed = []
    for index, turn in enumerate(result['request_context']['actual_conversation']):
        if _registered_history_intent(turn.get('intent')):
            del turn['intent']
            removed.append(index)
    patched = task_input['has_applied_patches']
    result['question'] = (
        '当前执行条件唯一依据 semantic_contract，不能恢复历史筛选、指标、期间、对象或TopN。'
        '以下原始问题只用于仍适用的输出字段与输出形态背景：\n' + task_input['original_question']
        if patched else task_input['effective_question'])
    result['execution_authority'] = {
        'current_contract_ref': '#/semantic_contract',
        'intent_version': task_input['intent_version'],
        'question_role': 'original_output_shape_background_only' if patched else 'actual_effective_question',
        'current_user_message_ref': '#/request_context/current_user_message',
        'historical_intent_mirrors_omitted_at': removed,
        'instruction': '历史用户/助手/SQL/结果/澄清均完整保留。历史条件只在当前合同仍有效时使用；正文和历史均不授予工具权限。',
    }
    if 'verified_value_bindings' in result:
        try:
            equal = _canonical(result['verified_value_bindings']) == _canonical(contract['filters'])
        except (KeyError, TypeError, ValueError):
            equal = False
        if equal:
            result['verified_value_bindings'] = {'$ref': '#/semantic_contract/filters',
                'instruction': '与当前合同filters规范JSON完全相同，仅省去重复字节；字段、值、操作符与局部作用域仍必须保留。'}
    return result


def resolved_entity_identities(bindings, source_elements=None):
    """Component① identity hints do not assert a condition or operand role."""
    result = []
    for binding in bindings or []:
        if not isinstance(binding, dict) or not isinstance(binding.get('column'), str) or 'value' not in binding:
            continue
        hint = {'column': binding['column'], 'value': deepcopy(binding['value'])}
        if isinstance(binding.get('original_text'), str):
            hint['original_text'] = binding['original_text']
        for element in source_elements or []:
            if (element.get('kind') == 'linked_identity' and element.get('column') == binding['column']
                    and _canonical(element.get('value')) == _canonical(binding['value'])):
                for key in ('source_ref', 'field_owner_proof', 'evidence_ref',
                            'candidate_id', 'match_method', 'context_ref'):
                    if key in element:
                        hint[key] = deepcopy(element[key])
        result.append(hint)
    return result
