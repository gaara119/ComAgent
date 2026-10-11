"""Parse registered sources with physical PDF pages and honest section locators."""
from __future__ import annotations

from pathlib import Path
import re
from statistics import median
from functools import lru_cache

from qa_agent.rag.chunker import is_heading_candidate


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
        if (body_size and is_heading_candidate(block_text, require_pattern=False) and record["char_start"] is not None
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


def _native_regions(page) -> list[dict]:
    """Use the same text engine for source text and its physical rectangles.

    Rectangles are in the *visible CropBox*, in unrotated PDF points. A block
    is the smallest claimed layout region; we never union adjacent columns to
    make a paragraph. Headings are restricted to source typography and the
    same column on this physical page. Cross-page headings remain unknown.
    """
    layout = page.get_text("dict", sort=False)
    source = []
    for number, block in enumerate(layout.get("blocks", [])):
        if block.get("type") != 0:
            continue
        # PyMuPDF may group same-height lines from separate columns into one
        # block. Separate observed line starts before claiming its rectangle.
        groups = []
        for line in block.get("lines", []):
            if not any(s.get("text", "").strip() for s in line.get("spans", [])):
                continue
            x0 = float(line["bbox"][0])
            group = next((g for g in groups if abs(g[0]["bbox"][0]-x0) < page.rect.width*.10), None)
            if group is None:
                groups.append([line])
            else:
                group.append(line)
        for group_number, lines in enumerate(groups):
            text = "\n".join("".join(s.get("text", "") for s in line["spans"]) for line in lines).strip()
            spans = [s for line in lines for s in line["spans"] if s.get("text", "").strip()]
            boxes = [line["bbox"] for line in lines]
            source.append({"block_id": f"{number}-{group_number}", "text": text,
                           "bbox": [round(float(v), 2) for v in
                                    (min(b[0] for b in boxes), min(b[1] for b in boxes),
                                     max(b[2] for b in boxes), max(b[3] for b in boxes))],
                           "max_font_size": max((float(s.get("size", 0)) for s in spans), default=0),
                           "bold": bool(spans) and sum(bool(s.get("flags", 0) & 16) for s in spans) >= len(spans)/2,
                           "heading_lines": [{"text": "".join(s.get("text", "") for s in line["spans"]).strip(),
                                              # Superscript trademark/copyright marks may
                                              # use a regular face inside a real bold title.
                                              # Weight emphasis by observed text characters,
                                              # rather than requiring every span to be bold.
                                              "bold": sum(len(s.get("text", "").strip()) for s in line["spans"] if s.get("flags", 0) & 16)
                                              >= .9 * sum(len(s.get("text", "").strip()) for s in line["spans"]),
                                              "size": max((float(s.get("size", 0)) for s in line["spans"]),default=0)}
                                             for line in lines],
                           "sizes": [float(s.get("size", 0)) for s in spans]})
    body_size = median([size for b in source for size in b.pop("sizes")]) if source else 0
    headings = []
    for block in source:
        text, bbox = block["text"], block["bbox"]
        prefix = []
        for line in block.pop("heading_lines"):
            if line["bold"] or line["size"] >= body_size*1.18:
                prefix.append(line["text"])
            else:
                break
        # Scientific PDFs often put a section number, title and its first
        # paragraph in one source block. Only its emphasized leading lines can
        # name the section; the paragraph must never become part of the label.
        heading_text = " ".join(prefix) if prefix else text
        # A numbered instruction is prose, even when it appears on a line by
        # itself. A heading must have genuine emphasis and no sentence stop.
        structural = is_heading_candidate(heading_text)
        emphasized = block["max_font_size"] >= body_size*1.18 or (block["bold"] and structural)
        if (body_size and (emphasized or bool(prefix)) and is_heading_candidate(heading_text, require_pattern=False)
                and not re.search(r"[.!?。！？]\s*$", heading_text)
                and (bbox[1] > page.rect.height*.06 or structural)):
            headings.append({**block,"heading_text":heading_text})
    records = []
    for block in source:
        x0, y0, x1, _ = block["bbox"]
        # Restrict section inheritance to a heading that starts in this column
        # and actually precedes this block. Margin headings from another column
        # and preceding physical pages cannot label the source.
        possible = [h for h in headings if h["bbox"][1] <= y0+1
                    and abs(h["bbox"][0]-x0) <= page.rect.width*.08
                    and h["bbox"][2] <= x1+page.rect.width*.15]
        heading = max(possible, key=lambda h: h["bbox"][1]) if possible else None
        records.append({"text": block["text"], "record_id": f"native-block-{block['block_id']}",
                        "section_path": [heading["heading_text"]] if heading else [],
                        "section_location_status": "same_column_heading" if heading else "unknown",
                        "blocks": [{**block, "char_start": 0, "char_end": len(block["text"])}]})
    return records


def _scan_image_coverage(page) -> float:
    """Detect scanned pages even if they contain a long hidden OCR layer."""
    import pymupdf
    area = page.rect.get_area()
    return max(((pymupdf.Rect(item["bbox"]) & page.rect).get_area() / area
                for item in page.get_image_info() if item.get("bbox")), default=0.0) if area else 0.0


def parse_pdf(document: dict, *, rendered_ocr_cache: dict[int,dict] | None = None) -> list[dict]:
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
                if rendered_ocr_cache and number in rendered_ocr_cache:
                    # Offline ingestion supplies a source-hash/fingerprint
                    # checked cache. Runtime ingestion does not pass a cache.
                    pages.append(rendered_ocr_cache[number])
                    continue
                # Keep lines/table cells in reading order; never merge physical pages.
                text = (page.extract_text(layout=False, x_tolerance=2, y_tolerance=3) or "").strip()
                words = page.extract_words(x_tolerance=2, y_tolerance=3) if text else []
                bbox = None
                if words:
                    bbox = [round(min(w["x0"] for w in words), 2),
                            round(min(w["top"] for w in words), 2),
                            round(max(w["x1"] for w in words), 2),
                            round(max(w["bottom"] for w in words), 2)]
                physical = layout_pdf[number - 1]
                original_rotation = physical.rotation
                # The source contract uses unrotated physical PDF points. OCR
                # must render that same coordinate space before converting px.
                if original_rotation:
                    physical.set_rotation(0)
                # PyMuPDF gives coordinates relative to the visible CropBox;
                # pdfplumber's top/left offsets can instead include MediaBox.
                # Text and rectangles therefore come from one engine below.
                regions = _native_regions(physical)
                text = "\n\n".join(record["text"] for record in regions)
                blocks, heading_candidates = [], []
                warnings = []
                parser = "pdfplumber+PyMuPDF"
                # Blank covers are allowed. OCR only pages without a usable text
                # layer and with an actual raster image; no synthetic text.
                image_coverage = _scan_image_coverage(physical)
                if (len(text.strip()) < 30 and physical.get_images()) or image_coverage >= .80:
                    pixmap = physical.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                    import numpy as np
                    image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.width, pixmap.n)
                    text, blocks, warnings = _ocr_text(image, scale_x=physical.rect.width/pixmap.width,
                                                       scale_y=physical.rect.height/pixmap.height)
                    bbox = _union_bbox(blocks)
                    heading_candidates = []
                    parser = "RapidOCR"
                    # The observed OCR boxes correspond to the rendered page,
                    # whereas the old hidden layer has not been validated.
                    regions = [{"text": text, "blocks": blocks, "record_id": "rendered-ocr",
                                "section_path": [], "section_location_status": "unknown"}]
                    warnings.append("Rendered-page OCR used; hidden text-layer geometry is not trusted")
                else:
                    bbox = _union_bbox([b for region in regions for b in region["blocks"]])
                pages.append({"doc_id": document["doc_id"], "doc_title": document["title"],
                              "page": number, "text": text, "bbox": bbox,
                              "width": float(physical.rect.width), "height": float(physical.rect.height),
                              "blocks": blocks, "heading_candidates": heading_candidates,
                              "regions": regions, "raster_image_coverage": image_coverage,
                              "layout_parser": "PyMuPDF source blocks / rendered RapidOCR",
                              "parser": parser, "warnings": warnings,
                              "source_url": document.get("source_url", ""),
                              "rotation": original_rotation,
                              "cropbox": list(physical.cropbox), "mediabox": list(physical.mediabox),
                              "coordinate_system": "visible CropBox PDF points; top-left origin; unrotated"})
                if original_rotation:
                    physical.set_rotation(original_rotation)
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f"文档 {document['doc_id']} PDF 解析失败：{type(exc).__name__}。", "pdf_parse_failed") from exc
    return pages


