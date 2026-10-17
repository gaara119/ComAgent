"""A season requires real dates; a model's calendar grain is not evidence."""
from __future__ import annotations
from copy import deepcopy
import re


def actual_calendar_anchor(question, payload):
    """Only literal calendar words and the injected clock can anchor a year."""
    from qa_agent.clarify.rules import explicit_period
    from qa_agent.clarify.grounding import partial_calendar_period, literal_relative_period
    years = set(re.findall(r'(?<!\d)(\d{4})\s*年', question))
    if len(years) == 1:
        year = next(iter(years))
        anchor = explicit_period(year + '年')
        without_year = re.sub(r'(?<!\d)' + year + r'\s*年', '', question)
        exact_range = partial_calendar_period(without_year, anchor)
        if exact_range:
            exact_range['current']['year_source'] = 'explicit_user_calendar_year'
            return exact_range
    literal = explicit_period(question)
    if literal is None and re.search(r'\d{4}\s*年\s*[上下]半年', question):
        from qa_agent.clarify.temporal_role import literal_hire_calendar_period
        half = literal_hire_calendar_period(question)
        if half:
            literal = {'current': {**half, 'grain': 'custom', 'label': question}}
    if literal:
        return literal
    relative = literal_relative_period(question, payload)
    if relative:
        exact_range = partial_calendar_period(question, relative)
        if exact_range:
            exact_range['current']['year_source'] = 'injected_clock_relative_year'
            return exact_range
        year = relative['current']['start'][:4]
        expanded = re.sub(r'前年|去年|今年|明年', year + '年', question, count=1)
        return explicit_period(expanded) or relative
    return None


def annual_definition_period(body, anchor):
    """Transfer a season only when its real definition explicitly recurs yearly."""
    if (not re.search(r'每年|每个自然年', body) or re.search(r'(?<!\d)\d{4}(?:\s*年|-)', body)
            or not anchor or (anchor.get('current') or {}).get('grain') != 'year'):
        return None
    from qa_agent.clarify.rules import explicit_period
    from qa_agent.clarify.grounding import partial_calendar_period
    period = partial_calendar_period(body, anchor)
    year = anchor['current']['start'][:4]
    quarter = re.search(r'第?[一二三四1-4]\s*季度', body)
    months = re.findall(r'(?<!\d)(\d{1,2})\s*月', body)
    if period is None and quarter:
        period = explicit_period(year + '年' + quarter.group())
    if period is None and len(months) == 1 and not re.search(r'\d\s*日', body):
        period = explicit_period(year + '年' + months[0] + '月')
    if period:
        period['current']['year_source'] = 'explicit_user_year_and_annual_definition'
    return period


def calendar_source_record(question, payload, source='explicit_user'):
    """The real calendar span, not a lower-priority definition, owns its source."""
    record = {'source':source, 'evidence':question, 'lifetime':'task', 'applies_to':'global'}
    if source == 'explicit_user' and re.search(r'前年|去年|今年|明年', question):
        record.update(reference_datetime=payload.get('reference_datetime'), timezone=payload.get('timezone'))
    return record


def adjacent_season_anchor(question, payload):
    """Only an actual immediately preceding season turn can supply its base year."""
    history = payload.get('actual_conversation') or []
    if not re.search(r'接着|刚才|上述|那(?:个)?旺季|同期', question) or not history or not isinstance(history[-1], dict):
        return None
    latest = history[-1]
    actual = str(latest.get('user') or '')
    if '旺季' not in actual:
        return None
    anchor = actual_calendar_anchor(actual, payload)
    saved = ((latest.get('intent') or {}).get('time_scope') or {}).get('current') or {}
    if anchor and all(saved.get(key) == anchor['current'].get(key) for key in ('start','end')):
        return anchor, actual
    return None


def temporal_source_matches(analysis, item, question, payload):
    """A real quote is necessary; an incompatible calendar quote is not proof."""
    current = (analysis.time_scope or {}).get('current') or {}
    if not current:
        # A year quote cannot substantiate all-data, or an absent interval.
        return bool((analysis.time_scope or {}).get('all_data') and re.search(
            r'全部数据|所有数据|所有年份|全部年份|不限(?:时间|期间|年份)|(?:去掉|取消|删除).{0,8}(?:时间|期间|年份)',
            str(item.get('evidence') or '')))
    evidence = str(item.get('evidence') or '')
    source = item.get('source')
    period = actual_calendar_anchor(evidence, payload)
    if source == 'confirmed_history':
        from qa_agent.clarify.grounding import confirmed_history_period
        if not confirmed_history_period(payload, evidence, analysis.time_scope):
            return False
        # A partial actual date reply can be grounded by its saved, confirmed period.
        if period is None:
            from qa_agent.clarify.grounding import partial_calendar_period
            period = partial_calendar_period(evidence, analysis.time_scope)
    if period is None and re.search(r'每年|每个自然年', evidence):
        anchor = actual_calendar_anchor(str(payload.get('current_user_message') or question), payload)
        period = annual_definition_period(evidence, anchor)
        if period:
            item['calendar_anchor'] = calendar_source_record(str(payload.get('current_user_message') or question), payload)
    if period:
        return all(current.get(key) == period['current'].get(key) for key in ('start','end'))
    return False  # A real but non-calendar fragment is not period evidence.


