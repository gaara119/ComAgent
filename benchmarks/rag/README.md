# 独立 RAG 评测

这套工具复用项目实际的解析、切片、检索、回答和引用校验代码，把“没有找到证据”和“找到之后没有答好”分开检查。评测不需要启动工作台、API 服务或数据库，也不会替换用户知识库。

## 1. 先了解评测对象

当前公开样本是 **32 道原创合成开发题、10 份 MD/HTML 文档**，涵盖单片段事实、多证据、跨文档、数字与期间、同名实体、无答案和续问场景。文档及标签的来源说明见 [fixtures/provenance.json](fixtures/provenance.json)，原文在项目的 `data/benchmark_fixtures/rag/`。

这些题不等同于原有 200 道 Agent 综合题。全部标签仍为 `pending_human_review`；原文哈希、章节和引句核验通过，也不代表人工已经确认答案语义。当前没有独立最终测试集，不应据此宣称生产准确率或未见文档泛化能力。

全库题使用全部允许文档，不向检索器提供正确文档提示。续问题保存历史，并提供作者显式标注的有效检索问题；它测试该问题下的检索，不测试 Agent 自动合并多轮条件。旧评测、旧保留集及其标签不会被这些入口加载。

## 2. 环境与最短运行路径

在项目根目录运行以下 PowerShell 命令。使用 Python 3.12；已有 `.venv` 时复用它，不要重新创建：

```powershell
py -3.12 -m venv .venv
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install -r requirements-runtime.txt
```

先运行纯 BM25，既不下载向量模型，也不调用收费 API：

```powershell
& $py -m benchmarks.rag.run_retrieval --strategies bm25 --embedding none --repeat 1 --output .runtime/rag-eval/bm25-r1
```

输出目录必须不存在。再次运行请换一个目录，例如 `bm25-r2`；程序拒绝覆盖已有预测和报告。索引写入独立工作目录，默认 `.runtime/rag-benchmark/`。

## 3. 三个入口各测什么

| 入口 | 实际操作 | 适合定位的问题 |
|---|---|---|
| `run_retrieval` | 只检索，不生成 | 证据未入片、候选召回不足、排序靠后 |
| `run_generation` | 跳过检索，用冻结参考证据生成 | 证据使用、引用、干扰和信息缺失诊断 |
| `run_end_to_end` | 实际检索后调用回答模块 | 检索到回答的工具链表现 |

默认回答模式为 `extractive`，只是展示真实原文及引用，不调用模型。它能检查工具衔接与来源保留，**不能把 `SUCCEEDED` 直接当作答案正确，也不能据此报告生成式忠实度或抗幻觉能力**。

无 API 的端到端检查示例：

```powershell
& $py -m benchmarks.rag.run_end_to_end --strategies bm25 --embedding none --answer-mode extractive --output .runtime/rag-eval/extractive-r1
```

## 4. 检索策略受控对照

| 策略 | 使用的技术 |
|---|---|
| `bm25` | 显式关键词基线，不初始化或查询向量编码器 |
| `dense` | 本地 BGE-M3 向量相似度 |
| `hybrid` | BM25 与向量候选通过 RRF 融合 |
| `hybrid_rerank` | 混合检索，加词项/短语覆盖率轻量重排与来源邻居补全 |

当前重排不是 Cross-Encoder。BM25 与其他组使用同一份冻结语料，通过开关控制通道，不通过删除模型文件模拟消融。缺少真实向量索引时，非 BM25 实验组会记录失败，不会静默回退后冒充向量实验。

四组对照需要先准备本地权重。现有下载脚本会联网下载并核验固定版本模型；这不是生成式模型 API 调用：

```powershell
$env:BGE_MODEL_PATH = "data/models/bge-m3"
& $py scripts/download_embeddings.py
& $py -m benchmarks.rag.run_retrieval --config benchmarks/rag/configs/retrieval-v1.json --output .runtime/rag-eval/four-strategies-r1
```

