"""Render the original D3 eight-item report from preserved actual evidence.

This script does not call a model, query a database, run predictions, alter
reference labels, or sign human reviews. Packaging is a separate root action.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eval/reports/d3-acceptance"
TITLE = "D3原清单八项逐项验收与证据"

FIXED = {
    "aw_import": "eval/artifacts/d3/a/bootstrap-result.json",
    "aw_source": "data/db/aw_source_manifest.json",
    "aw_dates": "data/db/aw_live_data_manifest.json",
    "aw_catalog": "eval/artifacts/d3/a/catalog/summary.json",
    "catalog_pass2": "eval/reports/d3-ai-review/catalog-pass2.json",
    "schema_dev": "eval/reports/d3-aw-schema-dev-final/report.json",
    "aw_dev": "eval/reports/d3-aw-live-dev-run1/report.json",
    "aw_observation": "eval/reports/d3-aw-live-dev-run1/schema-observation.json",
    "aw_labels": "eval/datasets/d3/aw_schema_link_v2_manifest.json",
    "clarify_labels": "eval/datasets/d3/clarify/manifest.json",
}
FINAL_KEYS = ("clarify_dev", "flow", "ui", "modules_command")

# Both question-builder source files contain literal protected questions. Their
# aggregate manifests and developer-only exported views are the delivery inputs.
PROTECTED = [
    "eval/artifacts/d3/a/gold/holdout/",
    "eval/datasets/d3/aw_schema_link.holdout.jsonl",
    "eval/datasets/d3/aw_schema_link.jsonl",
    "eval/datasets/d3/aw_schema_link.v2.jsonl",
    "eval/datasets/d3/clarify/protected_holdout/",
    "scripts/build_d3_aw_dataset.py",
    "scripts/build_d3_clarify_cases.py",
    "notes/d3/staging/",
    "eval/experiments/",
]


def local_path(name: str) -> Path:
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Evidence must stay inside the project: " + name)
    relative = path.relative_to(ROOT.resolve()).as_posix()
    if any(relative.casefold() == prefix.rstrip("/").casefold() or relative.casefold().startswith(prefix.casefold())
           for prefix in PROTECTED):
        raise ValueError("Protected content cannot be a report input: " + relative)
    return path


def read(name: str):
    return json.loads(local_path(name).read_text(encoding="utf-8"))


def digest(name: str) -> str:
    return hashlib.sha256(local_path(name).read_bytes()).hexdigest()


def link(name: str, label: str | None = None) -> str:
    path = local_path(name)
    if not path.exists():
        raise FileNotFoundError("Missing report evidence: " + name)
    relative = Path(os.path.relpath(path, OUT)).as_posix()
    return f"[{label or name}]({relative})"


def completed(data, name: str):
    if data.get("status") in {"RUNNING", "PENDING", "NOT_RUN"}:
        raise RuntimeError("Actual report has not completed: " + name)
    if any(data.get(field, 0) for field in ('holdout_predictions', 'holdout_prediction_count', 'protected_holdout_predictions', 'holdout_predictions_observed')):
        raise RuntimeError("Protected predictions found in an input report: " + name)


def actual_checks(data):
    checks = data.get("checks", [])
    if isinstance(checks, dict):
        return [{"name": key, "passed": bool(value)} for key, value in checks.items()]
    return checks


def check_summary(data):
    checks = actual_checks(data)
    if checks:
        passed = sum(bool(row.get("passed")) for row in checks)
        return f"{passed}/{len(checks)} 个实际检查通过；状态 {data.get('status', '未标记')}"
    return f"实际报告状态 {data.get('status', '未标记')}；逐步结果见原始报告"


def measured_checks_pass(data):
    """Use actual nonempty check/counter evidence, including legacy no-status reports."""
    if data.get('status') in {'RUNNING', 'PENDING', 'NOT_RUN', 'ABORTED', 'FAILED', 'FAIL'}:
        return False
    checks = actual_checks(data)
    if not checks or not all(row.get('passed') is True for row in checks):
        return False
    if data.get('total', len(checks)) != len(checks) or data.get('passed', len(checks)) != len(checks):
        return False
    if 'actual_api_requests' in data and data['actual_api_requests'] <= 0:
        return False
    return True


def modules_summary(command_path):
    record = read(command_path)
    stdout = str(Path(command_path).parent / "pytest.stdout.txt").replace("\\", "/")
    text = local_path(stdout).read_text(encoding="utf-8")
    match = re.search(r"(\d+) passed(?:[^\n]*?) in ([\d.]+)s", text)
    if not match:
        raise RuntimeError("No actual pytest result found: " + stdout)
    return {"passed": int(match[1]), "seconds": float(match[2]),
            "exit_code": record.get("exit_code"), "command": record.get("command"),
            "command_record": command_path, "stdout": stdout}


def item(number, group, requirement, implementation, changed, methods, results,
         evidence, pending, passed):
    return {"number": number, "group": group, "requirement": requirement,
            "implementation": implementation, "changed_files": changed,
            "test_method_and_commands": methods, "actual_results": results,
            "evidence": evidence, "pending_or_limitations": pending,
            "engineering_verdict": "实测完成，待人工验收" if passed else "存在未通过项，请复核原始结果",
            "human_review_status": "pending_human_review"}


def generate(inputs):
    paths = {**FIXED, **{key: inputs[key] for key in FINAL_KEYS}}
    # Prefer a completed same-runtime regression when it exists; a report still
    # running is never treated as completed, and its observation must be real.
    run2_report = "eval/reports/d3-aw-live-dev-run2/report.json"
    run2_observation = "eval/reports/d3-aw-live-dev-run2/schema-observation.json"
    if local_path(run2_report).is_file():
        run2 = read(run2_report)
        if run2.get('status') == 'ACTUALLY_RUN_DEV_EXPLORATORY':
            if not local_path(run2_observation).is_file():
                raise RuntimeError('Completed AW run2 needs saved-response-only observation before final report.')
            paths.update(aw_dev=run2_report, aw_observation=run2_observation)
    for key in ('aw_dev', 'aw_observation'):
        if inputs.get(key):
            paths[key] = inputs[key]
    values = {key: read(path) for key, path in paths.items()}
    for key in ("aw_dev", "schema_dev", "clarify_dev", "flow", "ui"):
        completed(values[key], paths[key])
    aw, obs, schema = values["aw_dev"], values["aw_observation"], values["schema_dev"]
    aw_run = Path(paths['aw_dev']).parent.as_posix()
    aw_responses = aw_run + '/responses.jsonl'
    aw_command = 'eval/artifacts/d3/a/' + Path(aw_run).name.removeprefix('d3-') + '-command.txt'
    boot, catalog, catreview = values["aw_import"], values["aw_catalog"], values["catalog_pass2"]
    clarify, flow, ui = values["clarify_dev"], values["flow"], values["ui"]
    awlabels, clabels, dates = values["aw_labels"], values["clarify_labels"], values["aw_dates"]
    modules = modules_summary(paths["modules_command"])
    module_ok = modules["exit_code"] == 0
    ui_ok = measured_checks_pass(ui)
    flow_ok = measured_checks_pass(flow)
    # Later real reruns added semantic origin checks after equal totals masked
    # a customer-country versus invoice-country projection/grouping error.
    country_sources = []
    for name in ('country-field', 'country-period'):
        evidence = Path(paths['flow']).parent.as_posix() + '/' + name + '.country-sources.json'
        if local_path(evidence).is_file():
            country_sources.append((evidence, read(evidence)))
    country_source_ok = (flow.get('country_output_source_checks') == flow.get('country_output_source_passed') == 2
                         and len(country_sources) == 2
                         and all(data.get('verified') is True and data.get('expected_scope_from_explicit_user_change') == 'customer.country'
                                 and data.get('sources') and all(row.get('source') == 'customer.country' for row in data['sources'])
                                 for _, data in country_sources))
    flow_ok = flow_ok and country_source_ok
    clarify_total = clarify.get("total", clarify.get("dev_prediction_count"))
    clarify_passed = clarify.get("passed")
    clarify_ok = clarify_passed == clarify_total == 21
    aw_all_match = aw["correct"] == aw["prediction_count"] == 21
    aw_usable = (aw['provenance']['actual_health'].get('aw_database_ready') is True
                 and obs['actual_sql_execution_adventureworks_cases'] == 21
                 and obs['validated_aw_scope_cases'] == 21)
    aw_dataset_run_complete = aw['prediction_count'] == 21 and awlabels['total_count'] == 30
    schema_ok = schema["all_gold_recalled_cases"] == schema["case_count"] == 21
    core = ["qa_agent/config.py", "qa_agent/llm.py", "qa_agent/schemas.py", "qa_agent/pipeline.py",
            "qa_agent/sql/generator.py", "qa_agent/sql/executor.py", "api/main.py", "ui/app.py"]
    records = [
        item(1, "A", "上午导入 lorint 完整版 AdventureWorks；2小时失败才采用§3.4.1兜底。",
             "使用独立 AW Compose 项目、端口和卷导入完整 OLTP；未重导、重建或覆盖已有 Chinook。新增 qa_reader 只读权限及5000ms语句超时。",
             ["docker-compose.aw.yml", "scripts/bootstrap_aw.py", "data/db/aw_source_manifest.json", "data/db/aw_live_data_manifest.json"],
             [".venv/Scripts/python.exe -B scripts/bootstrap_aw.py", "只读核验 BASE TABLE、FK、sales.salesorderdetail COUNT、账号权限和实际日期；实际命令记录保留。"],
             [f"{boot['base_table_count']}张真实业务表，{boot['foreign_key_count']}条外键，sales.salesorderdetail={boot['salesorderdetail_rows']}行。",
              f"qa_reader默认只读={boot['reader_default_read_only']}，statement_timeout={boot['statement_timeout_ms']}ms，旧Chinook触碰={boot['old_chinook_service_touched']}。",
              f"销售日期 {dates['sales_order_date_range']['min_date']} 至 {dates['sales_order_date_range']['max_date']}；真实年份 {dates['sales_order_years']}。"],
             [paths['aw_import'], paths['aw_source'], paths['aw_dates'], "eval/artifacts/d3/a/commands.jsonl", "eval/artifacts/d3/a/import-full-oltp.txt", "eval/artifacts/d3/a/catalog/reader-audit.json", "eval/artifacts/d3/a/actual-date-source-check.json"],
             ["当前官方CSV的实际年份与上游旧DDL注释不同；未推断转换器移年。最早/最晚年份不能视为完整年度；没有启用LT兜底。"],
             boot['base_table_count'] == 68 and boot['reader_default_read_only'] and not boot['old_chinook_service_touched']),
        item(2, "A", "对 AW 跑 build_catalog.py，生成中文描述。",
             "沿用现有 build_catalog.py 命令入口，增加AW实时结构导出与中文描述生成；精确校验模型返回的表/列键，保留原始响应及修正前目录。",
             ["scripts/build_catalog.py", "scripts/build_aw_catalog.py", "data/catalog/adventureworks.yaml", "data/catalog/aw_ai_directory_corrections.json"],
             [".venv/Scripts/python.exe -B scripts/build_catalog.py --db-id adventureworks", "独立第二遍AI按实时结构审查68表456列；中文修正不覆盖原模型响应。"],
             [f"真实目录{catalog['tables']}表/{catalog['columns']}列/{catalog['foreign_keys']}FK；{catalog['llm_descriptions_ok']}表完成模型描述，实际{catalog['llm_request_attempts']}次请求尝试。",
              f"结构核验{catreview['structural_checks_passed']}/{catreview['structural_checks_total']}；表语义{catreview['table_verdicts']}，列语义{catreview['column_verdicts']}。"],
             [paths['aw_catalog'], "eval/artifacts/d3/a/catalog-build-reviewed.txt", "eval/artifacts/d3/a/catalog/live-schema.json", paths['catalog_pass2'], "eval/artifacts/d3/b/catalog-pass2/usage.json", "eval/reports/d3-acceptance/A待人工核对表.md"],
             ["中文说明仍待人工核对；5张表及19列有条件通过，production.document.status的枚举语义证据不足。未擅自设定枚举或币种。"],
             catalog['llm_descriptions_ok'] == 68 and catreview['structural_checks_passed'] == 456),
        item(3, "A", "实现 schema_linker.py：双路召回＋RRF＋Steiner补全。",
             "BGE-M3分别编码表和列；列候选投票到表、真实值候选参加RRF；实际FK图用Steiner补桥表。按用户原文提取维度要素补充召回，保留各渠道候选、理由和耗时；接入既有SQL生成/校验/只读执行。",
             ["qa_agent/sql/schema_linker.py", "scripts/build_schema_index.py", "eval/d3_schema_eval.py", "qa_agent/pipeline.py", "qa_agent/sql/prompts/multi_table.txt"],
             [".venv/Scripts/python.exe -B scripts/build_schema_index.py --output data/indexes/schema-aw-d3-v2", ".venv/Scripts/python.exe -B eval/d3_schema_eval.py --output eval/reports/d3-aw-schema-dev-final", f".venv/Scripts/python.exe -B eval/d3_aw_reanalyze.py --input {aw_responses} --output {paths['aw_observation']}", "D3 schema模块7项测试，真实API响应21条再观察；修复前98.1%召回记录保留。"],
             [f"模块开发{schema['all_gold_recalled_cases']}/{schema['case_count']}覆盖gold表；平均召回{schema['mean_table_recall']:.2%}、精度{schema['mean_table_precision']:.2%}、候选{schema['average_candidate_table_count']:.2f}表、模块耗时{schema['average_latency_ms']:.2f}ms。",
              f"真实API中{obs['actual_sql_execution_adventureworks_cases']}/{obs['development_count']}执行AW；真实schema阶段平均{obs['average_actual_schema_latency_ms']:.2f}ms。"],
             [paths['schema_dev'], "eval/reports/d3-aw-schema-dev-final/responses.jsonl", "eval/reports/d3-aw-schema-dev-final/actual-steiner-bridge.json", paths['aw_observation'], "eval/artifacts/d3/a/schema-module-tests-final.txt", "eval/artifacts/d3/a/schema-index-summary.json", "eval/reports/d3-aw-schema-dev-v2/report.json"],
             ["候选集仍较宽，精度约14.49%；本阶段未实现D4 LLM剪枝/全量schema消融。模块耗时和真实请求阶段耗时分别报告。", "接口支持已验证值候选参加RRF；本轮AW未注册专属值索引，21题真实value渠道为空，不跨库套用Chinook值索引。表/列双路与FK补全已实际运行。"], schema_ok),
        item(4, "A", "建设30道 AW题，标注gold表/gold SQL，包含刻意干扰项。",
             "完整30题采用家族隔离21开发/9保留；只读逐条执行gold，保存SQL、列、行与哈希；开发题覆盖销售/采购、头/明细、实体/桥表等干扰。两遍AI审读后先执行开发集，保留题不产生预测。",
             ["eval/datasets/d3/aw_schema_link.dev.v2.jsonl", "eval/datasets/d3/aw_schema_link_v2_manifest.json", "scripts/revise_d3_aw_dev_v2.py", "eval/d3_aw_eval.py", "eval/d3_aw_reanalyze.py"],
             [f".venv/Scripts/python.exe -B eval/d3_aw_eval.py --output {aw_run}", "gold在已有只读账号/5000ms限制下执行；系统请求不含gold，失败均计入EX分母。", "EX复用现有compare_results：按题目ordered标记比较行次序，校验列值映射；声明的连续数值按两位小数比较，整数与NULL保持语义区别。原始结果完整保留，业务字段正确性仍单独审核。"],
             [f"标签共{awlabels['total_count']}题（开发{awlabels['dev_count']}、保留{awlabels['holdout_count']}）；开发真实EX={aw['correct']}/{aw['prediction_count']}={aw['exploratory_ex']:.2%}。",
              f"实际模型{aw['actual_model_attempts']}次尝试；总token={aw['usage']['total_tokens']}；平均请求{aw['average_latency_ms']:.2f}ms；保留预测={aw['holdout_predictions']}。"],
             [paths['aw_labels'], paths['aw_dev'], aw_responses, aw_command, "eval/artifacts/d3/a/gold/dev-v2", "eval/reports/d3-ai-review/aw-dev-v2-pass1.md", "eval/reports/d3-ai-review/aw-dev-pass2.md"],
             ["21道开发gold尚待人审，EX是本项目合成开发集自动探索结果，不能作为最终正式成绩。首次预测前4道日期题改到实际2024非空期间，保留1道2013空边界，旧版本与修订理由保留；未按预测结果改标准。9道保留内容不在开发交付包。"], aw_dataset_run_complete and aw_usable),
        item(5, "B", "实现 clarify_rules.yaml 与rules.py：L0/L1/L2判定。",
             "接入现有SQL入口：L0明确可答；L1仅使用已经共同确认的默认并声明假设；L2缺时间、缺对象/分子分母、相冲突或候选不唯一时先问。地区和热门口径补丁保持可核对的实际字段。",
             ["qa_agent/clarify/rules.py", "qa_agent/clarify/extractor.py", "qa_agent/clarify/service.py", "qa_agent/clarify/prompts/intent_extract.txt", "qa_agent/clarify/clarify_rules.yaml"],
             ["21道开发题通过真实API评测；规则模块及新增反例用pytest验证。", "第二遍独立审读核对多期间、精确日期、最近一年歧义；先保留原失败，再修复回归。"],
             [f"真实开发层级及行为正确 {clarify_passed}/{clarify_total}；L2召回={clarify.get('l2_recall')}，非L2误追问率={clarify.get('non_l2_false_ask_rate')}。", f"实际LLM调用/用量见最终报告：{clarify.get('usage')}。"],
             [paths['clarify_dev'], "eval/artifacts/d3/b/clarify-dev-v1/report.json", "eval/reports/d3/b/AI预审第一遍.md", "eval/reports/d3-ai-review/clarify-dev-pass2.md", "eval/reports/d3-ai-review/integration-pass2.md", "eval/artifacts/d3/b/ai-pass2-counterexamples-tests-final.txt"],
             ["规则与开发标签待人工最终核对；层级与执行状态正确不能单独证明整段业务答案正确。初轮17/21及错误记录保留。"], clarify_ok and module_ok),
        item(6, "B", "实现 state.py：IntentContract、补丁应用、版本号与失效处理。",
             "会话保留服务器可信意图与澄清选项；补丁更新版本，旧卡/来源改变/无效选项在模型和SQL前拒绝；条件修改记录依赖失效并重新生成验证SQL。",
             ["qa_agent/clarify/state.py", "qa_agent/clarify/service.py", "qa_agent/schemas.py", "qa_agent/pipeline.py", "api/main.py"],
             ["真实API逐步运行澄清→选择→回答、旧卡与来源变更、口径切换；实际完整步骤及检查见独立flow报告。", "模块用夹具验证版本、未知/无关补丁和条件保留；夹具结果不计模型EX。"],
             [check_summary(flow), f"共享模块实际{modules['passed']}项通过/{modules['seconds']}秒，exit_code={modules['exit_code']}。"],
             [paths['flow'], "eval/artifacts/d3/b/clarify-flow-v1/report.json", modules['command_record'], modules['stdout'], "eval/reports/d3-ai-review/integration-pass2.md"],
             ["会话已使用本机文件持久化（SessionStore按session_id的SHA256保存到.runtime/sessions），尚未实现多实例共享或TTL治理。D3提供依赖失效记录，D4参数缓存及6轮多轮评测不在本日范围。"], flow_ok and module_ok),
        item(7, "B", "界面实现按钮＋自由输入澄清卡、L1假设声明和切换口径按钮。",
             "复用现有Streamlit聊天与三个面板，显示需要补充的字段、可信选项、自由补充入口、当前假设；切换按钮提交新版本并重新生成答案，保存真实页面截图及对应API响应。",
             ["ui/app.py", "api/main.py", "scripts/capture_d3_clarify_demo.py", "tests/test_d3_clarify_ui.py"],
             ["真实Edge＋Streamlit＋现有API自动点选与截图；卡片前后、L1默认、金额切换、数量切回逐步记录请求与版本。", "AppTest仅用于UI组件回归，真实操作证据以浏览器report和raw为准。"],
             [check_summary(ui), f"实际截图数={len(ui.get('screenshots', []))}；浏览器错误={ui.get('errors', ui.get('browser_errors', []))}。"],
             [paths['ui'], *[row['file'] for row in ui.get('screenshots', [])]],
             ["截图证明当次真实交互；人工仍需检查提示语和选项业务含义。按钮刷新防重复请求、版本一致性结论以实测checks为准。"], ui_ok and module_ok),
        item(8, "B", "建设30道澄清题：15道L2与15道L0/L1。",
             "题库保留编号/题意/期望层级/缺失要素/理由/来源依据；按家族21开发＋9保护保留。两遍AI预审与人工审核分别记录，开发集运行器仅读取dev。",
             ["eval/datasets/d3/clarify/dev.jsonl", "eval/datasets/d3/clarify/manifest.json", "eval/d3_clarify_eval.py"],
             ["开发题21道真实API运行，所有错误计入分母；逐题raw记录层级、状态、意图、是否执行SQL、trace、用量。", "只读核对规则与业务字段，不为系统通过改标签；9保留题不预测且不向后续调参任务展开。"],
             [f"共{clabels['total']}题；层级计数={clabels['labels']}；开发={clabels['dev']}，保留={clabels['holdout']}；family_leakage={clabels['family_leakage']}。", f"真实开发初次层级/执行状态通过 {clarify_passed}/{clarify_total}；不是21题全部后续按钮/多轮EX，完整交互另见flow和真实UI；保留预测={clarify.get('holdout_prediction_count', 0)}。"],
             [paths['clarify_labels'], "eval/datasets/d3/clarify/dev.jsonl", paths['clarify_dev'], "eval/reports/d3/b/AI预审第一遍.md", "eval/reports/d3-ai-review/clarify-dev-pass2.json"],
             ["第二遍21道标签建议20通过、1有条件通过；clarify-20分母期间的语法范围需人工确认，不能因为系统给相同层级就认定口径完全正确。人工仍pending。"], clarify_ok and clabels['labels']['L2'] == 15 and not clabels['family_leakage']),
    ]
    records[5]['actual_results'].append(f"技术行为检查{flow.get('technical_passed', '未单列')}/{flow.get('technical_checks', '未单列')}；地区结果来源语义检查{flow.get('country_output_source_passed', '缺少')}/{flow.get('country_output_source_checks', '缺少')}；两个独立AST来源文件核验={country_source_ok}。金额相同不替代投影与分组字段核验。")
    records[5]['evidence'].extend(path for path, _ in country_sources)
    free_growth_path = 'eval/artifacts/d3/root-interface/free-growth-independent-readonly.json'
    if local_path(free_growth_path).is_file():
        free_growth = read(free_growth_path)
        records[5]['actual_results'].append('自由补充年份后的同比真实结果，又用独立single-pass CASE只读SQL逐列exact核验：' + json.dumps(free_growth['reference_result'], ensure_ascii=False) + f"；matched={free_growth['matched']}。增长为fraction，没有预先乘100；该核验没有新增模型预测，人工仍待审核。")
        records[5]['test_method_and_commands'].append('scripts/check_d3_free_growth_readonly.py：既有qa_reader、独立短只读事务、原5000ms限制；原flow证据保持不变。')
        records[5]['evidence'].append(free_growth_path)
    initial_flow_path = 'eval/artifacts/d3/b/clarify-flow-v1/report.json'
    if local_path(initial_flow_path).is_file():
        records[5]['actual_results'].append('历史初轮flow：' + check_summary(read(initial_flow_path)) + '；原始结果独立保留，不与最终轮合并。')
        records[5]['test_method_and_commands'].append('初轮包含“国家＋SUM”合法输出被首列标量抽取误判，以及真实值/字段/期间补丁失效两类问题；评测修正定位实际SUM投影，业务补丁修复采用通用校验及独立反例，未改参考金额。')
    previous_flow2 = 'eval/artifacts/d3/b/clarify-flow-v2/report.json'
    followup_analysis = 'eval/reports/d3/b/followup-failure-analysis.md'
    if local_path(previous_flow2).is_file() and paths['flow'] != previous_flow2:
        records[5]['actual_results'].append('历史第二轮flow：' + check_summary(read(previous_flow2)) + '；字段迁移时模型额外移除Canada筛选造成条件丢失，与初轮评测列抽取问题分别记录。')
        records[5]['evidence'].append(previous_flow2)
    aborted_flow3 = 'eval/artifacts/d3/b/clarify-flow-v3/aborted.json'
    if local_path(aborted_flow3).is_file():
        aborted = read(aborted_flow3)
        records[5]['actual_results'].append(f"历史第三轮flow：{aborted['status']}，已实际API请求{aborted['actual_api_requests']}次；参考只读事务在模型调用期间闲置触发原有idle-in-transaction超时，未形成完整成绩。原响应与中止记录保留，属于评测连接生命周期问题。")
        records[5]['test_method_and_commands'].append('修复runner使用短只读参考事务，不放宽数据库超时、只读或gold标准；中止轮不得补写完整通过成绩。')
        records[5]['evidence'].append(aborted_flow3)
    previous_flow4 = 'eval/artifacts/d3/b/clarify-flow-v4/report.json'
    if local_path(previous_flow4).is_file() and paths['flow'] != previous_flow4:
        records[5]['actual_results'].append('历史第四轮flow：' + check_summary(read(previous_flow4)) + '；已确认intent保留2023，但生成SQL漏期间导致303.96对独立2023参考55.44。属于真实产品条件丢失，与第三轮评测参考连接中止不同。')
        records[5]['test_method_and_commands'].append('对D3已明确确认/补丁的Chinook发票日期增加WHERE语义AST保护及技术repair；复杂未覆盖结构保守拒绝，不改变原参考答案。')
        records[5]['evidence'].append(previous_flow4)
    previous_flow5 = 'eval/artifacts/d3/b/clarify-flow-v5/report.json'
    if local_path(previous_flow5).is_file() and paths['flow'] != previous_flow5:
        records[5]['actual_results'].append('历史第五轮flow：' + check_summary(read(previous_flow5)) + '技术检查项通过，但独立第二遍逐SQL读发现country-field的SELECT/GROUP仍使用invoice.billing_country，与已确认customer.country口径不符。相同金额不能证明投影/分组语义正确，因此不能把该轮作为完整语义验收通过。')
        records[5]['evidence'].append(previous_flow5)
    previous_ui1 = 'eval/artifacts/d3/b/ui-live-v1/report.json'
    if local_path(previous_ui1).is_file() and paths['ui'] != previous_ui1:
        old_ui = read(previous_ui1)
        records[6]['actual_results'].append(f"历史首次UI观察状态{old_ui.get('status')}，报告登记checks={len(actual_checks(old_ui))}、screenshots={len(old_ui.get('screenshots', []))}；相对api-records路径直接relative_to绝对项目根导致观察脚本中止。原错误报告和实际请求保留，不计为完成截图或业务通过。")
        records[6]['test_method_and_commands'].append('仅正规化观察脚本的本地路径，再新建输出目录完成真实UI操作；未因此修改业务prompt、标准答案或重建数据库。')
        records[6]['evidence'].append(previous_ui1)
    previous_ui2 = 'eval/artifacts/d3/b/ui-live-v2/report.json'
    ui2_observation = 'eval/reports/d3-ai-review/ui-v2-additional-observation.json'
    if local_path(previous_ui2).is_file() and paths['ui'] != previous_ui2:
        old_ui2 = read(previous_ui2)
        records[6]['actual_results'].append(f"历史第二次UI观察状态{old_ui2.get('status')}；真实可信year:2024按钮已写入2024 current与2023 base，但仍返回NEEDS_CLARIFICATION/L2，属于残留time_ambiguous导致的真实交互缺陷。自由输入flow与21道初始层级不能代替此按钮路径验收。")
        records[6]['pending_or_limitations'].append('开发21道与flow-v6采集在按钮残留旗标修复前；它们用于各自初次分类/自由输入与条件修改范围。最终真实按钮/UI证据需在修复后另采，不冒称21题全部路径或多轮EX。')
        records[6]['evidence'].append(previous_ui2)
        if local_path(ui2_observation).is_file():
            records[6]['evidence'].append(ui2_observation)
    previous_ui3 = 'eval/artifacts/d3/b/ui-live-v3/report.json'
    if local_path(previous_ui3).is_file() and paths['ui'] != previous_ui3:
        old_ui3 = read(previous_ui3)
        records[6]['actual_results'].append(f"历史第三次UI观察状态{old_ui3.get('status')}；已登记{len(old_ui3.get('screenshots', []))}张截图和{len(actual_checks(old_ui3))}项检查。按钮后的请求编号在折叠面板DOM内但不可见，观察脚本等待visible超时；与第二轮真实按钮残留旗标缺陷分开，原失败报告保留。")
        records[6]['evidence'].append(previous_ui3)
    button_path = inputs.get('button_api') or 'eval/artifacts/d3/b/button-api-v1/report.json'
    if local_path(button_path).is_file():
        button = read(button_path)
        records[6]['actual_results'].append('按钮残留旗标增量修复后的真实API回归：' + check_summary(button) + f"；actual_api_requests={button.get('actual_api_requests')}，保留预测={button.get('protected_holdout_predictions', 0)}。有效年份会清除期间歧义，另有缺指标仍L2且不执行SQL；这是受影响按钮路径回归，不是全部21题多轮成绩。")
        records[6]['evidence'].append(button_path)
        button_run = Path(button_path).parent.as_posix() + '/run.json'
        if local_path(button_run).is_file():
            records[6]['evidence'].append(button_run)
        button_observation = Path(button_path).parent.as_posix() + '/independent-observation.json'
        if local_path(button_observation).is_file():
            observed = read(button_observation)
            records[6]['actual_results'].append('按钮报告首条reason误写另有缺指标，新增独立观察按保存raw区分：有效2024按钮实际SUCCEEDED/L0，缺指标反例实际NEEDS_CLARIFICATION/L2且无SQL；原report/raw没有改写。')
            records[6]['evidence'].append(button_observation)
            records[6]['pending_or_limitations'].append('同比输出须核对实际SQL是否乘100与显示单位：v7自由输入样本为fraction，v8按钮样本为ROUND后的百分数。不能仅凭同一yoy_growth_rate列名合并比对，不在本轮新增全局单位默认。')
    if local_path(followup_analysis).is_file():
        records[5]['evidence'].append(followup_analysis)
    extra_aw = 'eval/reports/d3-ai-review/aw-run2-additional-observation.json'
    if not aw_all_match and local_path(extra_aw).is_file():
        extra = read(extra_aw)
        records[3]['engineering_verdict'] = '实测完成，参考字段歧义待人工核对'
        records[3]['pending_or_limitations'].append(extra['reason'] + ' strict分数保持原报告；系统业务正确性暂不能确定。原两遍AI漏检意见保留。')
        records[3]['evidence'].extend([extra_aw, extra_aw.removesuffix('.json') + '.md'])
    elif not aw_all_match:
        records[3]['engineering_verdict'] = '实测完成，存在未匹配结果待复核'
        records[3]['pending_or_limitations'].append('严格EX未全部匹配，请按实际响应区分参考标准问题与系统错误；尚不能自动判定业务正确。')
    for row in records:
        for path in row['changed_files'] + row['evidence']:
            local_path(path)
            if not local_path(path).exists():
                raise FileNotFoundError("Missing item evidence/source: " + path)
    evening = {"requirement": "§4.3：AW能用，③至少完成一次澄清→回答闭环。",
               "aw_actual": f"{aw['correct']}/{aw['prediction_count']}实际AW开发查询匹配gold；全21响应实际执行AW。",
               "clarification_actual": check_summary(flow),
               "ui_actual": check_summary(ui),
               "passed": aw_usable and flow_ok and ui_ok,
               "evidence": [paths['aw_dev'], paths['aw_observation'], paths['flow'], paths['ui']]}
    if local_path(free_growth_path).is_file():
        evening['evidence'].append(free_growth_path)
    summary = {"title": TITLE, "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "status": "ENGINEERING_CHECKS_PASS_HUMAN_REVIEW_PENDING" if all(row['engineering_verdict'].startswith('实测完成') for row in records) and evening['passed'] else "ACTUAL_ISSUES_RECORDED_HUMAN_REVIEW_PENDING",
               "original_item_count": len(records), "items": records, "evening_checkpoint": evening,
               "modules": modules, "aw_development_ex": {key: aw[key] for key in ('correct', 'prediction_count', 'exploratory_ex', 'actual_model_attempts', 'usage')},
               "clarify_development": {"passed": clarify_passed, "total": clarify_total, "l2_recall": clarify.get('l2_recall'), "non_l2_false_ask_rate": clarify.get('non_l2_false_ask_rate')},
               "holdout": {"aw_count": awlabels['holdout_count'], "clarify_count": clabels['holdout'], "prediction_count": 0, "content_in_delivery": False},
               "human_review_status": "pending_human_review", "input_files": {key: {"file": path, "sha256": digest(path)} for key, path in paths.items()},
               "runtime_source_hashes_at_report_build": {path: digest(path) for path in core},
               "historical_evidence_preservation": read("eval/artifacts/d3/root-interface/history-preservation.json"),
               "scope": "D3 A4+B4和晚间检查点；夹具不计实际模型成绩；合成开发成绩不等于D5冻结后正式保留成绩。"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (TITLE + '.json')).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = [f"# {TITLE}", "", f"生成时间（UTC）：{summary['created_at_utc']}。", "",
             "本报告按总计划的A4＋B4原始八项逐项记录，再单独验收晚间检查点。证据来自已经实际运行并保存的文件；脚本只读取文件，不调用模型或数据库、不改代码/标签/人工审核记录。", "",
             f"当前状态：**{summary['status']}**。人工审核统一为 `pending_human_review`，没有A/B签字或人工确认日期。", "",
             f"实际开发结果：AW EX **{aw['correct']}/{aw['prediction_count']}（{aw['exploratory_ex']:.2%}）**；澄清初次层级/SQL执行状态 **{clarify_passed}/{clarify_total}**（不等于21题全部多轮EX）；模块回归 **{modules['passed']}项通过**。按钮、自由输入和L1切换的实际闭环另由flow/UI逐步证据验收。18道D3保留题未预测、未计算成绩、详细题目与答案不在本交付包。", "",
             "## 原清单对应关系", "", "|编号|分工|原始要求|本轮结论|", "|---|---|---|---|"]
    for row in records:
        lines.append(f"|{row['number']}|{row['group']}|{row['requirement']}|{row['engineering_verdict']}|")
    for row in records:
        lines += ["", f"## {row['number']}. {row['group']}：{row['requirement']}", "", "**实现情况**：" + row['implementation'], "", "**改动文件**：", ""]
        lines += ["- " + link(path) for path in row['changed_files']]
        for title, key in (("测试方法与实际命令", 'test_method_and_commands'), ("实际结果", 'actual_results')):
            lines += ["", f"**{title}**：", ""] + ["- " + text for text in row[key]]
        lines += ["", "**证据位置**：", ""] + ["- " + link(path) for path in row['evidence']]
        lines += ["", "**未完成事项、人工审核或限制**：", ""] + ["- " + text for text in row['pending_or_limitations']]
        lines += ["", f"**逐项判定**：{row['engineering_verdict']}；人工状态 `{row['human_review_status']}`。"]
    lines += ["", "## 晚间检查点（不并入八项计数）", "", evening['requirement'], "",
              f"- AW实际结果：{evening['aw_actual']}", f"- 澄清闭环：{evening['clarification_actual']}", f"- 实际页面：{evening['ui_actual']}", f"- 自动检查判定：{'通过' if evening['passed'] else '存在未通过项'}。", ""]
    lines += ["证据：" + "、".join(link(path) for path in evening['evidence']), "", "## 两遍AI预审与人工收尾", "",
              "先保留第一遍材料与发现，再独立第二遍核对真实schema、SQL/结果、规则及反例；目录更正有旧版和原始模型响应。人审无需重新追找源码，请从以下表和AI报告核对：", "",
              "- " + link("eval/reports/d3-acceptance/A待人工核对表.md"),
              "- " + link("eval/reports/d3-ai-review/catalog-pass2.md"),
              "- " + link("eval/reports/d3-ai-review/aw-dev-v2-pass1.md") + "；" + link("eval/reports/d3-ai-review/aw-dev-pass2.md"),
              "- " + link("eval/reports/d3/b/AI预审第一遍.md") + "；" + link("eval/reports/d3-ai-review/clarify-dev-pass2.md"),
              "- " + link("eval/reports/d3-ai-review/integration-pass2.md"), "",
              "目录枚举证据不足项优先确认，其次澄清-20的分母期间，再逐题核对21道AW与21道澄清开发标签。AI建议不代替人工签字，人工未核对的gold不能写成已审核。保留题的详细审核在独立环境另行进行。"]
    if local_path(extra_aw).is_file():
        lines += ['', 'AW真实第二轮发现aw-07“产品编号”字段歧义，优先人工确认：' + link(extra_aw.removesuffix('.json') + '.md') + '。原两遍通过意见存在漏检，历史文件保留；当前不改题面/gold/prompt，也不把严格分数改成21/21。']
    for name in inputs.get('human_review_documents', []):
        lines += ["", "统一人工核对入口：" + link(name)]
    lines += ["", "## 复现、版本与交付边界", "",
              "运行环境沿用Python3.12和已验证deepseek-flash，原D1/D2证据未覆盖。各轮真实请求、原始失败、修复后回归和模型用量分开保留；本报告不把预测前修订、离线观察或夹具测试当成实际API新成绩。", "",
              "历史证据保护：" + link("eval/artifacts/d3/root-interface/history-preservation.json") + f"；实查{summary['historical_evidence_preservation']['protected_old_evidence_count']}个旧D1/D2文件，状态{summary['historical_evidence_preservation']['status']}，changed={summary['historical_evidence_preservation']['changed']}，missing={summary['historical_evidence_preservation']['missing']}。", "",
              f"构建中文目录{catalog['llm_request_attempts']}次与最终AW开发{aw['actual_model_attempts']}次是不同用途的请求；澄清统计见其实际报告，不能将不同用途调用量混为测试题数。原始响应对应的运行prompt SHA、git基线及dirty状态在各run报告中。报告生成时源码SHA另存JSON，后续专项优化不应改写这些历史run。", "",
              "所有证据链接均相对项目根组织。先完整解压ZIP，再用浏览器打开此HTML；Markdown查看器也可打开相对源码/JSON/日志。不要仅发送Markdown而省略对应文件。", "",
              "交付不含真实.env、运行密码、模型权重、向量索引大文件、原始数据库卷、保留题内容或专项调参目录。含保留题文字的造题脚本不附入开发包，替代交付为开发集视图、标签数量/哈希manifest和gold真实结果。", "",
              "D4的LLM剪枝/消融/压测/完整多轮与跨源流程，以及D5冻结后保留集正式成绩，本日没有提前执行。", "",
              "报告机器记录：" + link("eval/reports/d3-acceptance/" + TITLE + ".json")]
    content = "\n".join(lines) + "\n"
    (OUT / (TITLE + '.md')).write_text(content, encoding='utf-8')
    from markdown_it import MarkdownIt
    body = MarkdownIt('commonmark').enable('table').render(content)
    page = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + html.escape(TITLE) + '</title><style>body{max-width:1120px;margin:32px auto;padding:0 24px;font:16px/1.75 "Microsoft YaHei",sans-serif;color:#243247;background:#fff}h1{font-size:29px}h2{margin-top:42px;border-bottom:2px solid #dbe4ef;padding-bottom:9px}a{color:#145f9b;overflow-wrap:anywhere}code{background:#f2f5f8;padding:2px 5px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #d5deea;padding:9px;text-align:left;vertical-align:top}th{background:#edf3fa}img{max-width:100%;height:auto}@media print{body{font-size:11px;margin:0}a{color:inherit}h2{break-after:avoid}tr{break-inside:avoid}}</style></head><body>' + body + '</body></html>'
    (OUT / (TITLE + '.html')).write_text(page, encoding='utf-8')
    write_manifest(inputs, records, paths, ui)
    return {"status": summary['status'], "items": len(records), "report": (OUT / (TITLE + '.html')).relative_to(ROOT).as_posix(), "modules": modules['passed']}


def write_manifest(inputs, records, paths, ui):
    include = ["qa_agent", "api", "ui", "requirements.txt", ".env.example", "README.md",
               "docker-compose.yml", "docker-compose.aw.yml", "scripts/bootstrap_aw.py", "scripts/build_catalog.py",
               "scripts/bootstrap_db.py", "scripts/download_embeddings.py", "scripts/check_embeddings.py", "scripts/build_value_index.py",
               "scripts/start_demo.ps1", "scripts/start_api.ps1", "scripts/start_demo.sh",
               "scripts/build_aw_catalog.py", "scripts/build_schema_index.py", "scripts/revise_d3_aw_dev_v2.py",
               "scripts/review_d3_aw_pass2.py", "scripts/review_d3_aw_catalog_pass2.py", "scripts/record_d3_aw_run2_observation.py",
               "scripts/check_d3_clarify_labels.py", "scripts/capture_d3_clarify_demo.py",
               "scripts/capture_d2_demo.py", "scripts/run_d3_shared_regression.py",
               "scripts/check_d3_free_growth_readonly.py",
               "scripts/build_d3_delivery.py", "scripts/package_stage_delivery.py",
               "eval/d3_aw_eval.py", "eval/d3_aw_reanalyze.py", "eval/d3_schema_eval.py",
               "eval/d3_clarify_eval.py", "eval/d3_clarify_flow_eval.py", "eval/run_eval.py", "eval/metrics.py",
               "eval/d3_clarify_button_eval.py",
               "data/catalog/adventureworks.yaml", "data/catalog/aw_ai_directory_corrections.json",
               "data/catalog/chinook.yaml", "data/aliases/aliases-d2-reviewed.csv", "data/rules/metric_definitions.json", "data/db/aw_source_manifest.json", "data/db/aw_live_data_manifest.json",
               "eval/datasets/d3/aw_schema_link.dev.jsonl", "eval/datasets/d3/aw_schema_link.dev.v2.jsonl",
               "eval/datasets/d3/aw_schema_link_manifest.json", "eval/datasets/d3/aw_schema_link_v2_manifest.json",
               "eval/datasets/d3/clarify/dev.jsonl", "eval/datasets/d3/clarify/manifest.json",
               "eval/artifacts/d3", "eval/reports/d3-ai-review", "eval/reports/d3/b", "eval/reports/d3-acceptance",
               "eval/reports/d3-aw-live-dev-run1", "eval/reports/d3-aw-schema-dev-final",
               "eval/reports/d3-aw-schema-dev-v2", "eval/reports/d3-aw-schema-dev-v2-facets", "eval/reports/d3-aw-schema-dev-v2-facetcoverage",
               "notes/d3/A线实施与实测记录.md", "notes/d3/b-shared-integration.md", "notes/dev-log.md", "notes/d2/业务指标口径提案.md", "notes/共享协议确认.md",
               "notes/references/d3-and-special/方案.md", "notes/references/d3-and-special/03-智能语义校验与澄清-技术方案.md",
               "notes/references/d3-and-special/module-reference-manifest.json",
               "tests/test_d3_schema_linker.py", "tests/test_d3_clarify.py", "tests/test_d3_clarify_ai_counterexamples.py",
               "tests/test_d3_clarify_ui.py", "tests/test_d3_ratio_binding.py", "tests/test_llm.py", "tests/test_config.py", "tests/test_sql_executor.py"]
    include += [str(Path(paths[key]).parent).replace('\\', '/') for key in FINAL_KEYS]
    include += [str(Path(paths['aw_dev']).parent).replace('\\', '/')]
    include += [row['file'] for row in ui.get('screenshots', [])]
    # Preserve actual earlier UI screenshots alongside failed observation runs,
    # including v2/v3. Their JSON traces are already included in D3 artifacts.
    for report in (ROOT / 'eval/artifacts/d3/b').glob('ui-live-v*/report.json'):
        earlier_ui = read(report.relative_to(ROOT).as_posix())
        include += [row['file'] for row in earlier_ui.get('screenshots', []) if row.get('file')]
    include += inputs.get('extra_include', []) + inputs.get('human_review_documents', [])
    include += [path for row in records for path in row['evidence'] + row['changed_files']]
    # Optional runtime-independent files vary across the original project; the
    # item/source links above are mandatory, this portability list is conditional.
    include = sorted({name for name in include if local_path(name).exists()})
    manifest = {"stage": "D3", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "entry_document": "eval/reports/d3-acceptance/" + TITLE + '.html',
                "include": include, "exclude_prefixes": PROTECTED,
                "holdout_content_policy": "AW9+clarify9: counts/hashes only; no questions/gold/predictions; question-builder source omitted",
                "human_review_status": "pending_human_review"}
    (OUT / 'delivery-input-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True,
                        help='Project-relative JSON with clarify_dev/flow/ui/modules_command actual paths.')
    parser.add_argument('--check-inputs', action='store_true', help='Readiness check only; no report or package mutation.')
    args = parser.parse_args()
    source = args.inputs if args.inputs.is_absolute() else ROOT / args.inputs
    if not source.resolve().is_relative_to(ROOT.resolve()):
        raise SystemExit('Input configuration must be inside the project.')
    inputs = json.loads(source.read_text(encoding='utf-8'))
    missing = [key for key in FINAL_KEYS if not inputs.get(key) or not local_path(inputs[key]).is_file()]
    if args.check_inputs:
        incomplete = []
        statuses = {}
        for key in FINAL_KEYS:
            if key in missing:
                continue
            record = read(inputs[key])
            status = record.get('exit_code') if key == 'modules_command' else record.get('status')
            statuses[key] = status
            if status in ('RUNNING', 'PENDING', 'NOT_RUN'):
                incomplete.append(key)
            elif status is None:
                # Flow/UI artifacts originally expose actual checks/counters,
                # not a status flag. Do not invent a missing runtime status.
                checks = actual_checks(record)
                if key == 'modules_command' or not checks or record.get('total', len(checks)) != len(checks):
                    incomplete.append(key)
                else:
                    statuses[key] = 'ACTUAL_CHECKS_RECORDED_WITHOUT_STATUS_FIELD'
        ready = not missing and not incomplete
        print(json.dumps({'ready': ready, 'missing_actual_reports': missing,
                          'incomplete_actual_reports': incomplete, 'actual_statuses': statuses}, ensure_ascii=False))
        raise SystemExit(0 if ready else 2)
    if missing:
        raise SystemExit('Missing actual final reports: ' + ', '.join(missing))
    result = generate(inputs)
    record = {"command": [sys.executable, '-B', *sys.argv],
              "cwd": str(ROOT), "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "exit_code": 0, "actual_result": result,
              "measurement": "Report construction from preserved files only; no API/model/DB queries",
              "generator_sha256": digest('scripts/build_d3_delivery.py')}
    (OUT / 'build-report-command.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
