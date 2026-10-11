# D1 开发日志：A 后端、B 文档问答与整合

日期：2026-10-10。实现目录：`E:\中国电子杯-赛题八\system`。

以下 A 部分保留原阶段运行记录；本次 B 的完成情况与整合验证见末节。

## 本次实现

保留用户已经创建的 Python 3.12.10 虚拟环境，在其中安装并固定依赖。实现共享 Pydantic 协议、项目本地配置、JSON 模型调用、请求级步骤记录、FastAPI 入口、Chinook 单表 SQL 链路、标注和执行结果评测工具。

数据库采用官方 Chinook 1.4.5，来源及 SHA256 记录在 `data/db/source_manifest.json`。PostgreSQL 16.15 通过 Compose 运行，仅绑定本机 `127.0.0.1:55432`，独立命名卷持久化。应用连接使用 qa_reader；已在 READ WRITE 事务中以零行 UPDATE 验证权限拒绝，数据修改数为 0。初始化重复运行后行数保持一致。

实际数据：11 张表、64 列、11 条外键；customer 59、track 3503、invoice 412、invoice_line 2240。发票日期为 2021-01-01 至 2025-12-22，不采用旧版本示例年份。艺术家销售额 Top10 已导出给 B，第一名为 Iron Maiden，金额 138.60；原数据未声明币种。客户所在国与账单国家在当前 412 张发票中的差异为 0，仍是不同业务字段。

## 已执行的验证

- `python -m pytest -q --tb=short`：91 passed，2.53 秒；包含真实 PostgreSQL 只读、超时、结果上限、NULL/零/空表和 API 接线测试，以及 JSON 调用预算、AST 校验、结果比较和共享配置兼容测试。Starlette TestClient 有一条 httpx 弃用提示，不影响本次通过。
- `python -m pip check`：No broken requirements found。
- `python scripts/check_secrets.py`：本地 `.env` 被 Git 忽略，待提交文件没有匹配到本机真实凭据；输出只显示匹配数和文件名。
- 30 条 gold SQL 在真实数据库中建立标准结果，又通过运行时 AST 校验器和只读执行器独立核对，30/30 与标注结果一致。这是标注验证，不是模型准确率。
- 模型真实接入成功：账号模型列表包含 `deepseek-flash` 与 `deepseek-v4-pro`，按用户选择使用 `deepseek-flash`。JSON 调用成功并保存实际模型、耗时和 token 用量；记录在 `notes/model-check.json`。
- API 已启动于 `127.0.0.1:8000`；实际 `/health` 返回 `database_ready=true` 和 `llm_configured=true`，`/docs` 可访问。真实模型对“客户表共有多少位客户？”生成 SELECT COUNT 并返回 59；完整请求、实际 SQL、结果及步骤在 `notes/api-smoke.json`。缺少 key 的失败路径也已经验证，没有伪造成功。
- 直接请求保留集评测被保护逻辑拒绝。保留集系统预测数为 0。

## 当前评测状态

30 道题固定为 21 开发题、9 保留题，题型按指导书分配。全部 gold 保留 `needs_human_review`；A 的逐题业务审核尚未记录。审核表位于 `eval/datasets/review/gold_review.md` 和 `.csv`。

已通过统一 API 唯一一次运行 21 道开发题的 `--draft-gold` 探索：19/21，`exploratory_ex=90.48%`，平均 HTTP 端到端耗时 3.217 秒/题。没有模型、数据库执行或接口格式失败。21 次模型调用实际累计输入 87,447、输出 1,565、合计 89,012 tokens；这些数值仅指本次 21 题，不含模型探测和独立 API 演示。完整报告、逐题原始响应和用量见 `eval/reports/d1-dev-draft/`，运行时代码版本为 `fe4c4b9bddc3dbc5e23aa1d0a7089f879e2be335`，启动评测时工作目录干净。

两项结果不一致为 `sql-22` 和 `sql-24`：问题写“名字”，gold 只取 first_name，模型另外取了 last_name，按严格列数口径判错。要求列的行值、条件和次序一致。已记录为人工审核时要明确的题意问题，没有删列提高原始成绩、改题或重跑。30 题仍待 A 人工接受，正式 EX 未发布；`eval/reports/d1-readiness/` 是正式模式的前置检查，本次不执行预测，只记录尚未人工确认的 gold，不代表项目从未运行草稿预测。

