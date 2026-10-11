"""Register D2 RAG 20 official + 10 self-authored cases without model calls.

D1 questions, IDs, groups and holdout exposure are preserved. All new gold
annotations remain pending human review. OCR quotes must already exist in
actual parser audit records rather than be copied from the native original.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eval.rag_dataset import load_dataset, review_hash
from qa_agent.rag.parsers import load_documents, parse_document


SELF_CASES = [
    ("rag-21", "artist-iron-maiden", "dev", "根据这份简介，Iron Maiden 是哪一年在什么地方组建的？", "1975年，英国伦敦东部的 Leyton。", "1975年在伦敦东部的 Leyton 组建。", True),
    ("rag-22", "artist-u2", "dev", "只根据 U2 简介，U2 于哪一年在哪座城市成立？", "1976年在都柏林成立。", "于1976年在都柏林成立。", True),
    ("rag-23", "artist-metallica", "holdout", "根据这份 DOCX 介绍，Metallica 于哪一年在哪座城市由哪两位成员组建？", "1981年在洛杉矶，由 James Hetfield 和 Lars Ulrich 组建。", "1981年在洛杉矶由主唱兼吉他手 James Hetfield 和鼓手 Lars Ulrich 组建。", True),
    ("rag-24", "artist-led-zeppelin", "dev", "根据这张简介图片，Led Zeppelin 于哪一年在哪座城市成立？", "1968年在伦敦成立。", "1968年在伦敦成立。", True),
    ("rag-25", "project-metric-manual", "dev", "根据口径手册，曲目最受欢迎的默认口径是什么，对应哪个汇总表达式？", "默认按购买数量，使用 SUM(invoice_line.quantity)；销售额与歌单收录数是明确的备选口径。", "曲目最受欢迎沿用总计划的购买数量默认，即 SUM(invoice_line.quantity)。", True),
    ("rag-26", "project-metric-manual", "dev", "按口径手册，客单价的主口径全名是什么，对应哪个 SQL 表达式？", "平均每张发票金额，AVG(invoice.total)。", "本项目将客单价主口径写全为平均每张发票金额，表达式 AVG(invoice.total)，每张发票权重相同。", True),
    ("rag-27", "project-chinook-dictionary", "dev", "根据中文数据字典，customer.country 和 invoice.billing_country 分别表示什么？", "customer.country 是客户所在地国家；invoice.billing_country 是发票账单地址国家，两个业务含义应分别保留。", "customer.country 表示客户所在地国家。invoice.billing_country 表示发票账单地址国家。", True),
    ("rag-28", "artist-iron-maiden", "dev", "只依据这份 Iron Maiden 简介，列出该乐队2026年在中国每场演出的门票收入。", "当前指定简介不包含所问的逐场中国演出票务收入，证据不足，应明确说明不能据此回答。", "", False),
    ("rag-29", "artist-u2", "holdout", "只依据这份 U2 简介，说明该乐队2027年巡演合同里的违约金具体金额。", "当前指定简介不包含未来巡演合同及违约金条款，证据不足。", "", False),
    ("rag-30", "project-chinook-dictionary", "holdout", "只依据这份数据字典，customer_id 等于1的客户最喜欢哪首歌？", "字段字典没有该客户的音乐偏好事实，不能据此回答。", "", False),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="eval/datasets/rag_single.jsonl")
    args = parser.parse_args()
    old_path = ROOT / "eval/datasets/rag_ohr.jsonl"
    old = load_dataset(old_path)
    if len(old) != 20 or Counter(item["split"] for item in old) != {"dev": 14, "holdout": 6}:
        raise ValueError("Actual D1 RAG split changed; exposure audit required before preparing D2")
    documents = {doc["doc_id"]: doc for doc in load_documents()}
    d1_responses_path = ROOT / "eval/reports/d1-acceptance/rag-dev/responses.jsonl"
    known_predictions = Counter(row["id"] for row in (json.loads(line) for line in d1_responses_path.read_text(encoding="utf8").splitlines()) )
    items = []
    for original in old:
        item = dict(original)
        item.update(case_id=item["id"], source_type="ohr_official", answerable=True,
                    expected_status="SUCCEEDED", source_scope={"route": "doc", "doc_ids": [item["doc_id"]]},
                    gold_evidence=[{"doc_id": item["doc_id"], "page": page, "text": item["reference_text"], "section_path": []}
                                   for page in item["physical_pages"]],
                    exposure_history={"prior_stage": "D1", "model_prediction_count": known_predictions[item["id"]],
                                      "count_scope": "known D1 acceptance run only; other development/probe runs are not inferred",
                                      "evidence_path": d1_responses_path.relative_to(ROOT).as_posix(),
                                      "classification": "existing_development_exposed" if item["split"] == "dev" else "untouched_holdout",
                                      "note": "D1 actual run included only 14 development IDs; six holdout IDs remain unpredicted"})
        item["gold_content_sha256"] = review_hash(item)
        items.append(item)
    parse_cache = {}
    quote_audit = []
    for case_id, doc_id, split, question, answer, quote, answerable in SELF_CASES:
        document = documents[doc_id]
        records = parse_cache.setdefault(doc_id, parse_document(document) if doc_id not in parse_cache else parse_cache[doc_id])
        matched = next((record for record in records if quote and quote in record["text"]), None)
        if answerable and matched is None:
            raise ValueError(f"Gold quote for {case_id} is not an exact substring of actual parsed source")
        pages = [matched["page"]] if matched and matched.get("page") is not None else []
        evidence = [{"doc_id": doc_id, "page": matched.get("page"), "text": quote,
                     "section_path": matched.get("section_path", []), "source_parser": matched.get("parser")}] if matched else []
        if doc_id == "ohr-manual-endoscope-scan":
            # Adjacent OCR boxes in the same physical column jointly state the
            # warranty. Keep both genuine strings/boxes instead of presenting
            # their concatenation as a contiguous recorded page substring.
            warranty_lines = ("InnoViewGMBHEndoscopes comewitha2", "yearminimumwarranty.")
            warranty_blocks = [next(block for block in matched["blocks"] if block["text"] == line)
                               for line in warranty_lines]
            evidence = [{"doc_id": doc_id, "page": 2, "text": block["text"], "section_path": [],
                         "source_parser": "RapidOCR", "bbox": block["bbox"], "ocr_confidence": block["ocr_confidence"]}
                        for block in warranty_blocks]
        item = {"id": case_id, "case_id": case_id, "family_id": "self-d2-" + case_id,
                "question": question, "doc_id": doc_id, "doc_title": document["title"],
                "domain": document["domain"], "answer": answer, "reference_text": quote,
                "physical_pages": pages, "page_numbering": "physical_pdf_1_based",
                "evidence_source": "image_ocr" if document["format"] in {"png"} or doc_id.endswith("-scan") else "text",
                "answer_form": "Free-form", "split": split, "source_qa_id": None,
                "source_type": "self_authored", "answerable": answerable,
                "expected_status": "SUCCEEDED" if answerable else "EMPTY_RESULT",
                "acceptable_insufficient_statuses": ["EMPTY_RESULT", "UNSUPPORTED"] if not answerable else [],
                "source_scope": {"route": "doc", "doc_ids": [doc_id]},
                "gold_evidence": evidence, "expected_facts": [answer],
                "source_url": document["source_url"], "source_sha256": document["content_hash"],
                "source_document_id": document.get("source_document_id", doc_id),
                "source_group": document.get("source_document_id", doc_id),
                "machine_verification": {"reference_is_exact_parser_substring": bool(matched),
                                         "source_hash_verified": True, "parser": matched.get("parser") if matched else None,
                                         "human_approval": False,
                                         "reading_order_warning": "Actual four-column OCR interleaves lines from neighbouring columns; gold keeps the exact recorded span. Warranty lines must be visually reviewed using their real boxes on PDF page 2." if doc_id.endswith("-scan") else None,
                                         "insufficient_evidence_reason": answer if not answerable else None},
                "gold_review": {"status": "needs_human_review", "reviewer": None, "reviewed_at_utc": None, "content_sha256": None},
                "exposure_history": {"prior_stage": None, "model_prediction_count": 0,
                                     "classification": "new_development" if split == "dev" else "new_untouched_holdout"}}
        item["gold_content_sha256"] = review_hash(item)
        items.append(item)
        quote_audit.append({"id": case_id, "doc_id": doc_id, "split": split, "answerable": answerable,
                            "actual_quote_match": bool(matched), "physical_pages": pages, "gold_evidence": evidence,
                            "semantic_gold_review": "pending_human_review"})
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf8")
    checked = load_dataset(output)
    split_counts = dict(Counter(item["split"] for item in checked))
    manifest = {"prepared_at_utc": datetime.now(timezone.utc).isoformat(), "source": "D1 unchanged OHR20 plus D2 self-authored10",
                "dataset_path": output.relative_to(ROOT).as_posix(), "dataset_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "d1_source_path": old_path.relative_to(ROOT).as_posix(), "d1_source_sha256": hashlib.sha256(old_path.read_bytes()).hexdigest(),
                "total": len(checked), "official_ohr": 20, "self_authored": 10, "splits": split_counts,
                "self_authored_document_source_check": all(not item["doc_id"].startswith("ohr-") for item in checked if item["source_type"] == "self_authored"),
                "insufficient_evidence_total": sum(not item["answerable"] for item in checked),
                "insufficient_evidence_dev": sum(not item["answerable"] and item["split"] == "dev" for item in checked),
                "existing_d1_holdout_preserved": [item["id"] for item in old if item["split"] == "holdout"],
                "new_holdout_ids": [item["id"] for item in checked if item["source_type"] == "self_authored" and item["split"] == "holdout"],
                "model_calls_during_preparation": 0, "human_accepted": 0, "human_pending": len(checked),
                "holdout_model_predictions": 0, "holdout_run_schedule": "D5 after freeze",
                "document_level_independence": "Not claimed: same source document may have independent development/holdout questions. D1 official questions share sources; this is question-family grouping, not cross-document generalization."}
    (output.parent / "rag_single.manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    audit_path = ROOT / "eval/artifacts/d2/source/rag-gold-source-audit.json"
    audit_path.write_text(json.dumps({"model_calls": 0, "quote_audit": quote_audit}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    review_dir = ROOT / "eval/datasets/review_d2"
    review_dir.mkdir(parents=True, exist_ok=True)
    fields = ["id", "split", "question", "doc_id", "answerable", "answer", "reference_text", "physical_pages", "review_status", "reviewer", "reviewed_at_utc"]
    with (review_dir / "rag_gold_review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for item in checked:
            writer.writerow({**{key: item[key] for key in fields[:8]}, "review_status": "needs_human_review", "reviewer": "", "reviewed_at_utc": ""})
    lines = ["# D2 RAG 三十题人工审核表", "", "OHR20题保持原D1分组；新增10题含3道证据不足题。开发21题、保留9题，D2不运行保留集。机器仅核对字串来源；题意、期望答案及忠实度全部待人工审核。", "", "保留题如需避免提前审题，统一安排D5解封后审核；本表不代表已经运行保留题。", ""]
    for item in checked:
        lines += [f"## {item['id']} {item['split']}", "", "审核状态：待人工审核。", "", "问题：" + item["question"], "", "文档：" + item["doc_title"] + "；可回答：" + str(item["answerable"]) + "；物理PDF页：" + str(item["physical_pages"]) + "。", "", "期望：" + item["answer"], "", "```text", item["reference_text"] or "无gold事实片段；应说明当前文档证据不足。", "```", "", "- [ ] 题意与范围正确。", "- [ ] 已核对原文、页码或章节、答案要点与证据不足判断。", "- [ ] 实际模型开发集回答的每个事实均被其引用支持（实跑完成后审核）。", ""]
    (review_dir / "rag_gold_review.md").write_text("\n".join(lines), encoding="utf8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
