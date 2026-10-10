"""RAG safety/grounding tests. Fixtures are test-only, never benchmark evidence."""
from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from qa_agent.config import Settings
from qa_agent.rag.answer import CitationError, DocumentAnswer, answer_from_chunks, validate_answer
from qa_agent.rag.chunker import chunk_pages
from qa_agent.rag.index import build_index, load_index
from qa_agent.rag.parsers import DocumentError, _attach_layout
from qa_agent.rag.retriever import retrieve, tokenize
from qa_agent.rag.service import run_doc_qa
from qa_agent.schemas import IntentContract
from qa_agent.trace import TraceRecorder


def _page(doc_id, page, text):
    return {"doc_id": doc_id, "doc_title": doc_id, "page": page, "text": text, "bbox": [0, 0, 100, 100]}


@pytest.fixture
def indexed(tmp_path, monkeypatch):
    """Mock PDF parser only; actual manifest/hash/index persistence is exercised."""
    from qa_agent.documents import load_documents
    import qa_agent.rag.index as index_module
    docs = tmp_path / "data/docs"
    docs.mkdir(parents=True)
    rows = []
    for doc_id, text in [("hospital", "hospital annual revenue assets liabilities income report"),
                         ("aw", "adventureworks transaction customer bicycle orders secretvalue")]:
        path = docs / f"{doc_id}.pdf"
        path.write_bytes(f"parser fixture only: {text}".encode())
        rows.append({"doc_id": doc_id, "title": doc_id, "format": "pdf", "path": f"data/docs/{doc_id}.pdf",
                     "content_hash": hashlib.sha256(path.read_bytes()).hexdigest(), "language": "en"})
    manifest = docs / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    monkeypatch.setattr(index_module, "load_documents", lambda manifest_path: load_documents(manifest_path, tmp_path))
    monkeypatch.setattr(index_module, "parse_pdf", lambda document: [
        _page(document["doc_id"], 1, "hospital annual revenue assets income 1234" if document["doc_id"] == "hospital"
              else "adventureworks bicycle customer orders secretvalue 9876"),
        _page(document["doc_id"], 2, "hospital annual cash liabilities 5000" if document["doc_id"] == "hospital"
              else "adventureworks transaction supplier inventory 5678"),
        _page(document["doc_id"], 3, "support policy of the report"),
    ])
    # A fake encoder must not be treated as the runtime BGE model in these lexical tests.
    import sys
    from types import ModuleType
    embeddings = ModuleType("qa_agent.rag.embeddings")
    embeddings.get_embedder = lambda settings: None
    monkeypatch.setitem(sys.modules, "qa_agent.rag.embeddings", embeddings)
    settings = Settings(db_url="", rag_manifest_path=manifest, rag_index_path=tmp_path / "data/index",
                        rag_answer_mode="extractive", rag_top_k=5)
    metadata = build_index(settings=settings)
    return settings, metadata, rows, tmp_path


def test_chunks_never_merge_physical_pages_and_are_stable():
    pages = [_page("d", 1, "PAGE ONE\n" + "alpha paragraph " * 50), _page("d", 2, "PAGE TWO\n" + "beta paragraph " * 50)]
    first = chunk_pages(pages, 300, 30)
    assert first == chunk_pages(pages, 300, 30)
    assert len({c["chunk_id"] for c in first}) == len(first)
    assert all(not ("alpha" in c["text"] and "beta" in c["text"]) for c in first)
    assert {c["page"] for c in first} == {1, 2}
    assert all(c["bbox"] is None and c["page_bbox"] == [0, 0, 100, 100] for c in first)


def test_empty_pages_keep_original_page_number():
    chunks = chunk_pages([_page("d", 1, ""), _page("d", 2, "Available source text")])
    assert len(chunks) == 1 and chunks[0]["page"] == 2


