"""Render a separately authored AI review from fully read original V0 records.

The decisions below are review judgments, never new scorer labels or predictions.
Only files under this reports directory are written.
"""
import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / "eval/experiments/after_d2_01_03"
REPORTS = EXP / "reports"
facts = json.loads((REPORTS / "v0-task03-evidence-read.json").read_text(encoding="utf-8"))
PASS, COND, ERROR = "AI建议通过", "AI建议有条件通过", "AI发现错误"

# id, reference judgment/reason, actual judgment/reason, attribution,
# human decision still needed; no A/B signature or approval date.
DECISIONS = [
 (1,PASS,"2020年、发票SUM(total)、无记录保留NULL均明确；存档gold为NULL。",PASS,"实际半开2020期间SUM返回NULL，说明没有可汇总的值，没有变为0。别名、字符串日期与DATE常量不改变此timestamp列的边界含义。",["semantic_equivalent_ast"],"确认NULL展示措辞即可。"),
 (2,PASS,"reside明确customer.country=France，客户COUNT正确，存档5。",PASS,"实际customer.country=France COUNT(*)=5，L0直接执行，没有账单国家替代。",[],"无新增口径事项。"),
 (3,ERROR,"题目仅‘巴西销售额’，未给客户所在地/账单国；固定L0和唯一customer.country gold缺业务依据。gold在明确客户归属条件下计算本身正确，不能据当前两国字段相等证明唯一。",COND,"实际仅问region_scope，保留2024/2023且没有SQL；这是有依据的业务澄清。controller无合法地区补充，无法完成；不能按唯一gold确定系统金额错误。",["new_reference_scope_dispute","legitimate_clarification","controller_unanswered"],"明确这类国家销售额是否必须问归属；既有材料没有国家默认。独立单案例报告保留。"),
 (4,COND,"曲目明细金额、2023、Top10登记默认与gold匹配；L1默认实际是条数，输入已经明确销售额。‘最高的’是否接受默认10及开关应对应条数，需要明确，不能因L1强行把显式销售额当缺失指标。",ERROR,"SQL/核心10个track_id与1.99逐项符合gold，多加track_name合理；自动列数fail不是金额错误。但metadata.clarify.switch=null，没有该L1默认的可切换控件；本轮没有真正点击开关。",["projection_count_scoring_limitation","l1_control_missing"],"确认TopN默认的切换交互和该题自然语言条数含义；不改原评分。"),
 (5,COND,"2007明确且无数据应空结果；登记热门数量默认支持L1。旧两遍争议导致原scorable=false，仍保留；空结果不意味着应该补最近年份。",ERROR,"EMPTY_RESULT及默认声明正确、Jazz和2007均保留，开关可用性有元数据；SQL并列键实际track.name，而已确认规则是track_id。空数据掩盖该排序差异；未实际点击开关。",["existing_exclusion","tie_breaker_loss"],"保留原待确认；确认当前空年是否仍作为有效题，稳定ID排序不能靠空结果认定通过。"),
 (6,COND,"销售额与同比已明确，只缺当前期间；gold在补2024后合理。离线回答含current与base，与逐key控制器及重复time标志卡粒度失配；旧排除仍保留。",COND,"初次L2缺期间正确，附加time_ambiguous及current两条近重复；controller在发送前因bundled拒绝，实际只有初始请求，无最终SQL。不能将未发送的补充写成系统实测失败回答。",["existing_exclusion","controller_card_granularity_mismatch","controller_unanswered"],"确认一次补充同一时间条件是否可以包含明示基期；冻结controller本轮不动。"),
 (7,PASS,"‘账单国是美国’明确billing_country；分母仍缺，应问分母。补全库2024后gold FILTER分子/同期间全库分母正确。",ERROR,"实际问region_scope而未问denominator。原provider正确billing scope却程序explicit_region_scope不识别‘账单国’，覆盖为歧义；provider还先猜全部发票分母，虽然程序后续清掉。controller没有地区补充而止步，未执行。",["program_region_synonym_coverage","model_unsupported_denominator","controller_unanswered"],"保留分子/分母区分；不能通过取消所有地区澄清规避短语覆盖问题。"),
 (8,COND,"L2缺对象正确；客户/花钱补充后发票金额、2023、Top1 gold正确。补充同含object与metric，当前卡两项均问，单key控制器却拒绝整条；这是离线控制器适配争议。",COND,"初次实际L2问metric和rank_object；没有凭‘谁’强选客户，符合无全局默认。controller把另一当前卡字段称unasked并拒绝，未向系统提交任何补充；最终正确性未运行。",["controller_card_granularity_mismatch","controller_unanswered"],"确认控制器只准一个issue还是允许一次回答卡内多个问题；原版本标签/score不动。"),
 (9,PASS,"摇滚两候选关系非自动绑定；用户选择Rock后2024销售数量SUM(quantity) gold164正确。",PASS,"初始保留Rock/Rock And Roll两候选L2；实际稳定choice_id选择Rock后SQL关联genre且2024半开日期，数量164。DATE/字符串AST区别不改变语义。",["semantic_equivalent_ast"],"无新增业务事项；此题是实际按钮闭环，不能与自由补充混称。"),
 (10,ERROR,"‘2024年巴西客户数’未明确在2024购买的活跃客户、年末存量或新增客户；customer表无创建日期。gold擅加年度购买活动定义，不能从复购规则推广一般客户数。旧排除保留。",ERROR,"实际只COUNT全部Brazil客户=5，SQL完全不使用2024，intent却显示2024；未经解释就忽略显式日期。正确值究竟5/4不能确定，应先澄清日期含义，不能把gold活跃客户4强作唯一。",["existing_exclusion","unsupported_reference_population","explicit_condition_loss"],"优先确认客户数的时间语义；不增全局活跃客户默认。"),
 (11,PASS,"reside USA明确客户所在地，COUNT客户gold13正确。",PASS,"实际country=USA COUNT13，直接L0，与字段含义一致。",[],"无新增业务事项。"),
 (12,PASS,"明确问客户，Italy客户所在地COUNT1，未问金额或账单。",PASS,"意大利唯一在客户字段链接Italy，COUNT1，L0符合业务。",[],"无新增业务事项。"),
 (13,ERROR,"invoice revenue确定金额粒度但‘for Canada’未明确地理归属；唯一billing_country和L0缺已登记依据。该gold在明确账单国后正确，不能由快照同值证明题意唯一。",COND,"程序要求region_scope澄清有业务依据且没有SQL；即使模型先选billing，不能据模型选择反过来批准默认。controller没有region补充，最终未运行。",["new_reference_scope_dispute","legitimate_clarification","controller_unanswered"],"与03统一确认国家金额口径，不因英语invoice上下文自行安装默认。"),
 (14,PASS,"两年逐年SUM invoice.total，2022至2024半开范围、year排序gold481.45/469.58正确。",PASS,"实际两行2022=481.45、2023=469.58，逐年SUM；EXTRACT numeric年份与gold cast int、自动上限200不会截断两年结果。AST差别需独立语义判断，已读全部原SQL。",["semantic_equivalent_ast"],"可确认年份展示类型；不改scorer或gold类型。"),
 (15,ERROR,"热门购买数量使用登记默认应L1，标签L0与business_basis‘默认使L0’错误，原source guard已指出并排除；SQL数量/2009–2010/Top1自身正确。",PASS,"实际声明购买数量默认、L1执行，范围2009至2011、track_id稳定排序LIMIT1，真实空结果；没有最近年补填。",["existing_exclusion","existing_reference_level_error"],"原分类争议待人工，继续保持原排除，不新计成绩。"),
 (16,PASS,"Jazz明确流派，曲目COUNT JOIN genre正确，gold130。",PASS,"实际genre.name=Jazz、track JOIN genre COUNT130，L0；没有按购买张数代替曲目目录数。",[],"无新增业务事项。"),
 (17,PASS,"明确期间至少两张发票，按客户GROUP HAVING COUNT>=2，再外COUNT；无符合客户输出0，gold符合已确认复购定义。",PASS,"实际2020半开范围、每客户至少2张、外COUNT0，与SUM NULL行为不同且保持正确。AST别名/日期常量差别无业务改动。",["semantic_equivalent_ast"],"无新增业务事项。"),
 (18,PASS,"2021到2022两年范围、数量默认和Top10默认、track_id排序，gold包含两年正确。",ERROR,"原semantic provider明确2021-01-01至2023-01-01，程序explicit_period只匹配带‘年’的2022，覆盖为仅2022；实际SQL和结果只2022，是真实期间丢失。额外name列不应掩盖这项错误。开关只证明可用性，未点击。",["program_calendar_override_loss","explicit_condition_loss","projection_count_scoring_limitation"],"日期解析改动需后续另立代码任务，不能让prompt输出绕过程序覆盖。"),
 (19,PASS,"对象客户明确，已确认金额默认、2022按customer_id合计取金额最高一位，gold45/32.75正确。",ERROR,"实际查询核心及winner45/32.75正确、额外姓名/company不会改变客户粒度；原列数fail不能当金额错。但登记L1金额默认只有声明，switch=null，未提供替代口径控件，实际切换未运行。",["projection_count_scoring_limitation","l1_control_missing"],"确认客户金额默认可切换的备选指标是否登记；不能凭空加新业务默认。"),
 (20,ERROR,"输入明确2023、艺术家、销售额、前10名，没有待应用的登记默认；L1标签不成立，原source guard已排除。gold金额/排序自身正确。",PASS,"实际L0无默认声明且正确取10位艺术家；name附加列合理，明细金额不重复SUM发票头。原排除仍保留。",["existing_exclusion","existing_reference_level_error"],"保留分类人审，不按运行结果将scorable改true。"),
 (21,ERROR,"L2缺年份正确但参考声称仅缺期间、默认customer.country德国缺依据；controller只有time补充，没有合法地区补充，最终唯一客户归属gold条件不完整。",COND,"实际问期间和地区合理，未填最近年或国家字段；controller还因time_ambiguous/current重复字段bundling停止。既未发送年份也未执行SQL，不能断言补年份后会自动正确。",["new_reference_scope_dispute","controller_card_granularity_mismatch","controller_unanswered"],"确认地区归属并补合法controller来源后需统一新标签评测；本轮不更改。"),
 (22,PASS,"法国居住客户明确分子；分母补2024所有发票后应全库分母，gold0.0767700458609930正确且防零。",ERROR,"初次L2问denominator正确，patch set分母正确。首个SQL CASE France分子/全库分母正确；绑定守卫要求全局WHERE France，repair实际加入c.country=France，结果100.00，分母被错误缩为France。不是百分数/小数显示差异。",["program_ratio_local_vs_global_binding","repair_introduced_semantic_error"],"优先处理比例范围模型与SQL绑定校验职责；不能为通过关闭其它问题全局筛选守卫。"),
 (23,COND,"与08重复初始输入，原scorable=false保留；客户2023金额及改2024目标合理，但重复题不能重新纳入分母。",ERROR,"选择客户后的2023 winner46/32.75查询核心正确；‘改看2024年’不匹配followup路由，转fresh lookup，全库2024总额477.53/83张，丢客户排名对象及金额默认。额外姓名投影不是真实错误来源。",["existing_exclusion","program_followup_routing_loss","known_field_loss"],"后续路由代码任务应覆盖合法改动表达；本轮prompt-only不伪装修复。"),
 (24,PASS,"国家金额未明归属先L2，用户选customer.country后SUM total/2022/Australia，再改billing_country保值，gold均正确。",PASS,"真实choice客户归属→0.99，随后真实普通用户改账单归属→0.99；两段实际SQL来源字段分别c.country和billing_country正确且2022未丢。通过依据是字段与范围，不是金额碰巧相等。",["semantic_equivalent_ast"],"无新增业务事项；这是实际国家归属迁移闭环。"),
 (25,ERROR,"两个允许补充分别指Rock和Rock And Roll，但唯一final gold=Rock，原source guard已指出冲突并排除。value补充还缺column，不能从candidate label强猜字段。",COND,"实际保留两候选正确；controller因离线value/column不能唯一匹配停止，没有用户选择及最终SQL。未测的金额与购买数量切换不补写实测。",["existing_exclusion","existing_controller_target_conflict","controller_unanswered"],"先统一允许补充与目标来源，未来统一新版标签重评；本轮保持原排除。"),
 (26,PASS,"同比缺metric/current先L2；补发票金额/2024后计算2024对2023，改2025再换AVG时应保留增长任务及2025/2024，gold正确。",ERROR,"metric/年份真实两次补充后增长0.016930正确，多输出469.58/477.53被列数规则误判；改2025增长-0.056436也正确。最后‘指标换成…’转fresh extractor，user上下文没有旧intent，time/comparison丢失并执行全库AVG5.65194，是真实路由错误。",["projection_count_scoring_limitation","program_followup_routing_loss","known_field_loss"],"代码路由不能由patch prompt补偿；保留前面实际正确子轮与最终真实失败，不混成全程通过。"),
 (27,PASS,"2023比例缺分子/分母，补客户所在地Brazil分子和全库同年分母后的CASE gold正确；后续修改应分别保持局部范围。",ERROR,"真实补充只答numerator，provider却仅set region_scope+addfilters且不setnumerator，并用field/op错误键；程序地区证据守卫拦下FAILED。没有执行denominator补充或两条post，不能写后续实测。",["prompt_patch_field_responsibility_error","unexecuted_dependent_turns"],"建议仅patch prompt界定局部分子/分母string及global条件边界；正确patch之后能否生成合规比例SQL仍需真实验证。"),
 (28,COND,"初始‘金属乐队’Metallica候选需用户确认，gold明细2022正确；business_basis含‘Metal与Metallic在artist与genre均有候选’不符合当前别名表，需更正依据。L2实际应为候选确认，不必凭band字眼强造genre初始歧义。",ERROR,"候选按钮Metallica后22.77正确；用户明确‘改成流派Metal’，provider正确remove旧artist/add真实Metal，程序却只认取消词，不接受对象替换语义，FAILED，后一2023/Germany步骤未执行。不能保留旧artist交集假称完成。",["reference_basis_dispute","program_entity_replacement_guard_limit","unexecuted_dependent_turns"],"确认替换对象是否应撤销原对象过滤，程序应做可证明且只删目标的迁移；本轮prompt-only不放宽guard。"),
 (29,PASS,"热门10首缺期间先L2，数量登记默认；补2023、改2024、改明细销售额，三段gold语义正确。",PASS,"实际三个已执行SQL逐项保持正确期间、对象、Top10、track_id排序，最后只换metric，旧默认声明清掉；结果核心ID/指标与参考相符。均多track_name导致原列数判fail，是展示投影差异；只测自由补充修改，未点击L1口径开关。",["projection_count_scoring_limitation","semantic_equivalent_ast"],"确认评分输出契约是否允许解释性附加列；不要因此修改参考业务答案。"),
 (30,COND,"L2缺对象/时期成立，补金额/客户/2023后的发票聚合正确；参考隐藏goal固定Top1，但实际补充没明确条数，而登记缺TopN默认10。‘谁最多’是否语义自带Top1或按默认10，是参考与规则边界待人审，不能把期望写入prompt强制。",COND,"实际三次补充保留metric/customer/year，改2024、改track数量也保留未改条件，Top10延续登记默认。与Top1 gold不同是真实条数差异，不能仅加展示列解释；直到人审确定‘谁’条数口径，不能确定完整语义通过。",["reference_topn_dispute","real_output_cardinality_difference"],"优先确定最高一位与Top10默认的适用范围；本轮不强制Top1，不改49分母。"),
]

