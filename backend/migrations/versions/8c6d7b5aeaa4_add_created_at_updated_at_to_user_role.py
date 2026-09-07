"""add created_at updated_at to user_role

Revision ID: 8c6d7b5aeaa4
Revises: f1c3d8a24b76
Create Date: 2026-08-28 00:47:48.377842

"""
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = '8c6d7b5aeaa4'
down_revision: str | Sequence[str] | None = 'f1c3d8a24b76'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SQLite rejects ALTER TABLE ADD COLUMN with a non-constant default when the
    # table contains rows; batch mode recreates the table instead.
    with op.batch_alter_table("user_role") as batch_op:
        batch_op.add_column(
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    # Backfill existing rows
    now = datetime.now(UTC).isoformat()
    op.execute(sa.text(f"UPDATE user_role SET created_at = '{now}', updated_at = '{now}' WHERE created_at IS NULL"))


def downgrade() -> None:
    op.drop_column("user_role", "created_at")
    op.drop_column("user_role", "updated_at")
