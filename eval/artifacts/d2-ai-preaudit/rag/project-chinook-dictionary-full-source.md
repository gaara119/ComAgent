# Chinook 数据字典 中文

项目自编字段说明，来源为本项目实际 PostgreSQL 目录。用于理解数据字段，不包含评测问题、标准答案或客户明细。

## 通用约定

数据库为 Chinook 1.4.5，表名和列名采用 snake_case。invoice.invoice_date 为发票日期；已核验快照覆盖2021年至2025年，精确范围见 A/B 数据交接。金额使用数据库金额单位，不推断币种或成功付款状态。

## 地区字段含义

customer.country 表示客户所在地国家。invoice.billing_country 表示发票账单地址国家。两列在当前快照中相等，不能据此将两种业务含义混为同一口径。

## 人名字段含义

customer.first_name 与 employee.first_name 表示名；last_name 表示姓。姓名应显式拼接名与姓。含糊的“名字”不能悄悄改变已确认的题目语义。

## 表与字段

### album

专辑，每张专辑关联一位艺术家

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| album_id | integer | 否 | 专辑编号 |
| title | character varying(160) | 否 | 专辑标题 |
| artist_id | integer | 否 | 艺术家编号 |

主键：album_id。

### artist

艺术家、乐队及组合的英文名称

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| artist_id | integer | 否 | 艺术家编号 |
| name | character varying(120) | 是 | 艺术家或乐队名称 |

主键：artist_id。

### customer

客户及其所在地、联系方式、销售支持员工

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| customer_id | integer | 否 | 客户编号 |
| first_name | character varying(40) | 否 | 名字 |
| last_name | character varying(20) | 否 | 姓氏 |
| company | character varying(80) | 是 | 客户公司名称，可为空 |
| address | character varying(70) | 是 | 所在地街道地址 |
| city | character varying(40) | 是 | 所在地城市 |
| state | character varying(40) | 是 | 所在地州或省，可为空 |
| country | character varying(40) | 是 | 所在地国家，使用原始英文标准值，例如 USA、Brazil |
| postal_code | character varying(10) | 是 | 所在地邮政编码，可为空 |
| phone | character varying(24) | 是 | 联系电话，可为空 |
| fax | character varying(24) | 是 | 传真号码，可为空 |
| email | character varying(60) | 否 | 电子邮箱 |
| support_rep_id | integer | 是 | 负责该客户的销售支持员工编号，关联 employee.employee_id |

主键：customer_id。

### employee

员工及其职位、入职日期、上下级关系

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| employee_id | integer | 否 | 员工编号 |
| last_name | character varying(20) | 否 | 姓氏 |
| first_name | character varying(20) | 否 | 名字 |
| title | character varying(30) | 是 | 员工职位，原始英文值 |
| reports_to | integer | 是 | 直接上级员工编号，关联 employee.employee_id；最高层员工为空 |
| birth_date | timestamp without time zone | 是 | 员工出生日期 |
| hire_date | timestamp without time zone | 是 | 员工入职日期 |
| address | character varying(70) | 是 | 所在地街道地址 |
| city | character varying(40) | 是 | 所在地城市 |
| state | character varying(40) | 是 | 所在地州或省，可为空 |
| country | character varying(40) | 是 | 所在地国家，使用原始英文标准值，例如 USA、Brazil |
| postal_code | character varying(10) | 是 | 所在地邮政编码，可为空 |
| phone | character varying(24) | 是 | 联系电话，可为空 |
| fax | character varying(24) | 是 | 传真号码，可为空 |
| email | character varying(60) | 是 | 电子邮箱 |

主键：employee_id。

### genre

曲目音乐流派

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| genre_id | integer | 否 | 流派编号 |
| name | character varying(120) | 是 | 流派英文名称 |

主键：genre_id。

### invoice

销售发票，含客户、开票时间、账单地址及发票总额

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| invoice_id | integer | 否 | 发票编号 |
| customer_id | integer | 否 | 客户编号 |
| invoice_date | timestamp without time zone | 否 | 开票时间，不是客户创建时间 |
| billing_address | character varying(70) | 是 | 发票账单街道地址 |
| billing_city | character varying(40) | 是 | 发票账单城市 |
| billing_state | character varying(40) | 是 | 发票账单州或省，可为空 |
| billing_country | character varying(40) | 是 | 发票账单地址国家，与 customer.country 是不同字段，不可直接互换 |
| billing_postal_code | character varying(10) | 是 | 发票账单邮政编码，可为空 |
| total | numeric(10,2) | 否 | 发票总额；按发票统计收入使用该列，避免明细 JOIN 导致重复求和 |

主键：invoice_id。

### invoice_line

发票销售明细，含实际成交单价及销售数量

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| invoice_line_id | integer | 否 | 发票明细编号 |
| invoice_id | integer | 否 | 发票编号 |
| track_id | integer | 否 | 曲目编号 |
| unit_price | numeric(10,2) | 否 | 本发票明细实际成交单价；销售额 = 单价 × quantity |
| quantity | integer | 否 | 本发票明细购买的曲目数量 |

主键：invoice_line_id。

### media_type

曲目媒体格式

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| media_type_id | integer | 否 | 媒体格式编号 |
| name | character varying(120) | 是 | 媒体格式名称 |

主键：media_type_id。

### playlist

播放列表

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| playlist_id | integer | 否 | 播放列表编号 |
| name | character varying(120) | 是 | 播放列表名称 |

主键：playlist_id。

### playlist_track

播放列表与曲目的多对多关系

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| playlist_id | integer | 否 | 播放列表编号 |
| track_id | integer | 否 | 曲目编号 |

主键：playlist_id、track_id。

### track

曲目、专辑、流派、媒体格式、时长和目录单价

| 字段 | 数据类型 | 可为空 | 中文说明 |
|---|---|---|---|
| track_id | integer | 否 | 曲目编号 |
| name | character varying(200) | 否 | 曲目名称 |
| album_id | integer | 是 | 专辑编号 |
| media_type_id | integer | 否 | 媒体格式编号 |
| genre_id | integer | 是 | 流派编号 |
| composer | character varying(220) | 是 | 曲目作曲者，可为空 |
| milliseconds | integer | 否 | 曲目时长，单位毫秒；秒 = 毫秒 / 1000.0 |
| bytes | integer | 是 | 媒体文件大小，单位字节，可为空 |
| unit_price | numeric(10,2) | 否 | 曲目目录单价，不是整张发票总额；币种未在本数据源声明 |

主键：track_id。

## 信息边界

本字典没有客户音乐偏好、银行卡号、实时库存或支付完成状态。字段定义不能替代具体客户事实，也不能提供数据库中不存在的外部指标。

## SQL 注释示例

```sql
-- # 这一行是代码块里的注释，不是正文标题
SELECT country FROM public.customer LIMIT 3;
```
