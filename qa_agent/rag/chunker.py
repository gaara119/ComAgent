"""Deterministic, page-local chunks with explicit source coordinates."""
from __future__ import annotations

import hashlib
import re


def _section(text: str, previous: list[str]) -> list[str]:
    for line in text.splitlines()[:12]:
        line = line.strip()
        if 3 <= len(line) <= 120 and (re.match(r"^\d+(?:\.\d+)*[.\s]+\S", line)
                or re.match(r"^(?:第[一二三四五六七八九十\d]+[章节]|[一二三四五六七八九十]+、)", line)
                or (len(line) < 90 and line.isupper() and re.search(r"[A-Z]{3}", line))):
            return [line]
    return previous


def chunk_pages(pages: list[dict], max_chars: int = 600, overlap: int = 80) -> list[dict]:
    if max_chars < 200 or not 0 <= overlap < max_chars:
        raise ValueError("chunk 参数必须满足 max_chars>=200 且 0<=overlap<max_chars")
    chunks: list[dict] = []
    sections: dict[str, list[str]] = {}
    for page in pages:
        text = page["text"].replace("\x00", "").strip()
        if not text:
            continue
        doc_id = page["doc_id"]
        actual_font_headings = page.get("heading_candidates", [])
        sections[doc_id] = ([actual_font_headings[0]] if actual_font_headings
                            else _section(text, sections.get(doc_id, [])))
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            if end < len(text):
                # Prefer whole lines so financial table headers stay readable.
                split = text.rfind("\n", start + max_chars // 2, end)
                if split > start:
                    end = split + 1
            chunk_text = text[start:end].strip()
            if chunk_text:
                content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                stable = f"{doc_id}:{page['page']}:{start}:{end}:{content_hash}"
                source_blocks = [block for block in page.get("blocks", [])
                                 if block.get("char_start") is not None and block.get("char_end") is not None
                                 and block["char_start"] < end and block["char_end"] > start]
                bbox = None
                if source_blocks:
                    bbox = [min(block["bbox"][0] for block in source_blocks),
                            min(block["bbox"][1] for block in source_blocks),
                            max(block["bbox"][2] for block in source_blocks),
                            max(block["bbox"][3] for block in source_blocks)]
                chunks.append({"chunk_id": hashlib.sha256(stable.encode()).hexdigest()[:24],
                               "doc_id": doc_id, "doc_title": page["doc_title"], "page": page["page"],
                               "section_path": list(sections[doc_id]), "text": chunk_text,
                               "bbox": bbox, "bbox_scope": "union_of_text_blocks" if bbox else None,
                               "source_blocks": [{key: block[key] for key in
                                                   ("block_id", "bbox", "char_start", "char_end")} for block in source_blocks],
                               "page_bbox": page.get("bbox"),
                               "char_start": start, "char_end": end, "content_hash": content_hash})
            if end >= len(text):
                break
            next_start = max(start + 1, end - overlap)
            # Start on a full line when the overlap includes one.
            line_break = text.find("\n", next_start, end)
            start = line_break + 1 if line_break >= 0 else next_start
    return chunks
