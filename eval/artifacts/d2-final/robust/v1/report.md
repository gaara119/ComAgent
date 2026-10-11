# D2 SQL 评测记录

状态：COMPLETED
题集：dev；选中 21 题；实际预测 21 题。
保留题预测：本次未运行
模型：deepseek-flash；Git commit：b76e0fd016abc2805f88aa11a395e5286d62461a。

草稿 gold 开发集探索值，等待人工核验：正确 20/21；95.24%。

全部失败、超时、误澄清和格式错误均计入分母。

错误分类：
- needs_clarification：1

逐题详情见 responses.jsonl；其中保留原请求、响应、SQL、步骤和判断。

## 溯源

```json
{
  "created_at_utc": "2026-10-11T17:53:57.745776+00:00",
  "git_commit": "b76e0fd016abc2805f88aa11a395e5286d62461a",
  "working_tree_dirty": true,
  "frozen_tag": null,
  "dataset": "eval/artifacts/d2-final/review/robust-dev-v1.jsonl",
  "dataset_sha256": "1d6c7732b5196e7146e3b3f01fe4f9ccb24ad354c6b20776631192c605d213f7",
  "source_sha256": [
    "e3fde5c1a5b51a2a91429a702c9ca6e69ba56e6c7f5e112724d70c3d03db695e"
  ],
  "configured_model": "deepseek-flash",
  "api_base_url": "http://127.0.0.1:8000",
  "run_id": "d2-user-audit-v1",
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
