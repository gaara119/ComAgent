"""Deterministic page-local excerpts that prefer complete source sentences."""
from __future__ import annotations

import hashlib
import re

_NUMBER = re.compile(r"(?<!\w)[+-]?(?:[$€£]\s*)?\d+(?:[.,]\d+)*(?:%|x)?(?!\w)")
_ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "prof", "inc", "corp", "ltd", "no", "st", "vs", "etc", "fig", "eq", "sec", "ft"}


def is_table_line(line: str) -> bool:
    words = line.split()
    numbers = _NUMBER.findall(line)
    return len(numbers) >= 2 and len(numbers) / max(1, len(words)) >= 0.20


def is_heading_candidate(line: str, *, require_pattern: bool = True) -> bool:
    line = line.strip()
    if not 3 <= len(line) <= 120 or is_table_line(line):
        return False
    if re.match(r"^(?:[$€£]|(?:19|20)\d{2}(?:\s|$))", line):
        return False
    if not require_pattern:
        return True
    return bool(re.match(r"^\d+(?:\.\d+)*[.\s]+[A-Za-z\u4e00-\u9fff]", line)
                or re.match(r"^(?:第[一二三四五六七八九十\d]+[章节]|[一二三四五六七八九十]+、)", line)
                or (len(line) < 90 and line.isupper() and re.search(r"[A-Z]{3}", line)))


def _section(text: str, previous: list[str]) -> list[str]:
    for line in text.splitlines()[:12]:
        if is_heading_candidate(line):
            return [line.strip()]
    return previous


def _skip_space(text: str, position: int) -> int:
    while position < len(text) and text[position].isspace():
        position += 1
    return position


def _boundaries(text: str) -> dict[int, str]:
    """Find sentence, heading and numeric-row ends in the unchanged source."""
    boundaries = {0: "page_start"}
    for match in re.finditer(r"[.!?。！？](?:[\"”’')\]]*)(?=\s|$)", text):
        if text[match.start()] == ".":
            before = text[:match.start()]
            word = re.search(r"([A-Za-z]+)$", before)
            if word and (word.group(1).lower() in _ABBREVIATIONS or len(word.group(1)) == 1):
                continue
            if re.fullmatch(r"\d+(?:\.\d+)*", before.rsplit("\n", 1)[-1].strip()):
                continue
        boundaries[match.end()] = "sentence"
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        offset += len(raw_line)
        line = raw_line.strip()
        if not line:
            boundaries[offset] = "paragraph"
        elif is_table_line(line):
            boundaries[offset] = "table_line"
        elif is_heading_candidate(line):
            boundaries[offset] = "heading_line"
    return boundaries


