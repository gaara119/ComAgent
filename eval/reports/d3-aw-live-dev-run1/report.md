# D3 AW 开发集真实问答评测

```json
{
  "status": "ACTUALLY_RUN_DEV_EXPLORATORY",
  "prediction_count": 21,
  "holdout_predictions": 0,
  "correct": 21,
  "exploratory_ex": 1.0,
  "all_failures_in_denominator": true,
  "failure_categories": {},
  "actual_model_attempts": 22,
  "actual_models": [
    "deepseek-flash"
  ],
  "usage": {
    "prompt_tokens": 219558,
    "completion_tokens": 2809,
    "total_tokens": 222367
  },
  "average_latency_ms": 4304.809523809524,
  "gold_review": "pending_human_review",
  "provenance": {
    "created_at": "2026-10-11T19:01:32.609219+00:00",
    "configured_model": "deepseek-flash",
    "configured_llm_base_url": "https://api.deepseek.com",
    "dataset": "eval\\datasets\\d3\\aw_schema_link.dev.v2.jsonl",
    "dataset_sha256": "bfacfc7fec9e2ec32f1f2a2f8c9005502686be11ccb831cbc5242b438415ad88",
    "git_commit": "ca0d551541acbfec6ca5642ab3c48e3e44ab326d",
    "working_tree_dirty": true,
    "base_url": "http://127.0.0.1:8000",
    "gold_human_status": "pending_human_review",
    "actual_health": {
      "status": "ok",
      "stage": "D3",
      "database_ready": true,
      "aw_database_ready": true,
      "sql_prompt_sha256": {
        "single_table_loaded": "e654d113a970693751744c295310c2edfb99b12898ad4368a02e25743956fe4a",
        "multi_table_file": "1a907b8b5f2877b8565e6dc1aee0cea149aaef7a26fabb2e4ce873751d2ed205"
      },
      "llm_configured": true,
      "model": "deepseek-flash",
      "catalog_exists": true,
      "statement_timeout_ms": 5000,
      "max_rows": 200,
      "llm_call_max_attempts": 3,
      "llm_request_max_attempts": 12,
      "aw_configured": true,
      "aw_catalog_exists": true,
      "aw_schema_index_exists": true
    }
  },
  "interpretation": "本项目合成开发集自动结果，非正式成绩；原始失败完整保留，不读取保留内容、不预测保留。"
}
```

原始请求、真实响应、SQL、步骤、usage及失败见 responses.jsonl。gold待人工最终审核，EX为探索值。
