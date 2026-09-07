"""Мост между синхронным воркером Celery и асинхронным слоем приложения.

Один :class:`asyncio.Runner` живёт всё время жизни процесса воркера, поэтому пул
соединений asyncpg переиспользуется между задачами, а не пересоздаётся — и, что
хуже, не привязывается к уже закрытому event loop'у.
"""

import asyncio
from collections.abc import Coroutine
from typing import Any


class WorkerLoop:
    """Владеет event loop'ом воркера; создаётся лениво на первой задаче."""

    def __init__(self) -> None:
        self._runner: asyncio.Runner | None = None

    def run[T](self, coroutine: Coroutine[Any, Any, T]) -> T:
        if self._runner is None:
            self._runner = asyncio.Runner()
        return self._runner.run(coroutine)

    def close(self) -> None:
        if self._runner is not None:
            self._runner.close()
            self._runner = None


worker_loop = WorkerLoop()
