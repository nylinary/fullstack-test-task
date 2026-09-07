"""Транспортные модели.

Намеренно отделены от доменных сущностей: формат на проводе — это контракт с
фронтендом, и он должен меняться независимо от бизнес-модели. Набор полей
совпадает с исходным API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.value_objects import AlertLevel, ProcessingStatus, ScanStatus


class FileItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_name: str
    mime_type: str
    size: int
    processing_status: ProcessingStatus
    scan_status: ScanStatus | None
    scan_details: str | None
    metadata_json: dict[str, Any] | None
    requires_attention: bool
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class AlertItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_id: str
    level: AlertLevel
    message: str
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
