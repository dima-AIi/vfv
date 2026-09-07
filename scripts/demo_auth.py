"""Manual demonstration of the identity/auth lifecycle.

Run with backend serving on 127.0.0.1:8010:
    cd backend && uv run python ../scripts/demo_auth.py
"""

import sqlite3
import sys
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8010/api/v1"
DB_PATH = Path(__file__).resolve().parents[1] / "devos.db"


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=30)

    unique = int(time.time())
    email = f"demo.user.{unique}@example.com"
    password = "demo-password-123"

    registered = client.post(
        "/auth/register",
        json={"email": email.upper(), "password": password, "displayName": "Demo User"},
    )
    print(f"register  -> {registered.status_code}")
    print("          ", registered.json()["data"])

    login = client.post("/auth/login", json={"email": email, "password": password})
    login_body = login.json()["data"]
    tokens = login_body["tokens"]
    print(f"login     -> {login.status_code} user={login_body['user']['email']}")
    print(f"           access_token[:25]={tokens['access_token'][:25]}...")
    print(f"           refresh_token[:12]={tokens['refresh_token'][:12]}...")

    failed = client.post(
        "/auth/login",
        json={"email": email, "password": "definitely-wrong-pass"},
    )
    print(
        f"bad login -> {failed.status_code} "
        f"{failed.json()['error']['code']} (audit: LOGIN_FAILED)",
    )
    assert failed.status_code == 401

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    print(f"me        -> {me.status_code} {me.json()['data']}")

    refreshed = client.post("/auth/refresh", json={"refreshToken": tokens["refresh_token"]})
    refreshed_tokens = refreshed.json()["data"]["tokens"]
    print(f"refresh   -> {refreshed.status_code} rotated=True "
          f"new_refresh[:12]={refreshed_tokens['refresh_token'][:12]}...")

    reuse = client.post("/auth/refresh", json={"refreshToken": tokens["refresh_token"]})
    error = reuse.json()["error"]
    print(f"reuse     -> {reuse.status_code} {error['code']}")
    assert reuse.status_code == 401 and error["code"] == "SESSION_REVOKED"

    logout = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {refreshed_tokens['access_token']}"},
    )
    print(f"logout    -> {logout.status_code}")

    connection = sqlite3.connect(DB_PATH)
    rows = connection.execute(
        "SELECT action_type, entity_type, user_id IS NOT NULL, detail"
        " FROM audit_record ORDER BY created_at",
    ).fetchall()
    connection.close()
    print("audit_record:")
    for action_type, entity_type, has_user, detail in rows:
        print(f"  - {action_type:16s} entity={entity_type:7s} user_linked={bool(has_user)}"
              f" detail={detail}")

    print("AUTH DEMONSTRATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
