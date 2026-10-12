本目录记录 10 月 12 日任务中的 NLU、澄清规则和别名增量。依据用户本轮明确要求执行的《12号任务.md》，原来的缺期间、缺对象和地区规则在授权的范围内调整。这里只证明模块测试、实库只读盘点与新索引构建；真实 DeepSeek/API 联调结果由总验收另列，不能从模块通过推断模型实测通过。

| 要求 | 实现与第二遍检查 | 证据 |
| --- | --- | --- |
| 发票/销售额默认账单国家，客户类默认客户所在地；显式口径优先 | `field_scope`、`extract_intent` 与执行条件使用一致的字段。明确“客户所在地”或“居住客户”保留 `customer.country`，清晰问题不额外弹卡。 | 项目内 `tests/test_oct12_nlu_clarify.py`、`tests/test_d3_clarify.py`；[最终模块输出](module-tests-004.txt) |
| 热门曲目、复购、客户排名没期间时取全部数据；旧期间保留 | `time_scope.all_data=true` 表示全部现有数据，不虚构起止年份。已有 `current` 不被默认替换。无日期原文的指标跟进不接受模型擅自清空年份。 | `test_confirmed_period_is_never_replaced_by_all_data_default`、`test_model_cannot_reset_confirmed_2023_period_during_customer_metric_followup` |
| 谁买得最多默认客户发票金额，曲目热门保持数量 | 新默认仅适用于 Chinook 的该表述，不覆盖已明确的曲目或艺术家对象，不套到 AdventureWorks。 | `test_who_default_is_customer_revenue_but_track_popular_stays_quantity`、`test_aw_never_receives_chinook_defaults` |
| 金额占比分母默认同期全部发票金额，客户数不套金额 | 只在 `invoice_revenue` 缺分母时补入；用户明确分母保留。后续改为客户数量时撤销程序生成的金额分母，重新询问相应范围。 | `test_default_denominator_is_restricted_to_invoice_amount`、`test_amount_denominator_default_is_invalidated_when_followup_changes_to_customer_count` |
| 老美直接绑定 USA | 在新表中只改 `customer.country`、`invoice.billing_country` 两个现有关系，保留 `alias_id`。没有其他别名自动通过。清晰题测试为 L0，无切换按钮。 | [授权、差异和实库盘点](alias-index-build.json)；新表 `data/aliases/aliases-oct12-approved.csv` |
| 时间词和低分候选不进卡 | 每年/今年等先排除；字符候选最低 0.60，向量候选最低 0.65；自动绑定仍使用既有 0.82 阈值与差距规则，分数不是概率。 | `test_time_words_do_not_enter_candidate_cards`、`test_zero_fuzzy_and_point43_vector_do_not_reach_llm` |
| 同比只询问一次期间，已有分子不漏掉 | 完整 `sp03-06` 题面及真实补充“2024年，和2023年比。”检查当前期 2024/基期 2023；完整 `sp03-22` 保留法国居住客户分子。 | `test_sp03_06_real_supplement_fills_current_once_and_derives_prior_year`、`test_explicit_numerator_and_residence_scope_survive_model_omission` |
| 完整跨年问题与比例多轮来源保持 | `sp03-14` 的连续两年分别汇总按 2022 起至 2024 止处理，排除比较语句。分子改德国使用本次真实链接证据替换旧法国绑定，标为局部分子，年与分母继续保留。 | `test_complete_sp03_14_keeps_both_years_when_model_only_extracts_last_one`、`test_numerator_followup_refreshes_provenance_without_losing_year_or_denominator` |
| 外键查询的主体值链接 | “Metallcia 有多少张专辑”按艺术家字段纠拼写，不把查询对象专辑当成过滤字段；英文 format 对应媒体类型。显式无记录流派保留原值，题面说明不当作实体。 | `test_album_artist_typo_uses_artist_name_instead_of_album_title`、`test_english_media_format_link_uses_media_type_lookup_field`、`test_explicit_missing_genre_is_preserved_instead_of_nearby_vector_choice` |

最终本模块测试为 **165 通过、0 失败，3.88 秒**。早期失败和修复记录继续保留：[首轮](baseline-after-patch.txt)、[中间模块 1](module-tests-001.txt)、[扩大回归](module-tests-002.txt)、[发现题面说明误识别](module-tests-003.txt)、[最终回归](module-tests-004.txt)。扩大回归中的两个比例守卫旧断言由总任务负责调整，本目录没有将它们抹去。

新索引 `data/indexes/values-oct12-approved` 基于既有数据库只读值重新组织记录和拼音索引。5607 条文本未改变，按照经过摘要验证的旧记录身份重新排列并复用 5607 个向量，索引加载校验完成。新政策为 **56 条直接批准、23 条仅候选关系、2 条待审核**。原 CSV 和旧索引未覆盖。

实际只读日期盘点为 **2021-01-01 至 2025-12-22**，确有数据的年份为 2021、2022、2023、2024、2025；这不证明各年数据完整。SQL、超时与结果保存在 [构建核验 JSON](alias-index-build.json)，默认规则没有硬写这些年份。

[命令账本](commands.json)保存实际命令；[第二遍 AI 自查与冻结摘要](second-ai-review-and-freeze.json)保存判断和源码摘要。此处没有填 A/B 签名或人工确认日期，没有改保留集题目或生成保留集预测。工程召回阈值仍需要后续用开发集评估召回影响；本轮没有借用保留集校准阈值。
