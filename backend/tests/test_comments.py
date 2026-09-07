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


def _task(owned: AuthorizedClient) -> dict:
    project = owned.post(
        "/api/v1/projects",
        json={"name": f"P-{uuid.uuid4().hex[:6]}"},
    ).json()["data"]
    return owned.post(
        "/api/v1/tasks",
        json={"project_id": project["id"], "title": "t"},
    ).json()["data"]


def test_author_creates_lists_and_deletes_comment(client: TestClient) -> None:
    owned, org_id = _owner_with_org(client, "cmt.author@example.com")
    employee = _invite_employee(client, owned, org_id, "cmt.author.emp@example.com")
    task = _task(owned)

    created = employee.post(f"/api/v1/tasks/{task['id']}/comments", json={"body": "first"})
    assert created.status_code == 201
    comment_id = created.json()["data"]["id"]
    assert created.json()["data"]["body"] == "first"
    assert created.json()["data"]["author_name"] == "Emp cmt.author.emp"

    listed = employee.get(f"/api/v1/tasks/{task['id']}/comments")
    assert listed.status_code == 200
    assert listed.json()["meta"]["pagination"]["totalItems"] == 1
    assert listed.json()["data"][0]["author_name"] == "Emp cmt.author.emp"

    deleted = employee.delete(f"/api/v1/comments/{comment_id}")
    assert deleted.status_code == 204

    after = employee.get(f"/api/v1/tasks/{task['id']}/comments").json()["data"]
    assert after == []


def test_non_author_employee_cannot_delete(client: TestClient) -> None:
    owned, org_id = _owner_with_org(client, "cmt.na@example.com")
    author = _invite_employee(client, owned, org_id, "cmt.na.a@example.com")
    other = _invite_employee(client, owned, org_id, "cmt.na.b@example.com")
    task = _task(owned)

    comment_id = author.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"body": "mine"},
    ).json()["data"]["id"]

    forbidden = other.delete(f"/api/v1/comments/{comment_id}")
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "COMMENT_DELETE_FORBIDDEN"


def test_org_admin_deletes_other_comment(client: TestClient) -> None:
    owned, org_id = _owner_with_org(client, "cmt.admin@example.com")
    employee = _invite_employee(client, owned, org_id, "cmt.admin.emp@example.com")
    task = _task(owned)

    comment_id = employee.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"body": "by employee"},
    ).json()["data"]["id"]

    removed = owned.delete(f"/api/v1/comments/{comment_id}")
    assert removed.status_code == 204


def test_comment_in_foreign_organization_not_found(client: TestClient) -> None:
    owned, _org_id = _owner_with_org(client, "cmt.fg@example.com")
    task = _task(owned)
    comment_id = owned.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"body": "secret"},
    ).json()["data"]["id"]

    outsider, _ = _owner_with_org(client, "cmt.fg.outsider@example.com")
    response = outsider.delete(f"/api/v1/comments/{comment_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "COMMENT_NOT_FOUND"


def test_comment_requires_task_read_permission(client: TestClient) -> None:
    owned, _org_id = _owner_with_org(client, "cmt.perm@example.com")
    task = _task(owned)
    outsider, _ = _owner_with_org(client, "cmt.perm.outsider@example.com")
    response = outsider.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"body": "nope"},
    )
    assert response.status_code == 404
