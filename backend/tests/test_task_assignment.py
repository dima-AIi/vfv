import uuid

from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers


def _owner_with_org(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"Org-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _invite_employee(
    client: TestClient,
    owned: AuthorizedClient,
    org_id: str,
    email: str,
) -> AuthorizedClient:
    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": email, "displayName": f"Emp {email.split('@')[0]}"},
    ).json()["data"]
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": invited["generated_password"]},
    ).json()["data"]["tokens"]["access_token"]
    return AuthorizedClient(client, {"Authorization": f"Bearer {login}"})


def _project(owned: AuthorizedClient) -> dict:
    return owned.post("/api/v1/projects", json={"name": f"P-{uuid.uuid4().hex[:6]}"}).json()["data"]


def test_assign_member_sets_assignee_name_and_due_date(client: TestClient) -> None:
    owned, org_id = _owner_with_org(client, "assign.owner@example.com")
    employee = _invite_employee(client, owned, org_id, "assign.emp@example.com")
    project = _project(owned)
    task = owned.post(
        "/api/v1/tasks",
        json={"project_id": project["id"], "title": "ship"},
    ).json()["data"]

    due = "2026-12-31"
    updated = owned.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"assignee_id": employee.get("/api/v1/auth/me").json()["data"]["id"], "due_date": due},
    )
    assert updated.status_code == 200
    data = updated.json()["data"]
    assert data["due_date"] == due
    assert data["assignee_name"] == "Emp assign.emp"


def test_assign_non_member_rejected(client: TestClient) -> None:
    owned, _org_id = _owner_with_org(client, "assign.o1@example.com")
    outsider, _ = _owner_with_org(client, "assign.o2@example.com")
    outsider_id = outsider.get("/api/v1/auth/me").json()["data"]["id"]
    project = _project(owned)
    task = owned.post(
        "/api/v1/tasks",
        json={"project_id": project["id"], "title": "t"},
    ).json()["data"]

    response = owned.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"assignee_id": outsider_id},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ASSIGNEE_NOT_IN_ORG"


def test_create_task_with_assignee_and_due_date(client: TestClient) -> None:
    owned, org_id = _owner_with_org(client, "assign.create@example.com")
    employee = _invite_employee(client, owned, org_id, "assign.create.emp@example.com")
    employee_id = employee.get("/api/v1/auth/me").json()["data"]["id"]
    project = _project(owned)

    task = owned.post(
        "/api/v1/tasks",
        json={
            "project_id": project["id"],
            "title": "with assignee",
            "assignee_id": employee_id,
            "due_date": "2026-06-15",
        },
    )
    assert task.status_code == 201
    data = task.json()["data"]
    assert data["assignee_id"] == employee_id
    assert data["assignee_name"] == "Emp assign.create.emp"
    assert data["due_date"] == "2026-06-15"


def test_task_detail_includes_comments(client: TestClient) -> None:
    owned, org_id = _owner_with_org(client, "assign.detail@example.com")
    employee = _invite_employee(client, owned, org_id, "assign.detail.emp@example.com")
    project = _project(owned)
    task = owned.post(
        "/api/v1/tasks",
        json={"project_id": project["id"], "title": "detail"},
    ).json()["data"]

    employee.post(f"/api/v1/tasks/{task['id']}/comments", json={"body": "hello"})
    detail = owned.get(f"/api/v1/tasks/{task['id']}").json()["data"]
    assert "comments" in detail
    assert len(detail["comments"]) == 1
    assert detail["comments"][0]["body"] == "hello"
    assert detail["comments"][0]["author_name"] == "Emp assign.detail.emp"
