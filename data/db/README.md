# Chinook 数据来源与初始化

数据源为 Luis Rocha 发布的官方 Chinook 1.4.5 PostgreSQL 脚本。原始 SQL、MIT 许可证、文件 SHA256、来源 URL、转换说明和固定容器镜像均记录在 `source_manifest.json`。

`Chinook_PostgreSql.sql` 是完整原始发布文件，含删除数据库的前言。初始化必须使用 `scripts/bootstrap_db.py`；脚本验证 SHA256 后生成 `Chinook_PostgreSql.import.sql`，剔除原始文件中的 `DROP DATABASE`、`CREATE DATABASE` 和 `\c`，保留实际表结构与数据，不直接执行原始文件。

在 `system` 目录运行：

```powershell
.\.venv\Scripts\python.exe scripts/bootstrap_db.py
.\.venv\Scripts\python.exe scripts/check_db.py
.\.venv\Scripts\python.exe scripts/build_catalog.py
```

本地 `.env` 必须配置 `POSTGRES_USER`、`POSTGRES_PASSWORD`、`DB_NAME`、`CHINOOK_PORT`、`DB_READER_USER`、`DB_READER_PASSWORD` 和只读账号 `DB_URL`。凭据不提交、不进入日志。数据库只绑定宿主机 `127.0.0.1` 的 55432 端口；容器项目为 `comagent-d1`、服务为 `chinook-pg`，数据保存在该项目的命名卷中。

重复初始化会保留业务数据和命名卷，重新核对只读角色及导出结构，不会重复导入或删除卷。初始化 SQL 只会在空 PostgreSQL 卷时自动运行。已有数据的表结构如果与固定数据源不一致，脚本会停止并报错。不要使用 `docker compose down --volumes` 修复初始化问题。

`db_check.json` 来自只读账号实际查询，记录表行数、日期范围、国家原始取值及账号权限。零行 UPDATE 检查在可写事务模式下测试数据库 ACL；权限不足会回滚，若意外允许该语句也会立即抛错并回滚，不修改业务记录。

`chinook_schema.sql` 是真实容器内 `pg_dump --schema-only --no-owner --no-privileges` 的结构导出。中文目录位于 `../catalog/chinook.yaml`；实际查询交接位于 `../handoff/A_to_B_chinook.json` 和 `.md`。

本次导入的发票年份为 **2021–2025**，应以 `db_check.json` 的实际结果为准。客户所在国 `customer.country` 与账单地址国家 `invoice.billing_country` 业务含义不同，但本数据源中两者的不同记录数为 0。

官方参考：[Chinook 1.4.5 发布页](https://github.com/lerocha/chinook-database/releases/tag/v1.4.5)、[PostgreSQL 官方容器说明](https://hub.docker.com/_/postgres)、[PostgreSQL 16 GRANT](https://www.postgresql.org/docs/16/sql-grant.html)、[连接参数与只读事务默认值](https://www.postgresql.org/docs/16/runtime-config-client.html)。
