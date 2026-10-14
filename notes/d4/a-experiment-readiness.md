# D4 A线实验准备、实跑结果与核验

记录日期：2026-10-13（America/Chicago）。本文件保留准备、Docker阻塞恢复和最终运行情况。用户已明确允许本轮 AW、Chinook、多轮、跨源及必要失败回归继续调用现用 DeepSeek。早期Docker不可访问，Windows重启后数据库恢复；待B线最终回归结束，A线已独占、依次完成42次AW对照和180次SQL规模测试。没有改动冻结运行代码，原始结果不覆盖。

| 实验 | 已完成准备 | 应运行 | 本轮实际模型预测 | 当前状态 |
|---|---|---:|---:|---|
| AW全量schema／完整④子图对照 | 68表456字段目录；固定21道DEV；同一pipeline的两个schema mode；参考SQL逐条只读执行 | 21题×2组＝42次 | 42/42 | 两组主EX／旧EX均21/21；1次模型超时重试后成功，保留耗时和未知usage |
| Chinook数据规模效率 | 原始2240行、独立10000／100000行压测副本及目录；固定20道DEV；各副本各题gold重新执行 | 20题×3规模×3次＝180次 | 180/180 | 每规模主EX／旧EX均60/60；全部trace可用，0模型错误／0schema逃逸 |
| RAG数据规模效率 | 同20题、10／100真实页面、完整五文档搜索范围 | 120次 | 已有120次实跑证据 | 已运行；引用命中、正常返回和答案正确性分别处理，不能据此填AW／SQL成绩 |

本轮本地准备检查没有连接数据库，没有调用模型，没有读取保留题内容：见[本地预检JSON](../../eval/artifacts/d4/a-readiness-001/local-preflight.json)、[原命令代码](../../eval/artifacts/d4/a-readiness-001/local_preflight.py)、[真实命令与输出](../../eval/artifacts/d4/commands/20261014T021306807954Z-d4-a-local-readiness-001.json)。预检真实退出码为0。

Windows重启后的补充检查已真实连接现有数据库，只读执行、0模型调用、0数据写入。结果：原public11表行数与完整内容哈希均未变；两个既有副本分别10000／100000明细、2060／18540发票、孤儿明细均0；各11条真实FK已验证且指向同一副本；全部表行数与创建manifest一致；只读事务开启，实际statement timeout为5s。见[重启后核验JSON](../../eval/artifacts/d4/a-readiness-001/restarted-scale-check.json)、[实际只读查询代码](../../eval/artifacts/d4/a-readiness-001/restarted_scale_check.py)、[实际命令和输出](../../eval/artifacts/d4/commands/20261014T021534330221Z-d4-a-restarted-scale-check-001.json)。该检查退出码0，未创建或重建任何schema。

## 固定题目和数据规模

- AW只读[21道开发题](../../eval/datasets/d3/aw_schema_link.dev.v2.jsonl)，不读取／调用9道保留题。全量组提供全部68表、字段和真实关联；子图组经过现有召回、真实FK补全和模型剪枝。其后SQL生成、校验、修复、执行和判分相同。推断期间不传入gold SQL、gold结果或gold表名单；完成推断后才用标签统计召回率。两种中间消融组本轮未扩展。
- Chinook复用既有15道联表DEV与5道单表DEV，同一20题在三种物理schema中各运行3次；不同规模改变的是数据，不是题目数量。压测目录来自[已建立并校验的副本manifest](../../eval/artifacts/d4/sql-scale-data-001/manifest.json)，创建时记录孤儿明细为0、真实FK完整、原public内容哈希未变。**该历史校验不等于当前Docker再次可访问**。
- 20题中3题涉及扩容`invoice_line`，7题涉及扩容`invoice`，10题仅涉及未扩容维表，属于对照。部分固定年份筛选不保证扫描所有新增行。正式报告必须保留这项限制，不能把全部20题的速度变化统称明细扩容效果。
- 历史只读参考执行证据为[AW21条](../../eval/artifacts/d4/aw-gold-readonly-001/report.json)与[Chinook三规模60条](../../eval/artifacts/d4/sql-scale-gold-readonly-001/report.json)，均记录`model_calls=0`和`system_predictions=0`。它们是参考标签核验，不是系统消融或效率预测。

## 计时、成本和评分

[公共测量函数](../../scripts/d4_bench_utils.py)保留每次真实trace、独立端到端计时和所有模型尝试，区分NLU、值链接、④定位／剪枝、SQL生成、SQL执行、文档检索及答案组织。单独统计`llm`步骤耗时；嵌套步骤有重叠，不能将所有步骤相加得到总耗时。P50／P90采用线性插值，原始样本和数量保留。

AW比较同时报全链路输入token、SQL生成输入token、④自身模型输入token及实际模型尝试，不能漏掉④调用。两组使用同一配置，仅`aw_schema_mode`不同；题目成对交替运行顺序，避免总是同一组先运行。一次性本地embedding加载独立记录，不把冷启动只压给子图组。

Chinook各规模重新执行相同业务逻辑的参考SQL，仅调整物理schema；生成SQL若逃回public，主EX和旧EX均判失败。三次重复轮换规模顺序；两条代表性查询的只读`EXPLAIN ANALYZE`在正式运行阶段留档。

