# D1逐项验收清单与计划边界

日期：2026-10-10（America/Chicago）。此清单从计划§4.2 D1、§9和早期D1指导书逐项映射到实际文件及实跑记录。核对方式为源文件检查和服务只读健康检查；没有运行模型或保留集，也没有自动签署人工审核。

当前核心工程、两条链路的真实页面演示和开发集草稿均有证据。人工gold接受、RAG实际回答语义复核和团队外部确认分别列为未完成，不以工程测试替代。私有远程由主任务根据用户最新授权补齐；此专项清单是检查快照，最终上传和回归结果以同目录主验收报告为准。

| 编号 | 责任 | D1要求 | 依据 | 现状 | 证据与缺项 |
|---|---|---|---|---|---|
| S01 | 团队 | 确认学校初赛截止日期及具体时刻、提交入口、额外材料/PPT | §9；指导书§2.1 | 外部信息待确认 | 用户明确目前暂无通知；notes/dev-log.md明确仍需学校核实。暂无学校通知，不把计划D9倒排日期当成已确认截止日期；团队获得通知后补记，未经授权不联系他人。 |
| S02 | A/B | 确认本机与B电脑开发环境/Docker可用 | §9；指导书§2.2 | 部分已确认 | 本机实际Python3.12.10、Docker29.8.2、Compose5.5.1；chinook-pg healthy。本机通过；没有B电脑的实际检查记录。D8另一台电脑从零复现是后续任务，今天不能冒称已完成。 |
| S03 | A/B | 确定A/B职责 | §9；指导书§2.3 | 通过 | 用户明确自己负责A、另交付B骨架；notes/B接口交接.md记录模块责任 |
| S04 | A | 初始化Git及建立私有远程协作 | §4.2 D1上午；§9 | 主任务补齐中 | 本地Git与提交历史已存在；私有仓库已创建并验证private=true，root正在上传并验证最终commit。私有仓库：https://github.com/gaara119/china-electronics-cup-task8-comagent；创建已验证，最终push与远程commit匹配待主任务记录。 |
| S05 | A/B | 按代码目录建立仓库骨架 | §3.7；§4.2 D1上午 | 通过 | README.md、qa_agent/{sql,rag}、api、ui、scripts、data、eval、notes均存在。后续nlu/clarify/fusion/AW/scale模块按D2-D4实现；不是D1欠项。 |
| S06 | A/B | 确定共享schemas及输入/响应/步骤/证据协议 | §3.5；§4.2 D1上午 | 已实现，有明确调整 | qa_agent/schemas.py；notes/B接口交接.md；A/B均使用共享API与模型。当前工程统一物理页page从1起；计划原示意为0起；根指导书及system副本已同步修订。官方OHR原页索引仍0起，仅转换一次+1。接口已实现、联调通过；双方人员正式共识签字记录尚无，不能自动代表两人签字。 |
| A01 | A | 起Chinook PostgreSQL并核对实际表名、年份范围 | §4.2 D1 A第一项 | 通过 | docker-compose.yml；data/db/source_manifest.json；data/db/db_check.json；11表64列13外键；2021-2025 |
| A02 | A | 只读qa_reader和SQL超时 | §4.2 D1 A第一项；§3.6.2 | 通过 | data/db/db_check.json：所有11表SELECT=true/write=false，非超级用户，无CREATE/TEMP权限，read_only=on、5s；零行写入拦截 |
| A03 | A | 查询账号可用model id、真实JSON接入 | §4.2 D1 A第二项；§7风险1 | 通过 | notes/model-check.json：models实际返回deepseek-flash/deepseek-v4-pro，配置flash；JSON真实成功；真实SQL/RAG开发响应。真实调用成功证明当次可用；未取得余额金额，不声称已核对余额充足。 |
| A04 | A | 统一LLM超时、有限重试、token及trace | §4.2 D1 A第三项 | 通过 | qa_agent/llm.py、trace.py；开发报告usage_summary.json及逐题真实steps |
| A05 | A | 真实schema目录和中文字段语义 | §3.6.2；指导书§3.3 | 通过 | data/catalog/chinook.yaml；scripts/build_catalog.py；data/db/chinook_schema.sql。字段语义的人工业务认可与逐题gold审核分开保留。 |
| A06 | A | NL2SQL v0：目录→生成→AST校验→只读执行 | §4.2 D1 A第四项 | 通过 | qa_agent/sql/{generator,validator,executor}.py；notes/api-smoke.json；SQL开发集21条真实预测 |
| A07 | A | 30道单表gold，逐条执行并保存结果 | §4.2 D1 A第五项 | 机器准备通过 | eval/datasets/nl2sql_chinook.jsonl：30题；21dev/9holdout；data/db实际结果；review/gold_review.md。30条结果已独立核验；人工业务审核属于A08，不能将机器准备通过当成人工接受。 |
| A08 | A | 人工核对SQL题意、标准SQL与结果；正式开发EX | 指导书§3.6；§6.1 | 人工审核待完成 | eval/datasets/review/gold_review.md；gold_review仍needs_human_review；d1-readiness；历史d1-dev-draft。sql-22/sql-24“名字”first_name/姓名口径待决定；A逐题接受后新跑正式21题，历史19/21保留。 |
| A09 | A | 评测脚本计算EX、保存真实基线 | §4.2 D1 A第五项；§4.1 D1当天验收 | 草稿基线通过 | eval/run_eval.py、metrics.py；eval/reports/d1-dev-draft/report.json：19/21 exploratory_ex=90.48%，3216.94ms，holdout预测0。正式EX尚未发布；当前分数以待人工确认gold计算，不能冒称正式成绩。 |
| A10 | A | 跑Top艺术家SQL并交名单给B | §4.2 D1 A第六项；附录C | 通过 | data/handoff/A_to_B_chinook.{json,md}；Top10，Iron Maiden第一138.60；原SQL可核验。币种未指定；榜单含电视内容，后续百科筛选要核实实体类型。 |
| A11 | A | 核对客户国与账单国地区口径差异 | §4.2 D1 A第七项；附录C | 通过 | data/handoff/A_to_B_chinook.json：412张发票比较，非空及NULL安全差异均0。当前数据不能用两国字段数值差异作澄清演示；字段业务含义仍不同。 |
| B01 | B | 固定OHR官方qas_v2及六域PDF、盘点语言 | §4.2 D1 B第一项；§3.4.2 | 通过 | scripts/prepare_rag_data.py；data/docs/manifest.csv/source_manifest.json；六域均英文，261物理页255文字页。实际定向HTTP Range取得固定官方文件，未整包下载；可重现来源而非要求唯一镜像。 |
| B02 | B | PDF解析、章节与真实文字/页码切片 | §4.2 D1 B第二项；§3.6.6 | 通过 | qa_agent/rag/parsers.py、chunker.py；notes/rag-corpus-check.json：1381片段，max600，1273有真实块bbox，不跨页。空白/图片页保留编号；本次不宣称OCR及逐字高亮已实现。 |
| B03 | B | 真实BGE-M3 + BM25索引 | §4.2 D1 B第二项；§3.3 | 通过 | qa_agent/rag/index.py、embeddings.py；notes/embedding-check.json、rag-index-check.json；实际1381×1024 CPU/QInt8向量。不是只有下载配置；有实际CPU编码、模型与向量哈希。 |
| B04 | B | 先指定单文档，再混合检索 | §4.2 D1 B第二项；§3.6.6 | 通过 | qa_agent/rag/retriever.py；真实开发report retrieval_methods=bm25+bge-m3_dense_rrf。Top-K采用用户配置5；计划设计Top8已记录调整，不能同时声明实际Top8。 |
| B05 | B | 带编号证据回答、引用约束和真实错误 | §4.2 D1 B第二项；指导书§4.4 | 通过 | qa_agent/rag/{answer,service}.py；实际14条响应；共享llm/trace，引用指定文档、编号存在。编号及原文真实性检查不等于完整语义/数值支持；D2深化核验。 |
| B06 | B | Streamlit来源选择、答案、SQL/表/引用/步骤面板 | §4.2 D1 B第三项；指导书§4.5 | 通过 | ui/app.py；api/main.py、api/documents.py；notes/ui-smoke.json；实际页面8501健康200 |
| B07 | B | 20道官方evidence_source=text QA、固定14dev/6holdout | §4.2 D1 B第四项；指导书§4.2 | 机器准备通过 | eval/datasets/rag_ohr.jsonl/manifest；rag_machine_audit.json：20/20来源/原问题/答案/页码/原文核验。全集六域、dev五域；唯一finance题属于holdout，今天没有预测它。 |
| B08 | B | 人工核对20道RAG gold及14条真实开发答案 | 指导书§4.2、§4.6；§6.1 | 人工审核待完成 | rag_review/rag_gold_review.md；rag-d1-dev-draft/human_review.md；当前gold接受0、答案语义审核0。机器定位原文不能代替人工题意/忠实度；rag-19需核对particularly限定及回答范围。 |
| B09 | B | 保存真实RAG开发基线、失败、耗时 | 指导书§4.6；§4.1 D1验收 | 草稿基线通过 | eval/reports/rag-d1-dev-draft：14/14调用与引用机械条件、平均3114.79ms；语义审核待完成。14/14不是RAG准确率；8/14字符串命中也是诊断，不发布语义成绩。 |
| I01 | A/B | 同一API接入SQL与文档，真实统一响应 | 指导书§3.5；§4.2 D1晚上 | 通过 | POST /api/chat；notes/B接口交接.md；SQL与RAG实际HTTP预测和UI记录 |
| I02 | A/B | 界面数据库题、文档题各跑通且给证据 | §4.2 D1晚上；§4.1 D1当天验收 | 通过 | notes/ui-smoke.json：SQL/答案渲染、doc/证据、引用点击、原页均true，page_errors=[]。此项已有实际浏览器证据；今天主任务将再按验收步骤检查。 |
| I03 | A/B | 保存D1真实截图 | §4.2 D1晚上 | 通过 | notes/screenshots/D1-sql.png、D1-rag.png、D1-rag-trace.png |
| I04 | A/B | 首条dev-log记录数字、问题及D2待修 | §4.2 D1晚上；§9 | 通过 | notes/dev-log.md：A/B实现、真实版本/分母/耗时/不一致、人工状态及D2问题。主任务补充本次验收日志；不覆盖旧草稿数字。 |
| I05 | A | 环境依赖、README、快速本机启动 | 指导书§2.3、§6.1；§3.7 | D1范围通过 | requirements.txt；README.md；scripts/start_demo.ps1/.sh；本机API/UI/database健康。脚本启动API/UI，依赖/容器/模型/索引按README先准备；从零一键打包验收计划D5/D8。 |
| I06 | A/B | 保护凭据并保证题库/运行库分离 | 指导书§2.3、§4.2；§3.4.2 | 已有记录通过，待终检 | .gitignore忽略.env/.venv/PDF缓存/模型/索引；scripts/check_secrets.py；RAG运行库来自原PDF，不读gold。已有扫描0；主任务最终提交前再次扫描，本专项只读核对不替代最新扫描。 |

