# D1B 完成记录与人工验收入口

**2026-10-10 原清单最新复查已完成：159项pytest、0skip、6.22秒；53/53项工程检查通过。** 本轮补齐真实`@traced`及固定三个折叠面板；用户确认当前协议双方同意。六份PDF本轮经hf-mirror实下载且SHA一致，QA镜像404而保留官方固定GitHub来源。数据库外键实数为11。新UI两题/3个LLM步骤/8项浏览器检查通过，详见 [十四项证据表](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/requested-d1-evidence.md)。原35题benchmark和下面前一轮57项工程/149项测试记录保持，不能把新UI耗时替换原均值。


## 2026-10-10 本轮最终技术验收状态

**本机技术验收 PASS；工程 57/57，完整 pytest 149 passed／0 skipped，5.71 秒。** 本轮真实 RAG 14 题的调用、指定文档、原页原文、金标页检索／引用与编号检查均为 14/14，平均 HTTP 耗时 **3184.143 ms**；开始版本 `596214c`，开始时工作区干净。[独立 AI 复核](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/b-review-final.md) 为语义正确 14/14、断言支持完整 14/14、联合通过 14/14。官方题目、答案与旧报告均未改写；AI 结论仍非人工签字，gold 人工接受为 0。

当前实际索引为 **v2，1527 × 1024**，全部向量有限且 L2 归一化，BM25／BGE-M3 都先按文档隔离后做 RRF；1402/1527 片段有可靠文字块联合 bbox，226 个不完整句子边界标志保留。最大 600 字符／目标重叠 80／不跨页；不声称每个片段都具备完整句子或逐字高亮。六域 PDF 共 261 个物理页／255 文字页，14 道开发题覆盖五域，6 道 RAG 保留题未运行。

SQL 的独立修正版同时实际完成 21/21 草稿探索，平均 3405.886 ms，开始版本 `379bfdf` 且工作区干净。两组本轮 benchmark 共 35 个请求／35 次模型调用／107751 total_tokens；不含历史草稿、模型探测、UI 或额外 live。工程中的额外四道真实边界题均通过，计 4 请求／5 个 LLM 步骤，其中 MacBook 手册不存在的 2035 年营业利润问题返回 `EMPTY_RESULT` 且无引用；这些不加入 35 题成绩分母。SQL 9 + RAG 6 保留题预测均为 0。

私有 GitHub 已首次推送并验证：版本 `a967f4d`，仓库私有，API／ls-remote／本地提交一致。最后报告手册的后续上传以最终交付记录为准。技术验收与实际证据已完成；团队 gold 签字、正式成绩和校内截止时间／提交入口的外部确认仍待完成。

- [本轮完整验收清单](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/checklist.md)
- [57 项工程检查及四道真实 live](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/engineering.json)
- [本轮 14 题 RAG 实跑](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/rag-dev/report.md)、[待人工逐条复核的回答](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/rag-dev/human_review.md)
- [20 题 gold 审核表](E:/中国电子杯-赛题八/system/eval/datasets/rag_review/rag_gold_review.md)、[本轮实际模型用量](E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/model-usage.json)

## 首次 D1B 实现与草稿记录（历史快照）

**以下保留首轮的 1381 片段、141 测试、14 题草稿及当时待办，不作为本轮重跑结果。** 当时的 rag-19 证据上下文不足在本轮修复与独立 AI 复核中另有记录；旧 gold 和旧报告均保留。文中“当前”“没有上传”等用语指首轮记录时的状态，最新状态以上节为准。

日期：2026-10-10。实现目录：`E:\中国电子杯-赛题八\system`。按用户授权执行《方案.md》的 D1B，已完成资料、PDF解析与切片、真实双通道检索、引用问答、统一API、Streamlit演示和开发集草稿实跑。人工 gold 接受与实际答案语义验收仍由团队完成。

## 首轮演示入口（历史）

- 演示页面：http://127.0.0.1:8501
- API文档：http://127.0.0.1:8000/docs
- 数据库和模型配置已经可用，六份文档均就绪；本机不用重复下载或重新建立环境。
- 以后服务停止时，在 system 中运行 `.\scripts\start_demo.ps1`；脚本复用健康API。设置改动后按 README 重启API。

原 comagent 附件是占位骨架，保留在用户资料目录。实际实现合并进已有 system，继续使用 A 的配置、模型、Pydantic 协议、trace 和SQL实现，没有用另一份协议覆盖现有接口。

## 首轮方案任务对应结果（历史）

