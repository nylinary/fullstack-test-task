"""Ошибки доменного уровня.

Домен ничего не знает про HTTP, Celery и SQLAlchemy, поэтому бросает собственные
исключения. Переводить их в ответы конкретного транспорта — задача слоя
представления (см. ``src.presentation.http.error_handlers``).
"""


class DomainError(Exception):
    """Базовый класс для всех ошибок, которые может бросить домен."""


class NotFoundError(DomainError):
    """Запрошенный агрегат не существует."""


class StoredFileNotFoundError(NotFoundError):
    def __init__(self, file_id: str) -> None:
        super().__init__("File not found")
        self.file_id = file_id


class StoredContentNotFoundError(NotFoundError):
    def __init__(self, stored_name: str) -> None:
        super().__init__("Stored file not found")
        self.stored_name = stored_name


class ValidationError(DomainError):
    """Команда нарушает бизнес-правило."""


class EmptyFileError(ValidationError):
    def __init__(self) -> None:
        super().__init__("File is empty")


class FileTooLargeError(ValidationError):
    def __init__(self, size: int, limit: int) -> None:
        super().__init__(f"File is larger than the {limit} byte limit")
        self.size = size
        self.limit = limit
