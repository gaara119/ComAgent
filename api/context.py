"""Public full-text context ingestion; separate from ordinary chat messages."""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from qa_agent.context import ContextError, DEFAULT_CONTEXT_STORE

router = APIRouter(prefix="/api", tags=["session-context"])


class ContextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=120000)
    reference_datetime: str | None = None
    timezone: str = "Asia/Shanghai"

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("无效IANA时区") from exc
        return value

    @field_validator("reference_datetime")
    @classmethod
    def valid_clock(cls, value):
        if value is not None and datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("参考时间必须包含时区偏移")
        return value


@router.post("/context", status_code=201)
def create_context(request: ContextRequest):
    try:
        return DEFAULT_CONTEXT_STORE.create(request.session_id, request.text,
            request.reference_datetime, request.timezone)
    except ContextError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.delete("/context/{context_id}")
def delete_context(context_id: str, session_id: str):
    try:
        DEFAULT_CONTEXT_STORE.delete(session_id, context_id)
        return {"deleted": True}
    except ContextError as exc:
        raise HTTPException(409, str(exc)) from exc
