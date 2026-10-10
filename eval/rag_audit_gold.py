"""Audit the official QA selection against immutable local original PDFs."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

from eval.rag_dataset import ROOT, DEFAULT_DATASET, load_dataset, reviewed


def main() -> None:
    dataset = load_dataset()
    source = ROOT / "data/raw/ohr/qas_v2.json"
    qa_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    upstream = {item['ID']: item for item in json.loads(source.read_bytes())}
    with (ROOT / 'data/docs/manifest.csv').open(encoding='utf8', newline='') as file:
        docs = {item['doc_id']: item for item in csv.DictReader(file)}
    readers = {}
    checks = []
    for item in dataset:
        doc = docs[item['doc_id']]
        path = (ROOT / doc['path']).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Original PDF is outside the project')
        if item['doc_id'] not in readers:
            readers[item['doc_id']] = PdfReader(path)
        original = upstream[item['source_qa_id']]
        page_index = original['evidence_page_no']
        text = readers[item['doc_id']].pages[page_index].extract_text() or ''
        facts = {'id': item['id'], 'doc_id': item['doc_id'], 'split': item['split'],
                 'source_qa_id': item['source_qa_id'], 'physical_page': page_index + 1,
                 'question_identical_to_official': item['question'] == original['questions'],
                 'answer_identical_to_official': item['answer'] == original['answers'],
                 'embedded_source_qa_identical_to_official': item['source_qa'] == original,
                 'source_qa_sha256_matches': item['source_qa_sha256'] == qa_hash,
                 'source_pdf_sha256_matches': item['source_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest() == doc['content_hash'],
                 'official_evidence_source_text': original['evidence_source'] == 'text',
                 'physical_page_converted_from_official_index': item['physical_pages'] == [page_index + 1],
                 'reference_is_exact_original_pdf_substring': item['reference_text'] in text,
                 'human_accepted': reviewed(item), 'semantic_gold_review': 'needs_human_review'}
        checks.append(facts)
    boolean_keys = [key for key, value in checks[0].items() if isinstance(value, bool) and key != 'human_accepted']
    report = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'dataset_sha256': hashlib.sha256(DEFAULT_DATASET.read_bytes()).hexdigest(),
              'qa_sha256': qa_hash, 'question_count': len(checks),
              'all_source_and_page_checks_passed': all(all(row[key] for key in boolean_keys) for row in checks),
              'human_accepted_count': sum(row['human_accepted'] for row in checks),
              'holdout_prediction_count': 0,
              'method': 'independent original QA byte hash and original PDF page text; no model calls',
              'semantic_review': 'Not performed by this audit; human reviewer must inspect meaning and layout',
              'checks': checks}
    target = ROOT / 'eval/datasets/rag_machine_audit.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    lines = ['# D1 RAG 官方题库机器溯源核验', '',
             '本文件记录机器完成的来源与页码核验，不签署人工业务审核，不声明模型回答准确率。', '',
             f"核验 {len(checks)} 个官方 text QA；全部来源与原页检查通过：{report['all_source_and_page_checks_passed']}。",
             f"人工接受：{report['human_accepted_count']}；本核验模型调用：0；保留题预测：0。", '',
             '检查项：原官方问题/答案/QA记录一致、官方QA整文件SHA一致、原PDF SHA一致、text类型、物理页=官方index+1、引用为原PDF页连续子串。', '',
             '| 题号 | 文档 | split | 物理页 | 来源及页核验 | 人工审核 |', '|---|---|---|---:|---|---|']
    for row in checks:
        valid = all(row[key] for key in boolean_keys)
        lines.append(f"| {row['id']} | {row['doc_id']} | {row['split']} | {row['physical_page']} | {'通过' if valid else '需检查'} | {'已接受' if row['human_accepted'] else '待人工'} |")
    lines += ['', '完整哈希与逐题布尔检查见 rag_machine_audit.json；人工审核表见 rag_review/rag_gold_review.md。', '']
    (ROOT / 'eval/datasets/rag_machine_audit.md').write_text('\n'.join(lines), encoding='utf8')
    print(json.dumps({key: report[key] for key in ['question_count', 'all_source_and_page_checks_passed', 'human_accepted_count']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
