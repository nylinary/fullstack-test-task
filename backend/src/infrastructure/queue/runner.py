"""Bridges Celery's synchronous worker to the async application layer.

One :class:`asyncio.Runner` is kept alive for the lifetime of the worker
process, so the asyncpg connection pool is reused across tasks instead of being
rebuilt - or, worse, bound to an event loop that has already been closed.
"""

import asyncio
from collections.abc import Coroutine
from typing import Any


class WorkerLoop:
    """Owns the worker's event loop; created lazily on the first task."""

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
