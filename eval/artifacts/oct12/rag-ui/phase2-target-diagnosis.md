# Phase2定向检查三项未通过的只读诊断

本轮只读取已经发生的响应、LLM provider原始记录、现行规则与总计划，没有发起新预测、修改源码、题库答案或人工审核记录。

| 条目 | 已有实测 | 诊断 | 建议 |
| --- | --- | --- | --- |
| oct12-default-repeat | 失败，请求编号`fc14a001-eb09-4f85-bea1-0a73efc9bbd9`，`error.code=llm_connection`，`retryable=true`。意图阶段成功，`repeat_customer_count`与`all_data=true`已经写入，SQL生成阶段三次连接错误，未生成/执行SQL。 | 上游传输失败；3次耗时18.008、2.032、2.008秒。provider均无response、无JSON validation_error。不足以判断DNS、TLS、代理、链路或服务端具体根因。 | 仅在新目录重新测这道开发题，保留本次失败，分别报告第一次失败与重试结果；无需据此改复购规则或gold。 |
| oct12-default-track | 失败，请求编号`1545be69-89b8-4737-b666-d736e8ba54e3`，`llm_connection`。意图阶段三次尝试：一次连接错误18.115秒，两次超时60.033与60.022秒。没有进入SQL生成和执行。 | 上游传输失败；没有格式错误证据，也没有已完成意图推理可用于判断购买数量默认是否正确。 | 仅新目录重测这道开发题，不能把已有lookup空意图当成模型错误业务判断，它是意图调用未完成时的初始对象。 |
| sp03-19 | 问句“2022年买得最多的客户是谁？”。模型意图JSON实际`top_n=null`，规则补10；SQL返回10行，首行为customer_id45、金额32.75；gold仅1行45、32.75。两次模型调用均有真实响应且JSON校验通过；SQL只读执行成功。 | 不是网络、格式或描述列比较故障。总计划§3.6.3的ranking默认top_n10，经rules.py326–330作用到本题；gold SQL却LIMIT1。EX应继续判row_count_mismatch，第一行相同不足以使10行结果等价于1行。 | 提请统一人工审核确认“最多的是谁”是否表达只取第一名，或题面本意是前10排名。不得为让系统通过而改gold。可在新题面版本明确“消费金额排名第一（并列取编号较小者）”保留Top1参考，或明确“消费金额前10名”并另立Top10参考；仍需批准具体修改。 |

实际响应证据：

- [复购raw](../targets-live-002/oct12-default-repeat.json)
- [热门曲目raw](../targets-live-002/oct12-default-track.json)
- [sp03-19 raw](../targets-live-002/sp03-19.json)
- [17项本轮报告：14/17匹配](../targets-live-002/report.json)

LLM provider核验记录（位置确为`live-001`，不是按阶段名称猜出的`live-002`）：

- 复购意图成功：[6e5d9fb4](../provider-captures/live-001/6e5d9fb49fdb4210ad6c61f23941c18b.json)；SQL生成三次连接失败：[d90893c2](../provider-captures/live-001/d90893c2acf84e83b013619ee8a7e07e.json)、[54d4ab4c](../provider-captures/live-001/54d4ab4c6723437ba0decb1d44db1b7d.json)、[2d0e4ca7](../provider-captures/live-001/2d0e4ca7745c437eb2fcea37856440a9.json)。
- 热门曲目意图调用三次连接/超时失败：[b2ab5a23](../provider-captures/live-001/b2ab5a233b514170b40e494d04f8fb50.json)、[f31c108d](../provider-captures/live-001/f31c108decb9410089681aab0bd1a8bd.json)、[2b8bc194](../provider-captures/live-001/2b8bc194682c495fb2ca6381ee71bc2a.json)。
- sp03-19意图实际输出top_n=null：[1f3cd97e](../provider-captures/live-001/1f3cd97e15c9458d94632af5d364ae88.json)；SQL生成遵守补入的LIMIT10：[b4da7fef](../provider-captures/live-001/b4da7fefc2a540408e61cb281e31b8b2.json)。

这些provider文件的trace_id逐个与raw核对一致；最后写入时间分别位于2026-10-12 16:17–16:21 UTC，属于本次定向检查。目录名称没有改变文件对应关系。日志和报告应沿用实际路径，另记录捕获目录命名与阶段命名不一致的问题。

接口层将APIConnectionError与APITimeoutError统一映射为llm_connection，具体连接失败根因不能由该错误码独自推断。这里没有观察到认证失败、额度失败、HTTP限流、SQL超时、SQL校验拒绝或JSON协议错误。