## D2-D9任务的归属

下列任务属于后续排期。正式PDF最终门槛与D1里程碑不同；尚未实现这些任务不能被写成今日已完成，也不把它们混入D1工程失败数量。

| 编号 | 日期阶段 | 内容 | 今日处理 |
|---|---|---|---|
| F01 | D2 | 要素级联/改写、50SQL及30鲁棒题 | D2任务，今天不因未完成它判D1工程失败。 |
| F02 | D2 | 多格式/OCR≥10文档、业务口径手册、30RAG及完善引用/数字核验 | 初赛最终必须补齐不同格式≥10份；D1六PDF不等于最终提交齐备。 |
| F03 | D3 | AW④与③澄清状态机/卡片 | D1工程通过不代表已满足初赛至少1中级任务门槛。 |
| F04 | D4 | 多轮、跨源、消融与两规模效率 | 后续需要真实功能和实验，不以D1计时替代两规模效率证明。 |
| F05 | D5 | 冻结全评测、评测看板、从零一键启动与final报告 | 冻结后按预先纪律评测保留集；今天不运行holdout。 |
| F06 | D6-D9 | 最终设计报告/实现说明书Word+PDF、演示视频与ZIP | 今日验收报告手册与初赛最终两份技术文档不同；不要提前宣称参赛材料已全部齐备。 |
| F07 | D8 | 另一台电脑从零解压README复现 | 提供协作交接说明；远机实际复现由D8按计划执行。 |

