主任务确认第一轮 77 道开发题真实回归和运行源码快照封存后，应用了 [staging 候选差异](../../../../notes/oct12/staging/nlu-candidate.patch)。只修改 `qa_agent/nlu/linker.py`，新增 `tests/test_oct12_nlu_live_fixes.py`；没有新增别名、改索引或改题库答案。

`sp01-22` 的 “Gudian 这个流派”现可以提取原文 Gudian，并通过已经批准的“古典→Classical”关系进行拼音绑定。`oct12-join-13` 的员工姓名修饰语明确限定到现有 `employee.first_name`、`employee.last_name`，避免把 Peacock 改成客户姓氏 Leacock。员工姓名列未登记时，程序保持原词并跳过这一范围的值链接，不借用客户名字猜测。

实际运行这两项新增测试及 NLU、澄清已有模块，**174 通过、0 失败，4.64 秒**；包含两条完整实际失败题面、真实索引、缺员工姓名列时不回退，以及姓名属于客户的反例。命令、源码摘要及应用记录见 [application-and-freeze.json](application-and-freeze.json)，原始输出见 [module-tests.txt](module-tests.txt)。

本文件仍只报告模块实测。新服务版本的真实 DeepSeek/API 重测由主任务在集中重启后运行，未在此预写成功结果。先前 `targets-live-001/sp01-22.json` 和 `join-live-001/responses.jsonl` 的失败原始记录保留。
