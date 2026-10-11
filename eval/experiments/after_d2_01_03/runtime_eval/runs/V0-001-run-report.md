**V0-001 实际专项运行、冻结评分与证据审计**

60条实际执行完毕，run内部完成score，离线classify完成；真实run与classify exit=0、stderr为空。首次sandbox GET /health被WinError10013拒绝，任何POST前失败；原command/stdout/stderr/exit保留，之后窄loopback执行成功。81个POST均保存真实响应，没有重放无响应POST，没有holdout预测，没有运行期间源码/prompt/controller/scorer/标签变更。

label SHA `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`；原score SHA `7f593311e7d4d1a6b3d3d01383b00e95e434d8c681ce029ed240bb8012516cab`；V0 run保存snapshot与formal snapshot完全一致。当前源已正式冻结为V1，与V0相比仅`qa_agent/clarify/prompts/intent_patch.txt`变化，因此本回顾不声称当前源码仍等于V0。

| 分组 | 总分母 | scorable | 标签pending | 冻结确认完成 | 自动失败 | 整条AI_pending | 确认/scorable | 描述性Wilson95%CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| 全部 | 60 | 49 | 11 | 18 | 22 | 9 | 18/49 | 24.67%–50.73% |
| ①值链接 | 30 | 26 | 4 | 14 | 8 | 4 | 14/26 | 35.46%–71.24% |
| ③澄清与修改 | 30 | 23 | 7 | 4 | 14 | 5 | 4/23 | 6.98%–37.14% |

18/60保留总任务分母，18/49=36.73%是冻结确认完成数；标签覆盖49/60=81.67%。9条整条语义pending与11条标签pending独立保留。固定synthetic dev、重复题面和family元数据缺口不能支持泛化/显著收益结论。普通query complete根据最终AST/result/post/L1行为判断，初始binding独立评分；sp01-04/17最终SQL匹配但初始resolved缺失，所以不能宣称18条同时证明D2初始绑定完整。

| 类别 | 总/scorable | 确认 | 自动失败 | 整条AI_pending | Wilson95%CI |
|---|---|---:|---:|---:|---|
| task:01/category:standard | 3/3 | 2 | 1 | 0 | 20.77%–93.85% |
| task:01/category:alias | 6/4 | 2 | 0 | 2 | 15.00%–85.00% |
| task:01/category:typo | 6/6 | 3 | 3 | 0 | 18.76%–81.24% |
| task:01/category:pinyin | 3/2 | 1 | 1 | 0 | 9.45%–90.55% |
| task:01/category:mixed_language | 3/3 | 2 | 1 | 0 | 20.77%–93.85% |
| task:01/category:colloquial | 3/3 | 2 | 0 | 1 | 20.77%–93.85% |
| task:01/category:multi_candidate | 3/2 | 1 | 1 | 0 | 9.45%–90.55% |
| task:01/category:explicit_absent | 3/3 | 1 | 1 | 1 | 6.15%–79.23% |
| task:03/category:L0 | 10/9 | 4 | 2 | 3 | 18.88%–73.33% |
| task:03/category:L1 | 5/3 | 0 | 3 | 0 | 0.00%–56.15% |
| task:03/category:L2 | 15/11 | 0 | 9 | 2 | 0.00%–25.88% |

| 指标 | 正项/适用任务分母 | 已观测 | 未解决 |
|---|---|---:|---:|
| ①初始column/operator/value绑定 | 15/26 | 24 | 2 |
| ③初始L0/L1/L2 | 21/23 | 23 | 0 |
| ③必要澄清召回 | 11/11 | 11 | 0 |
| ③L0/L1多余澄清（低优） | 2/12 | 12 | 0 |
| ③L2澄清后最终完成 | 0/11 | 9 | 2 |
| 全部最终条件保留 | 19/49 | 28 | 21 |
| ③L1默认/切换 | 1/3 | 3 | 0 |

outcome：42 finished、6 api_failed、3 candidate_only_clarification、8 controller_unanswered、1 post_completion_incomplete。api_failed均已有业务失败响应，不是timeout；L2 recall11/11仅证明提问，最终完成0/11（其中2条整条pending），不能以level-only当成功。

真实POST81，provider attempts112，全部usage可观测；prompt479,534 / completion14,115 / total493,649tokens。API累计393,978ms，中位3,711ms，p95 nearest10,291ms，最大15,791ms。60独立session，max澄清3，phase={'initial': 60, 'clarification': 12, 'post_completion': 9}，HTTP={200: 81}。无ambiguous delivery/无响应/transport timeout；费用不估算，离线生成/审核调用不混入。

