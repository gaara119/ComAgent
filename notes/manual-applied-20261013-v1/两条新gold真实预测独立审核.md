# 两条新 gold 真实预测的独立审核

审核对象为 `gold-two-v3-live-002` 已保存的两条真实 DEV 请求和响应，对照最终 `manual-applied-20261013-v3` 的题面、参考 SQL、结果及接受条件。审查只读取现有材料并解析 SQL AST，没有新增模型调用或数据库查询；没有修改业务代码、题库、gold、735 项原选择、原始响应或旧成绩。

结论：**sql-38、robust-23 两条均 AI 建议通过。** 不是仅凭 EX 或当前数值一致判断；分别核对了查询对象、非 NULL 条件、聚合粒度、单位、排序、条数及精度。

证据：[真实响应 JSONL](../../eval/artifacts/manual-applied-20261013-v1/gold-two-live-002/responses.jsonl)、[真实运行报告](../../eval/artifacts/manual-applied-20261013-v1/gold-two-live-002/report.json)、[独立 AST/数值/保护核验 JSON](../../eval/artifacts/manual-applied-20261013-v1/gold-two-live-002/independent-audit.json)。JSONL 按原编号分别定位。报告记录 actual main EX 2/2、legacy 2/2，未产生保留题预测。

| 原编号 | 独立业务与 SQL 核验 | 实际结果 | 判断 |
|---|---|---|---|
| sql-38 | 仅 `public.track`；投影 `track_id,name,bytes`；实际 `WHERE bytes IS NOT NULL`；`bytes DESC,track_id ASC LIMIT 3`；无 JOIN、聚合或额外筛选。请求逐字匹配 v3，新 gold hash 有效。 | 3 行按顺序与 v3 一致：3224／1059546140、2820／1054423946、3236／587051735；编号和大小为整数。Intent 为 lookup、N=3、主/并列序保留，未再反问 metric。 | AI建议通过。未知大小确实在实际 SQL 中被排除，而非仅排序到末尾或因为当前同值碰巧通过。 |
| robust-23 | 仅 `public.track`，单一 `AVG(milliseconds)`；无筛选、JOIN、分组、单位换算、ROUND 或购买量加权。AVG 的 NULL 规则与 v3 一致；请求逐字匹配 v3，新 gold hash 有效。 | numeric 序列化字符串 **393599.212103910933** 与 v3 完全同精度一致；实际列名 `avg_milliseconds`，gold 列名 `average_milliseconds`。 | AI建议通过。列别名变化符合已授权 EX，不改变数值、对象或毫秒单位。 |

robust-23 的自然语言答复只写“查询结果：393599.212103910933。”，没有再次写“毫秒”。这是当前展示限制；题面、真实 AVG 字段和结果列仍清楚对应毫秒，实际 SQL 没有除以 1000 或其他单位变换。本审查没有据此顺手修改界面或 prompt。

sql-38 的语义 filters 列表仍为空，但原题条件保留，实际执行 SQL 确实具有非 NULL 过滤。本次结论只证明该真实预测符合 v3，不宣称所有属性条件的结构化表示或多轮传播都已由此测试覆盖。

当前安装的 SQLGlot 将 `IS NOT NULL` 表示为 `Is` 节点并带 `negate=True`。独立核验初次只识别 `Not(Is(...))` 时发生检查器误报，检查器已同时识别两种等价 AST；没有改变实际 SQL、参考答案或模型输出。JSON 中保留该检查器说明。

## 历史与授权修改范围

再次按原入口清单检查 **384 个历史材料 SHA 全部一致，0 缺失、0 改动**，包含原题库、目录、别名及原始输出。132 个源码/测试/配置保护项中，**129 个不变，3 个在本次明确授权的必要技术修复范围内变化，0 个意外修改**：

- `qa_agent/clarify/extractor.py`：纯字节属性 lookup 证明，以及已批准默认的 L1 来源标记。
- `qa_agent/sql/pruner.py`：由主任务授权的实际 AW 回归暴露的返回结构校验修复。
- `tests/test_d3_clarify.py`：将快路径账单默认旧 L0 断言同步为 L1，并检查 default_assumptions。

完整前后 SHA 与授权理由保存在同目录独立核验 JSON。此处不是继续声称技术修复后所有 132 个文件均未变；也没有借例外覆盖或重写历史运行成绩。

