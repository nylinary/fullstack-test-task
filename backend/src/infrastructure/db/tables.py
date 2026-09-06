"""Table definitions and the imperative mapping onto the domain entities.

Using SQLAlchemy's *imperative* (classical) mapping instead of the declarative
base keeps the persistence schema here and the business rules in
:mod:`src.domain.entities`, without the duplication of a separate ORM model plus
a hand-written mapper.  Alembic still autogenerates from ``metadata``.
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
    # The listing is always "newest first"; without this index every page is a
    # full scan plus a sort.
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
    # Postgres does not index foreign keys automatically, so deleting a file had
    # to scan the whole alerts table to check the constraint.
    Index("ix_alerts_file_id", "file_id"),
    Index("ix_alerts_created_at_id", "created_at", "id"),
)


def configure_mappings() -> None:
    """Bind the domain entities to their tables (idempotent)."""
    if not mapper_registry.mappers:
        # ``eager_defaults`` makes SQLAlchemy fetch server-generated columns
        # (created_at / updated_at) via RETURNING as part of the INSERT or
        # UPDATE, instead of leaving them expired and needing an extra
        # round-trip refresh - which is what the original code paid for on
        # every write.
        mapper_registry.map_imperatively(StoredFile, files_table, eager_defaults=True)
        mapper_registry.map_imperatively(Alert, alerts_table, eager_defaults=True)


configure_mappings()
