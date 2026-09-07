import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.modules.tasks import events as task_events
from tests.auth_helper import AuthorizedClient, auth_headers


def _owner_with_org(client: TestClient, email: str) -> AuthorizedClient:
    headers = auth_headers(client, email, create_org=True, org_name=f"Org-{email}")
    return AuthorizedClient(client, headers)


def _task(owned: AuthorizedClient) -> dict:
    project = owned.post(
        "/api/v1/projects",
        json={"name": f"P-{uuid.uuid4().hex[:6]}"},
    ).json()["data"]
    return owned.post(
        "/api/v1/tasks",
        json={"project_id": project["id"], "title": "t"},
    ).json()["data"]


def test_task_events_publish_correct_names_and_payload(
    client: TestClient,
    monkeypatch,
) -> None:
    captured: list[dict[str, Any]] = []

    async def capture(event: dict[str, Any]) -> None:
        captured.append(event)

    monkeypatch.setattr(task_events, "publish_event", capture)

    owned = _owner_with_org(client, "evt.owner@example.com")
    task = _task(owned)

    created = next(e for e in captured if e["eventType"] == "TaskCreated")
    assert created["payload"]["taskId"] == task["id"]
    assert created["payload"]["status"] == "open"
    assert created["version"] == "1.0"
    assert created["organizationId"] is not None
    assert created["aggregateId"] == task["id"]
    assert created["eventId"].startswith("evt_")
    assert created["metadata"]["sourceModule"] == "Tasks"

    owned.patch(f"/api/v1/tasks/{task['id']}", json={"status": "done"})
    completed = next(e for e in captured if e["eventType"] == "TaskCompleted")
    assert completed["payload"]["taskId"] == task["id"]
    assert "completedAt" in completed["payload"]


def test_task_assigned_event_on_assignment(
    client: TestClient,
    monkeypatch,
) -> None:
    captured: list[dict[str, Any]] = []

    async def capture(event: dict[str, Any]) -> None:
        captured.append(event)

    monkeypatch.setattr(task_events, "publish_event", capture)

    owned = _owner_with_org(client, "evt.assign@example.com")
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": "evt.assign.emp@example.com", "displayName": "Emp"},
    ).json()["data"]
    task = _task(owned)

    owned.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"assignee_id": invited["id"]},
    )
    assigned = next(e for e in captured if e["eventType"] == "TaskAssigned")
    assert assigned["payload"]["taskId"] == task["id"]
    assert assigned["payload"]["assigneeId"] == invited["id"]
    assert assigned["payload"]["taskTitle"] == task["title"]
    assert assigned["payload"]["projectId"] == task["project_id"]
