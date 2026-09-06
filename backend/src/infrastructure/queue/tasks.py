"""Celery tasks: thin adapters that hand off to a use case."""

import logging

from celery.signals import worker_process_shutdown

from src.container import get_container
from src.infrastructure.queue.celery_app import PROCESS_FILE_TASK, celery_app
from src.infrastructure.queue.runner import worker_loop

logger = logging.getLogger(__name__)


@celery_app.task(name=PROCESS_FILE_TASK)
def process_file(file_id: str) -> None:
    """Run the scan -> metadata -> alert pipeline for one uploaded file."""
    worker_loop.run(get_container().process_file().execute(file_id))


@worker_process_shutdown.connect
def _dispose_resources(**_: object) -> None:
    try:
        worker_loop.run(get_container().dispose())
    finally:
        worker_loop.close()
