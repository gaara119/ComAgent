# D2 RAG 审计修正与回归验收

本报告对应用户授权修正的 D2 RAG 引用定位问题。改动沿用 D1/D2 的真实运行链路和已验证模型；原始 PDF、题库答案、旧验收材料、旧索引 `data/indexes/docs-final` 与初轮修正索引 `data/indexes/docs-d2-final-v4` 均保留。本轮仅运行开发集，未读取保留题内容、未生成保留题预测，未计算保留集成绩。

## 实现与证据

| 要求 | 本次实现 | 改动文件 | 新证据 |
|---|---|---|---|
| 不将扫描 PDF 的隐藏 OCR 当作可靠定位 | 可见扫描图覆盖页面达到 80% 时，即使隐藏文字很长，也用实际渲染图运行 RapidOCR；保留 OCR 来源和警告 | `qa_agent/rag/parsers.py` | `eval/artifacts/d2-final/rag/parsed-sources/`、`parse-events.json` |
| PDF 文字与框使用同一坐标系 | 原生 PDF 的文字、行和框均取 PyMuPDF；统一为可见 CropBox 左上原点、未旋转 PDF 点坐标；显示渲染也采用相同坐标系 | `qa_agent/rag/parsers.py` | `tests/test_d2_rag_locations.py`、`location-check-v4.3/` |
| 不串接不同栏的章节与段落 | 对原生块的实际行按水平位置分组；标题只可来自当前物理页、同一栏的真实强调标题；跨页未知则留空 | `qa_agent/rag/parsers.py`、`chunker.py` | 两栏、跨页与同块标题正文分离测试；原文画框 |
| 操作步骤不误判章节 | 对编号后操作动词作通用步骤识别；不按题号修补；To …: 程序标签不会持续标记后续独立正文 | `qa_agent/rag/chunker.py` | 操作步骤、To …: 程序标签与 Results 标题测试 |
| 无可靠章节时明示未知 | 索引记录 `section_location_status=unknown`；接口检索元数据返回定位可靠性；不伪造章节或框 | `qa_agent/rag/index.py`、`service.py` | 新索引 `index_meta.json`、实际 API 原始响应 |
| 数值回答保持原文对象、期间和单位 | 在已有 RAG 回答规则中补充实验数据集、模型、方法、shot 和比较基线约束；只问名称时按证据作简洁回答；增加显式研究机构/作者归属的本句引用核验，失败进入既有一次重试，trace 保留被拒原回答 | `qa_agent/rag/answer.py` | 原始响应、逐题 AI 核验 |
| 增量构建，保留旧证据 | 新建 `data/indexes/docs-d2-final-v4.3`；哈希核验同源 OCR 缓存和完全相同输入的真实 BGE 向量缓存 | `scripts/rebuild_d2_rag_sources.py` | `rebuild-v4.3/docs-audit.json`、`rebuild-v4.3/parse-events.json` |
| 用原文检验引用，而不是只看系统输出 | 按实际引用匹配冻结索引，再用原 PDF 物理页绘制真实框；机械检查与 AI 视觉判断分开记录 | `scripts/audit_d2_rag_locations.py` | `location-check-v4.3/citation-location-check.json`、`first-review-v4.3.json` |

## 已实际完成的模块验证与构建

