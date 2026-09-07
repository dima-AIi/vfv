import uuid

from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers


class _Context:
    def __init__(self, client: TestClient, email: str | None = None) -> None:
        email = email or "tasks.owner@example.com"
        self.headers = auth_headers(
            client,
            email,
            create_org=True,
            org_name=f"TaskOrg-{email}",
        )
        self.client = AuthorizedClient(client, self.headers)
        self.project = self.client.post(
            "/api/v1/projects",
            json={"name": f"Tasks project {email}"},
        ).json()["data"]


def _context(client: TestClient, email: str | None = None) -> _Context:
    return _Context(client, email)


def test_task_lifecycle(client: TestClient) -> None:
    context = _context(client)
    task = context.client.post(
        "/api/v1/tasks",
        json={"project_id": context.project["id"], "title": "original", "priority": "high"},
    ).json()["data"]

    listed = context.client.get(f"/api/v1/tasks?project_id={context.project['id']}")
    assert listed.status_code == 200
    body = listed.json()
    assert body["meta"]["pagination"]["totalItems"] == 1

    updated = context.client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "in_progress", "priority": "low"},
    )
    assert updated.json()["data"]["status"] == "in_progress"

    removed = context.client.delete(f"/api/v1/tasks/{task['id']}")
    assert removed.status_code == 204


def test_task_invalid_priority_rejected(client: TestClient) -> None:
    context = _context(client)
    response = context.client.post(
        "/api/v1/tasks",
        json={"project_id": context.project["id"], "title": "x", "priority": "urgent"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_task_requires_existing_project(client: TestClient) -> None:
    context = _context(client)
    response = context.client.post(
        "/api/v1/tasks",
        json={"project_id": str(uuid.uuid4()), "title": "orphan"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_task_foreign_organization_404(client: TestClient) -> None:
    owner = _context(client)
    task = owner.client.post(
        "/api/v1/tasks",
        json={"project_id": owner.project["id"], "title": "original"},
    ).json()["data"]

    outsider = _context(client, "outsider@example.com")
    foreign_project = outsider.client.get(
        f"/api/v1/projects/{owner.project['id']}",
    )
    assert foreign_project.status_code == 404

    foreign_task = outsider.client.get(f"/api/v1/tasks/{task['id']}")
    assert foreign_task.status_code == 404
