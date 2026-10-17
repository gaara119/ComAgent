"""Two actual named count operands do not imply an arbitrary Top10."""
from __future__ import annotations
import re


def explicit_paired_count(question,analysis):
    if re.search(r'排名|排行|前\s*[\d一二两三四五六七八九十]+|top\s*\d+',question,re.I):return analysis
    from qa_agent.sql.comparison_result import comparison_requirement
    required=comparison_requirement(question,analysis)
    if required is None:return analysis
    analysis.task_type='aggregation';analysis.rank_object=None;analysis.top_n=None;analysis.order=None
    analysis.grouping=[required['field']]
    for field in ('rank_object','top_n','order'):analysis.condition_sources.pop(field,None)
    for key in ('ranked_subset','ranking_scope','rank_metric','per_group_limit','partition_by'):
        analysis.query_scope.pop(key,None)
    analysis.query_scope['paired_count_comparison']={**required,'source':'program:explicit_paired_count',
        'source_evidence':question}
    analysis.assumptions=[text for text in analysis.assumptions if '未指定排名条数' not in text]
    analysis.default_assumptions=[text for text in analysis.default_assumptions if '未指定排名条数' not in text]
    analysis.output_requirements=[text for text in analysis.output_requirements if text not in {'ranked_subset_rows','ranked_subset_total'}]
    return analysis
