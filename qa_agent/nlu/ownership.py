"""Physical country ownership proved by an actual value mention and noun."""
from __future__ import annotations
import re

COUNTRY_COLUMNS={'customer.country','invoice.billing_country'}
COUNTRY_ROLE_PATTERNS={
    'customer.country':r'(?:customer\.country|customers?\s+(?:residence\s+)?country|客户(?:所在地(?:国家)?|所在国|居住国|国家))',
    'invoice.billing_country':r'(?:invoice\.billing_country|billing_country|invoices?\s+billing\s+country|billing\s+country|账单(?:国家|所在国|国)|开票国家)',
}
COUNTRY_OPERATOR=r'(?:改(?:成|为)|换(?:成|为)|不等于|不是|等于|为|是|!=|<>|=|:|：|is\s+not|is|equals?)'

def explicit_country_dimensions(question):
    """Only explicit physical role predicates, not any nearby table noun."""
    return {column for column,role in COUNTRY_ROLE_PATTERNS.items()
        if re.search(role+r'\s*'+COUNTRY_OPERATOR+r'\s*[\"\'“‘]?(?:[A-Za-z\u4e00-\u9fff])',question,re.I)}

def country_value_operator(question,start,end):
    prefix=question[max(0,start-24):start].rstrip().rstrip('\"\'“‘').rstrip()
    suffix=question[end:end+6]
    return '!=' if re.search(r'(?:不是|不在|不等于|除|非|not\s*|!=|<>)\s*$',prefix,re.I) or suffix.startswith('以外') else '='

def country_boolean_supported(question,bindings):
    """Independent physical owner predicates support conjunction, not cross-owner OR."""
    if len({item.get('column') for item in bindings if item.get('column')in COUNTRY_COLUMNS})<2:return
    equal_columns=[item.get('column')for item in bindings if item.get('column')in COUNTRY_COLUMNS and item.get('operator')=='=']
    repeated_owner=len(equal_columns)!=len(set(equal_columns))
    whole_not=r'(?:不是|并不是|并非|不满足|不符合|排除)\s*[(（]?\s*(?:'+ '|'.join(COUNTRY_ROLE_PATTERNS.values())+')'
    if repeated_owner or re.search(whole_not,question,re.I) or re.search(r'或者|或是|还是|或\s|\s或|或(?=账单|客户|invoice|customer)|\bor\b|任一|其中之一|并非同时|不是同时|不同时|不能同时|并不同时|(?:排除|不包括|不满足|不符合|并非|not)\s*[(（]|\bnot\s+(?:customer\.country|invoice\.billing_country)',question,re.I):
        raise ValueError('两个独立国家字段之间的OR或整体否定暂不支持安全合并；请明确各字段条件或拆分查询，未执行SQL。')

def country_value_delta(question,bindings,previous):
    """A literal edit to one existing country predicate, not a new analysis."""
    if previous is None or len(bindings)!=1:return False
    binding=bindings[0];column=binding.get('column');proof=binding.get('field_owner_proof')or{}
    if column not in COUNTRY_COLUMNS or column not in{item.get('column')for item in previous.bindings}:return False
    if not re.search(r'改成|改为|换成|换为',question):return False
    quote=proof.get('evidence','')
    if not quote or question.count(quote)!=1 or proof.get('column')!=column:return False
    remainder=question.replace(quote,'<condition>')
    return bool(re.fullmatch(r'\s*(?:那|请|只把|仅将|仅把|只|仅|把|将)?\s*<condition>\s*(?:[，,]\s*(?:其余|其他|其它)(?:条件)?不变)?\s*[。？?!！]?\s*',remainder))

