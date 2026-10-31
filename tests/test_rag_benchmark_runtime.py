"""Runtime benchmark adapters exercise real tools, without paid model calls."""
from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest

from qa_agent.config import Settings
from qa_agent.rag import evaluation
from qa_agent.rag.answer import DocumentAnswer
from qa_agent.rag.parsers import DocumentError
from qa_agent.rag.retrieval_cache import clear_retrieval_cache
from qa_agent.rag.retriever import retrieve


def passage(doc="d-a", eid="E1", text="Cedar 2026 budget is 1250 dollars."):
    return {"chunk_id": doc+"-chunk", "evidence_id": eid, "doc_id": doc,
            "doc_title": doc, "text": text, "page": None,
            "section_path": ["Budget"], "bbox": None}


@pytest.fixture
def frozen_dense_index(monkeypatch, tmp_path):
    from qa_agent.rag import retrieval_cache, embeddings
    chunks = [passage(), passage("d-b", "E2", "Borealis visitor policy prohibits parking.")]
    chunks[1]["section_path"] = ["Visitor policy"]
    metadata = {"dense_embedding": {"enabled": True}, "created_at": "fixture",
                "chunks_sha256": "test-frozen-corpus"}
    monkeypatch.setattr(retrieval_cache, "snapshot", lambda *args: (
        chunks, metadata, np.eye(2, dtype=np.float32), ("fixture",), False))
    calls = []
    def fail_encoder(*args, **kwargs):
        calls.append("encoder")
        raise AssertionError("BM25 must not initialize the vector model")
    monkeypatch.setattr(embeddings, "get_embedder", fail_encoder)
    monkeypatch.setattr(retrieval_cache, "query_vector", fail_encoder)
    settings = Settings(db_url="", bge_model_path=tmp_path/"model-is-not-deleted",
                        rag_top_k=2, rag_retrieval_strategy="hybrid")
    clear_retrieval_cache()
    yield settings, chunks, calls
    clear_retrieval_cache()


def test_explicit_bm25_with_dense_index_never_queries_encoder(frozen_dense_index):
    settings, frozen, calls = frozen_dense_index
    before = deepcopy(frozen)
    chunks, metadata = retrieve("Cedar budget", ["d-a", "d-b"], settings=settings, strategy="bm25")
    assert [c["doc_id"] for c in chunks] == ["d-a"]
    assert metadata["retrieval_strategy"] == "bm25"
    assert metadata["retrieval_method"] == "bm25" and not metadata["dense_enabled"]
    assert metadata["rankings"]["dense"] == [] and metadata["rankings"]["rrf"] == []
    assert chunks[0]["score_type"] == "bm25"
    assert chunks[0]["score"] == pytest.approx(chunks[0]["bm25_score"], abs=1e-6)
    assert metadata["retrieval_timing_ms"]["dense_scoring"] == 0
    assert metadata["retrieval_timing_ms"]["reranking_and_neighbors"] == 0
    assert calls == [] and frozen == before


def test_default_hybrid_still_uses_encoder(frozen_dense_index):
    settings, _, calls = frozen_dense_index
    with pytest.raises(AssertionError, match="vector model"):
        retrieve("Cedar budget", ["d-a"], settings=settings)
    assert calls == ["encoder"]


@pytest.mark.parametrize("scope", [[], "d-a", ["d-a", "d-a"], [" "], [1]])
def test_retrieval_adapter_rejects_invalid_scope_before_work(scope, monkeypatch):
    monkeypatch.setattr(evaluation, "retrieve", lambda *a, **k: pytest.fail("retrieval must not run"))
    with pytest.raises(DocumentError) as error:
        evaluation.retrieve_for_evaluation("budget?", scope, settings=Settings(db_url=""))
    assert error.value.code == "rag_scope_invalid"


def test_retrieval_adapter_preserves_scope_and_explicit_strategy(frozen_dense_index):
    settings, _, _ = frozen_dense_index
    chunks, metadata = evaluation.retrieve_for_evaluation(
        "Cedar budget", ["d-a", "d-b"], settings=settings, strategy="bm25")
    assert chunks[0]["doc_id"] == "d-a"
    assert metadata["allowed_doc_ids"] == ["d-a", "d-b"]
    assert metadata["candidate_count"] == 2


