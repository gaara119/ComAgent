# D3 接入与修复：第二遍 AI 技术审查

审查对象为实际运行源码和已保存真实开发输出；不读取、预测保留题，不改变题库参考答案。AI 判断与最终人工验收分开。

1. AW 接入：观察21条真实响应，Schema Linking 使用实际 `schema_linker` 元数据；SQL执行记录数据库为 `adventureworks`，68表目录按schema限定。原评测脚本只识别旧元数据键，改为兼容真实键是观测修复；原响应没有改写，实际结果21/21保持。
2. 模型预算：单个逻辑调用仍最多3尝试，新增整个请求12次总上限，为值链接、意图提取、SQL和修复提供共同预算。旧默认None仍退回3次总上限；HTTP夹具分别验证多阶段封顶及每call不扩重试。
3. 澄清保护：旧卡在值链接、模型和SQL之前核验版本；来源改变时拒绝旧卡；服务器保留可信选项补丁，模型不能修改默认审核依据。中文查询对象只规范化到实际目录ID，缺失对象仍需澄清，不据题号新增默认。
4. 地区字段补丁：地区口径切换仅允许 `invoice.billing_country` / `customer.country`，不能联带改 `employee.country`。已有无关条件保留反例，参数改变记录依赖失效；每次重新生成/验证SQL，不宣称D4参数缓存已完成。
5. 分子绑定审查：D3真实初跑显示 `clarify-07` 的国家分子CASE与全体分母被原全局WHERE保护误拦。允许的扩展必须限于已确认同期间全体发票分母及唯一账单国家分子，普通问题仍使用原保护。只读可执行与碰巧同值不能证明条件正确。

对首次扩展函数进一步审读发现三项守卫缺口，已交实现方修复，保留发现记录：

| 技术编号 | AI发现的问题 | 必须保留的回归反例 |
|---|---|---|
| guard-01 | WHERE具有>=年度开始、<年度结束，但另加年中开始条件仍会缩窄“全部同期间发票”分母 | 额外invoice_date边界、OR分支、NOT条件均不应以覆盖两个日期字面值就通过 |
| guard-02 | CASE分支确保国家是强制条件，但额外customer_id或日期条件会缩窄原分子 | 限定分支只含已确认国家等值，不允许新增未确认条件 |
| guard-03 | NULLIF(SUM(total),NULL)曾被通用zero_or_null当作0处理，不能防除0 | NULLIF第二参数仅允许真实数值0 |

修复后第二遍源码核验：CASE只接受真实invoice.billing_country与已绑定值的等值条件（允许反向等值/括号）；WHERE只接受同一期间的精确两个边界AND及重复等价边界；NULLIF第二参数仅数值0。额外日期、额外客户、OR/NOT及NULL参数的反例均被保留。`eval/artifacts/d3/b/shared-regression-v4/` 实际全量375 passed / 14.32s，command.json保存完整命令及源码SHA，pytest.stdout.txt为原输出。技术守卫AI建议通过；真实问答复跑的结果另列，不将模块通过替代模型成绩。其它未支持复杂比例继续普通绑定保护，仍属实现范围限制。

可选模型原始调用观测只记录项目内授权请求/响应，去除真实APIkey和连接串，写文件失败不改变模型调用返回。已有8项真实夹具测试的结果在 `eval/artifacts/d3/root-interface/observer-final-tests.txt`；夹具不计入真实模型EX。

## 真实跟进失败与第二遍修复核验

`eval/artifacts/d3/b/clarify-flow-v1/` 原始5/18包含观测脚本取错金额列和真实会话故障，分别处理；原始记录保留。修正金额列识别后，`clarify-flow-v2/` 为14/18。其余4项失败为两次国家字段/期间跟进中的同一真实问题：模型在地区归属迁移时输出删除旧国家筛选，导致已经确认的加拿大条件丢失。结果未按标准重写，未用全地区聚合冒充加拿大答案。

再次审读 `qa_agent/clarify/service.py`：只有本次原文明确指定账单国家或客户所在地、此前国家条件唯一、remove与旧条件column/operator/value完全匹配时，程序将该remove视为字段迁移的一部分并保留已确认值。其它remove必须有本次真实取消措辞、指定原条件以及真实字段/值依据；否定取消拒绝，取消账单国家不能连带删除员工条件。补丁提示词同时要求归属切换仅设置region_scope，由程序迁移值。此项修复针对实际条件丢失，不更改业务口径、国家值、开发题标准或保留集。

