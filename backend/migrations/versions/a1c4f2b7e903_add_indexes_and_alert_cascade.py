"""add listing indexes and cascade alerts on file delete

Исправляет две проблемы:

* ``GET /files`` и ``GET /alerts`` сортируют по ``created_at DESC``, и ни одного
  подходящего индекса не было — каждый запрос означал последовательное
  сканирование плюс сортировку.
* У ``alerts.file_id`` не было индекса (Postgres не создаёт его для внешнего
  ключа), поэтому проверка ссылочной целостности при ``DELETE FROM files``
  сканировала всю таблицу алертов. А поскольку у ограничения не было действия
  ``ON DELETE``, удаление файла, по которому уже был алерт, просто падало.

Revision ID: a1c4f2b7e903
Revises: 0d6439d2e79f
Create Date: 2026-09-06 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1c4f2b7e903"
down_revision: str | Sequence[str] | None = "0d6439d2e79f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ALERTS_FK = "alerts_file_id_fkey"


def upgrade() -> None:
    op.create_index("ix_files_created_at_id", "files", ["created_at", "id"])
    op.create_index("ix_alerts_created_at_id", "alerts", ["created_at", "id"])
    op.create_index("ix_alerts_file_id", "alerts", ["file_id"])

    op.drop_constraint(ALERTS_FK, "alerts", type_="foreignkey")
    op.create_foreign_key(ALERTS_FK, "alerts", "files", ["file_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.drop_constraint(ALERTS_FK, "alerts", type_="foreignkey")
    op.create_foreign_key(ALERTS_FK, "alerts", "files", ["file_id"], ["id"])

    op.drop_index("ix_alerts_file_id", table_name="alerts")
    op.drop_index("ix_alerts_created_at_id", table_name="alerts")
    op.drop_index("ix_files_created_at_id", table_name="files")
