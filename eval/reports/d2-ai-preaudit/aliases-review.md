# D2 81项别名 AI 预审

本报告仅为 AI 预审，没有人工签名、审核日期或批准状态，不启用任何别名。全部81行的实际状态均为“不适用（别名配置审核，未生成预测）”。没有调用问答API、项目模型或生成新系统预测；没有重建索引；未阅读/输出33项保留题内容。

本轮先对真实只读数据库材料、实际catalog、既有索引及原待审CSV交叉核验，再检查 raw/d2 字典/艺人简介及独立公开来源。81项字段与标准对象均存在；LLM草稿和既有建议没有作为独立证明。真值存在不代表译名准确、适用范围正确或可以唯一绑定。

“建议直接使用”只适用于目标字段已明确的别名匹配；“仅作为条件候选”需要音乐/国家/类型语境或用户澄清，且不能自动取第一或最高分候选。客户所在地国家与发票账单地址国家即使取值相同，也不允许换字段。

| 状态 | 数量 |
|---|---:|
| AI建议通过 | 54 |
| AI建议有条件通过 | 25 |
| AI发现错误 | 0 |
| 证据不足 | 2 |

证据完整：77；证据不完整：4。完整表示本行可核查的依据覆盖与局限已列，包含明确标注的常用语言组合推断；不代表人工批准。

关键判断：金属（艺人Metallica简称）与节奏摇滚（Rock And Roll译名）缺少独立用法证据；铁处女有二手译名依据，不能按旧建议直接判错，但原页与高等级译名证据仍需补强；齐柏林飞艇完整原页访问失败。Rock/Rock And Roll、Metal/Heavy Metal、一般AAC/Protected AAC/Purchased AAC都需保留真实分类边界。

| review_id | 别名 → 字段标准值 | 参考预审 | 处置建议 | 证据完整 |
|---|---|---|---|---|
| alias:a-3a8a1d5195e9c6a0 | 铁娘子 → artist.name = Iron Maiden | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-e36bfe04cba29de8 | 铁处女 → artist.name = Iron Maiden | AI建议有条件通过 | 仅作为条件候选 | 否 |
| alias:a-7a0187a2e65d10ae | Iron Maiden乐队 → artist.name = Iron Maiden | AI建议通过 | 建议直接使用 | 是 |
| alias:a-f6304e1cde119b8f | 齐柏林飞船 → artist.name = Led Zeppelin | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-751d38c444555de2 | 齐柏林飞艇 → artist.name = Led Zeppelin | AI建议有条件通过 | 仅作为条件候选 | 否 |
| alias:a-e7baa0eb0389f85e | Led Zeppelin乐队 → artist.name = Led Zeppelin | AI建议通过 | 建议直接使用 | 是 |
| alias:a-9ab23063254419e0 | 金属乐队 → artist.name = Metallica | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-0c47392129d13dd6 | 金属 → artist.name = Metallica | 证据不足 | 证据不足 | 否 |
| alias:a-713e91edadb5f817 | Metallica乐队 → artist.name = Metallica | AI建议通过 | 建议直接使用 | 是 |
| alias:a-a04cacbc074e2ac6 | U2乐队 → artist.name = U2 | AI建议通过 | 建议直接使用 | 是 |
| alias:a-5875ecf83bb89913 | U2乐团 → artist.name = U2 | AI建议通过 | 建议直接使用 | 是 |
| alias:a-b36489cadceee749 | 澳大利亚 → customer.country = Australia | AI建议通过 | 建议直接使用 | 是 |
| alias:a-7d3693714ee37b46 | 澳洲 → customer.country = Australia | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-840245fad126ae71 | 澳大利亚联邦 → customer.country = Australia | AI建议通过 | 建议直接使用 | 是 |
| alias:a-cf1b483ec6900d1a | 巴西 → customer.country = Brazil | AI建议通过 | 建议直接使用 | 是 |
| alias:a-48667df2696e251c | 巴西联邦共和国 → customer.country = Brazil | AI建议通过 | 建议直接使用 | 是 |
| alias:a-3cc0be84e1794908 | 加拿大 → customer.country = Canada | AI建议通过 | 建议直接使用 | 是 |
| alias:a-b25098af9fa5b17a | 法国 → customer.country = France | AI建议通过 | 建议直接使用 | 是 |
| alias:a-2ad4affe6af89ef4 | 法兰西 → customer.country = France | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-ca229f69098da675 | 法兰西共和国 → customer.country = France | AI建议通过 | 建议直接使用 | 是 |
| alias:a-e4d835eae26ef07e | 德国 → customer.country = Germany | AI建议通过 | 建议直接使用 | 是 |
| alias:a-9f5bb5a79e3b2818 | 德意志 → customer.country = Germany | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-fc51077551e79ac3 | 德意志联邦共和国 → customer.country = Germany | AI建议通过 | 建议直接使用 | 是 |
| alias:a-94e30cebbc64041f | 印度 → customer.country = India | AI建议通过 | 建议直接使用 | 是 |
| alias:a-4aca00f05bc3cd6c | 印度共和国 → customer.country = India | AI建议通过 | 建议直接使用 | 是 |
| alias:a-cbef6f7b472f48eb | 美国 → customer.country = USA | AI建议通过 | 建议直接使用 | 是 |
| alias:a-c43d08f9e0effe4d | 老美 → customer.country = USA | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-fab280bc88aa1682 | 美利坚合众国 → customer.country = USA | AI建议通过 | 建议直接使用 | 是 |
| alias:a-9a9f0da60f84554c | 英国 → customer.country = United Kingdom | AI建议通过 | 建议直接使用 | 是 |
| alias:a-b507c7d7ee1c26e7 | 联合王国 → customer.country = United Kingdom | AI建议通过 | 建议直接使用 | 是 |
| alias:a-1f08c5b75168548d | 大不列颠及北爱尔兰联合王国 → customer.country = United Kingdom | AI建议通过 | 建议直接使用 | 是 |
| alias:a-6f2b17a026a9ef9b | 古典 → genre.name = Classical | AI建议通过 | 建议直接使用 | 是 |
| alias:a-fb76d9986e52aa10 | 古典音乐 → genre.name = Classical | AI建议通过 | 建议直接使用 | 是 |
| alias:a-ae481372f2653475 | 爵士 → genre.name = Jazz | AI建议通过 | 建议直接使用 | 是 |
| alias:a-f3ab57aac4760fac | 爵士乐 → genre.name = Jazz | AI建议通过 | 建议直接使用 | 是 |
| alias:a-439ce0734774f114 | 金属 → genre.name = Metal | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-f637ff312a6fead6 | 金属乐 → genre.name = Metal | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-10514461292c596d | 流行 → genre.name = Pop | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-34701ceea8df41eb | 流行音乐 → genre.name = Pop | AI建议通过 | 建议直接使用 | 是 |
| alias:a-cb69b4bf22161e6e | 摇滚 → genre.name = Rock | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-5972cabfe64bae77 | 摇滚乐 → genre.name = Rock | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-0e44ca874f4ba96f | 摇滚乐 → genre.name = Rock And Roll | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-c748b229db869a4e | 节奏摇滚 → genre.name = Rock And Roll | 证据不足 | 证据不足 | 否 |
| alias:a-4c5e26e87ffb2aa2 | 澳大利亚 → invoice.billing_country = Australia | AI建议通过 | 建议直接使用 | 是 |
| alias:a-b5ca3e94894dee8d | 澳洲 → invoice.billing_country = Australia | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-f2ecb45e404feda1 | 澳大利亚联邦 → invoice.billing_country = Australia | AI建议通过 | 建议直接使用 | 是 |
| alias:a-bfc3cf35431dcceb | 巴西 → invoice.billing_country = Brazil | AI建议通过 | 建议直接使用 | 是 |
| alias:a-e8e5e4fe2d99ff1b | 巴西联邦共和国 → invoice.billing_country = Brazil | AI建议通过 | 建议直接使用 | 是 |
| alias:a-b33ce127772f748d | 加拿大 → invoice.billing_country = Canada | AI建议通过 | 建议直接使用 | 是 |
| alias:a-1146eff0ef203810 | 法国 → invoice.billing_country = France | AI建议通过 | 建议直接使用 | 是 |
| alias:a-9eb72fa09563fb7e | 法兰西 → invoice.billing_country = France | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-99f7789e108299a0 | 法兰西共和国 → invoice.billing_country = France | AI建议通过 | 建议直接使用 | 是 |
| alias:a-3414db81951a6279 | 德国 → invoice.billing_country = Germany | AI建议通过 | 建议直接使用 | 是 |
| alias:a-604796b76eb1cd3b | 德意志 → invoice.billing_country = Germany | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-43165309220a1f56 | 德意志联邦共和国 → invoice.billing_country = Germany | AI建议通过 | 建议直接使用 | 是 |
| alias:a-9c79948752527793 | 印度 → invoice.billing_country = India | AI建议通过 | 建议直接使用 | 是 |
| alias:a-5819628db78075fb | 印度共和国 → invoice.billing_country = India | AI建议通过 | 建议直接使用 | 是 |
| alias:a-dca9d898c8a31e37 | 美国 → invoice.billing_country = USA | AI建议通过 | 建议直接使用 | 是 |
| alias:a-9d6edadfda3e46a9 | 老美 → invoice.billing_country = USA | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-6d34332b7a54aaa8 | 美利坚合众国 → invoice.billing_country = USA | AI建议通过 | 建议直接使用 | 是 |
| alias:a-a51a0dfa5111c6b0 | 英国 → invoice.billing_country = United Kingdom | AI建议通过 | 建议直接使用 | 是 |
| alias:a-7528c8542cbf31a0 | 联合王国 → invoice.billing_country = United Kingdom | AI建议通过 | 建议直接使用 | 是 |
| alias:a-8fd10b20a82508de | 大不列颠及北爱尔兰联合王国 → invoice.billing_country = United Kingdom | AI建议通过 | 建议直接使用 | 是 |
| alias:a-6799bc523f9e8693 | AAC音频文件 → media_type.name = AAC audio file | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-7b241be59eef3bbb | AAC音频 → media_type.name = AAC audio file | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-623dcb996bdf111b | MPEG音频文件 → media_type.name = MPEG audio file | AI建议通过 | 建议直接使用 | 是 |
| alias:a-283ad9fbc2d748a9 | MPEG音频 → media_type.name = MPEG audio file | AI建议通过 | 建议直接使用 | 是 |
| alias:a-bfc4b2a75ae6d393 | 受保护AAC音频文件 → media_type.name = Protected AAC audio file | AI建议通过 | 建议直接使用 | 是 |
| alias:a-e6995d2d188f2d9e | 受保护AAC音频 → media_type.name = Protected AAC audio file | AI建议通过 | 建议直接使用 | 是 |
| alias:a-f1475c651575231c | 受保护MPEG-4视频文件 → media_type.name = Protected MPEG-4 video file | AI建议通过 | 建议直接使用 | 是 |
| alias:a-546993461dc3354d | 受保护MPEG-4视频 → media_type.name = Protected MPEG-4 video file | AI建议通过 | 建议直接使用 | 是 |
| alias:a-4fbad68319f9e10e | 已购买AAC音频文件 → media_type.name = Purchased AAC audio file | AI建议通过 | 建议直接使用 | 是 |
| alias:a-0c3df10756626f4a | 购买AAC音频文件 → media_type.name = Purchased AAC audio file | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-a974e81df263a782 | 已购买AAC音频 → media_type.name = Purchased AAC audio file | AI建议通过 | 建议直接使用 | 是 |
| alias:a-d0e9fad30baaded8 | 意大利 → customer.country = Italy | AI建议通过 | 建议直接使用 | 是 |
| alias:a-97a541d02a9d6f5b | 义大利 → customer.country = Italy | AI建议通过 | 建议直接使用 | 是 |
| alias:a-a653ead69db804b0 | 意国 → customer.country = Italy | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-97f75d30b3bcab32 | 意大利 → invoice.billing_country = Italy | AI建议通过 | 建议直接使用 | 是 |
| alias:a-477276f0186e7f07 | 义大利 → invoice.billing_country = Italy | AI建议通过 | 建议直接使用 | 是 |
| alias:a-14625e480dd8676e | 意国 → invoice.billing_country = Italy | AI建议有条件通过 | 仅作为条件候选 | 是 |
| alias:a-d2-plan-rock-and-roll | 摇滚 → genre.name = Rock And Roll | AI建议有条件通过 | 仅作为条件候选 | 是 |

