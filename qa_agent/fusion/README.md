# 跨源融合目录

对应《项目方案》§3.4.3、§3.7 和 D4 两类跨源流程。

`planner.py` 接入原 `/api/chat`，支持 `hybrid` 以及明确两类题面的 `auto` 路由：

- SQL→文档：原 SQL 通道实际查询销售额前1名，校验真实 `artist_id`、名称及明细汇总；以结果的 ID 和标准名精确匹配清单 `entity_ref`，再调用原检索和带引用回答模块。没有对应文档时保留 SQL 排名、说明文档不足，不换成另一艺术家。
- 文档→SQL：实际检索口径手册，模型提取逐字定义引文和聚合/字段；核对原文、目录及已确认口径后，将上下文传入原 SQL 生成器；`fusion_plan_validate` 在只读执行前核对 SQL 聚合、字段、粒度及 NULL。文档 SQL 只是资料，不能绕过原安全校验。

结构化澄清由原③状态机负责，保持同一 session 和原 scope。续问复用已检索定义，但检查源文件和定义 SHA，不以聊天记录重新猜全部条件。实际步骤和两边证据沿用 `AnswerEnvelope`，界面保留三个证据面板。

6道开发题位于 `eval/datasets/d4/cross_source_dev.jsonl`，实跑入口是 `scripts/run_d4_fusion.py`，只读重新计算本库参考结果。模块/页面模拟测试与实际模型回答分开保存在 `eval/artifacts/d4/fusion/`。这些新题的参考和文档完整语义仍待人工审核，不读保留题。
