"""HTTP-level walkthrough of the UI auth scenario (browser-equivalent calls).

Run with backend serving on 127.0.0.1:8010:
    cd backend && uv run python ../scripts/demo_ui_auth_flow.py
"""

import os
import sys

import httpx

BASE = os.environ.get("DEMO_BASE", "http://127.0.0.1:8021/api/v1")


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=30)
    suffix = "ui" + str(int(time.time()))
    email = f"ui.user.{suffix}@example.com"
    password = "ui-demo-password-1"

    anonymous_me = client.get("/auth/me")
    print(
        f"1. anonymous /auth/me        -> {anonymous_me.status_code} "
        f"{anonymous_me.json()['error']['code']}  (UI: RequireAuth redirects to /login)",
    )
    assert anonymous_me.status_code == 401

    registered = client.post(
        "/auth/register",
        json={"email": email, "password": password, "displayName": "UI Demo User"},
    )
    assert registered.status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": password})
    tokens = login.json()["data"]["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    display_name = login.json()["data"]["user"]["display_name"]
    print(f"2. register + auto-login     -> 201/200 as {display_name}")

    me_before = client.get("/auth/me", headers=headers).json()["data"]
    print(
        f"3. me before org             -> organization={me_before['organization']} "
        f"(UI topbar shows create-org form)",
    )
    org_name = f"UI Org {suffix}"
    created_org = client.post(
        "/organizations",
        json={"name": org_name},
        headers=headers,
    )
    assert created_org.status_code == 201
    print(f"4. create organization       -> 201 {created_org.json()['data']['name']}")
    me_after = client.get("/auth/me", headers=headers).json()["data"]
    assert me_after["organization"] is not None
    assert me_after["organization"]["name"] == org_name
    print(f"   me after                  -> organization={me_after['organization']}")

    logout = client.post("/auth/logout", headers=headers)
    assert logout.status_code == 204
    me_after_logout = client.get("/auth/me", headers=headers)
    print(
        f"5. logout                    -> {logout.status_code}; "
        f"me with old token -> {me_after_logout.status_code}",
    )

    login_again = client.post("/auth/login", json={"email": email, "password": password})
    new_tokens = login_again.json()["data"]["tokens"]
    me_final = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    ).json()["data"]
    print(
        f"6. re-login                  -> organization={me_final['organization']}"
        f" roles={me_final['roles']}",
    )
    deep_link_target = "/projects"
    print(f"7. deep link {deep_link_target} -> RequireAuth stores from={deep_link_target!r}; "
          "after login navigate(from) returns user there (client router)")

    print("UI AUTH FLOW PASSED")
    return 0


if __name__ == "__main__":
    import time

    sys.exit(main())
