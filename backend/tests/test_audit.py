import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.modules.rbac.seed import stable_id
from tests.auth_helper import AuthorizedClient, auth_headers

TEST_DB_PATH = Path(__file__).parent / "_test.db"


def _owner_org(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"AudOrg-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _make_platform_admin(client: TestClient) -> dict:
    email = f"pa-{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strong-password-123", "displayName": "Root"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-password-123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["data"]["tokens"]["access_token"]
    now = datetime.now(UTC).isoformat()
    with sqlite3.connect(TEST_DB_PATH) as connection:
        user_id = connection.execute(
            "SELECT id FROM user WHERE email = ?", (email,)
        ).fetchone()[0]
        connection.execute(
            "INSERT INTO user_role (id, user_id, role_id, organization_id, created_at, updated_at)"
            " VALUES (?, ?, ?, NULL, ?, ?)",
            (uuid.uuid4().hex, user_id, stable_id("role", "platform_admin").hex, now, now),
        )
        connection.commit()
    return {"Authorization": f"Bearer {token}"}


def test_audit_org_isolation(client: TestClient) -> None:
    a, a_org = _owner_org(client, "aud.a@example.com")
    b, _b_org = _owner_org(client, "aud.b@example.com")

    a_rows = a.get("/api/v1/audit").json()["data"]
    assert a_rows, "org_admin should see own-org audit rows"
    assert {r["organization_id"] for r in a_rows} == {a_org}
    assert all(r["action_type"] != "USER_REGISTERED" for r in a_rows)


def test_audit_filters(client: TestClient) -> None:
    a, _ = _owner_org(client, "aud.filter@example.com")
    rows = a.get("/api/v1/audit", params={"action_type": "ORGANIZATION_CREATED"}).json()["data"]
    assert rows
    assert all(r["action_type"] == "ORGANIZATION_CREATED" for r in rows)


def test_audit_platform_admin_sees_null_org(client: TestClient) -> None:
    _make_platform_admin(client)
    pa = _make_platform_admin(client)
    rows = client.get("/api/v1/audit", params={"pageSize": 100}, headers=pa).json()["data"]
    assert any(r["organization_id"] is None for r in rows)
