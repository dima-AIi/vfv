from typing import Any

from fastapi.testclient import TestClient

from app.core.events import subscribe, unsubscribe
from tests.auth_helper import auth_headers

REQUEST_ID = "corr-fixed-42"


def test_event_published_in_request_carries_request_id_as_correlation_id(
    client: TestClient,
) -> None:
    headers = auth_headers(client, "corr.id@example.com", create_org=True, org_name="Org-CorrId")
    project = client.post(
        "/api/v1/projects",
        json={"name": "Corr Project"},
        headers=headers,
    ).json()["data"]

    captured: list[dict[str, Any]] = []

    async def capture(event: dict[str, Any]) -> None:
        captured.append(event)

    subscribe("TaskCreated", capture)
    try:
        response = client.post(
            "/api/v1/tasks",
            json={"project_id": project["id"], "title": "corr task"},
            headers={**headers, "X-Request-ID": REQUEST_ID},
        )
        assert response.status_code == 201, response.text
        assert response.headers["X-Request-ID"] == REQUEST_ID
    finally:
        unsubscribe("TaskCreated", capture)

    event = next(e for e in captured if e["eventType"] == "TaskCreated")
    assert event["metadata"]["correlationId"] == REQUEST_ID
