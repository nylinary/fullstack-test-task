"""Decides which alert a processed file deserves."""

from src.domain.entities import Alert, StoredFile
from src.domain.value_objects import AlertLevel

PROCESSING_FAILED_MESSAGE = "File processing failed"
PROCESSED_SUCCESSFULLY_MESSAGE = "File processed successfully"


class AlertPolicy:
    def build(self, file: StoredFile) -> Alert:
        if file.has_failed:
            return Alert(file_id=file.id, level=AlertLevel.CRITICAL, message=PROCESSING_FAILED_MESSAGE)
        if file.requires_attention:
            return Alert(
                file_id=file.id,
                level=AlertLevel.WARNING,
                message=f"File requires attention: {file.scan_details}",
            )
        return Alert(file_id=file.id, level=AlertLevel.INFO, message=PROCESSED_SUCCESSFULLY_MESSAGE)
