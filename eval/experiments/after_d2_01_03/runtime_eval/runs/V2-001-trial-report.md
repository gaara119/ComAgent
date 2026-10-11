**V2-001 trial真实运行与三版本同冻结评分比较**

全60条V2真实run+内部score、离线classify完成，exit0、stderr空；预测已停止。root已决定回退V2的三个业务文件，最终选择V1，不进行V3。此报告保留V2正式冻结时的run snapshot、真实请求/响应/provider，不把当前恢复中的V1源码或服务冒称V2。80实际POST全部有响应，未重发无响应POST、未holdout预测，未修改runtimepy/controller/scorer/标签。

V2原score SHA `ecbd8cb3ce9d1dd1fc76290ddcbf145fb1a72c22c72c45b3ab8d037901039e91`；label SHA `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`；保存run snapshot与formal V2 snapshot一致，115→117等provider数量来自各自真实轮次，不混入root单独explicitratio诊断。

| 版本 | 总任务 | scorable | 标签pending | 冻结确认 | fail | 整条AI_pending | 确认/scorable | Wilson95%CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| V0 | 60 | 49 | 11 | 18 | 22 | 9 | 18/49 | 24.67%–50.73% |
| V1 | 60 | 49 | 11 | 18 | 22 | 9 | 18/49 | 24.67%–50.73% |
| V2 | 60 | 49 | 11 | 18 | 23 | 8 | 18/49 | 24.67%–50.73% |

三个版本均18/60总任务、18/49可评分=36.73%；coverage49/60=81.67%。V2新增确认sp03-01、sp01-24转pending，都是SQL表示匹配差异；不能归因目标guard。固定synthetic dev、重复题面/family缺口、一次随机模型输出不能支持泛化或显著改善结论。

| V2分组 | 总/scorable | 标签pending | 冻结确认 | fail | 整条AI_pending | Wilson95%CI |
|---|---|---:|---:|---:|---:|---|
| task:01 | 30/26 | 4 | 13 | 9 | 4 | 32.06%–67.94% |
| task:01/category:standard | 3/3 | 0 | 2 | 1 | 0 | 20.77%–93.85% |
| task:01/category:alias | 6/4 | 2 | 2 | 0 | 2 | 15.00%–85.00% |
| task:01/category:typo | 6/6 | 0 | 3 | 3 | 0 | 18.76%–81.24% |
| task:01/category:pinyin | 3/2 | 1 | 1 | 1 | 0 | 9.45%–90.55% |
| task:01/category:mixed_language | 3/3 | 0 | 1 | 1 | 1 | 6.15%–79.23% |
| task:01/category:colloquial | 3/3 | 0 | 2 | 0 | 1 | 20.77%–93.85% |
| task:01/category:multi_candidate | 3/2 | 1 | 1 | 1 | 0 | 9.45%–90.55% |
| task:01/category:explicit_absent | 3/3 | 0 | 1 | 2 | 0 | 6.15%–79.23% |
| task:03 | 30/23 | 7 | 5 | 14 | 4 | 9.66%–41.90% |
| task:03/category:L0 | 10/9 | 1 | 5 | 2 | 2 | 26.67%–81.12% |
| task:03/category:L1 | 5/3 | 2 | 0 | 3 | 0 | 0.00%–56.15% |
| task:03/category:L2 | 15/11 | 4 | 0 | 9 | 2 | 0.00%–25.88% |

| 指标 | V0 | V1 | V2 | V2未解决 |
|---|---|---|---|---:|
| ①初始绑定/字面契约 | 15/26 | 15/26 | 16/26 | 1 |
| ③初始level | 21/23 | 20/23 | 20/23 | 0 |
| ③必要召回 | 11/11 | 11/11 | 11/11 | 0 |
| ③多余澄清（低优） | 2/12 | 3/12 | 2/12 | 0 |
| ③澄清最终完成 | 0/11 | 0/11 | 0/11 | 2 |
| 最终条件保留 | 19/49 | 18/49 | 20/49 | 18 |
| ③L1默认/切换 | 1/3 | 1/3 | 1/3 | 0 |

