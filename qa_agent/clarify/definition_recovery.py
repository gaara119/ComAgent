"""Recover activated, complete user definitions without model filter proposals."""
from __future__ import annotations
import re
from collections import defaultdict


def complete_definitions(payload):
    definitions = defaultdict(dict)
    corpus = [str(payload.get('user_brief') or '')]
    corpus += [str(turn.get('user') or '') for turn in payload.get('actual_conversation', []) if isinstance(turn, dict)]
    for text in corpus:
        for line in text.splitlines():
            for match in re.finditer(r'[“"‘]([^”"’]{2,24})[”"’]\s*[:：]', line):
                clause = re.split(r'[。；;\n]', line[match.start():], maxsplit=1)[0]
                key = re.sub(r'\s+', '', clause).translate(str.maketrans({'“':'"', '”':'"', '‘':'"', '’':'"'}))
                definitions[match.group(1)][key] = clause
    return {name: list(clauses.values()) for name, clauses in definitions.items()}


def label_is_retired(label,question):
    occurrences=list(re.finditer(re.escape(label),question))
    if not occurrences:return False
    statuses=[]
    for match in occurrences:
        before=question[max(0,match.start()-10):match.start()]
        after=question[match.end():match.end()+14]
        following=bool(re.match(r'[”"’\x27]?\s*(?:的(?:限制|条件)\s*)?(?:先|暂时|暂且)?\s*(?:放一边|不看|不算|不考虑|不用|去掉|取消|删除)',after))
        preceding=re.search(r'(?:不看|不算|不考虑|不再限制|去掉|取消|删除|放弃)\s*(?:这些|这批|所有|全部)?\s*[“"‘\x27]?\s*$',before)
        negated=bool(preceding and re.search(r'不要|不能|别|并非|不是',before[:preceding.start()]))
        statuses.append(following or bool(preceding and not negated))
    # Conflicting positive/retired references do not authorize deleting a
    # scope. The semantic gate must handle that uncertainty separately.
    return all(statuses)


def label_is_referenced(label, question):
    if label_is_retired(label,question):
        return False
    if label in question:
        return True
    from qa_agent.nlu.value_index import pinyin_key
    if pinyin_key(label) in re.sub(r'[^a-z]', '', question.casefold()):
        return True
    # A label's untranslated head must remain explicit. Bare "market" or a
    # country example does not activate every named geographic list.
    if label.endswith('市场') and label[:-2]:
        return bool(re.search(re.escape(label[:-2]) + r'\s*market\b', question, re.I))
    return False


def closed_country_members(label, clause):
    if not re.search(r'市场|国家|地区|区域', label):
        return None
    match = re.search(r'只指|仅指', clause)
    if not match:
        return None
    body = clause[match.end():]
    declared=re.search(r'(?:这|共|合计)([\d一二两三四五六七八九十]+)(?:个)?(?:国家|市场|地区|国)',body)
    body = re.split(r'(?:这|共|合计)[\d一二两三四五六七八九十]+(?:个)?(?:国家|市场|地区|国)', body, maxsplit=1)[0]
    if re.search(r'…|\.\.\.|等(?:等|国家|市场|地区)?\s*$',body):
        return None
    members = [part.strip() for part in re.split(r'[、，,]|\s*[和与及]\s*', body) if part.strip()]
    canonical = []
    for member in members:
        names = [re.split(r'[（(]', member, maxsplit=1)[0].strip()]
        names += re.findall(r'[（(]([^）)]+)[）)]', member)
        english = [name for name in names if re.fullmatch(r'[A-Za-z][A-Za-z .\-]*', name)]
        if len(english) != 1:
            return None  # A translation is not a canonical database literal.
        canonical.append(english[0])
    if declared:
        from qa_agent.clarify.literal_structures import number
        if number(declared.group(1))!=len(canonical):return None
    return canonical if canonical and len(set(canonical)) == len(canonical) else None


