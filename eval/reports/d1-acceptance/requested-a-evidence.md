# 用户逐项 D1 清单：A 与共同协议核查证据

检查时间（UTC）：2026-10-10T13:43:42.192391+00:00。审核者 Codex / d1_a_exact_check，类型 AI。

本文件追加核查证据，不覆盖旧报告、不更改 gold 人工接受、不运行保留题模型预测。最新 PG 查询只读；模型历史成绩从保存的实际响应读取。

## 本次确认和补齐

真实新增 `@traced` 装饰器，已接入实际 SQL 执行；移除调用方原外层步骤以免双计。返回协议和 `schemas.py` 没有改动。新 8 项测试与相关回归共 39 passed / 0 skipped / 2.51s，真实模型调用 0。

实际 PostgreSQL 为 11 张表、64 列、**11 条外键约束**。旧文案的 13 与原始 a-review.json 不符，主验收报告已更正为 11；不倒写原始结果。

用户于 2026-10-10（America/Chicago）明确回复“双方已核对并同意当前协议”，当前 schemas.py 及物理页 1 起调整已确认，状态为 AGREED_USER_CONFIRMED。历史两人是否曾共同手写文件仍未核查；不将当前确认描述为历史共同手写或独立电子签名。确认绑定当前文件 SHA256 60b2816559f347dd60734f80563ae75fb453ab3903b528ed2d6075316b190445，后续实质改动仍须双方重新同意。

## 逐项结果

### COMMON_SCHEMA：一起写 schemas.py，之后更改必须 A/B 两人同意

状态：**AGREED_USER_CONFIRMED**。

- Step、Evidence、IntentContract、AnswerEnvelope 已实现并同时用于 API/SQL/RAG/UI
- 用户明确确认双方已核对并同意当前协议，当前版本共同同意已完成；历史两人共同手写未核查
- 原计划 Evidence.page 从 0 开始，当前协议从 1 开始且 ge=1；用户确认已包含此调整，本次不修改 schemas.py
- 确认绑定当前 SHA256 60b2816559f347dd60734f80563ae75fb453ab3903b528ed2d6075316b190445；后续实质内容变化必须重新取得双方同意

证据：

- [schemas.py](<E:/中国电子杯-赛题八/system/qa_agent/schemas.py:34>)
- [schemas.py](<E:/中国电子杯-赛题八/system/qa_agent/schemas.py:43>)
- [schemas.py](<E:/中国电子杯-赛题八/system/qa_agent/schemas.py:76>)
- [共享协议确认.md](<E:/中国电子杯-赛题八/system/notes/共享协议确认.md>)
- [requested-shared-evidence.json](<E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/requested-shared-evidence.json>)

### A01：Compose 起 Chinook PG；qa_reader；表名与年份

状态：**PASS**。

- Compose 服务 chinook-pg 为 running/healthy；PostgreSQL 16.15
- 只读 qa_reader：11 表 SELECT=true/write=false；非超级用户，无创建库/角色/复制/RLS 绕过权限
- public 的 11 表均 snake_case，64 列，11 条实际外键约束
- invoice 2021-01-01T00:00:00 至 2025-12-22T00:00:00，5 个年份 2021–2025；只读默认 on、statement_timeout=5s
- 旧文案的 13 外键已由主验收报告更正为实际 11；原始数据库/JSON 记录保持

证据：

- [docker-compose.yml](<E:/中国电子杯-赛题八/system/docker-compose.yml:4>)
- [bootstrap_db.py](<E:/中国电子杯-赛题八/system/scripts/bootstrap_db.py:127>)
- [db_check.json](<E:/中国电子杯-赛题八/system/data/db/db_check.json>)
- [chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml>)
- [a-review.json](<E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/a-review.json>)

### A02：查 /models 真实 model id 写入 .env；测试 JSON 输出

状态：**PASS_EQUIVALENT_SDK_REQUEST**。

- scripts/check_llm.py 实际调用 OpenAI-compatible SDK models.list，等价 GET /models；未按字面 curl 运行，凭据仅在本地读入请求
- 2026-10-10T11:37:18Z 记录模型 deepseek-flash，账号可用列表 deepseek-flash/deepseek-v4-pro
- 真实 JSON probe ok=true/message=接入成功，response_format=json_object；1 次 LLM、136 total_tokens、JSON 字段校验成功
- 当前 Settings 读入的 model 仍为 deepseek-flash；未读取或输出 .env 内容与密钥；无需降级为纯文本 JSON

