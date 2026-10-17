"""Bounded, version-bound persisted state for interrupted composed plans."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock
from uuid import uuid4
import re


class ComposedResumeError(ValueError):
    pass


def context_binding(context) -> dict:
    return {"context_id": context.context_id if context else None,
            "version": context.version if context else 0,
            "content_sha256": context.content_sha256 if context else None}


def looks_like_resume(request) -> bool:
    if request.clarification_id:
        return True
    from qa_agent.clarify.service import is_followup
    return bool(is_followup(request.message) or re.fullmatch(r"\s*\d{4}\s*年[。.!！]?\s*", request.message)
                or re.match(r"^\s*(?:是|不是|选|就|按|用|我指|我的意思|前者|后者)", request.message))


class ComposedStore:
    def __init__(self, root: Path | None = None, ttl_hours: int = 24):
        # Fixed relative to the installed project; never accept a client path.
        self.root = root or Path(__file__).resolve().parents[2] / ".runtime" / "composed"
        self.ttl = timedelta(hours=ttl_hours)
        self.lock = RLock()

    def path(self, session_id):
        return self.root / (sha256(session_id.encode("utf-8")).hexdigest() + ".json")

    def load(self, request, context, *, strict=False):
        with self.lock:
            path = self.path(request.session_id)
            if not path.is_file():
                return None
            if path.stat().st_size > 8_000_000:
                raise ComposedResumeError("跨源续跑状态过大，拒绝加载。")
            stored = json.loads(path.read_text(encoding="utf-8"))
        payload = stored["payload"]
        digest = sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if stored.get("sha256") != digest or payload.get("session_id") != request.session_id:
            raise ComposedResumeError("跨源续跑状态完整性不匹配。")
        if datetime.now(timezone.utc) >= datetime.fromisoformat(payload["expires_at"]):
            if strict:
                raise ComposedResumeError("跨源续跑状态已过期，请重新提交完整问题。")
            return None
        if payload.get("context_binding") != context_binding(context) or payload.get("scope") != request.scope.model_dump(mode="json"):
            if strict:
                raise ComposedResumeError("正文版本或来源范围已变化，旧跨源澄清不能继续。")
            return None
        if request.clarification_id and (request.clarification_id != payload.get("clarification_id")
                or request.intent_version != payload.get("intent_version")):
            raise ComposedResumeError("跨源澄清卡片或意图版本已失效。")
        return payload

    def save(self, request, context, payload):
        data = {**payload, "session_id": request.session_id, "scope": request.scope.model_dump(mode="json"),
                "context_binding": context_binding(context),
                "expires_at": (datetime.now(timezone.utc) + self.ttl).isoformat()}
        if not isinstance(data.get("next_index"), int) or not 0 <= data["next_index"] < 6:
            raise ComposedResumeError("跨源续跑位置无效。")
        text = json.dumps({"payload": data, "sha256": sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()},
                          ensure_ascii=False, indent=2)
        if len(text.encode("utf-8")) > 8_000_000:
            raise ComposedResumeError("跨源续跑状态超过有界容量。")
        with self.lock:
            self.root.mkdir(parents=True, exist_ok=True)
            target = self.path(request.session_id)
            temporary = target.with_suffix("." + uuid4().hex + ".tmp")
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(target)

    def discard(self, session_id):
        with self.lock:
            self.path(session_id).unlink(missing_ok=True)


DEFAULT_COMPOSED_STORE = ComposedStore()


def has_pending_composed(request) -> bool:
    if not looks_like_resume(request):
        return False
    # Bind validation happens in run_composed, so stale cards are rejected
    # explicitly rather than silently falling through to ordinary SQL.
    return DEFAULT_COMPOSED_STORE.path(request.session_id).is_file()
