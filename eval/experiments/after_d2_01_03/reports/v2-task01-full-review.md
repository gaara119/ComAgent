# V2专项①全部30条实际回答AI预审

状态：FINAL_ACTUAL_V2_REVIEW；全部人工仍pending。

原固定自动结果：13/26
原固定评分文件：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001-scores.json](<../runtime_eval/runs/V2-001-scores.json>)
实际读取30原始响应、provider 43份；本次0API/0模型/0SQL。
参考AI分布：{"AI建议通过": 16, "AI建议有条件通过": 10, "AI发现错误": 4}
系统AI分布：{"AI建议通过": 14, "AI建议有条件通过": 6, "AI发现错误": 6, "证据不足": 4}；AI分布不是重计成绩。

## sp01-01 · standard

原题：How many customers are from France?
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；customers明确客户对象；真实France值按customer.country等值COUNT(*)，客户记录粒度、NULL过滤和无期间条件均正确。V2实际绑定France、SQL和保存结果5一致，无改口径。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'France';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        5
      ]
    ],
    "table": [
      {
        "customer_count": 5
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'France'",
  "actual_final_table": [
    {
      "count": 5
    }
  ],
  "actual_answer": "查询结果：5。",
  "actual_nlu_bindings": [
    {
      "column": "customer.country",
      "operator": "=",
      "value": "France",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "v-352185818871f006e648",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'France'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-01",
    "task": "01",
    "category": "standard",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "actual": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'France'",
          "predicates": {
            "customer.country = 'France'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'France'",
          "predicates": {
            "customer.country = 'France'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-01/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-01/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-01/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-01/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-01/turns/000/provider/a0832af8cf5244cbbfe606488ce2b056.json](<../runtime_eval/runs/V2-001/cases/sp01-01/turns/000/provider/a0832af8cf5244cbbfe606488ce2b056.json>)；SHA=a1d0602148e7a1a70578174de2fe3138d992dc9ec1f124d555bf663d2669d154；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-02 · alias

原题：Iron Maiden乐队一共有多少张专辑？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；已批准Iron Maiden乐队别名被绑定并改写。实际album按artist_id FK内连接artist过滤Iron Maiden，COUNT(DISTINCT album.album_id)与参考COUNT(*)等价：album_id为非NULL主键，artist_id是artist主键且多对一，不会复制专辑记录。实际21；此结构证明独立于结果相等。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "album_count"
    ],
    "rows": [
      [
        21
      ]
    ],
    "table": [
      {
        "album_count": 21
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(DISTINCT album.album_id) AS album_count FROM \"public\".\"album\" JOIN \"public\".\"artist\" ON \"public\".\"album\".\"artist_id\" = \"public\".\"artist\".\"artist_id\" WHERE \"public\".\"artist\".\"name\" = 'Iron Maiden'",
  "actual_final_table": [
    {
      "album_count": 21
    }
  ],
  "actual_answer": "查询结果：21。",
  "actual_nlu_bindings": [
    {
      "column": "artist.name",
      "operator": "=",
      "value": "Iron Maiden",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-7a0187a2e65d10ae",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 13,
      "original": "Iron Maiden乐队",
      "replacement": "Iron Maiden",
      "method": "exact",
      "evidence_ref": "a-7a0187a2e65d10ae"
    }
  ],
  "actual_rewritten_question": "Iron Maiden一共有多少张专辑？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "album",
      "artist"
    ],
    "actual_predicate_expressions": [
      "\"public\".\"album\".\"artist_id\" = \"public\".\"artist\".\"artist_id\"",
      "\"public\".\"artist\".\"name\" = 'Iron Maiden'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(DISTINCT album.album_id)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "PK_FK_count_equivalence": {
      "album_primary_key": [
        "album_id"
      ],
      "artist_primary_key": [
        "artist_id"
      ],
      "album_id_nullable": false,
      "album_foreign_keys": [
        {
          "columns": [
            "artist_id"
          ],
          "references": {
            "schema": "public",
            "table": "artist",
            "columns": [
              "artist_id"
            ]
          }
        }
      ],
      "reason": "PK uniqueness/nonNULL and FK many-to-one prove album COUNT(*),COUNT(album_id),COUNT(DISTINCT album_id) equivalence for these unchanged inner FK joins"
    }
  },
  "original_automatic_score": {
    "id": "sp01-02",
    "task": "01",
    "category": "alias",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "artist.name",
          "=",
          "\"Iron Maiden\""
        ]
      ],
      "actual": [
        [
          "artist.name",
          "=",
          "\"Iron Maiden\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": true,
        "gold": {
          "ast": "SELECT COUNT(*) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'Iron Maiden'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'Iron Maiden'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(DISTINCT album.album_id) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'Iron Maiden'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'Iron Maiden'": 1
          },
          "aggregates": [
            "COUNT(DISTINCT album.album_id)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": null
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": null,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "AI_pending"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-02/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-02/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-02/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-02/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-02/turns/000/provider/901606b9e76149c2a019683fc2bd8a7c.json](<../runtime_eval/runs/V2-001/cases/sp01-02/turns/000/provider/901606b9e76149c2a019683fc2bd8a7c.json>)；SHA=5487612a29937a16148974305457b925845516263d6b977e9da849aca5d075c5；trace核验=true；实际system字符=[2195]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-03 · alias

原题：德国的发票一共开了多少钱？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；实际德国→invoice.billing_country=Germany且SUM(invoice.total)=156.48，按发票账单国家解释保持金额粒度，未联明细。参考与实际均选择账单国家，但已确认规则只区分两国字段，没有全局地区默认。维持V0地区解释争议，人工确认后才可完整通过。
```json
{
  "gold_sql_unchanged": "SELECT SUM(i.total) AS revenue FROM public.invoice i WHERE i.billing_country = 'Germany';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "revenue"
    ],
    "rows": [
      [
        "156.48"
      ]
    ],
    "table": [
      {
        "revenue": "156.48"
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT SUM(\"total\") FROM \"public\".\"invoice\" WHERE \"billing_country\" = 'Germany'",
  "actual_final_table": [
    {
      "sum": "156.48"
    }
  ],
  "actual_answer": "查询结果：156.48。",
  "actual_nlu_bindings": [
    {
      "column": "invoice.billing_country",
      "operator": "=",
      "value": "Germany",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-3414db81951a6279",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 2,
      "original": "德国",
      "replacement": "Germany",
      "method": "exact",
      "evidence_ref": "a-3414db81951a6279"
    }
  ],
  "actual_rewritten_question": "Germany的发票一共开了多少钱？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "invoice"
    ],
    "actual_predicate_expressions": [
      "\"billing_country\" = 'Germany'"
    ],
    "actual_aggregate_expressions": [
      "SUM(\"total\")"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-03",
    "task": "01",
    "category": "alias",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "invoice.billing_country",
          "=",
          "\"Germany\""
        ]
      ],
      "actual": [
        [
          "invoice.billing_country",
          "=",
          "\"Germany\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT SUM(invoice.total) FROM invoice WHERE invoice.billing_country = 'Germany'",
          "predicates": {
            "invoice.billing_country = 'Germany'": 1
          },
          "aggregates": [
            "SUM(invoice.total)"
          ],
          "tables": [
            "invoice"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT SUM(invoice.total) FROM invoice WHERE invoice.billing_country = 'Germany'",
          "predicates": {
            "invoice.billing_country = 'Germany'": 1
          },
          "aggregates": [
            "SUM(invoice.total)"
          ],
          "tables": [
            "invoice"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-03/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-03/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-03/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-03/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-03/turns/000/provider/c38d7812d71942e8a72639a8a068381e.json](<../runtime_eval/runs/V2-001/cases/sp01-03/turns/000/provider/c38d7812d71942e8a72639a8a068381e.json>)；SHA=7d7b369f250801d91967a202bffd25a987e66c3d7dd61086c9099e241e159a77；trace核验=true；实际system字符=[1359]

仍需人工确认：核对发票+国名这一语境能否作为账单国家的获准字段限定；与12/14/25保持一致；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-04 · typo

原题：Frnace 有多少客户？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；实际SQL确将Frnace变为France，COUNT客户结果5；但metadata.nlu mentions/bindings/patches及intent.filters均为空，response.rewritten_question为NULL。只能说在人工同意该拼写修正后查询正确；有限候选消歧、绑定和显式改写链未完成，不能按结果5认定专项①全通过。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'France';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        5
      ]
    ],
    "table": [
      {
        "customer_count": 5
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'France'",
  "actual_final_table": [
    {
      "count": 5
    }
  ],
  "actual_answer": "查询结果：5。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'France'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "query_vs_binding_chain": {
      "France_SQL_and_saved5": true,
      "verified_NLU_binding_present": false,
      "explicit_rewrite_present": false,
      "pipeline_full_acceptance_not_proven": true
    }
  },
  "original_automatic_score": {
    "id": "sp01-04",
    "task": "01",
    "category": "typo",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'France'",
          "predicates": {
            "customer.country = 'France'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'France'",
          "predicates": {
            "customer.country = 'France'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-04/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-04/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-04/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-04/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-04/turns/000/provider/49680e16094b4ab8bd9c3723288cc30f.json](<../runtime_eval/runs/V2-001/cases/sp01-04/turns/000/provider/49680e16094b4ab8bd9c3723288cc30f.json>)；SHA=49caff9af04f3588fbd255569d2b369565e55db0c652b6155d45b7ed9e0dd439；trace核验=true；实际system字符=[1359]

仍需人工确认：确认字面拼写恢复策略；NLU/声明缺项不标完整链路通过；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-05 · typo

原题：Metallcia 有多少张专辑？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；实际NLU无候选/绑定/改写；3次生成及修复仍LOWER(artist.name)=LOWER('Metallcia')，未修成参考Metallica，并被多表守卫拒绝，table为NULL。在人工确认参考拼写意图后仍存在未正确消歧及查询未执行的真实缺陷；不能把被拒SQL当已得到10。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Metallica';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "album_count"
    ],
    "rows": [
      [
        10
      ]
    ],
    "table": [
      {
        "album_count": 10
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "FAILED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"album\" AS a JOIN \"public\".\"artist\" AS ar ON a.\"artist_id\" = ar.\"artist_id\" WHERE LOWER(ar.\"name\") = LOWER('Metallcia')",
  "actual_final_table": null,
  "actual_answer": "SQL 未通过校验：该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "album",
      "artist"
    ],
    "actual_predicate_expressions": [
      "a.\"artist_id\" = ar.\"artist_id\"",
      "LOWER(ar.\"name\") = LOWER('Metallcia')"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-05",
    "task": "01",
    "category": "typo",
    "scorable": true,
    "initial_status": "FAILED",
    "final_status": "FAILED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "artist.name",
          "=",
          "\"Metallica\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "artist.name",
          "=",
          "\"Metallica\""
        ]
      ],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
        "gold": {
          "ast": "SELECT COUNT(*) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'Metallica'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'Metallica'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE LOWER(artist.name) = LOWER('Metallcia')",
          "predicates": {
            "LOWER(artist.name) = LOWER('Metallcia')": 1,
            "album.artist_id = artist.artist_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": false,
        "reason": "No successful query result"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "api_failed",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-05/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-05/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-05/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-05/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-05/turns/000/provider/70fb8551778040b08af8912b98855add.json](<../runtime_eval/runs/V2-001/cases/sp01-05/turns/000/provider/70fb8551778040b08af8912b98855add.json>)；SHA=b67f20b63391a9ec6dc33f86020fe877127ed918f3145f32cf12eef7ff0b6d6d；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-05/turns/000/provider/49362ebf19e44db2875c4f70bd8ee077.json](<../runtime_eval/runs/V2-001/cases/sp01-05/turns/000/provider/49362ebf19e44db2875c4f70bd8ee077.json>)；SHA=209de8aaef14ab995eb87bccd2efa34b22b948df53ccb5d25c5f7a67ba1fe930；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-05/turns/000/provider/0cb0c4e8314b48529ea6500c3b8cc54c.json](<../runtime_eval/runs/V2-001/cases/sp01-05/turns/000/provider/0cb0c4e8314b48529ea6500c3b8cc54c.json>)；SHA=455075133575bb86204ad8b78442072a671caf540ffb6e6978a6f991be7b611e；trace核验=true；实际system字符=[1359]

仍需人工确认：确认拼写恢复候选的业务接受规则；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-06 · pinyin

原题：Deguo 有多少张专辑？
参考判断：AI发现错误；保留V0冻结参考意见与新争议。
系统判断：**证据不足**；原参考题有Deguo专辑却canonical/控制器对应无关对象，gold为空，原先已排除评分，仍不能按该标准决定系统正确。V2实际猜成artist.name='Deguo'、无绑定/澄清、跨表守卫FAILED且无结果。独立观察为无依据的对象解释及未完成查询，未把坏参考变成系统通过。
```json
{
  "gold_sql_unchanged": "",
  "gold_result_from_preparation_unchanged": null,
  "actual_final_status": "FAILED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"album\" AS a JOIN \"public\".\"artist\" AS ar ON a.\"artist_id\" = ar.\"artist_id\" WHERE LOWER(ar.\"name\") = LOWER('Deguo')",
  "actual_final_table": null,
  "actual_answer": "SQL 未通过校验：该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "album",
      "artist"
    ],
    "actual_predicate_expressions": [
      "a.\"artist_id\" = ar.\"artist_id\"",
      "LOWER(ar.\"name\") = LOWER('Deguo')"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-06",
    "task": "01",
    "category": "pinyin",
    "scorable": false,
    "initial_status": "FAILED",
    "final_status": "FAILED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [],
      "actual": [],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "No deterministic SQL contract for this case"
      },
      "result": {
        "correct": null,
        "reason": "Saved gold_result unavailable"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": null,
    "pending_annotation": true,
    "outcome": "api_failed",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-06/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-06/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-06/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-06/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-06/turns/000/provider/e513be93d2f048319376ba61f0cb5742.json](<../runtime_eval/runs/V2-001/cases/sp01-06/turns/000/provider/e513be93d2f048319376ba61f0cb5742.json>)；SHA=2435732ea70b06894e39c9fa07d24714559d38660424239f63e8d1eba104ba39；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-06/turns/000/provider/e88d6a9e73cd420db20f33a0bd33722a.json](<../runtime_eval/runs/V2-001/cases/sp01-06/turns/000/provider/e88d6a9e73cd420db20f33a0bd33722a.json>)；SHA=a4a005a898eb8d4e2da04e13689d226b3a1ab7b6d08f2f20296b7c408023b168；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-06/turns/000/provider/b85b4039d70e450ba3c2a45a2283cffe.json](<../runtime_eval/runs/V2-001/cases/sp01-06/turns/000/provider/b85b4039d70e450ba3c2a45a2283cffe.json>)；SHA=716090d638fb94ff016fad3d8491f5f61cde7bd02c6bac169c0664340d4aa5b5；trace核验=true；实际system字符=[1359]

仍需人工确认：重审原题/改写/controller对应关系；保持当前不可评分状态；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-07 · mixed_language

原题：Chinook 里 Protected AAC audio file 这种 format 有多少首曲目？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；原文明确Protected AAC媒体格式与track数量，参考track.media_type_id→media_type主键FK有效。V2模型3次给出同一正确FK/名称过滤COUNT，调用实际仍单表system，sql_validate均拒绝跨表，NLU绑定空，table=NULL。实际未运行结果237，不能以候选SQL语义正确认定系统回答正确。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'Protected AAC audio file';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "track_count"
    ],
    "rows": [
      [
        237
      ]
    ],
    "table": [
      {
        "track_count": 237
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "FAILED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"track\" AS t JOIN \"public\".\"media_type\" AS m ON t.\"media_type_id\" = m.\"media_type_id\" WHERE m.\"name\" = 'Protected AAC audio file'",
  "actual_final_table": null,
  "actual_answer": "SQL 未通过校验：该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "media_type",
      "track"
    ],
    "actual_predicate_expressions": [
      "t.\"media_type_id\" = m.\"media_type_id\"",
      "m.\"name\" = 'Protected AAC audio file'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-07",
    "task": "01",
    "category": "mixed_language",
    "scorable": true,
    "initial_status": "FAILED",
    "final_status": "FAILED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "media_type.name",
          "=",
          "\"Protected AAC audio file\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "media_type.name",
          "=",
          "\"Protected AAC audio file\""
        ]
      ],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM track JOIN media_type ON track.media_type_id = media_type.media_type_id WHERE media_type.name = 'Protected AAC audio file'",
          "predicates": {
            "media_type.name = 'Protected AAC audio file'": 1,
            "track.media_type_id = media_type.media_type_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "media_type",
            "track"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM track JOIN media_type ON track.media_type_id = media_type.media_type_id WHERE media_type.name = 'Protected AAC audio file'",
          "predicates": {
            "media_type.name = 'Protected AAC audio file'": 1,
            "track.media_type_id = media_type.media_type_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "media_type",
            "track"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": false,
        "reason": "No successful query result"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "api_failed",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-07/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-07/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-07/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-07/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-07/turns/000/provider/34c1b2a0948c43dfa33cdc148c96eb3d.json](<../runtime_eval/runs/V2-001/cases/sp01-07/turns/000/provider/34c1b2a0948c43dfa33cdc148c96eb3d.json>)；SHA=38e48a0ef44cdbe2e48e8c3270d86b28917b5b931c5ad27c23183d60ad97ce3d；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-07/turns/000/provider/6afa14b12cf643e8a6094c7ced198c84.json](<../runtime_eval/runs/V2-001/cases/sp01-07/turns/000/provider/6afa14b12cf643e8a6094c7ced198c84.json>)；SHA=314c8a8755ab844c6efa335a2e7f82784a14afe40e8618077cad7bc77548e384；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-07/turns/000/provider/89633bf8a25c4bfe9e98e61751071946.json](<../runtime_eval/runs/V2-001/cases/sp01-07/turns/000/provider/89633bf8a25c4bfe9e98e61751071946.json>)；SHA=15a483dc32016c9b0308b12f918c44169de023c514dda8ad8c70c392a70ffcd1；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-08 · colloquial

原题：意大利那边现在有多少客户？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；意大利在明确客户对象下使用批准customer.country=Italy别名并显式改写；COUNT客户记录1。‘现在’对应现有数据快照，未发明客户创建日期或把invoice_date套到客户。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Italy';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        1
      ]
    ],
    "table": [
      {
        "customer_count": 1
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Italy'",
  "actual_final_table": [
    {
      "count": 1
    }
  ],
  "actual_answer": "查询结果：1。",
  "actual_nlu_bindings": [
    {
      "column": "customer.country",
      "operator": "=",
      "value": "Italy",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-d0e9fad30baaded8",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 3,
      "original": "意大利",
      "replacement": "Italy",
      "method": "exact",
      "evidence_ref": "a-d0e9fad30baaded8"
    }
  ],
  "actual_rewritten_question": "Italy那边现在有多少客户？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'Italy'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-08",
    "task": "01",
    "category": "colloquial",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"Italy\""
        ]
      ],
      "actual": [
        [
          "customer.country",
          "=",
          "\"Italy\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Italy'",
          "predicates": {
            "customer.country = 'Italy'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Italy'",
          "predicates": {
            "customer.country = 'Italy'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-08/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-08/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-08/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-08/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-08/turns/000/provider/2a84b282441d465bb02c12ad1056a6f0.json](<../runtime_eval/runs/V2-001/cases/sp01-08/turns/000/provider/2a84b282441d465bb02c12ad1056a6f0.json>)；SHA=b3abf1c95b4b9b355a531075bbb92dc0bd4f4effa2faad3fb8ea33849e4f9a98；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-09 · multi_candidate

原题：Chinook 里有多少首摇滚歌曲？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；实际仅给出genre.name的Rock和Rock And Roll两个真实候选，L2、filters为空、SQL/table为空，不强制唯一绑定。满足本条初始候选澄清目标；控制器无补充，因此不是续答成功或SQL执行通过。
```json
{
  "gold_sql_unchanged": null,
  "gold_result_from_preparation_unchanged": null,
  "actual_final_status": "NEEDS_CLARIFICATION",
  "actual_final_sql": null,
  "actual_final_table": null,
  "actual_answer": "“摇滚”具体指哪个对象？",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": [
    {
      "id": "value:issue-cef0fa76c70939e5:v-5abaeb142337ce5b27ed",
      "label": "Rock（genre.name）"
    },
    {
      "id": "value:issue-cef0fa76c70939e5:v-10facd793602b59518e7",
      "label": "Rock And Roll（genre.name）"
    }
  ],
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": false,
    "no_new_sql_execution": true,
    "candidate_only_gate": {
      "level": "L2",
      "options": [
        {
          "id": "value:issue-cef0fa76c70939e5:v-5abaeb142337ce5b27ed",
          "label": "Rock（genre.name）"
        },
        {
          "id": "value:issue-cef0fa76c70939e5:v-10facd793602b59518e7",
          "label": "Rock And Roll（genre.name）"
        }
      ],
      "no_auto_filters": true,
      "no_SQL_executed": true
    }
  },
  "original_automatic_score": {
    "id": "sp01-09",
    "task": "01",
    "category": "multi_candidate",
    "scorable": true,
    "initial_status": "NEEDS_CLARIFICATION",
    "final_status": "NEEDS_CLARIFICATION",
    "observed_initial_level": "L2",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "candidate_preservation",
      "expected": [
        [
          "genre.name",
          "=",
          "\"Rock And Roll\""
        ],
        [
          "genre.name",
          "=",
          "\"Rock\""
        ]
      ],
      "retained": [
        [
          "genre.name",
          "=",
          "\"Rock And Roll\""
        ],
        [
          "genre.name",
          "=",
          "\"Rock\""
        ]
      ],
      "bound": []
    },
    "query": {
      "complete": true,
      "semantic_preservation": {
        "correct": true,
        "reason": "Preserved candidate-only clarification contract"
      },
      "result": {
        "correct": null,
        "reason": "Initial clarification has no unique gold query"
      }
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "candidate_only_clarification",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-09/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-09/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-09/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-09/turns/000/response.raw.json>)

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-10 · explicit_absent

原题：查询 genre 为 Vaporwave 的曲目数量；如果数据库里根本没有这个流派，请直接报告没有记录。
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；Vaporwave在已保存25个流派事实中不存在；模型保留该字面值并给出track→genre FK COUNT，未换成相似流派，候选裁决unmatched可观察。但实际3次SQL均被单表守卫拒绝，table=NULL、未报告没有记录；正确候选SQL和预计COUNT0不能替代实际回答。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS track_count FROM public.track t JOIN public.genre g ON t.genre_id = g.genre_id WHERE g.name = 'Vaporwave';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "track_count"
    ],
    "rows": [
      [
        0
      ]
    ],
    "table": [
      {
        "track_count": 0
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "FAILED",
  "actual_final_sql": "SELECT COUNT(*) AS track_count FROM \"public\".\"track\" AS t JOIN \"public\".\"genre\" AS g ON t.\"genre_id\" = g.\"genre_id\" WHERE g.\"name\" = 'Vaporwave'",
  "actual_final_table": null,
  "actual_answer": "SQL 未通过校验：该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "genre",
      "track"
    ],
    "actual_predicate_expressions": [
      "t.\"genre_id\" = g.\"genre_id\"",
      "g.\"name\" = 'Vaporwave'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-10",
    "task": "01",
    "category": "explicit_absent",
    "scorable": true,
    "initial_status": "FAILED",
    "final_status": "FAILED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "unknown_literal_sql_contract",
      "expected": [
        [
          "genre.name",
          "=",
          "\"Vaporwave\""
        ]
      ],
      "actual": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM track JOIN genre ON track.genre_id = genre.genre_id WHERE genre.name = 'Vaporwave'",
          "predicates": {
            "genre.name = 'Vaporwave'": 1,
            "track.genre_id = genre.genre_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "genre",
            "track"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM track JOIN genre ON track.genre_id = genre.genre_id WHERE genre.name = 'Vaporwave'",
          "predicates": {
            "genre.name = 'Vaporwave'": 1,
            "track.genre_id = genre.genre_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "genre",
            "track"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": false,
        "reason": "No successful query result"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "api_failed",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-10/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-10/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-10/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-10/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-10/turns/000/provider/efc8ff630b89486492900b2443717408.json](<../runtime_eval/runs/V2-001/cases/sp01-10/turns/000/provider/efc8ff630b89486492900b2443717408.json>)；SHA=c4d19dca304c9c371134f9b3c62246058fe1043f9cf7e95327f53deecca609d9；trace核验=true；实际system字符=[1373]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-10/turns/000/provider/6f2032adb509450aa1babe5c2459ff99.json](<../runtime_eval/runs/V2-001/cases/sp01-10/turns/000/provider/6f2032adb509450aa1babe5c2459ff99.json>)；SHA=187f7bf215f0a826b93f6a4c2337af1249d961cdb8dcc197a0db476c633dbc04；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-10/turns/000/provider/72033bdaeba145c5bebe040f3d1629c4.json](<../runtime_eval/runs/V2-001/cases/sp01-10/turns/000/provider/72033bdaeba145c5bebe040f3d1629c4.json>)；SHA=48babecc0b1644f9b6702d6463613366bd9255587f8916f8cf673dd421830765；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-10/turns/000/provider/344a54838630421b971baaa1f9e0fe33.json](<../runtime_eval/runs/V2-001/cases/sp01-10/turns/000/provider/344a54838630421b971baaa1f9e0fe33.json>)；SHA=a03a2e6eaea630b08dded652c20479db26c66ca4677e25d5331c310ba45364cf；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-11 · standard

原题：How many customers are from Canada?
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；明确Canada客户按customer.country=Canada COUNT(*)，真实exact绑定、无额外期间/表/聚合，实际8。别名customer_count不会改语义。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Canada';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        8
      ]
    ],
    "table": [
      {
        "customer_count": 8
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Canada'",
  "actual_final_table": [
    {
      "customer_count": 8
    }
  ],
  "actual_answer": "查询结果：8。",
  "actual_nlu_bindings": [
    {
      "column": "customer.country",
      "operator": "=",
      "value": "Canada",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "v-f357d4a9aa3228c9d69b",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'Canada'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-11",
    "task": "01",
    "category": "standard",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"Canada\""
        ]
      ],
      "actual": [
        [
          "customer.country",
          "=",
          "\"Canada\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Canada'",
          "predicates": {
            "customer.country = 'Canada'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Canada'",
          "predicates": {
            "customer.country = 'Canada'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-11/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-11/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-11/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-11/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-11/turns/000/provider/539a521da73b4338abca7e7845ec1426.json](<../runtime_eval/runs/V2-001/cases/sp01-11/turns/000/provider/539a521da73b4338abca7e7845ec1426.json>)；SHA=10a790aa99b807c2d06ba79170a270ee9aefce84582615be104910578f521a76；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-12 · standard

原题：What was the total invoice revenue for France in 2022?
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；明确2022发票收入，但France未明说客户居住国还是账单国家；V2实际L2问这两种口径，未SQL且controller_unanswered。全局地区默认未获确认，原参考唯一账单国家39.60继续有条件待核；不能仅因原预期L0就把这条追问定为错误。
```json
{
  "gold_sql_unchanged": "SELECT SUM(total) AS revenue FROM public.invoice WHERE billing_country = 'France' AND invoice_date >= DATE '2022-01-01' AND invoice_date < DATE '2023-01-01';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "revenue"
    ],
    "rows": [
      [
        "39.60"
      ]
    ],
    "table": [
      {
        "revenue": "39.60"
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "NEEDS_CLARIFICATION",
  "actual_final_sql": null,
  "actual_final_table": null,
  "actual_answer": "国家按客户所在地还是发票账单国家？",
  "actual_nlu_bindings": [
    {
      "column": "invoice.billing_country",
      "operator": "=",
      "value": "France",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "v-da1995626f6b421035ba",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": [
    {
      "id": "billing_country",
      "label": "按发票账单国家"
    },
    {
      "id": "customer_country",
      "label": "按客户所在地国家"
    }
  ],
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": false,
    "no_new_sql_execution": true
  },
  "original_automatic_score": {
    "id": "sp01-12",
    "task": "01",
    "category": "standard",
    "scorable": true,
    "initial_status": "NEEDS_CLARIFICATION",
    "final_status": "NEEDS_CLARIFICATION",
    "observed_initial_level": "L2",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "invoice.billing_country",
          "=",
          "\"France\""
        ]
      ],
      "actual": [
        [
          "invoice.billing_country",
          "=",
          "\"France\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": false,
        "status": "failed",
        "reason": "No actual SQL"
      },
      "result": {
        "correct": false,
        "reason": "No successful query result"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": false,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "controller_unanswered",
    "controller_events": [
      {
        "after_turn": 0,
        "outcome": "controller_unanswered",
        "request": null,
        "asked_key": null,
        "supplement_key": null,
        "reason": "Unknown/unsupported asks, no allowed supplement, or a repeated unresolved key"
      }
    ],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-12/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-12/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-12/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-12/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-12/turns/000/provider/edf2d783d29c44d2938f9c4d6da92f0a.json](<../runtime_eval/runs/V2-001/cases/sp01-12/turns/000/provider/edf2d783d29c44d2938f9c4d6da92f0a.json>)；SHA=e3cabf008aa03bca03099c0a8c7cdc7eee777067da13c4b61ef789b858ed7bdc；trace核验=true；实际system字符=[4249]

仍需人工确认：确认invoice+for国家是否有团队批准的默认地区口径，或应要求澄清；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-13 · alias

原题：Iron Maiden乐队一共有多少张专辑？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；内容与sp01-02重复，原标签排除状态保留。V2已批准艺术家绑定/改写，album→artist主键FK过滤Iron Maiden，COUNT(album.album_id)与COUNT(*)等价，因为该主键非NULL且FK多对一；结果21正确，但重复题不增加独立覆盖。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS album_count FROM public.album al JOIN public.artist ar ON al.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "album_count"
    ],
    "rows": [
      [
        21
      ]
    ],
    "table": [
      {
        "album_count": 21
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(a.\"album_id\") AS album_count FROM \"public\".\"album\" AS a JOIN \"public\".\"artist\" AS ar ON a.\"artist_id\" = ar.\"artist_id\" WHERE ar.\"name\" = 'Iron Maiden'",
  "actual_final_table": [
    {
      "album_count": 21
    }
  ],
  "actual_answer": "查询结果：21。",
  "actual_nlu_bindings": [
    {
      "column": "artist.name",
      "operator": "=",
      "value": "Iron Maiden",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-7a0187a2e65d10ae",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 13,
      "original": "Iron Maiden乐队",
      "replacement": "Iron Maiden",
      "method": "exact",
      "evidence_ref": "a-7a0187a2e65d10ae"
    }
  ],
  "actual_rewritten_question": "Iron Maiden一共有多少张专辑？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "album",
      "artist"
    ],
    "actual_predicate_expressions": [
      "a.\"artist_id\" = ar.\"artist_id\"",
      "ar.\"name\" = 'Iron Maiden'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(a.\"album_id\")"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "PK_FK_count_equivalence": {
      "album_primary_key": [
        "album_id"
      ],
      "artist_primary_key": [
        "artist_id"
      ],
      "album_id_nullable": false,
      "album_foreign_keys": [
        {
          "columns": [
            "artist_id"
          ],
          "references": {
            "schema": "public",
            "table": "artist",
            "columns": [
              "artist_id"
            ]
          }
        }
      ],
      "reason": "PK uniqueness/nonNULL and FK many-to-one prove album COUNT(*),COUNT(album_id),COUNT(DISTINCT album_id) equivalence for these unchanged inner FK joins"
    }
  },
  "original_automatic_score": {
    "id": "sp01-13",
    "task": "01",
    "category": "alias",
    "scorable": false,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "artist.name",
          "=",
          "\"Iron Maiden\""
        ]
      ],
      "actual": [
        [
          "artist.name",
          "=",
          "\"Iron Maiden\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": true,
        "gold": {
          "ast": "SELECT COUNT(*) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'Iron Maiden'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'Iron Maiden'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(album.album_id) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'Iron Maiden'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'Iron Maiden'": 1
          },
          "aggregates": [
            "COUNT(album.album_id)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": null
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": null,
    "pending_annotation": true,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-13/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-13/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-13/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-13/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-13/turns/000/provider/f5adb83a22f948e7b814e12f086ffdf3.json](<../runtime_eval/runs/V2-001/cases/sp01-13/turns/000/provider/f5adb83a22f948e7b814e12f086ffdf3.json>)；SHA=5ad59b9d70a5ea46f002584b929e129f764f539e4322e4fb2d5484be7688bd51；trace核验=true；实际system字符=[2195]

仍需人工确认：是否保留重复作一致性样本；不改当前不可评分标记；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-14 · alias

原题：法兰西共和国的发票一共开了多少张？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**证据不足**；题面只说法兰西的发票，原参考按customer.country却allowed允许两口径且原标签待确认。实际绑定invoice.billing_country=France、COUNT发票35，保存结果与客户所在地参考也35；该巧合不能证明两字段等价。正式系统正确性继续不能确定，先核地区口径。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS invoice_count FROM public.invoice i JOIN public.customer c ON i.customer_id = c.customer_id WHERE c.country = 'France';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "invoice_count"
    ],
    "rows": [
      [
        35
      ]
    ],
    "table": [
      {
        "invoice_count": 35
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"invoice\" WHERE \"billing_country\" = 'France'",
  "actual_final_table": [
    {
      "count": 35
    }
  ],
  "actual_answer": "查询结果：35。",
  "actual_nlu_bindings": [
    {
      "column": "invoice.billing_country",
      "operator": "=",
      "value": "France",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-99f7789e108299a0",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 6,
      "original": "法兰西共和国",
      "replacement": "France",
      "method": "exact",
      "evidence_ref": "a-99f7789e108299a0"
    }
  ],
  "actual_rewritten_question": "France的发票一共开了多少张？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "invoice"
    ],
    "actual_predicate_expressions": [
      "\"billing_country\" = 'France'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-14",
    "task": "01",
    "category": "alias",
    "scorable": false,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "actual": [
        [
          "invoice.billing_country",
          "=",
          "\"France\""
        ]
      ],
      "missing": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "extra": [
        [
          "invoice.billing_country",
          "=",
          "\"France\""
        ]
      ]
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
        "gold": {
          "ast": "SELECT COUNT(*) FROM invoice JOIN customer ON invoice.customer_id = customer.customer_id WHERE customer.country = 'France'",
          "predicates": {
            "customer.country = 'France'": 1,
            "invoice.customer_id = customer.customer_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer",
            "invoice"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM invoice WHERE invoice.billing_country = 'France'",
          "predicates": {
            "invoice.billing_country = 'France'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "invoice"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": null
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": null,
    "pending_annotation": true,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-14/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-14/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-14/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-14/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-14/turns/000/provider/daa83c5a36244f949063b0c2a91d8ec9.json](<../runtime_eval/runs/V2-001/cases/sp01-14/turns/000/provider/daa83c5a36244f949063b0c2a91d8ec9.json>)；SHA=f216a3db79248152bdc3a15aaa152a9b8d3dfd284ca6c0628cdba697b56d1c9a；trace核验=true；实际system字符=[1359]

仍需人工确认：确认题面所需的地区字段或澄清策略；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-15 · alias

原题：受保护AAC音频文件这种媒体格式有多少首曲目？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；已批准受保护AAC音频文件别名明确指media_type.name，实际绑定/改写Protected AAC audio file；track→media_type FK主键内连接COUNT曲目237，统计曲目粒度且NULL外键不误并入。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'Protected AAC audio file';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "track_count"
    ],
    "rows": [
      [
        237
      ]
    ],
    "table": [
      {
        "track_count": 237
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS track_count FROM \"public\".\"track\" AS t JOIN \"public\".\"media_type\" AS mt ON t.\"media_type_id\" = mt.\"media_type_id\" WHERE mt.\"name\" = 'Protected AAC audio file'",
  "actual_final_table": [
    {
      "track_count": 237
    }
  ],
  "actual_answer": "查询结果：237。",
  "actual_nlu_bindings": [
    {
      "column": "media_type.name",
      "operator": "=",
      "value": "Protected AAC audio file",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-bfc4b2a75ae6d393",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 10,
      "original": "受保护AAC音频文件",
      "replacement": "Protected AAC audio file",
      "method": "exact",
      "evidence_ref": "a-bfc4b2a75ae6d393"
    }
  ],
  "actual_rewritten_question": "Protected AAC audio file这种媒体格式有多少首曲目？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "media_type",
      "track"
    ],
    "actual_predicate_expressions": [
      "t.\"media_type_id\" = mt.\"media_type_id\"",
      "mt.\"name\" = 'Protected AAC audio file'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-15",
    "task": "01",
    "category": "alias",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "media_type.name",
          "=",
          "\"Protected AAC audio file\""
        ]
      ],
      "actual": [
        [
          "media_type.name",
          "=",
          "\"Protected AAC audio file\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM track JOIN media_type ON track.media_type_id = media_type.media_type_id WHERE media_type.name = 'Protected AAC audio file'",
          "predicates": {
            "media_type.name = 'Protected AAC audio file'": 1,
            "track.media_type_id = media_type.media_type_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "media_type",
            "track"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM track JOIN media_type ON track.media_type_id = media_type.media_type_id WHERE media_type.name = 'Protected AAC audio file'",
          "predicates": {
            "media_type.name = 'Protected AAC audio file'": 1,
            "track.media_type_id = media_type.media_type_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "media_type",
            "track"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-15/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-15/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-15/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-15/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-15/turns/000/provider/1ce3153289bc461695dfead1beddd75c.json](<../runtime_eval/runs/V2-001/cases/sp01-15/turns/000/provider/1ce3153289bc461695dfead1beddd75c.json>)；SHA=eaf124c9d9e5fd921bddb181ad563056f0d2bfb7e84aea43da4f50f712e3be0d；trace核验=true；实际system字符=[2195]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-16 · alias

原题：U2乐队一共有多少张专辑？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；已批准U2乐队别名实际绑定/改写。COUNT(*)在album→artist主键FK内连接与参考COUNT(DISTINCT album_id)等价，album_id非NULL唯一且艺术家连接多对一；结果10只是附加保存数据核验，非唯一语义依据。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(DISTINCT a.album_id) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'U2';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "album_count"
    ],
    "rows": [
      [
        10
      ]
    ],
    "table": [
      {
        "album_count": 10
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS album_count FROM \"public\".\"album\" AS a JOIN \"public\".\"artist\" AS ar ON a.\"artist_id\" = ar.\"artist_id\" WHERE ar.\"name\" = 'U2'",
  "actual_final_table": [
    {
      "album_count": 10
    }
  ],
  "actual_answer": "查询结果：10。",
  "actual_nlu_bindings": [
    {
      "column": "artist.name",
      "operator": "=",
      "value": "U2",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-a04cacbc074e2ac6",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 4,
      "original": "U2乐队",
      "replacement": "U2",
      "method": "exact",
      "evidence_ref": "a-a04cacbc074e2ac6"
    }
  ],
  "actual_rewritten_question": "U2一共有多少张专辑？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "album",
      "artist"
    ],
    "actual_predicate_expressions": [
      "a.\"artist_id\" = ar.\"artist_id\"",
      "ar.\"name\" = 'U2'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "PK_FK_count_equivalence": {
      "album_primary_key": [
        "album_id"
      ],
      "artist_primary_key": [
        "artist_id"
      ],
      "album_id_nullable": false,
      "album_foreign_keys": [
        {
          "columns": [
            "artist_id"
          ],
          "references": {
            "schema": "public",
            "table": "artist",
            "columns": [
              "artist_id"
            ]
          }
        }
      ],
      "reason": "PK uniqueness/nonNULL and FK many-to-one prove album COUNT(*),COUNT(album_id),COUNT(DISTINCT album_id) equivalence for these unchanged inner FK joins"
    }
  },
  "original_automatic_score": {
    "id": "sp01-16",
    "task": "01",
    "category": "alias",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "artist.name",
          "=",
          "\"U2\""
        ]
      ],
      "actual": [
        [
          "artist.name",
          "=",
          "\"U2\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": true,
        "gold": {
          "ast": "SELECT COUNT(DISTINCT album.album_id) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'U2'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'U2'": 1
          },
          "aggregates": [
            "COUNT(DISTINCT album.album_id)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'U2'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'U2'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": null
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": null,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "AI_pending"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-16/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-16/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-16/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-16/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-16/turns/000/provider/bf17a759563d4036814cc7bb6391f73b.json](<../runtime_eval/runs/V2-001/cases/sp01-16/turns/000/provider/bf17a759563d4036814cc7bb6391f73b.json>)；SHA=a4a1ae6d9a0c5597a1fdbfc9a89ec4b2e1d6a0e2a704c7def8f09c76cc00dd6a；trace核验=true；实际system字符=[2195]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-17 · typo

原题：Fracne 有多少客户？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；V2实际Fracne被SQL生成阶段改成France且COUNT结果5；NLU mentions/bindings/patches为空、intent.filters为空、rewritten_question=NULL。与04一致，仅查询在人工确认拼写意图后可通过；未证明候选裁决或显式绑定/改写，不把自动结果正确当整个专项①链完成。原V0对此给错误的历史意见保留，本次明确拆分查询与链路维度。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'France';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        5
      ]
    ],
    "table": [
      {
        "customer_count": 5
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'France'",
  "actual_final_table": [
    {
      "count": 5
    }
  ],
  "actual_answer": "查询结果：5。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'France'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "query_vs_binding_chain": {
      "France_SQL_and_saved5": true,
      "verified_NLU_binding_present": false,
      "explicit_rewrite_present": false,
      "pipeline_full_acceptance_not_proven": true
    }
  },
  "original_automatic_score": {
    "id": "sp01-17",
    "task": "01",
    "category": "typo",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "customer.country",
          "=",
          "\"France\""
        ]
      ],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'France'",
          "predicates": {
            "customer.country = 'France'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'France'",
          "predicates": {
            "customer.country = 'France'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-17/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-17/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-17/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-17/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-17/turns/000/provider/7055b04488134d068d18d38b7adf950b.json](<../runtime_eval/runs/V2-001/cases/sp01-17/turns/000/provider/7055b04488134d068d18d38b7adf950b.json>)；SHA=1d8a9bef988d3f5996573d7674a53f365a014ec0a10bcd912b5aac876ab6dba0；trace核验=true；实际system字符=[1359]

仍需人工确认：核对拼写候选接受规则及声明展示要求；不据此改自动分数；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-18 · typo

原题：Led Zepelin 有多少张专辑？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；V2实际专辑计数对象比V0提取artist_id有所改善，但name仍LOWER('Led Zepelin')而不是人工待确认的Led Zeppelin，无绑定/改写，3次跨表校验拒绝、table=NULL。没有取得参考14，不构成正确消歧。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(DISTINCT a.album_id) AS album_count FROM public.album a JOIN public.artist ar ON a.artist_id = ar.artist_id WHERE ar.name = 'Led Zeppelin';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "album_count"
    ],
    "rows": [
      [
        14
      ]
    ],
    "table": [
      {
        "album_count": 14
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "FAILED",
  "actual_final_sql": "SELECT COUNT(*) AS album_count FROM \"public\".\"artist\" AS ar JOIN \"public\".\"album\" AS a ON a.\"artist_id\" = ar.\"artist_id\" WHERE LOWER(ar.\"name\") = LOWER('Led Zepelin')",
  "actual_final_table": null,
  "actual_answer": "SQL 未通过校验：该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "album",
      "artist"
    ],
    "actual_predicate_expressions": [
      "a.\"artist_id\" = ar.\"artist_id\"",
      "LOWER(ar.\"name\") = LOWER('Led Zepelin')"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-18",
    "task": "01",
    "category": "typo",
    "scorable": true,
    "initial_status": "FAILED",
    "final_status": "FAILED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "artist.name",
          "=",
          "\"Led Zeppelin\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "artist.name",
          "=",
          "\"Led Zeppelin\""
        ]
      ],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
        "gold": {
          "ast": "SELECT COUNT(DISTINCT album.album_id) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'Led Zeppelin'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'Led Zeppelin'": 1
          },
          "aggregates": [
            "COUNT(DISTINCT album.album_id)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM artist JOIN album ON album.artist_id = artist.artist_id WHERE LOWER(artist.name) = LOWER('Led Zepelin')",
          "predicates": {
            "LOWER(artist.name) = LOWER('Led Zepelin')": 1,
            "album.artist_id = artist.artist_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": false,
        "reason": "No successful query result"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "api_failed",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-18/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-18/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-18/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-18/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-18/turns/000/provider/d7bf59840ec545c29255a2c83526f25f.json](<../runtime_eval/runs/V2-001/cases/sp01-18/turns/000/provider/d7bf59840ec545c29255a2c83526f25f.json>)；SHA=4dace57162bbc70b144b8d88d6d25575cb5207d56bb812f64cf220601c8770cb；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-18/turns/000/provider/4128e82039774fa18e2608e905d8fa36.json](<../runtime_eval/runs/V2-001/cases/sp01-18/turns/000/provider/4128e82039774fa18e2608e905d8fa36.json>)；SHA=94dbe2244608f0b22d6149dc04a129ca8c48aeb66ab449552984be2fac340721；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-18/turns/000/provider/17cbbab7f2884939a649fb5a84e050f7.json](<../runtime_eval/runs/V2-001/cases/sp01-18/turns/000/provider/17cbbab7f2884939a649fb5a84e050f7.json>)；SHA=82ae1b9e5066ba9b96c23b5fd6c6a81c56667c72d626f2ddadcf71a870f44d7d；trace核验=true；实际system字符=[1359]

仍需人工确认：确认拼写恢复策略，但当前对象/计数丢失有直接证据；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-19 · typo

原题：Canda 的客户有多少？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；实际有限候选fuzzy匹配Canda→Canada，绑定customer.country、patch及rewritten_question均保存；COUNT客户8。API答案单句8，但既有UI源码在答案前显示改写/patch，可说明更正；本条未新增浏览器验收，不能冒称实际截图已核。拼写解释仍为参考人审事项。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Canada';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        8
      ]
    ],
    "table": [
      {
        "customer_count": 8
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Canada'",
  "actual_final_table": [
    {
      "count": 8
    }
  ],
  "actual_answer": "查询结果：8。",
  "actual_nlu_bindings": [
    {
      "column": "customer.country",
      "operator": "=",
      "value": "Canada",
      "mention_id": "mention-1",
      "method": "fuzzy",
      "evidence_ref": "v-f357d4a9aa3228c9d69b",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 5,
      "original": "Canda",
      "replacement": "Canada",
      "method": "fuzzy",
      "evidence_ref": "v-f357d4a9aa3228c9d69b"
    }
  ],
  "actual_rewritten_question": "Canada 的客户有多少？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'Canada'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-19",
    "task": "01",
    "category": "typo",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"Canada\""
        ]
      ],
      "actual": [
        [
          "customer.country",
          "=",
          "\"Canada\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Canada'",
          "predicates": {
            "customer.country = 'Canada'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Canada'",
          "predicates": {
            "customer.country = 'Canada'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-19/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-19/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-19/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-19/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-19/turns/000/provider/df4ff6048fd4479aaed76d37f293c827.json](<../runtime_eval/runs/V2-001/cases/sp01-19/turns/000/provider/df4ff6048fd4479aaed76d37f293c827.json>)；SHA=af0fde4a15a9b5eb122bc567d9b475775a88a9f15ba3dca88d81df4f29c73017；trace核验=true；实际system字符=[1359]

仍需人工确认：确认拼写恢复的业务接受边界；若需界面逐题截图另执行独立开发验证；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-20 · typo

原题：MPEG adiou file 有多少首曲目？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；V2模型把MPEG adiou修成MPEG audio，但NLU绑定/patch为空。最终候选SQL为track.media_type_id=(SELECT媒体ID WHERE name正确 LIMIT1)，完整保存媒体事实显示仅一个MPEG audio ID，当前数据下与参考FK联表计数相符；此唯一性仅是实际快照事实，并无名称唯一约束。实际多表守卫拒绝，无执行3034，不能当通过。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS track_count FROM public.track t JOIN public.media_type mt ON t.media_type_id = mt.media_type_id WHERE mt.name = 'MPEG audio file';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "track_count"
    ],
    "rows": [
      [
        3034
      ]
    ],
    "table": [
      {
        "track_count": 3034
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "FAILED",
  "actual_final_sql": "SELECT COUNT(*) AS track_count FROM \"public\".\"track\" AS t WHERE t.\"media_type_id\" = (SELECT \"media_type_id\" FROM \"public\".\"media_type\" WHERE \"name\" = 'MPEG audio file' LIMIT 1)",
  "actual_final_table": null,
  "actual_answer": "SQL 未通过校验：该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "media_type",
      "track"
    ],
    "actual_predicate_expressions": [
      "t.\"media_type_id\" = (SELECT \"media_type_id\" FROM \"public\".\"media_type\" WHERE \"name\" = 'MPEG audio file' LIMIT 1)",
      "\"name\" = 'MPEG audio file'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "saved_complete_media_type_rows": [
      [
        1,
        "MPEG audio file"
      ],
      [
        2,
        "Protected AAC audio file"
      ],
      [
        3,
        "Protected MPEG-4 video file"
      ],
      [
        4,
        "Purchased AAC audio file"
      ],
      [
        5,
        "AAC audio file"
      ]
    ],
    "snapshot_unique_name_not_schema_unique_constraint": true
  },
  "original_automatic_score": {
    "id": "sp01-20",
    "task": "01",
    "category": "typo",
    "scorable": true,
    "initial_status": "FAILED",
    "final_status": "FAILED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "media_type.name",
          "=",
          "\"MPEG audio file\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "media_type.name",
          "=",
          "\"MPEG audio file\""
        ]
      ],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
        "gold": {
          "ast": "SELECT COUNT(*) FROM track JOIN media_type ON track.media_type_id = media_type.media_type_id WHERE media_type.name = 'MPEG audio file'",
          "predicates": {
            "media_type.name = 'MPEG audio file'": 1,
            "track.media_type_id = media_type.media_type_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "media_type",
            "track"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM track WHERE track.media_type_id = (SELECT media_type.media_type_id FROM media_type WHERE media_type.name = 'MPEG audio file' LIMIT 1)",
          "predicates": {
            "media_type.name = 'MPEG audio file'": 1,
            "track.media_type_id = (SELECT media_type.media_type_id FROM media_type WHERE media_type.name = 'MPEG audio file' LIMIT 1)": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "media_type",
            "track"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": false,
        "reason": "No successful query result"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "api_failed",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-20/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-20/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-20/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-20/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-20/turns/000/provider/5d6e3724ba374bb582c4bc15f5d7f7fd.json](<../runtime_eval/runs/V2-001/cases/sp01-20/turns/000/provider/5d6e3724ba374bb582c4bc15f5d7f7fd.json>)；SHA=5514cde49d46440d0d5a21f6b5a8aa0a8c5bc48151eb5223b5c8607f7dcee524；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-20/turns/000/provider/eb2d683f0f194163b94f408a873ea574.json](<../runtime_eval/runs/V2-001/cases/sp01-20/turns/000/provider/eb2d683f0f194163b94f408a873ea574.json>)；SHA=b07ebef11c5ff6c9341904bb99bfb0958f0f57be559411314957f18194d8461a；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-20/turns/000/provider/f06c1da75883470a886aaada023913c3.json](<../runtime_eval/runs/V2-001/cases/sp01-20/turns/000/provider/f06c1da75883470a886aaada023913c3.json>)；SHA=f1217eb11fa52b918db8009d0d2b7ba3645955a7169ea4a587def89907ed93f3；trace核验=true；实际system字符=[1359]

仍需人工确认：确认该拼写恢复可接受；区别候选SQL等价与实际系统失败；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-21 · pinyin

原题：Deguo 的客户有多少个？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；客户对象明确；Deguo由批准德国别名pinyin链绑定customer.country=Germany并改写，COUNT客户4；未把拼音当艺术家或跨到billing_country。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Germany';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        4
      ]
    ],
    "table": [
      {
        "customer_count": 4
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Germany'",
  "actual_final_table": [
    {
      "customer_count": 4
    }
  ],
  "actual_answer": "查询结果：4。",
  "actual_nlu_bindings": [
    {
      "column": "customer.country",
      "operator": "=",
      "value": "Germany",
      "mention_id": "mention-1",
      "method": "pinyin",
      "evidence_ref": "a-e4d835eae26ef07e",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 5,
      "original": "Deguo",
      "replacement": "Germany",
      "method": "pinyin",
      "evidence_ref": "a-e4d835eae26ef07e"
    }
  ],
  "actual_rewritten_question": "Germany 的客户有多少个？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'Germany'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-21",
    "task": "01",
    "category": "pinyin",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"Germany\""
        ]
      ],
      "actual": [
        [
          "customer.country",
          "=",
          "\"Germany\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Germany'",
          "predicates": {
            "customer.country = 'Germany'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Germany'",
          "predicates": {
            "customer.country = 'Germany'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-21/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-21/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-21/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-21/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-21/turns/000/provider/bee92369191e48e0b479bf6cb282d7d8.json](<../runtime_eval/runs/V2-001/cases/sp01-21/turns/000/provider/bee92369191e48e0b479bf6cb282d7d8.json>)；SHA=577fe6d2dde1e5563b389950ccce226cf5b3e0aff129b13b81f1902dba76d778；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-22 · pinyin

原题：Gudian 这个流派的曲目有多少首？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；已批准古典→Classical及真实genre事实可支持pinyin目标，但V2实际NLU无mentions/bindings，SQL仍genre.name='Gudian'且跨表守卫FAILED。未得74、未改写正确值，不能因SQL形式COUNT/FK正确就通过。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS track_count FROM public.track t JOIN public.genre g ON t.genre_id = g.genre_id WHERE g.name = 'Classical';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "track_count"
    ],
    "rows": [
      [
        74
      ]
    ],
    "table": [
      {
        "track_count": 74
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "FAILED",
  "actual_final_sql": "SELECT COUNT(*) AS track_count FROM \"public\".\"track\" AS t JOIN \"public\".\"genre\" AS g ON t.\"genre_id\" = g.\"genre_id\" WHERE g.\"name\" = 'Gudian'",
  "actual_final_table": null,
  "actual_answer": "SQL 未通过校验：该查询没有跨表业务要求，生成 SQL 不得额外引入其它来源。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "genre",
      "track"
    ],
    "actual_predicate_expressions": [
      "t.\"genre_id\" = g.\"genre_id\"",
      "g.\"name\" = 'Gudian'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-22",
    "task": "01",
    "category": "pinyin",
    "scorable": true,
    "initial_status": "FAILED",
    "final_status": "FAILED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "genre.name",
          "=",
          "\"Classical\""
        ]
      ],
      "actual": [],
      "missing": [
        [
          "genre.name",
          "=",
          "\"Classical\""
        ]
      ],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
        "gold": {
          "ast": "SELECT COUNT(*) FROM track JOIN genre ON track.genre_id = genre.genre_id WHERE genre.name = 'Classical'",
          "predicates": {
            "genre.name = 'Classical'": 1,
            "track.genre_id = genre.genre_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "genre",
            "track"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM track JOIN genre ON track.genre_id = genre.genre_id WHERE genre.name = 'Gudian'",
          "predicates": {
            "genre.name = 'Gudian'": 1,
            "track.genre_id = genre.genre_id": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "genre",
            "track"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": false,
        "reason": "No successful query result"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "api_failed",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-22/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-22/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-22/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-22/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-22/turns/000/provider/181d26b542b84c9388e67b3788a6fab6.json](<../runtime_eval/runs/V2-001/cases/sp01-22/turns/000/provider/181d26b542b84c9388e67b3788a6fab6.json>)；SHA=40d706c1664f8afaebfdbf108849e43a76800ea42fff2136385891b23eb9313d；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-22/turns/000/provider/52e41b2ddecb4e588d7d7ae163b64e10.json](<../runtime_eval/runs/V2-001/cases/sp01-22/turns/000/provider/52e41b2ddecb4e588d7d7ae163b64e10.json>)；SHA=57604208837ebb6fee9ce0ea43b0ee180dba0ee3d6b113177726e48e432c69a6；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-22/turns/000/provider/b62ec312b08a46f295230a0f6fe64315.json](<../runtime_eval/runs/V2-001/cases/sp01-22/turns/000/provider/b62ec312b08a46f295230a0f6fe64315.json>)；SHA=658d441db4c6cc239229480a4e5528689c174a2b146fdc4307a3a815431e1972；trace核验=true；实际system字符=[1359]

仍需人工确认：人工可核对拼音大小写/分词接受边界；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-23 · mixed_language

原题：Canada 那边一共有多少 customers？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；中英混写仍明确Canada和customers，实际exact customer.country绑定、客户COUNT8，无不相关期间/发票字段。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Canada';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        8
      ]
    ],
    "table": [
      {
        "customer_count": 8
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"customer\" WHERE \"country\" = 'Canada'",
  "actual_final_table": [
    {
      "count": 8
    }
  ],
  "actual_answer": "查询结果：8。",
  "actual_nlu_bindings": [
    {
      "column": "customer.country",
      "operator": "=",
      "value": "Canada",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "v-f357d4a9aa3228c9d69b",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'Canada'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-23",
    "task": "01",
    "category": "mixed_language",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"Canada\""
        ]
      ],
      "actual": [
        [
          "customer.country",
          "=",
          "\"Canada\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Canada'",
          "predicates": {
            "customer.country = 'Canada'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Canada'",
          "predicates": {
            "customer.country = 'Canada'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-23/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-23/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-23/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-23/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-23/turns/000/provider/b2b466867f874f45bb9b48f923e9c332.json](<../runtime_eval/runs/V2-001/cases/sp01-23/turns/000/provider/b2b466867f874f45bb9b48f923e9c332.json>)；SHA=a643cbaaa31b5f1f94c6702a384985c111ef7b89e8e39ddffc66f33b0daacea1；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-24 · mixed_language

原题：Iron Maiden 这个 artist 有多少 albums？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；artist/albums对象明确，actual artist.name=Iron Maiden绑定正确，artist→album主键FK内连接COUNT(album_id)。album_id非NULL，COUNT(album_id)等同COUNT(*)，连接顺序不改变多对一粒度，保存结果21。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS album_count FROM public.album al JOIN public.artist ar ON al.artist_id = ar.artist_id WHERE ar.name = 'Iron Maiden';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "album_count"
    ],
    "rows": [
      [
        21
      ]
    ],
    "table": [
      {
        "album_count": 21
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(a.\"album_id\") AS album_count FROM \"public\".\"artist\" AS ar JOIN \"public\".\"album\" AS a ON a.\"artist_id\" = ar.\"artist_id\" WHERE ar.\"name\" = 'Iron Maiden'",
  "actual_final_table": [
    {
      "album_count": 21
    }
  ],
  "actual_answer": "查询结果：21。",
  "actual_nlu_bindings": [
    {
      "column": "artist.name",
      "operator": "=",
      "value": "Iron Maiden",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "v-26903b3204f3eef20547",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "album",
      "artist"
    ],
    "actual_predicate_expressions": [
      "a.\"artist_id\" = ar.\"artist_id\"",
      "ar.\"name\" = 'Iron Maiden'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(a.\"album_id\")"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "PK_FK_count_equivalence": {
      "album_primary_key": [
        "album_id"
      ],
      "artist_primary_key": [
        "artist_id"
      ],
      "album_id_nullable": false,
      "album_foreign_keys": [
        {
          "columns": [
            "artist_id"
          ],
          "references": {
            "schema": "public",
            "table": "artist",
            "columns": [
              "artist_id"
            ]
          }
        }
      ],
      "reason": "PK uniqueness/nonNULL and FK many-to-one prove album COUNT(*),COUNT(album_id),COUNT(DISTINCT album_id) equivalence for these unchanged inner FK joins"
    }
  },
  "original_automatic_score": {
    "id": "sp01-24",
    "task": "01",
    "category": "mixed_language",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "artist.name",
          "=",
          "\"Iron Maiden\""
        ]
      ],
      "actual": [
        [
          "artist.name",
          "=",
          "\"Iron Maiden\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": true,
        "gold": {
          "ast": "SELECT COUNT(*) FROM album JOIN artist ON album.artist_id = artist.artist_id WHERE artist.name = 'Iron Maiden'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'Iron Maiden'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(album.album_id) FROM artist JOIN album ON album.artist_id = artist.artist_id WHERE artist.name = 'Iron Maiden'",
          "predicates": {
            "album.artist_id = artist.artist_id": 1,
            "artist.name = 'Iron Maiden'": 1
          },
          "aggregates": [
            "COUNT(album.album_id)"
          ],
          "tables": [
            "album",
            "artist"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": null
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": null,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "AI_pending"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-24/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-24/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-24/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-24/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-24/turns/000/provider/a6656ae72faa467c88ba802399416bd3.json](<../runtime_eval/runs/V2-001/cases/sp01-24/turns/000/provider/a6656ae72faa467c88ba802399416bd3.json>)；SHA=6833ee1804f836608d2867d6c7362d05cb1fcb0155a62ee7d2a5b79ef3e3a368；trace核验=true；实际system字符=[2195]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-25 · colloquial

原题：意大利那边的发票总共开了多少钱？
参考判断：AI发现错误；保留V0冻结参考意见与新争议。
系统判断：**证据不足**；原参考声称意大利发票默认按客户所在地，已确认规则没有这种默认。V2实际按invoice.billing_country=Italy SUM(total)得到37.62，参考customer.country也37.62只为本快照巧合，不是语义证明。保留参考错误与人审，正式系统评分不能确定，不为系统改参考。
```json
{
  "gold_sql_unchanged": "SELECT SUM(i.total) AS revenue FROM public.invoice i JOIN public.customer c ON i.customer_id = c.customer_id WHERE c.country = 'Italy';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "revenue"
    ],
    "rows": [
      [
        "37.62"
      ]
    ],
    "table": [
      {
        "revenue": "37.62"
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT SUM(\"total\") AS total_amount FROM \"public\".\"invoice\" WHERE \"billing_country\" = 'Italy'",
  "actual_final_table": [
    {
      "total_amount": "37.62"
    }
  ],
  "actual_answer": "查询结果：37.62。",
  "actual_nlu_bindings": [
    {
      "column": "invoice.billing_country",
      "operator": "=",
      "value": "Italy",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-97f75d30b3bcab32",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 3,
      "original": "意大利",
      "replacement": "Italy",
      "method": "exact",
      "evidence_ref": "a-97f75d30b3bcab32"
    }
  ],
  "actual_rewritten_question": "Italy那边的发票总共开了多少钱？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "invoice"
    ],
    "actual_predicate_expressions": [
      "\"billing_country\" = 'Italy'"
    ],
    "actual_aggregate_expressions": [
      "SUM(\"total\")"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-25",
    "task": "01",
    "category": "colloquial",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"Italy\""
        ]
      ],
      "actual": [
        [
          "invoice.billing_country",
          "=",
          "\"Italy\""
        ]
      ],
      "missing": [
        [
          "customer.country",
          "=",
          "\"Italy\""
        ]
      ],
      "extra": [
        [
          "invoice.billing_country",
          "=",
          "\"Italy\""
        ]
      ]
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
        "gold": {
          "ast": "SELECT SUM(invoice.total) FROM invoice JOIN customer ON invoice.customer_id = customer.customer_id WHERE customer.country = 'Italy'",
          "predicates": {
            "customer.country = 'Italy'": 1,
            "invoice.customer_id = customer.customer_id": 1
          },
          "aggregates": [
            "SUM(invoice.total)"
          ],
          "tables": [
            "customer",
            "invoice"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT SUM(invoice.total) FROM invoice WHERE invoice.billing_country = 'Italy'",
          "predicates": {
            "invoice.billing_country = 'Italy'": 1
          },
          "aggregates": [
            "SUM(invoice.total)"
          ],
          "tables": [
            "invoice"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": null
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": null,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": null,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "AI_pending"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-25/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-25/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-25/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-25/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-25/turns/000/provider/713e43dbe3b64a3ca40098adeb839fca.json](<../runtime_eval/runs/V2-001/cases/sp01-25/turns/000/provider/713e43dbe3b64a3ca40098adeb839fca.json>)；SHA=5f85d03b99581762b5d85520faffcc71b1be21723973a2e7343d0f83a4d50664；trace核验=true；实际system字符=[1359]

仍需人工确认：核对参考声称的客户所在地默认依据；目前禁止自动补该默认；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-26 · colloquial

原题：加拿大那边现在有多少客户？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；加拿大在客户对象下已批准country=Canada别名绑定并改写，客户COUNT8；‘现在’只指数据快照，没有虚构客户时间字段。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Canada';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        8
      ]
    ],
    "table": [
      {
        "customer_count": 8
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Canada'",
  "actual_final_table": [
    {
      "customer_count": 8
    }
  ],
  "actual_answer": "查询结果：8。",
  "actual_nlu_bindings": [
    {
      "column": "customer.country",
      "operator": "=",
      "value": "Canada",
      "mention_id": "mention-1",
      "method": "exact",
      "evidence_ref": "a-3cc0be84e1794908",
      "source": "verified_value_index"
    }
  ],
  "actual_nlu_patches": [
    {
      "start": 0,
      "end": 3,
      "original": "加拿大",
      "replacement": "Canada",
      "method": "exact",
      "evidence_ref": "a-3cc0be84e1794908"
    }
  ],
  "actual_rewritten_question": "Canada那边现在有多少客户？",
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'Canada'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-26",
    "task": "01",
    "category": "colloquial",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "exact_column_operator_value",
      "expected": [
        [
          "customer.country",
          "=",
          "\"Canada\""
        ]
      ],
      "actual": [
        [
          "customer.country",
          "=",
          "\"Canada\""
        ]
      ],
      "missing": [],
      "extra": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Canada'",
          "predicates": {
            "customer.country = 'Canada'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Canada'",
          "predicates": {
            "customer.country = 'Canada'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-26/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-26/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-26/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-26/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-26/turns/000/provider/217fc0748df848b9b1860ac3deb1aa34.json](<../runtime_eval/runs/V2-001/cases/sp01-26/turns/000/provider/217fc0748df848b9b1860ac3deb1aa34.json>)；SHA=f8168d9440179ccaf182c8c8d45a13634f9fa3ca6a50ae9a817002a0ede1342b；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-27 · multi_candidate

原题：Chinook 里摇滚曲目有多少首？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；摇滚为已批准候选关系；实际L2完整保留Rock/Rock And Roll两genre选项，无自动绑定、无SQL。原冻结binding合同用一个IN列表，而候选观察是两个等值项，可能导致原scorer失败；保留原分，不以修改合同让系统通过。这里只通过初始澄清行为，不声称后续SQL成功。
```json
{
  "gold_sql_unchanged": null,
  "gold_result_from_preparation_unchanged": null,
  "actual_final_status": "NEEDS_CLARIFICATION",
  "actual_final_sql": null,
  "actual_final_table": null,
  "actual_answer": "“摇滚”具体指哪个对象？",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": [
    {
      "id": "value:issue-fbaa1127c30ea0e7:v-5abaeb142337ce5b27ed",
      "label": "Rock（genre.name）"
    },
    {
      "id": "value:issue-fbaa1127c30ea0e7:v-10facd793602b59518e7",
      "label": "Rock And Roll（genre.name）"
    }
  ],
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": false,
    "no_new_sql_execution": true,
    "candidate_only_gate": {
      "level": "L2",
      "options": [
        {
          "id": "value:issue-fbaa1127c30ea0e7:v-5abaeb142337ce5b27ed",
          "label": "Rock（genre.name）"
        },
        {
          "id": "value:issue-fbaa1127c30ea0e7:v-10facd793602b59518e7",
          "label": "Rock And Roll（genre.name）"
        }
      ],
      "no_auto_filters": true,
      "no_SQL_executed": true
    }
  },
  "original_automatic_score": {
    "id": "sp01-27",
    "task": "01",
    "category": "multi_candidate",
    "scorable": true,
    "initial_status": "NEEDS_CLARIFICATION",
    "final_status": "NEEDS_CLARIFICATION",
    "observed_initial_level": "L2",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "candidate_preservation",
      "expected": [
        [
          "genre.name",
          "in",
          "[\"Rock\", \"Rock And Roll\"]"
        ]
      ],
      "retained": [
        [
          "genre.name",
          "=",
          "\"Rock And Roll\""
        ],
        [
          "genre.name",
          "=",
          "\"Rock\""
        ]
      ],
      "bound": []
    },
    "query": {
      "complete": false,
      "semantic_preservation": {
        "correct": false,
        "reason": "Preserved candidate-only clarification contract"
      },
      "result": {
        "correct": null,
        "reason": "Initial clarification has no unique gold query"
      }
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": false,
    "overcorrection": true,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "candidate_only_clarification",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-27/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-27/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-27/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-27/turns/000/response.raw.json>)

仍需人工确认：确认候选集合标准表示及下轮评分器版本；本轮只附独立AI意见；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-28 · multi_candidate

原题：Chinook 里金属流派的曲目有多少首？
参考判断：AI发现错误；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；原题明确流派；参考把Metallica艺术家和Heavy Metal泛近义关系列入，原标签已排除且参考依据错保留。V2实际只给已批准candidate-only的genre Metal，L2不自动绑定、不出现pending Metallica，不猜艺术家。该候选确认行为合理；是否还应有Heavy Metal候选仍需人工，当前仅条件通过。
```json
{
  "gold_sql_unchanged": null,
  "gold_result_from_preparation_unchanged": null,
  "actual_final_status": "NEEDS_CLARIFICATION",
  "actual_final_sql": null,
  "actual_final_table": null,
  "actual_answer": "“金属”具体指哪个对象？",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": [
    {
      "id": "value:issue-e5d51e4bda1a9a15:v-bf1c51869eccaa9deddc",
      "label": "Metal（genre.name）"
    }
  ],
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": false,
    "no_new_sql_execution": true,
    "candidate_only_gate": {
      "level": "L2",
      "options": [
        {
          "id": "value:issue-e5d51e4bda1a9a15:v-bf1c51869eccaa9deddc",
          "label": "Metal（genre.name）"
        }
      ],
      "no_auto_filters": true,
      "no_SQL_executed": true
    }
  },
  "original_automatic_score": {
    "id": "sp01-28",
    "task": "01",
    "category": "multi_candidate",
    "scorable": false,
    "initial_status": "NEEDS_CLARIFICATION",
    "final_status": "NEEDS_CLARIFICATION",
    "observed_initial_level": "L2",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": false,
      "mode": "candidate_preservation",
      "expected": [
        [
          "artist.name",
          "=",
          "\"Metallica\""
        ],
        [
          "genre.name",
          "in",
          "[\"Metal\", \"Heavy Metal\"]"
        ]
      ],
      "retained": [
        [
          "genre.name",
          "=",
          "\"Metal\""
        ]
      ],
      "bound": []
    },
    "query": {
      "complete": false,
      "semantic_preservation": {
        "correct": false,
        "reason": "Preserved candidate-only clarification contract"
      },
      "result": {
        "correct": null,
        "reason": "Initial clarification has no unique gold query"
      }
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": false,
    "overcorrection": true,
    "l1_default_switch_behavior": null,
    "automatic_complete": null,
    "pending_annotation": true,
    "outcome": "candidate_only_clarification",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-28/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-28/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-28/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-28/turns/000/response.raw.json>)

仍需人工确认：拒绝未经批准的Metallica artist候选；确认Heavy Metal是否有获准关系；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-29 · explicit_absent

原题：查一下 customer.country='Atlantis' 的客户数量；如果数据库没有这个国家，就按这个字面值查，直接报告没有记录。
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；题面显式customer.country='Atlantis'并要求原字面查询。实际SQL原字面COUNT0，已保存完整countries中无Atlantis，未换成相似国家；COUNT单聚合行0是SUCCEEDED，不是空表或NULL。但answer只‘查询结果：0’，未明确说‘没有记录’，需人工确认说明措辞是否达要求；literal未入已验证绑定不能冒称实体绑定成功。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS customer_count FROM public.customer WHERE country = 'Atlantis';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "customer_count"
    ],
    "rows": [
      [
        0
      ]
    ],
    "table": [
      {
        "customer_count": 0
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'Atlantis'",
  "actual_final_table": [
    {
      "customer_count": 0
    }
  ],
  "actual_answer": "查询结果：0。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "customer"
    ],
    "actual_predicate_expressions": [
      "\"country\" = 'Atlantis'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true
  },
  "original_automatic_score": {
    "id": "sp01-29",
    "task": "01",
    "category": "explicit_absent",
    "scorable": true,
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": true,
      "mode": "unknown_literal_sql_contract",
      "expected": [
        [
          "customer.country",
          "=",
          "\"Atlantis\""
        ]
      ],
      "actual": []
    },
    "query": {
      "semantic_preservation": {
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
        "gold": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Atlantis'",
          "predicates": {
            "customer.country = 'Atlantis'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM customer WHERE customer.country = 'Atlantis'",
          "predicates": {
            "customer.country = 'Atlantis'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "customer"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": true,
        "matched": true,
        "reason": "equal",
        "column_mapping": [
          0
        ],
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
      },
      "complete": true
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": true,
    "overcorrection": false,
    "l1_default_switch_behavior": null,
    "automatic_complete": true,
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-29/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-29/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-29/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-29/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-29/turns/000/provider/39479176d1d9426a9304ea34d9610f9a.json](<../runtime_eval/runs/V2-001/cases/sp01-29/turns/000/provider/39479176d1d9426a9304ea34d9610f9a.json>)；SHA=abb11dc24b854c1a1b603f458d1bcb616b7a09b6e1ce49c79259e96bc540011f；trace核验=true；实际system字符=[1359]

仍需人工确认：确认COUNT0文字是否足以满足报告没有记录要求，或应明确补一句；本轮不改代码；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-30 · explicit_absent

原题：统计 invoice_date 在 2030-01-01 到 2030-12-31（左闭右开）之间的发票张数；如果那段时间没有发票，就按这个时间范围查询并报告没有记录。
参考判断：AI发现错误；保留V0冻结参考意见与新争议。
系统判断：**证据不足**；原题已明确[2030-01-01,2030-12-31)却参考写<2031-01-01，V0已发现参考边界错误保留；正式按该坏参考不能决定系统评分。V2新增可直接核对的错误行为：把‘之间’识别为invoice.billing_country模糊mention，候选为Argentina/Australia/Austria/Belgium/Brazil并L2询问，用户日期题无国家要求，未SQL。单列无依据追问，不把该行为冒充正确日期保留，也不改原gold/controller。
```json
{
  "gold_sql_unchanged": "SELECT COUNT(*) AS invoice_count FROM public.invoice WHERE invoice_date >= DATE '2030-01-01' AND invoice_date < DATE '2031-01-01';",
  "gold_result_from_preparation_unchanged": {
    "columns": [
      "invoice_count"
    ],
    "rows": [
      [
        0
      ]
    ],
    "table": [
      {
        "invoice_count": 0
      }
    ],
    "row_count": 1,
    "truncated": false
  },
  "actual_final_status": "NEEDS_CLARIFICATION",
  "actual_final_sql": null,
  "actual_final_table": null,
  "actual_answer": "“之间”具体指哪个对象？",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": [
    {
      "id": "value:issue-85e24ea7ac8016e9:v-be5c0e3f456509e86b50",
      "label": "Argentina（invoice.billing_country）"
    },
    {
      "id": "value:issue-85e24ea7ac8016e9:v-30a35165311e0978a54c",
      "label": "Australia（invoice.billing_country）"
    },
    {
      "id": "value:issue-85e24ea7ac8016e9:v-36b46ab9d6d2427d5c8f",
      "label": "Austria（invoice.billing_country）"
    },
    {
      "id": "value:issue-85e24ea7ac8016e9:v-a1e7e7214229ebf9909b",
      "label": "Belgium（invoice.billing_country）"
    },
    {
      "id": "value:issue-85e24ea7ac8016e9:v-035a5fa9bd5fc4b4175e",
      "label": "Brazil（invoice.billing_country）"
    }
  ],
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": false,
    "no_new_sql_execution": true,
    "direct_user_condition_observation": {
      "user_lower_bound": "2030-01-01",
      "user_exclusive_upper_bound": "2030-12-31",
      "frozen_gold_exclusive_upper_bound": "2031-01-01",
      "reference_boundary_matches_user": false,
      "actual_country_clarification_has_no_basis_in_question": true,
      "actual_SQL_exclusive_upper_bound": null,
      "actual_SQL_matches_user_explicit_exclusive_upper_bound": "未执行SQL",
      "actual_mention": [
        "之间"
      ],
      "observed_dimension_verdict": "AI发现错误",
      "formal_system_scoring_under_wrong_reference": "暂不能确定；保留原冻结自动评分"
    }
  },
  "original_automatic_score": {
    "id": "sp01-30",
    "task": "01",
    "category": "explicit_absent",
    "scorable": true,
    "initial_status": "NEEDS_CLARIFICATION",
    "final_status": "NEEDS_CLARIFICATION",
    "observed_initial_level": "L2",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": null,
      "mode": "unknown_literal_sql_contract",
      "expected": [],
      "actual": []
    },
    "query": {
      "semantic_preservation": {
        "correct": false,
        "status": "failed",
        "reason": "No actual SQL"
      },
      "result": {
        "correct": false,
        "reason": "No successful query result"
      },
      "complete": false
    },
    "post_completion": [],
    "necessary_clarification_recall": null,
    "false_clarification": null,
    "clarification_effectiveness": null,
    "condition_preservation": false,
    "overcorrection": null,
    "l1_default_switch_behavior": null,
    "automatic_complete": false,
    "pending_annotation": false,
    "outcome": "controller_unanswered",
    "controller_events": [
      {
        "after_turn": 0,
        "outcome": "controller_unanswered",
        "request": null,
        "asked_key": null,
        "supplement_key": null,
        "reason": "Unknown/unsupported asks, no allowed supplement, or a repeated unresolved key"
      }
    ],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-30/checkpoint.json](<../runtime_eval/runs/V2-001/cases/sp01-30/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-30/turns/000/response.raw.json](<../runtime_eval/runs/V2-001/cases/sp01-30/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-30/turns/000/provider/82e7d7cedbd04de5b00f79ae96c0a1e1.json](<../runtime_eval/runs/V2-001/cases/sp01-30/turns/000/provider/82e7d7cedbd04de5b00f79ae96c0a1e1.json>)；SHA=9eb9b8b151248f84d80c12aead5eee19a3f08ebf832c001a4a5dd872dda964a0；trace核验=true；实际system字符=[1203]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V2-001/cases/sp01-30/turns/000/provider/ea2bf027b3364aa6a4d4299a465a4701.json](<../runtime_eval/runs/V2-001/cases/sp01-30/turns/000/provider/ea2bf027b3364aa6a4d4299a465a4701.json>)；SHA=fb9f53adf8ae62869d95740e796c0b45dc22542940d7c20b7a06abe452434618；trace核验=true；实际system字符=[4249]

仍需人工确认：优先确认用户原句是否本意整年，或必须保持12/31左闭右开；另存修订版只在人工决定后实施；本轮逐条AI意见不代替人审；V2原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## 原材料与限制

- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](<../data/cases-v6-reviewed.jsonl>)；SHA=42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1
- [eval/experiments/after_d2_01_03/reports/v0-task01-full-review.json](<v0-task01-full-review.json>)；SHA=6f1a1cef42c692b7930f06fc334b08aeecee94b458319ef1584544e8cbe86a13
- [data/catalog/chinook.yaml](<../../../../data/catalog/chinook.yaml>)；SHA=4d97a3f7fdfd0c684b544f162e20d2253c4f9c0cd572ba1fcaf40fe439a391b8
- [data/rules/metric_definitions.json](<../../../../data/rules/metric_definitions.json>)；SHA=2a0df8d29a4fb5401fd0a5b33a0f44932e00ab005bc674eaaa8b8a33f1df5efc
- [data/aliases/aliases-d2-reviewed.csv](<../../../../data/aliases/aliases-d2-reviewed.csv>)；SHA=aa699e8ef59f5185a0626ed2a9aefb36a1e292bfa2e3c0efd4b0ba5b1ddaef04
- [eval/experiments/after_d2_01_03/materials/readonly_live_facts.json](<../materials/readonly_live_facts.json>)；SHA=391487ffea9c12f21f5444369dd2b87b48897ac363a032a6ea107e5507df7b8f
- [eval/experiments/after_d2_01_03/runtime_eval/V2-code-snapshot.json](<../runtime_eval/V2-code-snapshot.json>)；SHA=536a8754beed70fddcc1aa05dc0a5188684568cb6759dd55573eebd2cbe868da
- [qa_agent/pipeline.py](<../../../../qa_agent/pipeline.py>)；SHA=ef083f1af00331c8b22cf14788a134d5fb95c6af5decefe6594e811ac4c0a407
- [qa_agent/sql/generator.py](<../../../../qa_agent/sql/generator.py>)；SHA=3bfe719356bca0a4d9c5fc28a94c9a03fdfb175598c96507c643da04bde99bbd
- [ui/app.py](<../../../../ui/app.py>)；SHA=9dd56378c112f5b3b9c4058368ccfc8e8e602e5549e029459e0ea765dd1855e3
- V2逐项AI预审意见分布不是新通过率；正式自动结果沿用原scores.json。
- 原参考争议保留；结果相同不证明地区/时间含义正确。
- candidate_only只验证初始澄清，不伪称续答/SQL成功；未新增逐题浏览器测试。
- 04/17统一按查询与绑定链分别判断，原V0不同意见不覆盖。
- 30坏参考导致正式判断暂不能确定；V1实际日期上界扩大／V2实际无依据国家追问各自另列观察。
