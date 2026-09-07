"""Use case'ы чтения и жизненного цикла для файлов и алертов."""

from src.application.dto import FileDownload, Page
from src.domain.entities import Alert, StoredFile
from src.domain.errors import StoredContentNotFoundError, StoredFileNotFoundError
from src.domain.repositories import UnitOfWork, UnitOfWorkFactory
from src.domain.storage import FileStorage


async def _require_file(uow: UnitOfWork, file_id: str) -> StoredFile:
    file = await uow.files.get(file_id)
    if file is None:
        raise StoredFileNotFoundError(file_id)
    return file


class ListFilesUseCase:
    def __init__(self, *, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, page: Page) -> list[StoredFile]:
        async with self._uow_factory() as uow:
            return await uow.files.list_recent(limit=page.limit, offset=page.offset)


class ListAlertsUseCase:
    def __init__(self, *, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, page: Page) -> list[Alert]:
        async with self._uow_factory() as uow:
            return await uow.alerts.list_recent(limit=page.limit, offset=page.offset)


class GetFileUseCase:
    def __init__(self, *, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, file_id: str) -> StoredFile:
        async with self._uow_factory() as uow:
            return await _require_file(uow, file_id)


class RenameFileUseCase:
    def __init__(self, *, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, file_id: str, title: str) -> StoredFile:
        async with self._uow_factory() as uow:
            file = await _require_file(uow, file_id)
            file.rename(title)
            await uow.commit()
            return file


class DeleteFileUseCase:
    def __init__(self, *, uow_factory: UnitOfWorkFactory, storage: FileStorage) -> None:
        self._uow_factory = uow_factory
        self._storage = storage

    async def execute(self, file_id: str) -> None:
        async with self._uow_factory() as uow:
            file = await _require_file(uow, file_id)
            stored_name = file.stored_name
            await uow.files.delete(file)
            # Сначала удаляется строка: если транзакция упадёт, файл на диске
            # останется. Исходный порядок мог уничтожить содержимое файла,
            # который при этом остался в базе.
            await uow.commit()

        await self._storage.delete(stored_name)


class DownloadFileUseCase:
    def __init__(self, *, uow_factory: UnitOfWorkFactory, storage: FileStorage) -> None:
        self._uow_factory = uow_factory
        self._storage = storage

    async def execute(self, file_id: str) -> FileDownload:
        async with self._uow_factory() as uow:
            file = await _require_file(uow, file_id)

        if not await self._storage.exists(file.stored_name):
            raise StoredContentNotFoundError(file.stored_name)

        return FileDownload(
            file=file,
            open_stream=lambda: self._storage.read_chunks(file.stored_name),
            local_path=self._storage.local_path(file.stored_name),
        )
