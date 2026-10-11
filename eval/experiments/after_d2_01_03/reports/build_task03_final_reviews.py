"""Render independently authored V1/V2 semantic reviews from fully read evidence.

Only review artifacts are written; no API, DB, business, label or scorer mutation.
"""
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXP = ROOT / 'eval/experiments/after_d2_01_03'
REPORTS = EXP / 'reports'
PASS, COND, ERROR = 'AI建议通过', 'AI建议有条件通过', 'AI发现错误'

# Every system reason below is independently authored after reading that version's
# raw response, controller event, and original provider request/response.
V1 = {
 1:(PASS,'L0真实执行2020半开期间SUM(total)=NULL；未替成0，回答按无可用记录处理。',['semantic_equivalent_ast']),
 2:(PASS,'reside France明确客户所在地；真实customer.country=France COUNT=5，L0直接执行。',[]),
 3:(COND,'实际L2只问地区归属，保留2024/2023、发票金额与同比；国家金额缺客户/账单归属，澄清有依据。controller没有合法region补充，最终SQL未运行；参考唯一归属仍不能确定。',['new_reference_scope_dispute','legitimate_clarification','controller_unanswered']),
 4:(ERROR,'真实Top10明细金额/2023/track_id稳定排序、核心结果符合gold；额外track_name是展示列。但L1仅TopN默认声明，switch=null，没有该默认的切换控件。本轮未实际点击L1开关，不能据评分列数fail称金额错误。',['projection_count_scoring_limitation','l1_control_missing']),
 5:(PASS,'实际L1、Jazz曲目数量、2007范围、Top10及track_id稳定并列键均保持，返回空；LOWER(genre.name)=jazz在当前目录Jazz对象下可定位对应流派，不按空结果单独证明逻辑。switch有元数据但未点击。原排除保留。',['existing_exclusion','semantic_equivalent_ast']),
 6:(COND,'初始L2缺期间正确，额外time_ambiguous/current两条同域问题；controller在提交前因bundled补充拒绝，只有初始请求。没有最终SQL，不能把V2的实际年份按钮与percent结果写到V1。',['existing_exclusion','controller_card_granularity_mismatch','controller_unanswered']),
 7:(ERROR,'provider已识别账单国家USA，程序仍覆盖为region歧义；实际先问地区和分母，真实补全球2024分母后仍反问地区。两轮均无SQL，不能写成V0只问地区或V2猜分母；题面已明确地区却重复追问是真实错误。',['program_region_synonym_coverage','unexecuted_final_answer']),
 8:(COND,'初始问metric和rank_object合理，不强选谁为客户。离线补充同时回答同卡两项，却被单key控制器称another unasked而拒绝；没有把补充发送系统，最终未运行。Top1/Top10属于后续参考边界，不改原评分。',['controller_card_granularity_mismatch','controller_unanswered']),
 9:(PASS,'初次摇滚两候选L2；真实稳定choice选择Rock后按2024明细数量求和164，字段与期间正确。SQL使用COALESCE，当前非空结果不受影响，不能据此安装所有SUM空集=0的默认。',['semantic_equivalent_ast']),
10:(ERROR,'实际customer.country=Brazil COUNT5完全不使用题面2024，而intent记录2024；真实期间语义被忽略。参考活跃客户4定义也未获一般客户数口径批准，不能强称5必错或4唯一，应先确认时间对应客户活动还是存量。',['existing_exclusion','unsupported_reference_population','explicit_condition_loss']),
11:(PASS,'真实reside USA→customer.country COUNT13、L0，未用账单国家。',[]),
12:(PASS,'真实Italy客户所在地COUNT1、L0，未引入金额或发票活动。',[]),
13:(COND,'真实L2问地区归属，保留2024/发票金额；invoice revenue限定金额粒度，不等于Canada已经选账单国家。controller无region来源，最终未运行；参考新争议单列。',['new_reference_scope_dispute','legitimate_clarification','controller_unanswered']),
14:(ERROR,'本轮value_adjudication原provider将“每年”判ambiguous，候选竟为USA/Italy等账单国；实际L2反问“每年具体哪个对象”，无SQL。题意已经明确两年逐年发票金额，这是真实值提取/候选裁决误澄清，不是合法地区口径歧义。',['false_clarification','spurious_value_mention']),
15:(ERROR,'真实数量默认L1和2009–2010期间正确，但provider没提取“哪首”为Top1，程序补Top10、SQL LIMIT10；实际空结果掩盖单数排名差异。原分类L0错误仍排除，不能把空结果等同完整题意通过；与最高/缺N默认边界交人工确认。',['existing_exclusion','real_sql_cardinality_difference_masked_by_empty_result']),
16:(PASS,'真实Jazz目录曲目COUNT130，track→genre关联和字段过滤正确。',[]),
17:(PASS,'真实2020期间每客户至少2发票HAVING，再外COUNT=0，符合已确认复购口径与COUNT空集行为。',['semantic_equivalent_ast']),
18:(ERROR,'本轮实际SQL覆盖2021–2022两年、数量/Top10/track_id排序正确，核心结果符合参考；但Intent.current仍被日期覆盖为仅2022。当前答案可正确，持久意图存在真实期间丢失，不能照抄V0实际SQL仅2022，也不能仅金额一致批准完整状态。',['program_calendar_override_loss','intent_sql_period_inconsistency','projection_count_scoring_limitation']),
19:(ERROR,'真实2022客户发票金额Top1=45/32.75正确，多姓名列不改变客户粒度；L1金额默认声明却switch=null，未提供切换控件。题目SQL正确和完整默认交互缺口分别记录。',['projection_count_scoring_limitation','l1_control_missing']),
20:(PASS,'实际L0、2023艺术家明细金额Top10及artist_id稳定并列排序正确，无默认待应用。原L1标签已排除仍保留，name附列不改变对象粒度。',['existing_exclusion','existing_reference_level_error']),
21:(COND,'实际问期间与地区有依据，未猜最近年；controller因time同域补充bundling停止，只有初始请求。参考只缺期间并指定customer德国缺依据，不能把未发送补充后的结果写成错误金额。',['new_reference_scope_dispute','controller_card_granularity_mismatch','controller_unanswered']),
22:(ERROR,'本轮P2漏掉题面明确“法国居住客户的销售额”的numerator，虽country绑定正确，却同时问num/den；真实补2024所有发票分母后仍反问分子，controller无多余num补充而止步。全轮无SQL；V0的错误100和V2的守卫拒绝都不能移植为本轮实测。',['model_explicit_numerator_omission','false_extra_clarification','unexecuted_final_answer']),
23:(ERROR,'初始选客户后2023客户金额winner46/32.75正确；随后真实“改看2024年”被路由成fresh lookup，执行2024全83张发票SELECT*，丢客户排名对象/指标。原重复题排除保留，未把V2全库汇总SQL说成V1。',['existing_exclusion','program_followup_routing_loss','known_field_loss']),
24:(PASS,'真实地区choice选客户归属后2022 Australia金额0.99；真实改账单归属后invoice.billing_country SQL仍保2022/Australia、0.99。通过依据是两段字段来源及范围，非同金额巧合。',['semantic_equivalent_ast']),
25:(COND,'真实摇滚两候选L2正确；controller离线value缺column且允许Rock/RockAndRoll与唯一gold冲突，不能唯一匹配而停止。没有选择、最终SQL或口径切换，原排除保留。',['existing_exclusion','existing_controller_target_conflict','controller_unanswered']),
26:(ERROR,'实际metric补丁+年份按钮后2024/2023增长fraction0.016930正确；改2025后当前450.58/基期477.53/-0.056436也正确，额外基期列只是投影差异。但“指标换成平均每张发票金额”真实fresh路由、执行全库AVG5.65194，丢2025/2024与growth，完整任务失败。',['program_followup_routing_loss','known_field_loss','projection_count_scoring_limitation']),
27:(ERROR,'V1真实P3只set numerator，未提升全局filter/region；补2023全库分母后真实CASE Brazil / SUM(all total) fraction0.0421653392执行正确，局部职责改善有证据。但后续“分子换成德国…”fresh路由、原2023和已确认全库分母丢失，再问分母；后续2024未执行，不能称整题完成或V1整体提分。',['prompt_patch_local_improvement','program_followup_routing_loss','known_field_loss','unexecuted_dependent_turns']),
28:(ERROR,'真实单候选Metallica确认后2022明细额22.77正确；“改成流派Metal”P3本轮set filters只保Metal，原防丢条件守卫要求明确remove而拒绝。旧artist撤销没有完成，后一2023/Germany未执行；与V0 remove词限制不同的实际补丁形状已分开记录。',['program_entity_replacement_guard_limit','unexecuted_dependent_turns']),
29:(PASS,'实际年份按钮2023→自由改2024→自由换明细销售额三段SQL均保track/Top10/期间/稳定排序，核心ID及金额数量符合gold；显式换metric后旧数量默认清除。附track_name导致原列数fail属于评分契约；未点击L1口径按钮。',['projection_count_scoring_limitation','semantic_equivalent_ast']),
30:(ERROR,'真实只补metric和客户后P3把rank_object保存为中文“客户”，未规范成customer，绕过rules中customer+invoice_revenue缺期间必问规则，尚未收到2023即执行全库Top10。随后改2024、换track数量确实保持已改条件；最初漏问期间是真实对象规范问题。Top1/Top10默认边界另需人工，不以隐藏2023强补输入。',['noncanonical_rank_object_bypasses_period_requirement','unasked_expected_period','reference_topn_dispute']),
}

