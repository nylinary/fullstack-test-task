"""Правила проверки на угрозы.

Чистая бизнес-логика: нужны только заявленные метаданные загрузки, но не её
байты — поэтому сканирование вообще не обращается к файловой системе.
"""

from collections.abc import Iterator
from dataclasses import dataclass, field

from src.domain.entities import ScanReport, StoredFile
from src.domain.services.naming import file_extension
from src.domain.value_objects import ScanStatus

DEFAULT_SUSPICIOUS_EXTENSIONS = frozenset({".exe", ".bat", ".cmd", ".sh", ".js"})
DEFAULT_MAX_SAFE_SIZE = 10 * 1024 * 1024
DEFAULT_PDF_MIME_TYPES = frozenset({"application/pdf", "application/octet-stream"})

NO_THREATS_FOUND = "no threats found"


@dataclass(frozen=True)
class ThreatScanner:
    suspicious_extensions: frozenset[str] = DEFAULT_SUSPICIOUS_EXTENSIONS
    max_safe_size: int = DEFAULT_MAX_SAFE_SIZE
    pdf_mime_types: frozenset[str] = DEFAULT_PDF_MIME_TYPES
    max_safe_size_label: str = field(default="10 MB")

    def scan(self, file: StoredFile) -> ScanReport:
        reasons = list(self._reasons(file))
        return ScanReport(
            status=ScanStatus.SUSPICIOUS if reasons else ScanStatus.CLEAN,
            details=", ".join(reasons) if reasons else NO_THREATS_FOUND,
            requires_attention=bool(reasons),
        )

    def _reasons(self, file: StoredFile) -> Iterator[str]:
        extension = file_extension(file.original_name)

        if extension in self.suspicious_extensions:
            yield f"suspicious extension {extension}"

        if file.size > self.max_safe_size:
            yield f"file is larger than {self.max_safe_size_label}"

        if extension == ".pdf" and file.mime_type not in self.pdf_mime_types:
            yield "pdf extension does not match mime type"
