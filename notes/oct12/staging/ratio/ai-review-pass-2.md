# 午夜TIMESTAMP占比边界候选独立第二审核

结论：AI建议通过这项窄修复，仍需根代理应用后执行模块回归并重启真实服务验证。审核的候选为 `ratio_guard_candidate.py`，SHA256 `949a5306ccd57f20f716789a051b053dde9e6c1695e2c82d57207071bf66ca5c`。本审核不代替业务口径批准或人工签字。

读取了完整候选、与现有guard的diff以及15项原有隔离测试。改动仅新增静态期间常量证明，并替换边界右端常量解析；期间左闭右开、分子国家CASE、无条件发票金额分母、零分母保护、真实表与外键来源等原有限制保持原逻辑。没有执行候选应用、修改业务代码或运行保留题。

解析不会在第一步盲目丢弃CAST类型：每一层仅允许DATE或无时区TIMESTAMP类型，随后确认最终节点是字符串常量。文字只允许有效ISO日期，或同日期午夜00:00:00且小数秒全为0；非法日期、任意时区、非午夜小数、动态函数和经TEXT的转换均拒绝。返回的是证明后的日期，不是任意截取时间戳前10字符。

新增实际独立探针12/12通过。原始记录见 [ai-review-pass-2-probes.json](ai-review-pass-2-probes.json)，脚本为 `eval/artifacts/oct12/rag-ui/ratio-second-review-probes.py`。额外检查了嵌套DATE→TIMESTAMP可通过、嵌套TIMESTAMPTZ→TIMESTAMP与TEXT→TIMESTAMP不能绕过、非法2月30日及微秒偏移不能通过。完整guard探针证明放行午夜边界后，错误期间、分母国家WHERE和错误国家分子仍被拒绝。

所有探针为实际本地AST/guard调用，模型请求0、保留题0、数据库执行0。它们验证限定范围的SQL结构证明，不应写成真实模型或数据库执行成绩。Phase2实际失败记录仍是 `eval/artifacts/oct12/ui-live/run-003/invoice-ratio-raw.json`；需新版本真实运行后才能声称该场景修复通过。
