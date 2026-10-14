# D4 第二次启动的 Docker 只读诊断

日期：2026-10-13（America/Chicago）；日志原始UTC时间对应2026-10-14 02:02，未混用主机时区编造日期。这里仅保存与启动失败有关的少量脱敏行及文件元数据，不复制敏感日志全文，不读取Secrets内容。

明确的本机错误是 Secrets Engine 创建本地监听端点时无法将 `engine.sock` 改名为 `.stale`。随后backend记录崩溃，并停止Linux/WSL引擎，因此引擎pipe不可用。这与账号无法登录不是同一个已证实原因。日志同时记录WSL2磁盘存在，不能据本次错误说数据库卷丢失。

实际只读结果在 [diagnosis.json](diagnosis.json)：父目录是普通目录、非重解析点，只有一个 `engine.sock`；该条目0字节、`Archive, ReparsePoint`，`.stale`不存在。`fsutil reparsepoint query` 返回Windows1920，无法读取tag或实际目标；不能仅凭名字把它写成已确认AF_UNIX标签。默认沙箱未列出对应Docker进程，这不足以证明升权进程不存在或没有持有者。

Docker官方代码仓库的用户问题中有同类socket改名失败及1920的复现，并记录通过保留父运行时目录、让Docker建立新目录来恢复启动的办法。它属于已报告的可逆规避办法，不是官方确认本机根因或保证修复：[for-win #15064](https://github.com/docker/for-win/issues/15064)、[desktop-feedback #554](https://github.com/docker/desktop-feedback/issues/554)。

建议由root先核实失败的Docker自有进程已停止、核对完整源路径和同父唯一目标路径，再仅将这个单条目运行时目录改名保存；旧目录保留，让Docker自行创建干净端点。不要尝试递归删除重解析点，也不要进行工厂重置、WSL注销、卷或VHD删除。本诊断任务没有执行这些动作。

## 本机后续尝试未恢复

root后续执行了限定运行时目录的修复；[ipc-repair-result.json](ipc-repair-result.json) 实际记录管理员模式、WSL终止退出码0，但目录改名被拒绝，`success=false`。不能把网上其他机器的规避成功写成本机恢复成功。

root反馈普通及管理员改名均AccessDenied，原生DeleteFile返回1920；fsutil处理之后仍显示重解析点。本诊断代理随后再次实际读取文件元数据：`engine.sock`仍存在、0字节、属性1056（Archive／ReparsePoint），父目录属性16，没有据推测填写已修好。

root的早期Remove-Item失败后，一条后续stdout却写了“removed”；这条文字与实际文件存在检查冲突，已明确纠正，不能计为删除成功。其他尝试的详细原始stdout没有在这里凭空补写，来源范围见 `diagnosis.json.root_followup`。root修复脚本的最终结果已如实保留为false。

该阶段Docker未恢复，root请求用户重启Windows；未继续改变ACL、重置Docker或处理卷/VHD。重启前 `fusion/ui-live-002` 为0次请求、尚无输出目录。之前 `fusion/live-001` 六题和 `ui-live-001` 两次是真实已完成记录，仍保留。

随后用户重启Windows，root实际核验Docker29.8.2、两个原恢复容器healthy、双数据库ready；原记录是 [restarted-health.json](restarted-health.json) 和 `eval/artifacts/d4/runtime-005/health.json`。两类完整截图随后实际完成，分别使用 `fusion/ui-live-002` 的SQL→文档、`fusion/ui-live-003` 的文档→SQL。恢复成功的时序在Windows重启之后，不能说此前失败的限目录修复脚本已修好。
