# D1 开发日志：A 后端与 SQL

日期：2026-10-10。实现目录：`E:\中国电子杯-赛题八\system`。

## 本次实现

保留用户已经创建的 Python 3.12.10 虚拟环境，在其中安装并固定依赖。实现共享 Pydantic 协议、项目本地配置、JSON 模型调用、请求级步骤记录、FastAPI 入口、Chinook 单表 SQL 链路、标注和执行结果评测工具。

数据库采用官方 Chinook 1.4.5，来源及 SHA256 记录在 `data/db/source_manifest.json`。PostgreSQL 16.15 通过 Compose 运行，仅绑定本机 `127.0.0.1:55432`，独立命名卷持久化。应用连接使用 qa_reader；已在 READ WRITE 事务中以零行 UPDATE 验证权限拒绝，数据修改数为 0。初始化重复运行后行数保持一致。

实际数据：11 张表、64 列、13 条外键；customer 59、track 3503、invoice 412、invoice_line 2240。发票日期为 2021-01-01 至 2025-12-22，不采用旧版本示例年份。艺术家销售额 Top10 已导出给 B，第一名为 Iron Maiden，金额 138.60；原数据未声明币种。客户所在国与账单国家在当前 412 张发票中的差异为 0，仍是不同业务字段。

## 已执行的验证

- `python -m pytest -q --tb=short`：89 passed，2.53 秒；包含真实 PostgreSQL 只读、超时、结果上限、NULL/零/空表和 API 接线测试，以及 JSON 调用预算、AST 校验和结果比较测试。Starlette TestClient 有一条 httpx 弃用提示，不影响本次通过。
- `python -m pip check`：No broken requirements found。
- `python scripts/check_secrets.py`：本地 `.env` 被 Git 忽略，待提交文件没有匹配到本机真实凭据；输出只显示匹配数和文件名。
- 30 条 gold SQL 在真实数据库中建立标准结果，又通过运行时 AST 校验器和只读执行器独立核对，30/30 与标注结果一致。这是标注验证，不是模型准确率。
- API 已启动于 `127.0.0.1:8000`；实际 `/health` 返回 `database_ready=true`。真实 POST `/api/chat` 在缺少 key 时返回 `FAILED / missing_llm_key`，保留真实 trace，没有伪造 SQL 或结果。
- 直接请求保留集评测被保护逻辑拒绝。保留集系统预测数为 0。

## 当前评测状态

30 道题固定为 21 开发题、9 保留题，题型按指导书分配。全部 gold 保留 `needs_human_review`；A 的逐题业务审核尚未记录。审核表位于 `eval/datasets/review/gold_review.md` 和 `.csv`。

当前未配置模型 key，因此模型最小调用、真实自然语言 SQL 冒烟和开发集 EX 尚未运行。`eval/reports/d1-readiness/report.md` 明确记录实际预测 0 题，不填写 EX。`notes/model-check.json` 记录 missing_llm_key。收到本地配置完成消息后，使用实际账号查询模型列表、验证 JSON，再经统一 API 运行开发集；未人工接受的 gold 只能使用明确标记的 `--draft-gold` 探索模式。

## 接下来

1. A 保存本地 `.env` 的模型 key，运行 `scripts/check_llm.py` 并重启 API。
2. A 对照审核表逐题确认问题、标准 SQL、时间和单位、排序与结果，然后记录接受的 ID。自动 SQL 核验不能代替此项确认。
3. 通过统一 API 运行 21 开发题，保存真实响应、EX、错误类别和耗时；保留题留到 D5 冻结后。
4. B 按 `notes/B接口交接.md` 实现 RAG 函数与 UI，再合并两条链路并截图。B 的 RAG、文档下载与页面不属于本次 A 实现。
5. 双方确定私有远程仓库及同步方式；本次仅初始化本地 Git。校内截止时间与提交入口仍需团队向学校核实。

D2 待处理：中文国家别名及更完整的值链接、五级要素链接、意图细化和澄清、多表查询以及 B 文档检索。当前 AST 和业务表来源检查保证执行边界；查询是否忠实于题意仍需人工 gold 和真实评测判断。