def duration_threshold(clause):
    if not re.search(r'时长|时间|分钟|毫秒', clause):
        return None
    candidates = []
    for match in re.finditer(r'(不超过|小于等于|不低于|不少于|至少|超过|大于|小于|低于|至多)\s*(\d+(?:\.\d+)?|[一二两三四五六七八九十])\s*(毫秒|分钟|秒)', clause):
        operator = {'不超过':'<=', '小于等于':'<=', '不低于':'>=', '不少于':'>=', '至少':'>=',
                    '超过':'>', '大于':'>', '小于':'<', '低于':'<', '至多':'<='}[match.group(1)]
        word=match.group(2)
        value=float(word) if re.fullmatch(r'\d+(?:\.\d+)?',word) else float({'一':1,'二':2,'两':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}[word])
        number = value * {'毫秒':1, '秒':1000, '分钟':60000}[match.group(3)]
        if number.is_integer():
            candidates.append((operator, int(number)))
    values = set(candidates)
    return next(iter(values)) if len(values) == 1 else None


def recover_activated_definitions(question, analysis, payload, catalog):
    """Only one actual definition and a current reference can activate scope."""
    from qa_agent.clarify.grounding import contextual_filters, schema_columns
    definitions=complete_definitions(payload)
    if not definitions:
        return analysis
    if not getattr(catalog,'tables',None):
        raise ValueError('缺少真实目录，无法核验会话命名定义涉及的字段。')
    columns = schema_columns(catalog)
    existing = list(analysis.filters)
    for label, clauses in definitions.items():
        if len(clauses) != 1 or not label_is_referenced(label, question):
            continue
        clause = clauses[0]
        repeat_count=re.search(r'至少(?:开过|有|购买)?\s*(2|两|二)\s*张发票',clause)
        if repeat_count and re.search(r'客户',label) and re.search(re.escape(label)+r'.{0,8}(?:有多少|多少|几位|几名|数量)',question):
            # Canonicalize only the already registered >=2-invoice customer
            # count; an arbitrary different threshold is not that metric.
            analysis.metric='repeat_customer_count'
            analysis.condition_sources['metric']={'source':'user_brief','evidence':clause,'lifetime':'task','applies_to':'global'}
        countries = closed_country_members(label, clause)
        proposal = None
        if countries:
            explicit_customer = bool(re.search(r'客户(?:所在地|所在国|档案)|(?:国家|各国|市场|market).{0,24}客户.*分别', question, re.I))
            column = 'customer.country' if explicit_customer or analysis.region_scope == 'customer.country' else 'invoice.billing_country'
            proposal = {'column':column, 'operator':'IN', 'value':countries, 'scope_evidence':clause}
        else:
            threshold = duration_threshold(clause)
            if threshold and re.search(r'曲目|歌曲|曲子', label + clause):
                proposal = {'column':'track.milliseconds', 'operator':threshold[0], 'value':threshold[1], 'scope_evidence':clause}
        if proposal is None or proposal['column'] not in columns:
            continue
        grounded = contextual_filters([proposal], payload, catalog, question=question)
        if not grounded:
            continue
        item = grounded[0]
        marker = re.search(r'占(?:了)?', question)
        if analysis.task_type == 'ratio' and marker:
            before, after = question[:marker.start()], question[marker.end():]
            if label_is_referenced(label, before) and not label_is_referenced(label, after):
                item['binding_scope'] = 'numerator'
                if not analysis.numerator:
                    analysis.numerator = before.strip(' ，,？?')
                    analysis.condition_sources['numerator'] = {'source':'explicit_user', 'evidence':analysis.numerator,
                                                              'lifetime':'task', 'applies_to':'numerator'}
        # A complete program-recovered definition supersedes partial proposals
        # for this same named scope. Independent explicit literal filters stay.
        existing = [old for old in existing if not (old.get('source') == 'user_session_context' and
            old.get('column', old.get('field')) == item['column'] and label in str(old.get('scope_evidence') or ''))]
        if not any(old.get('column') == item['column'] and old.get('operator') == item['operator'] and old.get('value') == item['value']
                   and old.get('binding_scope') == item.get('binding_scope') for old in existing):
            existing.append(item)
    analysis.filters = existing
    return analysis


from qa_agent.clarify.output_requirements import (
    PERCENT_WORDS, precision_events, strip_unverified_percent_precision,
)