## alias:a-3a8a1d5195e9c6a0

**铁娘子 → artist.name = Iron Maiden**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 artist.name 字段与标准值 Iron Maiden 均存在，完整DISTINCT与既有标准值索引一致。本地简介与唱片公司中文资料均支持 Iron Maiden 的该中文乐队名。裸词还可作人物称号、作品名或刑具名，真实库仅有该艺人并不能消除库外语义；须先确认音乐艺人语境。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：裸词跨领域多义；不能仅因 artist 表中恰有一个匹配就对任意输入唯一绑定。

建议：明确“铁娘子乐队”、曲目/专辑或artist字段上下文时保留 Iron Maiden 候选；否则澄清指称。

需人确认：确认默认中文乐队名及裸词歧义处理；不要照抄既有建议作为人审结论。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:2>)：第2行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[113]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:461>)：第461行；kind=standard; candidate_id=v-26903b3204f3eef20547。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/iron-maiden.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/iron-maiden.html:4>)：第4行；公开背景第1段/标准名称页脚。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [索尼音乐：早晨後的配樂 十周年紀念版](<https://www.sonymusic.com.tw/?p=21566>)：专辑简介首段。唱片公司中文简介将 Iron Maiden 与“铁娘子”的繁体字形并列；简繁转换为AI语言推断。 访问：浏览工具已返回可读正文。
- [维基百科：铁处女](<https://zh.wikipedia.org/wiki/%E9%90%B5%E8%99%95%E5%A5%B3>)：条目首段。同一词形也用于刑具；只作为跨领域歧义佐证。 访问：搜索工具返回可读条目正文；未在本轮打开完整页。

## alias:a-e36bfe04cba29de8

**铁处女 → artist.name = Iron Maiden**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：否。

实查 artist.name 字段与标准值 Iron Maiden 均存在，完整DISTINCT与既有标准值索引一致。本地简介只支持“铁娘子”；外部百科可读条目正文另外列出“铁处女”为该乐团译名，因此现有材料不足以断言此词错误。该词同时明确指刑具，且完整原页未成功访问、未找到同等级唱片公司中文证据；仅能暂列音乐艺人语境下的条件候选。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：同词刑具义明显。；译名依据为外部二手百科可读节选；完整原页访问失败，证据链仍需补强。

建议：禁止对裸词自动唯一绑定；仅在用户明确讨论乐队且人审补充可信译名证据后考虑候选。

需人确认：核实完整中文译名来源，选择地域译法与条件检索范围；既有“拒绝”建议也不是证据。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:3>)：第3行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[113]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:461>)：第461行；kind=standard; candidate_id=v-26903b3204f3eef20547。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/iron-maiden.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/iron-maiden.html:4>)：第4行；公开背景第1段/标准名称页脚。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [索尼音乐：早晨後的配樂 十周年紀念版](<https://www.sonymusic.com.tw/?p=21566>)：专辑简介首段。唱片公司中文简介将 Iron Maiden 与“铁娘子”的繁体字形并列；简繁转换为AI语言推断。 访问：浏览工具已返回可读正文。
- [维基百科：铁娘子乐团](<https://zh.wikipedia.org/wiki/%E9%90%B5%E5%A8%98%E5%AD%90%E6%A8%82%E5%9C%98>)：条目首段与英文名信息框。可读搜索正文列出另一中文译名“铁处女”，支持其作为候选；不证明项目默认译名。 访问：搜索工具返回可读条目正文；open完整页返回 Internal Error，未取得完整原页。
- [维基百科：铁处女](<https://zh.wikipedia.org/wiki/%E9%90%B5%E8%99%95%E5%A5%B3>)：条目首段。同一词形也用于刑具；只作为跨领域歧义佐证。 访问：搜索工具返回可读条目正文；未在本轮打开完整页。

## alias:a-7a0187a2e65d10ae

**Iron Maiden乐队 → artist.name = Iron Maiden**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 artist.name 字段与标准值 Iron Maiden 均存在，完整DISTINCT与既有标准值索引一致。“Iron Maiden乐队”完整保留标准名称 Iron Maiden，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 Iron Maiden。

需人确认：人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

AI推断与局限：中文乐队/乐团限定语与公开band实体类型等价，是AI语言组合判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:4>)：第4行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[113]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:461>)：第461行；kind=standard; candidate_id=v-26903b3204f3eef20547。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/iron-maiden.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/iron-maiden.html:4>)：第4行；公开背景第1段/标准名称页脚。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [索尼音乐：早晨後的配樂 十周年紀念版](<https://www.sonymusic.com.tw/?p=21566>)：专辑简介首段。唱片公司中文简介将 Iron Maiden 与“铁娘子”的繁体字形并列；简繁转换为AI语言推断。 访问：浏览工具已返回可读正文。

## alias:a-f6304e1cde119b8f

**齐柏林飞船 → artist.name = Led Zeppelin**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 artist.name 字段与标准值 Led Zeppelin 均存在，完整DISTINCT与既有标准值索引一致。本地公开简介明确把该译名与 Led Zeppelin 并列，外部中文艺人条目旁证。该裸词又是飞船通名，翻译对应成立仅限音乐艺人语境；数据库标准对象存在不证明用户一定在问乐队。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：乐队译名与航空器名称多义。

建议：明确“乐队/乐团”、音乐作品或artist字段后保留 Led Zeppelin 候选；航空器语境不绑定。

需人确认：确认接受飞船/飞艇两个地区用名及音乐上下文约束；需要时补读完整外部变体原页。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:5>)：第5行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[136]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:484>)：第484行；kind=standard; candidate_id=v-962f8d82d2343d62bf1f。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/source/led-zeppelin-summary.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/source/led-zeppelin-summary.html:4>)：第4行；公开背景第1段/标准名称页脚。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [维基百科：齐柏林飞船（乐团）](<https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29>)：条目标题、首段与英文名信息。中文艺人条目与 Led Zeppelin 对应，并区分飞船等其他含义。 访问：搜索工具返回可读条目正文。

## alias:a-751d38c444555de2

**齐柏林飞艇 → artist.name = Led Zeppelin**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：否。

实查 artist.name 字段与标准值 Led Zeppelin 均存在，完整DISTINCT与既有标准值索引一致。本地简介使用“齐柏林飞船”；另有州旅游官网活动中文节选使用“齐柏林飞艇”且路径对应 Led Zeppelin，支持该译名变体。飞船/飞艇也有航空器语义；不能把这种词形变体作一般实体的固定替换。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：音乐乐队与航空器多义。；外部变体来源完整页open失败，仅取得官方搜索节选。

建议：明确“乐队/乐团”、音乐作品或artist字段后保留 Led Zeppelin 候选；航空器语境不绑定。

需人确认：确认接受飞船/飞艇两个地区用名及音乐上下文约束；需要时补读完整外部变体原页。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:6>)：第6行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[136]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:484>)：第484行；kind=standard; candidate_id=v-962f8d82d2343d62bf1f。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/source/led-zeppelin-summary.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/source/led-zeppelin-summary.html:4>)：第4行；公开背景第1段/标准名称页脚。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [维基百科：齐柏林飞船（乐团）](<https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29>)：条目标题、首段与英文名信息。中文艺人条目与 Led Zeppelin 对应，并区分飞船等其他含义。 访问：搜索工具返回可读条目正文。
- [新南威尔士州旅游官网：齐柏林飞艇乐队的生平与时代](<https://www.visitnsw.com/cn/destinations/central-coast/gosford-area/avoca-beach/events/the-life-times-led-zeppelin-featuring-zepplin-orchestral-strings>)：活动标题与简介。官方旅游活动中文页使用“齐柏林飞艇”，页面路径标明 Led Zeppelin；只支持中文名用法，不审核演出时效。 访问：搜索工具返回标题与正文节选；open完整页返回 Internal Error。

## alias:a-e7baa0eb0389f85e

**Led Zeppelin乐队 → artist.name = Led Zeppelin**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 artist.name 字段与标准值 Led Zeppelin 均存在，完整DISTINCT与既有标准值索引一致。“Led Zeppelin乐队”完整保留标准名称 Led Zeppelin，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 Led Zeppelin。

需人确认：人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

AI推断与局限：中文乐队/乐团限定语与公开band实体类型等价，是AI语言组合判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:7>)：第7行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[136]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:484>)：第484行；kind=standard; candidate_id=v-962f8d82d2343d62bf1f。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/source/led-zeppelin-summary.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/source/led-zeppelin-summary.html:4>)：第4行；公开背景第1段/标准名称页脚。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [维基百科：齐柏林飞船（乐团）](<https://zh.wikipedia.org/wiki/%E9%BD%90%E6%9F%8F%E6%9E%97%E9%A3%9E%E8%88%B9_%28%E4%B9%90%E5%9B%A2%29>)：条目标题、首段与英文名信息。中文艺人条目与 Led Zeppelin 对应，并区分飞船等其他含义。 访问：搜索工具返回可读条目正文。

## alias:a-9ab23063254419e0

**金属乐队 → artist.name = Metallica**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 artist.name 字段与标准值 Metallica 均存在，完整DISTINCT与既有标准值索引一致。本地 DOCX 标题使用此专名，文化部演出批复把它与 Metallica 并列，已取得独立中文名证据。它也可指任意演奏金属音乐的乐队；用户问“有哪些金属乐队”是一个类别问题，不能改成只查 Metallica。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：专名与音乐类别组合短语同形；类别查询可能包含多位artist。

建议：专名或 Metallica 指称明确时作候选；泛指一类乐队时按流派/作品分析并澄清，不强制唯一艺人。

需人确认：确认专名使用情形与类别问句的识别边界。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:8>)：第8行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[158]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:506>)：第506行；kind=standard; candidate_id=v-8cfcf0e35bfb7532e28a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/metallica-introduction.docx](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/metallica-introduction.docx>)：word/document.xml：段落1标题、段落3与5。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [文化部关于同意美国金属乐队到上海市演出的批复](<https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html>)：批复正文，第36行；文市函〔2013〕689号。文化部演出许可正文将中文乐队名与 Metallica 并列；证明专名“金属乐队”的对应关系。 访问：浏览工具已返回可读正文。

