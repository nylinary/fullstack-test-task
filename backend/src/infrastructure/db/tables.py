"""Определения таблиц и imperative mapping на доменные сущности.

*Imperative* (классический) маппинг вместо declarative base оставляет схему
хранения здесь, а бизнес-правила — в :mod:`src.domain.entities`, и при этом не
появляется дублирующей ORM-модели с ручным маппером. Alembic по-прежнему
автогенерирует миграции из ``metadata``.
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    func,
)
from sqlalchemy.orm import registry

from src.domain.entities import Alert, StoredFile
from src.domain.value_objects import AlertLevel, ProcessingStatus, ScanStatus
from src.infrastructure.db.types import StrEnumType

metadata = MetaData()
mapper_registry = registry(metadata=metadata)

files_table = Table(
    "files",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("title", String(255), nullable=False),
    Column("original_name", String(255), nullable=False),
    Column("stored_name", String(255), nullable=False, unique=True),
    Column("mime_type", String(255), nullable=False),
    Column("size", Integer, nullable=False),
    Column("processing_status", StrEnumType(ProcessingStatus, 50), nullable=False, default=ProcessingStatus.UPLOADED),
    Column("scan_status", StrEnumType(ScanStatus, 50), nullable=True),
    Column("scan_details", String(500), nullable=True),
    Column("metadata_json", JSON, nullable=True),
    Column("requires_attention", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    # Список всегда «сначала новые»; без этого индекса каждая страница — полное
    # сканирование плюс сортировка.
    Index("ix_files_created_at_id", "created_at", "id"),
)

alerts_table = Table(
    "alerts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_id", String(36), ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
    Column("level", StrEnumType(AlertLevel, 50), nullable=False),
    Column("message", String(500), nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    # Postgres не индексирует внешние ключи автоматически, поэтому при удалении
    # файла проверка ограничения сканировала всю таблицу алертов.
    Index("ix_alerts_file_id", "file_id"),
    Index("ix_alerts_created_at_id", "created_at", "id"),
)


def configure_mappings() -> None:
    """Привязать доменные сущности к их таблицам (идемпотентно)."""
    if not mapper_registry.mappers:
        # ``eager_defaults`` заставляет SQLAlchemy забирать колонки, которые
        # генерирует база (created_at / updated_at), через RETURNING прямо в
        # INSERT или UPDATE — вместо того чтобы оставлять их протухшими и делать
        # лишний refresh отдельным запросом, как платил исходный код на каждой
        # записи.
        mapper_registry.map_imperatively(StoredFile, files_table, eager_defaults=True)
        mapper_registry.map_imperatively(Alert, alerts_table, eager_defaults=True)


configure_mappings()
