"""Program-owned conflict decisions from real user-source references.

The model proposes points; it never chooses priority, dependencies or status.
Unsupported/legacy material remains an unverified generic blocker, not prose
which can declare an unconfirmed date to have been applied.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json,re
from qa_agent.clarify.conflict_contract import ConflictRecord

UNKNOWN='存在一项尚未核验的条件歧义，请明确本轮采用的具体条件。'
ACTIVE='存在已核实的互斥条件，请明确本轮采用哪一个。'

def _key(value):return sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()

def build_conflict_sources(question,payload):
    """Only actual human messages/briefs enter this registry, never plans."""
    current=str(payload.get('current_user_message')or question)
    history=payload.get('actual_conversation')or[]
    sources={}
    def add(kind,text,version,*,intent=None,index=None):
        if not text:return
        digest=sha256(text.encode()).hexdigest()
        identifier=f'{kind}:{version}:{digest[:20]}'
        sources[identifier]={'source_id':identifier,'kind':kind,'source_version':version,
            'content_sha256':digest,'text':text,'intent':intent,'history_index':index}
    add('current_user',current,f'{payload.get("context_id")or"request"}:{len(history)}')
    add('user_brief',str(payload.get('user_brief')or''),payload.get('context_version',0))
    for index,turn in enumerate(history):
        if not isinstance(turn,dict):continue
        intent=turn.get('intent')or{}
        add('confirmed_history',str(turn.get('user')or''),f'{index}:{intent.get("intent_version",0)}',intent=intent,index=index)
    return sources

def conflict_source_catalog(question,payload):
    """Model picks supplied IDs; full texts are already in question/context."""
    return [{k:v for k,v in item.items()if k not in{'text','intent'}}
            for item in build_conflict_sources(question,payload).values()]

def _exact_span(ref,source):
    text=source['text'];quote=ref.quote
    if ref.source_version is not None and ref.source_version!=source['source_version']:return None
    if ref.content_sha256 is not None and ref.content_sha256!=source['content_sha256']:return None
    if ref.char_start is not None:
        start=ref.char_start;end=ref.char_end if ref.char_end is not None else start+len(quote)
        if end!=start+len(quote)or text[start:end]!=quote:return None
        return start,end
    if ref.char_end is not None:return None
    matches=[m.start()for m in re.finditer(re.escape(quote),text)]
    return (matches[0],matches[0]+len(quote))if len(matches)==1 else None

def _period(value):
    current=(value or{}).get('current')or{}
    return {key:current[key]for key in('start','end')if key in current}

def _unique_actual_anchor(text,payload):
    """Conservative: a parser finding its first date is not uniqueness proof."""
    from qa_agent.clarify.season_authority import actual_calendar_anchor
    from qa_agent.clarify.calendar_range import parse_calendar_range
    # Literal presence does not make an excluded/example calendar the active
    # query period. Scope these cues to the date predicate's own clause; a
    # separate "不要按销售数量" must not cancel a later explicit year.
    for token in re.finditer(r'(?<!\d)\d{4}\s*年|(?<!\d)\d{4}-\d{1,2}-\d{1,2}|前年|去年|今年|明年',text):
        before=re.split(r'[。；;\n，,？！!?]',text[:token.start()])[-1]
        after=re.split(r'[。；;\n，,？！!?]',text[token.end():])[0]
        if re.search(r'(?:不要|别|禁止|不再|不)(?:按|采用|使用|查询|查|看|选)?\s*(?:在)?\s*$|(?:不是|并非)\s*$|(?:示例|例如|比如|假设|举例)\s*[:：]?\s*$',before):return None
        if re.match(r'\s*(?:第?[一二三四1-4]\s*季度|[上下]半年|\d{1,2}\s*月(?:\d{1,2}\s*日)?)?\s*(?:(?:只是|仅为|仅是|作为|用作)\s*)?(?:示例|例子|假设)|\s*(?:并非|不是)(?:实际|本次|查询)(?:的)?(?:年份|期间)',after):return None
    if re.search(r'相比|对比|基期|比较|或者|或是|或第|或\d|分别|同时',text):return None
    if len(re.findall(r'[上下]半年',text))>1:return None
    is_range,range_value=parse_calendar_range(text)
    if is_range:
        if not range_value:return None
        label=str(range_value.get('current',{}).get('label')or'')
        if not label or text.count(label)!=1:return None
        remaining=text.replace(label,'',1)
        if re.search(r'\d{4}\s*年|\d{1,2}\s*月|季度|[上下]半年|前年|去年|今年|明年',remaining):return None
        return range_value
    if len(re.findall(r'第?[一二三四1-4]\s*季度',text))>1:return None
    if len(re.findall(r'(?<!\d)\d{1,2}\s*月',text))>1:return None
    if len(re.findall(r'(?<!\d)\d{4}\s*年',text))>1:return None
    if len(re.findall(r'前年|去年|今年|明年',text))>1:return None
    if (re.search(r'季度',text) and re.search(r'\d{1,2}\s*月|[上下]半年',text) or
            re.search(r'[上下]半年',text) and re.search(r'\d{1,2}\s*月',text) or
            re.search(r'\d{4}\s*年',text) and re.search(r'前年|去年|今年|明年',text)):return None
    return actual_calendar_anchor(text,payload)

def _time_fact(ref,source,question,payload):
    """A date in a source is insufficient: its real semantic role must match."""
    from qa_agent.clarify.season_authority import actual_calendar_anchor
    from qa_agent.clarify.definition_recovery import complete_definitions
    from qa_agent.clarify.rules import explicit_period
    span=_exact_span(ref,source)
    if span is None:return None
    if source['kind']=='current_user':
        # A fragment cannot drop a month/quarter actually specified this turn.
        whole=_unique_actual_anchor(source['text'],payload)
        quoted=_unique_actual_anchor(ref.quote,payload)
        if not whole or not quoted or _period(whole)!=_period(quoted):return None
        # A user quote may be a natural complete phrase or sentence. The
        # program extracts its unique date role and compares it with the
        # entire actual turn; the model need not guess the shortest span.
        return {'field':'time_scope.current','role':'actual_current_period','value':_period(whole),'priority':3}
    if source['kind']=='confirmed_history':
        if (source['history_index']!=len(payload.get('actual_conversation')or[])-1 or
                not re.search(r'刚才|上述|接着|同期|保持.{0,6}(?:期间|年份)|(?:期间|年份)不变',question)):return None
        quoted=_unique_actual_anchor(ref.quote,payload)
        whole=_unique_actual_anchor(source['text'],payload)
        saved=(source.get('intent')or{}).get('time_scope')
        if not quoted or not whole or _period(quoted)!=_period(whole)or _period(whole)!=_period(saved):return None
        # Like the current turn, a natural full historical sentence may be
        # quoted. Both its unique interval and the saved confirmed interval
        # must agree; a short year may not discard an actual month/quarter.
        return {'field':'time_scope.current','role':'actual_confirmed_history_period','value':_period(whole),'priority':2}
    # This bounded source verifier recognizes a real, unique fixed season
    # definition, not an arbitrary example/date in the same long document.
    if source['kind']!='user_brief' or '旺季'not in question:return None
    definitions=complete_definitions(payload).get('旺季',[])
    if len(definitions)!=1:return None
    clause=definitions[0]
    if clause not in source['text']:return None
    body=re.split('[:：]',clause,maxsplit=1)[-1].strip()
    if not re.match(r'^(?:只指|仅指|指(?:的是)?|就是|是|为)',body):return None
    literal=re.sub(r'^(?:只指|仅指|指(?:的是)?|就是|是|为)\s*','',body)
    parsed=explicit_period(literal);label=str((parsed or{}).get('current',{}).get('label')or'')
    compact=lambda text:re.sub(r'\s+','',text)
    # A complete actual definition commonly includes its sentence terminator.
    # Only that punctuation/outer whitespace may extend the exact core; never
    # take a substring out of extra negation, examples or other conditions.
    core=ref.quote.strip().rstrip('。；;.!！?？').rstrip()
    if not parsed or compact(label)!=compact(literal)or core not in{literal,clause}:return None
    positions=[m.start()for m in re.finditer(re.escape(clause),source['text'])]
    core_start=span[0]+ref.quote.index(core);core_end=core_start+len(core)
    applicable=[]
    for start in positions:
        prefix=re.split(r'[。；;\n]',source['text'][:start])[-1]
        if re.search(r'示例|例如|比如|例子|举例|假设|不是|并非|不采用|可能|不确定|也许|或许|待确认',prefix):continue
        if start<=core_start<core_end<=start+len(clause):applicable.append(start)
    if len(applicable)!=1:return None
    return {'field':'time_scope.current','role':'unique_actual_named_season_definition','value':_period(parsed),'priority':1}

def verify_conflict_alternative(alternative,field,sources,question,payload):
    source=sources.get(alternative.source_ref.source_id)
    if source is None or field!='time_scope.current':return None
    fact=_time_fact(alternative.source_ref,source,question,payload)
    if fact is None or fact['field']!=field:return None
    span=_exact_span(alternative.source_ref,source)
    return {**fact,'source_ref':{'source_id':source['source_id'],'source_version':source['source_version'],
        'content_sha256':source['content_sha256'],'quote':alternative.source_ref.quote,'char_start':span[0],'char_end':span[1]}}

def _projection(analysis):
    analysis.conflicts=list(dict.fromkeys(UNKNOWN if r['status']=='unknown'else ACTIVE
        for r in analysis._program_conflict_records if r['status']in{'unknown','active'}))
    analysis._conflicts_projected=True

def _canonical_ref(ref,sources,prior_records):
    keys=('source_id','source_version','content_sha256','quote','char_start','char_end')
    source=sources.get(ref.source_id)
    if source is not None:
        span=_exact_span(ref,source)
        if span is None:return None
        return {'source_id':source['source_id'],'source_version':source['source_version'],
            'content_sha256':source['content_sha256'],'quote':ref.quote,
            'char_start':span[0],'char_end':span[1],'kind':source['kind'],
            'quote_occurrences':len(list(re.finditer(re.escape(ref.quote),source['text'])))}
    # A source-bound point can outlive the turn registry. Only previously
    # program-verified literal references may establish its old identity;
    # this does not reapprove their semantic field or revive the old facts.
    matches=[]
    for record in prior_records:
        for old in(record.get('review_hint')or{}).get('actual_source_quotes',[]):
            if old.get('source_id')!=ref.source_id or old.get('quote')!=ref.quote:continue
            if ref.char_start is None and old.get('quote_occurrences')!=1:continue
            if any(getattr(ref,key)is not None and getattr(ref,key)!=old.get(key)
                    for key in ('source_version','content_sha256','char_start','char_end')):continue
            matches.append(old)
    unique={_key({key:item.get(key)for key in keys}):item for item in matches}
    return deepcopy(next(iter(unique.values())))if len(unique)==1 else None

def _review_hint(proposal,sources,prior_records):
    """Display provenance is literal text proof, never semantic confirmation."""
    quotes=[]
    for alternative in proposal.alternatives:
        actual=_canonical_ref(alternative.source_ref,sources,prior_records)
        if actual is not None:quotes.append(actual)
    return {'status':'not_verified','proposed_field':proposal.field,
        'actual_source_quotes':quotes,'unverified_references':len(proposal.alternatives)-len(quotes)}

def conflict_review_label(record,index):
    """Identify one unverified point without quoting model prose as facts."""
    hint=record.get('review_hint')or{}
    fields={'time_scope.current':'当前期间','time_scope.base':'对比期间','metric':'指标','filters':'筛选',
        'region_scope':'地区归属','numerator':'比例分子','denominator':'比例分母','rank_object':'排名对象',
        'top_n':'排名数量','order':'排序','grouping':'分组'}
    subject=fields.get(hint.get('proposed_field'),'未结构化条件')
    label=f'候选{index+1}（{subject}，尚未核验）'
    names={'current_user':'提案引用的用户原文','user_brief':'用户正文原文','confirmed_history':'历史用户原文'}
    quotes=hint.get('actual_source_quotes')or[]
    for item in quotes:
        text=item['quote']
        label+=f'；{names.get(item["kind"],"实际来源原文")}“{text[:100]}”'+('（节选）'if len(text)>100 else'')
    if not quotes:label+='；not_verified：没有可核验来源引用'
    return label+'；拒绝此候选，保留已明确条件。'

def adjudicate_conflict_proposals(question,analysis,payload,*,prior_records=()):
    """Commit input-only proposals before any model_dump can discard them."""
    if analysis._conflicts_projected:return
    sources=build_conflict_sources(question,payload);records=[]
    for proposal in analysis.conflict_proposals:
        verified=[verify_conflict_alternative(alt,proposal.field,sources,question,payload)for alt in proposal.alternatives]
        if any(value is None for value in verified):
            status='unknown';reason='source_field_or_value_not_verified';dependencies=['*'];field=None
            verified=[value for value in verified if value is not None]
        else:
            field=proposal.field;dependencies=[field,field.split('.')[0]]
            highest=max(item['priority']for item in verified);top=[item for item in verified if item['priority']==highest]
            different=len({_key(item['value'])for item in top})>1
            status='active'if different else'retired'if len({_key(item['value'])for item in verified})==1 else'resolved_by_priority'
            reason='verified_same_priority_conflict'if different else'verified_source_priority'
        # Model labels and alternative ordering are audit details. The same
        # proposed field, source assertions and candidate values identify one
        # point, including unsupported points. New source/quote/value is new.
        candidate_alternatives=[]
        for alternative in proposal.alternatives:
            actual=_canonical_ref(alternative.source_ref,sources,prior_records)
            value=None
            fact=verify_conflict_alternative(alternative,proposal.field,sources,question,payload)
            if fact is not None:value=fact['value']
            elif actual is not None and value is None:
                historical=[]
                for old in prior_records:
                    if old.get('field')!=proposal.field:continue
                    for candidate in old.get('verified_alternatives',[]):
                        if candidate.get('source_ref')=={key:actual[key]for key in('source_id','source_version','content_sha256','quote','char_start','char_end')}:
                            historical.append(candidate['value'])
                if len({_key(item)for item in historical})==1:value=historical[0]
            identity_ref=({key:actual[key]for key in('source_id','source_version','content_sha256','quote','char_start','char_end')}
                if actual is not None else{'unverified_source_assertion':alternative.source_ref.model_dump()})
            candidate_alternatives.append({'source_ref':identity_ref,'value':value})
        # Repeating an identical source/value alternative does not create a
        # new candidate point. Preserve the raw model list in audit below.
        unique_alternatives={_key(item):item for item in candidate_alternatives}
        identity={'proposed_field':proposal.field,
            'alternatives':[unique_alternatives[key]for key in sorted(unique_alternatives)]}
        record=ConflictRecord(record_id='conflict:'+_key(identity)[:28],proposal_ids=[proposal.id],field=field,
            status=status,depends_on=dependencies,verified_alternatives=verified,reason_code=reason,
            not_authoritative=status=='unknown',review_hint=_review_hint(proposal,sources,prior_records)).model_dump()
        existing=next((old for old in records if old['record_id']==record['record_id']),None)
        if existing is None:records.append(record)
        elif proposal.id not in existing['proposal_ids']:existing['proposal_ids'].append(proposal.id)
        analysis._conflict_input_audit.append({'kind':'typed_model_proposal','proposal':proposal.model_dump(),'not_authoritative':True})
    for text in analysis.conflicts:
        record=ConflictRecord(record_id='legacy:'+_key(text)[:28],status='unknown',depends_on=['*'],
            reason_code='legacy_unstructured_proposal',not_authoritative=True,
            review_hint={'status':'not_verified','proposed_field':None,'actual_source_quotes':[],
                'reason':'legacy_no_structured_source'}).model_dump()
        if not any(old['record_id']==record['record_id']for old in records):records.append(record)
        analysis._conflict_input_audit.append({'kind':'legacy_model_prose','text':text,'status':'unverified',
            'not_authoritative':True,'retired_from_authoritative_text':True})
    analysis._program_conflict_records=records
    analysis.conflict_proposals=[]
    _projection(analysis)

def restore_conflict_ledger(state):
    state.analysis._program_conflict_records=deepcopy(state.conflict_ledger)
    _projection(state.analysis)

def commit_conflict_ledger(state):
    if state.analysis._conflicts_projected:
        # A save or unrelated metric edit is not a new conflict evaluation.
        # Zero denotes a freshly adjudicated input awaiting its task version.
        for record in state.analysis._program_conflict_records:
            if record['evaluated_intent_version']==0:record['evaluated_intent_version']=state.intent.intent_version
        state.conflict_ledger=deepcopy(state.analysis._program_conflict_records)
    if state.analysis._conflict_input_audit:
        state.history.append({'event':'conflict_proposal_audit','intent_version':state.intent.intent_version,
            'not_authoritative':True,'proposals':deepcopy(state.analysis._conflict_input_audit)})
        state.analysis._conflict_input_audit=[]

def reconcile_conflicts_after_patch(state,changed_fields,user_message,previous_analysis):
    """A real calendar patch can retire only verified time-dependent points."""
    from qa_agent.clarify.grounding import runtime_payload
    restore_conflict_ledger(state)
    if not any(field=='time_scope'or field.startswith('time_scope.')for field in changed_fields):return
    # Do not trust a model's query_scope source tag. Reparse the real message;
    # already confirmed base-year + real month ranges are independently gated
    # by the existing source-authority service before this commit.
    payload=runtime_payload();actual=_unique_actual_anchor(user_message,payload)
    actual_period=_period(actual);derivation=None
    if not actual_period:
        from qa_agent.clarify.calendar_range import parse_calendar_range
        # Only actual source quotes (or a previously verified conflict source)
        # can supply the omitted base year. A model-populated current cannot.
        anchors=[]
        prior_period=_period(previous_analysis.time_scope)
        # Prefer the latest actual, program-recorded date choice. Its evidence
        # must parse to the saved previous interval and occur in an actual user
        # resolution; neither a model current nor a source-name tag suffices.
        for item in reversed(state.constraint_ledger):
            quote=str(item.get('evidence')or'')
            if item.get('field')!='time_scope'or item.get('source')!='explicit_user':continue
            candidate=_unique_actual_anchor(quote,payload)
            real_user_evidence=quote and (quote in state.original_question or any(
                quote in str(resolution.get('message')or'')for resolution in state.resolutions[:-1]))
            if (candidate and real_user_evidence and _period(candidate)==prior_period and
                    _period(item.get('value'))==prior_period):
                anchors=[candidate]
                derivation={'source':'program:verified_previous_calendar_patch',
                    'intent_version':item['intent_version'],'quote':quote,'period':prior_period}
                break
        original=state.original_question
        original_anchor=_unique_actual_anchor(original,payload)
        if not anchors and original_anchor:
            anchors.append(original_anchor)
            derivation={'source':'program:actual_original_question','quote':original,'period':_period(original_anchor)}
        years={value['current'].get('start','')[:4]for value in anchors if value.get('current',{}).get('start')}
        if len(years)==1:
            from qa_agent.clarify.rules import explicit_period
            _,actual=parse_calendar_range(user_message,explicit_period(next(iter(years))+'年'))
            actual_period=_period(actual)
    if not actual_period or actual_period!=_period(state.analysis.time_scope):return
    # A year-only reply cannot decide a month/day disagreement. The bounded
    # resolver requires explicit sub-year dates, or an explicit whole-year reset.
    explicit_subyear=bool(re.search(r'\d{1,2}\s*月|第?[一二三四1-4]\s*季度|[上下]半年|\d{4}-\d{1,2}-\d{1,2}',user_message))
    whole_year_reset=bool(re.search(r'全年|整年',user_message))
    if not explicit_subyear and not whole_year_reset:return
    for record in state.analysis._program_conflict_records:
        if record['field']=='time_scope.current'and record['status']in{'active','resolved_by_priority','resolved_by_patch'}:
            record.update(status='resolved_by_patch',reason_code='verified_actual_time_patch',
                evaluated_intent_version=state.intent.intent_version,
                resolution={'source':'program:actual_calendar_patch','quote':user_message,
                    'content_sha256':sha256(user_message.encode()).hexdigest(),'value':actual_period,
                    'derived_base':derivation})
    _projection(state.analysis)
