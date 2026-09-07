import os
import pathlib
import tempfile
from collections.abc import Iterator

import pytest

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{pathlib.Path(__file__).parent / '_test.db'}"
os.environ["AI_PROVIDER"] = "mock"
os.environ["STORAGE_DIR"] = tempfile.mkdtemp(prefix="devos_test_storage_")

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Import all models to register them with SQLAlchemy metadata
import app.modules.ai.models  # noqa: F401
import app.modules.comments.models  # noqa: F401
import app.modules.crm.models  # noqa: F401
import app.modules.documents.models  # noqa: F401
import app.modules.files.models  # noqa: F401
import app.modules.identity.models  # noqa: F401
import app.modules.notifications.models  # noqa: F401
import app.modules.organizations.models  # noqa: F401
import app.modules.projects.models  # noqa: F401
import app.modules.rbac.models  # noqa: F401
import app.modules.settings.models  # noqa: F401
import app.modules.tasks.models  # noqa: F401
from app.main import app as fastapi_app  # noqa: E402

TABLES = (
    "ai_result",
    "ai_action",
    "session",
    "credential",
    "audit_record",
    "setting",
    "notification",
    "comment",
    "customer_tag",
    "customer_note",
    "contact",
    "tag",
    "customer",
    "company",
    "file_version",
    "file",
    "task_attachment",
    "document",
    "folder",
    "project_member",
    "task",
    "project",
    "user_role",
    "role_permission",
    "organization",
    "user",
    "project",
    "role",
    "permission",
)

_engine_ready = False


def _prepare_database() -> None:
    global _engine_ready
    if _engine_ready:
        return
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    _engine_ready = True


@pytest.fixture()
def client() -> Iterator[TestClient]:
    _prepare_database()
    import asyncio

    from app.modules.rbac.seed import ensure_system_seed

    asyncio.run(ensure_system_seed())
    with TestClient(fastapi_app) as test_client:
        yield test_client
    from sqlalchemy import text

    from app.core.database import engine

    async def _cleanup() -> None:
        async with engine.begin() as connection:
            for table in TABLES:
                await connection.execute(text(f"DELETE FROM {table}"))

    asyncio.run(_cleanup())
