"""Composition root.

Единственный модуль, которому позволено знать про все слои сразу: он подставляет
конкретные адаптеры в use case'ы. Всё остальное зависит от абстракций.
"""

from dataclasses import dataclass
from functools import cached_property, lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from src.application.ports import FileProcessingQueue
from src.application.use_cases.manage_files import (
    DeleteFileUseCase,
    DownloadFileUseCase,
    GetFileUseCase,
    ListAlertsUseCase,
    ListFilesUseCase,
    RenameFileUseCase,
)
from src.application.use_cases.process_file import ProcessFileUseCase
from src.application.use_cases.upload_file import UploadFileUseCase
from src.domain.repositories import UnitOfWork
from src.domain.services.alert_policy import AlertPolicy
from src.domain.services.metadata import MetadataExtractor
from src.domain.services.threat_scanner import ThreatScanner
from src.domain.storage import FileStorage
from src.infrastructure.config import Settings, get_settings
from src.infrastructure.db.engine import create_engine, create_session_factory
from src.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.queue.celery_app import celery_app
from src.infrastructure.queue.task_queue import CeleryFileProcessingQueue
from src.infrastructure.storage.local import LocalFileStorage


@dataclass
class Container:
    settings: Settings

    @cached_property
    def engine(self) -> AsyncEngine:
        return create_engine(self.settings)

    @cached_property
    def session_factory(self) -> async_sessionmaker:
        return create_session_factory(self.engine)

    @cached_property
    def storage(self) -> FileStorage:
        return LocalFileStorage(self.settings.storage_dir, self.settings.download_chunk_size)

    @cached_property
    def queue(self) -> FileProcessingQueue:
        return CeleryFileProcessingQueue(celery_app)

    @cached_property
    def scanner(self) -> ThreatScanner:
        return ThreatScanner()

    @cached_property
    def metadata_extractor(self) -> MetadataExtractor:
        return MetadataExtractor()

    @cached_property
    def alert_policy(self) -> AlertPolicy:
        return AlertPolicy()

    def unit_of_work(self) -> UnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory)

    # --- use case'ы ------------------------------------------------------

    def upload_file(self) -> UploadFileUseCase:
        return UploadFileUseCase(
            uow_factory=self.unit_of_work,
            storage=self.storage,
            queue=self.queue,
            max_upload_size=self.settings.max_upload_size,
        )

    def list_files(self) -> ListFilesUseCase:
        return ListFilesUseCase(uow_factory=self.unit_of_work)

    def list_alerts(self) -> ListAlertsUseCase:
        return ListAlertsUseCase(uow_factory=self.unit_of_work)

    def get_file(self) -> GetFileUseCase:
        return GetFileUseCase(uow_factory=self.unit_of_work)

    def rename_file(self) -> RenameFileUseCase:
        return RenameFileUseCase(uow_factory=self.unit_of_work)

    def delete_file(self) -> DeleteFileUseCase:
        return DeleteFileUseCase(uow_factory=self.unit_of_work, storage=self.storage)

    def download_file(self) -> DownloadFileUseCase:
        return DownloadFileUseCase(uow_factory=self.unit_of_work, storage=self.storage)

    def process_file(self) -> ProcessFileUseCase:
        return ProcessFileUseCase(
            uow_factory=self.unit_of_work,
            storage=self.storage,
            scanner=self.scanner,
            metadata_extractor=self.metadata_extractor,
            alert_policy=self.alert_policy,
        )

    async def dispose(self) -> None:
        if "engine" in self.__dict__:
            await self.engine.dispose()


@lru_cache(maxsize=1)
def get_container() -> Container:
    """Синглтон на процесс: один engine и один пул соединений на процесс."""
    return Container(settings=get_settings())
