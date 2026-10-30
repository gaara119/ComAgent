"""Enforce the declared S1 final-percent display precision, never its formula.

This module recognizes only a source-explicit, context-free single percentage
and a visibly scaled scalar division. It neither evaluates nor rewrites SQL.
"""
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import re
import unicodedata

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, build_scope, walk_in_scope

from qa_agent.sql.validator import SQLValidationError


_PRECISION = (r'小数|精度|舍入|四舍五入|ROUND|原始(?:值|数值|比率|比例)|原值|不截断|不取整|'
              r'保留.{0,10}(?:位|小数|精度|原始|原值)')


def _un(node):
    while isinstance(node, (exp.Alias, exp.Paren)):
        node = node.this
    return node


def _hundred(node):
    node = _un(node)
    if not isinstance(node, exp.Literal) or node.is_string:
        return False
    try:
        return Decimal(node.this) == Decimal(100)
    except (InvalidOperation, ValueError):
        return False


def _one_row(scope, seen=None):
    if scope is None or not isinstance(scope.expression, exp.Select):
        return False
    seen = set() if seen is None else set(seen)
    if id(scope) in seen:
        return False
    seen.add(id(scope))
    tree = scope.expression
    if any(tree.args.get(k) for k in ('group', 'having', 'qualify', 'distinct')):
        return False
    local = list(walk_in_scope(tree))
    if any(isinstance(n, exp.Window) for n in local):
        return False
    if any(isinstance(n, exp.AggFunc) for n in local):
        return True  # Ungrouped aggregate, not a proof of its business inputs.
    if not scope.selected_sources:
        return True
    return all(isinstance(value, Scope) and _one_row(value, seen)
               for _, value in scope.selected_sources.values())


