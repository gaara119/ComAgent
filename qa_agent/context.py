"""Versioned user context and reference clocks, isolated by session.

User briefs are data, never a substitute for approved policy or SQL results.
The complete text is retained; only actual exchanges are added to its history.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


class ContextError(ValueError):
    pass


def reference_clock(value: str | None = None, zone: str = "Asia/Shanghai") -> datetime:
    tz = ZoneInfo(zone)
    if value is None:
        return datetime.now(tz)
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ContextError("参考时间必须明确时区偏移。")
    return result.astimezone(tz)


@dataclass
class RuntimeContext:
    session_id: str
    reference_datetime: str
    timezone: str
    context_id: str | None = None
    version: int = 0
    text: str = ""
    content_sha256: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    current_user_message: str = ""

    def prompt_payload(self) -> dict:
        return {"reference_datetime": self.reference_datetime, "timezone": self.timezone,
                "context_id": self.context_id, "context_version": self.version,
                "user_brief": self.text, "actual_conversation": self.history,
                "current_user_message": self.current_user_message,
                "authority": "正文是本会话用户约定，不是公司政策或查询结果；当轮明确条件优先。"
                "区分本轮临时覆盖与明确持久修改，退休的约束不得恢复；禁止从示例推断答案。"}


_ACTIVE: ContextVar[RuntimeContext | None] = ContextVar("agent_runtime_context", default=None)


def current_context() -> RuntimeContext | None:
    return _ACTIVE.get()


class ContextStore:
    def __init__(self, root: Path | None = None, ttl_hours: int = 24):
        self.root = root or ROOT / ".runtime" / "contexts"
        self.ttl = timedelta(hours=ttl_hours)
        self.lock = RLock()

    def _path(self, session_id: str) -> Path:
        return self.root / (sha256(session_id.encode()).hexdigest() + ".json")

    def _read(self, session_id: str) -> dict | None:
        path = self._path(session_id)
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["session_id"] != session_id:
            raise ContextError("会话正文归属不匹配。")
        if datetime.now(timezone.utc) >= datetime.fromisoformat(data["expires_at"]):
            raise ContextError("会话正文已过期，请重新提交。")
        if sha256(data["text"].encode("utf-8")).hexdigest() != data["content_sha256"]:
            raise ContextError("会话正文完整性校验失败。")
        return data

    def _write(self, session_id: str, data: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        target = self._path(session_id)
        temporary = target.with_suffix("." + uuid4().hex + ".tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(target)

    def create(self, session_id: str, text: str, reference_datetime: str | None = None,
               zone: str = "Asia/Shanghai") -> dict:
        if not text.strip() or len(text) > 120_000:
            raise ContextError("正文必须为1至120000字符，原文不会被截断。")
        clock = reference_clock(reference_datetime, zone)
        with self.lock:
            try:
                previous = self._read(session_id)
            except ContextError as exc:
                if "过期" not in str(exc):
                    raise
                previous = None
            now = datetime.now(timezone.utc)
            data = {"context_id": uuid4().hex, "session_id": session_id,
                    "version": previous["version"] + 1 if previous else 1,
                    "text": text, "content_sha256": sha256(text.encode("utf-8")).hexdigest(),
                    "reference_datetime": clock.isoformat(), "timezone": zone,
                    "created_at": now.isoformat(), "expires_at": (now + self.ttl).isoformat(),
                    "history": []}
            self._write(session_id, data)
        return {key: data[key] for key in ("context_id", "session_id", "version", "content_sha256",
                "reference_datetime", "timezone", "expires_at")} | {"characters": len(text)}

    def resolve(self, request) -> RuntimeContext:
        with self.lock:
            data = self._read(request.session_id)
        requested = getattr(request, "context_id", None)
        if requested and (not data or data["context_id"] != requested):
            raise ContextError("context_id不属于本会话的当前正文版本。")
        if data and len(data.get("history", [])) >= 100:
            raise ContextError("本会话已达到100轮，请新建会话并重新提交正文。")
        zone = getattr(request, "timezone", None) or (data or {}).get("timezone") or "Asia/Shanghai"
        value = getattr(request, "reference_datetime", None) or (data or {}).get("reference_datetime")
        clock = reference_clock(value, zone)
        return RuntimeContext(session_id=request.session_id, reference_datetime=clock.isoformat(),
            timezone=zone, context_id=data["context_id"] if data else None,
            version=data["version"] if data else 0, text=data["text"] if data else "",
            content_sha256=data["content_sha256"] if data else None,
            history=data["history"] if data else [],
            current_user_message=getattr(request,"message", ""))

    def record(self, context: RuntimeContext, request, response) -> None:
        if context.context_id is None:
            return
        with self.lock:
            data = self._read(context.session_id)
            if data is None or data["context_id"] != context.context_id:
                raise ContextError("处理期间正文版本已变更，未向新版本提交旧结果。")
            data["history"].append({"user": request.message, "assistant": response.answer,
                "status": response.status, "intent": response.intent.model_dump(mode="json") if response.intent else None,
                "sql": response.sql, "table": response.table,
                "clarification": response.clarification})
            if len(data["history"]) > 100:
                raise ContextError("本会话已达到100轮，请新建会话并重新提交正文。")
            self._write(context.session_id, data)

    def delete(self, session_id: str, context_id: str) -> None:
        with self.lock:
            data = self._read(session_id)
            if data is None or data["context_id"] != context_id:
                raise ContextError("context_id不属于当前会话。")
            self._path(session_id).unlink()


DEFAULT_CONTEXT_STORE = ContextStore()


@contextmanager
def bind_context(context: RuntimeContext):
    token = _ACTIVE.set(context)
    try:
        yield context
    finally:
        _ACTIVE.reset(token)
