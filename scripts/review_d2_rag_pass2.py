"""Bind the root agent's source reading/visual observations to final DEV output.

This is an offline AI audit record, not a runtime scorer or a human approval.
Original data and predictions are never edited. Heldout content is not loaded.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'eval/artifacts/d2-final/rag'
OBSERVATIONS = {
    'rag-02': '已看原PDF物理页1条款2整段：45天从PSS包含合并后共同经营期间的第一财政季度结束起算，不是合并日起算。',
    'rag-03': '已看原PDF物理页2条款6完整上下文：合并生效后three years；Section13及1934位于紧接正文。三年与法律编号分开，不能只引期限片段却复述其它数字。',
    'rag-05': '已看扫描原页1INTRODUCTION：分水岭西侧经Tame/Etherow流入Mersey，未把东侧河流混入。',
    'rag-06': '已看扫描原页8首段：Coal Measures土壤背景下wheat/oats/potatoes，swedes/turnips的病害不是所问三种最满意作物。',
    'rag-07': '已看扫描原页14GENERAL STRATIGRAPHY：南部Sheet的Shale Grit厚450—550 feet，保留英尺。',
    'rag-08': '已看扫描原页8TABLE OF FORMATIONS正文：四颜色对应Rough Rock/Middle/Kinderscout/Shale四组，未用后续地层表替代。',
    'rag-10': '已看原页65左栏Radio and Television Interference的FCC正文：Class B、Part15同段；不是右栏未授权改装信息。',
    'rag-11': '已看原页3iMovie图文卡：collect/library与create/share movies in minutes；CropBox可见坐标框位于真实该卡。',
    'rag-12': '已看原页67左栏ENERGY STAR® Compliance及完整正文：promote energy-efficient products；®混合字体不改变标题。',
    'rag-13': '已看原页52完整页面：AirPort Base Station在NAT说明段。页首To use Network Diagnostics仅操作引导，后文不能继承该标题；未知章节应空。',
    'rag-15': '已看原页10两栏和11左栏：五能力为leadership/culture/strategy execution/management practices/robust process improvement；ASQ/Forbes归属在页10左栏，页10右栏/页11引文只支撑列表。',
    'rag-16': '已看原页11左栏RANKINGS OF QUALITY PROGRAMS：71% senior leaders world class/advanced，不能换成60% quality professional average/below。',
    'rag-18': '已看原页12右栏附录E续文与页5实验上下文：AUC-ROC衡量attention distributions与final prediction关联；当前框不是左栏或Limitations。',
    'rag-19': '已看原页6右栏3.1.3 Results与页7Table1：明确特别SST-2/EmoC；若附加比较值必须分清shot/基线，不能无基线计算提升。',
    'rag-21': '完整读取Iron Maiden本地署名改写HTML：1975/Leyton/east London，文档没有数据库排名因果信息。',
    'rag-22': '完整读取U2本地HTML：1976/Dublin，未用创始成员名字或专辑年份代替成立时间。',
    'rag-24': '实际查看Led Zeppelin原PNG及OCR：1968/London；是项目简介网页截图，不冒充维基原站页面；非PDF不填物理页。',
    'rag-25': '完整读取实际DOCX段落和表格：热门曲目默认购买数量SUM(invoice_line.quantity)，其它口径是明确备选，题目只问默认与表达式。',
    'rag-26': '完整读取指标DOCX：客单价主口径写全平均每张发票金额AVG(invoice.total)，不是平均每购买客户；NULL/零分母边界在手册。',
    'rag-27': '完整读取实际MD与表定义：customer.country客户所在地、invoice.billing_country账单地址，两者当前相等不允许交换含义。',
    'rag-28': '完整读取指定Iron Maiden HTML的信息边界，未见2026中国逐场票务收入；正确动作证据不足而非外部常识补数据。',
}
ALLOWED_PAGES = {'rag-02': {1}, 'rag-03': {2}, 'rag-05': {1}, 'rag-06': {8}, 'rag-07': {14}, 'rag-08': {8},
                 'rag-10': {65}, 'rag-11': {3}, 'rag-12': {67}, 'rag-13': {52}, 'rag-15': {10, 11},
                 'rag-16': {11}, 'rag-18': {5, 12}, 'rag-19': {6, 7}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()
    directory = BASE / f'regression-{args.version}'
    predictions = [json.loads(line) for line in (directory / 'responses.jsonl').read_text(encoding='utf-8').splitlines() if line]
    location_path = BASE / f'location-check-{args.version}/citation-location-check.json'
    locations = {row['id']: row for row in json.loads(location_path.read_text(encoding='utf-8'))['rows']}
    if len(predictions) != 21 or {row['id'] for row in predictions} != set(OBSERVATIONS):
        raise ValueError('Expected exactly the already read 21 DEV cases; new/heldout cases require separate review.')
    records = []
    for line, row in enumerate(predictions, 1):
        ident, response = row['id'], row['response']
        status = response['status']
        answer_verdict = ('AI建议通过' if status == ('SUCCEEDED' if row['answerable'] else 'EMPTY_RESULT') else 'AI发现错误')
        citation_verdict = 'AI建议通过' if answer_verdict == 'AI建议通过' else '未生成可审核成功引用'
        limitation = []
        if ident == 'rag-15' and status == 'SUCCEEDED':
            text = '\n'.join(item['text'] for item in response['evidences'])
            if ('ASQ' in response['answer'] or 'Forbes' in response['answer']) and not ('ASQ' in text and 'Forbes' in text):
                answer_verdict = citation_verdict = 'AI建议有条件通过'
                limitation.append('五能力与原文一致，但实际所引片段未含ASQ/Forbes归属句；建议删无支持归属或引已检索的真实归属片段。窄字面门禁不保证全部被动句变体。')
        citations = []
        for item in locations[ident]['citations']:
            page = item.get('page')
            physical_ok = item.get('index_membership') is True and (
                page is None or page in ALLOWED_PAGES.get(ident, set()) and item.get('bbox_within_visible_cropbox') is True)
            if not physical_ok:
                raise ValueError(f'Unobserved page or invalid source geometry for {ident}/{item["evidence_id"]}')
            section = item.get('section_path', [])
            if ident == 'rag-13' and section:
                raise ValueError('Procedure heading leak remains in final output; cannot certify corrected location.')
            if any(value == 'External USB Modem Information' for value in section) and ident == 'rag-12':
                raise ValueError('ENERGY STAR heading still incorrect.')
            citations.append({'evidence_id': item['evidence_id'], 'doc_id': item['doc_id'], 'page': page,
                              'bbox': item.get('bbox'), 'source_membership': True,
                              'physical_source_location': 'AI建议通过', 'section_path': section,
                              'section_review': 'AI建议通过' if section else '证据不足：章节未知，未填写',
                              'evidence_file': item.get('rendered_source'),
                              'source_text': item['text']})
        if status == 'FAILED':
            limitation.append('实际请求失败保留原trace/错误；参考答案正确不等于系统答对，不选用旧轮成功替换。')
        records.append({'id': ident, 'group': 'RAG/dev', 'review_object': 'reference / actual answer / citation / source location',
                        'reference_verdict': 'AI建议通过', 'answer_verdict': answer_verdict,
                        'citation_semantic_verdict': citation_verdict, 'source_observation': OBSERVATIONS[ident],
                        'actual_answer': response['answer'], 'status': status,
                        'raw_evidence': f'{directory.relative_to(ROOT).as_posix()}/responses.jsonl:{line}',
                        'trace_id': response['trace_id'], 'citations': citations,
                        'problems_and_suggestions': limitation, 'human_review': 'pending_human_review'})
    report = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'version': args.version,
              'reviewer': 'root AI independent second source review', 'reviewed_dev_count': 21,
              'reference_verdicts': dict(Counter(r['reference_verdict'] for r in records)),
              'answer_verdicts': dict(Counter(r['answer_verdict'] for r in records)),
              'citation_semantic_verdicts': dict(Counter(r['citation_semantic_verdict'] for r in records)),
              'physical_citation_count': sum(len(r['citations']) for r in records),
              'unknown_section_citation_count': sum(not c['section_path'] for r in records for c in r['citations']),
              'holdout_predictions': 0, 'human_signatures_added': False,
              'source_method': 'Read all final questions/references/answers/citations; visually inspected original PDF source pages and PNG; read entire local HTML/MD/DOCX paragraphs/tables. Root reasoning, no external common knowledge.',
              'responses_sha256': sha256((directory / 'responses.jsonl').read_bytes()).hexdigest(),
              'locations_sha256': sha256(location_path.read_bytes()).hexdigest(), 'rows': records}
    (BASE / f'second-review-{args.version}.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# D2 RAG 最终开发集：根代理独立第二遍原文审核', '',
             '这是AI预审记录，未填人工签名或确认日期。未访问保留题内容或生成其预测。物理定位与章节未知分别统计。', '',
             '| 原编号 | 参考答案 | 系统完整回答 | 引用语义 | 具体原文核对与问题 |', '|---|---|---|---|---|']
    for item in records:
        lines.append('|'+ '|'.join([item['id'], item['reference_verdict'], item['answer_verdict'], item['citation_semantic_verdict'],
                                    item['source_observation']+' '.join(item['problems_and_suggestions'])])+'|')
    lines += ['', '逐引用doc_id/物理页/bbox/章节/图片和原始输出行号见同名JSON；章节为空时仅页框确认，不冒称章节精确通过。', '',
              '原始失败/中间版本各保留在独立目录；本报告只绑定当前responses SHA和定位证据SHA，不把旧答案挪成新实测。']
    (BASE / f'second-review-{args.version}.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key in {'version','reviewed_dev_count','answer_verdicts','physical_citation_count','unknown_section_citation_count'}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
