"""Binary storage port."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol

DEFAULT_CHUNK_SIZE = 1024 * 1024


class FileStorage(Protocol):
    async def save(self, stored_name: str, chunks: AsyncIterator[bytes]) -> int:
        """Persist ``chunks`` under ``stored_name`` and return the number of bytes written."""
        ...

    def read_chunks(self, stored_name: str, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        """Stream the stored object back."""
        ...

    async def delete(self, stored_name: str) -> None: ...

    async def exists(self, stored_name: str) -> bool: ...

    def local_path(self, stored_name: str) -> Path | None:
        """Filesystem path of the object, when the adapter is backed by a local disk.

        Purely an optimisation hook: it lets the HTTP layer hand the descriptor
        to the kernel (``sendfile``) instead of pumping bytes through Python.
        Adapters backed by a remote object store return ``None`` and callers
        fall back to :meth:`read_chunks`.
        """
        ...
