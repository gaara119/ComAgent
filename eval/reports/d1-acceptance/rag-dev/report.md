# D1 RAG 实际 API 开发集记录

状态：COMPLETED
题集：dev；选中 14；实际 API 预测 14。
gold：draft；模型：deepseek-flash。

全文索引涵盖六域。20 题全集涵盖六域；14 道开发题涵盖五域，唯一入选金融题留在保留集。
保留题预测：0；未运行

## 自动检查

这些数值检查调用与引用的机械条件，不是答案语义准确率。所有失败计入选中题目分母。

| 检查 | 通过/题数 |
|---|---:|
| 接口 SUCCEEDED | 14/14 |
| 有实际引用证据 | 14/14 |
| 引用全部来自指定文档 | 14/14 |
| 引用文字全部是所标 PDF 物理页的原文子串 | 14/14 |
| 最终引用至少命中一个金标物理页 | 14/14 |
| 检索候选至少命中一个金标物理页 | 14/14 |
| 答案带有实际 evidence_id | 14/14 |
| 标准答案字符串在回答中出现（仅表面诊断） | 10/14 |

平均耗时：3184 ms。

**答案语义是否正确、每项断言是否受原文支持：全部等待人工复核，未计算 RAG 答案准确率或 groundedness。**

逐题原请求、原响应、实际 evidence_id/page、步骤、比较结果见 responses.jsonl；人工逐题记录见 human_review.md。

## 溯源

