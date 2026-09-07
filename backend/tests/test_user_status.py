import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.modules.rbac.seed import stable_id
from tests.auth_helper import AuthorizedClient, auth_headers

TEST_DB_PATH = Path(__file__).parent / "_test.db"


def _owner_org(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"StOrg-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _invite(
    client: TestClient, owned: AuthorizedClient, org_id: str, email: str
) -> tuple[str, str]:
    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": email, "displayName": "Emp"},
    ).json()["data"]
    return invited["id"], invited["generated_password"]


def _login(client: TestClient, email: str, password: str) -> int:
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).status_code


def test_block_and_unblock_member(client: TestClient) -> None:
    owned, org_id = _owner_org(client, "st.block@example.com")
    emp_id, emp_pass = _invite(client, owned, org_id, "st.block.emp@example.com")
    email = "st.block.emp@example.com"

    blocked = owned.patch(
        f"/api/v1/organizations/{org_id}/users/{emp_id}/status",
        json={"status": "blocked"},
    )
    assert blocked.status_code == 200
    assert blocked.json()["data"]["status"] == "blocked"
    assert _login(client, email, emp_pass) == 403

    unblocked = owned.patch(
        f"/api/v1/organizations/{org_id}/users/{emp_id}/status",
        json={"status": "active"},
    )
    assert unblocked.status_code == 200
    assert _login(client, email, emp_pass) == 200


def test_cannot_block_self(client: TestClient) -> None:
    owned, org_id = _owner_org(client, "st.self@example.com")
    me = owned.get("/api/v1/auth/me").json()["data"]
    response = owned.patch(
        f"/api/v1/organizations/{org_id}/users/{me['id']}/status",
        json={"status": "blocked"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CANNOT_BLOCK_SELF"


def test_cannot_block_platform_admin(client: TestClient) -> None:
    owned, org_id = _owner_org(client, "st.pa@example.com")
    pa_email = f"pa-{uuid.uuid4().hex[:6]}@example.com"
    pa_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    with sqlite3.connect(TEST_DB_PATH) as connection:
        connection.execute(
            "INSERT INTO user (id, email, display_name, status, organization_id, version,"
            " created_at, updated_at) VALUES (?, ?, 'PA', 'active', ?, 1, ?, ?)",
            (pa_id.replace("-", ""), pa_email, org_id.replace("-", ""), now, now),
        )
        connection.execute(
            "INSERT INTO user_role (id, user_id, role_id, organization_id, created_at, updated_at)"
            " VALUES (?, ?, ?, NULL, ?, ?)",
            (
                uuid.uuid4().hex,
                pa_id.replace("-", ""),
                stable_id("role", "platform_admin").hex,
                now,
                now,
            ),
        )
        connection.commit()
    response = owned.patch(
        f"/api/v1/organizations/{org_id}/users/{pa_id}/status",
        json={"status": "blocked"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CANNOT_BLOCK_PLATFORM_ADMIN"


def test_status_requires_permission(client: TestClient) -> None:
    owned, org_id = _owner_org(client, "st.perm@example.com")
    emp_id, _ = _invite(client, owned, org_id, "st.perm.emp@example.com")
    outsider, _ = _owner_org(client, "st.perm.out@example.com")
    response = outsider.patch(
        f"/api/v1/organizations/{org_id}/users/{emp_id}/status",
        json={"status": "blocked"},
    )
    assert response.status_code == 403