def test_short_sentence_retains_comma_qualification_in_one_excerpt():
    introduction = "The background describes earlier experiments and their limitations. " * 7
    statement = "The method improves the measured outcomes, particularly for the small and noisy cohorts."
    source = introduction + statement + " Further work is required."
    chunks = chunk_pages([_page("d", 4, source)])
    assert any(statement in chunk["text"] for chunk in chunks)
    assert all(len(chunk["text"]) <= 600 for chunk in chunks)
    assert all(source[c["char_start"]:c["char_end"]] == c["text"] for c in chunks)


def test_wrapped_hyphenated_condition_keeps_source_spelling():
    introduction = "Prior observations explain the survey design and its scope. " * 8
    statement = "The respondents rated their categor-\nies as outstanding or at least satisfactory."
    source = introduction + statement + " A different population was also surveyed."
    chunks = chunk_pages([_page("d", 3, source)])
    assert any(statement in c["text"] for c in chunks)
    assert not any("categories" in c["text"] for c in chunks)


def test_overlong_sentence_is_disclosed_and_source_content_is_not_lost():
    source = "A prolonged explanation " + "must retain every original source word " * 30 + "."
    chunks = chunk_pages([_page("d", 2, source)])
    assert len(chunks) >= 2 and all(len(c["text"]) <= 600 for c in chunks)
    assert any(c["incomplete_sentence_end"] for c in chunks)
    assert any(c["incomplete_sentence_start"] for c in chunks[1:])
    covered = set()
    for c in chunks:
        assert source[c["char_start"]:c["char_end"]] == c["text"]
        covered.update(range(c["char_start"], c["char_end"]))
    assert all(i in covered for i, char in enumerate(source) if not char.isspace())


def test_complete_sentence_overlap_advances_without_duplicate_chunks():
    sentences = [f"Sentence {i} describes an independent source observation in a complete statement." for i in range(12)]
    source = " ".join(sentences)
    chunks = chunk_pages([_page("d", 1, source)], max_chars=300, overlap=80)
    assert any(c["overlap_chars"] > 0 for c in chunks[1:])
    assert all(c["text"].startswith("Sentence ") for c in chunks)
    assert all(c["text"].endswith(".") and len(c["text"]) <= 300 for c in chunks)
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
    assert all(a["char_end"] < b["char_end"] for a, b in zip(chunks, chunks[1:]))


def test_table_numeric_rows_are_whole_and_not_section_titles():
    rows = ["2024 2023 2022", "ICL (MODEL-X) 100.00 100.00 51.90", "Revenue 1200 1100 1000"]
    source = "Financial Overview\n" + "\n".join(rows * 10)
    chunks = chunk_pages([_page("d", 1, source)], max_chars=200, overlap=20)
    assert all(c["section_path"] == [] for c in chunks)
    for row in rows:
        assert any(row in c["text"] for c in chunks)
    assert all(c["boundary_end"] in {"table_line", "page_end"} for c in chunks)


def test_original_offsets_account_for_leading_source_whitespace():
    source = "  Actual evidence.  \n"
    page = {**_page("d", 1, source), "blocks": [{"block_id": 1, "bbox": [1, 2, 20, 30],
            "char_start": 2, "char_end": 18}]}
    c = chunk_pages([page])[0]
    assert c["text"] == "Actual evidence."
    assert source[c["char_start"]:c["char_end"]] == c["text"]
    assert c["char_start"] == 2 and c["bbox"] == [1, 2, 20, 30]


def _layout_block(text, bbox, size=10):
    return {"type": 0, "bbox": bbox, "lines": [{"spans": [{"text": text, "size": size}]}]}


