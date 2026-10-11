"""Offline-only helpers. No evaluator label is accepted by the request builder."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def json_hash(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_new(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        import os
        os.fsync(handle.fileno())


def safe(value: Any) -> Any:
    """Keep actual payloads but redact credential-shaped text and secret fields."""
    if isinstance(value, dict):
        return {key: ("[redacted]" if re.search(r"(?i)(api.?key|password|authorization|db_url|access_token|secret)", key)
                      else safe(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [safe(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"postgres(?:ql)?://[^\s\"']+", "postgresql://[redacted]", value)
        value = re.sub(r"(?i)(bearer\s+)[^\s\"']+", r"\1[redacted]", value)
        return re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", value)
    return value


def load_cases(path: Path) -> list[dict]:
    # An explicit synthetic dev filename is mandatory: never inspect a mixed corpus.
    if not re.fullmatch(r"cases-(?:normalized-v\d+-auto|v\d+-reviewed)\.jsonl", path.name):
        raise ValueError("Only the explicit normalized/reviewed synthetic dev files are allowed")
    if path.resolve().parent != HERE.parent / "data":
        raise ValueError("Only this experiment's explicit synthetic dev data directory is allowed")
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if len(cases) != 60 or len({item["id"] for item in cases}) != 60:
        raise ValueError("The full fixed denominator must contain 60 unique case IDs")
    for item in cases:
        if item.get("split") != "dev" or item.get("dataset_label") != "本轮合成开发数据":
            raise ValueError("Refusing non-synthetic or non-dev data")
        if item.get("scope") != {"route": "sql", "db_id": "chinook", "doc_ids": []}:
            raise ValueError("Unsupported source scope in dev case")
    return cases


def request_payload(session_id: str, message: str, scope: dict, *, card_id=None, version=None, choice=None) -> dict:
    from qa_agent.schemas import ChatRequest
    payload = {"session_id": session_id, "message": message, "scope": dict(scope)}
    if card_id is not None:
        payload.update(clarification_id=card_id, intent_version=version)
        if choice is not None:
            payload["choice_id"] = choice
    # Validate against the REAL current API contract. Do not discard unsupported resume fields.
    return ChatRequest.model_validate(payload).model_dump(mode="json", exclude_none=True)


def history_messages(case: dict) -> list[str]:
    result = []
    for item in case.get("history") or []:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict) and item.get("role") == "user" and isinstance(item.get("content", item.get("message")), str):
            result.append(item.get("content", item.get("message")))
        else:
            raise ValueError("History must contain genuine prior user input only; assistant predictions cannot be fabricated")
    return result
