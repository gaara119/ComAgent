"""Turn component-1 evidence-linked clauses into an advisory SQL task.

No model, session store, SQL, defaults or confirmed semantic contract is made
here. The caller retains full original sources beside this compact main task.
"""
from __future__ import annotations

from hashlib import sha256
import re

from qa_agent.nlu.grounded_rewrite import QuestionElements, validate_evidence


_LABELS = {
    'object': '对象', 'metric': '度量', 'filter': '条件', 'period': '期间',
    'qualification': '资格集合', 'grouping': '分组', 'ranking': '排名',
    'comparison': '比较', 'ratio': '比例与分母', 'continuation': '本轮变更',
    'output': '需要交付',
}


def _positive_plural_proposition(question, match):
    """An optional explanation needs a positive request, not mere words.

    Unknown/quoted/conditional syntax keeps the original clauses untouched;
    declining this extra explanation does not decline the user's query.
    """
    if re.search(r'''["'“”‘’「」『』]''', question):
        return False
    left = max((m.end() for m in re.finditer(r'[。！？!?；;\n]', question[:match.start()])), default=0)
    ending = re.search(r'[。！？!?；;\n]', question[match.end():])
    right = match.end() + ending.start() if ending else len(question)
    statement = question[left:right]
    if re.search(r'不要|不用|无需|不必|不能|不应|不是|并非|不算|不求|不计算|不要求|不需要|不想|不打算|别算|勿|'
                 r'如果|假如|假设|若|举例|例如|比如|示例|例句|引用|引文|写道|原话', statement):
        return False
    prefix = re.split(r'[，,]', question[left:match.start()])[-1]
    action = re.fullmatch(r'\s*(?:请|麻烦)?\s*(?:再|也|还|并|顺便)?\s*'
                          r'(?:算算|计算|算一下|算|求出|求|看看|看|给出|展示|返回|说明)\s*', prefix)
    return bool(action or not prefix.strip() and re.search(r'多少|百分之几|几成|[?？]', question[match.end():right+1]))


def build_rewrite_task(question_elements, *, original_question: str,
                       sources: dict[str, str], tool_task: str | None = None) -> dict | None:
    """Return a source-checked natural-language task, or None for old fallback.

    ``original_question`` is the actual current user turn, including for a
    composed SQL subtask. ``sources`` comes from the original-source registry;
    a planner subtask is never a user source. Quotes/hashes/all offsets are
    recomputed by the same producer validator instead of trusting an advisory
    merely because it carries a successful status. Their meanings stay unproved.
    """
    if (not isinstance(question_elements, dict)
            or question_elements.get('status') != 'quote_checked_advisory'
            or question_elements.get('semantic_verified') is not False
            or not isinstance(original_question, str) or not original_question.strip()
            or not isinstance(sources, dict) or sources.get('current') != original_question
            or tool_task is not None and (not isinstance(tool_task, str) or not tool_task.strip())):
        return None
    try:
        clauses = question_elements['clauses']
        raw = []
        for clause in clauses:
            if not isinstance(clause, dict) or set(clause) != {'kind', 'text', 'refs'}:
                return None
            refs = []
            for ref in clause['refs']:
                if (not isinstance(ref, dict)
                        or set(ref) != {'source_id', 'quote', 'source_sha256', 'spans'}):
                    return None
                source_id = ref['source_id']
                if (not isinstance(source_id, str) or source_id not in
                        {'current', 'brief', 'clock', 'catalog', 'approved_metric_definitions'}
                        and not re.fullmatch(r'user_history_[1-9]\d*', source_id)):
                    return None
                refs.append({'source_id': source_id, 'quote': ref['quote']})
            raw.append({'kind': clause['kind'], 'text': clause['text'], 'refs': refs})
        parsed = QuestionElements.model_validate({'clauses': raw,
            'uncertainties': question_elements.get('uncertainties', [])})
        checked = validate_evidence(parsed, sources)
        if checked['clauses'] != clauses:
            return None
    except (ValueError, TypeError, KeyError, AttributeError):
        return None
    lines = ['本轮SQL任务（①理解提示，非③确认合同；原始用户来源优先）：']
    refs = []
    for clause in checked['clauses']:
        lines.append('【' + _LABELS[clause['kind']] + '】' + clause['text'])
        for ref in clause['refs']:
            if ref not in refs:
                refs.append(ref)
    derivations = []
    rankings = [clause for clause in checked['clauses'] if clause['kind'] == 'ranking']
    plural = re.search(r'(?:他们|它们|这几位|这几名|这几个)\s*(?:的)?\s*合计\s*占', original_question)
    if (rankings and plural and not re.search(r'每人|各自|分别', original_question)
            and _positive_plural_proposition(original_question, plural)):
        interpretation = ('把所选排名集合所有对象指标相加为一个集合合计，再用这个同一集合合计算占比；'
                          '不是逐对象分别占比。')
        derived = validate_evidence(QuestionElements.model_validate({'clauses': [{
            'kind': 'ratio', 'text': interpretation,
            'refs': [{'source_id': 'current', 'quote': plural.group()}]}]}), sources)['clauses'][0]
        derivations.append({'rule': 'plural_ranked_set_aggregate', 'text': interpretation,
            'refs': derived['refs'], 'antecedent_refs': [ref for clause in rankings for ref in clause['refs']],
            'authority': 'advisory_only', 'semantic_verified': False})
        lines.append('【复数合计解释（待核对）】' + interpretation)
        for ref in derived['refs']:
            if ref not in refs:
                refs.append(ref)
    if checked['uncertainties']:
        lines.append('未确定事项仍须保留，不据此选择默认或批准条件：')
        lines.extend('- ' + text for text in checked['uncertainties'])
    task = {'version': 's1-sql-task-1', 'status': 'quote_checked_advisory_task',
        'normalized_sql_question': '\n'.join(lines), 'original_question': original_question,
        'original_question_sha256': sha256(original_question.encode()).hexdigest(),
        'clauses': checked['clauses'], 'source_refs': refs,
        'uncertainties': checked['uncertainties'],
        'authority': 'advisory_only', 'semantic_verified': False}
    if derivations:
        task['advisory_derivations'] = derivations
    if tool_task is not None:
        task['tool_task'] = {'text': tool_task, 'authority': 'planner_subtask_not_user_evidence'}
    return task
