"""Export pending D3 developer clarification review, without held-out reads."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def main():
    dataset_path = 'eval/datasets/d3/clarify/dev.jsonl'
    cases = [json.loads(line) for line in (ROOT / dataset_path).read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(cases) != 21 or any(item['split'] != 'dev' for item in cases):
        raise SystemExit('Only the 21 developer cases may enter this review.')
    second = {item['id']: item for item in load('eval/reports/d3-ai-review/clarify-dev-pass2.json')['rows']}
    report = load('eval/artifacts/d3/b/clarify-dev-v4/report.json')
    actual = {item['id']: item for item in report['judgments']}
    rows = []
    for line, case in enumerate(cases, 1):
        row, check = second[case['id']], actual[case['id']]
        raw = 'eval/artifacts/d3/b/clarify-dev-v4/' + check['evidence']
        rows.append({
            'id': case['id'], 'group': 'D3澄清开发集', 'question': case['question'],
            'expected_level': case['expected_level'], 'expected_behavior': case['expected_behavior'],
            'reference_semantics': case['reference_semantics'], 'basis': case['basis'],
            'ai_reference_judgment': row['ai_judgment'], 'ai_reference_reason': row['rationale'],
            'actual_status': check['status'], 'actual_level': check['actual_level'],
            'ai_actual_level_judgment': 'AI建议通过' if check['passed'] else 'AI发现错误',
            'actual_answer_business_judgment': '待人工逐题核对；分级通过不等于完整SQL/答案业务正确',
            'evidence': [{'path': dataset_path, 'position': 'line=' + str(line) + '; id=' + case['id']},
                         {'path': raw, 'position': 'actual API response, SQL/table, steps, clarification and metadata'},
                         {'path': 'eval/reports/d3-ai-review/clarify-dev-pass2.json', 'position': 'rows/id=' + case['id']}],
            'still_needs_human': row['still_needs_human'], 'human_review_status': 'pending_human_review',
        })
    manual = [
        {'id': 'd3-b-protocol', 'group': '公共接口与会话',
         'requirement': '新增可选 ChatRequest.clarification_id/intent_version/choice_id 和 AnswerEnvelope.intent；IntentContract 延续 extra=forbid，卡片恢复需ID与版本同时匹配，PDF物理页从1开始的既有约定不改。',
         'ai_judgment': 'AI建议通过',
         'reason': '新增字段兼容旧首次请求；原协议与新协议的具体源码版本需双方最后核对。真实陈旧卡在模型/SQL前拒绝，年份选择不会清掉独立缺指标问题。',
         'evidence': ['qa_agent/schemas.py', 'qa_agent/clarify/state.py', 'eval/artifacts/d3/b/shared-regression-v13/command.json',
                      'eval/artifacts/d3/b/clarify-flow-v6/stale-card-rejected.json', 'eval/artifacts/d3/b/button-api-v1/missing-metric-after.json']},
        {'id': 'd3-b-defaults', 'group': '声明的对象限定假设',
         'requirement': '热门曲目缺指标采用已共同确认的购买数量口径；客户谁买得最多缺指标采用已共同确认金额；缺Top-N数量按方案默认10并声明；缺关键期间/对象不得猜。',
         'ai_judgment': 'AI建议有条件通过',
         'reason': '已确认四项指标不改。缺数量的10条假设和仅明确最近有记录年份的解释，需核对适用对象及声明；“数据中最近一年”不自动装成最大年份。数量→金额→数量真实切换均通过。',
         'evidence': ['qa_agent/clarify/clarify_rules.yaml', 'qa_agent/clarify/rules.py', 'data/rules/metric_definitions.json',
                      'eval/artifacts/d3/b/ui-live-v4/popular-default-raw.json', 'eval/artifacts/d3/b/ui-live-v4/switch-revenue-raw.json',
                      'eval/artifacts/d3/b/ui-live-v4/switch-back-quantity-raw.json']},
        {'id': 'd3-b-growth-display', 'group': '增长率显示单位',
         'requirement': '人工决定增长率结果表及文字采用fraction还是percent，以及统一舍入/单位说明方式；在决定前不修改原始输出。',
         'ai_judgment': 'AI建议有条件通过',
         'reason': '真实 valid-year-after 返回 ROUND(*100,2) 的24.24，free-year-resumed/UI返回0.24240365…；数学增长可一致，但同一列名不足以证明同一显示单位。技术恢复成功不替代该显示规范审核。',
         'evidence': ['eval/artifacts/d3/b/button-api-v1/valid-year-after.json',
                      'eval/artifacts/d3/b/clarify-flow-v6/free-year-resumed.json',
                      'eval/artifacts/d3/b/ui-live-v4/clarification-after-raw.json',
                      'eval/artifacts/d3/b/ui-live-v4/free-input-after-raw.json']},
        {'id': 'd3-b-measurement-scope', 'group': '测试结论范围',
         'requirement': '21/21仅初始分级与执行门；7请求20/20为具体状态链；7UI请求10/10为控件连线。全部21题的澄清交互最终答案正确率尚未实测。',
         'ai_judgment': 'AI建议通过',
         'reason': '保留9题预测0；D4的5段每段6轮、完整自动路由/混合跨源和复杂SQL数据流不提前声明完成。人工审核应分别检查参考判定与系统真实业务回答。',
         'evidence': ['eval/reports/d3/b/handoff-summary.json', 'eval/datasets/d3/clarify/manifest.json',
                      'eval/artifacts/d3/b/clarify-dev-v4/report.json', 'eval/artifacts/d3/b/clarify-flow-v6/report.json',
                      'eval/artifacts/d3/b/ui-live-v4/report.json']},
    ]
    for row in manual:
        row['human_review_status'] = 'pending_human_review'
    payload = {'title': 'D3 B 统一人审输入：21开发题与4项公共待核事项',
               'created_at_utc': datetime.now(timezone.utc).isoformat(),
               'dataset_sha256': hashlib.sha256((ROOT / dataset_path).read_bytes()).hexdigest(),
               'dev_checked': len(rows), 'rows': rows, 'manual_items': manual,
               'holdout': {'count': 9, 'predictions': 0, 'content_not_included': True, 'policy': 'D5冻结后运行'},
               'catalog_details_source': 'eval/reports/d3-ai-review/catalog-pass2.json',
               'human_review_status': 'pending_human_review'}
    out = ROOT / 'notes/d3'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'clarify-human-review.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    md = ['# D3 B 待人工统一审核输入', '',
          '这里只包含21道开发题和4项公共待核事项；9道隔离保留题不展开、预测为0。以下AI结论不是人工签字。逐题先核对参考判定，再打开真实raw核对系统业务输出；初始分级通过不能自动推出完整SQL和答案正确。', '',
          '| 编号 | 题目 | 参考级别 | 二遍AI参考建议 | 系统实际级别/状态 | 具体材料 |',
          '|---|---|---|---|---|---|']
    for row in rows:
        md.append('| ' + ' | '.join([row['id'], row['question'].replace('|', '\\|'), row['expected_level'],
                   row['ai_reference_judgment'], row['actual_level'] + ' / ' + row['actual_status'],
                   '`' + row['evidence'][1]['path'] + '`']) + ' |')
    md.extend(['', 'clarify-20的分母2024年范围表达为二遍AI有条件通过，请优先检查该题句意。完整reference_semantics、理由、真实材料具体位置在同名JSON逐项保存，人工状态均保持pending_human_review。', '',
               '## 公共待核事项', ''])
    for row in manual:
        md.extend(['### ' + row['id'] + '：' + row['group'], '', row['requirement'], '',
                   row['ai_judgment'] + '：' + row['reason'], '',
                   '证据：' + '；'.join('`' + path + '`' for path in row['evidence']) + '。', ''])
    md.extend(['AW目录条件与证据不足具体条目另见 `eval/reports/d3-ai-review/catalog-pass2.json`，本输入不复制改写该独立二遍记录。A负责合并AW21开发题、B21开发题、目录具体条件、协议与显示待核为最终统一表。', '',
               '未填写A/B签字、人工确认日期，未修改题库、启用别名、业务口径、原始数据或既有人工记录。'])
    (out / 'clarify-human-review.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print(json.dumps({'path': 'notes/d3/clarify-human-review.json', 'dev_rows': len(rows), 'manual_items': len(manual),
                      'holdout_content_reads': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
