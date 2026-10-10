# D1 RAG 题库与实际评测

`rag_ohr.jsonl` 中 20 题全部来自官方 `qas_v2.json`，保留原问题、答案和原 QA ID，无团队自拟题、无模型生成标准答案。仅挑单页 `evidence_source=text`，20 条引用均机器定位为原 PDF 指定物理页上的连续文字。**机器定位不等于人工接受 gold。**

固定划分为 14 dev / 6 holdout，六份文档各 1 道保留题。finance 仅有 1 道适合本次单页文本基线的 QA，因此此题放在保留集；开发集覆盖 law/textbook/manual/news/academic 五域，全文索引和完整题库覆盖六域。问题数量 finance1、law3、textbook5、manual5、news3、academic3。官方同题改写/相同事实不得跨 split，本次所选问题均为不同事实；保留集不默认运行。

## 人工 gold 审核

打开 `rag_review/rag_gold_review.md`，对照原 PDF 的物理页核对题意、标准答案、引用及页码。完成具体题目的人工核对后，才记录接受，例如：

```powershell
.\.venv\Scripts\python.exe scripts/review_rag_gold.py --accept rag-02,rag-03 --reviewer B
```

该命令绑定审核人与内容 SHA256；修改问题、答案、页码、文档哈希或 split 会使旧审核失效。单纯在 Markdown 打勾不会更改源题库。重新导出会覆盖手写备注，备注请另存。此交付全部 `needs_human_review`，未代替团队签署人工审核。

## 真实 API 评测

从项目根目录、API 已启动且索引构建完成时运行：

```powershell
# gold 尚未人工确认时，只运行开发集草稿探索
.\.venv\Scripts\python.exe -m eval.rag_run_eval --draft-gold

# 已人工接受全部开发题后，运行正式开发集
.\.venv\Scripts\python.exe -m eval.rag_run_eval
```

默认只预测 14 道 dev，实际 POST `/api/chat`，发送 route=doc 和该题唯一 doc_id。模型不获得 gold 答案、reference_text 或 gold 页码；完整请求响应、引用、步骤、耗时、实际检索方式及版本哈希留在 `eval/reports/rag_*`。

未就绪时生成 `READINESS_ONLY`，预测数为 0，不计算运行指标。运行报告拒绝覆盖已有报告目录。失败、超时、无引用均保留并计入分母。

自动指标包括状态成功、指定文档约束、引用原文子串、金标页候选检索命中、最终引用命中、有效 evidence_id，以及标准答案字符串在回答中是否出现。**这些是机械诊断，不是答案语义准确率或 groundedness。** 字符串未命中可能只是合理改写；命中也不能证明其余断言正确。实际回答的语义正确性、完整性及每项事实的引用支持需在每次报告的 `human_review.md` 中人工判断。

D1 不运行 6 道 holdout。未来冻结评测必须显式指定 `--split holdout --allow-holdout --frozen-tag 实际Git标签`，且标签指向当前 HEAD、工作目录干净、gold 已接受；`--draft-gold` 永不允许保留题。该开关不意味着现在应运行保留题。
