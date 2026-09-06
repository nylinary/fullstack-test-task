"""HTTP endpoints for files: parse, delegate, serialise. No business rules here."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse

from src.application.dto import UploadFileCommand
from src.application.use_cases.manage_files import (
    DeleteFileUseCase,
    DownloadFileUseCase,
    GetFileUseCase,
    ListFilesUseCase,
    RenameFileUseCase,
)
from src.application.use_cases.upload_file import UploadFileUseCase
from src.domain.storage import DEFAULT_CHUNK_SIZE
from src.presentation.http.dependencies import (
    PageDep,
    provide_delete_file,
    provide_download_file,
    provide_get_file,
    provide_list_files,
    provide_rename_file,
    provide_upload_file,
)
from src.presentation.http.schemas import ErrorResponse, FileItem, FileUpdate

router = APIRouter(prefix="/files", tags=["files"])

NOT_FOUND: dict[int | str, dict[str, type[ErrorResponse]]] = {404: {"model": ErrorResponse}}


async def _iter_upload(upload: UploadFile, chunk_size: int = DEFAULT_CHUNK_SIZE) -> AsyncIterator[bytes]:
    """Yield the upload in chunks instead of materialising it in memory."""
    while chunk := await upload.read(chunk_size):
        yield chunk


@router.get("", response_model=list[FileItem])
async def list_files(
    page: PageDep,
    use_case: Annotated[ListFilesUseCase, Depends(provide_list_files)],
) -> list[FileItem]:
    files = await use_case.execute(page)
    return [FileItem.model_validate(file) for file in files]


@router.post("", response_model=FileItem, status_code=status.HTTP_201_CREATED)
async def create_file(
    use_case: Annotated[UploadFileUseCase, Depends(provide_upload_file)],
    title: Annotated[str, Form(min_length=1, max_length=255)],
    file: Annotated[UploadFile, File()],
) -> FileItem:
    created = await use_case.execute(
        UploadFileCommand(
            title=title,
            original_name=file.filename,
            declared_mime_type=file.content_type,
            chunks=_iter_upload(file),
        )
    )
    return FileItem.model_validate(created)


@router.get("/{file_id}", response_model=FileItem, responses=NOT_FOUND)
async def get_file(
    file_id: str,
    use_case: Annotated[GetFileUseCase, Depends(provide_get_file)],
) -> FileItem:
    return FileItem.model_validate(await use_case.execute(file_id))


@router.patch("/{file_id}", response_model=FileItem, responses=NOT_FOUND)
async def update_file(
    file_id: str,
    payload: FileUpdate,
    use_case: Annotated[RenameFileUseCase, Depends(provide_rename_file)],
) -> FileItem:
    return FileItem.model_validate(await use_case.execute(file_id, payload.title))


@router.get("/{file_id}/download", responses=NOT_FOUND)
async def download_file(
    file_id: str,
    use_case: Annotated[DownloadFileUseCase, Depends(provide_download_file)],
) -> Response:
    download = await use_case.execute(file_id)
    headers = {"Content-Length": str(download.file.size)}

    if download.local_path is not None:
        # Local disk: let the kernel send the file, no bytes through Python.
        return FileResponse(
            path=download.local_path,
            media_type=download.file.mime_type,
            filename=download.file.original_name,
        )

    return StreamingResponse(
        download.open_stream(),
        media_type=download.file.mime_type,
        headers={
            **headers,
            "Content-Disposition": f'attachment; filename="{download.file.original_name}"',
        },
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
async def delete_file(
    file_id: str,
    use_case: Annotated[DeleteFileUseCase, Depends(provide_delete_file)],
) -> Response:
    await use_case.execute(file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
