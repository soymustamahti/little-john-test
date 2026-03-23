import re
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
EnvLevel = Literal["DEVELOPMENT", "PRODUCTION", "LOCAL"]


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="POSTGRES_",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Database host")
    port: str = Field(default="5432", description="Database port")
    db: str = Field(default="postgres", description="Database name")
    user: str = Field(default="postgres", description="Database username")
    password: SecretStr = Field(default=SecretStr("postgres"), description="Database password")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    ssl: bool = Field(default=False, description="Use SSL connection")
    pool_size: int = Field(default=5, ge=1, le=20, description="connection pool size")
    max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow connections")

    @staticmethod
    def _normalize_scheme(url: str, target_scheme: str) -> str:
        return re.sub(r"^postgres(?:ql)?(\+\w+)?://", f"{target_scheme}://", url)

    @property
    def url(self) -> str:
        if self.database_url:
            return self._normalize_scheme(self.database_url, "postgresql+psycopg")
        ssl_param = "?sslmode=require" if self.ssl else ""
        return (
            f"postgresql+psycopg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}{ssl_param}"
        )

    @property
    def async_url(self) -> str:
        if self.database_url:
            return self._normalize_scheme(self.database_url, "postgresql+asyncpg")
        ssl_param = "?sslmode=require" if self.ssl else ""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}{ssl_param}"
        )


class R2Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="R2_",
        extra="ignore",
        case_sensitive=False,
    )

    account_id: str = Field(default="", description="Cloudflare account identifier")
    access_key_id: str = Field(default="", description="R2 access key identifier")
    secret_access_key: SecretStr = Field(
        default=SecretStr(""),
        description="R2 secret access key",
    )
    bucket_name: str = Field(default="", description="R2 bucket name")
    public_url: str | None = Field(
        default=None,
        description="Optional public bucket base URL (custom domain or r2.dev)",
    )

    @property
    def endpoint_url(self) -> str:
        return f"https://{self.account_id}.r2.cloudflarestorage.com"

    @property
    def is_configured(self) -> bool:
        return all(
            [
                self.account_id.strip(),
                self.access_key_id.strip(),
                self.secret_access_key.get_secret_value().strip(),
                self.bucket_name.strip(),
            ]
        )


class DocumentUploadSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DOCUMENTS_",
        extra="ignore",
        case_sensitive=False,
    )

    max_upload_size_bytes: int = Field(
        default=25 * 1024 * 1024,
        ge=1,
        description="Maximum accepted upload size in bytes",
    )
    max_concurrent_ingestion_jobs: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum number of concurrent background ingestion jobs",
    )
    classification_excerpt_chars: int = Field(
        default=8_000,
        ge=500,
        le=40_000,
        description="Maximum number of extracted characters sent to classification",
    )
    chunk_max_characters: int = Field(
        default=1_200,
        ge=200,
        le=8_000,
        description="Maximum number of characters per stored retrieval chunk",
    )
    chunk_min_characters: int = Field(
        default=250,
        ge=50,
        le=4_000,
        description="Target minimum chunk size before flushing the current chunk",
    )
    hybrid_candidate_pool_size: int = Field(
        default=12,
        ge=2,
        le=32,
        description="Candidate pool size before hybrid retrieval reranking.",
    )
    pdf_direct_text_min_characters: int = Field(
        default=120,
        ge=1,
        description="Minimum extracted PDF text before OCR fallback is considered unnecessary",
    )
    pdf_direct_text_min_average_characters_per_page: int = Field(
        default=60,
        ge=1,
        description="Minimum average extracted PDF text per page before OCR fallback is skipped",
    )


class OpenAIProviderSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="OPENAI_",
        extra="ignore",
        case_sensitive=False,
    )

    api_key: SecretStr = Field(default=SecretStr(""), description="OpenAI API key")
    classification_model: str = Field(
        default="gpt-4o-mini",
        description="Model used for document classification",
    )
    extraction_model: str = Field(
        default="gpt-4.1-mini",
        description="Model used for document extraction and retrieval planning",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Model used for chunk embeddings",
    )
    reranking_model: str = Field(
        default="gpt-4o-mini",
        description="Model used for remote reranking of retrieval candidates",
    )
    ocr_model: str = Field(
        default="gpt-4o",
        description="Model used for OCR and document transcription",
    )
    request_timeout_seconds: int = Field(
        default=60,
        ge=5,
        le=300,
        description="Timeout for OpenAI API requests",
    )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key.get_secret_value().strip())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    db_echo_log: bool = Field(default=False, alias="DB_ECHO_LOG")
    log_level: LogLevel = Field(default="INFO", description="Logging level")
    env_mode: EnvLevel = Field(default="LOCAL")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    r2: R2Settings = Field(default_factory=R2Settings)
    documents: DocumentUploadSettings = Field(default_factory=DocumentUploadSettings)
    openai_provider: OpenAIProviderSettings = Field(default_factory=OpenAIProviderSettings)

    @property
    def is_production(self) -> bool:
        return self.env_mode == "PRODUCTION"


@lru_cache
def get_settings() -> Settings:
    return Settings()
