"""FastAPI dependency providers.

Routers ask for a use case, never for a session, an engine or a Celery app.
"""

from typing import Annotated

from fastapi import Depends, Query

from src.application.dto import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT, Page
from src.application.use_cases.manage_files import (
    DeleteFileUseCase,
    DownloadFileUseCase,
    GetFileUseCase,
    ListAlertsUseCase,
    ListFilesUseCase,
    RenameFileUseCase,
)
from src.application.use_cases.upload_file import UploadFileUseCase
from src.container import Container, get_container


def provide_container() -> Container:
    return get_container()


ContainerDep = Annotated[Container, Depends(provide_container)]


def provide_page(
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page:
    return Page(limit=limit, offset=offset)


PageDep = Annotated[Page, Depends(provide_page)]


def provide_upload_file(container: ContainerDep) -> UploadFileUseCase:
    return container.upload_file()


def provide_list_files(container: ContainerDep) -> ListFilesUseCase:
    return container.list_files()


def provide_list_alerts(container: ContainerDep) -> ListAlertsUseCase:
    return container.list_alerts()


def provide_get_file(container: ContainerDep) -> GetFileUseCase:
    return container.get_file()


def provide_rename_file(container: ContainerDep) -> RenameFileUseCase:
    return container.rename_file()


def provide_delete_file(container: ContainerDep) -> DeleteFileUseCase:
    return container.delete_file()


def provide_download_file(container: ContainerDep) -> DownloadFileUseCase:
    return container.download_file()
