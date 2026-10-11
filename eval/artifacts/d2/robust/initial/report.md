# D2 SQL 评测记录

状态：COMPLETED
题集：dev；选中 21 题；实际预测 21 题。
保留题预测：本次未运行
模型：deepseek-flash；Git commit：be79386147942e068b36ce7eb53cc4f95e200422。

草稿 gold 开发集探索值，等待人工核验：正确 18/21；85.71%。

全部失败、超时、误澄清和格式错误均计入分母。

错误分类：
- result_mismatch：1
- value_link_invalid_candidate：2

逐题详情见 responses.jsonl；其中保留原请求、响应、SQL、步骤和判断。

## 溯源

```json
{
  "created_at_utc": "2026-10-10T17:58:42.307624+00:00",
  "git_commit": "be79386147942e068b36ce7eb53cc4f95e200422",
  "working_tree_dirty": true,
  "frozen_tag": null,
  "dataset": "eval/datasets/robust.jsonl",
  "dataset_sha256": "81e820e4da818dee347bf96acbebe07a26a44b98ce9e11fae33dc58304044d1b",
  "source_sha256": [
    "e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e"
  ],
  "configured_model": "deepseek-flash",
  "api_base_url": "http://127.0.0.1:8000",
  "run_id": "d2-robust-initial",
  "comparison_policy": "global column mapping; duplicate rows preserved; continuous numbers 2dp, integer columns exact",
  "actual_models": [
    "deepseek-flash"
  ],
  "gold_review": "draft",
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
