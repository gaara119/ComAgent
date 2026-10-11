# 当前七种运行时 prompt：职责与候选改进位置

本索引在正式专项 V0 冻结后只读核对源码及调用点。没有调用问答系统，没有读取保留集，没有改业务源码、prompt、题库、标签或人工审核状态；以下候选位置是准备性索引，须结合 V0 的实际失败再判断是否需要 V1 修改。

已读实际材料：`qa_agent/llm.py`、`qa_agent/pipeline.py`、`qa_agent/nlu/linker.py`、`qa_agent/clarify/extractor.py`、`service.py`、两份澄清 prompt、`qa_agent/sql/generator.py`、多表 prompt、`qa_agent/rag/service.py`、`answer.py`，以及 `runtime_eval/V0-code-snapshot.json`、`V0-freeze.json`。以冻结文件及原始 provider payload 的 SHA/实际字符串为版本依据；prompt 分布在三个文本文件和四个 Python 内嵌字符串中。

## 七种职责与调用边界

| 编号 | 运行时职责与真实位置 | 何时调用，动态 user 内容 | 输出与后续程序边界 |
|---|---|---|---|
| P1 | 有限候选值链接裁决；`qa_agent/nlu/linker.py`，`ValueLinker.link()` 内的 `system_prompt` | 字符/拼音/模糊/向量阶段之后，只有仍为 unmatched 且存在候选的 mention 进入模型。user JSON 含本次 question、待决 mentions、候选 ID、真实字段/标准值、各 stage_scores | 动态 `BoundedCandidateDecisions`；mention_id/candidate_id 枚举来自本次候选。模型只能 resolved/ambiguous/unmatched，程序再核对每个 mention 恰好一次、候选属于该 mention、未决结果不能附已选 ID；有条件别名仍是候选关系，不能由 prompt 升级为自动绑定 |
| P2 | 初始语义意图提取；`qa_agent/clarify/prompts/intent_extract.txt`，调用点 `clarify/extractor.py::extract_intent()` | 复杂比较/占比/排名、相对或精细日期、范围指代、必要地区归属等才进入模型；明确简单单表有程序 fast path。user JSON 含 question、真实 catalog、verified_value_bindings | `SemanticIntent`。程序解析显式日期、校验模型填期的原文年份、标准化明确目录对象、清模型默认假设，使用真实值绑定覆盖 filters；之后 RuleEngine 决定 L0/L1/L2并推导允许的比较基期，模型不直接签发“可以执行” |
| P3 | 跟进消息→意图补丁；`qa_agent/clarify/prompts/intent_patch.txt`，调用点 `clarify/service.py::extract_patches()` | 自由补充或修改已有会话；可信按钮选择直接用后端保存的选项补丁，通常无需这个模型调用。user JSON 含本次 message、current_intent、当前 card（排除 trusted_options）、本次 verified_value_bindings | `PatchResponse`：set/add/remove 与连续原文 evidence。程序验证原文确实在本次消息中、path 白名单、筛选 field/operator/value 的真实依据、明确取消条件及地区迁移；版本/来源范围校验和 invalidation 由状态机执行，不能靠模型改审核依据 |
| P4 | 单表 PostgreSQL SQL 生成及同路径技术修复；`qa_agent/sql/generator.py::SQL_SYSTEM_PROMPT` | `allow_joins=False`。user JSON 含最终 question、catalog.prompt_schema()、IntentContract、非空 verified_value_bindings；修复时追加 previous_sql、technical_error、repair_rule | `SQLGeneration`：sql/tables_used/explanation。程序验证真实来源、SQLGlot、安全只读、绑定、执行超时；模型的用途解释不等于数据库成功或正确答案 |
| P5 | 多表/比较/排名 SQL 生成及同路径技术修复；`qa_agent/sql/prompts/multi_table.txt`，`generator.py::generate_sql()` | AW，或实际符合 pipeline.allow_joins 条件的 Chinook 排名/同比/占比、跨字段绑定/国家归属等。动态 user 结构与 P4 相同；AW catalog 是 SchemaLinker 实际召回与外键补全后的子目录 | 同为 `SQLGeneration`。外键、连接粒度、头明细金额、current/base、地区及 NULL 等规则在 prompt 内；最终 SQL 仍经过限定期间/地区来源/值绑定守卫和只读执行。修复最多原尝试＋2次，不改标准答案 |
| P6 | 中文问题→英文检索问题；`qa_agent/rag/service.py::run_doc_qa()` 内英文翻译字符串 | 仅 `rag_answer_mode=llm`、问题含中文、所选文档标记英文时调用。user JSON 仅含原问题 question；其输出作为检索 query，原问题仍进入检索和最终回答 | `SearchTranslation.english_query`。只翻译，不能回答或加入新年度/金额/事实；文档 ID 限定、文件 hash 检查和检索范围由程序执行 |
| P7 | 单文档有证据回答；`qa_agent/rag/answer.py::answer_from_chunks()` 内多行 prompt | 实际检索有 chunks 且 mode=llm；extractive 模式不调用。user JSON 含原 question 与本次 evidence 的 ID、doc_id/title、1起物理 page、section_path、text；验证失败重生成时追加 validation_feedback | `DocumentAnswer`：SUCCEEDED/EMPTY_RESULT、answer、citation_ids。程序校验真实编号/内联引用一致、逐句数字与单位、限定显式研究归属；只允许一次证据验证重生成。字面核验不证明完整语义忠实度，缺证据状态不能展示模型记忆补充 |

