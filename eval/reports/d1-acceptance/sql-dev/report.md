# D1 SQL 评测记录

状态：COMPLETED
题集：dev；选中 21 题；实际预测 21 题。
保留题预测：本次未运行
模型：deepseek-flash；Git commit：379bfdf95725c8dd193dd0524b751052f34cec47。

草稿 gold 开发集探索值，等待人工核验：正确 21/21；100.00%。

全部失败、超时、误澄清和格式错误均计入分母。

错误分类：
- 无

逐题详情见 responses.jsonl；其中保留原请求、响应、SQL、步骤和判断。

## 溯源

```json
{
  "created_at_utc": "2026-10-10T12:46:21.566546+00:00",
  "git_commit": "379bfdf95725c8dd193dd0524b751052f34cec47",
  "working_tree_dirty": false,
  "frozen_tag": null,
  "dataset": "E:\\中国电子杯-赛题八\\system\\eval\\datasets\\nl2sql_chinook_d1_acceptance.jsonl",
  "dataset_sha256": "d7ecb412982761ce746565a7d847058567cc13d60d95462bf0c6d431bc50c51c",
  "source_sha256": [
    "e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e"
  ],
  "configured_model": "deepseek-flash",
  "api_base_url": "http://127.0.0.1:8000",
  "actual_models": [
    "deepseek-flash"
  ],
  "gold_review": "draft",
  "health": {
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
