"""Deterministic execution accuracy with a single column mapping for all rows.

Numeric strings are accepted only in columns declared numeric (needed for JSON
Decimal serialization). Monetary rounding is restricted to declared money fields.
NULL, an empty table, zero, and the empty string remain distinct.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ComparisonResult:
    matched: bool
    reason: str
    column_mapping: tuple[int, ...] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"matched": self.matched, "reason": self.reason,
                "column_mapping": list(self.column_mapping) if self.column_mapping is not None else None}


def _matrix(rows: Sequence[Any], columns: Sequence[str] | None) -> tuple[list[list[Any]], list[str]]:
    if not rows:
        return [], list(columns or [])
    if isinstance(rows[0], Mapping):
        names = list(columns) if columns is not None else list(rows[0])
        if any(set(row) != set(names) for row in rows):
            raise ValueError("结果中各行的列集合不一致")
        return [[row[name] for name in names] for row in rows], names
    matrix = [list(row) for row in rows]
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise ValueError("结果中各行的列数不一致")
    if columns is not None and len(columns) != width:
        raise ValueError("结果列数与 columns 元数据不一致")
    return matrix, list(columns) if columns is not None else [str(i) for i in range(width)]


def _indices(fields: Iterable[int | str], names: list[str]) -> set[int]:
    result: set[int] = set()
    for field in fields:
        index = field if isinstance(field, int) else names.index(field)
        if not 0 <= index < len(names):
            raise ValueError("比较规则包含越界列")
        result.add(index)
    return result


def _canonical(value: Any, *, numeric: bool, money: bool, temporal: bool) -> tuple:
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float, Decimal)) or (numeric and isinstance(value, str)):
        try:
            number = Decimal(str(value))
            if not number.is_finite():
                return ("nonfinite", str(number))
            if money:
                number = number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return ("number", number)
        except (InvalidOperation, ValueError):
            return ("invalid_numeric", str(value))
    if isinstance(value, datetime):
        return ("datetime", value.isoformat())
    if isinstance(value, date):
        return ("date", value.isoformat())
    if temporal and isinstance(value, str):
        try:
            if len(value) == 10:
                return ("date", date.fromisoformat(value).isoformat())
            return ("datetime", datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat())
        except ValueError:
            return ("invalid_temporal", value)
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, (list, dict)):
        import json
        return ("json", json.dumps(value, sort_keys=True, ensure_ascii=False))
    return (type(value).__name__, str(value))


def compare_results(
    expected_rows: Sequence[Any], actual_rows: Sequence[Any], *, ordered: bool = False,
    monetary_columns: Iterable[int | str] = (), numeric_columns: Iterable[int | str] = (),
    temporal_columns: Iterable[int | str] = (), expected_columns: Sequence[str] | None = None,
    actual_columns: Sequence[str] | None = None,
) -> ComparisonResult:
    """Compare rows under a global column permutation, preserving multiplicity.

    Column flags refer to GOLD columns, so their meaning follows the discovered
    mapping even when the model changes aliases or swaps columns.
    """
    try:
        expected, names = _matrix(expected_rows, expected_columns)
        actual, actual_names = _matrix(actual_rows, actual_columns)
        if len(expected) != len(actual):
            return ComparisonResult(False, "row_count_mismatch")
        if not expected:
            if names and actual_names and len(names) != len(actual_names):
                return ComparisonResult(False, "column_count_mismatch")
            return ComparisonResult(True, "equal_empty_tables", tuple(range(len(names))))
        if len(names) != len(actual_names):
            return ComparisonResult(False, "column_count_mismatch")
        width = len(names)
        money = _indices(monetary_columns, names)
        numeric = _indices(numeric_columns, names) | money
        temporal = _indices(temporal_columns, names)
        for index in range(width):
            observed = [row[index] for row in expected if row[index] is not None]
            if observed and all(isinstance(v, (int, float, Decimal)) and not isinstance(v, bool) for v in observed):
                numeric.add(index)
            if observed and all(isinstance(v, (datetime, date)) for v in observed):
                temporal.add(index)

        def normalize(value: Any, column: int) -> tuple:
            return _canonical(value, numeric=column in numeric,
                              money=column in money, temporal=column in temporal)

        normalized_gold = [tuple(normalize(value, col) for col, value in enumerate(row)) for row in expected]
        candidates: dict[int, list[int]] = {}
        actual_values: dict[tuple[int, int], list[tuple]] = {}
        for gold_col in range(width):
            gold_values = [row[gold_col] for row in normalized_gold]
            candidates[gold_col] = []
            for actual_col in range(width):
                values = [normalize(row[actual_col], gold_col) for row in actual]
                actual_values[gold_col, actual_col] = values
                equal = gold_values == values if ordered else Counter(gold_values) == Counter(values)
                if equal:
                    candidates[gold_col].append(actual_col)
            if not candidates[gold_col]:
                return ComparisonResult(False, "column_values_mismatch")

        # Matching column marginals alone is insufficient: validate complete rows
        # and prune with partial rows, using the same mapping for every row.
        search_order = sorted(range(width), key=lambda i: (len(candidates[i]), i))
        mapping: dict[int, int] = {}
        used: set[int] = set()

        def search(depth: int) -> tuple[int, ...] | None:
            if depth == width:
                return tuple(mapping[index] for index in range(width))
            gold_col = search_order[depth]
            for actual_col in candidates[gold_col]:
                if actual_col in used:
                    continue
                mapping[gold_col] = actual_col
                selected = sorted(mapping)
                gold_partial = [tuple(row[col] for col in selected) for row in normalized_gold]
                actual_partial = [tuple(actual_values[col, mapping[col]][i] for col in selected)
                                  for i in range(len(actual))]
                equal = gold_partial == actual_partial if ordered else Counter(gold_partial) == Counter(actual_partial)
                if equal:
                    used.add(actual_col)
                    found = search(depth + 1)
                    used.remove(actual_col)
                    if found is not None:
                        return found
                del mapping[gold_col]
            return None

        found = search(0)
        if found is not None:
            return ComparisonResult(True, "equal", found)
        return ComparisonResult(False, "row_values_or_order_mismatch")
    except (TypeError, ValueError, KeyError) as exc:
        return ComparisonResult(False, f"invalid_result_shape: {exc}")