def confirmed_season_calendar_edit(message, state):
    """Recognize a bounded calendar-only edit of a real confirmed season."""
    if state is None or state.analysis.time_ambiguous:
        return None
    authority=state.analysis.query_scope.get('season_time_authority') or {}
    current=(state.analysis.time_scope or {}).get('current') or {}
    if (authority.get('status')!='confirmed' or authority.get('source')!='program:explicit_season_period'
            or not authority.get('evidence') or any((authority.get('period') or {}).get(k)!=current.get(k) for k in ('start','end'))):
        return None
    calendar=r'(?:\d{4}\s*年|前年|去年|今年|明年)'
    year_edit=re.fullmatch(r'\s*(?:那)?(?:只|仅)?(?:换成|改成|改为|改看|(?:改)?年份(?:改为|为|换成))\s*'+calendar+r'\s*(?:全年|整年)?(?:[，,]\s*(?:旺季月份|月份|其他条件|其它条件)不变)?\s*[。？！?!]?\s*',message)
    retire=re.fullmatch(r'\s*(?:(?:旺季(?:先|暂时)?放一边|不看旺季了?)[，,]\s*)?(?:改看|改查|换成|改成)\s*(?:'+calendar+r')?\s*(?:全年|整年)\s*[。？！?!]?\s*',message)
    if not year_edit and not retire:
        return None
    return 'whole_year' if retire or re.search(r'全年|整年',message) else 'year_only'


def season_calendar_edit_period(message, state, period, payload):
    """Retain confirmed month/day conditions when only the year is edited."""
    kind=confirmed_season_calendar_edit(message,state)
    if kind is None:
        return period, False
    from datetime import date
    from qa_agent.clarify.rules import explicit_period
    from qa_agent.clarify.state import SessionConflict
    old=state.analysis.time_scope['current']
    if period is None:
        year=re.search(r'(?<!\d)(\d{4})\s*年',message)
        if year:
            period=explicit_period(year.group())
        elif re.search(r'前年|去年|今年|明年',message):
            from qa_agent.clarify.grounding import literal_relative_period
            period=literal_relative_period(message,payload)
            if period is None:
                raise SessionConflict('相对年份缺少可信参考时钟，请明确目标年份。')
    if kind=='whole_year':
        year=(period or {}).get('current',{}).get('start',old['start'])[:4]
        return explicit_period(year+'年'), True
    if not period or (period.get('current') or {}).get('grain')!='year':
        return period, False
    start=date.fromisoformat(old['start']);end=date.fromisoformat(old['end'])
    new_year=date.fromisoformat(period['current']['start']).year
    try:
        shifted_start=start.replace(year=new_year)
        shifted_end=end.replace(year=new_year+(end.year-start.year))
    except ValueError as exc:
        raise SessionConflict('新年份无法保留已确认的月日边界，请明确完整起止日期。') from exc
    return {'current':{**deepcopy(old),'start':shifted_start.isoformat(),'end':shifted_end.isoformat(),
        'label':message,'year_source':'previous_confirmed_season_calendar_edit'}}, False


