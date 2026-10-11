# 专项版本复现与自有增量恢复说明

本轮工作建立在 D2、D3 已完成的项目上。V0 是专项运行前的实际 D3 完成版本，不能称作历史 D2 原版。代码库基线为 `4c61e6a`；专项运行时的源码、配置及索引 SHA 以各版本 `runtime_eval/V*-code-snapshot.json` 为准。本轮已实际撤回 V2 并恢复 V1，见 [实际恢复记录](../runtime_eval/version-changes/V2/actual-restore-to-V1.json)；以下说明供复现和后续恢复时使用。

路径基准：下面的 `qa_agent/`、`scripts/`、`.env` 均从项目 `system/` 根目录开始；`runtime_eval/` 均从专项目录 `system/eval/experiments/after_d2_01_03/` 开始。例如恢复档案的完整项目内路径是 `eval/experiments/after_d2_01_03/runtime_eval/version-changes/V2/before/qa_agent/pipeline.py`，目标是 `qa_agent/pipeline.py`。报告中的 Markdown 链接以本说明所在目录为基准，解压后可直接打开。

## 复现实跑

先按项目 README 配置 Python 3.12 虚拟环境、已验证的模型 ID、本地只读数据库和已下载的索引。交付附件不含真实 `.env`、密码、模型权重或完整检索索引。具体模型参数、只读超时和索引路径见各快照的 `safe_config`；实际模型名称为 `deepseek-flash`。

造题和参考核验的实际命令及材料版本见 [准备阶段复现说明](preparation-reproduction.md)。固定专项题库 SHA 为 `42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1`。60 个原编号、49 个可评分与 11 个原标注待确认的分组保持不变。

各轮运行命令、服务重启证据、完整原始输出分别存于 `../runtime_eval/execution-logs/V0-001/`、`V1-001/`、`V2-001/` 和 `../runtime_eval/runs/`。运行器要求标签、源码、配置、评分协议和服务装载记录匹配正式冻结。直接用最终代码运行 V0 的冻结文件会被拒绝，不能把一次当前代码运行冒充过去版本。

使用新目录与新 run ID 复现，保留旧记录。需要重复实跑时，先创建新的真实快照、冻结记录及服务重启记录，避免复用旧 PID 记录。独立案例由运行器创建独立会话；不重发交付状态不明确的 POST。

## 仅恢复本轮自己修改的文件

V1 只改变 `qa_agent/clarify/prompts/intent_patch.txt`。原文与修改后全文、准确字节 SHA、diff 见 [V1 改动记录](../runtime_eval/version-changes/V1/change-record.json)。V2 改变 `qa_agent/pipeline.py`、`qa_agent/sql/validator.py`，新增 `qa_agent/sql/ratio_guard.py`。两份修改前文件与 V1 快照 SHA 的核验见 [V2 归档定位核验](../runtime_eval/version-changes/V2/archive-location-verification.json)，差异见 [V2 源码差异](../runtime_eval/version-changes/V2/source-delta.json)。

恢复前先核对当前文件 SHA 与最终快照一致；如果用户或 B 已另有修改，停止恢复受影响文件并人工合并。保持其他文件、数据库、题库、报告与日志原样。不得使用 `git reset --hard`、`git clean` 或递归删除目录。

- 恢复到 V1：从 `runtime_eval/version-changes/V2/before/qa_agent/` 精确复制 `pipeline.py` 和 `sql/validator.py` 到其对应源码路径。只有确认新增的 `ratio_guard.py` 仍是本轮准确字节时，才能移除这一单个自有文件。P3 保持 `intent_patch.after.txt` 的准确原文。
- 恢复到 V0：先恢复上述 V2 两份文件并处理新增 helper，再将 `runtime_eval/version-changes/V1/intent_patch.before.txt` 精确复制回 `qa_agent/clarify/prompts/intent_patch.txt`。
- 再次使用 V2：精确复制 V1 的 `intent_patch.after.txt` 与 V2 的 `after/qa_agent/` 中三份文件。其他业务文件、已确认规则与索引必须保持同一版本。

恢复后用 `runner.py snapshot` 写入新路径，与目标版本 `files` 和 `safe_config` 逐项核对；重新运行模块检查，再重启本项目拥有的 API/UI 服务。过去的成绩和报告不随恢复而更改。

## 独立观察归档补充

原始评测观察器只识别 UUID36 文件名，而 JsonLLM 实际写 UUID32，因此原自动 provider 归档数为 0。`scripts/archive_special_provider_evidence.py` 对真实 capture 的路径、trace、请求和字节 SHA 独立核验后复制到对应 turn。补充材料的命令及结果另存；原始 rejected 记录、checkpoint 和分数不改写。补充归档不是重新调用模型。

## 人工审核与保留集

本轮合成题和 D3 新协议仍待人工签字。查看统一表时将参考答案、实际系统回答、控制器限制与原冻结评分分别核对。发现标签错误后，应生成新的标签版本，对需要对照的各版本使用一致新标准重新评分；本轮未做此项重标或重评分。

D2 的 33 道保留题及 D3 的 18 道保留题不在本轮预测和 ZIP 中，按总计划留到 D5。元数据重合检查只提供已知 ID/family 的结果，不等于证明自然语言语义完全无重合。
