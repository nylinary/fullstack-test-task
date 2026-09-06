"""Domain entities.

These are plain dataclasses: no SQLAlchemy, Pydantic or FastAPI imports.  They
are persisted through SQLAlchemy's *imperative* mapping
(:mod:`src.infrastructure.db.mapping`), which keeps the domain free of ORM
concerns while still avoiding a hand-written entity <-> row mapper.

All state transitions live here as methods, so the rules ("a failed file
requires attention", "renaming trims the title") cannot be bypassed by a caller
that pokes at the attributes directly.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.domain.errors import ValidationError
from src.domain.value_objects import AlertLevel, ProcessingStatus, ScanStatus

MAX_TITLE_LENGTH = 255
MAX_SCAN_DETAILS_LENGTH = 500
MAX_ALERT_MESSAGE_LENGTH = 500


@dataclass
class ScanReport:
    """Outcome of a threat scan, produced by :class:`~src.domain.services.threat_scanner.ThreatScanner`."""

    status: ScanStatus
    details: str
    requires_attention: bool


# ``eq=False`` keeps identity-based equality/hashing: entities are identified by
# their id, and SQLAlchemy's identity map requires hashable instances.
# ``repr=False`` avoids touching every attribute (and triggering a lazy load)
# from a log statement.
@dataclass(eq=False, repr=False)
class StoredFile:
    """An uploaded file together with its processing state."""

    id: str
    title: str
    original_name: str
    stored_name: str
    mime_type: str
    size: int
    processing_status: ProcessingStatus = ProcessingStatus.UPLOADED
    scan_status: ScanStatus | None = None
    scan_details: str | None = None
    metadata_json: dict[str, Any] | None = None
    requires_attention: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def rename(self, title: str) -> None:
        self.title = self.normalize_title(title)

    def start_processing(self) -> None:
        self.processing_status = ProcessingStatus.PROCESSING

    def apply_scan(self, report: ScanReport) -> None:
        self.scan_status = report.status
        self.scan_details = report.details[:MAX_SCAN_DETAILS_LENGTH]
        self.requires_attention = report.requires_attention

    def apply_metadata(self, metadata: dict[str, Any]) -> None:
        self.metadata_json = metadata
        self.processing_status = ProcessingStatus.PROCESSED

    def mark_failed(self, reason: str) -> None:
        self.processing_status = ProcessingStatus.FAILED
        # A file that already carries a scan verdict keeps it; otherwise the
        # scan is considered failed as well.
        self.scan_status = self.scan_status or ScanStatus.FAILED
        self.scan_details = reason[:MAX_SCAN_DETAILS_LENGTH]

    @property
    def has_failed(self) -> bool:
        return self.processing_status is ProcessingStatus.FAILED

    @staticmethod
    def normalize_title(title: str) -> str:
        cleaned = title.strip()
        if not cleaned:
            raise ValidationError("Title must not be empty")
        if len(cleaned) > MAX_TITLE_LENGTH:
            raise ValidationError(f"Title must be at most {MAX_TITLE_LENGTH} characters")
        return cleaned

    @classmethod
    def create(
        cls,
        *,
        id: str,  # noqa: A002 - mirrors the persisted column name
        title: str,
        original_name: str,
        stored_name: str,
        mime_type: str,
        size: int,
    ) -> StoredFile:
        return cls(
            id=id,
            title=cls.normalize_title(title),
            original_name=original_name,
            stored_name=stored_name,
            mime_type=mime_type,
            size=size,
            processing_status=ProcessingStatus.UPLOADED,
        )


@dataclass(eq=False, repr=False)
class Alert:
    """A notification emitted about a file at the end of the processing pipeline."""

    file_id: str
    level: AlertLevel
    message: str
    id: int | None = None
    created_at: datetime | None = field(default=None)

    def __post_init__(self) -> None:
        self.message = self.message[:MAX_ALERT_MESSAGE_LENGTH]
