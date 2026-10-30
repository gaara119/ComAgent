"""Extract a complete literal date range before interpreting either endpoint.

This bounded parser handles day-level Chinese/ISO endpoints, not arbitrary
natural-language time. Unsupported or conflicting ranges never become days.
"""
from __future__ import annotations

from datetime import date, timedelta
import re

_DATE = re.compile(r'(?<!\d)(?:(?P<year>\d{4})\s*(?:年|[-/])\s*)?'
                   r'(?P<month>\d{1,2})\s*(?:月|[-/])\s*(?P<day>\d{1,2})(?:\s*[日号])?(?!\d)')
_CONNECTOR = r'(?:到|至|—|–|--|——|~|～|\bto\b|-)'
_BOUNDARY = r'(?:[（(]\s*(?:不含|不包含|不包括|含|包含|包括)(?:当天|当日|该日|边界)?\s*[）)]|(?:不包含|不包括|不含|包含|包括|含)(?:当天|当日|该日|边界)?|之前)'
_MONTH_NUMBER = r'(?:\d{1,2}|十一|十二|十|[一二两三四五六七八九])'


def _month_number(word: str) -> int:
    return int(word) if word.isdigit() else {'一':1,'二':2,'两':2,'三':3,'四':4,'五':5,
        '六':6,'七':7,'八':8,'九':9,'十':10,'十一':11,'十二':12}.get(word, 0)


def month_convention_quote(source: str) -> str | None:
    """An actual natural-month/half-open convention, never a model label."""
    for clause in re.split(r'[。；;\n]', source):
        if (re.search(r'自然月', clause) and re.search(r'开始日(?:含|包含)', clause)
                and re.search(r'结束日(?:不含|不包含)', clause)
                and not re.search(r'例如|比如|示例|假设|可能|尚未|不按|不采用|并非|不是|或者', clause)):
            return clause.strip()
    return None


def parse_whole_month_reply(text: str, established: dict | None = None,
                            convention: str = '') -> dict | None:
    """Prove one finite, affirmative whole-month reply or explicit season span.

    Bare month endpoints need the source's natural-month convention; a literal
    month count or “月底” independently proves inclusion of the last month.
    Calendar years are explicit or reused from one already established year.
    This helper does not infer seasons or consume any non-calendar condition.
    """
    core = (r'(?:(?P<year>\d{4})\s*年\s*)?(?P<first>'+_MONTH_NUMBER+r')\s*月\s*'
            r'(?:到|至|—|–|~|～)\s*(?:(?P<last_year>\d{4})\s*年\s*)?'
            r'(?P<last>'+_MONTH_NUMBER+r')\s*月(?P<month_end>底)?'
            r'(?:\s*这\s*(?P<count>'+_MONTH_NUMBER+r')\s*个(?:整)?月)?')
    match = re.fullmatch(r'\s*(?:按|就按|我指(?:的是)?|旺季(?:就是|是|指|为))?\s*'+core+
                         r'\s*(?:算吧|算|吧)?\s*[。.!！?？]?\s*', text)
    if match is None:
        # An explicitly parenthesized season period leaves the surrounding
        # qualification/measure question intact. No arbitrary substring period.
        match = re.search(r'旺季\s*[（(]\s*'+core+r'\s*[）)]', text)
        if match is None or re.search(r'不是|并非|不要|不按|排除|例如|比如|示例|假设|可能|或者|还是', text[:match.start()]):
            return None
        outside = text[:match.start()] + text[match.end():]
        if re.search(r'\d{4}\s*年|'+_MONTH_NUMBER+r'\s*月|季度|半年|不是这个期间|不按(?:这个|该|上述)(?:期间|旺季)|排除这段', outside):
            return None
    first, last = _month_number(match['first']), _month_number(match['last'])
    if not 1 <= first <= last <= 12:
        return None
    if match['count'] and _month_number(match['count']) != last-first+1:
        return None
    if not (match['month_end'] or match['count'] or month_convention_quote(convention)):
        return None
    if match['last_year'] and match['last_year'] != match['year']:
        return None  # No implicit cross-year season or omitted first year.
    try:
        if match['year']:
            year = int(match['year'])
        else:
            current = (established or {}).get('current') or {}
            anchor = date.fromisoformat(current['start'])
            boundary = date.fromisoformat(current['end'])
            if not anchor < boundary <= date(anchor.year+1,1,1):
                return None
            year = anchor.year
        start = date(year,first,1)
        end = date(year+1,1,1) if last==12 else date(year,last+1,1)
    except (KeyError,TypeError,ValueError,OverflowError):
        return None
    return {'current': {'start':start.isoformat(),'end':end.isoformat(),
                        'grain':'custom','label':match.group().strip()}}


