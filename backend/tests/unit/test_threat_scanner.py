import pytest

from src.domain.entities import StoredFile
from src.domain.services.threat_scanner import ThreatScanner
from src.domain.value_objects import ScanStatus


def make_file(*, original_name: str = "report.txt", size: int = 10, mime_type: str = "text/plain") -> StoredFile:
    return StoredFile.create(
        id="id",
        title="t",
        original_name=original_name,
        stored_name="stored",
        mime_type=mime_type,
        size=size,
    )


@pytest.mark.parametrize(
    ("original_name", "size", "mime_type", "expected_details"),
    [
        ("report.txt", 10, "text/plain", "no threats found"),
        ("payload.EXE", 10, "application/octet-stream", "suspicious extension .exe"),
        ("big.txt", 10 * 1024 * 1024 + 1, "text/plain", "file is larger than 10 MB"),
        ("doc.pdf", 10, "text/html", "pdf extension does not match mime type"),
        ("doc.pdf", 10, "application/pdf", "no threats found"),
        ("doc.pdf", 10, "application/octet-stream", "no threats found"),
        (
            "script.sh",
            10 * 1024 * 1024 + 1,
            "text/plain",
            "suspicious extension .sh, file is larger than 10 MB",
        ),
    ],
)
def test_scan_details(original_name: str, size: int, mime_type: str, expected_details: str) -> None:
    report = ThreatScanner().scan(make_file(original_name=original_name, size=size, mime_type=mime_type))

    assert report.details == expected_details
    assert report.requires_attention is (expected_details != "no threats found")
    assert report.status is (ScanStatus.SUSPICIOUS if report.requires_attention else ScanStatus.CLEAN)


def test_exactly_at_the_size_limit_is_clean() -> None:
    report = ThreatScanner().scan(make_file(size=10 * 1024 * 1024))

    assert report.status is ScanStatus.CLEAN


def test_windows_paths_are_understood() -> None:
    report = ThreatScanner().scan(make_file(original_name=r"C:\Users\bob\payload.bat"))

    assert report.details == "suspicious extension .bat"
