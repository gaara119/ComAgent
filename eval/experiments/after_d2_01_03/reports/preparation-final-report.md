# 专项①③数据准备与 AI 标签预审记录

本记录覆盖专项造题、参考 SQL 标注、程序校验和两遍独立 AI 预审。最终标签为 `data/cases-v6-reviewed.jsonl`，60 个本轮模型生成的合成开发候选，规范化题面去重后 58 个，49 个可以按本轮协议评分，11 个待确认。全部 60 个的人工状态仍为 `pending_human_review`。本记录没有被测系统 V0/V1/V2 的预测或成绩；V0 必须由主流程在 D2/D3 实际完成版本上运行。

60 个候选满足原定类别数，但合格题并未完全满足所有配额。不能把候选配额写成“60 题全部验收通过”，不能把 49 题开发成绩称为正式泛化成绩，也不能把 AI 预审记为人工签字。

## 数量与有效覆盖

20 题真实 pilot 包含①10题、③10题，已经计入最终60题。先完成 pilot 的程序检查与一轮有界修正，再新增40题。全部原始尝试、修正与失败记录均保留。

| 专项①主类别 | 生成候选 | 可评分 | 待确认 |
|---|---:|---:|---:|
| 标准表达 | 3 | 3 | 0 |
| 别名 | 6 | 4 | 2 |
| 错字 | 6 | 6 | 0 |
| 拼音 | 3 | 2 | 1 |
| 中英混合 | 3 | 3 | 0 |
| 口语 | 3 | 3 | 0 |
| 多候选 | 3 | 2 | 1 |
| 明确不存在 | 3 | 3 | 0 |
| 合计 | 30 | 26 | 4 |

| 专项③主类别 | 生成候选 | 可评分 | 待确认 |
|---|---:|---:|---:|
| L0：信息完整且不使用默认 | 10 | 9 | 1 |
| L1：适用已确认默认 | 5 | 3 | 2 |
| L2：缺关键条件或存在多解释 | 15 | 11 | 4 |
| 合计 | 30 | 23 | 7 |

题面涉及多个国家、音乐流派、艺术家、媒体格式及发票、客户、曲目、专辑等对象。多轮控制器支持真实年份、地区及指标变化；普通后续修改存在于8个候选、共13个后续turn，其中重复或有争议的候选仍排除确定评分。最大3次澄清followup和普通后续修改分别计数，不能用隐藏目标代替用户逐项补充。

## 原始过程与标签变更

| 阶段 | 实际动作与结果 | 证据 |
|---|---|---|
| 原始 pilot | 4个模型生成call产出20题，程序14通过、6争议 | `data/cases-pilot-generated.jsonl`、`checks/program-pilot.json` |
| 一轮 pilot 修正 | 2个独立模型call修正8个选中候选；原题保留。修正后程序17通过、3争议，没有继续刷题 | `data/pilot-revision-manifest.json`、`data/pilot-repairs-v2.json`、`checks/program-pilot-v2.json` |
| 扩展40题 | 再执行8个生成call，凑齐30+30候选。一个生成call三次返回L2空SQL并失败 | `calls/generate-03-expansion-03/complete.json`、`provider_attempts.json` |
| 失败候选回收 | 从失败call的实际provider响应中按固定规则选“最早完整且ID/类别匹配的JSON”；保留失败状态，不把回收视为标签通过 | `data/invalid-protocol-recovery.json`、`calls/generate-03-expansion-03/recovered-invalid-candidates.json` |
| 参考 SQL 补齐 | 在任何V0运行前，经主流程明确授权，最多2个独立标注call为7个既有L2显式final_intent补SQL。原null和理由保留，问题/类别/目标不变 | `data/gold-completion-manifest.json`、`calls/complete-reference-sql-01/`、`calls/complete-reference-sql-02/` |
| 格式规范化 | 将原expected_bindings中的聚合、时间谓词、未解决占位分开保存，完整保留raw_expected_bindings；不改题目、gold或目标 | `data/format-normalization-manifest.json` |
| 最终程序检查 | 57通过、3争议；77条final/candidate/post-turn SQL检查，76实际只读执行成功，1条空SQL在执行前失败 | `checks/program-normalized-v4.json` |
| 第一遍 AI | 每5题一批，12个全新context逐项读实际材料，56建议通过、4争议 | `checks/ai-pass-1.json`、`calls/review-p1-*/` |
| 第二遍 AI | 另12个全新context逐项读实际材料，不提供第一遍判断 | `checks/ai-pass-2.json`、`calls/review-p2-*/` |
| 最终来源/控制器守卫 | 由已确认默认、停用别名及控制器一致性规则，排除4个AI漏检候选；保留原双AI判断，最终49可评分/11待确认 | `checks/final-source-guards.json`、`data/cases-v6-reviewed.jsonl` |

参考 SQL 补齐涉及 `sp03-06/07/21/22/23/24/25`。这些目标原先已由离线控制器明确，不是让标注模型猜原歧义，也没有看被测系统结果后调整答案。原始失败call仍为失败；“有参考SQL”不自动使题可评分。

跨各准备版本累计有251条成功只读参考SQL执行记录，另有9条真实源事实查询，共260条成功只读查询。阶段重复校验包含相同SQL，不能解释为260个独立SQL或260道题。全部通过现有`qa_reader`与只读事务、`statement_timeout=5000ms`执行，业务数据库没有写入。

## 待确认与预审限制

