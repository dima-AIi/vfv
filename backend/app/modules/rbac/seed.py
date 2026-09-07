"""System seed data for RBAC (roles, permissions, role_permission matrix).

Single source of truth used by both the Alembic migration (System Seed per
08_Database_Design) and test fixtures. Idempotent by natural keys.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Connection, text
from sqlalchemy.sql.elements import TextClause

SEED_NAMESPACE = uuid.UUID("6f1d2c34-7a5e-4b8f-9c0d-1e2f3a4b5c6d")


def stable_id(kind: str, key: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, f"devos:{kind}:{key}")


SYSTEM_ROLES: tuple[str, ...] = (
    "platform_admin",
    "org_admin",
    "manager",
    "employee",
    "guest",
)

ASSIGNABLE_ORG_ROLES: frozenset[str] = frozenset({"org_admin", "manager", "employee"})

ALL_PERMISSIONS: tuple[str, ...] = (
    "organization.organization.manage",
    "identity.user.manage",
    "projects.project.create",
    "projects.project.read",
    "projects.project.update",
    "projects.project.delete",
    "tasks.task.create",
    "tasks.task.read",
    "tasks.task.update",
    "tasks.task.delete",
    "documents.document.create",
    "documents.document.read",
    "documents.document.delete",
    "ai.action.run",
    "ai.action.read",
    "dashboard.dashboard.read",
    "audit.record.read",
    "comments.comment.delete",
    "files.file.upload",
    "files.file.read",
    "files.file.delete",
    "search.search.read",
    "crm.customer.create",
    "crm.customer.read",
    "crm.customer.update",
    "crm.customer.delete",
    "settings.platform.manage",
    "settings.organization.manage",
)

READ_PERMISSIONS: tuple[str, ...] = (
    "projects.project.read",
    "tasks.task.read",
    "documents.document.read",
    "files.file.read",
    "search.search.read",
    "crm.customer.read",
)

ROLE_PERMISSIONS: dict[str, Sequence[str]] = {
    "platform_admin": ALL_PERMISSIONS,
    "org_admin": (
        "organization.organization.manage",
        "identity.user.manage",
        "projects.project.create",
        "projects.project.read",
        "projects.project.update",
        "projects.project.delete",
        "tasks.task.create",
        "tasks.task.read",
        "tasks.task.update",
        "tasks.task.delete",
        "documents.document.create",
        "documents.document.read",
        "documents.document.delete",
        "ai.action.run",
        "ai.action.read",
        "dashboard.dashboard.read",
        "comments.comment.delete",
        "files.file.upload",
        "files.file.read",
        "files.file.delete",
        "search.search.read",
        "crm.customer.create",
        "crm.customer.read",
        "crm.customer.update",
        "crm.customer.delete",
        "settings.organization.manage",
        "audit.record.read",
    ),
    "manager": (
        "projects.project.create",
        "projects.project.read",
        "projects.project.update",
        "tasks.task.create",
        "tasks.task.read",
        "tasks.task.update",
        "documents.document.create",
        "documents.document.read",
        "ai.action.run",
        "ai.action.read",
        "dashboard.dashboard.read",
        "comments.comment.delete",
        "files.file.upload",
        "files.file.read",
        "search.search.read",
        "crm.customer.create",
        "crm.customer.read",
        "crm.customer.update",
        "crm.customer.delete",
    ),
    "employee": (
        "tasks.task.create",
        "tasks.task.read",
        "tasks.task.update",
        "documents.document.create",
        "documents.document.read",
        "ai.action.run",
        "ai.action.read",
        "dashboard.dashboard.read",
        "files.file.upload",
        "files.file.read",
        "search.search.read",
        "crm.customer.read",
    ),
    "guest": READ_PERMISSIONS,
}


def apply_seed_sync(connection: Connection) -> None:
    now = datetime.now(UTC).isoformat()

    existing_roles = {
        row[0]
        for row in connection.execute(
            text("SELECT name FROM role"),
        ).fetchall()
    }
    for name in SYSTEM_ROLES:
        if name in existing_roles:
            continue
        connection.execute(_role_insert(name, now))

    existing_permissions = {
        row[0]
        for row in connection.execute(
            text("SELECT code FROM permission"),
        ).fetchall()
    }
    for code in ALL_PERMISSIONS:
        if code in existing_permissions:
            continue
        connection.execute(_permission_insert(code, now))

    role_ids = {
        row[0]: uuid.UUID(row[1])
        for row in connection.execute(text("SELECT name, id FROM role")).fetchall()
    }
    permission_ids = {
        row[0]: uuid.UUID(row[1])
        for row in connection.execute(text("SELECT code, id FROM permission")).fetchall()
    }

    existing_pairs = {
        (row[0], row[1])
        for row in connection.execute(
            text(
                "SELECT r.name, p.code FROM role_permission rp"
                " JOIN role r ON r.id = rp.role_id"
                " JOIN permission p ON p.id = rp.permission_id",
            ),
        ).fetchall()
    }
    for role_name, codes in ROLE_PERMISSIONS.items():
        for code in codes:
            if (role_name, code) in existing_pairs:
                continue
            connection.execute(
                text(
                    "INSERT INTO role_permission (id, role_id, permission_id)"
                    " VALUES (:id, :role_id, :permission_id)",
                ),
                {
                    "id": stable_id("role_permission", f"{role_name}:{code}").hex,
                    "role_id": role_ids[role_name].hex,
                    "permission_id": permission_ids[code].hex,
                },
            )


def _role_insert(name: str, now: str) -> TextClause:

    return text(
        "INSERT INTO role (id, name, is_system, created_at, updated_at)"
        " VALUES (:id, :name, 1, :created_at, :updated_at)",
    ).bindparams(
        id=stable_id("role", name).hex,
        name=name,
        created_at=now,
        updated_at=now,
    )


def _permission_insert(code: str, now: str) -> TextClause:
    return text(
        "INSERT INTO permission (id, code, created_at, updated_at)"
        " VALUES (:id, :code, :created_at, :updated_at)",
    ).bindparams(
        id=stable_id("permission", code).hex,
        code=code,
        created_at=now,
        updated_at=now,
    )


async def ensure_system_seed() -> None:
    """Idempotent seed application for tests/runtime (async engine)."""
    from app.core.database import engine

    def _run(sync_connection: Connection) -> None:
        apply_seed_sync(sync_connection)

    async with engine.begin() as connection:
        await connection.run_sync(_run)
