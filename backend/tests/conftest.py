"""Shared fixtures.

The suite never needs Postgres or Redis: the domain and application layers only
know about ports, so tests plug in SQLite and in-memory doubles.
"""

import sqlite3
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.container import Container
from src.infrastructure.config import Settings
from src.infrastructure.db.engine import create_session_factory
from src.infrastructure.db.tables import metadata
from src.infrastructure.storage.local import LocalFileStorage
from tests.doubles import RecordingQueue


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(storage_dir=tmp_path / "files", max_upload_size=1024 * 1024)


@pytest.fixture
async def engine(tmp_path: Path) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_foreign_keys(connection: sqlite3.Connection, _: object) -> None:
        # SQLite ignores foreign keys unless asked, and we want the
        # ON DELETE CASCADE behaviour to be exercised here too.
        connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
def queue() -> RecordingQueue:
    return RecordingQueue()


@pytest.fixture
def container(settings: Settings, engine: AsyncEngine, queue: RecordingQueue) -> Container:
    container = Container(settings=settings)
    # ``cached_property`` reads through ``__dict__``: seeding it swaps the real
    # Postgres engine and Celery broker for test doubles without any patching.
    container.__dict__["engine"] = engine
    container.__dict__["session_factory"] = create_session_factory(engine)
    container.__dict__["storage"] = LocalFileStorage(settings.storage_dir)
    container.__dict__["queue"] = queue
    return container
