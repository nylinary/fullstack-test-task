"""Сквозная проверка настоящих адаптеров: SQLAlchemy, локальный диск, use case'ы."""

import pytest

from src.application.dto import Page, UploadFileCommand
from src.container import Container
from src.domain.errors import StoredContentNotFoundError, StoredFileNotFoundError
from src.domain.value_objects import AlertLevel, ProcessingStatus, ScanStatus
from tests.doubles import chunks_of


async def upload(container: Container, *, title: str, name: str, mime: str, content: bytes) -> str:
    file = await container.upload_file().execute(
        UploadFileCommand(title=title, original_name=name, declared_mime_type=mime, chunks=chunks_of(content))
    )
    return file.id


async def test_clean_text_file_is_processed_and_gets_an_info_alert(container: Container) -> None:
    file_id = await upload(container, title="Notes", name="notes.txt", mime="text/plain", content=b"alpha\nbeta\ngamma")

    await container.process_file().execute(file_id)

    file = await container.get_file().execute(file_id)
    assert file.processing_status is ProcessingStatus.PROCESSED
    assert file.scan_status is ScanStatus.CLEAN
    assert file.scan_details == "no threats found"
    assert file.requires_attention is False
    assert file.metadata_json == {
        "extension": ".txt",
        "size_bytes": 16,
        "mime_type": "text/plain",
        "line_count": 3,
        "char_count": 16,
    }

    alerts = await container.list_alerts().execute(Page())
    assert [(a.level, a.message) for a in alerts] == [(AlertLevel.INFO, "File processed successfully")]


async def test_suspicious_file_raises_a_warning_alert(container: Container) -> None:
    file_id = await upload(
        container, title="Installer", name="setup.exe", mime="application/octet-stream", content=b"MZ\x90\x00"
    )

    await container.process_file().execute(file_id)

    file = await container.get_file().execute(file_id)
    assert file.scan_status is ScanStatus.SUSPICIOUS
    assert file.requires_attention is True
    assert file.processing_status is ProcessingStatus.PROCESSED

    (alert,) = await container.list_alerts().execute(Page())
    assert alert.level is AlertLevel.WARNING
    assert alert.message == "File requires attention: suspicious extension .exe"


async def test_missing_blob_fails_the_file_and_raises_a_critical_alert(container: Container) -> None:
    file_id = await upload(container, title="Gone", name="gone.txt", mime="text/plain", content=b"data")
    file = await container.get_file().execute(file_id)
    await container.storage.delete(file.stored_name)

    await container.process_file().execute(file_id)

    file = await container.get_file().execute(file_id)
    assert file.processing_status is ProcessingStatus.FAILED
    assert file.scan_details == "stored file not found during metadata extraction"
    # Вердикт «чисто» от шага сканирования сохраняется; упала только обработка.
    assert file.scan_status is ScanStatus.CLEAN

    (alert,) = await container.list_alerts().execute(Page())
    assert alert.level is AlertLevel.CRITICAL
    assert alert.message == "File processing failed"


async def test_pdf_page_count(container: Container) -> None:
    content = b"%PDF-1.4" + b"/Type /Page" * 3
    file_id = await upload(container, title="Doc", name="doc.pdf", mime="application/pdf", content=content)

    await container.process_file().execute(file_id)

    file = await container.get_file().execute(file_id)
    assert file.metadata_json is not None
    assert file.metadata_json["approx_page_count"] == 3


async def test_processing_an_unknown_file_is_a_no_op(container: Container) -> None:
    await container.process_file().execute("does-not-exist")

    assert await container.list_alerts().execute(Page()) == []


async def test_listing_is_newest_first_and_paginated(container: Container) -> None:
    ids = [await upload(container, title=f"n{i}", name=f"n{i}.txt", mime="text/plain", content=b"x") for i in range(5)]

    page = await container.list_files().execute(Page(limit=2, offset=0))

    assert len(page) == 2
    assert {file.id for file in page} <= set(ids)
    assert page == sorted(page, key=lambda f: (f.created_at, f.id), reverse=True)


async def test_rename_and_delete(container: Container) -> None:
    file_id = await upload(container, title="Old", name="a.txt", mime="text/plain", content=b"x")
    stored_name = (await container.get_file().execute(file_id)).stored_name

    renamed = await container.rename_file().execute(file_id, "  New name  ")
    assert renamed.title == "New name"

    await container.process_file().execute(file_id)  # создаёт алерт, ссылающийся на файл
    await container.delete_file().execute(file_id)

    assert await container.storage.exists(stored_name) is False
    with pytest.raises(StoredFileNotFoundError):
        await container.get_file().execute(file_id)
    # Внешний ключ теперь каскадный, поэтому удаление файла с алертом не падает.
    assert await container.list_alerts().execute(Page()) == []


async def test_download_of_a_missing_blob_reports_it(container: Container) -> None:
    file_id = await upload(container, title="A", name="a.txt", mime="text/plain", content=b"x")
    file = await container.get_file().execute(file_id)
    await container.storage.delete(file.stored_name)

    with pytest.raises(StoredContentNotFoundError):
        await container.download_file().execute(file_id)
