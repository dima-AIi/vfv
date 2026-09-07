import uuid

from fastapi.testclient import TestClient

from tests.auth_helper import DEFAULT_PASSWORD, AuthorizedClient, auth_headers


def _owned(
    client: TestClient,
    email: str = "owner.projects@example.com",
) -> AuthorizedClient:
    headers = auth_headers(
        client,
        email,
        create_org=True,
        org_name=f"Org-{email}",
    )
    return AuthorizedClient(client, headers)


def _create(owned: AuthorizedClient, name: str = "Smoke Project") -> dict:
    response = owned.post(
        "/api/v1/projects",
        json={"name": name, "description": "created by smoke test"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_project_crud_flow(client: TestClient) -> None:
    owned = _owned(client)
    project = _create(owned)
    project_id = project["id"]

    listing = owned.get("/api/v1/projects")
    assert listing.status_code == 200
    body = listing.json()
    assert set(body.keys()) == {"data", "meta", "links"}
    assert any(p["id"] == project_id for p in body["data"])

    fetched = owned.get(f"/api/v1/projects/{project_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["name"] == "Smoke Project"

    updated = owned.patch(
        f"/api/v1/projects/{project_id}",
        json={"description": "updated", "status": "archived"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "archived"

    deleted = owned.delete(f"/api/v1/projects/{project_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert owned.get(f"/api/v1/projects/{project_id}").status_code == 404


def test_project_invalid_status_rejected(client: TestClient) -> None:
    owned = _owned(client)
    project = _create(owned, "Invalid Status Project")
    response = owned.patch(
        f"/api/v1/projects/{project['id']}",
        json={"status": "bogus"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_project_not_found_error_envelope(client: TestClient) -> None:
    owned = _owned(client)
    response = owned.get(f"/api/v1/projects/{uuid.uuid4()}")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "PROJECT_NOT_FOUND"
    assert "requestId" in error and "timestamp" in error


def test_create_project_validation(client: TestClient) -> None:
    owned = _owned(client)
    response = owned.post("/api/v1/projects", json={"name": ""})
    assert response.status_code == 422


def test_projects_require_auth(client: TestClient) -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_user_without_org_gets_403_no_organization(client: TestClient) -> None:
    headers = auth_headers(client, "no-org@example.com", DEFAULT_PASSWORD)
    owned = AuthorizedClient(client, headers)
    response = owned.get("/api/v1/projects")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "NO_ORGANIZATION"
