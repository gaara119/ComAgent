"""Bounded source restrictions from the actual current user instruction.

Source mentions alone are not restrictions. Quoted instructions, negated-only
phrases and explicitly staged mixed-source requests are distinguished before
single-source fallback or a persisted tool plan can execute.
"""
from dataclasses import dataclass,asdict
import re

CONTEXT_REF=(r'(?:本会话(?:的)?(?:正文|文本|上下文)|(?:这|本|那|该|此)(?:份|段|个)?(?:会话)?(?:的)?(?:正文|文本|内容|上下文)|'
             r'(?:我(?:刚刚|刚)?(?:贴出|贴上|粘贴|提供|提交|上传|贴)(?:的)?|所贴|已提供|已保存|上面(?:贴的)?|上述|以上|上文|以下|下方)(?:完整)?(?:正文|文本|内容|材料|上下文)|正文|'
             r'(?:the\s+)?(?:provided|pasted|current\s+session)\s+(?:text|context)|(?:this|the)\s+(?:pasted\s+)?text)')
DOCUMENT_REF=r'(?:(?:这|本|该)(?:份|个)?(?:指标|口径)?(?:手册|文档|PDF)|所选(?:文档|手册)|指定(?:文档|手册)|(?:指标|口径)?(?:手册|文档|PDF))'
DB_REF=r'(?:数据库|数据表|数据库查询|SQL|Chinook|AdventureWorks|\bdatabase\b)'
ONLY=r'(?:仅仅|仅|只|唯独|solely|exclusively|only)'
USE=r'(?:依据|根据|基于|参考|使用|利用|按|凭|看|用|从|using|use|from|based\s+on)'
ACTION=r'(?:查询|查|计算|统计|求|检索|读取|核算|使用|访问|引用|调用|看|query|read|search|access|calculate)'

@dataclass(frozen=True)
class SourceRestriction:
    mode:str='unrestricted'
    evidence:tuple[str,...]=()
    reason:str='no_explicit_exclusive_source'
    allowed_tools:tuple[str,...]=('context','doc','sql')

    def public(self):return asdict(self)

def _instruction_surface(question):
    # Preserve offsets; only quotations containing an instruction are masked.
    # Ordinary quoted entity/source names are not interpreted as commands.
    pattern=re.compile(r'“[^”]*”|‘[^’]*’|「[^」]*」|"[^"\n]*"|`[^`\n]*`')
    def mask(match):
        text=match.group()
        inner=text[1:-1]
        if re.fullmatch('(?:'+CONTEXT_REF+'|'+DOCUMENT_REF+'|'+DB_REF+')',inner,re.I):
            return ' '+inner+' '
        return ' '*len(text) if re.search(ONLY+r'.{0,16}'+USE+'|(?:不要|禁止|不得).{0,12}'+ACTION,text,re.I) else text
    return pattern.sub(mask,question)

def has_context_reference(question):
    return bool(re.search(CONTEXT_REF,_instruction_surface(question),re.I))

def _is_negated_only(surface,start):
    return bool(re.search(r'(?:不(?:要|必|用|能|应|是)?|并非|无需|没有要求|没让|not|do\s+not|don.t)\s*$',surface[max(0,start-16):start],re.I))

def _source_hits(surface,reference):
    pattern=re.compile(ONLY+r'\s*(?:允许|可以|能|需要|需)?\s*'+USE+r'\s*(?:完整的?|已保存的?)?\s*'+reference,re.I)
    return [m for m in pattern.finditer(surface)if not _is_negated_only(surface,m.start())]

def _positive_database_request(surface):
    # SQL must be the object of an action; a mere reference to DB is no demand.
    clauses=re.split(r'[，,。！？!?；;\n]|(?:但是|但|而是|同时|还要)',surface)
    for clause in clauses:
        negative=r'(?:不要|禁止|不得|无需|不必|不用|不需要|别|不允许|不|do\s+not|don.t|never)'
        if re.search(negative+r'.{0,10}'+ACTION+r'.{0,8}'+DB_REF+'|'+DB_REF+r'.{0,8}'+negative+r'.{0,8}'+ACTION,clause,re.I):continue
        if re.search(ACTION+r'.{0,8}'+DB_REF+'|'+DB_REF+r'.{0,12}(?:统计|计算|查询|读取|核算)',clause,re.I):return True
    return False

