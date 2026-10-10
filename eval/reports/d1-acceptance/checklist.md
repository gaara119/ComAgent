# D1逐项验收清单与计划边界

日期：2026-10-10（America/Chicago）。此清单从计划§4.2 D1、§9和指导书映射实际产物与检查。JSON保留original_snapshot，并增加final_snapshot；中途检查记录不改写成最终通过数。

本轮工程57/57检查、149项回归通过且0skip；独立修正版SQL开发21/21，RAG开发14条机械检查及独立AI审阅14/14。它们都已有真实报告。旧19/21和旧RAG报告保持不变；修正版改变3条开发题，不能作为同题集模型提分。人工gold仍未接受，正式分数未发布。

私有仓库已首次上传并验证private及API/ls-remote/local commit一致。本轮浏览器SQL和中文文档均SUCCEEDED，引用/原页四项检查全true、page_errors为空，三图已保存并逐张视觉核验通过；生成前175候选文件/207历史blob扫描均0匹配，最终增量上传及复检另记录，旧UI实证独立保留。

| 编号 | 责任 | D1要求 | 依据 | 现状 | 证据与缺项 |
|---|---|---|---|---|---|
| S01 | 团队 | 确认学校初赛截止日期及具体时刻、提交入口、额外材料/PPT | §9；指导书§2.1 | 外部信息待确认 | 用户明确目前暂无通知；notes/dev-log.md明确仍需学校核实。暂无学校通知，不把计划D9倒排日期当成已确认截止日期；团队获得通知后补记，未经授权不联系他人。 |
| S02 | A/B | 确认本机与B电脑开发环境/Docker可用 | §9；指导书§2.2 | 部分已确认 | 本机实际Python3.12.10、Docker29.8.2、Compose5.5.1；chinook-pg healthy。本机通过；没有B电脑的实际检查记录。D8另一台电脑从零复现是后续任务，今天不能冒称已完成。 |
| S03 | A/B | 确定A/B职责 | §9；指导书§2.3 | 通过 | 用户明确自己负责A、另交付B骨架；notes/B接口交接.md记录模块责任 |
| S04 | A | 初始化Git及建立私有远程协作 | §4.2 D1上午；§9 | 通过 | eval/reports/d1-acceptance/github-upload.json：首次push a967f4d6cf3191de1a170a82cfdc21237cd65208，private=true，API/ls-remote/local commit一致；私有仓库 https://github.com/gaara119/china-electronics-cup-task8-comagent。首次代码与新开发报告上传已验；最终手册/截图等新增产物由主任务再次push并记录。B账号权限未提供，不能声称B已可克隆。 |
| S05 | A/B | 按代码目录建立仓库骨架 | §3.7；§4.2 D1上午 | 通过 | README.md、qa_agent/{sql,rag}、api、ui、scripts、data、eval、notes均存在。后续nlu/clarify/fusion/AW/scale模块按D2-D4实现；不是D1欠项。 |
| S06 | A/B | 确定共享schemas及输入/响应/步骤/证据协议 | §3.5；§4.2 D1上午 | 已实现，有明确调整 | qa_agent/schemas.py；notes/B接口交接.md；A/B均使用共享API与模型。当前工程统一物理页page从1起；计划原示意为0起，已同步修订根指导书与system内副本。官方OHR原始evidence_page_no仍0起，仅转换一次+1。共享契约已实现并联调，后续字段修改由A/B同步；原方案没有要求书面签字，不新增审批事项。 |
| A01 | A | 起Chinook PostgreSQL并核对实际表名、年份范围 | §4.2 D1 A第一项 | 通过 | docker-compose.yml；data/db/source_manifest.json；data/db/db_check.json；11表64列13外键；2021-2025 |
| A02 | A | 只读qa_reader和SQL超时 | §4.2 D1 A第一项；§3.6.2 | 通过 | data/db/db_check.json：所有11表SELECT=true/write=false，非超级用户，无CREATE/TEMP权限，read_only=on、5s；零行写入拦截 |
| A03 | A | 查询账号可用model id、真实JSON接入 | §4.2 D1 A第二项；§7风险1 | 通过 | notes/model-check.json：models实际返回deepseek-flash/deepseek-v4-pro，配置flash；JSON真实成功；真实SQL/RAG开发响应。真实调用成功证明当次可用；未取得余额金额，不声称已核对余额充足。 |
| A04 | A | 统一LLM超时、有限重试、token及trace | §4.2 D1 A第三项 | 通过 | qa_agent/llm.py、trace.py；开发报告usage_summary.json及逐题真实steps |
| A05 | A | 真实schema目录和中文字段语义 | §3.6.2；指导书§3.3 | 通过 | data/catalog/chinook.yaml；scripts/build_catalog.py；data/db/chinook_schema.sql。字段语义的人工业务认可与逐题gold审核分开保留。 |
| A06 | A | NL2SQL v0：目录→生成→AST校验→只读执行 | §4.2 D1 A第四项 | 通过 | qa_agent/sql/{generator,validator,executor}.py；notes/api-smoke.json；SQL开发集21条真实预测 |
| A07 | A | 30道单表gold，逐条执行并保存结果 | §4.2 D1 A第五项 | 机器准备通过 | 原30题gold逐条执行，30/30结果一致，原题集磁盘内容保持；独立修正版nl2sql_chinook_d1_acceptance.jsonl，仅改变sql-11/22/24开发题；保留9题内容相同；eval/reports/d1-acceptance/a-review.json。修正版已修正平均总额保留两位小数（ROUND(AVG(total),2)实际5.65）以及名字含义不清；人工业务接受仍0/30，不把AI审计写成人工认可。 |
| A08 | A | 人工核对SQL题意、标准SQL与结果；正式开发EX | 指导书§3.6；§6.1 | 人工审核待完成 | a-review.json原题AI复核27语义吻合、1标准结果精度不符、2口径待明；另建修正版并执行3条修订gold；eval/datasets/review_d1_acceptance/gold_review.md；新21开发真实草稿21/21。sql-11改ROUND(AVG(total),2)，真实结果5.65；sql-22/sql-24题意已明确first_name。工程语义口径已处理；剩余是团队实际人工接受及随后正式评测，不再描述为实现未决定口径。 |
| A09 | A | 评测脚本计算EX、保存真实基线 | §4.2 D1 A第五项；§4.1 D1当天验收 | 草稿基线通过 | 新修正版sql-dev/report.json：21/21，exploratory_ex=100.00%，平均3405.89ms；holdout预测0；原d1-dev-draft/report.json：19/21保留。这是另建修正版的草稿；改变3条开发题，不能把与旧19/21的差值称同题集模型提分。正式EX仍待人工接受。 |
| A10 | A | 跑Top艺术家SQL并交名单给B | §4.2 D1 A第六项；附录C | 通过 | data/handoff/A_to_B_chinook.{json,md}；Top10，Iron Maiden第一138.60；原SQL可核验。币种未指定；榜单含电视内容，后续百科筛选要核实实体类型。 |
| A11 | A | 核对客户国与账单国地区口径差异 | §4.2 D1 A第七项；附录C | 通过 | data/handoff/A_to_B_chinook.json：412张发票比较，非空及NULL安全差异均0。当前数据不能用两国字段数值差异作澄清演示；字段业务含义仍不同。 |
| B01 | B | 固定OHR官方qas_v2及六域PDF、盘点语言 | §4.2 D1 B第一项；§3.4.2 | 通过 | scripts/prepare_rag_data.py；data/docs/manifest.csv/source_manifest.json；六域均英文，261物理页255文字页。实际定向HTTP Range取得固定官方文件，未整包下载；可重现来源而非要求唯一镜像。 |
| B02 | B | PDF解析、章节与真实文字/页码切片 | §4.2 D1 B第二项；§3.6.6 | 通过 | 新版真实句界/表格行切片，1527片段、max600字符、1402有可靠块bbox、目标重叠80、不跨物理页；rag-dev/report.json的index_metadata v2；b-review-final.json；engineering.json dense_index_v2_all_sources。226片段有不完整句界（start38/end202，交集14）；长句或物理页末不宣称完整，保留显式标记。未实现OCR/逐字高亮不冒称完成。 |
| B03 | B | 真实BGE-M3 + BM25索引 | §4.2 D1 B第二项；§3.3 | 通过 | engineering.json实际shape1527×1024、all_finite=true、norm约1；真实模型及新向量SHA；rag-dev/report.json：index_version2、bm25+bge-m3_dense_rrf、CPU/QInt8。旧1381向量记录作为历史保留；当前使用真实重建后的1527向量。 |
| B04 | B | 先指定单文档，再混合检索 | §4.2 D1 B第二项；§3.6.6 | 通过 | qa_agent/rag/retriever.py；rag-dev/report.json真实retrieval_methods bm25+bge-m3_dense_rrf；BM25/dense先限定doc_id，用户配置Top-K5。Top-K按实际配置5；计划原Top8调整已记录。运行时不读gold或gold页码。 |
| B05 | B | 带编号证据回答、引用约束和真实错误 | §4.2 D1 B第二项；指导书§4.4 | 通过 | 通用句界/表格行切片及不完整边界标记已改进；未修改回答prompt，新14条是在实际新证据上的真实模型响应；b-review-final.json独立AI审阅：正确14/14、事实支持14/14、joint14/14。rag-16断词证据与rag-19 particularly限定在新实际引用中恢复；这不是硬编码题目答案，仍需团队人工签字。 |
| B06 | B | Streamlit来源选择、答案、SQL/表/引用/步骤面板 | §4.2 D1 B第三项；指导书§4.5 | 通过 | ui/app.py；api/main.py、api/documents.py；notes/ui-smoke.json；实际页面8501健康200 |
| B07 | B | 20道官方evidence_source=text QA、固定14dev/6holdout | §4.2 D1 B第四项；指导书§4.2 | 机器准备通过 | eval/datasets/rag_ohr.jsonl/manifest；rag_machine_audit.json：20/20来源/原问题/答案/页码/原文核验。全集六域、dev五域；唯一finance题属于holdout，今天没有预测它。 |
| B08 | B | 人工核对20道RAG gold及14条真实开发答案 | 指导书§4.2、§4.6；§6.1 | 人工审核待完成 | 20道官方QA原问题/答案/页码/原文来源机器核验与AI核对；b-review-final.json对新14条实际回答AI正确与支持均14/14；human_signature不存在、gold人工接受0。原rag-16/19缺口已通用修复并在新回答上独立复核通过。剩余是团队人工gold接受和实际回答认可，AI复核不代替签字。 |
| B09 | B | 保存真实RAG开发基线、失败、耗时 | 指导书§4.6；§4.1 D1验收 | 草稿基线通过 | 新rag-dev/report.json：14条实跑、0请求失败、引用机械条件14/14，平均3184.14ms；b-review-final.json AI joint14/14；旧草稿原响应及原AI审计保留。AI语义审阅明确非正式分数；团队人工gold0/20，正式忠实度未发布。Dev五域，全集六域，未预测finance保留题。 |
| I01 | A/B | 同一API接入SQL与文档，真实统一响应 | 指导书§3.5；§4.2 D1晚上 | 通过 | POST /api/chat；notes/B接口交接.md；SQL与RAG实际HTTP预测和UI记录 |
| I02 | A/B | 界面数据库题、文档题各跑通且给证据 | §4.2 D1晚上；§4.1 D1当天验收 | 通过 | 本轮eval/reports/d1-acceptance/ui-smoke.json：SQL与中文MacBook文档均SUCCEEDED；SQL/答案、doc/证据、引用点击、原页PNG四项检查全true，page_errors=[]；本轮SQL trace=34bcd24b-5168-40e3-b353-de77d64d1b3b；doc trace=46298574-ba2f-40ea-b1f8-42bd0bf806e7。本轮浏览器观察LLM步骤共3；UI演示不计入35条开发集用量或分母。历史notes/ui-smoke.json保留。 |
| I03 | A/B | 保存D1真实截图 | §4.2 D1晚上 | 通过 | eval\reports\d1-acceptance\screenshots\D1-sql.png；eval\reports\d1-acceptance\screenshots\D1-rag.png；eval\reports\d1-acceptance\screenshots\D1-rag-trace.png。本轮真实Edge Chromium截取三图并逐张view_image视觉核验通过；SQL1440×1080、文档1440×1800、trace1440×1080。与旧notes/screenshots历史图区分，完整截图与ui-smoke.json保留。 |
| I04 | A/B | 首条dev-log记录数字、问题及D2待修 | §4.2 D1晚上；§9 | 通过 | notes/dev-log.md：A/B实现、真实版本/分母/耗时/不一致、人工状态及D2问题。主任务补充本次验收日志；不覆盖旧草稿数字。 |
| I05 | A | 环境依赖、README、快速本机启动 | 指导书§2.3、§6.1；§3.7 | D1范围通过 | requirements.txt、README、start_demo.ps1/.sh、修订指南及新机交接；本轮149项回归通过/0skip；57项工程检查全部通过。快速脚本启动API/UI；新机依赖/容器/模型/索引按README准备，B远机从零复现按D8执行。 |
| I06 | A/B | 保护凭据并保证题库/运行库分离 | 指导书§2.3、§4.2；§3.4.2 | 通过 | engineering.json credentials_current与credentials_git_history均PASS；.env忽略且未tracked；secret-scan.json：候选文件及Git历史真实凭据匹配均0。生成前artifact扫描175候选文件及207历史blob，实际凭据匹配均0，.env忽略且未tracked；最终上传前另行复检记录，不把扫描自动等同于未来上传完成。 |

