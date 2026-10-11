# D2 SQL 评测记录

状态：READINESS_ONLY
题集：dev；选中 35 题；实际预测 0 题。
保留题预测：本次未运行
模型：deepseek-flash；Git commit：be79386147942e068b36ce7eb53cc4f95e200422。

未运行模型预测，不计算 EX。

需要处理：
- gold 等待人工复核：sql-01, sql-02, sql-04, sql-05, sql-06, sql-07, sql-09, sql-10, sql-11, sql-13, sql-14, sql-15, sql-17, sql-18, sql-19, sql-21, sql-22, sql-24, sql-26, sql-27, sql-29, sql-31, sql-32, sql-33, sql-34, sql-35, sql-36, sql-37, sql-38, sql-39, sql-40, sql-41, sql-42, sql-43, sql-44

## 溯源

```json
{
  "created_at_utc": "2026-10-10T17:56:39.840229+00:00",
  "git_commit": "be79386147942e068b36ce7eb53cc4f95e200422",
  "working_tree_dirty": true,
  "frozen_tag": null,
  "dataset": "eval/datasets/nl2sql_chinook_d2.jsonl",
  "dataset_sha256": "ea6009fc9d05e14b351234819247ac7664f34cde3b504d13ce4fa8c6e048f4e5",
  "source_sha256": [
    "e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e"
  ],
  "configured_model": "deepseek-flash",
  "api_base_url": "http://127.0.0.1:8000",
  "run_id": "d2-formal-review-gate",
  "comparison_policy": "global column mapping; duplicate rows preserved; continuous numbers 2dp, integer columns exact",
  "actual_models": [],
  "gold_review": "pending_human_review",
  "health": {
    "status": "ok",
    "stage": "D2",
    "database_ready": true,
    "llm_configured": true,
    "model": "deepseek-flash",
    "catalog_exists": true,
    "statement_timeout_ms": 5000,
    "max_rows": 200
  }
}
```
