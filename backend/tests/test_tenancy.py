
from fastapi.testclient import TestClient

from tests.auth_helper import DEFAULT_PASSWORD, AuthorizedClient, auth_headers


def _login(
    client: TestClient,
    email: str,
    password: str = DEFAULT_PASSWORD,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['data']['tokens']['access_token']}"}


def _register(
    client: TestClient,
    email: str,
    password: str = DEFAULT_PASSWORD,
) -> dict[str, str]:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "displayName": email.split("@")[0]},
    )
    return _login(client, email, password)


def _create_org(
    client: TestClient,
    headers: dict[str, str],
    name: str,
) -> dict:
    response = client.post(
        "/api/v1/organizations",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_employee_creates_task_but_cannot_delete_project(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner.mgr@example.com", create_org=True)
    project = client.post(
        "/api/v1/projects",
        json={"name": "Managed project"},
        headers=owner_headers,
    ).json()["data"]

    # create org member with employee role
    invited = client.post(
        f"/api/v1/organizations/{_get_org_id(client, owner_headers)}/users",
        json={"email": "org.employee@example.com", "displayName": "Employee"},
        headers=owner_headers,
    )
    employee_headers = _login(
        client,
        "org.employee@example.com",
        password=invited.json()["data"]["generated_password"],
    )
    employee = AuthorizedClient(client, employee_headers)

    task = employee.post(
        "/api/v1/tasks",
        json={"project_id": project["id"], "title": "employee-added"},
    )
    assert task.status_code == 201, task.text

    denied = employee.delete(f"/api/v1/projects/{project['id']}")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


def test_guest_reads_but_cannot_create_project(client: TestClient) -> None:
    owner_headers = auth_headers(client, "owner.guest@example.com", create_org=True)
    org_id = _get_org_id(client, owner_headers)
    invited = client.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": "reader@example.com", "displayName": "Reader"},
        headers=owner_headers,
    )
    user_id = invited.json()["data"]["id"]

    # downgrade to guest via SQL (role turnover via API is protected by perm check)
    _assign_role_via_sql("guest", user_id, org_id)

    guest_headers = _login(
        client,
        "reader@example.com",
        password=invited.json()["data"]["generated_password"],
    )
    guest = AuthorizedClient(client, guest_headers)

    listed = guest.get("/api/v1/projects")
    assert listed.status_code == 200

    created = guest.post("/api/v1/projects", json={"name": "ghost project"})
    assert created.status_code == 403
    assert created.json()["error"]["code"] == "PERMISSION_DENIED"


def test_platform_admin_sees_all_orgs(client: TestClient) -> None:
    owner1 = auth_headers(client, "org1@example.com", create_org=True, org_name="Org One")
    proj1 = client.post(
        "/api/v1/projects",
        json={"name": "org1 project"},
        headers=owner1,
    ).json()["data"]

    admin_headers = auth_headers(client, "root@example.com")
    _make_platform_admin_via_service(client, admin_headers)

    listed = client.get("/api/v1/projects?pageSize=100", headers=admin_headers).json()
    assert any(p["id"] == proj1["id"] for p in listed["data"])


def test_project_organization_stamp_matches_creator(client: TestClient) -> None:
    owned_headers = auth_headers(client, "stamp@example.com", create_org=True)
    created = client.post(
        "/api/v1/projects",
        json={"name": "stamp check"},
        headers=owned_headers,
    ).json()["data"]
    import sqlite3
    from pathlib import Path

    with sqlite3.connect(Path(__file__).parent / "_test.db") as db:
        org_id = db.execute(
            "SELECT organization_id FROM project WHERE id = ?",
            (created["id"].replace("-", ""),),
        ).fetchone()[0]
    assert org_id is not None
    orgs = client.get("/api/v1/organizations", headers=owned_headers).json()["data"]
    assert org_id == orgs[0]["id"].replace("-", "")


def _get_org_id(client: TestClient, headers: dict[str, str]) -> str:
    response = client.get("/api/v1/organizations", headers=headers).json()
    assert response["data"], "expected at least one organization"
    return response["data"][0]["id"]


def _assign_role_via_sql(role_name: str, user_id: str, org_id: str) -> None:
    import asyncio
    import uuid as uuid_mod
    from datetime import UTC, datetime

    from sqlalchemy import text

    from app.core.database import engine

    async def run() -> None:
        async with engine.begin() as conn:
            role_row = (
                await conn.execute(
                    text("SELECT id FROM role WHERE name = :name"),
                    {"name": role_name},
                )
            ).scalar_one()
            now = datetime.now(UTC).isoformat()
            existing = (
                await conn.execute(
                    text(
                        "SELECT id FROM user_role WHERE user_id = :uid AND role_id = :role"
                        " AND organization_id = :org",
                    ),
                    {
                        "uid": user_id.replace("-", ""),
                        "role": role_row,
                        "org": org_id.replace("-", ""),
                    },
                )
            ).first()
            if existing is None:
                await conn.execute(
                    text(
                        "INSERT INTO user_role (id, user_id, role_id, organization_id)"
                        " VALUES (:id, :uid, :role, :org)",
                    ),
                    {
                        "id": uuid_mod.uuid5(
                            uuid_mod.NAMESPACE_URL,
                            f"matrix-ur-{org_id}-{user_id}",
                        ).hex,
                        "uid": user_id.replace("-", ""),
                        "role": role_row,
                        "org": org_id.replace("-", ""),
                        "created_at": now,
                    },
                )

    asyncio.run(run())


def _make_platform_admin_via_service(client: TestClient, headers: dict[str, str]) -> None:
    import asyncio
    import uuid as uuid_mod
    from datetime import UTC, datetime

    from sqlalchemy import text

    from app.core.database import engine

    current_user = client.get("/api/v1/auth/me", headers=headers).json()["data"]
    user_id = current_user["id"]

    async def run() -> None:
        async with engine.begin() as conn:
            role_id = (
                await conn.execute(
                    text("SELECT id FROM role WHERE name = 'platform_admin'"),
                )
            ).scalar_one()
            existing = (
                await conn.execute(
                    text(
                        "SELECT id FROM user_role WHERE user_id = :uid AND role_id = :rid "
                        "AND organization_id IS NULL",
                    ),
                    {"uid": user_id.replace("-", ""), "rid": role_id},
                )
            ).first()
            if existing is None:
                now = datetime.now(UTC).isoformat()
                await conn.execute(
                    text(
                        "INSERT INTO user_role (id, user_id, role_id, organization_id,"
                        " created_at, updated_at)"
                        " VALUES (:id, :uid, :rid, NULL, :created_at, :updated_at)",
                    ),
                    {
                        "id": uuid_mod.uuid4().hex,
                        "uid": user_id.replace("-", ""),
                        "rid": role_id,
                        "created_at": now,
                        "updated_at": now,
                    },
                )

    asyncio.run(run())
