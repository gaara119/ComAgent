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


def _project_path(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else PROJECT_ROOT / value


def _decimal(name: str, default: float, minimum: float = 0, maximum: float = 1) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"配置 {name} 必须为数值") from exc
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
    llm_request_max_attempts: int | None = None
    llm_max_tokens: int = 2048
    llm_thinking: bool = False
    llm_temperature: float = 0.0
    catalog_path: Path = PROJECT_ROOT / "data/catalog/chinook.yaml"
    statement_timeout_ms: int = 5000
    max_rows: int = 200
    sql_repair_attempts: int = 2
    typed_sql_compiler_enabled: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    rag_handler: str = "qa_agent.rag.service:run_doc_qa"
    aw_db_url: str = field(default="", repr=False)
    aw_catalog_path: Path = PROJECT_ROOT / "data/catalog/adventureworks.yaml"
    aw_schema_index_path: Path = PROJECT_ROOT / "data/indexes/schema-aw-d3-v2"
    aw_schema_mode: str = "subgraph"
    aw_schema_pruning_enabled: bool = True
    rag_manifest_path: Path = PROJECT_ROOT / "data/docs/manifest.csv"
    rag_index_path: Path = PROJECT_ROOT / "data/processed/rag/ohr"
    bge_model_path: Path = PROJECT_ROOT / "data/models/bge-m3"
    rag_top_k: int = 8
    rag_candidate_k: int = 20
    rag_rrf_k: int = 60
    rag_retrieval_strategy: str = "hybrid"
    rag_cache_enabled: bool = True
    rag_chunk_chars: int = 500
    rag_chunk_overlap: int = 80
    rag_ocr_model_path: Path = PROJECT_ROOT / "data/models/rapidocr"
    rag_embedding_max_length: int = 512
    rag_embedding_batch_size: int = 2
    rag_embedding_device: str = "cpu"
    rag_embedding_quantization: str = "int8"
    rag_answer_mode: str = "llm"
    nlu_enabled: bool = True
    value_index_path: Path = PROJECT_ROOT / "data/indexes/values"
    nlu_fuzzy_threshold: float = 0.82
    nlu_fuzzy_margin: float = 0.08
    nlu_vector_threshold: float = 0.82
    nlu_vector_margin: float = 0.08

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key.strip())

    def public(self) -> dict:
        return {
            "llm_configured": self.llm_configured,
            "model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "llm_temperature_effective": None if self.llm_thinking else self.llm_temperature,
            "llm_thinking": self.llm_thinking,
            "llm_max_tokens": self.llm_max_tokens,
            "llm_timeout_seconds": self.llm_timeout_seconds,
            "catalog_exists": self.catalog_path.is_file(),
            "statement_timeout_ms": self.statement_timeout_ms,
            "max_rows": self.max_rows,
            "llm_call_max_attempts": self.llm_max_attempts,
            "llm_request_max_attempts": self.llm_request_max_attempts or self.llm_max_attempts,
            "aw_configured": bool(self.aw_db_url),
            "aw_catalog_exists": self.aw_catalog_path.is_file(),
            "aw_schema_index_exists": self.aw_schema_index_path.is_dir(),
            "aw_schema_mode": self.aw_schema_mode,
            "aw_schema_pruning_enabled": self.aw_schema_pruning_enabled,
            "typed_sql_compiler_enabled": self.typed_sql_compiler_enabled,
            "rag_retrieval_strategy": self.rag_retrieval_strategy,
            "rag_cache_enabled": self.rag_cache_enabled,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    configured_path = Path(os.getenv("CATALOG_PATH", "data/catalog/chinook.yaml"))
    catalog_path = configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path
    return Settings(
        db_url=os.getenv("CHINOOK_DB_URL", "").strip() or os.getenv("DB_URL", ""),
        llm_api_key=os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/"),
        llm_model=os.getenv("LLM_MODEL", "deepseek-flash"),
        llm_timeout_seconds=_integer("LLM_TIMEOUT_SECONDS", 60, maximum=300),
        llm_max_attempts=_integer("LLM_MAX_ATTEMPTS", 3, maximum=5),
        llm_request_max_attempts=(
            _integer("LLM_REQUEST_MAX_ATTEMPTS", 12, maximum=30)
            if os.getenv("LLM_REQUEST_MAX_ATTEMPTS", "").strip() else None
        ),
        llm_max_tokens=_integer("LLM_MAX_TOKENS", 2048, maximum=16384),
        llm_thinking=os.getenv("LLM_THINKING", "false").lower() in {"true", "1", "yes"},
        llm_temperature=_decimal("LLM_TEMPERATURE", 0.0, maximum=2),
        catalog_path=catalog_path,
        statement_timeout_ms=_integer(
            "SQL_STATEMENT_TIMEOUT_MS" if os.getenv("SQL_STATEMENT_TIMEOUT_MS", "").strip()
            else "STATEMENT_TIMEOUT_MS", 5000, maximum=60000),
        max_rows=_integer("MAX_RESULT_ROWS", 200, maximum=5000),
        sql_repair_attempts=_integer("SQL_REPAIR_ATTEMPTS", 2, minimum=0, maximum=2),
        typed_sql_compiler_enabled=os.getenv("TYPED_SQL_COMPILER_ENABLED", "true").lower() not in {"false", "0", "no"},
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=_integer("API_PORT", 8000, maximum=65535),
        rag_handler=os.getenv("RAG_HANDLER", "qa_agent.rag.service:run_doc_qa"),
        aw_db_url=os.getenv("AW_DB_URL", ""),
        aw_catalog_path=_project_path("AW_CATALOG_PATH", "data/catalog/adventureworks.yaml"),
        aw_schema_index_path=_project_path("AW_SCHEMA_INDEX_PATH", "data/indexes/schema-aw-d3-v2"),
        aw_schema_mode=os.getenv("AW_SCHEMA_MODE", "subgraph"),
        aw_schema_pruning_enabled=os.getenv("AW_SCHEMA_PRUNING_ENABLED", "true").lower() in {"true", "1", "yes", "on"},
        rag_manifest_path=_project_path("RAG_MANIFEST_PATH", "data/docs/manifest.csv"),
        rag_index_path=_project_path("RAG_INDEX_PATH", "data/processed/rag/ohr"),
        bge_model_path=_project_path("BGE_MODEL_PATH", "data/models/bge-m3"),
        rag_top_k=_integer("RAG_TOP_K", 8, maximum=100),
        rag_candidate_k=_integer("RAG_CANDIDATE_K", 20, maximum=200),
        rag_rrf_k=_integer("RAG_RRF_K", 60, maximum=1000),
        rag_retrieval_strategy=os.getenv("RAG_RETRIEVAL_STRATEGY", "hybrid"),
        rag_cache_enabled=os.getenv("RAG_CACHE_ENABLED", "true").lower() in {"true", "1", "yes"},
        rag_chunk_chars=_integer("RAG_CHUNK_CHARS", 500, minimum=100, maximum=3000),
        rag_chunk_overlap=_integer("RAG_CHUNK_OVERLAP", 80, minimum=0, maximum=1000),
        rag_ocr_model_path=_project_path("RAPIDOCR_MODEL_PATH", "data/models/rapidocr"),
        rag_embedding_max_length=_integer("RAG_EMBEDDING_MAX_LENGTH", 512, maximum=8192),
        rag_embedding_batch_size=_integer("RAG_EMBEDDING_BATCH_SIZE", 2, maximum=256),
        rag_embedding_device=os.getenv("RAG_EMBEDDING_DEVICE", "cpu"),
        rag_embedding_quantization=os.getenv("RAG_EMBEDDING_QUANTIZATION", "int8"),
        rag_answer_mode=os.getenv("RAG_ANSWER_MODE", "llm"),
        nlu_enabled=os.getenv("NLU_ENABLED", "true").lower() in {"true", "1", "yes"},
        value_index_path=_project_path("VALUE_INDEX_PATH", "data/indexes/values"),
        nlu_fuzzy_threshold=_decimal("NLU_FUZZY_THRESHOLD", 0.82),
        nlu_fuzzy_margin=_decimal("NLU_FUZZY_MARGIN", 0.08),
        nlu_vector_threshold=_decimal("NLU_VECTOR_THRESHOLD", 0.82),
        nlu_vector_margin=_decimal("NLU_VECTOR_MARGIN", 0.08),
    )


def sanitize_error(value: object, settings: Settings | None = None) -> str:
    """Remove credential-bearing strings before errors reach traces or clients."""
    message = str(value)
    if settings:
        for secret in (settings.llm_api_key, settings.db_url, settings.aw_db_url,
                       os.getenv("POSTGRES_PASSWORD", ""), os.getenv("DB_READER_PASSWORD", "")):
            if secret:
                message = message.replace(secret, "[redacted]")
    message = re.sub(r"postgres(?:ql)?://[^\s]+", "postgresql://[redacted]", message)
    message = re.sub(r"(?i)(bearer\s+)[^\s\"']+", r"\1[redacted]", message)
    message = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", message)
    return message[:1600]
