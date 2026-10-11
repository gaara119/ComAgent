from copy import deepcopy
from decimal import Decimal

from eval.d2_rag_eval import candidate_gold_hit
from eval.metrics import compare_results
from eval.rag_dataset import review_hash


def test_d2_continuous_rounding_follows_global_mapping_and_integer_keys_stay_exact():
    expected=[{"id": 7, "mean": "12.34567"}]
    actual=[{"new_mean": "12.35", "new_id": 7}]
    assert compare_results(expected,actual,expected_columns=["id","mean"],
                           numeric_columns=[0,1],round_numeric_columns=[1]).matched
    actual[0]["new_id"]="7.004"
    assert not compare_results(expected,actual,expected_columns=["id","mean"],
                               numeric_columns=[0,1],round_numeric_columns=[1]).matched
    assert not compare_results([["001"]],[[1]]).matched
    assert not compare_results([[None]],[[0]],round_numeric_columns=[0]).matched


def test_sixth_gold_chunk_does_not_count_as_hit_at_five():
    item={"doc_id":"doc", "physical_pages":[8],"gold_evidence":[]}
    candidates=[{"doc_id":"doc","page":p,"chunk_id":str(p)} for p in range(3,9)]
    assert not candidate_gold_hit(item,candidates,{})
    assert candidate_gold_hit(item,candidates[1:],{})


def test_non_pdf_gold_requires_actual_text_in_retrieved_chunk():
    item={"doc_id":"manual","physical_pages":[],"gold_evidence":[{"doc_id":"manual","page":None,"text":"AVG(invoice.total)"}]}
    candidate=[{"doc_id":"manual","page":None,"chunk_id":"one"}]
    assert candidate_gold_hit(item,candidate,{"one":{"text":"主口径 AVG(invoice.total)，单位为金额。"}})
    assert not candidate_gold_hit(item,candidate,{"one":{"text":"另一个指标。"}})
    assert not candidate_gold_hit(item,[{"doc_id":"other","page":None,"text":"AVG(invoice.total)"}],{})


def test_d2_review_hash_is_invalidated_by_answerability_and_gold_evidence_changes():
    row={"id":"rag-test","question":"q","answer":"a","physical_pages":[],
         "answerable":True,"gold_evidence":[{"text":"evidence","page":None}]}
    edited=deepcopy(row)
    edited["answerable"]=False
    assert review_hash(edited)!=review_hash(row)
    edited=deepcopy(row)
    edited["gold_evidence"][0]["text"]="changed"
    assert review_hash(edited)!=review_hash(row)
