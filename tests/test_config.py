"""Compatibility with the shared environment fields supplied by A/B."""
import pytest

from qa_agent import config


@pytest.fixture
def isolated_config(monkeypatch):
    config.get_settings.cache_clear()
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: None)
    for name in ("CHINOOK_DB_URL", "DB_URL", "SQL_STATEMENT_TIMEOUT_MS", "STATEMENT_TIMEOUT_MS"):
        monkeypatch.delenv(name, raising=False)
    yield monkeypatch
    config.get_settings.cache_clear()


def test_shared_sql_names_take_precedence(isolated_config):
    isolated_config.setenv("CHINOOK_DB_URL", "preferred-test-url")
    isolated_config.setenv("DB_URL", "legacy-test-url")
    isolated_config.setenv("SQL_STATEMENT_TIMEOUT_MS", "4000")
    isolated_config.setenv("STATEMENT_TIMEOUT_MS", "3000")
    settings = config.get_settings()
    assert settings.db_url == "preferred-test-url"
    assert settings.statement_timeout_ms == 4000
    assert "db_url" not in settings.public()
    assert "preferred-test-url" not in repr(settings)


def test_blank_shared_sql_names_fall_back_to_legacy(isolated_config):
    isolated_config.setenv("CHINOOK_DB_URL", "")
    isolated_config.setenv("DB_URL", "legacy-test-url")
    isolated_config.setenv("SQL_STATEMENT_TIMEOUT_MS", "")
    isolated_config.setenv("STATEMENT_TIMEOUT_MS", "3000")
    isolated_config.setenv("RAG_MANIFEST_PATH", "data/docs/manifest.csv")
    isolated_config.setenv("RAG_ANSWER_MODE", "llm")
    settings = config.get_settings()
    assert settings.db_url == "legacy-test-url"
    assert settings.statement_timeout_ms == 3000
    assert settings.rag_manifest_path == config.PROJECT_ROOT / "data/docs/manifest.csv"
    assert settings.rag_answer_mode == "llm"
