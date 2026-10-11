# D3 B 线真实联调故障与修复记录

本记录针对开发场景，保留集预测为 0。以下内容不代替人工审核，不改题库标准、既有业务口径或 D1/D2 证据。

## 第一轮实际结果与观测错误

`eval/artifacts/d3/b/clarify-flow-v1/report.json` 原始记录为 5/18，7 次真实 API 请求。`country-initial.json` 的实际 SQL 合法返回 `billing_country` 和发票总额 127.98，与只读参考 SUM 相同；原 runner 误要求结果只有一列，因而把该步记为失败。该问题属于评测观测错误，标准 SQL、独立参考值没有修改，原失败记录保留。runner 随后根据实际 SQL AST 的直接 `SUM(invoice.total)` 投影名称提取金额，允许伴随国家上下文列，不能从任意数字中挑选等于标准值的数字。

第一轮另外存在三类真实系统问题：缺对象短句“改成加拿大”没有继承已确认字段范围，模型提出的新国家没有本次值链接证据；明确地区归属切换未允许保留原国家值的字段迁移；模型返回 `time_scope.current` 嵌套路径，状态机只接受顶层 `time_scope`，从而拒绝改年。

已采用通用修复：只继承旧已确认字段名，提取的文本仍只取本次新消息；地区迁移仅允许 `invoice.billing_country` 与 `customer.country` 且本次有明确归属原文，保留国家值和独立员工条件；明确日历原文由程序解析，只覆盖已知 current-period 路径，不忽略其它非法补丁。同一任务有两个独立国家筛选而短句没有唯一目标时拒绝自动修改或合并。模块证据为 `eval/artifacts/d3/b/shared-regression-v6/`，381 passed / 13.94s。

## 第二轮真实条件丢失

`eval/artifacts/d3/b/clarify-flow-v2/report.json` 原始结果为 14/18。国家改值、保留年份、失效标志、自由补年和陈旧卡拒绝均通过；地区字段迁移时实际模型额外返回 `remove filters`，删除了原先确认的 Canada 条件。因此该步虽然 SUCCEEDED，实际返回了所有国家分组，后续改年也继承了缺国家筛选的状态。该问题属于真实系统错误，不能当作评分列名问题。

关键原始材料：

- `eval/artifacts/d3/b/clarify-flow-v2/country-field.json`：实际 intent.filters 为空，SQL 缺 Canada 条件并返回 20 个国家分组。
- `eval/artifacts/d3/provider-capture/adc3f89fb6144db79f19274482bc314e.json`：真实模型补丁 set region_scope 后 remove 旧国家条件，证据片段仅为“改按客户所在地统计”。
- `eval/artifacts/d3/b/clarify-flow-v2/country-field.reference.json`：qa_reader、只读事务和 5s 超时下，独立查询 customer.country=Canada 的 2024 年发票 SUM。

已补限定修复：明确地区字段迁移时，若模型删除的恰为原已确认国家条件且用户没有取消它，程序执行字段迁移并保留值。其它删除必须具有本次真实取消词和具体字段或值链接依据，目标必须对应原已确认条件；“不要取消”拒绝；取消账单国家不能连带删除 employee.country。提示词同步说明迁移只需 set region_scope，不要求 remove filters。未修改 gold、全局地区默认或任何人工审核状态。

5 条正反例覆盖原模型错误形状、无关改年不许删除、否定取消、明确取消目标且保留员工条件、错误连带删除员工条件。真实全模块回归 `eval/artifacts/d3/b/shared-regression-v7/` 为 386 passed / 14.21s。修复后的实际 API 和 UI 复跑结果须另存新版本，不能把以上旧轮次数字改写成通过。

## 参考事务空闲超时与确认日期丢失

`eval/artifacts/d3/b/clarify-flow-v3/` 已保存 4 次实际成功 API 响应和前 3 项只读参考结果。第四次模型调用期间，runner 一直持有参考查询事务，超过 qa_reader 既有 idle-in-transaction 限制，数据库断开该空闲事务。`aborted.json` 标记 ABORTED，该轮没有完整分数。已把 runner 改为模型回答后才短暂连接并执行独立只读参考查询；不放宽数据库任何限制、不修改标准查询。

改正事务生命周期后的 `eval/artifacts/d3/b/clarify-flow-v4/report.json` 为实际 17/18。国家值和归属均保持，唯一错误是 `country-period.json`：IntentContract 已正确改为 2023，但 SQL 缺少整个日期筛选，返回 Canada 全库金额 303.96，独立只读 2023 年结果为 55.44。这是真实生成 SQL 丢失条件，不能用结构化状态正确代替最终查询正确。

新增 `qa_agent/clarify/sql_guard.py` 在限定 D3 路径证明确认期间：只有 Chinook 已补丁/澄清、非增长/占比任务且实际查询 invoice 时启用；单 SELECT 可使用真实 invoice/customer JOIN。每个真实 invoice 来源必须在 WHERE 强制保留 `>= start` 与 `< end`，支持别名、DATE/TIMESTAMP CAST、反向等价和每个 OR 分支都满足期间；SELECT 字面值、遗漏/错误年份、OR 绕过、额外缩窄与重复扫描缺期均拒绝执行并进入既有 SQL repair。多层 SQL/CTE 保守拒绝，避免外层再缩窄期间；本轮不扩展 D4 的复杂日期数据流分析。增长/占比不套用单 current-period 条件，原比例限定守卫继续独立使用。

