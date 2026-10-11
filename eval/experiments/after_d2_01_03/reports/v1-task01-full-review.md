# V1专项①全部30条实际回答AI预审

状态：FINAL_ACTUAL_V1_REVIEW；全部人工仍pending。

原固定自动结果：14/26
原固定评分文件：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001-scores.json](<../runtime_eval/runs/V1-001-scores.json>)
实际读取30原始响应、provider 44份；本次0API/0模型/0SQL。
参考AI分布：{"AI建议通过": 16, "AI建议有条件通过": 10, "AI发现错误": 4}
系统AI分布：{"AI建议通过": 14, "AI建议有条件通过": 7, "AI发现错误": 5, "证据不足": 4}；AI分布不是重计成绩。

## sp01-01 · standard

原题：How many customers are from France?
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；customers明确客户对象；真实France值按customer.country等值COUNT(*)，客户记录粒度、NULL过滤和无期间条件均正确。V1实际绑定France、SQL和保存结果5一致，无改口径。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-01/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-01/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-01/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-01/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-01/turns/000/provider/54c6a9769c1c4f44ba51878c0f35ba74.json](<../runtime_eval/runs/V1-001/cases/sp01-01/turns/000/provider/54c6a9769c1c4f44ba51878c0f35ba74.json>)；SHA=64238bc6fd7bff5d530181410ede4c1f38020b8af84037f926d0b24e127ccf6a；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-02 · alias

