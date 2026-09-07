"""setting storage + audit_record.organization_id + settings permissions

Revision ID: 8c4a7e21f0b3
Revises: 3b9d0e57a1c4
Create Date: 2026-09-07 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.modules.rbac.seed import apply_seed_sync

revision: str = "8c4a7e21f0b3"
down_revision: str | Sequence[str] | None = "3b9d0e57a1c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "setting",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_setting")),
        sa.UniqueConstraint(
            "scope", "owner_id", "key", name="uq_setting_scope_owner_id_key"
        ),
    )

    with op.batch_alter_table("audit_record") as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_audit_record_organization_id"),
            ["organization_id"],
            unique=False,
        )

    apply_seed_sync(op.get_bind())


def downgrade() -> None:
    with op.batch_alter_table("audit_record") as batch_op:
        batch_op.drop_index(batch_op.f("ix_audit_record_organization_id"))
        batch_op.drop_column("organization_id")
    op.drop_table("setting")