def parse_calendar_range(text: str, established: dict | None = None) -> tuple[bool, dict | None]:
    """Return (range_detected, proven_half_open_period_or_None).

    A right calendar day explicitly included is represented by next midnight,
    consistent with the existing day-range convention. A lower exclusive
    timestamp endpoint is unsupported; it is not shifted to the next day.
    """
    endpoints = list(_DATE.finditer(text))
    # Broad extraction also detects unsupported written-number ranges. It
    # does not interpret their dates or let a proposed model day bypass L2.
    months = list(re.finditer(r'(?<!\d)(?:\d{4}\s*年\s*)?(?:\d{1,2}|[一二两三四五六七八九十〇零廿卅]{1,4})\s*月', text))
    if len(endpoints) != 2 and len(months) >= 2 and re.search(_CONNECTOR, text[months[0].end():months[1].start()], re.I):
        return True, parse_whole_month_reply(text, established)
    if not endpoints:
        return False, None
    if len(endpoints) < 2:
        # A partial/unimplemented right endpoint still prevents first-day
        # fallback (e.g. Chinese numeral dates or an unfinished range).
        tail = text[endpoints[0].end():]
        detected = bool(re.match(r'\s*(?:' + _BOUNDARY + r')?\s*' + _CONNECTOR, tail, re.I))
        return detected, None
    between = text[endpoints[0].end():endpoints[1].start()]
    detected = bool(re.search(_CONNECTOR, between, re.I))
    if not detected:
        return False, None
    if len(endpoints) != 2:
        return True, None
    first, last = endpoints
    if re.search(r'(?:不是|并非|不要(?:查询|统计|查)?|不查|不统计|排除)\s*$', text[:first.start()]):
        return True, None
    if not (first['year'] or last['year'] or '月' in first.group() or '月' in last.group()):
        return False, None
    gap = re.fullmatch(r'\s*(?P<left>' + _BOUNDARY + r')?\s*(?:起\s*)?' + _CONNECTOR +
                       r'\s*(?P<next>次年|翌年)?\s*', between, re.I)
    if gap is None:
        return True, None
    suffix = text[last.end():]
    right = re.match(r'\s*(?P<bound>' + _BOUNDARY + r')?', suffix)
    left_mark = gap['left'] or ''
    right_mark = right['bound'] or ''
    rest = suffix[right.end():]
    if ((right_mark and not right_mark.lstrip().startswith(('（', '(')) and
         re.match(r'\s*(?!的)[\u4e00-\u9fffA-Za-z]', rest)) or
            re.match(r'\s*(?:之后|以后|上午|下午|中午|凌晨|午夜|晚上|时区)', rest)):
        return True, None  # Never truncate "不含税" into a date exclusion.
    if (re.match(r'\s*(?:' + _BOUNDARY + r'|[（(])', rest) or
            re.match(r'\s*(?:T\s*)?\d{1,2}(?::\d{2}|\s*[点时])', suffix, re.I) or
            re.match(r'\s*(?:T\s*)?\d{1,2}(?::\d{2}|\s*[点时])', rest, re.I) or
            re.search(r'UTC|GMT|北京时间|时区', between + suffix, re.I)):
        return True, None
    if re.search(r'不含|不包含|不包括|之前', left_mark):
        return True, None  # No invented timestamp epsilon or next-day shift.
    current = (established or {}).get('current') or {}
    try:
        anchor_year = date.fromisoformat(current['start']).year if current.get('start') else None
        first_year = int(first['year']) if first['year'] else anchor_year
        if first_year is None:
            return True, None
        last_year = int(last['year']) if last['year'] else first_year + bool(gap['next'])
        if gap['next'] and last['year'] and last_year != first_year + 1:
            return True, None
        start = date(first_year, int(first['month']), int(first['day']))
        end = date(last_year, int(last['month']), int(last['day']))
        if right_mark:
            exclusive = bool(re.search(r'不含|不包含|不包括|之前', right_mark))
        elif first['year'] and last['year']:
            exclusive = False  # Preserve the existing fully explicit range rule.
        else:
            return True, None  # Do not invent an end convention for a partial range.
        if not exclusive:
            end += timedelta(days=1)
        if start >= end:
            return True, None  # No implicit cross-year rollover.
    except (ValueError, OverflowError):
        return True, None
    return True, {'current': {'start': start.isoformat(), 'end': end.isoformat(),
                             'grain': 'custom', 'label': text[first.start():last.end() + right.end()].strip()}}
