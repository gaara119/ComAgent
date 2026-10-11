"""Check real D2 registration metadata without model calls or holdout prediction."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from eval.rag_dataset import load_dataset, reviewed

ROOT = Path(__file__).resolve().parents[1]


def test_d2_rag_preserves_original_official_gold_and_holdout_groups():
    originals = load_dataset(ROOT / "eval/datasets/rag_ohr.jsonl")
    current = load_dataset(ROOT / "eval/datasets/rag_single.jsonl")
    by_id = {item["id"]: item for item in current}
    # The core gold statement and original source identifiers must survive
    # extension. New annotations cannot rewrite a failed D1 question's answer.
    fields = ("question", "doc_id", "answer", "reference_text", "physical_pages",
              "split", "family_id", "source_qa_id", "source_qa_sha256", "source_sha256")
    for original in originals:
        assert all(by_id[original["id"]][key] == original[key] for key in fields)
        if original["split"] == "holdout":
            assert by_id[original["id"]]["exposure_history"]["model_prediction_count"] == 0


def test_d2_rag_total_and_insufficient_evidence_denominators():
    items = load_dataset(ROOT / "eval/datasets/rag_single.jsonl")
    assert len(items) == 30
    assert Counter(item["split"] for item in items) == {"dev": 21, "holdout": 9}
    assert Counter(item["source_type"] for item in items) == {"ohr_official": 20, "self_authored": 10}
    assert sum(not item["answerable"] for item in items) == 3
    assert sum(not item["answerable"] and item["split"] == "dev" for item in items) == 1
    assert sum(item["answerable"] and item["split"] == "dev" for item in items) == 20
    assert not any(reviewed(item) for item in items)
    assert all(item["source_scope"] == {"route": "doc", "doc_ids": [item["doc_id"]]} for item in items)


def test_d2_self_authored_questions_use_self_authored_sources_not_other_ohr():
    items = load_dataset(ROOT / "eval/datasets/rag_single.jsonl")
    assert all(not item["doc_id"].startswith("ohr-") for item in items if item["source_type"] == "self_authored")
    item = next(item for item in load_dataset(ROOT / "eval/datasets/rag_single.jsonl") if item["id"] == "rag-25")
    assert item["doc_id"] == "project-metric-manual"
    assert item["physical_pages"] == []
    assert "SUM(invoice_line.quantity)" in item["reference_text"]


def test_independent_scan_probe_preserves_real_boxes_without_inflating_rag30():
    item = json.loads((ROOT / "eval/artifacts/d2/source/ocr-e2e-case.json").read_text(encoding="utf8"))
    assert item["id"] == "e2e-ocr-endoscope-warranty"
    assert item["registered_suite"] == "independent_e2e_ocr_probe_not_counted_in_rag30"
    assert item["physical_pages"] == [2]
    assert item["evidence_source"] == "image_ocr"
    assert item["machine_verification"]["reading_order_warning"]
    evidence = item["gold_evidence"]
    assert len(evidence) == 2
    assert all(part["page"] == 2 and len(part["bbox"]) == 4 for part in evidence)
    assert evidence[0]["text"].endswith("2")
    assert evidence[1]["text"] == "yearminimumwarranty."
    assert abs(evidence[0]["bbox"][0] - evidence[1]["bbox"][0]) < 10


def test_d2_corpus_counts_independent_sources_instead_of_conversion_files():
    with (ROOT / "data/docs/manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        records = list(csv.DictReader(handle))
    assert len(records) == len({record["source_document_id"] for record in records}) == 13
    assert Counter(record["format"] for record in records) == {"pdf": 7, "html": 2, "docx": 2, "png": 1, "md": 1}
    assert Counter(record["language"] for record in records) == {"en": 7, "zh": 6}
    assert sum(record["format"] == "pdf" and record["is_derived"] == "true" for record in records) == 1
    for record in records:
        assert not Path(record["relative_path"]).is_absolute()
        assert record["relative_path"].startswith("data/docs/")
        assert record["content_hash"] == record["content_sha256"]
        assert record["license_note"] and record["source_url_or_dataset_id"]


def test_metric_approval_is_distinct_from_gold_review_and_runtime_d3_defaults():
    definitions = json.loads((ROOT / "data/rules/metric_definitions.json").read_text(encoding="utf8"))
    assert definitions["review_status"] == "approved"
    assert definitions["human_confirmation"]["method"] == "explicit_user_reply"
    assert definitions["runtime_defaults_enabled"] is False
    assert {metric["id"] for metric in definitions["metrics"]} == {
        "sales_revenue", "average_invoice_amount", "repeat_customer_count", "popular_tracks"}
    assert all(item["gold_review"]["status"] == "needs_human_review"
               for item in load_dataset(ROOT / "eval/datasets/rag_single.jsonl"))