按用户追加配置，已在本地 `.env` 填好真实只读 `CHINOOK_DB_URL`、5000ms 的 `SQL_STATEMENT_TIMEOUT_MS`，保持兼容旧字段；AW_DB_URL 留空。已保存 RAG 清单/索引/BGE 路径、Top-K 5、长度 512、批次 2、CPU/int8 和 llm 模式，共享 Settings 可读取。RAG 数据、模型加载和量化仍由 B 实现，配置不代表相应能力已完成。

## 接下来

1. A 对照审核表逐题确认问题、标准 SQL、时间和单位、排序与结果，特别明确 sql-22/sql-24 的“名字”，然后记录接受的 ID。自动 SQL 核验不能代替此项确认。
2. 完成人工确认后，通过统一 API 运行正式 21 题开发集，保存 EX、错误类别和耗时；保留题留到 D5 冻结后。
3. B 的 RAG、文档下载与页面已在后续整合阶段完成，见末节；A 原阶段的 21 题草稿报告保持不变。
4. 双方确定私有远程仓库及同步方式；本次仅初始化本地 Git。校内截止时间与提交入口仍需团队向学校核实。

D2 待处理：中文国家别名及更完整的值链接、五级要素链接、意图细化和澄清、多表查询，以及更完整的文档证据检查。当前 AST 和业务表来源检查保证执行边界；查询是否忠实于题意仍需人工 gold 和真实评测判断。

## D1B 实现与整合验证（2026-10-10）

用户提供的 comagent 目录含初始占位骨架；按用户“按照方案.md里面说的来执行”授权，在现有 system 实现 B，保留 A 协议与 SQL 代码，没有覆盖原资料目录。

已从官方 OHR-Bench 固定修订下载六域六份原 PDF，保留来源、许可、ZIP CRC32 和 SHA256。共 261 物理页、255 页有可抽取文字，6 个空白/图片页保留编号，不生成虚构 OCR。PyMuPDF 实际读取文字块与字体，pdfplumber 保留原文阅读顺序；片段最长 600 字符、目标重叠 80、不跨页，章节及可可靠映射的块坐标来自原 PDF。

BGE-M3 真实 QInt8 ONNX 权重已下载并校验，CPU 执行、1024 维 CLS/L2、max length 512、batch 2。真实编码检查通过。全文生成 1381×1024 有限向量，索引实际方式为 bm25+bge-m3_dense_rrf，Top-K 5；BM25 和 dense 均先限定指定 doc_id。1381 片段中 1273 有可可靠定位的文字块联合 bbox，其余保留 null；不声明逐字精确高亮。记录见 notes/embedding-check.json、rag-index-check.json、rag-corpus-check.json。

已实现统一文档 API、真实引用编号校验、证据不足与实际错误响应。中文问英文 PDF 时真实调用共享模型翻译检索问题，再结合原问题生成带证据答案；翻译和回答共享总尝试预算。notes/rag-core-smoke.json 与 rag-core-chinese-smoke.json 保留早期 BM25 的真实接口演示，不作为开发集成绩；当前混合索引另有真实记录，不改写历史实测方式。

Streamlit 页面通过 HTTP 调统一 API，同页展示 SQL/表格与文档答案。点击引用可查看原文、PDF 物理页 PNG、打开/下载原 PDF；页号从 1 起，空白页不重编号。Playwright 实浏览器完成 SQL 与开发题中文改写演示，点击引用并成功加载原页，无浏览器 page error，记录 notes/ui-smoke.json 与 notes/screenshots/D1-*.png。此前定位器与截图等待调整不改变问答代码。

20 道 gold 全部来自官方 evidence_source=text QA，14 dev/6 holdout；20/20 官方原问题/答案/QA hash/PDF hash/页码/原文引用机器审计通过，人工接受仍为 0。题集与全文覆盖六域，14 dev 覆盖五域，金融唯一入选题属于保留集。RAG 运行时未读 gold，保留题预测为 0。人工审核见 eval/datasets/rag_review/rag_gold_review.md。