V2 binding16/26较15/26唯一变化是sp01-10：Vaporwave未知字面SQL的AST恰好匹配，unknown_literal_sql_contract从None→True；actual resolved仍[]且响应仍sql_rejected，不能当成值索引/alias解析收益。普通query complete依据最终AST/result/post/L1，初始binding独立；不将18条解释为D2绑定全完整。sp01-27 IN列表与逐候选=表示缺口仍保留原score，overcorrection1/26不是已证明系统过纠正。

**V2目标guard的真实证据与未完成边界**

- **sp03-22**：三次sql_binding_validate拒绝未证明比例；最后SQL已无France全局WHERE，表达为ROUND(conditionalSUM/SUM(total)*100,2)。这是百分比表示，冻结gold为fraction；不能因guard拒绝就声称最后SQL仍缩窄分母。当前范围/单位证明限制导致未完成，root判断百分比表达被误拒，整题原score保持失败。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-22/turns/001/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-22/turns/001/provider/2ce2681aa4a5474cb7e5634bf5f0fcc6.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-22/turns/001/provider/cba30d135b99471b8a16b6df4bfadfac.json>)、[provider#3](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-22/turns/001/provider/8859f523cba14ee7ae8e75d12b0388f9.json>)、[provider#4](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-22/turns/001/provider/7e007faff956462cb0db57a9e01718cb.json>)；trace `ca591fb2-21bf-4fc4-993d-022ce27832e4`。
- **sp03-26**：真实先答2024全年、再答发票销售额，仍缺scope_missing，controller没有合法该key补充而停止；两个普通post均未执行。因此V2不能证明平均金额修改的同比/时期丢失问题已修复。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-26/turns/002/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-26/turns/002/provider/2eca380343cf4f4283702b7fa1c12118.json>)；trace `cdf95fdd-e989-4c96-a56a-081727dfb8e0`。
- **sp03-27**：turn1真实用户已经明确“巴西居住客户的销售额”，turn2合法给2023全库分母。最后SQL是条件Brazil分子/SUM(total)fraction、无Brazil全局WHERE，却被guard拒绝“分子客户归属没有实际用户原文证据”。先前用户证据直接存在于真实request/raw/provider；这是实际多轮证据边界，不能冒称SQL实际成功或自动等价通过。后续普通posts未执行。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/002/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/002/provider/7f380fea516541eb87c89c0311ad545a.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/002/provider/8e3dd585051e40aaba32f27fb309a28f.json>)、[provider#3](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/002/provider/7ebd46eeb5124ad5aff798ff0d7b5969.json>)、[provider#4](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/002/provider/179ef75cc176407d98cc887500f14359.json>)、[provider#5](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/002/provider/230e641d5d384f139e671d3448285b61.json>)；trace `7a2840d0-ecab-4f95-834e-6249eaa65ac3`。
  [先前实际分子补充请求](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/001/request.json>)；[先前实际分子补充响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/001/response.raw.json>)；[先前numerator provider](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-27/turns/001/provider/791bbdf0fce644e1b0287000a6e08273.json>)。
- **sp03-28**：真实普通修改“改成流派Metal”仍clarification_conflict，边界是替换筛选丢失未修改条件；第二普通post未执行。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-28/turns/002/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-28/turns/002/provider/f75e2c5372b447358c8541ac53e7104d.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp03-28/turns/002/provider/dc612b04e76443aeb2f9b1e7b69dbf67.json>)；trace `4d7fac99-d896-4eaf-b0f7-a346ba02ad0d`。

V1的sp03-27第一次被问numerator patch已有局部改善实证，但整题post仍未完成；V2新guard没有可靠端到端改善并引入合法多轮证据拒绝。root因此选择V1并回退V2 own三文件，不再优化/预测V3。完整来源恢复与最终重启由root独立记录，不在本报告冒称当前loaded版本。

**真实调用账目与完整性**

| 版本 | cohort POST | provider | prompt tokens | completion tokens | total tokens | 累计API ms | 自动archive | 独立verified |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V0 | 81 | 112 | 479534 | 14115 | 493649 | 393978 | 0 | 112 |
| V1 | 83 | 115 | 488418 | 13374 | 501792 | 426391 | 0 | 115 |
| V2 | 80 | 117 | 503640 | 14707 | 518347 | 405196 | 0 | 117 |

