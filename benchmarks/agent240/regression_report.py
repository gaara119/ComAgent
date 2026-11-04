"""Reporting over the existing scorer; no new prediction or scoring engine."""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET


def load_regression_evidence(source_manifest, directory=None):
    """Bind supplementary offline receipts to this exact historical panel.

    These receipts do not add predictions, change labels, or turn fixture checks
    into online measurements. Original JSON/XML bytes are checked before use.
    """
    directory = Path(directory or Path(__file__).parent / 'data' / 'regression-evidence')
    manifest_path = directory / 'manifest.json'
    if not manifest_path.exists():
        return {'status': 'not_verified', 'reason': 'no portable regression receipts supplied'}
    manifest = json.loads(manifest_path.read_text('utf-8'))
    files = source_manifest.get('files', {})
    if any(files.get(name) != digest for name, digest in manifest['panel_files'].items()):
        return {'status': 'not_verified', 'reason': 'receipts belong to another historical panel'}
    values = {}
    for item in manifest['artifacts']:
        # All receipt paths are a single local file, never an arbitrary path.
        name = item['file']
        if Path(name).name != name:
            raise ValueError('Invalid regression receipt path')
        path = directory / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f'Regression receipt hash mismatch: {name}')
        if path.suffix == '.json':
            values[name] = json.loads(path.read_text('utf-8'))
        elif path.suffix == '.xml':
            suites = ET.parse(path).getroot()
            selected = [suites] if suites.tag == 'testsuite' else list(suites.findall('testsuite'))
            values[name] = {field: sum(int(suite.get(field, '0')) for suite in selected)
                            for field in ('tests', 'failures', 'errors', 'skipped')}
    return {'status': 'hash_verified', 'manifest': manifest, 'receipts': values}


