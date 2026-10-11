"""Build D3 B handoff from completed actual evidence, without model calls."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'eval/reports/d3/b'


def read(path: str):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def main():
    paths = {
        'modules': 'eval/artifacts/d3/b/shared-regression-v13/command.json',
        'dev': 'eval/artifacts/d3/b/clarify-dev-v4/report.json',
        'flow': 'eval/artifacts/d3/b/clarify-flow-v6/report.json',
        'button': 'eval/artifacts/d3/b/button-api-v1/report.json',
        'button_observation': 'eval/artifacts/d3/b/button-api-v1/independent-observation.json',
        'ui': 'eval/artifacts/d3/b/ui-live-v4/report.json',
        'visual': 'eval/artifacts/d3/b/ui-live-v4/visual-review.json',
        'manifest': 'eval/datasets/d3/clarify/manifest.json',
        'catalog_pass2': 'eval/reports/d3-ai-review/catalog-pass2.json',
        'labels_pass2': 'eval/reports/d3-ai-review/clarify-dev-pass2.json',
    }
    data = {name: read(path) for name, path in paths.items()}
    if data['ui']['status'] != 'PASS' or len(data['ui']['screenshots']) != 7:
        raise SystemExit('Actual seven-screenshot UI acceptance is not complete.')
    if data['visual']['status'] != 'AI建议通过':
        raise SystemExit('The actual seven images must be visually inspected first.')
    modules = data['modules']
    source_match = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
        for path, digest in modules['source_sha256'].items()
    }
    if modules['exit_code'] != 0 or not all(source_match.values()):
        raise SystemExit('Module result is not tied to the current business source.')
    stdout = (ROOT / 'eval/artifacts/d3/b/shared-regression-v13/pytest.stdout.txt').read_text(encoding='utf-8')
    match = re.search(r'(\d+) passed in ([\d.]+)s', stdout)
    if not match:
        raise SystemExit('Actual pytest summary is missing.')
    dev_counts = Counter(item['expected_level'] for item in data['dev']['judgments'])
    ui_requests = [read(item['raw']) for item in data['ui']['screenshots']]
    ui_count = len({item['response']['trace_id'] for item in ui_requests})
    summary = {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'D3 B original four items; actual developer evidence and two AI preaudits; human final review pending',
        'evidence': paths,
        'module_result': {'passed': int(match[1]), 'elapsed_seconds': float(match[2]), 'exit_code': 0,
                          'business_source_matches_recorded_hashes': all(source_match.values())},
        'dataset': data['manifest'],
        'dev_result': {'passed': data['dev']['passed'], 'total': data['dev']['total'],
                       'l2_recall': data['dev']['l2_recall'],
                       'non_l2_false_ask_rate': data['dev']['non_l2_false_ask_rate'],
                       'dev_labels': dict(dev_counts), 'runtime': 'runtime-v7',
                       'measurement': 'initial clarification level and SQL gate behavior; not all-question answer EX'},
        'flow_result': {'passed': data['flow']['passed'], 'total': data['flow']['total'],
                        'technical_passed': data['flow']['technical_passed'],
                        'technical_total': data['flow']['technical_checks'],
                        'country_source_passed': data['flow']['country_output_source_passed'],
                        'country_source_total': data['flow']['country_output_source_checks'],
                        'actual_api_requests': data['flow']['actual_api_requests'], 'runtime': 'runtime-v7'},
        'affected_button_result': {'passed': data['button']['passed'], 'total': data['button']['total'],
                                   'actual_api_requests': data['button']['actual_api_requests'], 'runtime': 'runtime-v8'},
        'ui_result': {'status': data['ui']['status'], 'passed': sum(x['passed'] for x in data['ui']['checks']),
                      'total': len(data['ui']['checks']), 'screenshots': len(data['ui']['screenshots']),
                      'actual_api_requests': ui_count, 'runtime': 'runtime-v8'},
        'protected_holdout_predictions': 0,
        'human_review_status': 'pending_human_review',
        'limits': [
            'The final runtime-v8 increment only clears time ambiguity after a valid trusted user period choice; unaffected dev/flow runs were taken on runtime-v7 and are not represented as later sampling.',
            'No formal 21-question post-clarification answer EX or full interaction-success rate has been measured.',
            'Growth responses currently include both fractional and percent representations, with different rounding; the output display/unit convention remains for human review.',
            'No D4 5-dialogue-by-6-turn suite, full automatic router, hybrid cross-source planning or full SQL data-flow analysis is claimed.',
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'handoff-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [
        '# D3 B 原清单四项执行与实际证据', '',
        'B 线四项已接入原 D1/D2 的真实 `/api/chat`、Chinook/AW 数据来源选择和 Streamlit 流程。以下结论是本轮真实开发集测试和两遍 AI 预审；题意、默认口径细节与协议变更集中留给人工最终核对，未填写人工签字或确认日期。', '',
        '| 原清单要求 | 实现与改动文件 | 实际验收方法与结果 | 证据（项目内相对路径） |',
        '|---|---|---|---|',
        '| `clarify_rules.yaml`、`rules.py`，L0/L1/L2 | `qa_agent/clarify/clarify_rules.yaml`、`rules.py`、`extractor.py`、`service.py`；复杂中文复用已验证的真实 JsonLLM，明确简单单表保留直接执行 | 21 开发题初始分级/阻断 21/21；11 道应问召回 100%，10 道不应问误澄清 0%；复杂缺期、歧义、多候选先问再执行 | `eval/artifacts/d3/b/clarify-dev-v4/` |',
        '| `state.py`，IntentContract、补丁、版本号与失效 | `qa_agent/clarify/state.py`、`qa_agent/schemas.py`、`qa_agent/pipeline.py`；状态原子持久化，真实用户补丁需字段/运算符/值依据；卡片 ID/版本在模型和 SQL 前校验 | 7 次真实 API 的 18/18 条件/金额/失效检查，另 2/2 地区 SELECT/GROUP/HAVING 实际来源；仅改国家值失效 result，改地区字段失效 fields/schema/result，改时间失效 derived_period/result；陈旧卡无模型/SQL | `eval/artifacts/d3/b/clarify-flow-v6/` |',
        '| 页面卡片：按钮、自由输入、L1 声明、切换口径 | `ui/app.py`、`api/main.py`；可信后端选择不接受客户端任意补丁；数量→销售额→数量生成新版本卡片 | 真实 Edge/Streamlit/API：7 请求、7 张截图，10/10 控件连线检查；补充年份按钮/自由输入均恢复查询，L1 声明可见并两次切换；另受影响年份按钮正反例 4/4、4 API | `eval/artifacts/d3/b/ui-live-v4/`、`eval/artifacts/d3/b/button-api-v1/`、`notes/screenshots/D3-20261011T200137Z-*.png` |',
        '| 30 道澄清题，15 L2 + 15 L0/L1 | `eval/datasets/d3/clarify/dev.jsonl`、`manifest.json`；30 题总计 L0=10、L1=5、L2=15，21 开发/9 保留，按同源家庭分组 | 21 开发题真实执行；两遍 AI 逐题预审，人工标签保持 pending；9 保留题只列数量/隔离状态，预测 0，D5 冻结后运行 | `eval/datasets/d3/clarify/manifest.json`、`eval/reports/d3/b/AI预审第一遍.md`、`eval/reports/d3-ai-review/clarify-dev-pass2.json` |', '',
        '## 最终源码与实测版本', '',
        f'最终全模块真实命令记录为 `{paths["modules"]}`，实际 {match[1]} passed / {match[2]}s，exit code 0；该记录所含所有业务源码 SHA256 与当前文件逐一相同。AppTest 控件测试使用 API mock，不能冒充真实 DeepSeek 成绩；以上 7 张页面图来自另一次真实浏览器/API 运行。', '',
        '初始 21 题分级和 7 请求条件链在 runtime-v7 完成。随后真实 UI 发现按钮写入有效年份但旧 time_ambiguous 标志仍留存，已只在可信 period 真正赋值且 ISO 日期有效、start<end 时清该标志；其它未选指标/国家问题仍保留。最终 runtime-v8 仅含此增量，由 415 个模块、受影响实际按钮正反例和真实 UI 回归覆盖。未把之前的 v7 结果写成 v8 重新采集，也未重复未受影响题集凑分。', '',
        '## 问题、修复与失败保留', '',
        '全部早期实际失败另存，见 `eval/reports/d3/b/followup-failure-analysis.md`。该记录区分截图/评分观测故障和真正系统条件丢失。最终查询重新生成 SQL 并经值绑定、期间/地区来源守卫和只读执行；索引复用，没有宣称补丁后只执行数据库或采用 SQL AST 缓存。', '',
        '比例任务仅在已确认分子和全局同期间分母的限定结构下允许条件聚合；普通值绑定 WHERE 保护没有取消。对已确认国家/期间的实际 API 旧错误，增加通用结构反例并使用原有有限 SQL repair，而非根据题号填答案。多层 CTE 日期数据流、完整多轮指代和跨源规划属于后续范围，本轮保守限制并在能力边界中记录。', '',
        '## 人工最后核对事项', '',
        '1. 21 道开发题意、期望 L0/L1/L2 与按钮/自由输入表达；特别是 clarify-20 分母期间句意，二遍 AI 仅建议有条件通过。',
        '2. Top-N 缺数量采用并声明 10 的对象限定假设、热门曲目按购买数量等可切换声明，以及新 IntentContract/卡片可选协议字段；现有四项人审业务定义不改。',
        '3. 增长率显示规范：本轮原始实际 SQL 同时出现 fraction（如 0.2424…）与 percentage（如 24.24）的合法数学表示，舍入也有差别。不能凭同一列名认为单位相同；本报告不把技术恢复成功算作人工确认的完整答案正确。',
        '4. AW 中文目录独立二遍 68 表/456 列：63 表建议通过、5 表条件通过；436 列建议通过、19 列条件通过、1 列证据不足（production.document.status 业务枚举含义）。具体条目见 `eval/reports/d3-ai-review/catalog-pass2.json`。', '',
        '没有 A/B 签名，没有人工确认日期，没有 approved 状态变更，没有自动启用别名。保留集详细题目/答案不在开发交付正文或附件；隔离集元数据仅汇总，待 D5。正式的“全部应澄清题经过交互后最终答案正确率”尚未实测，本轮仅有明确列出的开发分级、真实状态链和控件场景数字。', '',
        '项目内证据路径以 system 根目录为基准；打包报告由上级汇总为《D3原清单八项逐项验收与证据》，本文件提供 B 线原始分项依据。',
    ]
    (OUT / 'B原清单四项验收与证据.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'output': 'eval/reports/d3/b/handoff-summary.json', 'modules': summary['module_result'],
                      'ui': summary['ui_result']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