| D1B任务 | 已落地结果 | 入口 |
|---|---|---|
| 六域原生PDF及语言盘点 | 金融、法律、教材、手册、新闻、学术各一篇，均英文，固定官方来源；261物理页、255文字页 | data/docs/manifest.csv、source_manifest.json |
| PDF解析、章节、坐标和切片 | PyMuPDF真实文字块/字体，pdfplumber原文；最大600字符、目标重叠80、不跨页，保留空白页编号 | qa_agent/rag/parsers.py、chunker.py |
| BGE-M3+BM25 | 实际CPU/QInt8 ONNX模型，1024维CLS/L2；1381个向量，先限制doc_id再RRF，Top-K5 | embeddings.py、index.py、retriever.py |
| 证据回答 | 共享真实DeepSeek JSON调用，答案编号和实际证据一致，证据不足允许EMPTY_RESULT，真实错误保留 | answer.py、service.py |
| 20道文本QA | 全部来自官方evidence_source=text，原QA ID/问题/答案保留，20/20来源与原页引用机器审计通过 | eval/datasets/rag_ohr.jsonl、rag_machine_audit.md |
| 统一演示页面 | SQL/结果表、所选PDF回答/引用、原页PNG、打开/下载PDF、处理步骤和真实耗时 | ui/app.py、api/documents.py |
| 页面截图与日志 | 浏览器实际点击引用并显示第3物理页，page error为0，SQL查询巴西客户实际返回5 | notes/screenshots/D1-*.png、ui-smoke.json、dev-log.md |
| 开发集基线 | 14题实际API草稿探索，所有请求和失败口径保留，6道保留题未预测 | eval/reports/rag-d1-dev-draft/ |

原PDF、模型权重及派生索引在本机保存并被Git忽略；新电脑按README固定版本脚本准备。模型下载约587MB，清单、模型和向量哈希均有记录。模型参数保持用户指定的cpu/int8、max length512、batch2、Top-K5。引用page从1起，原OHR索引只在转换时加1；前端不再加1。

1381个片段中1273个有可靠映射的文字块联合bbox，其余保持null。坐标是实际块的联合区域，页面展示完整原页；当前不声明逐字精确框选高亮。中文查询英文文档会真实调用模型翻译英文检索问题，答案用原问题，翻译与回答共享请求级尝试预算；此调用与耗时在trace中留存。

## 首轮验证与草稿结果（历史）

统一工程测试：141 passed，6.79秒；最后页面width参数调整另由3个UI测试再次验证。pip check无依赖冲突。浏览器实际SQL、文档、引用按钮、PDF原页与trace展示均通过。

RAG开发集实跑开始版本：`07b9e750ce00bc46d8c8bc341b9f2096aa2d0c2d`；开始时工作目录干净。实际模型：deepseek-flash；实际检索：bm25+bge-m3_dense_rrf。结果：

| 实际检查 | 结果 |
|---|---:|
| 实际API预测 | 14题 |
| 请求成功 | 14/14 |
| 指定文档约束 | 14/14 |
| 原PDF物理页的引用原文真实性 | 14/14 |
| 候选检索命中金标页 | 14/14 |
| 最终引用命中金标页 | 14/14 |
| 有效引用编号 | 14/14 |
| 表面标准答案字符串命中 | 8/14 |
| 平均HTTP耗时 | 3114.79ms |
| 真实LLM调用 | 14次 |
| 本次LLM总tokens | 19291 |
| 保留题系统预测 | 0 |

这是gold未人工确认时的草稿探索。14/14表示调用和引用机械条件，8/14是字符串诊断；两者都不等于答案语义准确率。全部实际回答仍等待逐项事实支持和完整性人工审核，没有发布RAG答案准确率或groundedness。

资料与20题全集涵盖六域，14dev涵盖五域。唯一入选的金融题留在保留集，不为取得六域开发分数而运行保留题。

## 首轮记录的待验收事项（历史）

1. B打开 `eval/datasets/rag_review/rag_gold_review.md`，逐题对照原PDF物理页，确认标准答案、原文和题意。20/20机器核验不能替代人工确认。真正核对后再用 `scripts/review_rag_gold.py --accept 已核对ID --reviewer B` 记录接受；目前接受0题。
2. B打开 `eval/reports/rag-d1-dev-draft/human_review.md`，核对14条实际答案。尤其rag-19：gold强调SST-2和EmoC，实际泛列四个评测数据集；原证据含particularly，而当前引用片段在该限定词之前结束。需要核对答案是否确实回答“显著提升”，不能只凭金标页命中认定正确。当前实际答案人工审核0/14。
3. 开发题gold全部人工接受后，用 `.\.venv\Scripts\python.exe -m eval.rag_run_eval` 生成正式标注上的新运行记录，保留旧草稿。答案语义指标仍需报告中的实际回答人工复核。
4. A继续原30题SQL人工审核，特别sql-22/sql-24的名字口径，之后运行正式21题开发集。历史19/21草稿报告保持不变。

人工接受绑定内容哈希，修改题意/答案/页码/split后失效。仅在Markdown打勾不会更改源题库。D1不预测SQL9道及RAG6道保留题。

## 首轮复现和后续边界（历史）

完整环境、数据库、资料、模型、索引、启动和评测命令见项目README及notes/B接口交接.md。本机现有配置保持可用，.env不提交Git，提交候选凭据扫描匹配数0。所有更改保存在本地Git，没有上传远程。

后续按方案推进更完整的分块上下文与数值/断言支持检查、多文档、跨来源、OCR和其他格式。本次交付为D1单文档原生PDF基线，实际已观察到的答案口径问题保留在开发报告，不借此更改gold或发布未经人工审核的成绩。
