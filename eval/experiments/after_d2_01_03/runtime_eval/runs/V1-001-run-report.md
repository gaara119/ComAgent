**V1-001 完整真实复测与冻结同口径结果**

全60条run+内部score、离线classify已实际完成，exit0、stderr为空。83真实POST均有响应、60独立session、最大3澄清，未无响应重放、未holdout预测，未修改冻结runtimepy/controller/scorer/业务prompt/标签。V1是父root正式冻结的intent_patch.txt单prompt修改；其余源码/标签/safe_config/评分与V0相同。这里只描述一次真实复测，未将其它随机输出变化归因P3。

原score SHA `af319fde76d4a617c365c7772b564fd88cd3dd7191d7272664aa6017099178fb`；label SHA `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。run保存snapshot与V1formal snapshot完全一致，115provider路径/trace/source-copy SHA匹配，受保护原证据未改。

| 分组 | 总分母 | scorable | 标签pending | 冻结确认 | 自动fail | 整条AI_pending | 确认/scorable | Wilson95%CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 全部 | 60 | 49 | 11 | 18 | 22 | 9 | 18/49 | 24.67%–50.73% |
| ① | 30 | 26 | 4 | 14 | 7 | 5 | 14/26 | 35.46%–71.24% |
| ③ | 30 | 23 | 7 | 4 | 15 | 4 | 4/23 | 6.98%–37.14% |

18/60和18/49=36.73%与V0相同，确认ID集合未变。覆盖49/60=81.67%，11pending标签不binary算正确。9整条AIpending与37逐query/post语义核验记录统计层次不同。普通query complete未将初始binding作为必要条件；绑定指标单列。严格AST未证明等价不转pass，数值相同不证明字段/分母/时期正确；候选IN评分兼容缺口仍保留原score。

| 类别 | 总/scorable | 冻结确认 | fail | 整条AI_pending | Wilson95%CI |
|---|---|---:|---:|---:|---|
| task:01/category:standard | 3/3 | 2 | 1 | 0 | 20.77%–93.85% |
| task:01/category:alias | 6/4 | 2 | 0 | 2 | 15.00%–85.00% |
| task:01/category:typo | 6/6 | 3 | 2 | 1 | 18.76%–81.24% |
| task:01/category:pinyin | 3/2 | 1 | 1 | 0 | 9.45%–90.55% |
| task:01/category:mixed_language | 3/3 | 2 | 1 | 0 | 20.77%–93.85% |
| task:01/category:colloquial | 3/3 | 2 | 0 | 1 | 20.77%–93.85% |
| task:01/category:multi_candidate | 3/2 | 1 | 1 | 0 | 9.45%–90.55% |
| task:01/category:explicit_absent | 3/3 | 1 | 1 | 1 | 6.15%–79.23% |
| task:03/category:L0 | 10/9 | 4 | 3 | 2 | 18.88%–73.33% |
| task:03/category:L1 | 5/3 | 0 | 3 | 0 | 0.00%–56.15% |
| task:03/category:L2 | 15/11 | 0 | 9 | 2 | 0.00%–25.88% |

| 指标 | V0正项/分母 | V1正项/分母 | V1未解决 |
|---|---|---|---:|
| ①绑定 | 15/26 | 15/26 | 2 |
| ③初始level | 21/23 | 20/23 | 0 |
| ③必要召回 | 11/11 | 11/11 | 0 |
| ③多余澄清（低优） | 2/12 | 3/12 | 0 |
| ③澄清最终完成 | 0/11 | 0/11 | 2 |
| 条件保留 | 19/49 | 18/49 | 20 |
| ③L1默认/切换 | 1/3 | 1/3 | 0 |

V1 outcome：41 finished、4 api_failed、3 candidate_only_clarification、10 controller_unanswered、2 post_completion_incomplete。所有业务FAILED有实际HTTP200响应；无transport timeout/ambiguous delivery/无响应。

实际POST83 / provider115；prompt488,418 + completion13,374 =501,792tokens，provider missing usage0；累计API426,391ms、中位3,918ms、p95 nearest10,879ms、最大15,962ms；phase={'initial': 60, 'clarification': 13, 'post_completion': 10}。原自动archive0、独立补充verified115/unverified0分列；补充observer未改变score。费用不估算，离线生成审核calls不混入。

**目标被问字段的局部变化与仍失败的问题**

- sp03-27首次numerator回答：V0实际patch改region_scope并add全局filters、未set numerator；V1只set numerator，2023时期保留，剩余仅denominator，version1→2且无error。该被问字段patch的局部正确性观察改善；[逐provider patch与真实响应证据](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-V1-sp03-27-target-patch-observation.md>)。V1后来普通改德国居住进入新clarification，整题仍post_completion_incomplete，不能称全through。
- sp03-26平均发票金额的普通修改仍变成全表AVG(total)，丢失同比与2025/2024时期，目标未修复。
- sp03-28改流派Metal仍clarification_conflict，边界为替换筛选丢失未改其它条件。
- sp03-05/18/19/29等输出投影与实际条件差异要分别核验；列数失败不能当所有语义错误，sp03-18时间范围确实仍需查验。
- sp01-05 api_failed→finished，但SQL WHERE album.title=Metallcia仍结果失败。sp01-20 api_failed→finished，仅结果相等，使用media_type_id=1，fail→AIpending。sp03-14 finished/pending→controller_unanswered/fail。确认ID集合无变化，不能据这些状态变化宣称P3全组收益。
- sp01-27两候选保留、bound=[]却因IN列表与=候选表示比较标失败，原overcorrection1/26仍不是已证明系统过纠正。

| ID | V0 outcome/complete | V1 outcome/complete | V1主result reason |
|---|---|---|---|
| sp01-05 | api_failed/False | finished/False | column_values_mismatch |
| sp01-06 | finished/None | api_failed/None | Saved gold_result unavailable |
| sp01-20 | api_failed/False | finished/None | equal |
| sp03-14 | finished/None | controller_unanswered/False | No successful query result |
| sp03-22 | finished/False | controller_unanswered/False | No successful query result |
| sp03-27 | api_failed/False | post_completion_incomplete/False | equal |

整条AIpending9：sp01-02, sp03-01, sp03-09, sp01-16, sp01-20, sp01-25, sp01-30, sp03-17, sp03-24。未证明SQL等价继续AIpending；11标签pending保存实际但不binary算correct。分类八类重叠finding={"environment": 115, "annotation_scoring": 49, "linking": 16, "sql": 59, "rules_catalog": 8, "session_state": 15}；environment115来自旧archive拒绝，独立补充已全核验，不是115网络故障。model/unimplemented无确认根因；全部root_cause_confirmed=False。CI仅描述固定synthetic dev，不声称泛化或显著收益。

**实际产物与命令证据**

- [formal freeze](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V1-freeze.json>)
- [正式SHA snapshot](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V1-code-snapshot.json>)
- [实际重启load record](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V1-restart-record.json>)
- [run manifest](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/run-manifest.json>)
- [冻结原score](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-scores.json>)
- [115补充provider核验summary](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-provider-supplement-summary.json>)
- [结束审计](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-final-integrity.json>)
- [全60机器证据索引](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-evidence-index.json>)
- [全60逐turn响应/provider可点击索引](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-evidence-index.md>)
- [同冻结评分变化表](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-V1-frozen-score-comparison.json>)
- [目标patch证据JSON](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-V1-sp03-27-target-patch-observation.json>)
- [分类JSON](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-classification/failure-classification.json>)
- [分类Markdown](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-classification/failure-classification.md>)
- [37逐query语义pending](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-classification/semantic-review-pending.jsonl>)
- [11标签pending](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-classification/pending-label-review.jsonl>)
- [真实run command](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V1-001/run-command-loopback.json>)
- [run stdout](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V1-001/run-stdout-loopback.log>)
- [run stderr空](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V1-001/run-stderr-loopback.log>)
- [run exit0](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V1-001/run-exit-loopback.json>)
- [实际classify command](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V1-001/classify-command.json>)
- [classify stdout](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V1-001/classify-stdout.log>)
- [classify stderr空](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V1-001/classify-stderr.log>)
- [classify exit0](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V1-001/classify-exit.json>)

runner内部score已实际执行；未额外重算或改原score。V2预测停止，等待父root正式freeze和授权。