15 条日期正反例连同全部现有模块实际回归 `eval/artifacts/d3/b/shared-regression-v9/` 为 401 passed / 14.05s。最终 API/界面数字另以新一轮完整报告为准，旧 17/18 和中止轮次保留。

## 金额相同不能证明地区分组来源正确

`eval/artifacts/d3/b/clarify-flow-v5/report.json` 完整 18/18 仅代表原先的条件、金额、失效和卡片技术检查通过。进一步逐条查看实际 SQL，发现 `country-field.json` 虽正确保留 `customer.country=Canada` 和 2024 年，但 SELECT/GROUP BY 仍使用 `invoice.billing_country`。在该库这次查询结果相同，不能据此证明地区归属口径正确。`flow-v5-source-recheck.json` 是对保留原响应新增的独立 AST 观察，未调用模型、未修改旧报告。

第二遍 AI 判断为真实来源/分组错误。已增加限定来源守卫：用户通过真实选择或补丁明确确认地区字段且目标唯一时，SELECT/GROUP BY/HAVING 不得继续使用另一国家字段。按实际表字段和别名作用域核验，`c.country AS billing_country` 仍是合法客户所在地来源，不能凭输出别名决定口径；独立 employee.country 不修改。页面显示真实的国家归属口径。

反例在隔离的 SQLite 内存库构造客户 Canada、两张账单分别 Canada=10 和 USA=20：错误的账单分组返回两行，正确的客户所在地分组返回 Canada=30，尽管总金额都是 30，业务结果不同。这不修改项目数据库或 gold。新增 9 条 SQL 来源反例及 1 条控件口径展示检查；最终固定源码的 `eval/artifacts/d3/b/shared-regression-v11/` 为实际 411 passed / 14.50s。原 v10 测试启动后又加入展示 caption，最终源码一致性以 v11 的 hash 与结果为准。

后续实际联调会独立保存 18 项原技术检查和 2 项实际投影/分组/HAVING 来源观察，不能把增加观测后识别出的旧错误回写为旧轮次成功。

## 最终真实状态链与年份按钮问题

`eval/artifacts/d3/b/clarify-flow-v6/report.json` 在 runtime-v7 完整实测 20/20：7 次实际 API 请求，原技术检查 18/18，另加物理国家投影/分组/HAVING 来源检查 2/2。正确保留 USA/Canada、2024/2023 和明确客户所在地字段；地区切换的错误账单投影被 `sql_region_validate` 拒绝，原有有限 repair 的全部尝试保留，最终正确 SQL 执行。`clarify-dev-v4/report.json` 的21题初始分级/执行门全部通过，不能把该数字当作21题完整业务答案EX或全部澄清交互成功率。

真实 UI `ui-live-v2` 发现另一个必要按钮问题：可信2024年按钮已经写入 current=2024 和 YoY base=2023，但旧 `time_ambiguous` 标志未清，结果再次返回L2。自由输入路径已清标志，所以之前API自由补充通过并没有覆盖该按钮分支。实际raw在 `ui-live-v2/button-still-l2-raw.json`，诊断在同目录 `diagnosis.json`，原失败和超时保留。

限定修复只在可信 `time_scope` 选择真正赋予有效ISO日期且 start<end 后清时间歧义；缺指标/未选国家等问题不清；无效日期拒绝且版本不变；playlist_snapshot取消期间选择仍保存用户声明。最后4条模块反例和完整回归 `shared-regression-v13/` 实际415 passed /14.85s，记录业务源码SHA与当前文件相同。runtime-v8的受影响真实按钮API `button-api-v1/report.json` 为4/4，4请求：完整同比指标题选2024后SUCCEEDED/L0，独立缺指标题仍L2/no SQL。原report理由共用措辞的逐条观察澄清另存 `independent-observation.json`，旧report与raw不变。

## 截图观测故障与最终真实UI

`ui-live-v1` 在保存实际首张L2后因runner相对路径处理报错；已仅把输入路径resolve。`ui-live-v3` 里真实年份按钮已经SUCCEEDED，但runner盲点展开面板把Streamlit保留的已展开面板折叠，导致新请求编号不可见而超时。该问题是截图观测错误，真实成功响应另存 `ui-live-v3/button-succeeded-raw.json`，诊断在 `diagnosis.json`，旧失败不改。helper随后先等待新trace DOM attached，仅在不可见时展开；未修改业务代码、没有新数据库导入。

最终 `ui-live-v4/report.json` 在runtime-v8实测PASS，10/10控件检查、7实际API请求、7张截图，覆盖按钮补年、自由输入補年、L1数量默认及数量→销售额→数量两次切换。7张PNG逐张AI视觉核对保存 `visual-review.json`，记录界面读数、控件和实际trace。截图为 `notes/screenshots/D3-20261011T200137Z-*.png`。

增长率原始SQL跨场景出现fraction和percentage以及不同舍入；本轮按钮API为ROUND(*100,2)的24.24，自由输入/实际UI为0.24240365…，数学增长可一致但不能凭相同列名默认单位一样。报告明确留待人工决定显示规范，没有顺手改提示词、业务口径或原始回答。最终v8仅按钮标志增量，所以v7初始题集/条件链如实保留实测版本，不声称全部在v8之后重采。保留集预测始终0。