统一回归 141 passed（6.79 秒）；UI 新版 width 参数另验证 3 passed；pip check 无冲突，凭据扫描匹配数 0，.env 被 Git 忽略。依赖已固定到 requirements.txt，原 PDF/大模型/派生索引保留本地且由固定来源脚本复现。

14 道开发题已通过统一 API 唯一一次运行草稿探索，开始版本 07b9e750ce00bc46d8c8bc341b9f2096aa2d0c2d，工作目录干净。实际模型 deepseek-flash，实际检索 bm25+bge-m3_dense_rrf。14/14 接口成功；指定文档、原页原文真实性、候选金标页、最终引用金标页及有效引用编号均 14/14。平均 HTTP 耗时 3114.79ms；中位数 2969.5ms；P95 最近秩 3854ms。14 次真实 LLM 调用，prompt 18426、completion 865、total 19291 tokens。完整记录见 eval/reports/rag-d1-dev-draft/，保留题预测 0。

标准答案字符串命中 8/14，仅为表面诊断，不能当作 RAG 答案准确率。rag-06/08/12/15/18 的差异主要涉及表述、标点或连字符，仍需人工判断完整性。rag-19 尤其需要核对：官方答案强调 SST-2 和 EmoC，实际回答泛列 SST-2、TREC、AGNews、EmoC 四个评测数据集。官方原证据第6物理页写有 particularly on the SST-2 and EmoC datasets；当前实际 E2 片段在前面的逗号处结束，另引用第7页全数据集表，体现片段上下文完整性和问题口径仍有改进空间。保留原始问题、答案、报告和全部14题分母，未把它改成成功的语义判定。

实际回答语义及每项断言支持均待人工复核，human_review.md 逐题保留标准答案、实际回答和证据。20题 gold 人工接受0，14条实际答案人工审核0；正式 RAG 答案准确率和 groundedness 未发布。A 的 gold 人工审核与正式21题开发评测继续按原流程处理。

## D1 全项技术验收、独立修正版与最终实跑（2026-10-10）

**本轮本机技术验收 PASS。** 以上 91／141 项测试、1381 个片段、SQL 19/21 和首轮 RAG 14 题均为历史快照，保留原报告与版本。本轮独立生成新 gold 版本、重建 v2 索引并保存新实跑记录，不用最新数字覆盖旧记录。最终验收证据集中在 `eval/reports/d1-acceptance/`。

### A 标注与真实数据库复核

原 30 条 gold 通过运行时 SQLGlot 和实际只读执行器再次核对，30/30 与保存结果逐字一致；原内容哈希保持不变。11 表、64 列、11 外键，表名／列名／可空性／行数与目录一致；只读 ACL、零行 UPDATE 拒绝、Top10 艺术家及地区口径交接全部通过。真实排序口径为 en_US.utf8。

独立 AI 语义审核给出 27 项 accepted、2 项 needs_clarification、1 项 error；这里 accepted 仅为 AI 结论。`sql-11` 要求两位小数但原 AVG(total) 返回多位小数；`sql-22`／`sql-24` 的“名字”需明确字段。创建 `eval/datasets/nl2sql_chinook_d1_acceptance.jsonl`，仅修三个开发题：ROUND(AVG(total), 2) 实算结果 5.65，以及明确只投影 first_name；其余 27 项及 9 道保留题不变，split／family 均保留，全部仍 needs_human_review。

可复现脚本为 `python -m eval.revise_d1_gold` 和 `python -m eval.a_acceptance_audit`。修订前后差异及父题集哈希保存于修正版 manifest；新人工审核表导出至 `eval/datasets/review_d1_acceptance/gold_review.md` 和 CSV，原审核表未覆盖。

### B v2 索引与实际回答复核

六域六份 PDF 保持 261 物理页／255 文字页，固定 SHA256 未改；20 条官方文本 QA 和原问题／答案保持不变。v2 chunker 采用完整句子／表格行边界优先，最大 600 字符／目标重叠 80／不跨页；全文重新实际编码为 **1527 × 1024** 有限 L2 归一化向量。1402/1527 片段保留可靠文字块联合 bbox；226 个不完整句子边界标志如实保存，不声称全部文本切分均完整。实际混合方式仍为 bm25+bge-m3_dense_rrf，先隔离 doc_id。

