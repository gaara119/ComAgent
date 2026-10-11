"""Append an honest AW regression observation without changing labels or runs."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUN = 'eval/reports/d3-aw-live-dev-run2'
OUTPUT = 'eval/reports/d3-ai-review/aw-run2-additional-observation'


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def main():
    if (ROOT / (OUTPUT + '.json')).exists():
        raise SystemExit('Additional observation already exists; preserve it.')
    report = read(RUN + '/report.json')
    observation = read(RUN + '/schema-observation.json')
    if report['status'] != 'ACTUALLY_RUN_DEV_EXPLORATORY':
        raise SystemExit('AW run2 is not complete.')
    responses = [json.loads(line) for line in (ROOT / (RUN + '/responses.jsonl')).read_text(encoding='utf-8').splitlines() if line]
    case = next(row for row in responses if row['id'] == 'aw-07')
    data = yaml.safe_load((ROOT / 'data/catalog/adventureworks.yaml').read_text(encoding='utf-8'))
    table = next(table for table in data['tables'] if table['schema'] == 'production' and table['name'] == 'product')
    columns = [column for column in table['columns'] if column['name'] in ('productid', 'productnumber')]
    reason = ('产品编号在实际目录中可能指productid主键，也可能指productnumber业务编号。'
              '原gold选productid，run2真实回答选productnumber并按该列处理同价顺序。'
              '两种字段在本题结果并不相同；题面没有明确字段，因此严格EX保留不匹配，但不能据此直接断言系统业务答案错误。')
    result = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Additional AI observation of preserved development run2; no model/DB calls and no protected content',
              'case_id': 'aw-07', 'reference_verdict': 'AI建议有条件通过',
              'system_business_verdict': '暂不能确定；字段含义需人工确认',
              'strict_execution_match': case['matched'], 'question': case['request']['message'],
              'actual_columns': columns, 'original_expected_result': case['expected_result'],
              'actual_sql': case['response']['sql'], 'actual_result': case['response']['table'],
              'reason': reason, 'previous_review_observation': '第一、第二遍AI未识别该歧义；原两遍报告保留不覆盖',
              'human_action': '明确产品主键ID(productid)还是产品业务编号(productnumber)，也核对同价排序字段；决定修订前原题、gold、raw和strict分数都不改变。',
              'human_status': 'pending_human_review', 'holdout_predictions': 0,
              'run2_summary': {key: report[key] for key in ('correct', 'prediction_count', 'exploratory_ex', 'actual_model_attempts', 'usage', 'average_latency_ms')},
              'schema_summary': {key: observation[key] for key in ('all_gold_recalled_cases', 'mean_table_recall', 'average_actual_schema_latency_ms', 'actual_sql_execution_adventureworks_cases')},
              'evidence_sha256': {name: sha(name) for name in (RUN + '/responses.jsonl', RUN + '/report.json', 'data/catalog/adventureworks.yaml', 'eval/datasets/d3/aw_schema_link.dev.v2.jsonl')}}
    (ROOT / (OUTPUT + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    content = '\n'.join(['# AW第二轮开发回归：新增AI观察', '',
        f"实际严格EX：{report['correct']}/{report['prediction_count']}（{report['exploratory_ex']:.2%}）；原run1的21/21保持原文件。", '',
        '**aw-07参考答案：AI建议有条件通过。系统业务答案：暂不能确定。**', '', reason, '',
        '两遍AI审读漏检该字段歧义；原意见原文件保留，不反写成当时已经发现。当前不改题面、标准SQL、标准结果、别名、prompt或系统代码。', '',
        '人工需明确productid还是productnumber及同价排序字段，修订决定另行记录。strict20/21先如实保存，不能将两种编号偷偷视为等价或仅为通过改gold。', '',
        '[实际run2报告](../d3-aw-live-dev-run2/report.json)、[真实请求/回答](../d3-aw-live-dev-run2/responses.jsonl)、[目录](../../../data/catalog/adventureworks.yaml)、[新增判断机器记录](aw-run2-additional-observation.json)。', '',
        f"候选gold表覆盖{observation['all_gold_recalled_cases']}/21，实际AW执行{observation['actual_sql_execution_adventureworks_cases']}/21，schema阶段平均{observation['average_actual_schema_latency_ms']}ms。", '',
        '本观察仅读取已保存文件；没有发起新模型预测或只读SQL，没有保留题内容，没有人工签字或确认日期。', ''])
    (ROOT / (OUTPUT + '.md')).write_text(content, encoding='utf-8')
    review_path = ROOT / 'eval/reports/d3-acceptance/A待人工核对表.json'
    review = json.loads(review_path.read_text(encoding='utf-8'))
    target = next(row for row in review['rows'] if row['id'] == 'aw-07')
    target['previous_ai_review_preserved'] = {'ai_judgment': target['ai_judgment'], 'reason': target['reason'], 'system_evidence': target['system_evidence']}
    target['ai_judgment'] = 'AI建议有条件通过；run2新增产品编号字段歧义'
    target['reason'] = reason
    target['human_action'] = result['human_action']
    target['system_evidence'] = RUN + '/responses.jsonl#id=aw-07'
    target['additional_ai_evidence'] = OUTPUT + '.json'
    review['additional_observation'] = {'file': OUTPUT + '.json', 'original_ai_reviews_not_overwritten': True}
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding='utf-8')
    md_path = ROOT / 'eval/reports/d3-acceptance/A待人工核对表.md'
    md = md_path.read_text(encoding='utf-8')
    before, tail = md.split('## aw-08', 1)
    addition = ('\n**run2新增AI观察**：AI建议有条件通过；以上原两遍通过意见漏检了编号字段歧义。' + reason + '\n\n'
                '人工请优先明确productid/productnumber及同价排序；原gold与raw均未修改。'
                '[独立新增观察](../d3-ai-review/aw-run2-additional-observation.md)。\n\n')
    md_path.write_text(before + addition + '## aw-08' + tail, encoding='utf-8')
    note = ROOT / 'notes/d3/A线实施与实测记录.md'
    with note.open('a', encoding='utf-8') as stream:
        stream.write('\n## 共享澄清修复后的AW同版本回归（run2）\n\n'
            f"后续真实回归为 **{report['correct']}/{report['prediction_count']} strict EX（{report['exploratory_ex']:.2%}）**，"
            f"{report['actual_model_attempts']}次模型尝试，total tokens={report['usage']['total_tokens']}，平均{report['average_latency_ms']:.2f}ms。"
            'run1原21/21原文件不覆盖。唯一差异aw-07的“产品编号”可指productid或productnumber，当前gold取前者、真实回答取后者；'
            '人工明确前不改标签或强制prompt，不能直接称系统业务错误。\n\n'
            '[run2实际报告](../../eval/reports/d3-aw-live-dev-run2/report.json)、'
            '[run2保存响应独立观测](../../eval/reports/d3-aw-live-dev-run2/schema-observation.json)、'
            '[新增AI观察](../../eval/reports/d3-ai-review/aw-run2-additional-observation.md)。'
            f"21/21都执行在AW，21/21召回gold表，真实schema阶段平均{observation['average_actual_schema_latency_ms']:.2f}ms。\n")
    registry_path = ROOT / 'eval/artifacts/d3/a/A-evidence-registry.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    for name in (RUN + '/report.json', RUN + '/schema-observation.json', OUTPUT + '.json', 'eval/reports/d3-acceptance/A待人工核对表.json'):
        registry[name] = {'sha256': sha(name), 'bytes': (ROOT / name).stat().st_size}
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding='utf-8')
    command = {'command': [sys.executable, '-B', *sys.argv], 'exit_code': 0, 'mode': 'Preserved files only; no model/DB requests',
               'additional_observation': OUTPUT + '.json', 'human_status_unchanged': 'pending_human_review'}
    (ROOT / 'eval/artifacts/d3/a/aw-run2-additional-observation-command.json').write_text(json.dumps(command, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'strict_ex': [report['correct'], report['prediction_count']], 'new_reference_condition': 'aw-07', 'raw_unchanged': sha(RUN + '/responses.jsonl') == result['evidence_sha256'][RUN + '/responses.jsonl']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
