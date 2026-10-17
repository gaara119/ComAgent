"""Start with: python -m uvicorn api.main:app --host 127.0.0.1 --port 8000."""
from fastapi import FastAPI
from hashlib import sha256
from pathlib import Path
import os
import psycopg

from qa_agent.config import get_settings
from qa_agent.pipeline import chat
from qa_agent.schemas import AnswerEnvelope, ChatRequest

app = FastAPI(title="赛题八 问数问答 API", version="0.4.0", description="D4：AdventureWorks 带理由剪枝与外键校验、结构化多轮补丁、SQL与文档两类跨源流程。")

from api.documents import router as documents_router
app.include_router(documents_router)
from api.context import router as context_router
app.include_router(context_router)


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    from qa_agent.ablation import cumulative_health
    from qa_agent.sql.generator import SQL_SYSTEM_PROMPT
    multi_prompt = Path(__file__).resolve().parents[1] / "qa_agent/sql/prompts/multi_table.txt"
    prompt_hashes = {"single_table_loaded": sha256(SQL_SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
                     "multi_table_file": sha256(multi_prompt.read_bytes()).hexdigest() if multi_prompt.is_file() else None}
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
    aw_ready = False
    try:
        if settings.aw_db_url:
            with psycopg.connect(settings.aw_db_url, connect_timeout=2) as connection:
                connection.read_only = True
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    aw_ready = cursor.fetchone() == (1,)
    except psycopg.Error:
        pass
    return {"status": "ok", "stage": "D4", "database_ready": database_ready,
            "aw_database_ready": aw_ready,
            "sql_prompt_sha256": prompt_hashes,
            "component_mode": os.getenv("AGENT_COMPONENT_MODE", "none"),
            **cumulative_health(settings),
            "nlu_enabled": settings.nlu_enabled,
            "clarify_grounding_enabled": os.getenv("AGENT_GROUNDING_ENABLED", "true").lower() not in {"0", "false", "no"},
            "clarify_state_enabled": os.getenv("AGENT_CLARIFY_STATE_ENABLED", "true").lower() not in {"0", "false", "no"},
            "schema_recall_enhanced": os.getenv("SCHEMA_RECALL_ENHANCED", "false").lower() not in {"0", "false", "no"},
            "link_grounding_enabled": os.getenv("AGENT_LINK_GROUNDING_ENABLED", "true").lower() not in {"0", "false", "no"},
            **settings.public()}


@app.post("/api/chat", response_model=AnswerEnvelope)
def api_chat(request: ChatRequest) -> AnswerEnvelope:
    return chat(request)