```json
{
  "created_at_utc": "2026-10-10T12:48:34.986986+00:00",
  "git_commit": "596214c95eb2736b2e74efac244a7e177d8c6482",
  "working_tree_dirty": false,
  "dataset_sha256": "f52197dcdd031bdbab51ad2b74da8dce0b0777cbcdad3f7803934fbeb00cfd98",
  "source_pdf_sha256": [
    "035b1659c5305a0c8157594cf41446fe72ade8d48efa99eb036dfa522d3431c4",
    "48981bbfdaf170bfc2ffceae813f17b49e528cb3cde75bac3b48b532b30e4274",
    "a4a646e9e36567c91424c29b05790d04b780df57f05342758f4a63e2b2bdbeef",
    "d99de99131b4d8a5471d3e3d96befaa1e6152560d12a93f854c5dd95e54225aa",
    "e7be7af7c911cccf6d391934ef062db94d10b1496659828d649af36201616612"
  ],
  "configured_model": "deepseek-flash",
  "actual_models": [
    "deepseek-flash"
  ],
  "retrieval_methods": [
    "bm25+bge-m3_dense_rrf"
  ],
  "frozen_tag": null,
  "gold_review": "draft",
  "api_base_url": "http://127.0.0.1:8000",
  "answer_metrics": "mechanical diagnostics only; semantic correctness and claim grounding unreviewed",
  "index_meta_sha256": "e468f0f3a197a1c6b7d9bfe275ab178a0ce6e401a6ab54424cfce11994b7bd4a",
  "index_metadata": {
    "index_version": 2,
    "created_at": "2026-10-10T12:43:03.123218+00:00",
    "retrieval_method": "bm25+bge-m3_dense_rrf",
    "manifest_hash": "d40d374a5b29d8efca0adda8e3c2f5c1b8ddac1e1f6e29a2daec3d3e1f80831e",
    "documents": [
      {
        "doc_id": "ohr-finance-amd-2022",
        "title": "AMD 2022 Form 10-K",
        "path": "data/docs/raw/finance/AMD_2022_10K.pdf",
        "content_hash": "a3bd74088fae0ad4aa03d04998a1f4c64fd0b3c693841601b0ac49b46cf5c1f4",
        "source_url": "https://huggingface.co/datasets/opendatalab/OHR-Bench/resolve/7f833e3eda9a571a9ea545a8f6d476fa1685033d/pdfs.zip",
        "license": "HF card: CC-BY-4.0; upstream PDF statement: research only, non-commercial; original rights retained",
        "language": "en",
        "domain": "finance",
        "page_count": 121,
        "text_page_count": 121,
        "chunk_count": 953,
        "blank_pages": []
      },
      {
        "doc_id": "ohr-law-affiliate",
        "title": "Gulf South Medical Supply Affiliate Agreement (1997)",
        "path": "data/docs/raw/law/GULFSOUTHMEDICALSUPPLYINC_12_24_1997-EX-4-AFFILIATE AGREEMENT.pdf",
        "content_hash": "a4a646e9e36567c91424c29b05790d04b780df57f05342758f4a63e2b2bdbeef",
        "source_url": "https://huggingface.co/datasets/opendatalab/OHR-Bench/resolve/7f833e3eda9a571a9ea545a8f6d476fa1685033d/pdfs.zip",
        "license": "HF card: CC-BY-4.0; upstream PDF statement: research only, non-commercial; original rights retained",
        "language": "en",
        "domain": "law",
        "page_count": 8,
        "text_page_count": 8,
        "chunk_count": 42,
        "blank_pages": []
      },
      {
        "doc_id": "ohr-textbook-geology",
        "title": "The Geology of the Country Around Holmfirth and Glossop (excerpt)",
        "path": "data/docs/raw/textbook/DUDE_89a3da3457ce1451bc01e4b83fb95f04.pdf",
        "content_hash": "e7be7af7c911cccf6d391934ef062db94d10b1496659828d649af36201616612",
        "source_url": "https://huggingface.co/datasets/opendatalab/OHR-Bench/resolve/7f833e3eda9a571a9ea545a8f6d476fa1685033d/pdfs.zip",
        "license": "HF card: CC-BY-4.0; upstream PDF statement: research only, non-commercial; original rights retained",
        "language": "en",
        "domain": "textbook",
        "page_count": 20,
        "text_page_count": 20,
        "chunk_count": 114,
        "blank_pages": []
      },
      {
        "doc_id": "ohr-manual-macbook-air",
        "title": "MacBook Air User Guide (archival edition)",
        "path": "data/docs/raw/manual/Macbook_air.pdf",
        "content_hash": "d99de99131b4d8a5471d3e3d96befaa1e6152560d12a93f854c5dd95e54225aa",
        "source_url": "https://huggingface.co/datasets/opendatalab/OHR-Bench/resolve/7f833e3eda9a571a9ea545a8f6d476fa1685033d/pdfs.zip",
        "license": "HF card: CC-BY-4.0; upstream PDF statement: research only, non-commercial; original rights retained",
        "language": "en",
        "domain": "manual",
        "page_count": 76,
        "text_page_count": 71,
        "chunk_count": 166,
        "blank_pages": [
          4,
          24,
          38,
          74,
          76
        ]
      },
      {
        "doc_id": "ohr-news-executive-insight",
        "title": "Executive Insight Healthcare Magazine (archival excerpt)",
        "path": "data/docs/raw/news/DUDE_62ba680b413005aa9f018454c4ab4c43.pdf",
        "content_hash": "48981bbfdaf170bfc2ffceae813f17b49e528cb3cde75bac3b48b532b30e4274",
        "source_url": "https://huggingface.co/datasets/opendatalab/OHR-Bench/resolve/7f833e3eda9a571a9ea545a8f6d476fa1685033d/pdfs.zip",
        "license": "HF card: CC-BY-4.0; upstream PDF statement: research only, non-commercial; original rights retained",
        "language": "en",
        "domain": "news",
        "page_count": 20,
        "text_page_count": 19,
        "chunk_count": 128,
        "blank_pages": [
          1
        ]
      },
      {
        "doc_id": "ohr-academic-label-words",
        "title": "Label Words are Anchors: An Information Flow Perspective for Understanding In-Context Learning",
        "path": "data/docs/raw/academic/2305.14160v4.pdf",
        "content_hash": "035b1659c5305a0c8157594cf41446fe72ade8d48efa99eb036dfa522d3431c4",
        "source_url": "https://huggingface.co/datasets/opendatalab/OHR-Bench/resolve/7f833e3eda9a571a9ea545a8f6d476fa1685033d/pdfs.zip",
        "license": "HF card: CC-BY-4.0; upstream PDF statement: research only, non-commercial; original rights retained",
        "language": "en",
        "domain": "academic",
        "page_count": 16,
        "text_page_count": 16,
        "chunk_count": 124,
        "blank_pages": []
      }
    ],
    "chunk_count": 1527,
    "chunks_sha256": "3af77dcca0b2938b2493cd68e849e86c247c45a4a8462d5a7bd457f6a37031b9",
    "parsing": {
      "text": "pdfplumber text layer",
      "layout": "PyMuPDF.get_text(dict)",
      "bbox_scope": "union_of_text_blocks",
      "coordinate_system": "PDF points; top-left origin"
    },
    "chunking": {
      "max_chars": 600,
      "overlap": 80,
      "cross_page": false,
      "boundary_policy": "complete_sentence_or_table_line",
      "incomplete_chunk_count": 226
    },
    "dense_embedding": {
      "model": "BAAI/bge-m3",
      "conversion_repo": "Xenova/bge-m3",
      "revision": "4de13258303883538bd53b696b452bf8099f0858",
      "source": "https://huggingface.co/Xenova/bge-m3/tree/4de13258303883538bd53b696b452bf8099f0858",
      "license": "MIT",
      "runtime": "onnxruntime",
      "device": "cpu",
      "weight_type": "QInt8",
      "pooling": "CLS",
      "normalization": "L2",
      "dimensions": 1024,
      "downloaded_at_utc": "2026-10-10T12:06:50.568592+00:00",
      "files": [
        {
          "path": "onnx/model_quantized.onnx",
          "size": 569694530,
          "sha256": "0826f8c1ab9edf1801db86c61919d4d108e8bfc0b809ec823ad366882ff0b77d"
        },
        {
          "path": "tokenizer.json",
          "size": 17082821,
          "sha256": "6710678b12670bc442b99edc952c4d996ae309a7020c1fa0096dd245c2faf790"
        },
        {
          "path": "tokenizer_config.json",
          "size": 1173,
          "sha256": "7e4c1cc848840aeccdd763458c18dd525eb0f795c992e00ebe9c28554e7db2d4"
        },
        {
          "path": "config.json",
          "size": 770,
          "sha256": "734a79bf12d388c1467a4e3ab625f45de7f6906cffcfb93a1eca1787504bed95"
        },
        {
          "path": "quantize_config.json",
          "size": 834,
          "sha256": "4d98142624026cf78a40b36896ae1b1bada4faf185b77784a03b6995324aa176"
        }
      ],
      "max_length": 512,
      "batch_size": 2,
      "providers": [
        "CPUExecutionProvider"
      ],
      "mode": "bge-m3_onnx_int8",
      "model_id": "BAAI/bge-m3",
      "model_revision": "4de13258303883538bd53b696b452bf8099f0858",
      "model_sha256": "0826f8c1ab9edf1801db86c61919d4d108e8bfc0b809ec823ad366882ff0b77d",
      "enabled": true,
      "dimension": 1024,
      "vectors_sha256": "009024fa8886a35d104964d7224634f5ec3141a5f2d7f09647c62c65f54a925b"
    }
  },
  "configured_retrieval": {
    "top_k": 5,
    "embedding_max_length": 512,
    "embedding_device": "cpu",
    "embedding_quantization": "int8",
    "answer_mode": "llm"
  },
  "independent_source_extractors": [
    "pypdf",
    "PyMuPDF",
    "pdfplumber (layout=False, x_tolerance=2, y_tolerance=3)"
  ],
  "api_health": {
    "status": "ok",
    "stage": "D1",
    "database_ready": true,
    "llm_configured": true,
    "model": "deepseek-flash",
    "catalog_exists": true,
    "statement_timeout_ms": 5000,
    "max_rows": 200
  }
}
```
