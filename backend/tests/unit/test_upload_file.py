import pytest

from src.application.dto import UploadFileCommand
from src.application.use_cases.upload_file import UploadFileUseCase
from src.domain.errors import EmptyFileError, FileTooLargeError, ValidationError
from src.domain.value_objects import ProcessingStatus
from tests.doubles import FakeUnitOfWork, InMemoryStorage, RecordingQueue, chunks_of


def build_use_case(
    *,
    storage: InMemoryStorage,
    queue: RecordingQueue,
    max_upload_size: int = 1024,
    uow: FakeUnitOfWork | None = None,
) -> UploadFileUseCase:
    uow = uow or FakeUnitOfWork({}, [])
    return UploadFileUseCase(
        uow_factory=lambda: uow,
        storage=storage,
        queue=queue,
        max_upload_size=max_upload_size,
        id_generator=lambda: "file-1",
    )


async def test_upload_persists_stores_and_enqueues() -> None:
    storage, queue = InMemoryStorage(), RecordingQueue()
    uow = FakeUnitOfWork({}, [])

    file = await build_use_case(storage=storage, queue=queue, uow=uow).execute(
        UploadFileCommand(
            title="  Contract  ",
            original_name="contract.pdf",
            declared_mime_type="application/pdf",
            chunks=chunks_of(b"%PDF-1.4 hello"),
        )
    )

    assert file.id == "file-1"
    assert file.title == "Contract"
    assert file.stored_name == "file-1.pdf"
    assert file.size == len(b"%PDF-1.4 hello")
    assert file.processing_status is ProcessingStatus.UPLOADED
    assert storage.objects["file-1.pdf"] == b"%PDF-1.4 hello"
    assert queue.enqueued == ["file-1"]


async def test_missing_content_type_is_guessed_from_the_name() -> None:
    storage, queue = InMemoryStorage(), RecordingQueue()

    file = await build_use_case(storage=storage, queue=queue).execute(
        UploadFileCommand("t", "notes.txt", None, chunks_of(b"hi"))
    )

    assert file.mime_type == "text/plain"


async def test_directory_traversal_in_the_filename_is_stripped() -> None:
    storage, queue = InMemoryStorage(), RecordingQueue()

    file = await build_use_case(storage=storage, queue=queue).execute(
        UploadFileCommand("t", "../../etc/passwd.txt", "text/plain", chunks_of(b"hi"))
    )

    assert file.original_name == "passwd.txt"
    assert file.stored_name == "file-1.txt"


async def test_empty_upload_is_rejected_and_leaves_nothing_behind() -> None:
    storage, queue = InMemoryStorage(), RecordingQueue()

    with pytest.raises(EmptyFileError):
        await build_use_case(storage=storage, queue=queue).execute(
            UploadFileCommand("t", "empty.txt", "text/plain", chunks_of(b""))
        )

    assert storage.objects == {}
    assert queue.enqueued == []


async def test_oversized_upload_is_aborted_mid_stream() -> None:
    storage, queue = InMemoryStorage(), RecordingQueue()

    with pytest.raises(FileTooLargeError):
        await build_use_case(storage=storage, queue=queue, max_upload_size=16).execute(
            UploadFileCommand("t", "big.txt", "text/plain", chunks_of(b"x" * 128, size=4))
        )

    assert storage.objects == {}


async def test_blank_title_is_rejected_before_anything_is_enqueued() -> None:
    storage, queue = InMemoryStorage(), RecordingQueue()

    with pytest.raises(ValidationError):
        await build_use_case(storage=storage, queue=queue).execute(
            UploadFileCommand("   ", "notes.txt", "text/plain", chunks_of(b"hi"))
        )

    assert storage.objects == {}
    assert queue.enqueued == []


async def test_failed_insert_does_not_leave_an_orphan_blob() -> None:
    storage, queue = InMemoryStorage(), RecordingQueue()
    uow = FakeUnitOfWork({}, [], fail_on_commit=True)

    with pytest.raises(RuntimeError):
        await build_use_case(storage=storage, queue=queue, uow=uow).execute(
            UploadFileCommand("t", "notes.txt", "text/plain", chunks_of(b"hi"))
        )

    assert storage.objects == {}
    assert queue.enqueued == []
