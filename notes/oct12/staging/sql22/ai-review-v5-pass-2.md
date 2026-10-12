# SQL22 日期候选 v5 独立第二次 AI 审查

判断：AI建议通过此次日期解析窄修复。候选 SHA256 为 `e5c70638135e892f10b2a9e59bedcf82df8dc19e29ddaf2130ecdcfaafeaebb7`；读取、执行和结束时文件内容一致。

实际运行隔离探针 22/22 通过，原始结果为 [ai-review-v5-pass-2-probes.json](ai-review-v5-pass-2-probes.json)。核验包括完整带空格日期、严格早于仅保留 end、非法日期、否定与含端点表达、显式时刻/时区不降级成日期窗口、普通单日查询附加金额/未支付属性、严格早于附加工资/未支付属性，以及历史 sql-22 的真实 provider 回答本地回放。回放修正原先虚构的起点并得到 L0；开放期间的增长问题仍要求基期，未伪造同比基期。

v5 的新增差异仅把“否定”限定在直接附着日期比较运算的表达，修复 v4 两条未支付属性误判。未支付、工资等属性在探针中只用于验证日期方向没有被吞掉，不表示本次增加了对应业务谓词支持。此修改不实现带时刻查询，不扩展日期比较词汇，不修改 gold、业务口径或保留集。

执行命令：`./.venv/Scripts/python.exe -B eval/artifacts/oct12/rag-ui/sql22-final-review-probes.py --candidate notes/oct12/staging/sql22/rules_candidate-v5.py`，标准输出保存为上述 JSON。命令曾错误追加不存在的 `--output` 参数，argparse 拒绝后才执行此正确命令；该失败没有运行探针或修改候选。

真实模型请求 0、数据库执行 0、保留集预测 0。历史 provider fixture 在本地 complete_json 回放 1 次；这是固定输出核验，不是新系统预测。AI 审查不代替人工签字，后续正式应用、全模块回归及实际 sql-22 补测由根任务完成。