@lru_cache(maxsize=1)
def _ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
        # The pinned 1.4.4 wheel includes its own detector/classifier/recognizer;
        # no implicit online model download is required during a user request.
        return RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
    except ImportError as exc:
        raise DocumentError("RapidOCR 未安装，扫描资料无法入库。", "ocr_unavailable") from exc


def _union_bbox(blocks: list[dict]):
    boxes = [b["bbox"] for b in blocks if b.get("bbox")]
    return [min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes)] if boxes else None


def _ocr_text(image, *, scale_x=1.0, scale_y=1.0) -> tuple[str, list[dict], list[str]]:
    try:
        output = _ocr_engine()(image)
        # Explicit legacy/current adapter, without confusing elapsed time with
        # records. The installed and audited version uses the first branch.
        if isinstance(output, tuple) and len(output) == 2:
            rows = output[0] or []
        elif hasattr(output, "boxes") and hasattr(output, "txts"):
            rows = zip(output.boxes, output.txts, output.scores)
        else:
            raise DocumentError("RapidOCR 返回接口不受支持。", "ocr_output_invalid")
        blocks, lines, warnings = [], [], []
        offset = 0
        for number, (box, text, confidence) in enumerate(rows):
            text = str(text).strip()
            if not text:
                continue
            coords = [[float(x)*scale_x, float(y)*scale_y] for x, y in box]
            bbox = [min(p[0] for p in coords), min(p[1] for p in coords),
                    max(p[0] for p in coords), max(p[1] for p in coords)]
            blocks.append({"block_id": number, "text": text, "bbox": bbox,
                           "char_start": offset, "char_end": offset+len(text),
                           "ocr_confidence": round(float(confidence), 6)})
            lines.append(text)
            offset += len(text)+1
            if float(confidence) < .80:
                warnings.append(f"OCR block {number} confidence={float(confidence):.3f}")
        if not lines:
            warnings.append("OCR produced no text")
        if hasattr(image, "shape") and blocks:
            # This is a geometry warning, not invented reading-order recovery.
            # Preserve the engine's raw block order; mixed columns must be
            # verified against their actual source boxes.
            starts = sorted(b["bbox"][0] for b in blocks)
            gap = float(image.shape[1])*scale_x*.10
            clusters = 1+sum(right-left > gap for left, right in zip(starts, starts[1:]))
            if clusters >= 2:
                warnings.append("Possible multi-column OCR: detector reading order may interleave columns; verify source boxes")
        return "\n".join(lines), blocks, warnings
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f"OCR 失败：{type(exc).__name__}。", "ocr_failed") from exc


