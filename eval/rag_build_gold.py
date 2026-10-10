"""Curate 20 official OHR text QA items and verify their original PDF pages."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/ohr"
DATASET = ROOT / "eval/datasets/rag_ohr.jsonl"

# Selection is frozen before running any model prediction. One question per
# document is held out; the single finance text QA is deliberately held out.
DOCUMENTS = [
    ("ohr-finance-amd-2022", "AMD 2022 Form 10-K", "finance/AMD_2022_10K"),
    ("ohr-law-affiliate", "Gulf South Medical Supply Affiliate Agreement (1997)",
     "law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT"),
    ("ohr-textbook-geology", "The Geology of the Country Around Holmfirth and Glossop (excerpt)",
     "textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04"),
    ("ohr-manual-macbook-air", "MacBook Air User Guide (archival edition)", "manual/Macbook_air"),
    ("ohr-news-executive-insight", "Executive Insight Healthcare Magazine (archival excerpt)",
     "news/DUDE_62ba680b413005aa9f018454c4ab4c43"),
    ("ohr-academic-label-words", "Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning",
     "academic/2305.14160v4"),
]
SELECTED = [
    # Finance 1, law 3, textbook 5, manual 5, news 3, academic 3.
    ("07d8ab49-76e2-44c4-b1a5-621012fdd312", "holdout"),
    ("2868c76b-7a94-4483-a8ce-122009b12bc9", "dev"),
    ("28805c5d-ad1b-4f60-89e4-dab20edc6d2b", "dev"),
    ("2866365a-fb4d-4ca6-b540-fe0246245efc", "holdout"),
    ("9c546b13-f581-4c4c-bdb3-784510aac204", "dev"),
    ("9c6725b2-7765-4a0a-95a6-ee8b3ced1be5", "dev"),
    ("9c7b49ee-0599-4b64-890a-58b48b8f0f0d", "dev"),
    ("9c6a4f19-6165-4ec6-b91d-55c727357c1d", "dev"),
    ("ecee26b3-1a3b-4354-aff7-6887110eb69f", "holdout"),
    ("3ff0b97a-a1f9-4f23-ae4e-8052329d0a1d", "dev"),
    ("401f8134-c3e5-4827-82bc-0550dfeddf7e", "dev"),
    ("406b40fe-fcde-40fe-bf9f-52c728a96c64", "dev"),
    ("410616bd-66bf-45f8-9cbe-3e7a74e0da1e", "dev"),
    ("40a2f403-fbb8-4582-b919-64532aff2792", "holdout"),
    ("864962b3-e99e-4364-a7da-a98e470a03a9", "dev"),
    ("864cce95-3e97-4b9e-a362-bc243927e72b", "dev"),
    ("86480bbe-9f76-49fa-a5a6-b8997f6bb6fb", "holdout"),
    ("5710c060-2ea2-4ca2-9fda-de0ea9b0a8ae", "dev"),
    ("571aa4f6-40a2-4015-8a40-a3799a1ab357", "dev"),
    ("57446b2d-ddb3-48ee-af8b-6cbeb759f3ec", "holdout"),
]


def alphanumeric(text: str) -> str:
    return "".join(char.lower() for char in text if char.isalnum())


def exact_pdf_quote(page_text: str, upstream_context: str) -> str:
    # Upstream context may contain Markdown/LaTeX and arbitrary whitespace. Use
    # it only to locate the span, then store the real unmodified PDF text span.
    normalized = alphanumeric(page_text)
    target = alphanumeric(upstream_context)
    start = normalized.find(target)
    if start < 0:
        raise ValueError("Official evidence is not present on its stated PDF page")
    positions = [index for index, char in enumerate(page_text) if char.isalnum()]
    return page_text[positions[start]:positions[start + len(target) - 1] + 1]


def main() -> None:
    from eval.rag_dataset import review_hash, reviewed, write_review_table

    questions = {item["ID"]: item for item in json.loads((RAW / "qas_v2.json").read_bytes())}
    source = json.loads((RAW / "qa_source.json").read_text(encoding="utf8"))
    downloads = {item["entry"].removesuffix(".pdf"): item
                 for item in json.loads((RAW / "download_records.json").read_text(encoding="utf8"))}
    docs = {doc_name: (doc_id, title) for doc_id, title, doc_name in DOCUMENTS}
    previous = ({item["id"]: item for item in (json.loads(line) for line in DATASET.read_text(encoding="utf8").splitlines() if line.strip())}
                if DATASET.exists() else {})
    readers, manifest, records = {}, [], []
    for doc_id, title, doc_name in DOCUMENTS:
        path = ROOT / "data/docs/raw" / (doc_name + ".pdf")
        reader = PdfReader(path)
        readers[doc_name] = reader
        download = downloads[doc_name]
        if hashlib.sha256(path.read_bytes()).hexdigest() != download["sha256"]:
            raise ValueError(f"PDF SHA256 mismatch: {doc_id}")
        domain = doc_name.split("/", 1)[0]
        manifest.append({"doc_id": doc_id, "title": title, "format": "pdf",
                         "source_url": download["source_url"],
                         "license": "HF card: CC-BY-4.0; upstream PDF statement: research only, non-commercial; original rights retained",
                         "content_hash": download["sha256"], "path": path.relative_to(ROOT).as_posix(),
                         "domain": domain, "language": "en", "derived_from": "",
                         "source_entry": download["entry"], "source_revision": download["source_revision"],
                         "page_count": str(len(reader.pages))})
    for number, (source_id, split) in enumerate(SELECTED, 1):
        question = questions[source_id]
        if question["evidence_source"] != "text" or not isinstance(question["evidence_page_no"], int):
            raise ValueError("D1 selection requires official single-page text evidence")
        doc_name = question["doc_name"]
        doc_id, title = docs[doc_name]
        page_index = question["evidence_page_no"]
        text = readers[doc_name].pages[page_index].extract_text() or ""
        context = question["evidence_context"]
        if not isinstance(context, str):
            raise ValueError("Expected a single official evidence context")
        quote = exact_pdf_quote(text, context)
        record = {
            "id": f"rag-{number:02}", "question": question["questions"],
            "doc_id": doc_id, "doc_title": title, "domain": question["doc_type"],
            "answer": question["answers"], "reference_text": quote,
            "physical_pages": [page_index + 1], "page_numbering": "physical_pdf_1_based",
            "evidence_source": "text", "answer_form": question["answer_form"],
            "split": split, "family_id": f"ohr-qa-{source_id}",
            "source_qa_id": source_id, "source_qa": question,
            "source_qa_url": source["qa_url"], "source_qa_sha256": source["qa_sha256"],
            "source_sha256": downloads[doc_name]["sha256"],
            "machine_verification": {"official_evidence_located_on_pdf_page": True,
                                     "reference_is_exact_pdf_substring": quote in text,
                                     "method": "pypdf original page text; alphanumeric span localization",
                                     "human_approval": False},
            "gold_review": {"status": "needs_human_review", "reviewer": None,
                            "reviewed_at_utc": None, "content_sha256": None},
        }
        record["gold_content_sha256"] = review_hash(record)
        old = previous.get(record["id"])
        if old and reviewed(old) and review_hash(old) == review_hash(record):
            record["gold_review"] = old["gold_review"]
        records.append(record)
    path = ROOT / "data/docs/manifest.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    DATASET.parent.mkdir(parents=True, exist_ok=True)
    DATASET.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf8")
    provenance = {"created_at_utc": datetime.now(timezone.utc).isoformat(), **source,
                  "selection": "20 original official text QA; no team-authored replacements",
                  "documents": manifest, "counts": {"all": 20, "dev": 14, "holdout": 6},
                  "domain_counts": {d: sum(x['domain'] == d for x in records)
                                    for d in ["finance", "law", "textbook", "manual", "news", "academic"]},
                  "dev_domain_note": "Five domains in dev; sole selected finance question is held out. All six in full dataset.",
                  "dataset_sha256": hashlib.sha256(DATASET.read_bytes()).hexdigest(),
                  "page_conversion": "official evidence_page_no is PDF index 0-based; physical_pages adds 1",
                  "human_review": "All pending; machine localization does not approve semantic gold",
                  "upstream_license_sources": ["https://huggingface.co/datasets/opendatalab/OHR-Bench", "https://github.com/opendatalab/OHR-Bench#copyright-statement"]}
    (ROOT / "eval/datasets/rag_ohr.manifest.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf8")
    (ROOT / "data/docs/source_manifest.json").write_text(json.dumps({**source, "downloads": list(downloads.values()),
        "download_method": "HTTP Range ZIP central directory + selected entry byte ranges; local CRC32 and SHA256 verified",
        "license_note": "HF metadata: CC-BY-4.0; GitHub PDF copyright statement additionally says research only/non-commercial; preserve original rights",
        "license_sources": provenance["upstream_license_sources"]}, ensure_ascii=False, indent=2), encoding="utf8")
    write_review_table(records)
    print(json.dumps({"documents": len(manifest), "questions": len(records), "dev": 14, "holdout": 6,
                      "verified_exact_pdf_substrings": sum(x['machine_verification']['reference_is_exact_pdf_substring'] for x in records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