## alias:a-0c47392129d13dd6

**金属 → artist.name = Metallica**

参考状态：证据不足；处置建议：证据不足；实际状态：不适用（别名配置审核，未生成预测）；证据完整：否。

实查 artist.name 字段与标准值 Metallica 均存在，完整DISTINCT与既有标准值索引一致。Metallica 是真实 artist，文化部支持其完整中文名“金属乐队”，但已读本地与外部资料没有把裸词“金属”独立作为该乐队简称的证据。相同词形在待审CSV另指 genre.name=Metal，真实流派库还包含 Heavy Metal；删去“乐队”是有歧义的AI猜测，不能据熟悉程度批准。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未取得“金属”作为Metallica简称的独立用法证据。；与 genre.name=Metal 同形且可能泛指金属音乐/材料。

建议：暂不作为可直接使用的艺人别名；补充真实简称来源后仍须限定艺人语境，不得剥夺流派候选。

需人确认：提供可信简称用例并确认优先级；找不到依据时不启用该裸词艺人映射。

原CSV同词候选：artist.name=Metallica；genre.name=Metal。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:9>)：第9行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[158]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:506>)：第506行；kind=standard; candidate_id=v-8cfcf0e35bfb7532e28a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/metallica-introduction.docx](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/metallica-introduction.docx>)：word/document.xml：段落1标题、段落3与5。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [文化部关于同意美国金属乐队到上海市演出的批复](<https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html>)：批复正文，第36行；文市函〔2013〕689号。文化部演出许可正文将中文乐队名与 Metallica 并列；证明专名“金属乐队”的对应关系。 访问：浏览工具已返回可读正文。
- [剑桥英语辞典：metal](<https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul>)：metal noun (MUSIC)及Synonym。辞典列出音乐义并将 heavy metal 视作同义词，支持真实分类间的语义歧义检查。 访问：搜索工具返回可读词条正文。
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.text_values["genre.name"].values：Metal和Heavy Metal。真实类别并存，提供歧义候选

## alias:a-713e91edadb5f817

**Metallica乐队 → artist.name = Metallica**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 artist.name 字段与标准值 Metallica 均存在，完整DISTINCT与既有标准值索引一致。“Metallica乐队”完整保留标准名称 Metallica，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 Metallica。

需人确认：人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

AI推断与局限：中文乐队/乐团限定语与公开band实体类型等价，是AI语言组合判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:10>)：第10行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[158]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:506>)：第506行；kind=standard; candidate_id=v-8cfcf0e35bfb7532e28a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/metallica-introduction.docx](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/metallica-introduction.docx>)：word/document.xml：段落1标题、段落3与5。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [文化部关于同意美国金属乐队到上海市演出的批复](<https://zwgk.mct.gov.cn/zfxxgkml/xzql/xzxk/202012/t20201205_914970.html>)：批复正文，第36行；文市函〔2013〕689号。文化部演出许可正文将中文乐队名与 Metallica 并列；证明专名“金属乐队”的对应关系。 访问：浏览工具已返回可读正文。

## alias:a-a04cacbc074e2ac6

**U2乐队 → artist.name = U2**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 artist.name 字段与标准值 U2 均存在，完整DISTINCT与既有标准值索引一致。“U2乐队”完整保留标准名称 U2，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 U2。

需人确认：人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

AI推断与局限：中文乐队/乐团限定语与公开band实体类型等价，是AI语言组合判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:11>)：第11行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[258]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:606>)：第606行；kind=standard; candidate_id=v-7050c980bcdbcadd0509。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/u2.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/u2.html:4>)：第4行；公开背景第1段/标准名称页脚。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [U2 官网：THE BAND](<https://www.u2.com/pages/band>)：页面标题与成员/建团首段。官网确认 U2 是乐队；“乐队/乐团”为同类中文限定语的AI语言判断，不采纳网页当前活动信息。 访问：浏览工具已返回可读正文。

## alias:a-5875ecf83bb89913

**U2乐团 → artist.name = U2**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 artist.name 字段与标准值 U2 均存在，完整DISTINCT与既有标准值索引一致。“U2乐团”完整保留标准名称 U2，后缀只说明乐队/乐团实体类型。本地公开简介确认其是乐队；没有把英文专名截短或替换成流派。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：在已确定 artist.name 的艺术家查询中可用该完整名称别名；输出仍显示 U2。

需人确认：人审确认项目接受中英混写及乐队/乐团限定语后再决定配置；本轮仅预审。

AI推断与局限：中文乐队/乐团限定语与公开band实体类型等价，是AI语言组合判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:12>)：第12行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:59>)：第59行；tables[artist].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 artist.name; $.text_values["artist.name"].values[258]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:606>)：第606行；kind=standard; candidate_id=v-7050c980bcdbcadd0509。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:31>)：第31行；### artist。字典中的字段范围说明
- [data/docs/raw/d2/u2.html](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/u2.html:4>)：第4行；公开背景第1段/标准名称页脚。本地项目改写艺人材料确认对象背景；不是LLM别名草稿
- [U2 官网：THE BAND](<https://www.u2.com/pages/band>)：页面标题与成员/建团首段。官网确认 U2 是乐队；“乐队/乐团”为同类中文限定语的AI语言判断，不采纳网页当前活动信息。 访问：浏览工具已返回可读正文。

## alias:a-b36489cadceee749

**澳大利亚 → customer.country = Australia**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。“澳大利亚”由外交部国家概况的国名与页面名称支持，对应真实标准值 Australia。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Australia；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Australia；invoice.billing_country=Australia。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:13>)：第13行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[1]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:746>)：第746行；kind=standard; candidate_id=v-08ebc61e3f77af84be3d。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：澳大利亚国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-7d3693714ee37b46

**澳洲 → customer.country = Australia**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。教育部译名索引直接将“澳洲”与 Australia 对应，国家用法有独立依据。该词在用户表达中也可能作大陆/广域地区用语；不能仅因当前国家库无洲级值就把地区意图压成一个国家。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：国家简称与大陆/广域地区意图可能混淆。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Australia；保留另一国家字段的独立口径。 用户谈大陆、洲或多个国家时先澄清范围。

需人确认：确认本项目接受该地区用名，并规定国别/洲别澄清方式。

原CSV同词候选：customer.country=Australia；invoice.billing_country=Australia。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:14>)：第14行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[1]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:746>)：第746行；kind=standard; candidate_id=v-08ebc61e3f77af84be3d。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：澳大利亚国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [教育部重编国语辞典：西文译名索引表](<https://dict.revised.moe.edu.tw/appendix.jsp?ID=28&la=1&page=14&powerMode=0&ver=4>)：澳洲—Australia条目。辞典索引将“澳洲”与 Australia 对应；未证明一切大陆/洲语境都能作国家筛选。 访问：搜索工具返回可读索引节选。

## alias:a-840245fad126ae71

**澳大利亚联邦 → customer.country = Australia**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。“澳大利亚联邦”由外交部国家概况的国名与页面名称支持，对应真实标准值 Australia。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Australia；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Australia；invoice.billing_country=Australia。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:15>)：第15行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[1]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:746>)：第746行；kind=standard; candidate_id=v-08ebc61e3f77af84be3d。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：澳大利亚国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-cf1b483ec6900d1a

**巴西 → customer.country = Brazil**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Brazil 均存在，完整DISTINCT与既有标准值索引一致。“巴西”由外交部国家概况的国名与页面名称支持，对应真实标准值 Brazil。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Brazil；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Brazil；invoice.billing_country=Brazil。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:16>)：第16行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:749>)：第749行；kind=standard; candidate_id=v-95ff10c443473368bada。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：巴西国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-48667df2696e251c

**巴西联邦共和国 → customer.country = Brazil**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Brazil 均存在，完整DISTINCT与既有标准值索引一致。“巴西联邦共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Brazil。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Brazil；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Brazil；invoice.billing_country=Brazil。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:17>)：第17行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:749>)：第749行；kind=standard; candidate_id=v-95ff10c443473368bada。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：巴西国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-3cc0be84e1794908

**加拿大 → customer.country = Canada**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Canada 均存在，完整DISTINCT与既有标准值索引一致。“加拿大”由外交部国家概况的国名与页面名称支持，对应真实标准值 Canada。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Canada；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Canada；invoice.billing_country=Canada。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:18>)：第18行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[5]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:750>)：第750行；kind=standard; candidate_id=v-f357d4a9aa3228c9d69b。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：加拿大国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/bmz_679954/1206_680426/1206x0_680428/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-b25098af9fa5b17a

