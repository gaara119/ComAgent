"""Explicit display precision from real user input, not model-authored contracts."""
import re
from hashlib import sha256
from qa_agent.clarify.output_requirements import MONEY_WORDS,precision_events


def money_precision_from_payload(payload, *, prior=None):
    def parse(text,authority):
        events=[]
        # A current explicit cancellation has no numeric event, but still
        # outranks a lower-priority brief's old numeric display grant.
        cancelled=re.compile('(?:'+MONEY_WORDS+r')[^。；;\n，,]{0,8}(?:不舍入|不四舍五入|按原值(?:展示)?|不限小数位|不设精度)|(?:取消|去掉|删除|不再限制)[^。；;\n，,]{0,8}(?:'+MONEY_WORDS+r')[^。；;\n，,]{0,8}(?:精度|小数|位数)',re.I)
        for match in cancelled.finditer(text):
            prefix=re.split(r'[。；;\n，,]',text[:match.start()])[-1]
            if re.search(r'不要|不能|别|并非|不是',prefix):continue
            whole_prefix=re.split(r'[。；;\n]',text[:match.start()])[-1]
            if re.search(r'例如|比如|示例|[“”"「」『』]',whole_prefix):continue
            events.append({'digits':None,'status':'removed','authority':authority,'source':'program:actual_user_money_precision',
                'evidence':match.group(),'start':match.start(),'end':match.end(),
                'text_sha256':sha256(text.encode('utf-8')).hexdigest(),
                'context_id':payload.get('context_id'),'context_version':payload.get('context_version',0)})
        for event in precision_events(text):
            if 'money' not in event.subjects:continue
            begin=max(text.rfind(s,0,event.start) for s in ('。','；',';','\n','!','?','！','？','，',','))+1
            ends=[text.find(s,event.end)for s in('。','；',';','\n','!','?','！','？','，',',')]
            end=min((n for n in ends if n>=0),default=len(text))
            segment=text[begin:end]
            negative=event.negative or event.ambiguous
            example=bool(re.search(r'例如|比如|示例|假设|如果将来|文档中|引用|原文|[“”"「」『』]|for\s+example|e\.g\.',segment,re.I))
            if re.search(r'或(?:者)?|还是|任选',text[event.end:end]):negative=True
            if example:continue
            events.append({'digits':None if negative else event.digits,'status':'pending'if negative else'confirmed','authority':authority,
                'source':'program:actual_user_money_precision','evidence':segment,
                'start':begin,'end':end,'text_sha256':sha256(text.encode('utf-8')).hexdigest(),
                'context_id':payload.get('context_id'),'context_version':payload.get('context_version',0)})
        return events
    # The current real user message has precedence over persistent brief text.
    current=parse(str(payload.get('current_user_message')or''),'current_user_message')
    if not current and prior is not None:
        # The producer/state transaction supplies a previously verified task
        # source; an unrelated current turn cannot resurrect an older brief.
        return dict(prior)
    events=current if current else parse(str(payload.get('user_brief')or''),'user_brief')
    if not events:return None
    choices={item['digits'] for item in events}
    if len(choices)!=1 or None in choices:
        removed=all(item['status']=='removed'for item in events)
        return {**events[-1],'authorized':False,'status':'removed'if removed else'pending',
                'reason':'explicit_precision_removed'if removed else'conflicting_or_negative_explicit_precision','sources':events}
    return {'authorized':True,**events[-1]}


def valid_money_precision_metadata(source):
    """Bounded display-only metadata, never a new database selection role."""
    allowed={'digits','status','authority','source','evidence','start','end','text_sha256','context_id','context_version','authorized','reason','sources'}
    if (not isinstance(source,dict)or set(source)-allowed or source.get('source')!='program:actual_user_money_precision'
        or source.get('authority')not in{'current_user_message','user_brief'}or not isinstance(source.get('evidence'),str)
        or not source['evidence']or not re.fullmatch('[0-9a-f]{64}',str(source.get('text_sha256')or''))
        or any(type(source.get(key))is not int for key in('start','end','context_version'))
        or not 0<=source['start']<source['end']or source['context_version']<0
        or source['end']-source['start']!=len(source['evidence'])
        or source.get('context_id')is not None and not isinstance(source['context_id'],str)):
        return False
    if source.get('status')=='removed':
        parsed=money_precision_from_payload({'current_user_message':source['evidence']})
        return source.get('authorized')is False and source.get('digits')is None and parsed is not None and parsed.get('status')=='removed'
    if source.get('status')!='confirmed'or source.get('authorized')is not True or type(source.get('digits'))is not int or not 0<=source['digits']<=9:
        return False
    events=[event for event in precision_events(source['evidence'])if'money'in event.subjects]
    return bool(events)and not any(event.negative or event.ambiguous for event in events)and {event.digits for event in events}=={source['digits']}


def actual_money_precision(intent=None):
    from qa_agent.context import current_context
    context=current_context()
    if context is None:return None
    get=lambda key,default=None:intent.get(key,default)if isinstance(intent,dict)else getattr(intent,key,default)
    prior=(get('query_scope',{})or{}).get('money_precision_source')
    if prior is not None and (not isinstance(prior,dict)or prior.get('source')!='program:actual_user_money_precision'
            or not isinstance(prior.get('authorized'),bool)or not prior.get('evidence')):
        return {'authorized':False,'reason':'invalid_program_money_precision_source'}
    return money_precision_from_payload(context.prompt_payload(),prior=prior)
