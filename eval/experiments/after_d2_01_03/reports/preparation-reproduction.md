# 专项数据准备复现与失败恢复

工作目录是 `E:\中国电子杯-赛题八\system`，Python为现有`.venv`。本目录为生成/标签准备，不启动服务，不运行被测系统，不读取holdout。已保存全部40逻辑call、45provider请求，正常审计和结果重放无需付费模型请求。

## 安全的本地交接核验

在PowerShell执行：

```powershell
.\.venv\Scripts\python.exe .\eval\experiments\after_d2_01_03\scripts\verify_handoff.py
```

该命令只读取本目录已保存证据，不读取`.env`、不出网、不连数据库、不重写标签。它核对标签/材料manifest/评分协议SHA，60ID与58唯一题面、49可评分/11待确认、人审pending、两遍AI逐ID原文与label对应、最终来源守卫、77SQL检查/76执行、历史prompt原始字节、40call/45请求和token/latency实账、family元数据与最终版本一致。输出`passed`仅代表交接内部一致，不等于人工验收或被测系统成绩。

## 已完成阶段顺序

`scripts/prepare_data.py`提供如下阶段。已有证据目录中的逻辑callID为固定缓存；有`result.json`时只读取缓存，有失败`complete.json`时拒绝自动重启，避免失败call反复付费刷题。不要删除call目录来绕过该限制。

```text
setup → pilot → repair-pilot → full（生成失败停止）
→ recover-invalid → full（缓存重放/继续剩余计划）
→ complete-gold → normalize → review → final-guards → usage
```

对应调用格式为：

```powershell
.\.venv\Scripts\python.exe .\eval\experiments\after_d2_01_03\scripts\prepare_data.py <stage>
```

`setup`和多数阶段会读取当前项目源材料并更新`generation_materials.json`；若现在项目代码/材料已经改变，不能把重跑后的材料误称为原始调用材料。原始请求的payload与prompt SHA以`calls/<id>/request.json`为准，生成准备时hash以`materials/source_manifest.json`为准。正式V0代码版本由主流程另行快照。本次提交的最终v6标签已交接，不为审计目的重跑修改它。

## 网络及数据库边界

模型阶段复用`qa_agent.config/llm/trace`和现有DeepSeek设置，每call最多3次尝试，串行小批执行。实际模型结果不是确定性可再现文本；已记录的provider响应才是本轮事实。不得把新provider输出覆盖为原call结果。需要新一轮实验时使用新的实验目录/ID并单独授权、记账，而非清空本轮失败标记。

数据库事实和参考SQL校验使用`qa_reader`、只读事务、5000ms timeout。只允许读取现有Chinook，不向业务库写数据。模型payload含公开音乐、国家实体及schema/已确认业务材料，无个人联系记录、key、DSN或`.env`。环境若禁止连接，按实际低风险用途明确申请提权；自动审核拒绝时保存拒绝原因，不换通道绕过。

## 本轮实际失败恢复

`generate-03-expansion-03`的3次provider返回都缺少5条L2的final reference SQL，原call保持失败。恢复程序仅回收最早语法有效且恰好匹配固定5个ID/类别的候选JSON，不按“更好答案”挑响应。回收候选仍带争议，详见`data/invalid-protocol-recovery.json`。

后续经主流程明确同意，在V0尚未开始时，用最多2个独立标注call为7条既有显式controller.final_intent补参考SQL。`original_missing_gold_sql`、`gold_revision_reason`、reference_version和原始失败证据均保留。之后重新只读执行并由两个新context逐项复核。补齐不能自动获得通过：最终sp03-06/23/25仍待确认。

原始pilot生成prompt后有修订，`generate-01-pilot-original-v1.txt`与`generate-03-pilot-original-v1.txt`恢复精确原始字节并匹配请求记录SHA，结果在`materials/original-prompt-recovery.json`。扩展③的v2prompt另存为`generate-03-expanded-v2.txt`，当前主prompt为后续显式L2 SQL要求的v3。查看实际调用要按request里的SHA定位prompt版本，不能用最新文件替代历史prompt。

## runner schema与会话约束

`data/cases-v6-reviewed.jsonl`每行一个候选，核心字段为：`id/family_id/task/category/input/scope/history/expected_behavior/allowed_interpretations/expected_bindings/missing_conditions/business_basis/reference_version/gold_sql/gold_result/auto_status/ai_status/human_review_status/scorable`。可评分开关是`scorable`，并非`scoreable`。

`expected_bindings`仅保留实体值谓词；日期、聚合和未解决条件分别在`expected_predicates/expected_aggregations/expected_unresolved_constraints`，原始记录在`raw_expected_bindings`。`expected_final_intent`为L2的controller.final_intent，否则为reference_intent。gold结果包含`columns/rows/table/row_count/truncated`；后续turn和candidate实际SQL结果按label在`checks/program-normalized-v4.json`定位。

L2 `controller`包含离线`hidden_goal/final_intent`、`allowed_user_supplements`、`expected_state_changes/max_clarification_followups`与可选`post_completion_turns`。补充map为`askedkey → {answer,value}`，只依据被测响应实际askedkey回答；允许语义等价字段别名，如`time_scope.current → time_scope/period/year`、`value/genre`、`rank_object/object`，但不能绕过不一致目标或一次泄漏整个隐藏目标。上限3次澄清followup，后续普通用户修改分别记turn。各题独立session。

①多候选题的初次gold为保留候选并澄清，通常main SQL为null，不将多个候选当作同时生效的筛选条件；不借hidden目标挑唯一候选。明确不存在题保留用户字面限制，即使结果空或COUNT0也不能偷偷改成近似存在值。结果比较需按查询语义、Decimal/NULL、集合及排名顺序；不强制SQL字符串或列别名完全相同。

冻结提案仅是准备阶段proposal。主流程正式冻结时应核对v6 SHA与评分协议SHA、固定实际D2/D3 commit和可公开配置指纹、做family元数据重合检查，再运行V0。历史根会话可能见过holdout，所有60题均为synthetic dev，不称独立泛化测试。