**法国 → customer.country = France**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。“法国”由外交部国家概况的国名与页面名称支持，对应真实标准值 France。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 France；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=France；invoice.billing_country=France。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:19>)：第19行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[10]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:755>)：第755行；kind=standard; candidate_id=v-352185818871f006e648。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：法国国家概况](<https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-2ad4affe6af89ef4

**法兰西 → customer.country = France**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表独立支持“法兰西”这一国家用名，不能按“正式国名截短”猜出。法兰西也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：历史政体、民族/文化形容语与现代国家指称须区分。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 France；保留另一国家字段的独立口径。 历史/民族语境需澄清，不把历史国家自动改成现代值。

需人确认：确认支持该地区/历史用名，并限制于本快照国家语境。

AI推断与局限：繁体原词形转换为该简体别名是AI通常语言推断。

原CSV同词候选：customer.country=France；invoice.billing_country=France。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:20>)：第20行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[10]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:755>)：第755行；kind=standard; candidate_id=v-352185818871f006e648。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：法国国家概况](<https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [教育部重编国语辞典：世界各国国名表及附图](<https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4>)：欧洲地区：法兰西、德意志、义大利各条目。国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。 访问：浏览工具已返回可读正文。

## alias:a-ca229f69098da675

**法兰西共和国 → customer.country = France**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。“法兰西共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 France。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 France；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=France；invoice.billing_country=France。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:21>)：第21行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[10]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:755>)：第755行；kind=standard; candidate_id=v-352185818871f006e648。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：法国国家概况](<https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-e4d835eae26ef07e

**德国 → customer.country = Germany**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。“德国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Germany。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Germany；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Germany；invoice.billing_country=Germany。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:22>)：第22行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[11]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:756>)：第756行；kind=standard; candidate_id=v-5d7a3cd6809395578682。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：德国国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-9f5bb5a79e3b2818

**德意志 → customer.country = Germany**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表独立支持“德意志”这一国家用名，不能按“正式国名截短”猜出。德意志也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：历史政体、民族/文化形容语与现代国家指称须区分。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Germany；保留另一国家字段的独立口径。 历史/民族语境需澄清，不把历史国家自动改成现代值。

需人确认：确认支持该地区/历史用名，并限制于本快照国家语境。

AI推断与局限：繁体原词形转换为该简体别名是AI通常语言推断。

原CSV同词候选：customer.country=Germany；invoice.billing_country=Germany。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:23>)：第23行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[11]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:756>)：第756行；kind=standard; candidate_id=v-5d7a3cd6809395578682。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：德国国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [教育部重编国语辞典：世界各国国名表及附图](<https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4>)：欧洲地区：法兰西、德意志、义大利各条目。国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。 访问：浏览工具已返回可读正文。

## alias:a-fc51077551e79ac3

**德意志联邦共和国 → customer.country = Germany**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。“德意志联邦共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Germany。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Germany；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Germany；invoice.billing_country=Germany。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:24>)：第24行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[11]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:756>)：第756行；kind=standard; candidate_id=v-5d7a3cd6809395578682。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：德国国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-94e30cebbc64041f

**印度 → customer.country = India**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 India 均存在，完整DISTINCT与既有标准值索引一致。“印度”由外交部国家概况的国名与页面名称支持，对应真实标准值 India。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 India；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=India；invoice.billing_country=India。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:25>)：第25行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[13]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:758>)：第758行；kind=standard; candidate_id=v-ab913411df755fcf0331。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：印度国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-4aca00f05bc3cd6c

**印度共和国 → customer.country = India**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 India 均存在，完整DISTINCT与既有标准值索引一致。“印度共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 India。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 India；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=India；invoice.billing_country=India。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:26>)：第26行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[13]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:758>)：第758行；kind=standard; candidate_id=v-ab913411df755fcf0331。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：印度国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-cbef6f7b472f48eb

**美国 → customer.country = USA**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。“美国”由外交部国家概况的国名与页面名称支持，对应真实标准值 USA。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 USA；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：数据库USA与外交部完整英文国名的缩写等价是通常语言推断；库内真实取值仍按USA。

原CSV同词候选：customer.country=USA；invoice.billing_country=USA。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:27>)：第27行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[22]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:767>)：第767行；kind=standard; candidate_id=v-5d60ecf4270e9f86054a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：美国国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-c43d08f9e0effe4d

**老美 → customer.country = USA**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。该口语词可以指美国人或以人员/政府借指美国；语言讨论支持俚语人员指称，外交部国名并不把它登记为标准国家名称。从“美国人”到所在地/账单国家不是等价关系：国籍、所在地、账单地址必须区分。只有用户明确用它表示国家地理筛选时，USA才可暂作候选。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：俚语人员/政府指称与国家地理实体不等价。；可能把国籍意图误改为customer.country或invoice.billing_country。

建议：明确国别地理语境且所需字段为 customer.country 时才提议 USA；人员、国籍或政治指称应澄清，不直接生成字段过滤。

需人确认：确认俚语是否应纳入检索及其地理筛选约束，不能把语体偏好误作事实错误。

AI推断与局限：该词在某些问句中借指美国的用法是AI语境推断；来源不证明可无条件换成country值。

原CSV同词候选：customer.country=USA；invoice.billing_country=USA。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:28>)：第28行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[22]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:767>)：第767行；kind=standard; candidate_id=v-5d60ecf4270e9f86054a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：美国国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [Language Log：Laowai: the old furriner](<https://languagelog.ldc.upenn.edu/nll/?p=11626>)：关于老美/美国人的讨论段。语言研究者讨论此词的俚语与人员指称；由该词推至国家是语境推断，不是地理字段的字面等价。 访问：浏览工具已返回可读正文。

## alias:a-fab280bc88aa1682

**美利坚合众国 → customer.country = USA**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。“美利坚合众国”由外交部国家概况的国名与页面名称支持，对应真实标准值 USA。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 USA；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：数据库USA与外交部完整英文国名的缩写等价是通常语言推断；库内真实取值仍按USA。

原CSV同词候选：customer.country=USA；invoice.billing_country=USA。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:29>)：第29行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[22]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:767>)：第767行；kind=standard; candidate_id=v-5d60ecf4270e9f86054a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：美国国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-9a9f0da60f84554c

**英国 → customer.country = United Kingdom**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。“英国”由外交部国家概况的国名与页面名称支持，对应真实标准值 United Kingdom。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=United Kingdom；invoice.billing_country=United Kingdom。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:30>)：第30行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[23]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:768>)：第768行；kind=standard; candidate_id=v-ab0ca67796ef4a666592。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：英国国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-b507c7d7ee1c26e7

**联合王国 → customer.country = United Kingdom**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。剑桥中英词条直接支持此中文短名与 United Kingdom 对应；外交部全称提供完整国家对象，不会缩成英格兰。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：此判断限定本项目现代国家值，不用于历史或其他联合王国语境。

原CSV同词候选：customer.country=United Kingdom；invoice.billing_country=United Kingdom。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:31>)：第31行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[23]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:768>)：第768行；kind=standard; candidate_id=v-ab0ca67796ef4a666592。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：英国国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [剑桥中文简体—英语辞典：联合王国](<https://dictionary.cambridge.org/zht/%E8%A9%9E%E5%85%B8/%E6%BC%A2%E8%AA%9E-%E7%B0%A1%E9%AB%94-%E8%8B%B1%E8%AA%9E/%E8%81%94%E5%90%88%E7%8E%8B%E5%9B%BD>)：联合王国主词条。中英词条直接支持 United Kingdom 的中文短名。 访问：搜索工具返回可读词条正文；open完整页返回 Internal Error。

## alias:a-1f08c5b75168548d

**大不列颠及北爱尔兰联合王国 → customer.country = United Kingdom**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。“大不列颠及北爱尔兰联合王国”由外交部国家概况的国名与页面名称支持，对应真实标准值 United Kingdom。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=United Kingdom；invoice.billing_country=United Kingdom。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:32>)：第32行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[23]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:768>)：第768行；kind=standard; candidate_id=v-ab0ca67796ef4a666592。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：英国国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-6f2b17a026a9ef9b

**古典 → genre.name = Classical**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Classical 均存在，完整DISTINCT与既有标准值索引一致。“古典”有剑桥 classical/ classical music 音乐义支持，目标为真实流派 Classical。在已明确 genre.name 的查询中，省略“音乐”不会改成艺术家或年代；不将它限制为字典列举的某个作曲年代。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：音乐流派语境中可用于 Classical；艺术/建筑等其他古典义不得绑定。

需人确认：确认项目Classical分类使用范围，避免把语言词典时代定义当成数据库分类规则。

AI推断与局限：省略“音乐”只在已确定genre字段时补全，是AI语境判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:33>)：第33行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1163>)：第1163行；kind=standard; candidate_id=v-e60d201656eb15032b4e。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：classical](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical>)：classical adjective (ART, MUSIC ETC)。词典支持古典义；结合数据库流派字段选取音乐义。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：classical-music](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical-music>)：主词条。词典支持 classical music 的中文音乐流派译法。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-fb76d9986e52aa10

**古典音乐 → genre.name = Classical**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Classical 均存在，完整DISTINCT与既有标准值索引一致。“古典音乐”有剑桥 classical/ classical music 音乐义支持，目标为真实流派 Classical。在已明确 genre.name 的查询中，省略“音乐”不会改成艺术家或年代；不将它限制为字典列举的某个作曲年代。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：音乐流派语境中可用于 Classical；艺术/建筑等其他古典义不得绑定。

需人确认：确认项目Classical分类使用范围，避免把语言词典时代定义当成数据库分类规则。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:34>)：第34行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1163>)：第1163行；kind=standard; candidate_id=v-e60d201656eb15032b4e。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：classical](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical>)：classical adjective (ART, MUSIC ETC)。词典支持古典义；结合数据库流派字段选取音乐义。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：classical-music](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/classical-music>)：主词条。词典支持 classical music 的中文音乐流派译法。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-ae481372f2653475

**爵士 → genre.name = Jazz**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Jazz 均存在，完整DISTINCT与既有标准值索引一致。词典的音乐义支持“爵士”与 Jazz 对应；真实库有Jazz。省略“乐”可在音乐流派语境成立，不能把爵位称号或品牌等非音乐义当作genre过滤。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：genre明确时可用Jazz；若“爵士”指人名/爵位/品牌则澄清。

需人确认：确认只接受音乐流派语境。

AI推断与局限：短词音乐义通过genre上下文选定，是AI语境判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:35>)：第35行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[11]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1170>)：第1170行；kind=standard; candidate_id=v-5394ef0bac37e993f465。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：jazz](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/jazz>)：jazz noun [U] 音乐义。词典支持爵士音乐义，也列出非音乐品牌义；须限 genre.name。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-f3ab57aac4760fac

**爵士乐 → genre.name = Jazz**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Jazz 均存在，完整DISTINCT与既有标准值索引一致。词典的音乐义支持“爵士乐”与 Jazz 对应；真实库有Jazz。省略“乐”可在音乐流派语境成立，不能把爵位称号或品牌等非音乐义当作genre过滤。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：genre明确时可用Jazz；若“爵士”指人名/爵位/品牌则澄清。