## 本次只读检查和已存在的实跑证据

- API健康：status=ok、stage=D1、database_ready=true、模型配置deepseek-flash、SQL timeout=5000ms、max_rows=200。
- 文档API：六份均ready=true，物理页共261；页面8501健康HTTP 200。
- 本机环境：Python3.12.10、Git2.49.0.windows.1、Docker29.8.2、Compose5.5.1，数据库容器healthy。
- 历史SQL草稿：21题真实预测，19/21，exploratory_ex=90.48%，平均3.217秒；保留题预测0。
- 历史RAG草稿：14题真实预测，引用机械条件14/14，平均3.115秒；人工语义审核0/14，不能发布RAG语义准确率。
- 全部30道SQL和20道RAG的gold目前未人工接受。只读来源核验可以检查全部gold；今天仍不运行任何holdout预测。

## 来源及可复查入口

- [计划书](<D:/wechat/WeChat Files/wxid_zb8l7g4m4o7i22/FileStorage/File/2026-10/方案.md>)：§3.5、§3.7、§4.2 D1与§9。
- [D1指导书](E:/中国电子杯-赛题八/D1执行指导书-A和B及Codex分工.md)：§2、§3.6、§4.6、§6.1。
- [正式赛题PDF](<C:/Users/郭乾冥/Desktop/8 赛题八：网信产业应用赛道-多模态数据驱动的可解释精准问数问答智能体（中电云计算技术有限公司）.pdf>)：物理p4-5为基础及中级能力，p8-11为最终初赛提交及评分。
- [机器可读逐项清单](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/checklist.json)：含检查时间、来源、每项状态和快照。
- [A/B协作交接说明](E:/中国电子杯-赛题八/system/notes/D1协作交接.md)：独立环境、固定数据准备、协议和端口。

接口页码现采用1起物理页，与早期示意的0起不同；根指导书及system副本已同步修订。代码已实现的契约与A/B人员正式签字是两件事，不能用子智能体协作记录代替团队确认。

补充修订：根指导书及 [仓库内指导书](E:/中国电子杯-赛题八/system/notes/D1执行指导书.md) 内容一致，当前 Python 3.12、page=1、Top-K5 和 EMPTY_RESULT 状态说明均已对齐实现；历史环境及原始成绩保留。私有仓库已创建并验证，最终上传结果待主验收记录。
