"""add soft delete columns to project and task

Revision ID: b7e4c2a91d53
Revises: ff34b89c63af
Create Date: 2026-08-25 21:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e4c2a91d53"
down_revision: str | Sequence[str] | None = "ff34b89c63af"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "project",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "task",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("task", "deleted_at")
    op.drop_column("project", "deleted_at")
