# D3 A 线实施与实测记录

本记录对应总计划 D3 A 的四项。实际工程、模块运行和已接入共享API的21题真实端到端运行已完成；数据库标准题仍为 `pending_human_review`，本记录不代替最终人工核对。表定位与NL2SQL EX分别记录，不把只读gold或schema模块结果混入实际问答成绩。

| 原清单要求 | 实施 | 已实际运行的证据 | 结果与限制 |
|---|---|---|---|
| 导入 lorint 完整版 AW，2小时失败才兜底 | 新增隔离的 `docker-compose.aw.yml`；微软官方 ZIP + lorint 固定提交 DDL/Ruby 转换；复用现有 PostgreSQL 16 镜像，新服务、新 volume、55433 | [导入核验](../../eval/artifacts/d3/a/bootstrap-result.json)、[完整导入 stdout](../../eval/artifacts/d3/a/import-full-oltp.txt)、[命令和耗时](../../eval/artifacts/d3/a/commands.jsonl) | 完整版可用：68业务 BASE TABLE、5 schema、90 FK、121317销售明细。没有启用LT，也没有重导、重建、删除Chinook。只读账号 `qa_reader`，默认只读、5秒超时，实际无写表权限见 reader-audit。 |
| 对 AW 跑 build_catalog.py 并生成中文描述 | 现有入口增加 `--db-id adventureworks`，转到新 AW 实现；只读 introspection + 现有 DeepSeek 真实调用，断点缓存可续跑 | [最终实际目录](../../data/catalog/adventureworks.yaml)、[LLM/结构导出实测汇总](../../eval/artifacts/d3/a/catalog/summary.json)、[账号只读核验](../../eval/artifacts/d3/a/catalog/reader-audit.json) | 68表456列均有中文说明。共71模型尝试、83678实际total tokens；有供应商漏列失败及UUID/numeric导出问题，已保留原失败并修复。3处中文说明按真实字段/外键完成两遍AI纠正；人工最终抽查仍待完成。 |
| schema_linker.py 双路召回 + RRF + Steiner补全 | 复用已验证本地BGE-M3 ONNX int8，表Top8/列Top20投票/真实值提示三路RRF；真实FK图按连通分量求Steiner；问题原文维度分别召回，保留每维度一个定位候选 | [源码](../../qa_agent/sql/schema_linker.py)、[最终模块结果](../../eval/reports/d3-aw-schema-dev-final/report.json)、[逐题真实候选/要素](../../eval/reports/d3-aw-schema-dev-final/responses.jsonl)、[真实桥接](../../eval/reports/d3-aw-schema-dev-final/actual-steiner-bridge.json)、[最终7测试stdout](../../eval/artifacts/d3/a/schema-module-tests-final.txt) | 21开发题，mean table recall100%、21/21全gold表召回；mean precision14.49%、平均10.95候选、59.29ms（此轮）。初版98.10%及中间失败输出均保留。没有D4 LLM剪枝，不把这些表定位数字当作SQL EX。 |
| 30 AW题，标注gold表/SQL，刻意干扰项 | 新增30个互不跨split的家族；21开发、9保留。30 SQL已在只读账号真实执行，SQLGlot核验目录及表标签一致性 | [原v1题库与元数据](../../eval/datasets/d3/aw_schema_link_manifest.json)、[v2修订元数据](../../eval/datasets/d3/aw_schema_link_v2_manifest.json)、[开发v2](../../eval/datasets/d3/aw_schema_link.dev.v2.jsonl)、[开发实际gold多表例](../../eval/artifacts/d3/a/gold/dev-v2/aw-18.json)、[v2第一遍AI预审](../../eval/reports/d3-ai-review/aw-dev-v2-pass1.md) | 原v1含多个2013空期，首次系统基线前按第二遍审读仅改4道开发题为真实有数据2024，保留aw11空边界；旧版完整保留。保留9题仅程序只读标签、不展开调参、不生成预测。原题为本项目合成标签，未来成绩不能称独立外部benchmark。 |

## 实际数据日期，不能照旧脚本注释推断

当前下载官方 ZIP 中 SalesOrderHeader CSV 与实际数据库日期是 **2022-05-30 至 2025-06-29**；采购订单日期是 **2022-04-15 至 2025-09-21**。两表实际 `DISTINCT EXTRACT(YEAR...)` 均为2022、2023、2024、2025，不能因此认定每个年度完整。lorint旧 SQL 注释仍写2011–2014；`update_csvs.rb`没有年份平移代码，不把这处差异归因到转换器。CSV日期与导入后范围对应的实际证据在 [当前源与范围核验](../../data/db/aw_live_data_manifest.json)。

