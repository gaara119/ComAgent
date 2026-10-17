"""Ensure model-projected ROW_NUMBER matches the actual displayed TopN order."""
from decimal import Decimal, InvalidOperation
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope
from qa_agent.sql.repair_guard import _qualified
from qa_agent.sql.semantic_guard import _resolve_projection
from qa_agent.sql.validator import SQLValidationError


def validate_ranking_result(sql, catalog, intent, columns, rows):
    if (getattr(intent,'task_type',None) != 'ranking' or not getattr(intent,'top_n',None) or
            (getattr(intent,'query_scope',{}) or {}).get('ranking_scope') == 'per_group'):
        return {'verified':True,'mode':'not_global_topn_row_number'}
    tree=_qualified(sql,catalog)
    root=next(scope for scope in traverse_scope(tree) if scope.parent is None)
    checked=[]
    for index,projection in enumerate(root.expression.selects):
        value,owner=_resolve_projection(projection,root)
        if not isinstance(value,exp.Window) or not isinstance(value.this,exp.RowNumber):
            continue
        if value.args.get('partition_by'):
            raise SQLValidationError('全局前N名的名次不能分组后重复编号。')
        if index>=len(columns):
            raise SQLValidationError('实际排名列与SQL投影位置不一致。')
        column=columns[index]
        for position,row in enumerate(rows,1):
            try:
                raw=row[column]
                if isinstance(raw,bool) or Decimal(str(raw)) != Decimal(position):
                    raise ValueError('Order mismatch')
            except (KeyError,InvalidOperation,ValueError):
                raise SQLValidationError('实际ROW_NUMBER名次与返回行顺序不一致；普通全局TopN可省略名次列由程序展示，或让窗口与最终排序使用同样完整排序键。') from None
        checked.append(column)
    return {'verified':True,'mode':'actual_global_row_number_order','checked_columns':checked,'rows':len(rows)}
