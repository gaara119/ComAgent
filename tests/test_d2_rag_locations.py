"""Regression fixtures for physical PDF provenance, never benchmark labels."""
from hashlib import sha256
from io import BytesIO

from qa_agent.rag.parsers import parse_document
from qa_agent.rag.chunker import chunk_pages, is_heading_candidate


def registered(path):
    return {"doc_id": "geometry-fixture", "title": "Geometry fixture", "resolved_path": path,
            "path": str(path), "format": "pdf", "content_hash": sha256(path.read_bytes()).hexdigest()}


def test_cropbox_coordinates_match_visible_page(tmp_path):
    import pymupdf
    path = tmp_path / "cropped.pdf"
    document = pymupdf.open()
    page = document.new_page(width=600, height=800)
    page.insert_text((160, 260), "Actual source sentence about video editing.")
    page.set_cropbox(pymupdf.Rect(129, 219, 529, 719))
    document.save(path)
    parsed = parse_document(registered(path))
    chunk = next(c for c in chunk_pages(parsed) if "video editing" in c["text"])
    assert 30 <= chunk["bbox"][0] <= 32
    assert 25 < chunk["bbox"][1] < 50
    assert parsed[0]["width"] == 400 and parsed[0]["height"] == 500
    assert "visible CropBox" in chunk["coordinate_system"]


def test_parallel_columns_never_borrow_heading_or_bbox(tmp_path):
    import pymupdf
    path = tmp_path / "columns.pdf"
    document = pymupdf.open()
    page = document.new_page(width=600, height=800)
    page.insert_text((30, 100), "1. Quality rankings", fontname="hebo", fontsize=15)
    page.insert_text((330, 100), "2. Culture building", fontname="hebo", fontsize=15)
    page.insert_text((30, 140), "Quality programs were rated 71%.")
    page.insert_text((330, 140), "Culture programs had a different objective.")
    document.save(path)
    chunks = chunk_pages(parse_document(registered(path)))
    left = next(c for c in chunks if "71%" in c["text"])
    right = next(c for c in chunks if "different objective" in c["text"])
    assert left["section_path"] == ["1. Quality rankings"]
    assert right["section_path"] == ["2. Culture building"]
    assert left["bbox"][2] < 300 and right["bbox"][0] > 300
    assert all(not ("71%" in c["text"] and "different objective" in c["text"]) for c in chunks)


def test_scanned_page_uses_rendered_ocr_even_with_long_hidden_layer(tmp_path, monkeypatch):
    import pymupdf
    from PIL import Image
    import qa_agent.rag.parsers as module
    path = tmp_path / "scan.pdf"
    stream = BytesIO()
    Image.new("RGB", (400, 600), "white").save(stream, format="PNG")
    document = pymupdf.open()
    page = document.new_page(width=400, height=600)
    page.insert_image(page.rect, stream=stream.getvalue())
    page.insert_text((30, 100), "Long hidden OCR text whose geometry cannot be trusted.", render_mode=3)
    document.save(path)
    called = []
    def observed(image, **scales):
        called.append(scales)
        return "Observed rendered-page line.", [{"block_id": 0, "text": "Observed rendered-page line.",
                "bbox": [20, 30, 220, 40], "char_start": 0, "char_end": 28}], []
    monkeypatch.setattr(module, "_ocr_text", observed)
    parsed = parse_document(registered(path))
    assert called and parsed[0]["parser"] == "RapidOCR"
    assert "hidden OCR text" not in parsed[0]["text"]
    assert chunk_pages(parsed)[0]["bbox"] == [20, 30, 220, 40]


def test_procedural_step_is_not_a_section_heading():
    assert not is_heading_candidate("4 Follow the onscreen instructions.")
    assert is_heading_candidate("3.1.3 Results")
    assert not is_heading_candidate("To use Network Diagnostics:", require_pattern=False)


def test_cross_page_section_is_explicitly_unknown(tmp_path):
    import pymupdf
    path = tmp_path / "continuation.pdf"
    document = pymupdf.open()
    first = document.new_page()
    first.insert_text((30, 100), "3. Results", fontname="hebo", fontsize=18)
    first.insert_text((30, 140), "Results on this physical page.")
    second = document.new_page()
    second.insert_text((30, 100), "A continuation without an observed heading.")
    document.save(path)
    chunk = next(c for c in chunk_pages(parse_document(registered(path))) if c["page"] == 2)
    assert chunk["section_path"] == [] and chunk["section_location_status"] == "unknown"