| ID | 保留争议的主要原因 |
|---|---|
| sp01-06 | 拼音Deguo与专辑对象的解释无有效唯一依据，gold为空且原模型说明不可靠 |
| sp01-13 | 与sp01-02规范化题面完全重复，不能作为独立合格题 |
| sp01-14 | 国家语义可指客户居住地或账单国，标签却直接选客户居住地 |
| sp01-28 | 使用pending的“金属→Metallica”候选，且原题明确流派却扩展艺术家；实际Heavy Metal存在，不以“不存在”作为排除理由 |
| sp03-05 | 两遍AI对显式2007无数据的热门曲目标签意见不一；保留争议，不因一遍通过而强制晋级 |
| sp03-06 | 复核意见出现并不存在的后续2021turn，标签预审仍有争议 |
| sp03-10 | 显式客户对象仍过度列地区口径缺项，复核还提及实际不存在的India后续turn |
| sp03-15 | 热门默认数量实际适用，候选L0分类与已确认L0/L1口径冲突 |
| sp03-20 | 已显式按销售额取前10，Top10默认并不适用，候选L1分类错误 |
| sp03-23 | 与sp03-08规范化题面完全重复 |
| sp03-25 | 同一控制器value补充为Rock、genre补充为Rock And Roll，显式唯一final target为Rock；无法一致回答合法askedkey |

两遍AI均实际调用并读取本轮真实材料，但AI存在漏检和幻觉。`checks/ai-review-quality-notes.json`记录4条涉及实际不存在后续turn的AI评语；请求原文可核实这些turn未提供。来源/控制器守卫也发现双AI都漏掉的类别和补充一致性问题。这些原始AI意见没有删除、重写或冒充人工审核；有争议项保留待确认。

## 模型实际使用

| 阶段 | 逻辑call | provider请求（含retry） | 实际总token | provider latency之和/ms |
|---|---:|---:|---:|---:|
| 生成 | 12 | 15 | 297091 | 213433 |
| pilot修正 | 2 | 3 | 67909 | 61706 |
| 既有显式目标参考SQL补齐 | 2 | 2 | 34822 | 13055 |
| AI第一遍 | 12 | 13 | 294173 | 104239 |
| AI第二遍 | 12 | 12 | 276973 | 153605 |
| 合计 | 40 | 45 | 970968 | 546038 |

provider实际返回模型均为`deepseek-flash`。prompt token共876911，completion token共94057。45次provider请求均成功返回；其中6次响应遭JSON/协议校验拒绝，1个逻辑生成call三次失败。每个逻辑call最多3次尝试，未越过额外2次retry。provider latency合计不是任务墙钟时间，金额成本未取得，不推算价格。早期36/38 call只是准备阶段估算，非用户规定的硬费用上限；本记录以40逻辑call/45请求实账为准。

真实prompt在`prompts/`，每次实际request、SHA、provider原始响应、token、latency、trace与error在`calls/`。早期pilot prompt更新过，已恢复原始字节并验证其SHA，见`materials/original-prompt-recovery.json`。生成prompt、修正prompt、SQL标注prompt和两遍checker prompt均用于真实模型调用；没有调用被测`/api/chat`生成gold。

## 材料范围、隐私与历史暴露

来源为项目指定的现有Chinook。材料含schema字段/类型、公开音乐实体/国家标准值、已确认业务口径、已审别名及公开样例数据库日期范围；未发送customer/employee姓名、邮件、电话、地址、数据库连接或`.env`。原始源manifest记载官方Chinook MIT来源。出网材料和授权证据见`materials/outbound_payload_audit.json`与`materials/model-network-authorization-evidence.md`。

第一次模型网络提权因可能导出敏感数据被自动审批拒绝。随后补充明确用户专项全文授权和公开Chinook无个人联系数据payload证据，重新审核相同授权动作获得批准；没有绕过拒绝、换隐蔽途径或伪造生成。只读数据库连接也由明确只读说明经审批恢复。

本造题context未读取holdout题目、答案或历史混合审核表；没有广搜整个eval。根会话历史可能早期接触过部分holdout，新的context不能消除历史暴露。所有60题标为本轮合成dev。本交接只提供dev `family-metadata.json`供主流程做元数据重合检查；不在这里宣称已获得独立保留集隔离或泛化证据。

## 交接文件与冻结边界

- 最终标签：`data/cases-v6-reviewed.jsonl`，SHA256 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。
- 冻结提案：`data/freeze-proposal.json`，状态`proposal_awaiting_root_formal_v0_freeze`。它不是主流程正式V0冻结记录。
- 生成时材料manifest：`materials/source_manifest.json`，SHA256 `5201b756d4e91a8ae5f383ca972740e4afd192997b57751a5a4497b02063b157`。其中clarify代码hash是生成准备时观察，D3后续实际提交需由主流程另存正式V0代码/config快照。
- 评分协议：`reports/scoring-protocol-draft.md`，SHA256 `b8f6b7d1d1d531d810a2244f6662db767d9654bc14e1bafa7a10637f918b480e`。
- SQL结果：主gold在label内，candidate和后续SQL结果在`checks/program-normalized-v4.json`。
- 费用实账：`reports/preparation-usage.json`、`reports/preparation-stage-usage.json`。
- 复现/恢复步骤：`reports/preparation-reproduction.md`；不出网不连DB的交接核验：`scripts/verify_handoff.py`。

主流程确认并正式冻结后，runner应保持这些label字节不变。预测只发送真实input/history/scope以及当轮askedkey合法补充，不把类别、hidden_goal、final_intent、goldSQL或答案送给被测系统。待确认题可保留运行覆盖，但不得强制判定对错。ZIP/GitHub和整体验收由主流程生成，本准备报告不把尚未执行的预测、优化或发布写成完成。