[configs/retrieval-v1.json](configs/retrieval-v1.json) 是可执行配置：四个策略、真实 BGE、Top-5、每通道 20 候选、500 字符切片、80 字符重叠、冷缓存、3 次重复。命令行参数可覆盖配置，例如加 `--repeat 1`。权重位于其他目录时加 `--model-path 该目录`。

也可以不用配置文件，显式运行：

```powershell
& $py -m benchmarks.rag.run_retrieval --embedding bge --strategies bm25 dense hybrid hybrid_rerank --repeat 1 --output .runtime/rag-eval/four-explicit-r1
```

所有组共用题面、来源、切片、Top-K 和评分协议。这里控制的是**每通道**候选数；Hybrid 可以融合两路候选，不宣称与单通道具有相同总候选量或计算成本。重复测量不增加独立题目数量。

## 5. 固定证据诊断与显式模型调用

固定证据模式提供三个条件：

| `--condition` | 输入给回答层的证据 |
|---|---|
| `reference` | 标签中的全部参考证据 |
| `reference_noise` | 参考证据，加允许来源内其他文档的干扰片段 |
| `missing_key` | 移除最后一条必要证据 |

例如先检查无 API 的固定证据工具链：

```powershell
& $py -m benchmarks.rag.run_generation --strategies bm25 --condition reference_noise --answer-mode extractive --output .runtime/rag-eval/reference-noise-r1
```

固定证据分支读取标签，因此只属于诊断，不计入正常系统的检索成绩，不能用它证明真实召回达到 100%。标签尚待人工确认时称为“参考证据”，不称为人工已审的充分证据。

生成式评测须先按项目根 README 在本地 `.env` 配置模型密钥，再显式选择 `llm` 并给预算。例如：

```powershell
& $py -m benchmarks.rag.run_generation --condition reference --answer-mode llm --max-model-calls 64 --deadline-seconds 600 --output .runtime/rag-eval/reference-llm-r1
```

这条命令会调用你配置的模型接口，**不是默认执行步骤**。同样可在 `run_end_to_end` 上选择 `--answer-mode llm`。当前交付的离线检查不代表已实测 DeepSeek 生成质量、神经重排或模型裁判。

预算规则：

- `--max-model-calls` 默认 0；生成式运行至少显式批准 2 次。
- 每道生成题在发送前保守预留最多 2 次物理调用：初次生成及必要的一次校验重生成。实际少用不自动释放预留，可能提前停止。
- 请求内调用上限为 2，每次模型调用只尝试一次，单次超时 60 秒。
- 剩余预算或时限不足时不发送新生成请求，保留相应未执行/失败记录，不自动增加额度。
- `--deadline-seconds` 默认 600；发送生成请求前还要留足最多 120 秒。它不是保证所有题都会完成的承诺。
- 失败与重生成同样统计；provider usage 缺失时总 token 保持未知，另保留观测子和，不能按零成本处理。未核验计费单价时金额留空。

## 6. 指标怎么读

| 指标 | 计算与边界 |
|---|---|
| Hit@5 | 前五片段中是否命中任一必要证据 |
| Recall@5 / 必要证据覆盖率 | 前五片段覆盖的唯一必要原文证据数 ÷ 全部必要证据数 |
| MRR@5 | 第一条命中片段的排名倒数 |
| nDCG@5 | 在全部允许语料片段上建立二元 chunk qrels，命中原文证据的片段相关；以全语料相关片段数计算理想排序 |
| `novelty_ndcg@5` | 单独保留的证据新增度诊断，避免把重叠片段的重复文本当成新增证据；不是标准 nDCG |
| 词面答案要点覆盖 | 检查答案是否出现标签中的文字变体；仅是机械诊断 |
| 拒答、误拒 | 依据真实 `EMPTY_RESULT` 状态；固定缺失证据条件单独解释，不混作正常问答成绩 |
| P50/P90、调用及 token | 根据实际记录汇总；usage 不完整时显示未知 |

