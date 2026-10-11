# D2 SQL 与鲁棒题 gold 人工审核表

50 条 gold 已只读实跑；30 变体复用同源 gold。业务含义仍待人工审核。保留题不调用模型，D5 冻结后再测。

## sql-01 · dev · count

同源：chinook-question-01；审核：needs_human_review。

客户表共有多少位客户？

```sql
SELECT COUNT(*) AS customer_count FROM customer;
```

```json
[
  {
    "customer_count": 59
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-02 · dev · count

同源：brazil_customer；审核：needs_human_review。

来自巴西的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-03 · holdout · count

同源：chinook-question-03；审核：needs_human_review。

曲目表中时长超过 5 分钟的曲目有多少首？

```sql
SELECT COUNT(*) AS track_count FROM track WHERE milliseconds > 300000;
```

```json
[
  {
    "track_count": 1069
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-04 · dev · filter

同源：brazil_customer；审核：needs_human_review。

列出来自巴西的客户编号、名字、姓氏和城市，按客户编号升序。

```sql
SELECT customer_id, first_name, last_name, city FROM customer WHERE country = 'Brazil' ORDER BY customer_id;
```

```json
[
  {
    "customer_id": 1,
    "first_name": "Luís",
    "last_name": "Gonçalves",
    "city": "São José dos Campos"
  },
  {
    "customer_id": 10,
    "first_name": "Eduardo",
    "last_name": "Martins",
    "city": "São Paulo"
  },
  {
    "customer_id": 11,
    "first_name": "Alexandre",
    "last_name": "Rocha",
    "city": "São Paulo"
  },
  {
    "customer_id": 12,
    "first_name": "Roberto",
    "last_name": "Almeida",
    "city": "Rio de Janeiro"
  },
  {
    "customer_id": 13,
    "first_name": "Fernanda",
    "last_name": "Ramos",
    "city": "Brasília"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-05 · dev · filter

同源：chinook-question-05；审核：needs_human_review。

列出来自美国的客户编号、城市和州，按客户编号升序。

```sql
SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;
```

```json
[
  {
    "customer_id": 16,
    "city": "Mountain View",
    "state": "CA"
  },
  {
    "customer_id": 17,
    "city": "Redmond",
    "state": "WA"
  },
  {
    "customer_id": 18,
    "city": "New York",
    "state": "NY"
  },
  {
    "customer_id": 19,
    "city": "Cupertino",
    "state": "CA"
  },
  {
    "customer_id": 20,
    "city": "Mountain View",
    "state": "CA"
  },
  {
    "customer_id": 21,
    "city": "Reno",
    "state": "NV"
  },
  {
    "customer_id": 22,
    "city": "Orlando",
    "state": "FL"
  },
  {
    "customer_id": 23,
    "city": "Boston",
    "state": "MA"
  },
  {
    "customer_id": 24,
    "city": "Chicago",
    "state": "IL"
  },
  {
    "customer_id": 25,
    "city": "Madison",
    "state": "WI"
  },
  {
    "customer_id": 26,
    "city": "Fort Worth",
    "state": "TX"
  },
  {
    "customer_id": 27,
    "city": "Tucson",
    "state": "AZ"
  },
  {
    "customer_id": 28,
    "city": "Salt Lake City",
    "state": "UT"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-06 · dev · filter

同源：chinook-question-06；审核：needs_human_review。

列出单价高于 0.99 的前 10 首曲目的编号、名称和单价，按曲目编号升序。

```sql
SELECT track_id, name, unit_price FROM track WHERE unit_price > 0.99 ORDER BY track_id LIMIT 10;
```

```json
[
  {
    "track_id": 2819,
    "name": "Battlestar Galactica: The Story So Far",
    "unit_price": "1.99"
  },
  {
    "track_id": 2820,
    "name": "Occupation / Precipice",
    "unit_price": "1.99"
  },
  {
    "track_id": 2821,
    "name": "Exodus, Pt. 1",
    "unit_price": "1.99"
  },
  {
    "track_id": 2822,
    "name": "Exodus, Pt. 2",
    "unit_price": "1.99"
  },
  {
    "track_id": 2823,
    "name": "Collaborators",
    "unit_price": "1.99"
  },
  {
    "track_id": 2824,
    "name": "Torn",
    "unit_price": "1.99"
  },
  {
    "track_id": 2825,
    "name": "A Measure of Salvation",
    "unit_price": "1.99"
  },
  {
    "track_id": 2826,
    "name": "Hero",
    "unit_price": "1.99"
  },
  {
    "track_id": 2827,
    "name": "Unfinished Business",
    "unit_price": "1.99"
  },
  {
    "track_id": 2828,
    "name": "The Passage",
    "unit_price": "1.99"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-07 · dev · filter

同源：chinook-question-07；审核：needs_human_review。

列出职位为 Sales Support Agent 的员工编号、名字和姓氏，按员工编号升序。

```sql
SELECT employee_id, first_name, last_name FROM employee WHERE title = 'Sales Support Agent' ORDER BY employee_id;
```

```json
[
  {
    "employee_id": 3,
    "first_name": "Jane",
    "last_name": "Peacock"
  },
  {
    "employee_id": 4,
    "first_name": "Margaret",
    "last_name": "Park"
  },
  {
    "employee_id": 5,
    "first_name": "Steve",
    "last_name": "Johnson"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-08 · holdout · filter

同源：chinook-question-08；审核：needs_human_review。

列出总额不少于 10 的前 10 张发票的编号、日期和总额，按发票编号升序。

```sql
SELECT invoice_id, invoice_date, total FROM invoice WHERE total >= 10 ORDER BY invoice_id LIMIT 10;
```

```json
[
  {
    "invoice_id": 5,
    "invoice_date": "2021-01-11T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 12,
    "invoice_date": "2021-02-11T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 19,
    "invoice_date": "2021-03-14T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 26,
    "invoice_date": "2021-04-14T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 33,
    "invoice_date": "2021-05-15T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 40,
    "invoice_date": "2021-06-15T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 47,
    "invoice_date": "2021-07-16T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 54,
    "invoice_date": "2021-08-16T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 61,
    "invoice_date": "2021-09-16T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 68,
    "invoice_date": "2021-10-17T00:00:00",
    "total": "13.86"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-09 · dev · aggregate

同源：invoice_global_totals；审核：needs_human_review。

全部发票的总金额是多少？

```sql
SELECT SUM(total) AS total_amount FROM invoice;
```

```json
[
  {
    "total_amount": "2328.60"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-10 · dev · aggregate

同源：chinook-question-10；审核：needs_human_review。

全部曲目的平均时长是多少毫秒？

```sql
SELECT AVG(milliseconds) AS average_milliseconds FROM track;
```

```json
[
  {
    "average_milliseconds": "393599.212103910933"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-11 · dev · aggregate

同源：invoice_global_totals；审核：needs_human_review。

全部发票的平均总额是多少？请保留两位小数。

```sql
SELECT ROUND(AVG(total), 2) AS average_total FROM invoice;
```

```json
[
  {
    "average_total": "5.65"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-12 · holdout · aggregate

同源：chinook-question-12；审核：needs_human_review。

客户所在国家共有多少种？

```sql
SELECT COUNT(DISTINCT country) AS country_count FROM customer;
```

```json
[
  {
    "country_count": 24
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-13 · dev · group

同源：chinook-question-13；审核：needs_human_review。

按客户所在国家统计客户数，先按客户数降序，并列时按国家名称升序。

```sql
SELECT country, COUNT(*) AS customer_count FROM customer GROUP BY country ORDER BY customer_count DESC, country ASC;
```

```json
[
  {
    "country": "USA",
    "customer_count": 13
  },
  {
    "country": "Canada",
    "customer_count": 8
  },
  {
    "country": "Brazil",
    "customer_count": 5
  },
  {
    "country": "France",
    "customer_count": 5
  },
  {
    "country": "Germany",
    "customer_count": 4
  },
  {
    "country": "United Kingdom",
    "customer_count": 3
  },
  {
    "country": "Czech Republic",
    "customer_count": 2
  },
  {
    "country": "India",
    "customer_count": 2
  },
  {
    "country": "Portugal",
    "customer_count": 2
  },
  {
    "country": "Argentina",
    "customer_count": 1
  },
  {
    "country": "Australia",
    "customer_count": 1
  },
  {
    "country": "Austria",
    "customer_count": 1
  },
  {
    "country": "Belgium",
    "customer_count": 1
  },
  {
    "country": "Chile",
    "customer_count": 1
  },
  {
    "country": "Denmark",
    "customer_count": 1
  },
  {
    "country": "Finland",
    "customer_count": 1
  },
  {
    "country": "Hungary",
    "customer_count": 1
  },
  {
    "country": "Ireland",
    "customer_count": 1
  },
  {
    "country": "Italy",
    "customer_count": 1
  },
  {
    "country": "Netherlands",
    "customer_count": 1
  },
  {
    "country": "Norway",
    "customer_count": 1
  },
  {
    "country": "Poland",
    "customer_count": 1
  },
  {
    "country": "Spain",
    "customer_count": 1
  },
  {
    "country": "Sweden",
    "customer_count": 1
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-14 · dev · group

同源：chinook-question-14；审核：needs_human_review。

按流派编号统计曲目数，先按曲目数降序，并列时按流派编号升序。

```sql
SELECT genre_id, COUNT(*) AS track_count FROM track GROUP BY genre_id ORDER BY track_count DESC, genre_id ASC;
```

```json
[
  {
    "genre_id": 1,
    "track_count": 1297
  },
  {
    "genre_id": 7,
    "track_count": 579
  },
  {
    "genre_id": 3,
    "track_count": 374
  },
  {
    "genre_id": 4,
    "track_count": 332
  },
  {
    "genre_id": 2,
    "track_count": 130
  },
  {
    "genre_id": 19,
    "track_count": 93
  },
  {
    "genre_id": 6,
    "track_count": 81
  },
  {
    "genre_id": 24,
    "track_count": 74
  },
  {
    "genre_id": 21,
    "track_count": 64
  },
  {
    "genre_id": 14,
    "track_count": 61
  },
  {
    "genre_id": 8,
    "track_count": 58
  },
  {
    "genre_id": 9,
    "track_count": 48
  },
  {
    "genre_id": 10,
    "track_count": 43
  },
  {
    "genre_id": 23,
    "track_count": 40
  },
  {
    "genre_id": 17,
    "track_count": 35
  },
  {
    "genre_id": 15,
    "track_count": 30
  },
  {
    "genre_id": 13,
    "track_count": 28
  },
  {
    "genre_id": 16,
    "track_count": 28
  },
  {
    "genre_id": 20,
    "track_count": 26
  },
  {
    "genre_id": 12,
    "track_count": 24
  },
  {
    "genre_id": 22,
    "track_count": 17
  },
  {
    "genre_id": 11,
    "track_count": 15
  },
  {
    "genre_id": 18,
    "track_count": 13
  },
  {
    "genre_id": 5,
    "track_count": 12
  },
  {
    "genre_id": 25,
    "track_count": 1
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-15 · dev · group

同源：chinook-question-15；审核：needs_human_review。

按发票的账单国家统计销售总额，先按销售总额降序，并列时按国家名称升序。

```sql
SELECT billing_country, SUM(total) AS sales_total FROM invoice GROUP BY billing_country ORDER BY sales_total DESC, billing_country ASC;
```

```json
[
  {
    "billing_country": "USA",
    "sales_total": "523.06"
  },
  {
    "billing_country": "Canada",
    "sales_total": "303.96"
  },
  {
    "billing_country": "France",
    "sales_total": "195.10"
  },
  {
    "billing_country": "Brazil",
    "sales_total": "190.10"
  },
  {
    "billing_country": "Germany",
    "sales_total": "156.48"
  },
  {
    "billing_country": "United Kingdom",
    "sales_total": "112.86"
  },
  {
    "billing_country": "Czech Republic",
    "sales_total": "90.24"
  },
  {
    "billing_country": "Portugal",
    "sales_total": "77.24"
  },
  {
    "billing_country": "India",
    "sales_total": "75.26"
  },
  {
    "billing_country": "Chile",
    "sales_total": "46.62"
  },
  {
    "billing_country": "Hungary",
    "sales_total": "45.62"
  },
  {
    "billing_country": "Ireland",
    "sales_total": "45.62"
  },
  {
    "billing_country": "Austria",
    "sales_total": "42.62"
  },
  {
    "billing_country": "Finland",
    "sales_total": "41.62"
  },
  {
    "billing_country": "Netherlands",
    "sales_total": "40.62"
  },
  {
    "billing_country": "Norway",
    "sales_total": "39.62"
  },
  {
    "billing_country": "Sweden",
    "sales_total": "38.62"
  },
  {
    "billing_country": "Argentina",
    "sales_total": "37.62"
  },
  {
    "billing_country": "Australia",
    "sales_total": "37.62"
  },
  {
    "billing_country": "Belgium",
    "sales_total": "37.62"
  },
  {
    "billing_country": "Denmark",
    "sales_total": "37.62"
  },
  {
    "billing_country": "Italy",
    "sales_total": "37.62"
  },
  {
    "billing_country": "Poland",
    "sales_total": "37.62"
  },
  {
    "billing_country": "Spain",
    "sales_total": "37.62"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-16 · holdout · group

同源：chinook-question-16；审核：needs_human_review。

按员工职位统计人数，按职位名称升序。

```sql
SELECT title, COUNT(*) AS employee_count FROM employee GROUP BY title ORDER BY title ASC;
```

```json
[
  {
    "title": "General Manager",
    "employee_count": 1
  },
  {
    "title": "IT Manager",
    "employee_count": 1
  },
  {
    "title": "IT Staff",
    "employee_count": 2
  },
  {
    "title": "Sales Manager",
    "employee_count": 1
  },
  {
    "title": "Sales Support Agent",
    "employee_count": 3
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-17 · dev · top

同源：chinook-question-17；审核：needs_human_review。

找出时长最长的 5 首曲目，返回编号、名称和毫秒时长；按时长降序，并列按编号升序。

```sql
SELECT track_id, name, milliseconds FROM track ORDER BY milliseconds DESC, track_id ASC LIMIT 5;
```

```json
[
  {
    "track_id": 2820,
    "name": "Occupation / Precipice",
    "milliseconds": 5286953
  },
  {
    "track_id": 3224,
    "name": "Through a Looking Glass",
    "milliseconds": 5088838
  },
  {
    "track_id": 3244,
    "name": "Greetings from Earth, Pt. 1",
    "milliseconds": 2960293
  },
  {
    "track_id": 3242,
    "name": "The Man With Nine Lives",
    "milliseconds": 2956998
  },
  {
    "track_id": 3227,
    "name": "Battlestar Galactica, Pt. 2",
    "milliseconds": 2956081
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-18 · dev · top

同源：chinook-question-18；审核：needs_human_review。

找出总额最高的 5 张发票，返回编号和总额；按总额降序，并列按编号升序。

```sql
SELECT invoice_id, total FROM invoice ORDER BY total DESC, invoice_id ASC LIMIT 5;
```

```json
[
  {
    "invoice_id": 404,
    "total": "25.86"
  },
  {
    "invoice_id": 299,
    "total": "23.86"
  },
  {
    "invoice_id": 96,
    "total": "21.86"
  },
  {
    "invoice_id": 194,
    "total": "21.86"
  },
  {
    "invoice_id": 89,
    "total": "18.86"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-19 · dev · top

同源：chinook-question-19；审核：needs_human_review。

按姓氏降序取前 5 位客户，返回编号、名字和姓氏；姓氏相同时按客户编号升序。

```sql
SELECT customer_id, first_name, last_name FROM customer ORDER BY last_name DESC, customer_id ASC LIMIT 5;
```

```json
[
  {
    "customer_id": 37,
    "first_name": "Fynn",
    "last_name": "Zimmermann"
  },
  {
    "customer_id": 49,
    "first_name": "Stanisław",
    "last_name": "Wójcik"
  },
  {
    "customer_id": 5,
    "first_name": "František",
    "last_name": "Wichterlová"
  },
  {
    "customer_id": 48,
    "first_name": "Johannes",
    "last_name": "Van der Berg"
  },
  {
    "customer_id": 3,
    "first_name": "François",
    "last_name": "Tremblay"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-20 · holdout · top

同源：chinook-question-20；审核：needs_human_review。

按名称升序取前 5 位艺术家，返回编号和名称；名称相同按艺术家编号升序。

```sql
SELECT artist_id, name FROM artist ORDER BY name ASC, artist_id ASC LIMIT 5;
```

```json
[
  {
    "artist_id": 43,
    "name": "A Cor Do Som"
  },
  {
    "artist_id": 1,
    "name": "AC/DC"
  },
  {
    "artist_id": 230,
    "name": "Aaron Copland & London Symphony Orchestra"
  },
  {
    "artist_id": 202,
    "name": "Aaron Goldberg"
  },
  {
    "artist_id": 214,
    "name": "Academy of St. Martin in the Fields & Sir Neville Marriner"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-21 · dev · date

同源：chinook-question-21；审核：needs_human_review。

列出 2021 年的前 10 张发票，返回编号、日期和总额，按发票编号升序。

```sql
SELECT invoice_id, invoice_date, total FROM invoice WHERE invoice_date >= '2021-01-01' AND invoice_date < '2022-01-01' ORDER BY invoice_id LIMIT 10;
```

```json
[
  {
    "invoice_id": 1,
    "invoice_date": "2021-01-01T00:00:00",
    "total": "1.98"
  },
  {
    "invoice_id": 2,
    "invoice_date": "2021-01-02T00:00:00",
    "total": "3.96"
  },
  {
    "invoice_id": 3,
    "invoice_date": "2021-01-03T00:00:00",
    "total": "5.94"
  },
  {
    "invoice_id": 4,
    "invoice_date": "2021-01-06T00:00:00",
    "total": "8.91"
  },
  {
    "invoice_id": 5,
    "invoice_date": "2021-01-11T00:00:00",
    "total": "13.86"
  },
  {
    "invoice_id": 6,
    "invoice_date": "2021-01-19T00:00:00",
    "total": "0.99"
  },
  {
    "invoice_id": 7,
    "invoice_date": "2021-02-01T00:00:00",
    "total": "1.98"
  },
  {
    "invoice_id": 8,
    "invoice_date": "2021-02-01T00:00:00",
    "total": "1.98"
  },
  {
    "invoice_id": 9,
    "invoice_date": "2021-02-02T00:00:00",
    "total": "3.96"
  },
  {
    "invoice_id": 10,
    "invoice_date": "2021-02-03T00:00:00",
    "total": "5.94"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-22 · dev · date

同源：chinook-question-22；审核：needs_human_review。

列出 2004 年 1 月 1 日之前入职的员工编号、名字（仅 first_name，不包含姓氏 last_name）和入职日期，按员工编号升序。

```sql
SELECT employee_id, first_name, hire_date FROM employee WHERE hire_date < '2004-01-01' ORDER BY employee_id;
```

```json
[
  {
    "employee_id": 1,
    "first_name": "Andrew",
    "hire_date": "2002-08-14T00:00:00"
  },
  {
    "employee_id": 2,
    "first_name": "Nancy",
    "hire_date": "2002-05-01T00:00:00"
  },
  {
    "employee_id": 3,
    "first_name": "Jane",
    "hire_date": "2002-04-01T00:00:00"
  },
  {
    "employee_id": 4,
    "first_name": "Margaret",
    "hire_date": "2003-05-03T00:00:00"
  },
  {
    "employee_id": 5,
    "first_name": "Steve",
    "hire_date": "2003-10-17T00:00:00"
  },
  {
    "employee_id": 6,
    "first_name": "Michael",
    "hire_date": "2003-10-17T00:00:00"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-23 · holdout · date

同源：chinook-question-23；审核：needs_human_review。

2025 年一共开了多少张发票？

```sql
SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2025-01-01' AND invoice_date < '2026-01-01';
```

```json
[
  {
    "invoice_count": 80
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-24 · dev · like

同源：chinook-question-24；审核：needs_human_review。

列出邮箱以 @gmail.com 结尾的客户编号、名字（仅 first_name，不包含姓氏 last_name）和邮箱，按客户编号升序。

```sql
SELECT customer_id, first_name, email FROM customer WHERE email LIKE '%@gmail.com' ORDER BY customer_id;
```

```json
[
  {
    "customer_id": 3,
    "first_name": "François",
    "email": "ftremblay@gmail.com"
  },
  {
    "customer_id": 6,
    "first_name": "Helena",
    "email": "hholy@gmail.com"
  },
  {
    "customer_id": 22,
    "first_name": "Heather",
    "email": "hleacock@gmail.com"
  },
  {
    "customer_id": 24,
    "first_name": "Frank",
    "email": "fralston@gmail.com"
  },
  {
    "customer_id": 28,
    "first_name": "Julia",
    "email": "jubarnett@gmail.com"
  },
  {
    "customer_id": 31,
    "first_name": "Martha",
    "email": "marthasilk@gmail.com"
  },
  {
    "customer_id": 40,
    "first_name": "Dominique",
    "email": "dominiquelefebvre@gmail.com"
  },
  {
    "customer_id": 53,
    "first_name": "Phil",
    "email": "phil.hughes@gmail.com"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-25 · holdout · like

同源：chinook-question-25；审核：needs_human_review。

查找名称含 love 的前 10 首曲目，不区分英文大小写，返回编号和名称，按曲目编号升序。

```sql
SELECT track_id, name FROM track WHERE name ILIKE '%love%' ORDER BY track_id LIMIT 10;
```

```json
[
  {
    "track_id": 24,
    "name": "Love In An Elevator"
  },
  {
    "track_id": 56,
    "name": "Love, Hate, Love"
  },
  {
    "track_id": 195,
    "name": "Let Me Love You Baby"
  },
  {
    "track_id": 335,
    "name": "My Love"
  },
  {
    "track_id": 341,
    "name": "The Girl I Love She Got Long Black Wavy Hair"
  },
  {
    "track_id": 345,
    "name": "Whole Lotta Love"
  },
  {
    "track_id": 413,
    "name": "Loverman"
  },
  {
    "track_id": 440,
    "name": "Love Gun"
  },
  {
    "track_id": 444,
    "name": "Do You Love Me"
  },
  {
    "track_id": 449,
    "name": "Calling Dr. Love"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-26 · dev · null

同源：chinook-question-26；审核：needs_human_review。

有多少位客户没有填写公司名称（company 为 NULL）？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE company IS NULL;
```

```json
[
  {
    "customer_count": 49
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-27 · dev · null

同源：chinook-question-27；审核：needs_human_review。

列出没有作曲者信息（composer 为 NULL）的前 10 首曲目编号和名称，按曲目编号升序。

```sql
SELECT track_id, name FROM track WHERE composer IS NULL ORDER BY track_id LIMIT 10;
```

```json
[
  {
    "track_id": 63,
    "name": "Desafinado"
  },
  {
    "track_id": 64,
    "name": "Garota De Ipanema"
  },
  {
    "track_id": 65,
    "name": "Samba De Uma Nota Só (One Note Samba)"
  },
  {
    "track_id": 66,
    "name": "Por Causa De Você"
  },
  {
    "track_id": 67,
    "name": "Ligia"
  },
  {
    "track_id": 68,
    "name": "Fotografia"
  },
  {
    "track_id": 69,
    "name": "Dindi (Dindi)"
  },
  {
    "track_id": 70,
    "name": "Se Todos Fossem Iguais A Você (Instrumental)"
  },
  {
    "track_id": 71,
    "name": "Falando De Amor"
  },
  {
    "track_id": 72,
    "name": "Angela"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-28 · holdout · null

同源：chinook-question-28；审核：needs_human_review。

列出没有直属上级（reports_to 为 NULL）的员工编号、名字和姓氏，按员工编号升序。

```sql
SELECT employee_id, first_name, last_name FROM employee WHERE reports_to IS NULL ORDER BY employee_id;
```

```json
[
  {
    "employee_id": 1,
    "first_name": "Andrew",
    "last_name": "Adams"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-29 · dev · no_match

同源：chinook-question-29；审核：needs_human_review。

列出国家字段为 Antarctica 的客户编号、名字和姓氏，按客户编号升序。

```sql
SELECT customer_id, first_name, last_name FROM customer WHERE country = 'Antarctica' ORDER BY customer_id;
```

```json
[]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-30 · holdout · no_match

同源：chinook-question-30；审核：needs_human_review。

账单国家字段为 Atlantis 的发票总金额是多少？若没有匹配记录，按 SQL SUM 的语义保留 NULL。

```sql
SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Atlantis';
```

```json
[
  {
    "total_amount": null
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-31 · dev · count

同源：chinook-question-31；审核：needs_human_review。

客户所在国家为 Italy 的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';
```

```json
[
  {
    "customer_count": 1
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-32 · dev · count

同源：chinook-question-32；审核：needs_human_review。

客户所在国家为 Canada 的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';
```

```json
[
  {
    "customer_count": 8
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-33 · dev · aggregate

同源：chinook-question-33；审核：needs_human_review。

账单国家为 Canada 的全部发票总额是多少？

```sql
SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Canada';
```

```json
[
  {
    "total_amount": "303.96"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-34 · dev · aggregate

同源：chinook-question-34；审核：needs_human_review。

曲目表中最短的时长是多少毫秒？

```sql
SELECT MIN(milliseconds) AS minimum_milliseconds FROM track;
```

```json
[
  {
    "minimum_milliseconds": 1071
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-35 · dev · aggregate

同源：chinook-question-35；审核：needs_human_review。

曲目表中最高的单价是多少？

```sql
SELECT MAX(unit_price) AS maximum_unit_price FROM track;
```

```json
[
  {
    "maximum_unit_price": "1.99"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-36 · dev · group

同源：chinook-question-36；审核：needs_human_review。

按发票账单城市统计发票数，先按数量降序，并列按城市名称升序，返回前 10 个城市。

```sql
SELECT billing_city, COUNT(*) AS invoice_count FROM invoice GROUP BY billing_city ORDER BY invoice_count DESC, billing_city ASC LIMIT 10;
```

```json
[
  {
    "billing_city": "Berlin",
    "invoice_count": 14
  },
  {
    "billing_city": "London",
    "invoice_count": 14
  },
  {
    "billing_city": "Mountain View",
    "invoice_count": 14
  },
  {
    "billing_city": "Paris",
    "invoice_count": 14
  },
  {
    "billing_city": "Prague",
    "invoice_count": 14
  },
  {
    "billing_city": "São Paulo",
    "invoice_count": 14
  },
  {
    "billing_city": "Amsterdam",
    "invoice_count": 7
  },
  {
    "billing_city": "Bordeaux",
    "invoice_count": 7
  },
  {
    "billing_city": "Boston",
    "invoice_count": 7
  },
  {
    "billing_city": "Brasília",
    "invoice_count": 7
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-37 · dev · group

同源：chinook-question-37；审核：needs_human_review。

按媒体类型编号统计曲目数，按媒体类型编号升序。

```sql
SELECT media_type_id, COUNT(*) AS track_count FROM track GROUP BY media_type_id ORDER BY media_type_id;
```

```json
[
  {
    "media_type_id": 1,
    "track_count": 3034
  },
  {
    "media_type_id": 2,
    "track_count": 237
  },
  {
    "media_type_id": 3,
    "track_count": 214
  },
  {
    "media_type_id": 4,
    "track_count": 7
  },
  {
    "media_type_id": 5,
    "track_count": 11
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-38 · dev · top

同源：chinook-question-38；审核：needs_human_review。

找出文件字节数最大的 3 首曲目，返回编号、名称和字节数；按字节数降序，并列按曲目编号升序。

```sql
SELECT track_id, name, bytes FROM track ORDER BY bytes DESC, track_id ASC LIMIT 3;
```

```json
[
  {
    "track_id": 3224,
    "name": "Through a Looking Glass",
    "bytes": 1059546140
  },
  {
    "track_id": 2820,
    "name": "Occupation / Precipice",
    "bytes": 1054423946
  },
  {
    "track_id": 3236,
    "name": "The Young Lords",
    "bytes": 587051735
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-39 · dev · date

同源：chinook-question-39；审核：needs_human_review。

2023 年一共开了多少张发票？

```sql
SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01';
```

```json
[
  {
    "invoice_count": 83
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-40 · dev · date

同源：chinook-question-40；审核：needs_human_review。

2022 年 7 月 1 日（含）到 2022 年 10 月 1 日（不含）的发票总额是多少？

```sql
SELECT SUM(total) AS total_amount FROM invoice WHERE invoice_date >= '2022-07-01' AND invoice_date < '2022-10-01';
```

```json
[
  {
    "total_amount": "111.87"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-41 · dev · like

同源：chinook-question-41；审核：needs_human_review。

列出名称以 The 开头的前 8 位艺术家，区分大小写，返回编号和名称，按艺术家编号升序。

```sql
SELECT artist_id, name FROM artist WHERE name LIKE 'The%' ORDER BY artist_id LIMIT 8;
```

```json
[
  {
    "artist_id": 137,
    "name": "The Black Crowes"
  },
  {
    "artist_id": 138,
    "name": "The Clash"
  },
  {
    "artist_id": 139,
    "name": "The Cult"
  },
  {
    "artist_id": 140,
    "name": "The Doors"
  },
  {
    "artist_id": 141,
    "name": "The Police"
  },
  {
    "artist_id": 142,
    "name": "The Rolling Stones"
  },
  {
    "artist_id": 143,
    "name": "The Tea Party"
  },
  {
    "artist_id": 144,
    "name": "The Who"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-42 · dev · filter

同源：chinook-question-42；审核：needs_human_review。

列出名称恰好为 U2 的艺术家编号和名称，按编号升序。

```sql
SELECT artist_id, name FROM artist WHERE name = 'U2' ORDER BY artist_id;
```

```json
[
  {
    "artist_id": 150,
    "name": "U2"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-43 · dev · null

同源：chinook-question-43；审核：needs_human_review。

没有填写州信息（state 为 NULL）的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE state IS NULL;
```

```json
[
  {
    "customer_count": 29
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-44 · dev · no_match

同源：chinook-question-44；审核：needs_human_review。

客户所在国家为 Wakanda 的客户有多少位？保留原筛选值，没匹配时返回 0。

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Wakanda';
```

```json
[
  {
    "customer_count": 0
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-45 · holdout · count

同源：chinook-question-45；审核：needs_human_review。

客户所在国家为 France 的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'France';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-46 · holdout · filter

同源：chinook-question-46；审核：needs_human_review。

列出名称恰好为 Metallica 的艺术家编号和名称，按编号升序。

```sql
SELECT artist_id, name FROM artist WHERE name = 'Metallica' ORDER BY artist_id;
```

```json
[
  {
    "artist_id": 50,
    "name": "Metallica"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-47 · holdout · aggregate

同源：chinook-question-47；审核：needs_human_review。

账单国家为 United Kingdom 的发票平均总额是多少？请保留两位小数。

```sql
SELECT ROUND(AVG(total), 2) AS average_total FROM invoice WHERE billing_country = 'United Kingdom';
```

```json
[
  {
    "average_total": "5.37"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-48 · holdout · group

同源：chinook-question-48；审核：needs_human_review。

按专辑编号统计曲目数，先按数量降序，并列按专辑编号升序，返回前 5 个专辑编号与曲目数。

```sql
SELECT album_id, COUNT(*) AS track_count FROM track GROUP BY album_id ORDER BY track_count DESC, album_id ASC LIMIT 5;
```

```json
[
  {
    "album_id": 141,
    "track_count": 57
  },
  {
    "album_id": 23,
    "track_count": 34
  },
  {
    "album_id": 73,
    "track_count": 30
  },
  {
    "album_id": 229,
    "track_count": 26
  },
  {
    "album_id": 230,
    "track_count": 25
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-49 · holdout · date

同源：chinook-question-49；审核：needs_human_review。

2024 年 1 月 1 日（含）到 2024 年 7 月 1 日（不含）一共开了多少张发票？

```sql
SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2024-01-01' AND invoice_date < '2024-07-01';
```

```json
[
  {
    "invoice_count": 42
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## sql-50 · holdout · like

同源：chinook-question-50；审核：needs_human_review。

列出名称包含 Air 的前 6 张专辑，区分大小写，返回编号和标题，按专辑编号升序。

```sql
SELECT album_id, title FROM album WHERE title LIKE '%Air%' ORDER BY album_id LIMIT 6;
```

```json
[
  {
    "album_id": 328,
    "title": "Charpentier: Divertissements, Airs & Concerts"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-01 · dev · typo

同源：brazil_customer；审核：needs_human_review。

来自巴稀的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-02 · dev · typo

同源：chinook-question-05；审核：needs_human_review。

列出来自美囯的客户编号、城市和州，按客户编号升序。

```sql
SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;
```

```json
[
  {
    "customer_id": 16,
    "city": "Mountain View",
    "state": "CA"
  },
  {
    "customer_id": 17,
    "city": "Redmond",
    "state": "WA"
  },
  {
    "customer_id": 18,
    "city": "New York",
    "state": "NY"
  },
  {
    "customer_id": 19,
    "city": "Cupertino",
    "state": "CA"
  },
  {
    "customer_id": 20,
    "city": "Mountain View",
    "state": "CA"
  },
  {
    "customer_id": 21,
    "city": "Reno",
    "state": "NV"
  },
  {
    "customer_id": 22,
    "city": "Orlando",
    "state": "FL"
  },
  {
    "customer_id": 23,
    "city": "Boston",
    "state": "MA"
  },
  {
    "customer_id": 24,
    "city": "Chicago",
    "state": "IL"
  },
  {
    "customer_id": 25,
    "city": "Madison",
    "state": "WI"
  },
  {
    "customer_id": 26,
    "city": "Fort Worth",
    "state": "TX"
  },
  {
    "customer_id": 27,
    "city": "Tucson",
    "state": "AZ"
  },
  {
    "customer_id": 28,
    "city": "Salt Lake City",
    "state": "UT"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-03 · dev · typo

同源：chinook-question-07；审核：needs_human_review。

列出职位为 Sales Suport Agent 的员工编号、名字和姓氏，按员工编号升序。

```sql
SELECT employee_id, first_name, last_name FROM employee WHERE title = 'Sales Support Agent' ORDER BY employee_id;
```

```json
[
  {
    "employee_id": 3,
    "first_name": "Jane",
    "last_name": "Peacock"
  },
  {
    "employee_id": 4,
    "first_name": "Margaret",
    "last_name": "Park"
  },
  {
    "employee_id": 5,
    "first_name": "Steve",
    "last_name": "Johnson"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-04 · holdout · typo

同源：chinook-question-45；审核：needs_human_review。

客户所在国家为 Frnace 的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'France';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-05 · holdout · typo

同源：chinook-question-46；审核：needs_human_review。

列出名称恰好为 Metalica 的艺术家编号和名称，按编号升序。

```sql
SELECT artist_id, name FROM artist WHERE name = 'Metallica' ORDER BY artist_id;
```

```json
[
  {
    "artist_id": 50,
    "name": "Metallica"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-06 · dev · alias

同源：chinook-question-05；审核：needs_human_review。

列出来自老美的客户编号、城市和州，按客户编号升序。

```sql
SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;
```

```json
[
  {
    "customer_id": 16,
    "city": "Mountain View",
    "state": "CA"
  },
  {
    "customer_id": 17,
    "city": "Redmond",
    "state": "WA"
  },
  {
    "customer_id": 18,
    "city": "New York",
    "state": "NY"
  },
  {
    "customer_id": 19,
    "city": "Cupertino",
    "state": "CA"
  },
  {
    "customer_id": 20,
    "city": "Mountain View",
    "state": "CA"
  },
  {
    "customer_id": 21,
    "city": "Reno",
    "state": "NV"
  },
  {
    "customer_id": 22,
    "city": "Orlando",
    "state": "FL"
  },
  {
    "customer_id": 23,
    "city": "Boston",
    "state": "MA"
  },
  {
    "customer_id": 24,
    "city": "Chicago",
    "state": "IL"
  },
  {
    "customer_id": 25,
    "city": "Madison",
    "state": "WI"
  },
  {
    "customer_id": 26,
    "city": "Fort Worth",
    "state": "TX"
  },
  {
    "customer_id": 27,
    "city": "Tucson",
    "state": "AZ"
  },
  {
    "customer_id": 28,
    "city": "Salt Lake City",
    "state": "UT"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-07 · dev · alias

同源：chinook-question-31；审核：needs_human_review。

来自意大利的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';
```

```json
[
  {
    "customer_count": 1
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-08 · dev · alias

同源：chinook-question-32；审核：needs_human_review。

来自加拿大的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';
```

```json
[
  {
    "customer_count": 8
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-09 · holdout · alias

同源：chinook-question-45；审核：needs_human_review。

来自法国的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'France';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-10 · holdout · alias

同源：chinook-question-47；审核：needs_human_review。

账单国家为英国的发票平均总额是多少？请保留两位小数。

```sql
SELECT ROUND(AVG(total), 2) AS average_total FROM invoice WHERE billing_country = 'United Kingdom';
```

```json
[
  {
    "average_total": "5.37"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-11 · dev · pinyin

同源：brazil_customer；审核：needs_human_review。

来自 ba xi 的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-12 · dev · pinyin

同源：chinook-question-31；审核：needs_human_review。

客户所在国家为 yi da li 的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Italy';
```

```json
[
  {
    "customer_count": 1
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-13 · dev · pinyin

同源：chinook-question-32；审核：needs_human_review。

客户所在国家为 jia na da 的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Canada';
```

```json
[
  {
    "customer_count": 8
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-14 · holdout · pinyin

同源：chinook-question-45；审核：needs_human_review。

客户所在国家为 fa guo 的客户有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'France';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-15 · holdout · pinyin

同源：chinook-question-47；审核：needs_human_review。

账单国家为 ying guo 的发票平均总额是多少？请保留两位小数。

```sql
SELECT ROUND(AVG(total), 2) AS average_total FROM invoice WHERE billing_country = 'United Kingdom';
```

```json
[
  {
    "average_total": "5.37"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-16 · dev · mixed_language

同源：brazil_customer；审核：needs_human_review。

country 是 Brazil 的 customer 有多少位？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-17 · dev · mixed_language

同源：chinook-question-05；审核：needs_human_review。

列出 country 为 USA 的客户编号 customer_id、城市 city 和州 state，按 customer_id 升序。

```sql
SELECT customer_id, city, state FROM customer WHERE country = 'USA' ORDER BY customer_id;
```

```json
[
  {
    "customer_id": 16,
    "city": "Mountain View",
    "state": "CA"
  },
  {
    "customer_id": 17,
    "city": "Redmond",
    "state": "WA"
  },
  {
    "customer_id": 18,
    "city": "New York",
    "state": "NY"
  },
  {
    "customer_id": 19,
    "city": "Cupertino",
    "state": "CA"
  },
  {
    "customer_id": 20,
    "city": "Mountain View",
    "state": "CA"
  },
  {
    "customer_id": 21,
    "city": "Reno",
    "state": "NV"
  },
  {
    "customer_id": 22,
    "city": "Orlando",
    "state": "FL"
  },
  {
    "customer_id": 23,
    "city": "Boston",
    "state": "MA"
  },
  {
    "customer_id": 24,
    "city": "Chicago",
    "state": "IL"
  },
  {
    "customer_id": 25,
    "city": "Madison",
    "state": "WI"
  },
  {
    "customer_id": 26,
    "city": "Fort Worth",
    "state": "TX"
  },
  {
    "customer_id": 27,
    "city": "Tucson",
    "state": "AZ"
  },
  {
    "customer_id": 28,
    "city": "Salt Lake City",
    "state": "UT"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-18 · dev · mixed_language

同源：invoice_global_totals；审核：needs_human_review。

全部 invoice 的 total 加起来是多少？

```sql
SELECT SUM(total) AS total_amount FROM invoice;
```

```json
[
  {
    "total_amount": "2328.60"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-19 · dev · mixed_language

同源：chinook-question-33；审核：needs_human_review。

billing_country 为 Canada 的全部 invoice 的 total 总和是多少？

```sql
SELECT SUM(total) AS total_amount FROM invoice WHERE billing_country = 'Canada';
```

```json
[
  {
    "total_amount": "303.96"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-20 · holdout · mixed_language

同源：chinook-question-46；审核：needs_human_review。

artist 的 name 恰好为 Metallica，列出 artist_id 和 name，按 artist_id 升序。

```sql
SELECT artist_id, name FROM artist WHERE name = 'Metallica' ORDER BY artist_id;
```

```json
[
  {
    "artist_id": 50,
    "name": "Metallica"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-21 · dev · colloquial

同源：chinook-question-01；审核：needs_human_review。

咱们客户表一共有几个人？

```sql
SELECT COUNT(*) AS customer_count FROM customer;
```

```json
[
  {
    "customer_count": 59
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-22 · dev · colloquial

同源：brazil_customer；审核：needs_human_review。

帮我数数，来自巴西的客户有几位呀？

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-23 · dev · colloquial

同源：chinook-question-10；审核：needs_human_review。

这批曲目的平均长度是几毫秒？

```sql
SELECT AVG(milliseconds) AS average_milliseconds FROM track;
```

```json
[
  {
    "average_milliseconds": "393599.212103910933"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-24 · dev · colloquial

同源：chinook-question-34；审核：needs_human_review。

曲目里最短的一首有几毫秒呀？

```sql
SELECT MIN(milliseconds) AS minimum_milliseconds FROM track;
```

```json
[
  {
    "minimum_milliseconds": 1071
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-25 · holdout · colloquial

同源：chinook-question-49；审核：needs_human_review。

帮我数一下，2024 年上半年，也就是 1 月 1 日起到 7 月 1 日之前，开了几张发票？

```sql
SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2024-01-01' AND invoice_date < '2024-07-01';
```

```json
[
  {
    "invoice_count": 42
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-26 · dev · extra_words

同源：brazil_customer；审核：needs_human_review。

你好，请帮忙查一下来自巴西的客户有多少位，谢谢。

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Brazil';
```

```json
[
  {
    "customer_count": 5
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-27 · dev · extra_words

同源：chinook-question-26；审核：needs_human_review。

麻烦帮我看看，有多少位客户没有填写公司名称，也就是 company 为 NULL 呢？谢谢。

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE company IS NULL;
```

```json
[
  {
    "customer_count": 49
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-28 · dev · extra_words

同源：chinook-question-39；审核：needs_human_review。

请帮我查一查，2023 年一共开了多少张发票，非常感谢。

```sql
SELECT COUNT(*) AS invoice_count FROM invoice WHERE invoice_date >= '2023-01-01' AND invoice_date < '2024-01-01';
```

```json
[
  {
    "invoice_count": 83
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-29 · dev · extra_words

同源：chinook-question-44；审核：needs_human_review。

麻烦查一下客户所在国家为 Wakanda 的客户有多少位，保留原值，没匹配返回 0，谢谢。

```sql
SELECT COUNT(*) AS customer_count FROM customer WHERE country = 'Wakanda';
```

```json
[
  {
    "customer_count": 0
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。

## robust-30 · holdout · extra_words

同源：chinook-question-50；审核：needs_human_review。

您好，请列出名称包含 Air 的前 6 张专辑，区分大小写，返回编号和标题，按专辑编号升序，谢谢。

```sql
SELECT album_id, title FROM album WHERE title LIKE '%Air%' ORDER BY album_id LIMIT 6;
```

```json
[
  {
    "album_id": 328,
    "title": "Charpentier: Divertissements, Airs & Concerts"
  }
]
```

- [ ] 已核对题意、字段、条件、单位和排序。
- [ ] 已核对实际 SQL 结果并记录审核人。
