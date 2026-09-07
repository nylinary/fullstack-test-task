"""Реализация порта :class:`~src.application.ports.FileProcessingQueue` поверх Celery."""

from anyio import to_thread
from celery import Celery

from src.infrastructure.queue.celery_app import PROCESS_FILE_TASK


class CeleryFileProcessingQueue:
    """Публикует задачу по *имени*, поэтому процесс API не импортирует модуль задач."""

    def __init__(self, celery_app: Celery, task_name: str = PROCESS_FILE_TASK) -> None:
        self._celery_app = celery_app
        self._task_name = task_name

    async def enqueue_processing(self, file_id: str) -> None:
        # ``send_task`` ходит к брокеру по блокирующему сокету; вынос в
        # отдельный поток не даёт event loop'у API встать.
        await to_thread.run_sync(self._send, file_id)

    def _send(self, file_id: str) -> None:
        self._celery_app.send_task(self._task_name, args=[file_id])