新运行引用较完整上下文，rag-19 的特别限定 SST-2 与 EmoC 等事实支持问题已在新记录中修复并独立审核。`b-review-final.json` 的 AI 复核为语义正确 14/14、断言支持完整 14/14、联合通过 14/14；该复核直接使用已保存回答和源 PDF，不额外调用模型、不改 gold、不代替人工签字。原首轮 AI 分析与实际回答保留。

### 两组开发集真实实跑

| 本轮开发集 | 实际预测与结果 | 平均 HTTP 耗时 | 开始版本／工作区 | 模型调用与 total_tokens |
|---|---|---:|---|---:|
| SQL 独立修正版 | 21/21，exploratory_ex=100% | 3405.886 ms | 379bfdf，干净 | 21 次／88996 |
| RAG | 14/14 成功；文档约束、原页原文、金标页检索／引用、编号机械检查均 14/14 | 3184.143 ms | 596214c，干净 | 14 次／18755 |

两次实跑共 **35 benchmark 请求、35 次模型调用、107751 total_tokens**（prompt 105290、completion 2461）。用量只从这两次已保存的 trace 计算，排除历史草稿、模型探测、UI 和额外 live，见 `model-usage.json`。RAG corpus 与 20 题覆盖六域，14 dev 仍实际覆盖五域。SQL 9 + RAG 6 保留题均未运行模型预测。

gold 人工接受为 0，因此 SQL 的 100% 为修正版草稿探索，RAG 的 14/14 机械与 AI 复核不等于人工核验的正式答案准确率或 groundedness。正式成绩需团队确认 gold，并另外人工审查实际答案。

### 57 项工程验收及额外真实边界题

实际执行 `python scripts/accept_d1.py --live`，记录 **57/57 PASS，0 FAIL**，输出 `engineering.json`。其中全量 pytest 为 **149 passed、0 skipped，5.71 秒**，pip check 无损坏依赖。当前扫描 154 候选文件与 Git 历史 207 blob 的真实凭据匹配均为 0，.env 被忽略。

API、数据库、Streamlit、六份 PDF 源文件 SHA256／magic、每份首末物理页实际 PNG、0／越界拒绝、非法消息 422、未知文档 404 均通过。auto／hybrid／AW／SQL 带文档／多文档五种范围均 UNSUPPORTED 且没有 LLM 步骤或 token。索引 v2 的所有来源、清单及向量哈希、形状、有限值／归一化／物理页范围检查通过；BGE 三句真实 CPU/int8 编码的中英同义 cosine 0.824720，高于无关句 0.328946。SQL 校验器拒绝写语句、多语句、未知列；executor 的只读 on、NULL／0／空表和 SQLSTATE 57014 超时均真实验证。

额外 live 共 4 请求、5 个实际 LLM 步骤、14088 total_tokens，独立保存完整 request／response／SQL／steps／usage，不加入上表的开发集指标：

| 独立 live 用例 | 实际状态／结果 | 耗时 |
|---|---|---:|
| 1990 年前 invoice 列表 | EMPTY_RESULT，空表 [] | 3447 ms |
| 1990 年前 invoice COUNT | SUCCEEDED，0 | 3364 ms |
| 1990 年前 invoice SUM | SUCCEEDED，NULL | 3403 ms |
| MacBook 手册所列 2035 年营业利润 | EMPTY_RESULT，证据 []，明确无财务信息 | 5745 ms |

工程验收运行时版本为 `596214c`；UTC 12:49:56 至 12:50:36，开始时存在新报告，working_tree_dirty=true 如实记录。两组 benchmark 的开始工作区均为干净，二者不同。四份工程命令日志均先脱敏再写文件，不包含 key／DSN。

### 私有同步与剩余团队验收

经用户明确授权，私有仓库 `gaara119/china-electronics-cup-task8-comagent` 已创建并首次推送；首推版本 **a967f4d**，API private=true、ls-remote 与本地提交一致均已验证。此为首次推送证据，最终报告手册及后续文档的上传由最终交付记录说明，不提前声明未发生的上传。

