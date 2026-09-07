"""document soft delete + nullable relative_path

Revision ID: 9d3b5f70c8e2
Revises: 7c1e4a90b2d3
Create Date: 2026-09-03 09:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9d3b5f70c8e2"
down_revision: str | Sequence[str] | None = "7c1e4a90b2d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("document") as batch_op:
        batch_op.add_column(
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.alter_column(
            "relative_path",
            existing_type=sa.String(length=1000),
            nullable=True,
        )
    # File-based documents previously stored an empty string; they now use NULL.
    op.execute(sa.text("UPDATE document SET relative_path = NULL WHERE relative_path = ''"))


def downgrade() -> None:
    op.execute(sa.text("UPDATE document SET relative_path = '' WHERE relative_path IS NULL"))
    with op.batch_alter_table("document") as batch_op:
        batch_op.alter_column(
            "relative_path",
            existing_type=sa.String(length=1000),
            nullable=False,
        )
        batch_op.drop_column("deleted_at")
