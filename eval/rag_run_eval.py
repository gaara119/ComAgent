"""Run the actual shared API on RAG dev QA and export honest evidence checks."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

import httpx
from pypdf import PdfReader

from eval.rag_dataset import DEFAULT_DATASET, ROOT, load_dataset, require_run_permission, reviewed
from eval.rag_metrics import measure_response
from eval.run_eval import _git, validate_frozen_tag
from qa_agent.config import get_settings, sanitize_error
from qa_agent.schemas import AnswerEnvelope, ChatRequest


def write_report(directory: Path, report: dict, responses: list[dict]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    (directory / "responses.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in responses), encoding="utf8")
    lines = ["# D1 RAG 实际 API 开发集记录", "", f"状态：{report['status']}",
             f"题集：{report['split']}；选中 {report['selected_count']}；实际 API 预测 {report['prediction_count']}。",
             f"gold：{report['provenance']['gold_review']}；模型：{report['provenance']['configured_model']}。",
             "", "全文索引涵盖六域。20 题全集涵盖六域；14 道开发题涵盖五域，唯一入选金融题留在保留集。",
             "保留题预测：" + ("本次显式冻结运行" if report['split'] == 'holdout' and responses else "0；未运行"), ""]
    if report["status"] == "READINESS_ONLY":
        lines += ["未调用模型，不计算任何运行指标。", "", "待处理："]
        lines += ["- " + blocker for blocker in report["blockers"]]
    else:
        lines += ["## 自动检查", "", "这些数值检查调用与引用的机械条件，不是答案语义准确率。所有失败计入选中题目分母。", "",
                  "| 检查 | 通过/题数 |", "|---|---:|"]
        for label, key in [
            ("接口 SUCCEEDED", "status_succeeded"),
            ("有实际引用证据", "has_evidence"),
            ("引用全部来自指定文档", "all_evidence_from_selected_doc"),
            ("引用文字全部是所标 PDF 物理页的原文子串", "all_evidence_text_authentic"),
            ("最终引用至少命中一个金标物理页", "evidence_gold_page_hit"),
            ("检索候选至少命中一个金标物理页", "retrieval_gold_page_hit"),
            ("答案带有实际 evidence_id", "answer_has_known_evidence_id"),
            ("标准答案字符串在回答中出现（仅表面诊断）", "answer_surface_match"),
        ]:
            value = report["mechanical_metrics"][key]
            lines.append(f"| {label} | {value['passed']}/{value['denominator']} |")
        lines += ["", f"平均耗时：{report['mean_latency_ms']:.0f} ms。", "",
                  "**答案语义是否正确、每项断言是否受原文支持：全部等待人工复核，未计算 RAG 答案准确率或 groundedness。**",
                  "", "逐题原请求、原响应、实际 evidence_id/page、步骤、比较结果见 responses.jsonl；人工逐题记录见 human_review.md。"]
    lines += ["", "## 溯源", "", "```json", json.dumps(report["provenance"], ensure_ascii=False, indent=2), "```", ""]
    (directory / "report.md").write_text("\n".join(lines), encoding="utf8")
    if responses:
        review = ["# D1 RAG 实际回答人工复核", "", "请逐项判断实际回答是否完整正确、断言是否由实际引用支持。机器没有替你完成这些语义审核。", ""]
        for row in responses:
            actual = row.get("response") or {}
            review += [f"## {row['id']} · {row['doc_id']}", "", "**问题**：" + row['request']['message'], "",
                       "**标准答案**：" + row['reference_answer'], "", "**实际回答**：", "", actual.get('answer', '(未获得有效响应)'), "",
                       "**实际引用**：", ""]
            for evidence in actual.get("evidences", []):
                review += [f"- {evidence['evidence_id']}；文档 {evidence['doc_id']}；物理页 {evidence['page']}",
                           "", "```text", evidence['text'], "```", ""]
            review += ["- [ ] 答案符合问题及标准口径。", "- [ ] 每项事实断言受到所引用原文支持。",
                       "- [ ] 引用物理页和文字已人工核对。", "", "审核人：待填写；结论：待填写；问题：待填写。", ""]
        (directory / "human_review.md").write_text("\n".join(review), encoding="utf8")


def evaluate(args: argparse.Namespace) -> tuple[dict, Path]:
    items = load_dataset(args.dataset)
    # Holdout protection executes before health probes or model requests.
    if args.split == "holdout":
        if not args.allow_holdout or not args.frozen_tag:
            raise ValueError("保留题需要 --allow-holdout 和 --frozen-tag")
        if args.draft_gold:
            raise ValueError("草稿模式只允许运行开发题")
        validate_frozen_tag(args.frozen_tag)
    selected = [item for item in items if item['split'] == args.split]
    if not selected:
        raise ValueError("Selected RAG split is empty")
    settings = get_settings()
    directory = args.output or ROOT / "eval/reports" / ("rag_" + args.split + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("报告目录已有内容；请使用新目录以保留原始实跑记录")
    provenance = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
                  "git_commit": _git("rev-parse", "HEAD"), "working_tree_dirty": bool(_git("status", "--porcelain")),
                  "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
                  "source_pdf_sha256": sorted({item['source_sha256'] for item in selected}),
                  "configured_model": settings.llm_model, "actual_models": [],
                  "retrieval_methods": [], "frozen_tag": args.frozen_tag,
                  "gold_review": "draft" if args.draft_gold else "human_accepted" if all(reviewed(item) for item in selected) else "pending_human_review",
                  "api_base_url": args.base_url, "answer_metrics": "mechanical diagnostics only; semantic correctness and claim grounding unreviewed"}
    report = {"status": "READINESS_ONLY", "split": args.split, "draft_gold": args.draft_gold,
              "selected_count": len(selected), "prediction_count": 0, "blockers": [],
              "provenance": provenance, "mechanical_metrics": {}, "semantic_human_review_count": 0}
    index_meta_path = settings.rag_index_path / 'index_meta.json'
    if index_meta_path.exists():
        provenance['index_meta_sha256'] = hashlib.sha256(index_meta_path.read_bytes()).hexdigest()
        provenance['index_metadata'] = json.loads(index_meta_path.read_text(encoding='utf8'))
    else:
        report['blockers'].append('RAG index_meta.json 不存在，先构建真实索引')
    provenance['configured_retrieval'] = {'top_k': settings.rag_top_k,
                                        'embedding_max_length': settings.rag_embedding_max_length,
                                        'embedding_device': settings.rag_embedding_device,
                                        'embedding_quantization': settings.rag_embedding_quantization,
                                        'answer_mode': settings.rag_answer_mode}
    blockers = report["blockers"]
    try:
        require_run_permission(items, args.split, args.draft_gold, args.allow_holdout, args.frozen_tag)
    except ValueError as error:
        blockers.append(str(error))
    import csv
    manifest_path = settings.rag_manifest_path
    if not manifest_path.exists():
        blockers.append("Missing PDF manifest")
        docs = {}
    else:
        with manifest_path.open(encoding="utf-8-sig", newline="") as file:
            docs = {item['doc_id']: item for item in csv.DictReader(file)}
    pages: dict[str, list[str]] = {}
    alternate_pages: dict[str, list[list[str]]] = {}
    pdf_paths: dict[str, Path] = {}
    provenance['independent_source_extractors'] = []
    for item in selected:
        if item['doc_id'] in pdf_paths:
            continue
        entry = docs.get(item['doc_id'])
        if not entry:
            blockers.append("文档未列入清单：" + item['doc_id'])
            continue
        pdf = (ROOT / entry['path']).resolve()
        if not pdf.is_relative_to(ROOT) or not pdf.exists():
            blockers.append("PDF 不存在或路径不在项目内：" + item['doc_id'])
        elif hashlib.sha256(pdf.read_bytes()).hexdigest() != item['source_sha256']:
            blockers.append("原始 PDF SHA256 与 gold 不一致：" + item['doc_id'])
        else:
            pdf_paths[item['doc_id']] = pdf
    with httpx.Client(timeout=args.timeout) as client:
        try:
            response = client.get(args.base_url.rstrip('/') + '/health')
            response.raise_for_status()
            health = response.json()
            provenance['api_health'] = health
            if settings.rag_answer_mode == 'llm' and not health.get('llm_configured'):
                blockers.append("API 模型凭据未配置")
            if health.get('rag_ready') is False:
                blockers.append('API RAG 索引未就绪')
        except Exception as error:
            blockers.append("API health unavailable: " + sanitize_error(error, settings))
        if blockers:
            write_report(directory, report, [])
            return report, directory
        for doc_id, pdf in pdf_paths.items():
            pages[doc_id] = [page.extract_text() or '' for page in PdfReader(pdf).pages]
            alternate_pages[doc_id] = []
            if 'pypdf' not in provenance['independent_source_extractors']:
                provenance['independent_source_extractors'].append('pypdf')
            try:
                import fitz
            except ImportError:
                pass
            else:
                with fitz.open(pdf) as source_pdf:
                    alternate_pages[doc_id].append([page.get_text('text') for page in source_pdf])
                if 'PyMuPDF' not in provenance['independent_source_extractors']:
                    provenance['independent_source_extractors'].append('PyMuPDF')
            try:
                import pdfplumber
            except ImportError:
                pass
            else:
                with pdfplumber.open(pdf) as source_pdf:
                    alternate_pages[doc_id].append([page.extract_text(layout=False, x_tolerance=2, y_tolerance=3) or '' for page in source_pdf.pages])
                if 'pdfplumber (layout=False, x_tolerance=2, y_tolerance=3)' not in provenance['independent_source_extractors']:
                    provenance['independent_source_extractors'].append('pdfplumber (layout=False, x_tolerance=2, y_tolerance=3)')
        rows = []
        for item in selected:
            request = ChatRequest(message=item['question'], scope={"route": "doc", "db_id": None, "doc_ids": [item['doc_id']]})
            row: dict[str, Any] = {"id": item['id'], "doc_id": item['doc_id'], "request": request.model_dump(mode='json'),
                                   "reference_answer": item['answer'], "gold_physical_pages": item['physical_pages'],
                                   "response": None, "failure": None}
            started = time.perf_counter()
            try:
                result = client.post(args.base_url.rstrip('/') + '/api/chat', json=row['request'])
                result.raise_for_status()
                payload = AnswerEnvelope.model_validate(result.json()).model_dump(mode='json')
                row['response'] = payload
                row['metrics'] = measure_response(item, payload, pages[item['doc_id']], alternate_pages.get(item['doc_id']))
                for step in payload.get('steps', []):
                    model = step.get('output_summary', {}).get('model')
                    if model and model not in provenance['actual_models']:
                        provenance['actual_models'].append(model)
                retrieval = payload.get('metadata', {}).get('retrieval_method')
                if retrieval and retrieval not in provenance['retrieval_methods']:
                    provenance['retrieval_methods'].append(retrieval)
            except Exception as error:
                row['failure'] = sanitize_error(error, settings)
                row['metrics'] = measure_response(item, {}, pages[item['doc_id']])
            row['latency_ms'] = round((time.perf_counter() - started) * 1000)
            rows.append(row)
            print(json.dumps({"id": item['id'], "status": (row.get('response') or {}).get('status', 'REQUEST_FAILED'),
                              "latency_ms": row['latency_ms'], "gold_page_hit": row['metrics']['evidence_gold_page_hit']}, ensure_ascii=False), flush=True)
            # Keep completed responses even if a later run is interrupted.
            directory.mkdir(parents=True, exist_ok=True)
            with (directory / 'responses.jsonl').open('a', encoding='utf8') as file:
                file.write(json.dumps(row, ensure_ascii=False) + '\n')
    keys = [key for key, value in rows[0]['metrics'].items() if isinstance(value, bool) or key == 'retrieval_gold_page_hit']
    report.update({"status": "COMPLETED", "prediction_count": len(rows),
                   "mechanical_metrics": {key: {"passed": sum(row['metrics'].get(key) is True for row in rows),
                                                 "denominator": len(selected),
                                                 "unknown": sum(row['metrics'].get(key) is None for row in rows)} for key in keys},
                   "mean_latency_ms": sum(row['latency_ms'] for row in rows) / len(rows),
                   "request_failure_count": sum(bool(row['failure']) for row in rows),
                   "api_status_counts": dict(Counter((row.get('response') or {}).get('status', 'REQUEST_FAILED') for row in rows)),
                   "answer_review_pending_count": len(rows)})
    write_report(directory, report, rows)
    return report, directory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--split', choices=['dev', 'holdout'], default='dev')
    parser.add_argument('--draft-gold', action='store_true')
    parser.add_argument('--allow-holdout', action='store_true')
    parser.add_argument('--frozen-tag')
    parser.add_argument('--timeout', type=float, default=240)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report, directory = evaluate(args)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps({'status': report['status'], 'prediction_count': report['prediction_count'], 'report': str(directory)}, ensure_ascii=False))
    if report['status'] == 'READINESS_ONLY':
        sys.exit(2)


if __name__ == '__main__':
    main()
