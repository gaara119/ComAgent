"""Opt-in test recording exercises the same app, without any real model call."""
from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from qa_agent.config import Settings
from qa_agent.schemas import AnswerEnvelope, ChatRequest
from scripts.d2_capture_api import D2EvidenceMiddleware


def test_capture_middleware_calls_existing_route_once_and_redacts_record_only(tmp_path, monkeypatch):
    import scripts.d2_capture_api as module
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(module, "get_settings", lambda: Settings(db_url="", llm_api_key="fixture_secret_not_a_live_key"))
    monkeypatch.setenv("D2_CAPTURE_DIR", "e2e/api")
    app = FastAPI()
    count = []
    @app.post("/api/chat")
    def handler(request: ChatRequest):
        count.append(request.message)
        return AnswerEnvelope(trace_id="test-only-trace", status="SUCCEEDED", answer="fixture_secret_not_a_live_key")
    app.add_middleware(D2EvidenceMiddleware)
    response = TestClient(app).post("/api/chat", json={"session_id": "test-only", "message": "fixture question"})
    assert response.status_code == 200 and len(count) == 1
    assert response.json()["answer"] == "fixture_secret_not_a_live_key"
    records = list((tmp_path/"e2e/api").glob("*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["response"]["answer"] == "[redacted]"
    assert record["request"]["session_id"] == "test-only"
    assert "headers" not in record and "env" not in record


def test_disabled_capture_does_not_write_any_record(tmp_path, monkeypatch):
    monkeypatch.delenv("D2_CAPTURE_DIR", raising=False)
    app = FastAPI()
    @app.post("/api/chat")
    def handler():
        return {"status": "SUCCEEDED"}
    app.add_middleware(D2EvidenceMiddleware)
    assert TestClient(app).post("/api/chat").status_code == 200
    assert not list(tmp_path.rglob("*.json"))
