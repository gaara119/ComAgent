"""Shared D1 contract. A and B should agree before changing these fields."""
from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceScope(ContractModel):
    route: Literal["sql", "doc", "auto", "hybrid"] = "sql"
    db_id: str | None = "chinook"
    doc_ids: list[str] = Field(default_factory=list)


class ChatRequest(ContractModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    scope: SourceScope = Field(default_factory=SourceScope)

    # Optional, backward-compatible binding to complete user context and one clock.
    context_id: str | None = Field(default=None, min_length=1, max_length=128)
    reference_datetime: str | None = Field(default=None, max_length=80)
    timezone: str | None = Field(default=None, max_length=80)

    @field_validator("reference_datetime")
    @classmethod
    def valid_reference_datetime(cls, value):
        if value is not None:
            from datetime import datetime
            if datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is None:
                raise ValueError("参考时间必须包含时区偏移")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        if value is not None:
            from zoneinfo import ZoneInfo
            try:
                ZoneInfo(value)
            except (KeyError, ValueError) as exc:
                raise ValueError("无效IANA时区") from exc
        return value

    clarification_id: str | None = Field(default=None, min_length=1, max_length=128)
    intent_version: int | None = Field(default=None, ge=1)
    choice_id: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def valid_clarification_resume(self):
        if (self.clarification_id is None) != (self.intent_version is None):
            raise ValueError("clarification_id 与 intent_version 必须同时提供")
        if self.choice_id is not None and self.clarification_id is None:
            raise ValueError("choice_id 必须属于带版本的澄清卡片")
        return self

    @field_validator("message")
    @classmethod
    def nonempty_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("问题不能为空")
        return value


class Step(ContractModel):
    name: str
    status: Literal["ok", "warn", "error", "skipped"] = "ok"
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int = 0


class Evidence(ContractModel):
    evidence_id: str
    doc_id: str
    doc_title: str
    # PDF physical page, starting at 1; None only for non-paginated evidence.
    page: int | None = Field(default=None, ge=1)
    section_path: list[str] = Field(default_factory=list)
    text: str
    bbox: list[float] | None = None


class IntentContract(ContractModel):
    intent_version: int = 1
    route: Literal["sql", "doc", "hybrid", "chitchat"]
    task_type: str = "lookup"
    metric: str | None = None
    time_scope: dict[str, Any] | None = None
    filters: list[dict[str, Any]] = Field(default_factory=list)
    grouping: list[str] = Field(default_factory=list)
    order: dict[str, Any] | None = None
    assumptions: list[str] = Field(default_factory=list)
    unresolved: list[dict[str, Any]] = Field(default_factory=list)


class ErrorDetail(ContractModel):
    code: str
    message: str
    retryable: bool = False


class AnswerEnvelope(ContractModel):
    trace_id: str
    status: Literal["SUCCEEDED", "EMPTY_RESULT", "NEEDS_CLARIFICATION", "UNSUPPORTED", "FAILED"]
    answer: str
    rewritten_question: str | None = None
    sql: str | None = None
    table: list[dict[str, Any]] | None = None
    evidences: list[Evidence] = Field(default_factory=list)
    clarification: dict[str, Any] | None = None
    intent: IntentContract | None = None
    steps: list[Step] = Field(default_factory=list)
    error: ErrorDetail | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SQLGeneration(ContractModel):
    sql: str = Field(min_length=1, max_length=20000)
    tables_used: list[str] = Field(default_factory=list)
    explanation: str = Field(default="", max_length=1000)
