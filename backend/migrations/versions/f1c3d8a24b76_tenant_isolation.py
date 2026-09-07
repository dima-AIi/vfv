"""tenant isolation: org stamp columns + platform role partial unique index

Revision ID: f1c3d8a24b76
Revises: e6a9b4c27d83
Create Date: 2026-08-26 00:30:00.000000

"""
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from app.modules.rbac.seed import stable_id

revision: str = "f1c3d8a24b76"
down_revision: str | Sequence[str] | None = "e6a9b4c27d83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLAYGROUND_ORG_NAME = "DevOS Playground"
TENANT_TABLES = ("project", "task", "document", "ai_action")


def upgrade() -> None:
    op.create_index(
        "ux_user_role_platform",
        "user_role",
        ["user_id", "role_id"],
        unique=True,
        sqlite_where=sa.text("organization_id IS NULL"),
    )

    for table in TENANT_TABLES:
        with op.batch_alter_table(table, schema=None) as batch:
            batch.add_column(
                sa.Column("organization_id", sa.Uuid(), nullable=True),
            )
            batch.create_foreign_key(
                f"fk_{table}_organization_id_organization",
                "organization",
                ["organization_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch.create_index(f"ix_{table}_organization_id", ["organization_id"])

    connection = op.get_bind()
    org_exists = connection.execute(
        sa.text("SELECT 1 FROM organization WHERE name = :name"),
        {"name": PLAYGROUND_ORG_NAME},
    ).first()
    if org_exists is None:
        now = datetime.now(UTC).isoformat()
        connection.execute(
            sa.text(
                "INSERT INTO organization (id, name, description, status, created_by,"
                " version, created_at, updated_at)"
                " VALUES (:id, :name, NULL, 'active', NULL, 1, :created_at, :updated_at)",
            ),
            {
                "id": stable_id("organization", PLAYGROUND_ORG_NAME).hex,
                "name": PLAYGROUND_ORG_NAME,
                "created_at": now,
                "updated_at": now,
            },
        )
    org_id = connection.execute(
        sa.text("SELECT id FROM organization WHERE name = :name"),
        {"name": PLAYGROUND_ORG_NAME},
    ).scalar_one()

    for table in TENANT_TABLES:
        connection.execute(
            sa.text(
                f"UPDATE {table} SET organization_id = :org_id"
                " WHERE organization_id IS NULL",
            ),
            {"org_id": org_id},
        )


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.drop_index(f"ix_{table}_organization_id", table_name=table)
        op.drop_constraint(f"fk_{table}_organization_id_organization", table)
        op.drop_column(table, "organization_id")
    op.drop_index("ux_user_role_platform", table_name="user_role")
