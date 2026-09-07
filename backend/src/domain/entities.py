"""Доменные сущности.

Это обычные dataclass'ы: ни SQLAlchemy, ни Pydantic, ни FastAPI. В базу они
кладутся через *imperative* mapping SQLAlchemy
(:mod:`src.infrastructure.db.tables`) — домен остаётся свободным от ORM, и при
этом не нужен ручной маппер «сущность <-> строка».

Все переходы состояний живут здесь в виде методов, поэтому правила («упавший
файл требует внимания», «переименование обрезает пробелы») нельзя обойти,
присвоив атрибут напрямую.
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
    """Результат проверки, который выдаёт :class:`~src.domain.services.threat_scanner.ThreatScanner`."""

    status: ScanStatus
    details: str
    requires_attention: bool


# ``eq=False`` оставляет сравнение и хеширование по идентичности: сущность
# определяется своим id, а identity map SQLAlchemy требует хешируемых объектов.
# ``repr=False`` не даёт логированию задеть все атрибуты сразу (и спровоцировать
# ленивую загрузку).
@dataclass(eq=False, repr=False)
class StoredFile:
    """Загруженный файл вместе с состоянием его обработки."""

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
        # Файл, у которого уже есть вердикт сканера, сохраняет его; иначе
        # сканирование тоже считается провалившимся.
        self.scan_status = self.scan_status or ScanStatus.FAILED
        self.scan_details = reason[:MAX_SCAN_DETAILS_LENGTH]

    @property
    def has_failed(self) -> bool:
        return self.processing_status is ProcessingStatus.FAILED

    @staticmethod
    def normalize_title(title: str) -> str:
        """Обрезать и проверить название.

        Публичный метод: вызывающий код может упасть до того, как начнёт дорогую
        работу вроде записи файла на диск.
        """
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
        id: str,  # noqa: A002 - повторяет имя колонки в базе
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
    """Уведомление о файле, выпускаемое в конце конвейера обработки."""

    file_id: str
    level: AlertLevel
    message: str
    id: int | None = None
    created_at: datetime | None = field(default=None)

    def __post_init__(self) -> None:
        self.message = self.message[:MAX_ALERT_MESSAGE_LENGTH]
