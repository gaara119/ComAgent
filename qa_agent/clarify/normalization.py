"""Normalize internal slots and derived mirrors around one semantic authority."""
from __future__ import annotations
import re
from copy import deepcopy

_NAME_IDENTITY_FIELDS={'artist.name','album.title','genre.name','playlist.name','track.name','media_type.name'}


def validate_scope_structure(value):
    """Validate known collection roles before any consumer sees a proposal."""
    if not isinstance(value,dict):return value
    result=deepcopy(value)
    def collection(container,key,path,*,strings=False,pending=False):
        if key not in container:return
        items=container[key]
        if items is None:container[key]=[];return
        if not isinstance(items,list):raise ValueError(f'{path} 必须是数组，不能用字符串或对象代替；不得丢弃筛选条件。')
        for index,item in enumerate(items):
            if strings:
                if not isinstance(item,str) or not item.strip():raise ValueError(f'{path}[{index}] 必须是真实字段名字符串。')
            else:
                if not isinstance(item,dict):raise ValueError(f'{path}[{index}] 必须是筛选对象，不能丢弃错误元素。')
                column=item.get('column') or item.get('field')
                if not isinstance(column,str) or not column.strip():raise ValueError(f'{path}[{index}] 缺少合法column或field。')
                if not pending:
                    if not isinstance(item.get('operator'),str) or not item['operator'].strip():raise ValueError(f'{path}[{index}] 缺少筛选operator。')
                    if item['operator'].upper() not in {'IS NULL','IS NOT NULL'} and 'value' not in item and 'values' not in item:
                        raise ValueError(f'{path}[{index}] 缺少筛选value或values；不能默认为无筛选。')
    collection(result,'partition_by','query_scope.partition_by',strings=True)
    collection(result,'qualification_filters','query_scope.qualification_filters')
    collection(result,'pending_filters','query_scope.pending_filters',pending=True)
    for name in ('numerator','denominator'):
        if name not in result or result[name] is None:continue
        if not isinstance(result[name],dict):raise ValueError(f'query_scope.{name} 必须是对象或null，不能隐式丢弃操作数范围。')
        collection(result[name],'filters',f'query_scope.{name}.filters')
    return result


def normalize_scope_collections(analysis):
    """JSON null is the empty value only for known collection contracts."""
    scope=dict(analysis.query_scope or {})
    for key in ('partition_by','qualification_filters','pending_filters'):
        if key in scope and scope[key] is None:scope[key]=[]
    for key in ('numerator','denominator'):
        if key in scope and scope[key] is None:scope.pop(key)
        elif isinstance(scope.get(key),dict) and 'filters' in scope[key] and scope[key]['filters'] is None:
            scope[key]={**scope[key],'filters':[]}
    analysis.query_scope=scope
    return analysis


def normalize_source_keys(analysis):
    """Known nested evidence paths are mirrors of one top-level field."""
    sources=dict(analysis.condition_sources)
    for key,value in list(sources.items()):
        root=key.split('.',1)[0]
        if key!=root and root in type(analysis).model_fields and root not in sources:
            sources[root]={**value,'source_path':key}
    analysis.condition_sources={key:value for key,value in sources.items() if key in type(analysis).model_fields}
    return analysis


