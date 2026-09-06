"""Persistence ports.

Declared in the domain and implemented in the infrastructure layer, so the
dependency arrow points inwards: use cases depend on these protocols, never on
SQLAlchemy.
"""

from types import TracebackType
from typing import Protocol

from src.domain.entities import Alert, StoredFile


class FileRepository(Protocol):
    async def add(self, file: StoredFile) -> None: ...

    async def get(self, file_id: str) -> StoredFile | None: ...

    async def list_recent(self, *, limit: int, offset: int) -> list[StoredFile]: ...

    async def delete(self, file: StoredFile) -> None: ...


class AlertRepository(Protocol):
    async def add(self, alert: Alert) -> None: ...

    async def list_recent(self, *, limit: int, offset: int) -> list[Alert]: ...


class UnitOfWork(Protocol):
    """A transactional scope grouping the repositories.

    Used as an async context manager; leaving the block without an explicit
    :meth:`commit` rolls back.
    """

    files: FileRepository
    alerts: AlertRepository

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> UnitOfWork: ...
