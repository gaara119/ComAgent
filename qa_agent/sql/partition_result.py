"""Bind a pre-execution lineage proof to actual database output positions."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation

from qa_agent.sql.validator import SQLValidationError


def bind_partition_result(proof, columns, rows):
    if proof.get('mode') != 'typed_partition_invoice_amount_lineage':
        return proof
    if len(rows) != 1 or len(columns) != len(set(columns)):
        raise SQLValidationError('分组金额比较必须交付一行且列身份唯一的实际查询结果。')
    bound = deepcopy(proof)
    positions = [item.get('position') for item in bound['roles'].values()]
    if len(positions) != 3 or any(not isinstance(index,int) or isinstance(index,bool) for index in positions) or len(set(positions)) != 3:
        raise SQLValidationError('两个比较金额与差额必须来自三个互异的实际输出位置。')
    values = {}
    for role, item in bound['roles'].items():
        index = item.get('position')
        if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(columns):
            raise SQLValidationError('比较操作数的位置与实际数据库投影不一致。')
        column = columns[index]
        if column not in rows[0]:
            raise SQLValidationError('实际结果缺少比较操作数，不能仅靠生成SQL声称已交付。')
        item['lineage_column'] = item['column']
        item['column'] = column
        value = rows[0][column]
        if value is None:
            values[role] = None
        else:
            try:
                if isinstance(value, bool):
                    raise ValueError('Boolean is not monetary data')
                values[role] = Decimal(str(value))
                if not values[role].is_finite():
                    raise ValueError('Non-finite monetary value')
            except (InvalidOperation, ValueError):
                raise SQLValidationError('比较操作数不是数据库返回的有限数值或NULL。') from None
    if set(values) != {'focus','other','difference'}:
        raise SQLValidationError('实际比较结果没有完整的两组金额与差额。')
    expected = None if values['focus'] is None or values['other'] is None else values['focus'] - values['other']
    if values['difference'] != expected:
        raise SQLValidationError('实际差额与重点市场金额减其余市场金额不一致，不能交付。')
    bound['actual_result_verified'] = True
    bound['actual_values'] = {role: str(value) if value is not None else None for role,value in values.items()}
    return bound