今天本机工程、数据、真实开发集和额外边界验证已完成。团队 gold 人工接受目前为 0，人工答案签字及正式成绩、校内截止时间与提交入口的外部确认仍待完成；这些不由 AI 冒签。D2 的值链接与题库扩充、其他文档格式／OCR，D3–D5 的 AW／澄清／多轮／跨源继续按原方案，不列为今天的工程遗漏。


### 本轮页面证据与收尾

Edge Chromium完成SQL巴西客户5、中文MacBook iMovie、引用E1/物理p3原页与真实trace展示；最终三图逐张视觉检查通过，记录eval/reports/d1-acceptance/ui-smoke.json。两次完成截图共已观察6个LLM步骤，单独记录，最初被中止的捕获实际调用数未知；这些都不计入35条开发集。捕获脚本增加作用域重渲染等待、任意终态观测及异常证据保存，修复内部滚动截图视口；问答运行代码没有因截图重试改变。详细见ui-capture-audit.json。

生成Markdown和10页PDF操作手册，包含真实工程/模型/AI复核结果、32项D1清单、启动与新机准备、人工接受及正式评测步骤、外部待确认和D2后续。PDF按最终渲染逐页检查；终检与私有远端main一致性由最终交付校验保存于.runtime/github-publish.json。


## 用户原清单十四项补齐与复查（2026-10-10）

用户明确双方已核对并同意当前共享协议，绑定SHA256 `60b2816559f347dd60734f80563ae75fb453ab3903b528ed2d6075316b190445`，包括1起PDF物理页。之后实质修改须双方同意具体版本；本轮未修改schemas.py。

补齐5个未来模块目录说明，审计19目录/45计划文件；D2-D4功能仍按阶段未实现。补真实@traced并接入sql_exec，除去重复计时，摘要白名单不包含DSN。补三个固定UI面板：SQL与结果/引用来源/处理步骤与耗时。

真实全量pytest为159 passed、0 skipped、6.22秒；最新工程53/53 PASS。原57项工程包含4条额外live题，本轮未再跑它们。11表64列实际外键11，先前文本13为文案错误已更正，原始a-review.json一直记录11。

本轮hf-mirror ZIP范围下载六份PDF，全部CRC及SHA256与原件一致，原PDF/索引不改。镜像独立qas_v2.json返回404，QA保留固定官方GitHub源8498条。六域各一份英文，20条原始text QA逐项来源审计通过。

新浏览器仅2个实际问题、3个LLM步骤，8/8检查通过、page_errors=[]。SQL巴西客户5；文档iMovie [E1]/物理p3。Trace分别为`38218d9f-e092-4663-9e45-7d0e70f1fbca`及`6dc49334-d3b1-4f6a-9718-982f42a38d62`。新图存notes/screenshots/D1-验收-*.png，旧图保留。

本轮不重新预测原35道开发题，不预测9SQL/6RAG保留题，不自动写人工gold接受。原21/21修正版与RAG14/14机械/AI结论保留既有版本来源，正式成绩继续待实际人工审核。完整证据：eval/reports/d1-acceptance/requested-d1-evidence.md/json。

## D2 增量开发与验收（实际2026-10-10）

逐项对照两份计划，A4＋B5九项覆盖。保留Python3.12.10、DeepSeekflash、只读库与协议；87份D1证据及11表内容哈希前后未变，旧BGE索引保留，无数据库重建/重复导入。

值索引34文本列、5528记录、5184不同文本、5528×1024实际向量。81别名全部待审排除；五级链接、span补丁、绑定AST校验接入原API。鲁棒18/21初轮的职位与候选覆盖问题修复为21/21；未知值保留、摇滚真歧义停止执行。

SQL50题35dev/15holdout；变体30题21dev/9holdout，六类各5。50gold真实只读运行，最终SQL35/35（D1同题21/21、新14/14）、鲁棒21/21下降0pp。gold人审0，正式入口READINESS_ONLY、预测0；上述是开发探索。

