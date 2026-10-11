# D2 别名表人工审核提案

状态：全部 pending，尚未进入运行值索引。

建议通过 78 项，建议拒绝 3 项；审核必须对应当前 CSV SHA256：`1675b387e59acea4928293ed9b6d9447ca4445ac8bc38feaf6927f9835796a7b`。

精确匹配限定真实表字段；同一词对应多个值时保留候选并澄清。尤其“摇滚/摇滚乐”同时映射 Rock 与 Rock And Roll，不替用户选一个。

| 字段 | 真实标准值 | 建议通过的别名 | 建议拒绝 |
|---|---|---|---|
| artist.name | Iron Maiden | 铁娘子、Iron Maiden乐队 | 铁处女 |
| artist.name | Led Zeppelin | 齐柏林飞船、齐柏林飞艇、Led Zeppelin乐队 |  |
| artist.name | Metallica | 金属乐队、Metallica乐队 | 金属 |
| artist.name | U2 | U2乐队、U2乐团 |  |
| customer.country | Australia | 澳大利亚、澳洲、澳大利亚联邦 |  |
| customer.country | Brazil | 巴西、巴西联邦共和国 |  |
| customer.country | Canada | 加拿大 |  |
| customer.country | France | 法国、法兰西、法兰西共和国 |  |
| customer.country | Germany | 德国、德意志、德意志联邦共和国 |  |
| customer.country | India | 印度、印度共和国 |  |
| customer.country | USA | 美国、老美、美利坚合众国 |  |
| customer.country | United Kingdom | 英国、联合王国、大不列颠及北爱尔兰联合王国 |  |
| genre.name | Classical | 古典、古典音乐 |  |
| genre.name | Jazz | 爵士、爵士乐 |  |
| genre.name | Metal | 金属、金属乐 |  |
| genre.name | Pop | 流行、流行音乐 |  |
| genre.name | Rock | 摇滚、摇滚乐 |  |
| genre.name | Rock And Roll | 摇滚乐、摇滚 | 节奏摇滚 |
| invoice.billing_country | Australia | 澳大利亚、澳洲、澳大利亚联邦 |  |
| invoice.billing_country | Brazil | 巴西、巴西联邦共和国 |  |
| invoice.billing_country | Canada | 加拿大 |  |
| invoice.billing_country | France | 法国、法兰西、法兰西共和国 |  |
| invoice.billing_country | Germany | 德国、德意志、德意志联邦共和国 |  |
| invoice.billing_country | India | 印度、印度共和国 |  |
| invoice.billing_country | USA | 美国、老美、美利坚合众国 |  |
| invoice.billing_country | United Kingdom | 英国、联合王国、大不列颠及北爱尔兰联合王国 |  |
| media_type.name | AAC audio file | AAC音频文件、AAC音频 |  |
| media_type.name | MPEG audio file | MPEG音频文件、MPEG音频 |  |
| media_type.name | Protected AAC audio file | 受保护AAC音频文件、受保护AAC音频 |  |
| media_type.name | Protected MPEG-4 video file | 受保护MPEG-4视频文件、受保护MPEG-4视频 |  |
| media_type.name | Purchased AAC audio file | 已购买AAC音频文件、购买AAC音频文件、已购买AAC音频 |  |
| customer.country | Italy | 意大利、义大利、意国 |  |
| invoice.billing_country | Italy | 意大利、义大利、意国 |  |

拒绝理由：泛称“金属”不能唯一代表 Metallica 乐队；“节奏摇滚”不足以唯一说明 Rock And Roll；“铁处女”不采用为本项目的默认中文乐队名。

别名来自已实跑 DeepSeek 初稿（Italy 为单独模型补充）；“摇滚”多候选对应关系来自总计划的明确例子。上述建议不代表人工已批准。

- [aliases.csv](../data/aliases/aliases.csv)
- [具体行 ID 与审核哈希](../eval/artifacts/d2/aliases-review-selection.json)