def validate_s1_percent_display(sql, source_question, *, brief='', has_history=False,
                                composed=False, evidence_text=''):
    """Return a format-only proof or a repairable final ROUND2 conflict.

    A composed caller must supply its complete actual parent question. The flag
    never promotes a planner subquestion or a document's model-written answer.
    """
    def no(reason):
        return {'status': 'not_verified', 'reason': reason,
                'business_correctness_asserted': False}
    if (not all(isinstance(t, str) for t in (source_question, brief, evidence_text))
            or not source_question.strip() or brief.strip() or has_history):
        return no('not_context_free_actual_source')
    text = unicodedata.normalize('NFKC', source_question)
    if re.search(r'同比|环比|增长率|增长了|上涨|涨了|下降了|降低了', text):
        return no('growth_calculation_preserves_raw_precision_display_is_separate')
    percent = list(re.finditer(r'百分之(?:几|多少)|百分比', text))
    if len(percent) != 1:
        return no('not_one_explicit_percentage_request')
    display_delegation = re.search(
        r'(?:照|按|遵照)[^，,。；;\n]{0,10}(?:文档|手册|资料)'
        r'(?:(?:中|里)?(?:规定|要求|约定)?的?(?:数值)?(?:显示|展示|输出)?(?:格式|方式|精度)|'
        r'[^，,。；;\n]{0,12}(?:显示|展示|输出)(?:格式|方式|规范|要求))', text)
    if (re.search(_PRECISION, text, re.I) or re.search(_PRECISION, evidence_text, re.I)
            or display_delegation):
        return no('explicit_source_or_document_precision_takes_priority')
    if re.search(r'不要|不需要|不用|无需|不必|不算|不求|不是|并非|只解释|仅解释|只说明|'
                 r'例如|比如|示例|举例|假设|如果|引用|定义|公式|含义|[“”"\x27‘’「」『』]', text):
        return no('negated_example_definition_or_unknown_source')
    if (len(re.findall(r'[?？]', text)) > 1
            or re.search(r'分别|各自|各占|每(?:个|位|张|国)|分组|按月|按年|名单|列出|同时|另外|此外|'
                         r'以及|顺便|再给|并(?:给|列|返回|显示|告诉)|金额(?:和|与)|(?:和|与).{0,6}金额', text)):
        return no('multiple_or_grouped_requested_outputs')
    try:
        tree = sqlglot.parse_one(sql, read='postgres')
        if (not isinstance(tree, exp.Select) or len(tree.expressions) != 1
                or not _one_row(build_scope(tree))):
            return no('not_proven_single_final_scalar')
        final = _un(tree.expressions[0])
        rounded = isinstance(final, exp.Round)
        decimals = final.args.get('decimals') if rounded else None
        value = _un(final.this) if rounded else final
        # Casts and algebraic simplification are deliberately not transparent.
        if isinstance(value, exp.Mul) and (_hundred(value.left) or _hundred(value.right)):
            value = _un(value.right if _hundred(value.left) else value.left)
            if not isinstance(value, exp.Div):
                return no('unknown_outer_percent_algebra')
            numerator, denominator = _un(value.left), _un(value.right)
        elif isinstance(value, exp.Div):
            numerator, denominator = _un(value.left), _un(value.right)
            if not isinstance(numerator, exp.Mul) or not (_hundred(numerator.left) or _hundred(numerator.right)):
                return no('raw_fraction_or_unknown_scale')
            numerator = _un(numerator.right if _hundred(numerator.left) else numerator.left)
        else:
            return no('unknown_final_percent_algebra')
        # Do not repair pre-rounded operands, repeated/cancelled100 factors,
        # casts, or a denominator whose scale this function cannot establish.
        if any(isinstance(n, (exp.Round, exp.Cast)) or _hundred(n)
               for operand in (numerator, denominator) for n in operand.walk()):
            return no('operand_transform_or_additional_100_not_proven')
        if (rounded and isinstance(decimals, exp.Literal) and not decimals.is_string
                and str(decimals.this) == '2'):
            return {'status': 'verified_final_percent_display_only', 'digits': 2,
                    'visible_scale': 100, 'business_correctness_asserted': False,
                    'state_committed': False}
        if rounded and decimals is not None and not isinstance(decimals, (exp.Literal, exp.Neg)):
            return no('unknown_dynamic_round_precision')
    except (ValueError, TypeError, KeyError, InvalidOperation, sqlglot.errors.ParseError):
        return no('unresolved_SQL_structure')
    error = SQLValidationError('①SQL百分数展示约定：实际原问明确要求百分数，未提供正文、历史或显式精度要求；'
        '本工具最终百分数保留两位小数。请仅在现有可见乘100的最终比例最外层使用ROUND(..., 2)，'
        '不要提前舍入分子、分母、排序金额或原始比率，不增加/取消任何乘100；'
        '保留原分子、分母、期间、筛选和NULLIF/NULL语义。这只修最终显示精度，不认证计算公式或业务口径。')
    error.percent_display_evidence = {'policy': 'declared_S1_final_percentage_two_decimals',
        'source': {'quote': source_question, 'sha256': sha256(source_question.encode()).hexdigest()},
        'actual_outer_round': rounded, 'actual_decimals': decimals.sql(dialect='postgres') if decimals is not None else None,
        'composed_parent_source': bool(composed), 'visible_scale': 100, 'required_final_digits': 2,
        'business_correctness_asserted': False, 'state_committed': False}
    raise error


def s1_percent_display_policy(sql, source_question, context, *, evidence_text=''):
    """Recheck a backend S1-only context, never a model/user precision field.

    The caller derives this separate context from actual feature flags and raw
    input. JSON/model metadata is not consulted. Existing semantic contracts
    and the shared explicit-user precision authority remain untouched.
    """
    if (not isinstance(context, dict)
            or set(context) != {'enabled', 'brief', 'has_history', 'composed'}
            or context.get('enabled') is not True or not isinstance(context.get('brief'), str)
            or type(context.get('has_history')) is not bool
            or type(context.get('composed')) is not bool):
        return None
    checked = validate_s1_percent_display(sql, source_question, brief=context['brief'],
        has_history=context['has_history'], composed=context['composed'], evidence_text=evidence_text)
    if checked.get('status') != 'verified_final_percent_display_only':
        return None
    return {**checked, 'authority': 'program:S1_declared_percent_display_policy',
        'actual_SQL_sha256': sha256(sql.encode()).hexdigest(),
        'actual_source_sha256': sha256(source_question.encode()).hexdigest(),
        'actual_document_evidence_sha256': sha256(evidence_text.encode()).hexdigest(),
        'user_precision_authorized': False, 'lossless_equivalence_claimed': False}
