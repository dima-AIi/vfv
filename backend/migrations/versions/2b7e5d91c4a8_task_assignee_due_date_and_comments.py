"""task assignee and due date; comment table

Revision ID: 2b7e5d91c4a8
Revises: 8c6d7b5aeaa4
Create Date: 2026-08-31 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.modules.rbac.seed import apply_seed_sync

revision: str = "2b7e5d91c4a8"
down_revision: str | Sequence[str] | None = "8c6d7b5aeaa4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("task") as batch_op:
        batch_op.add_column(sa.Column("due_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("assignee_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_task_assignee_id"),
            ["assignee_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_task_assignee_id_user",
            "user",
            ["assignee_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "comment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("body", sa.String(length=5000), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
            name=op.f("fk_comment_author_id_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_comment_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
            name=op.f("fk_comment_task_id_task"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comment")),
    )
    op.create_index(op.f("ix_comment_task_id"), "comment", ["task_id"], unique=False)
    op.create_index(
        op.f("ix_comment_organization_id"),
        "comment",
        ["organization_id"],
        unique=False,
    )

    apply_seed_sync(op.get_bind())


def downgrade() -> None:
    op.drop_index(op.f("ix_comment_organization_id"), table_name="comment")
    op.drop_index(op.f("ix_comment_task_id"), table_name="comment")
    op.drop_table("comment")
    with op.batch_alter_table("task") as batch_op:
        batch_op.drop_constraint("fk_task_assignee_id_user", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_task_assignee_id"))
        batch_op.drop_column("assignee_id")
        batch_op.drop_column("due_date")
