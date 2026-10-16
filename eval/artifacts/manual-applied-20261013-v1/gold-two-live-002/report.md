# D2 SQL 评测记录

状态：COMPLETED
题集：dev；选中 2 题；实际预测 2 题。
保留题预测：本次未运行
模型：deepseek-flash；Git commit：4bf59692b06fce3bd4d3153a2319804aec931ca3。

EX：正确 2/2；100.00%。

全部失败、超时、误澄清和格式错误均计入分母。

错误分类：
- 无

逐题详情见 responses.jsonl；其中保留原请求、响应、SQL、步骤和判断。

## 溯源

```json
{
  "created_at_utc": "2026-10-14T05:22:38.055540+00:00",
  "git_commit": "4bf59692b06fce3bd4d3153a2319804aec931ca3",
  "working_tree_dirty": true,
  "frozen_tag": null,
  "dataset": "eval/artifacts/manual-applied-20261013-v1/test-inputs/gold-two-v3.jsonl",
  "dataset_sha256": "ff36e202374f73971ce4327a50d0bf95c1c6978ea88d42f97edb147be8edfeae",
  "source_sha256": [
    "e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e"
  ],
  "configured_model": "deepseek-flash",
  "api_base_url": "http://127.0.0.1:8000",
  "run_id": "gold-two-v3-live-002",
  "comparison_policy": "oct12-plan-ex-v1: global column mapping, proven descriptive extras allowed, duplicates and requested row order preserved; declared continuous numbers 2dp, integers exact; legacy comparison separately retained",
  "actual_models": [
    "deepseek-flash"
  ],
  "gold_review": "human_accepted",
  "health": {
    "status": "ok",
    "stage": "D4",
    "database_ready": true,
    "aw_database_ready": true,
    "sql_prompt_sha256": {
      "single_table_loaded": "e654d113a970693751744c295310c2edfb99b12898ad4368a02e25743956fe4a",
      "multi_table_file": "1b27c6a7e75d1443f998227e8cc0e3d9345ca380598708aa40d31d9804feed60"
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
    "aw_schema_index_exists": true,
    "aw_schema_mode": "subgraph"
  }
}
```
