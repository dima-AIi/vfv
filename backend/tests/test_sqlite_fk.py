import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import engine


def test_foreign_keys_enforced_on_direct_sql(client: TestClient) -> None:
    assert client.get("/api/v1/health").status_code == 200

    orphan_project_id = uuid.uuid4().hex
    task_id = uuid.uuid4().hex

    async def insert_orphan_task() -> None:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO task (id, project_id, title, description, status,"
                    " priority, created_at, updated_at)"
                    " VALUES (:id, :project_id, 'orphan', '', 'open', 'low',"
                    " CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {"id": task_id, "project_id": orphan_project_id},
            )

    import asyncio

    with pytest.raises(IntegrityError):
        asyncio.run(insert_orphan_task())
