> 汇报阅读版；原始验收记录和源码固定于 `ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7`。证据链接需具有私有仓库访问权限。

# 按用户逐条清单复核：D1 B 与晚上联调

核查时间 UTC：2026-10-10T13:43:30.882141+00:00。本核查无模型调用，无保留题预测；不填写人工 gold 接受。

| 项 | 用户要求 | 状态 | 可点击证据 |
|---|---|---|---|
| B-1 | 用 hf-mirror 下载 OHR-Bench qas_v2.json 和 PDF，六域各一份并盘点语言 | PASS_WITH_SOURCE_ADJUSTMENT | [scripts/prepare_rag_data.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/scripts/prepare_rag_data.py>)；[data/docs/source_manifest.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/data/docs/source_manifest.json>)；[data/docs/manifest.csv](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/data/docs/manifest.csv>)；[notes/D1执行指导书.md](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/D1%E6%89%A7%E8%A1%8C%E6%8C%87%E5%AF%BC%E4%B9%A6.md>) |
| B-2 | PDF parsers/chunker/index(BGE-M3+BM25)/retriever/answer，编号引用 | PASS | [qa_agent/rag/parsers.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/parsers.py>)；[qa_agent/rag/chunker.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/chunker.py>)；[qa_agent/rag/index.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/index.py>)；[qa_agent/rag/embeddings.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/embeddings.py>)；[qa_agent/rag/retriever.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/retriever.py>)；[qa_agent/rag/answer.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/answer.py>)；[notes/rag-corpus-check.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/rag-corpus-check.json>)；[eval/reports/d1-acceptance/rag-dev/report.md](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/reports/d1-acceptance/rag-dev/report.md>) |
| B-3 | Streamlit 提问框、来源选择、三个折叠面板 | PASS_AFTER_FIX | [ui/app.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/ui/app.py>)；[tests/test_ui_app.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/tests/test_ui_app.py>)；[eval/reports/d1-acceptance/requested-ui-tests.txt](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/reports/d1-acceptance/requested-ui-tests.txt>) |
| B-4 | 从原 OHR QA 挑选20道 evidence_source=text 的题 | PASS | [eval/datasets/rag_ohr.jsonl](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/datasets/rag_ohr.jsonl>)；[eval/datasets/rag_ohr.manifest.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/datasets/rag_ohr.manifest.json>)；[eval/datasets/rag_machine_audit.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/datasets/rag_machine_audit.json>)；[eval/rag_build_gold.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/rag_build_gold.py>) |
| JOINT-EVENING | 界面各问一道 SQL/文档题；notes/screenshots/D1-*.png；数字写dev-log.md | PASS_WITH_PRESERVED_CAPTURES | [notes/ui-smoke.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/ui-smoke.json>)；[notes/screenshots/D1-evidence.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/screenshots/D1-evidence.json>)；[notes/dev-log.md](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/dev-log.md>)；[eval/reports/d1-acceptance/ui-smoke.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/reports/d1-acceptance/ui-smoke.json>) |

## 六域文件与来源

历史 qas_v2.json 来自固定 GitHub raw、PDF 来自固定 huggingface.co ZIP 条目 Range；历史记录保留。本轮已真实通过 hf-mirror 定向下载六份相同PDF并逐个核对SHA/CRC，全部与原PDF一致，实际传输14141278字节。镜像固定revision根路径的qas_v2.json实测404，所以QA保留官方GitHub固定来源。当前状态为PASS_WITH_SOURCE_ADJUSTMENT，下载内容与数据口径已落实，QA路径调整如实记录。证据：[镜像路由实测](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/reports/d1-acceptance/requested-download-route.json>)、[六PDF镜像实下载核验](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/reports/d1-acceptance/requested-mirror-pdfs.json>)。

官方原 QA 全文件含 8498 条记录，SHA256 `2446db28741fa9f392067ee7aae7f3b05e0d85c584069a50ddd5b1b5bc783f58`，与固定清单匹配 `True`。

| 域 | 文档 | 语言 | 物理页 | PDF SHA256匹配 |
|---|---|---|---:|---|
| finance | data/docs/raw/finance/AMD_2022_10K.pdf（原记录本机文件，未纳入交付包） | en | 121 | True |
| law | data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf（原记录本机文件，未纳入交付包） | en | 8 | True |
| textbook | data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf（原记录本机文件，未纳入交付包） | en | 20 | True |
| manual | data/docs/raw/manual/Macbook_air.pdf（原记录本机文件，未纳入交付包） | en | 76 | True |
| news | data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf（原记录本机文件，未纳入交付包） | en | 20 | True |
| academic | data/docs/raw/academic/2305.14160v4.pdf（原记录本机文件，未纳入交付包） | en | 16 | True |

## 真实检索和题目溯源

当前索引 v2，[1527, 1024]，有限／归一化／chunk 与 vector 哈希均实际检查通过；BGE 模型5个文件的固定哈希也通过。原PDF合计261页，六域均英文。

