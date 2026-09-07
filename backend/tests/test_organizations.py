import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.modules.rbac.seed import stable_id

ADMIN_EMAIL = "owner.acme@example.com"
ADMIN_PASSWORD = "owner-password-1"
TEST_DB_PATH = Path(__file__).parent / "_test.db"


def _register_and_login(
    client: TestClient,
    email: str,
    password: str = "some-password-1",
    display_name: str = "User",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "displayName": display_name},
    )
    assert response.status_code == 201, response.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return login.json()["data"]["tokens"]


def _auth(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create_org(client: TestClient, tokens: dict, name: str = "ACME Inc") -> dict:
    response = client.post(
        "/api/v1/organizations",
        json={"name": name, "description": "demo org"},
        headers=_auth(tokens),
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_create_organization_makes_creator_org_admin(client: TestClient) -> None:
    tokens = _register_and_login(client, ADMIN_EMAIL, ADMIN_PASSWORD, "Owner")
    organization = _create_org(client, tokens)

    me = client.get("/api/v1/auth/me", headers=_auth(tokens)).json()["data"]
    assert me["organization"]["id"] == organization["id"]
    assert me["organization"]["name"] == organization["name"]
    assert "org_admin" in me["roles"]

    members = client.get(
        f"/api/v1/organizations/{organization['id']}/users",
        headers=_auth(tokens),
    )
    assert members.status_code == 200
    member_ids = [m["id"] for m in members.json()["data"]]
    assert len(member_ids) == 1


def test_duplicate_organization_name_409(client: TestClient) -> None:
    tokens = _register_and_login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    _create_org(client, tokens, "Unique Name Org")

    second = client.post(
        "/api/v1/organizations",
        json={"name": "Unique Name Org"},
        headers=_auth(tokens),
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "ORGANIZATION_NAME_EXISTS"

    other_tokens = _register_and_login(client, "other.person@example.com")
    foreign = client.post(
        "/api/v1/organizations",
        json={"name": "Unique Name Org"},
        headers=_auth(other_tokens),
    )
    assert foreign.status_code == 409


def test_non_member_gets_404_on_foreign_organization(client: TestClient) -> None:
    owner_tokens = _register_and_login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    organization = _create_org(client, owner_tokens)

    outsider = _register_and_login(client, "outsider@example.com")
    response = client.get(
        f"/api/v1/organizations/{organization['id']}",
        headers=_auth(outsider),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ORGANIZATION_NOT_FOUND"

    listed = client.get("/api/v1/organizations", headers=_auth(outsider))
    assert listed.json()["data"] == []


def test_invite_flow_requires_admin_and_returns_password_once(client: TestClient) -> None:
    owner_tokens = _register_and_login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    organization = _create_org(client, owner_tokens)

    invitee_tokens = _register_and_login(client, "plain.member@example.com")

    denied = client.post(
        f"/api/v1/organizations/{organization['id']}/users",
        json={"email": "new.hire@example.com", "displayName": "New Hire"},
        headers=_auth(invitee_tokens),
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    invited = client.post(
        f"/api/v1/organizations/{organization['id']}/users",
        json={"email": "new.hire@example.com", "displayName": "New Hire"},
        headers=_auth(owner_tokens),
    )
    assert invited.status_code == 201
    body = invited.json()["data"]
    generated = body["generated_password"]
    assert generated is not None and len(generated) >= 12

    hire_login = client.post(
        "/api/v1/auth/login",
        json={"email": "new.hire@example.com", "password": generated},
    )
    assert hire_login.status_code == 200

    repeat_login_with_same_generated = client.post(
        "/api/v1/auth/login",
        json={"email": "new.hire@example.com", "password": generated},
    )
    assert repeat_login_with_same_generated.status_code == 200

    hire_me = client.get("/api/v1/auth/me", headers=_auth(hire_login.json()["data"]["tokens"]))
    hire_data = hire_me.json()["data"]
    assert hire_data["organization"]["id"] == organization["id"]
    assert "employee" in hire_data["roles"]

    second_admin_view = client.get(
        f"/api/v1/organizations/{organization['id']}/users",
        headers=_auth(owner_tokens),
    )
    emails = [m["email"] for m in second_admin_view.json()["data"]]
    assert "new.hire@example.com" in emails


def test_role_assignment_rules(client: TestClient) -> None:
    owner_tokens = _register_and_login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    organization = _create_org(client, owner_tokens)

    invited = client.post(
        f"/api/v1/organizations/{organization['id']}/users",
        json={
            "email": "member.one@example.com",
            "displayName": "Member One",
            "password": "member-password-1",
        },
        headers=_auth(owner_tokens),
    ).json()["data"]
    target_id = invited["id"]

    forbidden_roles = ("guest", "platform_admin")
    for role in forbidden_roles:
        response = client.patch(
            f"/api/v1/organizations/{organization['id']}/users/{target_id}/role",
            json={"role": role},
            headers=_auth(owner_tokens),
        )
        assert response.status_code == 422, role
        assert response.json()["error"]["code"] == "ROLE_ASSIGNMENT_FORBIDDEN", role

    unknown = client.patch(
        f"/api/v1/organizations/{organization['id']}/users/{target_id}/role",
        json={"role": "wizard"},
        headers=_auth(owner_tokens),
    )
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "ROLE_NOT_FOUND"

    promote = client.patch(
        f"/api/v1/organizations/{organization['id']}/users/{target_id}/role",
        json={"role": "manager"},
        headers=_auth(owner_tokens),
    )
    assert promote.status_code == 200

    me = client.get(
        "/api/v1/auth/me",
        headers=_auth(_login_user(client, "member.one@example.com", "member-password-1")),
    ).json()["data"]
    assert "manager" in me["roles"]
    assert "employee" not in me["roles"]

    outsider_tokens = _register_and_login(client, "random.guy@example.com")
    denied = client.patch(
        f"/api/v1/organizations/{organization['id']}/users/{target_id}/role",
        json={"role": "manager"},
        headers=_auth(outsider_tokens),
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


def test_seed_contains_roles_permissions_and_matrix(client: TestClient) -> None:
    import asyncio

    from sqlalchemy import text

    from app.core.database import engine

    async def fetch() -> tuple[set[str], set[str], int]:
        async with engine.connect() as connection:
            roles_result = await connection.execute(text("SELECT name FROM role"))
            permissions_result = await connection.execute(text("SELECT code FROM permission"))
            links_result = await connection.execute(
                text("SELECT COUNT(*) FROM role_permission"),
            )
            return (
                {row[0] for row in roles_result.all()},
                {row[0] for row in permissions_result.all()},
                int(links_result.scalar_one()),
            )

    roles, permissions, link_count = asyncio.run(fetch())
    assert roles >= {
        "platform_admin",
        "org_admin",
        "manager",
        "employee",
        "guest",
    }
    for code in (
        "organization.organization.manage",
        "identity.user.manage",
        "projects.project.create",
        "tasks.task.delete",
        "documents.document.read",
        "ai.action.run",
        "dashboard.dashboard.read",
        "audit.record.read",
        "comments.comment.delete",
        "files.file.upload",
        "files.file.read",
        "files.file.delete",
        "search.search.read",
        "crm.customer.create",
        "crm.customer.read",
        "crm.customer.update",
        "crm.customer.delete",
        "settings.platform.manage",
        "settings.organization.manage",
    ):
        assert code in permissions, code
    expected_links = 28 + 27 + 19 + 12 + 6
    assert link_count == expected_links


def test_check_user_permission_matrix(client: TestClient) -> None:
    import asyncio

    from app.core.database import session_factory
    from app.modules.rbac.service import RbacService

    checks_by_role: dict[str, tuple[tuple[str, bool], ...]] = {
        "platform_admin": (
            ("audit.record.read", True),
            ("identity.user.manage", True),
            ("projects.project.delete", True),
        ),
        "org_admin": (
            ("identity.user.manage", True),
            ("audit.record.read", True),
            ("settings.organization.manage", True),
            ("settings.platform.manage", False),
        ),
        "manager": (
            ("projects.project.create", True),
            ("projects.project.delete", False),
        ),
        "employee": (
            ("tasks.task.update", True),
            ("projects.project.create", False),
        ),
        "guest": (
            ("documents.document.read", True),
            ("ai.action.run", False),
        ),
    }

    async def probe() -> dict[str, list[tuple[str, bool, bool]]]:
        from app.core.models import utcnow
        from app.modules.identity.models import User
        from app.modules.rbac.models import UserRole
        from app.modules.rbac.seed import stable_id

        results: dict[str, list[tuple[str, bool, bool]]] = {}

        async with session_factory() as session:
            service = RbacService(session)
            for index, (role_name, expectations) in enumerate(checks_by_role.items()):
                user_id = uuid.uuid5(uuid.NAMESPACE_URL, f"matrix-user-{role_name}")
                session.add(
                    User(
                        id=user_id,
                        email=f"matrix-{role_name}@example.com",
                        display_name=f"Matrix {role_name}",
                        status="active",
                        created_at=utcnow(),
                        updated_at=utcnow(),
                    ),
                )
                await session.flush()
                session.add(
                    UserRole(
                        id=uuid.uuid5(uuid.NAMESPACE_URL, f"matrix-ur-{index}-{role_name}"),
                        user_id=user_id,
                        role_id=stable_id("role", role_name),
                        organization_id=None,
                    ),
                )
                await session.commit()

                role_results: list[tuple[str, bool, bool]] = []
                for code, expected in expectations:
                    held = await service.check_user_permission(user_id, code, None)
                    role_results.append((code, expected, held))
                results[role_name] = role_results
        return results

    matrix = asyncio.run(probe())
    for role_name, entries in matrix.items():
        for code, expected, actual in entries:
            assert actual is expected, (role_name, code, expected, actual)


def _login_user(client: TestClient, email: str, password: str = "some-password-1") -> dict:
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["data"]["tokens"]


def test_public_members_endpoint_access(client: TestClient) -> None:
    owner_tokens = _register_and_login(client, "pubmembers.owner@example.com", display_name="Owner")
    organization = _create_org(client, owner_tokens, name="PubMembers Org")
    org_id = organization["id"]

    invited = client.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": "pubmembers.emp@example.com", "displayName": "Pub Emp"},
        headers=_auth(owner_tokens),
    ).json()["data"]
    emp_tokens = _login_user(client, "pubmembers.emp@example.com", invited["generated_password"])

    as_employee = client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers=_auth(emp_tokens),
    )
    assert as_employee.status_code == 200
    body = as_employee.json()
    assert set(body["meta"].keys()) == set()
    names = {m["display_name"] for m in body["data"]}
    assert names == {"Owner", "Pub Emp"}
    assert all(set(m.keys()) == {"id", "display_name"} for m in body["data"])

    outsider_tokens = _register_and_login(client, "pubmembers.outsider@example.com")
    _create_org(client, outsider_tokens, name="Other Org")
    denied = client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers=_auth(outsider_tokens),
    )
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "ORGANIZATION_NOT_FOUND"

    missing = client.get(
        f"/api/v1/organizations/{uuid.uuid4()}/members",
        headers=_auth(emp_tokens),
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ORGANIZATION_NOT_FOUND"

    anonymous = client.get(f"/api/v1/organizations/{org_id}/members")
    assert anonymous.status_code == 401


def test_members_include_org_roles(client: TestClient) -> None:
    owner_tokens = _register_and_login(client, "roles.owner@example.com", display_name="Owner")
    organization = _create_org(client, owner_tokens, name="Roles Org")
    org_id = organization["id"]
    invited = client.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": "roles.emp@example.com", "displayName": "Emp"},
        headers=_auth(owner_tokens),
    ).json()["data"]

    members = client.get(
        f"/api/v1/organizations/{org_id}/users",
        headers=_auth(owner_tokens),
    ).json()["data"]
    by_email = {m["email"]: m["roles"] for m in members}
    assert by_email["roles.emp@example.com"] == ["employee"]
    assert "org_admin" in by_email["roles.owner@example.com"]
    assert invited["id"]


def test_role_change_reflected_in_members(client: TestClient) -> None:
    owner_tokens = _register_and_login(client, "roles.chg@example.com")
    organization = _create_org(client, owner_tokens, name="RolesChg Org")
    org_id = organization["id"]
    invited = client.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": "roles.chg.emp@example.com", "displayName": "Emp"},
        headers=_auth(owner_tokens),
    ).json()["data"]

    client.patch(
        f"/api/v1/organizations/{org_id}/users/{invited['id']}/role",
        json={"role": "manager"},
        headers=_auth(owner_tokens),
    )
    members = client.get(
        f"/api/v1/organizations/{org_id}/users",
        headers=_auth(owner_tokens),
    ).json()["data"]
    emp = next(m for m in members if m["email"] == "roles.chg.emp@example.com")
    assert emp["roles"] == ["manager"]


def test_platform_role_excluded_from_org_roles(client: TestClient) -> None:
    owner_tokens = _register_and_login(client, "roles.pa@example.com")
    organization = _create_org(client, owner_tokens, name="RolesPa Org")
    org_id = organization["id"]
    invited = client.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": "roles.pa.emp@example.com", "displayName": "Emp"},
        headers=_auth(owner_tokens),
    ).json()["data"]

    now = datetime.now(UTC).isoformat()
    with sqlite3.connect(TEST_DB_PATH) as connection:
        connection.execute(
            "INSERT INTO user_role (id, user_id, role_id, organization_id, created_at, updated_at)"
            " VALUES (?, ?, ?, NULL, ?, ?)",
            (
                uuid.uuid4().hex,
                invited["id"].replace("-", ""),
                stable_id("role", "platform_admin").hex,
                now,
                now,
            ),
        )
        connection.commit()

    members = client.get(
        f"/api/v1/organizations/{org_id}/users",
        headers=_auth(owner_tokens),
    ).json()["data"]
    emp = next(m for m in members if m["email"] == "roles.pa.emp@example.com")
    assert emp["roles"] == ["employee"]
    assert "platform_admin" not in emp["roles"]
