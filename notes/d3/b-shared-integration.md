# D3 B 与现有 D1/D2 共享流程的增量接入

本文件是接入设计记录，不表示接口已上线。D2 最终回归、截图、报告和提交完成前，`pipeline.py`、`schemas.py`、`ui/app.py` 与 `api/main.py` 保持原样。

1. `ChatRequest` 增加可选 `clarification_id`、`intent_version`、`choice_id`。旧客户端的 `session_id/message/scope` 保持有效；不开放任意客户端业务补丁。卡片 ID 与版本成对传入，点击选项还须提供后端保存的稳定选项 ID。
2. SQL 入口按明确 `scope.db_id` 选择 Chinook 或 AdventureWorks 的目录、只读连接、schema 索引。AW 不使用 Chinook 国家值索引。未知数据库和自动/混合来源仍明确不支持，不扩展 D4 路由。
3. 一次会话请求在 session lock 下运行。提交卡片时，先核验来源、ID、版本再调用模型；旧卡片失败不能修改当前意图或执行查询。
4. 普通清楚的单表问题沿用 D2 值链接及 SQL 路径。比较、排名、热门、复购、相对时间、指代范围、日期冲突与真实修改进入结构化 DeepSeek 意图提取。所有默认由规则表安装，模型无法偷偷把“最热门”提前解释成唯一计量。
5. NLU 有实际值索引时保存字段、操作符、值及出处；多候选只保存候选。会话状态持续保留尚未解决的候选集合，选择一个候选不能消除其它未解对象。候选 issue 使用问题指纹，不沿用裸 mention-1 跨新问题。
6. SQL 生成前运行 L0/L1/L2 规则门。L2 保存卡片并返回，不运行 SQL；L1 声明真实已启用默认并提供切换；完整比较任务走 L0，不一律因为同比/占比而追问。
7. 补丁由用户点击可信选项或实际自由输入提取。改同一地区字段的值使结果失效；改地区字段/过滤字段还使 fields/schema 失效；改期间使旧推导基期失效；改指标使粒度、聚合、字段、schema 与结果失效。每次实际变更增版本，未改的条件保留。
8. AdventureWorks 在规则门通过后调用现有 `SchemaLinker`，使用 `bundle.selected_catalog` 生成 SQL，保存 `bundle.as_dict()` 到实际 trace/metadata。D3 不加 LLM 剪枝。Chinook 仅为 D3 必需的热门、比较与已确认跨表筛选开放 JOIN；清楚单表问题保留 D2 安全行为。
9. 每次执行继续用 SQLGlot、真实目录、已确认值绑定校验、只读事务、5000ms 超时与结果行数上限。D3 不宣称实现地区修改后完全免模型的参数化 SQL 缓存；实际 SQL 会按当前条件重新生成，目录与向量索引复用。
10. UI 保留三个折叠面板；增加 L2 稳定选项按钮、自由输入补充，L1 默认声明和口径切换。口径确认记录与默认假设分开；数量→金额→数量每次使用新版本卡片，只产生一次 API 请求。

歌单收录次数没有收录日期。对一个有明确年份的热门问题切换歌单次数时，会再次澄清是否取消时期并统计当前快照，或保留时期换回有发票日期的数量/金额；不会擅自用发票日期冒充收录日期。

已有证据：`eval/artifacts/d3/b/module-check-v1/`、`module-check-v2/`、`module-check-v3/` 为实际规则/状态反例检查；`eval/reports/d3-ai-review/clarify-dev-pass2.json` 是独立第二遍开发标签预审。真实 API 运行器为 `eval/d3_clarify_eval.py`，仅读取 21 开发题；9 保留题继续留到 D5。工程 fixture、规则标签核验和实际模型回答会分别记录。
