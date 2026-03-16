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

    ssl: bool = Field(default=False, description="Use SSL connection")
    pool_size: int = Field(default=5, ge=1, le=20, description="connection pool size")
    max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow connections")

    @property
    def url(self) -> str:
        ssl_param = "?sslmode=require" if self.ssl else ""
        return (
            f"postgresql+psycopg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}{ssl_param}"
        )

    @property
    def async_url(self) -> str:
        ssl_param = "?sslmode=require" if self.ssl else ""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.db}{ssl_param}"
        )


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

    @property
    def is_production(self) -> bool:
        return self.env_mode == "PRODUCTION"


@lru_cache
def get_settings() -> Settings:
    return Settings()