原题：Iron Maiden乐队一共有多少张专辑？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；V1实际已批准Iron Maiden乐队绑定/改写，album→artist按真实artist_id FK内连接、name等值COUNT(*)与参考相同；21附加核对保存数据，不用相同结果替代对象/连接粒度证明。
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
  "actual_final_sql": "SELECT COUNT(*) AS album_count FROM \"public\".\"album\" AS a JOIN \"public\".\"artist\" AS ar ON ar.\"artist_id\" = a.\"artist_id\" WHERE ar.\"name\" = 'Iron Maiden'",
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
      "ar.\"artist_id\" = a.\"artist_id\"",
      "ar.\"name\" = 'Iron Maiden'"
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
        "predicate_match": false,
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
          "ast": "SELECT COUNT(*) FROM album JOIN artist ON artist.artist_id = album.artist_id WHERE artist.name = 'Iron Maiden'",
          "predicates": {
            "artist.artist_id = album.artist_id": 1,
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-02/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-02/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-02/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-02/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-02/turns/000/provider/0bc9c6849e7e406f97944e3cc627ba4e.json](<../runtime_eval/runs/V1-001/cases/sp01-02/turns/000/provider/0bc9c6849e7e406f97944e3cc627ba4e.json>)；SHA=b004ff0a855b9a7d5ed580c708393ed6e11cfbfc749718ebaf41c5c7a5270771；trace核验=true；实际system字符=[2195]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
  "actual_final_sql": "SELECT SUM(\"total\") AS total_amount FROM \"public\".\"invoice\" WHERE \"billing_country\" = 'Germany'",
  "actual_final_table": [
    {
      "total_amount": "156.48"
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-03/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-03/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-03/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-03/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-03/turns/000/provider/4617ec8fe12f492096fd66a85835b57b.json](<../runtime_eval/runs/V1-001/cases/sp01-03/turns/000/provider/4617ec8fe12f492096fd66a85835b57b.json>)；SHA=9fe2b27769327454c7fcc988161a3dd4d705f7ee94a70ce8c27bf4e8ace1a8f6；trace核验=true；实际system字符=[1359]

仍需人工确认：核对发票+国名这一语境能否作为账单国家的获准字段限定；与12/14/25保持一致；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
  "actual_final_sql": "SELECT COUNT(*) AS customer_count FROM \"public\".\"customer\" WHERE \"country\" = 'France'",
  "actual_final_table": [
    {
      "customer_count": 5
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-04/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-04/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-04/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-04/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-04/turns/000/provider/f736f71215f545cb98858a462f2b4c4e.json](<../runtime_eval/runs/V1-001/cases/sp01-04/turns/000/provider/f736f71215f545cb98858a462f2b4c4e.json>)；SHA=a2a9e8d6a07db48a708612aa8d64bd40c87fd10afcce47458621a5976398fb39；trace核验=true；实际system字符=[1359]

仍需人工确认：确认字面拼写恢复策略；NLU/声明缺项不标完整链路通过；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-05 · typo

原题：Metallcia 有多少张专辑？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；V1实际前两次SQL按artist.name='Metallcia'经album FK联表，跨表校验拒绝；第三次技术修复却改成album.title='Metallcia'单表COUNT并执行0。用户未确认把艺术家换为专辑标题，修复改变业务条件来源且仍无拼写纠正/绑定/改写。在人工确认Metallica拼写意图后该结果也不满足参考10；不能用SQL终于能执行宣称修复成功。
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
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"album\" WHERE \"title\" = 'Metallcia'",
  "actual_final_table": [
    {
      "count": 0
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
      "album"
    ],
    "actual_predicate_expressions": [
      "\"title\" = 'Metallcia'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "technical_repair_business_predicate_changed": {
      "before": "artist.name",
      "after": "album.title",
      "user_confirmed_field_change": false,
      "actual_saved_result": 0,
      "is_successful_execution_not_semantic_success": true
    }
  },
  "original_automatic_score": {
    "id": "sp01-05",
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
          "ast": "SELECT COUNT(*) FROM album WHERE album.title = 'Metallcia'",
          "predicates": {
            "album.title = 'Metallcia'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": false,
        "matched": false,
        "reason": "column_values_mismatch",
        "column_mapping": null,
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
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
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-05/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-05/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-05/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-05/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-05/turns/000/provider/9a68401f04fd4ab9be2787950a9d6d90.json](<../runtime_eval/runs/V1-001/cases/sp01-05/turns/000/provider/9a68401f04fd4ab9be2787950a9d6d90.json>)；SHA=19cd273f30063000d3ba214dfb9654912140188a60689fe1852234673268c562；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-05/turns/000/provider/55afb097e73f453cb07b62114595658d.json](<../runtime_eval/runs/V1-001/cases/sp01-05/turns/000/provider/55afb097e73f453cb07b62114595658d.json>)；SHA=561a4da075b05e1307f2900f3ac064901a629a98d51f0fa5f56af96d1ab5d7ed；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-05/turns/000/provider/d4eeed2c1d7d4d9aa18b3ecee294d402.json](<../runtime_eval/runs/V1-001/cases/sp01-05/turns/000/provider/d4eeed2c1d7d4d9aa18b3ecee294d402.json>)；SHA=1632ca8e7c81a4697376dae88eb3948d05c5457aaf6e3f47336ea1751204b865；trace核验=true；实际system字符=[1359]

仍需人工确认：确认拼写恢复候选的业务接受规则；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-06 · pinyin

原题：Deguo 有多少张专辑？
参考判断：AI发现错误；保留V0冻结参考意见与新争议。
系统判断：**证据不足**；原参考题有Deguo专辑却canonical/控制器对应无关对象，gold为空，原先已排除评分，仍不能按该标准决定系统正确。V1实际猜成artist.name='Deguo'、无绑定/澄清、跨表守卫FAILED且无结果。独立观察为无依据的对象解释及未完成查询，未把坏参考变成系统通过。
```json
{
  "gold_sql_unchanged": "",
  "gold_result_from_preparation_unchanged": null,
  "actual_final_status": "FAILED",
  "actual_final_sql": "SELECT COUNT(*) AS album_count FROM \"public\".\"album\" AS a INNER JOIN \"public\".\"artist\" AS ar ON a.\"artist_id\" = ar.\"artist_id\" WHERE LOWER(ar.\"name\") = LOWER('Deguo')",
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-06/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-06/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-06/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-06/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-06/turns/000/provider/500454c70910422388bbf2f0f1e42b9d.json](<../runtime_eval/runs/V1-001/cases/sp01-06/turns/000/provider/500454c70910422388bbf2f0f1e42b9d.json>)；SHA=37437d03b06d2077682eb36eef410e586bd2b9c3835de88726651511c4aafbb9；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-06/turns/000/provider/25677b22246b4bb59d2bc2e4ef2d8010.json](<../runtime_eval/runs/V1-001/cases/sp01-06/turns/000/provider/25677b22246b4bb59d2bc2e4ef2d8010.json>)；SHA=e07b51d0aa1c03d53ad86081ac3431d78fbcab66e555cb06a642b1f4a7ba7b2c；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-06/turns/000/provider/3817b1f40aae4948be09311fc104f9d2.json](<../runtime_eval/runs/V1-001/cases/sp01-06/turns/000/provider/3817b1f40aae4948be09311fc104f9d2.json>)；SHA=a3287bf4fd87f0b3578130660f8d030b12b9724b4fbd2428562c8a684c9aac11；trace核验=true；实际system字符=[1359]

仍需人工确认：重审原题/改写/controller对应关系；保持当前不可评分状态；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-07 · mixed_language

原题：Chinook 里 Protected AAC audio file 这种 format 有多少首曲目？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；V1实际3次模型由正确track→media_type FK JOIN改成媒体ID子查询，仍为同一媒体名称条件；完整已保存媒体事实证实Protected AAC只有ID2。候选SQL可满足当前查询，单表system/多表守卫仍拒绝联表及子查询，table=NULL、绑定空，没有实得237。最后tables_used省略子查询表不等于真实只使用track。
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
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"track\" WHERE \"media_type_id\" = (SELECT \"media_type_id\" FROM \"public\".\"media_type\" WHERE \"name\" = 'Protected AAC audio file')",
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
      "\"media_type_id\" = (SELECT \"media_type_id\" FROM \"public\".\"media_type\" WHERE \"name\" = 'Protected AAC audio file')",
      "\"name\" = 'Protected AAC audio file'"
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
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
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
          "ast": "SELECT COUNT(*) FROM track WHERE track.media_type_id = (SELECT media_type.media_type_id FROM media_type WHERE media_type.name = 'Protected AAC audio file')",
          "predicates": {
            "media_type.name = 'Protected AAC audio file'": 1,
            "track.media_type_id = (SELECT media_type.media_type_id FROM media_type WHERE media_type.name = 'Protected AAC audio file')": 1
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-07/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-07/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-07/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-07/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-07/turns/000/provider/1d33411bd36e4cb6bdd792fedb95be1a.json](<../runtime_eval/runs/V1-001/cases/sp01-07/turns/000/provider/1d33411bd36e4cb6bdd792fedb95be1a.json>)；SHA=4aee6d59cd06410eb4c30974e00b96bd307b77511f360c3d518661cd9fd7c57b；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-07/turns/000/provider/b8b9294ce14f4f799634d95af75c5fa7.json](<../runtime_eval/runs/V1-001/cases/sp01-07/turns/000/provider/b8b9294ce14f4f799634d95af75c5fa7.json>)；SHA=6d22c98c85dfe9d1ad7695ffb634ea1a04c8ed12ab9a774f4a2a066b0bc9d1fa；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-07/turns/000/provider/c3d943e3c55346899c803c6ec49b6cb3.json](<../runtime_eval/runs/V1-001/cases/sp01-07/turns/000/provider/c3d943e3c55346899c803c6ec49b6cb3.json>)；SHA=e7bb55c9717b16a1277422b9bfaaf7b500d71208d0ac28196ae3aec3c01af8e2；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-08/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-08/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-08/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-08/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-08/turns/000/provider/32d55b5b67614ccbb8ce680f23bc61f1.json](<../runtime_eval/runs/V1-001/cases/sp01-08/turns/000/provider/32d55b5b67614ccbb8ce680f23bc61f1.json>)；SHA=7cd86bf7baa8429a1fa7023cbac6389e384489679c52804f433144a0893fd599；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-09/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-09/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-09/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-09/turns/000/response.raw.json>)

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-10 · explicit_absent

原题：查询 genre 为 Vaporwave 的曲目数量；如果数据库里根本没有这个流派，请直接报告没有记录。
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；V1实际候选裁决对Vaporwave为unmatched，生成保留原字面genre FK JOIN，最后修成genre_id IN子查询，未猜相似流派。但所有3次SQL均被跨表守卫拒绝，未得到COUNT0也未报告没有记录；不能将未执行SQL或预期0当实际答案。
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
  "actual_final_sql": "SELECT COUNT(*) AS track_count FROM \"public\".\"track\" WHERE \"genre_id\" IN (SELECT \"genre_id\" FROM \"public\".\"genre\" WHERE \"name\" = 'Vaporwave')",
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
      "\"genre_id\" IN (SELECT \"genre_id\" FROM \"public\".\"genre\" WHERE \"name\" = 'Vaporwave')",
      "\"name\" = 'Vaporwave'"
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
      "correct": null,
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
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
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
          "ast": "SELECT COUNT(*) FROM track WHERE track.genre_id IN (SELECT genre.genre_id FROM genre WHERE genre.name = 'Vaporwave')",
          "predicates": {
            "genre.name = 'Vaporwave'": 1,
            "track.genre_id IN (SELECT genre.genre_id FROM genre WHERE genre.name = 'Vaporwave')": 1
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-10/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-10/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-10/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-10/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-10/turns/000/provider/ab9fd1b7834e47349261f4e348f80a67.json](<../runtime_eval/runs/V1-001/cases/sp01-10/turns/000/provider/ab9fd1b7834e47349261f4e348f80a67.json>)；SHA=8398e92bf32b6812a5e2bd5df0f3a31e257888da0035734bb365c1a10ec43709；trace核验=true；实际system字符=[1373]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-10/turns/000/provider/21f961068885479da232bdaf9a4bbcab.json](<../runtime_eval/runs/V1-001/cases/sp01-10/turns/000/provider/21f961068885479da232bdaf9a4bbcab.json>)；SHA=4cbda704364038b6595c20dfd7c4ea98420f1999557d971b73c95ba98fee91d5；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-10/turns/000/provider/2df71c8a166e40a9992902fc9ae6eaf9.json](<../runtime_eval/runs/V1-001/cases/sp01-10/turns/000/provider/2df71c8a166e40a9992902fc9ae6eaf9.json>)；SHA=f48a227db8b3311778bb1a9484f58cdcae6e6f13c182ed0bfee56ccd1250d0c1；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-10/turns/000/provider/c55a40371a7743e5b6b74613a8c0151e.json](<../runtime_eval/runs/V1-001/cases/sp01-10/turns/000/provider/c55a40371a7743e5b6b74613a8c0151e.json>)；SHA=92273aa8b9a44e0feed3bf4b54d9d42d683f8889fe760307b2fdbec1038f6410；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-11/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-11/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-11/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-11/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-11/turns/000/provider/7ef2ca82563446f7823b6192c133cbbe.json](<../runtime_eval/runs/V1-001/cases/sp01-11/turns/000/provider/7ef2ca82563446f7823b6192c133cbbe.json>)；SHA=a0f7f10d98baf88b84fbeaa16962824e8ce2c48eb839402f54da68b309a35d4a；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-12 · standard

原题：What was the total invoice revenue for France in 2022?
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；明确2022发票收入，但France未明说客户居住国还是账单国家；V1实际L2问这两种口径，未SQL且controller_unanswered。全局地区默认未获确认，原参考唯一账单国家39.60继续有条件待核；不能仅因原预期L0就把这条追问定为错误。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-12/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-12/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-12/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-12/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-12/turns/000/provider/60f53d968f8c44a78844aecd5a2c8f7a.json](<../runtime_eval/runs/V1-001/cases/sp01-12/turns/000/provider/60f53d968f8c44a78844aecd5a2c8f7a.json>)；SHA=bcbdd020240abeb30d00d42b24adbfc9a98de0721c45cfbbec86e79c0cae55ff；trace核验=true；实际system字符=[4249]

仍需人工确认：确认invoice+for国家是否有团队批准的默认地区口径，或应要求澄清；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-13 · alias

原题：Iron Maiden乐队一共有多少张专辑？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；与02重复的原标签排除状态保持；V1实际批准艺术家绑定/改写，album→artist真实主键FK内连接COUNT(*)按Iron Maiden21正确。重复题不增加独立测试覆盖。
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
  "actual_final_sql": "SELECT COUNT(*) AS album_count FROM \"public\".\"album\" AS a JOIN \"public\".\"artist\" AS ar ON a.\"artist_id\" = ar.\"artist_id\" WHERE ar.\"name\" = 'Iron Maiden'",
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
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
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
    "automatic_complete": null,
    "pending_annotation": true,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-13/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-13/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-13/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-13/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-13/turns/000/provider/0db5592bba95423fa1283d7c07eb8a85.json](<../runtime_eval/runs/V1-001/cases/sp01-13/turns/000/provider/0db5592bba95423fa1283d7c07eb8a85.json>)；SHA=2b799f6016778f68e50392b55a29fc8ce48ded4bc9c29685ac7b5ccd4dbd5a62；trace核验=true；实际system字符=[2195]

仍需人工确认：是否保留重复作一致性样本；不改当前不可评分标记；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-14/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-14/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-14/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-14/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-14/turns/000/provider/9b91564476ae4ab4a221decb4350381b.json](<../runtime_eval/runs/V1-001/cases/sp01-14/turns/000/provider/9b91564476ae4ab4a221decb4350381b.json>)；SHA=cc2805b5d765b109c804d704264c0cea29c19e8400a5ce2d99dfb32c63c82659；trace核验=true；实际system字符=[1359]

仍需人工确认：确认题面所需的地区字段或澄清策略；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-15/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-15/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-15/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-15/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-15/turns/000/provider/ec89731646524bfcb25b5d2544fbfa8c.json](<../runtime_eval/runs/V1-001/cases/sp01-15/turns/000/provider/ec89731646524bfcb25b5d2544fbfa8c.json>)；SHA=854e6e539b4c6e093152fda236cfd6add88eb84428001766171f3c1e88c39063；trace核验=true；实际system字符=[2195]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
  "actual_final_sql": "SELECT COUNT(*) AS album_count FROM \"public\".\"album\" AS a JOIN \"public\".\"artist\" AS ar ON a.artist_id = ar.artist_id WHERE ar.name = 'U2'",
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
      "a.artist_id = ar.artist_id",
      "ar.name = 'U2'"
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-16/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-16/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-16/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-16/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-16/turns/000/provider/b0b53d15265f440391b9caec9eaaa3de.json](<../runtime_eval/runs/V1-001/cases/sp01-16/turns/000/provider/b0b53d15265f440391b9caec9eaaa3de.json>)；SHA=c990b7338eede89d163e4fa779f70c75d9bdd7622e910f5fa95121bedcbce607；trace核验=true；实际system字符=[2195]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-17 · typo

原题：Fracne 有多少客户？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；V1实际Fracne被SQL生成阶段改成France且COUNT结果5；NLU mentions/bindings/patches为空、intent.filters为空、rewritten_question=NULL。与04一致，仅查询在人工确认拼写意图后可通过；未证明候选裁决或显式绑定/改写，不把自动结果正确当整个专项①链完成。原V0对此给错误的历史意见保留，本次明确拆分查询与链路维度。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-17/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-17/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-17/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-17/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-17/turns/000/provider/749fa1bced83401ebab03364e1e3aa30.json](<../runtime_eval/runs/V1-001/cases/sp01-17/turns/000/provider/749fa1bced83401ebab03364e1e3aa30.json>)；SHA=192caf630b5dc47c24a751c599208b0ce0dcdb83ac43f3680d736a88f9aad48c；trace核验=true；实际system字符=[1359]

仍需人工确认：核对拼写候选接受规则及声明展示要求；不据此改自动分数；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-18 · typo

原题：Led Zepelin 有多少张专辑？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；V1实际前两次按artist.name='led zepelin'做FK专辑计数，被跨表守卫拒绝；第三次技术修复改为LOWER(album.title) LIKE '%led zepelin%'，执行得到0。名称筛选从艺术家改成专辑标题且从等值变为子串，用户未确认这种业务改义；无绑定/改写，也未按待确认Led Zeppelin目标得14。
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
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS album_count FROM \"public\".\"album\" AS a WHERE LOWER(a.\"title\") LIKE '%led zepelin%'",
  "actual_final_table": [
    {
      "album_count": 0
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
      "album"
    ],
    "actual_predicate_expressions": [
      "LOWER(a.\"title\") LIKE '%led zepelin%'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "technical_repair_business_predicate_changed": {
      "before": "artist.name",
      "after": "album.title",
      "user_confirmed_field_change": false,
      "actual_saved_result": 0,
      "is_successful_execution_not_semantic_success": true
    }
  },
  "original_automatic_score": {
    "id": "sp01-18",
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
          "ast": "SELECT COUNT(*) FROM album WHERE LOWER(album.title) LIKE '%led zepelin%'",
          "predicates": {
            "LOWER(album.title) LIKE '%led zepelin%'": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "album"
          ],
          "limit": null
        }
      },
      "result": {
        "correct": false,
        "matched": false,
        "reason": "column_values_mismatch",
        "column_mapping": null,
        "ordered": false,
        "numeric_columns": [
          0,
          0
        ],
        "rounding": "none; exact numeric values",
        "gold_truncated": false,
        "actual_truncated": false
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
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "not_required"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-18/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-18/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-18/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-18/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-18/turns/000/provider/eef318054ca1466f91c5cf30b229e3f3.json](<../runtime_eval/runs/V1-001/cases/sp01-18/turns/000/provider/eef318054ca1466f91c5cf30b229e3f3.json>)；SHA=f03cc3d459cb851acd13157004dcea3ee03e6896b7470507d5f10ab49415bc59；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-18/turns/000/provider/c4e3d09df5f94c9d8c26761297899897.json](<../runtime_eval/runs/V1-001/cases/sp01-18/turns/000/provider/c4e3d09df5f94c9d8c26761297899897.json>)；SHA=52acb0f42baf801d0030a6d3a7ef4dd172ede24a4fe14f454f1050a7e20f715c；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-18/turns/000/provider/c87e7d3b246747b29656d536b1b27507.json](<../runtime_eval/runs/V1-001/cases/sp01-18/turns/000/provider/c87e7d3b246747b29656d536b1b27507.json>)；SHA=b5920ebc31dce4660c040c7e6e3baad7b1c0e75f5ff7d9855434be427dbe7212；trace核验=true；实际system字符=[1359]

仍需人工确认：确认拼写恢复策略，但当前对象/计数丢失有直接证据；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-19/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-19/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-19/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-19/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-19/turns/000/provider/9c088b7eb4e14f07a6709f9bdbbbddc3.json](<../runtime_eval/runs/V1-001/cases/sp01-19/turns/000/provider/9c088b7eb4e14f07a6709f9bdbbbddc3.json>)；SHA=d55b5d2b12f8a24a2f3e1fef3f2a0d0ff148ca66b39b8b0fa7e24820e72320f2；trace核验=true；实际system字符=[1359]

仍需人工确认：确认拼写恢复的业务接受边界；若需界面逐题截图另执行独立开发验证；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-20 · typo

原题：MPEG adiou file 有多少首曲目？
参考判断：AI建议有条件通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；V1实际前两次候选为正确MPEG audio媒体FK JOIN/子查询，但被守卫拦；第三次写track.media_type_id=1并执行3034。已有完整媒体事实确实ID1=MPEG audio，PK/FK使当前数据下该SQL与参考语义对应，这一事实比仅数值相同更强。但真实NLU绑定/patch/rewrite为空，provider user payload未提供完整ID-名称配对证据，仅各列sample_values，修复ID来源未验证。仅在人工确认拼写目标和ID映射依据后查询条件通过，不把3034判为有限候选消歧链全通过。
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
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS track_count FROM \"public\".\"track\" AS t WHERE t.\"media_type_id\" = 1",
  "actual_final_table": [
    {
      "track_count": 3034
    }
  ],
  "actual_answer": "查询结果：3034。",
  "actual_nlu_bindings": [],
  "actual_nlu_patches": [],
  "actual_rewritten_question": null,
  "actual_candidate_options": null,
  "independent_static_and_saved_result_proof": {
    "actual_sql_present": true,
    "actual_tables": [
      "track"
    ],
    "actual_predicate_expressions": [
      "t.\"media_type_id\" = 1"
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
    "snapshot_unique_name_not_schema_unique_constraint": true,
    "foreign_key_id_snapshot_mapping": {
      "actual_id": 1,
      "stored_source_fact_name": "MPEG audio file",
      "mapped_in_verified_NLU_binding": false,
      "binding_or_rewrite_whole_pipeline_not_proven": true
    }
  },
  "original_automatic_score": {
    "id": "sp01-20",
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
          "ast": "SELECT COUNT(*) FROM track WHERE track.media_type_id = 1",
          "predicates": {
            "track.media_type_id = 1": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-20/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-20/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-20/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-20/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-20/turns/000/provider/abe87ff347804fe8baeb5b959ee79e69.json](<../runtime_eval/runs/V1-001/cases/sp01-20/turns/000/provider/abe87ff347804fe8baeb5b959ee79e69.json>)；SHA=dca6d5be7812c95f54b94062e8c72505eea9d328f3f3a6c27890bb06cd82b34f；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-20/turns/000/provider/cfccd21768af4586a039689556f1692c.json](<../runtime_eval/runs/V1-001/cases/sp01-20/turns/000/provider/cfccd21768af4586a039689556f1692c.json>)；SHA=6fd136d75a0e2cda8363f0305e225aaca93458039463539ac749e19b05e2ec9a；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-20/turns/000/provider/dda05ca69d1747f68b185c5ebcc1d9f3.json](<../runtime_eval/runs/V1-001/cases/sp01-20/turns/000/provider/dda05ca69d1747f68b185c5ebcc1d9f3.json>)；SHA=4ea51e0fceaf1386124386968338fe20d2fe784e9bab2a2805e0dcda9b9f6d93；trace核验=true；实际system字符=[1359]

仍需人工确认：确认该拼写恢复可接受；区别候选SQL等价与实际系统失败；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-21/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-21/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-21/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-21/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-21/turns/000/provider/3c6f9e30d19e48c0abb13dd4e96ca6df.json](<../runtime_eval/runs/V1-001/cases/sp01-21/turns/000/provider/3c6f9e30d19e48c0abb13dd4e96ca6df.json>)；SHA=e7f489e1c57f377b5a8c0b7fdae1440e9fe6b173e4a205005217b24e5cc85f06；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-22 · pinyin

原题：Gudian 这个流派的曲目有多少首？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI发现错误**；已批准古典→Classical及真实genre事实可支持pinyin目标，但V1实际NLU无mentions/bindings，SQL仍genre.name='Gudian'且跨表守卫FAILED。未得74、未改写正确值，不能因SQL形式COUNT/FK正确就通过。
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
  "actual_final_sql": "SELECT COUNT(*) FROM \"public\".\"track\" WHERE \"genre_id\" = (SELECT \"genre_id\" FROM \"public\".\"genre\" WHERE \"name\" = 'Gudian')",
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
      "\"genre_id\" = (SELECT \"genre_id\" FROM \"public\".\"genre\" WHERE \"name\" = 'Gudian')",
      "\"name\" = 'Gudian'"
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
          "ast": "SELECT COUNT(*) FROM track WHERE track.genre_id = (SELECT genre.genre_id FROM genre WHERE genre.name = 'Gudian')",
          "predicates": {
            "genre.name = 'Gudian'": 1,
            "track.genre_id = (SELECT genre.genre_id FROM genre WHERE genre.name = 'Gudian')": 1
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-22/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-22/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-22/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-22/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-22/turns/000/provider/e20d5863b639474682977de32d7532c4.json](<../runtime_eval/runs/V1-001/cases/sp01-22/turns/000/provider/e20d5863b639474682977de32d7532c4.json>)；SHA=30dc6540a286a3edc598cd64c1163a9094d41b4f85b45fe000674b2bc4111983；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-22/turns/000/provider/6151472e144141a28182119fa77a9e70.json](<../runtime_eval/runs/V1-001/cases/sp01-22/turns/000/provider/6151472e144141a28182119fa77a9e70.json>)；SHA=77cbe39f6ff3aa8b6985ca448da259a9efe969238dbdcca74ee2a9b00138f0b6；trace核验=true；实际system字符=[1359]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-22/turns/000/provider/dbadc53056074d7996388ddf3433cb22.json](<../runtime_eval/runs/V1-001/cases/sp01-22/turns/000/provider/dbadc53056074d7996388ddf3433cb22.json>)；SHA=032f17cd6437e12f8a00a57e5ed660326c0dbddeb32a894440705a01952d252b；trace核验=true；实际system字符=[1359]

仍需人工确认：人工可核对拼音大小写/分词接受边界；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-23/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-23/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-23/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-23/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-23/turns/000/provider/b1a301cd19024b5bb8524897b30719d2.json](<../runtime_eval/runs/V1-001/cases/sp01-23/turns/000/provider/b1a301cd19024b5bb8524897b30719d2.json>)；SHA=59d79087f23cfb6d1dc3dee4ff6b3ce07fc334e4d072050a16b687acd675f876；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-24 · mixed_language

原题：Iron Maiden 这个 artist 有多少 albums？
参考判断：AI建议通过；保留V0冻结参考意见与新争议。
系统判断：**AI建议通过**；V1实际artist.name=Iron Maiden绑定正确，album→artist真实主键FK内连接COUNT(*)与原参考相同，连接不复制专辑，保存结果21。
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
  "actual_final_sql": "SELECT COUNT(*) AS album_count FROM \"public\".\"album\" AS a JOIN \"public\".\"artist\" AS ar ON a.\"artist_id\" = ar.\"artist_id\" WHERE ar.\"name\" = 'Iron Maiden'",
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
        "correct": true,
        "status": "confirmed",
        "reason": "Qualified SQL AST matches frozen semantic contract",
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-24/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-24/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-24/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-24/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-24/turns/000/provider/24576a8ecfb44cee937f3a8b72026af6.json](<../runtime_eval/runs/V1-001/cases/sp01-24/turns/000/provider/24576a8ecfb44cee937f3a8b72026af6.json>)；SHA=88d4cb0159d32905a010224794555f961cf82db401c0778dba746e1e984c4394；trace核验=true；实际system字符=[2195]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-25 · colloquial

原题：意大利那边的发票总共开了多少钱？
参考判断：AI发现错误；保留V0冻结参考意见与新争议。
系统判断：**证据不足**；原参考声称意大利发票默认按客户所在地，已确认规则没有这种默认。V1实际按invoice.billing_country=Italy SUM(total)得到37.62，参考customer.country也37.62只为本快照巧合，不是语义证明。保留参考错误与人审，正式系统评分不能确定，不为系统改参考。
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
  "actual_final_sql": "SELECT SUM(\"total\") AS total_invoice_amount FROM \"public\".\"invoice\" WHERE \"billing_country\" = 'Italy'",
  "actual_final_table": [
    {
      "total_invoice_amount": "37.62"
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-25/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-25/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-25/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-25/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-25/turns/000/provider/4123d604eaac4c31a2ddc013c598a419.json](<../runtime_eval/runs/V1-001/cases/sp01-25/turns/000/provider/4123d604eaac4c31a2ddc013c598a419.json>)；SHA=b83dc136648d1f77543108b08f733c2839be2fc7a2c1cdd443d92b343a120bee；trace核验=true；实际system字符=[1359]

仍需人工确认：核对参考声称的客户所在地默认依据；目前禁止自动补该默认；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-26/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-26/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-26/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-26/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-26/turns/000/provider/194b287cf55e4420bf6f77800a787cb0.json](<../runtime_eval/runs/V1-001/cases/sp01-26/turns/000/provider/194b287cf55e4420bf6f77800a787cb0.json>)；SHA=4db82a55f9b0636e716702e6bb4fdc42f1b187c947f062f9dd94d4bfae6cd4d7；trace核验=true；实际system字符=[1359]

仍需人工确认：AI意见不代替人工验收；保持pending_human_review；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-27/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-27/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-27/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-27/turns/000/response.raw.json>)

仍需人工确认：确认候选集合标准表示及下轮评分器版本；本轮只附独立AI意见；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-28 · multi_candidate

原题：Chinook 里金属流派的曲目有多少首？
参考判断：AI发现错误；保留V0冻结参考意见与新争议。
系统判断：**AI建议有条件通过**；原题明确流派；参考把Metallica艺术家和Heavy Metal泛近义关系列入，原标签已排除且参考依据错保留。V1实际只给已批准candidate-only的genre Metal，L2不自动绑定、不出现pending Metallica，不猜艺术家。该候选确认行为合理；是否还应有Heavy Metal候选仍需人工，当前仅条件通过。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-28/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-28/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-28/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-28/turns/000/response.raw.json>)

仍需人工确认：拒绝未经批准的Metallica artist候选；确认Heavy Metal是否有获准关系；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
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
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-29/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-29/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-29/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-29/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-29/turns/000/provider/950d42211a374e489b0f074d6112bd93.json](<../runtime_eval/runs/V1-001/cases/sp01-29/turns/000/provider/950d42211a374e489b0f074d6112bd93.json>)；SHA=f36c625e1ea0950f8116fedbab18a9cb68fa9663981a222773d2103df5dd2f84；trace核验=true；实际system字符=[1359]

仍需人工确认：确认COUNT0文字是否足以满足报告没有记录要求，或应明确补一句；本轮不改代码；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## sp01-30 · explicit_absent

原题：统计 invoice_date 在 2030-01-01 到 2030-12-31（左闭右开）之间的发票张数；如果那段时间没有发票，就按这个时间范围查询并报告没有记录。
参考判断：AI发现错误；保留V0冻结参考意见与新争议。
系统判断：**证据不足**；原题显式[2030-01-01,2030-12-31)，冻结gold错误扩大到2031-01-01，仍保留参考争议，正式系统评分不能依坏参考判定。V1实际NLU对‘之间’unmatched，没有国家追问；随后真实意图提取将end改成2031，SQL也<2031，实际0与错误gold相同只是未来空数据巧合。独立题意观察为日期上界扩大，应人工纠错；不为了系统得0通过而重写题面。
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
  "actual_final_status": "SUCCEEDED",
  "actual_final_sql": "SELECT COUNT(*) AS invoice_count FROM \"public\".\"invoice\" WHERE \"invoice_date\" >= '2030-01-01' AND \"invoice_date\" < '2031-01-01'",
  "actual_final_table": [
    {
      "invoice_count": 0
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
      "invoice"
    ],
    "actual_predicate_expressions": [
      "\"invoice_date\" >= '2030-01-01'",
      "\"invoice_date\" < '2031-01-01'"
    ],
    "actual_aggregate_expressions": [
      "COUNT(*)"
    ],
    "has_grouping": false,
    "limit": null,
    "no_new_sql_execution": true,
    "proof_is_not_a_recalculated_score": true,
    "direct_user_condition_observation": {
      "user_lower_bound": "2030-01-01",
      "user_exclusive_upper_bound": "2030-12-31",
      "frozen_gold_exclusive_upper_bound": "2031-01-01",
      "reference_boundary_matches_user": false,
      "actual_country_clarification_has_no_basis_in_question": false,
      "actual_SQL_exclusive_upper_bound": "2031-01-01",
      "actual_SQL_matches_user_explicit_exclusive_upper_bound": false,
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
    "initial_status": "SUCCEEDED",
    "final_status": "SUCCEEDED",
    "observed_initial_level": "L0",
    "initial_level_correct": null,
    "binding_correctness": {
      "correct": null,
      "mode": "unknown_literal_sql_contract",
      "expected": [],
      "actual": []
    },
    "query": {
      "semantic_preservation": {
        "correct": null,
        "status": "AI_pending",
        "reason": "Qualified AST differs; semantic equivalence needs independent review",
        "predicate_match": false,
        "gold": {
          "ast": "SELECT COUNT(*) FROM invoice WHERE invoice.invoice_date >= CAST('2030-01-01' AS DATE) AND invoice.invoice_date < CAST('2031-01-01' AS DATE)",
          "predicates": {
            "invoice.invoice_date < CAST('2031-01-01' AS DATE)": 1,
            "invoice.invoice_date >= CAST('2030-01-01' AS DATE)": 1
          },
          "aggregates": [
            "COUNT(*)"
          ],
          "tables": [
            "invoice"
          ],
          "limit": null
        },
        "actual": {
          "ast": "SELECT COUNT(*) FROM invoice WHERE invoice.invoice_date >= '2030-01-01' AND invoice.invoice_date < '2031-01-01'",
          "predicates": {
            "invoice.invoice_date < '2031-01-01'": 1,
            "invoice.invoice_date >= '2030-01-01'": 1
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
    "pending_annotation": false,
    "outcome": "finished",
    "controller_events": [],
    "semantic_review_status": "AI_pending"
  }
}
```
证据：[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-30/checkpoint.json](<../runtime_eval/runs/V1-001/cases/sp01-30/checkpoint.json>)；[eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-30/turns/000/response.raw.json](<../runtime_eval/runs/V1-001/cases/sp01-30/turns/000/response.raw.json>)
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-30/turns/000/provider/bc881ac9f99f451f96199224b1cd102a.json](<../runtime_eval/runs/V1-001/cases/sp01-30/turns/000/provider/bc881ac9f99f451f96199224b1cd102a.json>)；SHA=89d0356d86187229b04351ce415d2f43d74a39127e62f669c045fd6e55ba0695；trace核验=true；实际system字符=[1203]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-30/turns/000/provider/4fb2ab0eb01d42ef9e63d140084586b1.json](<../runtime_eval/runs/V1-001/cases/sp01-30/turns/000/provider/4fb2ab0eb01d42ef9e63d140084586b1.json>)；SHA=0615f9420425d4131c2b55006e8a00ea320fe52d2e64c10648a0221ddb8e3502；trace核验=true；实际system字符=[4249]
- [eval/experiments/after_d2_01_03/runtime_eval/runs/V1-001/cases/sp01-30/turns/000/provider/9ff8a48b015148e79507614707b452b0.json](<../runtime_eval/runs/V1-001/cases/sp01-30/turns/000/provider/9ff8a48b015148e79507614707b452b0.json>)；SHA=86dcda00cbaf69e6b0306d6af60df55b7ba0652805f508d6a03c62f30ffa7822；trace核验=true；实际system字符=[1359]

