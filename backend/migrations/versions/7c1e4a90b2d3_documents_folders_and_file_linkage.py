"""documents folders + document folder_id/file_id linkage

Revision ID: 7c1e4a90b2d3
Revises: 2f6a9c34e1b7
Create Date: 2026-09-02 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7c1e4a90b2d3"
down_revision: str | Sequence[str] | None = "2f6a9c34e1b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "folder",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_folder_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["folder.id"],
            name=op.f("fk_folder_parent_id_folder"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_folder")),
    )
    op.create_index(
        op.f("ix_folder_organization_id"), "folder", ["organization_id"], unique=False
    )
    op.create_index(op.f("ix_folder_parent_id"), "folder", ["parent_id"], unique=False)

    with op.batch_alter_table("document") as batch_op:
        batch_op.add_column(sa.Column("folder_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("file_id", sa.Uuid(), nullable=True))
        batch_op.create_index(batch_op.f("ix_document_folder_id"), ["folder_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_document_file_id"), ["file_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_document_folder_id_folder",
            "folder",
            ["folder_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_document_file_id_file",
            "file",
            ["file_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("document") as batch_op:
        batch_op.drop_constraint("fk_document_file_id_file", type_="foreignkey")
        batch_op.drop_constraint("fk_document_folder_id_folder", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_document_file_id"))
        batch_op.drop_index(batch_op.f("ix_document_folder_id"))
        batch_op.drop_column("file_id")
        batch_op.drop_column("folder_id")
    op.drop_index(op.f("ix_folder_parent_id"), table_name="folder")
    op.drop_index(op.f("ix_folder_organization_id"), table_name="folder")
    op.drop_table("folder")