def country_predicate_edit(question,bindings,previous):
    """Bounded explicit set/add/remove of one actual global country predicate.

    The other owner and period are immutable here. No model fields or history
    prose supply a new value, and unsupported operand-local edits defer.
    """
    if previous is None:return None
    if any(item.get('column')in COUNTRY_COLUMNS and any(item.get(role)not in(None,'global')
           for role in ('binding_scope','applies_to'))for item in list(previous.bindings)+list(bindings)):
        return None
    for operand in ('numerator','denominator'):
        shape=previous.analysis.query_scope.get(operand)
        if shape is not None and not isinstance(shape,dict):return None
        filters=(shape or{}).get('filters',[])
        if not isinstance(filters,list)or any(not isinstance(item,dict)for item in filters):return None
        if any((item.get('column')or item.get('field'))in COUNTRY_COLUMNS
               for item in filters):
            return None
    old=list(previous.bindings)
    role='(?:'+'|'.join(COUNTRY_ROLE_PATTERNS.values())+')'
    role_column=lambda text:next((column for column,pattern in COUNTRY_ROLE_PATTERNS.items()
        if re.fullmatch(pattern,text,re.I)),None)
    def unchanged(tail,edited):
        tail=tail.strip().strip('。.!！?？').strip().lstrip('，,').strip()
        if not tail:return True
        if re.fullmatch(r'(?:其余|其他|其它)(?:条件)?(?:保持)?不变',tail):return True
        names=re.fullmatch(r'(?P<names>(?:'+role+r'|年份|期间|指标)(?:\s*(?:、|和|与|及|以及)\s*(?:'+role+r'|年份|期间|指标))*)\s*(?:保持)?不变',tail,re.I)
        if names is None:return False
        return not any(role_column(match.group())==edited for match in re.finditer(role,names['names'],re.I))
    removal=re.match(r'\s*(?:请|那就|只)?\s*(?:去掉|删除|取消|移除)\s*(?P<role>'+role+r')\s*(?:限制|筛选|条件)?(?P<tail>.*)$',question,re.I)
    if removal:
        column=role_column(removal['role']);removed=[item for item in old if item.get('column')==column]
        if not removed:return None
        tail=removal['tail'].strip().lstrip('，,').strip()
        retained=re.match(r'只保留\s*(?P<role>'+role+r')\s*(?:为|是|=)?\s*(?P<value>[^，,。]+)(?P<tail>.*)$',tail,re.I)
        if retained:
            keep=role_column(retained['role'])
            if keep==column:return None
            matches=[item for item in bindings if item.get('column')==keep and item.get('operator')=='='
                and any(prior.get('column')==keep and prior.get('operator')=='='and prior.get('value')==item.get('value')for prior in old)]
            if len(matches)!=1 or not unchanged(retained['tail'],column):return None
        elif not unchanged(tail,column):return None
        return {'op':'remove','column':column,'filters':[item for item in old if item.get('column')!=column],
            'retired':removed,'evidence':question}
    if len(bindings)!=1:return None
    binding=bindings[0];column=binding.get('column');proof=binding.get('field_owner_proof')or{}
    quote=proof.get('evidence','')
    if column not in COUNTRY_COLUMNS or proof.get('column')!=column or not quote or question.count(quote)!=1:return None
    start=question.index(quote);prefix=question[:start].strip();tail=question[start+len(quote):]
    if re.fullmatch(r'(?:请|那就|那)?\s*(?:只|仅)?\s*(?:把|将)?',prefix)and re.search(r'改成|改为|换成|换为',quote):op='set'
    elif re.fullmatch(r'(?:请|那就|只)?\s*(?:增加|加上|添加)',prefix):
        op='add';tail=re.sub(r'^\s*的?(?:限制|筛选|条件)','',tail)
    else:return None
    if not unchanged(tail,column):return None
    prior=[item for item in old if item.get('column')==column]
    if op=='set'and not prior:return None
    if op=='add'and prior:
        raise ValueError('该国家字段已有独立筛选；增加不同条件的AND/OR含义尚未明确，未执行SQL。')
    return {'op':op,'column':column,'filters':[item for item in old if item.get('column')!=column]+[binding],
        'retired':prior,'evidence':question}

def country_edit_has_non_global_scope(question,bindings,previous):
    """Unqualified text cannot turn a local/unknown geographic carrier global."""
    if previous is None or re.search(r'分子|分母',question):return False
    role='(?:'+'|'.join(COUNTRY_ROLE_PATTERNS.values())+')'
    if not re.search(role,question,re.I)or not re.search(r'改成|改为|换成|换为|增加|添加|加上|去掉|删除|取消|移除',question):return False
    if any(item.get('column')in COUNTRY_COLUMNS and any(item.get(key)not in(None,'global')
           for key in ('binding_scope','applies_to'))for item in list(previous.bindings)+list(bindings)):
        return True
    for name in ('numerator','denominator'):
        operand=previous.analysis.query_scope.get(name)
        if operand is None:continue
        if not isinstance(operand,dict):return True
        filters=operand.get('filters',[])
        if not isinstance(filters,list)or any(not isinstance(item,dict)for item in filters):return True
        if any((item.get('column')or item.get('field'))in COUNTRY_COLUMNS for item in filters):return True
    return False


def literal_country_owner(question,start,end,column):
    if column not in COUNTRY_COLUMNS:
        return None
    if not 0<=start<end<=len(question):
        return None
    # A named physical field predicate owns its value even if the next noun
    # is the projected invoice/customer (e.g. customer.country=USA 的发票).
    explicit=[]
    for target,role in COUNTRY_ROLE_PATTERNS.items():
        match=re.search(role+r'\s*'+COUNTRY_OPERATOR+r'\s*[\"\'“‘]?\s*$',question[:start],re.I)
        if match:explicit.append((target,match))
    if explicit:
        if len(explicit)!=1 or explicit[0][0]!=column:return None
        match=explicit[0][1]
        return {'source':'program:literal_country_owner','column':column,'value_span':[start,end],
            'owner_span':[match.start(),match.end()],'evidence':question[match.start():end]}
    owner=re.match(r'\s*(?:的\s*)?(customers?(?![A-Za-z])|客户|顾客|invoices?(?![A-Za-z])|发票|账单)',question[end:],re.I)
    if not owner:
        role=COUNTRY_ROLE_PATTERNS[column]
        prefix=question[:start]
        explicit=re.search(role+r'\s*'+COUNTRY_OPERATOR+r'\s*[\"\'“‘]?\s*$',prefix,re.I)
        if explicit is None:return None
        return {'source':'program:literal_country_owner','column':column,'value_span':[start,end],
            'owner_span':[explicit.start(),explicit.end()], 'evidence':question[explicit.start():end]}
    noun=owner.group(1).casefold()
    target='customer.country' if noun in {'客户','顾客','customer','customers'} else 'invoice.billing_country'
    if target!=column:
        return None
    finish=end+owner.end()
    return {'source':'program:literal_country_owner','column':target,'value_span':[start,end],
            'owner_span':[end+owner.start(1),finish],'evidence':question[start:finish]}


