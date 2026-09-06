"""Data carried across the application boundary."""

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path

from src.domain.entities import StoredFile

DEFAULT_PAGE_LIMIT = 100
MAX_PAGE_LIMIT = 500


@dataclass(frozen=True, slots=True)
class Page:
    limit: int = DEFAULT_PAGE_LIMIT
    offset: int = 0


@dataclass(slots=True)
class UploadFileCommand:
    title: str
    original_name: str | None
    declared_mime_type: str | None
    chunks: AsyncIterator[bytes]


@dataclass(slots=True)
class FileDownload:
    """Everything the transport needs to serve a stored file."""

    file: StoredFile
    open_stream: Callable[[], AsyncIterator[bytes]]
    local_path: Path | None = None
