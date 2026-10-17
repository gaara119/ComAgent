"""Small typed structures proven by the current question, before SQL exists."""
from __future__ import annotations
import re
from qa_agent.clarify.output_requirements import requirement_has_semantics


def number(word):
    return int(word) if word.isdigit() else {'一':1,'二':2,'两':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}.get(word)


def explicit_literal_structures(question,analysis,catalog):
    if catalog.database.casefold()!='chinook':
        return analysis
    distinct_tracks=(re.search(r'多少\s*(?:首|条|个)?\s*(?:不同|不重复)(?:的)?\s*(?:曲目|歌曲|tracks?)',question,re.I) or
                     re.search(r'(?:不同|不重复)(?:的)?\s*(?:曲目|歌曲|tracks?).{0,5}(?:有多少|多少首|数量)',question,re.I) or
                     re.search(r'how\s+many\s+distinct\s+tracks?',question,re.I))
    if distinct_tracks:
        purchased=bool(re.search(r'卖出|售出|买过|购买|发票|账单|invoice|purchased|bought|sold',question,re.I))
        column='invoice_line.track_id' if purchased else 'track.track_id'
        if column in {f'{table.name}.{field.name}' for table in catalog.tables for field in table.columns}:
            analysis.metric='record_count'
            outer=bool(re.search(r'排名|排行|最多|最高|哪\s*[\d一二三四五六七八九十]+|前\s*[\d一二三四五六七八九十]+|top\s*\d+|同比|环比|增长|占比|比例|百分',question,re.I))
            if not outer:
                analysis.task_type='aggregation';analysis.rank_object=None;analysis.top_n=None;analysis.order=None
            analysis.query_scope['distinct_count']={'column':column,'object':'track','source':'program:explicit_distinct_tracks',
                'scope':'purchased_tracks' if purchased else 'catalog_tracks','source_evidence':distinct_tracks.group()}
            analysis.condition_sources['metric']={'source':'explicit_user','evidence':distinct_tracks.group(),
                                                  'lifetime':'task','applies_to':'global'}
    music_object=bool(re.search(r'艺术家|乐队|曲目|歌曲|专辑|artist|band|track|album',question,re.I) or
        any(item.get('column') in {'artist.name','album.title','track.name','genre.name'} for item in analysis.filters))
    sold_quantity=re.search(r'(?:卖出(?:去)?|售出|卖了|卖出去).{0,8}多少(?:张|份|件|首)|(?:购买数量|卖出数量|售出数量)(?:的)?(?:合计|总数|总计|是多少|有多少)',question)
    ranked_or_ratio_output=bool(re.search(r'排名|排行|排序|前[\d一二两三四五六七八九十]+|top\s*\d+|占比|比例|增长|同比|环比',question,re.I))
    if music_object and sold_quantity and not distinct_tracks and not ranked_or_ratio_output and not re.search(r'(?:发票|账单).{0,4}(?:张数|多少张)',question):
        analysis.task_type='aggregation';analysis.metric='purchased_quantity'
        analysis.numerator=None;analysis.denominator=None;analysis.comparison=None
        analysis.rank_object=None;analysis.top_n=None;analysis.order=None
        for key in ('numerator','denominator','ranked_subset','outer_operator','ranking_scope','rank_metric','rank_metric_source','numerator_ranking_metric'):
            analysis.query_scope.pop(key,None)
        for key in ('numerator','denominator','comparison','rank_object','top_n','order'):
            analysis.condition_sources.pop(key,None)
        analysis.clarification_requests=[item for item in analysis.clarification_requests if item.get('field') not in {'numerator','denominator','comparison.type','query_scope.rank_metric'}]
        analysis.output_requirements=[item for item in analysis.output_requirements if not requirement_has_semantics(item,'ratio','ranked_subset')]
        analysis.condition_sources['metric']={'source':'explicit_user','evidence':sold_quantity.group(),'lifetime':'task','applies_to':'global'}
    # A top-N calendar subtotal is one operand, never a different period.
    top_months=re.search(r'(?:发票|账单)(?:总额|金额).{0,4}(?:最高|最多)(?:的)?\s*([\d一二两三四五六七八九十]+)\s*个?\s*月',question)
    if top_months and re.search(r'占(?:了)?.{0,20}全年(?:发票|账单)(?:总额|金额)',question):
        count=number(top_months.group(1))
        if count:
            analysis.task_type='ratio';analysis.metric='invoice_revenue';analysis.top_n=count;analysis.rank_object='month'
            analysis.order={'field':'invoice_revenue','direction':'desc'}
            analysis.query_scope['ranked_subset']={'group_by':'invoice.invoice_date','grain':'month','limit':count,
                'metric':'invoice_revenue','direction':'desc','source_evidence':top_months.group()}
            if 'ranked_subset_total' not in analysis.output_requirements:analysis.output_requirements.append('ranked_subset_total')
            years=list(re.finditer(r'(?<!\d)(\d{4})\s*年',question))
            if len({match.group(1) for match in years})==1:
                from qa_agent.clarify.rules import explicit_period
                analysis.time_scope=explicit_period(years[0].group())
                analysis.time_ambiguous=False
                analysis.condition_sources['time_scope']={'source':'explicit_user','evidence':years[0].group(),'lifetime':'task','applies_to':'global'}
            analysis.condition_sources['metric']={'source':'explicit_user','evidence':top_months.group(),'lifetime':'task','applies_to':'global'}
            analysis.condition_sources['rank_object']={'source':'explicit_user','evidence':top_months.group(),'lifetime':'task','applies_to':'numerator'}
    ranked=re.search(r'哪\s*([\d一二两三四五六七八九十]+)\s*(?:张|首|位|个)?\s*(albums?|tracks?|artists?|专辑|曲目|歌曲|艺术家)',question,re.I)
    if ranked and re.search(r'(?:份数|件数|数量|销量).{0,8}(?:最多|最少)|(?:最多|最少).{0,8}(?:份数|件数|数量|销量)',question):
        target={'albums':'album','album':'album','专辑':'album','tracks':'track','track':'track','曲目':'track','歌曲':'track','artists':'artist','artist':'artist','艺术家':'artist'}[ranked.group(2).casefold()]
        count=number(ranked.group(1))
        if count and target in {table.name for table in catalog.tables}:
            analysis.task_type='ranking';analysis.rank_object=target;analysis.top_n=count;analysis.metric='purchased_quantity'
            analysis.order={'field':'purchased_quantity','direction':'asc' if '最少' in question else 'desc'}
            for field,evidence in [('rank_object',ranked.group(2)),('top_n',ranked.group()),('metric',question)]:
                analysis.condition_sources[field]={'source':'explicit_user','evidence':evidence,'lifetime':'task','applies_to':'global'}
    # Typed duration thresholds are not categorical value-index entities.
    if re.search(r'曲目|歌曲|track',question,re.I) and re.search(r'时长|分钟|毫秒',question):
        from qa_agent.clarify.definition_recovery import duration_threshold
        threshold=duration_threshold(question)
        if threshold:
            binding={'column':'track.milliseconds','operator':threshold[0],'value':threshold[1],
                     'source':'explicit_user','scope_evidence':question}
            if not any(old.get('column')=='track.milliseconds' for old in analysis.filters):analysis.filters.append(binding)
            if re.search(r'多少(?:首|条|个)?|几首|数量|count',question,re.I):analysis.metric='record_count';analysis.task_type='aggregation'
    return analysis