def _verified_path(document: dict) -> Path:
    from qa_agent.documents import verify_document_hash
    try:
        verify_document_hash(document)
    except ValueError as exc:
        raise DocumentError(str(exc), "document_hash_mismatch") from exc
    return Path(document["resolved_path"])


def _section_records(document: dict, blocks: list[dict], parser: str) -> list[dict]:
    """Group contiguous blocks only within an unchanged section and locator."""
    groups = []
    for block in blocks:
        section = block.get("section_path", [])
        if not groups or groups[-1]["section_path"] != section:
            groups.append({"section_path": list(section), "blocks": []})
        groups[-1]["blocks"].append(block)
    records = []
    for order, group in enumerate(groups):
        source_blocks, parts, offset = [], [], 0
        for block in group["blocks"]:
            text = block["text"].strip()
            if not text:
                continue
            parts.append(text)
            source_blocks.append({**block, "char_start": offset, "char_end": offset+len(text)})
            offset += len(text)+1
        if parts:
            records.append({"doc_id": document["doc_id"], "doc_title": document["title"],
                            "page": None, "text": "\n".join(parts), "bbox": None,
                            "section_path": group["section_path"], "blocks": source_blocks,
                            "block_order": order, "record_id": f"section-{order}",
                            "parser": parser, "warnings": [],
                            "source_url": document.get("source_url", "")})
    return records


