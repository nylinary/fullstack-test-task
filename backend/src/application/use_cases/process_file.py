"""Асинхронный конвейер после загрузки: сканирование -> метаданные -> алерт.

Изначально это были три Celery-задачи, вызывавшие друг друга по цепочке, и
каждая заново открывала сессию к базе и заново читала ту же строку. Это три
разных бизнес-шага, поэтому здесь они остаются тремя явными шагами — но
выполняются за один вызов воркера и на одной сессии, что убирает два обращения
к брокеру и два взятия соединения на каждую загрузку. Границы коммитов не
изменились, поэтому промежуточные состояния («processing», вердикт сканера до
метаданных) наблюдаемы ровно как раньше.
"""

import logging
from typing import Any

from src.domain.entities import StoredFile
from src.domain.repositories import UnitOfWork, UnitOfWorkFactory
from src.domain.services.alert_policy import AlertPolicy
from src.domain.services.metadata import MetadataExtractor
from src.domain.services.threat_scanner import ThreatScanner
from src.domain.storage import FileStorage

logger = logging.getLogger(__name__)

MISSING_CONTENT_REASON = "stored file not found during metadata extraction"


class ProcessFileUseCase:
    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        storage: FileStorage,
        scanner: ThreatScanner,
        metadata_extractor: MetadataExtractor,
        alert_policy: AlertPolicy,
    ) -> None:
        self._uow_factory = uow_factory
        self._storage = storage
        self._scanner = scanner
        self._metadata_extractor = metadata_extractor
        self._alert_policy = alert_policy

    async def execute(self, file_id: str) -> None:
        async with self._uow_factory() as uow:
            file = await uow.files.get(file_id)
            if file is None:
                # Файл удалили, пока задача лежала в очереди: обрабатывать
                # нечего и алертить не о чем.
                logger.warning("Skipping processing of unknown file %s", file_id)
                return

            await self._scan(uow, file)
            await self._extract_metadata(uow, file)
            await self._raise_alert(uow, file)

    async def _scan(self, uow: UnitOfWork, file: StoredFile) -> None:
        file.start_processing()
        file.apply_scan(self._scanner.scan(file))
        await uow.commit()

    async def _extract_metadata(self, uow: UnitOfWork, file: StoredFile) -> None:
        if not await self._storage.exists(file.stored_name):
            file.mark_failed(MISSING_CONTENT_REASON)
        else:
            file.apply_metadata(await self._collect_metadata(file))
        await uow.commit()

    async def _collect_metadata(self, file: StoredFile) -> dict[str, Any]:
        metadata = self._metadata_extractor.base_metadata(file)

        analyzer = self._metadata_extractor.analyzer_for(file.mime_type)
        if analyzer is not None:
            # Постоянный расход памяти: файл читается чанк за чанком и целиком
            # нигде не материализуется.
            async for chunk in self._storage.read_chunks(file.stored_name):
                analyzer.feed(chunk)
            metadata.update(analyzer.result())

        return metadata

    async def _raise_alert(self, uow: UnitOfWork, file: StoredFile) -> None:
        await uow.alerts.add(self._alert_policy.build(file))
        await uow.commit()
