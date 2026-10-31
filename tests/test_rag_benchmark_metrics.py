"""Public benchmark edge cases: labels, leakage, provenance and honest metrics."""
from copy import deepcopy
import csv
from hashlib import sha256
import json
import math

import pytest
from pydantic import ValidationError

from benchmarks.rag.dataset import Dataset, load_dataset, verify_sources
from benchmarks.rag.metrics import (
    answer_diagnostics, evidence_match, percentile, percentiles,
    retrieval_metrics, semantic_scores,
)


def label(id="e1", quote="Revenue was 45 million dollars.", **changes):
    return {"id": id, "doc_id": "source-a", "page": 2, "section_path": [],
            "quote": quote, "source_sha256": "a" * 64, **changes}


def chunk(text="Revenue was 45 million dollars.", **changes):
    return {"chunk_id": "c1", "doc_id": "source-a", "page": 2,
            "section_path": [], "text": text, "evidence_id": "E1", **changes}


def dataset(**changes):
    return {"version": "1", "title": "Testing sources", "corpus_manifest": "manifest.csv",
            "cases": [{"id": "q1", "split": "dev", "family_id": "revenue",
                       "category": "numeric", "question": "What was revenue?", "doc_ids": ["source-a"],
                       "answerable": True, "reference_answer": "45 million dollars.",
                       "required_evidence": [label()]}], **changes}


def test_dataset_forbids_unknown_fields_and_bool_page():
    bad = dataset();bad["cases"][0]["guess"] = "wrong"
    with pytest.raises(ValidationError):
        Dataset.model_validate(bad)
    bad = dataset();bad["cases"][0]["required_evidence"][0]["page"] = True
    with pytest.raises(ValidationError):
        Dataset.model_validate(bad)


@pytest.mark.parametrize("change", ["unknown_source", "duplicate_ids", "unknown_fact_evidence", "answerable_without_evidence", "unanswerable_with_evidence"])
def test_inconsistent_labels_rejected(change):
    raw = dataset();case = raw["cases"][0]
    if change == "unknown_source":case["doc_ids"] = ["other"]
    elif change == "duplicate_ids":raw["cases"].append(deepcopy(case))
    elif change == "unknown_fact_evidence":case["facts"] = [{"id": "f", "accepted_answers": ["45"], "evidence_ids": ["missing"]}]
    elif change == "answerable_without_evidence":case["required_evidence"] = []
    else:case["answerable"] = False
    with pytest.raises(ValidationError):
        Dataset.model_validate(raw)


@pytest.mark.parametrize("group", ["family_id", "session_id", "document"])
def test_cross_split_group_leakage_rejected(group):
    raw = dataset();dev = raw["cases"][0]
    test = deepcopy(dev);test.update(id="test-q", split="test", family_id="different-family")
    raw["cases"].append(test)
    if group == "family_id":test["family_id"] = dev["family_id"]
    elif group == "session_id":dev["session_id"] = test["session_id"] = "conversation-1"
    else:raw["split_group_policy"] = "document"
    with pytest.raises(ValidationError, match="Split leakage"):
        Dataset.model_validate(raw)


def test_dev_loader_never_returns_test_content_and_test_needs_explicit_opt_in(tmp_path):
    raw = dataset()
    test = deepcopy(raw["cases"][0]);test.update(id="test-q", split="test", family_id="different")
    raw["cases"].append(test)
    path = tmp_path / "dataset.json";path.write_text(json.dumps(raw), encoding="utf-8")
    assert [case.id for case in load_dataset(path).cases] == ["q1"]
    with pytest.raises(ValueError, match="allow_test"):
        load_dataset(path, split="test")
    assert [case.id for case in load_dataset(path, split="test", allow_test=True).cases] == ["test-q"]


