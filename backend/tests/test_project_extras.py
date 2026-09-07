from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers


def _owner(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"ProjOrg-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _invite(client: TestClient, owned: AuthorizedClient, org_id: str, email: str) -> str:
    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": email, "displayName": "Emp"},
    ).json()["data"]
    return invited["id"]


def test_project_due_date_roundtrip(client: TestClient) -> None:
    owned, _org = _owner(client, "proj.due@example.com")
    created = owned.post(
        "/api/v1/projects",
        json={"name": "Q3", "due_date": "2026-12-31"},
    )
    assert created.status_code == 201, created.text
    pid = created.json()["data"]["id"]
    assert created.json()["data"]["due_date"] == "2026-12-31"

    patched = owned.patch(f"/api/v1/projects/{pid}", json={"due_date": "2027-01-15"})
    assert patched.json()["data"]["due_date"] == "2027-01-15"

    cleared = owned.patch(f"/api/v1/projects/{pid}", json={"due_date": None})
    assert cleared.json()["data"]["due_date"] is None


def test_project_invalid_due_date_422(client: TestClient) -> None:
    owned, _org = _owner(client, "proj.baddue@example.com")
    response = owned.post(
        "/api/v1/projects",
        json={"name": "X", "due_date": "not-a-date"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_project_members_add_list_remove(client: TestClient) -> None:
    owned, org_id = _owner(client, "proj.mem@example.com")
    user_id = _invite(client, owned, org_id, "proj.mem.emp@example.com")
    pid = owned.post("/api/v1/projects", json={"name": "P"}).json()["data"]["id"]

    added = owned.post(f"/api/v1/projects/{pid}/members", json={"userId": user_id})
    assert added.status_code == 201, added.text
    assert added.json()["data"]["id"] == user_id

    members = owned.get(f"/api/v1/projects/{pid}/members").json()["data"]
    assert {m["id"] for m in members} == {user_id}

    dup = owned.post(f"/api/v1/projects/{pid}/members", json={"userId": user_id})
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "MEMBER_EXISTS"

    removed = owned.delete(f"/api/v1/projects/{pid}/members/{user_id}")
    assert removed.status_code == 204
    assert owned.get(f"/api/v1/projects/{pid}/members").json()["data"] == []


def test_project_member_foreign_user_404(client: TestClient) -> None:
    owned, _org = _owner(client, "proj.memxo.a@example.com")
    outsider, outsider_org = _owner(client, "proj.memxo.b@example.com")
    outsider_user = _invite(client, outsider, outsider_org, "proj.memxo.emp@example.com")
    pid = owned.post("/api/v1/projects", json={"name": "P"}).json()["data"]["id"]
    response = owned.post(f"/api/v1/projects/{pid}/members", json={"userId": outsider_user})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "USER_NOT_FOUND"


def test_project_member_requires_permission(client: TestClient) -> None:
    owned, org_id = _owner(client, "proj.memperm@example.com")
    pid = owned.post("/api/v1/projects", json={"name": "P"}).json()["data"]["id"]

    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": "proj.memperm.emp@example.com", "displayName": "Emp"},
    ).json()["data"]
    emp_login = client.post(
        "/api/v1/auth/login",
        json={"email": "proj.memperm.emp@example.com", "password": invited["generated_password"]},
    )
    assert emp_login.status_code == 200
    emp_token = emp_login.json()["data"]["tokens"]["access_token"]
    employee = AuthorizedClient(client, {"Authorization": f"Bearer {emp_token}"})

    response = employee.post(
        f"/api/v1/projects/{pid}/members", json={"userId": invited["id"]}
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
