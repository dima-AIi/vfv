"""Manual demonstration of organizations + RBAC flow.

Run with backend serving NEW code on 127.0.0.1:8010:
    cd backend && uv run python ../scripts/demo_org_flow.py
"""

import sqlite3
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8010/api/v1"
DB_PATH = Path(__file__).resolve().parents[1] / "devos.db"


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=30)
    suffix = str(int(time.time()))

    email_a = f"owner.{suffix}@example.com"
    password = "org-demo-password-1"

    reg_a = client.post(
        "/auth/register",
        json={"email": email_a, "password": password, "displayName": "Org Owner"},
    )
    print(f"register A          -> {reg_a.status_code} {reg_a.json()['data']['email']}")
    login_a = client.post("/auth/login", json={"email": email_a, "password": password})
    tokens_a = login_a.json()["data"]["tokens"]
    headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}

    org = client.post(
        "/organizations",
        json={"name": f"Demo Org {suffix}", "description": "flow demonstration"},
        headers=headers_a,
    )
    org_body = org.json()["data"]
    org_id = org_body["id"]
    print(f"create org          -> {org.status_code} {org_body['name']} id={org_id}")

    email_b = f"member.{suffix}@example.com"
    invited = client.post(
        f"/organizations/{org_id}/users",
        json={"email": email_b, "displayName": "Member B", "password": "member-pass-123"},
        headers=headers_a,
    )
    invited_body = invited.json()["data"]
    print(
        f"invite B            -> {invited.status_code} "
        f"{invited_body['email']} generated_password={invited_body['generated_password']}",
    )

    login_b = client.post(
        "/auth/login",
        json={"email": email_b, "password": "member-pass-123"},
    )
    tokens_b = login_b.json()["data"]["tokens"]
    headers_b = {"Authorization": f"Bearer {tokens_b['access_token']}"}
    print(f"login B             -> {login_b.status_code}")

    me_b = client.get("/auth/me", headers=headers_b).json()["data"]
    print(
        f"me B                -> organization={me_b['organization']} roles={me_b['roles']}",
    )
    assert me_b["organization"]["id"] == org_id
    assert "employee" in me_b["roles"]

    denied = client.post(
        f"/organizations/{org_id}/users",
        json={"email": f"sneaky.{suffix}@example.com", "displayName": "Sneaky"},
        headers=headers_b,
    )
    error = denied.json()["error"]
    print(f"B invites           -> {denied.status_code} {error['code']}")
    assert denied.status_code == 403 and error["code"] == "PERMISSION_DENIED"

    promote = client.patch(
        f"/organizations/{org_id}/users/{invited_body['id']}/role",
        json={"role": "manager"},
        headers=headers_a,
    )
    print(f"A promotes B        -> {promote.status_code} role=manager")
    me_b2 = client.get("/auth/me", headers=headers_b).json()["data"]
    print(f"me B after promote  -> roles={me_b2['roles']}")
    assert "manager" in me_b2["roles"] and "employee" not in me_b2["roles"]

    connection = sqlite3.connect(DB_PATH)
    rows = connection.execute(
        "SELECT action_type, entity_type, detail FROM audit_record"
        " ORDER BY created_at DESC LIMIT 6",
    ).fetchall()
    connection.close()
    print("audit_record (last 6):")
    for action_type, entity_type, detail in reversed(rows):
        print(f"  - {action_type:24s} entity={entity_type:12s} detail={detail}")

    print("ORG FLOW DEMONSTRATION PASSED")
    return 0


if __name__ == "__main__":
    import time

    sys.exit(main())
