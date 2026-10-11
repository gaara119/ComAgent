# D3 接入前的历史候选

本目录是等待 D2 封存时生成的四个共享文件候选及其差异，不是项目的运行入口。D2 封存后已将候选接入真实项目，并继续根据实跑发现的问题修复。此处保留当时快照，不再重新应用。

当前实际运行代码位于项目根的 `qa_agent/pipeline.py`、`qa_agent/schemas.py`、`ui/app.py`、`api/main.py`，以及 `qa_agent/clarify/`、`qa_agent/sql/validator.py`。测试报告中的 source_sha256 用于核对各轮真实源码版本。

本目录中的草案不能替代当前源码、真实开发集回答或验收报告。交付源码应使用上述实际运行文件。
