"""Тесты HTTP-контракта, прогоняемые через настоящее приложение FastAPI."""

from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.container import Container
from src.presentation.http.app import create_app
from src.presentation.http.dependencies import provide_container
from tests.doubles import RecordingQueue


@pytest.fixture
def app(container: Container) -> FastAPI:
    app = create_app(container.settings)
    app.dependency_overrides[provide_container] = lambda: container
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def upload(client: AsyncClient, *, title: str = "Doc", name: str = "a.txt", content: bytes = b"hi") -> dict:
    response = await client.post(
        "/files",
        data={"title": title},
        files={"file": (name, content, "text/plain")},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_upload_returns_the_full_file_representation(client: AsyncClient, queue: RecordingQueue) -> None:
    body = await upload(client, title="Contract", name="contract.txt", content=b"line\n")

    assert body.keys() == {
        "id",
        "title",
        "original_name",
        "mime_type",
        "size",
        "processing_status",
        "scan_status",
        "scan_details",
        "metadata_json",
        "requires_attention",
        "created_at",
        "updated_at",
    }
    assert body["title"] == "Contract"
    assert body["original_name"] == "contract.txt"
    assert body["size"] == 5
    assert body["processing_status"] == "uploaded"
    assert queue.enqueued == [body["id"]]


async def test_empty_upload_is_a_400(client: AsyncClient) -> None:
    response = await client.post("/files", data={"title": "t"}, files={"file": ("e.txt", b"", "text/plain")})

    assert response.status_code == 400
    assert response.json() == {"detail": "File is empty"}


async def test_oversized_upload_is_a_413(client: AsyncClient, container: Container) -> None:
    container.settings.max_upload_size = 8

    response = await client.post("/files", data={"title": "t"}, files={"file": ("big.txt", b"x" * 64, "text/plain")})

    assert response.status_code == 413


async def test_unknown_file_is_a_404(client: AsyncClient) -> None:
    response = await client.get("/files/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}


async def test_listing_is_paginated(client: AsyncClient) -> None:
    for index in range(3):
        await upload(client, name=f"f{index}.txt")

    assert len((await client.get("/files")).json()) == 3
    assert len((await client.get("/files", params={"limit": 2})).json()) == 2
    assert len((await client.get("/files", params={"limit": 2, "offset": 2})).json()) == 1

    assert (await client.get("/files", params={"limit": 0})).status_code == 422


async def test_rename(client: AsyncClient) -> None:
    file = await upload(client)

    response = await client.patch(f"/files/{file['id']}", json={"title": "Renamed"})

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"
    assert (await client.patch(f"/files/{file['id']}", json={"title": ""})).status_code == 422


async def test_download_returns_the_original_bytes_and_name(client: AsyncClient) -> None:
    file = await upload(client, name="report.txt", content=b"payload bytes")

    response = await client.get(f"/files/{file['id']}/download")

    assert response.status_code == 200
    assert response.content == b"payload bytes"
    assert "report.txt" in response.headers["content-disposition"]


async def test_delete(client: AsyncClient) -> None:
    file = await upload(client)

    assert (await client.delete(f"/files/{file['id']}")).status_code == 204
    assert (await client.get(f"/files/{file['id']}")).status_code == 404
    assert (await client.delete(f"/files/{file['id']}")).status_code == 404


async def test_alerts_endpoint(client: AsyncClient, container: Container) -> None:
    file = await upload(client, name="setup.exe")
    await container.process_file().execute(file["id"])

    body = (await client.get("/alerts")).json()

    assert len(body) == 1
    assert body[0]["file_id"] == file["id"]
    assert body[0]["level"] == "warning"


async def test_health(client: AsyncClient) -> None:
    assert (await client.get("/health")).json() == {"status": "ok"}
