"""Value objects shared across the domain.

The string values are part of the persisted contract (they are stored verbatim
in Postgres and returned by the public API), so they must not be renamed.
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