def regression_evidence_markdown(summary):
    evidence = load_regression_evidence(summary.get('source_manifest', {}))
    if evidence['status'] != 'hash_verified':
        return '\n'.join(['### 离线回归与历史重复运行', '',
                          f"not_verified：{evidence['reason']}。未将无对应收据的检查写成通过。", ''])
    receipts = evidence['receipts']
    fault = receipts['controlled-faults.json']
    regression = receipts['regression-summary.json']
    combined = receipts['all-agent-regressions.junit.xml']
    final_name = 'final-offline-regression-r2' if 'final-offline-regression-r2.junit.xml' in receipts else 'final-offline-regression'
    final_checks = receipts.get(final_name + '.junit.xml')
    correction = receipts['gold-status-correction.json']
    repeats = receipts['historical-repeat-audit.json']
    consistency = receipts['review-consistency-audit.json']
    recovered = fault['transient_recovery']
    stopped = fault['expected_fail_closed']
    base = (os.path.relpath(Path(__file__).parent / 'data' / 'regression-evidence',
                           summary['output_directory']).replace('\\', '/') + '/') if summary.get('output_directory') else '../../data/regression-evidence/'
    lines = ['### 离线回归、稳定性与安全的验证边界', '',
             '| 验证对象 | 实际结果 | 证据和适用范围 |', '|---|---|---|',
             f"| 生产LLM客户端受控故障 | {recovered['recovered']}/{recovered['eligible_scenarios']}可恢复场景恢复；{stopped['passed_policy']}/{stopped['eligible_scenarios']}应停止场景按策略停止 | [受控故障收据]({base}controlled-faults.json)，16个场景、{fault['physical_fixture_attempts']}次MockTransport尝试；真实API和SQL调用均为0 |",
             f"| SQL与来源/工具权限 | {regression['counts']['tests.test_sql_validator']}项SQL校验＋{regression['counts']['tests.test_source_scope_and_tool_permissions']}项权限检查通过 | [92项组合回归]({base}regression-summary.json)包含上述66项；不作为线上攻击防御率或真实数据库权限证明 |",
             f"| 阶段综合本地回归 | {combined['tests']}通过，{combined['failures']}失败、{combined['errors']}错误、{combined['skipped']}跳过 | [244项JUnit原始记录]({base}all-agent-regressions.junit.xml)，含指标、证据绑定、RAG、文档导入等；与92项组合回归有重叠，不相加 |",
             *([f"| 本轮综合本地回归 | {final_checks['tests']}通过，{final_checks['failures']}失败、{final_checks['errors']}错误、{final_checks['skipped']}跳过 | [实际命令]({base}{final_name}.json)与[JUnit]({base}{final_name}.junit.xml)；包含Gold状态、EvalScope联接与预算检查，不与先前测试数量相加 |"] if final_checks else []),
             f"| Gold状态纠正回归 | {correction['tests']['passed']}通过；Gold正文和原始预测均未改动 | [纠正收据]({base}gold-status-correction.json)绑定当前240题与480条预测；[本地JUnit]({base}gold-correction-regression.xml) |", '',
             '受控恢复覆盖429、503、连接超时、非法JSON、非法结构和截断；持续失败、鉴权/余额错误、共享预算耗尽及未配置密钥验证明确失败或停止。夹具中的usage不是实付用量，等待时间被替代，因此不产生线上延迟、可用性或并发性能结论。', '',
             '### 历史重复运行的只读诊断', '',
             '最近三次legacy40-S1记录的源码文件数为126、130、135，源码哈希不同，不能视为同一版本连续三轮稳定性验收。更早candidate029两轮的已记录源码、健康配置和输入一致性及输出如下：', '',
             '| 历史配置 | 状态一致/40 | 答案逐字一致/40 | 成功SQL对的有序结果一致 |', '|---|---|---|---|']
    for pair in repeats['older_candidate029_pairs']:
        table = pair['ordered_table_agreement']
        lines.append(f"| {pair['stage']} | {pair['status_agreement']}/{pair['logical_pairs']} | {pair['exact_answer_surface_agreement']}/{pair['logical_pairs']} | {table['matched']}/{table['eligible_successful_SQL_pairs']} |")
    lines += ['', f"[历史重复诊断]({base}historical-repeat-audit.json)没有完整证明数据库、文档和索引快照跨轮相同；这只是已有记录上的一致性诊断，不是当前240题的重复运行准确率或当前版本稳定性实测。答案逐字不同也不直接等于业务错误。", '',
              '### 历史系统回答判分的未决项', '',
              '当前Gold人工审核覆盖240/240；历史文件中的pending只反映旧导出状态。系统实际回答仍有8条业务判断和1条完整交付判断未知，这些是预测判分对象，与Gold是否审核是两件事。', '',
              f"另一次[审核理由一致性筛查]({base}review-consistency-audit.json)扫描{consistency['scope']['record_reasons_scanned']}条已有判分理由并详细核对其中{consistency['scope']['detailed_review_subset']}条，列出{consistency['findings_summary']['pending_rationale_consistency_items']}条FULL理由混用内部状态与外部交付的问题；这个8条清单与上述8条未知业务判断不是同一清单。配对BASE理由和可见回答仍指出具体交付遗漏，尚未证明存在只因关闭内部状态而给BASE判错的实例，原标签与成绩均保留。", '',
              '这些收据按原始字节保存。审核理由收据中旧的“Pending Gold”限制已被当前Gold状态纠正收据和版本绑定状态覆盖层取代；它不再代表当前Gold审核状态。复核语义判分理由不等于重新审核Gold，也不因工具路径与参考计划不同而扣分。', '',
              f"全部补充收据和SHA256见[回归证据清单]({base}manifest.json)。当前可报告的是历史业务预测复核与本地受控检查；线上完整240题、真实故障恢复、实际提示注入/敏感泄漏攻击和吞吐压测仍未完成。金额无可靠计费单价依据，保持未核验；输入/输出与缓存token分别报告。", '']
    return '\n'.join(lines)


def paired(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row['suite'], {}).setdefault(row['arm'], {})[row['id']] = row
    result = {}
    for suite, arms in grouped.items():
        before = arms.get('BASE', {})
        for arm, after in arms.items():
            if arm == 'BASE':
                continue
            axes = {}
            for name in ('accuracy', 'external_success', 'exact_match'):
                keys = sorted(before.keys() & after.keys())
                if name == 'exact_match':
                    keys = [key for key in keys if before[key].get('sql_eligible') or after[key].get('sql_eligible')]
                applicable = [(before[key].get(name), after[key].get(name)) for key in keys]
                known = [(a, b) for a, b in applicable if type(a) is bool and type(b) is bool]
                axes[name] = {'known_pairs': len(known), 'applicable_pairs': len(applicable),
                              'unknown_pairs': len(applicable) - len(known),
                              'wrong_to_right': sum(not a and b for a, b in known),
                              'right_to_wrong': sum(a and not b for a, b in known),
                              'both_right': sum(a and b for a, b in known),
                              'both_wrong': sum(not a and not b for a, b in known),
                              'net_change': sum(int(b) - int(a) for a, b in known)}
            result[suite + '/BASE_vs_' + arm] = axes
    return result