def canonical_slot(field: str, question: str='', source: str | None=None) -> str:
    value=str(field or '').strip()
    lower=value.casefold()
    precision_sources={'program:percent_precision':'output_precision.percent',
                       'program:money_precision':'output_precision.money'}
    precise=precision_sources.get(source)
    if precise and lower in {'output_precision',precise}:
        return precise
    if lower in {'metric','time_scope.current','time_scope.base','comparison.type','numerator','denominator','rank_object','filters','region_scope','scope_missing','top_n','order','grouping','query_scope.rank_metric'}:
        return lower
    if lower in {'average_grain','averaging_grain','mean_grain'} or re.search('平均.*粒度|平均.*对象|按人.*按张',value):
        return 'average_grain'
    if lower in {'numerator_ranking_metric','ranking_metric','rank_metric'} or re.search('分子.*排名.*指标',value):
        return 'query_scope.rank_metric'
    if lower in {'time_scope','time_range','period','year','season','season_months','season_month_range','peak_season','peak_season_months','peak_season_month_range','month_range'} or re.search('旺季|月份|期间|年月|时间范围|统计时间',value):
        return 'time_scope.current'
    if lower in {'seasonwindow','season_window','peak_season_window'} or re.fullmatch(r'time_scope\.(?:current\.)?(?:season|seasonwindow|season_window|season_months|season_month_range|month_range|peak_season|peak_season_window)',lower):
        return 'time_scope.current'
    if lower in {'country','billing_country','customer.country','invoice.billing_country','region_value'} or re.search('国家|地区筛选',value):
        return 'filters'
    # Never silently discard an unknown model uncertainty. Keep one bounded
    # backend slot; source field remains available for diagnosis.
    return 'unresolved_semantic_condition'


def _resolved_name_identity(item, filters, question):
    """Match an existing program-index binding, never a nonempty model guess.

    This narrow retirement only concerns an unresolved single entity identity.
    Extra predicates/local scopes remain pending; conditional aliases do not
    become confirmed merely because their spelling resembles a known value.
    """
    field=item.get('column') or item.get('field')
    if field not in _NAME_IDENTITY_FIELDS:
        return False
    if item.get('column') and item.get('field') and item['column']!=item['field']:
        return False
    if set(item)-{'column','field','reason','question','candidate_id','evidence_ref','binding_scope','applies_to'}:
        return False
    if any(item.get(key) not in (None,'global') for key in ('binding_scope','applies_to')):
        return False
    actual=[x for x in filters if x.get('column')==field]
    if not actual:
        return False
    from qa_agent.nlu.value_index import record_id
    identities=set()
    for binding in actual:
        value=binding.get('value')
        if (binding.get('source')!='verified_value_index' or binding.get('operator')!='='
                or not isinstance(value,str) or not value.strip()
                or binding.get('method') not in {'exact','actual_user_canonical'}
                or binding.get('binding_policy')=='candidate_only'
                or any(binding.get(key) not in (None,'global') for key in ('binding_scope','applies_to'))):
            return False
        # A previously verified artist is not the answer to a new "another
        # artist" card. Retirement needs this turn's actual canonical identity,
        # as supplied by apply_patches(user_message), not merely old state.
        if not re.search(r'(?<![A-Za-z0-9_])'+re.escape(value)+r'(?![A-Za-z0-9_])',question,re.I):
            return False
        candidate=record_id(field,value)
        if binding.get('evidence_ref')!=candidate or binding.get('candidate_id',candidate)!=candidate:
            return False
        if any(item.get(key) is not None and item[key]!=candidate for key in ('candidate_id','evidence_ref')):
            return False
        identities.add((value,candidate))
    return len(identities)==1