- 针对解析、切块、索引、回答与 RAG 评测的模块测试：90 项通过，耗时 2.99 秒。原始输出为 `eval/artifacts/d2-final/rag/module-tests-v43-final.txt`。包括裁剪框原点、同高度两栏、长隐藏 OCR 扫描图、编号步骤、跨页未知章节、同块标题正文分离、混合强调注册商标标题、程序引导标签不继承到后续正文、显式机构归属必须由本句引用支持等有实际意义的测试。
- 最终索引实际摄入 13 个来源、5132 个片段，0 个文档解析失败。解析阶段真实渲染 OCR 26 个 PDF 页面；第二轮只在源文件与 OCR 算法哈希均一致时复用这些已真实运行的 OCR 页面。
- 索引使用既有 BGE-M3 ONNX int8、CPU、1024 维、最大长度 512、批次 2，沿用模型文件 SHA256 `0826f8c1ab9edf1801db86c61919d4d108e8bfc0b809ec823ad366882ff0b77d`。最终构建在校验原索引片段与向量哈希、模型与编码参数之后，复用 5063 个完全相同输入的真实向量，重新真实编码 69 个已变化输入。
- 最终片段 SHA256：`f21416522546616317c9b08f2c5c5f9d0b17dab8f5f2a0995f280bf3c8f9461c`；最终向量 SHA256：`99060a5f8c008b6999f66c4ab4cc7ce75152800c8bef8d77c5119cf0897ea764`。完整信息保存在 `data/indexes/docs-d2-final-v4.3/index_meta.json` 和 `eval/artifacts/d2-final/rag/rebuild-v4.3/docs-audit.json`。

## 实际命令

以下均在 `system` 项目根目录执行；用单独的本机 8011 API 运行既有 `api.main:app`，未在原 8000 评测运行时重启它。模型配置沿用本地安全配置，报告不包含真实 API 密钥。

```powershell
.\.venv\Scripts\python.exe -B -m pytest tests/test_rag_core.py tests/test_d2_rag.py tests/test_rag_eval.py tests/test_d2_rag_locations.py --basetemp=.runtime/pytest-rag-v43-attribution-final -q
.\.venv\Scripts\python.exe -B scripts/rebuild_d2_rag_sources.py --index-path data/indexes/docs-d2-final-v4.3 --evidence eval/artifacts/d2-final/rag/rebuild-v4.3 --parse-cache-from eval/artifacts/d2-final/rag/rebuild-v4.2 --vectors-from data/indexes/docs-d2-final-v4.2
$env:RAG_INDEX_PATH='data/indexes/docs-d2-final-v4.3'
.\.venv\Scripts\python.exe -B eval/run_eval.py --suite rag --split dev --draft-gold --run-id d2-final-v4.3-final --base-url http://127.0.0.1:8011 --output eval/artifacts/d2-final/rag/regression-v4.3 --timeout 240
.\.venv\Scripts\python.exe -B scripts/audit_d2_rag_locations.py --responses eval/artifacts/d2-final/rag/regression-v4.3/responses.jsonl --index data/indexes/docs-d2-final-v4.3 --output eval/artifacts/d2-final/rag/location-check-v4.3
```

## 本次失败、修复与保留记录

1. 初次 pytest 使用系统临时目录时触发沙箱权限错误；改用项目内独立临时目录。有效运行中暴露 PyMuPDF 同高度左右栏合在一个块的问题，按实际行位置拆分后回归通过。
2. 初轮真实 v4 回归已跑完 21/21，Hit@5 20/20、证据不足处理 1/1；原始结果仍在 `eval/artifacts/d2-final/rag/regression/`。其原文视觉核验发现论文 Results 正文的标题继承到 Experiments，随后采用通用的同块标题前缀提取修正，生成新 v4.1 索引并重新运行全部 21 道开发题。
3. v4.1 首次构建在实际向量编码结束后，包装脚本写相对缓存路径时异常，未生成可用索引元数据。已修正为先解析绝对路径再生成项目相对路径，并重新实际完成编码和索引。错误原文独立保存在 `eval/artifacts/d2-final/rag/rebuild-v4.1/failed-build-relative-path.txt`，没有把失败构建写成成功。

4. v4.1 原文复核暴露 ENERGY STAR® 标题中的普通商标小字影响整行强调识别；改为按实际字符权重核对强调，原图与测试均正确。v4.2 所有真实输出保存在 `regression-v4.2/`。第二遍 AI 核验确认 To use 程序标签不宜持续继承，现已通用排除，无法确定章节时标未知。
5. v4.3 构建包装脚本曾只核验 parser 文件而漏了导入的标题分类依赖，导致旧章节缓存仍可复用。现已加入该依赖哈希并重新实际解析，错误中间索引和构建证据独立保存在 `data/indexes/docs-d2-final-v4.3-cache-invalidation-error` 与 `rebuild-v4.3-cache-invalidation-error/`。
6. 仅加强提示没有可靠阻止机构归属与引用不匹配。实际输出变体从 research from 变为具名主体 identified；新增通用显式归属校验及真实 fixture，并保留此前原始输出在 `regression-v4.3-pre-subject-attribution/`，然后完成最终回归。该检查是保守的字面归属核验，不替代全量语义审核。

