"""add listing indexes and cascade alerts on file delete

Two problems this fixes:

* ``GET /files`` and ``GET /alerts`` sort by ``created_at DESC`` with no
  supporting index, so every request was a sequential scan plus a sort.
* ``alerts.file_id`` had no index (Postgres does not create one for a foreign
  key), which made the referential check on ``DELETE FROM files`` scan the whole
  alerts table - and, because the constraint had no ``ON DELETE`` action,
  deleting a file that had already produced an alert failed outright.

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
