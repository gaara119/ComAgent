"""Keep literal calendar authority out of categorical entity binding."""
from __future__ import annotations
from datetime import date, timedelta
import re


def normalize_operand_calendar_roles(question, analysis, catalog=None):
    """Resolve a model year-label BETWEEN to the actual half-open period.

    This is deliberately restricted to a year written by the user, without
    literal month/day endpoints. A different proposed interval is retained for
    existing guards to reject; it is never silently broadened.
    """
    from qa_agent.clarify.rules import explicit_period
    if re.search(r'\d{1,2}\s*月|\d{4}-\d{1,2}-\d{1,2}|分母.{0,12}(?:前年|去年|\d{4})', question):
        return analysis
    literal = (explicit_period(question) or {}).get('current') or {}
    current = (analysis.time_scope or {}).get('current') or {}
    # "最高三个月" is a ranked subset of months, not a partial calendar
    # window. The existing general parser intentionally leaves it unparsed.
    years = set(re.findall(r'(?<!\d)(\d{4})\s*年', question))
    if (not literal and len(years) == 1 and '全年' in question and
            re.search(r'(?:最高|最多|前)(?:的)?\s*[\d一二两三四五六七八九十]+\s*个?\s*月(?:份)?', question)):
        literal = (explicit_period(next(iter(years)) + '年') or {}).get('current') or {}
    if not literal or any(literal.get(key) != current.get(key) for key in ('start', 'end')):
        return analysis
    date_columns=[f'{table.name}.{column.name}' for table in getattr(catalog,'tables',[]) for column in table.columns
                  if column.name=='invoice_date' and re.search(r'date|timestamp',column.data_type,re.I)]
    def calendar_column(item):
        if item.get('column') and item.get('field') and item['column']!=item['field']:
            return False
        field=item.get('column',item.get('field'))
        return field=='invoice.invoice_date' or field=='invoice_date' and date_columns==['invoice.invoice_date']
    def same_value_representations(item):
        return ('value' not in item or 'values' not in item or
                type(item['value']) is type(item['values']) and item['value']==item['values'])
    def quote_is_calendar_role(item,role,*,ranking=False):
        if 'scope_evidence' not in item:
            return True
        quote=item['scope_evidence']
        if not isinstance(quote,str) or not quote or quote not in question or not same_year_rank_mirror:
            return False
        rank_quotes={literal_rank.group()}
        prefix=re.search(r'(?<!\d)\d{4}\s*年\s*$',question[:literal_rank.start()])
        if prefix:
            rank_quotes.add(question[prefix.start():literal_rank.end()])
        if ranking:
            return role=='numerator' and quote in rank_quotes
        period_quotes={str(start_date.year)+'年','全年'}
        period_quotes.update(m.group() for m in re.finditer(r'全年(?:发票|账单)(?:总额|金额)',question))
        return quote in period_quotes
    def plain_calendar_predicate(item,role):
        # A local scope, another metric/N, or an unknown condition is not a
        # redundant calendar mirror. Preserve it for semantic validation.
        return (calendar_column(item) and same_value_representations(item) and
                set(item)<={'field','column','operator','value','values','scope_evidence'} and
                quote_is_calendar_role(item,role))
    def value_of(item):
        return item.get('value',item.get('values'))
    ranked=analysis.query_scope.get('ranked_subset') or {}
    ranked_quote=str(ranked.get('source_evidence') or '')
    literal_rank=re.search(r'(?:发票|账单)(?:总额|金额).{0,4}(?:最高|最多)(?:的)?\s*([\d一二两三四五六七八九十]+)\s*个?\s*月',question)
    from qa_agent.clarify.literal_structures import number
    ranked_is_literal=(analysis.rank_object=='month' and ranked.get('grain')=='month' and ranked_quote and ranked_quote in question
        and isinstance(analysis.top_n,int) and not isinstance(analysis.top_n,bool) and ranked.get('limit')==analysis.top_n
        and ranked.get('group_by')=='invoice.invoice_date' and ranked.get('metric')=='invoice_revenue'
        and ranked.get('direction')=='desc' and analysis.metric=='invoice_revenue'
        and (analysis.order or {}).get('field')=='invoice_revenue'
        and str((analysis.order or {}).get('direction','')).casefold()=='desc'
        and literal_rank and number(literal_rank.group(1))==analysis.top_n
        and ranked_quote==literal_rank.group()
        and re.search(r'占(?:了)?.{0,20}全年(?:发票|账单)(?:总额|金额)',question))
    # The model sometimes renders an already proved month-ranking operand as
    # a symbolic date filter. Only that exact same operator/metric/N/year may
    # refer to ranked_subset; unknown predicates remain for strict rejection.
    def prose_selector_identity(value):
        if not isinstance(value,str):return None
        number_words=r'[\d一二两三四五六七八九十]+'
        phrase=re.fullmatch(
            r'(?:(\d{4})\s*年\s*)?(?:各月)?(?:发票|账单)(?:总额|金额)'
            r'(?:最高(?:的)?\s*('+number_words+r')\s*个?\s*(?:自然)?月(?:份)?|'
            r'(?:排名)?前\s*('+number_words+r')\s*个?\s*(?:的)?月(?:份)?)',value.strip())
        if phrase:
            return {'year':phrase[1],'limit':number(phrase[2] or phrase[3]),
                    'metric':'invoice_revenue','grain':'month','direction':'desc'}
        symbolic=re.fullmatch(r'top_(\d+)_by_invoice_revenue',value)
        if symbolic:
            return {'year':None,'limit':int(symbolic[1]),'metric':'invoice_revenue','grain':'month','direction':'desc'}
        return None

    def duplicate_month_rank(item):
        allowed={'field','column','operator','value','values','top_n','time_scope','metric','order','scope_evidence'}
        if not (ranked_is_literal and same_value_representations(item) and set(item)<=allowed and
                quote_is_calendar_role(item,'numerator',ranking=True)):
            return False
        op=str(item.get('operator','')).casefold()
        value=value_of(item)
        # A selection is an abstract role, not a physical date predicate. Its
        # identity comes from the already proved source rank/metric/N/year.
        # A model reference must encode that same identity in full; neither
        # an arbitrary IN value nor a source quote alone grants permission.
        reference=False
        if op=='in' and same_year_rank_mirror:
            actual=prose_selector_identity(literal_rank.group())
            proposed=prose_selector_identity(value)
            prefix=re.split(r'[，,；;。？！?!]',question[:literal_rank.start()])[-1]
            denied=re.search(r'(?:不是|并非|不要(?:选|取)?|别(?:选|取)?|排除|不(?:选|取))(?:那(?:个|些)?|这(?:个|些)?|按)?\s*$',prefix)
            reference=bool(actual and proposed and not denied and
                all(proposed[key]==actual[key]==ranked[key] for key in ('metric','grain','direction')) and
                proposed['limit']==actual['limit']==analysis.top_n and
                proposed['year'] in {None,str(start_date.year)})
        if item.get('column') and item.get('field') and item['column']!=item['field']:
            return False
        field=item.get('column') or item.get('field')
        # Logical month labels in captured proposals are usable only when
        # they cannot name a real physical column in this actual catalog.
        physical={name for table in getattr(catalog,'tables',[]) for column in table.columns
                  for name in (column.name,f'{table.name}.{column.name}')}
        selector_column=(date_columns==['invoice.invoice_date'] and
            (field in {'invoice.invoice_date','invoice_date'} or
             field in {'month','invoice_month','invoice_date.month','invoice.invoice_date.month'} and field not in physical))
        if not (calendar_column(item) or reference and selector_column):
            return False
        if reference and not selector_column:
            return False
        # These two structured forms occurred in real proposals. Their
        # operator never grants scope: actual literal rank/metric/N/year above
        # must independently agree, and all supplied representations agree.
        symbol=op in {'in_top_months_by','within_top_months_by'}
        metric_value=(symbol and value=='invoice_revenue' and type(item.get('top_n')) is int and item['top_n']==analysis.top_n)
        numeric_value=(symbol and type(value) is int and value==analysis.top_n and item.get('metric')=='invoice_revenue')
        legacy_numeric=(op in {'month_top_n','in_top_months_by_invoice_revenue'} and type(value) is int and value==analysis.top_n
                        and set(item)<={'field','column','operator','value','values','scope_evidence'})
        if not (metric_value or numeric_value or legacy_numeric or reference):
            return False
        if ('metric' in item and item['metric']!='invoice_revenue' or
                'top_n' in item and (type(item['top_n']) is not int or item['top_n']!=analysis.top_n) or
                'order' in item and item['order']!='desc'):
            return False
        start=date.fromisoformat(current['start']);end=date.fromisoformat(current['end'])
        if not (start.month==start.day==end.month==end.day==1 and end.year==start.year+1):
            return False
        if 'time_scope' in item:
            return isinstance(item['time_scope'],str) and item['time_scope'] in {str(start.year),str(start.year)+'年'}
        # Without a second proposed period, the actual unique global natural
        # year and exact rank quote/numeric tuple already prove the mirror.
        return same_year_rank_mirror
    # BETWEEN is not treated as half-open in SQL. In this bounded producer
    # case it is a model-only mirror of the user's natural year, whose two
    # actual boundaries already live in current. Literal endpoint requests
    # and independent operand periods are never rewritten by this rule.
    start_date=date.fromisoformat(current['start']);end_date=date.fromisoformat(current['end'])
    natural_year=(start_date.month==start_date.day==end_date.month==end_date.day==1 and end_date.year==start_date.year+1)
    same_year_rank_mirror=(ranked_is_literal and natural_year and not re.search(
        r'[\d一二三四五六七八九十]+\s*月\s*(?:[\d一二三四五六七八九十]+\s*日)?|日|BETWEEN|截至|截止|次年|翌年|下一年',
        re.sub(r'(?:最高|最多)(?:的)?\s*[\d一二两三四五六七八九十]+\s*个?\s*月', '', question),re.I))
    for role in ('numerator', 'denominator'):
        operand = analysis.query_scope.get(role)
        if not isinstance(operand, dict):
            continue
        period_matches=(not operand.get('period') or isinstance(operand['period'],dict) and
                        all(operand['period'].get(key)==current[key] for key in ('start','end')))
        if same_year_rank_mirror:
            # Only this proved month/year family is changed here. Do not alter
            # the existing general calendar-role behavior of other tasks.
            period_matches=('period' not in operand or isinstance(operand['period'],dict) and
                            set(operand['period'])=={'start','end'} and
                            all(operand['period'].get(key)==current[key] for key in ('start','end')))
            period_matches=period_matches and ('metric' not in operand or operand['metric']=='invoice_revenue')
        filters=operand.get('filters',[])
        dates=[item for item in filters if calendar_column(item)]
        paired=(period_matches and len(dates)==2 and all(plain_calendar_predicate(item,role) for item in dates) and
            any(str(item.get('operator','')).upper()=='>=' and value_of(item)==current['start'] for item in dates) and
            any(str(item.get('operator','')).upper()=='<' and value_of(item)==current['end'] for item in dates))
        if paired:
            operand['period']={key:current[key] for key in ('start','end')}
            operand['period_source']={'source':'program:literal_calendar_role','evidence':question,
                'reason':'操作数的两个同字段精确半开边界与当前权威期间相同，统一到单份period。'}
            filters=[item for item in filters if item not in dates]
        kept = []
        selection={'kind':'ranked_subset','definition_ref':'query_scope.ranked_subset'}
        for item in filters:
            values = value_of(item)
            if (role=='numerator' and period_matches and operand.get('selection') in (None,selection) and duplicate_month_rank(item)):
                # One canonical reference; raw model proposals remain in the
                # existing immutable provider capture, never rewritten here.
                operand['selection']=selection
                continue
            equal_year_label = (period_matches and plain_calendar_predicate(item,role) and
                str(item.get('operator', '')).upper() == 'BETWEEN' and isinstance(values, list) and len(values) == 2 and
                str(values[0]) == current['start'] and str(values[1]) == (date.fromisoformat(current['end']) - timedelta(days=1)).isoformat())
            equal_rank_year_bounds=(same_year_rank_mirror and plain_calendar_predicate(item,role) and
                str(item.get('operator','')).upper()=='BETWEEN' and values==[current['start'],current['end']] and
                period_matches)
            if not equal_year_label and not equal_rank_year_bounds:
                kept.append(item)
                continue
            operand['period'] = {key:current[key] for key in ('start', 'end')}
            operand['period_source'] = {'source':'program:literal_calendar_role', 'evidence':question,
                                        'reason':'本轮明确自然年以权威半开期间表示；模型生成的年末日期标签不是独立日期筛选。'}
        if 'filters' in operand:
            operand['filters'] = kept
    return analysis