需人确认：确认只接受音乐流派语境。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:36>)：第36行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[11]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1170>)：第1170行；kind=standard; candidate_id=v-5394ef0bac37e993f465。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：jazz](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/jazz>)：jazz noun [U] 音乐义。词典支持爵士音乐义，也列出非音乐品牌义；须限 genre.name。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-439ce0734774f114

**金属 → genre.name = Metal**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Metal 均存在，完整DISTINCT与既有标准值索引一致。“金属”在音乐上下文可表达Metal，字典有metal音乐义和对应金属音乐术语；但真实genre同时有Metal和Heavy Metal，词典还把两者列为一般语言同义。因此能作Metal候选不代表数据库分类可合并或唯一绑定。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：真实数据库Metal与Heavy Metal是不同标准分类，泛称可能覆盖两者。；同一裸词在待审CSV还候选artist.name=Metallica，且另有材料义。

建议：明确用户指数据库Metal分类时选Metal；泛称金属音乐时展示Metal/Heavy Metal范围并澄清；艺人语境保留独立候选。

需人确认：确定泛称金属音乐的业务范围；多候选许可不是自动将标准值合并或唯一绑定。

AI推断与局限：中文“金属乐”与metal音乐义的术语组合属于AI语言推断，来源不定义Chinook类别边界。

原CSV同词候选：artist.name=Metallica；genre.name=Metal。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:37>)：第37行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[13]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1172>)：第1172行；kind=standard; candidate_id=v-bf1c51869eccaa9deddc。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英语辞典：metal](<https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul>)：metal noun (MUSIC)及Synonym。辞典列出音乐义并将 heavy metal 视作同义词，支持真实分类间的语义歧义检查。 访问：搜索工具返回可读词条正文。
- [剑桥英汉辞典：heavy-metal](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/heavy-metal>)：heavy metal noun (MUSIC)。词典支持重金属音乐义；此值与数据库 Metal 类别同列并存。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-f637ff312a6fead6

**金属乐 → genre.name = Metal**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Metal 均存在，完整DISTINCT与既有标准值索引一致。“金属乐”在音乐上下文可表达Metal，字典有metal音乐义和对应金属音乐术语；但真实genre同时有Metal和Heavy Metal，词典还把两者列为一般语言同义。因此能作Metal候选不代表数据库分类可合并或唯一绑定。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：真实数据库Metal与Heavy Metal是不同标准分类，泛称可能覆盖两者。

建议：明确用户指数据库Metal分类时选Metal；泛称金属音乐时展示Metal/Heavy Metal范围并澄清；艺人语境保留独立候选。

需人确认：确定泛称金属音乐的业务范围；多候选许可不是自动将标准值合并或唯一绑定。

AI推断与局限：中文“金属乐”与metal音乐义的术语组合属于AI语言推断，来源不定义Chinook类别边界。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:38>)：第38行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[13]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1172>)：第1172行；kind=standard; candidate_id=v-bf1c51869eccaa9deddc。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英语辞典：metal](<https://dictionary.cambridge.org/us/dictionary/english/metal?topic=pop-rock-and-soul>)：metal noun (MUSIC)及Synonym。辞典列出音乐义并将 heavy metal 视作同义词，支持真实分类间的语义歧义检查。 访问：搜索工具返回可读词条正文。
- [剑桥英汉辞典：heavy-metal](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/heavy-metal>)：heavy metal noun (MUSIC)。词典支持重金属音乐义；此值与数据库 Metal 类别同列并存。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-10514461292c596d

**流行 → genre.name = Pop**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Pop 均存在，完整DISTINCT与既有标准值索引一致。剑桥 Pop 的音乐义支持“流行”；标准对象真实存在。中文“流行”还可表示受欢迎程度，“最流行的曲目”不是genre=Pop的同义改写，必须识别这是分类请求。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：流派短名与受欢迎程度形容词多义。

建议：明确请求Pop流派时可用；热度/销量/流行程度比较不自动改成Pop过滤。

需人确认：确认分类语义与流行程度指标分开处理。

AI推断与局限：从裸词“流行”选定Pop音乐义是AI上下文推断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:39>)：第39行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[15]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1174>)：第1174行；kind=standard; candidate_id=v-d458c8175a18de796e8c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：pop](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/pop>)：pop noun (MUSIC)。词典支持 Pop 的音乐义，不能把普通形容词“流行”当作热度排序指标。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-34701ceea8df41eb

**流行音乐 → genre.name = Pop**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Pop 均存在，完整DISTINCT与既有标准值索引一致。剑桥 Pop 的音乐义支持“流行音乐”；标准对象真实存在。中文“流行”还可表示受欢迎程度，“最流行的曲目”不是genre=Pop的同义改写，必须识别这是分类请求。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：明确请求Pop流派时可用；热度/销量/流行程度比较不自动改成Pop过滤。

需人确认：确认分类语义与流行程度指标分开处理。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:40>)：第40行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[15]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1174>)：第1174行；kind=standard; candidate_id=v-d458c8175a18de796e8c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：pop](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/pop>)：pop noun (MUSIC)。词典支持 Pop 的音乐义，不能把普通形容词“流行”当作热度排序指标。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-cb69b4bf22161e6e

**摇滚 → genre.name = Rock**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Rock 均存在，完整DISTINCT与既有标准值索引一致。独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“摇滚”可表达 Rock，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：同字段同中文词形存在Rock/Rock And Roll两候选。

建议：保留 Rock 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。

需人确认：确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。

AI推断与局限：短词省略“乐”是AI中文语言判断；仍保留两分类候选。

原CSV同词候选：genre.name=Rock；genre.name=Rock And Roll。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:41>)：第41行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[18]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1177>)：第1177行；kind=standard; candidate_id=v-5abaeb142337ce5b27ed。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：rock](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock>)：rock noun (MUSIC)。词典支持 Rock 的中文音乐义。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：rock-and-roll](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll>)：主词条音乐义。词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。 访问：搜索工具返回可读词条正文；Rock And Roll完整页open为403。

## alias:a-5972cabfe64bae77

**摇滚乐 → genre.name = Rock**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Rock 均存在，完整DISTINCT与既有标准值索引一致。独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“摇滚乐”可表达 Rock，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：同字段同中文词形存在Rock/Rock And Roll两候选。

建议：保留 Rock 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。

需人确认：确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。

原CSV同词候选：genre.name=Rock；genre.name=Rock And Roll。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:42>)：第42行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[18]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1177>)：第1177行；kind=standard; candidate_id=v-5abaeb142337ce5b27ed。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：rock](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock>)：rock noun (MUSIC)。词典支持 Rock 的中文音乐义。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：rock-and-roll](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll>)：主词条音乐义。词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。 访问：搜索工具返回可读词条正文；Rock And Roll完整页open为403。

## alias:a-0e44ca874f4ba96f

**摇滚乐 → genre.name = Rock And Roll**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Rock And Roll 均存在，完整DISTINCT与既有标准值索引一致。独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“摇滚乐”可表达 Rock And Roll，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：同字段同中文词形存在Rock/Rock And Roll两候选。

建议：保留 Rock And Roll 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。

需人确认：确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。

原CSV同词候选：genre.name=Rock；genre.name=Rock And Roll。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:43>)：第43行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[19]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1178>)：第1178行；kind=standard; candidate_id=v-10facd793602b59518e7。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：rock](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock>)：rock noun (MUSIC)。词典支持 Rock 的中文音乐义。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：rock-and-roll](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll>)：主词条音乐义。词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。 访问：搜索工具返回可读词条正文；Rock And Roll完整页open为403。

## alias:a-c748b229db869a4e

**节奏摇滚 → genre.name = Rock And Roll**

参考状态：证据不足；处置建议：证据不足；实际状态：不适用（别名配置审核，未生成预测）；证据完整：否。

实查 genre.name 字段与标准值 Rock And Roll 均存在，完整DISTINCT与既有标准值索引一致。目标 Rock And Roll 在真实库存在，但已读本地字典仅说明流派字段，没有给出“节奏摇滚”译名。独立英汉词条支持一般摇滚译法，未支持加入“节奏”后能专指这一数据库分类；本轮检索没有取得该译名的可信来源。不能因为它能人为避开Rock歧义就认定翻译正确，也不能用未搜到断言该词绝不存在。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：没有独立来源证明“节奏摇滚”专指Rock And Roll。；加入“节奏”的意图可能只是人为区分类别，非真实译名依据。

建议：暂不启用该译名；补充可信音乐术语来源或明确人审定义后再评估，保留Rock/Rock And Roll本来的分类差异。

需人确认：补证据并确认术语；不要仅依照既有“拒绝”建议盖章。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:44>)：第44行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[19]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1178>)：第1178行；kind=standard; candidate_id=v-10facd793602b59518e7。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：rock](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock>)：rock noun (MUSIC)。词典支持 Rock 的中文音乐义。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：rock-and-roll](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll>)：主词条音乐义。词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。 访问：搜索工具返回可读词条正文；Rock And Roll完整页open为403。

## alias:a-4c5e26e87ffb2aa2

**澳大利亚 → invoice.billing_country = Australia**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。“澳大利亚”由外交部国家概况的国名与页面名称支持，对应真实标准值 Australia。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Australia；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Australia；invoice.billing_country=Australia。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:45>)：第45行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[1]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1297>)：第1297行；kind=standard; candidate_id=v-30a35165311e0978a54c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：澳大利亚国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-b5ca3e94894dee8d

**澳洲 → invoice.billing_country = Australia**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。教育部译名索引直接将“澳洲”与 Australia 对应，国家用法有独立依据。该词在用户表达中也可能作大陆/广域地区用语；不能仅因当前国家库无洲级值就把地区意图压成一个国家。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：国家简称与大陆/广域地区意图可能混淆。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Australia；保留另一国家字段的独立口径。 用户谈大陆、洲或多个国家时先澄清范围。

需人确认：确认本项目接受该地区用名，并规定国别/洲别澄清方式。