def test_actual_blocks_map_whitespace_without_changing_original_text():
    original = "Revenue\n1,234 million\nOther source"
    layout = {"blocks": [_layout_block("Revenue 1,234 million", [10, 20, 200, 60]),
                          _layout_block("Other source", [10, 70, 200, 90])]}
    blocks, headings = _attach_layout(original, layout)
    assert original[blocks[0]["char_start"]:blocks[0]["char_end"]] == "Revenue\n1,234 million"
    page = {**_page("d", 1, original), "blocks": blocks, "heading_candidates": headings}
    chunks = chunk_pages([page])
    assert chunks[0]["text"] == original
    assert chunks[0]["bbox"] == [10, 20, 200, 90]
    assert chunks[0]["bbox_scope"] == "union_of_text_blocks"
    assert [b["block_id"] for b in chunks[0]["source_blocks"]] == [0, 1]


def test_ambiguous_layout_text_does_not_claim_coordinate_match():
    blocks, _ = _attach_layout("2022 revenue\n2022 assets", {"blocks": [_layout_block("2022", [10, 20, 50, 30])]})
    assert blocks[0]["char_start"] is None and blocks[0]["char_end"] is None
    page = {**_page("d", 1, "2022 revenue\n2022 assets"), "blocks": blocks}
    assert chunk_pages([page])[0]["bbox"] is None


def test_actual_font_heading_is_used_without_invented_section():
    text = "Financial Overview\nRevenue was 1234.\nAssets were 5000."
    layout = {"blocks": [_layout_block("Financial Overview", [10, 10, 200, 30], 20),
                          _layout_block("Revenue was 1234.", [10, 40, 200, 60], 10),
                          _layout_block("Assets were 5000.", [10, 70, 200, 90], 10)]}
    blocks, headings = _attach_layout(text, layout)
    assert headings == ["Financial Overview"]
    page = {**_page("d", 1, text), "blocks": blocks, "heading_candidates": headings}
    assert chunk_pages([page])[0]["section_path"] == ["Financial Overview"]


def test_large_font_data_rows_cannot_become_heading_candidates():
    data_row = "ICL (MODEL-X) 100.00 100.00 51.90"
    text = data_row + "\nA body paragraph.\nAnother body paragraph."
    layout = {"blocks": [_layout_block(data_row, [10, 10, 200, 30], 20),
                         _layout_block("A body paragraph.", [10, 40, 200, 60], 10),
                         _layout_block("Another body paragraph.", [10, 70, 200, 90], 10)]}
    blocks, headings = _attach_layout(text, layout)
    assert headings == []
    assert chunk_pages([{**_page("d", 1, text), "blocks": blocks, "heading_candidates": headings}])[0]["section_path"] == []


def test_chinese_retrieval_uses_real_jieba_words():
    assert "中华人民共和国" in tokenize("中华人民共和国")


def test_english_and_chinese_tokenization():
    tokens = tokenize("2023 revenue 1,234 liabilities 医院收入")
    assert {"2023", "revenue", "1234", "liability", "医院", "收入"}.issubset(tokens)


def test_index_persistence_and_provenance(indexed):
    settings, meta, _, _ = indexed
    chunks, read = load_index(settings=settings)
    assert read == meta
    assert meta["retrieval_method"] == "bm25" and not meta["dense_embedding"]["enabled"]
    assert len(chunks) == 6
    assert all(d["page_count"] == 3 for d in meta["documents"])


def test_retrieval_filters_other_document_before_scoring(indexed):
    settings, _, _, _ = indexed
    matches, meta = retrieve("annual revenue assets", "hospital", settings=settings)
    assert matches and all(c["doc_id"] == "hospital" for c in matches)
    assert meta["candidate_count"] == 3
    assert all("secretvalue" not in c["text"] for c in matches)
    other, _ = retrieve("bicycle customer", "hospital", settings=settings)
    assert other == []


def test_unknown_document_is_not_indexed(indexed):
    settings, _, _, _ = indexed
    with pytest.raises(DocumentError) as error:
        retrieve("report", "missing", settings=settings)
    assert error.value.code == "document_not_indexed"