by_id = {f"sp03-{n:02d}": (rv,rr,sv,sr,tags,human) for n,rv,rr,sv,sr,tags,human in DECISIONS}
rows = []
for c in facts["cases"]:
    rv,rr,sv,sr,tags,human = by_id[c["id"]]
    refs = list(c["evidence"])
    for ref in refs:
        path = ref["path"]
        if path.endswith("response.raw.json"):
            ref.setdefault("location", "body JSON: status/sql/table/intent/clarification/metadata/steps")
        elif "provider-captures" in path:
            ref.setdefault("location", "request.messages and response.choices[0].message.content; actual trace_id")
        elif path.endswith("checkpoint.json"):
            ref.setdefault("location", "turns[] and controller_events[]; cross-checked against original response.raw.json")
        elif path.endswith("-scores.json"):
            ref.setdefault("location", f"cases[id={c['id']}]; unchanged original automatic judgment")
    rows.append({"id":c["id"],"group":"专项03合成开发题","original_category":c["reference"]["category"],"original_scorable":c["reference"]["scorable"],"input":c["reference"]["input"],"reference_review":{"verdict":rv,"reason":rr,"gold_sql_logic":"See case-specific review; stored gold was read, not rerun in this audit","gold_stored_result":c["reference"]["gold_result"],"fresh_sql_executions":0},"actual_system_review":{"verdict":sv,"reason":sr,"actual_outcome":c["outcome"],"turn_count":len(c["turns"]),"initial_level":c["automatic_score"]["observed_initial_level"],"actual_executed_sql_turns":[t["index"] for t in c["turns"] if t["sql"]],"unexecuted_expected_post_turns":max(0,len((c["reference"].get("controller") or {}).get("post_completion_turns") or [])-sum(t["phase"]=="post_completion" for t in c["turns"]))},"controller_review":{"actual_events":c["controller_events"],"no_hidden_goal_sent":True},"attribution_tags":tags,"original_automatic_score":{"automatic_complete":c["automatic_score"].get("automatic_complete"),"semantic_review_status":c["automatic_score"].get("semantic_review_status"),"query_result_reason":((c["automatic_score"].get("query") or {}).get("result") or {}).get("reason"),"l1_switch_availability_only":c["automatic_score"].get("l1_default_switch_behavior")},"human_review_status":"pending_human_review","remaining_human_decision":human,"evidence":refs})

