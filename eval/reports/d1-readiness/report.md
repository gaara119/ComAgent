# D1 SQL 评测记录

状态：READINESS_ONLY
题集：dev；选中 21 题；实际预测 0 题。
保留题预测：本次未运行
模型：deepseek-flash；Git commit：尚未提交。

未运行模型预测，不计算 EX。

需要处理：
- 本地 LLM_API_KEY 尚未配置；未调用模型，不能生成真实基线。
- gold 等待人工复核：sql-01, sql-02, sql-04, sql-05, sql-06, sql-07, sql-09, sql-10, sql-11, sql-13, sql-14, sql-15, sql-17, sql-18, sql-19, sql-21, sql-22, sql-24, sql-26, sql-27, sql-29
- 运行中的 API 未配置 LLM key。

## 溯源

```json
{
  "created_at_utc": "2026-10-10T11:31:36.010937+00:00",
  "git_commit": null,
  "working_tree_dirty": true,
  "frozen_tag": null,
  "dataset": "E:\\中国电子杯-赛题八\\system\\eval\\datasets\\nl2sql_chinook.jsonl",
  "dataset_sha256": "14ab118f0d325c8ab796a2802da78385c34619df809d13a2ad70d518943e4cfa",
  "source_sha256": [
    "e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e"
  ],
  "configured_model": "deepseek-flash",
  "api_base_url": "http://127.0.0.1:8000",
  "actual_models": [],
  "gold_review": "pending_human_review",
  "health": {
    "status": "ok",
    "stage": "D1",
    "database_ready": true,
    "llm_configured": false,
    "model": "deepseek-flash",
    "catalog_exists": true,
    "statement_timeout_ms": 5000,
    "max_rows": 200
  }
}
```