原CSV同词候选：customer.country=Australia；invoice.billing_country=Australia。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:46>)：第46行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[1]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1297>)：第1297行；kind=standard; candidate_id=v-30a35165311e0978a54c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：澳大利亚国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [教育部重编国语辞典：西文译名索引表](<https://dict.revised.moe.edu.tw/appendix.jsp?ID=28&la=1&page=14&powerMode=0&ver=4>)：澳洲—Australia条目。辞典索引将“澳洲”与 Australia 对应；未证明一切大陆/洲语境都能作国家筛选。 访问：搜索工具返回可读索引节选。

## alias:a-f2ecb45e404feda1

**澳大利亚联邦 → invoice.billing_country = Australia**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Australia 均存在，完整DISTINCT与既有标准值索引一致。“澳大利亚联邦”由外交部国家概况的国名与页面名称支持，对应真实标准值 Australia。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Australia；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Australia；invoice.billing_country=Australia。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:47>)：第47行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[1]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1297>)：第1297行；kind=standard; candidate_id=v-30a35165311e0978a54c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：澳大利亚国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/dyz_681240/1206_681242/1206x0_681244/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-bfc3cf35431dcceb

**巴西 → invoice.billing_country = Brazil**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Brazil 均存在，完整DISTINCT与既有标准值索引一致。“巴西”由外交部国家概况的国名与页面名称支持，对应真实标准值 Brazil。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Brazil；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Brazil；invoice.billing_country=Brazil。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:48>)：第48行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1300>)：第1300行；kind=standard; candidate_id=v-035a5fa9bd5fc4b4175e。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：巴西国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-e8e5e4fe2d99ff1b

**巴西联邦共和国 → invoice.billing_country = Brazil**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Brazil 均存在，完整DISTINCT与既有标准值索引一致。“巴西联邦共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Brazil。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Brazil；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Brazil；invoice.billing_country=Brazil。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:49>)：第49行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1300>)：第1300行；kind=standard; candidate_id=v-035a5fa9bd5fc4b4175e。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：巴西国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/nmz_680924/1206_680974/1206x0_680976/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-b33ce127772f748d

**加拿大 → invoice.billing_country = Canada**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Canada 均存在，完整DISTINCT与既有标准值索引一致。“加拿大”由外交部国家概况的国名与页面名称支持，对应真实标准值 Canada。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Canada；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Canada；invoice.billing_country=Canada。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:50>)：第50行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[5]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1301>)：第1301行；kind=standard; candidate_id=v-ed13ace46d49a0165890。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：加拿大国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/bmz_679954/1206_680426/1206x0_680428/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-1146eff0ef203810

**法国 → invoice.billing_country = France**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。“法国”由外交部国家概况的国名与页面名称支持，对应真实标准值 France。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 France；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=France；invoice.billing_country=France。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:51>)：第51行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[10]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1306>)：第1306行；kind=standard; candidate_id=v-da1995626f6b421035ba。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：法国国家概况](<https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-9eb72fa09563fb7e

**法兰西 → invoice.billing_country = France**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表独立支持“法兰西”这一国家用名，不能按“正式国名截短”猜出。法兰西也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：历史政体、民族/文化形容语与现代国家指称须区分。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 France；保留另一国家字段的独立口径。 历史/民族语境需澄清，不把历史国家自动改成现代值。

需人确认：确认支持该地区/历史用名，并限制于本快照国家语境。

AI推断与局限：繁体原词形转换为该简体别名是AI通常语言推断。

原CSV同词候选：customer.country=France；invoice.billing_country=France。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:52>)：第52行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[10]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1306>)：第1306行；kind=standard; candidate_id=v-da1995626f6b421035ba。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：法国国家概况](<https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [教育部重编国语辞典：世界各国国名表及附图](<https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4>)：欧洲地区：法兰西、德意志、义大利各条目。国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。 访问：浏览工具已返回可读正文。

## alias:a-99f7789e108299a0

**法兰西共和国 → invoice.billing_country = France**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 France 均存在，完整DISTINCT与既有标准值索引一致。“法兰西共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 France。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 France；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=France；invoice.billing_country=France。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:53>)：第53行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[10]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1306>)：第1306行；kind=standard; candidate_id=v-da1995626f6b421035ba。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：法国国家概况](<https://www.mfa.gov.cn/web//gjhdq_676201/gj_676203/oz_678770/1206_679134/1206x0_679136/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-3414db81951a6279

**德国 → invoice.billing_country = Germany**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。“德国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Germany。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Germany；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Germany；invoice.billing_country=Germany。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:54>)：第54行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[11]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1307>)：第1307行；kind=standard; candidate_id=v-475210ef4e08328852ec。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：德国国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-604796b76eb1cd3b

**德意志 → invoice.billing_country = Germany**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表独立支持“德意志”这一国家用名，不能按“正式国名截短”猜出。德意志也可能出现在历史政体、民族/文化形容语中，需限定本项目当代国家筛选。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：历史政体、民族/文化形容语与现代国家指称须区分。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Germany；保留另一国家字段的独立口径。 历史/民族语境需澄清，不把历史国家自动改成现代值。

需人确认：确认支持该地区/历史用名，并限制于本快照国家语境。

AI推断与局限：繁体原词形转换为该简体别名是AI通常语言推断。

原CSV同词候选：customer.country=Germany；invoice.billing_country=Germany。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:55>)：第55行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[11]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1307>)：第1307行；kind=standard; candidate_id=v-475210ef4e08328852ec。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：德国国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [教育部重编国语辞典：世界各国国名表及附图](<https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4>)：欧洲地区：法兰西、德意志、义大利各条目。国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。 访问：浏览工具已返回可读正文。

## alias:a-43165309220a1f56

**德意志联邦共和国 → invoice.billing_country = Germany**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Germany 均存在，完整DISTINCT与既有标准值索引一致。“德意志联邦共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 Germany。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Germany；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=Germany；invoice.billing_country=Germany。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:56>)：第56行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[11]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1307>)：第1307行；kind=standard; candidate_id=v-475210ef4e08328852ec。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：德国国家概况](<https://www.mfa.gov.cn/gjhdq_676201/gj_676203/oz_678770/1206_679086/1206x0_679088/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-9c79948752527793

**印度 → invoice.billing_country = India**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 India 均存在，完整DISTINCT与既有标准值索引一致。“印度”由外交部国家概况的国名与页面名称支持，对应真实标准值 India。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 India；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=India；invoice.billing_country=India。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:57>)：第57行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[13]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1309>)：第1309行；kind=standard; candidate_id=v-989037d188e20fe3ee6c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：印度国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-5819628db78075fb

**印度共和国 → invoice.billing_country = India**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 India 均存在，完整DISTINCT与既有标准值索引一致。“印度共和国”由外交部国家概况的国名与页面名称支持，对应真实标准值 India。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 India；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=India；invoice.billing_country=India。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:58>)：第58行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[13]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1309>)：第1309行；kind=standard; candidate_id=v-989037d188e20fe3ee6c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：印度国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/yz_645708/yd_648314/gqjj_648322/200702/t20070227_9307236.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-dca9d898c8a31e37

**美国 → invoice.billing_country = USA**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。“美国”由外交部国家概况的国名与页面名称支持，对应真实标准值 USA。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 USA；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：数据库USA与外交部完整英文国名的缩写等价是通常语言推断；库内真实取值仍按USA。

原CSV同词候选：customer.country=USA；invoice.billing_country=USA。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:59>)：第59行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[22]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1318>)：第1318行；kind=standard; candidate_id=v-ab7ca55351c9f4bae96b。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：美国国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-9d6edadfda3e46a9

**老美 → invoice.billing_country = USA**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。该口语词可以指美国人或以人员/政府借指美国；语言讨论支持俚语人员指称，外交部国名并不把它登记为标准国家名称。从“美国人”到所在地/账单国家不是等价关系：国籍、所在地、账单地址必须区分。只有用户明确用它表示国家地理筛选时，USA才可暂作候选。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：俚语人员/政府指称与国家地理实体不等价。；可能把国籍意图误改为customer.country或invoice.billing_country。

建议：明确国别地理语境且所需字段为 invoice.billing_country 时才提议 USA；人员、国籍或政治指称应澄清，不直接生成字段过滤。

需人确认：确认俚语是否应纳入检索及其地理筛选约束，不能把语体偏好误作事实错误。

AI推断与局限：该词在某些问句中借指美国的用法是AI语境推断；来源不证明可无条件换成country值。

原CSV同词候选：customer.country=USA；invoice.billing_country=USA。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:60>)：第60行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[22]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1318>)：第1318行；kind=standard; candidate_id=v-ab7ca55351c9f4bae96b。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：美国国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [Language Log：Laowai: the old furriner](<https://languagelog.ldc.upenn.edu/nll/?p=11626>)：关于老美/美国人的讨论段。语言研究者讨论此词的俚语与人员指称；由该词推至国家是语境推断，不是地理字段的字面等价。 访问：浏览工具已返回可读正文。

## alias:a-6d34332b7a54aaa8

**美利坚合众国 → invoice.billing_country = USA**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 USA 均存在，完整DISTINCT与既有标准值索引一致。“美利坚合众国”由外交部国家概况的国名与页面名称支持，对应真实标准值 USA。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 USA；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：数据库USA与外交部完整英文国名的缩写等价是通常语言推断；库内真实取值仍按USA。

原CSV同词候选：customer.country=USA；invoice.billing_country=USA。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:61>)：第61行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[22]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1318>)：第1318行；kind=standard; candidate_id=v-ab7ca55351c9f4bae96b。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：美国国家概况](<https://cs.mfa.gov.cn/zggmcg/ljmdd/bmz_655327/mg_656793/gqjj_656801/200608/t20060814_9359417.shtml>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-a51a0dfa5111c6b0

**英国 → invoice.billing_country = United Kingdom**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。“英国”由外交部国家概况的国名与页面名称支持，对应真实标准值 United Kingdom。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=United Kingdom；invoice.billing_country=United Kingdom。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:62>)：第62行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[23]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1319>)：第1319行；kind=standard; candidate_id=v-9b20c6c3e4caad1de69a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：英国国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-7528c8542cbf31a0

**联合王国 → invoice.billing_country = United Kingdom**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。剑桥中英词条直接支持此中文短名与 United Kingdom 对应；外交部全称提供完整国家对象，不会缩成英格兰。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：此判断限定本项目现代国家值，不用于历史或其他联合王国语境。

原CSV同词候选：customer.country=United Kingdom；invoice.billing_country=United Kingdom。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:63>)：第63行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[23]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1319>)：第1319行；kind=standard; candidate_id=v-9b20c6c3e4caad1de69a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：英国国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [剑桥中文简体—英语辞典：联合王国](<https://dictionary.cambridge.org/zht/%E8%A9%9E%E5%85%B8/%E6%BC%A2%E8%AA%9E-%E7%B0%A1%E9%AB%94-%E8%8B%B1%E8%AA%9E/%E8%81%94%E5%90%88%E7%8E%8B%E5%9B%BD>)：联合王国主词条。中英词条直接支持 United Kingdom 的中文短名。 访问：搜索工具返回可读词条正文；open完整页返回 Internal Error。

## alias:a-8fd10b20a82508de

**大不列颠及北爱尔兰联合王国 → invoice.billing_country = United Kingdom**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 United Kingdom 均存在，完整DISTINCT与既有标准值索引一致。“大不列颠及北爱尔兰联合王国”由外交部国家概况的国名与页面名称支持，对应真实标准值 United Kingdom。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 United Kingdom；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

原CSV同词候选：customer.country=United Kingdom；invoice.billing_country=United Kingdom。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:64>)：第64行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[23]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1319>)：第1319行；kind=standard; candidate_id=v-9b20c6c3e4caad1de69a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：英国国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679906/1206x0_679908/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-6799bc523f9e8693

