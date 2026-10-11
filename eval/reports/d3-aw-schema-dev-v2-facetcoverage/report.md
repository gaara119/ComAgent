# D3 AW schema 开发集实际模块评测

```json
{
  "status": "ACTUALLY_RUN_MODULE_DEV",
  "label_status": "pending_human_review",
  "created_at": "2026-10-11T18:11:30.559383+00:00",
  "case_count": 21,
  "holdout_predictions": 0,
  "configured_model": "local verified BGE-M3 ONNX int8",
  "dataset": "eval\\datasets\\d3\\aw_schema_link.dev.v2.jsonl",
  "dataset_sha256": "bfacfc7fec9e2ec32f1f2a2f8c9005502686be11ccb831cbc5242b438415ad88",
  "catalog_sha256": "359edf6b2e89b88f04d9d5a5d95364dd4a0013906e741b39748b28cfc084f69b",
  "index": "data\\indexes\\schema-aw-d3-v2",
  "mean_table_recall": 1.0,
  "mean_table_precision": 0.1448687555830413,
  "all_gold_recalled_cases": 21,
  "average_candidate_table_count": 10.952380952380953,
  "average_latency_ms": 60.0,
  "missing_gold_cases": [],
  "stage_scope": "D3 dual dense + column votes + value hints/RRF + Steiner; D4 pruning/ablation intentionally absent"
}
```

逐题候选、入选理由与缺失表在 responses.jsonl。该报告不计算NL2SQL EX，也不代替人工gold审核。
