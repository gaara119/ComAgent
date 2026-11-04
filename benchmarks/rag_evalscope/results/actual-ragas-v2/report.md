# EvalScope RAGAS 单次专项实测记录

本次对历史真实运行中可追溯的 **30 个已交付 RAG 子任务**执行一次官方 RAGAS `faithfulness` 评测。原 Agent 综合开发集为 240 道，Gold **240/240 已完成人工审核**。本次未生成新的 Agent 预测，未重跑 240 题，也未运行保留集。

## 1 实测结果与分母

| 项目 | 实际结果 |
|---|---:|
| 文档或跨源文档步骤目标的历史配置预测 | 60 |
| 可绑定实际提供片段与已交付回答的专项样本 | 30 |
| 官方框架输出行数 | 30 |
| 有效 Faithfulness 分数 | 17 |
| 未能评分、保留空值 | 13 |
| 评分覆盖 | 17/30 = 56.67% |
| 有效子集的 Faithfulness 均值 | 0.8873 |

**0.8873 仅是 17 个有效子任务的平均陈述支持比例，不是 30 个样本或 240 道综合题的准确率。** 13 个空值没有补零、没有改成通过，也没有隐藏。Faithfulness 核对回答中的陈述能否由当时提供的片段支持，不判断问题是否完整回答、Gold 是否匹配、检索是否召回全部相关证据。

| 历史配置 | 专项输出行 | 有效评分 | 未评分 | 有效子集均值 |
|---|---:|---:|---:|---:|
| final200 / BASE | 10 | 5 | 5 | 0.7833 |
| final200 / FULL | 11 | 5 | 6 | 1.0000 |
| legacy40 / BASE | 5 | 4 | 1 | 0.7917 |
| legacy40 / C1 | 4 | 3 | 1 | 1.0000 |

各配置的已交付样本与有效评分覆盖不相同，本表不能用于宣称配置间准确率提升或因果消融收益。Agent 的业务正确率和完整任务成功率仍以原评测程序的有效分母分别报告。

## 2 框架与实际参数

使用 EvalScope **1.14.1**、官方源码版本 `9d298b839375e735fbbef992b4042e0852d0b8aa`、RAGAS **0.4.3**；兼容依赖为 `langchain-community==0.4.1`。主应用虚拟环境未改动。官方配置、后端实际导入、LLM/embedding 客户端构造和 Faithfulness 初始化检查见[运行前校验](official-runtime-validation.json)。

配置写入 `max_tokens=4096, temperature=0`，但是官方 EvalScope `_build_llm()` 没有向 RAGAS 工厂转发这两个字段。**52 次实际请求均为 `deepseek-flash`、`max_tokens=1024`、`temperature=0.01`、`top_p=0.1`。** HTTP 守卫的 4096 上限不代表实际发送了 4096。

13 次响应的 `finish_reason=length`，框架报告 13 个 `IncompleteOutputException` 并输出空分数；其中拆句阶段截断 8 次、证据核对阶段截断 5 次。保留这项接口参数传递问题和无效评分，没有修改中途配置或为了提高分数重跑。

最早一次启动记录保存在[actual-ragas-v1](../actual-ragas-v1/execution.json)：依赖导入失败、0 次真实调用、0 个分数。定位为 RAGAS 引用已被 `langchain-community` 0.4.2 删除的模块；独立环境固定 0.4.1 并通过本地检查后，才执行本次唯一的真实专项批次。

## 3 实际成本与耗时

| 项目 | 实测 |
|---|---:|
| 本次专项物理模型调用 | 52 |
| HTTP 守卫结算成功 | 52 |
| HTTP/传输失败 | 0 |
| 实际输入 token | 56,963 |
| 缓存命中输入 token | 35,968 |
| 缓存未命中输入 token | 20,995 |
| 实际输出 token | 33,815 |
| usage 缺失调用 | 0 |
| 单次物理模型请求耗时 P50 | 3.724 秒 |
| 单次物理模型请求耗时 P90 | 5.671 秒 |
| 首次发送至最后结算跨度 | 204.468 秒 |

P50/P90 使用全部 52 次实际物理请求耗时，按 `(n−1)×p/100` 做线性插值；它们**不是 Agent 端到端延迟**。52 次请求包括 30 次拆句和 22 次证据核对；不能把 `52−30` 当成重试次数。SDK 没有输出独立的 attempt-ID，重试次数未单独核验；所有物理请求及截断输出都已计入 token 与耗时。

本次专项账本与历史 Agent 的 755 次模型调用分开保存。计费单价未核验，因此金额标记为未核验，不以 token 增幅代替费用增幅。实际预算限制为最多 120 次物理调用、20 分钟、最多 4 个并发，最后 2 分钟不发新请求；首次真实探针串行，失败即阻断后续发送。本次 52 次调用完成后停止，没有追加一轮。

## 4 原始证据与复现

- [官方逐样本分数](official-ragas-scores.json)：直接连接八个官方批次输出中的原始行，不改指标名或数值；原批次 `batch-000_score.json` 至 `batch-028_score.json` 保留。
- [运行绑定清单](agent-binding.json)：绑定原 Agent 预测、运行配置、真实生成捕获、问题、完整实际片段和回答哈希，并记录框架结果、执行记录与台账哈希。
- [逐调用原始请求、响应和预算结算](budget-ledger.json)：不保存鉴权 Header；捕获内容限定为已核对的公开艺术家资料与示例指标手册。
- [执行汇总](execution.json)、[参数与分数诊断](runtime-diagnostics.json)、[本地 20 项回归](bridge-regression.junit.xml)。两次运行的原始stderr包含本机用户目录，只在本地保留，不上传公共仓库；错误类型及截断统计保留在参数诊断中，见[发布范围说明](../publication-scope.json)。
- [可移植原始输入](../../data/actual-rag-v1/)与[复现步骤](../../README.md)。输入是历史真实生成请求中的全部片段，不是按 Gold 挑选或仅保留支持回答的最终引用。

Agent 复用此次结果：

```powershell
.\.venv\Scripts\python.exe -B -m benchmarks.agent240.evaluate --bundle benchmarks/agent240/data --rag-evalscope-results benchmarks/rag_evalscope/results/actual-ragas-v2/agent-binding.json --output .runtime/agent240/with-existing-ragas
```

此命令只校验并复用现有结果，不发生模型调用。若重新运行裁判，必须使用新的输出目录并显式添加 `--run-judge`；相关命令见专项 README。本次之后没有再调用模型修正截断结果。

## 5 已验证与未验证

已验证：官方后端真实执行、52 次实际调用及完整 usage、30 行官方输出、17 个有效分数、13 个未评分样本、原 Agent 与专项证据的哈希绑定；本地桥接及预算测试 **20/20 通过**。

尚未验证：MTEB 的完整检索执行及 Recall@K/MRR/nDCG、裁判人工校准、该子集的答案正确率与引用位置人工核验、真实计费金额。MTEB 已完成官方配置类型校验，缺少匹配冻结检索协议的完整 corpus/qrels 与排名证据；**不是 240 道 Gold 未审核**。不能把当前文档覆盖比例改名为检索召回率，也不能把这次部分有效的 Faithfulness 当成完整 RAG 质量结论。

原框架依据：[EvalScope v1.14.1 RAGAS 后端](https://github.com/modelscope/evalscope/blob/v1.14.1/docs/en/user_guides/backend/rageval_backend/ragas.md)、[官方实现](https://github.com/modelscope/evalscope/blob/v1.14.1/evalscope/backend/rag_eval/ragas/task_template.py)。
