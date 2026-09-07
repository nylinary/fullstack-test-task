"""In-memory реализации портов приложения."""

from collections.abc import AsyncIterator
from pathlib import Path
from types import TracebackType

from src.domain.entities import Alert, StoredFile
from src.domain.repositories import AlertRepository, FileRepository


class RecordingQueue:
    """:class:`~src.application.ports.FileProcessingQueue`, который просто запоминает вызовы."""

    def __init__(self) -> None:
        self.enqueued: list[str] = []

    async def enqueue_processing(self, file_id: str) -> None:
        self.enqueued.append(file_id)


class InMemoryStorage:
    """:class:`~src.domain.storage.FileStorage` поверх обычного словаря."""

    def __init__(self, chunk_size: int = 8) -> None:
        self.objects: dict[str, bytes] = {}
        self._chunk_size = chunk_size

    async def save(self, stored_name: str, chunks: AsyncIterator[bytes]) -> int:
        content = b""
        async for chunk in chunks:
            content += chunk
        self.objects[stored_name] = content
        return len(content)

    async def read_chunks(self, stored_name: str, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        content = self.objects[stored_name]
        step = chunk_size or self._chunk_size
        for start in range(0, len(content), step):
            yield content[start : start + step]

    async def delete(self, stored_name: str) -> None:
        self.objects.pop(stored_name, None)

    async def exists(self, stored_name: str) -> bool:
        return stored_name in self.objects

    def local_path(self, stored_name: str) -> Path | None:
        return None


async def chunks_of(data: bytes, size: int = 8) -> AsyncIterator[bytes]:
    for start in range(0, len(data), size):
        yield data[start : start + size]


class InMemoryFileRepository:
    def __init__(self, store: dict[str, StoredFile]) -> None:
        self._store = store

    async def add(self, file: StoredFile) -> None:
        self._store[file.id] = file

    async def get(self, file_id: str) -> StoredFile | None:
        return self._store.get(file_id)

    async def list_recent(self, *, limit: int, offset: int) -> list[StoredFile]:
        return list(self._store.values())[offset : offset + limit]

    async def delete(self, file: StoredFile) -> None:
        self._store.pop(file.id, None)


class InMemoryAlertRepository:
    def __init__(self, store: list[Alert]) -> None:
        self._store = store

    async def add(self, alert: Alert) -> None:
        self._store.append(alert)

    async def list_recent(self, *, limit: int, offset: int) -> list[Alert]:
        return self._store[offset : offset + limit]


class FakeUnitOfWork:
    """Делит состояние между экземплярами, чтобы повторные вызовы ``uow_factory()`` видели те же данные."""

    files: FileRepository
    alerts: AlertRepository

    def __init__(self, files: dict[str, StoredFile], alerts: list[Alert], *, fail_on_commit: bool = False) -> None:
        self._files = files
        self._alerts = alerts
        self.files = InMemoryFileRepository(files)
        self.alerts = InMemoryAlertRepository(alerts)
        self.commits = 0
        self.fail_on_commit = fail_on_commit

    async def __aenter__(self) -> FakeUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        if self.fail_on_commit:
            raise RuntimeError("commit failed")
        self.commits += 1

    async def rollback(self) -> None:
        return None