common_paths = ["data/catalog/chinook.yaml","data/aliases/aliases-d2-reviewed.csv","data/rules/metric_definitions.json","eval/experiments/after_d2_01_03/materials/generation_materials.json","eval/experiments/after_d2_01_03/materials/readonly_live_facts.json","eval/experiments/after_d2_01_03/materials/source_manifest.json","eval/experiments/after_d2_01_03/runtime_eval/V0-freeze.json","eval/experiments/after_d2_01_03/runtime_eval/V0-code-snapshot.json","eval/experiments/after_d2_01_03/reports/scoring-protocol-draft.md","qa_agent/clarify/extractor.py","qa_agent/clarify/rules.py","qa_agent/clarify/service.py","qa_agent/sql/validator.py","eval/experiments/after_d2_01_03/runtime_eval/controller.py","eval/experiments/after_d2_01_03/runtime_eval/scorer.py"]
common = []
for name in common_paths:
    raw=(ROOT/name).read_bytes()
    # Read full UTF8 material rather than an existence check or UI title.
    raw.decode("utf-8")
    common.append({"path":name,"sha256":hashlib.sha256(raw).hexdigest(),"status":"read","note":"Current shared code is checked against V0 snapshot for implicated .py files; V0 provider system messages supply frozen prompt evidence."})
