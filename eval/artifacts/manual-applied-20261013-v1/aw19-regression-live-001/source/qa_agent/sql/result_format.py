"""Describe percentage presentation without changing database evidence."""
from decimal import Decimal, InvalidOperation

import sqlglot
from sqlglot import exp


def percentage_formats(sql, columns, task_type):
    if task_type not in {"ratio", "growth", "yoy"}:
        return {}
    try:
        selections = sqlglot.parse_one(sql, read="postgres").selects
        result = {}
        for name, selected in zip(columns, selections):
            expression = selected.this if isinstance(selected, exp.Alias) else selected
            division = expression.find(exp.Div)
            explicit_rate = any(token in name.casefold() for token in ("ratio", "share", "rate", "percentage", "percent", "yoy", "增长", "占比", "比例"))
            amount_label = any(token in name.casefold() for token in ("amount", "average", "avg", "revenue", "金额", "销售额", "客单价", "平均"))
            if not division or (amount_label and not explicit_rate) or (len(columns) > 1 and not explicit_rate):
                continue
            # Amount per invoice/customer remains an amount even in a response
            # that also contains a genuine share column.
            if isinstance(division.right, exp.Count) and isinstance(division.left, exp.Sum):
                continue
            scaled = any(isinstance(child, exp.Literal) and not child.is_string and Decimal(child.this) == 100
                         for mul in expression.find_all(exp.Mul) for child in (mul.left, mul.right))
            result[name] = {"kind": "percentage", "scale": 1 if scaled else 100,
                            "raw_values_preserved": True, "source": "sql_projection"}
        return result
    except Exception:
        return {}


def display_percentage(value, rule):
    if value is None:
        return "NULL"
    try:
        number = Decimal(str(value)) * Decimal(str(rule["scale"]))
        return f"{number:.2f}%" if number.is_finite() else str(value)
    except (InvalidOperation, KeyError, ValueError):
        return str(value)
