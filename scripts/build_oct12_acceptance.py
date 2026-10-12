"""Build the Oct12 acceptance from completed, separately saved DEV evidence."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "eval/reports/oct12/acceptance"
FINAL_MODULE = "eval/artifacts/oct12/full-module-005"
FINAL_SNAPSHOT = "eval/artifacts/oct12/runtime-snapshot-004/manifest.json"
UI_SNAPSHOT = "eval/artifacts/oct12/runtime-snapshot-003/manifest.json"
SQL22_RUN = "eval/artifacts/oct12/sql22-live-004"


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def link(name, label=None):
    path = ROOT / name
    if not path.exists():
        raise ValueError("Missing acceptance evidence: " + name)
    return f"[{label or name}]({Path(os.path.relpath(path, OUT)).as_posix()})"


def main():
    review = read("eval/reports/oct12/manual-review/全部待人工审核统一入口.json")
    module = read(FINAL_MODULE + "/command.json")
    module_text = (ROOT / (FINAL_MODULE + "/pytest.stdout.txt")).read_text(encoding="utf-8")
    tests = re.search(r"(\d+) passed in ([\d.]+)s", module_text)
    if module["exit_code"] or not tests:
        raise ValueError("Final module verification has not passed")
    joins = read("eval/artifacts/oct12/join-live-002/report.json")
    targets = read("eval/artifacts/oct12/targets-live-002/report.json")
    retry = read("eval/artifacts/oct12/targets-live-003/report.json")
    d2 = read("eval/artifacts/oct12/d2-dev-live-002/report.json")
    if len(d2["results"]) != 3 or any(row["exit_code"] for row in d2["results"].values()):
        raise ValueError("Final complete DEV run has not finished")
    ui = read("eval/artifacts/oct12/ui-live/run-004/report.json")
    visual = read("eval/artifacts/oct12/ui-live/run-004/visual-review.json")
    ui_snapshot = read(UI_SNAPSHOT)
    snapshot = read(FINAL_SNAPSHOT)
    gold = read("eval/artifacts/oct12/review-gold/readonly-rerun/readonly-verification.json")
    repairs = read("eval/artifacts/oct12/repairs-live-001/report.json")
    final_sql = read("eval/artifacts/oct12/sql-final-live-003/report.json")
    sql22 = read(SQL22_RUN + "/report.json")
    sql22_record = read(SQL22_RUN + "/sql-22.json")
    date_review = read("notes/oct12/staging/sql22/ai-review-v5-pass-2-probes.json")
    if repairs["matched"] != 2 or final_sql["status"] != "COMPLETED" or ui["state"] != "PASS" or visual["state"] != "PASS":
        raise ValueError("Latest scoped or browser verification has not passed")
    if (sql22["count"] != 1 or sql22["matched"] != 1 or not sql22["literal_strict_before_intent"] or
            sql22["actual_status"] != "SUCCEEDED" or not sql22_record["comparison"]["matched"] or
            not sql22_record["literal_strict_before_intent"] or sql22_record["gold_changed"] or
            sql22["held_predictions"] or sql22["human_gold_changes"]):
        raise ValueError("Final scoped SQL22 actual regression has not passed unchanged gold")
    if (not date_review["passed"] or date_review["candidate_sha256"] != snapshot["source_sha256"]["qa_agent/clarify/rules.py"] or
            sha256((ROOT / "qa_agent/clarify/rules.py").read_bytes()).hexdigest() != date_review["candidate_sha256"]):
        raise ValueError("Applied final date source differs from the independently reviewed candidate")
    components = ["qa_agent/rag/answer.py", "qa_agent/rag/service.py", "ui/app.py"]
    if any(snapshot["source_sha256"][name] != ui_snapshot["source_sha256"][name] for name in components):
        raise ValueError("Phase3 screenshots cannot be reused after an unverified RAG/UI component change")
    checks = [passed for case in ui["cases"] for passed in case["checks"].values()]
    if len(ui["cases"]) != 5 or len(checks) != 33 or not all(checks) or visual["screenshots_inspected"] != 5:
        raise ValueError("Actual Phase3 UI five-scenario evidence is incomplete")
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
               "status": "技术实施与实际开发验收完成；业务与标签争议保留人工决定",
               "module_passed": int(tests[1]), "module_seconds": float(tests[2]),
               "join": {k: joins.get(k) for k in ["correct", "legacy_correct", "prediction_count", "gold_human_accepted_count"]},
               "targets_original": {k: targets[k] for k in ["count", "matched"]},
               "connectivity_retry": {k: retry[k] for k in ["count", "matched", "explicit_retry_ids"]},
               "latest_by_target": {row["id"]: row["comparison"] for row in targets["records"]},
               "d2_dev": {name: item["summary"] for name, item in d2["results"].items()},
               "manual_review": review["summary"], "holdout_predictions": 0,
               "human_records_written": 0, "business_source_snapshot": FINAL_SNAPSHOT,
               "ui_source_snapshot": UI_SNAPSHOT,
               "ui_report": "eval/artifacts/oct12/ui-live/run-004/report.json", "ui_visual_review": visual,
               "ui_checks": {"phase": "phase3", "scenarios": len(ui["cases"]), "passed": sum(checks), "total": len(checks)},
               "final_rag_ui_components_unchanged_since_phase3": {name: snapshot["source_sha256"][name] for name in components},
               "phase4_date_repair": {"candidate_review": "notes/oct12/staging/sql22/ai-review-v5-pass-2-probes.json",
                                       "candidate_sha256": date_review["candidate_sha256"], "actual_scoped_report": SQL22_RUN + "/report.json",
                                       "actual_scoped_result": sql22, "full_35_or_77_rerun_after_repair": False},
               "runtime_capture_contexts": {
                   "phase2": {"api": "eval/artifacts/oct12/api-records/live-002", "provider": "eval/artifacts/oct12/provider-captures/live-001"},
                   "phase3": {"api": "eval/artifacts/oct12/api-records/live-003", "provider": "eval/artifacts/oct12/provider-captures/live-003"},
                   "phase4": {"api": "eval/artifacts/oct12/api-records/live-004", "provider": "eval/artifacts/oct12/provider-captures/live-004"}}}
    summary["post_repair_checks"] = repairs
    summary["phase3_sql_35"] = {key: final_sql.get(key) for key in ["correct", "legacy_correct", "prediction_count", "gold_human_accepted_count"]}
    for row in retry["records"]:
        summary["latest_by_target"][row["id"]] = row["comparison"]
    summary["latest_target_matched"] = sum(row.get("matched") is True for row in summary["latest_by_target"].values())
    specs = [
        ("12-01", "地区口径默认及显式覆盖", "销售额/发票默认 invoice.billing_country；客户统计默认 customer.country。明确按居住地统计销售额时优先采用客户所在地。", ["qa_agent/clarify/rules.py", "qa_agent/clarify/extractor.py", "qa_agent/clarify/service.py"], ["eval/artifacts/oct12/targets-live-002/oct12-default-region.json", "eval/artifacts/oct12/targets-live-002/oct12-explicit-region.json"], "2024 巴西两种来源均真实通过，SQL实际分别读取账单国家和客户国家。", "无新增业务决定；原题标签的过期澄清理由另列人工审核。"),
        ("12-02", "缺期间默认全数据，保留会话年份", "只给授权的热门曲目、复购、客户排名补 all_data；已有日期保留，不硬编码数据年份。", ["qa_agent/clarify/rules.py", "qa_agent/clarify/extractor.py", "qa_agent/clarify/state.py"], ["eval/artifacts/oct12/targets-live-003/oct12-default-repeat.json", "eval/artifacts/oct12/targets-live-002/oct12-context-year.json", "eval/artifacts/oct12/review-gold/date-facts/readonly-verification.json"], "复购59人；续问前5位继续保留2023；实际发票2021-01-01至2025-12-22，逐年计数83/83/83/83/80。", "真实网络失败和独立重跑均保留，没有把失败改写为成功。"),
        ("12-03", "谁买得最多与热门曲目指标", "缺对象的谁买得最多按客户SUM(invoice.total)，热门曲目仍SUM(invoice_line.quantity)，范围限Chinook授权场景。", ["qa_agent/clarify/rules.py", "qa_agent/clarify/clarify_rules.yaml"], ["eval/artifacts/oct12/targets-live-002/oct12-default-who.json", "eval/artifacts/oct12/targets-live-003/oct12-default-track.json", "notes/oct12/phase2-target-readonly-diagnosis.md"], "前3客户和热门3曲目真实通过；额外姓名是描述列，旧EX列数失败另存。", "sp03-19 gold Top1与通用缺N默认Top10冲突待人工决定；原始EX失败不放宽行数。"),
        ("12-04", "金额占比的同期全部金额分母", "只适用于发票金额/销售额。程序附上可信分母，AST验证国家分子和全体同期发票分母；客户数量不能套金额分母。", ["qa_agent/sql/ratio_guard.py", "qa_agent/sql/validator.py", "qa_agent/clarify/rules.py"], ["eval/artifacts/oct12/targets-live-002/sp03-22.json", "eval/artifacts/oct12/targets-live-002/oct12-context-numerator.json", "tests/test_oct12_sql_and_ex.py"], "France2024占比通过；多轮改德国分子保持2023及全体分母；错误国家/缩窄分母/指标不符反例均拒绝。", "旧百分数与fraction评分争议保留，不自动重写旧gold；新prompt约定原始分数展示百分比。"),
        ("12-05", "老美直接链接USA", "依据用户12号任务授权，只将原来两条客户/账单国家的老美候选关系改为直接批准，新版本别名和索引保留旧版。", ["data/aliases/aliases-oct12-approved.csv", "scripts/prepare_oct12_aliases.py", ".env.example"], ["eval/artifacts/oct12/nlu-clarify/alias-index-build.json", "eval/artifacts/oct12/targets-live-002/oct12-alias-us.json"], "81关系中56直接、23候选、2仍停用；5607向量复用；真实老美客户COUNT13且L0。", "剩余2别名仍需人工审核；未擅自批准其他关系。"),
        ("12-06", "JOIN放行与修复筛选保护", "取消依赖artist/genre/media_type已绑定才放行JOIN的条件。实际目录外键校验关联，禁止OR/CROSS/错键绕过；修复不得换真实筛选列、值或逻辑范围。", ["qa_agent/pipeline.py", "qa_agent/sql/repair_guard.py", "qa_agent/sql/validator.py"], ["tests/test_oct12_sql_and_ex.py", "eval/artifacts/oct12/join-live-002/report.json", "eval/artifacts/oct12/nlu-fixes-002/NLU真实回归修复记录.md"], "真实15道JOIN全部通过；员工名/姓已指向真实employee列；错误FK及换列修复被模块测试拒绝。", "保留常规派生表校验，未把所有复杂SQL宣称已证明正确；AW完整开发模型集本轮未复跑。"),
        ("12-07", "补10–15道自然JOIN回归", "新增15道全部DEV题：艺术家/媒体/雇员/客户/购买明细等关联，含未知流派、空结果、零计数与错拼。", ["scripts/build_oct12_join_dev.py", "eval/datasets/oct12/chinook_join_dev_v1.jsonl"], ["eval/artifacts/oct12/join-gold/manifest.json", "eval/artifacts/oct12/join-live-001/report.json", "eval/artifacts/oct12/join-live-002/report.json"], "15/15只读gold执行；首轮14/15，修复员工范围后第二轮15/15，gold未改。", "15道参考答案仍pending_human_review，自动EX是开发探索值。"),
        ("12-08", "候选最低分与时间词", "fuzzy最低0.60、vector最低0.65，自动绑定门槛独立；每年/今年等时间词不当实体。补这个流派错拼、员工姓名范围与完整日期strict-before误读为月份的窄修复。", ["qa_agent/nlu/linker.py", "qa_agent/clarify/rules.py", "tests/test_oct12_nlu_clarify.py", "tests/test_oct12_nlu_live_fixes.py", "tests/test_oct12_before_date.py"], ["eval/artifacts/oct12/targets-live-002/sp03-14.json", "eval/artifacts/oct12/targets-live-002/sp01-22.json", "eval/artifacts/oct12/nlu-fixes-002/module-tests.txt", "eval/artifacts/oct12/sql22-diagnosis-004/readonly-diagnosis.json", "notes/oct12/staging/sql22/ai-review-v5-pass-2-probes.json", SQL22_RUN + "/sql-22.json"], "低分候选不入卡；2022/2023每年输出两年；Gudian这个流派实际Classical74；早期独立NLU/澄清174模块通过。日期候选独立22/22，应用后真实sql-22补测1/1，严格早于2004-01-01只保留end、无虚构start；未改题面或gold。", "阈值未用保留集调优；日期修复不扩展时刻或新业务谓词。早期候选误吞未支付条件的失败记录保留。最后只补测sql-22，未把phase3整套35题34/35回填为35/35。"),
        ("12-09", "同比一次期间卡与显式分子", "同一期间缺口合并为一条；当前/基期有角色，显式France分子及Germany续问更新链接和来源。", ["qa_agent/clarify/rules.py", "qa_agent/clarify/extractor.py", "qa_agent/clarify/service.py"], ["eval/artifacts/oct12/targets-live-002/sp03-06.json", "eval/artifacts/oct12/targets-live-002/sp03-22.json"], "sp03-06首问期间缺口数1，补2024对2023后真实通过；sp03-22明确分子通过。", "首轮同比只返回题问增长率而旧gold附两金额列；旧输出评分和投影合同争议完整保留待审核。"),
        ("12-10", "数字核验重生成一次后未核实", "只对第二次数字核验仍失败的回答添加未核实标记和本地校验警告，正常返回；引用ID与归属硬校验不降级。", ["qa_agent/rag/answer.py", "qa_agent/rag/service.py", "tests/test_oct12_rag_ui.py"], ["eval/artifacts/oct12/ui-live/run-003/rag-03-raw.json", "eval/artifacts/oct12/ui-live/run-003/rag-03.png", "eval/artifacts/oct12/ui-live/run-004/report.json", "eval/artifacts/oct12/ui-live/phase3-summary.json", "eval/artifacts/oct12/rag-ui/final-module-verification.json"], "模块覆盖两次生成、数字失败降级和引用硬错；phase2 run003真实rag-03重生成一次后仍数字核验失败，警告和未核实前缀实际可见。phase3 run004首次生成即引用E6和E1，通过数字核验，未触发回退。相关RAG/UI组件与phase4的SHA一致。", "run003未核实回答不是语义忠实度通过；run004机械核验通过也仍pending_human_review。历史分支实证不当成新版本再次触发。"),
        ("12-11", "来源文案、业务澄清理由及百分比", "来源使用实际候选方法/分数，去除内部技术关系说明；比例增长只格式化展示副本，原结果保持可审计。", ["ui/app.py", "qa_agent/sql/result_format.py", "qa_agent/sql/prompts/multi_table.txt"], ["eval/artifacts/oct12/ui-live/run-004", "eval/artifacts/oct12/ui-live/run-004/visual-review.json", "tests/test_oct12_rag_ui.py"], "phase3 run004真实5/5页面场景、33/33DOM/请求检查，5张截图逐张AI视觉核验：拼音实际1.00，比例11.20%、增长率24.24%；原始fraction仍保留。", "run001曾有3张渲染时序问题；run003实际33/36，比例SQL被严格守卫拒绝，失败保留；修复后run004另存33/33。run004对应snapshot003，之后rules.py日期窄修复未重拍5场景，UI/RAG组件未变。"),
        ("12-12", "方案EX主指标及旧EX", "主EX忽略列名/列顺序，用稳定全局列映射，只允许已证实的直接文字/主键描述列；要求列、行数、重复行和指定排序不放宽。", ["eval/metrics.py", "eval/run_eval.py", "tests/test_oct12_sql_and_ex.py"], ["eval/artifacts/oct12/join-live-002/report.json", "eval/artifacts/oct12/targets-live-003/oct12-default-track.json", "eval/artifacts/oct12/d2-dev-live-002/report.json"], "新旧EX逐题并存；热门曲目多名称列新EX通过旧EX列数失败；sp03-19多9行依然判错。", "原始旧评分、被冻结专项评分和旧报告未回填；EX不能单独证明业务口径或参考正确。"),
        ("12-13", "所有未审核材料统一过表", "合并D1历史待核、D2待定、D3、专项和本轮；同一对象多格式去重，不同真实输出版本单独审。AW全524说明纳入。题面删除指令、去重、标签改动均给草案。", ["scripts/build_oct12_review.py", "scripts/check_oct12_review.py"], ["eval/reports/oct12/manual-review/全部待人工审核统一入口.html", "eval/reports/oct12/manual-review/全部待人工审核统一入口.json", "eval/reports/oct12/manual-review/保留集隔离边界.json"], "数量由末次实际构建给出，编辑/筛选/导出具体验证另列。此前已授权项单列，不重复要求签字。", "保存/导出只生成审核决定草稿，未自动改代码、题库、人工状态。51条阶段保留记录不在开发审查页展开。"),
        ("12-14", "两道新gold的依据与操作", "分别核验sql-38 NULL排名与robust-23指代范围；原数据库qa_reader、只读5秒查询与VALUES边界反例，提供两种选择。", ["scripts/verify_oct12_gold.py", "notes/oct12/gold-38-23-proposal.md", "notes/oct12/gold-38-23-proposal.json"], ["eval/artifacts/oct12/review-gold/readonly-rerun/readonly-verification.json", "eval/artifacts/oct12/review-gold/readonly-rerun/queries.sql", "notes/oct12/参考答案与计分争议提案.md"], "13/13只读查询成功；3503曲目大小/时长NULL均0；AVG393599.212103910933毫秒，Top3实际结果在提案。", "推荐已知大小Top3；全库等权AVG毫秒。人工决定前不修改任何现有gold或人工日期。"),
    ]
    summary["items"] = [{"id": i, "requirement": title, "implementation": impl, "changed_files": files,
                          "test_evidence": ev, "actual_result": actual, "pending_or_limits": pending,
                          "ai_verdict": "AI建议有条件通过" if i in {"12-03", "12-07", "12-13", "12-14"} else "AI建议通过"}
                         for i,title,impl,files,ev,actual,pending in specs]
    lines = ["# 10月12日任务逐项验收与证据", "", "本报告依据用户明确要求执行的12号任务，在原D1/D2/D3项目增量完成。五项业务决定已获授权；两道新gold、过期标签与回答正确性仍留人工审核。没有新建第二套系统、重导数据库或代填签名。技术完成与人工接受分开记录。", "",
             "## 实测摘要", "", f"全模块实际 **{tests[1]} passed，{tests[2]}秒**；新增JOIN第二轮 **{joins['correct']}/{joins['prediction_count']}**，首轮14/15及员工范围错误保留。17项定向第二轮首次 **{targets['matched']}/{targets['count']}**；两个真实网络失败独立重跑 **{retry['matched']}/{retry['count']}** 后，按每题最新记录为 **{summary['latest_target_matched']}/17**。该跨运行摘要不替代原始单轮成绩，仍有sp03-19 Top1/Top10合同冲突。", "",
             "|开发集|最终真实记录|限制|", "|---|---|---|"]
    for name in ["sql", "robust"]:
        item = d2["results"][name]["summary"]
        lines.append(f"|D2 {name}|新EX {item['correct']}/{item['prediction_count']}；旧EX {item.get('legacy_correct')}/{item['prediction_count']}|gold待审及异常逐条保留，非保留集正式成绩|")
    rag = d2["results"]["rag"]["summary"]
    lines += [f"|D2 RAG|{json.dumps(rag.get('api_status_counts'), ensure_ascii=False)}；Hit@5 {rag['hit_at_5']['passed']}/{rag['hit_at_5']['denominator']}；完整gold引文命中 {rag['exact_gold_quote_hit_at_5']['passed']}/{rag['exact_gold_quote_hit_at_5']['denominator']}|回答与引用语义人工审核{rag['answer_human_review_count']}，机械指标不等同答案准确率|", "",
              "Phase3 UI真实报告（5/5场景、33/33检查）：" + link("eval/artifacts/oct12/ui-live/run-004/report.json") + "；逐张截图AI视觉结论：" + link("eval/artifacts/oct12/ui-live/run-004/visual-review.json") + "。实际比例11.20%、增长率24.24%，raw保留原始fraction。各检查对象来自实际浏览器请求，模块AppTest模拟不并入真实问答数量。Phase2 run003为33/36，原比例失败完整保留；不能把run003称最终全部通过。", "",
              "最终Phase4源码与非敏感配置快照：" + link(FINAL_SNAPSHOT) + "；上述UI截图对应Phase3快照：" + link(UI_SNAPSHOT) + "。之后只对rules.py日期误读作窄修复，三份RAG/UI组件SHA已核对一致；截图不声称来自最终全部源码。运行仍Python3.12、deepseek-flash、原只读数据库，索引只因老美授权产生新版本。Phase2 API/provider捕获分别live-002/live-001，Phase3为live-003/live-003，Phase4为live-004/live-004；trace、时间与快照对应，目录名字不当作版本证明。", "",
              "## 原要求逐项记录", ""]
    lines[lines.index("## 原要求逐项记录"):lines.index("## 原要求逐项记录")] = [
        f"上述77题是完整Phase2原始成绩。随后修复两处实测技术问题：纯客户属性排序被误当缺消费指标、合法午夜TIMESTAMP被过严期间证明拒绝。候选先隔离测试并独立第二审，混合营收余文旁路被审查发现后改完整句式证明；模型N或主排序与原文不符不纠偏。Phase3真实SQL全35题重新运行 **{final_sql['correct']}/35**，旧EX {final_sql['legacy_correct']}/35；两处专门真实补测 **{repairs['matched']}/2**。随后发现sql-22完整日期被确定性解析成月份，Phase4独立二审后应用窄修复，仅按原题原gold进行真实sql-22补测 **{sql22['matched']}/{sql22['count']}**，状态{sql22['actual_status']}、严格早于只保留end。最终源码未重跑整套35或77题；不将34/35历史报告回填为35/35，也不把不同版本成绩拼成一次完整运行。", "",
        link("eval/artifacts/oct12/sql-final-live-003/report.json", "Phase3整套35道SQL实际报告") + "；" + link(SQL22_RUN + "/report.json", "Phase4仅sql-22真实补测") + "；" + link(SQL22_RUN + "/sql-22.json", "原gold、实际输出及日期上下文") + "；" + link("eval/artifacts/oct12/repairs-live-001/report.json", "前两处修复真实补测") + "；" + link("eval/artifacts/oct12/repairs-live-001/original-midnight-sql-readonly.json", "原失败SQL只读核验") + "。Phase3对应snapshot003，Phase4对应snapshot004，既有原始报告与失败记录保留。", "",
        "RAG未核实分支的真实证据来自Phase2 " + link("eval/artifacts/oct12/ui-live/run-003/rag-03-raw.json", "rag-03原始回答") + " 与 " + link("eval/artifacts/oct12/ui-live/run-003/rag-03.png", "警告截图") + "：两次数字核验失败后仍返回回答，语义未核实。Phase3 run004该题首答已取到E6和E1上下文，机械核验passed，语义仍pending_human_review；这两种结果分别记录，不把引用中出现数字称为整句已证实。", ""]
    for i,title,impl,files,ev,actual,pending in specs:
        lines += [f"### {i} {title}", "", "**要求及实现：**" + impl, "", "**改动文件：**" + "、".join(link(f) for f in files), "",
                  "**测试方法与证据：**" + "、".join(link(f) for f in ev), "", "**实际结果：**" + actual, "", "**未完成事项、审核与限制：**" + pending, ""]
    r = review["summary"]
    lines += ["## 人工审核的使用方法", "", f"统一入口目前有 **{r['pending_rows']} 行、{r['pending_review_objects']} 个独立审核对象、{r['actual_output_versions']} 个实际回答版本**，已授权{r['already_authorized_records']}记录另列。行数不是题数：包含68表+456列说明、别名、gold、每次系统回答和引用判定。", "",
              "1. 打开 " + link("eval/reports/oct12/manual-review/全部待人工审核统一入口.html", "全部待人工审核统一入口") + "，先按高优先组筛选两gold、sp03-19、专项题面/标签冲突，再看RAG引用和AW目录。",
              "2. 展开原题、标准SQL/结果、原始实际回答和证据；分别决定参考答案、系统回答和引用。清洗题面只删除给模型的操作指令，保留对象、期间、排序、单位及合法业务约束。",
              "3. 查看去重候选和清洗建议，填写保留/删重复、正确标签及理由；同一题但不同续问不按字面相同删除。对各个实际回答版本分别判断，不替旧运行追填。",
              "4. 点击导出审核决定JSON。导出不自动应用；确认决定后再由新版本应用题面/gold/标签并重跑受影响开发题。A/B签名和日期留给真实人工确认。", "",
              "两gold建议全文：" + link("notes/oct12/gold-38-23-proposal.md") + "；推荐sql-38只排名大小已知记录，robust-23明确库里所有曲目的平均毫秒时长。两者当前值虽与历史相同，NULL和指代语义仍须人确认。", "",
              "## 失败记录、证据保护与复现", "",
              "保留集本轮预测0；D2的33条和D3的18条阶段记录仍隔离，不提前正式评测。审核代理早期检索曾触及一份D1混合源的局部保留内容，立即停止，未传给开发代理、未形成审核/预测/调参。具体边界见 " + link("eval/reports/oct12/manual-review/保留集隔离边界.json") + "。审核包仅提供安全DEV证据或内嵌DEV摘录，不把混合集以附件展开。", "",
              "模块首轮数据库未启动失败、后续三项断言失败、真实JOIN员工匹配错、网络失败、旧RAG机械核验失败与截图采集时序问题，都保留在各新目录；修复后复跑使用新目录。不能把模块数量、调用成功、检索命中或同一最高客户称为整体业务正确。", "",
              "实际命令和退出码：" + link("eval/artifacts/oct12/commands/commands.jsonl") + "；最终Phase4模块 " + link(FINAL_MODULE + "/command.json") + " 与 " + link(FINAL_MODULE + "/pytest.stdout.txt") + "。日期修复独立探针 " + link("notes/oct12/staging/sql22/ai-review-v5-pass-2.md") + "、" + link("notes/oct12/staging/sql22/ai-review-v5-pass-2-probes.json") + "；早期候选误吞普通条件的失败保留。服务启动日志观察进程曾因继承管道未结束，停止的是该观察进程而非API/UI；另取独立源码快照，健康检查实际正常，未伪写启动命令退出0。", "",
              "```powershell", ".\\.venv\\Scripts\\python.exe -B scripts/run_d3_shared_regression.py --output eval/artifacts/oct12/full-module-new", ".\\.venv\\Scripts\\python.exe -B -m eval.run_eval --suite nl2sql --dataset eval/datasets/oct12/chinook_join_dev_v1.jsonl --split dev --draft-gold --run-id oct12-join-new --output eval/artifacts/oct12/join-new --timeout 240", ".\\.venv\\Scripts\\python.exe -B scripts/run_oct12_dev_regression.py --output eval/artifacts/oct12/d2-dev-new", "```", "",
              "复现需自配.env、模型与索引；附件不给真实密钥或数据库密码。已有本机数据库不重复建库/导入。ZIP需整体解压后打开HTML，保持目录结构；统一审核入口和验收报告使用相对证据路径。"]
    content = "\n".join(lines) + "\n"
    name = "10月12日任务逐项验收与证据"
    (OUT / (name + ".md")).write_text(content, encoding="utf-8")
    from markdown_it import MarkdownIt
    html = MarkdownIt("commonmark").enable("table").render(content)
    (OUT / (name + ".html")).write_text("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>" + escape(name) + "</title><style>body{font-family:Microsoft YaHei,Arial,sans-serif;max-width:1080px;margin:32px auto;padding:0 22px;line-height:1.8;color:#202c39}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #c7d2dd;padding:10px;vertical-align:top}th{background:#ecf2f7}a{color:#1768a7;overflow-wrap:anywhere}pre{background:#f1f4f6;padding:14px;overflow:auto}h2{border-bottom:2px solid #306c8c;padding-bottom:6px}h3{margin-top:34px}@media print{body{max-width:none;margin:0}h3{break-after:avoid}pre{white-space:pre-wrap}}</style><body>" + html + "</body></html>", encoding="utf-8")
    (OUT / (name + ".json")).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"module": tests[1], "join": joins["correct"], "latest_targets": summary["latest_target_matched"], "review_rows": r["pending_rows"]}))


if __name__ == "__main__":
    main()
