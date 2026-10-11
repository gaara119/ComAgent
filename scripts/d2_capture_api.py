"""Opt-in recording wrapper around the project's unchanged real FastAPI app.

Run only for D2 evidence: set D2_CAPTURE_DIR to a project-local directory,
then ``python -m uvicorn scripts.d2_capture_api:app --host 127.0.0.1 --port 8000``.
The same /api/chat handler is called once. Headers and secrets are never stored.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from api.main import app
from qa_agent.config import PROJECT_ROOT, get_settings


def _safe(value):
    if isinstance(value, dict):
        return {key: _safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe(item) for item in value]
    if not isinstance(value, str):
        return value
    settings = get_settings()
    for secret in (settings.llm_api_key, settings.db_url, settings.aw_db_url,
                   os.getenv("POSTGRES_PASSWORD", ""), os.getenv("DB_READER_PASSWORD", "")):
        if secret:
            value = value.replace(secret, "[redacted]")
    value = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", value)
    value = re.sub(r"(?i)Bearer\s+\S+", "Bearer [redacted]", value)
    return re.sub(r"(?i)postgres(?:ql)?://[^\s]+", "postgresql://[redacted]", value)


class D2EvidenceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        configured = os.getenv("D2_CAPTURE_DIR", "")
        if not configured or request.method != "POST" or request.url.path != "/api/chat":
            return await call_next(request)
        directory = Path(configured)
        directory = directory if directory.is_absolute() else PROJECT_ROOT/directory
        directory = directory.resolve()
        if not directory.is_relative_to(PROJECT_ROOT):
            raise RuntimeError("D2_CAPTURE_DIR must stay in the existing project")
        requested_at = datetime.now(timezone.utc).isoformat()
        body = await request.body()
        response = await call_next(request)
        raw = b"".join([part async for part in response.body_iterator])
        try:
            request_data, response_data = json.loads(body), json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # /api/chat normally emits JSON; don't capture arbitrary binary data.
            return Response(raw, status_code=response.status_code, headers=dict(response.headers),
                            media_type=response.media_type)
        directory.mkdir(parents=True, exist_ok=True)
        record = {"started_at_utc": requested_at, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                  "method": "POST", "path": "/api/chat", "http_status": response.status_code,
                  "request": request_data, "response": response_data,
                  "recording": "one actual existing API invocation; headers omitted; credential strings redacted"}
        filename = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-"+str(uuid4())+".json"
        (directory/filename).write_text(json.dumps(_safe(record), ensure_ascii=False, indent=2), encoding="utf-8")
        return Response(raw, status_code=response.status_code, headers=dict(response.headers),
                        media_type=response.media_type)


app.add_middleware(D2EvidenceMiddleware)
