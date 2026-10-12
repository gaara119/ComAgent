# D2 SQL 评测记录

状态：COMPLETED
题集：dev；选中 35 题；实际预测 35 题。
保留题预测：本次未运行
模型：deepseek-flash；Git commit：d728e3b1e896e98a5a5fa1a5c0f47c125a88478f。

草稿 gold 开发集探索值，等待人工核验：正确 34/35；97.14%。

全部失败、超时、误澄清和格式错误均计入分母。

错误分类：
- result_mismatch：1

逐题详情见 responses.jsonl；其中保留原请求、响应、SQL、步骤和判断。

## 溯源

```json
{
  "created_at_utc": "2026-10-12T16:55:23.987066+00:00",
  "git_commit": "d728e3b1e896e98a5a5fa1a5c0f47c125a88478f",
  "working_tree_dirty": true,
  "frozen_tag": null,
  "dataset": "eval/artifacts/d2-final/review/sql-dev-v1.jsonl",
  "dataset_sha256": "7b4c18f203ce0d88f38837f0c788cbcff142b559dc70d3f281990a2d47175f35",
  "source_sha256": [
    "e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e"
  ],
  "configured_model": "deepseek-flash",
  "api_base_url": "http://127.0.0.1:8000",
  "run_id": "oct12-sql-final-003",
  "comparison_policy": "oct12-plan-ex-v1: global column mapping, proven descriptive extras allowed, duplicates and requested row order preserved; declared continuous numbers 2dp, integers exact; legacy comparison separately retained",
  "actual_models": [
    "deepseek-flash"
  ],
  "gold_review": "draft",
  "health": {
    "status": "ok",
    "stage": "D3",
    "database_ready": true,
    "aw_database_ready": true,
    "sql_prompt_sha256": {
      "single_table_loaded": "e654d113a970693751744c295310c2edfb99b12898ad4368a02e25743956fe4a",
      "multi_table_file": "31c4764bb84a17edf230560fdefdf2e5119d531ba50100b1895b77342803c904"
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
}
```
