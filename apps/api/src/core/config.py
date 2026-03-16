from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

from functools import lru_cache


EnvLevel = Literal["DEVELOPMENT", "PRODUCTION", "LOCAL"]


class DatabaseSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DATABASE_",
        extra="ignore",
    )

    host: str = Field(default="localhost", description="Database host")
    port: str = Field(default="5423", description="Databse port")
    db: str = Field(default="postgres", description="Databse name")
    user: str = Field(default="postgres", description="Databse username")
    password: SecretStr = Field(
        default=SecretStr("postgres"), description="Database password"
    )

    ssl: bool = Field(default=False, description="Use SSL connection")
    pool_size: int = Field(default=5, ge=1, le=20, description="connection pool size")
    max_overflow: int = Field(
        default=10, ge=0, le=50, description="Max overflow connections"
    )

    @property
    def url(self) -> str:
        ssl_param = "?sslmode=require" if self.ssl else ""
        return (
            f"postgresql://{self.username}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.name}{ssl_param}"
        )

    @property
    def async_url(self) -> str:
        ssl_param = "?sslmode=require" if self.ssl else ""
        return (
            f"postgresql+asyncpg://{self.username}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.name}{ssl_param}"
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    env_mode: EnvLevel = Field(default="LOCAL")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
