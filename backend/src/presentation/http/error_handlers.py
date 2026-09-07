"""Переводит доменные ошибки в HTTP-ответы.

Именно то, что этот маппинг собран в одном месте, позволяет use case'ам
обходиться без ``HTTPException``: раньше HTTP-ошибки бросал слой доступа к
данным, из-за чего он был непригоден для Celery-воркера.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.errors import DomainError, FileTooLargeError, NotFoundError, ValidationError
from src.infrastructure.storage.local import UnsafeStoredNameError

logger = logging.getLogger(__name__)


def _status_for(exc: DomainError) -> int:
    if isinstance(exc, NotFoundError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, FileTooLargeError):
        return status.HTTP_413_CONTENT_TOO_LARGE
    if isinstance(exc, ValidationError):
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_422_UNPROCESSABLE_ENTITY


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=_status_for(exc), content={"detail": str(exc)})

    @app.exception_handler(UnsafeStoredNameError)
    async def _handle_unsafe_name(_: Request, exc: UnsafeStoredNameError) -> JSONResponse:
        logger.warning("Blocked unsafe storage access: %s", exc)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid file reference"})
