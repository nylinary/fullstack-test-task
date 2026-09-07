"""Порты уровня приложения к внешней инфраструктуре."""

from typing import Protocol


class FileProcessingQueue(Protocol):
    """Передаёт только что загруженный файл в асинхронный конвейер."""

    async def enqueue_processing(self, file_id: str) -> None: ...


class IdGenerator(Protocol):
    """Выдаёт идентификаторы для новых агрегатов (внедряется, чтобы тесты оставались детерминированными)."""

    def __call__(self) -> str: ...