aliases=list(csv.DictReader((ROOT/"data/aliases/aliases-d2-reviewed.csv").open(encoding="utf-8-sig",newline="")))
alias_context=[x for x in aliases if (x.get("alias") or x.get("surface")) in {"摇滚","金属","金属乐队","Metallic","爵士","巴西","意大利"}]

label_now=hashlib.sha256((EXP/"data/cases-v6-reviewed.jsonl").read_bytes()).hexdigest()
score_now=hashlib.sha256((EXP/"runtime_eval/runs/V0-001-scores.json").read_bytes()).hexdigest()
assert label_now == facts["labels_sha256"] and score_now == facts["score_sha256"]
summary={"cases_read":30,"original_scorable":sum(x["original_scorable"] for x in rows),"original_excluded":sum(not x["original_scorable"] for x in rows),"original_raw_turns_read":sum(len(c["turns"]) for c in facts["cases"]),"original_provider_records_read":sum(len(t["providers"]) for c in facts["cases"] for t in c["turns"]),"raw_checkpoint_mismatches":0,"reference_verdicts":dict(Counter(x["reference_review"]["verdict"] for x in rows)),"actual_system_verdicts":dict(Counter(x["actual_system_review"]["verdict"] for x in rows)),"clear_original_evidence_cases":30,"missing_original_response_or_provider_cases":0,"new_api_requests":0,"new_database_queries":0,"original_task03_automatic_result":"4/23","original_all_automatic_result":"18/49 (18 pass, 22 fail, 9 AI_pending)","this_report_is_not_recalculated_score":True,"controller_outcomes":dict(Counter(x["actual_system_review"]["actual_outcome"] for x in rows))}
new_disputes=[{"ids":["sp03-03","sp03-13","sp03-21"],"finding":"国家金额地理归属没有默认依据，参考唯一范围/controller覆盖不足","action":"单列人审，不改本轮类别、SQL、控制器或分母"},{"ids":["sp03-28"],"finding":"alias业务依据表述与当前表不一致；候选确认合理但不是必须artiste/genre二选一","action":"人工核对依据文本；不以该争议消除真实remove guard失败"},{"ids":["sp03-30"],"finding":"隐藏目标Top1与已登记缺TopN默认10/用户语言边界待确认","action":"不往prompt强装Top1、不静默改评分"},{"ids":["sp03-06","sp03-08","sp03-21"],"finding":"逐key控制器拒绝另一个同卡字段/同一时间域补充；‘unasked’措辞与卡实际issues不同","action":"单独协议/数据适配争议，保持本轮controller冻结"}]
prompt_candidates=[{"priority":1,"runtime_prompt":"qa_agent/clarify/prompts/intent_patch.txt","supported_by":["sp03-27"],"judgment":"AI建议有条件通过","change_boundary":"卡片实际问numerator/denominator时，把本次确实答到的对应内容set为SemanticIntent str；局部对象/国别不提升全局region_scope/filters，不猜另一缺项。filters保留column/operator/value协议。原文evidence必须连续来自本次消息。","not_claimed":"不保证后续SQL/guard支持所有局部比例；不改规则、别名、国家默认、模型、标签或scorer。","validation":"由root做同一冻结60题完整V1；本审计零API，不对单题反复probe。"},{"priority":2,"runtime_prompt":"qa_agent/clarify/prompts/intent_extract.txt","supported_by":["sp03-07"],"judgment":"后续候选，本轮V1不实施","change_boundary":"提醒未给分母不得填全库；本轮provider已猜全部发票分母但程序清除。","not_claimed":"explicit_region_scope漏‘账单国’是程序问题，不能由该prompt修复。"}]
not_prompt_fixes=[{"ids":["sp03-07"],"reason":"明确地区短语被程序覆盖，patch模型未获调用"},{"ids":["sp03-18"],"reason":"semantic model给正确两年范围，calendar override覆盖错"},{"ids":["sp03-22"],"reason":"首SQL正确，guard/repair强加全球WHERE破坏分母"},{"ids":["sp03-23","sp03-26"],"reason":"合法修改未路由patch，旧intent未送模型；prompt没有真实旧条件可凭空恢复"},{"ids":["sp03-28"],"reason":"可证明对象替换被remove词白名单拒绝，保留旧artist以绕过不是修复"},{"ids":["sp03-04","sp03-19"],"reason":"L1控件/已登记备选项缺失是接口/规则职责，不靠模型捏造审核通过的新备选口径"},{"ids":["sp03-04","sp03-19","sp03-26","sp03-29"],"reason":"显示投影列数误判是固定评分契约限制，本轮不改scorer也不削用户可读信息迎合测试"}]
report={"report_kind":"独立逐项AI语义预审，非人工批准、非新EX成绩","created_at_utc":datetime.now(timezone.utc).isoformat(),"version_reviewed":"V0-001","scope":"30道专项03合成开发题；不读任何保留题","summary":summary,"immutable_proof":{"labels_sha256_before":facts["labels_sha256"],"labels_sha256_after":label_now,"score_sha256_before":facts["score_sha256"],"score_sha256_after":score_now,"business_mutations_by_this_auditor":0,"prompt_mutations_by_this_auditor":0,"label_mutations":0,"scorer_mutations":0,"human_record_mutations":0},"materials_read":common,"alias_rows_relevant_to_review":alias_context,"new_reference_or_protocol_disputes":new_disputes,"prompt_only_candidates":prompt_candidates,"must_not_disguise_as_prompt_fixes":not_prompt_fixes,"cases":rows,"limitations":["本轮完全只读原证据，不调用数据库；gold_result是此前只读实跑存档，本轮没有重新执行SQL。","本审计核对了schema键/FK/类型及已有结果，不宣称独立实时数据库结果核验。","V0原provider capture全部直接读到；archiver capture_path_rejected不代表原provider缺失，不能只看归档数量宣布证据不足。","L1元数据证明选项可用性，不是实际按钮点击试验；本轮03只有09/24/26/29/30相应稳定候选/年份选择真实请求，没有单独L1按钮切换预测。","部分参考重新发现争议而原scorable已true：只在本报告单列，原49分母、原分数不变，不据该内容偷偷调标签。","所有结论仍是AI建议，A/B签名和人工确认日期未填写。"]}
json_path=REPORTS/"v0-task03-semantic-review.json"
json_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def link(path,label=None):
    target=os.path.relpath(ROOT/path, REPORTS).replace("\\","/")
    return f"[{label or path}]({target})"

