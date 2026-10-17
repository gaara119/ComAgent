"""Whole output IDs and bounded prose precision have different meanings.

IDs are opaque unless a caller names an exact supported semantic ID. Display
scale is associated with a prose subject and its own precision directive;
neither an ID's spelling nor a decimal count for another subject grants it.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

ATOMIC_ID = re.compile(r'[A-Za-z][A-Za-z0-9_.:-]*\Z')
PERCENT_WORDS = r'百分比|百分数|百分率|(?<![A-Za-z0-9_.:-])(?:percentage|percent)(?![A-Za-z0-9_]|[.:-][A-Za-z0-9_])|%'
MONEY_WORDS = r'金额|销售额|人均消费|平均消费|消费额|(?<![A-Za-z0-9_.:-])(?:amount|money)(?![A-Za-z0-9_]|[.:-][A-Za-z0-9_])'
COUNT_WORDS = r'计数|数量|(?<![A-Za-z0-9_.:-])(?:count|quantity)(?![A-Za-z0-9_]|[.:-][A-Za-z0-9_])'
PERCENT_DIGITS = r'(?:保留|精确到|round(?:ed)?\s+to)\s*([0-9]+|[零一二两三四五六七八九])\s*(?:位小数|decimal\s+places?)'
SUBJECT = re.compile(f'(?P<percent>{PERCENT_WORDS})|(?P<money>{MONEY_WORDS})|(?P<count>{COUNT_WORDS})', re.I)
DIRECTIVE = re.compile(PERCENT_DIGITS, re.I)
NEGATIVE = re.compile(r'不要|不得|不能|不再|无需|无须|别|不必|不是|不要求|不采用|不需要|不需|不用|没有必要|避免|取消|作废|不生效|不适用|暂停|不执行|不舍入|不四舍五入|\bdo\s+not\b|\bdon.t\b', re.I)
HARD_END = re.compile(r'[。；;\n!?！？]')
CLAUSE_END = re.compile(r'[。；;\n!?！？，,]')
JOIN = re.compile(r'\s*(?:和|与|及|、|and)\s*', re.I)
NUMERALS = {word: index for index, word in enumerate('零一二三四五六七八九')}
NUMERALS['两'] = 2

# These are output operations already used by current producers/consumers,
# not a guess from an arbitrary identifier containing ratio/percent/growth.
SEMANTIC_IDS = {
    'ratio': frozenset({'ratio', 'percentage', 'percent', 'percentage_share', 'percent_share', 'ratio_percentage', 'percentage_one_decimal'}),
    'growth': frozenset({'growth', 'growth_rate', 'growth_percentage', 'percentage_growth', 'growth_rate_percent', 'growth_rate_percentage'}),
    'ranked_subset': frozenset({'ranked_subset_total', 'ranked_subset_rows', 'ranked_subset_ratios'}),
    'monthly_rows': frozenset({'monthly_invoice_revenue'}),
}
PROSE_SEMANTICS = {
    'ratio': r'(?:输出|返回|展示|给出)?(?:比例|占比|百分比|百分数|百分率)(?:(?:用|按|以)(?:百分比|百分数|百分率)(?:展示|表示|呈现)?)?|(?:show|return|output)\s+(?:ratio|percentage|percent)',
    'growth': r'(?:输出|返回|展示)?(?:同比|环比|增长率|增长率百分比|增长百分比)|(?:show|return|output)\s+growth',
    'ranked_subset': r'排名子集|前\s*\d+\s*(?:名|位|个客户)(?:合计|名单)',
    'monthly_rows': r'各月发票金额|每月发票金额',
}


def is_atomic_requirement(text):
    return isinstance(text, str) and ATOMIC_ID.fullmatch(text) is not None


def requirement_has_semantics(text, *kinds):
    if is_atomic_requirement(text):
        return any(text in SEMANTIC_IDS[kind] for kind in kinds)
    # Mixed or unfamiliar prose can carry another obligation. Only complete
    # bounded phrases are retired; a ratio word inside it cannot erase it.
    return any(re.fullmatch(PROSE_SEMANTICS[kind], text.strip(' \t，,、；;。'), re.I) for kind in kinds)


@dataclass(frozen=True)
class PrecisionEvent:
    start: int
    end: int
    directive_start: int
    directive_end: int
    digits: int
    subjects: tuple[str, ...]
    subject_spans: tuple[tuple[int, int, str], ...]
    negative: bool
    ambiguous: bool


def precision_events(text):
    """Associate each directive with its nearest subject, or explicit joint list.

    A comma can separate the target from its formatting instruction, but it
    cannot silently join a different subject. The next directive starts a
    new association, so money=3 and percentage=1 remain independent.
    """
    if not isinstance(text, str) or is_atomic_requirement(text):
        return []
    events = []
    previous_end = 0
    previous_subjects = []
    for directive in DIRECTIVE.finditer(text):
        hard_begin=max([0]+[match.end() for match in HARD_END.finditer(text, 0, directive.start())])
        begin = max(previous_end,hard_begin)
        previous_end = directive.end()
        if re.match(r'\s*(?:例如|比如|示例|for\s+example|e\.g\.)\s*[:：，,]?',text[hard_begin:directive.start()],re.I):
            continue
        subjects = list(SUBJECT.finditer(text, begin, directive.start()))
        inherited = False
        if not subjects and events and events[-1].end>=hard_begin:
            # Only an explicit continuation of the immediately preceding
            # subject may elide that subject. A new money/percent noun above
            # always wins; unrelated numbers never join this association.
            connector=text[begin:directive.start()]
            if re.fullmatch(r'\s*[,，、]?\s*(?:也|并|且|同时|再|also)?\s*',connector,re.I):
                subjects=list(previous_subjects);inherited=True
        if not subjects:
            continue
        selected = [subjects[-1]]
        if not inherited and directive.start() - selected[-1].end() > 80:
            continue
        for prior in reversed(subjects[:-1]):
            bridge = text[prior.end():selected[0].start()].strip('“”‘’" ')
            if JOIN.fullmatch(bridge) is None:
                break
            selected.insert(0, prior)
        # Only the clause containing the actual subject/verb can deny it.
        prefix_begin = max([begin] + [match.end() for match in CLAUSE_END.finditer(text, begin, selected[0].start())])
        negative_text = text[prefix_begin:directive.start()]
        next_clause = next(CLAUSE_END.finditer(text, directive.end()), None)
        suffix = text[directive.end():next_clause.start() if next_clause else len(text)]
        withdrawn = re.search(r'(?:这条|该|本条)(?:要求|精度|规则)?(?:作废|取消|不生效|不适用|不执行)|不是本题要求', suffix)
        ambiguous = (re.search(r'前者|后者|任选',text[selected[0].start():directive.start()]) or
                     re.match(r'\s*(?:或(?:者)?|还是|任选)',suffix) or
                     re.match(r'\s*(?:或(?:者)?|还是|任选)',text[begin:selected[0].start()]))
        word = directive.group(1)
        value=int(word) if word.isdigit() else NUMERALS[word]
        next_hard=next(HARD_END.finditer(text,directive.end()),None)
        following=next(DIRECTIVE.finditer(text,directive.end(),next_hard.start()if next_hard else len(text)),None)
        if following is not None:
            connector=text[directive.end():following.start()]
            later_word=following.group(1);later_value=int(later_word)if later_word.isdigit()else NUMERALS[later_word]
            if re.fullmatch(r'\s*[,，、]?\s*(?:也|并|且|同时|再|also)?\s*',connector,re.I)and later_value!=value:
                ambiguous=True
        if inherited and(events[-1].digits!=value or events[-1].negative or events[-1].ambiguous):ambiguous=True
        previous_subjects=selected
        events.append(PrecisionEvent(selected[0].start(), directive.end(), begin if inherited else directive.start(), directive.end(),value,
            tuple(dict.fromkeys(match.lastgroup for match in selected)),
            tuple((match.start(), match.end(), match.lastgroup) for match in selected),
            bool(NEGATIVE.search(negative_text) or withdrawn),bool(ambiguous)))
    return events


def strip_unverified_percent_precision(text):
    """Remove only a percent scale grant; keep IDs and other obligations whole."""
    if is_atomic_requirement(text):
        return [text]
    events = [event for event in precision_events(text) if 'percent' in event.subjects]
    if not events:
        return [text]
    replacements = []
    shared = False
    for event in events:
        if any(subject != 'percent' for subject in event.subjects):
            shared = True
            spans = event.subject_spans
            for index, (start, end, subject) in enumerate(spans):
                if subject != 'percent':
                    continue
                # Remove this known list member and its connector, rather
                # than stripping arbitrary Chinese characters from words.
                if index:
                    start = spans[index - 1][1]
                elif len(spans) > 1:
                    end = spans[index + 1][0]
                replacements.append((start, end, ''))
        else:
            replacements.append((event.directive_start, event.directive_end, ''))
    result = text
    for start, end, replacement in sorted(set(replacements), reverse=True):
        result = result[:start] + replacement + result[end:]
    result = result.strip(' \t，,、；;。')
    output = [result] if result else []
    if shared:
        output.append('百分比')
    return list(dict.fromkeys(output))
