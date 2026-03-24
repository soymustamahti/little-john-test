from src.core.config import DatabaseSettings, Settings


def test_database_settings_prefers_database_url(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://docker_user:docker_password@db.example.com:5432/extract_agent?sslmode=require",
    )
    monkeypatch.setenv("POSTGRES_HOST", "wrong-host")
    monkeypatch.setenv("POSTGRES_DB", "wrong-db")

    settings = DatabaseSettings(_env_file=None)

    assert (
        settings.url
        == "postgresql+psycopg://docker_user:docker_password@db.example.com:5432/extract_agent?sslmode=require"
    )
    assert (
        settings.async_url
        == "postgresql+asyncpg://docker_user:docker_password@db.example.com:5432/extract_agent?sslmode=require"
    )


def test_database_settings_falls_back_to_postgres_fields(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "extract_agent")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("POSTGRES_HOST", "postgres")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "extract_agent")

    settings = DatabaseSettings(_env_file=None)

    assert settings.url == "postgresql+psycopg://extract_agent:secret@postgres:5432/extract_agent"
    assert (
        settings.async_url
        == "postgresql+asyncpg://extract_agent:secret@postgres:5432/extract_agent"
    )


def test_settings_is_production_uses_env_mode(monkeypatch) -> None:
    monkeypatch.setenv("ENV_MODE", "PRODUCTION")

    settings = Settings(_env_file=None)

    assert settings.is_production is True
