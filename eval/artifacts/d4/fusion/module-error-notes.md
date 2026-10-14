# D4 跨源模块错误与修复记录

这些是模块/页面 fixture 测试，不能计为真实模型准确率。

- 首次命令：`.venv/Scripts/python.exe -m pytest tests/test_d4_fusion.py tests/test_oct12_rag_ui.py -q`。工具实测为15失败、19通过。原因是使用了当前已安装 SQLGlot 不支持的 `qualify(infer_schema=...)` 参数；这一首轮只有工具输出，没有独立完整 stdout 文件。已改用项目现有 `MappingSchema`、严格列校验参数。
- `fusion-module-v2`：2失败、32通过。真实完整命令/输出在 `commands/20261013T161105202599Z-fusion-module-v2.json` 和同名 `.txt`。SQLGlot 将第二排序列变成已核验的投影别名，守卫未解析这一合法情况；已解析到实际 `artist.artist_id`，没有取消并列稳定性检查。
- `fusion-module-v3`：34通过。已证实上述修复。
- `fusion-ui-module-v4`：37通过。加入来源选择、两步显示、④所选/排除理由和既有UI回归。
- `fusion-integrated-module-v5`：39通过。通过原 `_sql` 和真实生成器函数的模块 fixture，证明文档上下文进入 prompt，错误聚合在执行前拒绝且执行器调用数为0。
- `fusion-semantic-guard-v6/v7`：45、47通过。预审增补反例，拒绝 `AVG(total)+100`、乘100、整数转换、丢小数、预先固定艺术家ID等逻辑；保留两位金额展示和真实实体传值。

该阶段尚未启动6道真实API评测或两类实际页面截图，等待现有数据库恢复。实际文档索引检索已独立运行并保存 `source-retrieval-001/source-retrieval.json`，其 LLM 和 DB 调用数均为0。

## 后续实际记录

数据库恢复并启动 D4 runtime-003 后，6道真实API执行在进程创建前被自动审批拒绝，未发送问答或模型请求。审批认为现有可信授权不足以覆盖公开Chinook目录、项目自编手册和公开艺术家简介送往DeepSeek；root已就具体剩余范围请求用户明确同意，未绕过拒绝。

已完成两个较安全的独立步骤：`reference-only-001` 只读执行6条参考SQL，模型/HTTP问答/预测均为0；`ui-entry-002` 在真实Edge确认第三来源入口，5项检查通过且未提交问题。`ui-entry-001` 的DOM检查提前读取来源切换中间状态，1项检查失败，但随后截到的实际页面已有正确文档范围；只修复观察器等待，保留首轮原件。

冻结源码及root公共集成的 `fusion-frozen-module-v8` 为47项通过，3.68秒。真实六题及两类页面结果需另存新证据目录，不能以参考结果或这些fixture回填。

## 明确授权后的真实模型结果

用户后续已明确允许全部上述 D4 实测及必要回归。使用 runtime-004、原 DeepSeek 配置完成 `live-001`：六道开发题自动检查6/6，五题实际完成两步回答，受限文档题按预期保留SQL排名并返回文档不足。`cross-06` 首轮实际澄清年份，同会话补充2024年后成功。六题回答和引用的逐项AI语义复核另存 `notes/d4/fusion-real-review.md`；新题 gold 与文档完整语义保留待人工核对状态。

`ui-live-001` 是真实两次界面提交，18项自动页面检查通过，无浏览器异常。然而人工查看PNG发现原始文件下载仍显示加载占位、处理步骤链的底部被视口裁切。已仅修改观察脚本等待下载按钮及最后一个步骤就绪、按完整面板高度调整截图视口，未为了截图改变问答逻辑；旧PNG及原始API响应完整保留。

第一次启动 `ui-live-002` 在 `runtime_source_proof` 预检查因保存API进程不可查询而退出，0模型请求、尚未创建结果目录。完整错误另存 `commands/ui-live-002-preflight-error.json`。后续只有确认项目服务进程后才继续实际截图，不把预检查失败算成模型答错，也不伪造服务证明。

后续实际确认旧API/UI停止；Docker重启失败于Secrets Engine本地socket。root普通及管理员限目录修复均未恢复，结果为false，原socket仍在，详见 `eval/artifacts/d4/docker-restart-005/`。root已请求Windows重启；本轮补图因此未发送请求。仅观察脚本增加了下载就绪、完整处理链及最后步骤位于实际视口的检查，AST解析通过；这不等于新增24项真实页面检查已跑。

用户重启Windows后才完成新观察：`ui-live-002`两次真实请求，SQL→文档12/12；文档→SQL响应正确，但几何检查10/12，完整链仍超视口，退出码1。已保留这轮失败图和原始响应。仅修观察器布局稳定等待与边界计算，`ui-live-003`只重测文档→SQL12/12、退出码0。最终SQL→文档002与文档→SQL003组合24检查通过、整图实际查看通过；没有把业务正确性与截图观察错误混为一个成绩。实际命令/逐字解码stdout位于 `commands/ui-live-002.actual-*` 和 `commands/ui-live-003.actual-*`。