## 已接入实际问答并实跑21开发题

在共享API的D3 health真实确认AW就绪、request budget12、只读执行5000ms后，以21个独立会话提交21道开发v2问题。每个请求只带question、db_id和来源范围，没有gold、期望表、标准SQL或答案。实际结果 **21/21 EX探索值100%**，平均4304.81ms，22次真实DeepSeek调用（aw14包括一次语义提取与一次SQL生成），实际prompt219558/completion2809/total222367 tokens；没有失败、没有保留题预测。gold待人工最终核对，因此这不是正式保留集成绩。

实际[运行报告](../../eval/reports/d3-aw-live-dev-run1/report.json)、[原始请求和响应](../../eval/reports/d3-aw-live-dev-run1/responses.jsonl)、[命令stdout](../../eval/artifacts/d3/a/aw-live-dev-run1-command.txt)完整保存。初轮runner加载时未识别返回元数据的`schema_linker`键，原始响应实际上已经保存该键；仅修正观测脚本后对保存响应另行分析，没有再调用模型或覆盖原响应。[独立观测结果](../../eval/reports/d3-aw-live-dev-run1/schema-observation.json)确认21/21实际SQL执行db_id均为adventureworks、21/21SQL业务表都在AW五schema范围、21/21候选包含所有gold表；实际问答中schema阶段平均191.62ms（包含建图/索引验证等），不拿纯模块59.29ms替代端到端阶段耗时。

## 复现命令

在 `system` 下使用已经验证的 Python 3.12 虚拟环境。`.env`、`.runtime/aw.env` 不进入附件或Git；首次引导会自行生成新的AW管理员/只读密码，原Chinook配置保留。

```powershell
.\.venv\Scripts\python.exe -B scripts/bootstrap_aw.py
.\.venv\Scripts\python.exe -B scripts/build_catalog.py --db-id adventureworks
.\.venv\Scripts\python.exe -B scripts/build_schema_index.py
.\.venv\Scripts\python.exe -B -m pytest tests/test_d3_schema_linker.py -q --basetemp .runtime/pytest-d3-schema-new-run
.\.venv\Scripts\python.exe -B eval/d3_schema_eval.py --output eval/reports/d3-aw-schema-dev-new-run
.\.venv\Scripts\python.exe -B eval/d3_aw_eval.py --output eval/reports/d3-aw-live-dev-new-run
```

`bootstrap_aw.py`发现已有完整68表时只验证，不重新导入；发现非0/68表时拒绝覆盖。评测脚本拒绝输入任何带holdout的文件，也拒绝覆盖已存在结果目录。题库构建/首次v2修订命令作为一次性标签准备脚本保存，不能在基线后静默重写已冻结标签。

## 待人工统一检查

需要核对68表中文说明是否忠实、21开发题以及保护保留题标签的业务含义、4题首次基线前非空覆盖修订。3处目录AI修正原文和依据见 [独立修正记录](../../data/catalog/aw_ai_directory_corrections.json)；原模型返回与旧目录没有覆盖。验收报告不得填写A/B签名或人工通过日期。

目录第二遍AI实际逐表逐列审读：63表/436列AI建议通过，5表/19列AI建议有条件通过，1列（production.document.status）缺枚举证据；字段结构检查456/456通过。重点25个目录对象及21开发gold整理成 [A待人工核对表](../../eval/reports/d3-acceptance/A待人工核对表.md)，共46条。未知币种/状态/费率含税口径没有自动补造，条件通过也没有变成人工approved。

## 共享澄清修复后的AW同版本回归（run2）

后续真实回归为 **20/21 strict EX（95.24%）**，22次模型尝试，total tokens=222463，平均4198.90ms。run1原21/21原文件不覆盖。唯一差异aw-07的“产品编号”可指productid或productnumber，当前gold取前者、真实回答取后者；人工明确前不改标签或强制prompt，不能直接称系统业务错误。

[run2实际报告](../../eval/reports/d3-aw-live-dev-run2/report.json)、[run2保存响应独立观测](../../eval/reports/d3-aw-live-dev-run2/schema-observation.json)、[新增AI观察](../../eval/reports/d3-ai-review/aw-run2-additional-observation.md)。21/21都执行在AW，21/21召回gold表，真实schema阶段平均178.00ms。
