"""Transactional scope backed by an ``AsyncSession``."""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.repositories import AlertRepository, FileRepository
from src.infrastructure.db.repositories import SqlAlchemyAlertRepository, SqlAlchemyFileRepository


class SqlAlchemyUnitOfWork:
    """One session, one transaction, both repositories.

    Leaving the ``async with`` block without committing rolls the transaction
    back, so a failing use case can never half-persist an aggregate.
    """

    files: FileRepository
    alerts: AlertRepository

    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.files = SqlAlchemyFileRepository(self._session)
        self.alerts = SqlAlchemyAlertRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        session = self._require_session()
        try:
            if exc_type is not None and session.in_transaction():
                await session.rollback()
        finally:
            # ``close()`` releases the connection, which discards anything that
            # was not committed, and - unlike ``rollback()`` - leaves the loaded
            # entities readable after they are detached.  Use cases return
            # entities to the caller, so that difference matters.
            await session.close()
            self._session = None

    async def commit(self) -> None:
        await self._require_session().commit()

    async def rollback(self) -> None:
        await self._require_session().rollback()

    def _require_session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork must be used inside an 'async with' block")
        return self._session
