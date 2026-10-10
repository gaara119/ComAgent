# D1 SQL 评测记录

状态：COMPLETED
题集：dev；选中 21 题；实际预测 21 题。
保留题预测：本次未运行
模型：deepseek-flash；Git commit：fe4c4b9bddc3dbc5e23aa1d0a7089f879e2be335。

草稿 gold 开发集探索值，等待人工核验：正确 19/21；90.48%。

全部失败、超时、误澄清和格式错误均计入分母。

错误分类：
- result_mismatch：2

逐题详情见 responses.jsonl；其中保留原请求、响应、SQL、步骤和判断。

## 溯源

```json
{
  "created_at_utc": "2026-10-10T11:39:35.485392+00:00",
  "git_commit": "fe4c4b9bddc3dbc5e23aa1d0a7089f879e2be335",
  "working_tree_dirty": false,
  "frozen_tag": null,
  "dataset": "E:\\中国电子杯-赛题八\\system\\eval\\datasets\\nl2sql_chinook.jsonl",
  "dataset_sha256": "14ab118f0d325c8ab796a2802da78385c34619df809d13a2ad70d518943e4cfa",
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
