"""Bounded pending-field deltas, not a blanket '那 means patch' heuristic."""
from __future__ import annotations
import re

COUNTRY_FIELDS={'invoice.billing_country','customer.country','employee.country'}


def unfilled_country_delta(message,state):
    if state is None or state.phase not in {'ANSWERED','FAILED'}:
        return False
    countries=[item for item in state.bindings if item.get('column') in COUNTRY_FIELDS and not item.get('binding_scope')]
    if len(countries)!=1:
        return False
    return bool(re.search(r'(?:换成|改成|换为|改为).{0,6}(?:另一个|另外一个|其他|其它|别的|另个).{0,5}(?:国家|国|地区)',message))


def apply_unfilled_country_delta(state,message):
    from qa_agent.clarify.state import IntentPatch,apply_patches
    countries=[item for item in state.bindings if item.get('column') in COUNTRY_FIELDS and not item.get('binding_scope')]
    target=countries[0]['column']
    scope={**state.analysis.query_scope,'pending_filters':[{'column':target,'operator':'='}]}
    label={'invoice.billing_country':'账单国家','customer.country':'客户所在地国家','employee.country':'员工所在地国家'}[target]
    pending={'field':'filters','column':target,'question':f'请明确新的{label}。','reason':'用户明确要替换国家，但尚未给出新国家；其它已确认条件继续保留。','evidence':message}
    requests=[item for item in state.analysis.clarification_requests if item.get('field') not in {'filters','country','billing_country'}]+[pending]
    apply_patches(state,[IntentPatch(op='set',path='filters',value=[item for item in state.bindings if item not in countries],evidence=message),
                         IntentPatch(op='set',path='query_scope',value=scope,evidence=message),
                         IntentPatch(op='set',path='clarification_requests',value=requests,evidence=message)],user_message=message)
    state.history.append({'event':'pending_field_delta','field':target,'retained_period':state.analysis.time_scope,
                          'retained_metric':state.analysis.metric,'intent_version':state.intent.intent_version})
def ranking_limit_delta(message: str, state) -> int | None:
    """Recognize only complete, literal TopN-only edits of one active rank."""
    import re
    if state.phase!='ANSWERED' or state.analysis.task_type!='ranking':return None
    numbers={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    number=r'[\d一二三四五六七八九十]+'
    object_terms={'客户':'customer','顾客':'customer','曲目':'track','歌曲':'track','艺术家':'artist','专辑':'album','员工':'employee'}
    clauses=[part.strip() for part in re.split(r'[，,。；;？！?!]',message) if part.strip()]
    found=[]
    for clause in clauses:
        pattern=(r'(?:那)?(?:就)?(?:只要|只看|只取|改成|改为)前(?P<a>'+number+r')(?:名|位|个|首)?(?:呢|就行|即可)?|'
                 r'(?:把)?(?P<measure>买得最多的|销售额最高的|购买数量最高的|热门)?前(?P<b>'+number+r')(?:名|位|个|首)?'
                 r'(?P<object>客户|顾客|曲目|歌曲|艺术家|专辑|员工)?(?:列给我|列出来|给我|列出|呢)?')
        match=re.fullmatch(pattern,clause)
        if not match:return None
        word=match.group('a') or match.group('b');value=int(word) if word.isdigit() else numbers.get(word)
        if value is None or not 1<=value<=5000:return None
        if match.group('object') and object_terms[match.group('object')]!=state.analysis.rank_object:return None
        measure=match.group('measure')
        if measure=='购买数量最高的' and state.analysis.metric!='purchased_quantity':return None
        if measure=='销售额最高的' and state.analysis.metric not in {'invoice_revenue','detail_revenue'}:return None
        if measure=='买得最多的' and not (state.analysis.rank_object=='customer' and state.analysis.metric=='invoice_revenue'):return None
        found.append(value)
    return found[0] if found and len(set(found))==1 else None


def apply_ranking_limit_delta(state,message,value):
    import re
    from qa_agent.clarify.state import IntentPatch,apply_patches
    # Only an explicit old rank size is replaced. Time explanations such as
    # "前5年" and opaque output identifiers are independent obligations.
    old=state.analysis.top_n
    numbers={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
    rank_size=re.compile(r'前\s*(?P<n>[\d一二三四五六七八九十]+)(?=\s*(?:名|位|个(?:客户|顾客|艺术家|专辑|员工)|首(?:曲目|歌曲)|张专辑))')
    def replace(match):
        text=match.group('n');number=int(text) if text.isdigit() else numbers.get(text)
        return '前'+str(value) if number==old else match.group(0)
    requirements=[rank_size.sub(replace,item) for item in state.analysis.output_requirements]
    if not any(item in requirements for item in ('ranked_subset_rows','ranked_subset_total')):
        requirements.append('ranked_subset_rows')
    apply_patches(state,[IntentPatch(op='set',path='top_n',value=value,evidence=message),
        IntentPatch(op='set',path='output_requirements',value=requirements,evidence=message)],user_message=message)
    state.history.append({'event':'structured_rank_limit_delta','top_n':value,'evidence':message,
                          'preserved_fields':['metric','time_scope','filters','region_scope','query_scope']})

