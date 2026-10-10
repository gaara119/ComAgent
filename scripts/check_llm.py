"""Discover account models and validate JSON. Never log the key."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import BaseModel
from qa_agent.config import PROJECT_ROOT, get_settings, sanitize_error
from qa_agent.llm import JsonLLM, LLMError
from qa_agent.trace import TraceRecorder


class ProbeAnswer(BaseModel):
    ok: bool
    message: str


def main() -> int:
    settings = get_settings()
    trace = TraceRecorder(settings=settings)
    result = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "configured": settings.llm_configured, "model": settings.llm_model, "success": False}
    if not settings.llm_configured:
        result["reason"] = "missing_llm_key"
        result["action"] = "在本地 .env 配置 LLM_API_KEY 后重新运行本脚本"
    else:
        try:
            client = JsonLLM(settings)
            model_ids = client.list_models()
            result["available_models"] = model_ids
            if settings.llm_model not in model_ids:
                raise LLMError("当前配置的 LLM_MODEL 不在账号返回的模型列表中。", "model_unavailable")
            answer = client.complete_json("你是接口检查助手。", "返回 JSON：ok 为 true，message 为 接入成功。", ProbeAnswer, trace)
            result["success"] = answer.ok and answer.message.strip().rstrip("。.!！") == "接入成功"
            result["probe"] = answer.model_dump()
        except Exception as exc:
            result["reason"] = getattr(exc, "code", "probe_failed")
            result["error"] = sanitize_error(exc, settings)
    result["steps"] = [step.model_dump() for step in trace.steps]
    result["latency_ms"] = trace.latency_ms
    target = PROJECT_ROOT / "notes/model-check.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