def _denied_tools(surface):
    """Negative predicate and its finite source-object list share one clause.

    Never bridge punctuation/new positive predicates to a different source;
    'do not ONLY query X' is not a prohibition on X.
    """
    negative=r'(?:不要|禁止|不得|无需|不必|不用|不需要|别|不允许|不(?=查询|访问|读取|引用|使用|检索|调用|查)|do\s+not|don.t|never)'
    reference='(?:'+CONTEXT_REF+'|'+DOCUMENT_REF+'|'+DB_REF+')'
    modifiers=r'(?:任何|外部|其他|其它|已选|已保存的)?'
    objects=reference+r'(?:\s*(?:和|及|与|以及|或|、)\s*'+reference+r')*'
    before=re.compile(negative+r'\s*(?:再去|再|去)?\s*'+ACTION+r'\s*'+modifiers+r'\s*(?P<sources>'+objects+')',re.I)
    after=re.compile('(?P<sources>'+reference+r')\s*'+negative+r'\s*(?:再去|再|去)?\s*'+ACTION,re.I)
    denied=set()
    for match in list(before.finditer(surface))+list(after.finditer(surface)):
        for item in re.finditer(reference,match['sources'],re.I):
            token=item.group()
            denied.add('doc'if re.fullmatch(DOCUMENT_REF,token,re.I)else'sql'if re.fullmatch(DB_REF,token,re.I)else'context')
    return denied


def source_restriction(question):
    question=str(question or'')
    surface=_instruction_surface(str(question or''))
    denied=_denied_tools(surface)
    def make(mode='unrestricted',evidence=(),reason='no_explicit_exclusive_source',allowed_tools=('context','doc','sql')):
        if mode=='conflict':return SourceRestriction(mode,evidence,reason,())
        tools=set(allowed_tools)-denied
        if not tools:return SourceRestriction('conflict',evidence,'all_allowed_sources_explicitly_denied',())
        if len(tools)==1:mode={'context':'context_only','doc':'documents_only','sql':'database_only'}[next(iter(tools))]
        elif mode=='unrestricted'and denied:mode='allowed_set'
        return SourceRestriction(mode,evidence,reason,tuple(sorted(tools)))
    context=_source_hits(surface,CONTEXT_REF)
    documents=_source_hits(surface,DOCUMENT_REF)
    database=_source_hits(surface,DB_REF)
    # "先仅解释正文定义，再查询数据库" restricts one step, not the
    # complete task. Persist the local wording for normal mixed planning.
    staged=bool(re.search(r'(?:先|第一步).{0,100}'+ONLY+r'.{0,35}(?:'+CONTEXT_REF+'|'+DOCUMENT_REF+r').{0,120}(?:再|然后|第二步|随后).{0,45}'+ACTION+r'.{0,10}'+DB_REF,surface,re.I|re.S))
    evidence=lambda hits:tuple(question[m.start():m.end()]for m in hits)
    all_references='(?:'+CONTEXT_REF+'|'+DOCUMENT_REF+'|'+DB_REF+')'
    set_pattern=re.compile(ONLY+r'\s*(?:允许|可以|能|需要|需)?\s*'+USE+r'\s*(?P<sources>'+all_references+r'(?:\s*(?:和|及|与|以及)\s*'+all_references+r')+)',re.I)
    sets=[m for m in set_pattern.finditer(surface)if not _is_negated_only(surface,m.start())]
    if sets:
        tools=set()
        for item in re.finditer(all_references,sets[0]['sources'],re.I):
            token=item.group()
            tools.add('doc'if re.fullmatch(DOCUMENT_REF,token,re.I)else'sql'if re.fullmatch(DB_REF,token,re.I)else'context')
        return make('allowed_set',evidence(sets),'actual_user_allowed_source_set',tuple(sorted(tools)))
    local_reference=bool(re.search('(?:'+CONTEXT_REF+'|'+DOCUMENT_REF+r').{0,18}(?:定义|口径|公式|名单|筛选条件)',surface,re.I))
    calculation=bool(re.search(r'(?:计算|统计|核算|求).{0,45}(?:\d{4}\s*年|发票|客户|销售额|客单价|金额|订单|数据库)',surface,re.I))
    excludes_database=bool(re.search(r'(?:不要|不得|禁止|无需|别|不).{0,8}'+ACTION+r'.{0,8}'+DB_REF+'|'+DB_REF+r'.{0,8}(?:不要|无需|不必|不).{0,8}'+ACTION,surface,re.I))
    excludes_other_sources=bool(re.search(r'(?:不要|不得|禁止|不允许|不|无需|别).{0,8}(?:调用|使用|访问|引用|查询).{0,8}(?:其他工具|其它工具|外部(?:来源|资料|数据)|任何外部(?:来源|资料|数据))',surface,re.I))
    positive_database=_positive_database_request(surface)
    # A body-contained list/count can be answered from the body itself. A
    # calculation word alone never grants DB access. The narrow manual metric
    # definition -> dated business computation remains a supported mixed flow.
    manual_metric_definition=bool(documents and re.search(DOCUMENT_REF+r'.{0,18}(?:定义|口径|公式)',surface,re.I)
        and re.search(r'\d{4}\s*年|去年|今年|前年|本期|上期|本月|上月',surface))
    local_database=(staged and positive_database or local_reference and positive_database
                    or manual_metric_definition and calculation)
    if local_database and not excludes_database and not excludes_other_sources and(context or documents):
        tools={'sql'}|({'context'}if context else set())|({'doc'}if documents else set())
        return make('local_mixed',evidence(context+documents),'actual_definition_or_filter_scope_then_database',tuple(sorted(tools)))
    if context:
        if documents or database or _positive_database_request(surface):
            return make('conflict',evidence(context+documents),'exclusive_source_and_other_source_action_conflict')
        return make('context_only',evidence(context),'actual_user_exclusive_context_source',('context',))
    if documents:
        if database or _positive_database_request(surface):return make('conflict',evidence(documents),'exclusive_document_and_database_action_conflict')
        return make('documents_only',evidence(documents),'actual_user_exclusive_selected_document',('doc',))
    if database:return make('database_only',evidence(database),'actual_user_exclusive_database_source',('sql',))
    # A source-specific exclusion can express the same intent without "only".
    if has_context_reference(surface) and re.search(r'(?:不要|不得|禁止|无需|别|不).{0,8}'+ACTION+r'.{0,8}'+DB_REF,surface,re.I):
        if _positive_database_request(surface):return make('conflict',(),'excluded_database_also_requested')
        return make('context_only',(),'actual_context_reference_excludes_database',('context',))
    return make()