def test_source_verification_checks_real_quote_locator_and_hash_without_approving(tmp_path):
    source = tmp_path / "data/guide.md";source.parent.mkdir()
    source.write_text("# Metrics\n\nRevenue was 45 million dollars.\n", encoding="utf-8")
    digest = sha256(source.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, ["doc_id", "title", "format", "path", "content_hash"])
        writer.writeheader();writer.writerow({"doc_id": "source-a", "title": "Guide", "format": "md",
                                             "path": "data/guide.md", "content_hash": digest})
    raw = dataset(corpus_manifest_sha256=sha256(manifest.read_bytes()).hexdigest())
    raw["cases"][0]["required_evidence"] = [label(page=None, section_path=["Metrics"], source_sha256=digest)]
    validated = Dataset.model_validate(raw)
    result = verify_sources(validated, tmp_path / "dataset.json", project_root=tmp_path)
    assert result["evidence_checks"][0]["quote_and_locator_verified"]
    assert validated.cases[0].review_status == "pending_human_review"
    validated.cases[0].required_evidence[0].section_path = ["Nonexistent"]
    with pytest.raises(ValueError, match="quote/locator"):
        verify_sources(validated, tmp_path / "dataset.json", project_root=tmp_path)
    source.write_text("A changed document", encoding="utf-8")
    with pytest.raises(ValueError, match="哈希"):
        verify_sources(Dataset.model_validate(raw), tmp_path / "dataset.json", project_root=tmp_path)


def test_manifest_version_change_is_rejected_before_source_read(tmp_path):
    path = tmp_path / "manifest.csv";path.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="manifest hash"):
        verify_sources(Dataset.model_validate(dataset(corpus_manifest_sha256="b" * 64)),
                       tmp_path / "dataset.json", project_root=tmp_path)


def test_pdf_evidence_uses_actual_physical_page_and_region_section(tmp_path):
    import pymupdf
    source = tmp_path / "data/guide.pdf";source.parent.mkdir()
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((40, 100), "Metrics", fontsize=20)
        page.insert_text((40, 135), "Revenue was 45 million dollars.", fontsize=11)
        pdf.save(source)
    digest = sha256(source.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, ["doc_id", "title", "format", "path", "content_hash"])
        writer.writeheader();writer.writerow({"doc_id": "source-a", "title": "PDF Guide", "format": "pdf",
                                             "path": "data/guide.pdf", "content_hash": digest})
    raw = dataset()
    raw["cases"][0]["required_evidence"] = [label(page=1, section_path=["Metrics"], source_sha256=digest)]
    validated = Dataset.model_validate(raw)
    result = verify_sources(validated, tmp_path / "dataset.json", project_root=tmp_path)
    assert result["evidence_checks"][0]["page"] == 1
    assert result["evidence_checks"][0]["section_path"] == ["Metrics"]
    validated.cases[0].required_evidence[0].page = 2
    with pytest.raises(ValueError, match="quote/locator"):
        verify_sources(validated, tmp_path / "dataset.json", project_root=tmp_path)


@pytest.mark.parametrize("changes", [{"doc_id": "other"}, {"page": 3}, {"page": True}, {"text": "Revenue was 145 million dollars."}])
def test_plausible_but_wrong_evidence_does_not_hit(changes):
    assert not evidence_match(chunk(**changes), label())


def test_same_page_only_is_not_a_hit_and_rank_two_is_half_mrr():
    actual = retrieval_metrics([chunk("Contact information"), chunk()], [label()], k=5)
    assert actual["recall@5"] == 1
    assert actual["mrr@5"] == .5
    assert actual["novelty_ndcg@5"] == pytest.approx(1 / math.log2(3))
    assert actual["ndcg@5"] is None  # IDCG needs all frozen allowed chunks.
    assert actual["rank_matches"][0]["evidence_ids"] == []


def test_duplicate_overlap_never_inflates_source_unit_gain():
    first, second = label(), label("e2", "Operating margin was 10%.")
    duplicate = chunk(chunk_id="duplicate-overlap")
    ranked = [chunk(), duplicate, chunk("Operating margin was 10%.", chunk_id="new")]
    metrics = retrieval_metrics(ranked, [first, second], 3)
    assert metrics["recall@3"] == 1
    assert metrics["novelty_precision@3"] == pytest.approx(2 / 3)
    assert metrics["precision@3"] == 1  # Three distinct, relevant chunk qrels.
    assert metrics["novelty_ndcg@3"] == pytest.approx((1 + 1 / math.log2(4)) / (1 + 1 / math.log2(3)))
    assert metrics["rank_matches"][1]["new_evidence_ids"] == []


def test_one_chunk_can_cover_multiple_evidence_units_without_unbounded_ndcg():
    corpus = [chunk("Revenue was 45 million dollars. Operating margin was 10%.")]
    actual = retrieval_metrics(corpus, [label(), label("e2", "Operating margin was 10%.")], corpus_chunks=corpus)
    assert actual["recall@5"] == 1
    assert actual["ndcg@5"] == 1


