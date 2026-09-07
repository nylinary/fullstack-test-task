"""Помощники для работы с именами файлов, общие для домена и адаптеров хранилища."""

import mimetypes
from pathlib import PurePosixPath, PureWindowsPath

# Всё, чем подобранное имя файла могло бы вырваться за пределы директории
# хранилища или испортить заголовок Content-Disposition.
_UNSAFE_CHARS = str.maketrans({"\r": "_", "\n": "_", "\x00": "_", '"': "_"})
MAX_FILENAME_LENGTH = 255


def file_extension(name: str) -> str:
    """Вернуть расширение ``name`` в нижнем регистре (``".pdf"`` или ``""``).

    Понимает и POSIX-, и Windows-разделители: значение приходит прямо из
    multipart-тела браузера.
    """
    return PurePosixPath(PureWindowsPath(name).name).suffix.lower()


def sanitize_filename(name: str, *, fallback: str) -> str:
    """Убрать из ``name`` любые компоненты пути и управляющие символы."""
    base = PurePosixPath(PureWindowsPath(name).name).name.translate(_UNSAFE_CHARS).strip()
    if not base or base in {".", ".."}:
        return fallback
    return base[:MAX_FILENAME_LENGTH]


def guess_mime_type(name: str, *, default: str = "application/octet-stream") -> str:
    """MIME-тип по имени файла — на случай, если клиент его не прислал."""
    return mimetypes.guess_type(name)[0] or default
