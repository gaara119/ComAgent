# NLU 与要素识别目录

对应《项目方案》§3.7 的 `qa_agent/nlu/`。D1 仅建立目录；当前显式 SQL/文档路由由 `qa_agent/pipeline.py` 处理。

`extract.py`、`linker.py`、`rewrite.py` 尚未实现。D2 按计划实现值索引、别名与链接、问题改写；NLU 意图补丁及多轮行为依后续计划完善。这里的目录说明不表示已完成中级任务①或②。

后续新增代码复用 `qa_agent/schemas.py`。变更公共字段前，按 `notes/共享协议确认.md` 取得 A、B 对具体版本的明确同意。