def test_fixed_extractive_evidence_preserves_source_and_never_constructs_llm(monkeypatch):
    monkeypatch.setattr(evaluation, "JsonLLM", lambda *a: pytest.fail("No model client in extractive mode"))
    source = [passage(), passage("d-b", "E2", "Borealis budget is 3000 dollars.")]
    before = deepcopy(source)
    result = evaluation.generate_for_evaluation("What are both budgets?", source, settings=Settings(db_url=""))
    assert result["status"] == "SUCCEEDED" and result["citation_ids"] == ["E1", "E2"]
    assert result["input_chunks"] == result["used_evidence"] == before == source
    assert "1250" in result["answer"] and "3000" in result["answer"]
    assert result["generation_input"]["question"] == "What are both budgets?"
    assert result["generation_input"]["evidence"][0]["text"] == source[0]["text"]
    assert result["semantic_status"] == "not_applicable_extractive"
    assert result["usage"]["physical_calls"] == result["usage"]["input_tokens"] == 0
    assert result["usage"]["usage_complete"]
    assert result["latency_ms"] >= 0 and len(result["trace"]) == 2
    json.dumps(result)
    result["input_chunks"][0]["text"] = "caller mutation"
    assert source == before


def test_empty_evidence_is_real_refusal_not_a_generated_answer():
    result = evaluation.generate_for_evaluation("What budget?", [], settings=Settings(db_url=""))
    assert result["status"] == "EMPTY_RESULT"
    assert result["citation_ids"] == [] and result["used_evidence"] == []
    assert result["usage"]["physical_calls"] == 0


@pytest.mark.parametrize("evidence_ids", [["E1", "E1"], ["E0"], ["invented"]])
def test_invalid_fixed_evidence_cannot_reach_llm(monkeypatch, evidence_ids):
    monkeypatch.setattr(evaluation, "JsonLLM", lambda *a: pytest.fail("Do not call model for invalid evidence"))
    chunks = [passage("d-"+str(i), eid) for i, eid in enumerate(evidence_ids)]
    result = evaluation.generate_for_evaluation("budget?", chunks, settings=Settings(db_url=""), answer_mode="llm")
    assert result["status"] == "FAILED" and result["error"]["code"] == "rag_citation_invalid"
    assert result["usage"]["physical_calls"] == 0


@pytest.mark.parametrize("usage", [None, {"prompt_tokens": 160, "completion_tokens": 35,
                                       "prompt_cache_hit_tokens": 100, "prompt_cache_miss_tokens": 60}])
def test_model_trace_usage_is_observed_and_missing_usage_is_not_zero(monkeypatch, usage):
    class LocalModel:
        def __init__(self, settings): pass
        def complete_json(self, system, user, model, trace):
            trace.llm_attempts += 1
            payload = json.loads(user)
            assert payload["question"] == "What budget?"
            assert payload["evidence"][0]["text"] == passage()["text"]
            with trace.step("llm", {"model": "local-fixture"}) as step:
                if usage is not None:
                    step.output_summary["usage"] = usage
            return DocumentAnswer(status="SUCCEEDED", answer="The Cedar budget is 1250 dollars. [E1]",
                                  citation_ids=["E1"])
    monkeypatch.setattr(evaluation, "JsonLLM", LocalModel)
    result = evaluation.generate_for_evaluation("What budget?", [passage()],
                                              settings=Settings(db_url=""), answer_mode="llm")
    assert result["status"] == "SUCCEEDED" and result["usage"]["physical_calls"] == 1
    assert result["semantic_status"] == "not_verified"
    if usage is None:
        assert result["usage"]["missing_usage_attempts"] == 1
        assert result["usage"]["input_tokens"] is None and result["usage"]["output_tokens"] is None
        assert not result["usage"]["usage_complete"]
    else:
        assert result["usage"]["missing_usage_attempts"] == 0
        assert result["usage"]["input_tokens"] == 160 and result["usage"]["output_tokens"] == 35
        assert result["usage"]["cache_hit_input_tokens"] == 100
        assert result["usage"]["cache_miss_input_tokens"] == 60
    json.dumps(result)


def test_generation_failure_keeps_safe_error_trace_without_key(monkeypatch):
    key = "private-test-value"
    class FailedModel:
        def __init__(self, settings): pass
        def complete_json(self, system, user, model, trace):
            trace.llm_attempts += 1
            with trace.step("llm"):
                raise RuntimeError("provider failed: "+key)
    monkeypatch.setattr(evaluation, "JsonLLM", FailedModel)
    result = evaluation.generate_for_evaluation("What budget?", [passage()],
        settings=Settings(db_url="", llm_api_key=key), answer_mode="llm")
    assert result["status"] == "FAILED" and result["error"]
    assert result["usage"]["physical_calls"] == 1 and result["usage"]["input_tokens"] is None
    assert key not in json.dumps(result)
    assert any(step["status"] == "error" for step in result["trace"])
