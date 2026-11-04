"""Deterministic metrics. Unknown evidence is never converted to success or zero cost."""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
from itertools import permutations
import math
import re
import unicodedata

from benchmarks.agent240.table_compare import compare_results


def percentile(values, percent):
    if not 0 <= percent <= 100 or any(type(v) not in (float, int) or not math.isfinite(v) for v in values):
        raise ValueError("percentile requires finite samples and 0..100 percent")
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * percent / 100
    low, high = math.floor(index), math.ceil(index)
    return values[low] + (values[high] - values[low]) * (index - low)


def rate(values):
    values = list(values)
    known = [v for v in values if type(v) is bool]
    passed = sum(known)
    return {"passed": passed, "failed": len(known) - passed,
            "unknown": len(values) - len(known), "total": len(values),
            "known_rate": passed / len(known) if known else None,
            "full_rate": passed / len(values) if values and len(known) == len(values) else None,
            "lower_bound": passed / len(values) if values else None,
            "upper_bound": (passed + len(values) - len(known)) / len(values) if values else None}


def matrix(result):
    if not isinstance(result, dict) or result.get("available") is False or result.get("truncated") is True:
        raise ValueError("missing result")
    names, rows = result.get("columns"), result.get("rows")
    if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names) or len(set(names)) != len(names):
        raise ValueError("invalid projection")
    if not isinstance(rows, list):
        raise ValueError("invalid rows")
    output = []
    for row in rows:
        if isinstance(row, dict):
            if set(row) != set(names):
                raise ValueError("row/projection mismatch")
            output.append([row[n] for n in names])
        elif isinstance(row, (tuple, list)) and len(row) == len(names):
            output.append(list(row))
        else:
            raise ValueError("invalid row shape")
    return output, names


def numeric_indices(rows):
    if not rows:
        return []
    indices = []
    for col in range(len(rows[0])):
        values = [row[col] for row in rows if row[col] is not None]
        try:
            if values and all(type(v) is not bool and Decimal(str(v)).is_finite() for v in values):
                indices.append(col)
        except (InvalidOperation, ValueError, TypeError):
            pass
    return indices


def _cell(value, numeric):
    if value is None:
        return ("null",)
    if type(value) is bool:
        return ("bool", value)
    if numeric or isinstance(value, (int, float, Decimal)):
        try:
            number = Decimal(str(value))
            if number.is_finite():
                return ("number", number)
        except (InvalidOperation, ValueError, TypeError):
            pass
    return (type(value).__name__, str(value))


def table_scores(reference, predicted, *, ordered=False, observed=True, successful=True):
    """Exact EX plus multiset full-row F1, using one global column alignment.

    No rounding, scaling, removed columns or NULL imputation. F1 ignores row
    order; EX respects the reference's root ORDER BY. Aliases are ignored.
    More than seven columns without an exact alignment leaves partial F1 unknown.
    """
    unknown = {"exact_match": None, "row_f1": None}
    try:
        gold, columns = matrix(reference)
    except ValueError:
        return {**unknown, "reason": "reference_unavailable_or_invalid"}
    if not observed:
        return {**unknown, "reason": "prediction_not_observed"}
    if not successful:
        return {"exact_match": False, "row_f1": 0.0, "reason": "no_successful_result"}
    try:
        actual, actual_columns = matrix(predicted)
    except ValueError:
        return {"exact_match": False, "row_f1": 0.0, "reason": "missing_or_invalid_prediction_table"}
    numeric = numeric_indices(gold)
    ex = compare_results(gold, actual, ordered=ordered, expected_columns=columns,
                         actual_columns=actual_columns, numeric_columns=numeric,
                         monetary_columns=(), round_numeric_columns=())
    if len(columns) != len(actual_columns):
        return {"exact_match": False, "row_f1": 0.0, "reason": "column_count_mismatch"}
    if ex.matched:
        return {"exact_match": True, "row_f1": 1.0, "reason": ex.reason}
    if not gold or not actual:
        return {"exact_match": False, "row_f1": 0.0, "reason": ex.reason}
    if len(columns) > 7:
        return {"exact_match": False, "row_f1": None, "reason": "partial_alignment_over_seven_columns_not_verified"}
    expected = Counter(tuple(_cell(v, col in numeric) for col, v in enumerate(row)) for row in gold)
    best = 0
    for mapping in permutations(range(len(columns))):
        observed_rows = Counter(tuple(_cell(row[mapping[col]], col in numeric) for col in range(len(columns))) for row in actual)
        best = max(best, sum((expected & observed_rows).values()))
    return {"exact_match": False, "row_f1": 2 * best / (len(gold) + len(actual)), "reason": ex.reason}


def _normal(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def text_scores(reference, actual):
    """Conservative lexical diagnostic; never a semantic correctness label.

    CJK characters and Latin/number terms are tokens. Units, punctuation and
    signs are retained. No inferred reference answer from SQL/hidden goals.
    """
    if not isinstance(reference, str) or not reference.strip() or not isinstance(actual, str):
        return {"text_em": None, "text_f1": None}
    a, b = _normal(reference), _normal(actual)
    tokens = r"[\u3400-\u9fff]|[^\W_\u3400-\u9fff]+|[^\s]"
    x, y = Counter(re.findall(tokens, a, re.UNICODE)), Counter(re.findall(tokens, b, re.UNICODE))
    overlap = sum((x & y).values())
    denominator = sum(x.values()) + sum(y.values())
    return {"text_em": a == b, "text_f1": 2 * overlap / denominator if denominator else 1.0}


def provider_totals(attempts):
    """Physical provider captures are counted once, including failures/retries."""
    unique = {}
    collection_gaps = 0
    for attempt in attempts:
        if attempt.get("provider_collection_complete") is not True:
            collection_gaps += 1
        elif not attempt.get("provider_attempts") and attempt.get("no_model_call_verified") is not True:
            collection_gaps += 1
        for provider in attempt.get("provider_attempts", []):
            key = provider.get("capture_id")
            if not key:
                raise ValueError("provider evidence requires a capture_id")
            if key in unique and unique[key] != provider:
                raise ValueError("conflicting duplicate provider capture")
            unique[key] = provider
    entries = list(unique.values())
    fields = ("input_tokens", "output_tokens", "cache_hit_tokens", "cache_miss_tokens")
    result = {"physical_calls": len(entries) if not collection_gaps else None,
              "physical_calls_observed": len(entries), "collection_gap_requests": collection_gaps}
    for field in fields:
        values = [item.get(field) for item in entries]
        known = [v for v in values if type(v) is int and v >= 0]
        result[field] = sum(known) if len(known) == len(values) and not collection_gaps else None
        result[field + "_observed_sum"] = sum(known)
        result[field + "_missing_calls"] = len(values) - len(known)
    return result