V2 = {
 1:(PASS,'真实2020全年SUM(total)=NULL、L0；CAST DATE边界与timestamp列范围一致，未改0。',['semantic_equivalent_ast']),
 2:(PASS,'真实France客户所在地COUNT5、L0直接执行。',[]),
 3:(COND,'真实L2地区口径澄清保留2024/2023增长任务；controller无地区补充止步。国家销售额归属参考不足，不能把合法澄清视为模型凭空填条件。',['new_reference_scope_dispute','legitimate_clarification','controller_unanswered']),
 4:(COND,'本轮P2把“排名最高”解释Top1、L0，实际明细金额2023 winner2821/1.99正确；参考登记缺N应Top10/L1与最高单数理解存在边界，不只展示列数差异，人工需确定条数。没有L1默认或开关点击，本轮不能照抄V0 Top10。',['reference_topn_dispute','real_output_cardinality_difference']),
 5:(PASS,'真实L1 Jazz曲目数量/2007/Top10/track_id并列键均正确，空结果和switch元数据有原文；不以空结果掩盖V0曾用name排序，本轮实际已使用ID。原排除保留。',['existing_exclusion','semantic_equivalent_ast']),
 6:(PASS,'本轮初次只问current，真实year2024 choice成功，基期推导2023；SQL真实金额469.58/477.53及ROUND同比percent1.69正确。这是原排除题的一次真实新闭环，不自动纳评分；percent与gold fraction展示差别明示、不能据同列名错判。',['existing_exclusion','percentage_representation','semantic_equivalent_ast']),
 7:(ERROR,'本轮P2正确标billing USA但猜全库2024分母；程序仍把明确“账单国”覆盖为歧义，实际只问region而非denom，controller无地区补充停止、无SQL。正确国家澄清规则不能因本题短语覆盖失败整体取消。',['program_region_synonym_coverage','model_unsupported_denominator','unexecuted_final_answer']),
 8:(COND,'真实L2同时问metric/rank_object，controller离线答同卡两项被逐key拒绝。没有用户补充POST或最终SQL；不能以模型先猜customer后被程序清除当已合法选对象。',['controller_card_granularity_mismatch','controller_unanswered']),
 9:(PASS,'真实Rock稳定choice后2024 SUM(quantity)=164、流派与日期正确。',['semantic_equivalent_ast']),
10:(ERROR,'首provider擅选2024活跃客户定义，旧绑定守卫repair后真实SQL变全部Brazil客户COUNT5，完全丢2024。标准活跃客户4定义仍有争议；当前SQL忽略期间是真实问题，非V2新比例守卫作用类别。',['existing_exclusion','unsupported_reference_population','explicit_condition_loss']),
11:(PASS,'真实customer.country=USA COUNT13、L0。',[]),
12:(PASS,'真实customer.country=Italy COUNT1、L0。',[]),
13:(COND,'真实L2问Canada客户/账单归属，2024和发票金额保留；controller无补充，最终未运行。参考唯一billing口径缺依据仍单列。',['new_reference_scope_dispute','legitimate_clarification','controller_unanswered']),
14:(PASS,'本轮“每年”裁决unmatched，没有国家误绑定；实际2022/2023逐年SUM481.45/469.58、范围和排序正确。不能将V1的误澄清转写为V2结果。',['semantic_equivalent_ast']),
15:(PASS,'本轮P2明确Top1、真实数量默认L1，SQL2009–2010/track_id稳定排序LIMIT1，空结果正确。原L0错误标签仍排除，未实际点击L1开关。',['existing_exclusion','existing_reference_level_error']),
16:(PASS,'真实Jazz曲目目录COUNT130，track/genre关联正确。',[]),
17:(PASS,'真实2020期间至少两发票客户COUNT0，外COUNT与SUM空集区分正确。',['semantic_equivalent_ast']),
18:(ERROR,'本轮SQL及核心结果真实覆盖2021–2022两年、数量Top10正确；Intent.current仍被程序日期覆盖为2022，仅当前SQL偶然从原文恢复两年。真实持久状态错，不能称实际SQL缩短为一年，也不能据正确表结果宣布完整意图通过。',['program_calendar_override_loss','intent_sql_period_inconsistency','projection_count_scoring_limitation']),
19:(ERROR,'真实2022 customer金额winner45/32.75正确、姓名额外列合理；L1金额默认switch仍null，未有实际可切换控件，未点击。',['projection_count_scoring_limitation','l1_control_missing']),
20:(PASS,'真实L0艺术家2023明细金额Top10、artist_id并列排序正确；原错误L1标签排除不改变。',['existing_exclusion','existing_reference_level_error']),
21:(COND,'实际期间和国家归属L2有依据，controller time同域补充拒绝未发送。参考only time缺项及唯一德国客户归属不完整，最终SQL未运行。',['new_reference_scope_dispute','controller_card_granularity_mismatch','controller_unanswered']),
22:(ERROR,'真实P3补2024全库分母正确；随后3个provider SQL均为法国CASE分子/全库SUM分母，WHERE只有2024日期、无country，CASE零保护+ROUND((SUMCASE/SUMtotal)*100,2)数学正确。V2守卫仅接受(SUMCASE*100)/SUMtotal，三次误拒合法等价百分比，最终FAILED/table=null，没有执行结果；这是新增语法覆盖不足，不是分母错误或已改善EX。',['v2_guard_valid_equivalent_ast_rejection','unexecuted_generated_sql']),
23:(ERROR,'真实客户选择后2023 winner46/32.75正确；“改看2024”fresh路由后执行全库年度发票83/总额477.53，丢customer排名目标。原重复题排除保持。',['existing_exclusion','program_followup_routing_loss','known_field_loss']),
24:(PASS,'真实customer归属choice及随后billing归属修改均保2022/Australia，SQL来源字段正确；金额0.99相同不能替代字段证明。',['semantic_equivalent_ast']),
25:(COND,'真实Rock/RockAndRoll候选保留，controller value/column不唯一而止步；无选择、无SQL，原允许补充/唯一gold冲突排除保持。',['existing_exclusion','existing_controller_target_conflict','controller_unanswered']),
26:(ERROR,'本轮P2无原文依据标scope_missing=true，初始卡却问“这批/这些”范围，题面根本无指代。真实2024补充、发票金额补充后仍scope_missing，controller无合法补充停止，无SQL/后续year或metric修改。不是V1已执行后fresh路由bug的本轮复现。',['model_unsupported_reference_scope','false_extra_clarification','unexecuted_dependent_turns']),
27:(ERROR,'真实P3set numerator并额外set customer.country filters；当时value_link真实核验巴西→Brazil、补丁获接受。下一denom请求无巴西mention，过滤字典已丢evidence_ref，V2无法恢复之前中文已核验surface，三次误拒“无实际用户原文证据”。原用户明文和先前绑定确有证据；最终INNER JOIN CASE fraction数学正确，前两LEFT也能保全分母，但未执行/table=null。这是新增来源继承覆盖不足，不能说模型无分子或分母错。',['v2_guard_lost_verified_surface_provenance','unexecuted_generated_sql']),
28:(ERROR,'本轮真实Metallica确认后22.77正确；对象改Metal的P3 set filters丢oldartist，被原守卫要求explicit remove而拒绝。无后一2023/Germany运行；与V1同形状限制，非V2比例守卫修复范围。',['program_entity_replacement_guard_limit','unexecuted_dependent_turns']),
29:(PASS,'真实2023按钮、自由改2024、换明细额三段保track/Top10/期间/ID排序、旧默认被清；各核心结果符合gold。额外name列是原评分契约限制；L1开关元数据不是实际点击。',['projection_count_scoring_limitation','semantic_equivalent_ast']),
30:(ERROR,'本轮P3同样rank_object=中文客户，绕过canonical customer金额排名必问期间规则，只有metric/customer补充便执行全库Top10、未收到2023。后续2024/track数量修改实际保持未改条件；参考Top1争议另列，不把hidden2023送模型。',['noncanonical_rank_object_bypasses_period_requirement','unasked_expected_period','reference_topn_dispute']),
}

