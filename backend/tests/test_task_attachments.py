from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers


def _owner(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"AttOrg-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _task(owned: AuthorizedClient) -> str:
    pid = owned.post("/api/v1/projects", json={"name": "P"}).json()["data"]["id"]
    return owned.post(
        "/api/v1/tasks", json={"project_id": pid, "title": "T"}
    ).json()["data"]["id"]


def _upload(owned: AuthorizedClient, name: str = "doc.txt", data: bytes = b"payload") -> str:
    resp = owned.post("/api/v1/files", files={"file": (name, data, "text/plain")})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


def test_attachment_add_list_remove(client: TestClient) -> None:
    owned, _org = _owner(client, "att.crud@example.com")
    task_id = _task(owned)
    file_id = _upload(owned)

    added = owned.post(f"/api/v1/tasks/{task_id}/attachments", json={"fileId": file_id})
    assert added.status_code == 201, added.text
    att = added.json()["data"]
    assert att["file_id"] == file_id
    assert att["filename"] == "doc.txt"
    assert att["created_by_name"] == "att.crud"

    listed = owned.get(f"/api/v1/tasks/{task_id}/attachments").json()["data"]
    assert [a["id"] for a in listed] == [att["id"]]

    detail = owned.get(f"/api/v1/tasks/{task_id}").json()["data"]
    assert {a["id"] for a in detail["attachments"]} == {att["id"]}

    dup = owned.post(f"/api/v1/tasks/{task_id}/attachments", json={"fileId": file_id})
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "ATTACHMENT_EXISTS"

    removed = owned.delete(f"/api/v1/tasks/{task_id}/attachments/{att['id']}")
    assert removed.status_code == 204
    assert owned.get(f"/api/v1/tasks/{task_id}/attachments").json()["data"] == []


def test_attachment_foreign_file_404(client: TestClient) -> None:
    owned, _org = _owner(client, "att.xo.a@example.com")
    task_id = _task(owned)
    outsider, _ = _owner(client, "att.xo.b@example.com")
    foreign_file = _upload(outsider)
    response = owned.post(
        f"/api/v1/tasks/{task_id}/attachments", json={"fileId": foreign_file}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FILE_NOT_FOUND"


def test_attachment_delete_non_author_without_permission_403(client: TestClient) -> None:
    owned, org_id = _owner(client, "att.perm@example.com")
    task_id = _task(owned)
    file_id = _upload(owned)
    att_id = owned.post(
        f"/api/v1/tasks/{task_id}/attachments", json={"fileId": file_id}
    ).json()["data"]["id"]

    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": "att.perm.emp@example.com", "displayName": "Emp"},
    ).json()["data"]
    emp_login = client.post(
        "/api/v1/auth/login",
        json={"email": "att.perm.emp@example.com", "password": invited["generated_password"]},
    )
    emp_token = emp_login.json()["data"]["tokens"]["access_token"]
    employee = AuthorizedClient(client, {"Authorization": f"Bearer {emp_token}"})

    # employee has tasks.task.update (passes the endpoint gate) but is not the
    # creator and lacks tasks.task.delete
    response = employee.delete(f"/api/v1/tasks/{task_id}/attachments/{att_id}")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ATTACHMENT_DELETE_FORBIDDEN"
