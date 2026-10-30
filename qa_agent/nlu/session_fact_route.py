"""S1-only source-backed recall of a session label, never a tool grant.

The existing composed planner still validates source permissions and answers.
This hint cannot turn a numerical query into an approved definition/default.
"""
from __future__ import annotations

from hashlib import sha256
import re


_SESSION = re.compile(r'这次(?:的)?(?:复盘|会话)|本次(?:复盘|会话)|本轮(?:复盘|会话)|'
    r'咱们(?:这次)?复盘|(?:开头|前面|刚才)(?:那份)?(?:说明|正文|复盘)|'
    r'(?:正文|说明|资料)(?:里|中|里的|中的)')
_TERM = re.compile(r'门槛|阈值|定义|口径|名单|称呼|叫法|含义|意思')
_RECALL = re.compile(r'是多少(?:来着)?|是什么(?:来着)?|指(?:的是什么|什么|哪些)|'
    r'怎么(?:定义|叫|称呼)|如何定义|有哪些|包括哪些|哪几个|哪几国|叫什么|都有谁|列出.*名单')
_CALCULATION = re.compile(r'计算|统计|汇总|合计|求出|算出|算一下|查出|查询|'
    r'(?:销售额|销量|消费金额|发票金额|总额|平均|占比|比例)(?:是|有|为)?多少|'
    r'(?:多少|几)\s*(?:张|位|名|首|笔|件|条)|'
    r'列出\s*(?:符合|满足|达到|超过|低于|高于|所有)?\s*(?:客户|发票|订单|曲目)')
_UNSET = re.compile(r'例如|比如|示例|假设|可能|尚未|还没|未定|没定|待定|'
    r'未定义|不是|并非|不指|不再|取消|删除|作废|不要')
_DEFINITION = re.compile(r'^\s*[“‘\"\']?(?P<label>[A-Za-z0-9_\u4e00-\u9fff· ()（）]{1,32}?)'
    r'[”’\"\']?\s*(?:[:：]\s*(?:指|是)?|(?:仅指|只指|指(?:的是)?|就是|称为|叫作))'
    r'\s*(?P<definition>.+?)\s*$')
_RELATION = re.compile(r'(?:是不是|是否|算不算)\s*(?:一回事|一码事|一个意思|同义(?:词)?)|'
    r'是\s*同义词\s*吗')
_QUOTED = re.compile(r'“([^”\n]{1,32})”|"([^"\n]{1,32})"|‘([^’\n]{1,32})’|\x27([^\x27\n]{1,32})\x27')


def _relation_recall(question, runtime):
    """Route a source-backed definition comparison, never decide equivalence."""
    labels = list(dict.fromkeys(next(g for g in m.groups() if g is not None)
                               for m in _QUOTED.finditer(question)))
    if not 2 <= len(labels) <= 6:
        return None
    remaining = _RELATION.sub('', question)
    # A stated future use is not a request to execute its list now. Only this
    # bounded list intention is removed; immediate numeric/list work stays SQL.
    remaining = re.sub(r'(?:^|(?<=[。！？!?；;\n]))\s*(?:后面|之后|以后|稍后|接下来|下一步)'
        r'[^。！？!?；;\n]{0,80}列名单[。！？!?；;\n]', '', remaining)
    remaining = re.sub(r'(?:这个|该)?(?:门槛|阈值)(?:是|为)?几(?:张|笔)发票', '', remaining)
    if (_CALCULATION.search(remaining) or _UNSET.search(remaining)
            or re.search(r'哪些客户|哪些人|列(?:出)?[^。！？!?；;\n]{0,16}(?:名单|客户|发票|记录)', remaining)):
        return None
    refs = []
    for label in labels:
        candidates = []
        for match in _QUOTED.finditer(runtime.text):
            if next(g for g in match.groups() if g is not None) != label:
                continue
            definition = re.match(r'\s*[:：，,]?\s*(?:我|那)?'
                r'(?:仅指|只指|指(?:的(?:是|就是)?)?|就是(?:指)?|即(?:是)?|是指)'
                r'\s*(?P<body>[^。；;\n，,]+)', runtime.text[match.end():])
            if definition is None:
                continue
            prefix = re.split(r'[。；;\n]', runtime.text[:match.start()])[-1]
            if _UNSET.search(prefix) or _UNSET.search(definition['body']):
                return None
            start, end = match.start(), match.end() + definition.end()
            candidates.append((re.sub(r'\s+', '', definition['body']).casefold(), start, end))
        if not candidates or len({body for body, _, _ in candidates}) != 1:
            return None
        _, start, end = candidates[0]
        refs.append({'source_id':'brief', 'quote':runtime.text[start:end], 'start':start, 'end':end,
            'source_sha256':runtime.content_sha256, 'context_id':runtime.context_id,
            'context_version':runtime.version})
    return {'route':'composed', 'kind':'session_definition_relation_recall', 'labels':labels,
        'source_refs':refs, 'current_ref':{'source_id':'current', 'quote':question,
            'source_sha256':sha256(question.encode('utf-8')).hexdigest()},
        'authority':'仅有原文证据的会话术语关系解释路由；不判定同义，不选择默认、名单或确认状态'}