原自动provider归档0：冻结runner要求36字符UUID，observer实际为32hex UUID。原rejected manifest/checkpoint/score保持不变；父root独立离线补充观测112、verified112、unverified0，安全root+UUID+trace+SHA逐项核验，受保护原证据未变。0 model/API/DB补充调用。分类中的112个environment finding是此归档缺口，不是112次网络故障。

**关键观察与定位（不改分、不自动确认根因）**

- **sp01-05 / 链接+SQLguard**：Metallcia未纠正Metallica，resolved缺失；三次SQL/repair均被没有跨表业务要求guard拒绝。sp01-07/10/20/22同guard；sp01-07/20已有正确media_type字面仍拒绝。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-05/turns/000/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/4346b559dd5141e3b66d897b24e5ae51.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/0b9a859981c04fe580c54d892283391c.json>)、[provider#3](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-05/turns/000/provider/fa1b4a7aaa1b4fc29efced7c79ff1c8f.json>)；trace `300b313b-d7f3-428a-9930-7f1070585c72`。
- **sp01-18 / 链接+任务**：Led Zepelin未纠正，返回artist_id而非专辑计数。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-18/turns/000/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/d1ccb2b86f914827a044d7089bbb6be7.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/d9599e21191f4877992421a19b4a5db9.json>)、[provider#3](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-18/turns/000/provider/fd278ffb120f47809d78c1c0a0e61925.json>)；trace `7f4c5f60-cfcc-4224-814d-b51ad9c863b5`。
- **sp03-07 / 规则目录**：显式billing_country USA仍问region_scope，应问的denominator未出现；无合法region补充。sp01-12/sp03-13已有billing绑定仍问地区。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-07/turns/000/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-07/turns/000/provider/bc63572d0228412d9e61013453d86abf.json>)；trace `855e068b-2e8b-43fd-bfc8-bd54c9078df4`。
- **sp03-21 / controller边界**：time_ambiguous与time_scope.current同卡指向同一时间，bundle guard当不同key而拒绝年份；sp03-06（pending）亦同。未强猜补充。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-21/turns/000/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-21/turns/000/provider/f372e0d7586746fdba6ef3f5703aded2.json>)；trace `5c871f89-6c96-432e-bd2b-b8624b388d08`。
- **sp03-08 / controller/协议**：card同时问metric和rank_object；allowed rank回答带metric，控制器保守拒绝bundle，无POST补充。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-08/turns/000/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-08/turns/000/provider/8d52d1bf6b4f439fa121f4b496f7b6e5.json>)；trace `ee48a0a7-c5b6-4db9-9aa1-20c77958f6e4`。
- **sp03-22 / SQL分母**：WHERE customer.country=France使全球分母缩为France，另*100/ROUND与fraction单位不同，actual值不匹配。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-22/turns/001/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-22/turns/001/provider/902a90ee817a43eea8cbef5bf2803ce1.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-22/turns/001/provider/e676bb4ea8c141849cfb13e567d6a579.json>)、[provider#3](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-22/turns/001/provider/c2f80095c35742f790872aff7e2c8076.json>)；trace `bb13afb0-fa7c-476b-8964-7427acf9f774`。
- **sp03-26 / 会话条件丢失**：真实修改平均每张发票金额后SQL仅全表AVG(total)，2025/2024期间和同比任务丢失；早前额外current/base列问题分别保留。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/turns/004/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/turns/004/provider/9c9dff70c1814ba793b96ed58af5e211.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-26/turns/004/provider/cbb150285108478ba8e1406155ccda5d.json>)；trace `37c76dbd-ef6f-4936-8bdb-e1df3f405cd4`。
- **sp03-27 / 地区guard**：巴西居住客户的销售额触发clarification_conflict，后续denominator与普通修改未偷跑。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-27/turns/001/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-27/turns/001/provider/434e7099872f4d48b4e967476d1722d1.json>)；trace `669c4003-c08d-439e-9d36-285023991418`。
- **sp03-28 / 筛选替换guard**：改成流派Metal触发不得删除此前artist条件的clarification_conflict；第二普通修改未执行。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-28/turns/002/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-28/turns/002/provider/32cc9e2de3e24eb799576ff0f1ee85f4.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-28/turns/002/provider/9592be9ab8414255bc710e11b166a48d.json>)；trace `664bf829-abb0-4897-a24a-ca2626dfa3f5`。
- **sp03-18 / 时间**：2021到2022实际仅2022，且额外名称列；不能只归为投影差异。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-18/turns/000/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-18/turns/000/provider/c44c8968ae154a26a835e3ed0ab23ebe.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-18/turns/000/provider/d7b4d54a9c544c0698c43763bb78ad00.json>)；trace `9721037c-00a4-4fc7-aba6-5ef151bfbe53`。
- **sp03-04 / 投影/评分**：实际返回track_name导致strict column_count_mismatch；sp03-19/29同类。是否允许业务展示列需独立审查，SQL等价不自动pass。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-04/turns/000/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-04/turns/000/provider/fdef97271348481c87e39523eff3fe50.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-04/turns/000/provider/f8a3f7b5960a403ea0be9395cc5892d6.json>)；trace `53569b2b-117b-4c03-9530-346f7d14d7ff`。
- **sp03-30 / 默认/标签**：3澄清+2普通修改真实执行，时期及对象指标切换保留；top10延续而goldtop1，谁买最多与默认N边界需审查。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/005/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/005/provider/5e562af085c343d5917db5a6cd9e37c7.json>)、[provider#2](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp03-30/turns/005/provider/60912ea5c21c4d4bad0d0a95cc923c34.json>)；trace `a0013847-2038-4fb5-a6cc-6b42df5d53ae`。
- **sp01-27 / scorer表示缺口**：保留Rock/Rock AndRoll候选、bound=[]；IN列表标签和两个=候选比较不等，原score失败/overcorrection1。不能据1/26宣称系统已过纠正。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-27/turns/000/response.raw.json>)；该turn无provider调用；trace `7dfb1cee-9066-4c1b-8bb3-45dc64dddb5b`。
- **sp01-25 / 地区语义**：actual billing_country Italy而gold customer.country Italy；数值相同不证明语义一致，保留pending和字段差异。 [实际响应](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-25/turns/000/response.raw.json>)；[provider#1](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/cases/sp01-25/turns/000/provider/614447ac8b1849f3b013c0ecfeb0ee7e.json>)；trace `43981c0d-5078-4c06-9ef8-eb66d6596992`。

离线分类全部root_cause_confirmed=False，八类finding（可重叠）={"environment": 112, "annotation_scoring": 49, "linking": 16, "sql": 61, "rules_catalog": 7, "session_state": 12}。model/unimplemented未确认原因，不能仅凭状态归因。

整条AI_pending9：sp01-02, sp03-01, sp03-09, sp01-16, sp01-25, sp01-30, sp03-14, sp03-17, sp03-24。COUNT与DISTINCT、CAST日期、JOIN方向与投影差异仅证据待审，不因结果相同自动pass。semantic-review-pending有37条逐query/post记录，统计层次与整条9不同，也含结果失败和pending标签题。11标签pending继续独立人工审核。

**实际产物与可重复命令**

- [formal freeze](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V0-freeze.json>)
- [code/prompt/config frozen SHA](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V0-code-snapshot.json>)
- [服务重启证据](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/V0-restart-record.json>)
- [run snapshot+health+safeconfig](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001/run-manifest.json>)
- [冻结原score](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-scores.json>)
- [独立provider补充summary](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-provider-supplement-summary.json>)
- [原冻结/请求/归档审计](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-final-integrity.json>)
- [全60机器证据索引](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-evidence-index.json>)
- [全60点击请求/响应/provider索引](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-evidence-index.md>)
- [失败分类JSON](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-classification/failure-classification.json>)
- [失败分类Markdown](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-classification/failure-classification.md>)
- [37逐query语义待核验](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-classification/semantic-review-pending.jsonl>)
- [11标签待确认](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-classification/pending-label-review.jsonl>)
- [真实run command（含内部score）](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/run-command-loopback.json>)
- [run stdout](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/run-stdout-loopback.log>)
- [run stderr空](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/run-stderr-loopback.log>)
- [run exit0](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/run-exit-loopback.json>)
- [实际classify command](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/classify-command.json>)
- [classify stdout](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/classify-stdout.log>)
- [classify stderr空](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/classify-stderr.log>)
- [classify exit0](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/classify-exit.json>)
- [首次失败command（无POST）](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/run-command.json>)
- [首次失败stderr](<E:/中国电子杯-赛题八/system/eval/experiments/after_d2_01_03/runtime_eval/execution-logs/V0-001/run-stderr.log>)

真实run动作在末尾内部调用冻结scorer，command含--post-results和--output；未为报告重复API或score。下一版本由父root冻结后授权，未自行优化。
