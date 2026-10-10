"""Project-local configuration; credentials never appear in public settings."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _integer(name: str, default: int, minimum: int = 1, maximum: int = 1000000) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"配置 {name} 必须为整数") from exc
    if not minimum <= value <= maximum:
        raise ValueError(f"配置 {name} 必须在 {minimum}–{maximum} 范围内")
    return value


@dataclass(frozen=True)
class Settings:
    db_url: str = field(repr=False)
    llm_api_key: str = field(default="", repr=False)
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-flash"
    llm_timeout_seconds: int = 60
    llm_max_attempts: int = 3
    llm_max_tokens: int = 2048
    llm_thinking: bool = False
    catalog_path: Path = PROJECT_ROOT / "data/catalog/chinook.yaml"
    statement_timeout_ms: int = 5000
    max_rows: int = 200
    sql_repair_attempts: int = 2
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    rag_handler: str = "qa_agent.rag.service:run_doc_qa"

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key.strip())

    def public(self) -> dict:
        return {
            "llm_configured": self.llm_configured,
            "model": self.llm_model,
            "catalog_exists": self.catalog_path.is_file(),
            "statement_timeout_ms": self.statement_timeout_ms,
            "max_rows": self.max_rows,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    configured_path = Path(os.getenv("CATALOG_PATH", "data/catalog/chinook.yaml"))
    catalog_path = configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path
    return Settings(
        db_url=os.getenv("DB_URL", ""),
        llm_api_key=os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/"),
        llm_model=os.getenv("LLM_MODEL", "deepseek-flash"),
        llm_timeout_seconds=_integer("LLM_TIMEOUT_SECONDS", 60, maximum=300),
        llm_max_attempts=_integer("LLM_MAX_ATTEMPTS", 3, maximum=5),
        llm_max_tokens=_integer("LLM_MAX_TOKENS", 2048, maximum=16384),
        llm_thinking=os.getenv("LLM_THINKING", "false").lower() in {"true", "1", "yes"},
        catalog_path=catalog_path,
        statement_timeout_ms=_integer("STATEMENT_TIMEOUT_MS", 5000, maximum=60000),
        max_rows=_integer("MAX_RESULT_ROWS", 200, maximum=5000),
        sql_repair_attempts=_integer("SQL_REPAIR_ATTEMPTS", 2, minimum=0, maximum=2),
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=_integer("API_PORT", 8000, maximum=65535),
        rag_handler=os.getenv("RAG_HANDLER", "qa_agent.rag.service:run_doc_qa"),
    )


def sanitize_error(value: object, settings: Settings | None = None) -> str:
    """Remove credential-bearing strings before errors reach traces or clients."""
    message = str(value)
    if settings:
        for secret in (settings.llm_api_key, settings.db_url,
                       os.getenv("POSTGRES_PASSWORD", ""), os.getenv("DB_READER_PASSWORD", "")):
            if secret:
                message = message.replace(secret, "[redacted]")
    message = re.sub(r"postgres(?:ql)?://[^\s]+", "postgresql://[redacted]", message)
    message = re.sub(r"(?i)(bearer\s+)[^\s\"']+", r"\1[redacted]", message)
    message = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", message)
    return message[:1600]
