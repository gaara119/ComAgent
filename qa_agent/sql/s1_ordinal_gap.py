"""Check a declared S1 ordinal-row gap, never a business metric or population."""
import re

from sqlglot import exp
from sqlglot.optimizer.scope import build_scope, walk_in_scope

from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _resolve_projection
from qa_agent.sql.validator import SQLValidationError


def validate_ordinal_gap_sql(sql, catalog, question, shape):
    no = {'status': 'not_verified', 'business_correctness_asserted': False}
    if (not shape or shape.get('kind') != 'single_rank_difference'
            or re.search(r'并列|竞争|稠密|同一名次|同名次|同分|允许跳号|RANK|排名组', question, re.I)):
        return no
    try:
        tree = _qualified(sql, catalog)
        root = build_scope(tree)
        if root is None or not isinstance(root.expression, exp.Select):
            return no
        consumed = []
        for projection in root.expression.selects:
            for node in walk_in_scope(projection):
                if not isinstance(node, exp.Column):
                    continue
                value, _ = _resolve_projection(node, root)
                if isinstance(value, exp.Window) and isinstance(value.this, (exp.Rank, exp.DenseRank)):
                    consumed.append(value.sql(dialect='postgres'))
        if not consumed:
            return no
    except (ValueError, TypeError, KeyError, StopIteration):
        return no
    error = SQLValidationError('①SQL工具的第N位对象差额：当前原问未要求竞争/稠密/并列名次。'
        '按本工具稳定行位置约定，以原指标排序并用实际对象主键稳定同值后ROW_NUMBER编号；'
        '不能以RANK跳号或DENSE_RANK按不同数值组编号替代第N位对象。保留原筛选、指标、'
        '人口、单位及缺少足够对象时的NULL，不用COALESCE或常量补造差额。')
    error.ordinal_gap_evidence = {'source_requirement': shape, 'consumed_windows': consumed,
        'authority': 'S1_SQL_tool_ordinal_row_policy_not_business_semantic_proof',
        'business_correctness_asserted': False, 'state_committed': False}
    raise error