def artifacts(output, rows, cases):
    findings = []
    for row in rows:
        attribution = row.get('attribution', {})
        if (row.get('accuracy') is False or row.get('external_success') is False
                or row.get('exact_match') is False or row.get('error') is True or attribution.get('finding_evidence')):
            findings.append({'id': row['id'], 'arm': row['arm'], 'suite': row['suite'],
                             'question': cases[row['id']]['question'], 'status': row.get('status'),
                             'accuracy': row.get('accuracy'), 'SQL_result_EM': row.get('exact_match'),
                             'external_task_success': row.get('external_success'),
                             'match_reason': row.get('reason'), 'review_reason': row.get('review_reason'),
                             'gold_human_review_status': row.get('gold_human_review_status'),
                             'attribution': attribution, 'source': row.get('source'),
                             'rag_evalscope': row.get('rag_evalscope')})
    # One row per actual question/configuration, not one row per failed dimension.
    assert len({(r['id'], r['arm']) for r in findings}) == len(findings)
    (output / 'failure-attribution.json').write_text(json.dumps({
        'records': findings, 'record_count': len(findings),
        'counting': 'one question/configuration can have multiple dimension tags, never extra independent questions'}, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    with (output / 'per-question.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        fields = ['id', 'arm', 'suite', 'status', 'accuracy', 'external_success', 'exact_match', 'row_f1', 'elapsed_ms',
                  'gold_human_review_status', 'business_review_status', 'primary_failure_family']
        writer = csv.DictWriter(stream, fields, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, 'primary_failure_family': row.get('attribution', {}).get('primary_failure_family')})
    return findings


def markdown(summary, findings):
    lines = ['## 6 Agent端到端开发回归', '',
             'RAG专项由EvalScope的MTEB/RAGAS负责；本节复用项目既有业务判分、Gold和真实执行记录。RAG工具链属于Agent任务的一部分，但专项分数与端到端业务成功分别记录。', '',
             '### 原题范围与审核覆盖', '',
             '| 批次/配置 | 已运行 | 业务已判/总数 | Gold人工状态 | 模型P50/P90 | SQL P50/P90 | 检索单独计时 |',
             '|---|---:|---|---|---|---|---|']
    for suite, arms in summary['groups'].items():
        for arm, group in arms.items():
            label = '/'.join(group.get('configurations', [])) or arm
            timing = group['phase_timing']

            def fmt(name):
                value = timing[name]
                return f"{value['p50']/1000:.3f}/{value['p90']/1000:.3f}秒（{value['known']}题）" if value['p50'] is not None else '未核验'

            coverage = group['business_review_coverage']
            lines.append(f"| {suite}/{label} | {group['observed']} | {coverage['assessed']}/{coverage['total']}，未知{coverage['total']-coverage['assessed']} | {json.dumps(group['gold_human_review_statuses'],ensure_ascii=False)} | {fmt('model_ms')} | {fmt('SQL_ms')} | {fmt('retrieval_ms')} |")
    lines += ['', '模型计时包含实际失败和重试的llm span；SQL为sql_exec span；不与包含它们的规划/生成外层span重复相加。端到端HTTP耗时另列。历史未单独埋点检索，不能将工具整体时间减模型时间冒充检索耗时。', '',
              '模型请求内重试仅按实际llm attempt>1计数，SQL修复与RAG重生成作为另一类事件保留；不能把755−480次调用全部叫重试。逐配置重试输入/输出/缓存用量见summary.phase_timing.model_retry_usage，缺失usage保留未知。', '',
              '### 质量与成本的取舍', '',
              '| 比较 | 维度 | 有效配对/适用配对 | 错→对 | 对→错 | 净变化 |', '|---|---|---|---:|---:|---:|']
    for comparison, axes in summary['paired_comparison'].items():
        for name, values in axes.items():
            lines.append(f"| {comparison} | {name} | {values['known_pairs']}/{values['applicable_pairs']} | {values['wrong_to_right']} | {values['right_to_wrong']} | {values['net_change']:+d} |")
    lines += ['', '配对是同题历史描述性对照，非未见测试或同源因果消融。业务准确性、完整交付与数值EM可以不同步变化；表中保留所有正负收益。不同版本与多轮相关性限制了推断，不将两套性能简单合并。', '',
              '### 分层失败归因和典型案例', '',
              '路由没有进入RAG与检索器遗漏分别归因；没有同运行专项证据时，不将引用缺失判为检索器失败。实际状态或审核依据不充分的保留待核验。', '',
              '| 题目/配置 | 主要归因 | 证据与边界 |', '|---|---|---|']
    picked = set()
    for finding in findings:
        attribution = finding.get('attribution', {})
        family = attribution.get('primary_failure_family') or 'unresolved'
        # Representative examples are supplementary; all failures remain in JSON/CSV.
        if family in picked or len(picked) >= 8:
            continue
        picked.add(family)
        events = attribution.get('finding_evidence') or []
        detail = events[0].get('detail') if events else None
        if isinstance(detail, dict):
            step = detail.get('last_failed_step') or {}
            reason = f"错误代码={detail.get('error_code')}；步骤={step.get('name')}；证据位置={events[0].get('path')}"
        else:
            reason = str(detail or finding.get('review_reason') or finding.get('match_reason') or '原因未定位；保留未决，详见逐题证据')
        reason = reason.replace('|', '/').replace('\n', ' ')[:360]
        lines.append(f"| {finding['id']}/{finding['arm']} | {family} | {reason} |")
    lines += ['', '完整记录见failure-attribution.json和per-question.csv。同一道题的多维问题保留多个标签，但每个题目/配置仅一行。过程评测核对公开工具、参数、依赖、状态与实际结果，不评价内部思考；满足要求的替代路径不因与Gold步骤不同而扣分。', '',
              '### 专项联接及未完成项', '',
              f"EvalScope同题同运行已导入{summary['rag_specialist']['imported_predictions']}条；未导入的专项项保持not_verified，自定义返回覆盖、EM、F1和安全检查不改名为EvalScope结果。", '',
              '- 当前结果为240条综合开发回归、480份历史配置预测的复核，不是当前版本重新在线执行240题。',
              '- RAG完整排名、完备相关性标签、引用语义、故障注入、安全对抗分别记录适用分母和验证状态。',
              '- 受控MockTransport故障回归与真实业务预测、真实线上恢复和压力测试分开；来源和命令见独立回归收据。',
              '- Gold当前审核状态采用版本绑定的人工审核状态覆盖层；当前用户确认240题已完成人工审核。原始历史pending字段保留，不再代表当前状态。',
              '- 系统实际回答的业务/交付判分仍有未决项，与Gold人审不是同一对象；未知回答判断不作通过，也不从完整分母中隐藏。', '']
    if summary['rag_specialist']['imported_predictions']:
        lines += ['### EvalScope同运行专项结果', '',
                  '| 批次/配置 | 已联接Agent预测 | 专项指标及有效子任务 |', '|---|---:|---|']
        for suite, arms in summary['groups'].items():
            for arm, group in arms.items():
                label = '/'.join(group.get('configurations', [])) or arm
                value = group['rag_evalscope']
                lines.append(f"| {suite}/{label} | {value['matched_predictions']} | {json.dumps(value['metrics'],ensure_ascii=False)} |")
        lines += ['', '这些分数只评价RAG已交付子任务与实际输入上下文的关系，不能代替未进入RAG的任务、完整跨源答案或全部240题。Faithfulness是依据上下文的忠实度，不是答案正确率；检索召回仍须相同检索运行的排名和相关性标签。', '']
        external = summary['rag_specialist'].get('judge_execution')
        if external:
            execution = external['data']
            usage = execution['usage']
            source = os.path.relpath(Path(external['file']).parent / 'report.md',
                                    summary.get('output_directory', '.')).replace('\\', '/')
            lines += [f"独立RAGAS裁判本次真实调用{execution['physical_calls']}次，输入{usage['input_tokens']}、输出{usage['output_tokens']} token；缓存命中{usage['cache_hit_tokens']}、未命中{usage['cache_miss_tokens']}，缺失usage为{usage['missing_usage_calls']}次。这些调用不属于历史755次Agent调用，也没有生成新的Agent预测。原始裁判响应、预算、失败与截断及耗时见[EvalScope专项报告]({source})，金额未核验。", '']
    lines += [regression_evidence_markdown(summary)]
    return '\n'.join(lines)
