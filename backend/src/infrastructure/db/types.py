"""Custom SQLAlchemy types bridging domain value objects and plain columns."""

from enum import StrEnum
from typing import Any

from sqlalchemy import Dialect, String
from sqlalchemy.types import TypeDecorator


class StrEnumType(TypeDecorator[StrEnum]):
    """Stores a :class:`~enum.StrEnum` as a plain ``VARCHAR``.

    Deliberately not ``sqlalchemy.Enum``: the existing columns are ``VARCHAR``
    and must stay that way, and a native enum would make adding a status a
    migration instead of a code change.
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