def test_standard_ndcg_has_independent_overlapping_qrels_and_no_duplicate_id_gain():
    original = chunk()
    overlap = chunk(chunk_id="overlap", text="Metrics: Revenue was 45 million dollars.")
    irrelevant = chunk("Contact information", chunk_id="contact")
    corpus = [original, overlap, irrelevant]
    complete = retrieval_metrics([original, overlap], [label()], corpus_chunks=corpus)
    assert complete["recall@5"] == 1 and complete["ndcg@5"] == 1
    duplicated = retrieval_metrics([original, original, overlap], [label()], corpus_chunks=corpus)
    assert duplicated["ndcg@5"] == pytest.approx((1 + .5) / (1 + 1 / math.log2(3)))
    assert duplicated["precision@5"] == pytest.approx(2 / 5)
    assert duplicated["novelty_precision@5"] == pytest.approx(1 / 5)
    assert duplicated["relevant_chunk_count"] == 2


def test_standard_ndcg_uses_all_qrels_not_only_returned_candidates():
    first = chunk()
    second = chunk("Revenue was 45 million dollars. Other details.", chunk_id="c2")
    actual = retrieval_metrics([first], [label()], corpus_chunks=[first, second])
    assert actual["ndcg@5"] == pytest.approx(1 / (1 + 1 / math.log2(3)))
    assert actual["recall@5"] == 1


def test_standard_qrels_reject_changed_predictions_or_unknown_chunk_ids():
    with pytest.raises(ValueError, match="absent"):
        retrieval_metrics([chunk(chunk_id="unknown")], [label()], corpus_chunks=[chunk()])
    with pytest.raises(ValueError, match="content differs"):
        retrieval_metrics([chunk("Different text under same ID")], [label()], corpus_chunks=[chunk()])


def test_empty_results_are_failure_but_unanswerable_not_in_retrieval_denominator():
    missing = retrieval_metrics([], [label()])
    assert missing["eligible"] is True and missing["recall@5"] == 0
    unknown = retrieval_metrics([chunk()], [])
    assert unknown["eligible"] is False and unknown["recall@5"] is None


def test_section_prefix_and_physical_locator_are_both_required():
    evidence = label(page=None, section_path=["Guide", "Metrics"])
    assert evidence_match(chunk(page=None, section_path=["Guide", "Metrics", "Notes"]), evidence)
    assert not evidence_match(chunk(page=None, section_path=["Guide", "Contacts"]), evidence)


def test_answer_numbers_and_valid_citation_do_not_imply_semantic_correctness():
    facts = [{"id": "f1", "accepted_answers": ["71"], "evidence_ids": ["e1"]}]
    result = answer_diagnostics("Revenue is 171 [E1]", ["E1"], [chunk()], facts, True, "SUCCEEDED")
    assert result["lexical_fact_coverage"] == 0
    assert result["citation_ids_valid"] is True
    assert result["semantic_answer_correctness"] is None
    assert result["semantic_citation_support"] is None
    assert result["semantic_review_status"] == "not_verified"


def test_invalid_ids_changed_quotes_and_refusal_status_are_independent():
    result = answer_diagnostics("Insufficient information [E99]", [chunk(text="Changed quote")],
                                [chunk()], [], False, "EMPTY_RESULT")
    assert result["citation_ids_valid"] is False
    assert result["citation_quotes_unchanged"] is False
    assert result["refusal_status"] is True
    assert result["refusal_surface_heuristic"] is True


def test_semantic_scores_require_explicit_review_and_keep_reviewer_identity():
    assert semantic_scores(None)["answer_correct"] is None
    with pytest.raises(ValueError, match="disclose"):
        semantic_scores({"answer_correct": 1})
    result = semantic_scores({"reviewer_type": "ai", "answer_correct": 1})
    assert result["review_status"] == "ai_reviewed"
    assert result["fact_support_rate"] is None
    with pytest.raises(ValueError, match="Invalid semantic"):
        semantic_scores({"reviewer_type": "human", "answer_correct": float("nan")})


def test_percentiles_use_declared_interpolation_and_missing_is_unknown():
    assert percentiles([10, 30]) == {"count": 2, "p50": 20.0, "p90": 28.0, "method": "linear_interpolation_(n-1)*p"}
    assert percentile([], 50) is None
    with pytest.raises(ValueError):percentile([float("inf")], 90)
    with pytest.raises(ValueError):percentile([True], 50)
