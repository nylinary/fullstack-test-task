import random

import pytest

from src.domain.services.metadata import (
    ContentAnalyzer,
    MetadataExtractor,
    PdfContentAnalyzer,
    TextContentAnalyzer,
)
from tests.unit.test_threat_scanner import make_file

SAMPLE_TEXTS = [
    "",
    "one line",
    "one line\n",
    "a\nb\nc",
    "a\r\nb\r\nc\r\n",
    "trailing\r",
    "\n\n\n",
    "unicode \u00e9\u00e8\u00ea and \u2028 separator",
    "form\x0cfeed\x0bvertical",
    "mixed\r\n\r\nblank\n\rlines\r",
]


def feed_in_chunks(analyzer: ContentAnalyzer, data: bytes, size: int) -> None:
    for start in range(0, len(data), size):
        analyzer.feed(data[start : start + size])


@pytest.mark.parametrize("text", SAMPLE_TEXTS)
@pytest.mark.parametrize("chunk_size", [1, 2, 3, 7, 4096])
def test_streaming_text_counts_match_whole_file_counts(text: str, chunk_size: int) -> None:
    analyzer = TextContentAnalyzer()
    feed_in_chunks(analyzer, text.encode(), chunk_size)

    assert analyzer.result() == {"line_count": len(text.splitlines()), "char_count": len(text)}


def test_streaming_matches_on_random_input() -> None:
    alphabet = "ab\n\r\u2028\x0c \u00e9"
    rng = random.Random(1234)

    for _ in range(200):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 120)))
        analyzer = TextContentAnalyzer()
        feed_in_chunks(analyzer, text.encode(), rng.randint(1, 8))

        assert analyzer.result() == {"line_count": len(text.splitlines()), "char_count": len(text)}


@pytest.mark.parametrize("chunk_size", [1, 5, 11, 4096])
def test_pdf_page_markers_are_counted_across_chunk_boundaries(chunk_size: int) -> None:
    content = b"%PDF-1.4" + b"/Type /Page" * 7 + b"trailer"

    analyzer = PdfContentAnalyzer()
    feed_in_chunks(analyzer, content, chunk_size)

    assert analyzer.result() == {"approx_page_count": content.count(b"/Type /Page")}


def test_pdf_without_markers_reports_at_least_one_page() -> None:
    analyzer = PdfContentAnalyzer()
    analyzer.feed(b"%PDF-1.4 no markers here")

    assert analyzer.result() == {"approx_page_count": 1}


def test_base_metadata() -> None:
    file = make_file(original_name="Report.TXT", size=42, mime_type="text/plain")

    assert MetadataExtractor().base_metadata(file) == {
        "extension": ".txt",
        "size_bytes": 42,
        "mime_type": "text/plain",
    }


@pytest.mark.parametrize(
    ("mime_type", "expected"),
    [
        ("text/plain", TextContentAnalyzer),
        ("text/csv", TextContentAnalyzer),
        ("application/pdf", PdfContentAnalyzer),
        ("image/png", type(None)),
    ],
)
def test_analyzer_selection(mime_type: str, expected: type) -> None:
    assert isinstance(MetadataExtractor().analyzer_for(mime_type), expected)