证据：

- [model-check.json](<E:/中国电子杯-赛题八/system/notes/model-check.json>)
- [check_llm.py](<E:/中国电子杯-赛题八/system/scripts/check_llm.py:22>)
- [llm.py](<E:/中国电子杯-赛题八/system/qa_agent/llm.py:44>)
- [llm.py](<E:/中国电子杯-赛题八/system/qa_agent/llm.py:92>)

### A03：llm.py 统一调用/超时/重试/token；trace.py @traced

状态：**PASS_AFTER_FIX**。

- JsonLLM 统一模型调用：60s 默认超时，SDK 隐藏重试关闭，默认请求内总尝试上限 3（包含 SQL 修复/JSON 和网络重试），真实 usage 写 Step
- 本次发现旧实现只有 TraceRecorder.step，已新增真实 @traced 并接入 execute_sql；pipeline 外层 sql_exec 已移除避免双计
- 仅显式白名单 sql/db_id/row_count/columns/truncated 进入摘要，不自动记录 args/kwargs 或 DSN；错误利用原 step 做脱敏并保留原异常
- 同步/异步工具可用；trace 显式属于请求，无共享全局列表；Step 和所有返回协议保持不变
- 针对性回归 39 passed/0 skipped，2.51s；含新 8 项 trace 测试，均未调用真实模型

证据：

- [llm.py](<E:/中国电子杯-赛题八/system/qa_agent/llm.py:30>)
- [trace.py](<E:/中国电子杯-赛题八/system/qa_agent/trace.py:60>)
- [executor.py](<E:/中国电子杯-赛题八/system/qa_agent/sql/executor.py:69>)
- [pipeline.py](<E:/中国电子杯-赛题八/system/qa_agent/pipeline.py:106>)
- [test_trace.py](<E:/中国电子杯-赛题八/system/tests/test_trace.py>)

### A04：NL2SQL v0：目录→生成→SQLGlot 校验→只读执行

状态：**PASS**。

- 真实结构目录由 PG 导出，load_catalog→generate_sql→validate_sql→execute_sql
- SQLGlot AST + qualification 验证真实表列、函数及完整作用域；单业务表限定；拒绝写操作、多语句、未知列与无业务表常量
- executor 使用新只读事务、server cursor/max 200 行、5s 服务器超时；NULL、0、空表严格区分
- 修正版 21 dev 实际模型预测 21/21 执行结果匹配，exploratory_ex=1.0，平均 3405.886ms；正式分数待人工 gold 接受

证据：

- [pipeline.py](<E:/中国电子杯-赛题八/system/qa_agent/pipeline.py:80>)
- [pipeline.py](<E:/中国电子杯-赛题八/system/qa_agent/pipeline.py:89>)
- [pipeline.py](<E:/中国电子杯-赛题八/system/qa_agent/pipeline.py:94>)
- [pipeline.py](<E:/中国电子杯-赛题八/system/qa_agent/pipeline.py:106>)
- [validator.py](<E:/中国电子杯-赛题八/system/qa_agent/sql/validator.py:67>)
- [executor.py](<E:/中国电子杯-赛题八/system/qa_agent/sql/executor.py:86>)
- [report.json](<E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/sql-dev/report.json>)

### A05：30 道单表题；gold 逐条跑并保存结果；run_eval.py 计算 EX

状态：**DELIVERED_FORMAL_REVIEW_PENDING**。

- 原 30 题＝21 dev/9 holdout，9 类；gold 实际执行 30 次、30/30 原记录逐字一致，保存 gold_sql/gold_columns/gold_result/review_hash
- 独立修正版仅改 sql-11/22/24，27 项与父题集相同、保留 9 题相同；3 条改动 SQL 已实际执行保存
- sql-11 正确 ROUND(AVG(total),2)=5.65；sql-22/24明确 first_name 不包含 last_name
- run_eval 调 compare_results，按成功匹配数量/全部选中题计算 EX；失败计入分母，保存请求/响应、实际模型/耗时/版本
- 当前人工接受 0/30，正式评测被阻止；现有 21/21 属于新题集探索分数，不能覆盖原 19/21；保留题模型预测 0

证据：