检索命中要求文档、页码/章节和完整规范化引句匹配，不只看数字或页面重合。无答案题不进入正证据 Recall 分母；可回答题发生执行失败时保留在分母中并计零。标准 nDCG 的相关性标签来自冻结语料，不把参考证据条数直接当作相关片段数。

`--cache cold` 每题清空应用检索缓存；`--cache warm` 先预热同一查询，再计实际检索耗时，另存预热时间。两者都不清空操作系统页缓存或 ONNX 编码器会话，不等于整机冷启动。索引构建时间独立记录。

## 7. 查看产物、语义审核与同题对照

每个新输出目录包含：

- `report.md`、`summary.json`：统一报告、分母、错误分类与配对增减。
- `predictions.jsonl`：逐题问题、允许范围、排名、实际输入证据、回答、引用、trace 和错误。
- `results.csv`：便于逐题查阅的摘要。
- `manifest.json`：源码与语料哈希、Git 版本、实际命令、配置、模型、环境、缓存及预算。
- `quality.svg`、`errors.svg`、`transitions.svg`：检索覆盖、错误分类和同题迁移图。
- `failure-cases.json`：最多十个代表性记录；完整失败仍保留在逐题输出中。
- `review-template.json`：生成类运行的语义审核模板。

答案正确性、事实完整性、忠实性、引用语义支持分别判断，默认是 `not_verified`。复制 `review-template.json` 为另一文件后，保留原ID、策略、重复编号和 `prediction_sha256`；填写 `reviewer_kind`（`ai` 或 `human`）、`reviewer`（审核身份）、`notes`（依据与理由），并将该条 `review_status` 设为 `assessed`。四个分数分别是 `answer_correctness`、`faithfulness`、`citation_support`、`fact_completeness`，范围0–1；未判断的维度保留 `null`。这只提交本次回答的审核，不会批准题库标签或启用业务规则。完成后导入：

```powershell
& $py -m benchmarks.rag.review --predictions .runtime/rag-eval/extractive-r1/predictions.jsonl --assessments .runtime/rag-eval/extractive-r1/review-filled.json --output .runtime/rag-eval/extractive-r1/semantic-review.json
```

程序会核对预测内容的 SHA256 和题目/策略/重复编号，阻止将旧回答的审核套到新回答上；AI 与人工审核分开统计。导入审核不会自动批准原始标签。若审核对象是摘录模式，只能按摘录工具的性质解释分数，不能转述成生成式模型答案准确率。

在一个四组运行目录内，`summary.json` 已包含相对于 BM25 的同题迁移。比较两个独立运行目录时，使用：

```powershell
& $py -m benchmarks.rag.compare --before .runtime/rag-eval/four-strategies-r1 --after .runtime/rag-eval/four-strategies-r2 --before-strategy bm25 --after-strategy hybrid_rerank --output .runtime/rag-eval/paired-comparison.json
```

先按相同条件运行并生成第二个目录，再执行该命令。比较器检查数据、来源/索引、参数、缓存、题目范围和代码版本；改代码的修复对照需显式加 `--allow-code-change`，其他控制条件仍须一致。正、负和零收益都保留。固定证据诊断不能当作普通检索对照；开发集结果不作统计显著性或未见数据泛化宣称。

## 8. 本地回归

安装 pytest 后，可运行这一组无收费 API 的检查：

```powershell
& $py -m pip install pytest==9.1.1
& $py -m pytest tests/test_rag_benchmark_metrics.py tests/test_rag_benchmark_runtime.py tests/test_rag_benchmark_cli.py tests/test_rag_benchmark_reporting.py -q
```

CI 执行小规模离线回归，完整模型评测保持手动、显式预算运行。新数据集应使用同样的来源标注和家族/会话分组隔离规则，先审核标签，再扩量；不要把同一问题的改写当成多个独立最终测试样本。