V2：60独立session；phase={'initial': 60, 'clarification': 13, 'post_completion': 7}，HTTP={200: 80}，status={'SUCCEEDED': 43, 'FAILED': 10, 'NEEDS_CLARIFICATION': 25, 'EMPTY_RESULT': 2}；澄清上限3、真实最大2；累计405,196ms、中位3,727ms、p95 nearest10,152ms、最大17,325ms。无transport timeout/无响应/ambiguous delivery；provider全部有usage。

原自动archive0由UUID32/36检查造成；独立补充verified117/unverified0，安全root/trace/source-copy SHA完整匹配。145受保护文件SHA未改变，actual request/raw/checkpoint/card version/choice audit errors=[]。offline本报告/分类/补充产生0 model/API/DB调用，费用不估算。root的explicitratio-live-001单独诊断不属于此60case cohort，不混入表格调用或token分母。

V2分类35条逐query/post语义待核验，8条整题AIpending与11条pending标签分层保留。整题AIpending：sp01-02, sp03-09, sp01-16, sp01-24, sp01-25, sp03-14, sp03-17, sp03-24。未证明SQL等价不转pass，不因结果同数证明字段/时期/分母正确。finding是重叠次数={"environment": 117, "annotation_scoring": 47, "linking": 16, "sql": 77, "rules_catalog": 7, "session_state": 13}；environment117是旧archive拒绝，不是117网络故障。全部root_cause_confirmed=False，model/unimplemented无已确认根因。

| case变化 | V0 outcome/complete | V1 outcome/complete | V2 outcome/complete |
|---|---|---|---|
| sp01-05 | api_failed/False | finished/False | api_failed/False |
| sp01-06 | finished/None | api_failed/None | api_failed/None |
| sp01-10 | api_failed/False | api_failed/False | api_failed/False |
| sp03-01 | finished/None | finished/None | finished/True |
| sp03-06 | controller_unanswered/None | controller_unanswered/None | finished/None |
| sp01-18 | finished/False | finished/False | api_failed/False |
| sp01-20 | api_failed/False | finished/None | api_failed/False |
| sp01-24 | finished/True | finished/True | finished/None |
| sp01-30 | finished/None | finished/None | controller_unanswered/False |
| sp03-14 | finished/None | controller_unanswered/False | finished/None |
| sp03-22 | finished/False | controller_unanswered/False | api_failed/False |
| sp03-26 | finished/False | finished/False | controller_unanswered/False |
| sp03-27 | api_failed/False | post_completion_incomplete/False | api_failed/False |

**实际文件与命令证据**

- [V2trial formal freeze](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V2-freeze.json>)
- [V2trial snapshot](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V2-code-snapshot.json>)
- [V2真实重启record](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V2-restart-record.json>)
- [V2保存run snapshot/health](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/run-manifest.json>)
- [V2冻结原score](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-scores.json>)
- [117provider补充核验](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-provider-supplement-summary.json>)
- [V2trial完整性审计](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-final-integrity.json>)
- [V2全60机器索引](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-evidence-index.json>)
- [V2全60响应/provider直链](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-evidence-index.md>)
- [V2target原始证据](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-target-guard-observations.json>)
- [三版本同冻结评分比较](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-V1-V2-frozen-score-comparison.json>)
- [V2分类JSON](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-classification/failure-classification.json>)
- [V2分类Markdown](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-classification/failure-classification.md>)
- [35逐query语义pending](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-classification/semantic-review-pending.jsonl>)
- [11标签pending](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-classification/pending-label-review.jsonl>)
- [实际V2 run command（内部score）](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V2-001/run-command-loopback.json>)
- [run stdout](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V2-001/run-stdout-loopback.log>)
- [run stderr空](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V2-001/run-stderr-loopback.log>)
- [run exit0](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V2-001/run-exit-loopback.json>)
- [实际classify command](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V2-001/classify-command.json>)
- [classify stdout](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V2-001/classify-stdout.log>)
- [classify stderr空](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V2-001/classify-stderr.log>)
- [classify exit0](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V2-001/classify-exit.json>)
- [最终选择V1的实际复测报告](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-run-report-v2.md>)
- [V0实际报告](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-run-report.md>)

原score仅保留冻结结果，无重算/覆盖/迎合gold；预测已停止，不做V3。
