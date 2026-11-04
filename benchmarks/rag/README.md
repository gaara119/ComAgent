# RAG评测模块

当前项目评测采用原40题和原200题，合计240个综合开发题条目。后补32道合成题、配套虚构文档和旧结果已删除，不再是可运行基准或现行成绩。

- [原240题评测入口与使用说明](../agent240/README.md)
- [七维评测报告](../agent240/results/240-seven-dimensions-v1/report.md)
- [项目运行与环境说明](../../README.md)

## 当前评测命令

在项目根目录、已准备Python 3.12依赖的环境执行：

```powershell
.\.venv\Scripts\python.exe -m benchmarks.agent240.evaluate --bundle benchmarks/agent240/data --output .runtime/agent240/my-run
```

它校验已有题库、历史预测和审核绑定，再重新计算指标；不调用API、数据库或模型裁判。每次指定一个新的输出目录。480条预测来自两批各自的历史版本，不等于当前版本重新跑完240题。

## 保留的通用RAG工具

| 模块 | 作用 |
|---|---|
| `dataset.py` | 来源型标签模型、分组隔离、文档哈希与原文引句定位校验 |
| `metrics.py` | 有完备标签时计算检索覆盖与排序；将词面诊断和语义审核分开 |
| `run_retrieval.py` | 只调用实际检索工具，不生成回答 |
| `run_generation.py` | 使用明确标记的固定参考证据作回答层诊断，不计入正常检索成绩 |
| `run_end_to_end.py` | 实际检索后调用回答及引用校验 |
| `review.py` / `compare.py` | 绑定真实预测的审核导入及同题对照 |

这些通用入口**没有默认题库，必须显式传入`--dataset`**。新数据须符合`Dataset`模型，有真实文档清单、哈希、物理页或章节、必要引句和审核状态。没有完整Top-K与相关性标签时，不能给240综合题硬算Recall@K、MRR或nDCG。模块接口帮助可通过`python -m benchmarks.rag.run_retrieval --help`查看；已删除数据及其退役版本会在索引与模型配置读取前被拒绝，见[退役登记](deprecation.json)。

`extractive`模式只摘录真实原文，不能将成功状态当成生成式答案正确。生成式运行仍须显式选择`--answer-mode llm`并给调用上限；当前240题离线重计分不走该分支。

## 无API模块回归

安装项目测试依赖后，在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_rag_benchmark_metrics.py tests/test_rag_benchmark_runtime.py tests/test_rag_benchmark_reporting.py tests/test_rag_benchmark_cli.py tests/test_agent240_metrics.py
```

CLI集成测试只建立临时单题夹具，验证读写、来源和零模型调用边界；它不是新增正式题库，也不产生RAG能力成绩。[CI配置](../../.github/workflows/rag-eval.yml)在单元回归后重算原240题证据包。