主EX按方案§5.2对连续数值保留两位小数，保留既有整数／计数／标识精确校验、全局列映射、题目要求的排序、行重复数及NULL区别；解释性额外字段须由真实目录和SQL来源证明。另报历史EX：非金额连续值仍精确比较，不将主EX的两位小数开关误传给历史比较。标准答案和历史输出不改写。失败全部计入EX分母；没有trace的runner异常不虚构零耗时，计时汇总记录可用trace数和零模型调用数。

## 已真实通过的模块测试

实际命令：

```powershell
.\.venv\Scripts\python.exe scripts/d4_run_checks.py --output eval/artifacts/d4/benchmark-contracts-001 tests/test_d4_benchmark_contracts.py -q
```

实际结果：**12 passed in 0.91s，退出码0**。证据为[命令](../../eval/artifacts/d4/benchmark-contracts-001/command.json)、[原始输出](../../eval/artifacts/d4/benchmark-contracts-001/output.txt)、[结果记录](../../eval/artifacts/d4/benchmark-contracts-001/result.json)。本轮额外回归验证了“缺少trace不等于零耗时”和“主EX两位小数通过时，历史精确比较仍可失败”。这12项模块测试不连接数据库或外部模型，不能替代42／180次真实实验。

## 已正式执行的具体命令

以下两命令均已实际执行且退出码0。运行前确认数据库可读、压测副本和只读权限仍在；两组共用代码／prompt冻结，在无其他D4模型测试竞争的时段依次运行。输出目录全新，真实命令、原始响应、provider返回和trace保存在现有证据目录，汇入同一份D4验收报告。

```powershell
.\.venv\Scripts\python.exe scripts/d2_command.py --name d4-aw-ablation-live-001 --directory eval/artifacts/d4/commands -- .venv/Scripts/python.exe scripts/d4_aw_ablation.py --output eval/artifacts/d4/aw-ablation-live-001
```

```powershell
.\.venv\Scripts\python.exe scripts/d2_command.py --name d4-sql-scale-live-001 --directory eval/artifacts/d4/commands -- .venv/Scripts/python.exe scripts/d4_sql_scale.py --scale-manifest eval/artifacts/d4/sql-scale-data-001/manifest.json --output eval/artifacts/d4/sql-scale-live-001
```

AW真实命令记录：[20261014T025054447415Z-d4-aw-ablation-live-001.json](../../eval/artifacts/d4/commands/20261014T025054447415Z-d4-aw-ablation-live-001.json)。SQL真实命令记录：[20261014T025829683897Z-d4-sql-scale-live-001.json](../../eval/artifacts/d4/commands/20261014T025829683897Z-d4-sql-scale-live-001.json)。文件名时间是UTC；本地记录日期仍为2026-10-13。

两个runner前后源文件哈希均相同。独立复核确认：42条AW和180条SQL的DEV标记、各题／规模重复数、主EX／旧EX、模型尝试数、provider已报告usage及未知usage状态全部对应。见[完成性核验](../../eval/artifacts/d4/a-readiness-001/completed-run-check.json)、[核验代码](../../eval/artifacts/d4/a-readiness-001/verify_completed_runs.py)、[真实核验命令](../../eval/artifacts/d4/commands/20261014T031335548910Z-d4-a-completed-runs-check-001.json)。核验本身0模型、0数据库连接，不修改原始结果。

AW的[完整报告](../../eval/artifacts/d4/aw-ablation-live-001/report.json)记录：两组EX均21/21；全量／子图的已回报输入token为832958／243694，减少约70.74%；SQL生成输入795212／48207，减少约93.94%，但子图还使用157741个选表输入token。端到端P50／P90为4747.472／5438.653ms与8172.456／15855.341ms。本次准确率没有提升，子图整体较慢；不能把输入减少写成提速。aw-07首次选表调用超时61417ms，重试成功；该次未回报usage，token合计并非完整账单，也不能将未知usage当已知0。全42请求和66次模型尝试保留，没有删掉异常尾部。

SQL的[完整报告](../../eval/artifacts/d4/sql-scale-live-001/report.json)记录：三个规模各60/60匹配，原／10k／100k端到端P50／P90分别3697.432／4213.883、3755.084／4219.519、3855.098／4247.997ms；SQL执行25.5／36.0、25.5／38.0、32.5／41.2ms。每规模63次模型尝试，共189次，0错误、0未知usage。各3条`EMPTY_RESULT`都是join-15的预期空结果，不是模型失败。每次都有真实模型调用，不含模型0调用的伪速度样本。

代表性只读`EXPLAIN ANALYZE`的执行时间原／10k／100k：索引invoice_id查找0.070／0.046／0.061ms；全明细SUM扫描0.388／1.613／15.441ms。原始计划见[explain-readonly](../../eval/artifacts/d4/sql-scale-live-001/explain-readonly/original-scan_aggregate.json)等六份文件。这是单次数据库查询执行时间，不是完整问答P50；固定题集含维表对照和固定年份筛选，不能泛化为任意问题／冷缓存／大并发的性能。

RAG已完成的实际数字使用[其独立实跑报告](../../eval/artifacts/d4/rag-scale-live-001/report.json)，并保留六次证据不足等限制。以上结果继续汇入主任务的一份D4验收报告。