**AAC音频文件 → media_type.name = AAC audio file**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“AAC音频文件”保留AAC与audio的普通译义，未带Protected/Purchased修饰，适合作为数据库普通AAC类别的译名候选。但真实media_type还有Protected AAC与Purchased AAC；用户泛称AAC音频/文件可能指格式家族，不能自动只筛普通AAC。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：AAC格式泛称可能覆盖普通、Protected、Purchased三个真实枚举值。

建议：用户明确普通AAC类别时选AAC audio file；泛问AAC格式先澄清是否包含三个AAC类别。

需人确认：确认“普通类别”与“AAC格式总范围”的区别，禁止把父类说法直接绑定单个子类。

AI推断与局限：AAC+audio/file的中文组合是AI常用语言判断，格式缩写不变。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:65>)：第65行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[0]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1400>)：第1400行；kind=standard; candidate_id=v-48a78d9abfb7317315e9。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-7b241be59eef3bbb

**AAC音频 → media_type.name = AAC audio file**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“AAC音频”保留AAC与audio的普通译义，未带Protected/Purchased修饰，适合作为数据库普通AAC类别的译名候选。但真实media_type还有Protected AAC与Purchased AAC；用户泛称AAC音频/文件可能指格式家族，不能自动只筛普通AAC。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：AAC格式泛称可能覆盖普通、Protected、Purchased三个真实枚举值。

建议：用户明确普通AAC类别时选AAC audio file；泛问AAC格式先澄清是否包含三个AAC类别。

需人确认：确认“普通类别”与“AAC格式总范围”的区别，禁止把父类说法直接绑定单个子类。

AI推断与局限：AAC+audio/file的中文组合是AI常用语言判断，格式缩写不变。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:66>)：第66行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[0]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1400>)：第1400行；kind=standard; candidate_id=v-48a78d9abfb7317315e9。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-623dcb996bdf111b

**MPEG音频文件 → media_type.name = MPEG audio file**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 MPEG audio file 均存在，完整DISTINCT与既有标准值索引一致。“MPEG音频文件”保持MPEG格式缩写及audio音频类型，中文组合翻译不涉及缩写展开。真实库另有Protected MPEG-4 video file，但其中video与本行audio不同；不能仅匹配MPEG词段忽略音频/视频限定。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：media_type字段和音频语境明确时可用该枚举；省略音频只说MPEG时重新澄清，不延伸本别名。

需人确认：确认保留音频限定，避免MPEG音频与MPEG-4视频的词段匹配冲突。

AI推断与局限：MPEG+audio/file的中文组合是AI常用语言判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:67>)：第67行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[1]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1401>)：第1401行；kind=standard; candidate_id=v-e30ed9ffef5d9f1c3079。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-283ad9fbc2d748a9

**MPEG音频 → media_type.name = MPEG audio file**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 MPEG audio file 均存在，完整DISTINCT与既有标准值索引一致。“MPEG音频”保持MPEG格式缩写及audio音频类型，中文组合翻译不涉及缩写展开。真实库另有Protected MPEG-4 video file，但其中video与本行audio不同；不能仅匹配MPEG词段忽略音频/视频限定。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：media_type字段和音频语境明确时可用该枚举；省略音频只说MPEG时重新澄清，不延伸本别名。

需人确认：确认保留音频限定，避免MPEG音频与MPEG-4视频的词段匹配冲突。

AI推断与局限：MPEG+audio/file的中文组合是AI常用语言判断。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:68>)：第68行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[1]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1401>)：第1401行；kind=standard; candidate_id=v-e30ed9ffef5d9f1c3079。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-bfc4b2a75ae6d393

**受保护AAC音频文件 → media_type.name = Protected AAC audio file**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 Protected AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“受保护AAC音频文件”保留标准名称 Protected AAC audio file 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：媒体类型字段明确时可用；精确映射 Protected AAC audio file 并保留Protected，不能推断保护机制或客户付款状态。

需人确认：确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。

AI推断与局限：Protected+AAC+audio/file中文组合是AI语言推断，未证明DRM实现或法律权利状态。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:69>)：第69行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[2]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1402>)：第1402行；kind=standard; candidate_id=v-df2c0ee6493160aa791a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：protected](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected>)：一般形容词义。词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-e6995d2d188f2d9e

**受保护AAC音频 → media_type.name = Protected AAC audio file**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 Protected AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“受保护AAC音频”保留标准名称 Protected AAC audio file 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：媒体类型字段明确时可用；精确映射 Protected AAC audio file 并保留Protected，不能推断保护机制或客户付款状态。

需人确认：确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。

AI推断与局限：Protected+AAC+audio/file中文组合是AI语言推断，未证明DRM实现或法律权利状态。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:70>)：第70行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[2]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1402>)：第1402行；kind=standard; candidate_id=v-df2c0ee6493160aa791a。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：protected](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected>)：一般形容词义。词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-f1475c651575231c

**受保护MPEG-4视频文件 → media_type.name = Protected MPEG-4 video file**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 Protected MPEG-4 video file 均存在，完整DISTINCT与既有标准值索引一致。“受保护MPEG-4视频文件”保留标准名称 Protected MPEG-4 video file 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：媒体类型字段明确时可用；精确映射 Protected MPEG-4 video file 并保留Protected，不能推断保护机制或客户付款状态。

需人确认：确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。

AI推断与局限：video=file中的视频/文件为通常语言知识；未展开MPEG-4缩写或推断实际编码实现。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:71>)：第71行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[3]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1403>)：第1403行；kind=standard; candidate_id=v-063294056fde53d4a70e。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：protected](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected>)：一般形容词义。词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-546993461dc3354d

**受保护MPEG-4视频 → media_type.name = Protected MPEG-4 video file**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 Protected MPEG-4 video file 均存在，完整DISTINCT与既有标准值索引一致。“受保护MPEG-4视频”保留标准名称 Protected MPEG-4 video file 的Protected修饰、格式缩写及音频/视频类型；基于独立常用词义作中文组合翻译，未把Protected AAC缩成普通AAC，亦未把MPEG-4视频改成MPEG音频。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：媒体类型字段明确时可用；精确映射 Protected MPEG-4 video file 并保留Protected，不能推断保护机制或客户付款状态。

需人确认：确认该翻译用于枚举类型名称，保护实现/用户权限如需解释须有额外来源。

AI推断与局限：video=file中的视频/文件为通常语言知识；未展开MPEG-4缩写或推断实际编码实现。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:72>)：第72行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[3]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1403>)：第1403行；kind=standard; candidate_id=v-063294056fde53d4a70e。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：protected](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/protected>)：一般形容词义。词典支持受保护的字面描述，不证明具体 DRM 实现或客户付款状态。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-4fbad68319f9e10e

**已购买AAC音频文件 → media_type.name = Purchased AAC audio file**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 Purchased AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“已购买AAC音频文件”对应标准 Purchased AAC audio file 的中文组合，保留购买相关修饰与AAC音频。Purchased在此是真实媒体类型名称，不是“某客户已成功付款”的数据库事实；不能用media_type替代invoice或支付状态。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：只按媒体类型枚举 Purchased AAC audio file 使用；客户购买行为需销售关联与业务口径，付款状态无本字段证据。

需人确认：确认Purchased命名翻译及媒体类型/购买行为/支付状态边界。

AI推断与局限：Purchased形容词完成态的中文“已购买”为AI语法判断，独立词典只证明购买词义。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:73>)：第73行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1404>)：第1404行；kind=standard; candidate_id=v-d0ff7c80f8657fcfd77c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：purchase](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase>)：purchase verb / noun (BUYING)。词典支持购买语义；Purchased 的完成态中文表达为AI语法组合判断。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-0c3df10756626f4a

**购买AAC音频文件 → media_type.name = Purchased AAC audio file**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 Purchased AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“购买AAC音频文件”对应标准 Purchased AAC audio file 的中文组合，保留购买相关修饰与AAC音频。Purchased在此是真实媒体类型名称，不是“某客户已成功付款”的数据库事实；不能用media_type替代invoice或支付状态。该词形未明确完成态，还可能是“购买一个AAC文件”的动作请求；必须先确认是在问类型标签。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未标“已”，类型标签与购买动作请求多义。

建议：只按媒体类型枚举 Purchased AAC audio file 使用；客户购买行为需销售关联与业务口径，付款状态无本字段证据。 若为购买行为或动作请求，先澄清，不据该词形唯一选择Purchased类型。

需人确认：确认Purchased命名翻译及媒体类型/购买行为/支付状态边界。

AI推断与局限：Purchased形容词完成态的中文“已购买”为AI语法判断，独立词典只证明购买词义。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:74>)：第74行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1404>)：第1404行；kind=standard; candidate_id=v-d0ff7c80f8657fcfd77c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：purchase](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase>)：purchase verb / noun (BUYING)。词典支持购买语义；Purchased 的完成态中文表达为AI语法组合判断。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-a974e81df263a782

**已购买AAC音频 → media_type.name = Purchased AAC audio file**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 media_type.name 字段与标准值 Purchased AAC audio file 均存在，完整DISTINCT与既有标准值索引一致。“已购买AAC音频”对应标准 Purchased AAC audio file 的中文组合，保留购买相关修饰与AAC音频。Purchased在此是真实媒体类型名称，不是“某客户已成功付款”的数据库事实；不能用media_type替代invoice或支付状态。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：只按媒体类型枚举 Purchased AAC audio file 使用；客户购买行为需销售关联与业务口径，付款状态无本字段证据。

需人确认：确认Purchased命名翻译及媒体类型/购买行为/支付状态边界。