def test_modified_source_rejected_before_retrieval(indexed):
    settings, _, _, root = indexed
    (root / "data/docs/hospital.pdf").write_bytes(b"changed")
    with pytest.raises(DocumentError) as error:
        retrieve("annual", "hospital", settings=settings)
    assert error.value.code == "document_hash_mismatch"


def test_modified_chunks_rejected(indexed):
    settings, _, _, _ = indexed
    path = settings.rag_index_path / "chunks.jsonl"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(DocumentError) as error:
        load_index(settings=settings)
    assert error.value.code == "rag_index_corrupt"


def test_modified_manifest_rejected(indexed):
    settings, _, _, _ = indexed
    settings.rag_manifest_path.write_bytes(settings.rag_manifest_path.read_bytes() + b"\n")
    with pytest.raises(DocumentError) as error:
        load_index(settings=settings)
    assert error.value.code == "rag_index_stale"


def test_real_dense_interface_fuses_only_selected_document(indexed, monkeypatch):
    """A deterministic test encoder checks isolation; it is never runtime BGE data."""
    import numpy as np
    import sys
    embeddings = sys.modules["qa_agent.rag.embeddings"]
    settings, _, _, _ = indexed
    class TestEncoder:
        def encode(self, texts):
            return np.asarray([[1, 0] if "hospital" in text else [0, 1] for text in texts], dtype=np.float32)
        def metadata(self):
            return {"model_id": "test-only", "model_sha256": "test-only", "model_revision": "fixture"}
    monkeypatch.setattr(embeddings, "get_embedder", lambda settings: TestEncoder())
    meta = build_index(settings=settings)
    assert meta["dense_embedding"]["enabled"]
    matches, retrieved = retrieve("hospital revenue", "hospital", settings=settings)
    assert retrieved["dense_enabled"] and retrieved["retrieval_method"] == "bm25+bge-m3_dense_rrf"
    assert all(c["doc_id"] == "hospital" for c in matches)
    assert all("dense_score" in c for c in matches)


def test_dense_artifact_hash_is_checked(indexed, monkeypatch):
    import numpy as np
    import sys
    embeddings = sys.modules["qa_agent.rag.embeddings"]
    settings, _, _, _ = indexed
    class Encoder:
        def encode(self, texts):
            return np.asarray([[1.0, 0.0]] * len(texts), dtype=np.float32)
    monkeypatch.setattr(embeddings, "get_embedder", lambda settings: Encoder())
    build_index(settings=settings)
    path = settings.rag_index_path / "embeddings.npy"
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(DocumentError) as error:
        retrieve("hospital", "hospital", settings=settings)
    assert error.value.code == "rag_index_corrupt"


def test_dense_encoder_model_mismatch_is_rejected(indexed, monkeypatch):
    import numpy as np
    import sys
    embeddings = sys.modules["qa_agent.rag.embeddings"]
    settings, _, _, _ = indexed
    class Encoder:
        def __init__(self, model_id):
            self.model_id = model_id
        def encode(self, texts):
            return np.asarray([[1.0, 0.0]] * len(texts), dtype=np.float32)
        def metadata(self):
            return {"model_id": self.model_id}
    monkeypatch.setattr(embeddings, "get_embedder", lambda settings: Encoder("indexed-model"))
    build_index(settings=settings)
    monkeypatch.setattr(embeddings, "get_embedder", lambda settings: Encoder("changed-model"))
    with pytest.raises(DocumentError) as error:
        retrieve("hospital", "hospital", settings=settings)
    assert error.value.code == "embedding_model_mismatch"


def _evidence():
    return {"evidence_id": "E1", "doc_id": "d", "doc_title": "Title", "page": 7,
            "section_path": [], "text": "Revenue 1234", "bbox": None}


