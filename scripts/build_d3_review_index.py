"""Create a pending-human D3 index from existing developer-only review tables."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import html
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'eval/reports/d3-acceptance'
TITLE = 'D3统一待人工审核表'


def source(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or any(part in {'protected_holdout', '.runtime'} for part in path.parts) or 'holdout' in path.name.casefold():
        raise ValueError('Only explicit developer review sources are permitted')
    return path


def read(name):
    return json.loads(source(name).read_text(encoding='utf-8-sig'))


def link(name, label=None):
    path = source(name.split('#', 1)[0])
    if not path.is_file():
        raise FileNotFoundError(name)
    return '[' + (label or name) + '](<' + Path(os.path.relpath(path, OUT)).as_posix() + '>)'


def clean(value):
    return str(value or '').replace('|', '\\|').replace('\n', ' ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--b-review-json', required=True)
    args = parser.parse_args()
    a_name = 'eval/reports/d3-acceptance/A待人工核对表.json'
    a, b = read(a_name), read(args.b_review_json)
    a_rows = a['rows']
    b_rows = b.get('rows', b.get('items', b.get('cases', [])))
    if isinstance(b_rows, list):
        b_rows = b_rows + b.get('manual_items', [])
    if not isinstance(b_rows, list) or len(a_rows) != 46 or len(b_rows) < 21:
        raise ValueError('Expected 46 A rows and at least 21 actual B developer review rows')
    template = read('notes/d3/unified-review-template.json')
    protocol = next(group for group in template['groups'] if group['id'] == 'protocol_changes')['items']
    unit_note = '同比输出单位核对：v7自由输入为fraction，v8可信年份按钮为乘100后ROUND2百分数；同名growth字段不代表单位一致，不新增全局默认。决定采用的显示/标注方式后再修改。'
    evidence = ['eval/artifacts/d3/b/button-api-v1/independent-observation.json',
                'eval/artifacts/d3/root-interface/free-growth-independent-readonly.json',
                'eval/artifacts/d3/b/ui-live-v4/report.json',
                'eval/reports/d3-ai-review/aw-run2-additional-observation.md']
    report = {'title': TITLE, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'human_review_status': 'pending_human_review', 'human_signatures': None, 'human_confirmed_at': None,
              'scope': 'Developer-only A/B material and protocol review; no held questions or gold',
              'counts': {'a_rows': len(a_rows), 'b_rows': len(b_rows), 'protocol_boundaries': len(protocol) + 1},
              'priority': ['aw-07产品编号可能是productid或productnumber，strict EX20/21保持，系统业务正确性待定',
                           'production.document.status枚举缺少字典依据', 'clarify-20分母期间语法范围', unit_note],
              'a_row_index': [{k: row[k] for k in ('id', 'group', 'target', 'ai_judgment', 'reason', 'human_action', 'source', 'position') if k in row} for row in a_rows],
              'b_row_index': [{k: row[k] for k in ('id', 'group', 'question', 'requirement', 'ai_judgment', 'ai_reference_judgment', 'actual_answer_business_judgment', 'still_needs_human') if k in row} for row in b_rows],
              'protocol_boundaries': protocol + [unit_note],
              'holdout_progress': {'aw_count': 9, 'clarify_count': 9, 'prediction_count': 0, 'details_included': False},
              'sources': {name: sha256(source(name).read_bytes()).hexdigest() for name in [a_name, args.b_review_json]},
              'model_calls': 0, 'database_queries': 0, 'api_predictions': 0}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (TITLE + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# ' + TITLE, '', '以下是本轮统一人审入口，AI两遍建议与真实实测分开。没有A/B签字、人工确认日期或自动approved。原A/B审核材料与原始结果不覆盖。', '',
             f"A待核{len(a_rows)}项（目录条件/证据不足25＋AW开发21），B待核{len(b_rows)}项（21开发＋4公共），协议与显示边界补充说明{len(protocol)+1}条，与B公共项有对应关系，不另算互异题数。保留18题只列进度，不展开题目或答案，预测0。", '',
             '## 优先处理', ''] + ['- ' + text for text in report['priority']] + ['', '## 完整标准材料与实际回答', '',
             '- A逐项完整材料：' + link(a_name) + '；' + link(a_name.removesuffix('.json') + '.md'),
             '- B逐项完整材料：' + link(args.b_review_json)]
    b_md = args.b_review_json.removesuffix('.json') + '.md'
    if source(b_md).is_file():
        lines.append('- B可读版：' + link(b_md))
    lines += ['', '完整source JSON含真实题面、标签、理由、标准SQL/结果与具体证据位置；本索引表保持原编号，点击上述完整表逐项核对。', '']
    for title, rows in [('A线原编号索引', a_rows), ('B线原编号索引', b_rows)]:
        lines += ['## ' + title, '', '|原编号|对象/分组|AI意见或实测限制|需人工确认|', '|---|---|---|---|']
        for row in rows:
            lines.append('|'+clean(row.get('id', row.get('number')))+'|'+clean(row.get('target', row.get('question', row.get('requirement', row.get('group')))))+'|'+clean(row.get('ai_judgment', row.get('ai_reference_judgment', row.get('judgment'))))+'|'+clean(row.get('human_action', row.get('still_needs_human', row.get('reason'))))+'|')
        lines.append('')
    lines += ['## 协议与显示边界', ''] + [f"{index+1}. {text}（人工待核）" for index, text in enumerate(protocol + [unit_note])]
    lines += ['', '## 已实际运行的重点证据', ''] + ['- '+link(name) for name in evidence]
    lines += ['', 'AI预审不代替人工签字；澄清开发21/21为初次层级与阻断/执行状态，不是21题所有按钮及完整多轮EX。flow-v6为v7采集，按钮回归/UI-v4为v8；实际版本范围在验收报告说明。', '',
              '保留进度：AW9＋澄清9，标准标签准备，0模型预测、无成绩；开发交付不含详细保留内容。', '',
              '机器索引、原始审核表SHA与来源引用：'+link('eval/reports/d3-acceptance/'+TITLE+'.json')]
    markdown = '\n'.join(lines) + '\n'
    (OUT / (TITLE + '.md')).write_text(markdown, encoding='utf-8')
    from markdown_it import MarkdownIt
    body = MarkdownIt('commonmark').enable('table').render(markdown)
    css = 'body{max-width:1200px;margin:32px auto;padding:0 24px;font:16px/1.7 "Microsoft YaHei",sans-serif;color:#253047}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:8px;border:1px solid #d5deea;vertical-align:top}th{background:#eef3fa}a{color:#145f9b;overflow-wrap:anywhere}h2{margin-top:38px}'
    (OUT / (TITLE + '.html')).write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+html.escape(TITLE)+'</title><style>'+css+'</style><body>'+body+'</body></html>', encoding='utf-8')
    print(json.dumps({'report':'eval/reports/d3-acceptance/'+TITLE+'.html', 'counts':report['counts'], 'api_predictions':0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