20条题目逐条重新对照原 qas_v2 和原 PDF，原问题/答案/完整QA/哈希/物理页/连续原文均通过。14开发题、6保留题，人工接受0；本核查只读，不执行保留题预测。

源码入口：

- prepare_official_source：[scripts/prepare_rag_data.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/scripts/prepare_rag_data.py#L26>)
- pdf_parse：[qa_agent/rag/parsers.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/parsers.py#L69>)
- chunker：[qa_agent/rag/chunker.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/chunker.py#L84>)
- index：[qa_agent/rag/index.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/index.py#L22>)
- dense：[qa_agent/rag/embeddings.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/embeddings.py#L20>)
- bm25_dense_retrieval：[qa_agent/rag/retriever.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/retriever.py#L35>)
- numbered_citations：[qa_agent/rag/answer.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/qa_agent/rag/answer.py#L30>)
- ui_three_panels：[ui/app.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/ui/app.py#L135>)
- ui_source_selection：[ui/app.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/ui/app.py#L227>)
- ui_question_form：[ui/app.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/ui/app.py#L259>)
- select_20_text：[eval/rag_build_gold.py](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/rag_build_gold.py#L100>)
- dev_log_current：[notes/dev-log.md](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/dev-log.md#L88>)

## 页面缺口修复与验证

本次逐字核查发现原页面只有2个折叠面板；已补为3个固定面板。SQL与结果显示真实SQL、结果表、所选数据库；引用来源显示实际证据、编号、页和原PDF；处理步骤与耗时显示真实trace。SQL和文档通道、未提问、切换作用域时均保留3面板，占位不伪造运行数据。

定向 AppTest 5 passed in 2.35s：SQL/文档共享协议、三个面板、SQL结果归属、真实引用和页、引用点击不额外请求、切换作用域不显示旧SQL、空输入不调用、两个通道未提问占位。整套回归已实际完成159 passed in6.22s、0skipped；本轮工程53/53PASS、没有启用--live额外模型预测。新实浏览器捕获两题完成，8项检查均通过：SQL、文档、引用点击、PDF原页以及未提问/SQL/作用域切换/文档的三个固定面板。旧图仍不标为新UI。证据：[本轮工程](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/reports/d1-acceptance/requested-engineering.json>)、[新界面实跑](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/reports/d1-acceptance/requested-ui-smoke.json>)。

## 用户指定截图路径

原 notes/screenshots/D1-*.png 已存在。本次逐张查看确认真实内容并核对SHA，未覆盖旧PNG。原notes抓图与后来eval验收抓图有不同trace及哈希，完整清单见 [notes/screenshots/D1-evidence.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/screenshots/D1-evidence.json>)。

旧图原SQL trace：ddefcce0-cc88-4f39-a53f-d139174aa756；原文档 trace：14842eb2-77e4-4056-a837-e207bd61bee9。原SQL结果5，原文档答案iMovie、E1、物理p3。最终验收图的trace为另一次真实请求，不能与旧图混用。

当前核查完整版（包含每个PDF、模型及20题逐项布尔结果）见 [eval/reports/d1-acceptance/requested-b-evidence.json](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/eval/reports/d1-acceptance/requested-b-evidence.json>)。

## 补齐后的实浏览器联调与新截图

实际2个UI问题，SQL SUCCEEDED并显示巴西客户5；文档 SUCCEEDED，iMovie[E1]，物理第3页真实原文与PNG。SQL trace为38218d9f-e092-4663-9e45-7d0e70f1fbca；文档trace为6dc49334-d3b1-4f6a-9718-982f42a38d62。三个新PNG逐张view_image检查完成；SQL图第三面板在视口外，但真实DOM断言为3，文档总览完整显示三个面板及原页。浏览器page error为0。本次2请求/3个LLM步骤，不计入已有35题分母，保留题预测0。

三个新图未覆盖任何旧图，按字节复制到用户要求的位置并核对SHA：

- [D1-验收-sql.png](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/screenshots/D1-%E9%AA%8C%E6%94%B6-sql.png>)，SHA256 `2a9148ddf0a14ac7ce60485636a3ef82cd89c030074ccda58e92df016527a56e`。
- [D1-验收-rag.png](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/screenshots/D1-%E9%AA%8C%E6%94%B6-rag.png>)，SHA256 `d14bf5ac42fe7ceb46f16ac968c86d6abab4cedfe369b4be1d8669923050ddc4`。
- [D1-验收-rag-trace.png](<https://github.com/gaara119/china-electronics-cup-task8-comagent/blob/ccf4c49d4dd30a43ecbfe2162bf43dcd3eb3d0b7/notes/screenshots/D1-%E9%AA%8C%E6%94%B6-rag-trace.png>)，SHA256 `c77512bb1e3548ca2b01d4512d8a120c5a7058e8cbd48d184a64eacacea48827`。
