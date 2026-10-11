# Final决策与证据独立只读核对

采用 **V1**、撤回 **V2** 的交付口径与实际记录一致。本次核对14项：12项AI建议通过、2项AI建议有条件通过；发现的3处文档问题已由root补充并读回，未发现仍未处理的明确数字或版本事实错误。这个结论核对的是报告和证据，不能等同项目所有功能通过或人工批准。

|编号|核对对象|AI判断|核对要点|
|---|---|---|---|
|FC-01|材料访问与本次核验范围|AI建议通过|实际材料均读入，没有凭条目标题判定。|
|FC-02|冻结题库及三版本评分依据|AI建议通过|三轮相同60条、49/11分组、标签与评分SHA。|
|FC-03|三轮确认完成和失败数字|AI建议通过|V0/V1：18/49、22失败9待核；V2：18/49、23失败8待核。|
|FC-04|unknown、分母和计量边界|AI建议通过|各指标unresolved保留；L2完成0/11与召回11/11区分。|
|FC-05|调用数、token及额外诊断口径|AI建议通过|244POST、344provider、1,513,788预测token；费用未知。|
|FC-06|V1实际范围和局部效果|AI建议通过|仅P3：1406→2021字符；27局部改善，整题仍失败。|
|FC-07|V2拒绝事实及失败归因|AI建议通过|22合法percent被语法guard拒绝；27是真实中文来源继承丢失。|
|FC-08|采用V1/实际撤回V2|AI建议通过|73文件SHA匹配V1，V2helper/test已移除。|
|FC-09|Final装载记录与模块结果|AI建议通过|415passed14.76s；Final重启记录对应V1。|
|FC-10|人工状态与参考/预测分离|AI建议通过|60题和两版30题审读仍pending，参考与预测分列。|
|FC-11|剩余问题报告的实际对应|AI建议通过|真实每年/分子/期间/路由/替换问题均保留。|
|FC-12|相对证据链接与本轮报告勘误|AI建议通过|17相对链接0缺失；恢复路径基准与术语补充已更正。|
|FC-13|比例单位及独立只读金额记录|AI建议有条件通过|fraction/percent分明；显示/舍入仍需人审。|
|FC-14|保留集、Final D2回归及ZIP边界|AI建议有条件通过|本审未替代Final D2回归和ZIP成员/敏感材料核验。|

离线复核实际命令：

```powershell
.\.venv\Scripts\python.exe -B eval/experiments/after_d2_01_03/reports/verify_final_decision_evidence.py
```

实际exit0。目标11个原始交互和18条provider记录的request/response/source/copy SHA及响应内容核对无不符；完整复核结果见[证据核对JSON](final-decision-evidence-check.json)，逐项理由与原文件SHA见[本审完整JSON](final-decision-independent-review.json)。首次离线脚本未解包HTTP响应body而KeyError，修正仅影响报告读取器，成功复核没有重发任何请求。

初读的三个报告问题：恢复档案与源码路径根未区分、V2-27旧观察字段名把分子来源拒绝笼统称分母guard、gaps遗漏Final V1-14/22。现在[恢复说明](restore-instructions.md)已明确双路径根，[术语补充](V2-target-guard-terminology-clarification.md)保留原JSON字节另作说明，[剩余功能问题](remaining-feature-gaps.md)补列实况。

最终三轮成绩、版本取舍和调用边界见[决策报告](version-decisions.md)。[V1全部30题AI语义预审](v1-task03-semantic-review.md)用于Final人工检查，[V2全部30题AI语义预审](v2-task03-semantic-review.md)用于撤回试验档案，二者不覆盖冻结score。

仍需团队决定的是比例显示单位/舍入以及逐条人工审核；本审不填A/B签字或确认日期。最终ZIP包含哪些成员、是否排除了敏感配置/保留题，以及另行运行的D2Final回归，由相应真实交付记录证明。本审没有访问API/DB，也没有重新检查当前HTTP健康状态。审读者参与了D3/V2实现，因此不把这次root报告交叉核对包装成盲审。
