"""One authority for explicit percentage display precision, never an implicit default."""
from __future__ import annotations

from qa_agent.clarify.output_requirements import precision_events


def requested_percent_digits(intent, fail):
    get = lambda name, default=None: intent.get(name, default) if isinstance(intent, dict) else getattr(intent, name, default)
    digits = set()
    def collect(text):
        return {event.digits for event in precision_events(text) if 'percent' in event.subjects and not event.negative and not event.ambiguous}
    for text in get('output_requirements', []) or []:
        digits.update(collect(text))
    query = get('query_scope', {}) or {}
    typed, source = query.get('requested_percent_decimals'), query.get('percent_precision_source') or {}
    if isinstance(source,dict) and source.get('source') in {
            'program:explicit_percent_precision_removed','program:explicit_percent_precision_pending'}:
        if typed is not None or digits:
            fail('已撤销或待澄清的百分比精度不能由旧位数或输出散文重新授权。')
        return None
    if typed is not None:
        if (not isinstance(typed, int) or isinstance(typed, bool) or not 0 <= typed <= 9 or
                not isinstance(source, dict) or source.get('source') != 'program:explicit_percent_precision'):
            fail('百分比精度字段缺少合法程序来源，不能授权SQL舍入。')
        if collect(source.get('evidence')) != {typed}:
            fail('百分比精度字段与真实来源的位数不一致或来源有冲突。')
        digits.add(typed)
    if len(digits) > 1:
        fail('百分比展示精度要求冲突，不能自行选择。')
    if any(not 0 <= value <= 9 for value in digits):
        fail('百分比精度仅支持0至9位小数。')
    return next(iter(digits)) if digits else None
