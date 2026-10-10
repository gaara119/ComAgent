"""Parse physical PDF pages without guessing OCR text or printed page numbers."""
from __future__ import annotations

from pathlib import Path
import re
from statistics import median


class DocumentError(RuntimeError):
    def __init__(self, message: str, code: str = "document_error"):
        super().__init__(message)
        self.code = code


def _attach_layout(text: str, layout: dict) -> tuple[list[dict], list[str]]:
    """Map actual PDF text blocks to source characters only when unambiguous.

    PDF text engines can produce different whitespace/table reading orders. A
    block that cannot be matched uniquely has no claimed character location.
    Coordinates remain the real PyMuPDF block rectangle, not a fabricated word
    highlight or a guess based on paragraph length.
    """
    positions = [i for i, character in enumerate(text) if not character.isspace()]
    normalized = "".join(text[i] for i in positions)
    sizes = [float(span["size"]) for block in layout.get("blocks", []) if block.get("type") == 0
             for line in block.get("lines", []) for span in line.get("spans", [])
             if span.get("text", "").strip() and span.get("size")]
    body_size = median(sizes) if sizes else 0
    blocks = []
    headings = []
    for number, block in enumerate(layout.get("blocks", [])):
        if block.get("type") != 0:
            continue
        lines = ["".join(span.get("text", "") for span in line.get("spans", []))
                 for line in block.get("lines", [])]
        block_text = "\n".join(lines).strip()
        compact = re.sub(r"\s+", "", block_text)
        if not compact:
            continue
        record = {"block_id": number, "text": block_text,
                  "bbox": [round(float(v), 2) for v in block["bbox"]],
                  "char_start": None, "char_end": None}
        offset = normalized.find(compact)
        if offset >= 0 and normalized.find(compact, offset + 1) < 0:
            record["char_start"] = positions[offset]
            record["char_end"] = positions[offset + len(compact) - 1] + 1
        spans = [span for line in block.get("lines", []) for span in line.get("spans", []) if span.get("text", "").strip()]
        record["max_font_size"] = max((float(span.get("size", 0)) for span in spans), default=0)
        # Large actual source text is a candidate, not an invented section name.
        if (body_size and 3 <= len(block_text) <= 120 and record["char_start"] is not None
                and record["max_font_size"] >= body_size * 1.18 and len(lines) <= 3):
            headings.append(text[record["char_start"]:record["char_end"]])
        blocks.append(record)
    return blocks, headings


def load_documents(manifest_path=None, project_root=None) -> list[dict]:
    # The public document API and ingestion deliberately use the same validation.
    from qa_agent.documents import load_documents as load
    from qa_agent.config import PROJECT_ROOT
    try:
        return load(manifest_path=manifest_path, project_root=project_root or PROJECT_ROOT)
    except ValueError as exc:
        raise DocumentError(str(exc), "document_manifest_invalid") from exc


def parse_pdf(document: dict) -> list[dict]:
    import pdfplumber
    import pymupdf

    path = Path(document.get("resolved_path", document["path"]))
    from qa_agent.documents import verify_document_hash
    try:
        verify_document_hash(document)
    except ValueError as exc:
        raise DocumentError(str(exc), "document_hash_mismatch") from exc
    pages: list[dict] = []
    try:
        with pdfplumber.open(path) as pdf, pymupdf.open(path) as layout_pdf:
            if not pdf.pages:
                raise DocumentError("PDF 中没有可解析页面。", "empty_document")
            for number, page in enumerate(pdf.pages, start=1):
                # Keep lines/table cells in reading order; never merge physical pages.
                text = (page.extract_text(layout=False, x_tolerance=2, y_tolerance=3) or "").strip()
                words = page.extract_words(x_tolerance=2, y_tolerance=3) if text else []
                bbox = None
                if words:
                    bbox = [round(min(w["x0"] for w in words), 2),
                            round(min(w["top"] for w in words), 2),
                            round(max(w["x1"] for w in words), 2),
                            round(max(w["bottom"] for w in words), 2)]
                layout = layout_pdf[number - 1].get_text("dict", sort=True)
                blocks, heading_candidates = _attach_layout(text, layout)
                pages.append({"doc_id": document["doc_id"], "doc_title": document["title"],
                              "page": number, "text": text, "bbox": bbox,
                              "width": float(page.width), "height": float(page.height),
                              "blocks": blocks, "heading_candidates": heading_candidates,
                              "layout_parser": "PyMuPDF.get_text(dict)",
                              "coordinate_system": "PDF points; top-left origin"})
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f"文档 {document['doc_id']} PDF 解析失败：{type(exc).__name__}。", "pdf_parse_failed") from exc
    return pages
