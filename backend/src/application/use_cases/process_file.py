"""The asynchronous post-upload pipeline: scan -> extract metadata -> alert.

Originally these were three Celery tasks that chained into each other, each one
re-opening a database session and re-loading the same row.  They are three
distinct business steps, so they stay three explicit steps here - but they run
inside a single worker invocation and a single session, which removes two
broker round-trips and two connection acquisitions per upload.  The commit
boundaries are unchanged, so the intermediate states ("processing", scan
verdict before metadata) remain observable exactly as before.
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
                # The file was deleted while the job sat in the queue: nothing
                # to process and nothing to alert about.
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
            # Constant memory: the file is consumed chunk by chunk and never
            # materialised in full.
            async for chunk in self._storage.read_chunks(file.stored_name):
                analyzer.feed(chunk)
            metadata.update(analyzer.result())

        return metadata

    async def _raise_alert(self, uow: UnitOfWork, file: StoredFile) -> None:
        await uow.alerts.add(self._alert_policy.build(file))
        await uow.commit()