def read_ref(path, location):
    raw = (ROOT / path).read_bytes()
    raw.decode('utf-8')
    return {'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'location':location}

def build(version, decisions):
    suffix = version.lower()
    facts = json.loads((REPORTS / f'{suffix}-task03-evidence-read.json').read_text(encoding='utf-8'))
    assert facts['task03_count'] == 30 and facts['score_complete']
    previous = json.loads((REPORTS / 'v0-task03-semantic-review.json').read_text(encoding='utf-8'))
    ref_by_id = {r['id']:r for r in previous['cases']}
    labels_path = EXP / 'data/cases-v6-reviewed.jsonl'
    label_raw = labels_path.read_bytes()
    labels = {r['id']:r for r in map(json.loads,label_raw.decode('utf-8').splitlines())}
    score_path = EXP / f'runtime_eval/runs/{version}-001-scores.json'
    score_raw = score_path.read_bytes()
    score = json.loads(score_raw)
    assert hashlib.sha256(label_raw).hexdigest() == facts['labels_sha256']
    assert hashlib.sha256(score_raw).hexdigest() == facts['score_sha256']
    rows = []
    for c in facts['cases']:
        old_ref = ref_by_id[c['id']]
        label = labels[c['id']]
        # The exact same frozen label was reread. Reusing unchanged reference
        # rationale is explicit; actual system judgments are independent.
        rr = dict(old_ref['reference_review'])
        rr['revalidated_against_same_frozen_reference'] = True
        rr['gold_sql'] = label['gold_sql']
        rr['reference_intent'] = label.get('reference_intent')
        rr['missing_conditions'] = label.get('missing_conditions')
        rr['business_basis'] = label.get('business_basis')
        if c['id'] == 'sp03-30':
            rr['reason'] = '对象/时期澄清后2023客户发票金额SQL正确；ranking.required仅metric/object，但现有rules对canonical customer+invoice_revenue另要求期间。原hidden goal Top1并未出现在用户补充，登记缺TopN默认10与“谁最多”的条数语义需确认。不能把隐藏2023当已向系统发送；参考Top1边界保持有条件，不改原标签。'
        v, reason, tags = decisions[int(c['id'].split('-')[-1])]
        for ref in c['evidence']:
            ref.setdefault('location', 'request.messages/response.choices[0].message.content' if 'provider-captures' in ref['path'] else 'body JSON status/sql/table/intent/clarification/metadata/steps' if ref['path'].endswith('response.raw.json') else 'checkpoint.turns/controller_events' if ref['path'].endswith('checkpoint.json') else 'original JSON; case ID retained')
        executed = [t['index'] for t in c['turns'] if t['sql'] and t['status'] in {'SUCCEEDED','EMPTY_RESULT'} and t['table'] is not None]
        generated_unexecuted = [t['index'] for t in c['turns'] if t['sql'] and t['index'] not in executed]
        turns = [{'index':t['index'],'phase':t['phase'],'message':t['request']['request'].get('message'),'choice_id':t['request']['request'].get('choice_id'),'status':t['status'],'sql':t['sql'],'table':t['table'],'intent':t['intent'],'clarification':t['clarification'],'clarify_metadata':(t['metadata'] or {}).get('clarify'),'raw_matches_checkpoint':t['raw_matches_checkpoint']} for t in c['turns']]
        controller_reason = 'No controller supplement was issued.' if not c['controller_events'] else 'Actual events are preserved. A rejected offline supplement was not sent to the system; pending or dependent post turns are not predictions.'
        rows.append({'id':c['id'],'group':'专项03合成开发题','original_category':label['category'],'original_scorable':label['scorable'],'input':label['input'],'reference_review':rr,'actual_system_review':{'verdict':v,'reason':reason,'actual_outcome':c['outcome'],'turn_count':len(c['turns']),'initial_level':c['automatic_score']['observed_initial_level'],'actual_executed_sql_turns':executed,'generated_but_unexecuted_sql_turns':generated_unexecuted,'unexecuted_expected_post_turns':max(0,len((label.get('controller') or {}).get('post_completion_turns') or [])-sum(t['phase']=='post_completion' for t in c['turns']))},'controller_review':{'actual_events':c['controller_events'],'reason':controller_reason,'no_hidden_goal_sent':True},'attribution_tags':tags,'original_automatic_score':c['automatic_score'],'human_review_status':'pending_human_review','remaining_human_decision':old_ref['remaining_human_decision'] + (' 核对实体对象ID规范及由此漏问期间；不补写隐藏2023。' if c['id']=='sp03-30' else ''),'actual_turns':turns,'evidence':c['evidence']})
    common_names = ['data/catalog/chinook.yaml','data/aliases/aliases-d2-reviewed.csv','data/rules/metric_definitions.json','qa_agent/clarify/clarify_rules.yaml','eval/experiments/after_d2_01_03/materials/generation_materials.json','eval/experiments/after_d2_01_03/materials/readonly_live_facts.json',f'eval/experiments/after_d2_01_03/runtime_eval/{version}-freeze.json',f'eval/experiments/after_d2_01_03/runtime_eval/{version}-code-snapshot.json','eval/experiments/after_d2_01_03/reports/scoring-protocol-draft.md']
    if version == 'V2':
        common_names += ['eval/experiments/after_d2_01_03/runtime_eval/version-changes/V2/after/qa_agent/sql/ratio_guard.py','eval/experiments/after_d2_01_03/runtime_eval/version-changes/V2/after/qa_agent/sql/validator.py','eval/experiments/after_d2_01_03/runtime_eval/version-changes/V2/after/qa_agent/pipeline.py']
    common = [read_ref(p,'Full file read; version archive is used for V2 source after rollback, original provider supplies frozen runtime prompts.') for p in common_names]
    summary = {'cases_read':30,'original_scorable':sum(r['original_scorable'] for r in rows),'original_excluded':sum(not r['original_scorable'] for r in rows),'original_raw_turns_read':sum(len(c['turns']) for c in facts['cases']),'original_provider_records_read':sum(len(t['providers']) for c in facts['cases'] for t in c['turns']),'raw_checkpoint_mismatches':0,'reference_verdicts':dict(Counter(r['reference_review']['verdict'] for r in rows)),'actual_system_verdicts':dict(Counter(r['actual_system_review']['verdict'] for r in rows)),'clear_original_evidence_cases':30,'missing_original_response_or_provider_cases':sum(any(p.get('missing') for t in c['turns'] for p in t['providers']) for c in facts['cases']),'new_api_requests':0,'new_database_queries':0,'original_task03_automatic_result':score['summary']['groups']['task:03']['correct_over_scorable_tasks'],'original_all_automatic_result':score['summary']['groups']['all']['correct_over_scorable_tasks'],'original_all_automatic_counts':{k:score['summary']['groups']['all'][k] for k in ['confirmed_correct','automatic_failed','semantic_AI_pending']},'controller_outcomes':dict(Counter(r['actual_system_review']['actual_outcome'] for r in rows)),'this_report_is_not_recalculated_score':True}
    report = {'report_kind':'独立逐项AI语义预审；非人工批准、非重新计算EX','created_at_utc':datetime.now(timezone.utc).isoformat(),'version_reviewed':version+'-001','selection_role':'Final selected V1 snapshot' if version=='V1' else 'Rejected V2 trial archive; not Final runtime','scope':'30道专项03合成开发题；不读保留题；仅读本版本完整原始响应和provider','summary':summary,'immutable_proof':{'labels_sha256_before':facts['labels_sha256'],'labels_sha256_after':hashlib.sha256(labels_path.read_bytes()).hexdigest(),'score_sha256_before':facts['score_sha256'],'score_sha256_after':hashlib.sha256(score_path.read_bytes()).hexdigest(),'business_mutations_by_this_auditor':0,'prompt_mutations_by_this_auditor':0,'label_mutations':0,'scorer_mutations':0,'human_record_mutations':0},'materials_read':common,'new_reference_or_protocol_disputes':previous['new_reference_or_protocol_disputes'],'cases':rows,'limitations':['gold标准SQL和此前只读结果存档完整读取，本次0数据库查询，未宣称重新实跑标签。','原可评分23/排除7，全部固定49/60分母与原评分保留；AI分对象判断不能转换成新EX。','source当前已回退V1时，V2使用修改后字节档案和版本snapshot证据；不拿当前源码冒充旧运行。','L1 switch元数据仅为可用性证据；没有实际choice请求时不写完成口径按钮切换。','FAILED仍可能包含生成SQL字符串；只有实际SUCCEEDED/EMPTY_RESULT且有结果表才列入已执行SQL，误拒的SQL为未执行。','本审计者曾负责D3澄清代码及V2守卫，不能宣称角色盲审；父任务独立二遍与真实版本运行另外保存。','未填写A/B签字或人工确认日期，pending_human_review保持。']}
    if version=='V2':
        report['trial_rejection_evidence'] = [{'id':'sp03-22','finding':'Valid percent placement (SUMCASE/SUMtotal)*100 rejected by syntax-limited guard; all three SQLs retain all-invoice denominator; no execution.'},{'id':'sp03-27','finding':'Actual earlier Chinese customer-country text and value link exist; later canonical binding lost evidence_ref/surface provenance and was falsely rejected; no execution.'}]
    json_path = REPORTS / f'{suffix}-task03-semantic-review.json'
    json_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def link(path): return '['+path+']('+os.path.relpath(ROOT/path,REPORTS).replace('\\','/')+')'
    md = [f'# {version} 专项03逐项语义AI预审','',f"{report['selection_role']}。逐项重读30道原题、标准SQL和存档结果、{summary['original_raw_turns_read']}份原始响应及{summary['original_provider_records_read']}份原provider，本版本响应与checkpoint全部一致。没有新API或数据库调用，没有修改业务、prompt、标签、controller、scorer或人工记录。",'',f"原自动分数：专项03 **{summary['original_task03_automatic_result']}**，全部 **{summary['original_all_automatic_result']}**。分对象AI结论不是重新计算的EX，原49可评分/11待标签审核以及本组23可评分/7排除保持。",'', '| 对象 | AI建议通过 | AI建议有条件通过 | AI发现错误 | 证据不足 |','|---|---:|---:|---:|---:|']
    for name,key in [('参考答案、分类与控制器依据','reference_verdicts'),('本版本系统实际完整行为','actual_system_verdicts')]:
        n=summary[key];md.append(f"| {name} | {n.get(PASS,0)} | {n.get(COND,0)} | {n.get(ERROR,0)} | 0 |")
    md += ['',link(json_path.relative_to(ROOT).as_posix())+'包含原标准SQL、每轮实际SQL/表/意图/卡片、原评分、controller事件及所有证据SHA。','', '**V2试验边界：** 22合法等价百分比语法被拒绝、27此前真实中文绑定来源未继承；都没有执行结果，不能称分母算错或运行通过。V2已经不作为Final。' if version=='V2' else '**Final V1实际风险：** 14“每年”误当国家值；18SQL两年正确但持久意图仅2022；22漏已给分子而反问；23/26/27部分合法追问fresh路由丢旧条件；28实体替换未完成；30中文对象ID绕过必问期间。03/13/21地区标签依据与Top1/缺N默认边界单列待人工。','', '| 原编号 | 原分类/可评分 | 参考AI判断 | 实际系统AI判断 | 本版本结局 |','|---|---|---|---|---|']
    for r in rows:md.append(f"| {r['id']} | {r['original_category']} / {'可评分' if r['original_scorable'] else '原排除'} | {r['reference_review']['verdict']} | {r['actual_system_review']['verdict']} | {r['actual_system_review']['actual_outcome']} |")
    for r in rows:
        md += ['',f"## {r['id']}",'','原题：'+r['input'],'',f"**参考：{r['reference_review']['verdict']}。** {r['reference_review']['reason']}",'',f"**系统实际：{r['actual_system_review']['verdict']}。** {r['actual_system_review']['reason']}",'',f"真实请求 {r['actual_system_review']['turn_count']} 轮；已执行SQL轮号 {r['actual_system_review']['actual_executed_sql_turns'] or '无'}；生成未执行SQL轮号 {r['actual_system_review']['generated_but_unexecuted_sql_turns'] or '无'}；计划后续未执行 {r['actual_system_review']['unexecuted_expected_post_turns']} 轮。",'','证据：']
        for ref in r['evidence']:
            if ref['path'].endswith('checkpoint.json') or ref['path'].endswith('response.raw.json') or 'provider-captures' in ref['path']:
                md.append('- '+link(ref['path'])+'；'+ref['location']+'；SHA256 `'+ref['sha256']+'`。')
        md += ['','需人工确认：'+r['remaining_human_decision']+' 状态 `pending_human_review`。']
    md += ['','## 材料与限制','']
    md += ['- '+link(r['path'])+'；SHA256 `'+r['sha256']+'`。' for r in common]
    md += ['',*['- '+r for r in report['limitations']],'','原标签及该版本score SHA前后相同，证明记录见JSON。没有A/B签字或人工确认日期。','']
    (REPORTS/f'{suffix}-task03-semantic-review.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps({'version':version,'outputs':[str(json_path.relative_to(ROOT)),str((REPORTS/f'{suffix}-task03-semantic-review.md').relative_to(ROOT))],'summary':summary},ensure_ascii=False))

if __name__ == '__main__':
    build('V2', V2)
    build('V1', V1)