def _cut(text: str, start: int, limit: int, boundaries: dict[int, str]) -> tuple[int, str]:
    if limit >= len(text):
        return len(text), "page_end"
    safe = [position for position in boundaries if start < position <= limit]
    if safe:
        end = max(safe)
        return end, boundaries[end]
    # A long sentence/row must retain the hard limit; its flags disclose that
    # the excerpt is incomplete instead of silently claiming a whole sentence.
    line = text.rfind("\n", start + max(1, (limit-start)//2), limit + 1)
    if line >= start:
        return line + 1, "forced_line"
    word = text.rfind(" ", start + max(1, (limit-start)//2), limit + 1)
    return (word if word > start else limit), "forced_word"


def _chunk_records(pages: list[dict], max_chars: int = 500, overlap: int = 80) -> list[dict]:
    if max_chars < 200 or not 0 <= overlap < max_chars:
        raise ValueError("chunk 参数必须满足 max_chars>=200 且 0<=overlap<max_chars")
    chunks: list[dict] = []
    sections: dict[str, list[str]] = {}
    for page in pages:
        # No rewriting/dehyphenation: source characters and offsets remain real.
        text = page["text"]
        if not text.strip():
            continue
        doc_id = page["doc_id"]
        headings = [h for h in page.get("heading_candidates", [])
                    if is_heading_candidate(h, require_pattern=False)]
        sections[doc_id] = (list(page["section_path"]) if "section_path" in page else
                            ([headings[0]] if headings else _section(text, sections.get(doc_id, []))))
        boundaries = _boundaries(text)
        starts = {_skip_space(text, pos): kind for pos, kind in boundaries.items()}
        start = _skip_space(text, 0)
        start_kind = "page_start"
        previous_end = start
        while start < len(text):
            end, end_kind = _cut(text, start, min(start + max_chars, len(text)), boundaries)
            visible_end = end
            while visible_end > start and text[visible_end-1].isspace():
                visible_end -= 1
            chunk_text = text[start:visible_end]
            if chunk_text:
                content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                stable = f"{doc_id}:{page['page']}:{page.get('record_id', '')}:{page.get('source_offset', 0)+start}:{page.get('source_offset', 0)+visible_end}:{content_hash}"
                source_blocks = [b for b in page.get("blocks", [])
                                 if b.get("char_start") is not None and b.get("char_end") is not None
                                 and b["char_start"] < visible_end and b["char_end"] > start]
                boxed = [b for b in source_blocks if b.get("bbox") is not None]
                bbox = ([min(b["bbox"][0] for b in boxed), min(b["bbox"][1] for b in boxed),
                         max(b["bbox"][2] for b in boxed), max(b["bbox"][3] for b in boxed)]
                        if boxed else None)
                complete_end = end_kind in {"sentence", "paragraph", "heading_line", "table_line"}
                if end_kind == "page_end":
                    complete_end = visible_end in boundaries or bool(re.search(r"[.!?。！？][\"”’')\]]*$", chunk_text))
                chunks.append({"chunk_id": hashlib.sha256(stable.encode()).hexdigest()[:24],
                               "doc_id": doc_id, "doc_title": page["doc_title"], "page": page["page"],
                               "section_path": list(sections[doc_id]), "text": chunk_text,
                               "bbox": bbox, "bbox_scope": "union_of_text_blocks" if bbox else None,
                               "source_blocks": [{k: b[k] for k in ("block_id", "bbox", "char_start", "char_end")}
                                                 for b in source_blocks],
                               "page_bbox": page.get("bbox"),
                               "char_start": page.get("source_offset", 0)+start,
                               "char_end": page.get("source_offset", 0)+visible_end,
                               "source_record_id": page.get("record_id"), "parser": page.get("parser"),
                               "warnings": page.get("warnings", []), "source_url": page.get("source_url", ""),
                               "content_hash": content_hash, "boundary_start": start_kind, "boundary_end": end_kind,
                               "incomplete_sentence_start": start_kind.startswith("forced_"),
                               "incomplete_sentence_end": not complete_end,
                               "overlap_chars": max(0, previous_end-start)})
            if end >= len(text):
                break
            previous_end = end
            candidates = [pos for pos in starts if start < pos < end
                          and end-pos <= min(overlap * 2, max_chars//2)
                          and _cut(text, pos, min(pos+max_chars, len(text)), boundaries)[0] > end]
            if overlap and candidates:
                start = min(candidates, key=lambda pos: (abs(pos-(end-overlap)), -pos))
                start_kind = starts[start]
            else:
                start = _skip_space(text, end)
                start_kind = end_kind
    return chunks


def chunk_pages(pages: list[dict], max_chars: int = 500, overlap: int = 80) -> list[dict]:
    """Section-first, page-local chunks; never overlap into another heading.

    Non-paginated parsers already produce section records. PDF heading starts
    use unchanged source offsets, retaining the one-physical-page contract.
    """
    records = []
    inherited: dict[str, list[str]] = {}
    for page in pages:
        if "section_path" in page:
            records.append(page)
            inherited[page["doc_id"]] = list(page["section_path"])
            continue
        text = page["text"]
        supplied = [h for h in page.get("heading_candidates", [])
                    if is_heading_candidate(h, require_pattern=False)]
        offsets = []
        offset = 0
        for raw in text.splitlines(keepends=True):
            line = raw.strip()
            if line in supplied or is_heading_candidate(line):
                offsets.append((offset+len(raw)-len(raw.lstrip()), line))
            offset += len(raw)
        if not offsets:
            record = dict(page)
            record["section_path"] = inherited.get(page["doc_id"], [])
            # Keep multi-line font-based candidates even when no line matches.
            if supplied:
                record["section_path"] = [supplied[0]]
            records.append(record)
            inherited[page["doc_id"]] = record["section_path"]
            continue
        cuts = [(0, inherited.get(page["doc_id"], []))]
        for position, heading in offsets:
            if position == 0:
                cuts[0] = (0, [heading])
            else:
                cuts.append((position, [heading]))
        for number, (start, section) in enumerate(cuts):
            end = cuts[number+1][0] if number+1 < len(cuts) else len(text)
            if not text[start:end].strip():
                continue
            blocks = [{**block, "char_start": block["char_start"]-start,
                       "char_end": block["char_end"]-start}
                      for block in page.get("blocks", [])
                      if block.get("char_start") is not None and block.get("char_end") is not None
                      and block["char_start"] < end and block["char_end"] > start]
            records.append({**page, "text": text[start:end], "blocks": blocks,
                            "section_path": section, "source_offset": start})
            inherited[page["doc_id"]] = section
    return _chunk_records(records, max_chars, overlap)
