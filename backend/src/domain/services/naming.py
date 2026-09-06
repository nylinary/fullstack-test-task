"""Filename helpers shared by the domain and the storage adapters."""

import mimetypes
from pathlib import PurePosixPath, PureWindowsPath

# Everything that could let a crafted upload name escape the storage directory
# or poison a Content-Disposition header.
_UNSAFE_CHARS = str.maketrans({"\r": "_", "\n": "_", "\x00": "_", '"': "_"})
MAX_FILENAME_LENGTH = 255


def file_extension(name: str) -> str:
    """Return the lower-cased extension of ``name`` (``".pdf"``, or ``""``).

    Accepts both POSIX and Windows separators because the value comes straight
    from a browser's multipart payload.
    """
    return PurePosixPath(PureWindowsPath(name).name).suffix.lower()


def sanitize_filename(name: str, *, fallback: str) -> str:
    """Strip any directory component and control characters from ``name``."""
    base = PurePosixPath(PureWindowsPath(name).name).name.translate(_UNSAFE_CHARS).strip()
    if not base or base in {".", ".."}:
        return fallback
    return base[:MAX_FILENAME_LENGTH]


def guess_mime_type(name: str, *, default: str = "application/octet-stream") -> str:
    """Best-effort MIME type for a filename, used when the client sends none."""
    return mimetypes.guess_type(name)[0] or default