def season_period_authority(question,analysis,payload):
    analysis.query_scope.pop('season_time_authority',None)
    if '旺季' not in question or re.search(r'(?:不看|不算|取消|去掉|不按|不是|不用).{0,4}旺季|旺季.{0,8}(?:放一边|取消|不看)',question):return analysis
    from qa_agent.clarify.rules import explicit_period
    from qa_agent.clarify.grounding import partial_calendar_period
    from qa_agent.clarify.definition_recovery import complete_definitions
    proven=None;quote=None;source=None
    actual_anchor = actual_calendar_anchor(question, payload)
    literal=actual_anchor
    # A year in a question containing '旺季' proves the base year only.
    has_months=bool(re.search(r'\d{1,2}\s*月|\d{4}-\d{1,2}-\d{1,2}|第?[一二三四1-4]季度',question))
    if literal and has_months and (literal.get('current') or {}).get('grain') in {'custom','month','quarter'}:
        proven=literal;quote=question;source='explicit_user'
    definitions=complete_definitions(payload).get('旺季',[])
    if proven is None and len(definitions)==1:
        clause=definitions[0];body=re.split('[:：]',clause,maxsplit=1)[-1].strip()
        period=(actual_calendar_anchor(body, payload) or annual_definition_period(body, actual_anchor)) if re.match(r'只指|仅指|指(?:的是)?|就是|是|为',body) else None
        if period and (period.get('current') or {}).get('grain') in {'custom','month','quarter'}:
            proven=period;quote=clause;source='user_brief'
    history=payload.get('actual_conversation') or []
    refers=bool(re.search(r'接着|刚才|上述|那三个月|那(?:个)?旺季|同期',question))
    if proven is None and refers and history and isinstance(history[-1],dict):
        latest=history[-1];actual=str(latest.get('user') or '')
        prior=history[-2] if len(history)>1 and isinstance(history[-2],dict) else {}
        prior_user=str(prior.get('user') or '')
        was_season_reply=('旺季' in actual or '旺季' in prior_user and bool(prior.get('clarification')))
        prior_intent=prior.get('intent') or {};latest_intent=latest.get('intent') or {}
        actual_period=explicit_period(actual) or partial_calendar_period(actual,prior_intent.get('time_scope'))
        saved=(latest_intent.get('time_scope') or {}).get('current') or {}
        incoming=(analysis.time_scope or {}).get('current') or {}
        if actual_period is None and saved and all(incoming.get(key)==saved.get(key) for key in ('start','end')):
            # An already verified history-period proposal can anchor its own
            # literal month/day quote. A rejected or absent incoming period cannot.
            actual_period=partial_calendar_period(actual,latest_intent.get('time_scope'))
        current=(actual_period or {}).get('current') or {}
        if (was_season_reply and re.search(r'\d{1,2}\s*月|\d{4}-\d{1,2}-\d{1,2}',actual) and current and
             all(current.get(key)==saved.get(key) for key in ('start','end'))):
            proven=deepcopy(latest_intent['time_scope']);quote=actual;source='confirmed_history'
    if proven and actual_anchor is None and re.search(r'(?<!\d)\d{4}\s*(?:年|-)|前年|去年|今年|明年', question):
        # Multiple or unsupported actual calendar restrictions are not a
        # license to select one fixed year from a lower-priority definition.
        proven = None
    if proven and actual_anchor:
        current = actual_anchor.get('current') or {}
        candidate = proven.get('current') or {}
        # A fixed-year definition or past reply cannot replace an actual
        # present-turn calendar restriction. Conflicts remain a real L2.
        if not (current.get('start') and current.get('end') and candidate.get('start') and candidate.get('end')
                and current['start'] <= candidate['start'] < candidate['end'] <= current['end']):
            proven = None
            analysis.time_scope = deepcopy(actual_anchor)
    if proven:
        analysis.time_scope=deepcopy(proven);analysis.time_ambiguous=False
        analysis.condition_sources['time_scope']={'source':source,'evidence':quote,'lifetime':'task','applies_to':'global'}
        analysis.query_scope['season_time_authority']={'status':'confirmed','source':'program:explicit_season_period',
            'evidence':quote,'period':deepcopy(proven['current'])}
        analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field') not in {'time_scope','time_scope.current'}]
    else:
        if actual_anchor:
            # Base-year confirmation is separate from confirming the season's months.
            # Update interval and provenance together; the stale model source cannot survive.
            analysis.time_scope = deepcopy(actual_anchor)
            analysis.condition_sources['time_scope'] = calendar_source_record(question, payload)
        else:
            inherited = adjacent_season_anchor(question, payload)
            if inherited:
                analysis.time_scope = deepcopy(inherited[0])
                analysis.condition_sources['time_scope'] = calendar_source_record(inherited[1], payload, 'confirmed_history')
            else:
                analysis.time_scope = None
                analysis.condition_sources.pop('time_scope', None)
        analysis.time_ambiguous=True
        analysis.query_scope['season_time_authority']={'status':'unresolved','source':'program:season_period_not_confirmed','evidence':question}
        analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field') not in {'time_scope','time_scope.current'}]
        analysis.clarification_requests.append({'field':'time_scope.current','question':'请明确旺季的具体月份或起止日期。',
            'reason':'当轮和实际会话记录尚无已确认的旺季日期，主期间或grain标签不能代替旺季定义。','evidence':question})
    # Free prose is never a source-priority decision. The typed conflict
    # verifier owns its lifecycle; old unstructured claims remain unknown.
    return analysis
