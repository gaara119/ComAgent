# ①③真实专项 runner / scorer

此目录负责真实 `POST /api/chat` 执行、会话隔离、按当前卡片补充、不可重放断点和离线评分。代码不读取 holdout，也不调用造题/审核模型。最终准备验证记录在 `offline-check-04.json`：15项关键检查通过，69个主任务/后续修改参考SQL AST可解析，13个已保存后续结果可加载；API预测、provider调用和数据库查询均为0。这些检查不是被测系统成绩。

所有命令在 `E:\中国电子杯-赛题八\system` 用既有 `.venv\Scripts\python.exe` 执行。标签使用 `data/cases-v6-reviewed.jsonl`，SHA为 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`：60条合成dev，49可评分、11待确认，全60人工审核仍pending。正式V0由root冻结与启动，本目录准备阶段没有运行V0。

## 零预测准备检查

```powershell
.\.venv\Scripts\python.exe eval/experiments/after_d2_01_03/runtime_eval/runner.py check --cases eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl
.\.venv\Scripts\python.exe eval/experiments/after_d2_01_03/runtime_eval/offline_check.py --cases eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl --post-results eval/experiments/after_d2_01_03/checks/program-normalized-v4.json --output eval/experiments/after_d2_01_03/runtime_eval/offline-check-05.json
```

输出路径必须新建，不能覆盖历史证据。若另做检查请递增路径编号。

## 正式冻结与服务装载

全部业务代码、prompt与评分代码完成后生成安全快照；每次新版本都重新执行，并使用新输出路径。

```powershell
.\.venv\Scripts\python.exe eval/experiments/after_d2_01_03/runtime_eval/runner.py snapshot --output eval/experiments/after_d2_01_03/runtime_eval/V0-code-snapshot.json
```

快照包含qa_agent/api全部源码、独立prompt/config、目录/别名/值索引文件SHA、runner/scorer源码、Git head/status和白名单运行配置（model、model path、timeout、attempt cap等）。不复制或散列真实`.env`，不保存密码、DB URL、API key。变更任何快照文件都会阻止run。

root正式冻结JSON示例；文件路径相对该JSON父目录。SHA必须填实际值，proposal状态不能通过gate。

```json
{
  "status": "frozen",
  "label_file": "../data/cases-v6-reviewed.jsonl",
  "label_sha256": "42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1",
  "scoring_protocol_file": "../reports/scoring-protocol-draft.md",
  "scoring_protocol_sha256": "实际协议文件SHA256",
  "code_snapshot_file": "V0-code-snapshot.json",
  "code_snapshot_sha256": "实际快照文件SHA256"
}
```

服务须实际重启并启用观测环境变量 `LLM_CAPTURE_DIR`，建议目录 `eval/experiments/after_d2_01_03/runtime_eval/provider-captures/V0-<runid>` 或 `.runtime/provider-captures/V0-<runid>`。root提供 `V0-restart-record.json`，至少含 `restarted_at`、实际`pid`、`files_sha256`（值来自code snapshot的同名字段）。runner同时验证`/health`实际装载的单表和多表SQL prompt哈希；其余澄清/链接prompt使用完整重启记录。若将来health提供完整prompt_files哈希，runner支持直接比较而无需重启证明。

## 正式V0调用

```powershell
.\.venv\Scripts\python.exe eval/experiments/after_d2_01_03/runtime_eval/runner.py run --cases eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl --freeze eval/experiments/after_d2_01_03/runtime_eval/V0-freeze.json --restart-record eval/experiments/after_d2_01_03/runtime_eval/V0-restart-record.json --version V0 --base-url http://127.0.0.1:8000 --timeout 360 --run-dir eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001 --post-results eval/experiments/after_d2_01_03/checks/program-normalized-v4.json --output eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-scores.json
```

V1/V2更换version、freeze、restart record、run目录和score输出；全部用相同冻结标签。HTTP无隐藏重试；provider的每call retry/整request cap仍由真实业务服务持有并在日志记录。每case新建含版本+UUID的session；真实history先实际执行用户消息，无法伪造assistant历史。

当前真实接口为 `clarification.{clarification_id,intent_version,issues,options,resume_supported}` 与 `metadata.clarify`。只有结构化当前field/id能回答；支持time_scope.current/time_scope/period/year等同义键。用户补充只从允许离线补充取一项，message是用户answer，选择按钮message是当前真实label，choice_id是当前stable id。每次只回答一个被问key；同卡多个key不同时提交。多候选必须同时校验用户允许的column与value，同值跨客户国家/账单国家未获明确回答时不选择。卡ID和版本陈旧、未知询问、不一致补充、不得泄漏其它缺项的组合answer，都保存controller_unanswered。澄清最多3次；未真实完成澄清就不提交后续隐藏修改。post_completion_turns提交实际message，expected_intent/gold_sql从不发送。

## 原始证据与恢复

`runs/<version-run>/run-manifest.json`记录冻结SHA、完整安全快照、实际health、重启证明、调用上限。每case下`checkpoint.json`及`turns/NNN/request.json`、`response.raw.json`保存真实请求、响应、延迟、错误、trace、steps、SQL/table/state。API返回的每个llm step若有合法provider_capture，复制到该turn的`provider/`，`provider-evidence.json`保存源/副本SHA与trace对应。缺少capture或usage保留缺口，不能猜token或费用。只统计真实API内的provider步，不混入离线生成和审核调用。

中断后同version/freeze/run目录加`--resume`。已保存response先离线恢复状态；从不重复POST。request已写但没有response时无法知道服务器是否已应用，自动标`ambiguous_delivery`并跳过该case，不重放旧卡/历史。已有网络异常也不重试。独立新run目录用于重新试验；若要重试受影响案例须保留旧run并由root明确安排新的固定版本完整运行。

```powershell
.\.venv\Scripts\python.exe eval/experiments/after_d2_01_03/runtime_eval/runner.py run --resume --cases eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl --freeze eval/experiments/after_d2_01_03/runtime_eval/V0-freeze.json --restart-record eval/experiments/after_d2_01_03/runtime_eval/V0-restart-record.json --version V0 --base-url http://127.0.0.1:8000 --timeout 360 --run-dir eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001
.\.venv\Scripts\python.exe eval/experiments/after_d2_01_03/runtime_eval/runner.py score --cases eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl --run-dir eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001 --post-results eval/experiments/after_d2_01_03/checks/program-normalized-v4.json --output eval/experiments/after_d2_01_03/runtime_eval/runs/V0-001-rescore-02.json
```

## 评分解释

真实table对已保存gold_result使用现有`eval.metrics.compare_results`。金额/连续量按Decimal原值精确比较，无舍入；数值字符串只在原始数值类型或参考SQL证明数值类型的列转换，NULL、COUNT0和空表保留区别。排名保留行顺序，允许全局一致的列映射与合理列别名。列语义另外受qualified SQL AST证明约束，不能凭同值列交换通过语义。

绑定要求原始column/operator/value集合；多候选初次只评候选保存和暂停，gold_sql为空不伪造唯一目标；明确不存在值允许SQL保留字面值，不要求索引将未知值resolved。语义证明对真实目录做AST字段限定并统一合法alias/投影alias，比较全部筛选、日期、CASE、聚合、对象、分组、排序、limit；仅允许实际未截断且完整参考行数小于配置cap时消去程序添加的默认limit。等价SQL若无法自动证明，标`AI_pending`。成功结果+已证明AST才自动判complete；SQL错误/服务错误/超时/未实现/未完成计失败。L1不能只有level字段，还须成功、声明默认和实际可切换卡。

按总60、可评分49和待确认11同时报告；待确认可保存输出、诊断，但无binary correct。各task/category列confirmed correct/分母、自动失败、AI_pending与coverage；绑定、初始分级、必要澄清召回、误澄清、有效澄清、条件保持和过度纠错分开统计。Wilson区间是固定合成dev上自动确认正确下界的描述，不是独立泛化/显著提升结论。post_completion逐turn评分，缺后续gold_result不得退回主任务gold_result。
