"""Транзакционная область поверх ``AsyncSession``."""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.repositories import AlertRepository, FileRepository
from src.infrastructure.db.repositories import SqlAlchemyAlertRepository, SqlAlchemyFileRepository


class SqlAlchemyUnitOfWork:
    """Одна сессия, одна транзакция, оба репозитория.

    Выход из блока ``async with`` без коммита откатывает транзакцию, поэтому
    упавший use case не может сохранить агрегат наполовину.
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
            # ``close()`` возвращает соединение в пул, отбрасывая всё
            # незакоммиченное, и — в отличие от ``rollback()`` — оставляет
            # загруженные сущности читаемыми после отвязки от сессии. Use case'ы
            # возвращают сущности наружу, так что разница существенна.
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
