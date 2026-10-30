# ComAgent 前端工作台

使用 React、Ant Design 和 esbuild。页面通过同源本机代理调用 FastAPI，模型密钥只保存在后端配置中。

## 页面

- 数据概览：展示实际查询结果，不预置演示业务数字。
- 数据分析：本地导入 CSV、TSV、JSON，进行统计、可视化和导出。
- 问答工作台：来源选择、对话、上传文档、添加文字、澄清与证据展示。
- 数据与文档：查看登记的来源和文档。
- 运行记录：查看本次浏览器会话中的请求与返回。

“自动综合问答”可以按问题调度跨源处理；文档与数据库的具体能力仍受后端、来源和业务规则约束。

## 启动

后端启动后，在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe frontend-workbench/run_ui.py --port 8501 --api-url http://127.0.0.1:8000
```

访问 http://127.0.0.1:8501/。`dist/` 已包含预编译资源，日常运行无需 Node.js 或 CDN。

修改源码后，在本目录执行：

```powershell
pnpm install --frozen-lockfile
pnpm run build
pnpm test
```

## 上传与文字

- 上传 PDF、DOCX、TXT、Markdown，单文件最多 8 MB，PDF 最多 100 页。
- 长期文字资料会建立本地索引，完成后自动切换到该文档。
- 会话文字仅绑定当前会话，不进入长期索引；切换来源或新建会话后需重新添加。
- 后端串行处理导入任务，页面查询任务进度。失败保留原知识库；重复内容不再次登记。
- 已验证旧片段和向量直接复用，仅处理新增资料。OS 文件锁在进程退出时释放，遗留锁文件不会永久阻塞上传。

接口为 `POST /api/documents/import`、`POST /api/documents/text`、`GET /api/documents/imports/{job_id}` 与 `POST /api/context`。任务及备份保存在后端 `.runtime/document-imports/`。

本地表格分析与后端文档上传是两个入口。本地文件解析、图表和导出在浏览器内进行；主动发送问答内容后，相应内容才会进入后端并可能用于模型调用。

## 数据展示

原始表和查询范围是权威依据。展示时区分 NULL 与 0，保留 Decimal 字符串原始精度，图表近似结果与列表截断需要明确标记。不同单位、均值和比例不能随意混合求和。
