# 专项结束后 D2 开发集回归：命令与评分核对

本文件只记录实际执行过的离线入口、加载器和开发视图核对，以及建议使用的预测命令。编写本文件时没有调用问答 API、模型或数据库，没有读取保留题。预测是否完成及成绩必须以主流程随后保存的原始 `report.json`、`responses.jsonl` 和实际命令记录为准。

## 已实际核对的入口和视图

在 `system` 项目根目录实际执行 `.\.venv\Scripts\python.exe -B -m eval.run_eval --help`，退出码为 0。已有 SQL、鲁棒题加载器与 RAG 加载器均正常载入下面三份修正版视图；所有条目的 `split` 均为 `dev`，编号无重复，同源题没有跨分组。详细结果、源码 SHA、原始帮助输出见 [离线核验记录](d2-regression-cli-check.json)。

|分组|独立开发视图（从 system 根目录算起）|实际题数|已校验的人工接受记录|仍待人工核对|
|---|---|---:|---:|---:|
|SQL|`eval/artifacts/d2-final/review/sql-dev-v1.jsonl`|35|34|1|
|鲁棒|`eval/artifacts/d2-final/review/robust-dev-v1.jsonl`|21|20|1|
|RAG|`eval/artifacts/d2-final/review/rag-dev-view.jsonl`|21|0|21|

“已校验”表示现有接受记录及其内容哈希有效，不是本次重新签字。SQL 修正版的一道 NULL 排序题、鲁棒修正版的一道指代题和全部 RAG 视图尚待人工确认，所以回归继续显式使用 `--draft-gold`。本次离线检查没有改变任何审核状态。

三份视图 SHA256 分别为：

- SQL：`7b4c18f203ce0d88f38837f0c788cbcff142b559dc70d3f281990a2d47175f35`。
- 鲁棒：`1d6c7732b5196e7146e3b3f01fe4f9ccb24ad354c6b20776631192c605d213f7`。
- RAG：`12b8cc7de87ea73bc60a2e9b7d527d0721956ef1bf4256ccf6a70331a7f57f63`。

## 可直接使用的命令

下面三条是待主流程执行的预测命令，没有在上述离线检查中运行。工作目录为 `system`，API 采用现有 `127.0.0.1:8000`，复用已装载的模型、索引和数据库。不导入、重建或更改数据。最终保留版本必须先冻结并确认 API 已装载，再按顺序运行。

```powershell
.\.venv\Scripts\python.exe -B -m eval.run_eval --suite nl2sql --dataset eval/artifacts/d2-final/review/sql-dev-v1.jsonl --split dev --draft-gold --run-id special-final-sql-001 --base-url http://127.0.0.1:8000 --timeout 240 --output eval/experiments/after_d2_01_03/regression/final/sql-001
```

```powershell
.\.venv\Scripts\python.exe -B -m eval.run_eval --suite robust --dataset eval/artifacts/d2-final/review/robust-dev-v1.jsonl --split dev --draft-gold --run-id special-final-robust-001 --base-url http://127.0.0.1:8000 --timeout 240 --output eval/experiments/after_d2_01_03/regression/final/robust-001
```

```powershell
.\.venv\Scripts\python.exe -B -m eval.run_eval --suite rag --dataset eval/artifacts/d2-final/review/rag-dev-view.jsonl --split dev --draft-gold --run-id special-final-rag-001 --base-url http://127.0.0.1:8000 --timeout 240 --output eval/experiments/after_d2_01_03/regression/final/rag-001
```

若目录已存在 `report.json`，既有入口会拒绝覆盖，改用新的编号和新输出目录，保留失败尝试。RAG 会把 `run-id` 放入会话编号；每次真实新跑必须使用新的 `run-id`，避免继续旧会话。不要省略 `--dataset`：默认值会选含保留题的原始题库，即使指定 `--split dev` 也会先读完整原文件。本轮只传上述独立开发视图，不使用 `--allow-holdout` 或 `--frozen-tag`。

每条实际运行另存命令、时间、退出码和 stdout/stderr。输出目录保留 `report.json`、`report.md`、`responses.jsonl`；RAG 还生成 `human_review.md`。`COMPLETED` 仅表示已完成预测和自动统计；SQL/鲁棒必须分别确认为 35/35、21/21 次预测，RAG 为 21/21；`holdout_prediction_count` 必须为 0。`READINESS_ONLY`、中止、结果缺失或分母不符均不能填为实跑通过。

## 现有真实评分口径

SQL 和鲁棒题使用 `eval/run_eval.py` 与 `eval/metrics.py`。只有 `SUCCEEDED` 或 `EMPTY_RESULT` 且带结果表的响应才比较结果。追问、API 错误、超时和格式错误仍占所选题分母。原 D2 EX 在所有行使用同一全局列映射、保留重复行；有序题按标签核对顺序，无序题比较带重复计数的结果。连续数值依照题库列类型按两位小数比较，`integer_columns` 声明的计数或编号保持精确，NULL、0、空表与空字符串保持区别。`--draft-gold` 产生的比例字段是 `exploratory_ex`，不能写成已审核正式成绩。

这套 EX 只证明该数据上的结果一致。JOIN、过滤、分组、期间或口径写错却碰巧得到相同值时，也可能结果通过。它不替代本轮专项评分器的精确 Decimal 和 SQL AST 语义合同核验。报告分别给原 D2 回归 EX 与专项语义判断，不合并两种数值比较政策。

RAG 使用 `eval/d2_rag_eval.py`、`eval/rag_metrics.py` 和原实际索引。三份视图中 RAG 有 20 道可回答题、1 道不可回答题。`hit_at_5` 为最终前五候选中的金标 PDF 物理页命中，非 PDF 采用片段；它的分母是 20，不能把不可回答题加入检索命中分母。`exact_gold_quote_hit_at_5` 另报完整金标原文片段命中诊断。`insufficient_handling` 分别检查那 1 道不可回答题的状态和无证据行为。引用所属文档及 `evidence_id` 对应实际索引块的文档、页码、章节、文字、bbox 真实性，是 21 题的机械诊断。

RAG 答案表面子串匹配只是辅助诊断；出处真实也不足以单独证明整句的对象、年份、单位和上下文正确。入口明确保留 `human_correctness`、`human_faithfulness` 为待人工核对，`answer_human_review_count` 为 0。报告不得把机械检查比例冒称完整答案正确率或引用语义忠实率。

## 本次交付构建器的检查

专项报告构建器仅接收明确报告路径，不自行运行预测。它核对三组报告的状态、`suite`、`split=dev`、实际所选/预测题数、保留预测为 0、开发视图 SHA 和草稿标记，并要求实际命令记录存在；未完成报告即使文件已存在也会标为证据不足。ZIP 显式附六个既有评测源码及三份修正版开发视图，不附原始混合题库。正式统计和最终版本来源以主流程提供的实跑文件为准。