md=["# V0 专项03逐项语义AI预审", "", "本报告只审核 V0-001 原始材料。30 道均为本轮合成开发题，其中原可评分 23 道、原排除 7 道；已实际读取 51 份响应原文及 69 份原始 provider 记录，全部响应与 checkpoint 一致。没有调用问答 API、没有新增数据库查询，也没有修改业务源码、prompt、规则、别名、题库、控制器、scorer 或人工记录。", "", "原自动分数保持 **专项03：4/23；全部：18/49（18通过、22失败、9 AI_pending）**。下方是分开审核参考与实际行为的 AI 判断，不能将这些判断当成重新算出的EX，也不能把原未评分题重新纳入。", "", "| 审核对象 | AI建议通过 | AI建议有条件通过 | AI发现错误 | 证据不足 |", "|---|---:|---:|---:|---:|"]
for name,key in [("参考答案、分类及控制器依据","reference_verdicts"),("系统已有真实行为","actual_system_verdicts")]:
    n=summary[key];md.append(f"| {name} | {n.get(PASS,0)} | {n.get(COND,0)} | {n.get(ERROR,0)} | 0 |")
md += ["", "证据齐全不等于所有最终问答已运行：控制器中止、API失败后的依赖步骤按实际未运行记录。每项的完整原始文件SHA、JSON位置、原评分和控制器事件见 "+link(json_path.relative_to(ROOT).as_posix(),"JSON明细")+"；可复查紧凑原始材料 "+link((REPORTS/"v0-task03-evidence-read.json").relative_to(ROOT).as_posix(),"已读证据摘录")+"。", "", "## 先处理的真实问题与证据边界", "", "- **22：比例分母被修复链缩成分子。** 首SQL已经正确使用France CASE分子和全库分母，守卫要求全局WHERE France后得到100.00，正确参考约7.677%。这是业务错误，不能当百分数格式问题。", "- **18：程序把两年变成一年。** provider抽取2021–2022正确，日期规则覆盖为仅2022。", "- **23、26：合法追问转成新任务。** ‘改看2024’及‘指标换成平均每张发票金额’未路由patch，丢掉旧对象/期间/增长任务。", "- **28：明确替换对象被取消词守卫拒绝。** 用户改成流派Metal，不能继续保留Metallica条件以凑通过。", "- **27：patch职责错位。** 只回答分子却修改全局国家和filters，不set numerator；这是本轮有直接依据的prompt-only候选。", "- **03、13、21：参考地区范围新争议。** 未明示客户/账单归属，标签却固定唯一范围；不能为标签通过撤掉有依据的澄清。", "- **04、19、26、29：原列数评分的限制。** 核心值或已正确子轮可能只是多出名称/基期列；但18的日期丢失、26的最终追问失败、30的Top1/Top10条数差别仍是真实独立问题。", "", "## 逐项结果", "", "| 原编号 | 原分类 / 评分状态 | 参考AI判断 | 实际行为AI判断 | 原V0结局 |", "|---|---|---|---|---|"]
for r in rows:md.append(f"| {r['id']} | {r['original_category']} / {'原可评分' if r['original_scorable'] else '原排除'} | {r['reference_review']['verdict']} | {r['actual_system_review']['verdict']} | {r['actual_system_review']['actual_outcome']} |")
for r in rows:
    md += ["",f"### {r['id']}","",f"原题：{r['input']}","",f"**参考：{r['reference_review']['verdict']}。** {r['reference_review']['reason']}","",f"**系统实际：{r['actual_system_review']['verdict']}。** {r['actual_system_review']['reason']}","",f"实际请求轮数 {r['actual_system_review']['turn_count']}；执行SQL轮号：{r['actual_system_review']['actual_executed_sql_turns'] or '未执行'}；未执行的计划后续追问数量：{r['actual_system_review']['unexecuted_expected_post_turns']}。", "", "证据："]
    for ref in r["evidence"]:
        if ref["path"].endswith("-scores.json") or ref["path"].endswith("provider-evidence.json") or ref["path"].endswith("request.json"):continue
        md.append(f"- {link(ref['path'])}；位置：{ref.get('location','整个原文件')}；SHA256 `{ref['sha256']}`。")
    md += ["",f"需人工确认：{r['remaining_human_decision']} 人工状态保持 `pending_human_review`。"]