仍需人工确认：优先确认用户原句是否本意整年，或必须保持12/31左闭右开；另存修订版只在人工决定后实施；本轮逐条AI意见不代替人审；V1原自动分数与AI维度意见分别保留。
人工状态：pending_human_review；未填写签名/人工确认日期。

## 原材料与限制

- [eval/experiments/after_d2_01_03/data/cases-v6-reviewed.jsonl](<../data/cases-v6-reviewed.jsonl>)；SHA=42327cb68a65f84b736007da40e2551fd4ffd35f0651d99c41ec28b43b9bd0f1
- [eval/experiments/after_d2_01_03/reports/v0-task01-full-review.json](<v0-task01-full-review.json>)；SHA=6f1a1cef42c692b7930f06fc334b08aeecee94b458319ef1584544e8cbe86a13
- [data/catalog/chinook.yaml](<../../../../data/catalog/chinook.yaml>)；SHA=4d97a3f7fdfd0c684b544f162e20d2253c4f9c0cd572ba1fcaf40fe439a391b8
- [data/rules/metric_definitions.json](<../../../../data/rules/metric_definitions.json>)；SHA=2a0df8d29a4fb5401fd0a5b33a0f44932e00ab005bc674eaaa8b8a33f1df5efc
- [data/aliases/aliases-d2-reviewed.csv](<../../../../data/aliases/aliases-d2-reviewed.csv>)；SHA=aa699e8ef59f5185a0626ed2a9aefb36a1e292bfa2e3c0efd4b0ba5b1ddaef04
- [eval/experiments/after_d2_01_03/materials/readonly_live_facts.json](<../materials/readonly_live_facts.json>)；SHA=391487ffea9c12f21f5444369dd2b87b48897ac363a032a6ea107e5507df7b8f
- [eval/experiments/after_d2_01_03/runtime_eval/V1-code-snapshot.json](<../runtime_eval/V1-code-snapshot.json>)；SHA=13c8063f2c04e8762128aba22480088f2d4e96676e075f1a81ab89a1a8a9a7e8
- [qa_agent/pipeline.py](<../../../../qa_agent/pipeline.py>)；SHA=ef083f1af00331c8b22cf14788a134d5fb95c6af5decefe6594e811ac4c0a407
- [qa_agent/sql/generator.py](<../../../../qa_agent/sql/generator.py>)；SHA=3bfe719356bca0a4d9c5fc28a94c9a03fdfb175598c96507c643da04bde99bbd
- [ui/app.py](<../../../../ui/app.py>)；SHA=9dd56378c112f5b3b9c4058368ccfc8e8e602e5549e029459e0ea765dd1855e3
- V1逐项AI预审意见分布不是新通过率；正式自动结果沿用原scores.json。
- 原参考争议保留；结果相同不证明地区/时间含义正确。
- candidate_only只验证初始澄清，不伪称续答/SQL成功；未新增逐题浏览器测试。
- 04/17统一按查询与绑定链分别判断，原V0不同意见不覆盖。
- 30坏参考导致正式判断暂不能确定；V1实际日期上界扩大／V2实际无依据国家追问各自另列观察。