`eval/artifacts/d3/b/shared-regression-v7/` 全量实跑386 passed / 14.21s。新增5条反例覆盖实际模型remove形状、无取消依据、否定取消、保留独立员工条件及连带删除拒绝。技术保护AI建议通过；真实多轮复测尚需查看后续v3实际结果，模块测试不能代替该结果。runtime-v4已实际重启并验证两数据库ready；只终止本项目PID及其已验证服务子进程，未终止其它应用。

v3在4次真实响应后因评测参考事务跨模型等待、超过既有idle-in-transaction timeout而中止。仅将评测参考查询改为每次短只读事务，保留aborted及部分响应，不放宽数据库设置。v4完整17/18；唯一真实失败是后续年份已改2023、SQL却没有期间筛选，Canada金额303.96与只读标准55.44不符。

新增 `qa_agent/clarify/sql_guard.py` 的第二遍源码审查：仅对D3已补丁/澄清的Chinook非增长/占比查询启用；通过真实目录qualified AST定位每个invoice扫描。>=start/<end必须在各扫描WHERE中为强制边界，AND并集、OR交集计算，反向比较与日期字符串CAST保留等价；SELECT字面值、别名混淆、额外缩窄、错误年份及另一扫描漏期均不能证明。函数不改SQL和标准答案，失败进入现有SQL repair。复杂期间等价写法未被自动证明时拒绝并修复，不能冒称支持全部SQL。

`shared-regression-v8/` 实跑399 passed / 14.33s，其中13条日期正反例；技术保护AI建议通过，最终真实flow结果另存。增长和占比具有多期间/分子分母语义，不套用单期间保护；AW及初始D1/D2单表链路未被这个限定守卫扩大。这是已确认会话条件的D3保护，不是D4参数缓存或完整多轮压力测试。

进一步一遍审查发现派生表外层可以另缩期间；限定保护收紧为单SELECT作用域，允许真实JOIN，多层/CTE保守拒绝进入repair。v9全量401通过，两个外层缩窄反例保留。runtime-v5仅重启未用于预测；runtime-v6加载最终单作用域版本。

flow-v5的18/18仅为条件、金额、失效技术检查。逐条原SQL审读发现country-field虽使用c.country='Canada'，却仍SELECT/GROUP BY i.billing_country；当数据恰好同值时金额相同不能证明地区口径正确。原报告不重写，新 `flow-v5-source-recheck.json` 独立标记该来源错误；country-period实际源c.country、输出别名billing_country，不能仅凭别名认定源错误。

针对这一真实错误，新增确认地区输出的有限AST保护：仅在地区真实选项或补丁已确认、当前country字段唯一时，qualified单SELECT的SELECT/GROUP BY/HAVING不能继续引用另一国家来源，独立employee.country保留。c.country AS billing_country仍按customer.country真实源识别，页面caption显示真实地区口径；多层来源不自动证明。隔离SQLite反例设置客户Canada、账单Canada10/USA20，证实总额同为30时仍可能分组错误；没有改业务库。root第二遍审读函数实际源解析、别名展开、employee保留及反例，技术保护AI建议通过。

最终v11全量411 passed / 14.50s；source SHA以v11记录为准。flow新增两个真实地区来源核验，总20项；旧18项结果与新增核验各自留档，不以补检查为由删除失败或改gold。最终真实flow/dev/UI结果仍以新报告为准。

flow-v6真实20/20（条件/金额/失效18+地区真实来源2）。原trace还显示守卫确实拒绝了country-field前两次旧billing_country SQL、country-period首次旧源SQL，走原repair后才执行正确customer.country；不是只在模块夹具里生效。dev-v4真实21/21为初始分级/询问行为，尚不能据此声称所有澄清回答已正确完成。

真实UI-live-v2另发现可信年份按钮补齐日期后仍保留time_ambiguous=true，导致继续L2；自由输入能清该旗，因此freeflow没有覆盖此缺陷。保留按钮后原API及页面timeout。最小修复的第二遍审读：仅在可信time_scope.current含有效ISO日期且start<end时清time_ambiguous；无效选项在任何版本修改之前拒绝，其它指标/对象/国家缺项继续保留。playlist_snapshot不含current，不会误清时间歧义，并保留用户明确取消期间的说明。

v13全量415 passed / 14.85s，新增4项有效确认、无效日期不改版本、缺指标仍L2、取消快照说明反例。技术状态修复AI建议通过；最终需实际年份按钮API和UI7验证。已有flow-v6/dev-v4采集在这项最小增量之前，分别测试自由输入/初始分类；不重写其源码SHA或冒称采集于后来版本，不再次调用未受影响路径凑成绩。
