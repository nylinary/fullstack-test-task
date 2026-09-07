"""Value objects, общие для всего домена.

Строковые значения — часть контракта хранения: они лежат в Postgres как есть и
возвращаются публичным API, поэтому переименовывать их нельзя.
"""

from enum import StrEnum


class ProcessingStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ScanStatus(StrEnum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    FAILED = "failed"


class AlertLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
