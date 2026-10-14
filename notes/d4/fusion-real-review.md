# D4 六道跨源开发题实际回答与引用核对

核对日期：2026-10-13（America/Chicago）。本记录是 AI 对已经生成的真实回答的检查，不是人工签字，也不改变六道新题的 `pending_human_review` 状态。没有读取或运行保留题。

实际运行入口是 `scripts/run_d4_fusion.py`，原始结果保存在 `eval/artifacts/d4/fusion/live-001/`。该轮自动检查为 6/6：其中五题完成两步并作答，一题按允许文档范围返回文档不足，符合该题预期。`cross-06` 含同一会话的两次请求，不能将首轮澄清算成独立答对题。

本次逐项读取了每个文件的 `case`、`gold_sql`、`gold_result`、`turns[].request`、`turns[].response.answer/sql/evidences/intent/steps/metadata.fusion`；另直接读取注册清单、原始 Iron Maiden HTML 和指标手册 DOCX 的正文。不是仅按题目标题或自动检查状态判断。

## 来源与计算依据

- 原始艺术家简介：`data/docs/raw/d2/iron-maiden.html`，`公开背景` 三段正文。文档哈希为 `4f071c465c5417f5867e8571fb4ea37098dd8829d86b9b253ac26184a145b270`。这是项目根据维基百科精简并改写的中文文档，带原来源和 CC BY-SA 4.0 说明，不是原站完整页面。
- 原始指标手册：`data/docs/raw/d2/Chinook业务指标口径手册.docx`，`四项指标的定义与限制 → 平均每张发票金额`。文档哈希为 `b50f5683e735baa3ca6fe08bde3b437377d810732357e2a4898d6820b0456a9a`。
- 清单：`data/docs/manifest.csv` 对应 `artist-iron-maiden`、`artist-u2` 和 `project-metric-manual` 三行。艺术家实体映射分别是 `chinook:artist:90:Iron Maiden` 与 `chinook:artist:150:U2`，不能只靠名称相似匹配文档。
- 已保存的独立源与查询复核：`eval/artifacts/d4/fusion/second-review-001/material-checks.json`，`sources`、`readonly_probes`。全库排名第一为 Iron Maiden 138.60，第二为 U2 105.93；2024年第一为 Iron Maiden 33.66，第二为 U2 27.72，本快照没有第一名并列。
- 美国2024年共有21张发票、13位购买客户、金额127.98；发票等权均值为 6.0942857142857143，客户粒度均值为 9.8446153846…，二者不能混用。加拿大2023年11张发票、6位购买客户、金额55.44；发票均值为5.04，客户粒度为9.24。上述数值来源于该文件实际只读查询，不是模型常识。

## 逐题判断

| 原编号 | 实际行为与核对 | 完整回答判断 | 引用语义支持判断 | 证据位置与限制 |
|---|---|---|---|---|
| cross-01 | 实际明细销售额排名得到 `artist_id=90 / Iron Maiden / 138.60`，随后将该ID和标准名传到检索，仅取对应艺术家文档。回答的英国重金属、Steve Harris、1975年Leyton、英国重金属新浪潮、歌词题材、1980年首专和1982年作品均与原正文一致。 | AI建议通过 | AI建议通过：每句背景均有 `[E1]`；E1位于正确文档 `公开背景`，完整支持这些句子。数据库排名由SQL结果支持，不用简介替代排名。 | `eval/artifacts/d4/fusion/live-001/cross-01.json` 的 `turns[0].response`。金额仅称数据库金额单位，没有臆测币种。 |
| cross-02 | 用户明确2024年，生成SQL按发票日期 `[2024-01-01, 2025-01-01)` 过滤明细后按艺术家排名，实际返回 Iron Maiden 33.66；简介仍对应ID90。 | AI建议通过 | AI建议通过：E1三段支持实际回答的背景内容；简介不证明2024年销售额，销售额有本次SQL和结果。 | `eval/artifacts/d4/fusion/live-001/cross-02.json` 的 `turns[0].response`、`gold_result`。音乐介绍是一般背景，回答未将其说成2024年的变化。 |
| cross-03 | 仅允许U2文档，数据库第一名仍是Iron Maiden。实际返回 `EMPTY_RESULT`，保留SQL与138.60排名，明确当前允许文档没有该艺术家介绍，未借用U2资料，`evidences=[]`、`completed_stages=1`。 | AI建议通过：符合受限来源下的预期文档不足，不计为两步成功的介绍回答。 | AI建议通过：此题应当没有音乐介绍引用；没有无依据背景陈述。 | `eval/artifacts/d4/fusion/live-001/cross-03.json` 的请求 `scope.doc_ids`、回答及 `metadata.fusion`。不是数据库无记录。 |
| cross-04 | 原始手册定义是 `AVG(invoice.total)`、发票等权。实际检索和模型逐字提取该定义，再把2024年、`customer.country='USA'` 带入SQL；实际均值6.0942857142857143，与参考结果及独立总额/发票数复核一致。 | AI建议通过 | AI建议通过：E1支持所述客单价定义；数值由SQL结果支持，不能说数值来自手册。 | `eval/artifacts/d4/fusion/live-001/cross-04.json` 的 `definition_context`、`definition_used_in_generation`、`definition_sql_guard` 和 `fusion_plan_validate`。美国指客户所在地，不是账单国家；原SQL使用正确字段。 |
| cross-05 | 同一定义，用户改为2023年加拿大。SQL使用2023区间与`customer.country='Canada'`，实际5.0400000000000000，未套用手册2024年示例或美国筛选。 | AI建议通过 | AI建议通过：E1支持发票等权定义，5.04由实际SQL支持。 | `eval/artifacts/d4/fusion/live-001/cross-05.json` 的SQL、结果与 `definition_context`。未把客单价切换成客户粒度。 |
| cross-06 | 首轮“某年”触发年份澄清，首轮没有SQL；同session、同原scope提交“2024年”与原卡片/version后，`intent_version` 由1变2，保留USA和发票均值定义，生成正确2024年查询，结果6.0942857142857143。续问走 `fusion_resume`，没有重复检索或重复追问已明确字段。 | AI建议通过 | AI建议通过：续问复用同一实际检索E1及定义哈希，引用仍支持发票均值；期间是用户补充，不是从手册示例偷填。 | `eval/artifacts/d4/fusion/live-001/cross-06.json` 的两轮请求/响应、`intent` 与 `steps`。首轮 `NEEDS_CLARIFICATION` 与最终成功分别记录。 |

