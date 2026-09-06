"""Celery application used by the worker and by the producing API process."""

from celery import Celery

from src.infrastructure.config import get_settings

PROCESS_FILE_TASK = "files.process"


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        "file_tasks",
        broker=settings.celery_broker_url,
        backend=settings.result_backend,
        include=["src.infrastructure.queue.tasks"],
    )
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        worker_hijack_root_logger=False,
    )
    return app


celery_app = create_celery_app()
