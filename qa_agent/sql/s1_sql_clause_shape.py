"""Source-only scalar shapes for a sold quantity or one independent SQL clause.

This never chooses a measure, edits SQL or verifies business semantics. A
planner's question is not parsed as source. Unknown text or identity flow is
left unverified so existing tool/source obligations keep their own authority.
"""
from hashlib import sha256
import json
import re


_NON_ASSERTION = re.compile(r"例如|比如|示例|假如|假设|如果|不要|不用|不需要|无需|无须|不必|不只|并非|"
                            r"引用|翻译|解释这句|[“”\"'‘’「」『』`]")
_EXTRA = re.compile(r"每|各|逐|分别|分组|名单|列表|列出|哪(?:个|位|些|张|首|种)|是谁|谁的|"
                    r"姓名|字段|列数|只(?:要|给|留|列|输出|返回)|仅(?:要|给|输出|返回)|"
                    r"并(?:给|列|输出|返回)|再(?:给|列|输出|返回)|以及|同时|占比|比例|百分|"
                    r"金额|多少钱|平均|时长|排名|排行|第[一二三四五六七八九十0-9]+|"
                    r"前[一二三四五六七八九十0-9]+")
_DOC = re.compile(r"(?<![A-Za-z])profile(?![A-Za-z])|简介|公开背景|公开资料|文档|资料里|资料中", re.I)
_DB = re.compile(r"库里|数据库|数据中|album|track|invoice|专辑|曲目|曲子|发票|员工|客户|歌单|播放列表", re.I)
_SOLD = re.compile(r"一共(?:卖出|售出)(?:了)?多少份[。！？?!\s]*$")
_COUNT = re.compile(r"(?:有几(?:张|首|条|个|位|人)|(?:总数|数量)(?:是|为)?多少|"
                    r"一共(?:有)?多少(?:张|首|条|个|位|人)?)[。！？?!\s]*$")


def _requirement(question, start, end, kind, role):
    return {'policy': 's1_source_output_shape_v1', 'kind': kind, 'width': 1,
            'single_row': True,
            'source': {'quote': question[start:end], 'start': start, 'end': end,
                       'sha256': sha256(question.encode()).hexdigest()},
            'sql_role': role,
            'authority': 'declared_SQL_tool_result_shape_not_business_semantic_certificate',
            'business_correctness_asserted': False, 'state_committed': False}


def _independent_sql_role(context, question):
    """Check the actual program-retained DAG, never free planner instructions."""
    if (not isinstance(context, dict) or context.get('kind') != 'composed'
            or type(context.get('sql_step_count')) is not int or context['sql_step_count'] != 1
            or context.get('original_question') != question
            or context.get('debut_identity_lookup') is True):
        return None
    plan = context.get('_program_composed_plan')
    current = context.get('sql_step')
    if not isinstance(plan, dict) or not isinstance(current, dict):
        return None
    steps = plan.get('steps')
    if not isinstance(steps, list) or not 2 <= len(steps) <= 6:
        return None
    seen = {}
    for step in steps:
        if not isinstance(step, dict):
            return None
        key, tool, deps = step.get('step_id'), step.get('tool'), step.get('depends_on')
        if (not isinstance(key, str) or not re.fullmatch(r's[1-6]', key) or key in seen
                or tool not in {'sql', 'doc', 'context'} or not isinstance(deps, list)
                or any(not isinstance(dep, str) or dep not in seen for dep in deps)):
            return None
        seen[key] = step
    sql = [step for step in steps if step['tool'] == 'sql']
    if len(sql) != 1 or sql[0]['step_id'] != current.get('step_id') or not any(s['tool'] == 'doc' for s in steps):
        return None
    # Even a document step may need actual PK/name from this SQL. Removing
    # those columns is unsafe. Do not infer that a named parent needs no IDs.
    key = sql[0]['step_id']
    if any(key in step['depends_on'] for step in steps):
        return None
    return {'kind': 'sole_SQL_without_downstream_identity_consumer', 'step_id': key,
            'sql_step_count': 1, 'no_downstream_consumer': True,
            'plan_sha256': sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True,
                separators=(',', ':')).encode()).hexdigest(),
            'source_question_sha256': sha256(question.encode()).hexdigest()}


def _clauses(question):
    """Keep exact original offsets; commas may contain SQL filter conditions."""
    return [(m.start(), m.end(), m.group()) for m in re.finditer(r'[^。！？?；;\n]+[。！？?；;]?', question)
            if m.group().strip()]


def source_sql_scalar_shape(question, *, context=None, brief='', has_history=False):
    """Return one bounded output requirement, or None; not execution permission.

    Body/history may carry display or group requirements, so this finite helper
    does not infer shape in their presence. Source text is never rewritten or
    truncated. The second family records a source clause while retaining the
    whole parent question's hash and actual DAG role.
    """
    if (not isinstance(question, str) or not question.strip() or not isinstance(brief, str)
            or brief.strip() or has_history is not False or _NON_ASSERTION.search(question)):
        return None
    if context is None or context == {}:
        if (_SOLD.search(question) and len(_clauses(question)) == 1
                and not _EXTRA.search(question) and not _DOC.search(question)
                and not re.search(r'另外|此外|还有|顺便|并且|\b(?:and|or)\b', question, re.I)):
            return _requirement(question, 0, len(question), 'single_sold_quantity',
                                {'kind': 'direct_SQL_source_only'})
        return None
    role = _independent_sql_role(context, question)
    if role is None:
        return None
    clauses = _clauses(question)
    if not 2 <= len(clauses) <= 3:
        return None
    sql_candidates = [(start, end, text) for start, end, text in clauses
                      if _COUNT.search(text) and _DB.search(text) and not _DOC.search(text)]
    if len(sql_candidates) != 1:
        return None
    start, end, text = sql_candidates[0]
    if _EXTRA.search(text):
        return None
    for left, right, clause in clauses:
        if (left, right) == (start, end):
            continue
        if (not _DOC.search(clause) or _COUNT.search(clause)
                or re.search(r'多少份|多少钱|销售额|发票|前[一二三四五六七八九十0-9]+|列出|名单|分别|分组', clause)):
            return None
    return _requirement(question, start, end, 'single_composed_count_clause', role)
