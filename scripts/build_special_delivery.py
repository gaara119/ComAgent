"""Build the ten-item 01/03 development delivery from preserved actual files.

This script makes no HTTP, model, or database requests and changes no labels,
runtime prompts, business code, aliases, or human approval fields. Missing runs
are reported as not run. Root supplies the actual version/regression paths.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
from hashlib import sha256
import html
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXP = "eval/experiments/after_d2_01_03"
TITLE = "①③专项造题与提示词优化-逐项验收与证据"
OUT = ROOT / EXP / "reports" / "acceptance"
PROTECTED = ["eval/datasets/sql_holdout", "eval/datasets/robust_holdout",
             "eval/datasets/rag_holdout", "eval/datasets/d3/clarify/protected_holdout/",
             "eval/datasets/nl2sql_chinook.jsonl", "eval/datasets/nl2sql_chinook_d2.jsonl",
             "eval/datasets/robust.jsonl", "eval/datasets/rag_single.jsonl", "eval/datasets/rag_ohr.jsonl",
             "eval/artifacts/d3/a/gold/holdout/", "eval/datasets/d3/aw_schema_link.holdout.jsonl",
             "eval/datasets/d3/aw_schema_link.jsonl", "eval/datasets/d3/aw_schema_link.v2.jsonl",
             "scripts/build_d3_aw_dataset.py", "scripts/build_d3_clarify_cases.py"]
D2_REGRESSION = {
    'sql': {'dataset': 'eval/artifacts/d2-final/review/sql-dev-v1.jsonl', 'count': 35,
            'suite': 'nl2sql', 'sha256': '7b4c18f203ce0d88f38837f0c788cbcff142b559dc70d3f281990a2d47175f35'},
    'robust': {'dataset': 'eval/artifacts/d2-final/review/robust-dev-v1.jsonl', 'count': 21,
               'suite': 'robust', 'sha256': '1d6c7732b5196e7146e3b3f01fe4f9ccb24ad354c6b20776631192c605d213f7'},
    'rag': {'dataset': 'eval/artifacts/d2-final/review/rag-dev-view.jsonl', 'count': 21,
            'suite': 'rag', 'sha256': '12b8cc7de87ea73bc60a2e9b7d527d0721956ef1bf4256ccf6a70331a7f57f63'},
}
D2_EVALUATION_SOURCES = ['eval/run_eval.py', 'eval/dataset.py', 'eval/metrics.py',
                         'eval/d2_rag_eval.py', 'eval/rag_dataset.py', 'eval/rag_metrics.py']
D2_REGRESSION_METHOD = [
    '三份修正版独立开发视图：SQL 35题、鲁棒21题、RAG 21题；显式 --dataset、--split dev、--draft-gold、唯一 --run-id 与新 --output。不得使用入口的默认混合题库。',
    'SQL/鲁棒沿用原D2结果EX：全局列映射、重复行保留，标签声明的有序结果保留顺序；连续数值按两位小数比较，整数列保持精确，NULL/零/空表区分。失败、超时和追问仍占所选题分母。',
    'RAG机械指标分开报告：20道可回答题的金标页/片段Hit@5和完整原文命中诊断，1道不可回答题的证据不足处理，以及21题引用所属文档/实际索引文字真实性；子串匹配不等同完整答案正确或语义忠实。',
    '专项评分使用其已冻结的精确Decimal及SQL语义合同；不把旧D2结果EX套作专项语义分数，也不以相同结果证明SQL业务含义正确。人工待核修正版仍是草稿探索回归。',
]


def local(name: str) -> Path:
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or any(path.relative_to(ROOT).as_posix().casefold().startswith(p.casefold()) for p in PROTECTED):
        raise ValueError("Unsupported or protected delivery path: " + name)
    if path.name.startswith('.env') and path.name != '.env.example':
        raise ValueError("Private environment files must not be read by this builder")
    return path


def digest(name: str) -> str:
    return sha256(local(name).read_bytes()).hexdigest()


def read(name: str):
    return json.loads(local(name).read_text(encoding='utf-8-sig'))


def save(name: str, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def link(name: str, label: str | None = None) -> str:
    target = local(name)
    if not target.is_file():
        raise FileNotFoundError("Missing linked evidence: " + name)
    return '[' + (label or name) + '](<' + Path(os.path.relpath(target, OUT)).as_posix() + '>)'


def prompt_sources(before: dict, after: dict) -> list[dict]:
    """Extract actual literal system arguments without importing business modules."""
    specs = [
        ('qa_agent/sql/generator.py', 'SQL_SYSTEM_PROMPT', 'assignment', 'SQL单表生成及技术修复', 'generate_sql → JsonLLM.complete_json; allow_joins=False'),
        ('qa_agent/nlu/linker.py', 'system_prompt', 'keyword', '有限合法候选值链接裁决', 'ValueLinker → JsonLLM.complete_json(system_prompt=...)'),
        ('qa_agent/rag/answer.py', 'prompt', 'assignment', '仅以实际检索证据作答并附编号引用', 'answer_from_chunks → JsonLLM.complete_json(prompt, payload, DocumentAnswer)'),
        ('qa_agent/rag/service.py', 'complete_json', 'first_argument', '中文问题在英文文档范围内的检索翻译', 'run_doc_qa → JsonLLM.complete_json(translation instruction, question, SearchTranslation)'),
    ]
    result = []
    target = OUT / 'runtime-system-prompts'
    target.mkdir(parents=True, exist_ok=True)
    for source, symbol, kind, duty, callsite in specs:
        tree = ast.parse(local(source).read_text(encoding='utf-8-sig'))
        candidates = []
        for node in ast.walk(tree):
            if kind == 'assignment' and isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == symbol for t in node.targets):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    candidates.append((node.lineno, node.value.value))
            elif kind == 'keyword' and isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == symbol and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        candidates.append((node.lineno, kw.value.value))
            elif kind == 'first_argument' and isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == symbol and node.args:
                if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    candidates.append((node.lineno, node.args[0].value))
        if len(candidates) != 1:
            raise ValueError(f"Expected one real literal system prompt for {source}:{symbol}, got {len(candidates)}")
        line, text = candidates[0]
        filename = source.replace('/', '__').removesuffix('.py') + '.txt'
        (target / filename).write_text(text, encoding='utf-8')
        result.append(dict(source_file=source, source_line=line, source_symbol=symbol,
                           extraction='Python AST literal; exact string value, no model invocation',
                           duty=duty, actual_callsite=callsite, text=text, delivery_file=(target / filename).relative_to(ROOT).as_posix()))
    for source, duty, callsite in [
        ('qa_agent/sql/prompts/multi_table.txt', 'AW多表SQL生成及技术修复', 'qa_agent/sql/generator.py: generate_sql, allow_joins=True'),
        ('qa_agent/clarify/prompts/intent_extract.txt', '语义条件和L0/L1/L2判断所需的意图抽取', 'qa_agent/clarify/extractor.py: extract_intent → JsonLLM.complete_json'),
        ('qa_agent/clarify/prompts/intent_patch.txt', '显式用户补充和后续修改对应的条件补丁', 'qa_agent/clarify/service.py: JsonLLM.complete_json(PATCH_PROMPT.read_text(...), ...)'),
    ]:
        text = local(source).read_text(encoding='utf-8')
        filename = source.replace('/', '__')
        (target / filename).write_bytes(local(source).read_bytes())
        result.append(dict(source_file=source, source_line=1, source_symbol=None,
                           extraction='Exact runtime prompt file bytes', duty=duty, actual_callsite=callsite,
                           text=text, delivery_file=(target / filename).relative_to(ROOT).as_posix()))
    for item in result:
        text = item.pop('text')
        source = item['source_file']
        item.update(character_count=len(text), utf8_bytes=len(text.encode('utf-8')),
                    extracted_text_sha256=sha256(text.encode('utf-8')).hexdigest(),
                    source_file_sha256_at_build=digest(source),
                    before_source_sha256=before.get('files', {}).get(source),
                    after_source_sha256=after.get('files', {}).get(source),
                    baseline_text_sha256=None,
                    baseline_text_sha256_note='Not inferred from whole-module hash; see baseline snapshot/diff for embedded strings',
                    user_payload_is_dynamic=True,
                    human_review_status='pending_human_review')
        if before.get('files', {}).get(source) == after.get('files', {}).get(source) == digest(source):
            item['baseline_text_sha256'] = item['extracted_text_sha256']
            item['baseline_text_sha256_note'] = 'Same source bytes in baseline/final/current; same literal or read_text string verified'
        if after.get('files', {}).get(source) and after['files'][source] != digest(source):
            raise ValueError('Prompt source differs from the declared final snapshot: ' + source)
    return result


def provider_system_messages(versions) -> list[dict]:
    """Save exact already-observed provider system content, including JSON Schema.

    Candidate response schemas can contain dynamically bounded legal IDs. Never
    reconstruct those from labels or claim a base business string is the entire
    provider message. Only the explicitly supplied development run is traversed.
    """
    target = OUT / 'runtime-system-prompts' / 'actual-provider-system'
    target.mkdir(parents=True, exist_ok=True)
    messages = {}
    for version in versions:
        manifest = version['paths'].get('run_manifest')
        if not manifest or not local(manifest).is_file():
            continue
        run = local(manifest).parent
        for capture in run.glob('cases/*/turns/*/provider/*.json'):
            relative = capture.relative_to(ROOT).as_posix()
            payload = read(relative)
            for message in (payload.get('request') or {}).get('messages', []):
                if message.get('role') != 'system' or not isinstance(message.get('content'), str):
                    continue
                text = message['content']
                checksum = sha256(text.encode('utf-8')).hexdigest()
                if checksum not in messages:
                    output = target / (checksum + '.txt')
                    output.write_text(text, encoding='utf-8')
                    messages[checksum] = dict(actual_system_sha256=checksum, character_count=len(text),
                        utf8_bytes=len(text.encode('utf-8')), delivery_file=output.relative_to(ROOT).as_posix(),
                        source='Exact saved provider request.messages[role=system].content; includes adapter JSON constraint and runtime JSON Schema',
                        observed_versions=[], capture_evidence=[])
                entry = messages[checksum]
                if version['version'] not in entry['observed_versions']:
                    entry['observed_versions'].append(version['version'])
                entry['capture_evidence'].append({'file': relative, 'sha256': digest(relative)})
    return sorted(messages.values(), key=lambda item: item['actual_system_sha256'])


def load_versions(inputs):
    versions = []
    seen = set()
    for entry in inputs.get('versions', []):
        name = entry['version']
        if name not in {'V0', 'V1', 'V2'} or name in seen:
            raise ValueError('Only one actual run per supplied V0/V1/V2 version is allowed')
        seen.add(name)
        paths = {key: entry.get(key) for key in ('score', 'run_manifest', 'code_snapshot', 'freeze', 'restart_record', 'errors', 'command', 'changes', 'provider_supplement', 'semantic_review')}
        actual = {key: read(path) if path and local(path).is_file() and key in ('score', 'run_manifest', 'code_snapshot', 'freeze', 'restart_record', 'provider_supplement') else None for key, path in paths.items()}
        score = actual['score']
        if score:
            if score.get('version') != name:
                raise ValueError('Version mismatch in score: ' + paths['score'])
            if score.get('labels_sha256') != digest(EXP + '/data/cases-v6-reviewed.jsonl'):
                raise ValueError('Actual score label SHA does not match the unchanged final preparation labels')
            summary = score['summary']
            completion = summary['groups']['all']
            statuses = [c.get('outcome', '') for c in score.get('cases', [])]
            finished = bool(len(score.get('cases', [])) == 60 and not any(s in {'not_started', 'running'} for s in statuses))
        else:
            summary, completion, finished = None, None, False
        supplement = actual.get('provider_supplement')
        archive = {'original_automatic_archive_count': summary.get('provider_captures_archived') if summary else None,
                   'verified_supplement_capture_count': supplement.get('verified_captures') if supplement else None,
                   'unverified_supplement_capture_count': supplement.get('unverified_captures') if supplement else None,
                   'protected_original_evidence_unchanged': supplement.get('protected_evidence_unchanged') if supplement else None,
                   'supplement_model_calls': supplement.get('model_calls') if supplement else None,
                   'supplement_api_calls': supplement.get('api_calls') if supplement else None,
                   'note': 'Original run/checkpoint/score remains unchanged; exact original provider requests copied only after trace, path and SHA verification. This does not add predictions or change the score.'}
        versions.append({'version': name, 'paths': paths, 'artifacts': actual, 'summary': summary,
                         'provider_archive': archive,
                         'completion': completion, 'actual_run_complete': finished,
                         'status': '实际运行并评分' if score else '未运行或缺少实际评分证据'})
    if not versions or versions[0]['version'] != 'V0':
        raise ValueError('V0 must be the first supplied version')
    if [v['version'] for v in versions] != sorted([v['version'] for v in versions]):
        raise ValueError('Actual versions must be supplied in chronological V0/V1/V2 order')
    return versions


def regression_check(group, entry):
    """Verify completed developer-only results, without generating predictions."""
    expected = D2_REGRESSION[group]
    issues = []
    dataset = entry.get('dataset') or expected['dataset']
    if not local(expected['dataset']).is_file():
        issues.append('immutable developer-view file missing')
    elif digest(expected['dataset']) != expected['sha256']:
        issues.append('immutable developer-view SHA mismatch')
    if dataset != expected['dataset']:
        issues.append('immutable developer-view path/SHA mismatch')
    path = entry.get('report')
    if not path or not local(path).is_file():
        return {'complete': False, 'issues': issues + ['actual report missing'], 'expected': expected}
    report = read(path)
    provenance = report.get('provenance') or {}
    checks = {
        'status': report.get('status') == 'COMPLETED',
        'suite': report.get('suite') == expected['suite'],
        'split': report.get('split') == 'dev',
        'selected_count': report.get('selected_count') == expected['count'],
        'prediction_count': report.get('prediction_count') == expected['count'],
        'holdout_prediction_count': report.get('holdout_prediction_count') == 0,
        'dataset_sha256': provenance.get('dataset_sha256') == expected['sha256'],
        'draft_gold': provenance.get('gold_review') == 'draft',
        'command_file': bool(entry.get('command') and local(entry['command']).is_file()),
    }
    issues += ['failed actual evidence check: ' + key for key, passed in checks.items() if not passed]
    return {'complete': not issues, 'checks': checks, 'issues': issues, 'expected': expected}


def readiness(inputs):
    missing = []
    for index, entry in enumerate(inputs.get('versions', [])):
        for field in ('score', 'run_manifest', 'code_snapshot', 'freeze', 'restart_record', 'command', 'errors'):
            if not entry.get(field) or not local(entry[field]).is_file():
                missing.append(f"versions[{index}].{field}")
        if entry.get('score') and local(entry['score']).is_file():
            score = read(entry['score'])
            cases = score.get('cases', [])
            if len(cases) != 60 or any(case.get('outcome', '') in {'not_started', 'running'} for case in cases):
                missing.append(f"versions[{index}].completed_60_case_score")
            observed = score.get('summary', {}).get('provider_attempts_observed_in_api_steps', 0)
            archived = score.get('summary', {}).get('provider_captures_archived', 0)
            if observed > archived:
                supplement_path = entry.get('provider_supplement')
                supplement = read(supplement_path) if supplement_path and local(supplement_path).is_file() else {}
                if not (supplement.get('verified_captures') == observed
                        and supplement.get('unverified_captures') == 0
                        and supplement.get('protected_evidence_unchanged') is True
                        and supplement.get('dry_run') is False
                        and supplement.get('model_calls') == 0
                        and supplement.get('api_calls') == 0):
                    missing.append(f"versions[{index}].verified_original_provider_supplement")
    if not inputs.get('versions'):
        missing.append('versions[V0]')
    for field in ('version_decisions', 'restore_instructions', 'regression_summary', 'manual_review'):
        if not inputs.get(field) or not local(inputs[field]).is_file():
            missing.append(field)
    regression_checks = {}
    for group in ('sql', 'robust', 'rag'):
        entry = inputs.get('regression', {}).get(group, {})
        regression_checks[group] = regression_check(group, entry)
        if not regression_checks[group]['complete']:
            missing.append('regression.' + group + '.completed_dev_report_and_command')
    return {'ready': not missing, 'missing_actual_evidence': missing,
            'regression_evidence_checks': regression_checks, 'prediction_calls': 0}


def metric_table(version):
    summary = version['summary']
    if not summary:
        return [f"{version['version']}：未运行或未取得原始评分文件；无实测分数。"]
    lines = [f"{version['version']}：API实际请求{summary['api_post_requests']}次；模型provider观测{summary['provider_attempts_observed_in_api_steps']}次；原始token {json.dumps(summary['provider_token_usage_observed'], ensure_ascii=False)}；缺usage {summary['provider_attempts_without_usage']}次；API耗时之和{summary['api_latency_ms_observed']}ms（不等于墙钟时间）。"]
    archive = version['provider_archive']
    lines.append(f"{version['version']} provider归档：原运行器自动归档{archive['original_automatic_archive_count']}条；独立合法补充归档已核验{archive['verified_supplement_capture_count'] if archive['verified_supplement_capture_count'] is not None else '未取得补充证据'}条；未核验{archive['unverified_supplement_capture_count'] if archive['unverified_supplement_capture_count'] is not None else '未知'}条。原始评分/检查点不改，补充归档不新增模型或API调用。")
    for group in ('all', 'task:01', 'task:03'):
        current = summary['groups'].get(group)
        if current:
            lines.append(f"{group}：自动确认正确{current['confirmed_correct']}/{current['scorable_tasks']}可评分；总题{current['total_tasks']}；自动失败{current['automatic_failed']}；语义待AI复核{current['semantic_AI_pending']}；标签待确认{current['pending_annotation']}。")
    return lines


def record(number, requirement, implementation, files, methods, results, evidence, pending, status):
    return dict(number=number, requirement=requirement, implementation=implementation,
                changed_or_related_files=files, test_method_and_commands=methods, actual_results=results,
                evidence=evidence, pending_or_limitations=pending, verdict=status,
                human_review_status='pending_human_review')


def build(inputs):
    OUT.mkdir(parents=True, exist_ok=True)
    prep = read(EXP + '/reports/data-preparation-summary.json')
    usage = read(EXP + '/reports/preparation-usage.json')
    versions = load_versions(inputs)
    baseline = versions[0]
    selected_name = inputs.get('selected_final_version') or versions[-1]['version']
    matches = [version for version in versions if version['version'] == selected_name]
    if len(matches) != 1:
        raise ValueError('selected_final_version must name one of the actual supplied versions')
    final = matches[0]
    before = baseline['artifacts']['code_snapshot'] or {}
    after = final['artifacts']['code_snapshot'] or {}
    prompts = prompt_sources(before, after)
    actual_system = provider_system_messages(versions)
    adapter = {'source_file': 'qa_agent/llm.py', 'actual_callsite': 'JsonLLM.complete_json',
               'composition': 'system_prompt + "\\n只输出一个 JSON 对象，不输出 Markdown。字段遵守以下 JSON Schema：\\n" + json.dumps(response_model.model_json_schema(), ensure_ascii=False)',
               'source_file_sha256_at_build': digest('qa_agent/llm.py'),
               'before_source_sha256': before.get('files', {}).get('qa_agent/llm.py'),
               'after_source_sha256': after.get('files', {}).get('qa_agent/llm.py'),
               'schema_is_dynamic': True,
               'retry_note': 'Format-validation retry appends a user-role correction message; original system content remains intact.'}
    provider_character_range = ({'minimum': min(p['character_count'] for p in actual_system),
                                 'maximum': max(p['character_count'] for p in actual_system)} if actual_system else None)
    save('runtime-system-prompts/inventory.json', {'created_at_utc': datetime.now(timezone.utc).isoformat(),
         'purpose': 'Actual project DeepSeek system instructions; not Codex hidden system instructions',
         'prompts': prompts, 'fixed_business_system_template_count': len(prompts),
         'total_characters_of_business_templates': sum(p['character_count'] for p in prompts),
         'json_adapter': adapter, 'actual_provider_system_messages': actual_system,
         'exact_observed_system_variants': len(actual_system),
         'actual_provider_system_character_range': provider_character_range,
         'dynamic_payload_note': 'RAG question/evidence, catalog, legal candidates, current intent/state, and repair feedback are assembled at runtime. These are not one universal static system prompt.',
         'minimum_length_required': False, 'model_calls': 0})
    records = []
    def exp(suffix):
        return EXP + '/' + suffix
    def exists(paths):
        return [p for p in paths if p and local(p).is_file()]
    labels = exp('data/cases-v6-reviewed.jsonl')
    manual_stats = None
    manual_path = inputs.get('manual_review')
    if manual_path and local(manual_path).is_file():
        manual_json = manual_path if manual_path.endswith('.json') else str(Path(manual_path).with_suffix('.json')).replace('\\', '/')
        if local(manual_json).is_file():
            manual = read(manual_json)
            if (manual.get('labels_sha256') != digest(labels)
                    or len(manual.get('cases', [])) != 60
                    or manual.get('selected_final_version') != selected_name
                    or any(case.get('human_review', {}).get('status') != 'pending_human_review' for case in manual['cases'])):
                raise ValueError('Unified manual review must preserve all60 pending-human cases, frozen labels, and the actual selected final version')
            manual_stats = manual['summary']
    all_runtime = [p for v in versions for p in v['paths'].values() if p and local(p).is_file()]
    runtime_methods = [v['paths']['command'] for v in versions if v['paths']['command'] and local(v['paths']['command']).is_file()]
    ready = readiness(inputs)
    records.append(record(1, '项目与数据核查说明：复用现有数据库、schema、已确认口径和别名，保护保留集',
        '项目材料、真实只读源事实与出网内容都有独立manifest；本轮数据全部标为合成dev。',
        [exp('scripts/prepare_data.py')], ['既有qa_reader、只读事务及5000ms超时核对实际schema/实体/年份；程序和AI审查请求payload。'],
        [f"合成候选{prep['dataset_total']}条，规范化题面{prep['unique_inputs']}个；不宣称独立泛化。", '历史根上下文可能接触保留信息的限制已披露；本轮不读取保留内容、不生成保留预测。'],
        [exp('reports/project-data-check.md'), exp('materials/source_manifest.json'), exp('materials/readonly_live_facts.json'), exp('materials/outbound_payload_audit.json')],
        ['正式独立保留集由D5冻结后按总计划执行；AI不是人工审核。'], '已取得实际核查证据'))
    records.append(record(2, '①/③真实造题prompt及自动复核规则', '保留生成、修正、显式目标SQL标注及两遍独立审读prompt和实际request/response/trace。',
        [exp('prompts/generate-01.txt'), exp('prompts/generate-03.txt'), exp('prompts/review-p1.txt'), exp('prompts/review-p2.txt')],
        ['用同一已验证deepseek-flash适配调用；每logical call最多3次尝试；不同AI复核上下文独立读题。'],
        ['原始pilot提示词恢复有SHA证明；生成/审核不调用被测问答接口。', '双AI存在漏检及引用不存在后续turn的幻觉，原意见保留，来源守卫另记。'],
        [exp('materials/original-prompt-recovery.json'), exp('checks/ai-pass-1.json'), exp('checks/ai-pass-2.json'), exp('checks/ai-review-quality-notes.json'), exp('reports/preparation-stage-usage.json')],
        ['49可评分与11待确认分开；两遍AI建议不能代替人工签字。'], '实际调用与审核证据已保存'))
    records.append(record(3, '生成脚本、类别配额、最终题库、参考依据与审核状态', '先20题pilot，再扩展40题；保留原始、失败、回收、格式修订、gold补齐及最终来源守卫。',
        [exp('scripts/prepare_data.py'), labels, exp('data/family-metadata.json')], ['参考SQL只通过现有只读账号执行；先程序再独立AI两遍；重复与争议保留。'],
        [f"候选{prep['dataset_total']}，可评分{prep['scorable']}，待确认{prep['pending_confirmation']}，全部人工待核{prep['all_human_pending']}。", '候选①30/③30与目标类别吻合；合格可评分①26/③23，部分合格类别配额不足，不能写成60题全部验收通过。'],
        [exp('reports/data-preparation-summary.json'), exp('checks/program-normalized-v4.json'), exp('checks/final-source-guards.json'), exp('reports/preparation-final-report.md'), exp('checks/root-family-metadata.json')],
        ['11个争议/重复/来源或分类冲突候选待人工决定；不在被测结果之后改标签刷分。'], '候选生成完成；可评分覆盖与人工状态有明确限制'))
    baseline_evidence = exists(list(baseline['paths'].values()))
    records.append(record(4, 'V0真实基线原始输出、评分及错误清单', '固定代码/prompt/配置/标签/评分协议；独立真实会话请求，只发送用户信息和当前询问对应的合法补充。',
        [exp('runtime_eval/runner.py'), exp('runtime_eval/scorer.py'), exp('runtime_eval/controller.py')],
        runtime_methods[:1] or ['未取得实际运行命令。'], metric_table(baseline), baseline_evidence,
        ['待确认标签无binary correctness；AST无法证明的等价SQL另记AI_pending；失败、超时及未实现不从分母删除。'],
        '真实基线已记录' if baseline['actual_run_complete'] else '未运行完或证据不足'))
    optimization = versions[1:]
    decisions = inputs.get('version_decisions')
    records.append(record(5, '实际采用V1/V2提示词/代码差异及原始结果；最多两轮优化',
        f"V1仅提示词；V2按实际失败原因选择提示词修订或一项局部代码修复。实际保留版本为{selected_name}；试验轮次即使回退也保留原始结果，是否采用、保留或回退以版本决策及diff为准。",
        ['scripts/build_special_delivery.py'] + [p['source_file'] for p in prompts], runtime_methods[1:] or ['本报告不自行执行优化或预测。'],
        [line for version in optimization for line in metric_table(version)] or ['没有实际V1/V2成绩；不为凑轮次虚构优化。'],
        exists([decisions] + [p for v in optimization for p in v['paths'].values()]),
        ['无V1/V2若有实际原因记录，不等于完成两轮优化；优化收益与局部代码修复分别说明。'],
        '实际版本记录已提供' if decisions and local(decisions).is_file() else '缺少实际优化决策记录'))
    regressions = inputs.get('regression', {})
    reg_results, reg_evidence = [], []
    for group in ('sql', 'robust', 'rag'):
        item = regressions.get(group, {})
        file = item.get('report')
        if file and local(file).is_file():
            report = read(file)
            observed = {key: report[key] for key in ('status', 'split', 'draft_gold', 'selected_count', 'total', 'prediction_count', 'holdout_prediction_count', 'correct', 'exploratory_ex', 'ex', 'passed', 'successful', 'answer_correct', 'citation_correct', 'hit_at_5', 'exact_gold_quote_hit_at_5', 'insufficient_handling', 'mechanical_metrics', 'gold_human_accepted_count', 'answer_human_review_count', 'error_types', 'failure_categories', 'api_status_counts', 'segments', 'usage', 'metrics', 'summary', 'blockers') if key in report}
            reg_results.append(group + '实际报告：' + (json.dumps(observed, ensure_ascii=False) if observed else '报告存在但统计字段未被本构建器识别；请读原报告，不能推断分数或通过状态。'))
            check = ready['regression_evidence_checks'][group]
            reg_results.append(group + '已完成且视图/分母匹配核验：' + json.dumps(check, ensure_ascii=False))
            reg_evidence.append(file)
            reg_evidence += exists([item.get('command')])
        else:
            reg_results.append(group + '开发集回归未运行或实际报告缺失。')
    records.append(record(6, '修改前后对照与既有D2 SQL/鲁棒/RAG开发集回归', '复用原D2修正版独立开发视图与既有评分入口，原始D1/D2报告和标签不覆盖；保留集不运行。',
        [exp('runtime_eval/scorer.py')] + D2_EVALUATION_SOURCES + [r['dataset'] for r in D2_REGRESSION.values()],
        D2_REGRESSION_METHOD + ([r.get('command') for r in regressions.values() if r.get('command')] or ['未取得实际回归命令。']),
        metric_table(baseline) + metric_table(final) + reg_results,
        exists([inputs.get('regression_summary'), decisions, exp('reports/d2-regression-cli-check.json'), exp('reports/d2-regression-cli-and-scoring.md')]) + reg_evidence,
        ['自动成绩仅描述本轮合成dev；AI_pending/缺usage/原模块不足须保留；没有实际跑完的回归不得填通过。'],
        '三组真实开发回归已完成；结果EX/机械指标与语义审核分开' if all(r['complete'] for r in ready['regression_evidence_checks'].values()) else '回归未完成或视图/计数/原始命令证据不完整'))
    report_name = (OUT / (TITLE + '.json')).relative_to(ROOT).as_posix()
    records.append(record(7, '《①③专项造题与提示词优化-逐项验收与证据》', '本文件按原文10项分别给要求、实现、源码、方法、真实结果、证据与未完成事项。',
        ['scripts/build_special_delivery.py'], ['仅读取明确路径的原始文件构建；不调用API、模型或DB。'],
        ['各版本分母/争议/失败/未运行与人工待核独立列出；报告自身不代替验收签字。'], [], ['ZIP内链接另由打包校验器新解压核对。'], '已生成可审阅报告'))
    records.append(record(8, '可复现命令、真实路径、恢复说明及运行时prompt交付',
        '附实际运行命令、冻结与装载证明、代码SHA和恢复说明；AST提取嵌入源码的真实system字符串，直接复制文件型prompt。',
        ['scripts/build_special_delivery.py', exp('runtime_eval/snapshot.py'), exp('runtime_eval/README.md')],
        ['AST静态提取，不导入业务模块、不执行prompt；抽取的字符和UTF-8字节逐项记录。'],
        [f"业务system模板{len(prompts)}份，共{sum(p['character_count'] for p in prompts)}字符；真实已归档provider完整system消息{len(actual_system)}个去重版本（包含适配器JSON约束及动态Schema）；完整消息字符数范围{json.dumps(provider_character_range, ensure_ascii=False) if provider_character_range else '未取得实际SYSTEM capture，不能推算'}；未填充字数。", 'RAG问题/检索证据、真实目录/候选和当前意图属于动态user payload；不冒称存在一个固定万能prompt。'],
        exists([inputs.get('restore_instructions')]) + [exp('reports/preparation-reproduction.md'), exp('runtime_eval/README.md'), exp('reports/acceptance/runtime-system-prompts/inventory.json')] + [p['delivery_file'] for p in prompts],
        ['嵌入式prompt前版本字符SHA仅在源文件字节相同且匹配冻结快照时认定相同，否则提供模块SHA+实际diff，不猜旧字符串SHA。'], 'prompt原文合集已提取；运行与恢复以实际输入记录为准'))
    records.append(record(9, '待人工确认及未实现功能清单', '保留全部人工状态，列明重复、口径、控制器冲突与AI漏检；运行时剩余问题由各版本错误清单与03功能差距报告提供。',
        [labels, exp('checks/final-source-guards.json'), 'scripts/build_special_review.py'], ['先程序+AI两遍，最后留给用户统一核对；无A/B签名与人工日期；参考判断、实际回答、控制器和原评分分别展示。'],
        [f"全部{prep['all_human_pending']}个人工pending；{prep['pending_confirmation']}个原标签争议不能强制评分。"]
        + ([f"统一表实际保留{manual_stats['original_cases']}个原编号、冻结{manual_stats['frozen_scorable']}/{manual_stats['original_annotation_pending']}分组；新增参考争议{len(manual_stats['new_reference_disputes_beyond_original11'])}项、控制器/协议争议{len(manual_stats['new_controller_or_protocol_disputes'])}项另列，未替换原自动分数。"] if manual_stats else ['统一逐题表未取得完整JSON核验材料，不能宣称已核对全部条目。']),
        [exp('reports/preparation-final-report.md'), exp('checks/ai-review-quality-notes.json')] + exists([inputs.get('manual_review'), inputs.get('feature_gaps')]),
        ['待人工决定标签及别名/口径问题；当前任何AI评分都不是人工批准。'], '人工审核仍待完成'))
    records.append(record(10, '对应源码、原始结果、日志、prompt及截图打成本轮ZIP',
        '交付清单/源码/原始输出/可复现命令已整理，正式ZIP及最终打包验证作为本报告同行交付；本报告构建器不运行打包。',
        ['scripts/package_stage_delivery.py', 'scripts/build_special_delivery.py'],
        ['主流程使用既有package_stage_delivery构建器实际执行敏感扫描、CRC、哈希、新目录解压和相对链接核验；实际命令与结果见同行交付的独立verification。'],
        ['本报告保存显式交付manifest；正式ZIP及其最终哈希/验证记录由主流程同行交付，ZIP SHA不写入自身内容。'],
        exists([inputs.get('zip_verification')]), ['真实.env、密钥/密码、数据库卷、模型权重、保留题与无关工作目录不附入。'],
        '交付材料已整理；正式ZIP及最终验证同行交付'))
    summary = {'title': TITLE, 'created_at_utc': datetime.now(timezone.utc).isoformat(), 'original_item_count': 10,
               'claim': '本轮合成开发集上的自动评测／AI预审结果', 'dataset': prep, 'records': records,
               'versions': [{key: value for key, value in v.items() if key != 'artifacts'} for v in versions],
               'selected_final_version': selected_name,
               'preparation_usage': usage, 'runtime_system_prompts': prompts, 'system_json_adapter': adapter,
               'actual_provider_system_messages': actual_system,
               'actual_provider_system_character_range': provider_character_range,
               'input_readiness': ready, 'human_review_status': 'pending_human_review',
               'prediction_calls_by_report_builder': 0, 'holdout_prediction_calls': 0,
               'input_sha256': {path: digest(path) for path in all_runtime + exists([decisions, inputs.get('regression_summary'), inputs.get('restore_instructions')])}}
    save(TITLE + '.json', summary)
    lines = ['# ' + TITLE, '', '本报告对应专项原文10个交付要求，读取保留的真实生成、审核与运行证据。没有运行或无法取得的材料如实标“未运行／证据不足”。全部人工审核状态为`pending_human_review`。', '',
             f"候选{prep['dataset_total']}条，规范化题面{prep['unique_inputs']}个，可评分{prep['scorable']}条、待确认{prep['pending_confirmation']}条；全部{prep['all_human_pending']}条仍待人工核对。候选类别配额达到，合格可评分配额部分不足，两者分开报告。", '',
             '结果定位：**本轮合成开发集上的自动评测／AI预审结果**，不称官方题、正式保留成绩或独立泛化证据。', '', '|编号|原文交付要求|当前判定|', '|---|---|---|']
    lines[6:6] = [f"实际选择保留版本：**{selected_name}**。其他实际试验版本仍保留并逐轮报告，不把最后试验自动当作最终保留版本。", '']
    for row in records:
        lines.append(f"|{row['number']}|{row['requirement']}|{row['verdict']}|")
    for row in records:
        lines += ['', f"## {row['number']}. {row['requirement']}", '', '**实现情况**：' + row['implementation'], '']
        for title, key in [('改动或关联文件', 'changed_or_related_files'), ('测试方法与命令', 'test_method_and_commands'), ('实际结果', 'actual_results'), ('证据位置', 'evidence'), ('未完成事项或限制', 'pending_or_limitations')]:
            lines += ['**' + title + '**：', '']
            for value in row[key]:
                rendered = link(value) if key in ('changed_or_related_files', 'evidence') and local(value).is_file() else value
                lines.append('- ' + rendered)
            if not row[key]:
                lines.append('- 当前没有对应实际证据文件。')
            lines.append('')
        lines.append('**判定**：' + row['verdict'] + '；人工仍待核对。')
    lines += ['', '## 运行版本与逐指标分母', '']
    metric_names = {'binding_correctness': '绑定正确', 'initial_level_correct': '初始层级正确', 'necessary_clarification_recall': '必要澄清召回', 'false_clarification': '误澄清', 'clarification_effectiveness': '有效澄清', 'condition_preservation': 'SQL语义/条件保留', 'overcorrection': '过度纠错', 'l1_default_switch_behavior': 'L1默认切换'}
    for version in versions:
        lines += ['### ' + version['version'], ''] + ['- ' + value for value in metric_table(version)] + ['']
        if version['summary']:
            lines += ['|指标|正向/适用题分母|实观测分母|未确定|', '|---|---|---|---|']
            for key, data in version['summary']['groups']['all']['metrics'].items():
                lines.append(f"|{metric_names.get(key, key)}|{data['positive_over_task_denominator']}|{data['observed_denominator']}|{data['unresolved']}|")
            lines += ['', '误澄清、过度纠错表中positive表示发生该错误，数值越小越好；其他指标positive按该指标定义。SQL结果相同但AST合同未证明的输出仍待AI复核，不强行通过。']
        lines += ['', '实际证据：' + '、'.join(link(p) for p in exists(list(version['paths'].values()))) if exists(list(version['paths'].values())) else '实际证据：未取得。', '']
    lines += ['## 运行时system prompt清单', '', '|文件与实际调用职责|字符数|提取方式|', '|---|---:|---|']
    for prompt in prompts:
        lines.append('|'+link(prompt['delivery_file'], prompt['source_file'])+'：'+prompt['duty']+'|'+str(prompt['character_count'])+'|'+prompt['extraction']+'|')
    lines += ['', '以上是业务模板。JsonLLM实际拼接统一JSON约束及response_model的动态JSON Schema后才发送；有限候选裁决Schema包含当次合法ID边界。源文件、调用位置、模板字符数、前后源码SHA以及已归档provider完整system内容、完整字符数与SHA见' + link(exp('reports/acceptance/runtime-system-prompts/inventory.json')) + '。完整system消息按实际capture去重保存，不由题库标签重构。动态user payload没有伪装成固定prompt。', '',
              '生成/标注/AI复核用量与被测API运行用量分开。准备阶段真实40个logical call、45个provider请求及token分项见' + link(exp('reports/preparation-stage-usage.json')) + '；这些不计入系统预测次数。金额未取得，不按猜测价格推算。', '',
              '完整解压本轮ZIP后打开HTML；源码、JSON和日志链接全部为相对路径。原始尝试与失败保留，不覆盖D1/D2验收证据。', '',
              '机器报告：' + link(report_name)]
    content = '\n'.join(lines) + '\n'
    (OUT / (TITLE + '.md')).write_text(content, encoding='utf-8')
    from markdown_it import MarkdownIt
    body = MarkdownIt('commonmark').enable('table').render(content)
    css = 'body{max-width:1120px;margin:32px auto;padding:0 24px;font:16px/1.75 "Microsoft YaHei",sans-serif;color:#253047}h2{margin-top:42px;border-bottom:2px solid #dce5f0;padding-bottom:8px}a{color:#145f9b;overflow-wrap:anywhere}code{background:#f1f5f8;padding:2px 5px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border:1px solid #d5deea;padding:9px;text-align:left;vertical-align:top}th{background:#eef3fa}@media print{body{font-size:11px;margin:0}h2{break-after:avoid}tr{break-inside:avoid}}'
    (OUT / (TITLE + '.html')).write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(TITLE)+'</title><style>'+css+'</style><body>'+body+'</body></html>', encoding='utf-8')
    include = [EXP, 'qa_agent', 'api', 'ui', 'requirements.txt', '.env.example', 'README.md', 'scripts/build_special_delivery.py', 'scripts/build_special_review.py', 'scripts/run_special_d2_regression.py', 'scripts/package_stage_delivery.py',
               'data/catalog/chinook.yaml', 'data/aliases/aliases-d2-reviewed.csv', 'data/rules/metric_definitions.json', 'notes/references/d3-and-special/专项造题.txt']
    include += D2_EVALUATION_SOURCES + [r['dataset'] for r in D2_REGRESSION.values()]
    include += ['eval/artifacts/d2-final/review/user-attestation-and-revisions.json']
    include += all_runtime + [p for row in records for p in row['evidence']] + inputs.get('extra_include', [])
    for value in regressions.values():
        if value.get('report'):
            include.append(Path(value['report']).parent.as_posix())
        include += exists([value.get('command')])
    manifest = dict(stage='special-01-03', entry_document=(OUT / (TITLE + '.html')).relative_to(ROOT).as_posix(),
                    include=sorted({p for p in include if p and local(p).exists()}),
                    exclude_prefixes=PROTECTED + inputs.get('exclude_prefixes', []),
                    human_review_status='pending_human_review', label_scope='60 synthetic development candidates; no held questions, gold, or predictions')
    save('delivery-input-manifest.json', manifest)
    return {'items': 10, 'candidate_count': prep['dataset_total'], 'scorable': prep['scorable'], 'pending': prep['pending_confirmation'], 'versions': [v['version'] for v in versions],
            'selected_final_version': selected_name, 'actual_final_run_complete': final['actual_run_complete'], 'readiness': ready, 'report': manifest['entry_document']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--check-inputs', action='store_true')
    args = parser.parse_args()
    inputs = read(args.inputs)
    if args.check_inputs:
        result = readiness(inputs)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result['ready'] else 2)
    result = build(inputs)
    save('build-report-command.json', {'command': [sys.executable, '-B', *sys.argv], 'cwd': str(ROOT), 'exit_code': 0,
         'created_at_utc': datetime.now(timezone.utc).isoformat(), 'actual_result': result,
         'generator_sha256': digest('scripts/build_special_delivery.py'), 'model_calls': 0, 'database_queries': 0, 'api_predictions': 0})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
