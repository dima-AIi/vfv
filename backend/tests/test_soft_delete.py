import sqlite3
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers

TEST_DB_PATH = Path(__file__).parent / "_test.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(TEST_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _create_project(
    client: TestClient,
    owned: AuthorizedClient,
    name: str = "Soft Delete Project",
) -> dict:
    response = owned.post(
        "/api/v1/projects",
        json={"name": name, "description": "soft delete scenario"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _list_project_ids(owned: AuthorizedClient) -> set[str]:
    body = owned.get("/api/v1/projects?pageSize=100").json()
    return {p["id"] for p in body["data"]}


def test_deleted_project_hidden_but_row_kept(client: TestClient) -> None:
    owned = AuthorizedClient(
        client,
        auth_headers(client, "soft1@example.com", create_org=True),
    )
    total_before = owned.get("/api/v1/projects").json()["meta"]["pagination"]["totalItems"]

    project = _create_project(client, owned)
    project_id = project["id"]

    deleted = owned.delete(f"/api/v1/projects/{project_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert owned.get(f"/api/v1/projects/{project_id}").status_code == 404
    assert project_id not in _list_project_ids(owned)

    total_after = owned.get("/api/v1/projects").json()["meta"]["pagination"]["totalItems"]
    assert total_after == total_before

    updated = owned.patch(
        f"/api/v1/projects/{project_id}",
        json={"description": "zombie"},
    )
    assert updated.status_code == 404

    with _connect() as connection:
        row = connection.execute(
            "SELECT deleted_at FROM project WHERE id = ?",
            (project_id.replace("-", ""),),
        ).fetchone()
    assert row is not None
    assert row["deleted_at"] is not None


def test_delete_project_with_items_conflict_then_success(client: TestClient) -> None:
    owned = AuthorizedClient(
        client,
        auth_headers(client, "soft2@example.com", create_org=True, org_name="Soft2 Org"),
    )
    project = _create_project(client, owned, "Non Empty Project")
    project_id = project["id"]

    task = owned.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "blocking task"},
    ).json()["data"]
    document = owned.post(
        "/api/v1/documents",
        json={
            "title": "blocking doc",
            "relative_path": "99_AI/03_GLOSSARY.md",
            "project_id": project_id,
        },
    ).json()["data"]

    conflict = owned.delete(f"/api/v1/projects/{project_id}")
    assert conflict.status_code == 409
    error = conflict.json()["error"]
    assert error["code"] == "PROJECT_NOT_EMPTY"
    assert error["details"][0]["tasks"] >= 1
    assert error["details"][0]["documents"] >= 1

    removed_task = owned.delete(f"/api/v1/tasks/{task['id']}")
    assert removed_task.status_code == 204
    removed_document = owned.delete(f"/api/v1/documents/{document['id']}")
    assert removed_document.status_code == 204

    second_attempt = owned.delete(f"/api/v1/projects/{project_id}")
    assert second_attempt.status_code == 204

    with _connect() as connection:
        row = connection.execute(
            "SELECT deleted_at FROM project WHERE id = ?",
            (project_id.replace("-", ""),),
        ).fetchone()
    assert row is not None and row["deleted_at"] is not None


def test_soft_delete_task_cycle(client: TestClient) -> None:
    owned = AuthorizedClient(
        client,
        auth_headers(client, "soft3@example.com", create_org=True, org_name="Soft3 Org"),
    )
    project = _create_project(client, owned, "Task Cycle Project")
    project_id = project["id"]

    task = owned.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "doomed task", "priority": "high"},
    ).json()["data"]
    task_id = task["id"]

    deleted = owned.delete(f"/api/v1/tasks/{task_id}")
    assert deleted.status_code == 204

    assert owned.get(f"/api/v1/tasks/{task_id}").status_code == 404

    listed = owned.get(f"/api/v1/tasks?project_id={project_id}")
    assert listed.json()["meta"]["pagination"]["totalItems"] == 0
    assert listed.json()["data"] == []

    updated = owned.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"})
    assert updated.status_code == 404

    with _connect() as connection:
        row = connection.execute(
            "SELECT deleted_at FROM task WHERE id = ?",
            (task_id.replace("-", ""),),
        ).fetchone()
    assert row is not None
    assert row["deleted_at"] is not None


def test_delete_missing_project_returns_404(client: TestClient) -> None:
    owned = AuthorizedClient(
        client,
        auth_headers(client, "soft4@example.com", create_org=True, org_name="Soft4 Org"),
    )
    response = owned.delete(f"/api/v1/projects/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_delete_missing_task_returns_404(client: TestClient) -> None:
    owned = AuthorizedClient(
        client,
        auth_headers(client, "soft5@example.com", create_org=True, org_name="Soft5 Org"),
    )
    response = owned.delete(f"/api/v1/tasks/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TASK_NOT_FOUND"