以上六题的参考SQL、系统SQL及结果已分别核对。全库/期间艺术家查询沿真实FK连接，没有将发票总额在明细JOIN后重复求和；客单价查询按发票连接客户，再计算发票总额均值，没有按客户平均。实际来源与引用都是HTML章节或DOCX章节，因此 `page=null` 配合 `section_path` 是适用定位，不应人为编造PDF页码。

另外直接读取了模型供应商捕获文件，不仅信任 `definition_used_in_generation=true` 标记。以下三份实际SQL生成请求的 `request.messages[role=user]` JSON均包含 `verified_fusion_context`，其逐字原文、`AVG(invoice.total)`、发票粒度和源哈希一致；各自 `response.choices[0].message.content` 实际返回对应期间和国家的均值SQL：

- cross-04：`eval/artifacts/d4/provider-api-004/18d3a2656c36432f844794df33264255.json`。
- cross-05：`eval/artifacts/d4/provider-api-004/627e850ce96e4409b83e838b3824eed2.json`。
- cross-06 的续问：`eval/artifacts/d4/provider-api-004/32953d7ac906454884334cb49c564361.json`。

这三份原始请求证明检索定义真实进入了生成输入，而不是在查询完成后才附加一段手册。生成后仍分别经过项目原SQL校验和跨源定义守卫再只读执行。

## 尚需人工检查与适用范围

六道新开发题的题面、参考标签及以上AI语义判断仍留给人工统一核对；本记录不填写A/B签名或人工确认日期。艺术家文档为已注册中文改写资料，本轮核对其内部原文支持关系，没有重新上网审计原始百科全文，也没有扩大到其他音乐事实。跨源能力按D4两类流程实现，不能据这六题推断任意跨源问法都可靠。

`ui-live-001` 的两条请求和18项自动页面检查是真实通过，但初版截图存在原文件下载尚未就绪及底部处理链被裁切的观察时机问题，不能将其当作完整可读截图。后续观察需保存为新目录，保留本轮图片与原始响应，不覆盖旧证据。

本次补图预检查发现原API/UI进程已停止，0请求退出。随后Docker重启曾因本机Secrets Engine运行时socket的1920／拒绝访问错误未恢复；见 `eval/artifacts/d4/docker-restart-005/diagnosis.json` 及root修复结果。用户重启Windows后双库恢复ready，才继续以下真实观察。

最终完整截图使用两份新证据：`eval/artifacts/d4/fusion/ui-live-002` 的SQL→文档为12/12检查；同目录文档→SQL问答正确且下载已就绪，但观察器提前测量Streamlit尚在增长的布局，几何检查2项失败，退出码1，图和raw都保留。仅修改观察器等待布局四次稳定采样、同时按末步骤与面板的最大底部确定视口；随后 `ui-live-003` 只重测文档→SQL，12/12、退出码0。不是把失败检查改成通过，也没有再跑已成功的SQL→文档。

最终两类共24项实际页面检查通过，无浏览器异常；两张原像素PNG均已 `view_image` 实际查看，下载按钮、真实引用原文、SQL/结果、完整23／21项处理步骤及最后一步都显示。对应图为 `notes/screenshots/D4-fusion-sql-to-doc-20261013.png` 和 `notes/screenshots/D4-fusion-doc-to-sql-20261013.png`。完整SQL文本与引用仍以各目录 `*-raw-api.json` 为准；截图中的单行SQL可以横向滚动。

这两次最终观察是runtime-005对应源码的代表性回归，没有修改融合planner／UI／题库；启动时序、全源SHA和两个项目进程归属保存在相应 `report.json.runtime_source_proof`。该证明不等于远程加载模块完整证明，也不宣称覆盖随后多轮修复的新版源。此前六题 `live-001` 是保留的已完成实测，未为了截图重写其记录。

随后共享当前合同守卫及SQL生成prompt更新，按必要回归又在最新API007完成原六题，另存 `eval/artifacts/d4/fusion/live-002/`，退出0、6/6预期检查通过，共7次实际API调用。新raw的六份答案、引文、SQL与原文逐项复核，结果仍为5题两步回答、1题正确文档不足，cross-06仍真实先澄清年份再同会话成功。新生成请求实际携带逐字定义，并真实使用最新生成prompt；详见该目录 `latest-version-review.md`、`actual-command.json` 和 `actual-output.txt`。旧live-001及005两张图保留，不改gold；最新回归没有重拍界面，也没有做计时实验。
