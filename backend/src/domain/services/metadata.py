"""Правила извлечения метаданных.

Исходная реализация целиком загружала файл в память (``read_text()`` /
``read_bytes()``) только ради подсчёта строк, символов и страниц PDF.
Анализаторы ниже читают файл потоком по чанкам и хранят постоянный объём
состояния: пиковая память больше не зависит от размера файла, а получаемые
метаданные совпадают байт в байт.
"""

from codecs import getincrementaldecoder
from typing import Any, Protocol, runtime_checkable

from src.domain.entities import StoredFile
from src.domain.services.naming import file_extension

TEXT_MIME_PREFIX = "text/"
PDF_MIME_TYPE = "application/pdf"

# Последовательность байт, которой Adobe открывает объект страницы. Её подсчёт —
# грубая, но дешёвая оценка числа страниц; оставлена из исходного кода.
_PDF_PAGE_MARKER = b"/Type /Page"

# Ровно тот набор символов, который ``str.splitlines()`` считает границей строки.
_LINE_BOUNDARIES = frozenset("\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029")


@runtime_checkable
class ContentAnalyzer(Protocol):
    """Инкрементально выводит метаданные из сырых байт файла."""

    def feed(self, chunk: bytes) -> None: ...

    def result(self) -> dict[str, Any]: ...


class TextContentAnalyzer:
    """Считает строки и символы ровно как ``len(text.splitlines())`` и ``len(text)``.

    UTF-8 декодируется инкрементально, поэтому многобайтовый символ, разорванный
    границей чанков, всё равно декодируется как один символ, а пара ``\\r\\n``,
    разорванная границей, всё равно считается одним переводом строки.
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
        # Хвост неполон, если он не заканчивается границей строки, а также если
        # он оканчивается одиночным "\r": следующий чанк может начаться с "\n",
        # и вместе они дадут один перевод строки CRLF.
        if tail[-1] not in _LINE_BOUNDARIES or tail.endswith("\r"):
            self._pending = tail
            parts = parts[:-1]

        self._lines += len(parts)

    def result(self) -> dict[str, Any]:
        self._consume(self._decoder.decode(b"", True))
        lines = self._lines + (1 if self._pending else 0)
        return {"line_count": lines, "char_count": self._chars}


class PdfContentAnalyzer:
    """Оценивает число страниц, считая маркеры страниц через границы чанков."""

    def __init__(self) -> None:
        self._pages = 0
        self._overlap = b""

    def feed(self, chunk: bytes) -> None:
        if not chunk:
            return
        buffer = self._overlap + chunk
        self._pages += buffer.count(_PDF_PAGE_MARKER)
        # Оставляем ровно столько байт, сколько нужно маркеру на стыке двух
        # чанков; целиком маркер в перекрытие не помещается, поэтому дважды
        # ничего не посчитается.
        self._overlap = buffer[-(len(_PDF_PAGE_MARKER) - 1) :]

    def result(self) -> dict[str, Any]:
        return {"approx_page_count": max(self._pages, 1)}


class MetadataExtractor:
    """Решает, *что* извлекать из файла; байты подаёт вызывающий код."""

    def base_metadata(self, file: StoredFile) -> dict[str, Any]:
        return {
            "extension": file_extension(file.original_name),
            "size_bytes": file.size,
            "mime_type": file.mime_type,
        }

    def analyzer_for(self, mime_type: str) -> ContentAnalyzer | None:
        """Вернуть анализатор для ``mime_type`` или ``None``, если байты не нужны.

        ``None`` позволяет вызывающему коду вовсе не читать файл.
        """
        if mime_type.startswith(TEXT_MIME_PREFIX):
            return TextContentAnalyzer()
        if mime_type == PDF_MIME_TYPE:
            return PdfContentAnalyzer()
        return None