def strip_model_percent_precision(analysis):
    """Keep output obligations, but remove unverified prose scale grants."""
    retained=[]
    for requirement in analysis.output_requirements:
        for whole in strip_unverified_percent_precision(requirement):
            if whole and whole not in retained:retained.append(whole)
    analysis.output_requirements=retained


def recover_percent_precision(question, analysis, payload, *, preserve_confirmed=False):
    strip_model_percent_precision(analysis)
    if analysis.task_type not in {'ratio','growth'}:
        return analysis
    def candidates(text):
        found=[];denied=set();uncertain=set();masked=list(text)
        negative=r'不要|不得|不必|无需|不能|不准|禁止|别|并非|不是|(?<!不)不|do\s+not|not'
        for quote in re.finditer(r'“[^”]*”|‘[^’]*’|"[^"\n]*"',text):
            if re.fullmatch(PERCENT_WORDS,quote.group()[1:-1],re.I):continue
            prefix=re.split(r'[。；;\n，,、？！!?]',text[:quote.start()])[-1]
            adopted=bool(re.search(r'(?:按|依|采用|照|执行|use|follow)\s*$',prefix,re.I))and not re.search(negative,prefix,re.I)
            if adopted:continue
            if re.search(negative,prefix,re.I):
                denied.update(event.digits for event in precision_events(quote.group()) if 'percent'in event.subjects)
            masked[quote.start():quote.end()]=' '*len(quote.group())
        surface=''.join(masked)
        for event in precision_events(surface):
            if 'percent'not in event.subjects:continue
            decimals=event.digits
            prefix=re.split(r'[。；;\n，,、？！!?]',surface[:event.start])[-1]
            if event.ambiguous:uncertain.add(decimals);continue
            if event.negative:denied.add(decimals);continue
            if re.search(r'(?:示例|例如|比如|例子|写着)\s*[:：]?\s*$',prefix):continue
            found.append((decimals,text[event.start:event.end]))
        return found,denied,surface,uncertain
    actual=str(payload.get('current_user_message')or question)
    explicit,denied,surface,uncertain=candidates(actual)
    reset=re.search(r'(?:取消|去掉|删除|不再限制|不指定)[^\n，,。；;]{0,8}(?:'+PERCENT_WORDS+r')[^\n，,。；;]{0,10}(?:精度|小数|位数)|(?:'+PERCENT_WORDS+r')\s*(?:结果|数值|输出)?\s*(?:按原值(?:展示)?|不舍入|不四舍五入|不设精度|不限小数位)',surface,re.I)
    if reset and not re.search(r'不要|不能|别|不应|并非|不是|不\s*$',re.split(r'[。；;\n，,]',surface[:reset.start()])[-1]):
        analysis.query_scope.pop('requested_percent_decimals',None)
        analysis.query_scope['percent_precision_source']={'source':'program:explicit_percent_precision_removed',
            'evidence':actual[reset.start():reset.end()],'authority':'explicit_user'}
        analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('source')!='program:percent_precision']
        return analysis
    previous=analysis.query_scope.get('requested_percent_decimals')
    prior_source=(analysis.query_scope.get('percent_precision_source')or{}).get('source')
    if not explicit and not denied and not uncertain and preserve_confirmed and prior_source in{
            'program:explicit_percent_precision_removed','program:explicit_percent_precision_pending'}:
        if prior_source=='program:explicit_percent_precision_pending'and not any(
                item.get('source')=='program:percent_precision'for item in analysis.clarification_requests):
            # Another independently pending format may have occupied an old
            # generic card slot. The authoritative unresolved source survives;
            # derive its question again instead of silently treating it done.
            analysis.clarification_requests.append({'field':'output_precision','source':'program:percent_precision',
                'question':'百分比展示精度仍待确认，请用完整格式“百分比保留N位小数”指定所需精度（支持0至9位）。',
                'reason':'已保存的真实百分比格式尚未解决，不能因金额条件补齐而取消。'})
        return analysis
    if not explicit and not uncertain and preserve_confirmed and previous is not None and previous not in denied:
        return analysis
    brief,_,_,brief_uncertain=candidates(str(payload.get('user_brief') or ''))
    if uncertain or(not explicit and brief_uncertain):
        analysis.query_scope.pop('requested_percent_decimals',None)
        analysis.query_scope['percent_precision_source']={'source':'program:explicit_percent_precision_pending',
            'evidence':actual if uncertain else str(payload.get('user_brief')or''),
            'authority':'explicit_user'if uncertain else'user_brief','alternatives_not_verified':True}
        analysis.clarification_requests.append({'field':'output_precision','source':'program:percent_precision',
            'question':'百分比精度仍有未确定的备选或指代，请用完整格式“百分比保留N位小数”指定一种精度。',
            'reason':'当前未确定的真实格式要求不能被旧正文精度代替。'})
        return analysis
    found=explicit or [candidate for candidate in brief if candidate[0]not in denied]
    if not found:
        if denied:
            analysis.query_scope.pop('requested_percent_decimals',None)
            analysis.query_scope['percent_precision_source']={'source':'program:explicit_percent_precision_pending',
                'evidence':actual,'authority':'explicit_user','denied_decimals':sorted(denied)}
            analysis.clarification_requests.append({'field':'output_precision','source':'program:percent_precision',
                'question':'已排除一种百分比精度，请用完整格式“百分比保留N位小数”补充所需精度。','reason':'不能把被否定的精度当作授权。'})
        return analysis
    analysis.query_scope.pop('requested_percent_decimals',None)
    analysis.query_scope.pop('percent_precision_source',None)
    if len({value for value,clause in found})!=1 or any(not 0<=value<=9 for value,clause in found):
        # An actual unsupported/conflicting request is still an outstanding
        # source condition. An unrelated patch must not silently replace it
        # with a lower-priority brief's precision on the next turn.
        analysis.query_scope['percent_precision_source']={'source':'program:explicit_percent_precision_pending',
            'evidence':actual if explicit else str(payload.get('user_brief')or''),
            'authority':'explicit_user'if explicit else'user_brief',
            'requested_decimals':sorted({value for value,clause in found})}
        unsupported=any(not 0<=value<=9 for value,clause in found)
        analysis.clarification_requests.append({'field':'output_precision',
            'question':('当前仅支持0至9位小数，请用完整格式“百分比保留N位小数”补充所需精度。'if unsupported else
                        '百分比展示精度存在冲突，请用完整格式“百分比保留N位小数”补充所需精度。'),
            'source':'program:percent_precision','reason':'不能把真实但不支持或互相冲突的精度静默改成另一口径。'})
        return analysis
    decimals,clause=found[0]
    analysis.query_scope['requested_percent_decimals']=decimals
    analysis.query_scope['percent_precision_source']={'source':'program:explicit_percent_precision','evidence':clause,
        'authority':'explicit_user' if explicit else 'user_brief'}
    analysis.clarification_requests=[item for item in analysis.clarification_requests if not (
        item.get('source')=='program:percent_precision'or
        ((item.get('source_field')or item.get('field'))=='output_precision'and
         re.search(PERCENT_WORDS,str(item.get('question')or''),re.I)))]
    return analysis


def recover_money_precision(question,analysis,payload,*,preserve_confirmed=False):
    """A task-bound actual source also records a withdrawal, not just digits."""
    from qa_agent.sql.money_precision_source import money_precision_from_payload
    actual={**payload,'current_user_message':str(payload.get('current_user_message')or question)}
    prior=analysis.query_scope.get('money_precision_source')if preserve_confirmed else None
    source=money_precision_from_payload(actual,prior=prior)
    analysis.query_scope.pop('money_precision_source',None)
    analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('source')!='program:money_precision']
    if source is None:return analysis
    analysis.query_scope['money_precision_source']=source
    # Display accepts an explicitly sourced 0..9 scale, or an explicit raw
    # value withdrawal. Unknown alternatives are not an arbitrary new scale.
    if source.get('status')!='removed'and(not source.get('authorized')or type(source.get('digits'))is not int or not 0<=source['digits']<=9):
        analysis.clarification_requests.append({'field':'output_precision','source':'program:money_precision',
            'question':'请用完整格式“金额保留N位小数”明确金额精度（支持0至9位），或明确“金额按原值展示”。',
            'reason':'真实金额格式要求尚不能完整执行，不能回退旧正文精度或静默舍入。'})
    return analysis

