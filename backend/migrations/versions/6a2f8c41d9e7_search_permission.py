"""search permission: seed search.search.read to all system roles

Revision ID: 6a2f8c41d9e7
Revises: 4e8a1c62d0b5
Create Date: 2026-09-05 09:00:00.000000

"""
from collections.abc import Sequence

from alembic import op

from app.modules.rbac.seed import apply_seed_sync

revision: str = "6a2f8c41d9e7"
down_revision: str | Sequence[str] | None = "4e8a1c62d0b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Idempotent seed: adds the new permission and its role_permission links
    # for every system role (single source of truth in rbac/seed.py).
    apply_seed_sync(op.get_bind())


def downgrade() -> None:
    conn = op.get_bind()
    conn.exec_driver_sql(
        "DELETE FROM role_permission WHERE permission_id ="
        " (SELECT id FROM permission WHERE code = 'search.search.read')"
    )
    conn.exec_driver_sql("DELETE FROM permission WHERE code = 'search.search.read'")