## 后续日期的任务归属

正式PDF最终门槛与今日D1里程碑不同。下列事项归后续，不因今日未实现它们而判D1工程失败，也不提前声明已完成。

| 编号 | 日期阶段 | 内容 | 边界 |
|---|---|---|---|
| F01 | D2 | 要素级联/改写、50SQL及30鲁棒题 | D2任务，今天不因未完成它判D1工程失败。 |
| F02 | D2 | 多格式/OCR≥10文档、业务口径手册、30RAG及完善引用/数字核验 | 初赛最终必须补齐不同格式≥10份；D1六PDF不等于最终提交齐备。 |
| F03 | D3 | AW④与③澄清状态机/卡片 | D1工程通过不代表已满足初赛至少1中级任务门槛。 |
| F04 | D4 | 多轮、跨源、消融与两规模效率 | 后续需要真实功能和实验，不以D1计时替代两规模效率证明。 |
| F05 | D5 | 冻结全评测、评测看板、从零一键启动与final报告 | 冻结后按预先纪律评测保留集；今天不运行holdout。 |
| F06 | D6-D9 | 最终设计报告/实现说明书Word+PDF、演示视频与ZIP | 今日验收报告手册与初赛最终两份技术文档不同；不要提前宣称参赛材料已全部齐备。 |
| F07 | D8 | 另一台电脑从零解压README复现 | 提供协作交接说明；远机实际复现由D8按计划执行。 |

