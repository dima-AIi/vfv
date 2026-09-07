"""project due_date, project_member, task_attachment

Revision ID: 5d2b8f30c6a1
Revises: 8c4a7e21f0b3
Create Date: 2026-09-08 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5d2b8f30c6a1"
down_revision: str | Sequence[str] | None = "8c4a7e21f0b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("project") as batch_op:
        batch_op.add_column(sa.Column("due_date", sa.Date(), nullable=True))

    op.create_table(
        "project_member",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
            name=op.f("fk_project_member_project_id_project"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name=op.f("fk_project_member_user_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_project_member")),
        sa.UniqueConstraint(
            "project_id", "user_id", name="uq_project_member_project_id_user_id"
        ),
    )
    op.create_index(
        op.f("ix_project_member_project_id"), "project_member", ["project_id"], unique=False
    )
    op.create_index(
        op.f("ix_project_member_user_id"), "project_member", ["user_id"], unique=False
    )

    op.create_table(
        "task_attachment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user.id"],
            name=op.f("fk_task_attachment_created_by_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["file.id"],
            name=op.f("fk_task_attachment_file_id_file"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
            name=op.f("fk_task_attachment_task_id_task"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_task_attachment")),
        sa.UniqueConstraint("task_id", "file_id", name="uq_task_attachment_task_id_file_id"),
    )
    op.create_index(
        op.f("ix_task_attachment_task_id"), "task_attachment", ["task_id"], unique=False
    )
    op.create_index(
        op.f("ix_task_attachment_file_id"), "task_attachment", ["file_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_attachment_file_id"), table_name="task_attachment")
    op.drop_index(op.f("ix_task_attachment_task_id"), table_name="task_attachment")
    op.drop_table("task_attachment")
    op.drop_index(op.f("ix_project_member_user_id"), table_name="project_member")
    op.drop_index(op.f("ix_project_member_project_id"), table_name="project_member")
    op.drop_table("project_member")
    with op.batch_alter_table("project") as batch_op:
        batch_op.drop_column("due_date")