@pytest.mark.parametrize("answer,ids", [
    ("Revenue 1234", ["E1"]), ("Revenue 1234 [E2]", ["E2"]),
    ("Revenue 1234 [E1]", ["E1", "E1"]), ("Revenue 1234 [E1] [E2]", ["E1"]),
    ("Revenue 1234", []),
])
def test_invalid_citations_fail_instead_of_success(answer, ids):
    with pytest.raises(CitationError):
        validate_answer(DocumentAnswer(status="SUCCEEDED", answer=answer, citation_ids=ids), [_evidence()])


def test_empty_result_cannot_claim_cited_success():
    with pytest.raises(CitationError):
        validate_answer(DocumentAnswer(status="EMPTY_RESULT", answer="missing [E1]", citation_ids=["E1"]), [_evidence()])


def test_used_evidence_subset_only():
    second = {**_evidence(), "evidence_id": "E2", "page": 8, "text": "unrelated"}
    used = validate_answer(DocumentAnswer(status="SUCCEEDED", answer="1234 [E1]", citation_ids=["E1"]), [_evidence(), second])
    assert len(used) == 1 and used[0]["page"] == 7


def test_extractive_explicitly_does_not_call_llm():
    class NoCalls:
        def complete_json(self, *args):
            raise AssertionError("extractive must not invoke model")
    answer, used = answer_from_chunks("revenue?", [_evidence()], NoCalls(), TraceRecorder(), mode="extractive")
    assert answer.status == "SUCCEEDED" and "extractive" in answer.answer and used[0]["page"] == 7


def test_retrieved_text_does_not_force_answer():
    class Insufficient:
        def complete_json(self, *args):
            return DocumentAnswer(status="EMPTY_RESULT", answer="所给片段没有支持所问年度。")
    answer, used = answer_from_chunks("2022 revenue?", [_evidence()], Insufficient(), TraceRecorder())
    assert answer.status == "EMPTY_RESULT" and used == []


def test_service_preserves_actual_failure_code(indexed, monkeypatch):
    import qa_agent.rag.service as module
    from qa_agent.llm import LLMError
    from qa_agent.documents import load_documents
    settings, _, _, root = indexed
    monkeypatch.setattr(module, "get_settings", lambda: replace(settings, rag_answer_mode="llm"))
    monkeypatch.setattr(module, "load_documents", lambda manifest_path: load_documents(manifest_path, root))
    class Failed:
        def __init__(self, settings):
            pass
        def complete_json(self, *args):
            raise LLMError("认证失败", "llm_auth")
    monkeypatch.setattr(module, "JsonLLM", Failed)
    result = run_doc_qa(question="hospital revenue", doc_id="hospital", trace_id="test-real-code",
                        intent=IntentContract(route="doc"))
    assert result.status == "FAILED" and result.error.code == "llm_auth"
    assert any(step.name == "doc_answer" and step.status == "error" for step in result.steps)


def test_service_returns_only_matching_page_evidence(indexed, monkeypatch):
    import qa_agent.rag.service as module
    from qa_agent.documents import load_documents
    settings, _, _, root = indexed
    monkeypatch.setattr(module, "get_settings", lambda: replace(settings, rag_answer_mode="llm"))
    monkeypatch.setattr(module, "load_documents", lambda manifest_path: load_documents(manifest_path, root))
    class Answerer:
        def __init__(self, settings):
            pass
        def complete_json(self, system, user, response_model, trace):
            evidence = json.loads(user)["evidence"]
            assert all(c["doc_id"] == "hospital" for c in evidence)
            return DocumentAnswer(status="SUCCEEDED", answer="Revenue 1234 [E1]", citation_ids=["E1"])
    monkeypatch.setattr(module, "JsonLLM", Answerer)
    result = run_doc_qa(question="hospital annual revenue assets", doc_id="hospital", trace_id="test-evidence",
                        intent=IntentContract(route="doc"))
    assert result.status == "SUCCEEDED" and len(result.evidences) == 1
    assert result.evidences[0].doc_id == "hospital" and result.evidences[0].page == 1
    assert result.trace_id == "test-evidence"
