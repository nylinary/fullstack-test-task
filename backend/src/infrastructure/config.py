"""Typed application settings.

Replaces the scattered ``os.environ.get(...)`` calls, which silently produced a
DSN containing the literal string ``None`` when a variable was missing.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

MEGABYTE = 1024 * 1024


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"  # noqa: S105 - local-dev fallback, overridden by the environment
    postgres_db: str = "test"
    postgres_host: str = "backend-db"
    pgport: int = 5432

    celery_broker_url: str = "redis://backend-redis:6379/0"
    celery_result_backend: str | None = None

    storage_dir: Path = BASE_DIR / "storage" / "files"
    max_upload_size: int = Field(default=100 * MEGABYTE, gt=0)
    download_chunk_size: int = Field(default=MEGABYTE, gt=0)

    cors_allow_origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")

    log_level: str = "INFO"
    sql_echo: bool = False

    db_pool_size: int = Field(default=5, gt=0)
    db_max_overflow: int = Field(default=10, ge=0)

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.pgport}/{self.postgres_db}"
        )

    @computed_field
    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.celery_broker_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