AI推断与局限：Purchased形容词完成态的中文“已购买”为AI语法判断，独立词典只证明购买词义。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:75>)：第75行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:545>)：第545行；tables[media_type].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 media_type.name; $.text_values["media_type.name"].values[4]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1404>)：第1404行；kind=standard; candidate_id=v-d0ff7c80f8657fcfd77c。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:131>)：第131行；### media_type。字典中的字段范围说明
- [剑桥英汉辞典：audio](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/audio>)：audio adjective / audio noun。词典支持音频用语；格式缩写保持数据库原词形。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：purchase](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/purchase>)：purchase verb / noun (BUYING)。词典支持购买语义；Purchased 的完成态中文表达为AI语法组合判断。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。

## alias:a-d0e9fad30baaded8

**意大利 → customer.country = Italy**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。“意大利”由外交部国家概况的国名与页面名称支持，对应真实标准值 Italy。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：外交部意大利对象及中文国名支持国家指称；Italy英文名对应是通常语言知识，并由既有真实数据库值核验。

原CSV同词候选：customer.country=Italy；invoice.billing_country=Italy。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:76>)：第76行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[15]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:760>)：第760行；kind=standard; candidate_id=v-ec3f5c892a21c72c35e1。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：意大利国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-97a541d02a9d6f5b

**义大利 → customer.country = Italy**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表使用繁体“義大利”并对应意大利国家，地域译名有独立依据；本别名转为简体“义大利”是通常字形转换。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

需人确认：确认所指的是客户所在地国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：该地区译名的简繁转换是AI语言推断，不是意/义字随意纠错。

原CSV同词候选：customer.country=Italy；invoice.billing_country=Italy。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:77>)：第77行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[15]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:760>)：第760行；kind=standard; candidate_id=v-ec3f5c892a21c72c35e1。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：意大利国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [教育部重编国语辞典：世界各国国名表及附图](<https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4>)：欧洲地区：法兰西、德意志、义大利各条目。国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。 访问：浏览工具已返回可读正文。

## alias:a-a653ead69db804b0

**意国 → customer.country = Italy**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 customer.country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。日本国立国会图书馆参考库的中文国名答复明确列出该简称，不能仅因它少见就判断为错。材料未证明本项目用户高频使用，短词也需限定国家语境；作为保守候选比直接唯一匹配合适。这里的 customer.country 表示客户所在地国家；中文国家名翻译正确不代表可替换成 invoice.billing_country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：简称来源属于图书馆参考答复；本项目真实用法和频率未提供。

建议：先确认问题要筛选客户所在地国家，再在 customer.country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

需人确认：确认目标用户地域/语体是否需要此简称；没有真实用例也不自动扩大映射范围。

原CSV同词候选：customer.country=Italy；invoice.billing_country=Italy。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:78>)：第78行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:131>)：第131行；tables[customer].columns[country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 customer.country; $.text_values["customer.country"].values[15]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:760>)：第760行；kind=standard; candidate_id=v-ec3f5c892a21c72c35e1。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:42>)：第42行；### customer。字典中的字段范围说明
- [外交部：意大利国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [日本国立国会图书馆参考协同数据库：主要国家汉字表记](<https://crd.ndl.go.jp/reference/entry/reference/show?asc=desc&fi=5_%E7%A4%BE%E4%BC%9A%E4%BA%BA+8_22+3_%E6%96%87%E7%8C%AE%E7%B4%B9%E4%BB%8B&id=1000203470&lsmp=1&mcmd=25&page=ref_view&rnk=1&st=ref_cnt_all>)：回答第85–87行：中国语表记。图书馆参考答复列出意大利中文国名的该简称；未证明中国大陆当代查询中的频率。 访问：浏览工具已返回可读正文。

## alias:a-97f75d30b3bcab32

**意大利 → invoice.billing_country = Italy**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。“意大利”由外交部国家概况的国名与页面名称支持，对应真实标准值 Italy。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：外交部意大利对象及中文国名支持国家指称；Italy英文名对应是通常语言知识，并由既有真实数据库值核验。

原CSV同词候选：customer.country=Italy；invoice.billing_country=Italy。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:79>)：第79行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[15]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1311>)：第1311行；kind=standard; candidate_id=v-f00a4dabb94dd7295e40。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：意大利国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。

## alias:a-477276f0186e7f07

**义大利 → invoice.billing_country = Italy**

参考状态：AI建议通过；处置建议：建议直接使用；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。教育部国名表使用繁体“義大利”并对应意大利国家，地域译名有独立依据；本别名转为简体“义大利”是通常字形转换。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：未发现实质性映射错误；仍遵守字段限定与人审启用要求。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

需人确认：确认所指的是发票账单地址国家及目标国家名称；人审后再决定是否启用，不填人审签名。

AI推断与局限：该地区译名的简繁转换是AI语言推断，不是意/义字随意纠错。

原CSV同词候选：customer.country=Italy；invoice.billing_country=Italy。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:80>)：第80行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[15]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1311>)：第1311行；kind=standard; candidate_id=v-f00a4dabb94dd7295e40。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：意大利国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [教育部重编国语辞典：世界各国国名表及附图](<https://dict.revised.moe.edu.tw/appendix.jsp?ID=29&page=2&ver=4>)：欧洲地区：法兰西、德意志、义大利各条目。国名表支持法兰西及德意志对应现代国家、义大利的地区译名；简繁转换和英文短名等价为AI语言推断。 访问：浏览工具已返回可读正文。

## alias:a-14625e480dd8676e

**意国 → invoice.billing_country = Italy**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 invoice.billing_country 字段与标准值 Italy 均存在，完整DISTINCT与既有标准值索引一致。日本国立国会图书馆参考库的中文国名答复明确列出该简称，不能仅因它少见就判断为错。材料未证明本项目用户高频使用，短词也需限定国家语境；作为保守候选比直接唯一匹配合适。这里的 invoice.billing_country 表示发票账单地址国家；中文国家名翻译正确不代表可替换成 customer.country，也不能由国家字段推断个人国籍。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：简称来源属于图书馆参考答复；本项目真实用法和频率未提供。

建议：先确认问题要筛选发票账单地址国家，再在 invoice.billing_country 中使用精确标准值 Italy；保留另一国家字段的独立口径。

需人确认：确认目标用户地域/语体是否需要此简称；没有真实用例也不自动扩大映射范围。

原CSV同词候选：customer.country=Italy；invoice.billing_country=Italy。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:81>)：第81行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:418>)：第418行；tables[invoice].columns[billing_country]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 invoice.billing_country; $.text_values["invoice.billing_country"].values[15]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1311>)：第1311行；kind=standard; candidate_id=v-f00a4dabb94dd7295e40。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:99>)：第99行；### invoice。字典中的字段范围说明
- [外交部：意大利国家概况](<https://www.mfa.gov.cn/web/gjhdq_676201/gj_676203/oz_678770/1206_679882/1206x0_679884/>)：页面标题、国名段及英/本国语国名。官方页面支持该国家中文简称或正式国名与英文对象的对应；本审核只使用名称，不使用动态政经内容。 访问：浏览工具已返回可读正文。
- [日本国立国会图书馆参考协同数据库：主要国家汉字表记](<https://crd.ndl.go.jp/reference/entry/reference/show?asc=desc&fi=5_%E7%A4%BE%E4%BC%9A%E4%BA%BA+8_22+3_%E6%96%87%E7%8C%AE%E7%B4%B9%E4%BB%8B&id=1000203470&lsmp=1&mcmd=25&page=ref_view&rnk=1&st=ref_cnt_all>)：回答第85–87行：中国语表记。图书馆参考答复列出意大利中文国名的该简称；未证明中国大陆当代查询中的频率。 访问：浏览工具已返回可读正文。

## alias:a-d2-plan-rock-and-roll

**摇滚 → genre.name = Rock And Roll**

参考状态：AI建议有条件通过；处置建议：仅作为条件候选；实际状态：不适用（别名配置审核，未生成预测）；证据完整：是。

实查 genre.name 字段与标准值 Rock And Roll 均存在，完整DISTINCT与既有标准值索引一致。独立英汉词条将Rock和Rock And Roll的音乐义都映射到摇滚用语；本行“摇滚”可表达 Rock And Roll，同时另一真实标准对象也成立。待审CSV内相同genre别名已对应两个值，数据库两值并存；因此这是真实同字段多义，不应只取第一条、最高分或强制唯一标准值。 仅在目标字段已明确的语境下适用；AI预审不是启用操作。

问题：同字段同中文词形存在Rock/Rock And Roll两候选。

建议：保留 Rock And Roll 为条件候选；用户明确数据库分类或补充判别语后才选一个。泛称摇滚范围应澄清是否包括两类。

需人确认：确认两分类的查询边界与候选澄清流程；不得把两个译名任意重命名以掩盖歧义。

AI推断与局限：短词省略“乐”是AI中文语言判断；仍保留两分类候选。

原CSV同词候选：genre.name=Rock；genre.name=Rock And Roll。跨国家字段重复登记不会授权字段互换。

证据：

- [data/aliases/aliases.csv](<E:/中国电子杯-赛题八/system/data/aliases/aliases.csv:82>)：第82行；待审行；LLM草稿仅作对象/来源登记，不作译名证明。原待审别名、字段、标准值、pending配置
- [data/catalog/chinook.yaml](<E:/中国电子杯-赛题八/system/data/catalog/chinook.yaml:354>)：第354行；tables[genre].columns[name]。实际目录中的字段与业务含义
- [eval/artifacts/d2-ai-preaudit/database-materials.json](<E:/中国电子杯-赛题八/system/eval/artifacts/d2-ai-preaudit/database-materials.json>)：$.schema中的 genre.name; $.text_values["genre.name"].values[19]; 原始queries内该列SELECT DISTINCT。qa_reader只读实查确认字段、真实标准值、完整DISTINCT未截断
- [data/indexes/values/records.jsonl](<E:/中国电子杯-赛题八/system/data/indexes/values/records.jsonl:1178>)：第1178行；kind=standard; candidate_id=v-10facd793602b59518e7。既有标准值索引旁证；未重建索引
- [data/docs/raw/d2/chinook-dictionary-zh.md](<E:/中国电子杯-赛题八/system/data/docs/raw/d2/chinook-dictionary-zh.md:88>)：第88行；### genre。字典中的字段范围说明
- [剑桥英汉辞典：rock](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock>)：rock noun (MUSIC)。词典支持 Rock 的中文音乐义。 访问：搜索工具返回可读词条正文；本轮未单独open完整页。
- [剑桥英汉辞典：rock-and-roll](<https://dictionary.cambridge.org/dictionary/english-chinese-simplified/rock-and-roll>)：主词条音乐义。词典的中文译法与 Rock 音乐义重叠，不能单靠中文词形分开数据库两个分类。 访问：搜索工具返回可读词条正文；Rock And Roll完整页open为403。
