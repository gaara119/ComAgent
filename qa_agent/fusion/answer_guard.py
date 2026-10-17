"""Mechanical provenance checks for composed summaries, with no judge API."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
import re


class CombinedAnswerError(ValueError):
    pass


_NUMBER = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d[\d,]*(?:\.\d+)?(?:%|％)?")


def _numbers(text):
    return _NUMBER.findall(str(text))


_DATE = re.compile(r"(?<!\d)(?P<year>\d{4})(?:-|年\s*)(?P<month>\d{1,2})(?:-|月\s*)(?P<day>\d{1,2})(?:日)?(?!\d)")


def _dates(text):
    for match in _DATE.finditer(str(text)):
        try:
            value = date(*(int(match[key]) for key in ("year", "month", "day")))
        except ValueError:
            continue
        yield match, value


def _normal(value):
    percent = str(value).endswith(("%", "％"))
    try:
        number = Decimal(str(value).rstrip("%％").replace(",", ""))
    except InvalidOperation:
        return None
    return (number.normalize(), percent) if number.is_finite() else None


def validate_combined_answer(answer, citation_ids, evidences, outputs, *, question=""):
    available = {e.evidence_id: e for e in evidences}
    inline = set(re.findall(r"\[(E\d+)\]", answer))
    declared = set(citation_ids)
    if len(citation_ids) != len(declared) or declared != inline or not inline <= set(available):
        raise CombinedAnswerError("合并答案引用编号与实际文档及正文引用不一致。")
    if available and not inline:
        raise CombinedAnswerError("合并答案缺少支持文档结论的实际引用。")
    allowed = set()
    allowed_dates = {value for _, value in _dates(question)}
    artist_entities, doc_ids, record_counts = set(), set(), set()
    artist_names={ref.split(":",3)[2]:ref.split(":",3)[3].casefold() for output in outputs.values()
        for ref in output.get("entity_refs",[]) if ref.startswith("chinook:artist:") and len(ref.split(":",3))==4}
    # Scope/period labels may repeat the user-specified year, but user brief
    # numeric examples and model-produced intermediate SQL text are excluded.
    allowed.update(_normal(year) for year in re.findall(r"(?<!\d)(?:19|20)\d{2}(?=\s*年)", question))
    for output in outputs.values():
        if output.get("source") != "database" or output.get("status") not in {"SUCCEEDED", "EMPTY_RESULT"}:
            continue
        metadata = output.get("metadata") or {}
        formats = metadata.get("result_format") or {}
        contract = (metadata.get("clarify") or {}).get("semantic_contract") or {}
        # Only the validated current execution contract can provide scope dates;
        # arbitrary model SQL text and user examples are not numeric proof.
        for role in ("current", "base"):
            period = (contract.get("time_scope") or {}).get(role) or {}
            for boundary in ("start", "end"):
                allowed_dates.update(value for _, value in _dates(period.get(boundary) or ""))
        for row in output.get("table") or []:
            artist = next((str(row[key]).casefold() for key in ("artist_name","艺术家","乐队名") if row.get(key) is not None),None)
            if not artist:
                artist_id=next((str(row[key]) for key in ("artist_id","艺术家编号") if row.get(key) is not None),None)
                artist=artist_names.get(artist_id,"@id:"+artist_id) if artist_id else None
            if artist:
                artist_entities.add(artist)
            for column, value in row.items():
                # Accept only scalar numeric cells; SQL strings, arbitrary
                # narrative and JSON payload fields cannot become result proof.
                if value is None or isinstance(value, bool):
                    continue
                try:
                    number = Decimal(str(value))
                except InvalidOperation:
                    continue
                if not number.is_finite():
                    continue
                allowed.add((number.normalize(), False))
                allowed.add((number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP).normalize(), False))
                rule = formats.get(column, {})
                if rule.get("kind") == "percentage" and rule.get("source") == "sql_projection" and rule.get("scale") in {1, 100}:
                    scaled = number * Decimal(str(rule["scale"]))
                    for places in ("0.1", "0.01"):
                        allowed.add((scaled.quantize(Decimal(places), rounding=ROUND_HALF_UP).normalize(), True))
        record_counts.add(len(output.get("table") or []))
    for output in outputs.values():
        if output.get("source")=="documents" and output.get("status")=="SUCCEEDED":
            artist_entities.update(ref.split(":",3)[3].casefold() for ref in output.get("entity_refs",[]) if ref.startswith("chinook:artist:") and len(ref.split(":",3))==4)
    for evidence_id in inline:
        doc_ids.add(available[evidence_id].doc_id)
        allowed.update(_normal(value) for value in _numbers(available[evidence_id].text))
    factual_text = re.sub(r"(?m)^\s*\d+[.)、]\s+", "", answer)
    derived_spans=[]
    for match, value in _dates(factual_text):
        if value in allowed_dates:
            derived_spans.extend((atom.start(), atom.end()) for atom in _NUMBER.finditer(factual_text)
                                 if match.start() <= atom.start() and atom.end() <= match.end())
    for match in re.finditer(r"(\d+)\s*(支(?:乐队)?|位艺术家|个艺术家|份(?:文档|资料)|条记录)",factual_text):
        count=int(match[1]);unit=match[2]
        accepted=(count==len(doc_ids) if unit.startswith("份") else count in record_counts if unit=="条记录" else bool(artist_entities) and count==len(artist_entities))
        if accepted:
            derived_spans.append((match.start(1),match.end(1)))
    bad=[]
    for match in _NUMBER.finditer(factual_text):
        if _normal(match.group()) not in allowed and not any(start==match.start() and end==match.end() for start,end in derived_spans):
            bad.append(match.group())
    if bad:
        raise CombinedAnswerError("合并答案数值没有对应实际查询结果或所引原文，不能改写金额、数量或无依据转换百分比：" + ", ".join(bad[:8]))
    return {"verified": True, "citation_ids": sorted(inline), "numeric_source_check": "actual_table_or_cited_evidence",
            "semantic_faithfulness": "requires_human_review" if available else "not_applicable"}
