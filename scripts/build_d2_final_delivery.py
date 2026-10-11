"""Write a new D2 close-out report; never overwrite the original acceptance."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'eval/reports/d2-final'


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def rows(name):
    return [json.loads(line) for line in (ROOT / name).read_text(encoding='utf-8').splitlines() if line]


def link(name, label=None):
    path = ROOT / name
    if not path.exists():
        raise FileNotFoundError(name)
    return f'[{label or name}]({Path(os.path.relpath(path, OUT)).as_posix()})'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rag-version', required=True)
    parser.add_argument('--ui-run', required=True)
    args = parser.parse_args()
    artifact = 'eval/artifacts/d2-final'
    rag_dir = f'{artifact}/rag/regression-{args.rag_version}'
    index_revision = args.rag_version if (ROOT / f'{artifact}/rag/rebuild-{args.rag_version}').exists() else 'v4.3'
    sql = read(f'{artifact}/nl2sql/v1/report.json')
    robust = read(f'{artifact}/robust/v1/report.json')
    rag = read(f'{rag_dir}/report.json')
    first = read(f'{artifact}/rag/first-review-{args.rag_version}.json')
    second = read(f'{artifact}/rag/second-review-{args.rag_version}.json')
    ui = read(f'{artifact}/ui/browser/{args.ui_run}/report.json')
    preflight = read(f'{artifact}/preflight-final.json')
    original = read(f'{artifact}/protected-originals-before.json')
    changed = [name for name, digest in original['files'].items()
               if not (ROOT / name).is_file() or sha256((ROOT / name).read_bytes()).hexdigest() != digest]
    protection = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
                  'original_file_count': len(original['files']), 'changed_paths': changed,
                  'status': 'PASS' if not changed else 'FAILED',
                  'holdout_predictions_this_stage': 0, 'operation': 'hash only; no heldout question content'}
    (ROOT / artifact / 'protected-originals-after.json').write_text(json.dumps(protection, ensure_ascii=False, indent=2), encoding='utf-8')
    records = sorted((ROOT / artifact / 'commands').glob('*-d2-final-module-final.json'))
    command = read(records[-1].relative_to(ROOT))
    stdout = (ROOT / command['output']).read_text(encoding='utf-8')
    match = re.search(r'(\d+) passed.*?in ([\d.]+)s', stdout)
    if changed or preflight['status'] != 'PASS' or ui['status'] != 'PASSED' or command['exit_code'] or not match:
        raise RuntimeError('Protection, module or UI checks have not passed; report cannot claim completion.')
    module_count, module_time = int(match[1]), float(match[2])
    usage, calls = Counter(), 0
    for directory in [f'{artifact}/nl2sql/v1', f'{artifact}/robust/v1', rag_dir]:
        for row in rows(directory + '/responses.jsonl'):
            for step in (row.get('response') or {}).get('steps', []):
                if step['name'] == 'llm':
                    calls += 1
                    usage.update({key: step.get('output_summary', {}).get('usage', {}).get(key, 0) or 0
                                  for key in ('prompt_tokens', 'completion_tokens', 'total_tokens')})
    summary = {'title': 'D2原清单九项逐项验收与证据', 'revision': 'user-audit-closeout',
               'created_at_utc': datetime.now(timezone.utc).isoformat(),
               'baseline_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'working_tree_dirty': True, 'python': '3.12.10', 'model': 'deepseek-flash',
               'status': 'IMPLEMENTED_AND_TESTED_WITH_EXPLICIT_REVIEW_LIMITS',
               'sql': {'correct': sql['correct'], 'count': sql['prediction_count']},
               'robust': {'correct': robust['correct'], 'count': robust['prediction_count'],
                          'uncompleted_id': 'robust-06', 'reason': 'approved candidate requires user confirmation'},
               'rag': {'report': rag, 'first_review': first, 'second_review': second},
               'module': {'passed': module_count, 'seconds': module_time, 'output': command['output']},
               'ui': {'status': ui['status'], 'cases': len(ui['cases']), 'api_probes': len(ui.get('api_only_cases', []))},
               'protection': protection, 'alias_policy': {'approved': 54, 'approved_candidate': 25, 'pending': 2},
               'review': {'user_attestation': 'agreed with prior D2 AI audit conclusions',
                          'new_gold_revisions_pending': ['sql-38', 'robust-23'], 'A_B_signatures_added': False,
                          'rag_current_predictions_human_signed': False},
               'final_dev_benchmark_usage_only': {'api_requests': 77, 'llm_steps': calls, **usage},
               'holdout_prediction_count': 0}
    lines = ['# D2原清单九项逐项验收与证据', '',
             '**本次交付：按用户已共同审计的结论完成 D2 收尾修正、实际回归和可携带证据包。原 D1/D2 报告、题库与日志不覆盖。**', '',
             '执行日期为 2026-10-11；真实命令保存 UTC 时间。项目继续使用 Python 3.12.10、已验证的 DeepSeek `deepseek-flash`、既有 Chinook 与只读 `qa_reader`。不重导或重建 Chinook。', '',
             '| 实测维度 | 本轮实际结果 | 含义与限制 |', '|---|---|---|',
             f"| SQL 开发题 | {sql['correct']}/{sql['prediction_count']}（{sql['exploratory_ex']:.2%}） | 34 项原 gold 有用户审计接受依据；sql-38 新修订仍待人审 |",
             f"| 鲁棒开发题 | {robust['correct']}/{robust['prediction_count']}（{robust['exploratory_ex']:.2%}） | robust-06 进入最小澄清，按原 EX 计未通过；robust-23 新修订待人审 |",
             f"| RAG 开发题 | 21 次请求；可答 Hit@5 {rag['hit_at_5']['passed']}/{rag['hit_at_5']['denominator']}；不足拒答 {rag['insufficient_handling']['passed']}/{rag['insufficient_handling']['denominator']} | 页/片段命中不代表整句正确；答案与引用另做两遍原文审核 |",
             f"| RAG 实际执行状态 | {json.dumps(rag['api_status_counts'], ensure_ascii=False)} | FAILED 仍计入21题，不用历史成功结果覆盖；逐项语义结论见两遍审核 |",
             f"| 更严格引文诊断 | {rag['exact_gold_quote_hit_at_5']['passed']}/{rag['exact_gold_quote_hit_at_5']['denominator']} | 完整 gold 引文是否位于一个 Top5 片段 |",
             f'| 模块回归 | {module_count} passed，{module_time:.2f} 秒 | 真实 pytest 输出；mock 与真实 API 证据各自标明 |',
             f"| 页面联调 | {len(ui['cases'])} 个实际场景，状态 {ui['status']} | 原始 API、DOM 与未加工截图对应同一 trace |",
             f"| 历史保护 | {len(original['files'])} 个原文件哈希未变，11 表内容未变 | 保留集 33 题预测仍为 0，D5 冻结后再测 |", '',
             '用户明确表示“我们审计了和你的这个意见一样”。本轮保存该授权原文、原审计哈希及具体采用范围，54 个别名关系直接使用、25 个只作条件候选、2 个继续停用。接受候选关系不等于接受唯一自动绑定。不会补写 A/B 签名或确认日期，也不会改旧审核表的历史状态。', '',
             'RAG 本轮新输出仍属于自动评测／AI预审结果，先前用户接受的历史答案不能代替对本轮新输出的人签。章节未知时明确返回空列表；页和块框定位与章节判断分别记录。', '',
             '## 原清单逐项验收', '']
    sections = [
        ('D2-01 / A1', '值索引、LLM 别名初稿经人工审核、拼音和向量。',
         '复用原值索引实现，在独立审核版 CSV 和独立索引目录应用用户确认范围。34 个低基数文本列产生 5528 标准值记录，增加 79 条通过或条件候选关系，总 5607 条、1024 维真实 BGE-M3 向量。25 条候选关系保留 candidate_only，不因精确、拼音或 LLM 裁决自动唯一绑定；2 条证据不足不入运行索引。',
         ['scripts/build_value_index.py', 'qa_agent/nlu/value_index.py', 'data/aliases/aliases-d2-reviewed.csv', 'scripts/finalize_d2_review.py'],
         '只读 DISTINCT 与实际编码、向量形状/有限值/归一化检查；candidate-only 精确和别名拼音回归。构建实跑耗时与候选计数保存在审计 JSON。',
         [f'{artifact}/value-index-build.json', f'{artifact}/review/user-attestation-and-revisions.json', 'tests/test_d2_final_nlu.py'],
         '2 条证据不足保留 pending；25 条候选必须在查询语境中澄清，不能批量改为自动绑定。'),
        ('D2-02 / A2', '五级 linker、补丁式 rewrite、绑定硬约束传给 SQL。',
         '精确→拼音→字符→向量→受限 LLM 级联沿用 D1/D2 链路。修复“你好、帮忙、来自”等前缀被算进实体 span 的问题，补丁只替换实体文本。conditional_alias 的候选关系在所有选择路径保留歧义保护，不能由最终模型自动消除人工设定的条件。',
         ['qa_agent/nlu/linker.py', 'qa_agent/nlu/rewrite.py', 'qa_agent/pipeline.py', 'qa_agent/sql/validator.py'],
         '4 个新局部回归与原 NLU、SQL 绑定校验测试；真实鲁棒开发21题和页面拼写纠错。保留不存在值边界，失败题不删、不改 gold。',
         ['tests/test_d2_final_nlu.py', f'{artifact}/robust/v1/responses.jsonl', f'{artifact}/ui/browser/{args.ui_run}/report.json'],
         'D2 只能发起澄清，完整会话续接属于随后 D3；robust-06 当前未完成查询，如实计未通过。'),
        ('D2-03 / A3', '单表 50 题、鲁棒 30 题，标准 SQL 及结果。',
         '沿用原 50/30 题与家族划分；读取先按 split 筛出的35/21开发视图。原 sql-38 最大值排序补 NULLS LAST；robust-23 将缺少先行范围的“这批”改为“全部曲目”，各保存新修订而不覆盖原题。56 个开发标签逐条只读执行，记录实际结果与原标签哈希。',
         ['eval/build_d2_sql_datasets.py', 'scripts/finalize_d2_review.py', f'{artifact}/review/sql-dev-v1.jsonl', f'{artifact}/review/robust-dev-v1.jsonl'],
         '结构、split 和同源 gold 检查；56 条真实标准查询和结果。原保留题只做元数据保护，不向被测系统产生预测。',
         [f'{artifact}/review/gold-readonly-results.jsonl', f'{artifact}/review/user-attestation-and-revisions.json'],
         'sql-38 与 robust-23 是新修订，仍需统一人审；其余54个开发参考答案沿用用户已审计接受范围。附件提供开发视图，保护保留题内容。'),
        ('D2-04 / A4', '按错误类型修正，目标 EX≥85%。',
         '修正候选启用边界、实体补丁 span、最大值排序 NULL 位置和已发现的原文定位错误；每次试验与错误日志保存独立版本。SQL 的通用生成约束增加降序最大值/TopN 的 NULLS LAST，不含题 ID 或答案。',
         ['qa_agent/sql/generator.py', 'qa_agent/nlu/linker.py', 'tests/test_d2_final_nlu.py', 'tests/test_d2_rag_locations.py'],
         f"SQL {sql['correct']}/35、鲁棒 {robust['correct']}/21，分别达到探索 EX≥85%；鲁棒唯一未通过是有条件别名要求澄清。新 gold 与本轮 RAG 输出的人审未完成，不发布正式独立泛化成绩。",
         [f'{artifact}/nl2sql/v1/report.json', f'{artifact}/robust/v1/report.json', f'{artifact}/commands/commands.jsonl'],
         '保留失败日志。合格阈值是本轮开发探索验收，不把用户原审计扩大成对全部新修改的人工签字。'),
        ('D2-05 / B1', 'trace 进入页面，每步时间线可以展开。',
         '沿用三面板、逐步输入/输出/耗时/状态、改写差异与引用原文；在当前最终 D2 服务实际操作五个场景，保存同 trace 原始响应、DOM 和截图。展开步骤仍复用会话内响应。',
         ['ui/app.py', 'api/main.py', 'scripts/capture_d2_demo.py', 'scripts/d2_capture_api.py', 'scripts/restart_services.ps1'],
         f"真实 Edge/Playwright 五场景 {ui['status']}；SQL表格、拼写补丁、PNG原文、证据不足与明确失败分别核验。展开前后 API POST 数保持不变，浏览器错误数 {len(ui['browser_errors'])}。",
         [f'{artifact}/ui/browser/{args.ui_run}/report.json', *ui['screenshots']],
         '截图来自实际页面，不拼装模拟；接口录制器仅保存脱敏测试输入与真实结果。'),
        ('D2-06 / B2', 'RRF 混合检索、引用编号及数字核验。',
         '保留指定文档筛选、BGE/BM25 两路与 RRF、真实 chunk ID、数值单位核验和受限再生成。此次增加原文布局一致性：OCR/原生文字与框使用同一来源，不跨栏/跨页继承不可靠标题，分离同块标题和正文，并正确识别混合字体标题。章节未知留空。',
         ['qa_agent/rag/retriever.py', 'qa_agent/rag/answer.py', 'qa_agent/rag/service.py', 'qa_agent/rag/parsers.py', 'qa_agent/rag/chunker.py'],
         '21 道真实模型请求；字面数值核验、引用 ID 成员校验与答案语义核对分开。两遍 AI 逐题核对原文，最终 PDF 页框截图可复核，块框不冒称逐词精确高亮。',
         [f'{rag_dir}/responses.jsonl', f'{artifact}/rag/first-review-{args.rag_version}.json', f'{artifact}/rag/second-review-{args.rag_version}.json', f'{artifact}/rag/location-check-{args.rag_version}/citation-location-check.json'],
         '数字出现不等于整句正确；答案/引用语义、页框、章节分别判定。任何条件通过或未知项以两遍报告具体结论为准，不能用 Hit@5 代替。'),
        ('D2-07 / B3', 'PDF/DOCX/HTML/MD/图片OCR，13份资料，manifest含来源格式许可。',
         '原13份注册资料和来源不改；重新解析6份原生PDF与1扫描派生件，长隐藏文本层的扫描页仍实际 OCR。26页真实 OCR，源文件/函数指纹校验后可复用。最终独立索引保留原索引，所有非 PDF 物理页为 null。',
         ['qa_agent/rag/parsers.py', 'qa_agent/rag/chunker.py', 'qa_agent/rag/index.py', 'scripts/rebuild_d2_rag_sources.py', 'data/docs/manifest.csv'],
         '13文档真实入库、1024维真实向量、解析错误0；大图扫描检测、CropBox坐标、双栏隔离和混合标题均有真实fixture回归。构建复用精确文本向量，不将复用计作重新模型推理。',
         [f'{artifact}/rag/rebuild-{index_revision}/docs-audit.json', f'{artifact}/rag/rebuild-{index_revision}/parse-events.json', f'{artifact}/rag/rebuild-{index_revision}/ocr-cache-fingerprints.json', 'tests/test_d2_rag_locations.py'],
         '扫描多栏阅读顺序和 OCR 本身仍有限制，按实际审计保留；PDF bbox为可见页坐标、左上原点、物理页从1开始，块框仅辅助查原文。'),
        ('D2-08 / B4', '2–3页DOCX指标手册，销售额/客单价/复购/热门曲目定义与SQL。',
         '直接复用原3页手册和 A/B 已共同同意的四项口径，不重新定义业务。发票销售额用 total，曲目/艺术家金额用明细；客单价为每张发票平均；指定期间至少两张发票为复购；热门曲目按购买数量，客户“谁买最多”保留金额，缺对象无全局默认。',
         ['data/docs/raw/d2/Chinook业务指标口径手册.docx', 'data/rules/metric_definitions.json', 'notes/d2/业务指标口径提案.md'],
         '复用已经实际执行的6段只读示例SQL和真实 Word 三页渲染，不把复用写成此轮重新制作或重新运行。来源、手册哈希与已确认机器规则一致。',
         ['eval/artifacts/d2/source/metric-human-review.json', 'eval/artifacts/d2/source/metric-sql-checks.json', 'eval/artifacts/d2/source/docx-authoring-audit.json'],
         '金额不自行补币种；具体 SQL题标签与指标口径是两个审核对象，四指标同意不代表每题 gold 自动通过。'),
        ('D2-09 / B5', 'RAG 30题＝20 OHR＋10自建，实际第一轮评测。',
         '沿用原官方 text QA、改写/自编题来源区分及21dev/9holdout；本次只对21开发题运行最终定位修复版。原 gold、历史回答与历史预审保存不变；新实际输出另存。',
         ['eval/d2_rag_eval.py', 'eval/rag_dataset.py', 'scripts/prepare_d2_rag_dataset.py'],
         f"最终真实21请求：Hit@5 {rag['hit_at_5']['passed']}/20、不足拒答 {rag['insufficient_handling']['passed']}/1、完整引文Top5 {rag['exact_gold_quote_hit_at_5']['passed']}/20。多轮定位修复的旧结果、首次构建路径异常保留，最新成绩只引用 {args.rag_version}。",
         [f'{rag_dir}/report.json', f'{rag_dir}/human_review.md', f'{artifact}/rag/first-review-{args.rag_version}.md', f'{artifact}/rag/second-review-{args.rag_version}.md'],
         '开发题来源和 gold 已有用户审计接受依据，原评测器旧字段仍显示历史 pending/draft，不追改历史记录；新回答未人签，9道保留预测0。')]
    for ident, requirement, implementation, files, method, evidence, pending in sections:
        lines += ['## ' + ident, '', '**要求：** ' + requirement, '', '**实现情况：** ' + implementation, '',
                  '**改动/复用文件：** ' + '；'.join(link(p) for p in files), '',
                  '**测试方法与实际结果：** ' + method, '',
                  '**证据位置：** ' + '；'.join(link(p) for p in evidence), '',
                  '**未完成事项或限制：** ' + pending, '']
    lines += ['## 错误记录、复现和保护', '',
              '真实命令、exit code和原始脱敏 stdout：' + link(f'{artifact}/commands/commands.jsonl') + '；最终模块输出：' + link(command['output']) + '。最初沙箱临时目录/数据库限制、错误测试路径、RAG构建路径异常与多轮章节修正均保留，不把失败或未运行写成通过。', '',
              '历史文件核验：' + link(f'{artifact}/protected-originals-after.json') + '；数据库与D1证据核验：' + link(f'{artifact}/preflight-final.json') + '。原33保留题没有调用被测系统，附件仅提供本轮开发材料。', '',
              f"最终77道开发请求的trace合计 {calls} 个LLM步骤、{usage['total_tokens']} total_tokens；这是最终三套跑批的用量，未含构建、重跑、页面和AI审核。报告不猜测费用。", '',
              '运行入口复用 `eval/run_eval.py`，开发集用 `--split dev --draft-gold` 和独立 `--dataset/--output-dir/--run-id`；具体已执行命令以命令 JSON 为准。RAG独立服务仅改变本机索引路径，正式8000已切到最终索引并完成页面验收。', '',
              '## 集中人工复核', '',
              '| 编号/范围 | 已做处理 | 仍需人工确认 |', '|---|---|---|',
              '| sql-38 | 新 gold 加 NULLS LAST，实际重跑 | 最大文件大小的 NULL 排序语义 |',
              '| robust-23 | 新题明确全部曲目，结果重跑 | 新措辞是否保留原预期业务 |',
              '| 25 条条件别名 | candidate_only已生效 | 按具体对象/语境选择，不是唯一绑定 |',
              '| 2 条证据不足别名 | 未启用 | 补可靠来源或拒绝 |',
              '| 本轮21个RAG回答及章节未知项 | 两遍AI原文审核、页框证据 | 新回答正确性、引用语义与章节未知的可接受性 |', '',
              '当前最终 RAG 完整回答的第二遍结论为 '+json.dumps(second['answer_verdicts'], ensure_ascii=False)+'。rag-03 参考期限正确，但实际模型两次只引期限片段并复述未在所引片段中的法规数字，被数字门禁拒绝，真实状态 FAILED。未把以前成功轮次挪作本轮答案。rag-15 五个能力和全文归属正确，当前所引列表不含机构归属，引用语义有条件通过。23条实际引用来源区域核对通过，9条章节未知单列；这些数值不等于21题全部答对。', '',
              '最后尝试的数量/期限精简提示只对 rag-03 实跑，仍失败；没有 v4.4 全套成绩，候选提示未改善已回退，仅保留试验文件与错误。当前源码与 v4.3 整套实际测试一致。', '',
              '这些项汇总在新报告，不给旧表填签名、不把新待审改 approved。后续 D3、专项各交付独立报告和待审清单。', '',
              '## 附件查看', '',
              '完整解压ZIP后打开同目录HTML，全部源码、测试、原始回答、日志、截图和13份原文使用项目内相对路径。查看报告无需密钥或服务。运行项目需按 README 在本地准备 Python3.12、模型和私密配置。ZIP不含真实.env、凭据、虚拟环境、模型权重、数据库卷或保留题；根目录 delivery-manifest.json 提供逐文件SHA。']
    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / 'D2原清单九项逐项验收与证据'
    content = '\n'.join(lines) + '\n'
    stem.with_suffix('.md').write_text(content, encoding='utf-8')
    stem.with_suffix('.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    from markdown_it import MarkdownIt
    body = MarkdownIt('commonmark').enable('table').render(content)
    css = 'body{max-width:1120px;margin:32px auto;padding:0 20px;font:16px/1.75 system-ui,Microsoft YaHei,sans-serif;color:#202830}table{width:100%;border-collapse:collapse}th,td{padding:9px;border:1px solid #ccd3da;text-align:left;vertical-align:top}th{background:#f2f5f8}h2{margin-top:36px}a{overflow-wrap:anywhere;color:#075eb1}pre{white-space:pre-wrap}code{font-family:Consolas,monospace}'
    stem.with_suffix('.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>D2原清单九项逐项验收与证据</title><style>'+css+'</style><body>'+body+'</body></html>', encoding='utf-8')
    rag_dev = [item for item in rows('eval/datasets/rag_single.jsonl') if item.get('split') == 'dev']
    (ROOT / artifact / 'review/rag-dev-view.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False)+'\n' for item in rag_dev), encoding='utf-8')
    include = ['README.md', 'requirements.txt', 'docker-compose.yml', '.env.example', 'api', 'ui', 'qa_agent',
               'data/catalog/chinook.yaml', 'data/rules', 'data/aliases/aliases-d2-reviewed.csv', 'data/docs/manifest.csv',
               'tests', artifact, 'eval/reports/d2-final', 'notes/d2/业务指标口径提案.md',
               'scripts/build_value_index.py', 'scripts/finalize_d2_review.py', 'scripts/rebuild_d2_rag_sources.py',
               'scripts/audit_d2_rag_locations.py', 'scripts/review_d2_rag_pass2.py', 'scripts/build_d2_final_delivery.py', 'scripts/package_stage_delivery.py',
               'scripts/restart_services.ps1', 'scripts/check_d2_preflight.py', 'scripts/d2_command.py',
               'scripts/capture_d2_demo.py', 'scripts/d2_capture_api.py', 'scripts/prepare_d2_rag_dataset.py',
               'eval/run_eval.py', 'eval/d2_rag_eval.py', 'eval/dataset.py', 'eval/rag_dataset.py', 'eval/metrics.py',
               'eval/build_d2_sql_datasets.py', 'eval/artifacts/d2/source/metric-human-review.json',
               'eval/artifacts/d2/source/metric-sql-checks.json', 'eval/artifacts/d2/source/docx-authoring-audit.json']
    import csv
    with (ROOT / 'data/docs/manifest.csv').open(encoding='utf-8-sig', newline='') as stream:
        for doc in csv.DictReader(stream):
            include.append(doc['path'])
            derived = doc.get('derived_from', '')
            if derived.startswith('data/') and (ROOT / derived).is_file():
                include.append(derived)
    manifest = {'stage': 'D2-final', 'entry_document': stem.with_suffix('.html').relative_to(ROOT).as_posix(),
                'include': include, 'exclude_prefixes': ['qa_agent/clarify/', 'qa_agent/sql/schema_linker.py',
                'qa_agent/sql/prompts/', 'tests/test_d3_', 'eval/reports/d2-final/package-verification.json']}
    (OUT / 'package-inputs.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'report': stem.relative_to(ROOT).as_posix(), 'modules': module_count,
                      'protected_originals': len(original['files']), 'ui': ui['status']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
