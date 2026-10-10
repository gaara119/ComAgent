"""Start with: python -m uvicorn api.main:app --host 127.0.0.1 --port 8000."""
from fastapi import FastAPI
import psycopg

from qa_agent.config import get_settings
from qa_agent.pipeline import chat
from qa_agent.schemas import AnswerEnvelope, ChatRequest

app = FastAPI(title="赛题八 D1 问数 API", version="0.1.0", description="A SQL 通道与 B RAG 通道共用入口；D1 按显式来源路由。")


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    database_ready = False
    try:
        if settings.db_url:
            with psycopg.connect(settings.db_url, connect_timeout=2) as connection:
                connection.read_only = True
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    database_ready = cursor.fetchone() == (1,)
    except psycopg.Error:
        pass
    return {"status": "ok", "stage": "D1", "database_ready": database_ready,
            **settings.public()}


@app.post("/api/chat", response_model=AnswerEnvelope)
def api_chat(request: ChatRequest) -> AnswerEnvelope:
    return chat(request)
