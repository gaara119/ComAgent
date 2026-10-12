# sql-19第三版候选独立第二审核

结论：AI建议通过第三版窄分类纠偏，需根代理应用后完整模块回归及真实sql-19验证。候选 `extractor_candidate-v3.py` 的SHA256为 `f203c3f39b6e74adbab8a2434c0983b9dcedb48451550f723d4175030358259d`；业务源码尚未由本审核应用，第一版旁路和第二版条件意见全部保留。

独立读取了第三版完整逻辑及56项候选测试。完整主句和所有余句白名单仍成立，每个允许属性在真实public.customer schema中存在；调用限定ranking、metric为空、客户对象或空对象，不覆盖其它业务任务或已有指标。新增要求模型N非空并与主句明确N相等，主order非空、字段和方向与主句属性排序相等。缺失或错误模型条件保持原任务，不自动填写或改变N、order、业务指标。

新增实际独立12/12 fixture探针通过，见 [ai-review-v3-pass-2-probes.json](ai-review-v3-pass-2-probes.json)，脚本为 `eval/artifacts/oct12/rag-ui/sql19-v3-second-review-probes.py`。验证了真实纯字段与tie问题恢复lookup；错/缺N、空/缺order、错误字段与方向、artist对象保持ranking；营收、revenue、支出三种第一版业务旁路仍保持ranking/L2指标缺口。所有案例提取器输出保留原fixture N、order和metric。

这些探针调用模型0次、保留题0次，不能替代实际模型成绩或SQL执行结果。修复仅证明主排序及纯属性查阅范围，不独立证明完整模型order的全部tie-breaker细节；原题明确tie规则应由最终SQL和实际结果继续核验。应用后若模型提取缺失N或order，该窄恢复会保守跳过，不能把这种未恢复状态记录为已通过。

本记录为AI代码复审，未填写A/B签字、人工日期或审核批准状态。
