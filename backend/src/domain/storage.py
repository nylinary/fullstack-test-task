"""Порт бинарного хранилища."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Protocol

DEFAULT_CHUNK_SIZE = 1024 * 1024


class FileStorage(Protocol):
    async def save(self, stored_name: str, chunks: AsyncIterator[bytes]) -> int:
        """Сохранить ``chunks`` под именем ``stored_name`` и вернуть число записанных байт."""
        ...

    def read_chunks(self, stored_name: str, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        """Отдать сохранённый объект потоком."""
        ...

    async def delete(self, stored_name: str) -> None: ...

    async def exists(self, stored_name: str) -> bool: ...

    def local_path(self, stored_name: str) -> Path | None:
        """Путь к объекту в файловой системе, если адаптер работает поверх локального диска.

        Чисто оптимизационный хук: позволяет HTTP-слою отдать дескриптор ядру
        (``sendfile``) вместо того, чтобы гнать байты через Python. Адаптеры
        поверх удалённого объектного хранилища возвращают ``None``, и вызывающий
        код откатывается на :meth:`read_chunks`.
        """
        ...
