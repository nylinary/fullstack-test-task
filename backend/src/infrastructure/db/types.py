"""Свои типы SQLAlchemy, связывающие доменные value objects с обычными колонками."""

from enum import StrEnum
from typing import Any

from sqlalchemy import Dialect, String
from sqlalchemy.types import TypeDecorator


class StrEnumType(TypeDecorator[StrEnum]):
    """Хранит :class:`~enum.StrEnum` как обычный ``VARCHAR``.

    Намеренно не ``sqlalchemy.Enum``: существующие колонки — ``VARCHAR`` и
    должны такими остаться, а нативный enum превратил бы добавление статуса из
    правки кода в миграцию.
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_type: type[StrEnum], length: int) -> None:
        super().__init__(length=length)
        self._enum_type = enum_type

    def process_bind_param(self, value: Any, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return str(self._enum_type(value).value)

    def process_result_value(self, value: Any, dialect: Dialect) -> StrEnum | None:
        if value is None:
            return None
        return self._enum_type(value)