def temporal_schema_columns(db_id):
    """Only actual typed catalog columns bypass a categorical value index."""
    from qa_agent.config import get_settings
    from qa_agent.sql.catalog import load_catalog
    settings = get_settings()
    path = settings.aw_catalog_path if db_id == 'adventureworks' else settings.catalog_path
    catalog = load_catalog(path)
    return {f'{table.name}.{column.name}' for table in catalog.tables for column in table.columns
            if re.search(r'date|timestamp|time', column.data_type, re.I)}


def recover_explicit_named_period(question,analysis,payload):
    """An explicit period label can resolve against one complete real clause."""
    from qa_agent.clarify.rules import explicit_period
    if explicit_period(question):
        return analysis  # Current literal dates take priority over definitions.
    labels={canonical for surface,canonical in {'主期间':'主期间','本期':'主期间','对比期':'对比期','上期':'对比期'}.items() if surface in question}
    using_primary=False
    retired_source=(analysis.condition_sources.get('time_scope') or {}).get('lifetime')=='retired'
    if not labels and (not analysis.time_scope or retired_source) and re.search(r'本次.{0,12}(?:复盘|分析|汇总).{0,8}主期间|本次复盘的主期间',str(payload.get('user_brief') or '')):
        # The named primary analysis period in this actual session brief is
        # the base of a fresh analysis, not the prior comparison's task-local
        # override. Explicit follow-up/season/date edits cannot use this path.
        temporal_reference=bool(re.search(r'刚才|接着|上述|同样|那个期间|这期间|去年|今年|前年|旺季|最近|月份|季度|半年|\d{4}',question))
        policies_defer=(analysis.task_type=='ranking' and analysis.rank_object=='customer' or analysis.metric=='repeat_customer_count')
        persistent_change=any(re.search(r'以后|后面都|接下来都|整个会话',str(turn.get('user') or '')) and
                              (explicit_period(str(turn.get('user') or '')) or re.search(r'全部数据|所有数据|不限(?:时间|期间|年份)',str(turn.get('user') or '')))
                              for turn in payload.get('actual_conversation',[]) if isinstance(turn,dict))
        from qa_agent.clarify.definition_recovery import complete_definitions,closed_country_members,label_is_referenced
        named_market=any(len(clauses)==1 and closed_country_members(label,clauses[0]) and label_is_referenced(label,question)
                         for label,clauses in complete_definitions(payload).items())
        sales_analysis=bool(re.search(r'卖了多少钱|销售额|明细金额|成交金额',question) and
            re.search(r'曲风|流派|艺术家|曲目|专辑|genre|artist|track|album',question,re.I) and
            re.search(r'各|分别|每|按.{0,10}(?:汇总|分组)',question))
        if named_market and sales_analysis and not temporal_reference and not policies_defer and not persistent_change:
            labels={'主期间'};using_primary=True
    if len(labels)!=1:
        return analysis
    label=next(iter(labels));candidates={}
    brief=str(payload.get('user_brief') or '')
    for match in re.finditer(re.escape(label)+r'\s*(?:是|为|指|[:：])[^。；;\n]+',brief):
        clause=match.group();period=explicit_period(clause)
        current=(period or {}).get('current') or {}
        if current.get('start') and current.get('end'):
            candidates.setdefault((current['start'],current['end']),[]).append((clause,period))
    if len(candidates)!=1:
        return analysis
    clause,period=next(iter(candidates.values()))[0]
    analysis.time_scope=period;analysis.time_ambiguous=False
    analysis.condition_sources['time_scope']={'source':'user_brief','evidence':clause,'lifetime':'task','applies_to':'global',
        'verified':True,'definition_label':label,
        'application':'session_primary_analysis_period' if using_primary else 'explicit_current_period_reference'}
    analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field') not in {'time_scope','time_scope.current'}]
    return analysis