def _literal_occurs(label: str, question: str) -> bool:
    for match in re.finditer(re.escape(label), question, re.I):
        # ASCII identifier tokens need a real boundary; Chinese labels do not
        # require whitespace and must stay an exact original surface.
        before = question[match.start()-1:match.start()]
        after = question[match.end():match.end()+1]
        if ((label[0].isascii() and before and re.match(r'[A-Za-z0-9_]', before))
                or (label[-1].isascii() and after and re.match(r'[A-Za-z0-9_]', after))):
            continue
        return True
    return False


def session_fact_route_hint(question: str, *, nlu_enabled: bool = False,
                            semantic_gate: bool = True, runtime=None) -> dict | None:
    """Advise composed recall only for a source-verified session definition.

    No SQL, body-derived new default, value binding, semantic state or external
    source is selected here. Unknown or conflicting definitions have no hint.
    """
    if not nlu_enabled or semantic_gate:
        return None
    if _RELATION.search(question):
        if runtime is None:
            from qa_agent.context import current_context
            runtime = current_context()
        if (runtime is None or not runtime.session_id or not runtime.context_id
                or runtime.current_user_message != question or not runtime.text
                or sha256(runtime.text.encode('utf-8')).hexdigest() != runtime.content_sha256):
            return None
        return _relation_recall(question, runtime)
    if not (_SESSION.search(question) and _TERM.search(question) and _RECALL.search(question)):
        return None
    if _CALCULATION.search(question) or _UNSET.search(question):
        return None
    if runtime is None:
        from qa_agent.context import current_context
        runtime = current_context()
    if (runtime is None or not runtime.session_id or not runtime.context_id
            or runtime.current_user_message != question or not runtime.text
            or sha256(runtime.text.encode('utf-8')).hexdigest() != runtime.content_sha256):
        return None
    definitions = {}
    for match in re.finditer(r'[^。；;\n]+', runtime.text):
        clause = match.group()
        definition = _DEFINITION.fullmatch(clause)
        if definition is None:
            continue
        label = definition['label'].strip()
        if not label or not _literal_occurs(label, question):
            continue
        # A literal quote proves availability, not acceptance of an uncertain,
        # example or cancelled definition. Separate conflicting bodies fail closed.
        # A disclaimer about policy status does not negate the session's own
        # label. All other uncertain/negated definitions remain unsupported.
        certainty_text=re.sub(r'不是(?:公司政策|公司制度|正式政策|政策)', '', clause)
        if _UNSET.search(certainty_text):
            return None
        definitions.setdefault(label, []).append((definition['definition'], match))
    if len(definitions) != 1:
        return None
    label, candidates = next(iter(definitions.items()))
    bodies = {re.sub(r'\s+', '', body).casefold() for body, _ in candidates}
    if len(bodies) != 1:
        return None
    _, found = candidates[0]
    quote = found.group().strip()
    start = found.start() + len(found.group())-len(found.group().lstrip())
    return {'route': 'composed', 'kind': 'session_definition_recall', 'label': label,
        'source_ref': {'source_id':'brief', 'quote':quote, 'start':start,'end':start+len(quote),
            'source_sha256':runtime.content_sha256, 'context_id':runtime.context_id,
            'context_version':runtime.version},
        'current_ref': {'source_id':'current', 'quote':question,
            'source_sha256':sha256(question.encode('utf-8')).hexdigest()},
        'authority': '仅原文定义回忆的路由建议；不是确认状态、业务默认或工具授权'}
