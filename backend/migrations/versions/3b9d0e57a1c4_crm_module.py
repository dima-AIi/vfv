"""CRM module: company, customer, contact, customer_note, tag, customer_tag;
project.customer_id link; crm permissions seed.

Revision ID: 3b9d0e57a1c4
Revises: 6a2f8c41d9e7
Create Date: 2026-09-06 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.modules.rbac.seed import apply_seed_sync

revision: str = "3b9d0e57a1c4"
down_revision: str | Sequence[str] | None = "6a2f8c41d9e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "company",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_company_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company")),
    )
    op.create_index(
        op.f("ix_company_organization_id"), "company", ["organization_id"], unique=False
    )

    op.create_table(
        "customer",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="lead"),
        sa.Column("description", sa.String(length=5000), nullable=False, server_default=""),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["company.id"],
            name=op.f("fk_customer_company_id_company"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_customer_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer")),
    )
    op.create_index(
        op.f("ix_customer_organization_id"), "customer", ["organization_id"], unique=False
    )
    op.create_index(
        op.f("ix_customer_company_id"), "customer", ["company_id"], unique=False
    )

    op.create_table(
        "contact",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customer.id"],
            name=op.f("fk_contact_customer_id_customer"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_contact_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contact")),
    )
    op.create_index(
        op.f("ix_contact_customer_id"), "contact", ["customer_id"], unique=False
    )
    op.create_index(
        op.f("ix_contact_organization_id"), "contact", ["organization_id"], unique=False
    )

    op.create_table(
        "customer_note",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("body", sa.String(length=5000), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
            name=op.f("fk_customer_note_author_id_user"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customer.id"],
            name=op.f("fk_customer_note_customer_id_customer"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_customer_note_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_note")),
    )
    op.create_index(
        op.f("ix_customer_note_customer_id"), "customer_note", ["customer_id"], unique=False
    )
    op.create_index(
        op.f("ix_customer_note_organization_id"),
        "customer_note",
        ["organization_id"],
        unique=False,
    )

    op.create_table(
        "tag",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_tag_organization_id_organization"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tag")),
        sa.UniqueConstraint(
            "organization_id", "name", name=op.f("uq_tag_organization_id_name")
        ),
    )
    op.create_index(op.f("ix_tag_organization_id"), "tag", ["organization_id"], unique=False)

    op.create_table(
        "customer_tag",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customer.id"],
            name=op.f("fk_customer_tag_customer_id_customer"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tag.id"],
            name=op.f("fk_customer_tag_tag_id_tag"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_customer_tag")),
        sa.UniqueConstraint(
            "customer_id", "tag_id", name=op.f("uq_customer_tag_customer_id_tag_id")
        ),
    )
    op.create_index(
        op.f("ix_customer_tag_customer_id"), "customer_tag", ["customer_id"], unique=False
    )
    op.create_index(
        op.f("ix_customer_tag_tag_id"), "customer_tag", ["tag_id"], unique=False
    )

    with op.batch_alter_table("project") as batch_op:
        batch_op.add_column(sa.Column("customer_id", sa.Uuid(), nullable=True))
        batch_op.create_index(batch_op.f("ix_project_customer_id"), ["customer_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_project_customer_id_customer",
            "customer",
            ["customer_id"],
            ["id"],
            ondelete="SET NULL",
        )

    apply_seed_sync(op.get_bind())


def downgrade() -> None:
    with op.batch_alter_table("project") as batch_op:
        batch_op.drop_constraint("fk_project_customer_id_customer", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_project_customer_id"))
        batch_op.drop_column("customer_id")

    op.drop_index(op.f("ix_customer_tag_tag_id"), table_name="customer_tag")
    op.drop_index(op.f("ix_customer_tag_customer_id"), table_name="customer_tag")
    op.drop_table("customer_tag")
    op.drop_index(op.f("ix_tag_organization_id"), table_name="tag")
    op.drop_table("tag")
    op.drop_index(op.f("ix_customer_note_organization_id"), table_name="customer_note")
    op.drop_index(op.f("ix_customer_note_customer_id"), table_name="customer_note")
    op.drop_table("customer_note")
    op.drop_index(op.f("ix_contact_organization_id"), table_name="contact")
    op.drop_index(op.f("ix_contact_customer_id"), table_name="contact")
    op.drop_table("contact")
    op.drop_index(op.f("ix_customer_company_id"), table_name="customer")
    op.drop_index(op.f("ix_customer_organization_id"), table_name="customer")
    op.drop_table("customer")
    op.drop_index(op.f("ix_company_organization_id"), table_name="company")
    op.drop_table("company")
