"""Реализации доменных портов репозиториев на SQLAlchemy."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Alert, StoredFile
from src.infrastructure.db.tables import alerts_table, files_table


class SqlAlchemyFileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, file: StoredFile) -> None:
        self._session.add(file)

    async def get(self, file_id: str) -> StoredFile | None:
        return await self._session.get(StoredFile, file_id)

    async def list_recent(self, *, limit: int, offset: int) -> list[StoredFile]:
        stmt = (
            select(StoredFile)
            # ``id`` разрешает ничьи, чтобы при одинаковых метках времени
            # пагинация не показала и не пропустила строку дважды.
            .order_by(files_table.c.created_at.desc(), files_table.c.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, file: StoredFile) -> None:
        await self._session.delete(file)


class SqlAlchemyAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, alert: Alert) -> None:
        self._session.add(alert)

    async def list_recent(self, *, limit: int, offset: int) -> list[Alert]:
        stmt = (
            select(Alert)
            .order_by(alerts_table.c.created_at.desc(), alerts_table.c.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