13资料全部入库、2193×1024实际向量；原生PDF6/扫描1、HTML2、DOCX2、PNG1、MD1，7英文/6中文。首次两DOCX改动hash导致11/13失败后保留旧记录、改在docs-final重建。扫描四栏顺序与562不完整边界标志如实保存。指标手册实际3页，四指标已有A/B明确确认，6示例SQL实跑。

RAG30＝OHR20＋自建文档10，21dev/9holdout，不足1dev/2holdout。准备阶段扫描OHR题误算自建来源，在模型预测前纠正并移为独立OCR探针。两轮各21请求；最终可答Hit@5 20/20、不足1/1，完整gold引文单片段诊断14/20另报。辅助模型答案/断言支持各21/21，人审0。

最终281 passed/9.99秒、工程58/58，依赖与凭据检查通过。5真实UI场景通过，每会话Step开关前后POST1→1、trace不变、0浏览器错误；PNG/扫描OCR证据真实性通过。UI发现显式未知表被SELECT1 LIMIT0伪装空结果，修复来源guard并真实4/4正反例回归；77题最终跑批在新增guard之前，源码版本差异如实记载，未宣称再跑77题。

最终77题模型用量从trace计算，排除初轮/辅助评审/UI/probe/消融。原失败在eval/artifacts/d2/errors-and-fixes.json，命令在commands/commands.jsonl。33保留题预测0，D5待测。

用户要求审核先跳过、末尾统一。统一表195行＝191待审＋4既有批准；110gold及77开发实际答案语义人审0，33保留行无预测。九项报告、对应源码/真实结果/日志/原资料/截图按相对路径打ZIP，不附真实env/模型权重/虚拟环境。

## D3 B 增量与最终真实验收（实际2026-10-11）

在原Python3.12、DeepSeek和D1/D2项目上接入L0/L1/L2规则、真实中文结构化意图、IntentContract持久会话、补丁依据校验、ID/version陈旧卡防护和具体失效标志。明确简单单表不额外问；缺必需年份不猜最大年份。显式SQL/文档与Chinook/AW来源选择保留，D4全路由/跨源和5段6轮 suite未提前扩展。现有四项已确认指标定义未改变，待审别名不自动启用。

30澄清题满足L2=15、L0=10、L1=5；21开发/9隔离保留按同源家庭分组。第一遍B自审、第二遍A独立逐条审，20建议通过/clarify20条件通过，人工标签仍pending。runtime-v7实际初始分级开发21/21，L2召回11/11、非L2误问0/10；该指标不代表全部最终业务答案EX。原17/21和全部失败保留。

最终真实状态链runtime-v7：7API，20/20＝18条件/金额/失效技术检查＋2物理地区投影/分组/HAVING来源；USA2024=127.98→Canada2024=42.57，账单国家切客户国家仍保留Canada，换2023=55.44，自由补2024推导同比2023，旧卡在LLM/SQL前拒绝。原5/18评分观测错误、14/18真实条件丢失、参考事务空闲中止、17/18日期漏筛和18/18技术观测漏地区来源分别保留并修复。查询每轮重新生成SQL，索引复用，不声明仅DB执行或AST缓存。

真实UI发现年份按钮仍保留时间歧义，最后只在可信有效期间选择时清标志，并保留独立缺指标问题；runtime-v8受影响按钮实际4/4检查、4API。最终全模块415 passed/14.85s，源码SHA全部匹配最新版本。v7题集/状态链没有冒称v8后采；该增量由模块、受影响实际按钮和真实UI覆盖。

最终真实Edge/Streamlit/API `ui-live-v4` PASS10/10，7请求/7张截图：按钮和自由输入补年各前后、L1数量默认、切销售额、切回数量；全部逐张视觉核对。图为notes/screenshots/D3-20261011T200137Z-*.png。原截图路径故障与展开控件观测故障单独保留，不冒充产品业务失败。

增长率实测存在fraction和percent、舍入差别，显示规范待人审，未因测试调整业务口径。最后人工输入notes/d3/clarify-human-review.json含21开发题＋4公共待核项，无签字/人工日期；9保留题预测0，不展开给调参。B证据索引eval/reports/d3/b/handoff-summary.json，逐项报告B原清单四项验收与证据.md；正式8项交付由A汇总。
