"""Application-level ports for outbound infrastructure."""

from typing import Protocol


class FileProcessingQueue(Protocol):
    """Hands a freshly uploaded file over to the asynchronous pipeline."""

    async def enqueue_processing(self, file_id: str) -> None: ...


class IdGenerator(Protocol):
    """Supplies identifiers for new aggregates (injected so tests stay deterministic)."""

    def __call__(self) -> str: ...