md += ["", "## V1 prompt-only 二遍意见", "", "只建议本轮改 `intent_patch.txt` 的同一职责：先看 current_card 实际 issues.field，识别用户本次确实答到哪一项；比例分子、分母是字符串描述。用户只给分子时只set numerator，不把该局部国家提升全局 region_scope/filters、不补分母；反向亦然。filter字典保持column/operator/value协议，evidence必须来自本次原文。sp03-27实际provider支持这项建议。", "", "保持国家默认、规则、别名、模型、controller、标签和scorer不变，交由root完整固定60题V1验证。本报告没有做单题API probe；正确patch仍可能遇到原SQL比例守卫范围限制，不能预写通过。", "", "18、22、23、26、28的已证实问题是程序解析、路由、局部绑定/守卫限制；04/19是控件或登记备选职责。不要用prompt猜旧上下文、保留错误过滤或放宽业务口径掩盖。", "", "## 原始材料与限制", ""]
for p in common:md.append(f"- {link(p['path'])}：SHA256 `{p['sha256']}`。")
md += ["", *["- "+s for s in report["limitations"]], "", "标签SHA256前后相同：`"+label_now+"`；V0 score SHA256前后相同：`"+score_now+"`。未填A/B签名或人工确认日期。", ""]
(REPORTS/"v0-task03-semantic-review.md").write_text("\n".join(md),encoding="utf-8")
print(json.dumps({"outputs":[json_path.relative_to(ROOT).as_posix(),"eval/experiments/after_d2_01_03/reports/v0-task03-semantic-review.md"],"summary":summary},ensure_ascii=False))
