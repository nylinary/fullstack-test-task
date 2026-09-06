"""Metadata extraction rules.

The original implementation loaded whole files into memory
(``read_text()`` / ``read_bytes()``) just to count lines, characters and PDF
pages.  The analyzers below consume the file as a stream of chunks and keep a
constant amount of state, so peak memory no longer scales with file size while
the produced metadata stays byte-for-byte identical.
"""

from codecs import getincrementaldecoder
from typing import Any, Protocol, runtime_checkable

from src.domain.entities import StoredFile
from src.domain.services.naming import file_extension

TEXT_MIME_PREFIX = "text/"
PDF_MIME_TYPE = "application/pdf"

# Byte sequence Adobe uses to introduce a page object.  Counting it is a rough
# but cheap approximation of the page count - kept from the original code.
_PDF_PAGE_MARKER = b"/Type /Page"

# The exact set of characters ``str.splitlines()`` treats as a line boundary.
_LINE_BOUNDARIES = frozenset("\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029")


@runtime_checkable
class ContentAnalyzer(Protocol):
    """Incrementally derives metadata from the raw bytes of a file."""

    def feed(self, chunk: bytes) -> None: ...

    def result(self) -> dict[str, Any]: ...


class TextContentAnalyzer:
    """Counts lines and characters exactly like ``len(text.splitlines())``/``len(text)``.

    UTF-8 is decoded incrementally so that a multi-byte character split across
    two chunks is still decoded as one character, and a ``\\r\\n`` pair split
    across two chunks is still counted as a single line break.
    """

    def __init__(self, encoding: str = "utf-8", errors: str = "ignore") -> None:
        self._decoder = getincrementaldecoder(encoding)(errors)
        self._chars = 0
        self._lines = 0
        self._pending = ""

    def feed(self, chunk: bytes) -> None:
        self._consume(self._decoder.decode(chunk))

    def _consume(self, text: str) -> None:
        if not text:
            return
        self._chars += len(text)

        buffer = self._pending + text
        self._pending = ""
        parts = buffer.splitlines(keepends=True)
        if not parts:
            return

        tail = parts[-1]
        # The tail is incomplete when it is not terminated by a boundary, and
        # also when it ends with a bare "\r": the next chunk may start with a
        # "\n" that turns it into a single CRLF break.
        if tail[-1] not in _LINE_BOUNDARIES or tail.endswith("\r"):
            self._pending = tail
            parts = parts[:-1]

        self._lines += len(parts)

    def result(self) -> dict[str, Any]:
        self._consume(self._decoder.decode(b"", True))
        lines = self._lines + (1 if self._pending else 0)
        return {"line_count": lines, "char_count": self._chars}


class PdfContentAnalyzer:
    """Approximates a page count by counting page markers across chunk boundaries."""

    def __init__(self) -> None:
        self._pages = 0
        self._overlap = b""

    def feed(self, chunk: bytes) -> None:
        if not chunk:
            return
        buffer = self._overlap + chunk
        self._pages += buffer.count(_PDF_PAGE_MARKER)
        # Keep just enough bytes for a marker that straddles two chunks; a full
        # marker can never fit in the overlap, so nothing is counted twice.
        self._overlap = buffer[-(len(_PDF_PAGE_MARKER) - 1) :]

    def result(self) -> dict[str, Any]:
        return {"approx_page_count": max(self._pages, 1)}


class MetadataExtractor:
    """Decides *what* to derive from a file; the caller supplies the bytes."""

    def base_metadata(self, file: StoredFile) -> dict[str, Any]:
        return {
            "extension": file_extension(file.original_name),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
        }

    def analyzer_for(self, mime_type: str) -> ContentAnalyzer | None:
        """Return an analyzer for ``mime_type``, or ``None`` when the bytes are irrelevant.

        Returning ``None`` lets the caller skip reading the file entirely.
        """
        if mime_type.startswith(TEXT_MIME_PREFIX):
            return TextContentAnalyzer()
        if mime_type == PDF_MIME_TYPE:
            return PdfContentAnalyzer()
        return None