- [nl2sql_chinook.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook.jsonl>)
- [nl2sql_chinook_d1_acceptance.jsonl](<E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.jsonl>)
- [nl2sql_chinook_d1_acceptance.manifest.json](<E:/中国电子杯-赛题八/system/eval/datasets/nl2sql_chinook_d1_acceptance.manifest.json>)
- [a-review.json](<E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/a-review.json>)
- [run_eval.py](<E:/中国电子杯-赛题八/system/eval/run_eval.py:152>)
- [run_eval.py](<E:/中国电子杯-赛题八/system/eval/run_eval.py:181>)
- [metrics.py](<E:/中国电子杯-赛题八/system/eval/metrics.py:85>)

### A06：跑附录 C Top 艺术家 SQL 并给 B 名单

状态：**PASS**。

- 已保存原查询 SQL、Top10 名单和收入定义；本次只读重新查数与交接数据完全一致
- Top3：Iron Maiden 138.60、U2 105.93、Metallica 90.09；未推断币种
- A_to_B_chinook.{json,md} 已进双方共享私有 Git；名单含 Lost/The Office 电视内容，后续知识库需核对实体类型
- 当前可证明材料在共享仓库，不证明 B 已另行阅读；跨源文档实现属于后续计划

证据：

- [check_db.py](<E:/中国电子杯-赛题八/system/scripts/check_db.py:18>)
- [A_to_B_chinook.json](<E:/中国电子杯-赛题八/system/data/handoff/A_to_B_chinook.json>)
- [A_to_B_chinook.md](<E:/中国电子杯-赛题八/system/data/handoff/A_to_B_chinook.md>)
- [B接口交接.md](<E:/中国电子杯-赛题八/system/notes/B接口交接.md:132>)

### A07：跑地区口径 SQL 并决定 03 演示例子是否更换

状态：**PASS_DECISION_RECORDED**。

- 实际比较 412 张发票，非空不同数 0、NULL-aware不同数 0、含 NULL 数 0；与保存交接记录完全一致
- 客户所在地与账单地址国家仍是不同业务含义；当前 Chinook 不能演示两口径导致数值差异
- 03 澄清演示应改成缺比较年度、最受欢迎定义或 Rock/Rock And Roll；D1 完成取数和更换决定，正式澄清实现/设计文档改写为 D3
- 原 03 资料仍有地区口径示例，不能声称已改写原 03

证据：

- [check_db.py](<E:/中国电子杯-赛题八/system/scripts/check_db.py:29>)
- [A_to_B_chinook.json](<E:/中国电子杯-赛题八/system/data/handoff/A_to_B_chinook.json>)
- [A_to_B_chinook.md](<E:/中国电子杯-赛题八/system/data/handoff/A_to_B_chinook.md>)
- [项目方案.md](<E:/中国电子杯-赛题八/system/notes/references/项目方案.md:116>)

## 最新数据库关键值