当前 `extract_mentions()` 是字段范围、真实索引 surface、显式模式和原文 span 的程序提取，未使用另一份“mention 提取 system prompt”。`schema_linker.py` 的双路召回、RRF与外键补全也是程序步骤，本轮没有 D4 的 LLM 剪枝 prompt。SQL结果文字使用数据库结果模板，因此没有第八份“SQL结果润色模型”。

## JsonLLM 实際追加内容

七种调用均经过 `qa_agent/llm.py::JsonLLM.complete_json()`。它发送的 system 消息并非只有上述原始字符串，而是：

```text
对应职责的原始 system_prompt
只输出一个 JSON 对象，不输出 Markdown。字段遵守以下 JSON Schema：
response_model.model_json_schema() 的完整 JSON
```

然后发送调用方提供的动态 `user_prompt`。P1 的 Schema 含本次动态候选枚举，不能仅比较源码固定字符串就认定完整 system 消息相同；其余 schema 也包含实际模型字段、类型、长度和 extra=forbid 约束。服务端使用 `response_format={"type":"json_object"}`，随后客户端实际 `json.loads`＋Pydantic 校验；它不等于服务端保证业务语义正确。

JSON/字段校验失败时，JsonLLM在 messages 追加一个新的 user 提醒：“上次结果未通过 JSON/字段校验。请重读原始任务，保持用户条件不变，只返回符合 Schema 的 JSON 对象。”逻辑调用最多3次尝试；整个请求共享12次尝试预算，OpenAI SDK隐藏自动重试关闭。SQL技术修复和RAG证据重生成是调用方发起的独立有界调用，不能与JSON重试混算。实际 token、耗时、每次 provider 请求/返回及错误以 trace 和捕获文件为准。

动态问题、catalog、候选、会话、技术错误、文档 evidence 均是资料。模型收到这些上下文，不代表它们能替代程序规则或授予变更来源/口径的权限。正式V0标签与gold不放入运行时user消息；审读时要把评分参考与被测系统收到的上下文分开。

## 等 V0 实际失败后可定位的位置

| 实际失败表现 | 先核对的证据 | 可考虑的 prompt-only 位置与限制 |
|---|---|---|
| 正确候选已经出现但模型选错国家/值、误把候选别名当唯一对象 | value_link_llm 的实际 mentions/candidates、动态枚举、provider原返回、程序选择记录 | P1 内嵌字符串；只改善候选判断语义与不确定性表达，不改召回算法/别名启用/候选关系或给题号答案 |
| 明确条件被漏提、用户没给的年/对象被填入、比较/占比缺项误判 | clarification_gate 的结构意图、原问题、P2 provider JSON、RuleEngine实际依据 | P2 文本；说明显式原文和字段区别。若上下文根本未提供必要条件或程序后处理造成偏差，不能靠改prompt宣称解决 |
| 补年份/换国家/换指标时其它条件丢失，或模型要求多余 remove | 本次消息、旧意图、P3 patches/evidence、ground拒绝或实际新意图 | P3 文本；强调最小补丁与保留未改项。陈旧版本、状态失效、字段映射和删除权限仍须程序控制 |
| 意图/绑定正确，但SQL漏条件、排名排序/NULL错误、聚合或连接粒度错误 | 最终给SQL的question/intent/catalog、每次SQL、校验错误、DB原结果 | 按实际 `allow_joins` 对应 P4/P5；增加可普遍适用的查询约束解释，保留原已确认口径。增长率percent/fraction和舍入须人工决定显示规范，不能为得分擅改单位 |
| 中文检索转译改变对象或期间，造成后续检索未命中 | P6原问题/english_query、原文语义、真实retrieve候选 | P6字符串；只保留翻译范围。不能用答案或外部知识补检索query，也不能把检索算法变化装成prompt-only |
| 检索证据足够但回答误读对象/期间/单位、遗漏条件或引用不支撑 | 原PDF/章节/物理页、实际chunks、P7生成与重生成原返回、逐句引用 | P7内嵌字符串；限定现有证据的语义使用。若缺原文或检索证据，应先标证据不足，不能加常识答案或把“数字在片段里”视作整句正确 |

本索引没有根据预计得分选方案，没有生成V1候选内容，也没有预判V0成功率。下一步应先读取实际开发侧失败和原始上下文，分清参考标签问题、系统语义问题、程序边界与环境失败，再决定是否存在能由 prompt-only 改善的具体问题。
