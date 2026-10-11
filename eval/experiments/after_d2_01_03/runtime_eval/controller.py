"""A bounded simulated user; only responds to the latest card's actual key."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from common import request_payload

ALIASES = {
    "time_scope.current": ("time_scope.current", "time_scope", "period", "year"),
    "time_ambiguous": ("time_scope.current", "time_scope", "period", "year"),
    "time_scope.base": ("time_scope.base", "base_period"),
    "metric": ("metric", "indicator", "popularity"),
    "rank_object": ("rank_object", "object"),
    "filters": ("value", "genre", "reference", "object", "artist_or_genre"),
    "region_scope": ("region_scope", "region_column"),
    "scope_missing": ("reference", "scope", "reference_scope"),
    "denominator": ("denominator", "ratio_base", "denominator_scope"),
    "numerator": ("numerator", "numerator_object"),
    "comparison.type": ("comparison.type", "comparison"),
}


@dataclass
class UserAnswer:
    outcome: str
    request: dict | None = None
    asked_key: str | None = None
    supplement_key: str | None = None
    reason: str = ""

    def as_dict(self):
        return dict(self.__dict__)


def _key(issue: dict) -> str | None:
    field = issue.get("field")
    if field in ALIASES:
        return field
    ident = issue.get("id", "")
    if ident.startswith("missing:") and ident[8:] in ALIASES:
        return ident[8:]
    if ident.startswith("value:"):
        return "filters"
    return None


def _standard(value: Any):
    if isinstance(value, dict):
        return value.get("standard_value", value.get("canonical_value", value.get("name", value.get("value"))))
    return value


def _column(value: Any):
    if isinstance(value, dict):
        if value.get("column"):
            return value["column"]
        if value.get("object_type") in {"artist", "genre"}:
            return value["object_type"] + ".name"
    return None


def _period(value: Any):
    if isinstance(value, int):
        return {"start": f"{value}-01-01", "end": f"{value+1}-01-01"}
    if isinstance(value, dict):
        if "year" in value:
            return _period(value["year"])
        current = value.get("current", value)
        if current.get("start") and (current.get("end") or current.get("end_exclusive")):
            return {"start": current["start"], "end": current.get("end", current.get("end_exclusive"))}
        if current.get("current_start") and current.get("current_end_exclusive"):
            return {"start": current["current_start"], "end": current["current_end_exclusive"]}
    return None


def _metric(value: Any):
    if isinstance(value, dict):
        value = value.get("metric", value.get("id"))
    return {"by_quantity": "purchased_quantity", "by_revenue": "detail_revenue",
            "sales_revenue": "invoice_revenue", "amount": "invoice_revenue",
            "purchase_amount": "invoice_revenue"}.get(value, value) if isinstance(value, str) else None


def _matches(option: dict, key: str, value: Any) -> bool:
    patch = option.get("patch") or {}
    ident = option.get("id")
    label = option.get("label")
    if not isinstance(ident, str) or not ident or not isinstance(label, str) or not label:
        return False
    if key == "filters":
        # Never choose a same-valued candidate in an unconfirmed different column.
        column, standard = _column(value), _standard(value)
        if not column or standard is None:
            return False
        actual_column = patch.get("column", option.get("column"))
        actual_value = patch.get("value", option.get("standard_value", option.get("value")))
        if actual_column is None and f"（{column}）" in label:
            actual_column = column
            actual_value = label.split("（", 1)[0]
        return actual_column == column and actual_value == standard
    if key in {"time_scope.current", "time_ambiguous"}:
        wanted = _period(value)
        actual = _period(patch.get("value"))
        if actual is None and re.fullmatch(r"year:\d{4}", ident):
            actual = _period(int(ident[5:]))
        return wanted is not None and wanted == actual
    if key == "region_scope":
        wanted = _column(value) or (value.get("region_column") if isinstance(value, dict) else value)
        actual = patch.get("value")
        if actual is None:
            actual = {"customer_country": "customer.country", "billing_country": "invoice.billing_country"}.get(ident)
        return wanted in {"customer.country", "invoice.billing_country"} and actual == wanted
    if key == "metric":
        wanted = _metric(value)
        actual = patch.get("value") or {"by_quantity": "purchased_quantity", "by_revenue": "detail_revenue",
                                          "by_playlist": "playlist_memberships"}.get(ident)
        return wanted is not None and actual == wanted
    if key == "comparison.type":
        wanted = value.get("type") if isinstance(value, dict) else value
        actual = (patch.get("value") or {}).get("type") if isinstance(patch.get("value"), dict) else ident
        return actual == wanted and actual in {"yoy", "mom"}
    return False


def next_answer(case: dict, response: dict, session_id: str, used_keys: list[str], latest_version: int | None,
                seen_card_ids: list[str] | None = None) -> UserAnswer:
    card = response.get("clarification") or {}
    controller = case.get("controller") or {}
    allowed = controller.get("allowed_user_supplements") or {}
    if not card.get("resume_supported"):
        return UserAnswer("controller_unanswered", reason="Current card has no supported session resume")
    version = card.get("intent_version")
    response_version = (response.get("intent") or {}).get("intent_version")
    if not card.get("clarification_id") or not isinstance(version, int) or response_version != version:
        return UserAnswer("controller_unanswered", reason="Card ID/version missing or mismatches actual response intent")
    if latest_version is not None and version <= latest_version:
        return UserAnswer("controller_unanswered", reason="Stale intent/card version")
    if card["clarification_id"] in (seen_card_ids or []):
        return UserAnswer("controller_unanswered", reason="Current card ID was already consumed")
    issues = card.get("issues") or []
    if not issues:
        return UserAnswer("controller_unanswered", reason="No supported structured asked key; free-form question is not guessed")
    for issue in issues:
        key = _key(issue)
        if key is None:
            continue
        if key in used_keys:
            continue
        supplement_key = next((name for name in ALIASES[key] if name in allowed), None)
        if supplement_key is None:
            continue
        entry = allowed[supplement_key]
        if not isinstance(entry, dict) or not isinstance(entry.get("answer"), str) or not entry["answer"].strip() or "value" not in entry:
            return UserAnswer("controller_unanswered", asked_key=key, reason="Malformed offline supplement")
        # Use only options belonging to this issue; a card may have multiple unanswered keys.
        options = issue.get("options") or []
        if not options and len(issues) == 1:
            options = card.get("options") or []
        matches = [item for item in options if _matches(item, key, entry["value"])]
        if len(matches) > 1:
            return UserAnswer("controller_unanswered", asked_key=key, reason="Multiple matching current options; cannot force a candidate")
        choice = matches[0] if matches else None
        # An option-based ambiguous value cannot be resolved by a guessed column.
        if key == "filters" and options and not choice:
            return UserAnswer("controller_unanswered", asked_key=key, supplement_key=supplement_key,
                              reason="Allowed value/column does not uniquely match an actual current candidate")
        # Reject bundled supplements which would secretly fill another missing key.
        if not choice and isinstance(entry["value"], dict):
            other_asks = {_key(item) for item in issues} - {key, None}
            bundles = {"metric": {"metric", "expression"}, "rank_object": {"object", "rank_object"},
                       "time_scope.current": {"time_scope", "current", "start", "year"},
                       "comparison.type": {"comparison"}, "region_scope": {"region_scope", "region_column"}}
            if any(set(entry["value"]) & bundles.get(other, set()) for other in other_asks):
                return UserAnswer("controller_unanswered", asked_key=key, supplement_key=supplement_key,
                                  reason="Offline answer bundles another currently unasked missing condition")
        try:
            payload = request_payload(session_id, choice["label"] if choice else entry["answer"], case["scope"],
                                      card_id=card["clarification_id"], version=version,
                                      choice=choice["id"] if choice else None)
        except Exception as exc:
            return UserAnswer("controller_unanswered", asked_key=key, reason=f"Actual API contract rejects resume: {type(exc).__name__}")
        return UserAnswer("answer", payload, key, supplement_key)
    return UserAnswer("controller_unanswered", reason="Unknown/unsupported asks, no allowed supplement, or a repeated unresolved key")
