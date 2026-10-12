第二版三个目标题的只读诊断如下。没有修改源码、提示词、gold、别名、索引或人工记录。

| 编号 | 原始证据 | 错误来源 | 最小处理建议 |
| --- | --- | --- | --- |
| `oct12-default-repeat` | `eval/artifacts/oct12/targets-live-002/oct12-default-repeat.json`，`sql_gen` 与三条错误 `llm` 步骤 | 当前意图已经正确为 `repeat_customer_count`，期间 `all_data=true`，L1 无待澄清卡；生成 SQL 时连续三次 `Connection error.`，错误码 `llm_connection`，没有产生 SQL。不能把此失败归为默认期间规则错误。 | 使用相同冻结源码和配置，新会话有限重跑，保存新输出；保留三次失败原始记录，不修改重试预算或通过改题降低要求。 |
| `oct12-default-track` | `eval/artifacts/oct12/targets-live-002/oct12-default-track.json`，`clarification_gate` 与三条错误 `llm` 步骤 | 语义模型调用第一次连接失败、第二和第三次请求超时，错误码 `llm_connection`。尚未形成完整语义意图或生成 SQL，不能证明热门数量/全部数据默认有错。 | 使用相同冻结源码和配置，新会话有限重跑并另存结果；失败与重跑都进入验收记录。 |
| `sp03-19` | `eval/artifacts/oct12/targets-live-002/sp03-19.json` 的意图、SQL、结果和比较字段 | 问题“2022年买得最多的客户是谁？”gold 返回 1 行；系统使用 `top_n=10`，返回 10 行。第一行 customer_id=45、金额32.75与gold一致，多出的姓名描述列不是当前失败原因。实际比较为 `row_count_mismatch`。总计划 ranking defaults 是 `top_n:10`，当前模型未提取“最高一位”的条数，程序按缺失N默认前10执行。 | 参考题目仍待人工审核，应明确这是“最高1位”还是前10名排名；不能放宽EX行数或把gold改为系统输出。若确认最高1位，可在该种明确argmax题面中提取 `top_n=1`，显式Top-N优先、一般排名的缺失N默认仍保持10；并列最高的输出范围另核对。 |

网络失败的三次调用均有 provider capture 指针，保存在 `eval/artifacts/oct12/provider-captures/live-001/`。本诊断没有根据错误字符串猜测网络根因，例如代理、防火墙或模型服务状态；材料只能证明实际连接失败/超时。

`sp03-19` 的标准 SQL 和系统排名对第一位结果一致，但行数合同尚未统一。题面、参考答案与系统回答三个对象继续分开记录，待人工定稿前不把任何一方评分写成已确认通过。
