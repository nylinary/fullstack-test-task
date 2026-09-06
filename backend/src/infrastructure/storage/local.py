"""Filesystem-backed implementation of the :class:`~src.domain.storage.FileStorage` port.

Every operation is awaited off the event loop (``anyio``), so a slow disk can no
longer stall the whole API process the way the previous blocking
``Path.write_bytes`` / ``Path.exists`` calls did.
"""

import logging
from collections.abc import AsyncIterator
from pathlib import Path

import anyio

from src.domain.storage import DEFAULT_CHUNK_SIZE

logger = logging.getLogger(__name__)


class UnsafeStoredNameError(ValueError):
    """Raised when a stored name would resolve outside the storage root."""


class LocalFileStorage:
    def __init__(self, root: Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._chunk_size = chunk_size

    async def save(self, stored_name: str, chunks: AsyncIterator[bytes]) -> int:
        path = self._resolve(stored_name)
        size = 0
        async with await anyio.open_file(path, "wb") as handle:
            async for chunk in chunks:
                if not chunk:
                    continue
                await handle.write(chunk)
                size += len(chunk)
        return size

    async def read_chunks(self, stored_name: str, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        path = self._resolve(stored_name)
        async with await anyio.open_file(path, "rb") as handle:
            while chunk := await handle.read(chunk_size or self._chunk_size):
                yield chunk

    async def delete(self, stored_name: str) -> None:
        try:
            await anyio.Path(self._resolve(stored_name)).unlink(missing_ok=True)
        except OSError:
            # Losing a blob must not fail the surrounding transaction; the row
            # is already gone and the leftover is visible in the logs.
            logger.exception("Could not delete stored file %s", stored_name)

    async def exists(self, stored_name: str) -> bool:
        return await anyio.Path(self._resolve(stored_name)).is_file()

    def local_path(self, stored_name: str) -> Path | None:
        return self._resolve(stored_name)

    def _resolve(self, stored_name: str) -> Path:
        candidate = (self._root / stored_name).resolve()
        if candidate.parent != self._root:
            raise UnsafeStoredNameError(f"Refusing to access {stored_name!r} outside the storage root")
        return candidate