```json
{
  "server_version": "16.15",
  "reader": {
    "reader": "qa_reader",
    "database": "chinook"
  },
  "role_flags": {
    "rolsuper": false,
    "rolcreatedb": false,
    "rolcreaterole": false,
    "rolreplication": false,
    "rolbypassrls": false
  },
  "table_names": [
    "album",
    "artist",
    "customer",
    "employee",
    "genre",
    "invoice",
    "invoice_line",
    "media_type",
    "playlist",
    "playlist_track",
    "track"
  ],
  "column_count": 64,
  "foreign_key_constraint_count": 11,
  "foreign_key_constraints": [
    {
      "conname": "album_artist_id_fkey",
      "table_name": "album",
      "definition": "FOREIGN KEY (artist_id) REFERENCES artist(artist_id)"
    },
    {
      "conname": "customer_support_rep_id_fkey",
      "table_name": "customer",
      "definition": "FOREIGN KEY (support_rep_id) REFERENCES employee(employee_id)"
    },
    {
      "conname": "employee_reports_to_fkey",
      "table_name": "employee",
      "definition": "FOREIGN KEY (reports_to) REFERENCES employee(employee_id)"
    },
    {
      "conname": "invoice_customer_id_fkey",
      "table_name": "invoice",
      "definition": "FOREIGN KEY (customer_id) REFERENCES customer(customer_id)"
    },
    {
      "conname": "invoice_line_invoice_id_fkey",
      "table_name": "invoice_line",
      "definition": "FOREIGN KEY (invoice_id) REFERENCES invoice(invoice_id)"
    },
    {
      "conname": "invoice_line_track_id_fkey",
      "table_name": "invoice_line",
      "definition": "FOREIGN KEY (track_id) REFERENCES track(track_id)"
    },
    {
      "conname": "playlist_track_playlist_id_fkey",
      "table_name": "playlist_track",
      "definition": "FOREIGN KEY (playlist_id) REFERENCES playlist(playlist_id)"
    },
    {
      "conname": "playlist_track_track_id_fkey",
      "table_name": "playlist_track",
      "definition": "FOREIGN KEY (track_id) REFERENCES track(track_id)"
    },
    {
      "conname": "track_album_id_fkey",
      "table_name": "track",
      "definition": "FOREIGN KEY (album_id) REFERENCES album(album_id)"
    },
    {
      "conname": "track_genre_id_fkey",
      "table_name": "track",
      "definition": "FOREIGN KEY (genre_id) REFERENCES genre(genre_id)"
    },
    {
      "conname": "track_media_type_id_fkey",
      "table_name": "track",
      "definition": "FOREIGN KEY (media_type_id) REFERENCES media_type(media_type_id)"
    }
  ],
  "invoice_range": {
    "min_date": "2021-01-01T00:00:00",
    "max_date": "2025-12-22T00:00:00"
  },
  "invoice_years": [
    2021,
    2022,
    2023,
    2024,
    2025
  ],
  "reader_defaults": {
    "default_transaction_read_only": "on",
    "statement_timeout": "5s",
    "lock_timeout": "2s"
  },
  "table_privileges": [
    {
      "table_name": "album",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "artist",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "customer",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "employee",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "genre",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "invoice",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "invoice_line",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "media_type",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "playlist",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "playlist_track",
      "can_select": true,
      "can_write": false
    },
    {
      "table_name": "track",
      "can_select": true,
      "can_write": false
    }
  ],
  "top_artists": [
    {
      "artist_id": 90,
      "name": "Iron Maiden",
      "revenue": "138.60"
    },
    {
      "artist_id": 150,
      "name": "U2",
      "revenue": "105.93"
    },
    {
      "artist_id": 50,
      "name": "Metallica",
      "revenue": "90.09"
    },
    {
      "artist_id": 22,
      "name": "Led Zeppelin",
      "revenue": "86.13"
    },
    {
      "artist_id": 149,
      "name": "Lost",
      "revenue": "81.59"
    },
    {
      "artist_id": 156,
      "name": "The Office",
      "revenue": "49.75"
    },
    {
      "artist_id": 113,
      "name": "Os Paralamas Do Sucesso",
      "revenue": "44.55"
    },
    {
      "artist_id": 58,
      "name": "Deep Purple",
      "revenue": "43.56"
    },
    {
      "artist_id": 82,
      "name": "Faith No More",
      "revenue": "41.58"
    },
    {
      "artist_id": 81,
      "name": "Eric Clapton",
      "revenue": "39.60"
    }
  ],
  "country_difference": {
    "non_null_difference_count": 0,
    "null_aware_difference_count": 0,
    "rows_with_null_country": 0,
    "compared_invoice_count": 412
  },
  "compose_services": [
    {
      "Service": "chinook-pg",
      "State": "running",
      "Health": "healthy",
      "Image": "postgres:16.15-alpine3.23@sha256:621a761097839bdb50207afd6b87a72f38e2d718dd46c3d744828d8917c4f1e0",
      "Publishers": [
        {
          "URL": "127.0.0.1",
          "TargetPort": 5432,
          "PublishedPort": 55432,
          "Protocol": "tcp"
        }
      ]
    }
  ],
  "catalog_foreign_key_constraint_count": 11,
  "top_artists_match_saved_handoff": true,
  "country_difference_match_saved_handoff": true
}
```

## 测试与协议约束

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_trace.py tests/test_sql_executor.py tests/test_api_pipeline.py tests/test_llm.py -q --tb=short
```

schemas.py SHA256：`60b2816559f347dd60734f80563ae75fb453ab3903b528ed2d6075316b190445`。

[完整结构化记录](<E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/requested-a-evidence.json>)。

## 后续全量回归（保留上方 39 项针对性测试历史）

主验收随后运行 [requested-engineering.json](<E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/requested-engineering.json>)：**53/53 工程检查通过，0 失败；全量 pytest 159 passed、0 skipped，6.22 秒**。真实模型预测 0 次、保留题模型预测 0 次。本记录追加后续验证，不替换前述 39 passed/2.51 秒的针对性测试。

测试原始日志：[全量 pytest 日志](<E:/中国电子杯-赛题八/system/eval/reports/d1-acceptance/engineering-20261010T134438489202Z-pytest.txt>)。
