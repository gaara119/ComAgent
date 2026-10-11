# 既有模型调用的授权与载荷核查

用户明确要求实际执行`notes/references/d3-and-special/专项造题.txt`，§三要求造题prompt说明“可使用的数据源、schema、业务目录与已确认规则”，并要求“必须实际使用这些prompt生成数据”“优先编写独立生成脚本，复用现有模型适配器”。§三与§四明确本轮依据已接入Chinook和已确认定义，不虚构企业数据。其指定工作本身需要把这些获准源材料提供给已有模型。

本次载荷只含公开MIT许可的Chinook1.4.5结构与音乐/国家数据样本，以及本项目自编音乐样本指标/别名审核材料。公开来源由项目`data/db/source_manifest.json`记录为官方`github.com/lerocha/chinook-database`固定发布版本；本轮未读取真实私企业务数据。只读事实查询仅发送国家、音乐艺术家/流派/媒体格式/日期与非敏感只读角色设置；不发送客户姓名、地址、邮箱、电话、员工记录。

现有DeepSeek key只由原有`qa_agent.config`与`JsonLLM._client()`读取作为认证，不进入prompt、trace或附件。只写新实验目录；没有业务DB写权限、没有API测试调用、没有holdout内容。每个模型调用SDK隐藏retry关闭，最大总attempt3，含失败response逐次落盘；SQL有真实目录/字段/函数白名单检查后再由qa_reader只读执行、5000ms超时。

首次pilot权限审核拒绝理由为具体资料外传授权不足。此文件用于再次审核已有明确任务授权与公开样本性质，不绕过拒绝或换通道执行。`outbound_payload_audit.json`由程序核查载荷不含配置密钥和DSN并保存载荷SHA。再次审核仍拒绝时不发送资料，继续完成不依赖模型的准备产物并报告阻塞。
