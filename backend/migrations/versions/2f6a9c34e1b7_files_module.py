"""files platform module: file, file_version, files permissions seed

Revision ID: 2f6a9c34e1b7
Revises: 2b7e5d91c4a8
Create Date: 2026-09-01 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.modules.rbac.seed import apply_seed_sync

revision: str = "2f6a9c34e1b7"
down_revision: str | Sequence[str] | None = "2b7e5d91c4a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "file",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user.id"],
            name=op.f("fk_file_created_by_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_file_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_file_storage_key")),
    )
    op.create_index(op.f("ix_file_organization_id"), "file", ["organization_id"], unique=False)

    op.create_table(
        "file_version",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["user.id"],
            name=op.f("fk_file_version_created_by_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["file.id"],
            name=op.f("fk_file_version_file_id_file"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_file_version")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_file_version_storage_key")),
        sa.UniqueConstraint(
            "file_id",
            "version",
            name=op.f("uq_file_version_file_id_version"),
        ),
    )
    op.create_index(op.f("ix_file_version_file_id"), "file_version", ["file_id"], unique=False)

    apply_seed_sync(op.get_bind())


def downgrade() -> None:
    op.drop_index(op.f("ix_file_version_file_id"), table_name="file_version")
    op.drop_table("file_version")
    op.drop_index(op.f("ix_file_organization_id"), table_name="file")
    op.drop_table("file")