def normalize_internal_contract(analysis, question: str=''):
    normalize_scope_collections(analysis)
    scope=dict(analysis.query_scope or {})
    if analysis.metric in {'average_customer_amount','average_invoice_amount'}:
        scope['average_grain']='customer' if analysis.metric=='average_customer_amount' else 'invoice'
        scope['average_grain_missing']=False
    pending=list(scope.get('pending_filters') or [])
    retired_identities={item.get('column') or item.get('field') for item in pending
                        if _resolved_name_identity(item,analysis.filters,question)}
    scope['pending_filters']=[item for item in pending if not any(
        item.get('column') and item.get('column') not in _NAME_IDENTITY_FIELDS
        and actual.get('column')==item.get('column') and actual.get('operator') in {'=','IN'}
        for actual in analysis.filters) and not _resolved_name_identity(item,analysis.filters,question)]
    if not scope['pending_filters']:
        scope.pop('pending_filters',None)

    if scope.get('ranking_scope')=='per_group' and analysis.region_scope:
        country=analysis.region_scope
        country_fields={'invoice.billing_country','customer.country'}
        scope['region_scope']=country
        analysis.grouping=[country if field in country_fields else field for field in analysis.grouping]
        if country in scope.get('partition_by',[]) and country not in analysis.grouping:
            analysis.grouping.append(country)
        scope['qualification_filters']=[{**item,'column':country} if item.get('column') in country_fields else item
                                         for item in scope.get('qualification_filters',[]) if isinstance(item,dict)]
        analysis.filters=[{**item,'column':country} if item.get('column') in country_fields else item for item in analysis.filters]
        source=analysis.condition_sources.get('region_scope')
        if source and any(field in str(source) for field in country_fields-{country}):
            analysis.condition_sources.pop('region_scope',None)

    requests=[]
    seen=set()
    for item in analysis.clarification_requests:
        original=str(item.get('source_field') or item.get('field') or '')
        # Only the corresponding physical-field identity question is closed.
        # Other generic conditions/metrics/pending entities retain their cards.
        identity={'field':original,**{key:item[key] for key in
            ('candidate_id','evidence_ref','binding_scope','applies_to') if key in item}}
        if original in retired_identities and _resolved_name_identity(identity,analysis.filters,question):
            continue
        field=canonical_slot(original,str(item.get('question') or ''),item.get('source'))
        normalized={**item,'field':field}
        if original!=field:
            normalized['source_field']=original
        # A model's grain label does not prove a season was confirmed. The
        # trusted literal-date patch clears its own resolved request; fresh
        # proposals must retain uncertainty until real source grounding.
        if field=='average_grain' and scope.get('average_grain'):
            continue
        if field=='query_scope.rank_metric' and scope.get('rank_metric'):
            continue
        if field=='filters' and not scope.get('pending_filters') and analysis.filters:
            continue
        if field not in seen:
            requests.append(normalized);seen.add(field)
    analysis.query_scope=scope
    analysis.clarification_requests=requests
    return analysis


def normalize_ranked_output(question: str, analysis):
    if analysis.task_type!='ranking':
        return
    # Separate explicit row delivery from a scalar TopN total. Do not let an
    # intervening year or metric hide "列出...前N名...及各自金额".
    clauses=[part for part in re.split(r'[，,。；;？！?!\n]',question) if part.strip()]
    def positive(pattern):
        for clause in clauses:
            for match in re.finditer(pattern,clause):
                before=clause[:match.start()]
                # One explicit negative applies to its remaining clause,
                # including a later "各自金额"; an arbitrary 10-char window
                # could accidentally re-authorize what the user forbade.
                switch=r'(?:(?:但(?:是)?|而是)(?:要|请|需要|给|列出|展示|返回)|改为|改成)'
                negative=r'(?:不要|不需要|不用|不必|无需|不含|不包括|(?<![另分])别)(?:(?!'+switch+r').)*$'
                if not re.search(negative,before):
                    return True
        return False
    total=positive(r'合计|总计|一共.{0,6}(?:多少钱|金额)|金额.{0,6}合计')
    rows=positive(r'名单|分别|各自|每(?:个|组|位)|各个|列(?:出)?[^。；;\n]{0,80}?前\s*[\d一二三四五六七八九十]+\s*(?:名|位|个(?:客户|顾客|专辑|艺术家|员工)|首(?:曲目|歌曲)|张专辑)')
    requirements=[item for item in analysis.output_requirements if item not in {'ranked_subset_total','ranked_subset_rows'}]
    if total:
        requirements.append('ranked_subset_total')
        if rows:
            requirements.append('ranked_subset_rows')
        analysis.query_scope['output_shape']='ranked_rows_and_total' if rows else 'scalar_total'
    else:
        requirements.append('ranked_subset_rows')
        analysis.query_scope['output_shape']='ranked_rows'
        for key in ('outer_operator','outer_aggregation','outer_aggregate'):
            analysis.query_scope.pop(key,None)
    analysis.output_requirements=list(dict.fromkeys(requirements))
