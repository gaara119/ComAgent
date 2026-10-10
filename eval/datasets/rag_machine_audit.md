# D1 RAG 官方题库机器溯源核验

本文件记录机器完成的来源与页码核验，不签署人工业务审核，不声明模型回答准确率。

核验 20 个官方 text QA；全部来源与原页检查通过：True。
人工接受：0；本核验模型调用：0；保留题预测：0。

检查项：原官方问题/答案/QA记录一致、官方QA整文件SHA一致、原PDF SHA一致、text类型、物理页=官方index+1、引用为原PDF页连续子串。

| 题号 | 文档 | split | 物理页 | 来源及页核验 | 人工审核 |
|---|---|---|---:|---|---|
| rag-01 | ohr-finance-amd-2022 | holdout | 51 | 通过 | 待人工 |
| rag-02 | ohr-law-affiliate | dev | 1 | 通过 | 待人工 |
| rag-03 | ohr-law-affiliate | dev | 2 | 通过 | 待人工 |
| rag-04 | ohr-law-affiliate | holdout | 1 | 通过 | 待人工 |
| rag-05 | ohr-textbook-geology | dev | 1 | 通过 | 待人工 |
| rag-06 | ohr-textbook-geology | dev | 8 | 通过 | 待人工 |
| rag-07 | ohr-textbook-geology | dev | 14 | 通过 | 待人工 |
| rag-08 | ohr-textbook-geology | dev | 8 | 通过 | 待人工 |
| rag-09 | ohr-textbook-geology | holdout | 4 | 通过 | 待人工 |
| rag-10 | ohr-manual-macbook-air | dev | 65 | 通过 | 待人工 |
| rag-11 | ohr-manual-macbook-air | dev | 3 | 通过 | 待人工 |
| rag-12 | ohr-manual-macbook-air | dev | 67 | 通过 | 待人工 |
| rag-13 | ohr-manual-macbook-air | dev | 52 | 通过 | 待人工 |
| rag-14 | ohr-manual-macbook-air | holdout | 64 | 通过 | 待人工 |
| rag-15 | ohr-news-executive-insight | dev | 10 | 通过 | 待人工 |
| rag-16 | ohr-news-executive-insight | dev | 11 | 通过 | 待人工 |
| rag-17 | ohr-news-executive-insight | holdout | 8 | 通过 | 待人工 |
| rag-18 | ohr-academic-label-words | dev | 12 | 通过 | 待人工 |
| rag-19 | ohr-academic-label-words | dev | 6 | 通过 | 待人工 |
| rag-20 | ohr-academic-label-words | holdout | 2 | 通过 | 待人工 |

完整哈希与逐题布尔检查见 rag_machine_audit.json；人工审核表见 rag_review/rag_gold_review.md。