## 定位能力边界与人工审核

框是同一来源区域内实际文本行或块的外包框，可能覆盖整个段落，不能称为逐句、逐字精确高亮。物理页码从 1 开始，封面计页；坐标采用可见 CropBox 左上原点、未旋转 PDF 点坐标。图片 OCR 使用原始图片像素坐标，两种单位不得混用。

章节只有当前物理页同栏标题足以支持时才登记；扫描图或跨页续文缺可靠标题时明确为未知。已知的物理页和块框可核验，未知章节单独标记为证据不足，不据此宣称章节定位通过。扫描 OCR 警告表示仍需核对阅读顺序和识别文字，不能把警告当作已经解决多栏排版。

本报告和第一遍、第二遍 AI 核验均为 AI 判断，不填 A/B 签名，不填人工确认日期，不修改原题库的人工审核字段，也不自动替代人工签字。用户已认可原 21 道参考答案的结论可以在总体交付报告的独立确认记录中体现，原历史报告仍保留其当时的 draft 状态。


## 最终实际回归与两遍 AI 核验

最终全套原始记录为 `eval/artifacts/d2-final/rag/regression-v4.3/`，实际 API 8011，实际模型 `deepseek-flash`，实际索引 `data/indexes/docs-d2-final-v4.3`。21/21开发题均实际发起：19个SUCCEEDED、1个FAILED、1个EMPTY_RESULT。可回答题Hit@5为20/20，不足题处理1/1；前者是检索页/片段命中，不能当成21道系统回答都正确。

第一遍独立原文审读为 `eval/artifacts/d2-final/rag/first-review-v4.3.json` 和 `.md`：21参考答案建议通过；完整系统输出19建议通过、1有条件、1错误。实际23条引用全部真实匹配冻结索引；其中15条PDF物理页及块框经原文渲染核对、8条非PDF由原HTML/DOCX/Markdown/PNG核对。9条章节明确unknown、不计精确章节定位通过。未知章节与实际输出FAILED分别列出，不混成成功。

- `rag-03`最终全套真实FAILED：模型两次仅引包含期限的E6，却重复题干法律编号和年份，缺同句E1支持，严格数字门禁正确拒绝。参考答案仍正确，不能修改它迁就模型，也不能用旧轮成功掩盖当前失败。
- `rag-15`完整原文确有五种能力及ASQ/Forbes归属，但实际仅引用列表/摘要片段E2/E4，归属句在第10页左侧未引用正文；引用语义只能有条件通过。字面门禁覆盖部分研究from/by与具名主体结构，未覆盖所有被动语义表达；不称全量语义核验完成。

全套后按明确限定仅补通用数量/期限直接作答、不主动复述题干编号/年份提示，然后只运行受影响rag03 probe。该probe仍FAILED，故未运行v4.4全套，停止继续循环跑分。probe原始文件位于 `eval/artifacts/d2-final/rag/probe-v4.4-rag03/`；试用错误本机端点 `/chat` 的404记录单独保留在 `probe-v4.4-rag03-output.txt` 和 `failed-endpoint-command.json`，不计作模型结果。候选未改善后已仅回退这两条提示，恢复v4.3最终21题实际测试代码。候选完整提示、小差异及回退说明保存在probe目录；21题全套对应已恢复源码，失败probe独立保留。

第二遍由父任务独立读取原文、实际回答、画框及哈希记录，在总体D2交付报告记录；第一遍报告不会自行假填第二遍签核。仍需人工确认rag03系统失败处理和rag15归属引用条件，以及未知章节是否满足本阶段允许的定位粒度。原始人工审核状态、签名和日期保持不变。
