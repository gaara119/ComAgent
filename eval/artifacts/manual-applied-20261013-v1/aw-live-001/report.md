# 正式审核应用后 AW21 开发集 API 回归

采用 v3 正式题库、新中文目录和匹配BGE索引；每题一次正常subgraph请求。

方案EX：20/21；旧EX：20/21。
provider关联完整：21/21；原始返回/调用记录：42条。

只发送题面、来源范围和独立session；gold/标签/审核文件仅留在本地评分。保留集未读取、未预测。
SQL gold复用本轮已保存的qa_reader只读5秒实跑记录，并逐项核对SQL/列/结果摘要。
本次是正确性回归，其他正确性套件可同时运行，耗时不作为新效率成绩。

|原ID|实际状态|方案EX|旧EX|问题|
|---|---|---|---|---|
|aw-01|SUCCEEDED|True|True||
|aw-02|SUCCEEDED|True|True||
|aw-03|SUCCEEDED|True|True||
|aw-04|SUCCEEDED|True|True||
|aw-05|SUCCEEDED|True|True||
|aw-06|SUCCEEDED|True|True||
|aw-07|SUCCEEDED|True|True||
|aw-08|SUCCEEDED|True|True||
|aw-09|SUCCEEDED|True|True||
|aw-10|SUCCEEDED|True|True||
|aw-11|SUCCEEDED|True|True||
|aw-12|SUCCEEDED|True|True||
|aw-13|SUCCEEDED|True|True||
|aw-14|SUCCEEDED|True|True||
|aw-15|SUCCEEDED|True|True||
|aw-16|SUCCEEDED|True|True||
|aw-17|SUCCEEDED|True|True||
|aw-18|SUCCEEDED|True|True||
|aw-19|FAILED|False|False|pipeline_error|
|aw-20|SUCCEEDED|True|True||
|aw-21|SUCCEEDED|True|True||

命令与来源摘要见command.json/provenance.json；逐题raw request/response见cases/和responses.jsonl；trace见traces/；provider原始记录见provider/。