def test_heading_and_body_in_same_native_block_do_not_contaminate_section(tmp_path):
    import pymupdf
    path = tmp_path / "mixed-heading.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((50,100),"3.1.3",fontname="hebo",fontsize=11)
    page.insert_text((90,100),"Results",fontname="hebo",fontsize=11)
    page.insert_text((50,113),"The proposed method improves these two datasets.",fontsize=11)
    document.save(path)
    chunk = next(c for c in chunk_pages(parse_document(registered(path))) if "improves" in c["text"])
    assert chunk["section_path"] == ["3.1.3 Results"]
    assert "proposed" not in chunk["section_path"][0]


def test_regular_trademark_span_does_not_hide_a_real_bold_heading(tmp_path):
    import pymupdf
    path = tmp_path / "mixed-emphasis.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((50, 70), "Previous device information", fontname="hebo", fontsize=11)
    page.insert_text((50, 100), "The previous device uses an external modem.", fontsize=11)
    page.insert_text((50, 140), "Efficiency", fontname="hebo", fontsize=11)
    page.insert_text((100, 140), "®", fontsize=7)
    page.insert_text((110, 140), " Compliance", fontname="hebo", fontsize=11)
    page.insert_text((50, 175), "This program promotes energy-efficient products.", fontsize=11)
    document.save(path)
    chunk = next(c for c in chunk_pages(parse_document(registered(path))) if "promotes" in c["text"])
    assert "Compliance" in chunk["section_path"][0]
    assert "Previous device" not in chunk["section_path"][0]


def test_local_procedure_label_does_not_label_later_independent_prose(tmp_path):
    import pymupdf
    path = tmp_path / "procedure-label.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((50, 100), "To use connection diagnostics:", fontname="hebo", fontsize=11)
    page.insert_text((50, 125), "1 Click the diagnostic button.", fontsize=11)
    page.insert_text((50, 220), "A router can share one IP address among computers.", fontsize=11)
    document.save(path)
    chunk = next(c for c in chunk_pages(parse_document(registered(path))) if "router" in c["text"])
    assert chunk["section_path"] == [] and chunk["section_location_status"] == "unknown"


def test_attribution_cannot_borrow_support_from_an_uncited_chunk():
    import pytest
    from qa_agent.rag.answer import CitationError, DocumentAnswer, validate_answer
    answer = DocumentAnswer(status="SUCCEEDED", answer="According to research from Alpha Group and Beta Institute, the capabilities are leadership and culture. [E2]", citation_ids=["E2"])
    chunks = [{"evidence_id":"E1","text":"Research from Alpha Group and Beta Institute identifies these capabilities."},
              {"evidence_id":"E2","text":"The capabilities are leadership and culture."}]
    with pytest.raises(CitationError,match="归属"):
        validate_answer(answer,chunks)


def test_explicit_attribution_passes_when_that_sentence_cites_its_source():
    from qa_agent.rag.answer import DocumentAnswer, validate_answer
    answer = DocumentAnswer(status="SUCCEEDED", answer="According to research from Alpha Group and Beta Institute, the capabilities are leadership and culture. [E1][E2]", citation_ids=["E1","E2"])
    chunks = [{"evidence_id":"E1","text":"Research from Alpha Group and Beta Institute identifies these capabilities."},
              {"evidence_id":"E2","text":"The capabilities are leadership and culture."}]
    assert len(validate_answer(answer,chunks)) == 2


def test_named_subject_identified_statement_also_requires_its_cited_source():
    import pytest
    from qa_agent.rag.answer import CitationError, DocumentAnswer, validate_answer
    answer = DocumentAnswer(status="SUCCEEDED", answer="Alpha Group and Beta Institute identified two capabilities: leadership and culture. [E2]", citation_ids=["E2"])
    chunks = [{"evidence_id":"E1","text":"Alpha Group and Beta Institute identified these capabilities."},
              {"evidence_id":"E2","text":"The capabilities are leadership and culture."}]
    with pytest.raises(CitationError,match="归属"):
        validate_answer(answer,chunks)