def verified_unique_owner(question,bindings):
    proofs=[]
    for binding in bindings:
        proof=binding.get('field_owner_proof')
        if not isinstance(proof,dict) or binding.get('source') not in {'verified_value_index','explicit_user_literal'}:
            continue
        span=proof.get('value_span')
        if not isinstance(span,list) or len(span)!=2 or not all(isinstance(n,int) and not isinstance(n,bool) for n in span):
            continue
        real=literal_country_owner(question,span[0],span[1],binding.get('column'))
        if real is not None and real==proof:
            proofs.append(real)
    if not proofs or len({item['column'] for item in proofs})!=1:
        return None
    column=proofs[0]['column']
    # A second explicit country dimension cannot be collapsed into one
    # session-wide region_scope by the first true mention proof.
    if column=='customer.country' and re.search(r'账单(?:国家|地区)|开票国家|invoice\.billing_country|billing_country|(?:客户|customers?).{0,8}(?:在|来自|和|以及|，|,).{1,20}(?:发票|账单|invoices?)',question,re.I):
        return None
    if column=='invoice.billing_country' and re.search(r'客户(?:所在地|所在国|居住国)|customer\.country|(?:发票|账单|invoices?).{0,8}(?:在|来自|和|以及|，|,).{1,20}(?:客户|customers?)',question,re.I):
        return None
    if re.search(r'城市|州省|省份|\bcity\b|\bstate\b',question,re.I):
        return None
    return proofs[0]


def ground_explicit_owner(question,analysis,bindings):
    dimensions={item.get('column')for item in bindings if item.get('column')in COUNTRY_COLUMNS}
    if len(dimensions)>1:
        country_boolean_supported(question,bindings)
        # A single display/default owner must never rebind two actual roles.
        analysis.region_scope=None;analysis.region_ambiguous=False
        analysis.condition_sources.pop('region_scope',None)
        return analysis
    proof=verified_unique_owner(question,bindings)
    if proof is None:
        return analysis
    analysis.region_scope=proof['column'];analysis.region_ambiguous=False
    analysis.condition_sources['region_scope']={'source':'explicit_user','evidence':proof['evidence'],
        'lifetime':'task','applies_to':'global','verified':True,'proof':'literal_country_owner'}
    analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field')!='region_scope']
    def solely_region_uncertainty(text):
        return (bool(re.search(r'未明确|不明确|不确定|还是',text)) and
                bool(re.search(r'客户所在地|customer\.country',text,re.I)) and
                bool(re.search(r'账单国家|invoice\.billing_country',text,re.I)) and
                not re.search(r'\d{4}|日期|期间|销售额|金额|数量|币种|指标|时间|互斥|相反|不一致',text))
    analysis.conflicts=[text for text in analysis.conflicts if not solely_region_uncertainty(text)]
    return analysis


def remove_inapplicable_average_region_question(question,analysis):
    """A country field role cannot affect an unfiltered overall mean.

    This narrow proof recognizes only a deictic overall-average request with
    no literal or typed geographic predicate. Unknown country requests, named
    sets, geographic grouping and missing-scope flags keep their uncertainty.
    """
    if analysis.scope_missing or not re.search(r'咱们这边|我们这边|咱这边|咱们这里|我们这里',question):
        return analysis
    residue=re.sub(r'(?<!\d)\d{4}\s*年|咱们这边|我们这边|咱这边|咱们这里|我们这里|[\s，,。.?？：:]','',question)
    if not re.fullmatch(r'的?(?:人均消费|平均消费)(?:金额)?(?:是|有)?多少',residue):
        return analysis
    geo=r'country|billing_country|region|city|state|国家|市场|地区|区域|城市|省份|所在地'
    # Inspect every typed operand/scope, not only the global filter list.
    import json
    operands={'filters':analysis.filters,'grouping':analysis.grouping,
        'numerator':analysis.numerator,'denominator':analysis.denominator,
        'query_scope':analysis.query_scope}
    if re.search(geo,json.dumps(operands,ensure_ascii=False),re.I):
        return analysis
    def vacuous(item):
        field=item.get('source_field') or item.get('field')
        return (field in {'filters.region','region_scope'} and
            str(item.get('evidence') or '') in {'咱们这边','我们这边','咱这边','咱们这里','我们这里'} and
            re.search(r'客户所在地|customer\.country',str(item.get('question') or ''),re.I) and
            re.search(r'账单国家|invoice\.billing_country',str(item.get('question') or ''),re.I))
    analysis.clarification_requests=[item for item in analysis.clarification_requests if not vacuous(item)]
    return analysis
