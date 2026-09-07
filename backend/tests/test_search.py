import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.modules.rbac.seed import stable_id
from tests.auth_helper import AuthorizedClient, auth_headers

TEST_DB_PATH = Path(__file__).parent / "_test.db"


def _owner(client: TestClient, email: str) -> AuthorizedClient:
    headers = auth_headers(client, email, create_org=True, org_name=f"SearchOrg-{email}")
    return AuthorizedClient(client, headers)


def _make_guest(
    client: TestClient, owned: AuthorizedClient, email: str, display: str
) -> AuthorizedClient:
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": email, "displayName": display},
    ).json()["data"]
    user_id = invited["id"]
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": invited["generated_password"]},
    ).json()["data"]["tokens"]["access_token"]
    now = datetime.now(UTC).isoformat()
    with sqlite3.connect(TEST_DB_PATH) as connection:
        connection.execute(
            "DELETE FROM user_role WHERE user_id = ? AND organization_id = ?",
            (user_id.replace("-", ""), org_id.replace("-", "")),
        )
        connection.execute(
            "INSERT INTO user_role (id, user_id, role_id, organization_id, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                uuid.uuid4().hex,
                user_id.replace("-", ""),
                stable_id("role", "guest").hex,
                org_id.replace("-", ""),
                now,
                now,
            ),
        )
        connection.commit()
    return AuthorizedClient(client, {"Authorization": f"Bearer {login}"})


def test_search_cyrillic_case_insensitive(client: TestClient) -> None:
    owned = _owner(client, "search.cy@example.com")
    owned.post("/api/v1/projects", json={"name": "Отчёт Q3", "description": "квартальный"})

    upper = owned.get("/api/v1/search", params={"q": "ОТЧЁТ"}).json()
    assert upper["meta"]["counts"]["projects"] >= 1
    assert any(p["name"] == "Отчёт Q3" for p in upper["data"]["projects"])

    lower = owned.get("/api/v1/search", params={"q": "отч"}).json()
    assert any(p["name"] == "Отчёт Q3" for p in lower["data"]["projects"])


def test_search_escapes_like_wildcards(client: TestClient) -> None:
    owned = _owner(client, "search.escape@example.com")
    owned.post("/api/v1/projects", json={"name": "План 100%"})
    owned.post("/api/v1/projects", json={"name": "План 1000"})

    results = owned.get("/api/v1/search", params={"q": "100%"}).json()["data"]["projects"]
    names = {p["name"] for p in results}
    assert "План 100%" in names
    assert "План 1000" not in names


def test_search_cross_org_isolation(client: TestClient) -> None:
    owned = _owner(client, "search.a@example.com")
    owned.post("/api/v1/projects", json={"name": "Секретный проект"})
    outsider = _owner(client, "search.b@example.com")
    results = outsider.get("/api/v1/search", params={"q": "Секретный"}).json()
    assert results["meta"]["counts"]["projects"] == 0
    assert results["data"]["projects"] == []


def test_search_short_query_rejected(client: TestClient) -> None:
    owned = _owner(client, "search.short@example.com")
    response = owned.get("/api/v1/search", params={"q": "а"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_search_empty_result(client: TestClient) -> None:
    owned = _owner(client, "search.empty@example.com")
    body = owned.get("/api/v1/search", params={"q": "zzzz-нет-такого"}).json()
    assert body["data"] == {
        "projects": [],
        "tasks": [],
        "documents": [],
        "files": [],
        "customers": [],
    }
    assert body["meta"]["counts"] == {
        "projects": 0,
        "tasks": 0,
        "documents": 0,
        "files": 0,
        "customers": 0,
    }


def test_search_finds_task_document_file(client: TestClient) -> None:
    owned = _owner(client, "search.types@example.com")
    project = owned.post("/api/v1/projects", json={"name": "Alpha"}).json()["data"]
    owned.post(
        "/api/v1/tasks",
        json={"project_id": project["id"], "title": "Alpha задача"},
    )
    owned.post(
        "/api/v1/documents",
        json={"title": "Alpha док", "relative_path": "99_AI/03_GLOSSARY.md"},
    )
    owned.post(
        "/api/v1/files",
        files={"file": ("alpha.txt", b"data", "text/plain")},
    )
    body = owned.get("/api/v1/search", params={"q": "Alpha"}).json()
    assert body["meta"]["counts"]["projects"] >= 1
    assert body["meta"]["counts"]["tasks"] >= 1
    assert body["meta"]["counts"]["documents"] >= 1
    assert body["meta"]["counts"]["files"] >= 1


def test_guest_can_search(client: TestClient) -> None:
    owned = _owner(client, "search.g@example.com")
    owned.post("/api/v1/projects", json={"name": "Видимый гостю"})
    guest = _make_guest(client, owned, "search.guest@example.com", "Guest")
    response = guest.get("/api/v1/search", params={"q": "Видимый"})
    assert response.status_code == 200
    assert response.json()["meta"]["counts"]["projects"] >= 1


def test_search_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/search", params={"q": "что-угодно"})
    assert response.status_code == 401