def restriction_conflict(restriction,route,has_context,doc_ids):
    """Return a safe explanation before tools; never silently switch explicit UI scope."""
    if restriction.mode=='conflict':return '本轮同时出现互相冲突的来源要求，请明确仅依据正文/所选文档，还是还需查询数据库；本轮未查询数据库。'
    if restriction.mode=='context_only':
        if route!='auto':return '本轮要求仅依据本会话正文，但当前选择了其他来源范围。请切换到自动综合问答后重试；本轮未查询数据库或文档。'
        if not has_context:return '本会话尚未提供可核验正文。请先保存正文；本轮未用数据库或文档替代。'
    if restriction.mode=='documents_only':
        if route not in{'auto','doc'}:return '本轮要求仅依据所选文档，但当前选择了数据库或跨源范围；请先选择指定文档问答，本轮未执行数据库查询。'
        if len(doc_ids)!=1:return '本轮要求仅依据所选文档，请明确选择一份已登记文档；本轮未用数据库替代。'
    if restriction.mode=='database_only' and route not in{'auto','sql'}:
        return '本轮要求仅依据数据库，但当前选择了文档或跨源范围；请切换数据库问数，本轮未访问文档或数据库。'
    if restriction.mode in{'allowed_set','local_mixed'}:
        required={'sql':{'sql'},'doc':{'doc'},'hybrid':{'sql','doc'},'auto':set()}.get(route,{'unsupported'})
        if not required<=set(restriction.allowed_tools):
            return '当前入口需要的工具不在本轮允许来源内；请切换兼容的来源范围，本轮未执行工具。'
    return None


def restored_restriction(payload):
    """Only consume our server-persisted, finite source contract."""
    if not payload:return SourceRestriction()
    if not isinstance(payload,dict):raise ValueError('保存的来源权限格式无效。')
    tools=payload.get('allowed_tools')
    if not isinstance(tools,(list,tuple))or not tools or not set(tools)<={'context','doc','sql'}:
        raise ValueError('保存的工具权限无效。')
    return SourceRestriction(mode=str(payload.get('mode','allowed_set')),
        evidence=tuple(payload.get('evidence')or()),reason=str(payload.get('reason','server_saved_source_scope')),
        allowed_tools=tuple(tools))
