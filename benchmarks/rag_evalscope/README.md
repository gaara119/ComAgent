# EvalScope RAG 专项评测

本目录使用 **EvalScope 1.14.1 的官方 RAGAS 后端**评估历史真实 RAG 子任务。Agent 的 240 道综合开发回归仍由[原 Agent 评测程序](../agent240/README.md)负责，两者按实际运行、预测、问题与上下文哈希关联，复用同一批执行记录。

- [本次专项结果](results/actual-ragas-v2/report.md)：30 个已交付文档子任务，17 个有效 Faithfulness 分数，13 个未能评分。不是 240 道 Agent 的总体正确率。
- [原始框架分数](results/actual-ragas-v2/official-ragas-scores.json)、[实际调用与用量](results/actual-ragas-v2/execution.json)、[逐调用预算台账](results/actual-ragas-v2/budget-ledger.json)。
- [可移植输入](data/actual-rag-v1/)来自原始运行捕获，不重新造题、生成问答或运行保留集。**240 道 Gold 已全部人工审核**；MTEB 尚缺的是匹配检索协议的完整 corpus/qrels，与 Gold 审核状态无关。

## 评测边界

| 对象 | 实现与当前状态 |
|---|---|
| RAG 答案忠实度 | 官方 RAGAS `faithfulness`，判断回答中的陈述能否由当时实际提供的片段支持；已运行一次，保留所有空分数 |
| RAG 检索效果 | 官方 MTEB 配置已通过类型校验；尚未执行匹配本项目的完整检索实验，不输出 Recall@K、MRR 或 nDCG |
| Agent 最终任务 | 由原程序检查 SQL 结果、业务答案、路由、状态、工具与证据；不能把 RAG 子任务分数代替整题成功率 |

Faithfulness 不等于答案正确率：即使回答忠实于片段，也可能漏答用户问题；检索缺失的证据也不能由忠实度分数补足。原始生成请求中的**全部实际提供片段**作为上下文，不只挑最终引用片段。

本次可匹配到 30 个已交付子任务，来自 60 个以文档或跨源文档步骤为目标的配置预测。不同配置的可交付样本与有效评分覆盖不相同，不能仅比较各自均值就宣称因果提升。

## 独立安装评测环境

在项目根目录执行，主运行环境 `.venv` 保持独立：

```powershell
py -3.12 -m venv .runtime/evalscope-env
.\.runtime\evalscope-env\Scripts\python.exe -m pip install -r requirements-evalscope.txt
.\.runtime\evalscope-env\Scripts\python.exe -B -m benchmarks.rag_evalscope.validate --output .runtime/evalscope-validation.json
```

依赖锁定 EvalScope 1.14.1、RAGAS 0.4.3、MTEB 2.26.33 等版本。`langchain-community==0.4.1` 是实际验证的兼容依赖：0.4.2 删除了 RAGAS 0.4.3 在导入时仍引用的模块。校验命令会检查官方配置、实际后端导入、客户端构造与指标初始化，不调用模型。

## 复现与复用

只重算已有 Agent 记录，复用已经完成的专项评分，不发生模型费用：

```powershell
.\.venv\Scripts\python.exe -B -m benchmarks.agent240.evaluate --bundle benchmarks/agent240/data --rag-evalscope-results benchmarks/rag_evalscope/results/actual-ragas-v2/agent-binding.json --output .runtime/agent240/with-existing-ragas
```

如需**重新运行付费的 RAGAS 裁判**，先在本地 `.env` 配置 `LLM_BASE_URL`、`LLM_MODEL=deepseek-flash`、`LLM_API_KEY`；再显式执行：

```powershell
.\.runtime\evalscope-env\Scripts\python.exe -B -m benchmarks.rag_evalscope.run --inputs benchmarks/rag_evalscope/data/actual-rag-v1 --output .runtime/ragas-new-run --run-judge
```

输出目录必须为新目录。未提供 `--run-judge` 时只写就绪记录，不发送请求。运行器仅允许已核对哈希的 30 个子任务及五份公开/示例文档；不发送私有会话正文、客户结果表、审核附件、保留题或密钥内容。

预算保护位于实际 HTTP 发送边界，所有框架重试共用最多 120 次物理调用、从第一次真实调用起 20 分钟、最后 2 分钟不发新请求、最多 4 个并发。首次真实探针串行，失败后阻断后续发送；缺少 usage 的请求保守预留，不按零成本处理。Faithfulness 不需要 embeddings 请求，守卫拒绝该接口。

**参数实测差异：**官方 EvalScope 1.14.1 的 `_build_llm()` 未将配置的 `max_tokens=4096` 和 `temperature=0` 传入 RAGAS 工厂；本次实际请求为 `max_tokens=1024`、`temperature=0.01`、`top_p=0.1`，HTTP 守卫仍将最大输出限制为 4096。13 个输出被截断。本次没有修改参数后重跑；未来修复时必须先校验实际发送体，再建立新的结果版本，不覆盖此次记录。

`export.py` 供持有原始开发运行档案时重新导出输入；普通仓库复现直接使用已随仓库保存的 `data/actual-rag-v1`，不依赖未提交的历史档案目录。

## 指标与证据保护

`bridge.py` 依次核对 Agent 响应、运行配置、生成捕获、问题、上下文和 RAG 回答哈希，再关联官方逐样本分数。官方分数文件、原始请求与响应不改写；JSON `null` 或官方 NaN 作为未评分保存，不补零，也不算通过。无效类型、超界分数和串用其他运行的结果会被拒绝。

当前缺项包括完整 MTEB corpus/qrels/排名、裁判人工校准、匹配样本的答案正确率与证据位置人工核验。费用单价未核验，只报告真实调用、缓存与 token。

框架依据为 [EvalScope v1.14.1 RAGAS 后端](https://github.com/modelscope/evalscope/blob/v1.14.1/docs/en/user_guides/backend/rageval_backend/ragas.md)与 [MTEB 后端](https://github.com/modelscope/evalscope/blob/v1.14.1/docs/en/user_guides/backend/rageval_backend/mteb.md)。精确源码版本和来源哈希见[official-sources.json](official-sources.json)。