## 事实与审阅的区分

- 本轮工程57/57、149项pytest/0skip，是工程与边界验证。
- SQL修正版21/21是待人工gold上的开发探索；原版19/21保持原目录。
- RAG14/14机械条件与新AI审阅14/14分别记录；AI审阅不是团队人工签字。
- 标注语义问题已经独立修正或通用改进；剩余人工接受应写成审核步骤，不再写成未处理的实现问题。
- 学校截止时刻、提交入口、额外PPT暂无通知；B电脑尚未实际接入，私有仓库账号权限需实际配置；协议已共同使用，后续改动由两人同步。
- 15道保留题模型预测维持0；全部gold可进行一次性来源核验。

## 来源及证据入口

- [计划书](<D:/wechat/WeChat Files/wxid_zb8l7g4m4o7i22/FileStorage/File/2026-10/方案.md>)：§3.5、§3.7、§4.2 D1与§9。
- [修订D1指导书](E:/中国电子杯-赛题八/system/notes/D1执行指导书.md)：Python3.12、内部1起页码/原始OHR0起一次转换、Top-K5。
- [完整清单JSON](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/checklist.json)：原始快照与本轮快照分开。
- [工程检查](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/engineering.json)；[A独立AI审计](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/a-review.md)；[B新回答AI复核](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/b-review-final.md)。
- [新SQL开发报告](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/sql-dev/report.md)；[新RAG开发报告](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/rag-dev/report.md)。
- [私有仓库首次上传验证](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/github-upload.json)；[协作交接说明](E:/中国电子杯-赛题八/system/notes/D1协作交接.md)。