def _heading(path: list[str], text: str, level: int) -> list[str]:
    # Do not invent absent parent headings when source skips a heading level.
    return path[:max(0, level-1)]+[text.strip()]


def parse_docx(document: dict) -> list[dict]:
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    source = Document(_verified_path(document))
    blocks, path = [], []
    for order, child in enumerate(source.element.body.iterchildren()):
        if child.tag.endswith("}p"):
            paragraph = Paragraph(child, source)
            text = paragraph.text.strip()
            if not text:
                continue
            style = paragraph.style.name if paragraph.style else ""
            match = re.match(r"(?:Heading|标题)\s*(\d+)", style, re.I)
            if match:
                path = _heading(path, text, int(match.group(1)))
            blocks.append({"block_id": order, "text": text, "section_path": list(path),
                           "bbox": None, "style": style, "kind": "paragraph"})
        elif child.tag.endswith("}tbl"):
            table = Table(child, source)
            text = "\n".join(" | ".join(cell.text.strip() for cell in row.cells) for row in table.rows)
            if text.strip():
                blocks.append({"block_id": order, "text": text, "section_path": list(path),
                               "bbox": None, "kind": "table"})
    return _section_records(document, blocks, "python-docx")


def parse_html(document: dict) -> list[dict]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(_verified_path(document).read_text(encoding="utf-8-sig"), "html.parser")
    for node in soup.select("script,style,nav,header,footer,aside,noscript,form,[aria-hidden='true']"):
        node.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    blocks, path = [], []
    for order, node in enumerate(root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table", "pre"])):
        if node.find_parent(["table", "pre", "li"]) is not None:
            continue
        if node.name == "table":
            text = "\n".join(" | ".join(cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"]))
                             for row in node.find_all("tr"))
        else:
            text = node.get_text(" ", strip=True)
        if not text:
            continue
        if re.fullmatch(r"h[1-6]", node.name):
            path = _heading(path, text, int(node.name[1]))
        blocks.append({"block_id": order, "text": text, "section_path": list(path),
                       "bbox": None, "kind": node.name})
    return _section_records(document, blocks, "BeautifulSoup")


def parse_markdown(document: dict) -> list[dict]:
    text = _verified_path(document).read_text(encoding="utf-8-sig")
    blocks, path, pending, fenced, fence_marker = [], [], [], False, ""
    def flush():
        if pending:
            blocks.append({"block_id": len(blocks), "text": "\n".join(pending),
                           "section_path": list(path), "bbox": None,
                           "kind": "code" if fenced else "paragraph"})
            pending.clear()
    for line in text.splitlines():
        fence = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence and (not fenced or fence.group(1)[0] == fence_marker):
            flush()
            fenced = not fenced
            fence_marker = fence.group(1)[0] if fenced else ""
            pending.append(line)
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$", line) if not fenced else None
        if match:
            flush()
            path = _heading(path, match.group(2), len(match.group(1)))
            pending.append(line)
        elif not line.strip() and not fenced:
            flush()
        else:
            pending.append(line)
    flush()
    return _section_records(document, blocks, "markdown-headings")


def parse_png(document: dict) -> list[dict]:
    from PIL import Image
    import numpy as np
    path = _verified_path(document)
    with Image.open(path) as source:
        image = np.asarray(source.convert("RGB"))
        text, blocks, warnings = _ocr_text(image)
        return [{"doc_id": document["doc_id"], "doc_title": document["title"],
                 "page": None, "record_id": "image", "text": text, "blocks": blocks,
                 "bbox": _union_bbox(blocks), "section_path": ["图像 OCR"],
                 "width": source.width, "height": source.height, "parser": "RapidOCR",
                 "warnings": warnings, "coordinate_system": "image pixels; top-left origin",
                 "source_url": document.get("source_url", "")}]


def parse_document(document: dict) -> list[dict]:
    parsers = {"pdf": parse_pdf, "docx": parse_docx, "html": parse_html,
               "md": parse_markdown, "png": parse_png}
    try:
        parser = parsers[document["format"].lower()]
    except KeyError as exc:
        raise DocumentError("未知资料格式。", "format_unsupported") from exc
    try:
        return parser(document)
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError(f"文档 {document['doc_id']} 解析失败：{type(exc).__name__}。", "document_parse_failed") from exc
