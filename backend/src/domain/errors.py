"""Domain-level errors.

The domain never knows about HTTP, Celery or SQLAlchemy, so it raises its own
exceptions.  The presentation layer is responsible for translating them into
transport-specific responses (see ``src.presentation.http.error_handlers``).
"""


class DomainError(Exception):
    """Base class for every error the domain can raise."""


class NotFoundError(DomainError):
    """A requested aggregate does not exist."""


class StoredFileNotFoundError(NotFoundError):
    def __init__(self, file_id: str) -> None:
        super().__init__("File not found")
        self.file_id = file_id


class StoredContentNotFoundError(NotFoundError):
    def __init__(self, stored_name: str) -> None:
        super().__init__("Stored file not found")
        self.stored_name = stored_name


class ValidationError(DomainError):
    """The command violates a business rule."""


class EmptyFileError(ValidationError):
    def __init__(self) -> None:
        super().__init__("File is empty")


class FileTooLargeError(ValidationError):
    def __init__(self, size: int, limit: int) -> None:
        super().__init__(f"File is larger than the {limit} byte limit")
        self.size = size
        self.limit = limit
