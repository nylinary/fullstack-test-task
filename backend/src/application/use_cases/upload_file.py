"""Загрузить файл, сохранить его запись и поставить асинхронную обработку в очередь."""

import logging
from collections.abc import AsyncIterator
from uuid import uuid4

from src.application.dto import UploadFileCommand
from src.application.ports import FileProcessingQueue, IdGenerator
from src.domain.entities import StoredFile
from src.domain.errors import EmptyFileError, FileTooLargeError
from src.domain.repositories import UnitOfWorkFactory
from src.domain.services.naming import file_extension, guess_mime_type, sanitize_filename
from src.domain.storage import FileStorage

logger = logging.getLogger(__name__)


class UploadFileUseCase:
    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        storage: FileStorage,
        queue: FileProcessingQueue,
        max_upload_size: int,
        id_generator: IdGenerator = lambda: str(uuid4()),
    ) -> None:
        self._uow_factory = uow_factory
        self._storage = storage
        self._queue = queue
        self._max_upload_size = max_upload_size
        self._id_generator = id_generator

    async def execute(self, command: UploadFileCommand) -> StoredFile:
        # Проверяем до обращения к хранилищу: отклонённая команда не должна
        # оставлять за собой файл на диске.
        title = StoredFile.normalize_title(command.title)

        file_id = self._id_generator()
        original_name = sanitize_filename(command.original_name or "", fallback=file_id)
        stored_name = f"{file_id}{file_extension(original_name)}"

        size = await self._store_content(stored_name, command.chunks)

        file = StoredFile.create(
            id=file_id,
            title=title,
            original_name=original_name,
            stored_name=stored_name,
            mime_type=command.declared_mime_type or guess_mime_type(stored_name),
            size=size,
        )

        try:
            async with self._uow_factory() as uow:
                await uow.files.add(file)
                await uow.commit()
        except Exception:
            # Не оставляем осиротевший файл, если строку записать не удалось.
            await self._storage.delete(stored_name)
            raise

        await self._queue.enqueue_processing(file.id)
        return file

    async def _store_content(self, stored_name: str, chunks: AsyncIterator[bytes]) -> int:
        """Писать загрузку прямо в хранилище потоком, попутно следя за лимитом размера."""
        try:
            size = await self._storage.save(stored_name, self._capped(chunks))
        except Exception:
            await self._storage.delete(stored_name)
            raise

        if size == 0:
            await self._storage.delete(stored_name)
            raise EmptyFileError()
        return size

    async def _capped(self, chunks: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """Оборвать поток сразу, как только он превысит лимит, а не буферизовать целиком."""
        written = 0
        async for chunk in chunks:
            written += len(chunk)
            if written > self._max_upload_size:
                raise FileTooLargeError(written, self._max_upload_size)
            yield chunk
