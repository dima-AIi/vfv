import uuid

from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers


def _owner(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"NotifOrg-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _invite_employee(
    client: TestClient, owned: AuthorizedClient, org_id: str, email: str
) -> AuthorizedClient:
    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": email, "displayName": f"Emp {email.split('@')[0]}"},
    ).json()["data"]
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": invited["generated_password"]},
    ).json()["data"]["tokens"]["access_token"]
    return AuthorizedClient(client, {"Authorization": f"Bearer {login}"}), invited["id"]


def _project(owned: AuthorizedClient) -> str:
    return owned.post(
        "/api/v1/projects", json={"name": f"P-{uuid.uuid4().hex[:6]}"}
    ).json()["data"]["id"]


def _unread_count(client: AuthorizedClient) -> int:
    body = client.get("/api/v1/notifications?unread=true").json()
    return int(body["meta"]["pagination"]["totalItems"])


def test_assign_task_notifies_assignee(client: TestClient) -> None:
    owned, org_id = _owner(client, "notif.assign@example.com")
    employee, employee_id = _invite_employee(
        client, owned, org_id, "notif.assign.emp@example.com"
    )
    project_id = _project(owned)
    task = owned.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Prepare release"},
    ).json()["data"]

    assigned = owned.patch(f"/api/v1/tasks/{task['id']}", json={"assignee_id": employee_id})
    assert assigned.status_code == 200

    unread = employee.get("/api/v1/notifications?unread=true").json()
    assert unread["meta"]["pagination"]["totalItems"] == 1
    item = unread["data"][0]
    assert item["title"] == "Вам назначена задача"
    assert "Prepare release" in item["body"]
    assert item["read_at"] is None


def test_comment_notifies_assignee_not_author(client: TestClient) -> None:
    owned, org_id = _owner(client, "notif.comment@example.com")
    employee, employee_id = _invite_employee(
        client, owned, org_id, "notif.comment.emp@example.com"
    )
    project_id = _project(owned)
    task = owned.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Review PR", "assignee_id": employee_id},
    ).json()["data"]

    # employee already has 1 assignment notification
    before = employee.get("/api/v1/notifications").json()["meta"]["pagination"]["totalItems"]

    # author (owner, not assignee) comments -> assignee notified
    owned.post(f"/api/v1/tasks/{task['id']}/comments", json={"body": "please update"})
    after_author = employee.get("/api/v1/notifications").json()["meta"]["pagination"]["totalItems"]
    assert after_author == before + 1
    latest = employee.get("/api/v1/notifications").json()["data"][0]
    assert latest["title"] == "Новый комментарий к задаче"
    assert "please update" in latest["body"]

    # assignee comments their own task -> no new notification for themselves
    employee.post(f"/api/v1/tasks/{task['id']}/comments", json={"body": "on it"})
    after_self = employee.get("/api/v1/notifications").json()["meta"]["pagination"]["totalItems"]
    assert after_self == after_author


def test_read_and_read_all(client: TestClient) -> None:
    owned, org_id = _owner(client, "notif.read@example.com")
    employee, employee_id = _invite_employee(
        client, owned, org_id, "notif.read.emp@example.com"
    )
    project_id = _project(owned)
    task = owned.post(
        "/api/v1/tasks", json={"project_id": project_id, "title": "T"}
    ).json()["data"]
    owned.patch(f"/api/v1/tasks/{task['id']}", json={"assignee_id": employee_id})

    items = employee.get("/api/v1/notifications").json()["data"]
    notification_id = items[0]["id"]

    marked = employee.post(f"/api/v1/notifications/{notification_id}/read")
    assert marked.status_code == 204
    assert _unread_count(employee) == 0

    all_read = employee.post("/api/v1/notifications/read-all")
    assert all_read.status_code == 200
    assert all_read.json()["data"]["updated"] == 0


def test_read_all_resets_unread(client: TestClient) -> None:
    owned, org_id = _owner(client, "notif.readall@example.com")
    employee, employee_id = _invite_employee(
        client, owned, org_id, "notif.readall.emp@example.com"
    )
    project_id = _project(owned)
    for title in ("A", "B"):
        task = owned.post(
            "/api/v1/tasks", json={"project_id": project_id, "title": title}
        ).json()["data"]
        owned.patch(f"/api/v1/tasks/{task['id']}", json={"assignee_id": employee_id})

    assert _unread_count(employee) == 2
    result = employee.post("/api/v1/notifications/read-all")
    assert result.json()["data"]["updated"] == 2
    assert _unread_count(employee) == 0


def test_foreign_notification_not_found(client: TestClient) -> None:
    owned, org_id = _owner(client, "notif.fgn@example.com")
    employee, employee_id = _invite_employee(
        client, owned, org_id, "notif.fgn.emp@example.com"
    )
    project_id = _project(owned)
    task = owned.post(
        "/api/v1/tasks", json={"project_id": project_id, "title": "T"}
    ).json()["data"]
    owned.patch(f"/api/v1/tasks/{task['id']}", json={"assignee_id": employee_id})
    notification_id = employee.get("/api/v1/notifications").json()["data"][0]["id"]

    outsider, _ = _owner(client, "notif.fgn.outsider@example.com")
    response = outsider.post(f"/api/v1/notifications/{notification_id}/read")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOTIFICATION_NOT_FOUND"


def test_notifications_require_auth(client: TestClient) -> None:
    response = client.get("/api/v1/notifications")
    assert response.status_code == 401
