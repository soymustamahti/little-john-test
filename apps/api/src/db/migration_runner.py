import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from src.core.config import get_settings


def get_alembic_config() -> Config:
    config_path = Path(__file__).resolve().parent / "alembic.ini"
    config = Config(str(config_path))
    config.set_main_option("sqlalchemy.url", get_settings().database.url)
    return config


def run_app_migrations() -> None:
    command.upgrade(get_alembic_config(), "head")


async def run_app_migrations_async() -> None:
    await asyncio.to_thread(run_app_migrations)
