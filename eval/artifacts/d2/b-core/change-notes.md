# D2 B 核心实现及实际测试记录

本文件只记录实际运行结果。确定性单元测试使用测试夹具或模拟模型，其通过数不是线上 RAG 正确率；真实模型开发集结果由 `eval/reports/d2.md` 汇总。D1 验收记录、原始 PDF 和 D1 索引目录没有在本任务中覆盖。

## 改动与入口

- `qa_agent/documents.py`：在原登记/路径范围/SHA256 校验上支持 PDF、DOCX、HTML、MD、PNG；兼容 D1 清单字段并校验新字段与旧字段一致。
- `qa_agent/rag/parsers.py`：`parse_document` 路由多格式。PDF 有可用原生文本时保持原抽取方式；仅实际带图像且文本不足的页调用 RapidOCR。扫描 PDF 坐标回到 PDF points，页码从 1 开始；PNG 为真实像素坐标、`page=null`。DOCX 保留标题和表格，HTML 去除导航/脚本噪声，Markdown 代码围栏内 `#` 不形成章节。
- `qa_agent/rag/chunker.py`：先按真实章节/物理页分开，再切片；默认目标 500 字、重叠 80，短章节允许不足 400，过长句保留截断告警。重复入库的稳定 ID 不重复；独立章节中的相同文本不会错误合并。
- `qa_agent/rag/index.py`：新索引版本 3，读取兼容原版本 2；按清单实际解析，失败项保留错误状态而不生成假片段；输出每份资料解析器、真实位置、警告、片段数和向量审计。
- `qa_agent/rag/retriever.py`：先限制 `doc_id`，两路各取 Top-20，名次从 1 开始、RRF `k=60`，按稳定 `chunk_id` 打破同分；保存 BM25、dense、RRF 排名，生成 Top-8 和 Hit@5 范围分开。英文翻译查询同时用于词检索和向量编码。
- `qa_agent/rag/answer.py`：保留已有引用 membership/inline 检查，增加数字核验。全角、千分位和空格作展示规范化；百分号、负号、币种、年度和显式数量级保持区别。只使用当前事实句引用的证据核验，其他未引用片段不能授权数字。失败带原因重生成一次，再失败抛出明确错误；证据不足固定返回不足说明，防止混入模型记忆事实。
- `qa_agent/rag/service.py`：增加限定文档防御检查、真实生成/校验/重试步骤和来源章节，保留请求 trace_id；机器校验结果不冒充人工忠实度审核。
- `api/documents.py`：多格式下载 MIME、NULL 页码和位置类型；只有 PDF 有物理页预览，PNG 可图像查看，其他格式提供下载和章节定位。HTML 下载为附件，避免在 API 同源执行资料脚本。
- `scripts/ingest_docs.py`：沿用 `--index-path` 并补 `--output-dir`、`--audit-output`，不再覆盖 D1 `notes/rag-index-check.json`。有失败文档返回非零退出码。

## 实际命令与结果

在项目根目录使用 Python 3.12 的原虚拟环境。

```powershell
.\.venv\Scripts\python.exe -m pip install 'rapidocr-onnxruntime==1.4.4' 'python-docx==1.2.0' 'beautifulsoup4==4.13.5'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests/test_d2_rag.py tests/test_rag_core.py -q
.\.venv\Scripts\python.exe scripts/ingest_docs.py --help
```

依赖安装成功，`pip check` 实测 `No broken requirements found.`。原 `onnxruntime=1.31.0`、`numpy=2.5.3` 未升级；RapidOCR 1.4.4 wheel 自带 OCR 权重，在用户请求中不隐式联网下载。实际版本见 `dependency-imports.txt`，安装输出见 `dependency-install.txt`。

最终目标测试 **64 passed in 1.83s**：原 D1 RAG 34 项 + 新 D2 30 项。包括原生 PDF 不误调用 OCR、DOCX 表格、HTML 清洗、MD 代码围栏、PNG NULL 页码、章节隔离、稳定 ID、RRF 公式/Top-20/范围、索引加载时向量行数/维度验证、异常数字/引用、有界重试和无引用文字的启发式告警。原始初始失败和修复后日志均保留：

- `targeted-tests.txt`：实际发现 BM25 通道在常见词场景被丢弃，1 failed / 60 passed。
- `targeted-tests-regression.txt`：修复后 61 passed。
- `targeted-tests-final.txt`：新增 OCR 粘连数字、证据不足输出保护、索引矩阵行数和潜在无引用文字告警后 64 passed。
- `d1-rag-regression.txt`：独立跑原 D1 RAG 34 passed。
- `ingest-help.txt`：实际帮助参数输出；帮助调用没有建立索引或调用模型。

实际错误原因：BM25Okapi 中词在每个片段出现时得分可能为零或负数；旧 `score > 0` 过滤把真实匹配全部丢弃。修复为先检查真实分词交集，再按 BM25 名次参与 RRF，保留确实无词命中的空词检索行为。

## 真实 OCR 结果

- `real-scan-ocr.json` / `real-scan-ocr.txt`：读取 `data/docs/raw/d2/ohr-endoscope-scan.pdf`，两页均无原生文字层，真实 RapidOCR 输出 **2/2 页**。包含识别文本、框坐标、置信度和低置信度告警。第 2 页两个独立 OCR 块分别为 `InnoViewGMBHEndoscopes comewitha2` 和 `yearminimumwarranty.`；页级文字里中间插入其他栏内容，**两块拼接不是连续的源文字引用**。应分开取真实字串与框，或者保留包含中间内容的真实连续段，不能人工拼接伪称逐字引用。空格缺失和多栏阅读顺序未伪装为完美复原。
- `real-png-ocr.json` / `real-png-ocr.txt`：读取清单内 `artist-led-zeppelin` 的真实网页 PNG，真实 RapidOCR 成功；`page=null`、`section_path=["图像 OCR"]`、框为像素坐标。1968 年伦敦成立的字句有直接源定位。OCR 对 URL 字母 `o` 可能识别为数字 `0`，实际来源 URL 仍以清单为准。

真实 OCR 使用的 Python 调用及原始结果文件可复查；它们没有使用测试模拟引擎。完整 13 份正式索引及真实模型 RAG 开发集由主执行流程另存 `docs-audit.json` 和 RAG 原始响应，不能用上述局部 OCR 成功替代完整验收。

## 人工审核状态

本次没有把任何答案标为人工审核通过。数字出现匹配只作低成本拦截，不能证明对象、期间、单位和陈述整体忠实；真实 RAG 答案仍需团队逐题审核。非数字的文字陈述没有引用时显示 `potential_uncited_statement_count` 启发式告警和 `warn` 步骤；这不是语义事实识别器，仍明确要求人工检查。公共 `schemas.py` 未修改，沿用 D1 双方确认版本。
